"""Bridge persisted jobs to governed execution fabrics."""
from __future__ import annotations

from dataclasses import dataclass, is_dataclass, asdict
import json
from typing import Any, Dict

from .autonomy_fabric import AutonomyFabric
from .persistence import RuntimeStore
from .pipeline_runner import GovernedPipeline


@dataclass
class JobExecution:
    job_id: str
    status: str
    result: Dict[str, Any]


class PipelineJobRunner:
    """Legacy governed pipeline worker entry point."""

    def __init__(self, pipeline: GovernedPipeline | None = None):
        self.pipeline = pipeline or GovernedPipeline()

    def execute(self, job_id: str, objective: str, approved: bool = False) -> JobExecution:
        result = self.pipeline.run(objective, business_approved=approved)
        status = result.business.get("status", "completed")
        self.pipeline.store.record("job.completed", job_id=job_id, status=status)
        return JobExecution(job_id, status, {"business": result.business})


class AutonomyJobRunner:
    """Worker entry point for the complete durable autonomy fabric."""

    def __init__(self, store: RuntimeStore):
        self.store = store
        self.fabric = AutonomyFabric(store=store)

    def _persist_engine_knowledge_state(self) -> None:
        payload = {}
        for key, value in self.fabric.engines.knowledge.items():
            if is_dataclass(value):
                payload[key] = asdict(value)
            else:
                payload[key] = value
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                ("engine.knowledge", json.dumps(payload, sort_keys=True)),
            )

    def execute(self, job_id: str, objective: str, approved: bool = False) -> JobExecution:
        claimed = self.store.get(job_id)
        if claimed is None:
            raise KeyError(f"unknown job: {job_id}")
        if claimed.status == "completed":
            durable = self.store.get_result(job_id) or {}
            return JobExecution(job_id, durable.get("status", "completed"), durable)
        if claimed.status != "running":
            raise RuntimeError(f"job {job_id} must be claimed before autonomy execution")
        run = self.fabric.run_claimed(claimed)
        self._persist_engine_knowledge_state()
        return JobExecution(job_id, run.status, {"autonomy": run.__dict__})

    def close(self) -> None:
        self.fabric.close()
