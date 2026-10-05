import streamlit as st

from healthlens.models import Patient
from healthlens.supabase import PatientSaveError, save_patient
from healthlens.workspace import Workspace
from ui.components import heading, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Make the workspace yours.", "Control motion, understand data handling, and manage demonstration records.", "WORKSPACE SETTINGS")
with st.container(border=True):
    st.subheader("Patient workspaces")
    st.caption("Save patient details to Supabase and open their workspace. This does not create a Supabase login.")
    if st.session_state.pop("patient_saved", False):
        st.success("Patient details saved to Supabase. Workspace added.")
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
            patient = Patient(
                id=normalized_id,
                name=normalized_name,
                initials=initials or "P",
                age=new_patient_age,
                sex=new_patient_sex,
                description="Cloud patient workspace",
            )
            try:
                try:
                    secrets = st.secrets.to_dict()
                except FileNotFoundError:
                    secrets = {}
                with st.spinner("Saving patient to Supabase..."):
                    save_patient(patient, secrets)
            except PatientSaveError as exc:
                st.error(str(exc))
            else:
                ws.patients.append(patient)
                st.session_state["patient_saved"] = True
                st.session_state["reset_patient"] = normalized_id
                st.rerun()
with st.container(border=True):
    st.subheader("Appearance & accessibility")
    st.toggle("Reduce floating animations", key="reduce_motion")
    st.caption("Your operating system's reduced-motion preference is also respected automatically.")
with st.container(border=True):
    st.subheader("Data & privacy")
    st.write("New patient profiles are stored in Supabase and loaded into the patient dropdown when you open the app. Use Refresh patients to fetch newly added profiles. Documents, extracted values, and reports remain in the current Streamlit session.")
    st.caption("Imported document text is sent to Pinecone's embedding model and stored as vector records when configured. Resetting this demo does not delete Supabase profiles or Pinecone vectors. Original files and derived analysis reports remain session-local.")
    docs = ws.docs(pid)
    if docs:
        with st.expander("Delete a document and its derived data"):
            chosen = st.selectbox("Document to delete", [d.id for d in docs], format_func=lambda x:next(d.name for d in docs if d.id == x), key=f"delete_doc_{pid}")
            confirm = st.checkbox("Delete this document, its observations, discharge sections, review history, and patient analysis reports from this demo session.")
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
