"""Streamlit entry point. Run: python -m streamlit run app.py."""
import os
import time

import streamlit as st

from healthlens.workspace import Workspace
from healthlens.supabase import PatientSaveError, list_patients
from healthlens.pinecone_db import PineconeConnectionError, load_patient_records
from ui.components import e, footer, html, load_styles, topbar

st.set_page_config(page_title="HealthLens AI · Clinical intelligence", page_icon=":material/ecg_heart:", layout="wide", initial_sidebar_state="expanded")
load_styles()
if os.getenv("APP_MODE", "demo") != "demo":
    st.error("This release supports synthetic demo mode only. Connected patient-data deployment is not enabled.")
    st.stop()

st.session_state.workspace = Workspace.from_session(st.session_state.get("workspace"))
st.session_state.workspace.ensure_demo_records()
st.session_state.workspace.activate_pending_uploads()
try:
    cloud_secrets = st.secrets.to_dict()
except FileNotFoundError:
    cloud_secrets = {}
cloud_configured = bool((os.getenv("SUPABASE_URL") or cloud_secrets.get("SUPABASE_URL"))
                        and (os.getenv("SUPABASE_KEY") or cloud_secrets.get("SUPABASE_KEY")))
if not cloud_configured:
    st.session_state["supabase_available"] = False
# Keep patient data and refresh timing isolated to this browser session.
if cloud_configured and (time.monotonic() - st.session_state.get("patients_loaded_at", 0) >= 60
                         or st.session_state.pop("refresh_cloud_patients", False)):
    try:
        cloud_patients = list_patients(cloud_secrets)
    except PatientSaveError as exc:
        st.session_state["supabase_available"] = False
        st.session_state["patients_load_error"] = str(exc)
    else:
        st.session_state["supabase_available"] = True
        by_id = {p.id: p for p in st.session_state.workspace.patients}
        by_id.update({p.id: p for p in cloud_patients})
        st.session_state.workspace.patients = list(by_id.values())
        st.session_state.pop("patients_load_error", None)
    st.session_state["patients_loaded_at"] = time.monotonic()
if cloud_configured and st.session_state.get("patients_load_error"):
    st.warning(st.session_state["patients_load_error"])
if not st.session_state.workspace.patients:
    st.info("No patient records are available. Import or connect a patient workspace to begin.")
    st.stop()
patient_ids = {patient.id for patient in st.session_state.workspace.patients}
requested_patient = st.session_state.pop("pending_patient_id", None)
if requested_patient is None:
    requested_patient = st.session_state.pop("reset_patient", None)
if requested_patient is True:
    selected_patient = st.session_state.workspace.patients[0].id
elif requested_patient is not None and requested_patient in patient_ids:
    selected_patient = requested_patient
else:
    selected_patient = st.session_state.get("patient_id")
    if selected_patient not in patient_ids:
        selected_patient = st.session_state.workspace.patients[0].id
if requested_patient is not None or st.session_state.get("patient_id") not in patient_ids:
    st.session_state.patient_id = selected_patient
st.session_state.setdefault("reduce_motion", False)
if st.session_state.reduce_motion:
    html('<style>*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}.hero:hover .orb-scene,.stat:hover,.doc-row:hover,.stage:hover,.connection:hover,.hero-tags span:hover,button:hover{transform:none!important}</style>')

pages = [
    st.Page("app_pages/overview.py", title="Overview", icon=":material/space_dashboard:", default=True),
    st.Page("app_pages/documents.py", title="Documents", icon=":material/folder_open:"),
    st.Page("app_pages/discharge.py", title="Discharge summary", icon=":material/clinical_notes:"),
    st.Page("app_pages/trends.py", title="Lab trends", icon=":material/monitoring:"),
    st.Page("app_pages/analysis.py", title="AI analysis", icon=":material/auto_awesome:"),
    st.Page("app_pages/evidence.py", title="Evidence & review", icon=":material/fact_check:"),
    st.Page("app_pages/timeline.py", title="Patient timeline", icon=":material/timeline:"),
    st.Page("app_pages/reports.py", title="Reports", icon=":material/article:"),
    st.Page("app_pages/connections.py", title="Connections", icon=":material/hub:"),
    st.Page("app_pages/settings.py", title="Settings", icon=":material/tune:"),
]
nav = st.navigation(pages, position="hidden")
with st.sidebar:
    html('<div class="brand"><div class="brand-icon">+</div><div><div class="brand-name">HealthLens<span>AI</span></div><div class="brand-sub">Clinical intelligence</div></div></div><div class="workspace-tag">◈ &nbsp; <b>Personal workspace</b> &nbsp; ⌄</div><div class="nav-label">WORKSPACE</div>')
    for page in pages[:-2]:
        st.page_link(page)
    html('<div class="nav-label">MANAGE</div>')
    for page in pages[-2:]:
        st.page_link(page)
    html('<div class="sidebar-note"><div class="eyebrow">BUILT AROUND EVIDENCE</div><h4>Every insight. A source.</h4><p>Explore connected records with a transparent, source-linked workflow.</p></div>')
    active_profile = st.session_state.workspace.patient(selected_patient)
    if selected_patient == "DUMMY-0001":
        profile_avatar, profile_title, profile_detail = "HL", "Demo workspace", "Synthetic data only"
    else:
        profile_avatar, profile_title, profile_detail = active_profile.initials, "Patient Data", active_profile.name
    html(
        f'<div class="sidebar-profile"><div class="avatar">{e(profile_avatar)}</div>'
        f'<div>{e(profile_title)}<br><span style="font-size:10px;color:#9ab0bd">'
        f'{e(profile_detail)}</span></div></div>'
    )

topbar(nav.title)
left, right = st.columns([2.4, 1], vertical_alignment="center")
with left:
    html('<div class="eyebrow">CLINICAL DOCUMENT INTELLIGENCE</div>')
with right:
    if cloud_configured:
        st.button("Refresh patients", icon=":material/refresh:",
                  on_click=lambda: st.session_state.__setitem__("refresh_cloud_patients", True))
    patients = st.session_state.workspace.patients
    ids = [p.id for p in patients]
    selected = st.selectbox("Active patient", ids, format_func=lambda pid: next(p.name + " · " + pid for p in patients if p.id == pid), key="patient_id", label_visibility="collapsed")
pinecone_configured = bool((os.getenv("PINECONE_API_KEY") or cloud_secrets.get("PINECONE_API_KEY"))
                           and (os.getenv("PINECONE_INDEX_NAME") or cloud_secrets.get("PINECONE_INDEX_NAME")))
if pinecone_configured:
    refresh_records = st.button("Refresh patient records", icon=":material/cloud_download:")
    loaded_at = st.session_state.setdefault("pinecone_patient_loaded_at", {})
    errors = st.session_state.setdefault("pinecone_patient_errors", {})
    if refresh_records or time.monotonic() - loaded_at.get(selected, 0) >= 60:
        try:
            with st.spinner("Loading selected patient's Pinecone records..."):
                records = load_patient_records(selected, cloud_secrets)
                st.session_state.workspace.restore_cloud_records(selected, records)
        except (PineconeConnectionError, ValueError) as exc:
            errors[selected] = str(exc)
        else:
            errors.pop(selected, None)
        loaded_at[selected] = time.monotonic()
    if selected in errors:
        st.warning(errors[selected])
nav.run()
footer()
