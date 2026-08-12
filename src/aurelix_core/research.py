from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Iterable


class SourceKind(str, Enum):
    WEB = "WEB"
    DOCUMENT = "DOCUMENT"
    DATASET = "DATASET"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    title: str
    uri: str
    kind: SourceKind
    publisher: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class ResearchFinding:
    finding_id: str
    query: str
    claim: str
    source_ids: tuple[str, ...]
    confidence: float
    captured_at: str

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.source_ids:
            raise ValueError("a finding requires at least one source")


class ResearchEngine:
    """Evidence-first research boundary.

    Retrieval is intentionally supplied by adapters. The core stores and
    evaluates normalized evidence; it does not pretend that an unverified
    model output is a source.
    """

    def __init__(self) -> None:
        self._sources: dict[str, ResearchSource] = {}
        self._findings: dict[str, ResearchFinding] = {}

    def add_source(self, source: ResearchSource) -> None:
        self._sources[source.source_id] = source

    def add_finding(self, *, query: str, claim: str,
                    source_ids: Iterable[str], confidence: float) -> ResearchFinding:
        ids = tuple(source_ids)
        if any(source_id not in self._sources for source_id in ids):
            raise ValueError("finding references an unknown source")
        raw = f"{query}\n{claim}\n{'|'.join(ids)}".encode()
        finding_id = hashlib.sha256(raw).hexdigest()[:16]
        finding = ResearchFinding(
            finding_id=finding_id,
            query=query,
            claim=claim,
            source_ids=ids,
            confidence=confidence,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )
        self._findings[finding_id] = finding
        return finding

    def sources(self) -> tuple[ResearchSource, ...]:
        return tuple(self._sources.values())

    def findings(self) -> tuple[ResearchFinding, ...]:
        return tuple(self._findings.values())
