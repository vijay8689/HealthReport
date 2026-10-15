from datetime import date

import pytest

from healthlens.markers import marker_key
from healthlens.models import Document, Observation, Patient


def result(name, unit="mg/dL", method="Jaffes", year=2026):
    return Observation(patient_id="P-HISTORY", document_id=str(year), name=name, unit=unit,
                       method=method, value=0.7, original_value="0.7", date=date(year, 3, 28),
                       source_text="Creatinine 0.7 mg/dL", locator="Page 1", status="accepted")


def test_equivalent_names_group_without_changing_source_or_combining_units():
    old = result("Creatinine.", method="Alkaline Picrate", year=2025)
    new = result("SERUM CREATININE")
    assert marker_key(old) == marker_key(new)
    assert marker_key(new) != marker_key(result("Creatinine", unit="umol/L"))
    assert marker_key(new) != marker_key(result("Urine creatinine"))
    assert old.name == "Creatinine." and old.method == "Alkaline Picrate"


def test_hemoglobin_legacy_units_share_history_without_combining_hba1c():
    assert marker_key(result("HAEMOGLOBIN", unit="gm%")) == marker_key(result("Hemoglobin", unit="g/dL"))
    assert marker_key(result("Hemoglobin", unit="g/L")) != marker_key(result("Hemoglobin", unit="g/dL"))
    assert marker_key(result("GLYCOSYLATED HAEMOGLOBIN (HBA1C)", unit="%")) != marker_key(result("HAEMOGLOBIN", unit="gm%"))


def test_supplied_reports_form_one_three_date_hemoglobin_history():
    from pathlib import Path
    from healthlens.ingestion import ingest
    from ui.charts import lab_chart

    records = []
    for filename in ("951972010.pdf", "277693287.pdf", "532642229.pdf"):
        path = Path("docs") / filename
        if not path.exists():
            pytest.skip("User-provided report is not present")
        _, observations = ingest(path.read_bytes(), filename, "P-HISTORY", "Sumana")
        records.extend(o for o in observations if marker_key(o)[0] == "Hemoglobin")
    assert len({marker_key(o) for o in records}) == 1
    assert [(o.date, o.value) for o in sorted(records, key=lambda o: o.date)] == [
        (date(2023, 8, 19), 13.2), (date(2025, 2, 27), 13.7), (date(2026, 3, 28), 12.2)]
    assert len(lab_chart(records).data[-1].x) == 3


@pytest.mark.usefixtures("signed_in_demo")
@pytest.mark.parametrize("records", [
    [("Creatinine.", "Alkaline Picrate", 2025, "mg/dL"), ("SERUM CREATININE", "Jaffes", 2026, "mg/dL")],
    [("HAEMOGLOBIN", "SLS", 2023, "gm%"), ("Hemoglobin", "Spectrophotometry", 2025, "g/dL"),
     ("HAEMOGLOBIN", "Photometry", 2026, "gm%")],
])
def test_chart_shows_reports_with_different_names_and_methods(records):
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("app.py", default_timeout=30).run()
    workspace = app.session_state.workspace
    workspace.patients.append(Patient(id="P-HISTORY", name="History", initials="H"))
    for name, method, year, unit in records:
        observation = result(name, unit=unit, method=method, year=year)
        document = Document(id=str(year), patient_id="P-HISTORY", name=f"{year}.pdf", date=observation.date,
                            hash=str(year), pages=[], status="Imported")
        workspace.add(document, [observation], b"source")
    app.session_state.pending_patient_id = "P-HISTORY"
    app.switch_page("app_pages/trends.py").run()
    assert not app.exception
    choice = next(widget for widget in app.selectbox if widget.label == "Choose a test")
    assert len(choice.options) == 1
    assert f"{len(records)} results across {len(records)} dates" in choice.options[0]
    assert len(app.dataframe[-1].value) == len(records)
    assert not any("Only one dated result" in message.value for message in app.info)


@pytest.mark.usefixtures("signed_in_demo")
def test_overview_and_trends_list_each_test_once_across_unit_contexts():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("app.py", default_timeout=30).run()
    workspace = app.session_state.workspace
    workspace.patients.append(Patient(id="P-HISTORY", name="History", initials="H"))
    workspace.observations.extend([
        result("RBC Count", unit="millions/cumm", year=2023),
        result("Total RBC Count", unit="mill /cu.mm", year=2025),
        result("RBC", unit="10^6/cu.mm", year=2026),
        result("WBC Count", unit="cells/cumm", year=2025),
        result("Total Leucocyte Count", unit="10^3/µL", year=2026),
    ])
    app.session_state.pending_patient_id = "P-HISTORY"
    app.run()
    assert not app.exception
    overview = app.selectbox(key="overview_marker_P-HISTORY")
    assert overview.options.count("Red blood cell count") == 1
    assert overview.options.count("White blood cell count") == 1
    overview.set_value("Red blood cell count").run()
    assert not app.exception
    assert len(next(widget for widget in app.selectbox if widget.label == "Units and sample").options) == 3
    app.switch_page("app_pages/trends.py").run()
    assert not app.exception
    options = next(widget for widget in app.selectbox if widget.label == "Choose a test").options
    assert sum(option.startswith("Red blood cell count ·") for option in options) == 1
    assert sum(option.startswith("White blood cell count ·") for option in options) == 1
