from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .governor import Governor
from .revenue import RevenueEngine
from .treasury import Treasury


class HealthState(str, Enum):
    HEALTHY = "healthy"
    ATTENTION = "attention"
    PENDING = "pending"


@dataclass(frozen=True)
class ComponentStatus:
    name: str
    state: HealthState
    detail: str


@dataclass(frozen=True)
class ControlCenterSnapshot:
    system: HealthState
    components: tuple[ComponentStatus, ...]
    treasury_free_eur: str = "0"
    revenue_total_eur: str = "0"

    @property
    def all_healthy(self) -> bool:
        return self.system is HealthState.HEALTHY and all(
            component.state is HealthState.HEALTHY for component in self.components
        )


class ControlCenter:
    """Read-only facade for the private operational control plane."""

    def __init__(self, *, treasury: Treasury, revenue: RevenueEngine, governor: Governor) -> None:
        self.treasury = treasury
        self.revenue = revenue
        self.governor = governor

    def snapshot(self, components: list[ComponentStatus] | None = None) -> ControlCenterSnapshot:
        components = components or []
        system = (
            HealthState.HEALTHY
            if all(component.state is HealthState.HEALTHY for component in components)
            else HealthState.ATTENTION
        )
        treasury = self.treasury.snapshot()
        total_revenue = sum(
            (record.amount_eur for record in self.revenue._records.values()),
            treasury.free_eur * 0,
        )
        return ControlCenterSnapshot(
            system=system,
            components=tuple(components),
            treasury_free_eur=str(treasury.free_eur),
            revenue_total_eur=str(total_revenue),
        )


def build_snapshot(components: list[ComponentStatus]) -> ControlCenterSnapshot:
    system = (
        HealthState.HEALTHY
        if all(component.state is HealthState.HEALTHY for component in components)
        else HealthState.ATTENTION
    )
    return ControlCenterSnapshot(system=system, components=tuple(components))
