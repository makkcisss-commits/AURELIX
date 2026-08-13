"""Bridge persisted jobs to governed execution fabrics."""
from __future__ import annotations

from dataclasses import dataclass
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
        return JobExecution(job_id, run.status, {"autonomy": run.__dict__})

    def close(self) -> None:
        self.fabric.close()
