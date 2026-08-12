from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceProfile:
    source_ref: str
    uri: str
    publisher: str
    source_type: str
    published_at: datetime | None
    retrieved_at: datetime
    authority: float
    freshness: float
    independence_group: str

    @property
    def quality_score(self) -> float:
        return round(0.5 * self.authority + 0.3 * self.freshness + 0.2 * min(1.0, len(self.independence_group) / 10), 4)


def profile_source(*, source_ref: str, uri: str, publisher: str, source_type: str,
                   authority: float, freshness: float,
                   published_at: datetime | None = None,
                   independence_group: str = "unknown") -> SourceProfile:
    parsed = urlparse(uri)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("source URI must be an absolute HTTP(S) URL")
    if not source_ref.strip() or not publisher.strip() or not source_type.strip():
        raise ValueError("source_ref, publisher and source_type are required")
    if not 0 <= authority <= 1 or not 0 <= freshness <= 1:
        raise ValueError("authority and freshness must be between 0 and 1")
    return SourceProfile(
        source_ref=source_ref, uri=uri, publisher=publisher,
        source_type=source_type, published_at=published_at,
        retrieved_at=datetime.now(timezone.utc), authority=authority,
        freshness=freshness, independence_group=independence_group,
    )


def prioritize_sources(sources: list[SourceProfile]) -> list[SourceProfile]:
    return sorted(sources, key=lambda source: source.quality_score, reverse=True)


def independent_groups(sources: list[SourceProfile]) -> set[str]:
    return {source.independence_group for source in sources if source.independence_group != "unknown"}
