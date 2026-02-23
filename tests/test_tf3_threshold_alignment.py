"""TF3 H6 regression: YAML/code default alignment for vector retrieval caps."""

from pathlib import Path


def test_stage2_defaults_align_with_validation_yaml():
    text = Path("modules/core/stage2_preflight.py").read_text(encoding="utf-8")
    # [P0-B3-2] 기본값을 YAML 값(16)과 정합
    assert '_threshold("context.vector_max_results_s2", 16)' in text


def test_stage3_stage4_defaults_align_with_validation_yaml():
    text3 = Path("modules/core/stage3_orchestrator.py").read_text(encoding="utf-8")
    text4 = Path("modules/core/stage4_context_builder.py").read_text(encoding="utf-8")
    assert '_s3_th("context.vector_max_results_s4", 16)' in text3
    assert '_threshold("context.vector_max_results_s4", 20)' in text4
