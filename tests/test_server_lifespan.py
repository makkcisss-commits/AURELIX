from __future__ import annotations

from fastapi.testclient import TestClient

import aurelix_core.server as server


class FakeSystem:
    def __init__(self) -> None:
        self.scheduled: list[tuple[str, float, str]] = []
        self.started = 0
        self.stopped = 0

    def schedule_system_cycle(self, name: str, interval: float, objective: str) -> None:
        self.scheduled.append((name, interval, objective))

    def run_forever(self) -> None:
        self.started += 1

    def stop(self) -> None:
        self.stopped += 1


def test_lifespan_owns_long_running_system(monkeypatch):
    fake = FakeSystem()
    monkeypatch.setattr(server, "_system", fake)
    monkeypatch.setenv("AURELIX_AUTONOMY_ENABLED", "true")
    monkeypatch.setenv("AURELIX_AUTONOMY_INTERVAL_SECONDS", "30")
    monkeypatch.setenv("AURELIX_AUTONOMY_OBJECTIVE", "test objective")
    monkeypatch.setattr(server, "_system_thread", None)

    with TestClient(server.app):
        assert fake.scheduled == [("economic-discovery", 30.0, "test objective")]
        assert fake.started == 1
        assert server._system_thread is not None

    assert fake.stopped == 1
    assert server._system_thread is None
