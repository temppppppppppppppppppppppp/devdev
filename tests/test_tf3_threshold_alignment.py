"""TF3 H6 regression: YAML/code default alignment for vector retrieval caps."""

import json
from pathlib import Path

import yaml


def test_stage2_defaults_align_with_validation_yaml():
    validation = yaml.safe_load(Path("config/settings/validation.yaml").read_text(encoding="utf-8"))
    assert int(validation["context"]["vector_max_results_s2"]) == 40
    text = Path("modules/core/stage2_preflight.py").read_text(encoding="utf-8")
    assert '_threshold("context.vector_max_results_s2", 40)' in text


def test_stage3_stage4_defaults_align_with_validation_yaml():
    validation = yaml.safe_load(Path("config/settings/validation.yaml").read_text(encoding="utf-8"))
    assert int(validation["context"]["vector_max_results_s4"]) == 50
    text3 = Path("modules/core/stage3_orchestrator.py").read_text(encoding="utf-8")
    text4 = Path("modules/core/stage4_context_builder.py").read_text(encoding="utf-8")
    assert '_s3_th("context.vector_max_results_s4", 50)' in text3
    assert '_threshold("context.vector_max_results_s4", 50)' in text4


def test_validation_threshold_single_truth_uses_validation_yaml_defaults():
    validation = yaml.safe_load(Path("config/settings/validation.yaml").read_text(encoding="utf-8"))
    settings = json.loads(Path("config/settings.json").read_text(encoding="utf-8"))
    orchestrator_text = Path("modules/validation/validation_orchestrator.py").read_text(encoding="utf-8")
    auditor_text = Path("modules/domain/agents/director_auditor.py").read_text(encoding="utf-8")

    assert int(validation["scoring"]["default_pass_threshold"]) == 60
    assert "scoring_threshold" not in settings["validation"]
    assert '"scoring_threshold"' in orchestrator_text
    assert "config.get(" in orchestrator_text
    assert '_threshold("scoring.default_pass_threshold", 60)' in orchestrator_text
    assert '"scoring_threshold": _threshold("scoring.default_pass_threshold", 60)' in auditor_text
