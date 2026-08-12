"""Provider-agnostic model gateway with explicit policy and audit hooks."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import os
from typing import Any, Callable

import httpx


class ModelProviderError(RuntimeError):
    pass


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2000) -> str: ...

    @abstractmethod
    def structured_output(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def embeddings(self, text: str) -> list[float]: ...

    @abstractmethod
    def health(self) -> bool: ...


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    max_tokens: int = 2000
    action: str = "model.generate"
    actor_id: str = "system"


class OpenAICompatibleProvider(ModelProvider):
    """Works with OpenAI-compatible /chat/completions and /embeddings APIs."""

    def __init__(self, base_url: str, api_key: str | None, model: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider | None":
        base = os.getenv("AURELIX_MODEL_BASE_URL", "").strip()
        if not base:
            return None
        return cls(base, os.getenv("AURELIX_MODEL_API_KEY"), os.getenv("AURELIX_MODEL_NAME", "gpt-4o-mini"))

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        try:
            r = httpx.post(f"{self.base_url}/chat/completions", json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            return str(data["choices"][0]["message"]["content"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelProviderError(f"model generation failed: {exc}") from exc

    def structured_output(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        raw = self.generate(prompt + "\nReturn only JSON matching this schema:\n" + json.dumps(schema), 2000)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ModelProviderError("model returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise ModelProviderError("model structured output must be an object")
        return value

    def embeddings(self, text: str) -> list[float]:
        try:
            r = httpx.post(f"{self.base_url}/embeddings", json={"model": self.model, "input": text}, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            value = r.json()["data"][0]["embedding"]
            if not isinstance(value, list):
                raise ValueError("invalid embedding")
            return [float(x) for x in value]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelProviderError(f"embedding failed: {exc}") from exc

    def health(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/models", headers=self._headers(), timeout=min(self.timeout, 10.0))
            return r.is_success
        except httpx.HTTPError:
            return False


class GovernedModelGateway:
    def __init__(self, provider: ModelProvider, policy: Callable[[GenerationRequest], bool] | None = None, audit: Callable[..., Any] | None = None):
        self.provider = provider
        self.policy = policy
        self.audit = audit

    def generate(self, request: GenerationRequest) -> str:
        if self.policy and not self.policy(request):
            raise ModelProviderError("model request denied by policy")
        if self.audit:
            self.audit("model.generation.requested", actor_id=request.actor_id, action=request.action)
        result = self.provider.generate(request.prompt, request.max_tokens)
        if self.audit:
            self.audit("model.generation.completed", actor_id=request.actor_id, action=request.action)
        return result
