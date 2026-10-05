"""Server-side patient inserts through the Supabase REST API."""
import os
import json
import errno
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from healthlens.models import Patient


class PatientSaveError(Exception):
    """A safe, user-facing cloud save failure."""


def _connection(secrets=None):
    secrets = secrets or {}
    url = str(os.environ.get("SUPABASE_URL") or secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
    key = str(os.environ.get("SUPABASE_KEY") or secrets.get("SUPABASE_KEY", "")).strip()
    if not url or not key:
        raise PatientSaveError("Configure SUPABASE_URL and SUPABASE_KEY in server environment variables or Streamlit secrets before adding patients.")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/rest/v1"):
        raise PatientSaveError("SUPABASE_URL must be your HTTPS project URL or REST API URL.")
    endpoint = url if parsed.path == "/rest/v1" else url + "/rest/v1"
    headers = {"apikey": key, "Content-Type": "application/json", "Prefer": "return=minimal"}
    # Legacy JWT keys need Bearer auth; sb_secret_/sb_publishable_ keys do not.
    if not key.startswith("sb_"):
        headers["Authorization"] = f"Bearer {key}"
    return endpoint, headers


def list_patients(secrets=None) -> list[Patient]:
    """Fetch all profiles in stable pages without caching across user sessions."""
    endpoint, headers = _connection(secrets)
    patients = []
    offset = 0
    try:
        while True:
            request = Request(endpoint + f"/patients?select=id,name,initials,age,sex,description&order=id.asc&limit=500&offset={offset}", headers=headers)
            with urlopen(request, timeout=15) as response:
                rows = json.loads(response.read())
            if not isinstance(rows, list):
                raise ValueError("Invalid patients response")
            patients.extend(Patient.model_validate(row) for row in rows)
            if not rows:
                return patients
            offset += len(rows)
    except HTTPError as exc:
        if exc.code == 404:
            message = "Supabase patients table was not found. Run docs/supabase.sql in the Supabase SQL editor."
        elif exc.code in (401, 403):
            message = "Supabase rejected access while loading patients. Check your server key and table SELECT permissions."
        else:
            message = f"Could not load Supabase patients (HTTP {exc.code})."
        raise PatientSaveError(message) from None
    except (URLError, TimeoutError, OSError):
        raise PatientSaveError("Could not load Supabase patients. Check the app's network access and connection. Existing workspace patients remain available.") from None
    except (ValueError, TypeError):
        raise PatientSaveError("Supabase returned invalid patient details. Check the patients table schema.") from None


def save_patient(patient: Patient, secrets=None):
    """Insert once; never overwrite an existing patient with the same ID."""
    endpoint, headers = _connection(secrets)
    request = Request(endpoint + "/patients", data=patient.model_dump_json().encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            if response.status not in (200, 201, 204):
                raise PatientSaveError("Supabase did not confirm the save. Check the database before retrying.")
    except HTTPError as exc:
        if exc.code == 409:
            message = "That patient ID already exists in Supabase. Use a different Patient ID."
        elif exc.code in (401, 403):
            message = "Supabase rejected access. Check the server API key and patients table permissions."
        elif exc.code == 404:
            message = "Supabase patients table was not found. Run docs/supabase.sql in the Supabase SQL editor."
        else:
            message = f"Supabase could not save the patient (HTTP {exc.code}). Check the table schema and server configuration."
        raise PatientSaveError(message) from None
    except (URLError, TimeoutError, OSError) as exc:
        reason = exc.reason if isinstance(exc, URLError) else exc
        if isinstance(reason, PermissionError) or getattr(reason, "errno", None) in (errno.EACCES, errno.EPERM):
            message = "The app's network access is blocked. Restart Streamlit outside the restricted sandbox to connect to Supabase."
        elif isinstance(reason, ssl.SSLError):
            message = "The secure connection to Supabase failed. Check the server's TLS certificates and proxy configuration."
        elif isinstance(reason, socket.gaierror):
            message = "The Supabase hostname could not be resolved. Check SUPABASE_URL and the server's internet connection."
        else:
            message = "Could not confirm the Supabase save. Check your connection and the database before retrying."
        raise PatientSaveError(message) from None
