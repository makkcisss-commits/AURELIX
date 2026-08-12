from aurelix_core.experiments import ExperimentService, ExperimentStatus


def test_experiment_starts_proposed() -> None:
    service = ExperimentService()
    item = service.propose(
        opportunity_id="opp-1",
        objective="Validate landing-page demand",
        sandbox="sandbox/web/exp-1",
        success_metric="5 qualified leads",
        budget_eur=0,
    )
    assert item.status is ExperimentStatus.PROPOSED


def test_experiment_can_be_blocked_without_execution() -> None:
    service = ExperimentService()
    item = service.propose(
        opportunity_id="opp-1",
        objective="test",
        sandbox="sandbox/test",
        success_metric="signal",
        budget_eur=10,
    )
    blocked = service.mark_blocked(item.experiment_id)
    assert blocked.status is ExperimentStatus.BLOCKED
