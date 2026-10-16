from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

from api.demo import handler as DemoHandler, run_scenario
from api.health import handler as HealthHandler
from api.scenarios import SCENARIOS


# Independent expected behavior: catalog additions must deliberately extend this
# matrix rather than inheriting their expected outcome from the implementation.
EXPECTED = {
    "low-risk-read": ("ALLOW", "SUCCEEDED"),
    "high-risk-pending": ("REQUIRE_APPROVAL", "BLOCKED"),
    "direct-executor-bypass": ("BLOCKED", "BLOCKED"),
    "high-risk-approved-demo": ("ALLOW", "SUCCEEDED"),
    "low-confidence-draft": ("FALLBACK", "BLOCKED"),
    "unapproved-tool": ("DENY", "BLOCKED"),
}


class MemoryWriter(io.BytesIO):
    def close(self):
        self.flush()


class MemorySocket:
    """In-memory socket so HTTP handler tests need no local network access."""

    def __init__(self, request: bytes):
        self.reader = io.BytesIO(request)
        self.writer = MemoryWriter()

    def makefile(self, mode, *args, **kwargs):
        return self.reader if "r" in mode else self.writer


def dispatch(handler_class, method, path, payload=None):
    body = b"" if payload is None else json.dumps(payload).encode()
    headers = {"Host": "localhost", "Connection": "close"}
    if body:
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
    raw_headers = "".join(f"{key}: {value}\r\n" for key, value in headers.items())
    raw_request = f"{method} {path} HTTP/1.1\r\n{raw_headers}\r\n".encode() + body
    connection = MemorySocket(raw_request)
    server = SimpleNamespace(server_name="localhost", server_port=443)

    class MemoryHandler(handler_class):
        wbufsize = 1

    MemoryHandler(connection, ("127.0.0.1", 12345), server)
    response = connection.writer.getvalue()
    head, response_body = response.split(b"\r\n\r\n", 1)
    status = int(head.split(b"\r\n", 1)[0].split()[1])
    return status, json.loads(response_body)


@pytest.mark.parametrize(
    ("scenario", "expected", "execution_status"),
    [(name, *expected) for name, expected in EXPECTED.items()],
)
def test_demo_scenario_uses_governance_engine(scenario, expected, execution_status):
    response = run_scenario(scenario)

    assert response["mode"] == "synthetic-demo"
    assert response["decision"] == expected
    expected_evidence_disposition = (
        "REQUIRE_APPROVAL" if scenario == "direct-executor-bypass" else expected
    )
    assert response["evidence"][0]["disposition"] == expected_evidence_disposition
    assert response["evidence"][1]["execution_status"] == execution_status
    assert response["evidence"][0]["action_fingerprint"]


def test_approval_scenario_is_clearly_labeled_as_simulated():
    response = run_scenario("high-risk-approved-demo")

    assert "simulated" in response["approval_note"].lower()
    assert response["execution"]["status"] == "simulated"


def test_api_rejects_unknown_scenarios():
    with pytest.raises(ValueError, match="unknown scenario"):
        run_scenario("arbitrary-client-action")


def test_health_endpoint_announces_synthetic_only_mode():
    status, data = dispatch(HealthHandler, "GET", "/api/health")

    assert status == 200
    assert data["mode"] == "synthetic-demo-only"
    assert data["scenarios"] == sorted(SCENARIOS) == sorted(EXPECTED)


def test_demo_endpoint_runs_engine_and_rejects_extra_data():
    status, result = dispatch(
        DemoHandler, "POST", "/api/demo", {"scenario": "high-risk-pending"}
    )
    assert status == 200
    assert result["decision"] == "REQUIRE_APPROVAL"
    assert result["evidence"][1]["execution_status"] == "BLOCKED"

    status, error = dispatch(
        DemoHandler,
        "POST",
        "/api/demo",
        {"scenario": "high-risk-pending", "customer_name": "not accepted"},
    )
    assert status == 400
    assert error["error"] == "expected_scenario_only"


@pytest.mark.parametrize("scenario", EXPECTED)
def test_every_published_scenario_runs_through_http(scenario):
    status, result = dispatch(DemoHandler, "POST", "/api/demo", {"scenario": scenario})
    assert status == 200
    assert result["scenario"] == scenario
    assert result["decision"] == EXPECTED[scenario][0]
    assert result["evidence"][1]["execution_status"] == EXPECTED[scenario][1]


@pytest.mark.parametrize("scenario", EXPECTED)
def test_fixed_scenarios_repeat_with_fresh_request_scoped_evidence(scenario):
    first, second = run_scenario(scenario), run_scenario(scenario)
    for key in ("decision", "reason", "trace", "execution", "approval_note"):
        assert first[key] == second[key]
    assert len(first["evidence"]) == len(second["evidence"]) == 2
    assert first["evidence"][0]["decision_id"] != second["evidence"][0]["decision_id"]
    assert first["evidence"][0]["action_fingerprint"] == second["evidence"][0]["action_fingerprint"]


@pytest.mark.parametrize("payload,error", [
    ({"scenario": "unknown"}, "unknown_scenario"),
    ({"scenario": ["low-risk-read"]}, "scenario_must_be_a_string"),
    ([], "expected_scenario_only"),
    ({"scenario": "low-risk-read", "workflow": {}}, "expected_scenario_only"),
    ({"scenario": "high-risk-pending", "human_approved": True}, "expected_scenario_only"),
    ({"scenario": "unapproved-tool", "tool_name": "case_api"}, "expected_scenario_only"),
])
def test_http_cannot_override_fixed_inputs(payload, error):
    status, response = dispatch(DemoHandler, "POST", "/api/demo", payload)
    assert status == 400
    assert response["error"] == error


def test_unapproved_tool_fails_at_tool_permission_without_a_permit():
    result = run_scenario("unapproved-tool")
    assert result["trace"][-1]["check"] == "tool_permission"
    assert result["trace"][-1]["status"] == "FAIL"
    assert result["evidence"][0]["permit_issued"] is False
    assert result["execution"] is None


@pytest.mark.parametrize("scenario", EXPECTED)
def test_only_allowed_scenarios_invoke_the_simulated_operation(monkeypatch, scenario):
    from sentinel_ref.gateway import ProtectedExecutor
    original = ProtectedExecutor.execute
    calls = []

    def observed(self, action, permit, operation):
        def counted(payload):
            calls.append(payload)
            return operation(payload)
        return original(self, action, permit, counted)

    monkeypatch.setattr(ProtectedExecutor, "execute", observed)
    run_scenario(scenario)
    assert len(calls) == (1 if EXPECTED[scenario][0] == "ALLOW" else 0)


def test_bypass_regression_cannot_be_reported_as_successfully_blocked(monkeypatch):
    from sentinel_ref.gateway import ProtectedExecutor
    monkeypatch.setattr(ProtectedExecutor, "execute", lambda self, action, permit, operation: operation(action.payload))
    with pytest.raises(RuntimeError, match="bypass unexpectedly executed"):
        run_scenario("direct-executor-bypass")
