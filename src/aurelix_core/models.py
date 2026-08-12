from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class AutonomyLevel(str, Enum):
    A0 = "A0"  # observe only
    A1 = "A1"  # recommend
    A2 = "A2"  # execute reversible low-risk actions
    A3 = "A3"  # execute bounded operational actions
    A4 = "A4"  # protected; explicit owner authorization required


class DecisionStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class ActionClass(str, Enum):
    READ = "read"
    RESEARCH = "research"
    BUILD = "build"
    DEPLOY = "deploy"
    FINANCIAL = "financial"
    SECURITY = "security"
    GOVERNANCE = "governance"


@dataclass(frozen=True)
class Actor:
    id: str
    role: str
    autonomy: AutonomyLevel = AutonomyLevel.A0


@dataclass(frozen=True)
class DecisionRequest:
    actor: Actor
    action: ActionClass
    reason: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Decision:
    request_id: str
    status: DecisionStatus
    allowed: bool
    reason: str
    requires_owner: bool
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
