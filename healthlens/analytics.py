"""Deterministic calculations; never diagnose or invent reference ranges."""
from collections import defaultdict

from healthlens.models import Observation


def comparison(o: Observation) -> str:
    if o.status not in {"accepted", "corrected"} or o.comparator != "=":
        return "UNKNOWN"
    if o.low is None or o.high is None:
        return "UNKNOWN"
    if o.value < o.low:
        return "LOW"
    if o.value > o.high:
        return "HIGH"
    return "IN RANGE"


def eligible(observations: list[Observation]) -> list[Observation]:
    return [o for o in observations if o.status in {"accepted", "corrected"}]


def latest(observations: list[Observation]) -> list[Observation]:
    grouped = {}
    for o in sorted(eligible(observations), key=lambda x: (str(x.date or ""), x.id)):
        grouped[(o.name, o.unit, o.specimen, o.method)] = o
    return list(grouped.values())


def trends(observations: list[Observation]) -> list[dict]:
    groups = defaultdict(list)
    for o in eligible(observations):
        if o.date and o.comparator == "=":
            groups[(o.name, o.unit, o.specimen, o.method)].append(o)
    results = []
    for (name, unit, specimen, method), values in groups.items():
        values.sort(key=lambda x: (x.date, x.id))
        if len(values) < 2:
            continue
        # Same-day duplicates are ambiguous; no arbitrary selection for deltas.
        if len({v.date for v in values}) != len(values):
            continue
        previous, current = values[-2:]
        delta = current.value - previous.value
        results.append(dict(name=name, unit=unit, current=current.value,
                            previous=previous.value, delta=round(delta, 4),
                            percent=round(delta / previous.value * 100, 2) if previous.value else None,
                            count=len(values), start=str(values[0].date), end=str(current.date),
                            evidence=[previous.id, current.id], specimen=specimen, method=method))
    return results


def contradictions(observations: list[Observation]) -> list[dict]:
    groups = defaultdict(list)
    for o in eligible(observations):
        if o.date:
            groups[(o.name, o.unit, o.date, o.specimen, o.method)].append(o)
    return [dict(name=k[0], date=str(k[2]), evidence=[o.id for o in values],
                 message="Different values are recorded for the same test and date; review the sources.")
            for k, values in groups.items() if len({(o.value, o.comparator) for o in values}) > 1]

