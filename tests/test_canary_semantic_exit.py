from scripts.canary_semantic_exit import (
    guarded_stage4_exit_code,
    guarded_stage4_success,
    semantic_exit_code,
    semantic_success,
)


def test_semantic_success_requires_pass_proof_status():
    assert semantic_success({"hard_gates": {"status": "pass"}}) is True
    assert semantic_exit_code({"hard_gates": {"status": "pass"}}) == 0
    assert semantic_success({"hard_gates": {"status": "fail"}}) is False
    assert semantic_exit_code({"hard_gates": {"status": "fail"}}) == 1


def test_semantic_success_accepts_custom_proof_key():
    payload = {"multi_stage_proof_scope_summary": {"status": "pass"}}

    assert semantic_success(payload, proof_keys=("multi_stage_proof_scope_summary",)) is True
    assert semantic_exit_code(payload, proof_keys=("multi_stage_proof_scope_summary",)) == 0
    assert semantic_success(payload) is False


def test_semantic_success_blocks_failed_archive_when_present():
    payload = {"hard_gates": {"status": "pass"}, "benchmark_archive": {"status": "error"}}

    assert semantic_success(payload) is False
    assert semantic_exit_code(payload) == 1
    assert semantic_success(payload, require_archive_ok=False) is True


def test_guarded_stage4_success_requires_payload_success_and_archive_ok():
    assert guarded_stage4_success({"success": True, "benchmark_archive": {"status": "ok"}}) is True
    assert guarded_stage4_exit_code({"success": True, "benchmark_archive": {"status": "ok"}}) == 0
    assert guarded_stage4_success({"success": False, "benchmark_archive": {"status": "ok"}}) is False
    assert guarded_stage4_exit_code({"success": True, "benchmark_archive": {"status": "error"}}) == 1
