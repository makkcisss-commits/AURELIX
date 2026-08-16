"""Durable adapter for the existing :class:`RevenuePortfolio` contract.

The existing portfolio remains the business API. This adapter only adds
persistence and restart recovery in the RuntimeStore's SQLite database.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from .revenue_portfolio import PortfolioTarget, RevenuePortfolio, RevenueSource, SourceStatus


class DurableRevenuePortfolio(RevenuePortfolio):
    """RevenuePortfolio with transparent persistence and restart recovery."""

    _TABLE = "revenue_portfolio_sources"
    _EVENT_TABLE = "revenue_portfolio_events"

    def __init__(self, store, target: PortfolioTarget | None = None) -> None:
        self._store = store
        super().__init__(target)
        self._ensure_schema()
        self._restore()

    def _ensure_schema(self) -> None:
        with self._store.lock, self._store.db:
            self._store.db.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS {self._TABLE} (
                    source_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS {self._EVENT_TABLE} (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _source_payload(source: RevenueSource) -> dict[str, Any]:
        return {
            "source_id": source.source_id,
            "owner_role": source.owner_role,
            "name": source.name,
            "channel": source.channel,
            "status": source.status.value,
            "expected_daily_eur": str(source.expected_daily_eur),
            "realized_daily_eur": str(source.realized_daily_eur),
            "confidence": source.confidence,
            "risk": source.risk,
            "human_approval_required": source.human_approval_required,
            "human_approved": source.human_approved,
            "replacement_for": source.replacement_for,
            "connector": source.connector,
            "last_checked_at": source.last_checked_at.isoformat(),
        }

    @staticmethod
    def _source_from_payload(payload: dict[str, Any]) -> RevenueSource:
        return RevenueSource(
            source_id=payload["source_id"],
            owner_role=payload["owner_role"],
            name=payload["name"],
            channel=payload["channel"],
            status=SourceStatus(payload["status"]),
            expected_daily_eur=Decimal(payload["expected_daily_eur"]),
            realized_daily_eur=Decimal(payload["realized_daily_eur"]),
            confidence=float(payload["confidence"]),
            risk=float(payload["risk"]),
            human_approval_required=bool(payload["human_approval_required"]),
            human_approved=bool(payload["human_approved"]),
            replacement_for=payload.get("replacement_for"),
            connector=payload.get("connector"),
            last_checked_at=datetime.fromisoformat(payload["last_checked_at"]),
        )

    def _restore(self) -> None:
        with self._store.lock:
            rows = self._store.db.execute(
                f"SELECT payload FROM {self._TABLE} ORDER BY source_id"
            ).fetchall()
            events = self._store.db.execute(
                f"SELECT event, payload, created_at FROM {self._EVENT_TABLE} ORDER BY event_id"
            ).fetchall()
        self._sources = {}
        for row in rows:
            source = self._source_from_payload(json.loads(row[0]))
            self._sources[source.source_id] = source
        self._events = [
            {"event": row[0], **json.loads(row[1]), "time": row[2]}
            for row in events
        ]

    def _persist_source(self, source: RevenueSource) -> None:
        payload = self._source_payload(source)
        with self._store.lock, self._store.db:
            self._store.db.execute(
                f"INSERT INTO {self._TABLE}(source_id,payload,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(source_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (source.source_id, json.dumps(payload, sort_keys=True), datetime.now(timezone.utc).isoformat()),
            )

    def _persist_new_events(self, start: int) -> None:
        events = self._events[start:]
        if not events:
            return
        with self._store.lock, self._store.db:
            for event in events:
                payload = {k: v for k, v in event.items() if k not in {"event", "time"}}
                self._store.db.execute(
                    f"INSERT INTO {self._EVENT_TABLE}(event,payload,created_at) VALUES(?,?,?)",
                    (event["event"], json.dumps(payload, sort_keys=True, default=str), event["time"]),
                )

    def add(self, source: RevenueSource) -> RevenueSource:
        start = len(self._events)
        result = super().add(source)
        self._persist_source(result)
        self._persist_new_events(start)
        return result

    def approve(self, source_id: str) -> RevenueSource:
        start = len(self._events)
        result = super().approve(source_id)
        self._persist_source(result)
        self._persist_new_events(start)
        return result

    def activate(self, source_id: str) -> RevenueSource:
        start = len(self._events)
        result = super().activate(source_id)
        self._persist_source(result)
        self._persist_new_events(start)
        return result

    def record_realized_daily(self, source_id: str, amount_eur: Decimal) -> RevenueSource:
        start = len(self._events)
        result = super().record_realized_daily(source_id, amount_eur)
        self._persist_source(result)
        self._persist_new_events(start)
        return result

    def replace(self, failed_source_id: str, candidate_source_id: str) -> RevenueSource:
        start = len(self._events)
        result = super().replace(failed_source_id, candidate_source_id)
        self._persist_source(self.get(failed_source_id))
        self._persist_source(result)
        self._persist_new_events(start)
        return result

    def reload(self) -> None:
        """Reload the durable portfolio state without changing the public API."""
        self._restore()
