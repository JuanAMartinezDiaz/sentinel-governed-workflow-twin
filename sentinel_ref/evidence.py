from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .models import ArbitrationResult, ExecutionPermit, ProposedAction


class EvidenceLedger:
    """Structured, append-only-at-the-interface decision evidence."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.events: list[dict[str, Any]] = []

    def record(
        self,
        action: ProposedAction,
        result: ArbitrationResult,
        permit: ExecutionPermit | None,
    ) -> dict[str, Any]:
        event = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "workflow_id": action.workflow_id,
            "step_id": action.step_id,
            "agent_id": action.agent_id,
            "action_class": action.action_class,
            "tool_name": action.tool_name,
            "risk_tier": action.risk_tier.name,
            "action_fingerprint": action.fingerprint(),
            "disposition": result.disposition.value,
            "reason": result.reason,
            "permit_issued": permit is not None,
            "trace": [asdict(item) for item in result.trace],
        }
        self.events.append(event)

        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event
