"""Small escaped HTML components and shared native Streamlit controls."""
from datetime import date
from html import escape
from pathlib import Path

import streamlit as st

from healthlens.analytics import comparison, latest


def html(value):
    # Avoid Streamlit's lazy-loaded Html.* JavaScript chunk. Browsers can keep
    # an obsolete hashed chunk URL across a Streamlit restart or upgrade.
    st.markdown(value, unsafe_allow_html=True)


def e(value):
    return escape(str(value))


def load_styles():
    html(f"<style>{Path('ui/styles.css').read_text(encoding='utf-8')}</style>")


def heading(title, subtitle, eyebrow="YOUR HEALTH, IN FOCUS"):
    html(f'<div class="eyebrow">{e(eyebrow)}</div><div class="heading">{e(title)}</div><p class="subheading">{e(subtitle)}</p>')


def panel_title(title, subtitle=""):
    html(f'<div class="panel-title">{e(title)}</div><div class="panel-caption">{e(subtitle)}</div>')


def topbar(title):
    html(f'<div class="topbar"><div>Workspace &nbsp; / &nbsp; <strong>{e(title)}</strong></div><div class="topbar-right"><span class="date-label">{date.today().strftime("%d %b %Y")}</span><span class="demo-pill"><i class="dot"></i> Synthetic demo</span><span class="avatar" style="width:30px;height:30px">HL</span></div></div>')


def hero():
    html('''<section class="hero"><div class="hero-copy"><div class="eyebrow"><span class="dot"></span> CLARITY STARTS WITH YOUR RECORDS</div><h1>A clearer picture.<br><em>A healthier perspective.</em></h1><p>Turn complex health reports into connected insights.<br>Every observation grounded in your source documents.</p><div class="hero-tags"><span>◈ &nbsp; Evidence first</span><span>↗ &nbsp; Longitudinal insights</span><span>◎ &nbsp; Human reviewed</span></div></div><div class="orb-scene" aria-hidden="true"><div class="orbit"></div><div class="orb"></div><div class="orbit second"></div><div class="float-label one">CONNECTED RECORDS<b>One complete view</b></div><div class="float-label two">◈ &nbsp; SOURCE-GROUNDED<b>Clarity you can trace</b></div></div></section>''')


def stats(workspace, patient_id):
    docs, obs = workspace.docs(patient_id), workspace.obs(patient_id)
    reviewed = [o for o in obs if o.status in {"accepted", "corrected"}]
    outside = sum(comparison(o) in {"LOW", "HIGH"} for o in latest(obs))
    review_count = sum(o.status == "needs_review" for o in obs)
    cards = [("Documents", len(docs), "▤", "Source records in this workspace"),
             ("Reviewed observations", len(reviewed), "⌁", "<span>Traceable</span> to original evidence"),
             ("Outside source range", outside, "↗", "Latest results · not a diagnosis"),
             ("Awaiting review", review_count, "◎", "Human review keeps you in control")]
    html('<div class="stat-grid">' + ''.join(f'<div class="stat"><div class="stat-top">{title}<span class="stat-symbol">{symbol}</span></div><div class="stat-number">{number:02d}</div><div class="stat-foot">{foot}</div></div>' for title, number, symbol, foot in cards) + '</div>')


def doc_rows(documents):
    if not documents:
        st.caption("No documents imported yet.")
    for doc in documents:
        label = "Reviewed" if doc.status == "Reviewed" else doc.status
        klass = "" if label == "Reviewed" else " amber"
        html(f'<div class="doc-row"><span class="doc-icon">{e(Path(doc.name).suffix[1:].upper())}</span><div class="doc-info"><b>{e(doc.name)}</b><p>{e(doc.date or "Date unavailable")} &nbsp; · &nbsp; {e(doc.source)}</p></div><span class="small-pill{klass}">{e(label)}</span></div>')


def patient_snapshot(patient, workspace):
    docs = workspace.docs(patient.id)
    html(f'<div class="patient-heading"><div class="avatar">{e(patient.initials)}</div><div><b>{e(patient.name)}</b><p>{e(patient.id)} &nbsp; · &nbsp; Synthetic profile</p></div></div>')
    for label, value in [("Age / sex", f"{patient.age or '—'} years / {patient.sex}"),
                         ("Latest report", str(docs[0].date) if docs else "No records"),
                         ("Records available", f"{len(docs)} documents"),
                         ("Profile type", "Demonstration")]:
        html(f'<div class="detail-row"><span>{e(label)}</span><b>{e(value)}</b></div>')
    html('<div class="mini-note">◈ &nbsp; Every result has a source. Open the evidence viewer to see the original record.</div>')


def footer():
    html(f'<div class="footer"><span>HealthLens AI &nbsp; / &nbsp; Clinical document intelligence<br>© {date.today().year} Vijay Kumar Kothapalli. All rights reserved.</span><span>Synthetic demonstration · Research and education only.<br>Does not replace professional medical evaluation, diagnosis, or treatment.</span></div>')


def workspace():
    return st.session_state.workspace


def patient_id():
    return st.session_state.patient_id
