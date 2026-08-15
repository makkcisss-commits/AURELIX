from pathlib import Path

from aurelix_core.academy_curriculum import AcademyCurriculum
from aurelix_runtime.persistence import RuntimeStore


def test_curriculum_contains_requested_roles_and_skills(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "academy.db")
    curriculum = AcademyCurriculum(store)

    role_ids = {role.role_id for role in curriculum.roles()}
    assert {"ai-engineer", "devsecops", "data-engineer", "mlops", "ai-red-team", "forward-deployed-engineer"} <= role_ids

    skill_ids = {skill.skill_id for skill in curriculum.skills()}
    assert {"python", "sql", "power-bi", "kubernetes", "docker", "aws", "terraform", "agents-ai", "api-security", "code-review"} <= skill_ids
    store.close()


def test_learning_progress_survives_restart(tmp_path: Path) -> None:
    db = tmp_path / "academy.db"
    store = RuntimeStore(db)
    curriculum = AcademyCurriculum(store)
    curriculum.mark_learned("python", evidence_refs=["learning-1"], confidence=0.9)
    store.close()

    restored_store = RuntimeStore(db)
    restored = AcademyCurriculum(restored_store)
    assert restored.status("python") == "learned"
    assert restored.roadmap("ai-engineer")["remaining"]
    restored_store.close()


def test_unknown_requirements_become_durable_skill_gaps(tmp_path: Path) -> None:
    db = tmp_path / "academy.db"
    store = RuntimeStore(db)
    curriculum = AcademyCurriculum(store)

    gap = curriculum.discover_from_requirement("new quantum database tool", source="research")

    assert gap is not None
    assert gap.status == "open"
    assert gap.skill_id == "new-quantum-database-tool"
    assert any(item.gap_id == gap.gap_id for item in curriculum.open_gaps())
    store.close()


def test_known_requirement_does_not_create_duplicate_gap(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "academy.db")
    curriculum = AcademyCurriculum(store)
    assert curriculum.discover_from_requirement("Python", source="runtime") is None
    store.close()
