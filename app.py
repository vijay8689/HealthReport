"""Streamlit entry point. Run: python -m streamlit run app.py."""
import os

import streamlit as st

from healthlens.workspace import Workspace
from ui.components import e, footer, html, load_styles, topbar

st.set_page_config(page_title="HealthLens AI · Clinical intelligence", page_icon=":material/ecg_heart:", layout="wide", initial_sidebar_state="expanded")
load_styles()
if os.getenv("APP_MODE", "demo") != "demo":
    st.error("This release supports synthetic demo mode only. Connected patient-data deployment is not enabled.")
    st.stop()

if "workspace" not in st.session_state:
    st.session_state.workspace = Workspace()
st.session_state.workspace.ensure_demo_records()
st.session_state.workspace.activate_pending_uploads()
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
    for page in pages[:7]:
        st.page_link(page)
    html('<div class="nav-label">MANAGE</div>')
    for page in pages[7:]:
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
    patients = st.session_state.workspace.patients
    ids = [p.id for p in patients]
    selected = st.selectbox("Active patient", ids, format_func=lambda pid: next(p.name + " · " + pid for p in patients if p.id == pid), key="patient_id", label_visibility="collapsed")
nav.run()
footer()
