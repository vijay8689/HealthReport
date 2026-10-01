import streamlit as st

from ui.components import heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Trust begins at the source.", "Inspect original evidence and source locations for automatically saved observations.", "SOURCE EVIDENCE")
st.session_state.setdefault(f"review_filter_{pid}", "All observations")
scope = st.segmented_control("Observation filter", ["All observations", "Needs review", "Available", "Rejected"], key=f"review_filter_{pid}")
query = st.text_input("Find an observation", placeholder="Search test name or source text…", icon=":material/search:")
obs = [o for o in ws.obs(pid) if query.lower() in (o.name + o.source_text).lower()]
if scope == "Needs review":
    obs = [o for o in obs if o.status == "needs_review"]
elif scope == "Available":
    obs = [o for o in obs if o.status in {"accepted", "corrected"}]
elif scope == "Rejected":
    obs = [o for o in obs if o.status == "rejected"]
if not obs:
    st.info("No observations match this view. Uploaded observations are saved automatically and appear here with their source evidence.")
else:
    selected = st.selectbox("Observation", [o.id for o in obs], format_func=lambda x:next(f"{o.name} · {o.date or 'Date unavailable'} · {o.original_value} {o.unit}" for o in obs if o.id == x), key=f"review_choice_{pid}")
    o = next(x for x in obs if x.id == selected)
    doc = next(d for d in ws.docs(pid) if d.id == o.document_id)
    with st.container(border=True):
        panel_title("Original evidence", f"{doc.name} · {o.locator}")
        st.code(o.source_text, language=None, wrap_lines=True)
        st.caption(f"Original extracted value: {o.original_value} · Current status: {o.status.replace('_', ' ')} · Revision {o.version}")
        with st.expander("Full source text"):
            for page in doc.pages:
                st.code(page["text"], language=None, wrap_lines=True)
    revisions = [r for r in ws.revisions if r.observation_id == o.id]
    if revisions:
        with st.expander(f"Review history · {len(revisions)} revisions"):
            for revision in reversed(revisions):
                st.write(f"**{revision.actor}** · {revision.at[:19]} · {revision.reason}")
                st.json({"before": revision.before, "after": revision.after}, expanded=False)
