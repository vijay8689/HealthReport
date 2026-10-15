"""One test entry with a separate choice for incompatible measurement contexts."""
import streamlit as st

from healthlens.markers import marker_key


def select_marker(observations, *, label, key, history_first=False, label_visibility="visible"):
    grouped = {}
    for observation in observations:
        grouped.setdefault(marker_key(observation), []).append(observation)
    names = sorted({context[0] for context in grouped})
    history = {name: {o.date for context, rows in grouped.items() if context[0] == name for o in rows if o.date}
               for name in names}
    if history_first:
        names.sort(key=lambda name: (-len(history[name]), name))
    counts = {name: sum(len(rows) for context, rows in grouped.items() if context[0] == name) for name in names}
    name = st.selectbox(label, names,
                        index=names.index("Fasting glucose") if not history_first and "Fasting glucose" in names else 0,
                        format_func=(lambda name: f"{name} · {counts[name]} results across {len(history[name])} dates") if history_first else str,
                        key=key, label_visibility=label_visibility)
    contexts = sorted((context for context in grouped if context[0] == name),
                      key=lambda context: (-len({o.date for o in grouped[context] if o.date}), context))
    context = contexts[0]
    if len(contexts) > 1:
        context = st.selectbox("Units and sample", contexts,
                               format_func=lambda item: f"{item[1]} · {item[2]} · {len(grouped[item])} results",
                               key=f"{key}_context_{name}")
        st.caption("This test uses different units or samples across reports. Choose which results to compare.")
    return context, grouped[context]
