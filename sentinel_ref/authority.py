from __future__ import annotations

from .models import AgentAuthority


class AuthorityRegistry:
    """Declared authority for agents that may participate in governed workflows."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentAuthority] = {}

    def register(self, authority: AgentAuthority) -> None:
        self._agents[authority.agent_id] = authority

    def get(self, agent_id: str) -> AgentAuthority | None:
        return self._agents.get(agent_id)

    def snapshot(self) -> dict[str, AgentAuthority]:
        return dict(self._agents)
