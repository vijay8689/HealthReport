from datetime import date
from pathlib import Path

import pytest

from healthlens.ingestion import ingest
from healthlens.models import Patient
from healthlens.workspace import Workspace


SOURCE = """Test Name
Observed Values
Units
Biological Reference Intervals
* HAEMOGLOBIN
Method:Photometry
12.2
gm%
12.0 - 15.0
* GLYCOSYLATED HAEMOGLOBIN
(HBA1C)
Method:HPLC
5.4
%
Non-diabetic: <= 5.8 %
Pre-diabetic: 5.8 - 6.5 %
Diabetic: >= 6.5 %
* RBC
Normocytic Normochromic
Name
: Mrs. Sumana Pattapu
Collected On
: 28-Mar-2026 11:31 AM
Reported On: 29-Mar-2026 02:35 PM
"""


def test_separate_value_unit_method_and_multiline_name():
    document, observations = ingest(SOURCE.encode(), "report.txt", "P-002", "Sumana")
    assert document.date == date(2026, 3, 28)
    assert document.status == "Imported"
    assert [(o.name, o.value, o.unit) for o in observations] == [
        ("HAEMOGLOBIN", 12.2, "gm%"), ("GLYCOSYLATED HAEMOGLOBIN (HBA1C)", 5.4, "%")]
    assert (observations[0].low, observations[0].high) == (12, 15)
    assert observations[0].method == "Photometry"
    assert observations[1].low is None and observations[1].high is None
    assert all(o.date == document.date and o.status == "accepted" for o in observations)
    assert all(o.original_value in o.source_text for o in observations)


def test_three_column_table_uses_result_and_reference_units():
    source = """Patient: Sumana Pattapu
Investigation
Observed Value
Biological Reference Interval
Hemoglobin
Method:Spectrophotometry
13.7
12.0-15.0 g/dL
Neutrophils
67.0
40.0-80.0 %
"""
    _, observations = ingest(source.encode(), "report.txt", "P-002", "Sumana")
    assert [(o.name, o.value, o.unit, o.low, o.high) for o in observations] == [
        ("Hemoglobin", 13.7, "g/dL", 12, 15), ("Neutrophils", 67, "%", 40, 80)]


def test_existing_text_only_cloud_records_recover_without_original_bytes():
    document, _ = ingest(SOURCE.encode(), "report.txt", "P-002", "Sumana")
    document.status = "Text only"
    document.date = None
    document.source = "Pinecone"
    document.warnings = ["No supported numeric laboratory rows found.", "No single observation date could be determined."]
    workspace = Workspace.empty()
    workspace.restore_cloud_records("P-002", [(document, [], None)])
    assert len(workspace.documents) == 1
    assert len(workspace.obs("P-002")) == 2
    assert document.status == "Imported" and document.date == date(2026, 3, 28)
    assert document.warnings == []
    assert all(o.document_id == document.id for o in workspace.observations)
    assert len(workspace.reports[-1]["claims"]) == 2
    Workspace.from_session(workspace)
    assert len(workspace.observations) == 2
    assert len(workspace.reports) == 1


@pytest.mark.parametrize("filename,count,observed_on,marker,value", [
    ("532642229.pdf", 71, date(2026, 3, 28), "FASTING BLOOD GLUCOSE", 97),
    ("277693287.pdf", 39, date(2025, 2, 27), "Hemoglobin", 13.7),
    ("951972010.pdf", 42, date(2023, 8, 19), "HAEMOGLOBIN", 13.2),
])
def test_supplied_reports_extract_results(filename, count, observed_on, marker, value):
    path = Path("docs") / filename
    if not path.exists():
        pytest.skip("User-provided report is not present")
    document, observations = ingest(path.read_bytes(), filename, "P-002", "Sumana")
    assert len(observations) == count
    assert document.date == observed_on
    assert next(o.value for o in observations if o.name == marker) == value
    assert all(o.status == "accepted" and o.source_text and o.locator for o in observations)


def test_partial_import_recovers_missing_results_and_preserves_saved_ids():
    document, observations = ingest(SOURCE.encode(), "report.txt", "P-002", "Sumana")
    document.extraction_version = 0
    workspace = Workspace.empty()
    workspace.documents.append(document)
    workspace.observations.append(observations[0])
    Workspace.from_session(workspace)
    assert len(workspace.observations) == 2
    assert workspace.observations[0].id == observations[0].id
    Workspace.from_session(workspace)
    assert len(workspace.observations) == 2


def test_supplied_customer_name_pdf_extracts_hemoglobin_and_collection_date():
    path = next(Path("docs").glob("15_Oct*.pdf"), None)
    if path is None:
        pytest.skip("User-provided report is not present")
    document, observations = ingest(path.read_bytes(), path.name, "P-002", "Sumana")
    assert document.status == "Imported"
    assert document.date == date(2026, 10, 10)
    assert len(observations) == 63
    hemoglobin = next(o for o in observations if o.name == "Hemoglobin")
    assert (hemoglobin.value, hemoglobin.unit, hemoglobin.low, hemoglobin.high) == (13.1, "g/dL", 12, 15)
    workspace = Workspace.empty()
    assert workspace.add(document, observations, path.read_bytes())
    assert len(workspace.obs("P-002")) == 63
    Workspace.from_session(workspace)
    assert len(workspace.observations) == 63


@pytest.mark.usefixtures("signed_in_demo")
def test_recovered_results_appear_in_dashboard_and_trends():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("app.py", default_timeout=30).run()
    workspace = app.session_state.workspace
    workspace.patients.append(Patient(id="P-002", name="Sumana", initials="S"))
    document, _ = ingest(SOURCE.encode(), "report.txt", "P-002", "Sumana")
    document.status = "Text only"
    workspace.documents.append(document)
    app.session_state.pending_patient_id = "P-002"
    app.run()
    assert not app.exception
    assert app.selectbox(key="overview_marker_P-002").options
    assert len(app.session_state.workspace.obs("P-002")) == 2
    for page in ("trends", "evidence", "analysis", "reports"):
        app.switch_page(f"app_pages/{page}.py").run()
        assert not app.exception
