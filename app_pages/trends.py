import pandas as pd
import streamlit as st

from healthlens.analytics import comparison, eligible, trends
from healthlens.exports import csv_observations
from ui.marker_selector import select_marker
from ui.charts import lab_chart
from ui.components import heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("See the story over time.", "Explore source-linked laboratory results, with the context that makes them meaningful.", "LONGITUDINAL INSIGHTS")
obs = eligible(ws.obs(pid))
if not obs:
    st.info("No observations yet. Import a report to see its extracted values automatically.")
else:
    with st.expander("Uploaded reports and extracted results"):
        st.dataframe([{"Report": document.name, "Report date": str(document.date or "Not recorded"),
                       "Extracted results": len([o for o in obs if o.document_id == document.id])}
                      for document in ws.docs(pid)], hide_index=True, width="stretch")
    categories = sorted({o.category for o in obs})
    category = st.pills("Clinical domain", ["All", *categories], default="All") or "All"
    filtered = [o for o in obs if category == "All" or o.category == category]
    choice, rows = select_marker(filtered, label="Choose a test", key=f"trend_marker_{pid}", history_first=True)
    dates = [o.date for o in rows if o.date]
    with st.container(border=True):
        a, b = st.columns([3, 1])
        with a:
            panel_title(choice[0], f"{choice[1]} · {len(rows)} results from {len({o.document_id for o in rows})} reports")
        with b:
            show_range = st.toggle("Source ranges", value=True)
        if dates:
            chosen_dates = st.date_input("Observation date range", value=(min(dates), max(dates)), key=f"trend_dates_{pid}_{choice}_{min(dates)}_{max(dates)}")
            if len(chosen_dates) == 2:
                rows = [o for o in rows if o.date and chosen_dates[0] <= o.date <= chosen_dates[1]]
        st.plotly_chart(lab_chart(rows, show_range, 330, display_unit=choice[1]), config={"displayModeBar": False})
        if len({o.unit for o in rows}) > 1:
            st.caption("Equivalent unit labels are grouped in this chart. The table keeps each report's original units.")
        if len(dates) < 2 or len(set(dates)) < 2:
            st.info("Only one dated result is available for this test. Other uploaded reports may contain different tests or have no extracted result for this one. Choose a test with multiple dates to compare over time.")
        if len({o.method for o in rows}) > 1:
            st.caption("These reports use different measurement methods. All results are shown together; calculated changes require matching methods and original test names.")
        t = trends(rows)
        if t:
            result = t[0]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Latest value", f"{result['current']:g} {choice[1]}")
            c2.metric("Previous value", f"{result['previous']:g} {choice[1]}")
            c3.metric("Absolute change", f"{result['delta']:+g}")
            c4.metric("Percentage change", f"{result['percent']:+g}%" if result["percent"] is not None else "Undefined")
        else:
            st.caption("At least two dated, exact results on distinct dates are required for a trend calculation.")
    st.caption("Direction of change does not by itself indicate improvement or deterioration. Shading represents the reference range recorded for each observation.")
    frame = pd.DataFrame([{"Date": str(o.date or "Unknown"), "Result": f"{o.comparator if o.comparator != '=' else ''}{o.value:g} {o.unit}",
                           "Original test name": o.name, "Method": o.method,
                           "Source range": f"{o.low}–{o.high}", "Comparison": comparison(o), "Source": next((d.name for d in ws.docs(pid) if d.id == o.document_id), o.document_id), "Location": o.locator} for o in sorted(rows, key=lambda o: str(o.date or ""))])
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button("Export these results", csv_observations(rows), "healthlens_lab_results.csv", "text/csv", icon=":material/download:")

