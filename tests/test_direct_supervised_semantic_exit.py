from pathlib import Path

from scripts.direct_supervised_semantic_exit import semantic_exit_code


def test_semantic_exit_code_requires_success_true():
    assert semantic_exit_code({"success": True}) == 0
    assert semantic_exit_code({"success": False}) == 1
    assert semantic_exit_code({"success": None}) == 1
    assert semantic_exit_code({}) == 1
    assert semantic_exit_code(None) == 1


def test_semantic_exit_code_requires_archive_ok_when_archive_present():
    assert semantic_exit_code({"success": True, "benchmark_archive": {"status": "ok"}}) == 0
    assert semantic_exit_code({"success": True, "benchmark_archive": {"status": "error"}}) == 1
    assert semantic_exit_code({"success": True, "benchmark_archive": {"status": "operational_failure"}}) == 1
    assert semantic_exit_code({"success": True, "benchmark_archive": {}}) == 0


def test_direct_supervised_mains_return_semantic_exit_code():
    for script in (
        "scripts/run_stage2_direct_supervised.py",
        "scripts/run_stage3_direct_supervised.py",
        "scripts/run_stage4_direct_supervised.py",
    ):
        source = Path(script).read_text(encoding="utf-8")
        assert "from scripts.direct_supervised_semantic_exit import semantic_exit_code" in source
        assert "return semantic_exit_code(payload)" in source
