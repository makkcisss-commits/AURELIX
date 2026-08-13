"""HTTPS research adapters with bounded, source-backed retrieval."""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import httpx

from .integrated_engines import Evidence


class ResearchProviderError(RuntimeError):
    pass


class HttpResearchProvider:
    def __init__(self, url: str, api_key: str | None = None, timeout: float = 20.0):
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("research provider URL must use HTTPS")
        self.url = url
        self.api_key = api_key
        self.timeout = max(1.0, min(float(timeout), 120.0))

    @classmethod
    def from_env(cls) -> "HttpResearchProvider | TavilyResearchProvider | None":
        provider = os.environ.get("AURELIX_RESEARCH_PROVIDER", "http").strip().lower()
        if provider == "tavily":
            return TavilyResearchProvider.from_env()
        url = os.environ.get("AURELIX_RESEARCH_URL", "").strip()
        if not url:
            return None
        return cls(url, os.environ.get("AURELIX_RESEARCH_API_KEY"))

    def __call__(self, objective: str) -> list[Evidence]:
        objective = objective.strip()
        if not objective:
            raise ValueError("research objective is required")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = httpx.post(self.url, json={"query": objective}, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ResearchProviderError(f"research provider request failed: {exc}") from exc
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise ResearchProviderError("research provider returned invalid results")
        return _generic_results(results)


class TavilyResearchProvider:
    """Tavily Search API adapter; only returns evidence with HTTPS source URLs."""
    ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout: float = 30.0, max_results: int = 10):
        if not api_key:
            raise ValueError("Tavily API key is required")
        self.api_key = api_key
        self.timeout = max(1.0, min(float(timeout), 120.0))
        self.max_results = max(1, min(int(max_results), 20))

    @classmethod
    def from_env(cls) -> "TavilyResearchProvider | None":
        key = os.environ.get("AURELIX_RESEARCH_API_KEY", "").strip()
        return cls(key) if key else None

    def __call__(self, objective: str) -> list[Evidence]:
        objective = objective.strip()
        if not objective:
            raise ValueError("research objective is required")
        try:
            response = httpx.post(self.ENDPOINT, json={
                "api_key": self.api_key,
                "query": objective,
                "search_depth": "advanced",
                "max_results": self.max_results,
                "include_answer": False,
            }, timeout=self.timeout)
            response.raise_for_status()
            payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ResearchProviderError(f"Tavily request failed: {exc}") from exc
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise ResearchProviderError("Tavily returned invalid results")
        evidence: list[Evidence] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            url = str(result.get("url", "")).strip()
            content = str(result.get("content", "")).strip()
            if not _valid_source_url(url) or not content:
                continue
            try:
                confidence = max(0.0, min(1.0, float(result.get("score", 0.5))))
            except (TypeError, ValueError):
                confidence = 0.5
            evidence.append(Evidence(url, content, confidence, False))
        return evidence


def _valid_source_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _generic_results(results: list[Any]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        source = str(result.get("source", "")).strip()
        claim = str(result.get("claim", "")).strip()
        if not source or not claim or not _valid_source_url(source):
            continue
        try:
            confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0
        evidence.append(Evidence(source, claim, confidence, bool(result.get("verified", False))))
    return evidence
