from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class AcademyProposal:
    proposal_id: str
    knowledge_id: str
    title: str
    rationale: str
    learning_refs: tuple[str, ...]
    requires_governor: bool = True


class AcademyGovernorBoundary:
    """Creates advisory proposals; it never executes or authorizes them."""

    def __init__(self) -> None:
        self._proposals: dict[str, AcademyProposal] = {}

    def propose(self, *, knowledge_id: str, title: str, rationale: str,
                learning_refs: list[str]) -> AcademyProposal:
        if not knowledge_id.strip():
            raise ValueError("knowledge_id is required")
        if not title.strip() or not rationale.strip():
            raise ValueError("title and rationale are required")
        if not learning_refs:
            raise ValueError("proposal must reference at least one learning")
        proposal = AcademyProposal(
            proposal_id=str(uuid4()),
            knowledge_id=knowledge_id,
            title=title,
            rationale=rationale,
            learning_refs=tuple(learning_refs),
        )
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def get(self, proposal_id: str) -> AcademyProposal:
        return self._proposals[proposal_id]
