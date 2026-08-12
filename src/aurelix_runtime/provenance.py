"""Traceability primitives for AURELIX knowledge and experiments."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ProvenanceRecord:
    record_id: str
    kind: str
    subject_id: str
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=now)


class ProvenanceLedger:
    def __init__(self) -> None:
        self._records: Dict[str, ProvenanceRecord] = {}

    def append(self, kind: str, subject_id: str, parent_ids: List[str] | None = None, **metadata: str) -> ProvenanceRecord:
        record = ProvenanceRecord(str(uuid4()), kind, subject_id, parent_ids or [], metadata)
        self._records[record.record_id] = record
        return record

    def for_subject(self, subject_id: str) -> List[ProvenanceRecord]:
        return [r for r in self._records.values() if r.subject_id == subject_id]

    def lineage(self, subject_id: str) -> List[ProvenanceRecord]:
        result: List[ProvenanceRecord] = []
        seen: set[str] = set()
        pending = [r.record_id for r in self.for_subject(subject_id)]
        while pending:
            rid = pending.pop()
            if rid in seen:
                continue
            seen.add(rid)
            record = self._records.get(rid)
            if record is None:
                continue
            result.append(record)
            pending.extend(record.parent_ids)
        return result
