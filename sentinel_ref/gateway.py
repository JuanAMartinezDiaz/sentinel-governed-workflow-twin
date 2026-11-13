from __future__ import annotations

import hmac
import json
import math
from threading import RLock
from time import monotonic
from hashlib import sha256
import secrets
from dataclasses import asdict, dataclass
from typing import Any, Callable

from .arbitration import ArbitrationEngine
from .evidence import EvidenceLedger
from .models import ArbitrationResult, Disposition, ExecutionPermit, ProposedAction


class EvidencePersistenceError(RuntimeError):
    """Evidence persistence failed after a protected operation completed."""

    def __init__(self, outcome: Any, decision_id: str) -> None:
        super().__init__(
            "protected operation succeeded, but SUCCEEDED evidence could not be persisted; "
            "do not retry the operation"
        )
        self.outcome = outcome
        self.decision_id = decision_id
        self.execution_status = "SUCCEEDED"


@dataclass(frozen=True)
class _PendingPermit:
    action_fingerprint: str
    context_fingerprint: str
    nonce: str
    expires_at: float
    human_approved: bool


class ProtectedExecutor:
    """Single-process reference boundary, not an OS or database isolation boundary.

    A permit is unique, time-limited, context-bound and consumed before dispatch.
    This does not provide durable business idempotency or authenticated approval.
    Existing in-flight operations are not cancelled by revocation.
    """

    def __init__(
        self,
        engine: ArbitrationEngine,
        *,
        permit_ttl_seconds: float = 60.0,
        max_pending_permits: int = 1024,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if isinstance(permit_ttl_seconds, bool) or not isinstance(permit_ttl_seconds, (int, float)):
            raise ValueError("permit lifetime must be finite and positive")
        if not math.isfinite(permit_ttl_seconds) or permit_ttl_seconds <= 0:
            raise ValueError("permit lifetime must be finite and positive")
        if isinstance(max_pending_permits, bool) or not isinstance(max_pending_permits, int) or max_pending_permits <= 0:
            raise ValueError("pending permit capacity must be a positive integer")
        self._engine = engine
        self._signing_key = secrets.token_bytes(32)
        self._permit_ttl = permit_ttl_seconds
        self._max_pending = max_pending_permits
        self._clock = clock
        self._pending: dict[str, _PendingPermit] = {}
        self._lock = RLock()

    def _context_fingerprint(self, action: ProposedAction) -> str:
        authority = self._engine.registry.get(action.agent_id)
        context = {
            "policy": asdict(self._engine.policy),
            "policy_revision": self._engine.policy_revision,
            "authority_revision": self._engine.registry.revision(action.agent_id),
            "authority": None if authority is None else {
                "agent_id": authority.agent_id,
                "allowed_actions": sorted(authority.allowed_actions),
                "allowed_tools": sorted(authority.allowed_tools),
                "max_risk_tier": int(authority.max_risk_tier),
            },
        }
        return sha256(json.dumps(context, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _signature_for(self, pending: _PendingPermit) -> str:
        message = json.dumps(asdict(pending), sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(self._signing_key, message, sha256).hexdigest()

    def _purge_expired(self, now: float) -> None:
        for signature, pending in list(self._pending.items()):
            if pending.expires_at <= now:
                del self._pending[signature]

    def invalidate_all_permits(self) -> int:
        """Invalidate outstanding permits; this does not stop dispatched actions."""
        with self._lock:
            count = len(self._pending)
            self._pending.clear()
            return count

    def _discard_permit(self, permit: ExecutionPermit | None) -> None:
        if permit is not None:
            with self._lock:
                self._pending.pop(permit.signature, None)

    def authorize(
        self,
        action: ProposedAction,
        *,
        human_approved: bool = False,
    ) -> tuple[ArbitrationResult, ExecutionPermit | None]:
        with self._lock:
            result = self._engine.evaluate(action, human_approved=human_approved)
            if result.disposition is not Disposition.ALLOW:
                return result, None
            now = self._clock()
            self._purge_expired(now)
            if len(self._pending) >= self._max_pending:
                raise RuntimeError("pending permit capacity reached; no permit issued")
            pending = _PendingPermit(
                action.fingerprint(), self._context_fingerprint(action),
                secrets.token_hex(24), now + self._permit_ttl, human_approved,
            )
            signature = self._signature_for(pending)
            self._pending[signature] = pending
            return result, ExecutionPermit(pending.action_fingerprint, signature)

    def _permit_is_valid(self, action: ProposedAction, permit: ExecutionPermit | None) -> bool:
        # Called under the dispatch lock. No caller-supplied approval is accepted here.
        if not isinstance(permit, ExecutionPermit):
            return False
        if not isinstance(permit.signature, str) or not isinstance(permit.action_fingerprint, str):
            return False
        pending = self._pending.get(permit.signature)
        if pending is None or pending.expires_at <= self._clock():
            return False
        fingerprint = action.fingerprint()
        if not hmac.compare_digest(permit.action_fingerprint, fingerprint):
            return False
        if not hmac.compare_digest(pending.action_fingerprint, fingerprint):
            return False
        if not hmac.compare_digest(pending.context_fingerprint, self._context_fingerprint(action)):
            return False
        if not hmac.compare_digest(permit.signature, self._signature_for(pending)):
            return False
        return self._engine.evaluate(action, human_approved=pending.human_approved).disposition is Disposition.ALLOW

    def execute(
        self,
        action: ProposedAction,
        permit: ExecutionPermit | None,
        operation: Callable[[dict[str, Any]], Any],
    ) -> Any:
        with self._lock:
            self._purge_expired(self._clock())
            if not self._permit_is_valid(action, permit):
                raise PermissionError("protected execution denied: valid arbitration permit required")
            # Consume BEFORE dispatch, including failures/unknown outcomes.
            # One-use permits are not durable, cross-worker business deduplication.
            del self._pending[permit.signature]
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
        try:
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
        except Exception:
            self._discard_permit(permit)
            raise
        action_fingerprint = (
            decision["action_fingerprint"]
            if permit is None
            else permit.action_fingerprint
        )
        if permit is None:
            ledger.record_execution(
                action,
                "BLOCKED",
                decision["decision_id"],
                action_fingerprint=action_fingerprint,
            )
            return result, None
        try:
            outcome = self.execute(action, permit, operation)
        except Exception:
            ledger.record_execution(
                action,
                "FAILED",
                decision["decision_id"],
                action_fingerprint=action_fingerprint,
            )
            raise
        try:
            ledger.record_execution(
                action,
                "SUCCEEDED",
                decision["decision_id"],
                action_fingerprint=action_fingerprint,
            )
        except Exception as error:
            raise EvidencePersistenceError(outcome, decision["decision_id"]) from error
        return result, outcome
