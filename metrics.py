"""
Metrics and output reporting for the UAM simulation.

summarize() reads a finished run: dispatch acceptance, why rides were rejected,
and the battery aircraft left with.
"""
from collections import Counter
from models import LogCategory


def summarize(sim) -> dict:
    sectors = list(sim.sectors.values())
    rejected = [s for s in sectors if s.status == "rejected"]
    departure_batteries = [e.meta["battery"] for e in sim.logs_by(category=LogCategory.DEPARTED)]

    return {
        "policy": sim.dispatch_policy.__name__,
        "acceptance_rate": (len(sectors) - len(rejected)) / max(len(sectors), 1),
        "rejections_by_reason": dict(Counter(s.reject_reason for s in rejected)),
        "avg_departure_battery": sum(departure_batteries) / len(departure_batteries) if departure_batteries else None,
    }
