"""[LOG-1] SessionLogger 단위 테스트."""

import json
from unittest.mock import patch

import pytest

from modules.core.session_logger import SessionLogger


@pytest.fixture
def log_dir(tmp_path):
    return tmp_path / "session_logs"


@pytest.fixture
def logger(log_dir):
    return SessionLogger(
        log_dir=log_dir,
        enabled=True,
        max_file_mb=1,
        max_prompt_chars=500,
        max_rotations=3,
    )


@pytest.fixture
def disabled_logger(log_dir):
    return SessionLogger(log_dir=log_dir, enabled=False)


# ── 기본 동작 ───────────────────────────────────────────────


class TestBasicWrite:
    def test_log_llm_call_creates_jsonl(self, logger, log_dir):
        logger.log_llm_call(
            agent_name="director",
            model="gemini-2.5-pro",
            prompt="hello",
            response='{"result": "ok"}',
            temperature=0.5,
            duration_ms=123.4,
            success=True,
        )
        filepath = log_dir / "llm_io.jsonl"
        assert filepath.exists()
        lines = filepath.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["agent"] == "director"
        assert record["model"] == "gemini-2.5-pro"
        assert record["success"] is True
        assert record["duration_ms"] == 123.4
        assert "ts" in record

    def test_log_decision_creates_jsonl(self, logger, log_dir):
        logger.log_decision(
            stage="stage4",
            ep_num=5,
            round_num=2,
            decision_type="manuscript",
            result="PASS",
            score=92,
            advisories=["warning1", "warning2"],
        )
        filepath = log_dir / "decisions.jsonl"
        assert filepath.exists()
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["stage"] == "stage4"
        assert record["ep_num"] == 5
        assert record["result"] == "PASS"
        assert record["score"] == 92
        assert len(record["advisories"]) == 2

    def test_log_state_change_creates_jsonl(self, logger, log_dir):
        logger.log_state_change(
            ep_num=3,
            change_type="world_state",
            entity="npc_death",
            before={"alive": True},
            after={"alive": False},
            source="post_processor",
        )
        filepath = log_dir / "state_changes.jsonl"
        assert filepath.exists()
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["change_type"] == "world_state"
        assert record["before"] == {"alive": True}
        assert record["after"] == {"alive": False}


# ── disabled 모드 ───────────────────────────────────────────


class TestDisabledMode:
    def test_disabled_logger_writes_nothing(self, disabled_logger, log_dir):
        disabled_logger.log_llm_call(
            agent_name="test",
            model="test",
            prompt="test",
            response="test",
        )
        disabled_logger.log_decision(stage="s4", ep_num=1)
        disabled_logger.log_state_change(ep_num=1, change_type="ws")
        assert not log_dir.exists() or not list(log_dir.iterdir())

    def test_begin_shutdown_disables_future_writes(self, logger, log_dir):
        logger.begin_shutdown()

        logger.log_llm_call(agent_name="test", model="test", prompt="test", response="test")
        logger.log_decision(stage="s4", ep_num=1)
        logger.log_state_change(ep_num=1, change_type="ws")
        logger.log_ui_event(session_id="sess", message="ignored")

        assert not log_dir.exists() or not list(log_dir.iterdir())


# ── 프롬프트 절삭 ──────────────────────────────────────────


class TestTruncation:
    def test_long_prompt_truncated(self, logger, log_dir):
        # max_prompt_chars floor is 1000, so use 2000 to exceed it
        long_prompt = "A" * 2000
        logger.log_llm_call(
            agent_name="test",
            model="test",
            prompt=long_prompt,
            response="ok",
        )
        filepath = log_dir / "llm_io.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert len(record["prompt"]) < 2000
        assert "TRUNCATED" in record["prompt"]

    def test_short_prompt_not_truncated(self, logger, log_dir):
        short_prompt = "A" * 100
        logger.log_llm_call(
            agent_name="test",
            model="test",
            prompt=short_prompt,
            response="ok",
        )
        filepath = log_dir / "llm_io.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["prompt"] == short_prompt


# ── 로테이션 ────────────────────────────────────────────────


class TestRotation:
    def test_rotation_on_size_exceeded(self, tmp_path):
        log_dir = tmp_path / "rotate_test"
        logger = SessionLogger(
            log_dir=log_dir,
            enabled=True,
            max_file_mb=1,  # will use _max_file_bytes
            max_prompt_chars=200000,
            max_rotations=3,
        )
        # Override to tiny size for testing
        logger._max_file_bytes = 100  # 100 bytes

        # Write enough to trigger rotation
        for i in range(10):
            logger.log_decision(
                stage="test",
                ep_num=i,
                decision_type="test",
                result="PASS",
                score=90,
            )

        filepath = log_dir / "decisions.jsonl"
        rotated = log_dir / "decisions.jsonl.1"
        assert filepath.exists()
        assert rotated.exists()


# ── set_log_dir ──────────────────────────────────────────────


class TestSetLogDir:
    def test_set_log_dir_changes_path(self, logger, tmp_path):
        new_dir = tmp_path / "new_logs"
        logger.set_log_dir(new_dir)
        logger.log_decision(stage="test", ep_num=1)
        assert (new_dir / "decisions.jsonl").exists()


# ── safe_serialize ──────────────────────────────────────────


class TestSafeSerialize:
    def test_nested_dict_serialized(self, logger, log_dir):
        logger.log_state_change(
            ep_num=1,
            change_type="test",
            after={"nested": {"deep": [1, 2, 3]}},
        )
        filepath = log_dir / "state_changes.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["after"]["nested"]["deep"] == [1, 2, 3]

    def test_non_serializable_converted(self, logger, log_dir):
        class Custom:
            def __str__(self):
                return "custom_obj"

        logger.log_state_change(
            ep_num=1,
            change_type="test",
            after=Custom(),
        )
        filepath = log_dir / "state_changes.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert "custom_obj" in record["after"]


# ── meta kwargs ──────────────────────────────────────────────


class TestMetaKwargs:
    def test_extra_kwargs_in_meta(self, logger, log_dir):
        logger.log_llm_call(
            agent_name="test",
            model="test",
            prompt="p",
            response="r",
            custom_field="value",
        )
        filepath = log_dir / "llm_io.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["meta"]["custom_field"] == "value"

    def test_decision_extra_kwargs(self, logger, log_dir):
        logger.log_decision(
            stage="stage2",
            ep_num=1,
            generation_method="four_phase",
        )
        filepath = log_dir / "decisions.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["meta"]["generation_method"] == "four_phase"

    def test_decision_join_metadata_persists_in_meta(self, logger, log_dir):
        logger.log_decision(
            stage="stage4",
            ep_num=7,
            decision_type="manuscript",
            result="PASS",
            score=96,
            attempt_key="s4:ep7:arc1:a1:sess_demo",
            candidate_key="A|balanced",
            content_hash="hash-7",
            artifact_path="logs/artifacts/stage4/ep_0007/attempt_01/final_manuscript__A_balanced.txt",
            selection_reason="best candidate",
            verdict_reason="final pass rationale",
            runtime_advisory="[advisory] keep continuity",
        )
        filepath = log_dir / "decisions.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["meta"]["attempt_key"] == "s4:ep7:arc1:a1:sess_demo"
        assert record["meta"]["candidate_key"] == "A|balanced"
        assert record["meta"]["content_hash"] == "hash-7"
        assert record["meta"]["artifact_path"].endswith("final_manuscript__A_balanced.txt")
        assert record["meta"]["selection_reason"] == "best candidate"
        assert record["meta"]["verdict_reason"] == "final pass rationale"
        assert record["meta"]["runtime_advisory"] == "[advisory] keep continuity"

    def test_ui_event_creates_ui_events_jsonl(self, logger, log_dir):
        logger.log_ui_event(
            session_id="sess-ui",
            seq=3,
            component="Stage4",
            stage=4,
            ep_num=9,
            round_num=2,
            attempt_key="s4:ep9:arc1:a2:sess-ui",
            message="operator-visible frame",
            meta={"origin": "unit"},
        )
        filepath = log_dir / "ui_events.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert record["session_id"] == "sess-ui"
        assert record["seq"] == 3
        assert record["component"] == "Stage4"
        assert record["stage"] == 4
        assert record["ep_num"] == 9
        assert record["round_num"] == 2
        assert record["attempt_key"] == "s4:ep9:arc1:a2:sess-ui"
        assert record["message"] == "operator-visible frame"
        assert record["meta"]["origin"] == "unit"


# ── 에러 내성 ────────────────────────────────────────────────


class TestErrorResilience:
    def test_none_prompt_handled(self, logger, log_dir):
        """None prompt should not raise."""
        logger.log_llm_call(
            agent_name="test",
            model="test",
            prompt=None,
            response=None,
        )
        filepath = log_dir / "llm_io.jsonl"
        assert filepath.exists()

    def test_error_field_truncated(self, logger, log_dir):
        logger.log_llm_call(
            agent_name="test",
            model="test",
            prompt="p",
            response="r",
            success=False,
            error="x" * 5000,
        )
        filepath = log_dir / "llm_io.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert len(record["error"]) <= 2000


# ── [TF-28] thinking content ─────────────────────────────


class TestThinkingField:
    """[TF-28] LLM thinking content 로깅 검증."""

    def test_thinking_recorded(self, logger, log_dir):
        """Non-empty thinking → JSONL 기록."""
        logger.log_llm_call(
            agent_name="director",
            model="gemini-2.5-pro",
            prompt="evaluate",
            response='{"verdict":"PASS"}',
            thinking="Let me analyze each blueprint...\nCandidate 1 has strong arc...",
        )
        filepath = log_dir / "llm_io.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert "thinking" in record
        assert "analyze each blueprint" in record["thinking"]

    def test_empty_thinking_omitted(self, logger, log_dir):
        """Empty thinking → JSONL 미기록."""
        logger.log_llm_call(
            agent_name="director",
            model="gemini-2.5-pro",
            prompt="evaluate",
            response='{"verdict":"PASS"}',
            thinking="",
        )
        filepath = log_dir / "llm_io.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert "thinking" not in record

    def test_thinking_truncated(self, logger, log_dir):
        """Thinking도 prompt/response와 동일하게 절삭 (fixture max_prompt_chars=1000)."""
        long_thinking = "T" * 2000
        logger.log_llm_call(
            agent_name="director",
            model="gemini-2.5-pro",
            prompt="evaluate",
            response='{"verdict":"PASS"}',
            thinking=long_thinking,
        )
        filepath = log_dir / "llm_io.jsonl"
        record = json.loads(filepath.read_text(encoding="utf-8").strip())
        assert "thinking" in record
        assert len(record["thinking"]) < 2000
        assert "TRUNCATED" in record["thinking"]


class TestLoggerHealth:
    def test_health_snapshot_tracks_soft_failures(self, tmp_path):
        log_dir = tmp_path / "session"
        logger = SessionLogger(log_dir=log_dir, enabled=True)

        with patch("builtins.open", side_effect=OSError("disk full")):
            logger.log_decision(stage="stage4", ep_num=7, result="PASS")

        snapshot = logger.get_health_snapshot()
        assert snapshot["enabled"] is True
        assert snapshot["soft_failures"] == 1
        assert snapshot["last_soft_failure"]["operation"] == "write"
        assert (tmp_path / "soft_failures.jsonl").exists()
