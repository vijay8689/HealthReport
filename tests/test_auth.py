import json
import time
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest
from streamlit.testing.v1 import AppTest

from conftest import OWNER, auth_session
from healthlens.auth import AuthError, connection, sign_in, sign_up, validate_session
from healthlens.models import Document, Patient
from healthlens.supabase import PatientSaveError, list_patients, require_patient_access, save_patient
from healthlens.pinecone_db import PineconeConnectionError, index_document, load_patient_records, patient_namespace
from healthlens.workspace import Workspace

OTHER = "22222222-2222-4222-8222-222222222222"


@pytest.fixture(autouse=True)
def configured_auth(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "sb_publishable_test")
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.delenv("PINECONE_INDEX_NAME", raising=False)


def response(payload):
    result = MagicMock()
    result.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    result.__enter__.return_value.status = 201
    return result


def logged_in_app(owner=OWNER):
    app = AppTest.from_file("app.py", default_timeout=30)
    app.session_state.auth_session = auth_session(owner)
    return app


def test_password_sign_in_verifies_user_with_provider():
    payload = {"access_token": "access", "refresh_token": "refresh", "expires_in": 3600,
               "user": {"id": OTHER}}
    with patch("healthlens.auth.urlopen", side_effect=[response(payload), response({"id": OWNER, "email": "user@example.test"})]) as calls:
        session = sign_in(" user@example.test ", "password")
    assert session["user"]["id"] == OWNER
    assert calls.call_args_list[0].args[0].full_url.endswith("/token?grant_type=password")
    assert json.loads(calls.call_args_list[0].args[0].data)["email"] == "user@example.test"
    assert calls.call_args_list[1].args[0].get_header("Authorization") == "Bearer access"


def test_signup_waits_for_email_confirmation_without_session():
    with patch("healthlens.auth.urlopen", return_value=response({"user": {"id": OWNER}})):
        assert sign_up("user@example.test", "password") is None


def test_provider_errors_never_display_password_or_provider_body():
    with patch("healthlens.auth.urlopen", side_effect=HTTPError("https://example", 400, "private secret", {}, None)):
        with pytest.raises(AuthError, match="Authentication was rejected") as error:
            sign_in("user@example.test", "secret-password")
    assert "private secret" not in str(error.value)
    assert "secret-password" not in str(error.value)


def test_refresh_rotates_tokens_and_checks_identity():
    session = auth_session()
    session["expires_at"] = time.time() - 1
    payload = {"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 3600}
    with patch("healthlens.auth.request_auth", side_effect=[payload, {"id": OWNER}]) as calls:
        renewed = validate_session(session)
    assert renewed["access_token"] == "new-access"
    assert renewed["refresh_token"] == "new-refresh"
    assert calls.call_args_list[0].args[0] == "token?grant_type=refresh_token"
    with patch("healthlens.auth.request_auth", side_effect=[payload, {"id": OTHER}]):
        with pytest.raises(AuthError, match="account changed"):
            validate_session(session)


def test_old_session_revalidates_user():
    session = auth_session()
    session["verified_at"] = 0
    with patch("healthlens.auth.request_auth", return_value={"id": OTHER}):
        with pytest.raises(AuthError, match="account changed"):
            validate_session(session)


@pytest.mark.parametrize("key", ["sb_secret_private", "not-a-jwt"])
def test_auth_rejects_server_role_keys(monkeypatch, key):
    monkeypatch.setenv("SUPABASE_ANON_KEY", key)
    with pytest.raises(AuthError, match="publishable or legacy anon"):
        connection()


@pytest.mark.parametrize("operation", [lambda: list_patients(),
    lambda: save_patient(Patient(id="P-1", name="Test", initials="T")),
    lambda: require_patient_access("P-1")])
def test_patient_api_requires_login_before_any_network_access(operation):
    with patch("healthlens.supabase.urlopen") as request:
        with pytest.raises(PatientSaveError, match="sign in"):
            operation()
    request.assert_not_called()


def test_patient_list_sends_user_jwt_and_owner_filter():
    with patch("healthlens.supabase.urlopen", return_value=response([])) as call:
        assert list_patients(session=auth_session()) == []
    request = call.call_args.args[0]
    assert "owner_id=eq." + OWNER in request.full_url
    assert request.get_header("Authorization") == "Bearer user-access-token"
    assert request.get_header("Apikey") == "sb_publishable_test"


def test_patient_insert_assigns_logged_in_owner():
    with patch("healthlens.supabase.urlopen", return_value=response({})) as call:
        save_patient(Patient(id="P-1", name="Test", initials="T"), session=auth_session(OTHER))
    assert json.loads(call.call_args.args[0].data)["owner_id"] == OTHER


def test_ownership_denial_blocks_pinecone_reads_and_writes():
    doc = Document(patient_id="P-OTHER", name="report.txt", hash="hash", pages=[{"text": "Evidence", "locator": "Page 1"}])
    with patch("healthlens.supabase.urlopen", return_value=response([])), patch("healthlens.pinecone_db.check_connection") as pinecone:
        with pytest.raises(PineconeConnectionError, match="not available in your account"):
            load_patient_records("P-OTHER", session=auth_session())
        with pytest.raises(PineconeConnectionError, match="not available in your account"):
            index_document(doc, session=auth_session())
    pinecone.assert_not_called()


def test_report_namespaces_isolate_same_patient_id_and_avoid_delimiter_collisions():
    assert patient_namespace(OWNER, "P-1") != patient_namespace(OTHER, "P-1")
    assert patient_namespace(OWNER, "P-1") != patient_namespace(OWNER, "P-2")
    assert patient_namespace(OWNER, "P-1") != "patient-P-1"


def test_loader_rejects_other_owner_metadata():
    records = {"vectors": {"v1": {"metadata": {"patient_id": "P-1", "owner_id": OTHER}}}}
    info = {"host": "test.svc.pinecone.io", "field_map": {"text": "chunk_text"}}
    with patch("healthlens.pinecone_db.require_patient_access"), patch("healthlens.pinecone_db.check_connection", return_value=info), patch("healthlens.pinecone_db.urlopen", side_effect=[response({"vectors": [{"id": "v1"}]}), response(records)]):
        with pytest.raises(PineconeConnectionError, match="metadata does not match"):
            load_patient_records("P-1", session=auth_session())


def test_anonymous_ui_shows_dummy_data_without_loading_private_records():
    with patch("healthlens.supabase.list_patients") as patients, patch("healthlens.pinecone_db.load_patient_records") as records:
        app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    assert not app.text_input
    assert [p.id for p in app.session_state.workspace.patients] == ["DUMMY-0001"]
    assert len(app.session_state.workspace.docs("DUMMY-0001")) == 3
    assert any(b.label == "Login" for b in app.button)
    assert any(b.label == "Sign up" for b in app.button)
    patients.assert_not_called()
    records.assert_not_called()


def test_sign_in_ui_opens_empty_private_workspace():
    with patch("ui.auth.sign_in", return_value=auth_session()), patch("healthlens.supabase.list_patients", return_value=[]):
        app = AppTest.from_file("app.py", default_timeout=30).run()
        next(b for b in app.button if b.label == "Login").click().run()
        app.text_input[0].set_value("user@example.test")
        app.text_input[1].set_value("password")
        next(b for b in app.button if b.label == "Sign in").click().run()
    assert not app.exception
    assert app.session_state.workspace.patients == []
    assert app.session_state.workspace.documents == []
    assert any(b.label == "Add patient workspace" for b in app.button)


def test_signup_ui_confirms_email_and_rejects_mismatched_passwords():
    with patch("ui.auth.sign_up", return_value=None) as signup:
        app = AppTest.from_file("app.py", default_timeout=30).run()
        next(b for b in app.button if b.label == "Sign up").click().run()
        app.text_input[0].set_value("user@example.test")
        app.text_input[1].set_value("password1")
        app.text_input[2].set_value("password2")
        next(b for b in app.button if b.label == "Create account").click().run()
        signup.assert_not_called()
        assert any("Passwords must match" in e.value for e in app.error)
        app.text_input[0].set_value("user@example.test")
        app.text_input[1].set_value("password1")
        app.text_input[2].set_value("password1")
        next(b for b in app.button if b.label == "Create account").click().run()
    assert not app.exception
    assert any("Check your email" in s.value for s in app.success)
    assert [p.id for p in app.session_state.workspace.patients] == ["DUMMY-0001"]


def test_new_account_can_add_first_patient_without_demo_data():
    patient = Patient(id="P-NEW", name="New Patient", initials="NP", age=30, sex="Female", description="Cloud patient workspace")
    with patch("healthlens.supabase.list_patients", side_effect=[[], [patient]]), patch("ui.patient_form.save_patient") as save:
        app = logged_in_app().run()
        app.text_input[0].set_value(patient.id)
        app.text_input[1].set_value(patient.name)
        next(b for b in app.button if b.label == "Add patient workspace").click().run()
    assert not app.exception
    assert [p.id for p in app.session_state.workspace.patients] == ["P-NEW"]
    assert app.session_state.patient_id == "P-NEW"
    assert save.call_args.kwargs["session"]["user"]["id"] == OWNER


def test_switching_accounts_clears_patient_documents_and_widget_values():
    app = logged_in_app(OTHER)
    app.session_state.workspace_owner_id = OWNER
    app.session_state.workspace = Workspace()
    app.session_state.patient_id = "DUMMY-0001"
    app.session_state.original_upload = b"private old evidence"
    app.session_state.old_patient_filter = "Private patient name"
    with patch("healthlens.supabase.list_patients", return_value=[]):
        app.run()
    assert not app.exception
    assert app.session_state.workspace_owner_id == OTHER
    assert not app.session_state.workspace.documents
    assert not app.session_state.workspace.patients
    assert "original_upload" not in app.session_state
    assert "old_patient_filter" not in app.session_state


def test_signout_clears_private_state_even_when_provider_is_unreachable():
    with patch("healthlens.supabase.list_patients", return_value=[]):
        app = logged_in_app().run()
    app.session_state.workspace.originals["private"] = b"private report"
    app.session_state.pinecone_patient_errors = {"private": "error"}
    with patch("ui.auth.request_auth", side_effect=AuthError("Unavailable")):
        next(b for b in app.button if b.label == "Sign out").click().run()
    assert not app.exception
    assert "auth_session" not in app.session_state
    assert [p.id for p in app.session_state.workspace.patients] == ["DUMMY-0001"]
    assert "pinecone_patient_errors" not in app.session_state
    assert "private" not in app.session_state.workspace.originals
    assert any(b.label == "Login" for b in app.button)


def test_invalid_session_clears_private_data_and_returns_to_demo():
    app = logged_in_app()
    app.session_state.workspace = Workspace()
    with patch("ui.auth.validate_session", side_effect=AuthError("Session expired")), patch("healthlens.supabase.list_patients") as load:
        app.run()
    assert not app.exception
    assert [p.id for p in app.session_state.workspace.patients] == ["DUMMY-0001"]
    assert "auth_session" not in app.session_state
    load.assert_not_called()


@pytest.mark.parametrize("role,allowed", [("anon", True), ("service_role", False)])
def test_legacy_key_role_must_be_anon(monkeypatch, role, allowed):
    import base64
    payload = base64.urlsafe_b64encode(json.dumps({"role": role}).encode()).decode().rstrip("=")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "header." + payload + ".signature")
    if allowed:
        assert connection()[1].endswith(".signature")
    else:
        with pytest.raises(AuthError, match="not a service-role key"):
            connection()


def test_guest_navigation_never_reads_or_writes_cloud_even_when_configured(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "configured-key")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "healthlens")
    with patch("healthlens.supabase.list_patients") as patients, patch("healthlens.supabase.save_patient") as save, patch("healthlens.pinecone_db.load_patient_records") as records, patch("healthlens.pinecone_db.check_connection") as check, patch("healthlens.pinecone_db.index_document") as index:
        app = AppTest.from_file("app.py", default_timeout=30).run()
        for page in ["documents", "discharge", "trends", "analysis", "evidence", "timeline", "reports", "connections", "settings"]:
            app.switch_page(f"app_pages/{page}.py").run()
            assert not app.exception, page
        assert not any(b.label == "Add patient workspace" for b in app.button)
        app.switch_page("app_pages/documents.py").run()
        button = next(b for b in app.button if b.label == "Sync documents to Pinecone")
        button.click().run()
        assert not app.exception
        assert [p.id for p in app.session_state.workspace.patients] == ["DUMMY-0001"]
    patients.assert_not_called()
    save.assert_not_called()
    records.assert_not_called()
    check.assert_not_called()
    index.assert_not_called()


def test_guest_can_close_login_and_continue_demo():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    next(b for b in app.button if b.label == "Login").click().run()
    assert [t.label for t in app.text_input if t.label != "Confirmation email"] == ["Email", "Password"]
    next(b for b in app.button if b.label == "Back to demo").click().run()
    assert not app.exception
    assert not app.text_input
    assert app.session_state.patient_id == "DUMMY-0001"


def test_guest_demo_works_without_auth_configuration():
    with patch("ui.auth.connection", side_effect=AuthError("Configure Supabase")) as config:
        app = AppTest.from_file("app.py", default_timeout=30).run()
        assert not app.exception
        assert not app.error
        config.assert_not_called()
        next(b for b in app.button if b.label == "Login").click().run()
        assert not app.exception
        assert any(e.value == "Configure Supabase" for e in app.error)
        assert next(b for b in app.button if b.label == "Sign in").disabled
        assert app.session_state.patient_id == "DUMMY-0001"


def test_account_buttons_are_in_main_header_and_forms_hidden_on_launch():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    assert not app.text_input
    assert not any(b.label in {"Login", "Sign up", "Sign in", "Create account"} for b in app.sidebar.button)
    assert {"Login", "Sign up"}.issubset({b.label for b in app.main.button})
    assert not any(b.label in {"Sign in", "Create account"} for b in app.main.button)
    assert app.session_state.patient_id == "DUMMY-0001"
    next(b for b in app.button if b.label == "Sign up").click().run()
    assert not app.exception
    assert [t.label for t in app.text_input if t.label != "Confirmation email"] == ["Email", "Password", "Confirm password"]
    assert not app.sidebar.text_input


@pytest.mark.parametrize("code,guidance", [
    ("invalid_credentials", "Email or password is incorrect"),
    ("email_not_confirmed", "Your email is not confirmed"),
    ("signup_disabled", "registration is disabled"),
    ("email_provider_disabled", "login is disabled"),
    ("over_email_send_rate_limit", "Too many emails"),
    ("bad_jwt", "session is invalid or expired"),
    ("weak_password", "stronger password"),
])
def test_provider_error_codes_show_specific_safe_guidance(code, guidance):
    import io
    error = HTTPError("https://example", 400, "private provider details", {},
                      io.BytesIO(json.dumps({"error_code": code, "msg": "private password or token"}).encode()))
    with patch("healthlens.auth.urlopen", side_effect=error):
        with pytest.raises(AuthError, match=guidance) as raised:
            sign_in("user@example.test", "private-password")
    assert "private password or token" not in str(raised.value)
    assert "private-password" not in str(raised.value)


def test_wrong_project_api_key_is_not_reported_as_bad_password():
    import io
    error = HTTPError("https://example", 401, "Unauthorized", {}, io.BytesIO(b'{"message":"Invalid API key"}'))
    with patch("healthlens.auth.urlopen", side_effect=error):
        with pytest.raises(AuthError, match="API key was rejected"):
            sign_in("user@example.test", "password")


def test_unknown_provider_body_remains_private():
    import io
    error = HTTPError("https://example", 400, "private provider details", {},
                      io.BytesIO(b'{"error_code":"unknown","msg":"secret-password"}'))
    with patch("healthlens.auth.urlopen", side_effect=error):
        with pytest.raises(AuthError, match="Authentication was rejected") as raised:
            sign_in("user@example.test", "secret-password")
    assert "secret-password" not in str(raised.value)


def test_login_failure_keeps_guest_demo_and_shows_specific_reason():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    next(b for b in app.button if b.label == "Login").click().run()
    app.text_input[0].set_value("user@example.test")
    app.text_input[1].set_value("password")
    with patch("ui.auth.sign_in", side_effect=AuthError("Email or password is incorrect.")):
        next(b for b in app.button if b.label == "Sign in").click().run()
    assert not app.exception
    assert any(e.value == "Email or password is incorrect." for e in app.error)
    assert "auth_session" not in app.session_state
    assert app.session_state.patient_id == "DUMMY-0001"


@pytest.mark.parametrize("app_url", ["http://localhost:8501", "https://health.example.com"])
def test_signup_confirmation_uses_configured_app_redirect(monkeypatch, app_url):
    from urllib.parse import parse_qs, urlsplit
    monkeypatch.setenv("APP_URL", app_url)
    with patch("healthlens.auth.urlopen", return_value=response({"user": {"id": OWNER}})) as call:
        assert sign_up("user@example.test", "password") is None
    request = call.call_args.args[0]
    assert urlsplit(request.full_url).path.endswith("/signup")
    assert parse_qs(urlsplit(request.full_url).query)["redirect_to"] == [app_url]


def test_resend_uses_signup_endpoint_and_app_redirect(monkeypatch):
    from urllib.parse import parse_qs, urlsplit
    from healthlens.auth import resend_confirmation
    monkeypatch.setenv("APP_URL", "http://localhost:8501")
    with patch("healthlens.auth.urlopen", return_value=response({})) as call:
        resend_confirmation(" user@example.test ")
    request = call.call_args.args[0]
    assert urlsplit(request.full_url).path.endswith("/resend")
    assert parse_qs(urlsplit(request.full_url).query)["redirect_to"] == ["http://localhost:8501"]
    assert json.loads(request.data) == {"type": "signup", "email": "user@example.test"}


@pytest.mark.parametrize("url", ["http://unsafe.example.com", "https://user:password@example.com", "javascript:alert(1)", "https://example.com/#secret"])
def test_confirmation_rejects_invalid_redirect_before_any_email_request(monkeypatch, url):
    from healthlens.auth import resend_confirmation
    monkeypatch.setenv("APP_URL", url)
    with patch("healthlens.auth.urlopen") as call:
        with pytest.raises(AuthError, match="APP_URL"):
            resend_confirmation("user@example.test")
    call.assert_not_called()


def test_resend_ui_only_sends_after_user_submits_email():
    with patch("ui.auth.resend_confirmation") as resend:
        app = AppTest.from_file("app.py", default_timeout=30).run()
        next(b for b in app.button if b.label == "Login").click().run()
        resend.assert_not_called()
        next(t for t in app.text_input if t.label == "Confirmation email").set_value("user@example.test")
        next(b for b in app.button if b.label == "Resend confirmation email").click().run()
    assert not app.exception
    assert resend.call_args.args[0] == "user@example.test"
    assert any("fresh confirmation link" in s.value for s in app.success)
    assert "auth_session" not in app.session_state
    assert app.session_state.patient_id == "DUMMY-0001"


def test_resend_ui_handles_provider_rate_limit():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    next(b for b in app.button if b.label == "Login").click().run()
    next(t for t in app.text_input if t.label == "Confirmation email").set_value("user@example.test")
    with patch("ui.auth.resend_confirmation", side_effect=AuthError("Too many emails have been requested.")):
        next(b for b in app.button if b.label == "Resend confirmation email").click().run()
    assert not app.exception
    assert any("Too many emails" in e.value for e in app.error)


def test_signin_with_older_workspace_without_empty_method(monkeypatch):
    monkeypatch.delattr(Workspace, "empty")
    with patch("healthlens.supabase.list_patients", return_value=[]):
        app = logged_in_app().run()
    assert not app.exception
    workspace = app.session_state.workspace
    assert workspace.patients == []
    assert workspace.documents == []
    assert workspace.observations == []
    assert workspace.revisions == []
    assert workspace.reports == []
    assert workspace.originals == {}
    assert workspace.discharge_summaries == []
    assert any(b.label == "Add patient workspace" for b in app.button)


def test_clear_private_workspace_with_older_workspace_without_empty_method(monkeypatch):
    monkeypatch.delattr(Workspace, "empty")
    patient = Patient(id="P-1", name="Private Patient", initials="PP")
    with patch("healthlens.supabase.list_patients", return_value=[patient]):
        app = logged_in_app().run()
        app.session_state.workspace.originals["old-report"] = b"private report"
        app.switch_page("app_pages/settings.py").run()
        next(c for c in app.checkbox if c.label.startswith("Remove your session imports")).check().run()
        next(b for b in app.button if b.label == "Clear session data").click().run()
    assert not app.exception
    workspace = app.session_state.workspace
    assert [p.id for p in workspace.patients] == ["P-1"]
    assert not workspace.documents
    assert not workspace.originals
    assert not workspace.reports
