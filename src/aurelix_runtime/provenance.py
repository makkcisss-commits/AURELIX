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
        record = ProvenanceRecord(str(uuid4()), kind, subject_id, list(parent_ids or []), metadata)
        self._records[record.record_id] = record
        return record

    def for_subject(self, subject_id: str) -> List[ProvenanceRecord]:
        return [r for r in self._records.values() if r.subject_id == subject_id]

    def lineage(self, subject_id: str) -> List[ProvenanceRecord]:
        """Return records for the subject and recursively for parent subjects."""
        result: List[ProvenanceRecord] = []
        seen_records: set[str] = set()
        pending_subjects = [subject_id]
        seen_subjects: set[str] = set()
        while pending_subjects:
            current = pending_subjects.pop()
            if current in seen_subjects:
                continue
            seen_subjects.add(current)
            for record in self.for_subject(current):
                if record.record_id in seen_records:
                    continue
                seen_records.add(record.record_id)
                result.append(record)
                pending_subjects.extend(record.parent_ids)
        return result
