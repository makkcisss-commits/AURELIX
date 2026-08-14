"""Governed bridge from approved opportunities into bounded Runtime execution.

The bridge is intentionally narrow: Opportunity describes a business candidate,
Governor decides whether the requested action may proceed, ExecutionRuntime
performs only a caller-supplied bounded operation, and realized revenue is
recorded through OpportunityRevenueBridge for later economic learning.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from .execution import ExecutionRequest, ExecutionResult, ExecutionRuntime
from .governor import Governor, GovernorRoute
from .opportunities import Opportunity, OpportunityStage
from .opportunity_revenue_bridge import OpportunityRevenueBridge, RevenueSource
from .resource_scope import ResourceKind, ResourcePermission, ResourceRequest


@dataclass(frozen=True)
class OpportunityExecutionOutcome:
    opportunity_id: str
    route: GovernorRoute
    executed: bool
    execution: ExecutionResult | None
    revenue_source_id: str | None
    observed_revenue_eur: Decimal


class OpportunityExecutionBridge:
    """Connect approved opportunity, Governor, Runtime and realized revenue."""

    def __init__(
        self,
        governor: Governor | None = None,
        runtime: ExecutionRuntime | None = None,
        revenue: OpportunityRevenueBridge | None = None,
    ) -> None:
        self.governor = governor or Governor()
        self.runtime = runtime or ExecutionRuntime()
        self.revenue = revenue or OpportunityRevenueBridge()

    def execute(
        self,
        opportunity: Opportunity,
        *,
        actor_id: str,
        owner_role: str,
        channel: str,
        permission: ResourcePermission,
        operation: Callable[[], object],
        requires_capital: bool = False,
        production_change: bool = False,
    ) -> OpportunityExecutionOutcome:
        if opportunity.stage is not OpportunityStage.APPROVED:
            raise ValueError("opportunity must be approved before execution")

        route = self.governor.route(
            source=opportunity.opportunity_id,
            action="business.execute",
            requires_capital=requires_capital,
            risk=opportunity.risk,
            production_change=production_change,
        )
        if route is not GovernorRoute.POLICY_ALLOWED:
            return OpportunityExecutionOutcome(opportunity.opportunity_id, route, False, None, None, Decimal("0"))

        source: RevenueSource = self.revenue.admit(
            opportunity,
            owner_role=owner_role,
            channel=channel,
        )
        request = ExecutionRequest(
            actor_id=actor_id,
            resource=ResourceRequest(
                actor_id=actor_id,
                resource=ResourceKind.BUSINESS,
                operation="execute",
                target_scope=opportunity.opportunity_id,
            ),
            permission=permission,
        )
        result = self.runtime.execute(request, operation)

        observed = Decimal("0")
        if isinstance(result.output, dict) and "revenue_eur" in result.output:
            observed = Decimal(str(result.output["revenue_eur"]))
            if observed > 0:
                source = self.revenue.record_observation(source.source_id, observed)

        return OpportunityExecutionOutcome(
            opportunity.opportunity_id,
            route,
            True,
            result,
            source.source_id,
            observed,
        )
