from decimal import Decimal

from aurelix_core.business import BusinessStage, create_activity
from aurelix_core.continuous_intelligence import (
    ContinuousIntelligence,
    EvidenceKind,
)
from aurelix_core.enterprise_intelligence import AssetKind, EnterpriseRegistry
from aurelix_core.governor import GovernorRoute
from aurelix_core.opportunities import build_opportunity
from aurelix_core.revenue import RevenueEngine
from aurelix_runtime.orchestrator import Capability, Orchestrator
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_master_sandbox_identity_to_learning_and_value(tmp_path):
    registry = EnterpriseRegistry()
    profile = registry.create_profile(
        identity_id="sandbox-identity",
        name="AURELIX Sandbox",
    )
    asset = registry.register_asset(
        profile_id=profile.profile_id,
        name="Content Production Capability",
        kind=AssetKind.CAPABILITY,
        scope="sandbox",
    )

    intelligence = ContinuousIntelligence()
    objective = intelligence.propose_objective(
        domain="creative-commerce",
        title="Validate sponsor content capability",
        question="Can a reusable content workflow produce a commercial result?",
        target_competencies=("content-production",),
    )
    evidence = intelligence.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.PRACTICE,
        reference="sandbox-practice-001",
        strength=0.9,
    )
    experiment = intelligence.propose_experiment(
        objective_id=objective.objective_id,
        hypothesis="A governed content workflow can create a sellable result.",
        method="sandbox execution",
        success_criteria=("execution succeeds", "commercial result recorded"),
    )
    evaluation = intelligence.evaluate(
        objective_id=objective.objective_id,
        score=0.9,
        evidence_refs=(evidence.evidence_id,),
    )
    capability = intelligence.validate_capability(
        name="content-production",
        domain="creative-commerce",
        required_competencies=("content-production",),
        evidence_refs=(evidence.evidence_id,),
    )
    knowledge = intelligence.record_knowledge(
        domain="creative-commerce",
        claim="The sandbox workflow can produce a governed commercial outcome.",
        evidence_refs=(evidence.evidence_id,),
        confidence=0.9,
    )

    activity = create_activity(
        name="Sponsor Content Sandbox",
        channel="sponsor",
        description="Controlled sandbox business activity",
    )
    opportunity = build_opportunity(
        title="Sponsor content experiment",
        finding_ids=(knowledge.knowledge_id,),
        cost_eur=Decimal("5"),
        monthly_revenue_eur=Decimal("100"),
        hours=Decimal("2"),
        complexity=1,
        risk=1,
        confidence=Decimal("0.9"),
    )

    runtime = AurelixRuntime(
        RuntimeConfig(database_path=str(tmp_path / "sandbox.db"), heartbeat_seconds=1)
    )
    try:
        executed = []
        orchestrator = Orchestrator(runtime=runtime)
        orchestrator.register(
            Capability(
                name="sandbox.content.execute",
                handler=lambda payload: executed.append(payload) or {"success": True},
                read_only=False,
            )
        )
        route = orchestrator.governor.route(
            source="master-sandbox",
            action="sandbox.content.execute",
            requires_capital=False,
            risk=opportunity.risk,
            production_change=False,
        )
        assert route.route is GovernorRoute.POLICY_ALLOWED
        job_id = orchestrator.submit(
            capability="sandbox.content.execute",
            payload={"objective": objective.objective_id},
            risk=opportunity.risk,
        )
        assert runtime.run_once() is True
        assert executed == [{"objective": objective.objective_id}]

        revenue = RevenueEngine()
        revenue_record = revenue.record(
            activity_id=activity.activity_id,
            amount_eur=Decimal("100"),
            source="sandbox-sponsor",
            external_reference=job_id,
        )

        link = registry.link(
            profile_id=profile.profile_id,
            asset_ids=(asset.asset_id,),
            competency_ids=(),
            knowledge_refs=(knowledge.knowledge_id,),
            learning_refs=(objective.objective_id,),
            opportunity_id=opportunity.opportunity_id,
            experiment_id=experiment.experiment_id,
            runtime_execution_id=job_id,
            business_activity_id=activity.activity_id,
            revenue_source_id=revenue_record.revenue_id,
        )

        assert evaluation.score == 0.9
        assert capability.validated is True
        assert activity.stage is BusinessStage.IDEA
        assert revenue.total_for_activity(activity.activity_id) == Decimal("100")
        assert link.profile_id == profile.profile_id
        assert link.opportunity_id == opportunity.opportunity_id
        assert link.runtime_execution_id == job_id
        assert link.revenue_source_id == revenue_record.revenue_id
    finally:
        runtime.close()


def test_master_sandbox_governor_blocks_high_risk_execution():
    orchestrator = Orchestrator(queue=None, runtime=AurelixRuntime(RuntimeConfig(database_path=":memory:")))
    try:
        orchestrator.register(Capability(name="dangerous", handler=lambda payload: payload, read_only=False))
        route = orchestrator.governor.route(
            source="master-sandbox",
            action="dangerous",
            requires_capital=False,
            risk=9,
            production_change=True,
        )
        assert route.route is GovernorRoute.BLOCKED
    finally:
        orchestrator.runtime.close()
