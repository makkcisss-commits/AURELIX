from aurelix_core.knowledge_graph import KnowledgeGraph, NodeType, Relation


def test_graph_links_research_to_academy_memory() -> None:
    graph = KnowledgeGraph()
    source = graph.add_node(node_type=NodeType.SOURCE, label="Source A")
    claim = graph.add_node(node_type=NodeType.CLAIM, label="Claim A")
    lesson = graph.add_node(node_type=NodeType.LESSON, label="Lesson A")

    graph.link(source_id=source.node_id, relation=Relation.SUPPORTS, target_id=claim.node_id)
    graph.link(source_id=claim.node_id, relation=Relation.LEADS_TO, target_id=lesson.node_id)

    assert graph.node_count() == 3
    assert graph.edge_count() == 2
    assert len(graph.neighbors(claim.node_id)) == 2


def test_unknown_nodes_cannot_be_linked() -> None:
    graph = KnowledgeGraph()
    node = graph.add_node(node_type=NodeType.CONCEPT, label="Concept")
    try:
        graph.link(source_id=node.node_id, relation=Relation.RELATES_TO, target_id="missing")
        assert False
    except KeyError:
        assert True
