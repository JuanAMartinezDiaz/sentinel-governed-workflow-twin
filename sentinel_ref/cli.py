from __future__ import annotations

import argparse

from .arbitration import ArbitrationEngine
from .authority import AuthorityRegistry
from .evidence import EvidenceLedger
from .gateway import ProtectedExecutor
from .models import AgentAuthority, ProposedAction, RiskTier


def main() -> None:
    parser = argparse.ArgumentParser(description="Demonstrate governed execution and export its evidence.")
    parser.add_argument("--evidence-package", help="Write the synthetic decision and execution records as JSON")
    args = parser.parse_args()
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

    operation = lambda payload: {"status": "executed", **payload}
    pending, _ = gateway.run_governed(action, operation, ledger)
    print(f"Without approval: {pending.disposition.value}")

    approved, outcome = gateway.run_governed(action, operation, ledger, human_approved=True)
    print(f"With approval: {approved.disposition.value}")
    print(f"Evidence fingerprint: {action.fingerprint()[:16]}...")
    print(outcome)
    if args.evidence_package:
        ledger.export_package(args.evidence_package)
        print(f"Evidence package: {args.evidence_package}")


if __name__ == "__main__":
    main()
