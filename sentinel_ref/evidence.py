from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

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
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "decision_id": str(uuid4()),
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
        if context is not None:
            # Copy the snapshot so later caller mutations cannot rewrite history.
            event["decision_context"] = json.loads(json.dumps(context))
        self.events.append(event)

        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def record_execution(
        self,
        action: ProposedAction,
        status: str,
        decision_id: str,
        *,
        action_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        """Record observed execution status without retaining sensitive outputs."""
        if status not in {"SUCCEEDED", "FAILED", "BLOCKED"}:
            raise ValueError("unknown execution status")
        event = {
            "event_type": "execution",
            "decision_id": decision_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "workflow_id": action.workflow_id,
            "step_id": action.step_id,
            "action_fingerprint": (
                action.fingerprint() if action_fingerprint is None else action_fingerprint
            ),
            "execution_status": status,
        }
        self.events.append(event)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def export_package(self, path: str | Path) -> None:
        """Export captured evidence; this is not a signed or immutable archive."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({
            "schema_version": "1.0",
            "events": self.events,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
