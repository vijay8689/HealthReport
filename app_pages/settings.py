import streamlit as st

from healthlens.models import Patient
from healthlens.workspace import Workspace
from ui.components import heading, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Make the workspace yours.", "Control motion, understand data handling, and manage demonstration records.", "WORKSPACE SETTINGS")
with st.container(border=True):
    st.subheader("Patient workspaces")
    st.caption("Create a local patient workspace. This does not create a Supabase login.")
    with st.form("add_patient_workspace"):
        new_patient_id = st.text_input("Patient ID", placeholder="P-0002")
        new_patient_name = st.text_input("Patient name")
        new_patient_age = st.number_input("Age", min_value=0, max_value=130, value=0, step=1)
        new_patient_sex = st.selectbox("Sex", ["Not recorded", "Female", "Male", "Intersex"])
        add_patient = st.form_submit_button("Add patient workspace", type="primary")
    if add_patient:
        normalized_id = new_patient_id.strip()
        normalized_name = new_patient_name.strip()
        existing_ids = {patient.id for patient in ws.patients}
        if not normalized_id or not normalized_name:
            st.error("Patient ID and name are required.")
        elif normalized_id in existing_ids:
            st.error("That patient ID already exists.")
        else:
            initials = "".join(part[0] for part in normalized_name.split()[:2]).upper()
            ws.patients.append(Patient(
                id=normalized_id,
                name=normalized_name,
                initials=initials or "P",
                age=new_patient_age or None,
                sex=new_patient_sex,
                description="Local patient workspace",
            ))
            st.session_state["reset_patient"] = normalized_id
            st.rerun()
with st.container(border=True):
    st.subheader("Appearance & accessibility")
    st.toggle("Reduce floating animations", key="reduce_motion")
    st.caption("Your operating system's reduced-motion preference is also respected automatically.")
with st.container(border=True):
    st.subheader("Data & privacy")
    st.write("This release stores synthetic records in the current Streamlit session. Refreshing the browser or restarting the server can reset the workspace. Export anything you want to keep.")
    st.caption("No documents, prompts, or extracted values are sent to cloud databases or LLM providers. Parser/OCR availability depends on your local installation. This is not a production patient-record system.")
    docs = ws.docs(pid)
    if docs:
        with st.expander("Delete a document and its derived data"):
            chosen = st.selectbox("Document to delete", [d.id for d in docs], format_func=lambda x:next(d.name for d in docs if d.id == x), key=f"delete_doc_{pid}")
            confirm = st.checkbox("Delete this document, its observations, review history, and patient analysis reports from this demo session.")
            if st.button("Delete selected document", disabled=not confirm, icon=":material/delete:"):
                ws.remove_document(pid, chosen)
                st.rerun()
    with st.expander("Reset demo workspace"):
        confirm_reset = st.checkbox("Restore the synthetic sample data and remove all session imports and reports.")
        if st.button("Reset demonstration", disabled=not confirm_reset, icon=":material/restart_alt:"):
            st.session_state.workspace = Workspace()
            # Patient selection widget is owned by the entry point; set via callback next rerun.
            st.session_state["reset_patient"] = True
            st.rerun()

