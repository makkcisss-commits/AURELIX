from aurelix_core.source_intelligence import independent_groups, prioritize_sources, profile_source


def test_sources_are_prioritized_by_quality() -> None:
    low = profile_source(source_ref="a", uri="https://example.com/a", publisher="A", source_type="blog", authority=0.2, freshness=0.2, independence_group="a")
    high = profile_source(source_ref="b", uri="https://example.org/b", publisher="B", source_type="paper", authority=0.9, freshness=0.9, independence_group="b")
    assert prioritize_sources([low, high])[0] is high


def test_independence_groups_are_deduplicated() -> None:
    a = profile_source(source_ref="a", uri="https://example.com/a", publisher="A", source_type="paper", authority=0.8, freshness=0.8, independence_group="publisher-a")
    b = profile_source(source_ref="b", uri="https://example.com/b", publisher="A", source_type="mirror", authority=0.8, freshness=0.8, independence_group="publisher-a")
    assert independent_groups([a, b]) == {"publisher-a"}
