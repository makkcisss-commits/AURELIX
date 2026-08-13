"""Turns operational outcomes into durable, traceable learning."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from .integrated_engines import Evidence, KnowledgeItem


class LearningFeedbackLoop:
    """Feeds diagnostics, validations and recoveries back into durable knowledge."""

    def __init__(self, factory) -> None:
        self.factory = factory

    def record_cycle(self, *, event: str, outcome: str, details: dict[str, Any]) -> dict[str, Any]:
        summary = self._summarize(details)
        item = KnowledgeItem(
            id=str(uuid4()),
            title=f"Operational learning: {event}",
            content=summary,
            evidence=[Evidence(source="aurelix://runtime", claim=summary, confidence=1.0, verified=outcome == "verified")],
            tags=["operational", "feedback", event, outcome],
        )
        self.factory.knowledge.put(item)
        self.factory.runtime.store.audit(
            "academy.feedback.recorded",
            "learning_feedback",
            "learn_from_cycle",
            "succeeded",
            {"knowledge_id": item.id, "event": event, "outcome": outcome},
        )
        return {"knowledge_id": item.id, "event": event, "outcome": outcome}

    @staticmethod
    def _summarize(details: dict[str, Any]) -> str:
        before = details.get("before_validation", {}).get("status")
        after = details.get("after_validation", {}).get("status")
        recovery = details.get("recovery", {}).get("decision")
        execution = details.get("execution", {}).get("status")
        return (
            f"Self-improvement cycle observed execution={execution!r}, "
            f"validation_before={before!r}, validation_after={after!r}, "
            f"recovery_decision={recovery!r}. This record is operational evidence, "
            "not proof of external business or financial success."
        )
