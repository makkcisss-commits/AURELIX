from aurelix_runtime.pipeline_runner import GovernedPipeline


def test_pipeline_is_end_to_end_and_business_waits_for_validation():
    pipeline = GovernedPipeline()
    result = pipeline.run("research objective")
    assert result.research["objective"] == "research objective"
    assert result.knowledge["knowledge_id"] is None
    assert result.innovation["status"] == "awaiting_knowledge"
    assert result.experiment["status"] == "awaiting_innovation"
    assert result.evaluation["passed"] is False
    assert result.business["status"] == "awaiting_validation"


def test_pipeline_does_not_bypass_validation_with_explicit_business_approval():
    pipeline = GovernedPipeline()
    result = pipeline.run("approved objective", business_approved=True)
    assert result.business["status"] == "awaiting_validation"
