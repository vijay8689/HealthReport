import time
from unittest.mock import patch

import pytest

OWNER = "11111111-1111-4111-8111-111111111111"


def auth_session(owner=OWNER):
    return {"access_token": "user-access-token", "refresh_token": "refresh-token",
            "expires_at": time.time() + 3600, "verified_at": time.time(),
            "user": {"id": owner, "email": "owner@example.test"}}


@pytest.fixture
def signed_in_demo():
    """Existing page tests use an authenticated, explicitly seeded synthetic account."""
    import streamlit as st
    from healthlens.workspace import Workspace
    def login(secrets):
        if "auth_session" not in st.session_state:
            st.session_state.auth_session = auth_session()
            st.session_state.workspace_owner_id = OWNER
            st.session_state.workspace = Workspace()
        return st.session_state.auth_session
    def patients(secrets=None, *, session=None):
        return list(st.session_state.workspace.patients)
    with patch("ui.auth.require_login", side_effect=login), patch("healthlens.supabase.list_patients", side_effect=patients):
        yield
