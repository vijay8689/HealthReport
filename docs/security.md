# Demo security boundaries

This application has no user authentication or tenant isolation. Newly added patient profiles are inserted into Supabase using a server-only API key; documents and derived data remain session-local. No token vault, durable queue, or real patient-data production deployment is provided. Restrict access to the Streamlit server because its trusted key permits inserts for every app visitor. See README.md for Supabase configuration.

The session repository is isolated by Streamlit browser session; it is not an authorization mechanism suitable for healthcare records. There are no externally callable data endpoints beyond Streamlit's normal session transport. Do not disable Streamlit's XSRF or CORS protection.

Uploaded content is parsed as data. No file macros, instructions, external links, or attachments are executed. Output HTML uses escaping. PDF export escapes text; CSV neutralizes formula-leading strings. Parsers enforce signature checks, byte/page/text/pixel/archive limits. English OCR has per-image timeouts and a five-scanned-page demo cap. Parsing runs in the Streamlit process; process sandboxing and total-job time limits are future connected-deployment work.

The report patient name must match the selected profile before extraction. Matching ignores case, extra whitespace, and common titles, including titles without a following space. A profile may use a first name or a prefix of the full report name; unrelated and multiple names are excluded. Source patient IDs are not required and do not need to match. Missing or conflicting names quarantine the file. Observations retain the selected internal patient ID, and the graph checks their patient scope. This is a demo association rule, not medical identity verification.

Original evidence is immutable during review. Changes create revisions and invalidate previous analyses. Deleting a document also removes observations, revisions, and patient analysis reports from the session. No app-managed backups are created.

No raw clinical content is explicitly logged by the app, and no external tracing or provider calls are configured. Avoid enabling raw third-party LangChain tracing through environment settings. No private data is globally cached. Use synthetic test artifacts only.

Before a connected deployment, implement and test every authorization, retention, encrypted token, storage, worker, and external-provider control in section 47 of the specification. An attractive interface or application disclaimer does not establish legal or healthcare compliance.

