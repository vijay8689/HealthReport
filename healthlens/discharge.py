"""Source-preserving discharge extraction; no clinical facts are inferred."""
import hashlib
import re
from pathlib import Path

from healthlens.ingestion import IntakeError, _patient_names, normalize_patient_name, parse_bytes
from healthlens.models import DischargeEntry, DischargeSummary, Document

# Canonical sections and the explicit source headings that map to them.
SECTION_ALIASES = {
    "Patient details": ["patient details", "patient information", "patient name", "name", "age", "sex", "gender", "patient id", "uhid", "mrn", "address", "date of birth", "dob"],
    "Admission and discharge": ["admission details", "admission date", "date of admission", "discharge date", "date of discharge", "admitted on", "discharged on", "admitting doctor", "consultant", "hospital", "ward", "ip no"],
    "Diagnoses": ["diagnosis", "diagnoses", "final diagnosis", "discharge diagnosis", "discharge diagnoses", "primary diagnosis", "secondary diagnosis", "provisional diagnosis"],
    "Reason for admission": ["reason for admission", "chief complaints", "chief complaint", "presenting complaints", "presenting complaint"],
    "Medical history": ["medical history", "past medical history", "past history", "history", "history of present illness", "family history", "personal history"],
    "Allergies": ["allergies", "allergy", "drug allergies", "known allergies"],
    "Examination and vitals": ["examination", "physical examination", "clinical examination", "examination findings", "vitals", "vital signs", "on examination"],
    "Investigations": ["investigations", "investigation", "lab results", "laboratory results", "laboratory investigations", "imaging", "test results"],
    "Procedures": ["procedures", "procedure", "surgery", "operations", "operative notes", "procedures performed"],
    "Hospital course and treatment": ["hospital course", "course in hospital", "hospital stay", "treatment", "treatment given", "treatment received", "hospital course and treatment"],
    "Condition at discharge": ["condition at discharge", "discharge condition", "discharge status"],
    "Discharge medications": ["discharge medications", "medications at discharge", "medication on discharge", "medications on discharge", "discharge medication", "medicines on discharge", "discharge medicines", "medications", "medicines", "treatment advised"],
    "Discharge instructions": ["discharge instructions", "discharge advice", "advice on discharge", "instructions", "advice", "diet", "diet advice", "activity", "activity restrictions", "wound care"],
    "Follow-up": ["follow up", "follow-up", "followup", "follow up advice", "follow-up advice", "follow up plan", "follow-up plan", "review", "next appointment"],
    "Warning signs": ["warning signs", "red flags", "when to seek help", "return precautions", "emergency instructions"],
    "Other information": [],
}
ALIASES = {alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases}


def discharge_patient_names(pages: list[dict]) -> set[str]:
    """Allow name evidence when scanned headers lose their label alignment."""
    names = _patient_names(pages)
    # Scanned forms can put the Name label after its value in OCR reading order.
    # Honorifics also identify patient names in the admission-history narrative.
    # Exclude Dr. so consultant names alone do not satisfy patient-name presence.
    pattern = r"\b(?:Mr|Mrs|Ms|Miss)\.?[ \t]+((?:[^\W\d_]+\.?[ \t]+){1,5}[^\W\d_]+\.?)"
    for page in pages:
        for match in re.finditer(pattern, page["text"], re.I):
            names.add(normalize_patient_name(match.group(1)))
    return names


def extract_sections(pages: list[dict]) -> dict[str, list[DischargeEntry]]:
    sections = {section: [] for section in SECTION_ALIASES}
    current = "Other information"
    for page in pages:
        for index, raw in enumerate(page["text"].splitlines(), 1):
            line = raw.strip()
            if not line:
                continue
            # Match only explicit headings or labeled fields, never words in prose.
            label = re.split(r"\s*[:：]\s*", line, maxsplit=1)[0]
            normalized = re.sub(r"\s+", " ", label).strip(" .\t").casefold()
            section = ALIASES.get(normalized)
            if section:
                current = section
            elif normalized in {"discharge summary", "discharge report"}:
                current = "Other information"
            sections[current].append(DischargeEntry(text=raw, locator=f"{page['locator']}, line {index}"))
    return sections


def ingest_discharge(content: bytes, filename: str, patient_id: str,
                     patient_name: str) -> tuple[Document, DischargeSummary]:
    if Path(filename).suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise IntakeError("Upload a discharge summary as PDF, PNG, JPG, or JPEG.")
    pages, ocr = parse_bytes(content, filename)
    document = Document(patient_id=patient_id, name=Path(filename).name,
                        kind="Discharge summary", hash=hashlib.sha256(content).hexdigest(),
                        pages=pages, ocr=ocr, status="Needs review")
    sections = extract_sections(pages)
    summary = DischargeSummary(patient_id=patient_id, document_id=document.id, sections=sections)
    names = discharge_patient_names(pages)
    if not names:
        document.status = "Quarantined"
        summary.status = "quarantined"
        document.warnings.append("No patient name was found in the document. This record is quarantined; upload a copy with a readable patient name.")
    if not any(sections[name] for name in sections if name != "Other information"):
        document.warnings.append("No supported section headings were recognized. All readable content is retained under Other information for review.")
    if ocr:
        document.warnings.append("Text was read using OCR. Check medication names, doses, dates, and other details against the original.")
    return document, summary
