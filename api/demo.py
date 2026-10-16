"""Synthetic-only HTTP API for exercising the Sentinel reference engine.

This API intentionally accepts scenario names, not customer workflow records.
It demonstrates the governance engine and is not a production execution service.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
import json
from typing import Any

from api.scenarios import SCENARIOS
from sentinel_ref.arbitration import ArbitrationEngine
from sentinel_ref.authority import AuthorityRegistry
from sentinel_ref.evidence import EvidenceLedger
from sentinel_ref.gateway import ProtectedExecutor
from sentinel_ref.models import AgentAuthority, ProposedAction, RiskTier


MAX_BODY_BYTES = 2_048
ALLOWED_ORIGINS = {
    "https://martinez-applied-intelligence.morbiaus.chatgpt.site",
}


def run_scenario(scenario_name: str) -> dict[str, Any]:
    """Run one fixed synthetic case through the repository's real engine."""
    if scenario_name not in SCENARIOS:
        raise ValueError("unknown scenario")

    registry = AuthorityRegistry()
    registry.register(
        AgentAuthority(
            agent_id="demo-workflow-agent",
            allowed_actions=frozenset(
                {"READ_CASE", "DRAFT_RECOMMENDATION", "COMMIT_ACCOUNT_CHANGE"}
            ),
            allowed_tools=frozenset(
                {"case_api", "recommendation_service", "account_change_api"}
            ),
            max_risk_tier=RiskTier.HIGH,
        )
    )
    scenario = SCENARIOS[scenario_name]
    action = ProposedAction(
        workflow_id="synthetic-customer-dispute",
        step_id="SYNTHETIC-REVIEW",
        agent_id="demo-workflow-agent",
        action_class=scenario["action_class"],
        tool_name=scenario["tool_name"],
        risk_tier=scenario["risk_tier"],
        confidence=scenario["confidence"],
        reversible=True,
        payload={"case_id": "SYN-1042", "operation": "illustrative-state-update"},
    )

    ledger = EvidenceLedger()
    executor = ProtectedExecutor(ArbitrationEngine(registry))
    decision, outcome = executor.run_governed(
        action,
        lambda payload: {"status": "simulated", "operation": payload["operation"]},
        ledger,
        human_approved=scenario["human_approved"],
    )
    trace = [
        {"check": step.check, "status": step.status, "detail": step.detail}
        for step in decision.trace
    ]
    disposition = decision.disposition.value
    reason = decision.reason
    if scenario.get("attempt_direct_bypass"):
        try:
            executor.execute(
                action,
                None,
                lambda payload: {"status": "unsafe-execution", **payload},
            )
        except PermissionError:
            disposition = "BLOCKED"
            reason = "protected executor rejected a direct call without a valid permit"
            trace.append(
                {
                    "check": "protected_executor_permit_validation",
                    "status": "FAIL",
                    "detail": "direct execution was blocked; no business action ran",
                }
            )
        else:
            raise RuntimeError("synthetic bypass unexpectedly executed")
    return {
        "mode": "synthetic-demo",
        "scenario": scenario_name,
        "decision": disposition,
        "reason": reason,
        "trace": trace,
        "execution": outcome,
        "evidence": ledger.events,
        "approval_note": (
            "Approval is simulated by this fixed demo scenario; no person approved an action."
            if scenario["human_approved"]
            else None
        ),
    }


class handler(BaseHTTPRequestHandler):
    """Vercel Python Function handler for POST /api/demo."""

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            self._send_json(403, {"error": "origin_not_allowed"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:
        self._send_json(405, {"error": "method_not_allowed"})

    def do_POST(self) -> None:
        if self.path != "/api/demo":
            self._send_json(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "request_body_size_invalid"})
            return

        try:
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "invalid_json"})
            return
        if not isinstance(body, dict) or set(body) != {"scenario"}:
            self._send_json(400, {"error": "expected_scenario_only"})
            return
        if not isinstance(body["scenario"], str):
            self._send_json(400, {"error": "scenario_must_be_a_string"})
            return

        try:
            self._send_json(200, run_scenario(body["scenario"]))
        except ValueError:
            self._send_json(400, {"error": "unknown_scenario"})

    def log_message(self, format: str, *args: Any) -> None:
        # Avoid recording request bodies or client identifiers in platform logs.
        return
