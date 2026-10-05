import streamlit as st
import time

from healthlens.pinecone_db import PineconeConnectionError, check_connection

from ui.components import heading, html

heading("A workspace built to connect.", "See what's available in this release and what a connected deployment needs.", "INTEGRATIONS")
openai_key = str(st.secrets.get("OPENAI_API_KEY", ""))
llm_status = "Configured" if openai_key and not openai_key.startswith("your-") else "Not connected"
llm_description = ("An OpenAI API key is configured, but this demo keeps external LLM calls disabled."
                   if llm_status == "Configured" else
                   "The demo uses deterministic source-grounded summaries and does not call an external language model.")
retry_pinecone = st.button("Test Pinecone connection", icon=":material/refresh:")
if retry_pinecone or time.monotonic() - st.session_state.get("pinecone_checked_at", 0) >= 60:
    try:
        with st.spinner("Checking Pinecone cloud connection..."):
            st.session_state["pinecone_info"] = check_connection(st.secrets.to_dict())
        st.session_state.pop("pinecone_error", None)
    except PineconeConnectionError as exc:
        st.session_state.pop("pinecone_info", None)
        st.session_state["pinecone_error"] = str(exc)
    st.session_state["pinecone_checked_at"] = time.monotonic()
pinecone_info = st.session_state.get("pinecone_info")
pinecone_status = "Available" if pinecone_info else "Not connected"
pinecone_description = ("Connected to Pinecone cloud vector DB. Imported document chunks are embedded and stored in patient namespaces. Sync existing documents from the document library. Semantic search is not yet enabled."
                        if pinecone_info else "Configure a Pinecone API key and index name, then test the connection.")
if st.session_state.get("pinecone_error"):
    st.warning(st.session_state["pinecone_error"])
if pinecone_info:
    st.caption(f"Pinecone vectors: {pinecone_info['vector_count']} · Dimensions: {pinecone_info['dimension'] or 'N/A'} · Metric: {pinecone_info['metric'] or 'N/A'}")
supabase_status = "Available" if st.session_state.get("supabase_available", False) else "Not connected"
supabase_description = (
    "Connected to Supabase DB. Patient profiles are saved in the cloud and loaded into the patient dropdown."
    if supabase_status == "Available" else
    "Supabase DB is unavailable. Check the server URL, API key, patients table, and network access, then use Refresh patients."
)
cards = [
    ("▤", "Local document upload", "Available", "Import synthetic PDF, DOCX, TXT, and image reports. Review extracted text and supported laboratory rows."),
    ("◈", "LangGraph", "Available", "Intake, parallel trend/range/conflict checks, evidence mapping, and a final evidence integrity check."),
    ("△", "Google Drive", "Not connected", "OAuth folder browsing and incremental sync belong to the connected deployment phase. This release does not request Drive access."),
    ("ϟ", "Supabase", supabase_status, supabase_description),
    ("⌘", "Pinecone", pinecone_status, pinecone_description),
    ("✧", "LLM provider", llm_status, llm_description),
]
for start in range(0, len(cards), 2):
    columns = st.columns(2)
    for column, (symbol, title, status, description) in zip(columns, cards[start:start+2]):
        with column:
            html(f'<div class="connection"><div style="display:flex;justify-content:space-between"><span class="vendor">{symbol}</span><span class="small-pill{(" amber" if status != "Available" else "")}">{status}</span></div><h3>{title}</h3><p>{description}</p></div>')
st.info("Supabase stores patient profiles when connected. Documents and reports remain session-local. Other configured services need their integrations enabled.", icon=":material/info:")
with st.expander("Connected deployment checklist"):
    st.markdown("- Application authentication and tenant/patient authorization\n- Supabase migrations and tested row-level policies\n- Private original-file storage and retention/deletion jobs\n- Google OAuth callback, encrypted token storage, and scope verification\n- Scoped Pinecone indexing and reconciliation\n- Durable workers/checkpoints and per-run budgets\n- Vendor data-processing review and integration tests")
