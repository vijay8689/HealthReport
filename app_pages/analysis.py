import streamlit as st

from healthlens.workflow import analyze
from ui.components import heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Your results, explained simply.", "See what needs a closer look, what changed, and where each result came from.", "AI ANALYSIS")
observations = ws.obs(pid)
documents = {document.id: document for document in ws.docs(pid)}
fingerprint = ws.fingerprint(pid)
reports = [report for report in ws.reports if report["patient_id"] == pid]
current = next((report for report in reversed(reports) if report["fingerprint"] == fingerprint), None)
left, right = st.columns([2.5, 1], vertical_alignment="center")
with left:
    st.write(f"**{ws.patient(pid).name}**")
    st.caption(f"{len(documents)} documents · {len(observations)} saved lab results")
with right:
    run = st.button("Run analysis" if not current else "Analysis is up to date", disabled=current is not None or not observations, icon=":material/auto_awesome:", type="primary", width="stretch")
if run:
    with st.spinner("Checking your saved results…"):
        try:
            current = analyze(pid, observations, fingerprint)
            ws.reports.append(current)
        except Exception:
            st.error("We couldn't finish checking your results. Please try again.")
            current = None

if not current:
    with st.container(border=True):
        if observations:
            panel_title("Your summary is ready to create")
            st.write("Select Run analysis to check your lab results and compare them with earlier reports.")
        else:
            panel_title("No lab results to summarize yet")
            st.write("Upload a laboratory report first. Saved document text needs to contain supported numeric results before it can be analyzed.")
            if st.button("Go to documents", icon=":material/upload_file:"):
                st.switch_page("app_pages/documents.py")
        if reports:
            st.info("Your records have changed. Run analysis to update the summary.")
else:
    claims = current["claims"]
    outside = [claim for claim in claims if claim["status"] in {"LOW", "HIGH"}]
    within = [claim for claim in claims if claim["status"] == "IN RANGE"]
    unclassified = len(claims) - len(outside) - len(within)
    by_id = {observation.id: observation for observation in observations}
    labels = {"LOW": "Below range", "HIGH": "Above range", "IN RANGE": "Within range"}
    if current["status"] == "blocked":
        st.warning("A summary isn't available yet. Open Evidence & review to check the saved results.")
    else:
        a, b, c = st.columns(3)
        a.metric("Outside the report's range", len(outside))
        b.metric("Within the report's range", len(within))
        c.metric("Need more information", unclassified)
        st.caption("Counts use the latest comparable results for each test. A result outside a report's range does not by itself mean illness.")
        with st.container(border=True):
            panel_title("What needs a closer look")
            if outside:
                st.write(f"{len(outside)} results are above or below the ranges printed in your reports. You can discuss these with your clinician.")
                rows = []
                for claim in outside:
                    observation = by_id[claim["observation_id"]]
                    rows.append({"Test": observation.name, "Your result": f"{observation.value:g} {observation.unit}",
                                 "Report range": f"{observation.low:g}–{observation.high:g} {observation.unit}",
                                 "Comparison": labels[claim["status"]], "Date": str(observation.date or "Not recorded")})
                st.dataframe(rows, hide_index=True, width="stretch")
            else:
                st.write("None of the results we could compare are outside the report's range.")
            if unclassified:
                st.caption(f"{unclassified} other results could not be classified. They may be missing a usable reference range or have a result reported as a limit.")
        with st.expander("See all results and their sources"):
            rows = []
            for claim in claims:
                observation = by_id[claim["observation_id"]]
                document = documents.get(claim["document_id"])
                rows.append({"Test": observation.name,
                             "Your result": f"{observation.comparator if observation.comparator != '=' else ''}{observation.value:g} {observation.unit}",
                             "Comparison": labels.get(claim["status"], "Not enough information"),
                             "Date": str(observation.date or "Not recorded"),
                             "Report": document.name if document else "Source document"})
            st.dataframe(rows, hide_index=True, width="stretch")
            selected = st.selectbox("View the original text for a result", claims,
                                    format_func=lambda claim: f"{by_id[claim['observation_id']].name} · {by_id[claim['observation_id']].date or 'Date not recorded'}",
                                    key=f"analysis_source_{pid}")
            if selected:
                document = documents.get(selected["document_id"])
                st.caption(f"{document.name if document else 'Source document'} · {selected['locator']}")
                st.code(selected["source_text"], language=None, wrap_lines=True)
    with st.expander("What changed over time?"):
        if current["trends"]:
            st.dataframe([{"Test": trend["name"], "Earlier result": f"{trend['previous']:g} {trend['unit']}",
                           "Latest result": f"{trend['current']:g} {trend['unit']}", "Change": f"{trend['delta']:+g} {trend['unit']}",
                           "From": str(trend["start"]), "To": str(trend["end"])} for trend in current["trends"]],
                         hide_index=True, width="stretch")
            st.caption("An increase or decrease does not automatically mean your health improved or worsened.")
        else:
            st.write("We need at least two comparable, dated results for the same test to show a change.")
    with st.expander("Missing details or results to check"):
        for conflict in current["conflicts"]:
            st.warning(f"{conflict['name']} ({conflict['date']}): {conflict['message']}")
        if current["gaps"]:
            st.caption("Some results may need a date, reference range, or a check against the original report.")
            st.dataframe({"Details to check": current["gaps"]}, hide_index=True, width="stretch")
        elif not current["conflicts"]:
            st.write("No missing details or conflicting values were found in the supported lab results. This does not mean the medical record is complete.")
        if st.button("Open evidence & review", icon=":material/fact_check:"):
            st.switch_page("app_pages/evidence.py")
    if current["status"] != "blocked" and st.button("Open report downloads", icon=":material/download:"):
        st.switch_page("app_pages/reports.py")

st.caption("This summary uses calculations from your saved lab results. It does not use a live AI model or provide a diagnosis or treatment advice.")
if current:
    with st.expander("How this summary was checked"):
        for check in current["checks"]:
            st.write(check)
        st.caption(f"Created: {current['created_at']}")
