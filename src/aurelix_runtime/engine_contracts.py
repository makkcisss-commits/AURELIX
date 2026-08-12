"""Typed contracts for the AURELIX engineering loop.

The contracts deliberately separate data produced by engines from authority to
execute external side effects. Engine outputs are evidence/proposals until the
Governor/approval layer authorizes an action.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class EngineName(str, Enum):
    GOVERNOR = "governor"
    RESEARCH = "research"
    ACADEMY = "academy"
    KNOWLEDGE = "knowledge"
    INNOVATION = "innovation"
    EXPERIMENT = "experiment"
    EVALUATION = "evaluation"
    OPPORTUNITY = "opportunity"
    BUSINESS = "business"


@dataclass(frozen=True)
class Evidence:
    source: str
    claim: str
    confidence: float
    retrieved_at: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class EngineContext:
    objective: str
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    data: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)

    def add_evidence(self, source: str, claim: str, confidence: float, metadata=None) -> None:
        confidence = max(0.0, min(1.0, float(confidence)))
        self.evidence.append(Evidence(
            source=source,
            claim=claim,
            confidence=confidence,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        ))

    def propose(self, kind: str, payload: Mapping[str, Any]) -> None:
        self.proposals.append({"kind": kind, "payload": dict(payload), "trace_id": self.trace_id})
