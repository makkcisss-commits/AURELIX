from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class EngineResult:
    engine: str
    status: str
    output: dict[str, Any]


class EngineRegistry:
    """Explicit allowlist of engine capabilities. No dynamic execution by name."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, name: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if not name or name in self._handlers:
            raise ValueError("engine name must be unique and non-empty")
        self._handlers[name] = handler

    def execute(self, name: str, payload: dict[str, Any]) -> EngineResult:
        handler = self._handlers.get(name)
        if handler is None:
            raise PermissionError(f"engine is not registered: {name}")
        output = handler(payload)
        if not isinstance(output, dict):
            raise TypeError("engine handlers must return a dictionary")
        return EngineResult(engine=name, status="completed", output=output)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))
