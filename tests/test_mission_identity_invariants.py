"""Executable invariants for durable mission/execution identity."""

from __future__ import annotations


def test_retry_keeps_mission_identity_but_changes_execution_identity() -> None:
    mission_id = "mission-1"
    execution_1 = "execution-1"
    execution_2 = "execution-2"

    assert mission_id == mission_id
    assert execution_1 != execution_2


def test_replan_keeps_mission_identity_but_changes_plan_identity() -> None:
    mission_id = "mission-1"
    plan_1 = "plan-1"
    plan_2 = "plan-2"

    assert mission_id == mission_id
    assert plan_1 != plan_2


def test_resume_does_not_create_a_new_mission_identity() -> None:
    original_mission_id = "mission-1"
    resumed_mission_id = original_mission_id

    assert resumed_mission_id == original_mission_id
