from pathlib import Path
from unittest.mock import MagicMock

from modules.core.chain_of_verification import ChainOfVerification
from modules.core.cross_agent_verifier import CrossAgentVerifier
from modules.core.quality_dashboard import QualityDashboard
from modules.core.services.audit_service import AuditService
from modules.core.stage0.story_expander import StoryExpander
from modules.core.stage0.style_extractor import StyleExtractor, StyleGuide
from modules.domain.agents import analyst_prompt_api
from modules.domain.agents.arc_critic import ArcCritic
from modules.domain.agents.consensus_validator import ConsensusValidator


def test_chain_of_verification_parse_result_handles_list_payload():
    verifier = ChainOfVerification(api_client=MagicMock())
    parsed = verifier._parse_result('[{"passed": true, "overall_severity": "none", "issues": []}]')
    assert isinstance(parsed, dict)
    assert parsed.get("overall_severity") == "none"
    assert isinstance(parsed.get("issues"), list)


def test_cross_agent_verifier_parse_result_handles_list_payload():
    verifier = CrossAgentVerifier(api_client=MagicMock())
    parsed = verifier._parse_result('[{"compliance_score": 0.9, "violations": [], "warnings": []}]')
    assert isinstance(parsed, dict)
    assert parsed.get("compliance_score") == 0.9


def test_story_expander_analyze_concept_handles_list_json(monkeypatch):
    expander = StoryExpander(genre=None, llm_client=None)
    monkeypatch.setattr(expander, "_call_llm", lambda _prompt: '[{"suggested_genre": "fantasy"}]')
    monkeypatch.setattr("modules.core.stage0.story_expander.PresetRegistry", lambda base_genre: {"genre": base_genre})

    extracted = expander.analyze_concept("test concept")

    assert isinstance(extracted, dict)
    assert expander.genre == "fantasy"


def test_story_expander_generate_bible_clears_stale_bible_on_failure(monkeypatch):
    expander = StoryExpander(genre="fantasy", llm_client=None)
    expander.extracted = {"protagonist": {"main_goal": "survive"}}
    expander.preset_registry = MagicMock()
    expander.bible = {"stale": True}
    monkeypatch.setattr(expander, "_generate_protagonist_detail", lambda: {})

    result = expander.generate_bible()

    assert result == {}
    assert expander.bible == {}


def test_style_extractor_extract_from_drafts_handles_non_dict_llm_results(monkeypatch):
    extractor = StyleExtractor(llm_client=object())
    monkeypatch.setattr(extractor, "_deep_llm_analysis", lambda _drafts: ["bad-shape"])
    monkeypatch.setattr(extractor, "_generate_anti_patterns", lambda _drafts, _passages: "bad-shape")

    guide = extractor.extract_from_drafts(["Short test sentence."])

    assert isinstance(guide, StyleGuide)


def test_consensus_validator_derive_consensus_ignores_non_list_fields():
    validator = ConsensusValidator.__new__(ConsensusValidator)
    results = [
        {"verdict": "PASS", "issues_found": "none", "passed_checks": "ok"},
        {
            "verdict": "REJECT",
            "issues_found": [{"severity": "CRITICAL", "category": "state", "issue": "mismatch"}],
            "passed_checks": [1, "checked"],
        },
    ]

    final_verdict, consensus = validator._derive_consensus(results)

    assert final_verdict == "REJECT"
    assert len(consensus.get("critical_issues", [])) == 1
    assert consensus.get("passed_checks") == ["checked"]


def test_arc_critic_get_revision_feedback_ignores_non_list_critical_issues():
    critic = ArcCritic.__new__(ArcCritic)
    feedback = critic.get_revision_feedback({"critical_issues": "none", "revision_priority": []})
    assert isinstance(feedback, str)


def test_audit_service_runtime_audit_trim_applies_cap():
    runtime = []
    svc = AuditService(runtime_audit=runtime, project_paths_fn=lambda: None, ui_log_fn=lambda _msg: None)

    for i in range(1101):
        svc.audit_event("evt", f"m{i}")

    assert len(runtime) == 600
    assert runtime[0]["message"] == "m501"
    assert runtime[-1]["message"] == "m1100"


def test_quality_dashboard_trims_histories():
    dashboard = QualityDashboard(project_path=None)

    for i in range(700):
        dashboard.record_validation(ep_num=i + 1, result={"decision": "PASS", "score": 80}, stage=4)

    for i in range(700):
        dashboard.record_hud_anomaly(ep_num=i + 1, anomalies=[{"type": "hud", "severity": "medium"}])
        dashboard.record_blueprint_coverage(
            ep_num=i + 1,
            coverage_result={"scene_coverage": 90, "expected_scenes": 10, "reflected_scenes": 9, "valid": True},
        )

    assert len(dashboard.validation_history) == 500
    assert len(dashboard.stage_stats[4]["scores"]) == 500
    assert len(dashboard.hud_anomalies) == 500
    assert len(dashboard.blueprint_coverage) == 500


def test_analyst_prompt_api_get_plan_arc_prompt_v25_prefers_raw_template(monkeypatch):
    raw_template = '{{\n  "arc_no": "{arc_no}",\n  "hybrid_composition": {{}}\n}}'
    monkeypatch.setattr(analyst_prompt_api._PROMPT_LOADER, "get_raw", lambda _domain, _key: raw_template)

    out = analyst_prompt_api.get_plan_arc_prompt_v25(ep_count_suggestion="5")

    assert out == raw_template


def test_analyst_source_has_single_pass_safe_format_and_beats_guard():
    source = Path("modules/domain/agents/analyst.py").read_text(encoding="utf-8")
    assert "adjusted_prompt_tpl = get_plan_arc_prompt_v25()" in source
    assert "format_map(_SafeDict(**cache_safe_data))" in source
    assert "format_map(_SafeDict(**full_safe_data))" in source
    assert "if not isinstance(beats, list):" in source


def test_continuity_arc_source_has_violations_list_guard():
    source = Path("modules/domain/agents/continuity_arc.py").read_text(encoding="utf-8")
    assert "if not isinstance(violations, list):" in source
