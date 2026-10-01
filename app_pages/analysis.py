import streamlit as st

from healthlens.workflow import analyze
from ui.components import e, heading, html, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Connected evidence. Considered insights.", "A transparent workflow that checks the records before assembling a summary.", "ORCHESTRATED ANALYSIS")
html('<div class="pipeline"><div class="stage"><span>▤</span>Intake</div><div class="stage-arrow">→</div><div class="stage"><span>⌁</span>Trends & ranges</div><div class="stage-arrow">→</div><div class="stage"><span>◈</span>Evidence</div><div class="stage-arrow">→</div><div class="stage"><span>◎</span>Safety checks</div><div class="stage-arrow">→</div><div class="stage"><span>▧</span>Report</div></div>')
st.caption("DEMO ENGINE · Real LangGraph orchestration with deterministic calculations. No live LLM, semantic RAG, or predictive risk model is connected.")
fingerprint = ws.fingerprint(pid)
reports = [r for r in ws.reports if r["patient_id"] == pid]
current = next((r for r in reversed(reports) if r["fingerprint"] == fingerprint), None)
a, b = st.columns([2.5, 1])
with a:
    st.write(f"**{ws.patient(pid).name}** · {len(ws.docs(pid))} documents · {len(ws.obs(pid))} extracted observations")
with b:
    run = st.button("Run analysis" if not current else "Analysis is up to date", disabled=current is not None or not ws.obs(pid), icon=":material/auto_awesome:", type="primary", width="stretch")
if run:
    with st.status("Orchestrating your records…", expanded=True) as status:
        def stage(name):
            st.write(f"✓ {name.replace('_', ' ').title()}")
        try:
            current = analyze(pid, ws.obs(pid), fingerprint, stage)
            ws.reports.append(current)
            status.update(label="Analysis complete" if current["status"] != "blocked" else "Analysis needs review", state="complete", expanded=False)
        except Exception:
            status.update(label="Analysis could not finish. Review the records and retry.", state="error")
            current = None
if not current:
    with st.container(border=True):
        html('<div class="empty-graphic">✧</div><div class="empty-title">Clarity is a workflow away.</div>')
        st.write("Run analysis to assemble saved observations, source-based range checks, longitudinal changes, and data gaps.")
        if reports:
            st.warning("The records changed since the previous analysis. Regenerate before downloading a current report.")
else:
    if current["status"] == "blocked":
        st.warning("No publishable summary is available. Review or accept source observations first.")
    tabs = st.tabs(["Source-based summary", "Trends", "Data gaps & conflicts", "Workflow checks"])
    with tabs[0]:
        for claim in current["claims"]:
            with st.container(border=True):
                st.write(claim["text"])
                st.caption(f"Source: {claim['document_id']} · {claim['locator']}")
                with st.expander("Show original evidence"):
                    st.code(claim["source_text"], language=None)
        st.info("No validated risk model is configured. HealthLens does not produce a disease prediction or treatment recommendation.", icon=":material/info:")
    with tabs[1]:
        for trend in current["trends"]:
            with st.container(border=True):
                panel_title(trend["name"], f"{trend['start']} to {trend['end']} · {trend['count']} observations")
                st.write(f"{trend['previous']:g} → **{trend['current']:g} {trend['unit']}** · Change: {trend['delta']:+g}")
                st.caption("Evidence: " + ", ".join(trend["evidence"]))
        if not current["trends"]:
            st.caption("Not enough comparable dated observations to calculate trends.")
    with tabs[2]:
        for gap in current["gaps"]:
            st.warning(gap)
        for conflict in current["conflicts"]:
            st.warning(f"{conflict['name']} ({conflict['date']}): {conflict['message']}")
        if not current["gaps"] and not current["conflicts"]:
            st.success("No gaps or contradictions detected in the supported structured fields. This does not establish that the medical record is complete.")
    with tabs[3]:
        for check in current["checks"]:
            st.write(f"✓ {check}")
        st.caption(f"Run {current['id']} · Workflow {current['workflow_version']} · {current['created_at']}")
        for limitation in current["limitations"]:
            st.caption(limitation)
    if current["status"] != "blocked" and st.button("Open report downloads", icon=":material/download:"):
        st.switch_page("app_pages/reports.py")

