import pytest

from aurelix_core.research_adapters import StaticResearchAdapter


def test_static_adapter_normalizes_and_hashes_content() -> None:
    adapter = StaticResearchAdapter({"https://example.test/a": "evidence"})
    document = adapter.fetch("https://example.test/a")
    assert document.source.uri == "https://example.test/a"
    assert document.content == "evidence"
    assert len(document.content_hash) == 64
    assert document.warnings


def test_adapter_rejects_non_http_uri() -> None:
    adapter = StaticResearchAdapter({})
    with pytest.raises(ValueError):
        adapter.fetch("file:///etc/passwd")
