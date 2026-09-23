# HealthLens AI — Complete End-to-End Code Generation Prompt

## 0. MASTER INSTRUCTION

Act as a senior Python architect, LangGraph/LangChain engineer, RAG engineer, Streamlit engineer, Google Cloud OAuth engineer, Supabase engineer, Pinecone engineer, ML engineer, QA automation architect, security engineer, and DevOps engineer.

Generate a **complete, runnable, tested, modular, production-structured GitHub repository** called:

# HealthLens AI

**Tagline:**  
Clinical Document Intelligence • Evidence-Grounded Health Insights • Longitudinal Patient Analytics

The repository must be designed to deploy directly to **Streamlit Community Cloud** after the user configures secrets.

Do not provide pseudocode where working code can reasonably be written.

Generate:
- actual Python source files;
- configuration;
- database migration SQL;
- tests;
- synthetic sample data;
- documentation;
- deployment files;
- Google Drive integration;
- Supabase integration;
- Pinecone integration;
- LangGraph workflow;
- Streamlit UI;
- evaluation framework.

Do not invent credentials, medical evidence, clinical validation results, proprietary model weights, or unsupported patient-specific conclusions.

---

# 1. PRODUCT VISION

HealthLens AI is a clinical document intelligence platform that allows a user to:

1. Upload patient diagnostic documents from a computer.
2. Connect to Google Drive using OAuth 2.0.
3. Browse Google Drive folders and files.
4. Select one or multiple files.
5. Read an entire Google Drive patient folder.
6. Parse PDF, DOCX, TXT and image documents.
7. Perform OCR for scanned documents.
8. Classify documents.
9. Extract structured clinical observations.
10. Normalize clinical terminology and units where safe.
11. Preserve source/page-level provenance.
12. Store structured information in Supabase.
13. Store searchable evidence/chunks in Pinecone.
14. Use LangGraph for multi-agent orchestration.
15. Perform evidence-grounded RAG.
16. Build a longitudinal patient timeline.
17. Analyze laboratory trends.
18. Identify values outside reference ranges supplied by the source report.
19. Detect contradictory information.
20. Identify missing information.
21. Produce evidence-grounded summaries.
22. Support an extensible disease-specific validated risk-model interface.
23. Display risk results only when an appropriately configured model is available.
24. Provide a professional Streamlit clinical analytics dashboard.
25. Provide evaluation and testing tools.
26. Deploy on Streamlit Community Cloud.

The application must support both:

```text
LOCAL COMPUTER
     ↓
Upload Files
```

and:

```text
GOOGLE DRIVE
     ↓
Connect
     ↓
Browse
     ↓
Select Folder/File
     ↓
Read
```

---

# 2. HEALTHCARE SAFETY AND RESPONSIBLE AI

This application is intended for:
- research;
- education;
- clinical document organization;
- evidence-grounded summarization;
- decision-support prototyping.

It must NOT be presented as an autonomous diagnostic system.

Display prominently:

> HealthLens AI is a research and educational clinical document intelligence tool. It does not replace professional medical evaluation, diagnosis, or treatment. Risk assessments are displayed only when an appropriately configured and validated model is available.

Never:
- invent diagnoses;
- invent lab values;
- invent patient history;
- invent missing information;
- infer a disease solely from one abnormal value;
- claim that a patient will develop a disease;
- fabricate medical references;
- fabricate clinical validation;
- provide unsupported treatment instructions;
- silently substitute guessed values for missing risk-model inputs;
- present an LLM inference as a verified clinical fact.

Preferred language:

- "The supplied report records..."
- "The available records show..."
- "The laboratory report lists..."
- "The value is outside the reference range supplied by the source report."
- "The available information is insufficient to assess..."
- "This finding may warrant review by a qualified healthcare professional."

Avoid:

- "You definitely have..."
- "You will develop..."
- "This proves..."
- "You should take..."

For public/demo deployment, include only synthetic or de-identified data.

---

# 3. HIGH-LEVEL ARCHITECTURE

Implement:

```text
                           ┌─────────────────────┐
                           │   Local Computer    │
                           │ PDF/DOCX/TXT/Image  │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │ Document Upload     │
                           └──────────┬──────────┘
                                      │
                                      │
┌───────────────────────┐             │
│      Google Drive     │             │
│ OAuth → Browse → Read │─────────────┤
└───────────────────────┘             │
                                      ▼
                           ┌─────────────────────┐
                           │ Document Intake     │
                           └──────────┬──────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Parser + OCR        │
                           └──────────┬──────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Document Classifier │
                           └──────────┬──────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Clinical Extraction │
                           └──────────┬──────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Normalization       │
                           └──────────┬──────────┘
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                  ┌─────────────┐           ┌─────────────┐
                  │  Supabase   │           │  Pinecone   │
                  │ Structured  │           │ RAG Evidence│
                  │ Data        │           │ Vectors     │
                  └──────┬──────┘           └──────┬──────┘
                         │                         │
                         └────────────┬────────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ LangGraph Supervisor│
                           └──────────┬──────────┘
                                      │
       ┌──────────────────────────────┼──────────────────────────────┐
       ▼                              ▼                              ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│ Clinical RAG │              │ Trend Agent  │              │ Abnormality  │
│ Agent        │              │              │              │ Agent        │
└──────────────┘              └──────────────┘              └──────────────┘
       │                              │                              │
       └──────────────────────────────┼──────────────────────────────┘
                                      │
             ┌────────────────────────┼───────────────────────┐
             ▼                        ▼                       ▼
     ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
     │ Contradiction│        │ Missing Data │        │ Risk Model   │
     │ Agent        │        │ Agent        │        │ Router       │
     └──────────────┘        └──────────────┘        └──────────────┘
             │                        │                       │
             └────────────────────────┼───────────────────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Evidence Agent      │
                           └──────────┬──────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Safety / Critic     │
                           │ Agent               │
                           └──────────┬──────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Final Report        │
                           └──────────┬──────────┘
                                      ▼
                           ┌─────────────────────┐
                           │ Streamlit Dashboard │
                           └─────────────────────┘
```

---

# 4. TECHNOLOGY STACK

Use:

## Core

- Python 3.11+
- Streamlit
- Plotly
- Pandas
- Pydantic

## AI

- LangChain
- LangGraph

## Vector database

- Pinecone

## Cloud database

- Supabase

Do not require the user to install or operate a standalone PostgreSQL server.

## Document processing

- PyMuPDF
- python-docx
- Pillow
- pytesseract where available
- OCR abstraction layer

The application must gracefully handle environments where Tesseract is not installed.

## Analytics / ML

- NumPy
- SciPy
- scikit-learn
- optional XGBoost

Do not represent generic ML models as clinically validated.

## Evaluation

- DeepEval-compatible structure
- RAGAS-compatible structure

## Testing

- pytest

## Deployment

- Streamlit Community Cloud
- Docker

---

# 5. COMPLETE REPOSITORY STRUCTURE

Generate:

```text
healthlens-ai/
│
├── app.py
├── README.md
├── LICENSE
├── requirements.txt
├── packages.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── .env.example
│
├── .streamlit/
│   └── config.toml
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── model_config.py
│
├── agents/
│   ├── __init__.py
│   ├── intake_agent.py
│   ├── extraction_agent.py
│   ├── normalization_agent.py
│   ├── rag_agent.py
│   ├── trend_agent.py
│   ├── abnormality_agent.py
│   ├── contradiction_agent.py
│   ├── missing_data_agent.py
│   ├── risk_agent.py
│   ├── evidence_agent.py
│   ├── safety_agent.py
│   └── supervisor.py
│
├── graph/
│   ├── __init__.py
│   ├── state.py
│   ├── nodes.py
│   ├── edges.py
│   └── workflow.py
│
├── ingestion/
│   ├── __init__.py
│   ├── base.py
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   ├── image_parser.py
│   ├── txt_parser.py
│   ├── ocr.py
│   └── classifier.py
│
├── clinical/
│   ├── __init__.py
│   ├── schemas.py
│   ├── terminology.py
│   ├── units.py
│   ├── observations.py
│   └── provenance.py
│
├── analytics/
│   ├── __init__.py
│   ├── trends.py
│   ├── statistics.py
│   └── completeness.py
│
├── rag/
│   ├── __init__.py
│   ├── embeddings.py
│   ├── chunking.py
│   ├── pinecone_client.py
│   ├── retriever.py
│   └── metadata.py
│
├── database/
│   ├── __init__.py
│   ├── supabase_client.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── patients.py
│   │   ├── documents.py
│   │   ├── observations.py
│   │   ├── medications.py
│   │   ├── conditions.py
│   │   ├── analyses.py
│   │   └── audit.py
│   └── migrations/
│       └── 001_initial_schema.sql
│
├── integrations/
│   ├── __init__.py
│   └── google_drive/
│       ├── __init__.py
│       ├── auth.py
│       ├── client.py
│       ├── folders.py
│       ├── files.py
│       ├── reader.py
│       ├── metadata.py
│       └── sync.py
│
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── model_registry.py
│   ├── risk_router.py
│   └── examples/
│       ├── __init__.py
│       └── demo_model.py
│
├── security/
│   ├── __init__.py
│   ├── secrets.py
│   ├── validation.py
│   ├── access_control.py
│   └── audit.py
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── patients.py
│   ├── documents.py
│   ├── google_drive.py
│   ├── timeline.py
│   ├── trends.py
│   ├── risk.py
│   ├── ai_analysis.py
│   ├── evidence.py
│   └── components.py
│
├── evaluation/
│   ├── __init__.py
│   ├── rag_evaluation.py
│   ├── extraction_evaluation.py
│   ├── retrieval_evaluation.py
│   ├── hallucination_tests.py
│   └── safety_evaluation.py
│
├── tests/
│   ├── unit/
│   ├── agents/
│   ├── rag/
│   ├── google_drive/
│   ├── database/
│   ├── security/
│   ├── safety/
│   └── integration/
│
├── data/
│   └── synthetic/
│       ├── patient_001/
│       └── patient_002/
│
└── docs/
    ├── deployment.md
    ├── google-drive-setup.md
    ├── supabase-setup.md
    ├── pinecone-setup.md
    └── security.md
```

---

# 6. DOCUMENT INGESTION

Create a common interface:

```python
class DocumentReader(Protocol):
    def can_read(self, mime_type: str, filename: str) -> bool:
        ...

    def read(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        ...
```

Support:

- PDF
- DOCX
- TXT
- PNG
- JPG
- JPEG

For each document store:

```text
document_id
patient_id
source
source_file_id
filename
mime_type
document_type
document_date
page_count
content_hash
ocr_used
```

Calculate SHA-256 content hashes.

Duplicate behavior:

```text
same source file ID + same hash
    -> SKIP

same source file ID + changed hash
    -> REPROCESS
```

A failed document must not stop the entire patient batch.

---

# 7. PDF AND OCR

For normal PDFs:
- extract page-level text with PyMuPDF.

For scanned PDFs/images:
- use OCR abstraction.
- record `ocr_used=True`.
- preserve page number.
- preserve OCR confidence when available.

If OCR is unavailable:
- show a clear error;
- do not silently generate fake text.

---

# 8. CLINICAL DATA SCHEMAS

Implement Pydantic models.

Example:

```python
class ClinicalObservation(BaseModel):
    patient_id: str
    document_id: str
    observation_id: str
    category: str
    test_name: str
    standardized_name: str | None = None
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    abnormal_flag: str | None = None
    observation_date: datetime | None = None
    source_page: int | None = None
    source_text: str
    extraction_confidence: float | None = None
```

Also create schemas for:

- Medication
- Condition
- VitalSign
- ImagingFinding
- DocumentMetadata
- Evidence
- TrendResult
- Contradiction
- MissingDataItem
- RiskResult
- AnalysisReport

Never infer fields that are not present in source evidence.

---

# 9. TERMINOLOGY AND UNITS

Create normalization modules.

Where practical, support compatibility with:

- LOINC
- SNOMED CT
- ICD-10
- RxNorm
- UCUM

Do not fabricate codes.

If no mapping exists:

```text
mapping_status = "unmapped"
```

Preserve original terminology.

Unit conversion must only occur when conversion is unambiguous.

Always retain original value/unit.

---

# 10. SUPABASE DATABASE

Create migration SQL for:

## patients

```text
id
external_patient_id
display_name
date_of_birth
sex
created_at
updated_at
```

## documents

```text
id
patient_id
source
source_file_id
filename
mime_type
document_type
document_date
content_hash
page_count
processing_status
processing_error
created_at
updated_at
```

## observations

```text
id
patient_id
document_id
category
test_name
standardized_name
value_numeric
value_text
unit
reference_low
reference_high
abnormal_flag
observation_date
source_page
source_text
extraction_confidence
created_at
```

## medications

```text
id
patient_id
document_id
medication_name
dose
route
frequency
start_date
end_date
source_page
created_at
```

## conditions

```text
id
patient_id
document_id
condition_name
standardized_code
status
source_page
created_at
```

## analysis_runs

```text
id
patient_id
run_id
workflow_version
status
summary
created_at
completed_at
```

## risk_results

```text
id
patient_id
model_name
model_version
endpoint
horizon
result
input_completeness
limitations
created_at
```

## audit_events

```text
id
user_id
patient_id
event_type
resource_id
metadata_json
created_at
```

Create useful indexes.

Implement repository classes:
- PatientRepository
- DocumentRepository
- ObservationRepository
- MedicationRepository
- ConditionRepository
- AnalysisRepository
- AuditRepository

Do not place database operations directly inside UI modules.

Provide `docs/supabase-setup.md`.

---

# 11. GOOGLE DRIVE

Google Drive is a first-class input source.

Streamlit UI:

```text
Document Source

○ Upload from Computer
○ Read from Google Drive
```

Google Drive flow:

```text
Connect Google Drive
       ↓
OAuth 2.0
       ↓
Browse folders
       ↓
Select patient folder
       ↓
Select documents
       ↓
Read Selected Files
       ↓
Process
```

Implement:

```text
integrations/google_drive/
    auth.py
    client.py
    folders.py
    files.py
    reader.py
    metadata.py
    sync.py
```

Requirements:

- OAuth 2.0;
- no passwords requested;
- no credentials in source;
- Streamlit secrets/environment configuration;
- folder browsing;
- file browsing;
- multi-file selection;
- whole-folder processing;
- file metadata;
- modified timestamps;
- file IDs;
- content hashes;
- duplicate detection;
- modified-file detection;
- sync status.

Supported:
- PDF
- DOCX
- PNG/JPG/JPEG
- TXT

UI buttons:

```text
[ Connect Google Drive ]
[ Read Selected Files ]
[ Read Entire Folder ]
[ Sync Changes ]
```

Preserve metadata:

```json
{
  "source": "google_drive",
  "source_file_id": "drive-file-id",
  "document_name": "blood_report.pdf",
  "folder_path": "Patients/P001",
  "modified_time": "..."
}
```

Create `docs/google-drive-setup.md` explaining:
- Google Cloud project;
- Drive API;
- OAuth consent screen;
- OAuth client;
- redirect URI;
- Streamlit secrets;
- local development;
- Streamlit Cloud deployment.

Do not fake OAuth functionality.

---

# 12. PINECONE

Use Pinecone for semantic document evidence.

Environment:

```text
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
PINECONE_CLOUD=
PINECONE_REGION=
```

Do not hard-code vector dimension.

Use the configured embedding model/provider to determine dimension.

Metadata:

```json
{
  "patient_id": "P001",
  "document_id": "DOC123",
  "document_name": "blood_report.pdf",
  "source": "google_drive",
  "document_type": "lab_report",
  "document_date": "2026-08-15",
  "page": 2,
  "clinical_domain": "metabolic",
  "chunk_id": "DOC123_CHUNK004"
}
```

Every retrieval must filter by active patient ID.

For multi-tenant deployment, enforce tenant isolation.

Provide `docs/pinecone-setup.md`.

---

# 13. RAG

Implement:

## Patient Evidence Retriever

Retrieves only evidence for the selected patient.

## General Reference Retriever

Optional separate source for general reference content.

Never silently mix general reference content with patient evidence.

Return structured evidence:

```python
{
    "claim": "...",
    "document_id": "...",
    "document_name": "...",
    "page": 2,
    "source_text": "...",
    "relevance_score": 0.91
}
```

If no evidence exists:

```text
No supporting evidence was found in the supplied records.
```

---

# 14. LANGGRAPH STATE

Create:

```python
class HealthAnalysisState(TypedDict):
    patient_id: str
    document_ids: list[str]
    query: str | None

    extracted_observations: list[dict]
    retrieved_evidence: list[dict]

    trends: list[dict]
    abnormalities: list[dict]
    contradictions: list[dict]
    missing_data: list[dict]

    risk_results: list[dict]

    evidence_map: list[dict]

    draft_analysis: dict
    safety_findings: list[dict]

    final_report: dict
```

Workflow:

```text
START
  ↓
Intake
  ↓
Extraction
  ↓
Normalization
  ↓
Parallel analysis
  ├── RAG
  ├── Trends
  ├── Abnormalities
  ├── Contradictions
  └── Missing Data
  ↓
Risk Router
  ↓
Evidence Mapping
  ↓
Safety Critic
  ↓
Final Report
  ↓
END
```

Implement actual LangGraph code.

---

# 15. AGENTS

## 15.1 Intake Agent

Responsibilities:
- classify documents;
- identify dates;
- identify document type;
- identify source;
- validate patient association.

## 15.2 Clinical Extraction Agent

Extract:
- laboratory values;
- units;
- reference ranges;
- dates;
- vital signs;
- medications;
- explicitly mentioned conditions;
- imaging findings;
- procedures.

Always preserve:
- source document;
- page;
- source text.

## 15.3 Normalization Agent

Normalize:
- terminology;
- units;
- categories.

Do not invent mappings.

## 15.4 RAG Agent

Retrieve evidence and synthesize only evidence-supported information.

## 15.5 Trend Agent

Use deterministic Python for:
- latest value;
- previous value;
- absolute delta;
- percentage change;
- direction;
- time span;
- number of observations.

Do not ask an LLM to perform arithmetic.

## 15.6 Abnormality Agent

Compare values against source-provided reference ranges.

Return:

```text
LOW
NORMAL
HIGH
UNKNOWN
```

Do not turn abnormality into diagnosis.

## 15.7 Contradiction Agent

Detect:
- conflicting values;
- conflicting dates;
- inconsistent units;
- medication conflicts;
- patient identity conflicts;
- duplicate documents.

## 15.8 Missing Data Agent

Detect missing information required for:
- analysis;
- trend interpretation;
- risk models.

## 15.9 Risk Model Router

Implement:

```python
class RiskModel(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def endpoint(self) -> str: ...

    @property
    def horizon(self) -> str: ...

    def required_inputs(self) -> list[str]: ...

    def is_eligible(self, patient_data: dict) -> bool: ...

    def predict(self, patient_data: dict) -> RiskResult: ...
```

Implement model registry.

If no validated model is available:

```text
No validated risk model is configured for this outcome.
```

Do not produce a fake prediction.

A demo model, if included, must be clearly labeled:

```text
DEMO ONLY — NOT CLINICALLY VALIDATED
```

## 15.10 Evidence Agent

Map each patient-specific claim to:
- document;
- page;
- source text;
- observation ID.

## 15.11 Safety/Critic Agent

Flag:
- unsupported diagnosis;
- unsupported prediction;
- missing citation;
- hallucinated values;
- numerical errors;
- contradictions;
- missing risk inputs;
- excessive certainty.

If the safety critic rejects a draft, do not display it as a final report.

---

# 16. STREAMLIT UI

Build a polished clinical analytics interface.

Do not make it look like a generic chatbot.

Sidebar:

```text
🏥 HealthLens AI

Dashboard
Patients
Documents
Google Drive
Lab Results
Timeline
Trends
Medications
Conditions
Risk Analysis
AI Analysis
Evidence
Evaluation
Settings
```

## Dashboard

Display:
- patient selector;
- document count;
- observation count;
- latest report date;
- latest analysis;
- data completeness.

Category cards:

```text
Metabolic
Cardiovascular
Renal
Thyroid
Hematology
Liver
```

Only show categories supported by available data.

## Documents

Show:
- source;
- filename;
- type;
- date;
- processing status;
- page count;
- source ID;
- sync status.

## Google Drive

Show:

```text
☁ Google Drive

Status: Connected / Not Connected

Folder:
Patients / P001

☑ Blood_Report.pdf
☑ MRI_Report.pdf
☐ ECG_Report.pdf
☐ Prescription.pdf

[ Read Selected Files ]
[ Read Entire Folder ]
[ Sync Changes ]
```

## Timeline

Show:
- documents;
- lab observations;
- medications;
- conditions;
- imaging events.

## Lab Trends

Use Plotly.

Features:
- test selector;
- date filter;
- units;
- reference range;
- hover source;
- document name;
- page number.

## AI Analysis

Sections:

```text
Evidence-Based Summary
Observed Trends
Observed Out-of-Range Values
Potential Areas for Professional Review
Data Gaps
Contradictions
Risk Assessments
Evidence
Limitations
```

## Evidence Viewer

For every claim show:

```text
Claim
↓
Evidence
↓
Document
↓
Page
↓
Extracted value
```

If a valid Google Drive web URL is available, show an "Open in Google Drive" link.

## Risk Analysis

Only show registered/configured risk models.

Display:

```text
Model
Version
Endpoint
Population
Prediction Horizon
Input Completeness
Result
Limitations
```

---

# 17. REPORT SCHEMA

Generate a structured report:

```text
Patient Overview
Document Summary
Key Observations
Laboratory Trends
Observed Out-of-Range Values
Longitudinal Changes
Medication Information
Conditions Explicitly Mentioned
Contradictions
Missing Data
Risk Assessments
Evidence
Limitations
Safety Notes
```

Every section should be generated from structured state.

---

# 18. SECURITY

Implement:

- secrets from Streamlit secrets/environment;
- no secrets in Git;
- file type validation;
- file size limits;
- safe filenames;
- patient-level filtering;
- tenant isolation hooks;
- audit events;
- least-privilege Google Drive permissions;
- safe error messages;
- no raw medical data in logs;
- no OAuth token logging;
- no API key logging.

Do not log:
- passwords;
- OAuth tokens;
- API keys;
- unnecessary PHI.

Create `docs/security.md`.

---

# 19. CONFIGURATION

Create `.env.example`:

```text
APP_ENV=development
LOG_LEVEL=INFO

SUPABASE_URL=
SUPABASE_KEY=

PINECONE_API_KEY=
PINECONE_INDEX_NAME=
PINECONE_CLOUD=
PINECONE_REGION=

LLM_PROVIDER=
LLM_MODEL=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

EMBEDDING_PROVIDER=
EMBEDDING_MODEL=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
```

Only require keys for the provider actually configured.

Create `config/settings.py`.

Never hard-code secrets.

---

# 20. STREAMLIT SECRETS

Document Streamlit Cloud secrets.

Example:

```toml
SUPABASE_URL = "..."
SUPABASE_KEY = "..."

PINECONE_API_KEY = "..."
PINECONE_INDEX_NAME = "..."
PINECONE_CLOUD = "..."
PINECONE_REGION = "..."

LLM_PROVIDER = "..."
LLM_MODEL = "..."

OPENAI_API_KEY = "..."

EMBEDDING_PROVIDER = "..."
EMBEDDING_MODEL = "..."

GOOGLE_CLIENT_ID = "..."
GOOGLE_CLIENT_SECRET = "..."
GOOGLE_REDIRECT_URI = "..."
```

Do not commit real values.

---

# 21. PROVIDER ABSTRACTIONS

Create clean interfaces for:

- LLM;
- embeddings;
- OCR;
- vector store;
- structured database;
- document source.

The application should not be tightly coupled to one LLM provider.

Use dependency injection where practical.

---

# 22. PERFORMANCE

Implement:

- `st.cache_resource` for safe reusable external clients;
- lazy initialization;
- batching for embeddings;
- duplicate detection;
- incremental Google Drive sync;
- pagination;
- no unnecessary full-database reloads;
- patient-specific retrieval;
- restartable document processing.

Never cache patient-specific confidential data globally.

---

# 23. OBSERVABILITY

Implement structured logging with:
- run ID;
- pseudonymous patient ID;
- workflow stage;
- duration;
- status;
- error category.

Never log:
- secrets;
- tokens;
- unnecessary raw clinical content.

---

# 24. EVALUATION

Create:

```text
evaluation/
├── rag_evaluation.py
├── extraction_evaluation.py
├── retrieval_evaluation.py
├── hallucination_tests.py
└── safety_evaluation.py
```

Evaluate:

## RAG
- retrieval relevance;
- context precision;
- context recall;
- answer relevance;
- faithfulness;
- citation accuracy.

## Extraction
- test name accuracy;
- value accuracy;
- unit accuracy;
- date accuracy;
- reference-range accuracy;
- page/source accuracy.

## Safety
- unsupported claim rate;
- uncited claim rate;
- hallucination rate;
- missing-input handling;
- contradiction detection.

## Risk models

Only evaluate a real configured model:
- AUROC;
- AUPRC;
- sensitivity;
- specificity;
- calibration;
- Brier score;
- subgroup performance.

Never fabricate evaluation results.

---

# 25. TESTING

Create comprehensive pytest tests.

Test:
- PDF parsing;
- DOCX parsing;
- OCR fallback;
- extraction validation;
- normalization;
- duplicate detection;
- Google Drive adapter;
- Supabase repositories;
- Pinecone metadata;
- patient filtering;
- LangGraph state transitions;
- trend calculations;
- abnormality detection;
- contradiction detection;
- missing-data handling;
- safety critic;
- report generation.

Mock:
- Google Drive;
- Pinecone;
- Supabase;
- LLM;
- embeddings.

Unit tests must not require production credentials.

Commands:

```bash
pytest
python -m compileall .
```

---

# 26. SYNTHETIC DATA

Create synthetic data:

```text
data/synthetic/
├── patient_001/
│   ├── blood_report_2025.pdf
│   ├── blood_report_2026.pdf
│   └── sample_report.txt
└── patient_002/
    ├── blood_report_2026.pdf
    └── sample_report.txt
```

If generating PDFs programmatically, ensure they contain clearly synthetic information.

Display:

```text
SYNTHETIC DEMONSTRATION DATA
```

Do not include real PHI.

---

# 27. DEPLOYMENT

Create:

```text
.streamlit/config.toml
requirements.txt
packages.txt
Dockerfile
docker-compose.yml
```

The default path should be Streamlit Community Cloud.

`app.py` must be the entry point.

The application must not require local Docker for Streamlit Cloud.

Use environment/Streamlit secrets.

Provide `docs/deployment.md` containing:

1. GitHub repository setup.
2. Supabase project setup.
3. Pinecone setup.
4. Google Cloud OAuth setup.
5. Local `.env` setup.
6. Local execution.
7. Git push.
8. Streamlit Community Cloud deployment.
9. Streamlit secrets configuration.
10. Redirect URI configuration.
11. Health check.
12. Troubleshooting.

Local run:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

# 28. DOCKER

Create a minimal production-style Dockerfile.

It must:

- use Python 3.11 slim;
- install requirements;
- expose Streamlit port;
- use environment variables;
- run `streamlit run app.py`.

Do not bake secrets into the image.

Create `docker-compose.yml` for local development.

---

# 29. STREAMLIT CONFIGURATION

Create:

```text
.streamlit/config.toml
```

Use a professional layout.

Recommended:

```toml
[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false

[theme]
base = "light"
```

Keep styling professional and accessible.

---

# 30. UI DESIGN

Design a modern clinical analytics dashboard.

Use:
- sidebar navigation;
- cards;
- tabs;
- expandable evidence;
- Plotly;
- status indicators;
- progress bars;
- clear empty states;
- clear errors;
- consistent typography;
- responsive layout.

Avoid:
- excessive emojis;
- generic chatbot UI;
- huge walls of AI text;
- unsupported medical severity colors;
- fake confidence meters.

---

# 31. DATABASE / VECTOR SEPARATION

Maintain strict separation:

```text
Google Drive
    = Original documents

Supabase
    = Structured patient/application data

Pinecone
    = Semantic evidence/chunks

LangGraph
    = Workflow/orchestration

Streamlit
    = UI
```

Do not use Pinecone as the primary structured patient database.

---

# 32. PROVENANCE

Every extracted observation must retain:

```text
patient_id
document_id
document_name
source
source_file_id
page
source_text
observation_id
```

Every AI claim should be traceable.

Example:

```text
HbA1c: 6.2%

Source:
Blood_Report_2026.pdf
Page: 2
Source: Google Drive
```

If no source exists:

```text
Source unavailable.
```

Do not fabricate citations.

---

# 33. GOOGLE DRIVE SYNC

Implement incremental sync:

```text
Google Drive
     ↓
List known files
     ↓
Compare file ID + modified timestamp/hash
     ↓
New file?
   ├── yes → process
   └── no
Changed?
   ├── yes → reprocess
   └── no → skip
```

Display:

```text
Last Sync
New Documents
Modified Documents
Skipped Documents
Failed Documents
```

Store sync metadata in Supabase.

---

# 34. SAMPLE USER JOURNEY

The completed application must support:

```text
1. Open HealthLens AI.

2. Select:
   Read from Google Drive.

3. Click:
   Connect Google Drive.

4. Browse:
   Patients / P001.

5. Select:
   Blood_Report.pdf
   MRI_Report.pdf
   ECG_Report.pdf

6. Click:
   Read Selected Files.

7. System:
   downloads/read documents
   ↓
   parses text
   ↓
   OCR if needed
   ↓
   classifies documents
   ↓
   extracts clinical observations
   ↓
   validates schemas
   ↓
   normalizes safe fields
   ↓
   writes structured data to Supabase
   ↓
   chunks documents
   ↓
   generates embeddings
   ↓
   writes vectors to Pinecone
   ↓
   runs LangGraph analysis

8. User opens AI Analysis.

9. LangGraph:
   RAG
   ↓
   trends
   ↓
   abnormality analysis
   ↓
   contradictions
   ↓
   missing data
   ↓
   risk router
   ↓
   evidence mapping
   ↓
   safety critic

10. Dashboard:
   patient overview
   timeline
   lab trends
   evidence-grounded observations
   data gaps
   configured risk results
   limitations
```

---

# 35. REPORT GENERATION

Create a structured report:

```text
Patient Overview
Document Summary
Key Observations
Laboratory Trends
Observed Out-of-Range Values
Longitudinal Changes
Medication Information
Conditions Explicitly Mentioned
Contradictions
Missing Data
Risk Assessments
Evidence
Limitations
Safety Notes
```

The report must be generated from structured workflow state.

---

# 36. ERROR HANDLING

Handle clearly:

```text
Google Drive authentication failed.
Google Drive permission denied.
Folder not found.
File download failed.
Unsupported file type.
Document parsing failed.
OCR unavailable.
Clinical extraction failed.
Supabase connection failed.
Pinecone connection failed.
Embedding generation failed.
LLM provider unavailable.
Risk model unavailable.
Risk model inputs missing.
```

Do not expose stack traces or secrets in the UI.

Provide a developer-friendly log while keeping user-facing messages safe.

---

# 37. EMPTY STATES

Examples:

No patient:

> Select or import a patient to begin.

No documents:

> No documents have been imported yet.

No trends:

> Not enough observations are available to build a longitudinal trend.

No risk model:

> No validated risk model is configured for this outcome.

No evidence:

> No supporting evidence was found in the supplied records.

---

# 38. CODE QUALITY

Use:
- type hints;
- docstrings;
- Pydantic;
- small functions;
- clear interfaces;
- dependency injection;
- meaningful exceptions;
- structured logging;
- modular services;
- no unnecessary global state.

Avoid giant files.

Do not put the entire application in `app.py`.

`app.py` should primarily initialize the application and route UI.

---

# 39. README

Create a professional README containing:

1. Product overview.
2. Architecture diagram.
3. Feature list.
4. Technology stack.
5. Repository structure.
6. Local setup.
7. Supabase setup.
8. Pinecone setup.
9. Google Drive setup.
10. Environment variables.
11. Streamlit Cloud deployment.
12. Docker deployment.
13. Synthetic data.
14. Security.
15. Healthcare disclaimer.
16. Testing.
17. Evaluation.
18. Troubleshooting.
19. Roadmap.

Include example screenshots as placeholders only if actual screenshots are unavailable.

Do not fabricate live URLs.

---

# 40. LICENSE

Use a simple permissive open-source license such as MIT unless the user specifies another license.

Include a disclaimer that the software is not medical advice.

---

# 41. GITIGNORE

Include:

```text
.env
.env.*
!.env.example
.streamlit/secrets.toml
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.DS_Store
.idea/
.vscode/
logs/
*.log
```

Never commit:
- credentials;
- tokens;
- real patient records;
- API keys;
- OAuth secrets.

---

# 42. ACCEPTANCE CRITERIA

The generated repository is complete only if:

- `streamlit run app.py` starts.
- Local file upload works.
- Google Drive integration code is implemented.
- Google Drive browsing/selection UI exists.
- Google OAuth configuration is documented.
- PDF/DOCX/image/TXT ingestion exists.
- OCR fallback exists.
- Clinical extraction schemas exist.
- Supabase integration exists.
- SQL migrations exist.
- Pinecone integration exists.
- Patient-filtered retrieval exists.
- LangGraph workflow exists.
- All major agents exist.
- Deterministic trend calculations exist.
- Abnormality logic uses source reference ranges.
- Contradiction detection exists.
- Missing-data detection exists.
- Risk model registry exists.
- No fake clinical prediction is produced.
- Evidence mapping exists.
- Safety critic exists.
- Streamlit UI is polished.
- Synthetic sample data exists.
- Tests exist.
- External integrations are mocked in tests.
- `.env.example` exists.
- Streamlit Cloud deployment documentation exists.
- Docker files exist.
- README exists.
- No real patient data is included.

---

# 43. FINAL CODE-GENERATION PROCEDURE

When generating the repository:

### Step 1
Create the complete directory tree.

### Step 2
Create all Python modules.

### Step 3
Create Supabase SQL migrations.

### Step 4
Create Google Drive OAuth/integration modules.

### Step 5
Create Pinecone and embedding modules.

### Step 6
Create clinical schemas and extraction pipeline.

### Step 7
Create LangGraph state, nodes, edges and workflow.

### Step 8
Create Streamlit pages/components.

### Step 9
Create synthetic data.

### Step 10
Create tests and mocks.

### Step 11
Create evaluation modules.

### Step 12
Create deployment files.

### Step 13
Create documentation.

### Step 14
Run:

```bash
python -m compileall .
```

Then:

```bash
pytest
```

Fix all obvious syntax/import/test failures that do not require unavailable external credentials.

### Step 15
Verify:

```bash
streamlit run app.py
```

where the execution environment supports Streamlit.

### Step 16
Provide a final report:

```text
Files created:
...

Required secrets:
...

Local setup:
...

Supabase setup:
...

Pinecone setup:
...

Google Drive setup:
...

Streamlit Cloud deployment:
...

Known limitations:
...
```

---

# 44. IMPORTANT IMPLEMENTATION RULES

1. Do not invent APIs.
2. Do not invent credentials.
3. Do not invent clinical evidence.
4. Do not invent model validation.
5. Do not invent patient data.
6. Do not hide missing information.
7. Do not hard-code secrets.
8. Do not use patient data from one patient in another patient's retrieval.
9. Do not let an LLM perform arithmetic that Python can safely perform.
10. Do not let an LLM create unsupported medical diagnoses.
11. Do not expose raw exceptions containing secrets.
12. Do not make Google Drive OAuth a fake placeholder if an actual adapter can be implemented.
13. Use mocks for tests instead of production credentials.
14. Keep the application runnable when optional integrations are not configured.
15. If a required service is not configured, show a useful configuration message instead of crashing.
16. Use feature detection/configuration flags for optional components.
17. Make the application graceful when LLM, OCR, Google Drive, Pinecone or Supabase is unavailable.
18. Preserve document provenance throughout the entire pipeline.

---

# 45. PRODUCT BRANDING

Use consistently:

**HealthLens AI**

Subtitle:

**Clinical Document Intelligence**

Tagline:

**Evidence-Grounded Health Insights • Longitudinal Patient Analytics**

Suggested navigation title:

```text
🏥 HealthLens AI
Clinical Document Intelligence
```

---

# 46. FINAL APPLICATION FOOTER

Every relevant analysis screen should show:

> For research and educational use only. HealthLens AI summarizes information contained in supplied records and does not replace professional medical evaluation, diagnosis, or treatment. Use synthetic or appropriately authorized data for demonstrations.

---

# 47. REVIEW ADDITIONS: IMPLEMENTATION REQUIREMENTS

Review date: 2026-09-23. These additions close gaps in the original specification. They are requirements for a future implementation, not evidence that the app or integrations have been built or validated. Where earlier examples are less specific, apply the requirements below. Sections 17 and 35 describe one report schema and must share one implementation.

## 47.1 Delivery phases and deployment modes

Build and verify a working vertical slice before expanding to every integration:

1. **MVP:** synthetic demo, local upload, parsing/OCR, patient association, structured extraction, review/correction, deterministic lab comparisons, evidence viewer, LangGraph analysis, and report export.
2. **Connected application:** authentication, enforced access controls, Supabase persistence/private original-file storage, Pinecone indexing, Google Drive OAuth/sync, durable runs, and deletion workflows.
3. **Advanced features:** optional reference retrieval, record-grounded Q&A, interoperability exports, and separately validated risk-model integrations.

The complete target still includes the original integrations; phases are delivery checkpoints, not permission to call an incomplete repository complete.

Provide explicit modes:

- `demo`: synthetic fixtures only, no credentials required, conspicuous demo label; fixture outputs must never masquerade as live AI analysis.
- `development`: local uploads and explicitly configured providers; unavailable features show actionable setup messages.
- `connected`: authenticated access, durable storage, access policies, and all required integration checks enabled.

Treat Streamlit Community Cloud as the default synthetic demonstration target. A real patient-data deployment needs a separately documented assessment of hosting, access, vendor processing, retention, and applicable organizational requirements. Do not claim healthcare compliance from architecture or a disclaimer alone.

## 47.2 Application identity, authorization, and tenant isolation

- Implement sign-in, sign-out, session expiry handling, and roles: administrator, reviewer, and viewer. Publish an operation-by-role permission matrix.
- Choose and document one supported app-authentication path. Prefer Supabase Auth for connected database access under user JWTs; if Streamlit OIDC is chosen, implement and test the identity-to-database authorization bridge. Do not assume an OIDC identity is a Supabase access token.
- Google Drive consent is a separate authorization flow from application login.
- Add `tenants`, `memberships`, and patient-access assignments. Add non-null `tenant_id` to tenant-owned records, including documents, observations, analyses, reviews, jobs, and exports.
- Enforce Supabase row-level security and storage policies for SELECT/INSERT/UPDATE/DELETE. Use composite constraints where necessary to prevent a child row referencing another tenant's patient or document.
- Separate `SUPABASE_PUBLISHABLE_KEY` from an optional server-only administrative secret. Replace the ambiguous `SUPABASE_KEY` examples in generated configuration. Normal patient operations must use the authenticated user's context; privileged background tasks require independently checked tenant scope.
- Derive tenant and allowed patient scope from verified identity and membership, never from an LLM or an untrusted widget/query parameter alone.
- Apply authorization to vector retrieval, source previews, report downloads, run/checkpoint access, and resume operations. A hidden navigation item is not access control.
- Test two users, two tenants, and unauthorized patients within the same tenant, including guessed resource IDs and expired/revoked membership.

## 47.3 Patient matching and extraction review

- Require an explicit patient selection or patient-creation step before import. Folder names and filenames are hints, not proof of identity.
- Show extracted identity fields alongside the selected patient. Quarantine mismatches and mixed-patient documents before indexing or analysis; do not automatically merge patients.
- Add a review queue for ambiguous dates/units, low-quality OCR, contradictory identity, and failed extraction validation.
- Provide source preview beside editable structured fields. Support accept, correct, reject, and reprocess actions with a reason.
- Preserve immutable raw extraction plus append-only revisions containing actor, timestamp, previous value, new value, reason, and source locator. Use optimistic concurrency to prevent one reviewer overwriting another.
- Distinguish `extracted`, `needs_review`, `accepted`, `corrected`, and `rejected`. Exclude unresolved observations from numerical analysis and risk inputs; show why they were excluded.
- User-supplied additions without source evidence must be labeled as user-entered, not source-verified. Never manufacture confidence scores; keep parser/OCR scores distinct from model assertions.
- A correction invalidates affected summaries, trends, risk results, and indexes. Show old reports as stale and allow explicit regeneration.

## 47.4 Clinical representation and comparison edge cases

Extend the example schemas and migrations consistently:

- Preserve original value strings, numeric comparator (`<`, `<=`, `>`, `>=`, exact), qualitative values, original units, normalized units, conversion rule/version, specimen, method, and reporting laboratory when present.
- Distinguish specimen/observation date, report date, upload time, date precision, timezone, and ambiguous date text. Never silently treat upload time as observation time.
- Retain source reference-range text, bounds/inclusivity, applicable population qualifiers, source abnormal flag, and separately computed comparison status. Missing or incompatible ranges produce `UNKNOWN`.
- Do not replace a censored result such as `<5` with an exact value of 5. Do not join trends across incompatible specimens, methods, or units without a documented comparability rule.
- Plot per-observation reference ranges rather than applying the latest range to all historical results. Return undefined percentage change when the prior value is zero; handle duplicates and same-day values explicitly.
- Store conditions/findings with assertion status: present, absent/negated, uncertain, historical, or family history, plus the subject. Do not turn family history or a ruled-out condition into an active patient diagnosis.
- Preserve medication status and evidence dates; a medication mentioned in an old document is not automatically current. Record allergies and source-reported reactions separately.
- Keep source-reported urgent/critical flags distinct from ordinary out-of-range comparisons. Do not invent urgency thresholds or imply a continuously monitored emergency service.
- Treat MRI/ECG/radiology report text as document evidence; direct interpretation of scan pixels or waveforms is outside this specification.
- For DOCX/TXT, use paragraph/table/line locators where pagination is unavailable. For PDF/images, retain page and optional bounding box. Never fabricate a page number.

## 47.5 Durable and bounded orchestration

- Use deterministic nodes for validation, arithmetic, access checks, and database operations. Use LLM calls only where language understanding or synthesis is needed; an agent module need not make an LLM call.
- Extend graph state with `tenant_id`, `actor_id`, `run_id`, `thread_id`, schema/workflow versions, immutable input-version manifest, node status, review decisions, budget usage, and sanitized error records.
- Use a persistent LangGraph checkpointer in connected mode, protected by the same access and retention rules as patient records. Document the supported managed database connection; in-memory persistence is demo-only.
- Define parallel branch reducers and an explicit join. Prevent concurrent nodes from overwriting each other's state. A required failed branch blocks finalization; optional failures produce a visibly partial report.
- Add bounded retries with backoff/jitter for transient failures, node timeouts, maximum graph steps, per-run token/cost limits, and cancellation checks. Validation and authorization failures must not trigger blind retries.
- Make writes and external side effects idempotent using tenant, document version, stage version, and operation/run keys. Resume must not duplicate observations, vectors, or completed external calls where a saved result is available.
- Human review must pause and resume a persisted run. Validate the resuming user's permission and reject stale decisions after input changes.
- Limit safety-critic regeneration attempts. On exhaustion or critic failure, return `blocked`/`needs_review` and safe structured findings, not an unchecked final narrative.
- Define run states: `queued`, `running`, `needs_review`, `succeeded`, `partial`, `failed`, `cancel_requested`, and `cancelled`.
- Connected long-running imports require a durable queue/worker or equivalent external execution service with leases/heartbeats. Streamlit polls persisted progress. Demo mode may process bounded batches synchronously; do not promise work continues after the UI process terminates.

## 47.6 Streamlit session behavior and usability

- Keep durable jobs, reviews, and reports outside `st.session_state`; it is UI state, not the system of record.
- Use forms and explicit submit actions for costly work. Persist an operation key so reruns, double clicks, or reconnections do not start duplicate imports or analyses.
- Show per-file and per-stage progress, failures, retry/cancel actions, and partial completion. Reopening a run should restore its persisted status.
- On patient change or logout, clear prior patient widgets, previews, draft answers, and selected evidence. Recheck authorization before every read/write.
- Cache only reusable thread-safe resources globally. Do not globally cache user-authenticated clients, Drive tokens, patient data, or mutable objects containing user identity.
- Add Review Queue, Analysis History, Downloads, and Data Controls screens. Show integration health and which features are available without exposing secrets.
- Provide keyboard-friendly controls, meaningful labels, readable contrast, text labels alongside colors, date/number locale clarity, and useful small-screen layouts.
- Define supported document/OCR languages. Detect unsupported language where feasible and surface limitations; do not silently translate clinical content or assume English OCR covers every report.

## 47.7 Original files, versioning, and cross-store consistency

- Local uploads need a durable private original-file store in connected mode, such as Supabase Storage, with access policies and short-lived authorized preview links. Store object identifiers in the database; never embed file bytes in vector metadata.
- Record source content hash, document version, parser/OCR version, extraction prompt/model version, schema version, embedding model/dimension, and index version.
- Pin each analysis to an immutable set of document/observation versions. Replaced or amended reports supersede earlier active versions without destroying historical provenance.
- Scope duplicate detection to tenant/patient. Support identical content from different sources without duplicating clinical observations while retaining source associations.
- Supabase is the authority for active versions. Use a transactional outbox plus retryable index jobs for Pinecone updates; do not imply database and vector writes form one atomic transaction.
- Build a new index version, verify completion, and then activate it. Reject stale/tombstoned evidence at read time, including when vector deletion is delayed.
- Drive sync must handle pagination, shared-drive capabilities where supported, inaccessible/deleted files, moved files, expired change cursors, and bounded recursive folder traversal. Display a preview/count before importing an entire folder.
- Revoked Drive access makes a source unavailable; imported-copy retention follows the documented policy. Never delete or modify the user's original Drive files as part of app cleanup.

## 47.8 Drive OAuth details

- Choose explicit scope behavior. Per-file `drive.file` access is not equivalent to browsing every existing Drive folder; broad read-only browsing requires an appropriate broader scope and documented verification requirements.
- Provide a capability-limited selected-file flow when broad browsing is unavailable. Do not label it as complete Drive browsing.
- Bind the OAuth callback to the authenticated app user with expiring, one-time state and use PKCE where supported. Validate configured redirect URIs and handle consent denial/revocation.
- Document a real callback route/service that works with the chosen deployment. Do not assume Streamlit's OIDC callback handles Drive authorization.
- Encrypt refresh tokens at rest, isolate them per user, avoid URLs/logs containing tokens, and support Disconnect Drive with token revocation/deletion handling.

## 47.9 Privacy, deletion, and untrusted document handling

- Before external processing, disclose which configured services receive originals, extracted text, embeddings, and model inputs. Record the user's import authorization and policy version.
- Define retention for originals, extracted text, vectors, reports, exports, checkpoints, tokens, temporary files, and backups. Provide patient/document export and deletion controls.
- Deletion immediately tombstones data and blocks retrieval, then removes derived records and external artifacts through retryable jobs. Track pending/failed/completed deletion and explain backup expiry limits; do not claim immediate backup erasure.
- Disable raw prompt/response tracing by default. Scrub PHI and secrets from logs, exceptions, telemetry, evaluation artifacts, and audit metadata.
- Treat document text, OCR, retrieved chunks, and filenames as untrusted data. Embedded instructions must not change system behavior, call tools, fetch URLs, reveal secrets, or alter patient scope.
- Validate file signatures as well as extension/MIME. Bound bytes, pages, pixels, decompressed archive size, OCR runtime, and batch size; handle encrypted/corrupt files explicitly.
- Isolate parsing and clean temporary files on success/failure. Do not execute document macros, scripts, attachments, or external relationships. Sanitize rendered HTML and exported spreadsheet-formula prefixes.

## 47.10 Reports, history, and optional Q&A

- Add downloadable PDF and versioned JSON reports plus CSV observation export. Generate them from the same structured report model used by the UI.
- Include source citations/locators, analysis time, input versions, review status, unavailable sections, and limitations. Verify exported pagination and tables with representative long reports.
- Let users compare report versions and see why regeneration is needed. Label reports as draft, reviewed, stale, or blocked; do not export a rejected narrative as a final report.
- Optional patient-record Q&A must inherit patient/tenant authorization, citation checks, and abstention rules. Clear conversation scope on patient change and clearly distinguish general references from patient evidence.
- Optional future FHIR export should use an explicitly selected version/profile and validation; do not claim interoperability merely because JSON is produced.

## 47.11 Configuration and repository extensions

Add modules/packages for authentication, extraction review, original-file storage, durable jobs, graph checkpoint access, outbox reconciliation, report export, and retention/deletion. Extend the section 5 tree and relevant migrations; avoid parallel implementations of the same service.

Add tables or equivalent durable structures for memberships, patient access, document versions, observation revisions, review decisions, jobs, index/outbox operations, and deletion requests. Add foreign keys, uniqueness constraints, status validation, and access policies.

Extend `.env.example`, Streamlit secret examples, and settings validation with:

```text
APP_MODE=demo
AUTH_PROVIDER=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_ADMIN_SECRET_KEY=
PRIVATE_DOCUMENT_BUCKET=
CHECKPOINT_DATABASE_URL=
TOKEN_ENCRYPTION_KEY=
MAX_UPLOAD_MB=20
MAX_PAGES_PER_DOCUMENT=100
MAX_FILES_PER_BATCH=20
MAX_RUN_TOKENS=30000
MAX_RUN_COST_USD=1.00
RUN_TIMEOUT_SECONDS=300
RETENTION_DAYS=
ENABLE_RAW_TRACING=false
```

Numeric values above are initial engineering defaults, not measured platform limits. Require retention configuration in connected mode. Require only the secrets needed for enabled features; administrative secrets must never be available to normal user clients. Enforce cost caps using configured provider prices where available, and always enforce token/call limits even if price estimation is unavailable.

Pin a tested Python/dependency combination and document it. Check compatibility among Streamlit, LangGraph, LangChain, Pydantic, provider SDKs, and the checkpoint adapter. Keep heavy evaluation/ML dependencies optional for the demo runtime. Record dependency/license review, particularly document parsers and clinical terminology resources; the project's MIT license does not override dependency or terminology licenses.

## 47.12 Additional release acceptance checks

These supplement section 42. Tests must verify behavior, not merely that modules exist.

| Scenario | Required result |
| --- | --- |
| Start with no external keys | Synthetic demo loads; no invented live AI results |
| Two tenants request the same resource ID | Unauthorized database, vector, preview, checkpoint, and export access is denied |
| Wrong-patient document or mixed identities | Quarantined before indexing/analysis |
| Source says `<5`, negates a condition, or records family history | Semantics remain intact; no false exact value or active diagnosis |
| Missing range, incompatible units, ambiguous date, zero baseline | Explicit unknown/exclusion/undefined result; no guessed interpretation |
| Reviewer corrects an observation | Immutable revision saved; affected reports marked stale |
| Browser rerun, double submit, process restart, or transient timeout | No duplicate side effects; durable run can resume |
| One parallel branch fails or critic times out | Partial/blocked result; unchecked final report withheld |
| Document contains instructions to reveal secrets or change patient | Instructions ignored; no unauthorized action or cross-patient retrieval |
| Supabase succeeds and Pinecone fails | Retryable pending index state; no false ready status |
| Document replaced, deleted, or access revoked | Retrieval respects active version and authorization; cleanup status is visible |
| Oversized/corrupt file or unsupported OCR language | Bounded, actionable failure without crashing the batch |
| Long report exported | Readable PDF and valid JSON/CSV with matching values and citations |
| Live integration unavailable | Mark the integration test skipped/unverified with its reason; mocks are not live verification |

Use Streamlit AppTest for appropriate UI state transitions and browser-level tests for OAuth callbacks/downloads where needed. Add CI for unit tests, import/compile checks, schema/migration tests, and secret scanning. Use synthetic fixtures only.

Create a versioned evaluation set containing expected values, units, dates, assertion status, and evidence locators. Define release thresholds before evaluation, report denominators and failures, and distinguish deterministic checks, human assessment, and optional LLM judging. Do not substitute an LLM judge for access-control tests or clinical validation.

## 47.13 Official implementation references

Checked during the specification review; recheck against the dependency versions selected at implementation time:

- [Streamlit authentication and its distinction from authorization](https://docs.streamlit.io/develop/concepts/connections/authentication).
- [Streamlit session state and connection lifecycle](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state).
- [Supabase row-level security and privileged-key behavior](https://supabase.com/docs/guides/database/postgres/row-level-security).
- [Google Drive scopes and access/verification tradeoffs](https://developers.google.com/workspace/drive/api/guides/api-specific-auth).
- [LangGraph persistence and checkpointing](https://docs.langchain.com/oss/python/langgraph/persistence).

---

# 48. FINAL COMMAND

Now generate the **entire HealthLens AI repository** according to every requirement above.

Do not return only an architecture or explanation.

Generate the actual complete project files and code.

The final result must be structured so it can be pushed to GitHub and deployed to **Streamlit Community Cloud** after configuring:
- Supabase;
- Pinecone;
- selected LLM/embedding provider;
- Google Drive OAuth;
- Streamlit secrets.

Ensure the generated repository is internally consistent, imports correctly, has tests, contains no secrets, uses synthetic data, and follows the healthcare safety requirements above.
