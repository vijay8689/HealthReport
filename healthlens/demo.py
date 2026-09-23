"""Coherent synthetic records used by the local demonstration workspace."""
from datetime import date
import hashlib

from healthlens.models import Document, Observation, Patient, Revision

PATIENTS = [
    Patient(id="DUMMY-0001", name="Dummy Patient", initials="DP", age=42,
            sex="Female", description="Synthetic longitudinal demonstration profile"),
]

SAMPLE = """SYNTHETIC DEMONSTRATION DATA
Patient ID: HL-2048
Patient: Alex Morgan
Date: 2026-09-20
Test | Value | Unit | Reference range
Hemoglobin | 13.9 | g/dL | 12 - 15.5
Fasting glucose | 93 | mg/dL | 70 - 99
LDL cholesterol | 110 | mg/dL | 0 - 99
Vitamin D | 29 | ng/mL | 30 - 100
"""


_REPORTS = [
    ("dummy_wellness_2025-03.txt", date(2025, 3, 18), [
        ("Hemoglobin", "Blood count", 12.8, "g/dL", 12.0, 15.5, "accepted"),
        ("Fasting glucose", "Metabolic", 101, "mg/dL", 70, 99, "accepted"),
        ("LDL cholesterol", "Lipids", 126, "mg/dL", 0, 99, "accepted"),
        ("Vitamin D", "Vitamins", 22, "ng/mL", 30, 100, "accepted"),
        ("TSH", "Thyroid", 3.4, "mIU/L", 0.4, 4.5, "accepted"),
    ]),
    ("dummy_followup_2025-10.txt", date(2025, 10, 7), [
        ("Hemoglobin", "Blood count", 13.1, "g/dL", 12.0, 15.5, "accepted"),
        ("Fasting glucose", "Metabolic", 97, "mg/dL", 70, 99, "accepted"),
        ("LDL cholesterol", "Lipids", 114, "mg/dL", 0, 99, "accepted"),
        ("Vitamin D", "Vitamins", 28, "ng/mL", 30, 100, "corrected"),
        ("TSH", "Thyroid", 2.8, "mIU/L", 0.4, 4.5, "accepted"),
    ]),
    ("dummy_annual_2026-09.txt", date(2026, 9, 12), [
        ("Hemoglobin", "Blood count", 13.4, "g/dL", 12.0, 15.5, "accepted"),
        ("Fasting glucose", "Metabolic", 94, "mg/dL", 70, 99, "accepted"),
        ("LDL cholesterol", "Lipids", 104, "mg/dL", 0, 99, "accepted"),
        ("Vitamin D", "Vitamins", 34, "ng/mL", 30, 100, "needs_review"),
        ("TSH", "Thyroid", 2.2, "mIU/L", 0.4, 4.5, "rejected"),
    ]),
]


def demo_records():
    """Return fresh source-linked records for DUMMY-0001."""
    documents, observations, originals = [], [], {}
    for report_index, (filename, report_date, rows) in enumerate(_REPORTS, start=1):
        lines = ["SYNTHETIC DEMONSTRATION DATA", "Patient ID: DUMMY-0001",
                 "Patient: Dummy Patient", f"Date: {report_date.isoformat()}",
                 "Test | Value | Unit | Reference range"]
        lines.extend(f"{name} | {value:g} | {unit} | {low:g} - {high:g}"
                     for name, _, value, unit, low, high, _ in rows)
        source = ("\n".join(lines) + "\n").encode()
        document_id = f"DUMMY-DOC-{report_index:02d}"
        documents.append(Document(
            id=document_id, patient_id="DUMMY-0001", name=filename, date=report_date,
            hash=hashlib.sha256(source).hexdigest(),
            pages=[{"locator": "Lines 1-10", "text": source.decode()}],
            status="Needs review" if any(row[-1] == "needs_review" for row in rows) else "Reviewed",
            source="Bundled synthetic sample",
        ))
        originals[document_id] = source
        for line_number, (name, category, value, unit, low, high, status) in enumerate(rows, start=6):
            observations.append(Observation(
                id=f"DUMMY-OBS-{report_index:02d}-{line_number:02d}",
                patient_id="DUMMY-0001", document_id=document_id, name=name,
                category=category, value=value, original_value=f"{value:g}", unit=unit,
                low=low, high=high, date=report_date, locator=f"Line {line_number}",
                source_text=lines[line_number - 1], status=status,
                version=2 if status == "corrected" else 1, specimen="Serum",
                method="Routine laboratory method",
            ))
    corrected = next(item for item in observations if item.status == "corrected")
    revision = Revision(
        observation_id=corrected.id, actor="Demo reviewer",
        reason="Corrected transcription after checking the synthetic source report.",
        before={**corrected.model_dump(mode="json"), "value": 82.0, "original_value": "82"},
        after=corrected.model_dump(mode="json"),
    )
    return documents, observations, [revision], originals

