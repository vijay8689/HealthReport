from streamlit.testing.v1 import AppTest


def seed_app(app):
    from healthlens.demo import SAMPLE
    from healthlens.ingestion import ingest
    from healthlens.models import Patient
    doc, observations = ingest(SAMPLE.encode(), "sample.txt", "HL-2048")
    app.session_state.workspace.patients.append(Patient(id="HL-2048", name="Alex Morgan", initials="AM"))
    app.session_state.workspace.add(doc, observations, SAMPLE.encode())
    app.session_state.pending_patient_id = "HL-2048"
    return app.run()


def test_all_pages_and_analysis_flow():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app = seed_app(app)
    assert not app.exception
    sidebar_html = " ".join(item.value for item in app.markdown)
    assert "Patient Data" in sidebar_html
    assert "Alex Morgan" in sidebar_html
    for page in ["documents", "trends", "evidence", "timeline", "reports", "connections", "settings", "analysis"]:
        app.switch_page(f"app_pages/{page}.py").run()
        assert not app.exception, f"{page}: {app.exception}"
    assert next(b for b in app.button if b.label == "Analysis is up to date").disabled
    assert not app.exception
    assert len([r for r in app.session_state.workspace.reports if r["patient_id"] == "HL-2048"]) == 1
    app.switch_page("app_pages/reports.py").run()
    assert not app.exception
    assert len(app.get("download_button")) == 3


def test_dummy_patient_has_sample_data_in_all_sections():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app.selectbox(key="patient_id").select("DUMMY-0001").run()
    assert not app.exception
    ws = app.session_state.workspace
    assert len(ws.docs("DUMMY-0001")) == 3
    assert len(ws.obs("DUMMY-0001")) == 15
    assert any(o.status == "needs_review" for o in ws.obs("DUMMY-0001"))
    assert any(o.status == "rejected" for o in ws.obs("DUMMY-0001"))
    assert any(r["patient_id"] == "DUMMY-0001" for r in ws.reports)
    app.switch_page("app_pages/analysis.py").run()
    assert not app.exception
    assert next(b for b in app.button if b.label == "Analysis is up to date").disabled


def test_upload_shortcut_and_automatic_trends_handoff():
    from healthlens.demo import SAMPLE
    from healthlens.ingestion import ingest
    app = AppTest.from_file("app.py", default_timeout=30).run()
    next(b for b in app.button if b.label == "Upload report").click().run()
    assert not app.exception
    assert app.session_state.document_view == "Upload reports"
    doc, obs = ingest(SAMPLE.encode(), "sample.txt", "HL-2048", patient_name="Alex Morgan")
    from healthlens.models import Patient
    app.session_state.workspace.patients.append(Patient(id="HL-2048", name="Alex Morgan", initials="AM"))
    app.session_state.workspace.add(doc, obs, SAMPLE.encode())
    app.session_state.last_import_patient_id = "HL-2048"
    # AppTest does not retain st.switch_page's destination for the next run.
    app.switch_page("app_pages/documents.py").run()
    next(b for b in app.button if b.label == "View imported lab trends").click().run()
    assert not app.exception
    assert app.session_state.patient_id == "HL-2048"
    assert len(app.get("plotly_chart")) == 1
    app.switch_page("app_pages/evidence.py").run()
    assert not app.exception
    assert not any(b.label == "Save review" for b in app.button)
    assert not app.number_input
    assert any("Current status: accepted" in c.value for c in app.caption)
    app.switch_page("app_pages/reports.py").run()
    assert len(app.get("download_button")) == 3


def test_attached_lab_report_is_available_in_all_patient_sections():
    from pathlib import Path
    import pytest
    from healthlens.ingestion import ingest
    from healthlens.models import Patient
    source = Path("docs/Vijay_Jan_2026.pdf")
    if not source.exists():
        pytest.skip("User-provided validation report is not present")
    app = AppTest.from_file("app.py", default_timeout=30).run()
    ws = app.session_state.workspace
    ws.patients.append(Patient(id="P-001", name="Vijay", initials="VK"))
    document, observations = ingest(source.read_bytes(), source.name, "P-001", patient_name="Vijay")
    ws.add(document, observations, source.read_bytes())
    app.session_state.pending_patient_id = "P-001"
    app.run()
    assert not app.exception
    assert len(ws.obs("P-001")) == 29
    for page in ["documents", "trends", "evidence", "timeline", "analysis", "reports"]:
        app.switch_page(f"app_pages/{page}.py").run()
        assert not app.exception, page
        if page == "trends":
            assert len(app.get("plotly_chart")) == 1
        if page == "analysis":
            assert next(b for b in app.button if b.label == "Analysis is up to date").disabled
        if page == "reports":
            assert len(app.get("download_button")) == 3
    assert len(ws.reports[-1]["claims"]) == 29
