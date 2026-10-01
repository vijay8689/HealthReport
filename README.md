# HealthLens AI

An animated Streamlit workspace for exploring clinical documents, laboratory trends, evidence, and orchestrated summaries. Midnight-blue navigation, mint accents, a floating orbital hero, responsive cards, and reduced-motion support.

**This release is a working synthetic-data demo/MVP, not the entire connected production system described in the specification.** It makes no external AI calls and requires no API keys. It does not provide diagnosis, treatment recommendations, or clinical risk predictions.

## Run locally

Tested with Python 3.13 and Streamlit 1.59.2.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. On Linux/macOS, use `.venv/bin/python` instead. OCR also requires the **Tesseract executable** and English language data; text-based PDF/DOCX/TXT parsing works without it.

## Working features

- Nine pages: overview, documents, trends, analysis, evidence/review, timeline, reports, connections, settings.
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

