from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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

    @property
    def all_healthy(self) -> bool:
        return self.system is HealthState.HEALTHY and all(
            component.state is HealthState.HEALTHY for component in self.components
        )


def build_snapshot(components: list[ComponentStatus]) -> ControlCenterSnapshot:
    system = (
        HealthState.HEALTHY
        if all(component.state is HealthState.HEALTHY for component in components)
        else HealthState.ATTENTION
    )
    return ControlCenterSnapshot(system=system, components=tuple(components))
