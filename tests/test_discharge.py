import io

import pymupdf
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from healthlens.discharge import discharge_patient_names, extract_sections, ingest_discharge
from healthlens.ingestion import IntakeError
from healthlens.workspace import Workspace


SOURCE = """DISCHARGE SUMMARY
Patient Name: Alex Morgan
Admission Date: 2026-09-20
Discharge Date: 2026-09-24
Final Diagnosis: Example diagnosis
Hospital Course:
Observed during admission.
Discharge Medications:
Example tablet | 5 mg | daily | 7 days
Follow-up: Review in one week
Warning Signs: Return for worsening symptoms
"""


def pdf_bytes(text=SOURCE):
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((40, 40), text, fontsize=10)
        return pdf.tobytes()


def test_pdf_sections_preserve_every_source_line_and_medication_details():
    document, summary = ingest_discharge(pdf_bytes(), "discharge.pdf", "P-1", "Alex Morgan")
    assert document.kind == "Discharge summary"
    assert summary.status == "needs_review"
    assert "5 mg | daily | 7 days" in summary.sections["Discharge medications"][-1].text
    assert summary.sections["Follow-up"][0].locator.startswith("Page 1, line")
    assert summary.sections["Allergies"] == []
    source_lines = [line for page in document.pages for line in page["text"].splitlines() if line.strip()]
    extracted_lines = [entry.text for entries in summary.sections.values() for entry in entries]
    assert sorted(source_lines) == sorted(extracted_lines)


@pytest.mark.parametrize("format, filename", [("PNG", "discharge.png"), ("JPEG", "discharge.jpg")])
def test_image_ocr_intake_and_missing_headings(monkeypatch, format, filename):
    monkeypatch.setattr("healthlens.ingestion.ocr_image", lambda image: SOURCE)
    image = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(image, format=format)
    document, summary = ingest_discharge(image.getvalue(), filename, "P-1", "Alex")
    assert document.ocr
    assert summary.sections["Diagnoses"]
    unclassified = extract_sections([{"locator": "Page 1", "text": "An unfamiliar narrative\nAnother line"}])
    assert len(unclassified["Other information"]) == 2


def test_scanned_pdf_uses_ocr(monkeypatch):
    monkeypatch.setattr("healthlens.ingestion.ocr_image", lambda image: SOURCE)
    with pymupdf.open() as pdf:
        pdf.new_page()
        content = pdf.tobytes()
    document, summary = ingest_discharge(content, "scan.pdf", "P-1", "Alex")
    assert document.ocr
    assert summary.sections["Discharge medications"]


def test_missing_patient_name_is_quarantined():
    document, summary = ingest_discharge(pdf_bytes("No patient header"), "discharge.pdf", "P-1", "Alex Morgan")
    assert document.status == "Quarantined"
    assert summary.status == "quarantined"


@pytest.mark.parametrize("text", [
    ": Mr. K HANUMANTA RAO\nIP No : EXAMPLE\nName\nAge/Gender: 59 Years/Male",
    "BRIEF HISTORY OF THE PATIENT:\nMr. K. Hanumanta Rao, aged 59 years old male",
    "Patient Name\n: Alex Morgan",
])
def test_scanned_name_with_displaced_label_is_recognized(text):
    assert discharge_patient_names([{"text": text}])
    document, summary = ingest_discharge(pdf_bytes(text), "discharge.pdf", "P-1", "Selected Profile")
    assert summary.status == "needs_review"
    assert document.status == "Needs review"


def test_consultant_name_does_not_replace_patient_name():
    assert not discharge_patient_names([{"text": "Consultant: Dr. Example Doctor\nNo patient header"}])


def test_hanumanta_rao_profile_accepts_initial_and_title_in_document():
    document, summary = ingest_discharge(
        pdf_bytes("Name\n: Mr. K HANUMANTA RAO\nPrimary Diagnosis: Example"),
        "discharge.pdf", "P-HR", "Hanumanta rao",
    )
    assert summary.status == "needs_review"
    document.warnings.append("Patient name could not be matched to the selected profile. Check the source and upload under the matching patient; this record is quarantined.")
    ws = Workspace()
    ws.add_discharge(document, summary, b"original")
    Workspace.from_session(ws)
    assert document.warnings == []
    summary.status = "reviewed"
    document.status = "Reviewed"
    Workspace.from_session(ws)
    assert summary.status == "reviewed"
    assert document.status == "Reviewed"


@pytest.mark.parametrize("text", [SOURCE.replace("Alex Morgan", "Someone Else"), SOURCE + "\nPatient Name: Another Name"])
def test_any_document_patient_name_proceeds_under_selected_profile(text):
    document, summary = ingest_discharge(pdf_bytes(text), "discharge.pdf", "P-1", "Alex Morgan")
    assert document.status == "Needs review"
    assert summary.status == "needs_review"
    assert document.patient_id == summary.patient_id == "P-1"


@pytest.mark.parametrize("text, warning", [
    (SOURCE.replace("Alex Morgan", "Someone Else"), "Patient name could not be matched to the selected profile. Old policy."),
    ("Name\n: Mr. K HANUMANTA RAO\nDiagnosis: Example", "No patient name was found in the document. This record is quarantined; upload a copy with a readable patient name."),
])
def test_existing_named_quarantined_discharge_is_released_on_session_upgrade(text, warning):
    original = pdf_bytes(text)
    document, summary = ingest_discharge(original, "discharge.pdf", "P-1", "Alex Morgan")
    document.status = "Quarantined"
    summary.status = "quarantined"
    document.warnings.append(warning)
    ws = Workspace()
    ws.add_discharge(document, summary, original)
    upgraded = Workspace.from_session(ws)
    assert upgraded.discharges("P-1")[0].status == "needs_review"
    assert document.status == "Needs review"
    assert not document.warnings
    assert upgraded.originals[document.id] == original


def test_repository_duplicate_isolation_upgrade_and_removal():
    ws = Workspace()
    original = pdf_bytes()
    document, summary = ingest_discharge(original, "discharge.pdf", "P-1", "Alex Morgan")
    assert ws.add_discharge(document, summary, original)
    duplicate, duplicate_summary = ingest_discharge(original, "copy.pdf", "P-1", "Alex Morgan")
    assert not ws.add_discharge(duplicate, duplicate_summary, original)
    assert ws.discharges("P-2") == []
    assert not ws.obs("P-1")
    assert ws.originals[document.id] == original
    ws.remove_document("P-1", document.id)
    assert not ws.discharges("P-1")
    assert document.id not in ws.originals
    del ws.discharge_summaries
    assert Workspace.from_session(ws).discharge_summaries == []


def test_reject_wrong_format_and_association():
    with pytest.raises(IntakeError):
        ingest_discharge(SOURCE.encode(), "discharge.txt", "P-1", "Alex")
    ws = Workspace()
    document, summary = ingest_discharge(pdf_bytes(), "discharge.pdf", "P-1", "Alex")
    summary.patient_id = "P-2"
    with pytest.raises(ValueError):
        ws.add_discharge(document, summary, b"source")


def test_discharge_page_empty_populated_reviewed_and_patient_switch():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app.switch_page("app_pages/discharge.py").run()
    assert not app.exception
    ws = app.session_state.workspace
    pid = app.session_state.patient_id
    original = pdf_bytes(SOURCE.replace("Alex Morgan", ws.patient(pid).name))
    document, summary = ingest_discharge(original, "discharge.pdf", pid, ws.patient(pid).name)
    ws.add_discharge(document, summary, original)
    app.run()
    assert not app.exception
    assert len(app.get("download_button")) == 2
    next(b for b in app.button if b.label == "Mark as checked against source").click().run()
    assert not app.exception
    assert ws.discharges(pid)[0].status == "reviewed"
    assert document.status == "Reviewed"
    from healthlens.models import Patient
    another_pid = "DISCHARGE-OTHER"
    ws.patients.append(Patient(id=another_pid, name="Another Patient", initials="AP"))
    app.run()
    app.selectbox(key="patient_id").select(another_pid).run()
    assert not app.exception
    assert not app.get("download_button")
