from aurelix_runtime.integrated_engines import AcademyEngine, EngineStore, Evidence, KnowledgeEngine


def test_evidence_survives_academy_to_knowledge() -> None:
    store = EngineStore()
    evidence = [Evidence("https://example.test/source", "validated finding", 0.9, True)]

    academy = AcademyEngine().run({"objective": "bounded automation", "evidence": evidence}, store)
    knowledge = KnowledgeEngine().run(academy, store)

    item = store.knowledge[knowledge["knowledge_id"]]
    assert item.evidence == evidence
    assert knowledge["validated"] is True
    assert "validated" in item.tags
