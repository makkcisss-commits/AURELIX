import json
from pathlib import Path

import pytest

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.persistence import RuntimeStore
from aurelix_runtime.runtime import RuntimeConfig
from aurelix_runtime.system_integrity import SystemIntegrityController, SystemIntegrityError


def make_factory(tmp_path: Path):
    return EngineFactory(
        EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "integrity.db")))
    )


def test_integrity_control_plane_accepts_canonical_composition(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    factory = make_factory(tmp_path)
    try:
        report = factory.check_integrity()
        assert report["status"] == "ok"
        assert report["summary"]["failed"] == 0
        assert factory.system_validation.run()["checks"][-1]["name"] == "knowledge_store"
        integrity = next(item for item in factory.system_validation.run()["checks"] if item["name"] == "system_integrity")
        assert integrity["status"] == "ok"
    finally:
        factory.runtime.close()


def test_integrity_detects_split_canonical_owner(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    factory = make_factory(tmp_path)
    try:
        factory.autonomy_fabric.research = object()
        report = factory.check_integrity()
        assert report["status"] == "failed"
        finding = next(item for item in report["findings"] if item["code"] == "DUPLICATE_OR_SPLIT_OWNER")
        assert finding["responsibility"] == "research"
        with pytest.raises(SystemIntegrityError):
            factory.integrity.assert_ready()
    finally:
        factory.runtime.close()


def test_integrity_detects_ambiguous_runtime_registration(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    factory = make_factory(tmp_path)
    try:
        factory.runtime.handlers["autonomy.run"] = lambda payload: payload
        report = factory.check_integrity()
        assert report["status"] == "failed"
        assert any(item["code"] == "AMBIGUOUS_RUNTIME_REGISTRATION" for item in report["findings"])
    finally:
        factory.runtime.close()


def test_integrity_detects_unsafe_legacy_resume_record(tmp_path):
    store = RuntimeStore(tmp_path / "legacy.db")
    try:
        with store.lock, store.db:
            store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?)",
                ("mission-resume:blocked-legacy", json.dumps({"state": "reserved", "execution_id": "old"})),
            )
        class Factory:
            config = type("Config", (), {"register_autonomy": False})()
            runtime = type("Runtime", (), {"store": store})()
        controller = SystemIntegrityController(Factory())
        report = controller.run()
        assert report["status"] == "failed"
        assert any(item["code"] == "LEGACY_RESUME_LEASE" for item in report["findings"])
    finally:
        store.close()


def test_integrity_detects_duplicate_schedule_identity(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    factory = make_factory(tmp_path)
    try:
        from aurelix_runtime.scheduler import Schedule
        class System:
            scheduler = type("Scheduler", (), {"schedules": [
                Schedule("economic-discovery", 10, "autonomy.run", {"objective": "a"}),
                Schedule("economic-discovery", 20, "autonomy.run", {"objective": "b"}),
            ]})()
        factory.system = System()
        report = factory.check_integrity()
        assert report["status"] == "failed"
        assert any(item["code"] == "DUPLICATE_SCHEDULE_IDENTITY" for item in report["findings"])
    finally:
        factory.runtime.close()
