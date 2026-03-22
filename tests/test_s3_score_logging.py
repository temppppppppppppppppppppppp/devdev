"""Stage 3 score logging regression tests."""

from __future__ import annotations

import pathlib


def test_s3_score_pass_path_sets_last_score() -> None:
    """three_phase_blueprint_generator PASS 경로에서 pipeline_result['last_score']가 세팅됨."""
    src = pathlib.Path("modules/domain/agents/three_phase_blueprint_runtime.py").read_text(encoding="utf-8")
    assert 'pipeline_result["last_score"] = score' in src

    pass_block_idx = src.index('pipeline_result["final_verdict"] = verdict')
    last_score_idx = src.index('pipeline_result["last_score"] = score')
    assert abs(last_score_idx - pass_block_idx) < 300, "last_score 세팅이 final_verdict와 너무 멀리 떨어짐"


def test_s3_score_orchestrator_pass_has_fallback() -> None:
    """stage3_orchestrator PASS 경로의 _score 추출이 phases 폴백을 포함함."""
    src = pathlib.Path("modules/core/stage3_orchestrator.py").read_text(encoding="utf-8")
    assert "phases" in src and "selected_score" in src
    assert 'pipeline_result.get("last_score") or pipeline_result.get("phases"' in src


def test_s3_score_extraction_logic() -> None:
    """pipeline_result에 last_score 없을 때 phases 폴백으로 score 추출."""

    def extract_score(pipeline_result: dict) -> int:
        _score = pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get(
            "selected_score", 0
        )
        if not isinstance(_score, int):
            try:
                _score = int(_score)
            except (ValueError, TypeError):
                _score = 0
        return _score

    pr1 = {"phases": {"generate": {"selected_score": 95}}}
    assert extract_score(pr1) == 95

    pr2 = {"last_score": 88, "phases": {"generate": {"selected_score": 95}}}
    assert extract_score(pr2) == 88

    pr3 = {}
    assert extract_score(pr3) == 0
