from __future__ import annotations

import hmac
import json
from hashlib import sha256
import secrets
from dataclasses import asdict
from typing import Any, Callable

from .arbitration import ArbitrationEngine
from .evidence import EvidenceLedger
from .models import ArbitrationResult, Disposition, ExecutionPermit, ProposedAction


class ProtectedExecutor:
    """Application-layer enforcement boundary.

    The private signing key is held by the gateway. A protected operation executes
    only when the exact action fingerprint carries a valid permit produced after
    arbitration. Production deployments should add process/OS/network isolation.
    """

    def __init__(self, engine: ArbitrationEngine) -> None:
        self._engine = engine
        self._signing_key = secrets.token_bytes(32)

    def authorize(
        self,
        action: ProposedAction,
        *,
        human_approved: bool = False,
    ) -> tuple[ArbitrationResult, ExecutionPermit | None]:
        result = self._engine.evaluate(action, human_approved=human_approved)
        if result.disposition is not Disposition.ALLOW:
            return result, None

        fingerprint = action.fingerprint()
        signature = hmac.new(self._signing_key, fingerprint.encode(), sha256).hexdigest()
        return result, ExecutionPermit(fingerprint, signature)

    def _permit_is_valid(self, action: ProposedAction, permit: ExecutionPermit | None) -> bool:
        if permit is None:
            return False
        fingerprint = action.fingerprint()
        if not hmac.compare_digest(permit.action_fingerprint, fingerprint):
            return False
        expected = hmac.new(self._signing_key, fingerprint.encode(), sha256).hexdigest()
        return hmac.compare_digest(permit.signature, expected)

    def execute(
        self,
        action: ProposedAction,
        permit: ExecutionPermit | None,
        operation: Callable[[dict[str, Any]], Any],
    ) -> Any:
        if not self._permit_is_valid(action, permit):
            raise PermissionError("protected execution denied: valid arbitration permit required")
        return operation(action.payload)

    def run_governed(
        self,
        action: ProposedAction,
        operation: Callable[[dict[str, Any]], Any],
        ledger: EvidenceLedger,
        *,
        human_approved: bool = False,
    ) -> tuple[ArbitrationResult, Any]:
        """Capture policy/authority context and actual protected execution outcome."""
        result, permit = self.authorize(action, human_approved=human_approved)
        authority = self._engine.registry.get(action.agent_id)
        policy = self._engine.policy
        policy_snapshot = asdict(policy)
        policy_snapshot["human_approval_at_or_above"] = policy.human_approval_at_or_above.name
        decision = ledger.record(action, result, permit, context={
            "policy_snapshot": policy_snapshot,
            "policy_fingerprint": sha256(json.dumps(
                policy_snapshot, sort_keys=True, separators=(",", ":")
            ).encode()).hexdigest(),
            "authority_snapshot": None if authority is None else {
                "agent_id": authority.agent_id,
                "allowed_actions": sorted(authority.allowed_actions),
                "allowed_tools": sorted(authority.allowed_tools),
                "max_risk_tier": authority.max_risk_tier.name,
            },
            "human_approved": human_approved,
            "approval_evidence_type": "caller_assertion",
            "required_confidence": policy.threshold(action.risk_tier),
        })
        if permit is None:
            ledger.record_execution(action, "BLOCKED", decision["decision_id"])
            return result, None
        try:
            outcome = self.execute(action, permit, operation)
        except Exception:
            ledger.record_execution(action, "FAILED", decision["decision_id"])
            raise
        ledger.record_execution(action, "SUCCEEDED", decision["decision_id"])
        return result, outcome
