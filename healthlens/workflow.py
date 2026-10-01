"""Actual LangGraph fan-out/join workflow using deterministic, cited demo nodes."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context

from healthlens.analytics import comparison, contradictions, eligible, latest, trends
from healthlens.models import Observation, timestamp, uid


class AnalysisState(TypedDict, total=False):
    patient_id: str
    observations: list[Observation]
    fingerprint: str
    trends: list[dict]
    abnormalities: list[dict]
    conflicts: list[dict]
    gaps: list[str]
    claims: list[dict]
    checks: Annotated[list[str], operator.add]
    safe: bool


def validate(state):
    if any(o.patient_id != state["patient_id"] for o in state["observations"]):
        raise ValueError("Patient scope validation failed.")
    return {"checks": ["Patient scope validated"]}


def trend_node(state):
    return {"trends": trends(state["observations"]), "checks": ["Comparable longitudinal values calculated"]}


def abnormality_node(state):
    return {"abnormalities": [{"observation_id": o.id, "status": comparison(o)}
                             for o in latest(state["observations"]) if comparison(o) in {"LOW", "HIGH"}],
            "checks": ["Source-provided reference ranges checked"]}


def conflict_node(state):
    return {"conflicts": contradictions(state["observations"]), "checks": ["Same-date conflicts checked"]}


def gap_node(state):
    obs = state["observations"]
    gaps = []
    if not eligible(obs):
        gaps.append("No usable observations are available for analysis.")
    for o in obs:
        if o.status == "needs_review":
            gaps.append(f"{o.name}: extraction awaits review.")
        if not o.date:
            gaps.append(f"{o.name}: observation date is unavailable.")
        if o.low is None or o.high is None:
            gaps.append(f"{o.name}: source reference range is incomplete.")
        if o.comparator != "=":
            gaps.append(f"{o.name}: bounded result excluded from exact numerical comparisons.")
    return {"gaps": sorted(set(gaps)), "checks": ["Missing information recorded"]}


def evidence_node(state):
    claims = []
    for o in latest(state["observations"]):
        status = comparison(o)
        sentence = f"The supplied report records {o.name} at {o.comparator if o.comparator != '=' else ''}{o.value:g} {o.unit}"
        sentence += f" on {o.date}." if o.date else "; the observation date is unavailable."
        if status in {"LOW", "HIGH"}:
            sentence += f" This is {status.lower()} relative to the source range ({o.low:g}–{o.high:g} {o.unit})."
        claims.append({"text": sentence, "observation_id": o.id, "document_id": o.document_id,
                       "locator": o.locator, "source_text": o.source_text, "status": status})
    return {"claims": claims, "checks": ["Every generated observation mapped to source evidence"]}


def safety_node(state):
    known = {o.id: o for o in eligible(state["observations"])}
    safe = all(c["observation_id"] in known and c["source_text"] and
               c["document_id"] == known[c["observation_id"]].document_id
               for c in state["claims"])
    return {"safe": safe, "checks": ["Evidence integrity check passed" if safe else "Evidence integrity check failed"]}


def build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("intake", validate)
    for name, node in [("trends", trend_node), ("ranges", abnormality_node),
                       ("contradictions", conflict_node), ("missing_data", gap_node)]:
        graph.add_node(name, node)
        graph.add_edge("intake", name)
    graph.add_node("evidence", evidence_node)
    graph.add_node("safety", safety_node)
    graph.add_edge(START, "intake")
    graph.add_edge(["trends", "ranges", "contradictions", "missing_data"], "evidence")
    graph.add_edge("evidence", "safety")
    graph.add_edge("safety", END)
    return graph.compile()


def analyze(patient_id, observations, fingerprint, on_stage=None) -> dict:
    state = {"patient_id": patient_id, "observations": observations,
             "fingerprint": fingerprint, "checks": []}
    # Ambient LangSmith settings must not send demo source records to a service.
    with tracing_context(enabled=False):
        for update in build_graph().stream(state, config={"recursion_limit": 15}, stream_mode="updates"):
            for node, values in update.items():
                for key, value in values.items():
                    if key == "checks":
                        state.setdefault(key, []).extend(value)
                    else:
                        state[key] = value
                if on_stage:
                    on_stage(node)
    return dict(id=uid(), patient_id=patient_id, created_at=timestamp(), fingerprint=fingerprint,
                schema_version="1.0", workflow_version="demo-1.0",
                status="draft" if state.get("safe") and state.get("claims") else "blocked",
                mode="Deterministic demo · no LLM calls", claims=state.get("claims", []) if state.get("safe") else [],
                trends=state.get("trends", []), abnormalities=state.get("abnormalities", []),
                conflicts=state.get("conflicts", []), gaps=state.get("gaps", []), checks=state["checks"],
                limitations=["Synthetic research demonstration; not medical advice.",
                             "No validated risk model is configured. No risk score is produced.",
                             "Only saved, supported laboratory rows are analyzed. No diagnosis or treatment recommendation is generated.",
                             "LangGraph orchestration uses deterministic nodes; no live LLM or semantic RAG provider is connected."])
