"""Optional account controls at the top right of the public synthetic demo workspace."""
import streamlit as st
from healthlens.auth import AuthError, connection, request_auth, resend_confirmation, sign_in, sign_up, validate_session


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def logout(secrets):
    session = st.session_state.get("auth_session")
    try:
        if session:
            request_auth("logout?scope=local", secrets, {}, session["access_token"])
    except AuthError:
        pass
    finally:
        clear_session()


def require_login(secrets):
    """Return a verified account or None; guests retain access to the synthetic demo."""
    session = st.session_state.get("auth_session")
    if session:
        try:
            session = validate_session(session, secrets)
        except AuthError as exc:
            clear_session()
            st.warning(str(exc))
        else:
            st.session_state.auth_session = session
            return session
    with st.container(key="account_controls"):
        _, login_column, signup_column = st.columns([8, 1.2, 1.2], gap="small")
        with login_column:
            st.button("Login", on_click=lambda: st.session_state.__setitem__("auth_mode", "Sign in"), width="stretch")
        with signup_column:
            st.button("Sign up", on_click=lambda: st.session_state.__setitem__("auth_mode", "Create account"), width="stretch")
    with st.container(key="account_form"):
        mode = st.session_state.get("auth_mode")
        if mode is None:
            return None
        st.subheader("Login" if mode == "Sign in" else "Sign up")
        st.caption("Access your private patient workspace.")
        if mode == "Sign in":
            st.caption("Use the email and password you created with HealthLens Sign up.")
        configured = True
        try:
            connection(secrets)
        except AuthError as exc:
            configured = False
            st.error(str(exc))
        with st.form("authentication", clear_on_submit=True):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirmation = st.text_input("Confirm password", type="password") if mode == "Create account" else None
            submitted = st.form_submit_button("Sign in" if mode == "Sign in" else "Create account", type="primary", disabled=not configured)
        st.button("Back to demo", on_click=lambda: st.session_state.pop("auth_mode", None))
        if submitted:
            if not email.strip() or "@" not in email or not password:
                st.error("Enter your email and password.")
            elif confirmation is not None and (password != confirmation or len(password) < 8):
                st.error("Passwords must match and contain at least 8 characters.")
            else:
                try:
                    with st.spinner("Connecting to your account..."):
                        session = (sign_in if mode == "Sign in" else sign_up)(email, password, secrets)
                except AuthError as exc:
                    st.error(str(exc))
                else:
                    if session:
                        clear_session()
                        st.session_state.auth_session = session
                        st.rerun()
                    else:
                        st.success("Check your email to confirm your account, then log in.")
        with st.expander("Confirmation email missing or expired?"):
            st.caption("Request a fresh link, open the latest confirmation email, then return here to log in.")
            with st.form("resend_confirmation", clear_on_submit=True):
                confirmation_email = st.text_input("Confirmation email")
                resend = st.form_submit_button("Resend confirmation email", disabled=not configured)
            if resend:
                try:
                    with st.spinner("Requesting a new confirmation email..."):
                        resend_confirmation(confirmation_email, secrets)
                except AuthError as exc:
                    st.error(str(exc))
                else:
                    st.success("If this email has a pending signup, a fresh confirmation link has been requested. Use the newest email link, then log in.")
    return None
