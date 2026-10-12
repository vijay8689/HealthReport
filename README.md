# HealthLens AI

An animated Streamlit workspace for exploring clinical documents, laboratory trends, evidence, and orchestrated summaries. Midnight-blue navigation, mint accents, a floating orbital hero, responsive cards, and reduced-motion support.

**This release is a working demo/MVP, not the entire connected production system described in the specification.** It makes no external AI calls. Adding patient workspaces requires Supabase configuration. It does not provide diagnosis, treatment recommendations, or clinical risk predictions.

## Sign up, sign in, and private patient workspaces

1. Run [docs/supabase.sql](docs/supabase.sql) in your Supabase SQL editor. This migrates the existing patients table and enables row-level ownership policies.
2. Set `SUPABASE_URL` to the HTTPS project URL and `SUPABASE_ANON_KEY` to your **publishable** (`sb_publishable_...`) or legacy **anon** key in `.streamlit/secrets.toml` or environment variables. Copy `.streamlit/secrets.toml.example` as a starting point. A publishable/anon `SUPABASE_KEY` is supported for compatibility. Secret/service-role keys are rejected for login and patient requests.
3. Enable email/password authentication and account sign-up in Supabase. Under Authentication ? URL Configuration, set Site URL to `http://localhost:8501` for local development and add `http://localhost:8501/**` to Redirect URLs. Set `APP_URL` to your deployed HTTPS app URL when hosting remotely and allow that URL in Supabase. Signup and resend requests include this redirect explicitly. If email confirmation is enabled, confirm your email first and then sign in with your password. The app does not consume confirmation tokens from URL fragments. If a link is invalid or expired, open Login ? Confirmation email missing or expired? and use Resend confirmation email. Open only the newest email link, then log in with your password.
4. Open the app to explore **Dummy Patient** without logging in. Use **Login** or **Sign up** in the top-right corner to open your private account. New accounts start with an empty patient list. Add your first patient on the welcome screen; add more through **Settings**.
5. Each patient is saved with the authenticated user's ID. Database policies allow users to read and insert only their own patient profiles. Different users may use the same patient ID. Unauthenticated visitors can view and download bundled synthetic dummy records only. Guest mode never loads Supabase patients or Pinecone records and cannot add private patients. Demo imports remain in that browser session.

**Sign out** returns to the dummy demo and clears the private browser session, including patient profiles, uploaded files, observations, reports, selections, and connection state. Authentication tokens are stored only in Streamlit's server session; passwords are sent to Supabase Auth and are not saved by this app. Tokens refresh on subsequent app interactions. Reloading or losing the Streamlit session requires signing in again.

**Existing records:** the SQL migration leaves historical patient rows without an owner. They are hidden from every regular account. An administrator must verify ownership and assign each row to the correct `auth.users.id` using its `row_id` (example in the migration). Never assign all legacy records to the first person who signs in.

Patient profiles persist in Supabase and refresh on interactions after 60 seconds or with **Refresh patients**. Documents and derived reports remain session-local unless document text and observations are synced to Pinecone. Legacy shared Pinecone namespaces are not loaded; re-upload the source reports under their verified owner's account. Clearing session data does not delete cloud profiles or vectors.

## Run locally

### Pinecone cloud connection

Selecting a patient first verifies ownership using the user's Supabase token, then loads records from `user-<User UUID>-patient-<SHA256 of Patient ID>` into the session workspace before rendering any patient section. **Refresh patient records** retries immediately; otherwise records refresh on interactions after 60 seconds. Source text, typed laboratory observations, and discharge sections populate Documents, Lab trends, AI analysis, Evidence & review, Timeline, and Reports. Analysis is regenerated from restored observations. Original binary files are not stored in Pinecone; restored downloads contain source text. Older text-only vectors use the existing parser as a fallback; re-sync original reports to preserve PDF table values, dates, and exact provenance. Patient and owner metadata are validated against the selected namespace. Local imports and reviewed session observations are preserved during cloud refreshes.

Set `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` in `.streamlit/secrets.toml` or server environment variables. Use an API key from the same Pinecone project as the index. Open **Connections → Test Pinecone connection**. The app verifies index readiness and reads vector statistics before showing **Available**. Checks are retained per session for 60 seconds. `PINECONE_ENVIRONMENT` is not needed: the index host is discovered automatically.

Non-quarantined report and discharge uploads automatically sync extracted text to an index with integrated embeddings. Existing session documents can be synced with **Documents → Library → Sync documents to Pinecone**. Text is divided into 1,200-character chunks with 200-character overlap; batches contain up to 96 records. The index's embedding field mapping is discovered automatically. Patient records use namespace `user-<User UUID>-patient-<SHA256 of Patient ID>` and stable chunk IDs for safe retries. Success is shown only after all upserts are acknowledged. Pinecone can take a short time to update vector counts. Inspect the patient's namespace in the Pinecone console. Document deletion and clearing session data affect the local session only; cloud vectors remain. Semantic search is not yet enabled.

Tested with Python 3.13 and Streamlit 1.59.2.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. On Linux/macOS, use `.venv/bin/python` instead. OCR also requires the **Tesseract executable** and English language data; text-based PDF/DOCX/TXT parsing works without it.

## Working features

- Ten pages: overview, documents, discharge summary, trends, analysis, evidence/review, timeline, reports, connections, settings.
- Email/password sign-up, sign-in, sign-out, and private user-owned patient profiles.
- Synthetic fixtures for development tests; signed-in accounts start empty.
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
- Session-local deletion and session clearing. OS reduced-motion support and an in-app motion toggle.

## Try the import flow

1. Sign in and add a synthetic patient named **Alex Morgan** with Patient ID **HL-2048**.
2. Open **Documents ? Upload reports** and download the sample TXT.
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

For a synthetic demo on Streamlit Community Cloud: push this repository, select `app.py`, choose Python 3.13, and deploy using `requirements.txt` and `packages.txt`. Supabase configuration and the ownership migration are required for login; the guest dummy demo works without credentials. This workflow has not been tested against a live Community Cloud account.

For Docker:

```sh
docker compose up --build
```

Read [deployment and scope](docs/deployment.md) and [security](docs/security.md) before extending this demo.

## Connected roadmap

Supabase email/password authentication and patient ownership policies are implemented. Live authentication and RLS verification against your project remain deployment checks. Google Drive OAuth/sync, Supabase private original-file storage, Pinecone semantic RAG, provider-backed LLM extraction/synthesis, durable workers/checkpoints, retention jobs, validated risk models, and interoperability are **not implemented or live-verified in this release**. The Connections page accurately marks them unavailable. Adding secrets does not activate them.

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
