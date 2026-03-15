import json
from pathlib import Path

from modules.api.process_runner import ProcessRunner, _decode_runtime_stream


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "2026-03-13" / "encoding-boundary-contract.json"


def _read_source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_contract_locks_stage0_input_and_generated_report_policy():
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert payload["contract_id"] == "encoding-boundary-contract-v1"
    assert payload["stage0_input_policy"]["read_order"] == ["utf-8", "cp949"]
    assert payload["stage0_input_policy"]["failure_mode"] == "fail_closed"
    assert payload["operator_artifact_policy"]["authoritative_runtime_channel"] == "stdout"
    assert payload["operator_artifact_policy"]["stderr_authoritative"] is False
    assert payload["operator_artifact_policy"]["stderr_decode_policy"] == "utf-8-replace"
    assert (
        payload["scanner_generated_artifact_policy"]["ignore_name_glob"]
        == "mojibake-global-survey-*.json"
    )


def test_main_a_bootstraps_stdio_before_bootstrap_runtime_notice():
    source = _read_source("main_a.py")

    bootstrap_call = source.rindex("_bootstrap_windows_stdio_utf8()")
    faulthandler_enable = source.index("faulthandler.enable(")
    runtime_notice = source.index('print("[V61.3] Faulthandler 활성화 → crash_dump.log")')

    assert bootstrap_call < faulthandler_enable
    assert bootstrap_call < runtime_notice
    assert "if not _STDIO_BOOTSTRAPPED and sys.platform == \"win32\"" in source
    assert 'print("[V61.3] Faulthandler 활성화 → crash_dump.log", file=sys.stderr)' not in source
    assert 'print(f"[V61.3] Faulthandler 초기화 실패 (비차단): {_fh_err}", file=sys.stderr)' in source


def test_process_runner_runtime_decode_is_explicit_and_non_durable():
    assert _decode_runtime_stream(b"ok\xfftail") == "ok\ufffdtail"
    assert ProcessRunner()._build_env(None)["PYTHONIOENCODING"] == "utf-8"

    source = _read_source("modules/api/process_runner.py")
    assert "def _decode_runtime_stream(raw: bytes) -> str:" in source
    assert "def _is_benign_stderr_line(text: str) -> bool:" in source
    assert '_RUNTIME_STDERR_DECODE_POLICY = "utf-8-replace"' in source
    assert '"stderr_authoritative": False' in source
    assert source.count("_decode_runtime_stream(") >= 5


def test_stage4_smoke_console_fallback_is_named_and_utf8_outputs_remain():
    source = _read_source("scripts/run_stage4_smoke.py")

    assert "def _console_only_fallback_text(text: str) -> str:" in source
    assert 'out.write_text(f"# {final_title}\\n\\n{final_manuscript}", encoding="utf-8")' in source
