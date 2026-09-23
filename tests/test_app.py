from streamlit.testing.v1 import AppTest


def seed_app(app):
    from healthlens.demo import SAMPLE
    from healthlens.ingestion import ingest
    from healthlens.models import Patient
    doc, observations = ingest(SAMPLE.encode(), "sample.txt", "HL-2048")
    for observation in observations:
        observation.status = "accepted"
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
    next(b for b in app.button if b.label == "Run analysis").click().run()
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


def test_upload_shortcut_and_review_handoff():
    from healthlens.demo import SAMPLE
    from healthlens.ingestion import ingest
    app = AppTest.from_file("app.py", default_timeout=30).run()
    next(b for b in app.button if b.label == "Upload report").click().run()
    assert not app.exception
    assert app.session_state.document_view == "Upload reports"
    doc, obs = ingest(SAMPLE.encode(), "sample.txt", "DUMMY-0001", use_source_patient=True)
    from healthlens.models import Patient
    app.session_state.workspace.patients.append(Patient(id="HL-2048", name="Alex Morgan", initials="AM"))
    app.session_state.workspace.add(doc, obs, SAMPLE.encode())
    app.session_state.last_import_patient_id = "HL-2048"
    # AppTest does not retain st.switch_page's destination for the next run.
    app.switch_page("app_pages/documents.py").run()
    next(b for b in app.button if b.label == "Review extracted observations").click().run()
    assert not app.exception
    assert app.session_state["review_filter_HL-2048"] == "Needs review"
    assert any("Current status: needs review" in c.value for c in app.caption)
