"""Junction Risk Score, risk-factor breakdown and rule-based interventions.

The score is a transparent weighted heuristic computed from the *measured*
conflict events, not a black box and not fabricated data:

score = 100 *
  0.35 * density_term   # event count saturation (few events = low base risk)
+ 0.35 * severity_term  # summed severity-weight saturation
+ 0.20 * ped_term       # pedestrian-involvement saturation
+ 0.10 * cadence_term   # events per minute

Each term is ``1 - exp(-x/scale)`` so the score saturates at 100 for very
dangerous clips and grows monotonically with real detections.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.core.conflict import ConflictEvent

CUTOFFS = [
    (25, "LOW"),
    (50, "MODERATE"),
    (75, "HIGH"),
    (101, "CRITICAL"),
]

_SEV_WEIGHT = {1: 0.4, 2: 0.8, 3: 1.5, 4: 2.5}

# Heuristic weighting for risk-factor ranking of a clip.
_FACTOR_WEIGHTS = {
    "vehicle_pedestrian": 2.6,
    "trajectory_intersection": 1.6,
    "near_miss": 1.0,
    "sudden_braking": 0.8,
}


@dataclass
class RiskResult:
    score: int
    category: str
    counts: dict[str, int]
    severity_counts: dict[str, int]
    events_per_minute: float
    factors: list[dict]
    recommendations: list[dict]


def risk_category(score: int) -> str:
    for threshold, label in CUTOFFS:
        if score < threshold:
            return label
    return "CRITICAL"


def compute_risk(
    events: list[ConflictEvent],
    duration_s: float,
    pedestrian_conflicts: int | None = None,
) -> RiskResult:
    counts: dict[str, int] = {}
    sev_counts: dict[str, int] = {label: 0 for label in ("LOW", "MODERATE", "HIGH", "CRITICAL")}
    sev_sum = 0.0
    n_ped = 0

    for ev in events:
        counts[ev.type] = counts.get(ev.type, 0) + 1
        sev_counts[ev.severity_label] = sev_counts.get(ev.severity_label, 0) + 1
        sev_sum += _SEV_WEIGHT.get(ev.severity, 1.0)
        if ev.type == "vehicle_pedestrian":
            n_ped += 1

    if pedestrian_conflicts is not None:
        n_ped = pedestrian_conflicts

    minutes = max(duration_s / 60.0, 1e-6)
    total = sum(counts.values())
    per_min = total / minutes

    density = 1.0 - math.exp(-total / 6.0)
    severity = 1.0 - math.exp(-sev_sum / 9.0)
    ped = 1.0 - math.exp(-n_ped / 2.0)
    cadence = 1.0 - math.exp(-per_min / 8.0)

    score = min(100.0, 100.0 * (0.35 * density + 0.35 * severity + 0.20 * ped + 0.10 * cadence))
    score_int = int(round(score))

    factors = _risk_factors(counts, sev_sum, n_ped, per_min, score_int)
    recommendations = _recommendations(counts, sev_counts, per_min)

    return RiskResult(
        score=score_int,
        category=risk_category(score_int),
        counts=counts,
        severity_counts=sev_counts,
        events_per_minute=round(per_min, 2),
        factors=factors,
        recommendations=recommendations,
    )


def _risk_factors(
    counts: dict[str, int], sev_sum: float, n_ped: int, per_min: float, score: int
) -> list[dict]:
    """Real aggregate signals, ranked by estimated contribution."""
    raw: list[tuple[str, float, str, int]] = []
    total_events = sum(counts.values()) or 1

    for kind, wt in _FACTOR_WEIGHTS.items():
        n = counts.get(kind, 0)
        raw.append(
            (
                "vehicle–pedestrian proximity" if kind == "vehicle_pedestrian"
                else "path intersection risk" if kind == "trajectory_intersection"
                else "unsafe proximity (near miss)" if kind == "near_miss"
                else "sudden-braking intensity",
                min(1.0, n / total_events) * wt,
                f"{n} × {kind.replace('_', ' ')}", n,
            )
        )
    raw.append(("reaction margin", min(1.0, sev_sum / 20.0), "severity-weighted events", int(sev_sum)))
    raw.append(("traffic density", min(1.0, per_min / 16.0), f"{per_min:.1f} events/min", total_events))

    raw.sort(key=lambda x: x[1], reverse=True)
    weight_sum = sum(w for _, w, _, _ in raw) or 1e-6
    factors = []
    for label, w, evidence, n in raw[:5]:
        factors.append(
            {
                "factor": label,
                "weight": round(w / weight_sum * 100.0, 1),
                "evidence": evidence,
                "count": n,
            }
        )
    return factors


def _recommendations(
    counts: dict[str, int], sev_counts: dict[str, int], per_min: float
) -> list[dict]:
    """Rule-based, evidence-driven safety interventions (decision rules only)."""
    out: list[dict] = []
    n_ped = counts.get("vehicle_pedestrian", 0)
    n_intersect = counts.get("trajectory_intersection", 0)
    n_miss = counts.get("near_miss", 0)
    n_brake = counts.get("sudden_braking", 0)

    if n_ped > 0:
        out.append(
            {
                "priority": 1,
                "measure": "Separate pedestrian movements",
                "action": "Install a pedestrian signal phase and a marked zebra crossing to route "
                "crossing movements away from the main traffic stream.",
                "rationale": (
                    f"{n_ped} vehicle–pedestrian conflict(s) detected — the interaction most likely "
                    "to cause severe injury."
                ),
                "evidence": {"vehicle_pedestrian": n_ped},
            }
        )
    if n_intersect > 0:
        out.append(
            {
                "priority": 2,
                "measure": "Restrict conflict-prone turning",
                "action": "Regulate turning conflicts (no-right-turn-on-red, protected turning phase) "
                "and reduce turning speeds through geometry.",
                "rationale": (
                    f"{n_intersect} predicted path intersection(s) — drivers and other road users "
                    "would otherwise share space in the box."
                ),
                "evidence": {"trajectory_intersection": n_intersect},
            }
        )
    if n_brake > 0 or (n_miss > 0 and per_min >= 2.0):
        out.append(
            {
                "priority": 3,
                "measure": "Stabilise approach speeds",
                "action": "Review signal timing/coordination to reduce stop-and-go, and deploy "
                "variable-message advance warning near the recorded braking zone.",
                "rationale": (
                    f"{n_brake} sudden-braking event(s) and {n_miss} near miss(es) indicate "
                    "unpredictable speed profiles at the approach."
                ),
                "evidence": {"sudden_braking": n_brake, "near_miss": n_miss},
            }
        )
    if n_miss > 0:
        out.append(
            {
                "priority": 4,
                "measure": "Calm traffic and mark lanes",
                "action": "Improve lane markings, add a raised/signalised crossing near the hotspot "
                "and consider a lower posted speed through the junction.",
                "rationale": f"{n_miss} unsafe-proximity event(s) point to a hotspot needing geometric or speed calming.",
                "evidence": {"near_miss": n_miss},
            }
        )
    if not out:
        out.append(
            {
                "priority": 1,
                "measure": "Continue monitoring",
                "action": "No intervention warranted from this clip; keep the camera feed under routine review.",
                "rationale": "No conflict threshold was exceeded during the analysed period.",
                "evidence": {},
            }
)
    return out
