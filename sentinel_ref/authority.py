from __future__ import annotations

from .models import AgentAuthority


class AuthorityRegistry:
    """Declared authority for agents that may participate in governed workflows."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentAuthority] = {}
        self._revisions: dict[str, int] = {}

    def register(self, authority: AgentAuthority) -> None:
        self._agents[authority.agent_id] = authority
        self._revisions[authority.agent_id] = self.revision(authority.agent_id) + 1

    def get(self, agent_id: str) -> AgentAuthority | None:
        return self._agents.get(agent_id)

    def revoke(self, agent_id: str) -> None:
        """Synthetic administrative operation; caller authentication is external."""
        self._agents.pop(agent_id, None)
        self._revisions[agent_id] = self.revision(agent_id) + 1

    def revision(self, agent_id: str) -> int:
        return self._revisions.get(agent_id, 0)

    def snapshot(self) -> dict[str, AgentAuthority]:
        return dict(self._agents)
