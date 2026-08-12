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
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
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
            response = httpx.post(
                f"{self.base_url}/embeddings",
                json={"model": self.model, "input": text},
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            value = response.json()["data"][0]["embedding"]
            if not isinstance(value, list):
                raise ValueError("invalid embedding")
            return [float(x) for x in value]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelProviderError(f"embedding failed: {exc}") from exc

    def health(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/models", headers=self._headers(), timeout=min(self.timeout, 10.0))
            return response.is_success
        except httpx.HTTPError:
            return False


class GovernedModelGateway:
    def __init__(
        self,
        provider: ModelProvider,
        policy: Callable[[GenerationRequest], bool] | None = None,
        audit: Callable[..., Any] | None = None,
    ):
        self.provider = provider
        self.policy = policy
        self.audit = audit

    def _authorize(self, request: GenerationRequest) -> None:
        if self.policy and not self.policy(request):
            raise ModelProviderError("model request denied by policy")

    def _audit(self, event: str, request: GenerationRequest, **metadata: Any) -> None:
        if self.audit:
            self.audit(event, actor_id=request.actor_id, action=request.action, **metadata)

    def generate(self, request: GenerationRequest) -> str:
        self._authorize(request)
        self._audit("model.generation.requested", request)
        try:
            result = self.provider.generate(request.prompt, request.max_tokens)
        except Exception as exc:
            self._audit("model.generation.failed", request, error=str(exc))
            raise
        self._audit("model.generation.completed", request)
        return result

    def structured_output(self, request: GenerationRequest, schema: dict[str, Any]) -> dict[str, Any]:
        self._authorize(request)
        self._audit("model.structured.requested", request)
        try:
            result = self.provider.structured_output(request.prompt, schema)
        except Exception as exc:
            self._audit("model.structured.failed", request, error=str(exc))
            raise
        self._audit("model.structured.completed", request)
        return result

    def embeddings(self, request: GenerationRequest) -> list[float]:
        self._authorize(request)
        self._audit("model.embedding.requested", request)
        try:
            result = self.provider.embeddings(request.prompt)
        except Exception as exc:
            self._audit("model.embedding.failed", request, error=str(exc))
            raise
        self._audit("model.embedding.completed", request)
        return result

    def health(self) -> bool:
        return self.provider.health()
