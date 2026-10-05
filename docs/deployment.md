# Deployment and current scope

## Local demonstration

Use Python 3.13, install `requirements.txt`, then run `python -m streamlit run app.py` from the repository root. The default URL is http://localhost:8501. `APP_MODE=demo` is the only supported mode.

Use `requirements-dev.txt` for pytest. Core tests do not require network access, production credentials, or Tesseract. OCR is optional and displays an actionable error when unavailable.

## Streamlit Community Cloud

1. Push application files to a repository, excluding `.venv`, secrets, runtime artifacts, and patient data.
2. Select `app.py` as the entry point and Python 3.13.
3. Let Cloud install `requirements.txt`; `packages.txt` requests English Tesseract.
4. To add patient workspaces, configure `SUPABASE_URL` and `SUPABASE_KEY` in app secrets and run `docs/supabase.sql` in the Supabase SQL editor. Existing demo pages work without credentials.
5. Verify overview, patient switching, sample import/review, analysis, and PDF download.

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

Application authentication, Supabase schema/RLS and private storage, durable checkpoints/workers, real Google OAuth callback and token vault, Pinecone index lifecycle, provider-backed LLM/RAG, process isolation, evaluation thresholds, retention/deletion reconciliation, and live integration verification are not in this release. Refer to the specification rather than treating the visual demo as complete production implementation.

