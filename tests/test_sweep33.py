from pathlib import Path
from unittest.mock import MagicMock

from modules.core.confidence_calibration import ConfidenceCalibrator
from modules.core.cross_agent_verifier import CrossAgentVerifier
from modules.core.prompt_builder import PromptBuilder
from modules.core.semantic_plot_guard import SemanticPlotGuard
from modules.core.writer_template import WriterTemplate
from modules.domain.agents.director_ensemble import DirectorEnsembleSelector


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_director_ensemble_rejects_string_scene_breakdown_as_zero_scenes():
    de = DirectorEnsembleSelector.__new__(DirectorEnsembleSelector)
    de._d = MagicMock()
    result = de._evaluate_single_blueprint(
        blueprint={"scene_breakdown": "1: 전투\n2: 대화", "integrated_scenario": "x" * 1000},
        arc_data={},
        ep_num=1,
        prev_blueprint={},
        entity_registry={},
        state_tracker=None,
    )
    assert result["decision"] == "REJECT"
    assert "씬 개수 부족" in result["reason"]


def test_cross_agent_verifier_writer_precheck_handles_string_scene_breakdown():
    cav = CrossAgentVerifier.__new__(CrossAgentVerifier)
    violations = cav._python_precheck_writer("원고 " * 3000, {"scene_breakdown": "1: 전투\n2: 대화"})
    assert isinstance(violations, list)


def test_prompt_builder_returns_empty_guide_for_string_scene_breakdown():
    pb = PromptBuilder()
    result = pb.generate_high_impact_zone_guide({"scene_breakdown": "1: 전투\n2: 대화"})
    assert result == ""


def test_writer_template_handles_string_scene_breakdown_without_crash():
    wt = WriterTemplate(genre="wuxia")
    template = wt.generate_template({"ep_num": 1, "scene_breakdown": "1: 전투\n2: 대화"})
    assert template.total_scenes == 0
    assert len(template.slots) == 0


def test_confidence_calibration_treats_string_scene_breakdown_as_zero():
    cc = ConfidenceCalibrator()
    result = cc._assess_blueprint(
        {"scene_breakdown": "1: 전투\n2: 대화", "integrated_scenario": "x" * 1200, "ending_hook": "다음 화 떡밥"},
        {},
    )
    assert result.factors["scene_count"] == 0


def test_semantic_plot_guard_converts_non_string_tactical_doc():
    spg = SemanticPlotGuard.__new__(SemanticPlotGuard)
    spg._client = None
    spg._resolved_embeddings = []
    spg._resolved_keywords = []
    result = spg.check_new_arc(tactical_doc={"content": "전투 장면"}, new_plot_names=None)
    assert isinstance(result, list)


def test_sweep33_source_guards_and_cleanup_exist():
    assert "if scene_breakdown and isinstance(scene_breakdown, dict):" in _read(
        "modules/core/constitutional_checker.py"
    )
    assert "if not scene_breakdown or not isinstance(scene_breakdown, dict):" in _read("modules/core/prompt_builder.py")
    assert "if not isinstance(scene_breakdown, dict):" in _read("modules/core/writer_template.py")
    assert "if not isinstance(scene_breakdown, dict):" in _read("modules/core/confidence_calibration.py")
    pdc = _read("modules/core/pre_director_checklist.py")
    assert "scene_count = len(_sb) if isinstance(_sb, dict) else 0" in pdc
    assert "if scene_breakdown and isinstance(scene_breakdown, dict):" in pdc
    pdm = _read("modules/core/pre_director_manuscript_checker.py")
    assert "if not scene_breakdown or not isinstance(scene_breakdown, dict):" in pdm
    assert "if not isinstance(scene_breakdown, dict) or not scene_breakdown or len(scene_breakdown) < 3:" in pdm
    assert 'scores["structure"] = min(100, 80 + (0.5 - abs(cv - 0.35)) * 100)' in _read(
        "modules/core/diversity_sampler.py"
    )
    assert "if tactical_doc and not isinstance(tactical_doc, str):" in _read("modules/core/semantic_plot_guard.py")
    assert "current_len=current_len," not in _read("modules/domain/agents/director_auditor.py")
