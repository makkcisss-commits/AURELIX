from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    role: str
    owner: str
    tools: tuple[str, ...]
    environment: str


def derive_agent_id(*, role: str, owner: str, tools: tuple[str, ...], environment: str) -> str:
    """Derive a stable identity from the declared agent contract."""
    payload = {"role": role, "owner": owner, "tools": sorted(tools), "environment": environment}
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return f"agt_{digest[:24]}"


def create_identity(*, role: str, owner: str, tools: tuple[str, ...], environment: str) -> AgentIdentity:
    if not role.strip() or not owner.strip() or not environment.strip():
        raise ValueError("role, owner and environment are required")
    return AgentIdentity(
        agent_id=derive_agent_id(role=role, owner=owner, tools=tools, environment=environment),
        role=role,
        owner=owner,
        tools=tuple(sorted(set(tools))),
        environment=environment,
    )
