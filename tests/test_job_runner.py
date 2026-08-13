from aurelix_runtime.job_runner import PipelineJobRunner


def test_job_runner_executes_full_pipeline_and_stops_at_validation_gate():
    runner = PipelineJobRunner()
    execution = runner.execute("job-1", "research objective")
    assert execution.job_id == "job-1"
    assert execution.status == "awaiting_validation"
    assert execution.result["business"]["status"] == "awaiting_validation"
