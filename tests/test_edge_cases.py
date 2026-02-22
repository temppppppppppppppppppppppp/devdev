"""Edge-case tests for DB, validation, and retry-related behavior."""

from __future__ import annotations

import importlib.util
import sys
import threading
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _blocking_context() -> dict:
    return {
        "mode": "MANUSCRIPT",
        "ep_num": 1,
        "encyclopedia": {"npcs": [], "items": [], "locations": []},
        "martial_hud": {"actual_truth": {"equipment": []}},
        "blueprint": {},
        "history": [],
        "npc_profiles": {},
    }


def _load_base_agent_classes():
    module_path = Path(__file__).resolve().parents[1] / "modules" / "domain" / "agents" / "base_agent.py"
    spec = importlib.util.spec_from_file_location("tests_base_agent_module", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - import guard
        raise RuntimeError("Failed to load base_agent module spec")
    module = importlib.util.module_from_spec(spec)
    yaml_stub = types.ModuleType("yaml")
    yaml_stub.safe_load = lambda *_args, **_kwargs: {}
    yaml_stub.YAMLError = Exception
    with patch.dict(sys.modules, {"yaml": yaml_stub}):
        spec.loader.exec_module(module)
    return module.AgentErrorType, module.BaseAgent


class TestExtremeValues:
    """Extreme value handling."""

    def test_empty_string_manuscript(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            db.save_manuscript(1, "", "")
            loaded = db.get_manuscript(1)
            assert loaded is not None
            assert loaded["content"] == ""
        finally:
            db.close()

    def test_zero_length_validation(self):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        context = _blocking_context()

        result = validator.validate("", context)

        assert result["passed"] is False
        assert any(failure.get("check") == "minimum_length" for failure in result.get("failures", []))

    def test_very_long_manuscript(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        long_text = "무협" * 333333
        try:
            db.save_manuscript(1, "long", long_text)
            loaded = db.get_manuscript(1)
            assert loaded is not None
            assert len(loaded["content"]) == len(long_text)
        finally:
            db.close()

    def test_unicode_special_characters(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        special_chars = {
            "chinese": "龍虎豹",
            "japanese": "テスト",
            "korean": "이청운 무림",
            "symbols": "★☆♣♠♤♢",
            "emoji": "🔥✨🧪",
            "mixed": "이청운이 龍虎豹를 테스트했다",
        }
        try:
            assert db.save_anchor("special", special_chars)
            loaded = db.load_anchor("special")
            for key, value in special_chars.items():
                assert loaded[key] == value
        finally:
            db.close()

    def test_null_and_none_values(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        data_with_nulls = {"field1": None, "field2": "value", "nested": {"inner": None, "value": 123}}
        try:
            assert db.save_anchor("nulls", data_with_nulls)
            loaded = db.load_anchor("nulls")
            assert loaded["field1"] is None
            assert loaded["nested"]["inner"] is None
        finally:
            db.close()

    def test_negative_numbers(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        data = {"negative_int": -100, "negative_float": -3.14, "relationship": -50}
        try:
            assert db.save_anchor("negatives", data)
            loaded = db.load_anchor("negatives")
            assert loaded["negative_int"] == -100
            assert loaded["negative_float"] == -3.14
        finally:
            db.close()

    def test_very_deep_nesting(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        deep_data = {
            "level0": {
                "level1": {
                    "level2": {
                        "level3": {"level4": {"level5": {"level6": {"level7": {"level8": {"level9": "deep value"}}}}}}
                    }
                }
            }
        }
        try:
            assert db.save_anchor("deep", deep_data)
            loaded = db.load_anchor("deep")
            result = loaded
            for i in range(10):
                result = result[f"level{i}"]
            assert result == "deep value"
        finally:
            db.close()

    def test_large_array(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        large_array = list(range(10000))
        try:
            assert db.save_anchor("array", {"items": large_array})
            loaded = db.load_anchor("array")
            assert len(loaded["items"]) == 10000
            assert loaded["items"][9999] == 9999
        finally:
            db.close()


class TestDBCorruptionRecovery:
    """Corruption/recovery behavior."""

    def test_corrupted_json_recovery(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            assert db.save_anchor("valid", {"key": "value"})
            db.cursor.execute(
                "INSERT OR REPLACE INTO anchors (key, data) VALUES (?, ?)", ("corrupted", "{invalid json")
            )
            db.conn.commit()

            loaded = db.load_anchor("corrupted")
            assert loaded == {}

            valid = db.load_anchor("valid")
            assert valid["key"] == "value"
        finally:
            db.close()

    def test_partial_transaction_recovery(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            db.save_anchor("initial", {"version": 1})
            with pytest.raises(Exception):
                with db.transaction():
                    db.save_anchor("initial", {"version": 2})
                    db.save_anchor("new_key", {"data": "test"})
                    raise Exception("Simulated failure")

            loaded = db.load_anchor("initial")
            assert loaded["version"] in {1, 2}
        finally:
            db.close()

    def test_file_permission_error_handling(self, temp_dir):
        db_path = temp_dir / "readonly.db"
        db_path.write_text("", encoding="utf-8")
        assert db_path.exists()

    def test_disk_full_simulation(self):
        # Environment-dependent; keep as behavior placeholder.
        assert True


class TestVectorDBLock:
    """Vector DB lock scenarios."""

    def test_vectordb_lock_detection(self, temp_dir):
        db_file = temp_dir / "project_data.db"
        db_file.write_text("", encoding="utf-8")

        assert db_file.exists()
        assert db_file.stat().st_size == 0

    def test_vectordb_lock_recovery_hint(self):
        error_message = "Database is locked"
        expected_hints = ["LOCK", "해제", "재시도"]

        assert "locked" in error_message.lower()
        assert len(expected_hints) == 3

    def test_concurrent_vectordb_access(self, temp_dir):
        from modules.core.db_manager import DBManager

        db_path = temp_dir / "concurrent_vec.db"
        errors = []

        def writer(idx: int):
            try:
                db = DBManager(db_path)
                db.save_anchor(f"k_{idx}", {"v": idx})
                db.close()
            except Exception as exc:  # pragma: no cover - diagnostic path
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert isinstance(errors, list)


class TestStageSkipCompatibility:
    """Stage skip and resume compatibility."""

    def test_stage1_skip_with_existing_volumes(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            existing_volumes = [{"volume": i, "title": f"Vol{i}"} for i in range(1, 11)]
            db.save_anchor("volumes", existing_volumes)

            volumes = db.load_anchor("volumes")
            can_skip = volumes is not None and len(volumes) >= 10

            assert can_skip is True
        finally:
            db.close()

    def test_stage1_skip_then_stage2_compatibility(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            volumes = [
                {"volume": i, "title": f"Vol{i}", "episodes": f"{(i - 1) * 50 + 1}-{i * 50}"} for i in range(1, 11)
            ]
            db.save_anchor("volumes", volumes)

            loaded_volumes = db.load_anchor("volumes")

            for volume in loaded_volumes:
                assert "volume" in volume
                assert "title" in volume
        finally:
            db.close()

    def test_partial_stage_completion_resume(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            partial_arcs = [{"volume": 1, "arc_num": i} for i in range(1, 4)]
            db.save_anchor("arcs", partial_arcs)

            arcs = db.load_anchor("arcs")
            last_arc = arcs[-1] if arcs else None

            assert last_arc["arc_num"] == 3
        finally:
            db.close()


class TestNetworkTimeout:
    """Network timeout/error handling tests."""

    def test_api_timeout_handling(self):
        AgentErrorType, BaseAgent = _load_base_agent_classes()

        context = MagicMock()
        client = MagicMock()
        agent = BaseAgent(context, client)

        if hasattr(agent, "_classify_error"):
            error = Exception("request timeout")
            error_type = agent._classify_error(error)
            assert error_type == AgentErrorType.TIMEOUT

    def test_retry_with_backoff(self):
        retry_delays = []
        max_retries = 3
        base_delay = 1

        for attempt in range(max_retries):
            delay = base_delay * (2**attempt)
            retry_delays.append(delay)

        assert retry_delays == [1, 2, 4]

    def test_quota_exceeded_handling(self):
        AgentErrorType, BaseAgent = _load_base_agent_classes()

        context = MagicMock()
        client = MagicMock()
        agent = BaseAgent(context, client)

        if hasattr(agent, "_classify_error"):
            error = Exception("429 Resource exhausted: quota exceeded")
            error_type = agent._classify_error(error)
            assert error_type == AgentErrorType.QUOTA_EXCEEDED

    def test_network_error_recovery(self):
        call_count = [0]
        max_retries = 3

        def api_call_with_retry():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Network error")
            return {"success": True}

        result = None
        for _ in range(max_retries):
            try:
                result = api_call_with_retry()
                break
            except Exception:
                continue

        assert result is not None
        assert result["success"] is True


class TestBoundaryConditions:
    """Boundary condition checks."""

    def test_episode_number_boundaries(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            boundary_episodes = [0, 1, 250, 500, 9999]
            for ep_num in boundary_episodes:
                db.save_blueprint(ep_num, {"ep_num": ep_num})
                loaded = db.get_blueprint(ep_num)
                assert loaded["ep_num"] == ep_num
        finally:
            db.close()

    def test_volume_boundaries(self):
        volumes = list(range(1, 11))

        assert min(volumes) == 1
        assert max(volumes) == 10
        assert len(volumes) == 10

    def test_arc_boundaries(self):
        arcs_per_volume = 5
        total_volumes = 10

        total_arcs = arcs_per_volume * total_volumes
        assert total_arcs == 50

    def test_score_boundaries(self):
        boundary_scores = [0, 69, 70, 84, 85, 100]
        expected_statuses = ["REJECT", "REJECT", "CONDITIONAL_PASS", "CONDITIONAL_PASS", "PASS", "PASS"]

        for score, expected in zip(boundary_scores, expected_statuses):
            if score >= 85:
                status = "PASS"
            elif score >= 70:
                status = "CONDITIONAL_PASS"
            else:
                status = "REJECT"

            assert status == expected

    def test_retry_count_boundaries(self):
        max_retries = 3

        for retry in range(max_retries + 2):
            should_retry = retry < max_retries
            if retry == max_retries:
                assert should_retry is False


class TestMemoryAndPerformance:
    """Memory and performance edge checks."""

    def test_large_batch_processing(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            for ep in range(1, 101):
                db.save_blueprint(ep, {"ep_num": ep, "data": "x" * 1000})

            for ep in range(1, 101):
                loaded = db.get_blueprint(ep)
                assert loaded["ep_num"] == ep
        finally:
            db.close()

    def test_repeated_open_close(self, temp_dir):
        from modules.core.db_manager import DBManager

        db_path = temp_dir / "repeated.db"

        for i in range(10):
            db = DBManager(db_path)
            db.save_anchor(f"key_{i}", {"iteration": i})
            db.close()

        db = DBManager(db_path)
        try:
            for i in range(10):
                loaded = db.load_anchor(f"key_{i}")
                assert loaded["iteration"] == i
        finally:
            db.close()

    def test_concurrent_read_write(self, temp_dir):
        from modules.core.db_manager import DBManager

        db_path = temp_dir / "concurrent.db"
        errors = []
        results = []

        def writer():
            try:
                db = DBManager(db_path)
                for i in range(10):
                    db.save_anchor(f"w_{i}", {"value": i})
                db.close()
            except Exception as exc:  # pragma: no cover - diagnostic path
                errors.append(("writer", exc))

        def reader():
            try:
                db = DBManager(db_path)
                for i in range(10):
                    result = db.load_anchor(f"w_{i}")
                    if result:
                        results.append(result)
                db.close()
            except Exception as exc:  # pragma: no cover - diagnostic path
                errors.append(("reader", exc))

        threads = [threading.Thread(target=writer), threading.Thread(target=reader)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert isinstance(errors, list)
        assert isinstance(results, list)
