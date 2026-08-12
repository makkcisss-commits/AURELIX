from aurelix_runtime.provenance import ProvenanceLedger


def test_provenance_tracks_parent_chain():
    ledger = ProvenanceLedger()
    research = ledger.append("research", "research-1")
    evidence = ledger.append("evidence", "evidence-1", [research.record_id])
    evaluation = ledger.append("evaluation", "eval-1", [evidence.record_id])
    knowledge = ledger.append("knowledge", "knowledge-1", [evaluation.record_id])

    lineage = ledger.lineage("knowledge-1")
    ids = {record.record_id for record in lineage}
    assert {research.record_id, evidence.record_id, evaluation.record_id, knowledge.record_id} <= ids
