# Deployment and current scope

## Local demonstration

Use Python 3.13, install `requirements.txt`, then run `python -m streamlit run app.py` from the repository root. The default URL is http://localhost:8501. `APP_MODE=demo` is the only supported mode.

Use `requirements-dev.txt` for pytest. Core tests do not require network access, production credentials, or Tesseract. OCR is optional and displays an actionable error when unavailable.

## Streamlit Community Cloud

1. Push application files to a repository, excluding `.venv`, secrets, runtime artifacts, and patient data.
2. Select `app.py` as the entry point and Python 3.13.
3. Let Cloud install `requirements.txt`; `packages.txt` requests English Tesseract.
4. Configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` (publishable or legacy anon key) in app secrets and run `docs/supabase.sql` in the Supabase SQL editor. Enable Supabase email/password sign-up and set the Auth Site URL. Login is required for private patient records. Guests can browse bundled dummy data without credentials.
5. Create two test accounts. Confirm each can add patients, see only their own profiles and reports, and cannot access another owner's patient even with the same patient ID. Verify sign-out clears private state, then test upload, analysis, and downloads.

Cloud deployment remains unverified until performed against a real account. Demo sessions are ephemeral. Do not use this deployment for real patient records.

## Docker

`docker compose up --build` binds the application to `127.0.0.1:8501`. The image runs as a non-root user and installs English OCR. Docker configuration is supplied but was not executed during local app verification.

## Troubleshooting

- Module missing: install requirements using the same interpreter that starts Streamlit.
- OCR unavailable: install Tesseract and English language data, then restart your terminal/app.
- No extracted values: use the documented four-column sample format; unsupported layouts remain source text.
- Quarantined document: verify the `Patient:` or `Patient Name:` header matches the selected patient name. A source patient ID is optional.
- Empty analysis: accept imported observations in Evidence & review first.
- Stale report: rerun analysis after corrections/imports.
- Data reset: sessions are temporary; export reports before closing/reloading.
- Port in use: run with `--server.port 8502`.

## Production phases still required

Supabase authentication and patient schema/RLS policies are implemented and require live verification. Private original-file storage, durable checkpoints/workers, real Google OAuth callback and token vault, Pinecone index lifecycle, provider-backed LLM/RAG, process isolation, evaluation thresholds, retention/deletion reconciliation, and live integration verification are not in this release. Refer to the specification rather than treating the visual demo as complete production implementation.


## Existing patient migration

The SQL migration preserves historical profiles with NULL ownership; regular accounts cannot see them. Verify the correct owner for each record before assigning `owner_id` using its `row_id`. Legacy shared Pinecone vectors are not loaded; re-upload the original reports in the verified owner's account. See README.md for full setup.
