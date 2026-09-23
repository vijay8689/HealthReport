# Demo security boundaries

This application is for synthetic demonstration data only. No authentication, tenant database, cloud storage, token vault, durable queue, or real patient-data production deployment is provided.

The session repository is isolated by Streamlit browser session; it is not an authorization mechanism suitable for healthcare records. There are no externally callable data endpoints beyond Streamlit's normal session transport. Do not disable Streamlit's XSRF or CORS protection.

Uploaded content is parsed as data. No file macros, instructions, external links, or attachments are executed. Output HTML uses escaping. PDF export escapes text; CSV neutralizes formula-leading strings. Parsers enforce signature checks, byte/page/text/pixel/archive limits. English OCR has per-image timeouts and a five-scanned-page demo cap. Parsing runs in the Streamlit process; process sandboxing and total-job time limits are future connected-deployment work.

Patient IDs must match the selected synthetic profile before extraction. All observations sent to the graph are checked against that patient. Missing identifiers quarantine the file. This is a conservative demo rule, not medical identity verification.

Original evidence is immutable during review. Changes create revisions and invalidate previous analyses. Deleting a document also removes observations, revisions, and patient analysis reports from the session. No app-managed backups are created.

No raw clinical content is explicitly logged by the app, and no external tracing or provider calls are configured. Avoid enabling raw third-party LangChain tracing through environment settings. No private data is globally cached. Use synthetic test artifacts only.

Before a connected deployment, implement and test every authorization, retention, encrypted token, storage, worker, and external-provider control in section 47 of the specification. An attractive interface or application disclaimer does not establish legal or healthcare compliance.

