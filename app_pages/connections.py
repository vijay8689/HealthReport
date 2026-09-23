import streamlit as st

from ui.components import heading, html

heading("A workspace built to connect.", "See what's available in this release and what a connected deployment needs.", "INTEGRATIONS")
openai_key = str(st.secrets.get("OPENAI_API_KEY", ""))
llm_status = "Configured" if openai_key and not openai_key.startswith("your-") else "Not connected"
llm_description = ("An OpenAI API key is configured, but this demo keeps external LLM calls disabled."
                   if llm_status == "Configured" else
                   "The demo uses deterministic source-grounded summaries and does not call an external language model.")
pinecone_key = str(st.secrets.get("PINECONE_API_KEY", ""))
pinecone_index = str(st.secrets.get("PINECONE_INDEX_NAME", ""))
pinecone_configured = (pinecone_key and not pinecone_key.startswith("your-")) and (pinecone_index and not pinecone_index.startswith("your-"))
pinecone_status = "Configured" if pinecone_configured else "Not connected"
pinecone_description = ("Pinecone credentials and index are configured, but semantic search is not enabled in this demo."
                        if pinecone_status == "Configured" else
                        "Semantic evidence search requires a Pinecone API key and index configuration.")
cards = [
    ("▤", "Local document upload", "Available", "Import synthetic PDF, DOCX, TXT, and image reports. Review extracted text and supported laboratory rows."),
    ("◈", "LangGraph", "Available", "Intake, parallel trend/range/conflict checks, evidence mapping, and a final evidence integrity check."),
    ("△", "Google Drive", "Not connected", "OAuth folder browsing and incremental sync belong to the connected deployment phase. This release does not request Drive access."),
    ("ϟ", "Supabase", "Not connected", "Authenticated patient storage, private files, and row-level access policies are required before real patient-data deployment."),
    ("⌘", "Pinecone", pinecone_status, pinecone_description),
    ("✧", "LLM provider", llm_status, llm_description),
]
for start in range(0, len(cards), 2):
    columns = st.columns(2)
    for column, (symbol, title, status, description) in zip(columns, cards[start:start+2]):
        with column:
            html(f'<div class="connection"><div style="display:flex;justify-content:space-between"><span class="vendor">{symbol}</span><span class="small-pill{(" amber" if status != "Available" else "")}">{status}</span></div><h3>{title}</h3><p>{description}</p></div>')
st.info("This is the functional demo website, not an authenticated enterprise deployment. Adding API keys alone does not enable the cloud services shown above.", icon=":material/info:")
with st.expander("Connected deployment checklist"):
    st.markdown("- Application authentication and tenant/patient authorization\n- Supabase migrations and tested row-level policies\n- Private original-file storage and retention/deletion jobs\n- Google OAuth callback, encrypted token storage, and scope verification\n- Scoped Pinecone indexing and reconciliation\n- Durable workers/checkpoints and per-run budgets\n- Vendor data-processing review and integration tests")

