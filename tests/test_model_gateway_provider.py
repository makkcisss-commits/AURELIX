import httpx
import pytest

from aurelix_core.model_gateway import (
    GenerationRequest,
    GovernedModelGateway,
    ModelProviderError,
    OpenAICompatibleProvider,
)


def test_structured_output_accepts_fenced_json(monkeypatch):
    provider = OpenAICompatibleProvider("https://example.test/v1", None, "test-model")
    monkeypatch.setattr(provider, "generate", lambda prompt, max_tokens=2000: '```json\n{"title":"ok"}\n```')

    assert provider.structured_output("prompt", {"title": "string"}) == {"title": "ok"}


def test_structured_output_rejects_non_object(monkeypatch):
    provider = OpenAICompatibleProvider("https://example.test/v1", None, "test-model")
    monkeypatch.setattr(provider, "generate", lambda prompt, max_tokens=2000: '[1, 2, 3]')

    with pytest.raises(ModelProviderError):
        provider.structured_output("prompt", {"title": "string"})


def test_generate_supports_content_blocks(monkeypatch):
    provider = OpenAICompatibleProvider("https://example.test/v1", None, "test-model")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": [{"type": "text", "text": "hello"}]}}]}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: Response())
    assert provider.generate("prompt") == "hello"


def test_denied_model_request_is_audited():
    events = []
    gateway = GovernedModelGateway(
        provider=type("Provider", (), {
            "generate": lambda self, prompt, max_tokens=2000: "ok",
            "structured_output": lambda self, prompt, schema: {},
            "embeddings": lambda self, text: [1.0],
            "health": lambda self: True,
        })(),
        policy=lambda request: False,
        audit=lambda event, **metadata: events.append((event, metadata)),
    )

    with pytest.raises(ModelProviderError):
        gateway.generate(GenerationRequest("prompt", action="test.action", actor_id="test"))

    assert events[0][0] == "model.request.denied"
