from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from hashlib import sha256
import json
from typing import Any


class RiskTier(IntEnum):
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


class Disposition(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    FALLBACK = "FALLBACK"


@dataclass(frozen=True)
class ProposedAction:
    workflow_id: str
    step_id: str
    agent_id: str
    action_class: str
    tool_name: str
    risk_tier: RiskTier
    confidence: float
    reversible: bool = True
    payload: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        canonical = {
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "action_class": self.action_class,
            "tool_name": self.tool_name,
            "risk_tier": int(self.risk_tier),
            "confidence": round(self.confidence, 6),
            "reversible": self.reversible,
            "payload": self.payload,
        }
        encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class AgentAuthority:
    agent_id: str
    allowed_actions: frozenset[str]
    allowed_tools: frozenset[str]
    max_risk_tier: RiskTier


@dataclass(frozen=True)
class TraceEntry:
    check: str
    status: str
    detail: str


@dataclass(frozen=True)
class ArbitrationResult:
    disposition: Disposition
    reason: str
    trace: tuple[TraceEntry, ...]


@dataclass(frozen=True)
class ExecutionPermit:
    action_fingerprint: str
    signature: str
