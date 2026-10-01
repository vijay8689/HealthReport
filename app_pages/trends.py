import pandas as pd
import streamlit as st

from healthlens.analytics import comparison, eligible, trends
from healthlens.exports import csv_observations
from ui.charts import lab_chart
from ui.components import heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("See the story over time.", "Explore source-linked laboratory results, with the context that makes them meaningful.", "LONGITUDINAL INSIGHTS")
obs = eligible(ws.obs(pid))
if not obs:
    st.info("No observations yet. Import a report to see its extracted values automatically.")
else:
    categories = sorted({o.category for o in obs})
    category = st.pills("Clinical domain", ["All", *categories], default="All") or "All"
    filtered = [o for o in obs if category == "All" or o.category == category]
    groups = sorted({(o.name, o.unit, o.specimen, o.method) for o in filtered})
    choice = st.selectbox("Test and measurement context", groups, format_func=lambda x:f"{x[0]} · {x[1]}")
    rows = [o for o in filtered if (o.name, o.unit, o.specimen, o.method) == choice]
    dates = [o.date for o in rows if o.date]
    with st.container(border=True):
        a, b = st.columns([3, 1])
        with a:
            panel_title(choice[0], f"{choice[1]} · {len(rows)} source observations")
        with b:
            show_range = st.toggle("Source ranges", value=True)
        if dates:
            chosen_dates = st.date_input("Observation date range", value=(min(dates), max(dates)), key=f"trend_dates_{pid}_{choice[0]}")
            if len(chosen_dates) == 2:
                rows = [o for o in rows if o.date and chosen_dates[0] <= o.date <= chosen_dates[1]]
        st.plotly_chart(lab_chart(rows, show_range, 330), config={"displayModeBar": False})
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
                           "Source range": f"{o.low}–{o.high}", "Comparison": comparison(o), "Source": o.document_id, "Location": o.locator} for o in rows])
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button("Export these results", csv_observations(rows), "healthlens_lab_results.csv", "text/csv", icon=":material/download:")

