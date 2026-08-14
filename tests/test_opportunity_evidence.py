from datetime import datetime, timezone, timedelta

import pytest

from aurelix_core.opportunity_evidence import (
    EvidenceKind,
    qualify_opportunity_evidence,
    record_evidence,
)


def test_opportunity_requires_multiple_distinct_sources_and_verification():
    observed = datetime.now(timezone.utc) - timedelta(minutes=1)
    evidence = [
        record_evidence(
            opportunity_id="opp-1",
            kind=EvidenceKind.MARKET_SIGNAL,
            source_url="https://example.com/market",
            source_name="Market source",
            summary="Observed demand signal",
            observed_at=observed,
        ),
        record_evidence(
            opportunity_id="opp-1",
            kind=EvidenceKind.CUSTOMER_NEED,
            source_url="https://example.org/customer",
            source_name="Customer source",
            summary="Customer need confirmed",
            observed_at=observed,
            independently_verified=True,
        ),
    ]

    result = qualify_opportunity_evidence("opp-1", evidence)

    assert result.qualified is True
    assert result.evidence_count == 2
    assert result.distinct_sources == 2
    assert result.verified_count == 1
    assert result.reasons == ()


def test_one_source_or_unverified_evidence_is_not_qualified():
    evidence = [
        record_evidence(
            opportunity_id="opp-2",
            kind=EvidenceKind.MARKET_SIGNAL,
            source_url="https://example.com/market",
            source_name="Market source",
            summary="Possible demand",
        ),
        record_evidence(
            opportunity_id="opp-2",
            kind=EvidenceKind.PRICING,
            source_url="https://example.com/pricing",
            source_name="Market source",
            summary="Indicative pricing",
        ),
    ]

    result = qualify_opportunity_evidence("opp-2", evidence)

    assert result.qualified is False
    assert "need at least 2 distinct sources" in result.reasons
    assert "need at least one independently verified record" in result.reasons


def test_future_evidence_is_rejected():
    with pytest.raises(ValueError, match="cannot be in the future"):
        record_evidence(
            opportunity_id="opp-3",
            kind=EvidenceKind.MARKET_SIGNAL,
            source_url="https://example.com/market",
            source_name="Market source",
            summary="Future claim",
            observed_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
