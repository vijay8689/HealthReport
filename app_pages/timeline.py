import streamlit as st

from healthlens.models import Patient, uid
from ui.components import e, heading, html, patient_id, patient_snapshot, workspace

ws, pid = workspace(), patient_id()
heading("Every record has a place in the story.", "Explore the source documents behind your patient's longitudinal profile.", "PATIENT TIMELINE")
left, right = st.columns([2, 1])
with left:
    docs = ws.docs(pid)
    if not docs:
        st.info("This patient has no documents yet. Upload a synthetic report to begin.")
    for doc in docs:
        count = len([o for o in ws.obs(pid) if o.document_id == doc.id])
        with st.container(border=True):
            html(f'<div class="eyebrow">{e(doc.date or "Date unavailable")}</div><div class="insight"><b>{e(doc.name)}</b><p>{count} extracted observations · {e(doc.source)} · {e(doc.status)}</p></div>')
            with st.expander("View source record"):
                for page in doc.pages:
                    st.code(page["text"], language=None, wrap_lines=True)
with right:
    with st.container(border=True):
        patient_snapshot(ws.patient(pid), ws)
    with st.expander("Create a synthetic patient"):
        with st.form("new_patient"):
            name = st.text_input("Display name", max_chars=80)
            age = st.number_input("Age", min_value=0, max_value=120, value=35)
            sex = st.selectbox("Sex recorded in source", ["Not recorded", "Female", "Male", "Other"])
            add = st.form_submit_button("Create profile", icon=":material/person_add:")
        if add:
            if not name.strip():
                st.error("Enter a synthetic display name.")
            else:
                new_id = "HL-" + uid()[:6].upper()
                ws.patients.append(Patient(id=new_id, name=name.strip(), initials="".join(w[0] for w in name.split()[:2]).upper(), age=age, sex=sex))
                st.success(f"Created {new_id}. Select the new patient from the menu above.")

