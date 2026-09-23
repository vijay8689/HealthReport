from datetime import date

import streamlit as st

from healthlens.analytics import comparison
from ui.components import heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Trust begins at the source.", "Inspect original evidence, correct extraction errors, and keep a complete review history.", "EVIDENCE & HUMAN REVIEW")
st.session_state.setdefault(f"review_filter_{pid}", "All observations")
scope = st.segmented_control("Review filter", ["All observations", "Needs review", "Reviewed", "Rejected"], key=f"review_filter_{pid}")
query = st.text_input("Find an observation", placeholder="Search test name or source text…", icon=":material/search:")
obs = [o for o in ws.obs(pid) if query.lower() in (o.name + o.source_text).lower()]
if scope == "Needs review":
    obs = [o for o in obs if o.status == "needs_review"]
elif scope == "Reviewed":
    obs = [o for o in obs if o.status in {"accepted", "corrected"}]
elif scope == "Rejected":
    obs = [o for o in obs if o.status == "rejected"]
if not obs:
    st.info("No observations match this view. Imported extractions appear here for review.")
else:
    selected = st.selectbox("Observation", [o.id for o in obs], format_func=lambda x:next(f"{o.name} · {o.date or 'Date unavailable'} · {o.original_value} {o.unit}" for o in obs if o.id == x), key=f"review_choice_{pid}")
    o = next(x for x in obs if x.id == selected)
    doc = next(d for d in ws.docs(pid) if d.id == o.document_id)
    left, right = st.columns([1.2, 1])
    with left:
        with st.container(border=True):
            panel_title("Original evidence", f"{doc.name} · {o.locator}")
            st.code(o.source_text, language=None, wrap_lines=True)
            st.caption(f"Original extracted value: {o.original_value} · Current status: {o.status.replace('_', ' ')} · Revision {o.version}")
            with st.expander("Full source text"):
                for page in doc.pages:
                    st.code(page["text"], language=None, wrap_lines=True)
            st.caption("Correcting an extracted value never changes the original source text.")
    with right:
        with st.form(f"review_{o.id}_{o.version}"):
            panel_title("Review observation", o.name)
            c1,c2 = st.columns([2,1])
            value = c1.number_input("Value", value=float(o.value), format="%.4f")
            comparator = c2.selectbox("Comparator", ["=", "<", ">", "<=", ">="], index=["=", "<", ">", "<=", ">="].index(o.comparator))
            unit = st.text_input("Unit", value=o.unit)
            lo,hi = st.columns(2)
            low = lo.number_input("Source range minimum", value=o.low, format="%.4f")
            high = hi.number_input("Source range maximum", value=o.high, format="%.4f")
            day = st.date_input("Observation date", value=o.date, min_value=date(1900,1,1), max_value=date(2100,12,31))
            decision = st.selectbox("Decision", ["Accept", "Correct", "Reject"])
            reason = st.text_input("Review reason", placeholder="Checked against source report…")
            submit = st.form_submit_button("Save review", type="primary", icon=":material/check:", width="stretch")
        if submit:
            changed = any([value != o.value, unit != o.unit, low != o.low, high != o.high, day != o.date, comparator != o.comparator])
            status = "rejected" if decision == "Reject" else ("corrected" if changed or decision == "Correct" else "accepted")
            try:
                ws.review(pid, o.id, o.version, dict(value=value, comparator=comparator, unit=unit, low=low, high=high, date=day, status=status), reason)
                st.success("Review saved. Existing analyses are now marked stale.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    revisions = [r for r in ws.revisions if r.observation_id == o.id]
    if revisions:
        with st.expander(f"Review history · {len(revisions)} revisions"):
            for revision in reversed(revisions):
                st.write(f"**{revision.actor}** · {revision.at[:19]} · {revision.reason}")
                st.json({"before": revision.before, "after": revision.after}, expanded=False)
