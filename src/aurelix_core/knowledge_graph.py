from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class NodeType(str, Enum):
    CLAIM = "CLAIM"
    SOURCE = "SOURCE"
    FINDING = "FINDING"
    CONCEPT = "CONCEPT"
    EXPERIMENT = "EXPERIMENT"
    LESSON = "LESSON"
    OPPORTUNITY = "OPPORTUNITY"


class Relation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"
    RELATES_TO = "RELATES_TO"
    TESTED_BY = "TESTED_BY"
    LEADS_TO = "LEADS_TO"
    LEARNED_FROM = "LEARNED_FROM"


@dataclass(frozen=True)
class KnowledgeNode:
    node_id: str
    node_type: NodeType
    label: str
    payload: dict[str, str]


@dataclass(frozen=True)
class KnowledgeEdge:
    edge_id: str
    source_id: str
    relation: Relation
    target_id: str


class KnowledgeGraph:
    """Small auditable knowledge graph for Academy memory."""

    def __init__(self) -> None:
        self._nodes: dict[str, KnowledgeNode] = {}
        self._edges: dict[str, KnowledgeEdge] = {}

    def add_node(self, *, node_type: NodeType, label: str, payload: dict[str, str] | None = None) -> KnowledgeNode:
        if not label.strip():
            raise ValueError("label is required")
        node = KnowledgeNode(str(uuid4()), node_type, label, payload or {})
        self._nodes[node.node_id] = node
        return node

    def link(self, *, source_id: str, relation: Relation, target_id: str) -> KnowledgeEdge:
        if source_id not in self._nodes or target_id not in self._nodes:
            raise KeyError("both graph nodes must exist")
        edge = KnowledgeEdge(str(uuid4()), source_id, relation, target_id)
        self._edges[edge.edge_id] = edge
        return edge

    def neighbors(self, node_id: str) -> tuple[KnowledgeNode, ...]:
        if node_id not in self._nodes:
            raise KeyError("unknown node")
        ids = {edge.target_id for edge in self._edges.values() if edge.source_id == node_id}
        ids.update(edge.source_id for edge in self._edges.values() if edge.target_id == node_id)
        return tuple(self._nodes[item] for item in ids)

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)
