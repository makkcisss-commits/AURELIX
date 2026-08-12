"""Explicit provider adapters for AURELIX.

Providers are intentionally dependency-free here: HTTP/model/search clients are
injected by the host application. The adapters enforce a narrow interface and
never expose provider credentials to engine prompts or engine state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .integrated_engines import Evidence


@dataclass(frozen=True)
class ProviderPolicy:
    name: str
    allowed_operations: frozenset[str]
    max_items: int = 20


class ProviderDenied(PermissionError):
    pass


class ResearchProviderAdapter:
    def __init__(self, policy: ProviderPolicy, search_fn: Callable[[str, int], List[Dict[str, Any]]]):
        self.policy = policy
        self.search_fn = search_fn

    def search(self, query: str) -> List[Evidence]:
        if "search.read" not in self.policy.allowed_operations:
            raise ProviderDenied(f"provider operation denied: {self.policy.name}")
        rows = self.search_fn(query, self.policy.max_items)
        return [
            Evidence(
                source=str(row.get("source", "unknown")),
                claim=str(row.get("claim", "")),
                confidence=float(row.get("confidence", 0.0)),
                verified=bool(row.get("verified", False)),
            )
            for row in rows[: self.policy.max_items]
        ]


class ModelProviderAdapter:
    def __init__(self, policy: ProviderPolicy, generate_fn: Callable[[str], str]):
        self.policy = policy
        self.generate_fn = generate_fn

    def generate(self, prompt: str) -> str:
        if "model.generate" not in self.policy.allowed_operations:
            raise ProviderDenied(f"model operation denied: {self.policy.name}")
        return self.generate_fn(prompt)


class SecretResolver:
    """Resolve secrets at the host boundary; never serializes them into engine state."""

    def __init__(self, getter: Callable[[str], Optional[str]]):
        self.getter = getter

    def require(self, name: str) -> str:
        value = self.getter(name)
        if not value:
            raise RuntimeError(f"required secret is not configured: {name}")
        return value
