from __future__ import annotations

import hmac
from hashlib import sha256
import secrets
from typing import Any, Callable

from .arbitration import ArbitrationEngine
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
