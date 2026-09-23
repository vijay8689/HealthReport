from datetime import timedelta

import streamlit as st

from healthlens.analytics import comparison, latest, trends
from ui.charts import lab_chart
from ui.components import doc_rows, e, heading, hero, html, panel_title, patient_id, patient_snapshot, stats, workspace

ws, pid = workspace(), patient_id()
patient = ws.patient(pid)
head, action = st.columns([3.6, 1], vertical_alignment="center")
with head:
    heading("Your health, connected.", "One workspace for your records, results, and the story between them.")
with action:
    if st.button("Upload report", type="primary", icon=":material/add:", width="stretch"):
        st.session_state.document_view = "Upload reports"
        st.switch_page("app_pages/documents.py")
hero()
stats(ws, pid)
main, side = st.columns([1.95, 1], gap="medium")
obs = ws.obs(pid)
with main:
    with st.container(border=True, key="chart_panel"):
        panel_title("The bigger picture", "Follow a result over time. Reference ranges come from each source report.")
        choices = sorted({(o.name, o.unit) for o in obs if o.status in {"accepted", "corrected"}})
        if choices:
            a, b = st.columns([1.7, 1.1], vertical_alignment="bottom")
            with a:
                selected = st.selectbox("Lab marker", choices, index=next((i for i,x in enumerate(choices) if x[0] == "Fasting glucose"), 0), format_func=lambda x:x[0], key=f"overview_marker_{pid}", label_visibility="collapsed")
            with b:
                period = st.segmented_control("Period", ["6M", "1Y", "All"], default="All", key=f"overview_period_{pid}", label_visibility="collapsed")
            rows = [o for o in obs if (o.name, o.unit) == selected]
            dated = [o.date for o in rows if o.date]
            if dated and period in {"6M", "1Y"}:
                start = max(dated) - timedelta(days=183 if period == "6M" else 365)
                rows = [o for o in rows if o.date and o.date >= start]
            st.plotly_chart(lab_chart(rows), config={"displayModeBar": False}, key="overview_plot")
            st.caption("● Recorded value   ·   Shaded area: source reference range")
        else:
            st.info("Upload and review a report to see the first trend.")
with side:
    with st.container(border=True, key="snapshot_panel"):
        panel_title("Patient snapshot", "A little context for the bigger picture")
        patient_snapshot(patient, ws)
        if st.button("Explore patient timeline", icon=":material/arrow_forward:", width="stretch", type="tertiary"):
            st.switch_page("app_pages/timeline.py")

lower_left, lower_right = st.columns([1.95, 1], gap="medium")
with lower_left:
    with st.container(border=True, key="docs_panel"):
        a,b = st.columns([3,1])
        with a:
            panel_title("Recent documents", "Your latest records, organized and traceable")
        with b:
            if st.button("View all", type="tertiary", icon=":material/arrow_forward:"):
                st.switch_page("app_pages/documents.py")
        doc_rows(ws.docs(pid)[:3])
with lower_right:
    with st.container(border=True, key="insights_panel"):
        panel_title("Worth a closer look", "Source-based observations · not medical advice")
        outside = [o for o in latest(obs) if comparison(o) in {"LOW", "HIGH"}]
        for o in outside[:2]:
            html(f'<div class="insight"><b>{e(o.name)} · {o.value:g} {e(o.unit)}</b><p>{comparison(o).title()} relative to the source range of {o.low:g}–{o.high:g} {e(o.unit)}. Review the source for context.</p></div>')
        if not outside:
            st.caption("No out-of-range results in the latest comparable observations.")
        if st.button("Explore analysis", width="stretch", icon=":material/auto_awesome:"):
            st.switch_page("app_pages/analysis.py")
