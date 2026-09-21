import pytest

from sentinel_ref.models import ExecutionPermit, RiskTier
from conftest import make_action


def _high_risk_action():
    return make_action(
        action_class="COMMIT_ACCOUNT_CHANGE",
        tool_name="account_change_api",
        risk_tier=RiskTier.HIGH,
        confidence=0.97,
    )


def test_direct_execution_without_permit_is_blocked(gateway):
    action = _high_risk_action()
    with pytest.raises(PermissionError):
        gateway.execute(action, None, lambda payload: payload)


def test_tampered_permit_is_blocked(gateway):
    action = _high_risk_action()
    _, permit = gateway.authorize(action, human_approved=True)
    bad = ExecutionPermit(action_fingerprint=permit.action_fingerprint, signature="0" * 64)
    with pytest.raises(PermissionError):
        gateway.execute(action, bad, lambda payload: payload)


def test_valid_permit_executes_exact_action(gateway):
    action = _high_risk_action()
    _, permit = gateway.authorize(action, human_approved=True)
    result = gateway.execute(action, permit, lambda payload: {"ok": True, **payload})
    assert result["ok"] is True
