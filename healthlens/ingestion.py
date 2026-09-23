"""Bounded local parsing and conservative source-linked lab extraction."""
import hashlib
import io
import re
import zipfile
from datetime import date
from pathlib import Path

from healthlens.models import Document, Observation

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 100
MAX_TEXT = 1_000_000
NUMBER = r"[-+]?\d+(?:\.\d+)?"
ROW = re.compile(rf"^\s*(?P<name>[^|]{{1,100}})\|\s*(?P<cmp><=|>=|<|>)?\s*(?P<value>{NUMBER})\s*\|\s*(?P<unit>[^|]{{1,30}})\|\s*(?P<low>{NUMBER})\s*[-–]\s*(?P<high>{NUMBER})\s*$")
BLOCK_NAME = re.compile(r"^[A-Z0-9][A-Z0-9 /,&().\-]{1,100}$")
BLOCK_VALUE = re.compile(r"^\s*(?P<cmp><=|>=|<|>)?\s*(?P<value>[-+]?\d[\d,]*(?:\.\d+)?)\s*$")
BLOCK_RANGE = re.compile(rf"^\s*(?P<low>{NUMBER})\s*[-–]\s*(?P<high>{NUMBER})\s*(?P<unit>[^\d].*)?$")
SAMPLE_DATE = re.compile(r"Sample Collected on\s*:\s*(\d{1,2})-(\d{1,2})-(\d{4})", re.I)
CATEGORIES = {"hemoglobin": "Hematology", "glucose": "Metabolic", "hba1c": "Metabolic",
              "cholesterol": "Cardiovascular", "triglycer": "Cardiovascular", "vitamin": "Nutritional",
              "creatinine": "Renal", "urea": "Renal", "tsh": "Thyroid"}
NON_TEST_PREFIXES = ("sample collected", "description:", "apollo clinic", "phone no", "email:",
                     "disclaimer:", "lab panel", "health report", "purpose of visit")


class IntakeError(ValueError):
    """Safe, actionable error that can be displayed to the user."""


def ocr_image(image) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(image, lang="eng", timeout=20)
    except ImportError as exc:
        raise IntakeError("OCR is unavailable. Install pytesseract and Tesseract, or upload a text-based report.") from exc
    except Exception as exc:
        raise IntakeError("OCR could not run. Check that English Tesseract is installed, or use a text-based report.") from exc


def parse_bytes(content: bytes, filename: str) -> tuple[list[dict], bool]:
    if not content or len(content) > MAX_BYTES:
        raise IntakeError("The document must contain data and be smaller than 20 MB.")
    ext = Path(filename).suffix.lower()
    pages, used_ocr = [], False
    try:
        if ext == ".txt":
            text = content.decode("utf-8-sig")
            if "\x00" in text:
                raise IntakeError("This file is not supported UTF-8 text.")
            pages = [{"locator": "Text", "text": text}]
        elif ext == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise IntakeError("The file signature does not match PDF.")
            import pymupdf
            from PIL import Image
            with pymupdf.open(stream=content, filetype="pdf") as pdf:
                if pdf.needs_pass:
                    raise IntakeError("Password-protected PDFs are not supported. Upload an unlocked copy.")
                if len(pdf) > MAX_PAGES:
                    raise IntakeError("This report exceeds the 100-page limit.")
                scanned = 0
                for index, page in enumerate(pdf):
                    text = page.get_text()
                    if len(text.strip()) < 15:
                        scanned += 1
                        if scanned > 5:
                            raise IntakeError("Demo OCR supports up to five scanned pages per file. Split this report.")
                        if page.rect.width * page.rect.height * 4 > 20_000_000:
                            raise IntakeError("This PDF page exceeds the safe raster size.")
                        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                        text = ocr_image(Image.open(io.BytesIO(pix.tobytes("png"))))
                        used_ocr = True
                    pages.append({"locator": f"Page {index + 1}", "text": text})
        elif ext == ".docx":
            if not zipfile.is_zipfile(io.BytesIO(content)):
                raise IntakeError("The file signature does not match DOCX.")
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if sum(i.file_size for i in archive.infolist()) > 30 * 1024 * 1024:
                    raise IntakeError("The expanded document exceeds the safe size limit.")
                if "word/document.xml" not in archive.namelist():
                    raise IntakeError("This archive is not a Word document.")
            from docx import Document as WordDocument
            doc = WordDocument(io.BytesIO(content))
            pages = [{"locator": f"Paragraph {i + 1}", "text": p.text}
                     for i, p in enumerate(doc.paragraphs) if p.text.strip()]
            for ti, table in enumerate(doc.tables):
                for ri, row in enumerate(table.rows):
                    pages.append({"locator": f"Table {ti + 1}, row {ri + 1}",
                                  "text": " | ".join(c.text for c in row.cells)})
        elif ext in {".png", ".jpg", ".jpeg"}:
            from PIL import Image
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in {"PNG", "JPEG"} or image.width * image.height > 20_000_000:
                    raise IntakeError("Use a PNG/JPEG image under 20 megapixels.")
                pages = [{"locator": "Image 1", "text": ocr_image(image)}]
                used_ocr = True
        else:
            raise IntakeError("Use PDF, DOCX, TXT, PNG, JPG, or JPEG.")
    except IntakeError:
        raise
    except Exception as exc:
        raise IntakeError("The document could not be read. Check its format and try an unlocked, undamaged copy.") from exc
    if sum(len(page["text"]) for page in pages) > MAX_TEXT:
        raise IntakeError("The extracted text exceeds the demo processing limit.")
    if not any(page["text"].strip() for page in pages):
        raise IntakeError("No readable text was found in this document.")
    return pages, used_ocr


def _identities(pages: list[dict]) -> set[str]:
    text = "\n".join(page["text"] for page in pages)
    return {value.strip() for value in re.findall(r"Patient\s+ID\s*:?\s*([^\r\n]+)", text, re.I)}


def detect_patient_id(content: bytes, filename: str) -> str | None:
    identities = _identities(parse_bytes(content, filename)[0])
    return next(iter(identities)) if len(identities) == 1 else None


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\ufffd", " ").replace("Â", " ")).strip()


def _looks_like_name(value: str) -> bool:
    if not value or len(value) > 110 or value.lower().startswith(NON_TEST_PREFIXES):
        return False
    letters = [char for char in value if char.isalpha()]
    return bool(letters) and BLOCK_NAME.match(value) is not None and sum(c.isupper() for c in letters) / len(letters) > .72


def _page_date(text: str, fallback: date | None) -> date | None:
    match = SAMPLE_DATE.search(text)
    if not match:
        return fallback
    day_value, month, year = map(int, match.groups())
    try:
        return date(year, month, day_value)
    except ValueError:
        return fallback


def _block_observations(page: dict, patient_id: str, document_id: str,
                        fallback_date: date | None) -> list[Observation]:
    raw = page["text"].splitlines()
    lines = [_clean(line) for line in raw]
    observed_on = _page_date(page["text"], fallback_date)
    results = []
    for index in range(2, len(lines)):
        range_match = BLOCK_RANGE.match(lines[index])
        value_match = BLOCK_VALUE.match(lines[index - 1])
        if not (range_match and value_match):
            continue
        names, cursor = [], index - 2
        while cursor >= 0 and len(names) < 3 and _looks_like_name(lines[cursor]):
            names.insert(0, lines[cursor])
            cursor -= 1
        if not names:
            continue
        name = " ".join(names)
        unit = _clean(range_match.group("unit") or "").strip(" *") or "Not recorded"
        value_text = value_match.group("value")
        locator_start = index - len(names)
        category = next((category for token, category in CATEGORIES.items() if token in name.lower()), "General")
        try:
            results.append(Observation(
                patient_id=patient_id, document_id=document_id, name=name, category=category,
                value=float(value_text.replace(",", "")), original_value=(value_match.group("cmp") or "") + value_text,
                comparator=value_match.group("cmp") or "=", unit=unit,
                low=float(range_match.group("low")), high=float(range_match.group("high")), date=observed_on,
                locator=f"{page['locator']}, lines {locator_start + 1}-{index + 1}",
                source_text="\n".join(raw[locator_start:index + 1]),
            ))
        except ValueError:
            continue
    return results


def ingest(content: bytes, filename: str, patient_id: str,
           use_source_patient: bool = False) -> tuple[Document, list[Observation]]:
    pages, used_ocr = parse_bytes(content, filename)
    text = "\n".join(page["text"] for page in pages)
    identities = _identities(pages)
    target_patient_id = next(iter(identities)) if use_source_patient and len(identities) == 1 else patient_id
    mismatch = bool(identities and identities != {target_patient_id})
    dates = set(re.findall(r"^Date:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.M))
    dates.update(f"{year}-{month.zfill(2)}-{day_value.zfill(2)}"
                 for day_value, month, year in SAMPLE_DATE.findall(text))
    report_date = None
    if len(dates) == 1:
        try:
            report_date = date.fromisoformat(next(iter(dates)))
        except ValueError:
            pass
    doc = Document(patient_id=target_patient_id, name=Path(filename).name, date=report_date,
                   hash=hashlib.sha256(content).hexdigest(), pages=pages, ocr=used_ocr)
    if mismatch:
        doc.status = "Quarantined"
        doc.warnings.append("The report's patient ID does not match the selected patient, or multiple IDs are present.")
        return doc, []
    if not identities:
        doc.status = "Quarantined"
        doc.warnings.append("No explicit Patient ID was found. The report is quarantined until patient association can be verified.")
        return doc, []
    if not report_date:
        doc.warnings.append("No single unambiguous observation date was found. Review dates before analysis.")
    observations = []
    for page in pages:
        for line_no, line in enumerate(page["text"].splitlines(), 1):
            match = ROW.match(line)
            if not match:
                continue
            row = match.groupdict()
            name = row["name"].strip()
            category = next((value for key, value in CATEGORIES.items() if key in name.lower()), "General")
            locator = f"Line {line_no}" if page["locator"] == "Text" else f"{page['locator']}, line {line_no}"
            try:
                observations.append(Observation(
                    patient_id=target_patient_id, document_id=doc.id, name=name, category=category,
                    value=float(row["value"]), original_value=(row["cmp"] or "") + row["value"],
                    comparator=row["cmp"] or "=", unit=row["unit"].strip(), low=float(row["low"]),
                    high=float(row["high"]), date=report_date, locator=locator, source_text=line,
                ))
            except ValueError:
                doc.warnings.append(f"Invalid range/value at {locator}; row excluded.")
        observations.extend(_block_observations(page, target_patient_id, doc.id, report_date))
    unique = {}
    for observation in observations:
        key = (observation.name, observation.date, observation.value,
               observation.unit, observation.low, observation.high)
        unique.setdefault(key, observation)
    observations = list(unique.values())
    if not observations:
        doc.warnings.append("No supported laboratory rows found. Source text remains available for review.")
        doc.status = "Text only"
    elif any(o.low == 0 and o.high == 0 for o in observations):
        doc.warnings.append("The source contains one or more 0-0 reference ranges. Review them before use; they are not treated as validated thresholds.")
    return doc, observations
