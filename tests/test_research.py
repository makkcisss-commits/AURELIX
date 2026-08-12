from aurelix_core.research import ResearchEngine, ResearchSource, SourceKind
import pytest


def test_finding_requires_known_evidence() -> None:
    engine = ResearchEngine()
    engine.add_source(ResearchSource("s1", "Official source", "https://example.com", SourceKind.WEB))
    finding = engine.add_finding(
        query="market",
        claim="A claim supported by evidence",
        source_ids=["s1"],
        confidence=0.9,
    )
    assert finding.source_ids == ("s1",)
    assert finding.confidence == 0.9


def test_unknown_source_is_rejected() -> None:
    engine = ResearchEngine()
    with pytest.raises(ValueError):
        engine.add_finding(query="x", claim="y", source_ids=["missing"], confidence=0.5)


def test_confidence_is_bounded() -> None:
    engine = ResearchEngine()
    engine.add_source(ResearchSource("s1", "Source", "https://example.com", SourceKind.WEB))
    with pytest.raises(ValueError):
        engine.add_finding(query="x", claim="y", source_ids=["s1"], confidence=1.2)
