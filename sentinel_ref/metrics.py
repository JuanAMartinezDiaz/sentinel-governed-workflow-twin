from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowMetrics:
    cycle_time_minutes: float
    cost_units: float
    quality_defect_rate: float
    human_touches: int
    evidence_completeness: float


def _reduction(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round((before - after) / before * 100, 2)


def compare(baseline: WorkflowMetrics, redesigned: WorkflowMetrics) -> dict[str, float]:
    return {
        "cycle_time_reduction_pct": _reduction(
            baseline.cycle_time_minutes, redesigned.cycle_time_minutes
        ),
        "cost_reduction_pct": _reduction(baseline.cost_units, redesigned.cost_units),
        "defect_reduction_pct": _reduction(
            baseline.quality_defect_rate, redesigned.quality_defect_rate
        ),
        "human_touch_reduction_pct": _reduction(
            float(baseline.human_touches), float(redesigned.human_touches)
        ),
        "evidence_completeness_change_points": round(
            (redesigned.evidence_completeness - baseline.evidence_completeness) * 100,
            2,
        ),
    }
