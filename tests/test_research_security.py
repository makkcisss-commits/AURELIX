import pytest

from aurelix_core.research_security import validate_content_size, validate_research_url


def test_https_public_url_is_accepted() -> None:
    assert validate_research_url("https://example.com/article") == "https://example.com/article"


def test_non_https_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_research_url("http://example.com")


def test_private_ip_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_research_url("https://127.0.0.1/internal")


def test_embedded_credentials_are_rejected() -> None:
    with pytest.raises(ValueError):
        validate_research_url("https://user:pass@example.com")


def test_large_response_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_content_size(5_000_001)
