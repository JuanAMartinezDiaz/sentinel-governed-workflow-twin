from __future__ import annotations

from dataclasses import dataclass

from .authority import AuthorityRegistry
from .models import ArbitrationResult, Disposition, ProposedAction, RiskTier, TraceEntry


@dataclass(frozen=True)
class ArbitrationPolicy:
    min_confidence_low: float = 0.60
    min_confidence_moderate: float = 0.75
    min_confidence_high: float = 0.90
    min_confidence_critical: float = 0.98
    human_approval_at_or_above: RiskTier = RiskTier.HIGH

    def threshold(self, tier: RiskTier) -> float:
        return {
            RiskTier.LOW: self.min_confidence_low,
            RiskTier.MODERATE: self.min_confidence_moderate,
            RiskTier.HIGH: self.min_confidence_high,
            RiskTier.CRITICAL: self.min_confidence_critical,
        }[tier]


class ArbitrationEngine:
    """Deterministic decision path for proposed agent actions."""

    def __init__(self, registry: AuthorityRegistry, policy: ArbitrationPolicy | None = None) -> None:
        self.registry = registry
        self.policy = policy or ArbitrationPolicy()

    def evaluate(self, action: ProposedAction, *, human_approved: bool = False) -> ArbitrationResult:
        trace: list[TraceEntry] = []

        authority = self.registry.get(action.agent_id)
        if authority is None:
            trace.append(TraceEntry("agent_registry", "FAIL", "agent is not registered"))
            return ArbitrationResult(Disposition.DENY, "unregistered agent", tuple(trace))
        trace.append(TraceEntry("agent_registry", "PASS", "agent is registered"))

        if action.action_class not in authority.allowed_actions:
            trace.append(TraceEntry("delegated_action", "FAIL", "action class is outside delegated authority"))
            return ArbitrationResult(Disposition.DENY, "action outside delegated authority", tuple(trace))
        trace.append(TraceEntry("delegated_action", "PASS", "action class is delegated"))

        if action.tool_name not in authority.allowed_tools:
            trace.append(TraceEntry("tool_permission", "FAIL", "tool is not approved for this agent"))
            return ArbitrationResult(Disposition.DENY, "tool not approved", tuple(trace))
        trace.append(TraceEntry("tool_permission", "PASS", "tool is approved"))

        if action.risk_tier > authority.max_risk_tier:
            trace.append(TraceEntry("risk_ceiling", "FAIL", "action exceeds agent risk ceiling"))
            return ArbitrationResult(Disposition.DENY, "risk ceiling exceeded", tuple(trace))
        trace.append(TraceEntry("risk_ceiling", "PASS", "risk tier is within agent ceiling"))

        minimum = self.policy.threshold(action.risk_tier)
        if action.confidence < minimum:
            trace.append(
                TraceEntry(
                    "confidence",
                    "FAIL",
                    f"confidence {action.confidence:.2f} is below required {minimum:.2f}",
                )
            )
            trace.append(TraceEntry("bounded_fallback", "PASS", "safe fallback selected; no execution permit"))
            return ArbitrationResult(Disposition.FALLBACK, "confidence below threshold", tuple(trace))
        trace.append(TraceEntry("confidence", "PASS", f"confidence meets {minimum:.2f} threshold"))

        if action.risk_tier >= self.policy.human_approval_at_or_above and not human_approved:
            trace.append(TraceEntry("human_approval", "WAIT", "human approval is required before execution"))
            return ArbitrationResult(Disposition.REQUIRE_APPROVAL, "human approval required", tuple(trace))

        if action.risk_tier >= self.policy.human_approval_at_or_above:
            trace.append(TraceEntry("human_approval", "PASS", "required human approval is present"))
        else:
            trace.append(TraceEntry("human_approval", "SKIP", "approval not required at this risk tier"))

        trace.append(TraceEntry("disposition", "PASS", "all declared checks passed"))
        return ArbitrationResult(Disposition.ALLOW, "authorized", tuple(trace))
