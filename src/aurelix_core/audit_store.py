from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from .audit import AuditEvent


class AuditStore:
    """Append-only JSONL audit store for local development and tests.

    This is a durable-on-disk foundation, not the final production audit backend.
    Production should use protected append-only storage with integrity controls,
    retention policy, access controls, and backup/recovery procedures.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = Lock()

    def append(self, event: AuditEvent) -> None:
        record = event.to_record()
        line = json.dumps(record, sort_keys=True, separators=(",", ":"))
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()

    def read_all(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
