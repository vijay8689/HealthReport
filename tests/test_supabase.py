import io
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from healthlens.models import Patient
from healthlens.supabase import PatientSaveError, save_patient
from healthlens.supabase import list_patients


@pytest.mark.parametrize("key,bearer", [("sb_secret_test", False), ("legacy-jwt", True)])
def test_insert_payload_and_auth(key, bearer, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    response = MagicMock()
    response.__enter__.return_value.status = 201
    with patch("healthlens.supabase.urlopen", return_value=response) as post:
        save_patient(Patient(id="P-1", name="Test Patient", initials="TP", age=0),
                     {"SUPABASE_URL": "https://example.supabase.co/rest/v1/", "SUPABASE_KEY": key})
    request = post.call_args.args[0]
    assert request.full_url == "https://example.supabase.co/rest/v1/patients"
    assert request.method == "POST"
    assert b'"age":0' in request.data
    assert request.get_header("Apikey") == key
    assert (request.get_header("Authorization") is not None) == bearer
    assert post.call_args.kwargs["timeout"] == 15


@pytest.mark.parametrize("error,message", [
    (HTTPError("https://example", 409, "conflict", {}, io.BytesIO()), "already exists"),
    (HTTPError("https://example", 403, "forbidden", {}, io.BytesIO()), "rejected access"),
    (URLError("private details"), "Could not confirm"),
    (URLError(PermissionError(13, "private details")), "network access is blocked"),
])
def test_failures_are_safe(error, message, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "sb_secret_test")
    with patch("healthlens.supabase.urlopen", side_effect=error):
        with pytest.raises(PatientSaveError, match=message):
            save_patient(Patient(id="P-1", name="Test", initials="T"))


def test_settings_only_adds_after_confirmed_save():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app.switch_page("app_pages/settings.py").run()
    app.text_input[0].set_value("P-CLOUD")
    app.text_input[1].set_value("Cloud Patient")
    button = next(b for b in app.button if b.label == "Add patient workspace")
    with patch("healthlens.supabase.save_patient", side_effect=PatientSaveError("Save failed")):
        button.click().run()
    assert not app.exception
    assert "P-CLOUD" not in {p.id for p in app.session_state.workspace.patients}
    assert any(e.value == "Save failed" for e in app.error)
    with patch("healthlens.supabase.save_patient") as save:
        next(b for b in app.button if b.label == "Add patient workspace").click().run()
    assert not app.exception
    save.assert_called_once()
    assert app.session_state.patient_id == "P-CLOUD"
    assert any("saved to Supabase" in s.value for s in app.success)


def test_load_patients_paginates_until_empty(monkeypatch):
    import json
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "sb_secret_test")
    responses = []
    for rows in [[Patient(id="C-1", name="Cloud Patient", initials="CP").model_dump()], []]:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(rows).encode()
        responses.append(response)
    with patch("healthlens.supabase.urlopen", side_effect=responses) as get:
        patients = list_patients()
    assert [p.id for p in patients] == ["C-1"]
    assert "offset=1" in get.call_args.args[0].full_url


def test_cloud_profiles_populate_dropdown_and_refresh_without_duplicates(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "sb_secret_test")
    patient = Patient(id="C-1", name="Cloud Patient", initials="CP", age=42)
    with patch("healthlens.supabase.list_patients", return_value=[patient]) as fetch:
        app = AppTest.from_file("app.py", default_timeout=30).run()
        assert not app.exception
        assert "Cloud Patient · C-1" in app.selectbox(key="patient_id").options
        app.selectbox(key="patient_id").select("C-1").run()
        assert fetch.call_count == 1
        assert app.session_state.workspace.patient("C-1").age == 42
        next(b for b in app.button if b.label == "Refresh patients").click().run()
        assert fetch.call_count == 2
        assert [p.id for p in app.session_state.workspace.patients].count("C-1") == 1
    with patch("healthlens.supabase.list_patients", side_effect=PatientSaveError("Connection unavailable")):
        next(b for b in app.button if b.label == "Refresh patients").click().run()
    assert not app.exception
    assert app.session_state.patient_id == "C-1"
    assert any(w.value == "Connection unavailable" for w in app.warning)
