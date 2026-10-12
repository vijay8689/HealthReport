"""User-scoped patient access through Supabase REST and row-level security."""
import json
import errno
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from healthlens.models import Patient
from healthlens.auth import AuthError, connection, user_id


class PatientSaveError(Exception):
    """A safe, user-facing cloud save failure."""


def _connection(secrets=None, session=None):
    try:
        user_id(session)
        url, key = connection(secrets)
    except AuthError as exc:
        raise PatientSaveError(str(exc)) from None
    return url + "/rest/v1", {"apikey": key, "Authorization": "Bearer " + session["access_token"],
                             "Content-Type": "application/json", "Prefer": "return=minimal"}


def list_patients(secrets=None, *, session=None) -> list[Patient]:
    """Fetch only the signed-in owner's profiles. RLS also enforces this scope."""
    endpoint, headers = _connection(secrets, session)
    owner_filter = urlencode({"owner_id": "eq." + user_id(session)})
    patients = []
    offset = 0
    try:
        while True:
            request = Request(endpoint + f"/patients?select=id,name,initials,age,sex,description&{owner_filter}&order=id.asc&limit=500&offset={offset}", headers=headers)
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
            message = "Supabase rejected access while loading patients. Check your login and run docs/supabase.sql to enable ownership policies."
        else:
            message = f"Could not load Supabase patients (HTTP {exc.code})."
        raise PatientSaveError(message) from None
    except (URLError, TimeoutError, OSError):
        raise PatientSaveError("Could not load Supabase patients. Check the app's network access and connection. Existing workspace patients remain available.") from None
    except (ValueError, TypeError):
        raise PatientSaveError("Supabase returned invalid patient details. Check the patients table schema.") from None


def save_patient(patient: Patient, secrets=None, *, session=None):
    """Insert once; never overwrite an existing patient with the same ID."""
    endpoint, headers = _connection(secrets, session)
    request = Request(endpoint + "/patients", data=json.dumps({**patient.model_dump(), "owner_id": user_id(session)}).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            if response.status not in (200, 201, 204):
                raise PatientSaveError("Supabase did not confirm the save. Check the database before retrying.")
    except HTTPError as exc:
        if exc.code == 409:
            message = "That patient ID already exists in your workspace. Use a different Patient ID."
        elif exc.code in (401, 403):
            message = "Supabase rejected access. Check your login and run docs/supabase.sql to enable ownership policies."
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


def require_patient_access(patient_id, secrets=None, *, session=None):
    """Authorize the patient via the user's JWT before accessing server-key services."""
    endpoint, headers = _connection(secrets, session)
    query = urlencode({"select": "id", "id": "eq." + patient_id,
                       "owner_id": "eq." + user_id(session), "limit": 1})
    try:
        with urlopen(Request(endpoint + "/patients?" + query, headers=headers), timeout=15) as response:
            rows = json.loads(response.read())
        if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("id") != patient_id:
            raise PatientSaveError("This patient is not available in your account.")
    except (HTTPError, URLError, OSError, ValueError, TypeError, AttributeError):
        raise PatientSaveError("Could not verify access to this patient. Sign in again or retry later.") from None
