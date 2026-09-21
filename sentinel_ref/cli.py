from __future__ import annotations

from .arbitration import ArbitrationEngine
from .authority import AuthorityRegistry
from .evidence import EvidenceLedger
from .gateway import ProtectedExecutor
from .models import AgentAuthority, ProposedAction, RiskTier


def main() -> None:
    registry = AuthorityRegistry()
    registry.register(
        AgentAuthority(
            agent_id="workflow-agent-01",
            allowed_actions=frozenset({"READ_CASE", "DRAFT_RECOMMENDATION", "COMMIT_ACCOUNT_CHANGE"}),
            allowed_tools=frozenset({"case_api", "recommendation_service", "account_change_api"}),
            max_risk_tier=RiskTier.HIGH,
        )
    )

    action = ProposedAction(
        workflow_id="synthetic-bank-001",
        step_id="S16",
        agent_id="workflow-agent-01",
        action_class="COMMIT_ACCOUNT_CHANGE",
        tool_name="account_change_api",
        risk_tier=RiskTier.HIGH,
        confidence=0.97,
        reversible=True,
        payload={"case_id": "SYN-1042", "change": "illustrative-state-update"},
    )

    gateway = ProtectedExecutor(ArbitrationEngine(registry))
    ledger = EvidenceLedger()

    pending, permit = gateway.authorize(action)
    ledger.record(action, pending, permit)
    print(f"Without approval: {pending.disposition.value}")

    approved, permit = gateway.authorize(action, human_approved=True)
    event = ledger.record(action, approved, permit)
    print(f"With approval: {approved.disposition.value}")
    print(f"Evidence fingerprint: {event['action_fingerprint'][:16]}...")

    outcome = gateway.execute(action, permit, lambda payload: {"status": "executed", **payload})
    print(outcome)


if __name__ == "__main__":
    main()
