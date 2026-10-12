import streamlit as st
from healthlens.models import Patient
from healthlens.supabase import PatientSaveError, save_patient


def add_patient_form(ws, secrets, session):
    if not session:
        st.info("Log in or sign up to add your own patients. Guest mode shows synthetic dummy data.")
        return
    with st.container(border=True):
        st.subheader("Patient workspaces")
        st.caption("Save patient details to Supabase and open their workspace. These patients belong only to your signed-in account.")
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
                    with st.spinner("Saving patient to Supabase..."):
                        save_patient(patient, secrets, session=session)
                except PatientSaveError as exc:
                    st.error(str(exc))
                else:
                    ws.patients.append(patient)
                    st.session_state["patient_saved"] = True
                    st.session_state.pop("patients_loaded_at", None)
                    st.session_state["reset_patient"] = normalized_id
                    st.rerun()
