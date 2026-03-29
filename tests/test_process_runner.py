"""ProcessRunner 단위 테스트 — Step 4a/4b 검증."""

import asyncio
import json
import sqlite3
import time

import pytest

from modules.api import process_runner
from modules.api.process_runner import ProcessRunner, _strip_ansi


def _seed_runner_project(
    tmp_path,
    monkeypatch,
    *,
    project_name: str = "sample-project",
    selected_genre_type: str = "investment",
    stored_genre_type: str | None = None,
) -> dict:
    projects_root = tmp_path / "projects"
    project_dir = projects_root / project_name
    project_dir.mkdir(parents=True)

    db_path = project_dir / "project_data.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE anchors (
                key TEXT PRIMARY KEY,
                data TEXT,
                updated_at TEXT
            )
            """
        )
        if stored_genre_type is not None:
            payload = json.dumps({"name": stored_genre_type, "type": stored_genre_type}, ensure_ascii=False)
            conn.execute(
                "INSERT INTO anchors (key, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                ("genre_info", payload),
            )
        conn.commit()

    monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(projects_root))
    return {
        "genre_index": 3,
        "genre_type": selected_genre_type,
        "project_index": 1,
        "project_name": project_name,
    }


class TestStripAnsi:
    """ANSI 이스케이프 코드 제거."""

    def test_plain_text(self):
        assert _strip_ansi("hello world") == "hello world"

    def test_color_codes(self):
        assert _strip_ansi("\x1b[31mERROR\x1b[0m") == "ERROR"

    def test_bold_underline(self):
        assert _strip_ansi("\x1b[1m\x1b[4mBOLD\x1b[0m") == "BOLD"

    def test_cursor_movement(self):
        assert _strip_ansi("\x1b[2A\x1b[10Gtext") == "text"

    def test_osc_sequence(self):
        assert _strip_ansi("\x1b]0;title\x07content") == "content"

    def test_carriage_return(self):
        assert _strip_ansi("line1\rline2") == "line1line2"

    def test_mixed(self):
        text = "\x1b[32m✓\x1b[0m Stage 4 \x1b[1mPASS\x1b[0m (87점)\r"
        result = _strip_ansi(text)
        assert "✓" in result
        assert "PASS" in result
        assert "87점" in result
        assert "\x1b" not in result
        assert "\r" not in result

    def test_empty_string(self):
        assert _strip_ansi("") == ""

    def test_whitespace_only_stripped(self):
        assert _strip_ansi("   ") == ""


class TestProcessRunnerState:
    """상태머신 테스트."""

    def test_initial_state(self):
        runner = ProcessRunner()
        assert runner.state == "idle"
        assert runner.run_id is None
        assert runner.pid is None

    def test_stop_idempotent(self):
        """idle 상태에서 stop 호출해도 에러 없음."""
        runner = ProcessRunner()
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(runner.stop())
        finally:
            loop.close()
        assert runner.state == "idle"


class TestStdinSequence:
    """stdin 시퀀스 빌드 테스트."""

    def test_basic_key_mode_a_skips_genre_confirm_when_genre_matches(self, monkeypatch, tmp_path):
        runner = ProcessRunner()
        runner._mode = "A"
        inputs = _seed_runner_project(
            tmp_path,
            monkeypatch,
            stored_genre_type="investment",
        )
        seq = runner._build_stdin_sequence("4", None, inputs)
        lines = seq.strip().split("\n")
        assert lines[0] == "3"  # genre_index default (투자물)
        assert lines[1] == ""   # [Enter] 프로젝트 이동
        assert lines[2] == "1"  # project_index default
        assert lines[3] == "4"  # same genre: confirm 없이 menu key 진입
        # 확인 패딩 5개
        assert lines[4:9] == ["y"] * 5
        assert lines[9] == "5"  # exit

    def test_stage0_with_subkey_mode_a_injects_genre_confirm_on_mismatch(self, monkeypatch, tmp_path):
        runner = ProcessRunner()
        runner._mode = "A"
        inputs = _seed_runner_project(
            tmp_path,
            monkeypatch,
            stored_genre_type="wuxia",
        )
        seq = runner._build_stdin_sequence("0", "1", inputs)
        lines = seq.strip().split("\n")
        assert lines[0] == "3"  # genre
        assert lines[1] == ""   # [Enter]
        assert lines[2] == "1"  # project
        assert lines[3] == "y"  # mismatch confirm
        assert lines[4] == "0"  # stage 0
        assert lines[5] == "1"  # sub_key

    def test_custom_project_index(self):
        runner = ProcessRunner()
        runner._mode = "A"
        seq = runner._build_stdin_sequence("2", None, {"project_index": 3})
        lines = seq.strip().split("\n")
        assert lines[2] == "3"  # project at position 2

    def test_custom_confirm_count_mode_a(self, monkeypatch, tmp_path):
        runner = ProcessRunner()
        runner._mode = "A"
        inputs = _seed_runner_project(
            tmp_path,
            monkeypatch,
            stored_genre_type="wuxia",
        )
        inputs["confirm_count"] = 10
        seq = runner._build_stdin_sequence("6", None, inputs)
        lines = seq.strip().split("\n")
        # 1 genre + 1 enter + 1 project + 1 confirm + 1 key + 10 confirms + 1 exit = 16
        assert len(lines) == 16

    def test_mode_b_boot_sequence_skips_confirm_when_stored_genre_absent(self, monkeypatch, tmp_path):
        """Mode B: stored genre가 없으면 confirm을 미리 주입하지 않는다."""
        runner = ProcessRunner()
        runner._mode = "B"
        inputs = _seed_runner_project(
            tmp_path,
            monkeypatch,
            stored_genre_type=None,
        )
        seq = runner._build_stdin_sequence("4", None, inputs)
        lines = seq.strip().split("\n")
        assert lines[0] == "3"  # genre_index default (투자물)
        assert lines[1] == ""   # [Enter]
        assert lines[2] == "1"  # project_index default
        assert lines[3] == "4"  # stored genre absent: confirm 없이 menu key 진입
        assert len(lines) == 4  # Mode B: 확인 패딩/exit 없음

    def test_mode_b_stage0_subkey_injects_confirm_on_mismatch(self, monkeypatch, tmp_path):
        """Mode B: stored genre mismatch일 때만 confirm을 먼저 소비한다."""
        runner = ProcessRunner()
        runner._mode = "B"
        inputs = _seed_runner_project(
            tmp_path,
            monkeypatch,
            stored_genre_type="wuxia",
        )
        seq = runner._build_stdin_sequence("0", "1", inputs)
        lines = seq.strip().split("\n")
        assert lines[3] == "y"  # mismatch confirm
        assert lines[4] == "0"  # stage 0
        assert lines[5] == "1"  # sub_key
        assert len(lines) == 6

    def test_stdin_lines_override(self):
        runner = ProcessRunner()
        seq = runner._build_stdin_sequence("X", "Y", {"stdin_lines": ["a", "b", "c"]})
        assert seq == "a\nb\nc\n"

    def test_ends_with_newline(self):
        runner = ProcessRunner()
        seq = runner._build_stdin_sequence("2", None, None)
        assert seq.endswith("\n")


class TestBuildEnv:
    """환경 변수 빌드 테스트."""

    def test_default_env(self):
        runner = ProcessRunner()
        env = runner._build_env(None)
        assert env["PYTHONIOENCODING"] == "utf-8"
        assert env["PYTHONUNBUFFERED"] == "1"

    def test_api_key_injection(self):
        runner = ProcessRunner()
        env = runner._build_env({"api_key": "AIzaTestKey123"})
        assert env["GOOGLE_API_KEY"] == "AIzaTestKey123"

    def test_extra_keys(self):
        runner = ProcessRunner()
        env = runner._build_env({"api_key_2": "key2", "api_key_5": "key5"})
        assert env["GOOGLE_API_KEY_2"] == "key2"
        assert env["GOOGLE_API_KEY_5"] == "key5"
        assert "GOOGLE_API_KEY_3" not in env

    def test_slack_webhook(self):
        runner = ProcessRunner()
        env = runner._build_env({"slack_webhook": "https://hooks.slack.com/xxx"})
        assert env["SLACK_WEBHOOK_URL"] == "https://hooks.slack.com/xxx"

    def test_empty_values_skipped(self):
        runner = ProcessRunner()
        env = runner._build_env({"api_key": "", "slack_webhook": ""})
        # 빈 문자열은 falsy → 설정하지 않음
        # 기존 환경의 GOOGLE_API_KEY가 있을 수도 있으므로 추가 확인 불가
        # 빈 값이 주입되지 않았는지만 확인
        assert env.get("SLACK_WEBHOOK_URL") is None

    def test_default_provider_mode_scrubs_non_gemini_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
        monkeypatch.setenv("CLAUDE_API", "sk-claude")
        monkeypatch.setenv("VERTEX_API_KEY", "vk")
        monkeypatch.setenv("VERTEX_PROJECT_ID", "proj")
        monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/sa.json")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")

        runner = ProcessRunner()
        env = runner._build_env({})

        assert env["GEULDOBI_PROVIDER_MODE"] == "gemini_direct"
        for key in (
            "ANTHROPIC_API_KEY",
            "CLAUDE_API",
            "VERTEX_API_KEY",
            "VERTEX_PROJECT_ID",
            "VERTEX_LOCATION",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "OPENAI_API_KEY",
        ):
            assert key not in env

    def test_ambient_provider_mode_preserves_non_gemini_passthrough(self):
        runner = ProcessRunner()
        env = runner._build_env(
            {
                "provider_mode": "ambient",
                "anthropic_api_key": "sk-ant-123",
                "vertex_api_key": "vk-123",
                "vertex_project_id": "my-proj",
                "vertex_location": "us-central1",
                "google_credentials_path": "/tmp/sa.json",
                "openai_api_key": "sk-openai",
            }
        )

        assert env["GEULDOBI_PROVIDER_MODE"] == "ambient"
        assert env["ANTHROPIC_API_KEY"] == "sk-ant-123"
        assert env["CLAUDE_API"] == "sk-ant-123"
        assert env["VERTEX_API_KEY"] == "vk-123"
        assert env["VERTEX_PROJECT_ID"] == "my-proj"
        assert env["VERTEX_LOCATION"] == "us-central1"
        assert env["GOOGLE_APPLICATION_CREDENTIALS"] == "/tmp/sa.json"
        assert env["OPENAI_API_KEY"] == "sk-openai"


class TestPathResolution:
    def test_resolve_projects_root_prefers_explicit_env(self, monkeypatch, tmp_path):
        explicit_root = tmp_path / "workspace-projects"
        monkeypatch.setenv("GEULDOBI_PROJECTS_ROOT", str(explicit_root))
        monkeypatch.setenv("GEULDOBI_WORKSPACE", str(tmp_path / "workspace"))

        assert process_runner._resolve_projects_root() == explicit_root.resolve()

    def test_resolve_launch_command_falls_back_to_main_script_when_engine_exe_missing(self, monkeypatch, tmp_path):
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        main_script = engine_root / "main_a.py"
        main_script.write_text("print('ok')\n", encoding="utf-8")

        monkeypatch.setattr(process_runner, "PROJECT_ROOT", engine_root)
        monkeypatch.setenv("GEULDOBI_ENGINE_EXE", str(engine_root / "engine.exe"))
        monkeypatch.setenv("GEULDOBI_PYTHON_PATH", "embedded-python.exe")

        assert process_runner._resolve_launch_command() == [
            "embedded-python.exe",
            "-u",
            str(main_script),
        ]


class TestRuntimeDiagnostics:
    def test_runtime_diagnostics_include_recent_tails(self):
        runner = ProcessRunner()
        runner._key = "4"
        runner._sub_key = "1"
        runner._mode = "B"
        runner._started_at_iso = "2026-03-10T00:00:00+00:00"
        runner._started_monotonic = time.monotonic() - 1.2
        runner.remember_prompt_step("style_choice")
        runner._remember_stdout_line("stdout one")
        runner._remember_stderr_line("stderr boom")

        diagnostics = runner.get_runtime_diagnostics()

        assert diagnostics["key"] == "4"
        assert diagnostics["sub_key"] == "1"
        assert diagnostics["last_prompt_step"] == "style_choice"
        assert diagnostics["failure_phase"] == "prompt:style_choice"
        assert diagnostics["stdout_tail"][-1] == "stdout one"
        assert diagnostics["stderr_tail"][-1] == "stderr boom"
        assert diagnostics["stderr_authoritative"] is False
        assert diagnostics["stderr_decode_policy"] == "utf-8-replace"
        assert diagnostics["duration_ms"] >= 1000

    def test_runtime_diagnostics_ignore_benign_bootstrap_stderr_notice(self):
        runner = ProcessRunner()
        runner._remember_stderr_line("[V61.3] Faulthandler 활성화 → crash_dump.log")

        diagnostics = runner.get_runtime_diagnostics()

        assert diagnostics["stderr_tail"] == []
        assert diagnostics["failure_phase"] == "startup"


class TestBridgeServerWiring:
    """bridge_server.py 배선 검증 (fastapi 필수)."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_fastapi(self):
        pytest.importorskip("fastapi")

    def test_import_bridge_server(self):
        """bridge_server 모듈 import 성공."""
        from modules.api.bridge_server import app
        assert app is not None

    def test_build_event_structure(self):
        from modules.api.bridge_server import _build_event
        ev = _build_event("run-123", "stdout", {"text": "hello"})
        assert ev["event_version"] == "v1"
        assert ev["run_id"] == "run-123"
        assert ev["type"] == "stdout"
        assert ev["payload"]["text"] == "hello"
        assert "seq" in ev
        assert "ts" in ev

    def test_build_run_exit_payload_includes_runtime_diagnostics(self):
        from modules.api.bridge_server import _build_run_exit_payload

        runner = ProcessRunner()
        runner._key = "4"
        runner._mode = "B"
        runner._started_at_iso = "2026-03-10T00:00:00+00:00"
        runner._started_monotonic = time.monotonic() - 0.5
        runner._remember_stdout_line("last stdout")
        runner._remember_stderr_line("last stderr")
        runner.remember_prompt_step("confirm_api")

        payload = _build_run_exit_payload(runner, 2)

        assert payload["returncode"] == 2
        assert payload["key"] == "4"
        assert payload["failure_phase"] == "prompt:confirm_api"
        assert payload["stdout_tail"][-1] == "last stdout"
        assert payload["stderr_tail"][-1] == "last stderr"
        assert payload["stderr_authoritative"] is False
        assert payload["stderr_decode_policy"] == "utf-8-replace"
