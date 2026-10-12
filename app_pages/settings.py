import streamlit as st

from ui.components import heading, patient_id, workspace
from ui.patient_form import add_patient_form

ws, pid = workspace(), patient_id()
heading("Make the workspace yours.", "Control motion, understand data handling, and manage demonstration records.", "WORKSPACE SETTINGS")
try:
    secrets = st.secrets.to_dict()
except FileNotFoundError:
    secrets = {}
add_patient_form(ws, secrets, st.session_state.get("auth_session"))
with st.container(border=True):
    st.subheader("Appearance & accessibility")
    st.toggle("Reduce floating animations", key="reduce_motion")
    st.caption("Your operating system's reduced-motion preference is also respected automatically.")
with st.container(border=True):
    st.subheader("Data & privacy")
    if not st.session_state.get("auth_session"):
        st.caption("Guest mode contains synthetic dummy data only. Login or Sign up opens your private workspace.")
    st.write("Patient profiles are stored in Supabase under your account and only your profiles appear in the patient dropdown. Use Refresh patients to fetch newly added profiles. Documents, extracted values, and reports remain in the current Streamlit session.")
    st.caption("Imported document text is sent to Pinecone's embedding model and stored as vector records when configured. Clearing session data does not delete Supabase profiles or Pinecone vectors. Original files and derived analysis reports remain session-local.")
    docs = ws.docs(pid)
    if docs:
        with st.expander("Delete a document and its derived data"):
            chosen = st.selectbox("Document to delete", [d.id for d in docs], format_func=lambda x:next(d.name for d in docs if d.id == x), key=f"delete_doc_{pid}")
            confirm = st.checkbox("Delete this document, its observations, discharge sections, review history, and patient analysis reports from this demo session.")
            if st.button("Delete selected document", disabled=not confirm, icon=":material/delete:"):
                ws.remove_document(pid, chosen)
                st.rerun()
    with st.expander("Clear session workspace"):
        confirm_reset = st.checkbox("Remove your session imports and reports. Saved patient profiles and cloud records remain.")
        if st.button("Clear session data", disabled=not confirm_reset, icon=":material/restart_alt:"):
            # The entry point recreates the appropriate guest/private workspace.
            st.session_state.workspace = None
            # Patient selection widget is owned by the entry point; set via callback next rerun.
            st.session_state.pop("patients_loaded_at", None)
            st.session_state["reset_patient"] = True
            st.rerun()
