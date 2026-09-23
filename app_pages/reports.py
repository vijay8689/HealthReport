import streamlit as st

from healthlens.exports import csv_observations, json_report, pdf_report
from ui.components import heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Clarity, ready to take with you.", "Download structured results and source-linked summaries from your analysis history.", "REPORTS & DOWNLOADS")
reports = [r for r in ws.reports if r["patient_id"] == pid]
if not reports:
    with st.container(border=True):
        panel_title("Your first report is one analysis away", "Run the analysis workflow to assemble a source-grounded report.")
        if st.button("Go to AI analysis", type="primary", icon=":material/auto_awesome:"):
            st.switch_page("app_pages/analysis.py")
for report in reversed(reports):
    stale = report["fingerprint"] != ws.fingerprint(pid)
    with st.container(border=True):
        panel_title(f"Health summary · {report['created_at'][:10]}", f"Run {report['id'][:8]} · {len(report['claims'])} cited observations")
        if stale:
            st.warning("Stale report: source observations have changed. Run analysis again to create a current export.")
        elif report["status"] == "blocked":
            st.warning("Blocked report: review source data before exporting a narrative.")
        else:
            st.caption("DRAFT · Synthetic data · Source-linked deterministic summary")
            a,b = st.columns(2)
            a.download_button("Download PDF", pdf_report(report, ws.patient(pid).name), f"HealthLens_{pid}.pdf", "application/pdf", key=f"pdf_{report['id']}", icon=":material/picture_as_pdf:", width="stretch")
            b.download_button("Download JSON", json_report(report), f"HealthLens_{pid}.json", "application/json", key=f"json_{report['id']}", icon=":material/data_object:", width="stretch")
        with st.expander("Analysis metadata"):
            st.json({k:report[k] for k in ["id", "created_at", "status", "mode", "workflow_version", "fingerprint"]})
st.download_button("Export all patient observations (CSV)", csv_observations(ws.obs(pid)), f"HealthLens_{pid}_observations.csv", "text/csv", icon=":material/download:")
st.caption("CSV includes review status so pending or rejected values can be distinguished from accepted observations.")

