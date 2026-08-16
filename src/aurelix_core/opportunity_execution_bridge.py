"""Governed bridge from approved opportunities into bounded Runtime execution.

The bridge is intentionally narrow: Opportunity describes a business candidate,
EconomicQualification proves the opportunity is ready for the revenue pipeline,
Governor decides whether the requested action may proceed, ExecutionRuntime
performs only a caller-supplied bounded operation, and realized revenue is
recorded through OpportunityRevenueBridge with an explicit synthetic/productive
boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from .economic_opportunity_validation import EconomicQualification
from .execution import ExecutionRequest, ExecutionResult, ExecutionRuntime
from .governor import Governor, GovernorRoute
from .opportunities import Opportunity, OpportunityStage
from .opportunity_revenue_bridge import OpportunityRevenueBridge, RevenueSource
from .resource_scope import ResourceKind, ResourcePermission, ResourceRequest, authorize_resource


@dataclass(frozen=True)
class OpportunityExecutionOutcome:
    opportunity_id: str
    route: GovernorRoute
    executed: bool
    execution: ExecutionResult | None
    revenue_source_id: str | None
    observed_revenue_eur: Decimal


class OpportunityExecutionBridge:
    """Connect a qualified, approved opportunity to Governor, Runtime and revenue."""
    def __init__(self, governor: Governor | None = None, runtime: ExecutionRuntime | None = None, revenue: OpportunityRevenueBridge | None = None) -> None:
        self.governor = governor or Governor()
        self.runtime = runtime or ExecutionRuntime()
        self.revenue = revenue or OpportunityRevenueBridge()

    def execute(self, opportunity: Opportunity, *, qualification: EconomicQualification, actor_id: str, owner_role: str, channel: str, permission: ResourcePermission, operation: Callable[[], object], requires_capital: bool = False, production_change: bool = False, synthetic: bool = False) -> OpportunityExecutionOutcome:
        if opportunity.stage is not OpportunityStage.APPROVED:
            raise ValueError("opportunity must be approved before execution")
        if qualification.opportunity_id != opportunity.opportunity_id or not qualification.is_qualified:
            raise ValueError("opportunity must have matching economic qualification before execution")

        orchestration = self.governor.route(source=opportunity.opportunity_id, action="business.execute", requires_capital=requires_capital, risk=opportunity.risk, production_change=production_change)
        route = orchestration.route
        if route is not GovernorRoute.POLICY_ALLOWED:
            return OpportunityExecutionOutcome(opportunity.opportunity_id, route, False, None, None, Decimal("0"))

        request = ExecutionRequest(
            actor_id=actor_id,
            resource=ResourceRequest(actor_id=actor_id, resource=ResourceKind.BUSINESS, operation="execute", target_scope=opportunity.opportunity_id),
            permission=permission,
        )
        authorize_resource(request.resource, permission)
        source: RevenueSource = self.revenue.admit(opportunity, qualification=qualification, owner_role=owner_role, channel=channel)
        result = self.runtime.execute(request, operation)

        observed = Decimal("0")
        if isinstance(result.output, dict) and "revenue_eur" in result.output:
            reported = Decimal(str(result.output["revenue_eur"]))
            if reported > 0:
                external_reference = result.output.get("external_reference") or result.output.get("reference")
                source = self.revenue.record_observation(source.source_id, reported, external_reference=external_reference, synthetic=synthetic)
                if source.is_productive:
                    observed = source.observed_daily_eur

        return OpportunityExecutionOutcome(opportunity.opportunity_id, route, True, result, source.source_id, observed)
