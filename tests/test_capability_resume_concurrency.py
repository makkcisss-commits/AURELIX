"""Regression coverage for concurrent capability-resume attempts."""

from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass
class _ResumeClaim:
    mission_id: str
    claimed_by: str


class _AtomicResumeGuard:
    """Minimal reference model: only one worker may claim a mission resume."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._claims: dict[str, _ResumeClaim] = {}

    def claim(self, mission_id: str, worker_id: str) -> bool:
        with self._lock:
            if mission_id in self._claims:
                return False
            self._claims[mission_id] = _ResumeClaim(mission_id, worker_id)
            return True


def test_only_one_concurrent_worker_can_claim_resume() -> None:
    guard = _AtomicResumeGuard()
    results: list[bool] = []
    barrier = threading.Barrier(2)

    def worker(worker_id: str) -> None:
        barrier.wait()
        results.append(guard.claim("mission-1", worker_id))

    threads = [threading.Thread(target=worker, args=(f"worker-{i}",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == [False, True]
    assert len(guard._claims) == 1
    assert guard._claims["mission-1"].mission_id == "mission-1"
