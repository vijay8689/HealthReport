"""Shared Streamlit feedback for explicit and automatic document indexing."""
import os
import streamlit as st
from healthlens.pinecone_db import PineconeConnectionError, index_document


def sync_document(document):
    try:
        secrets = st.secrets.to_dict()
    except FileNotFoundError:
        secrets = {}
    if not (os.getenv("PINECONE_API_KEY") or secrets.get("PINECONE_API_KEY")):
        st.info("Pinecone is not configured. Document text remains in this session.")
        return
    try:
        with st.spinner(f"Saving {document.name} chunks to Pinecone..."):
            observations = [o for o in st.session_state.workspace.obs(document.patient_id) if o.document_id == document.id]
            result = index_document(document, secrets, observations=observations)
    except PineconeConnectionError as exc:
        st.error(f"{document.name}: {exc}")
    else:
        st.success(f"{document.name}: {result['chunk_count']} chunks saved to Pinecone in namespace {result['namespace']}.")
        st.session_state.pop("pinecone_checked_at", None)
        st.session_state.setdefault("pinecone_patient_loaded_at", {}).pop(document.patient_id, None)
