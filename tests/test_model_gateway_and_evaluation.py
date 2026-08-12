from aurelix_core.evaluation import EvaluationEngine
from aurelix_core.model_gateway import GenerationRequest, GovernedModelGateway, ModelProvider


class FakeProvider(ModelProvider):
    def generate(self, prompt, max_tokens=2000):
        return "ok"

    def structured_output(self, prompt, schema):
        return {"ok": True}

    def embeddings(self, text):
        return [1.0, 2.0]

    def health(self):
        return True


class FailingProvider(FakeProvider):
    def generate(self, prompt, max_tokens=2000):
        raise RuntimeError("provider exploded")


def test_model_gateway_enforces_policy_and_audits():
    events = []
    gateway = GovernedModelGateway(
        FakeProvider(),
        policy=lambda request: request.actor_id == "agent",
        audit=lambda *args, **kwargs: events.append(args[0]),
    )
    assert gateway.generate(GenerationRequest("hello", actor_id="agent")) == "ok"
    assert events == ["model.generation.requested", "model.generation.completed"]


def test_model_gateway_records_failed_generation():
    events = []
    gateway = GovernedModelGateway(
        FailingProvider(),
        audit=lambda event, **metadata: events.append((event, metadata["error"])),
    )
    try:
        gateway.generate(GenerationRequest("hello"))
    except RuntimeError as exc:
        assert str(exc) == "provider exploded"
    else:
        raise AssertionError("expected provider failure")
    assert events[0][0] == "model.generation.requested"
    assert events[1][0] == "model.generation.failed"
    assert events[1][1] == "provider exploded"


def test_evaluation_fails_closed_without_measurement():
    result = EvaluationEngine().evaluate(
        "exp-1", [{"metric": "conversion", "operator": ">=", "target": 0.1}], {}
    )
    assert result.passed is False
    assert result.confidence == 0.0


def test_evaluation_passes_when_all_criteria_are_met():
    result = EvaluationEngine().evaluate(
        "exp-1", [{"metric": "conversion", "operator": ">=", "target": 0.1}], {"conversion": 0.2}
    )
    assert result.passed is True
    assert result.confidence == 1.0
