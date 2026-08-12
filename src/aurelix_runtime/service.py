"""Long-running AURELIX service lifecycle."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from .job_queue import PersistentJobQueue
from .supervised_worker import SupervisedWorker, WorkerConfig


@dataclass
class RuntimeConfig:
    tick_seconds: float = 1.0


class RuntimeService:
    def __init__(self, queue: Optional[PersistentJobQueue] = None, config: Optional[RuntimeConfig] = None):
        self.queue = queue or PersistentJobQueue()
        self.config = config or RuntimeConfig()
        self.worker = SupervisedWorker(self.queue, WorkerConfig())
        self._stop = threading.Event()
        self._started = False

    @property
    def status(self) -> str:
        return "stopping" if self._stop.is_set() else ("running" if self._started else "stopped")

    def start(self) -> None:
        if self._started:
            return
        self.queue.recover_running()
        self._stop.clear()
        self._started = True
        self.queue.store.record("runtime.started")

    def tick(self) -> None:
        if not self._started:
            raise RuntimeError("runtime is not started")
        self.worker.run_once()

    def stop(self) -> None:
        if not self._started:
            return
        self._stop.set()
        self.queue.store.record("runtime.stopping")
        self._started = False
        self.queue.store.record("runtime.stopped")

    def run_forever(self) -> None:
        self.start()
        try:
            while not self._stop.is_set():
                self.tick()
                self._stop.wait(self.config.tick_seconds)
        finally:
            self.stop()
