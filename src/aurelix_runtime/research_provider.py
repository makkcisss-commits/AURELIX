"""HTTPS adapter for a configured external research service."""
from __future__ import annotations

import os
from typing import Any

import httpx

from .integrated_engines import Evidence


class ResearchProviderError(RuntimeError):
    pass


class HttpResearchProvider:
    def __init__(self, url: str, api_key: str | None = None, timeout: float = 20.0):
        if not url.startswith("https://"):
            raise ValueError("research provider URL must use HTTPS")
        self.url = url
        self.api_key = api_key
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "HttpResearchProvider | None":
        url = os.environ.get("AURELIX_RESEARCH_URL", "").strip()
        if not url:
            return None
        return cls(url, os.environ.get("AURELIX_RESEARCH_API_KEY"))

    def __call__(self, objective: str) -> list[Evidence]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = httpx.post(
                self.url,
                json={"query": objective},
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ResearchProviderError(f"research provider request failed: {exc}") from exc

        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise ResearchProviderError("research provider returned invalid results")

        evidence: list[Evidence] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            source = str(result.get("source", "")).strip()
            claim = str(result.get("claim", "")).strip()
            if not source or not claim:
                continue
            confidence = float(result.get("confidence", 0.0))
            verified = bool(result.get("verified", False))
            evidence.append(Evidence(source, claim, max(0.0, min(1.0, confidence)), verified))
        return evidence
