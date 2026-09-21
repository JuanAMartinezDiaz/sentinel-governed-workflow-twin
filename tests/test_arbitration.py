from sentinel_ref.models import Disposition, RiskTier
from conftest import make_action


def test_unregistered_agent_is_denied(engine):
    result = engine.evaluate(make_action(agent_id="unknown"))
    assert result.disposition is Disposition.DENY


def test_unauthorized_action_is_denied(engine):
    result = engine.evaluate(make_action(action_class="DELETE_ACCOUNT"))
    assert result.disposition is Disposition.DENY


def test_unapproved_tool_is_denied(engine):
    result = engine.evaluate(make_action(tool_name="shell"))
    assert result.disposition is Disposition.DENY


def test_risk_ceiling_is_enforced(engine):
    result = engine.evaluate(make_action(risk_tier=RiskTier.CRITICAL, confidence=1.0))
    assert result.disposition is Disposition.DENY


def test_low_confidence_selects_fallback(engine):
    result = engine.evaluate(
        make_action(
            action_class="DRAFT_RECOMMENDATION",
            tool_name="recommendation_service",
            risk_tier=RiskTier.MODERATE,
            confidence=0.50,
        )
    )
    assert result.disposition is Disposition.FALLBACK


def test_high_risk_requires_human_approval(engine):
    result = engine.evaluate(
        make_action(
            action_class="COMMIT_ACCOUNT_CHANGE",
            tool_name="account_change_api",
            risk_tier=RiskTier.HIGH,
            confidence=0.97,
        )
    )
    assert result.disposition is Disposition.REQUIRE_APPROVAL


def test_high_risk_allows_after_human_approval(engine):
    result = engine.evaluate(
        make_action(
            action_class="COMMIT_ACCOUNT_CHANGE",
            tool_name="account_change_api",
            risk_tier=RiskTier.HIGH,
            confidence=0.97,
        ),
        human_approved=True,
    )
    assert result.disposition is Disposition.ALLOW
