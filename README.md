# HealthLens AI

An animated Streamlit workspace for exploring clinical documents, laboratory trends, evidence, and orchestrated summaries. Midnight-blue navigation, mint accents, a floating orbital hero, responsive cards, and reduced-motion support.

**This release is a working demo/MVP, not the entire connected production system described in the specification.** It makes no external AI calls. Adding patient workspaces requires Supabase configuration. It does not provide diagnosis, treatment recommendations, or clinical risk predictions.

## Save new patient profiles to Supabase

1. Run [docs/supabase.sql](docs/supabase.sql) in your project's Supabase SQL editor.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `SUPABASE_URL` and `SUPABASE_KEY`. Use a server-only `sb_secret_...` key or legacy `service_role` key. Environment variables with these names also work and take precedence. On Streamlit Cloud, set these values in app secrets. Never commit the real key.
3. Open **Settings**, enter patient details, and click **Add patient workspace**. The profile is inserted into `public.patients` through the Supabase REST API before the workspace is added. Failed saves leave the form available for correction; duplicate IDs never overwrite existing patients.

Patient profiles persist in Supabase and load into the active patient dropdown on app startup. The list refreshes on interactions after 60 seconds; **Refresh patients** fetches immediately. Cloud and session profiles are merged by patient ID. This flow does not create authentication users. Documents, reports, and extracted values remain session-local. Demo reset does not delete cloud profiles. The app has no user authentication or tenant isolation; restrict access to the server. The supplied table has RLS enabled and no public access policies. Existing installations should run `grant select, insert on public.patients to service_role;` in the SQL editor if SELECT access is missing.

## Run locally

### Pinecone cloud connection

Selecting a patient loads all records from `patient-<Patient ID>` into the session workspace before rendering any patient section. **Refresh patient records** retries immediately; otherwise records refresh on interactions after 60 seconds. Source text, typed laboratory observations, and discharge sections populate Documents, Lab trends, AI analysis, Evidence & review, Timeline, and Reports. Analysis is regenerated from restored observations. Original binary files are not stored in Pinecone; restored downloads contain source text. Older text-only vectors use the existing parser as a fallback; re-sync original reports to preserve PDF table values, dates, and exact provenance. Patient metadata is validated against the selected namespace. Local imports and reviewed session observations are preserved during cloud refreshes.

Set `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` in `.streamlit/secrets.toml` or server environment variables. Use an API key from the same Pinecone project as the index. Open **Connections → Test Pinecone connection**. The app verifies index readiness and reads vector statistics before showing **Available**. Checks are retained per session for 60 seconds. `PINECONE_ENVIRONMENT` is not needed: the index host is discovered automatically.

Non-quarantined report and discharge uploads automatically sync extracted text to an index with integrated embeddings. Existing session documents can be synced with **Documents → Library → Sync documents to Pinecone**. Text is divided into 1,200-character chunks with 200-character overlap; batches contain up to 96 records. The index's embedding field mapping is discovered automatically. Patient records use namespace `patient-<Patient ID>` and stable chunk IDs for safe retries. Success is shown only after all upserts are acknowledged. Pinecone can take a short time to update vector counts. Inspect the patient's namespace in the Pinecone console. Document deletion and demo reset affect the local session only; cloud vectors remain. Semantic search is not yet enabled.

Tested with Python 3.13 and Streamlit 1.59.2.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. On Linux/macOS, use `.venv/bin/python` instead. OCR also requires the **Tesseract executable** and English language data; text-based PDF/DOCX/TXT parsing works without it.

## Working features

- Ten pages: overview, documents, discharge summary, trends, analysis, evidence/review, timeline, reports, connections, settings.
- Three synthetic patient profiles and nine source reports; eight lab markers with dated provenance.
- Patient switching, custom synthetic profiles, document search, filtering, text preview, source download.
- PDF/DOCX/TXT parsing and optional PNG/JPEG/scanned PDF OCR; bounded upload sizes and duplicate detection.
- Patient-name matching (allowing first names or a prefix of the full name, ignoring case, spacing, and common titles); patient IDs do not need to match. Missing or conflicting names are quarantined.
- Laboratory extraction for pipe-separated rows, multi-line panels, and ruled five-column PDF tables with methods and source ranges; imported observations are saved automatically and immediately available for trends and analysis.
- Source evidence viewer, retained revision history, and stale-analysis detection.
- Plotly trends with units, source links in tooltips, per-observation source ranges, date filtering and CSV export.
- Real LangGraph fan-out/join workflow: scope validation, trends, range checks, contradictions, data gaps, evidence mapping, evidence integrity check.
- Collection-date parsing supports ISO, day/month/year, and month-name dates, with per-page provenance.
- Source-linked deterministic summaries; no simulated LLM output, confidence score, or risk model.
- PDF/JSON analysis downloads and formula-safe CSV observations.
- Session-local deletion and demo reset. OS reduced-motion support and an in-app motion toggle.

## Try the import flow

1. Select **Alex Morgan · HL-2048**.
2. Open **Documents → Upload reports** and download the sample TXT.
3. Upload the sample and confirm it is synthetic.
4. Open **Lab trends** to see saved observations, or **Evidence & review** to inspect their source.
5. Open **AI analysis** to inspect the automatically generated summary, and download a report.

The supported text extraction format is explicit and intentionally narrow:

```text
SYNTHETIC DEMONSTRATION DATA
Patient ID: HL-2048
Date: 2026-09-20
Hemoglobin | 13.9 | g/dL | 12 - 15.5
```

Arbitrary lab layouts are retained as text; the demo does not pretend to understand unsupported tables. It does not interpret scan pixels, ECG waveforms, diagnoses, medications, or allergies.

## Architecture

```text
app.py + app_pages/         Streamlit routing and native interactive widgets
ui/                        Shared components, requested CSS animations, Plotly charts
healthlens/models.py        Validated source-preserving schemas
healthlens/ingestion.py     File parsing, OCR adapter, conservative extraction
healthlens/workspace.py     Session-isolated demo repository and revision history
healthlens/analytics.py     Deterministic comparisons and longitudinal calculations
healthlens/workflow.py      LangGraph orchestration and cited report assembly
healthlens/exports.py       PDF, JSON, CSV exports
tests/                     Domain behavior and Streamlit AppTest coverage
```

Data remains in the current Streamlit session. Browser reloads, session loss, and server restarts can reset it. Do not upload real patient information. This release intentionally refuses `APP_MODE` values other than `demo`.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py app_pages healthlens ui
```

Tests cover identity quarantine, duplicate imports, correction history, stale reports, bounded values, zero baselines, incompatible units, patient scope, cited workflow outputs, PDF/DOCX parsing, exports, deletion, every UI page, and the analysis/download flow. These are software tests, not clinical validation.

## Deployment

For a synthetic demo on Streamlit Community Cloud: push this repository, select `app.py`, choose Python 3.13, and deploy using `requirements.txt` and `packages.txt`. No secrets are needed. This workflow has not been tested against a live Community Cloud account.

For Docker:

```sh
docker compose up --build
```

Read [deployment and scope](docs/deployment.md) and [security](docs/security.md) before extending this demo.

## Connected roadmap

Google Drive OAuth/sync, Supabase authentication/RLS/private storage, Pinecone semantic RAG, provider-backed LLM extraction/synthesis, durable workers/checkpoints, retention jobs, validated risk models, and interoperability are **not implemented or live-verified in this release**. The Connections page accurately marks them unavailable. Adding secrets does not activate them.

The supplied [full specification](HealthLens_AI_Complete_End_to_End_Code_Generation_Prompt.md) remains the requirements source for later phases. Enterprise visual design is not a claim of production healthcare readiness.

# Discharge summaries

The **Discharge summary** page accepts PDF, PNG, JPG, and JPEG files up to 20 MB.
It extracts text locally (English Tesseract is required for images and scanned
PDFs) and organizes explicit headings into patient details, admission/discharge,
diagnoses, history, allergies, examination, investigations, procedures, hospital
course, condition at discharge, medications, instructions, follow-up, and warning
signs. Unrecognized content is preserved, and every extracted line has a source
location. Medication wording and doses are retained verbatim rather than inferred.
Discharge records proceed when a patient name is present, even if it differs from
the selected profile, and are saved under the selected patient. Records without a
readable patient name are quarantined.

Discharge records are separate from laboratory observations and remain available
across page navigation in the current session. Like other uploads in this demo,
they are not saved permanently; download the structured JSON and original file to
keep a copy. Check extracted content against the original before marking it reviewed.
