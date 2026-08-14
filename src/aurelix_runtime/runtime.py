from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from aurelix_core.evaluation import EvaluationEngine
from .experiment_runner import ExperimentRunner
from .integrated_engines import Experiment
from .message_fabric import MessageFabric
from .persistence import JobRecord, LeaseLostError, RuntimeStore
from .pipeline_runner import GovernedPipeline


@dataclass(frozen=True)
class RuntimeConfig:
    database_path: str = "data/aurelix.db"
    heartbeat_seconds: float = 30.0
    worker_poll_seconds: float = 1.0
    max_attempts: int = 3


@dataclass(frozen=True)
class Job:
    job_id: str
    kind: str
    payload: dict[str, str]
    status: str
    attempts: int
    worker_id: str | None = None
    lease_token: str | None = None


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


class AurelixRuntime:
    """24/7 orchestration loop with one durable, fenced execution fabric."""

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()
        if self.config.heartbeat_seconds <= 0:
            raise ValueError("heartbeat_seconds must be positive")
        if self.config.worker_poll_seconds <= 0:
            raise ValueError("worker_poll_seconds must be positive")
        if self.config.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        self.store = RuntimeStore(self.config.database_path, lease_seconds=self.config.heartbeat_seconds)
        self.handlers: dict[str, Callable[[dict[str, str]], Any]] = {}
        self.claimed_handlers: dict[str, Callable[[JobRecord], Any]] = {}
        self._stop = threading.Event()
        self.worker_id = str(uuid4())
        stale_after = max(self.config.heartbeat_seconds * 2.0, 1.0)
        self.store.recover_running_jobs(self.config.max_attempts, stale_after_seconds=stale_after)

    def register(self, kind: str, handler: Callable[[dict[str, str]], Any]) -> None:
        if not kind.strip():
            raise ValueError("job kind is required")
        self.handlers[kind] = handler
        self.claimed_handlers.pop(kind, None)

    def register_claimed(self, kind: str, handler: Callable[[JobRecord], Any]) -> None:
        """Register a handler that executes the current claim, not a nested job."""
        if not kind.strip():
            raise ValueError("job kind is required")
        self.claimed_handlers[kind] = handler
        self.handlers.pop(kind, None)

    def register_autonomy(self, kind: str = "autonomy.run", *, message_fabric: MessageFabric | None = None) -> None:
        """Mount the full research→knowledge→experiment→business fabric on this runtime."""
        from .autonomy_fabric import AutonomyFabric

        fabric = AutonomyFabric(store=self.store, message_fabric=message_fabric)

        def handle(record: JobRecord) -> Any:
            return fabric.run_claimed(record)

        # Keep the mounted fabric inspectable so the composition root and
        # integration tests can prove that autonomy uses the shared bus.
        handle.autonomy_fabric = fabric  # type: ignore[attr-defined]
        self.register_claimed(kind, handle)

    def register_pipeline(self, pipeline: GovernedPipeline | None = None, kind: str = "pipeline.run") -> None:
        governed = pipeline or GovernedPipeline()

        def handle(payload: dict[str, str]) -> None:
            objective = payload.get("objective", "").strip()
            if not objective:
                raise ValueError("pipeline objective is required")
            governed.run(objective, business_approved=False)

        self.register(kind, handle)

    def register_experiment(self, experiment: Experiment) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.store.lock, self.store.db:
            self.store.db.execute("""INSERT INTO experiments(experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(experiment_id) DO UPDATE SET hypothesis=excluded.hypothesis,
                success_criteria=excluded.success_criteria,status=excluded.status,result=excluded.result,updated_at=excluded.updated_at""",
                (experiment.id, experiment.hypothesis, json.dumps(experiment.success_criteria), experiment.status,
                 json.dumps(experiment.result) if experiment.result is not None else None, now, now))

    def record_observation(self, experiment_id: str, observation: dict[str, Any]) -> str:
        observation_id = str(uuid4())
        with self.store.lock, self.store.db:
            self.store.db.execute("INSERT INTO observations(id,experiment_id,observation,recorded_at) VALUES (?,?,?,?)",
                                  (observation_id, experiment_id, json.dumps(observation), datetime.now(timezone.utc).isoformat()))
        return observation_id

    def query_experiment_observations(self, experiment_id: str) -> list[dict[str, Any]]:
        with self.store.lock:
            rows = self.store.db.execute("SELECT observation FROM observations WHERE experiment_id=? ORDER BY recorded_at", (experiment_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def query_experiments(self, status: str | None = None) -> list[dict[str, Any]]:
        with self.store.lock:
            if status:
                rows = self.store.db.execute("SELECT experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at FROM experiments WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = self.store.db.execute("SELECT experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at FROM experiments ORDER BY created_at DESC").fetchall()
        return [{"experiment_id": r[0], "hypothesis": r[1], "success_criteria": json.loads(r[2]), "status": r[3], "result": json.loads(r[4]) if r[4] else None, "created_at": r[5], "updated_at": r[6]} for r in rows]

    def get_experiment(self, experiment_id: str) -> Experiment:
        match = next((item for item in self.query_experiments() if item["experiment_id"] == experiment_id), None)
        if match is None:
            raise KeyError(f"experiment not found: {experiment_id}")
        return Experiment(id=match["experiment_id"], hypothesis=match["hypothesis"], success_criteria=match["success_criteria"], status=match["status"], result=match["result"])

    def create_experiment_runner(self) -> ExperimentRunner:
        def collector(experiment: Experiment) -> list[dict[str, Any]]:
            self.register_experiment(experiment)
            return self.query_experiment_observations(experiment.id)
        def on_complete(experiment: Experiment, _run) -> None:
            self.register_experiment(experiment)
            self.store.audit("experiment.evaluated", "experiment-runner", experiment.id,
                             "succeeded" if experiment.result and experiment.result.get("passed") else "evaluated", experiment.result or {})
        return ExperimentRunner(collector=collector, evaluator=EvaluationEngine(), on_complete=on_complete)

    def submit(self, kind: str, payload: dict[str, str] | None = None) -> str:
        if kind not in self.handlers and kind not in self.claimed_handlers:
            raise ValueError(f"unregistered job kind: {kind}")
        record = self.store.enqueue(kind, payload or {})
        self.store.audit("job.queued", "runtime", record.job_id, "queued", {"kind": kind})
        return record.job_id

    def _heartbeat_loop(self, job: Job, stop_event: threading.Event) -> None:
        interval = max(self.config.heartbeat_seconds / 2.0, 0.1)
        while not stop_event.wait(interval):
            if not self.store.heartbeat(job.job_id, job.worker_id, job.lease_token):
                return

    def run_once(self) -> bool:
        self.store.heartbeat()
        record = self.store.claim_next(max_attempts=self.config.max_attempts, worker_id=self.worker_id)
        if not record:
            return False
        job = Job(record.job_id, record.name, {str(k): str(v) for k, v in record.payload.items()}, record.status,
                  record.attempts, record.worker_id, record.lease_token)
        heartbeat_stop = threading.Event()
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, args=(job, heartbeat_stop),
                                             name=f"aurelix-heartbeat-{job.job_id[:8]}", daemon=True)
        heartbeat_thread.start()
        try:
            if job.kind in self.claimed_handlers:
                output = self.claimed_handlers[job.kind](record)
            else:
                output = self.handlers[job.kind](job.payload)
            result = _jsonable(output) if output is not None else {"ok": True}
            self.store.complete(job.job_id, result, worker_id=job.worker_id, lease_token=job.lease_token)
            self.store.audit("job.completed", "runtime", job.job_id, "succeeded", {"kind": job.kind})
        except LeaseLostError as exc:
            self.store.audit("job.lease_lost", "runtime", job.job_id, "aborted", {"kind": job.kind, "error": str(exc)})
        except Exception as exc:
            retry = job.attempts < self.config.max_attempts
            try:
                self.store.finish(job.job_id, False, str(exc), retry=retry, worker_id=job.worker_id, lease_token=job.lease_token)
            except LeaseLostError:
                self.store.audit("job.lease_lost", "runtime", job.job_id, "aborted", {"kind": job.kind, "error": str(exc)})
            else:
                self.store.audit("job.retry" if retry else "job.failed", "runtime", job.job_id,
                                 "queued" if retry else "failed", {"kind": job.kind, "error": str(exc), "attempt": job.attempts})
        finally:
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=max(self.config.heartbeat_seconds, 1.0))
        return True

    def serve_forever(self) -> None:
        while not self._stop.is_set():
            worked = self.run_once()
            if not worked:
                self._stop.wait(self.config.worker_poll_seconds)

    def stop(self) -> None:
        self._stop.set()

    def close(self) -> None:
        self.stop()
        self.store.close()
