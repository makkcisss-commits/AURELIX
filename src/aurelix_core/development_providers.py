"""Deterministic local providers for development and end-to-end verification."""
from __future__ import annotations

from typing import Any

from .model_gateway import ModelProvider
from aurelix_runtime.integrated_engines import Evidence


class DevelopmentModelProvider(ModelProvider):
    """Offline model substitute; never contacts an external service."""

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "Development lesson synthesized from supplied evidence."

    def structured_output(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": "Development automation opportunity",
            "problem": "A bounded workflow remains manual.",
            "proposed_solution": "Automate the bounded workflow.",
            "expected_value": "Reduce cycle time.",
            "estimated_cost": 100.0,
            "risk": 2,
            "confidence": 0.8,
        }

    def embeddings(self, text: str) -> list[float]:
        return [1.0, 0.0]

    def health(self) -> bool:
        return True


def development_research_provider(query: str) -> list[Evidence]:
    """Deterministic evidence source for local development."""
    return [
        Evidence(
            "https://example.test/aurelix-development-source",
            f"Development finding for {query}",
            0.95,
            True,
        )
    ]
