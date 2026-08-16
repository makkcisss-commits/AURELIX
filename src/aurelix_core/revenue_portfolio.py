"""Unified revenue-source portfolio and replacement control plane.

This module plans and measures revenue channels. It never fabricates revenue,
creates third-party accounts, or performs payments. Realized measurements must
carry an externally verifiable reference before they can influence economic
feedback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4


class SourceStatus(StrEnum):
    DISCOVERED = "discovered"
    VALIDATING = "validating"
    READY = "ready"
    ACTIVE = "active"
    DEGRADED = "degraded"
    PAUSED = "paused"
    RETIRED = "retired"


@dataclass
class RevenueSource:
    source_id: str
    owner_role: str
    name: str
    channel: str
    status: SourceStatus = SourceStatus.DISCOVERED
    expected_daily_eur: Decimal = Decimal("0")
    realized_daily_eur: Decimal = Decimal("0")
    confidence: float = 0.0
    risk: float = 0.0
    human_approval_required: bool = True
    human_approved: bool = False
    replacement_for: str | None = None
    connector: str | None = None
    last_checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def viable(self) -> bool:
        return self.status in {SourceStatus.READY, SourceStatus.ACTIVE} and self.confidence >= 0.6 and self.risk <= 0.4 and (not self.human_approval_required or self.human_approved)


@dataclass(frozen=True)
class PortfolioTarget:
    minimum_sources: int = 100
    preferred_sources: int = 150
    maximum_sources: int = 500
    minimum_daily_eur_per_source: Decimal = Decimal("1")


class RevenuePortfolio:
    """Manages many independent revenue experiments behind one business objective."""
    def __init__(self, target: PortfolioTarget | None = None) -> None:
        self.target = target or PortfolioTarget()
        self._sources: dict[str, RevenueSource] = {}
        self._events: list[dict] = []

    def add(self, source: RevenueSource) -> RevenueSource:
        if len(self._sources) >= self.target.maximum_sources:
            raise ValueError("maximum revenue-source portfolio size reached")
        if source.source_id in self._sources:
            raise ValueError("duplicate revenue source")
        if source.expected_daily_eur < 0 or source.realized_daily_eur < 0:
            raise ValueError("revenue values cannot be negative")
        self._sources[source.source_id] = source
        self._event("source.added", source_id=source.source_id)
        return source

    def discover(self, *, owner_role: str, name: str, channel: str, expected_daily_eur: Decimal = Decimal("0"), confidence: float = 0.0, risk: float = 1.0, connector: str | None = None) -> RevenueSource:
        source = RevenueSource(str(uuid4()), owner_role, name, channel, expected_daily_eur=expected_daily_eur, confidence=max(0.0, min(1.0, confidence)), risk=max(0.0, min(1.0, risk)), connector=connector)
        return self.add(source)

    def approve(self, source_id: str) -> RevenueSource:
        source = self.get(source_id)
        source.human_approved = True
        source.status = SourceStatus.READY
        self._event("source.approved", source_id=source_id)
        return source

    def activate(self, source_id: str) -> RevenueSource:
        source = self.get(source_id)
        if source.human_approval_required and not source.human_approved:
            raise PermissionError("human approval is required before activation")
        if not source.connector:
            raise RuntimeError("source has no real connector")
        source.status = SourceStatus.ACTIVE
        source.last_checked_at = datetime.now(timezone.utc)
        self._event("source.activated", source_id=source_id)
        return source

    def record_realized_daily(self, source_id: str, amount_eur: Decimal, *, external_reference: str | None = None) -> RevenueSource:
        if amount_eur < 0:
            raise ValueError("realized revenue cannot be negative")
        if external_reference is None or not external_reference.strip():
            raise ValueError("realized revenue requires an externally verifiable reference")
        source = self.get(source_id)
        source.realized_daily_eur = amount_eur
        source.last_checked_at = datetime.now(timezone.utc)
        if source.status == SourceStatus.ACTIVE and amount_eur == 0:
            source.status = SourceStatus.DEGRADED
        self._event("source.revenue_recorded", source_id=source_id, amount_eur=str(amount_eur), external_reference=external_reference.strip())
        return source

    def health(self) -> dict:
        active = [s for s in self._sources.values() if s.status == SourceStatus.ACTIVE]
        viable = [s for s in self._sources.values() if s.viable]
        daily = sum((s.realized_daily_eur for s in self._sources.values()), Decimal("0"))
        return {"total_sources": len(self._sources), "active_sources": len(active), "viable_sources": len(viable), "daily_realized_eur": daily, "minimum_target_met": len(viable) >= self.target.minimum_sources, "preferred_target_met": len(viable) >= self.target.preferred_sources, "maximum_target": self.target.maximum_sources}

    def needs_replacement(self) -> list[RevenueSource]:
        return [s for s in self._sources.values() if s.status in {SourceStatus.DEGRADED, SourceStatus.RETIRED}]

    def replacement_candidates(self) -> list[RevenueSource]:
        return [s for s in self._sources.values() if s.status == SourceStatus.READY and s.viable]

    def replace(self, failed_source_id: str, candidate_source_id: str) -> RevenueSource:
        failed = self.get(failed_source_id)
        candidate = self.get(candidate_source_id)
        if failed.status not in {SourceStatus.DEGRADED, SourceStatus.RETIRED}:
            raise ValueError("only degraded or retired sources can be replaced")
        if not candidate.viable:
            raise ValueError("replacement candidate is not viable")
        candidate.replacement_for = failed.source_id
        candidate.status = SourceStatus.ACTIVE
        failed.status = SourceStatus.RETIRED
        self._event("source.replaced", failed_source_id=failed.source_id, replacement_source_id=candidate.source_id)
        return candidate

    def get(self, source_id: str) -> RevenueSource:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise KeyError(f"unknown revenue source: {source_id}") from exc

    def all(self) -> list[RevenueSource]:
        return list(self._sources.values())

    def events(self) -> list[dict]:
        return list(self._events)

    def _event(self, event: str, **data) -> None:
        self._events.append({"event": event, "time": datetime.now(timezone.utc).isoformat(), **data})
