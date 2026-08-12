"""Bridge persisted jobs to the governed AURELIX pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .pipeline_runner import GovernedPipeline


@dataclass
class JobExecution:
    job_id: str
    status: str
    result: Dict[str, Any]


class PipelineJobRunner:
    """Host-facing worker entry point; queue/worker supervisor owns scheduling."""

    def __init__(self, pipeline: GovernedPipeline | None = None):
        self.pipeline = pipeline or GovernedPipeline()

    def execute(self, job_id: str, objective: str, approved: bool = False) -> JobExecution:
        result = self.pipeline.run(objective, business_approved=approved)
        status = "awaiting_approval" if result.business["status"] == "awaiting_approval" else "ready_for_execution"
        self.pipeline.store.record("job.completed", job_id=job_id, status=status)
        return JobExecution(job_id=job_id, status=status, result={"business": result.business})
