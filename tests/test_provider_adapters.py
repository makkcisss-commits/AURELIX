import pytest

from aurelix_runtime.provider_adapters import (
    ModelProviderAdapter,
    ProviderDenied,
    ProviderPolicy,
    ResearchProviderAdapter,
    SecretResolver,
)


def test_research_provider_policy_and_mapping():
    adapter = ResearchProviderAdapter(
        ProviderPolicy("research", frozenset({"search.read"}), max_items=1),
        lambda q, n: [{"source": "source-a", "claim": q, "confidence": 0.9, "verified": True}],
    )
    result = adapter.search("objective")
    assert len(result) == 1
    assert result[0].verified is True


def test_provider_denies_unlisted_operation():
    adapter = ModelProviderAdapter(ProviderPolicy("model", frozenset()), lambda p: "ok")
    with pytest.raises(ProviderDenied):
        adapter.generate("prompt")


def test_secret_resolver_requires_host_config():
    resolver = SecretResolver(lambda _: None)
    with pytest.raises(RuntimeError):
        resolver.require("MODEL_PROVIDER_API_KEY")
