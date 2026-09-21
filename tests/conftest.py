from __future__ import annotations

import pytest

from sentinel_ref.arbitration import ArbitrationEngine
from sentinel_ref.authority import AuthorityRegistry
from sentinel_ref.gateway import ProtectedExecutor
from sentinel_ref.models import AgentAuthority, ProposedAction, RiskTier


@pytest.fixture
def registry() -> AuthorityRegistry:
    registry = AuthorityRegistry()
    registry.register(
        AgentAuthority(
            agent_id="agent-1",
            allowed_actions=frozenset({"READ_CASE", "DRAFT_RECOMMENDATION", "COMMIT_ACCOUNT_CHANGE"}),
            allowed_tools=frozenset({"case_api", "recommendation_service", "account_change_api"}),
            max_risk_tier=RiskTier.HIGH,
        )
    )
    return registry


@pytest.fixture
def engine(registry: AuthorityRegistry) -> ArbitrationEngine:
    return ArbitrationEngine(registry)


@pytest.fixture
def gateway(engine: ArbitrationEngine) -> ProtectedExecutor:
    return ProtectedExecutor(engine)


def make_action(**overrides) -> ProposedAction:
    values = dict(
        workflow_id="wf-1",
        step_id="S01",
        agent_id="agent-1",
        action_class="READ_CASE",
        tool_name="case_api",
        risk_tier=RiskTier.LOW,
        confidence=0.95,
        reversible=True,
        payload={"case_id": "SYN-1"},
    )
    values.update(overrides)
    return ProposedAction(**values)
