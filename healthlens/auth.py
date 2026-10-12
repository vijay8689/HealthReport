"""Supabase authentication. Credentials and tokens stay in the server session."""
import base64
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from uuid import UUID


class AuthError(Exception):
    """Safe authentication failure for display."""


def connection(secrets=None):
    secrets = secrets or {}
    url = str(os.getenv("SUPABASE_URL") or secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
    key = str(os.getenv("SUPABASE_ANON_KEY") or secrets.get("SUPABASE_ANON_KEY")
              or os.getenv("SUPABASE_KEY") or secrets.get("SUPABASE_KEY", "")).strip()
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/rest/v1"):
        raise AuthError("Configure SUPABASE_URL with your HTTPS Supabase project URL.")
    if not key:
        raise AuthError("Configure SUPABASE_ANON_KEY with your Supabase publishable or legacy anon key.")
    if not key.startswith("sb_publishable_"):
        try:
            payload = json.loads(base64.urlsafe_b64decode(key.split(".")[1] + "=="))
            if payload.get("role") != "anon":
                raise ValueError()
        except (ValueError, IndexError, TypeError):
            raise AuthError("Login requires a Supabase publishable or legacy anon key, not a service-role key.") from None
    return url.removesuffix("/rest/v1"), key


def request_auth(path, secrets=None, payload=None, token=None):
    url, key = connection(secrets)
    headers = {"apikey": key, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url + "/auth/v1/" + path, headers=headers,
                      data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read()
            result = json.loads(body) if body else {}
            if not isinstance(result, dict):
                raise ValueError()
            return result
    except HTTPError as exc:
        # Map provider codes to fixed guidance; never display raw provider bodies.
        try:
            error = json.loads(exc.read(16384))
            error = error if isinstance(error, dict) else {}
        except (ValueError, OSError, AttributeError):
            error = {}
        messages = {
            "invalid_credentials": "Email or password is incorrect. Use the credentials you created with HealthLens Sign up.",
            "otp_expired": "This confirmation link is invalid or expired. Request a new confirmation email and use its latest link.",
            "email_not_confirmed": "Your email is not confirmed. Open the Supabase confirmation email and click its link before signing in.",
            "signup_disabled": "New account registration is disabled in Supabase. Ask the app administrator to enable sign-up.",
            "email_provider_disabled": "Email and password login is disabled in Supabase. Ask the app administrator to enable it.",
            "user_banned": "This account is disabled. Contact the app administrator.",
            "weak_password": "Choose a stronger password that meets the Supabase project's password requirements.",
            "email_address_invalid": "Enter a valid email address.",
            "over_email_send_rate_limit": "Too many emails have been requested. Wait a few minutes before trying again.",
            "over_request_rate_limit": "Too many authentication attempts. Please try again later.",
            "bad_jwt": "Your session is invalid or expired. Please log in again.",
            "session_not_found": "Your session is no longer available. Please log in again.",
            "refresh_token_not_found": "Your session has expired. Please log in again.",
            "refresh_token_already_used": "Your session has expired. Please log in again.",
        }
        code = error.get("error_code") or error.get("code")
        if isinstance(code, str) and code in messages:
            message = messages[code]
        elif error.get("message") == "Invalid API key":
            message = "The Supabase API key was rejected. Configure the publishable or anon key from the same project as SUPABASE_URL."
        elif exc.code in (400, 401, 403, 422):
            message = "Authentication was rejected. Check your email, password, and email confirmation."
        elif exc.code == 429:
            message = "Too many authentication attempts. Please try again later."
        else:
            message = "Authentication is unavailable. Please try again later."
        raise AuthError(message) from None
    except (URLError, OSError, ValueError):
        raise AuthError("Could not reach the authentication service. Please try again.") from None


def user_id(session):
    try:
        if not session["access_token"] or session["expires_at"] <= time.time():
            raise ValueError()
        return str(UUID(session["user"]["id"]))
    except (KeyError, TypeError, ValueError, AttributeError):
        raise AuthError("Please sign in to access patient records.") from None


def verified_session(payload, secrets=None):
    try:
        token = payload["access_token"]
        user = request_auth("user", secrets, token=token)
        result = {"access_token": token, "refresh_token": payload["refresh_token"],
                  "expires_at": time.time() + int(payload["expires_in"]),
                  "user": user, "verified_at": time.time()}
        user_id(result)
        return result
    except (KeyError, TypeError, ValueError):
        raise AuthError("Authentication returned an invalid session. Please sign in again.") from None


def sign_in(email, password, secrets=None):
    return verified_session(request_auth("token?grant_type=password", secrets,
                            {"email": email.strip(), "password": password}), secrets)


def confirmation_redirect(secrets=None):
    secrets = secrets or {}
    url = str(os.getenv("APP_URL") or secrets.get("APP_URL") or "http://localhost:8501").strip().rstrip("/")
    parsed = urlsplit(url)
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AuthError("APP_URL must be the app's public URL without credentials, query parameters, or fragments.")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
        raise AuthError("APP_URL must use HTTPS, or HTTP for localhost development.")
    return url


def sign_up(email, password, secrets=None):
    path = "signup?" + urlencode({"redirect_to": confirmation_redirect(secrets)})
    payload = request_auth(path, secrets, {"email": email.strip(), "password": password})
    return verified_session(payload, secrets) if payload.get("access_token") else None


def resend_confirmation(email, secrets=None):
    if "@" not in email.strip():
        raise AuthError("Enter the email address you used to sign up.")
    path = "resend?" + urlencode({"redirect_to": confirmation_redirect(secrets)})
    request_auth(path, secrets, {"type": "signup", "email": email.strip()})


def validate_session(session, secrets=None):
    if session.get("expires_at", 0) <= time.time() + 60:
        refreshed = verified_session(request_auth("token?grant_type=refresh_token", secrets,
                                    {"refresh_token": session.get("refresh_token", "")}), secrets)
        if refreshed["user"]["id"] != session["user"]["id"]:
            raise AuthError("Your account changed. Please sign in again.")
        return refreshed
    user_id(session)
    if time.time() - session.get("verified_at", 0) >= 60:
        user = request_auth("user", secrets, token=session["access_token"])
        if user.get("id") != session["user"]["id"]:
            raise AuthError("Your account changed. Please sign in again.")
        session = {**session, "user": user, "verified_at": time.time()}
    return session
