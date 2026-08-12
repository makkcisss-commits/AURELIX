from aurelix_runtime.pipeline_runner import GovernedPipeline


def test_pipeline_is_end_to_end_and_business_is_gated():
    pipeline = GovernedPipeline()
    result = pipeline.run("research objective")
    assert result.research["objective"] == "research objective"
    assert result.knowledge["knowledge_id"] in pipeline.store.knowledge
    assert result.innovation["status"] == "proposal"
    assert result.experiment["status"] == "proposed"
    assert result.evaluation["passed"] is False
    assert result.business["status"] == "awaiting_approval"


def test_pipeline_can_prepare_business_after_explicit_approval():
    pipeline = GovernedPipeline()
    result = pipeline.run("approved objective", business_approved=True)
    assert result.business["status"] == "ready_for_execution"
