import httpx
import pytest

from aurelix_runtime.research_provider import HttpResearchProvider, ResearchProviderError


def test_provider_rejects_plain_http():
    with pytest.raises(ValueError):
        HttpResearchProvider("http://example.test/research")


def test_provider_parses_research_results(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"results": [{"source": "paper", "claim": "finding", "confidence": 0.8, "verified": True}]}

    def fake_post(*args, **kwargs):
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    evidence = HttpResearchProvider("https://example.test/research")("objective")
    assert evidence[0].source == "paper"
    assert evidence[0].verified is True


def test_provider_rejects_invalid_response(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"unexpected": []}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: Response())
    with pytest.raises(ResearchProviderError):
        HttpResearchProvider("https://example.test/research")("objective")
