from pathlib import Path
from unittest.mock import MagicMock

import pytest

from modules.core.chain_of_verification import (
    ChainOfVerification,
    ChainOfVerificationLLMError,
    ChainOfVerificationParseError,
)
from modules.core.adversarial_self_play import AdversarialSelfPlay, AdversaryFeedback
from modules.core.cross_agent_verifier import CrossAgentVerifier
from modules.core.multi_agent_deliberation import AgentOpinion, AgentRole, MultiAgentDeliberation
from modules.core.quality_dashboard import QualityDashboard
from modules.core.self_reflection import ReflectionTarget, SelfReflector
from modules.core.services.audit_service import AuditService
from modules.core.stage0.story_expander import StoryExpander
from modules.core.stage0.style_extractor import StyleExtractor, StyleGuide
from modules.domain.agents import analyst_prompt_api
from modules.domain.agents.arc_critic import ArcCritic
from modules.domain.agents.director_auditor import DirectorQualityAuditor
from modules.domain.agents.director_continuity import DirectorContinuityValidator
from modules.domain.agents.consensus_validator import ConsensusValidator


def test_chain_of_verification_parse_result_handles_list_payload():
    verifier = ChainOfVerification(api_client=MagicMock())
    parsed = verifier._parse_result('[{"passed": true, "overall_severity": "none", "issues": []}]')
    assert isinstance(parsed, dict)
    assert parsed.get("overall_severity") == "none"
    assert isinstance(parsed.get("issues"), list)


def test_chain_of_verification_call_llm_raises_on_router_failure(monkeypatch):
    verifier = ChainOfVerification(api_client=MagicMock())

    def _raise_router_error(**_kwargs):
        raise RuntimeError("router down")

    monkeypatch.setattr("modules.core.chain_of_verification.generate_content_via_router", _raise_router_error)

    with pytest.raises(ChainOfVerificationLLMError, match="router down"):
        verifier._call_llm("prompt")


def test_chain_of_verification_verify_raises_on_invalid_json(monkeypatch):
    verifier = ChainOfVerification(api_client=MagicMock())
    monkeypatch.setattr(verifier, "_call_llm", lambda _prompt: "not-json")

    with pytest.raises(ChainOfVerificationParseError, match="JSONDecodeError"):
        verifier.verify("원고 " * 300, {}, content_type="manuscript")


def test_chain_of_verification_verify_preserves_tail_context(monkeypatch):
    verifier = ChainOfVerification(api_client=MagicMock())
    captured = {}

    def _fake_call(prompt):
        captured["prompt"] = prompt
        return '{"passed": true, "overall_severity": "none", "issues": [], "summary": "ok"}'

    monkeypatch.setattr(verifier, "_call_llm", _fake_call)

    generated = "HEAD-GEN\n" + ("G" * 32000) + "\nTAIL-GEN"
    qv_tail = "TAIL-QV"

    result = verifier.verify(
        generated,
        {
            "prev_manuscript": ("직전 " * 600) + "TAIL-PREV",
            "quick_verify_warnings": "HEAD-QV\n" + ("Q" * 15000) + "\n" + qv_tail,
        },
        content_type="manuscript",
    )

    assert result.passed is True
    assert "TAIL-GEN" in captured["prompt"]
    assert "TAIL-PREV" in captured["prompt"]
    assert qv_tail in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_chain_of_verification_build_context_string_preserves_section_tails():
    verifier = ChainOfVerification(api_client=MagicMock())

    hud_tail = "TAIL-HUD"
    blueprint_tail = "TAIL-BP"
    arc_tail = "TAIL-ARC"
    context_text = verifier._build_context_string(
        {
            "hud": {"payload": "H" * 16000, "tail": hud_tail},
            "blueprint": {"payload": "B" * 25000, "tail": blueprint_tail},
            "arc_data": {"payload": "A" * 16000, "tail": arc_tail},
        }
    )

    assert hud_tail in context_text
    assert blueprint_tail in context_text
    assert arc_tail in context_text
    assert "...(중간 생략)..." in context_text


def test_cross_agent_verifier_parse_result_handles_list_payload():
    verifier = CrossAgentVerifier(api_client=MagicMock())
    parsed = verifier._parse_result('[{"compliance_score": 0.9, "violations": [], "warnings": []}]')
    assert isinstance(parsed, dict)
    assert parsed.get("compliance_score") == 0.9


def test_cross_agent_verifier_writer_compliance_preserves_tail_context(monkeypatch):
    verifier = CrossAgentVerifier(api_client=MagicMock())
    captured = {}
    monkeypatch.setattr(verifier, "_python_precheck_writer", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        verifier,
        "_parse_result",
        lambda _text: {"compliance_score": 0.9, "violations": [], "warnings": [], "summary": "ok"},
    )

    def _fake_call(prompt, temperature=0.1):
        captured["prompt"] = prompt
        return '{"compliance_score": 0.9, "violations": [], "warnings": [], "summary": "ok"}'

    monkeypatch.setattr(verifier, "_call_llm", _fake_call)

    result = verifier.verify_writer_compliance(
        manuscript="HEAD-MS\n" + ("M" * 12000) + "\nTAIL-MS",
        blueprint={"payload": "B" * 20000, "tail": "TAIL-BP"},
        use_llm=True,
    )

    assert result.score == 0.9
    assert "TAIL-MS" in captured["prompt"]
    assert "TAIL-BP" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_cross_agent_verifier_architect_compliance_preserves_tail_context(monkeypatch):
    verifier = CrossAgentVerifier(api_client=MagicMock())
    captured = {}
    monkeypatch.setattr(verifier, "_python_precheck_architect", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        verifier,
        "_parse_result",
        lambda _text: {"compliance_score": 0.9, "violations": [], "warnings": [], "summary": "ok"},
    )

    def _fake_call(prompt, temperature=0.1):
        captured["prompt"] = prompt
        return '{"compliance_score": 0.9, "violations": [], "warnings": [], "summary": "ok"}'

    monkeypatch.setattr(verifier, "_call_llm", _fake_call)

    result = verifier.verify_architect_compliance(
        blueprint={"payload": "B" * 70000, "tail": "TAIL-ARCH-BP"},
        arc_design={"payload": "A" * 45000, "tail": "TAIL-ARCH-ARC"},
        use_llm=True,
    )

    assert result.score == 0.9
    assert "TAIL-ARCH-BP" in captured["prompt"]
    assert "TAIL-ARCH-ARC" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_cross_agent_verifier_no_legacy_head_cut_assignments():
    source = Path("modules/core/cross_agent_verifier.py").read_text(encoding="utf-8")

    assert 'json.dumps(arc_design, ensure_ascii=False, indent=2)[:40000]' not in source
    assert 'json.dumps(blueprint, ensure_ascii=False, indent=2)[:60000]' not in source
    assert 'json.dumps(blueprint, ensure_ascii=False, indent=2)[:15000]' not in source
    assert 'ms_text = manuscript[:8000]' not in source


def test_director_continuity_entity_prompt_preserves_tail_context():
    director = MagicMock()
    director.entity_consistency_enabled = True
    director._escape_braces.side_effect = lambda value: value
    director.ask.return_value = "raw"
    director._extract_json_robust.return_value = {"decision": "PASS", "mismatches": [], "fix_instructions": ""}
    validator = DirectorContinuityValidator(director)

    result = validator.validate_entity_consistency(
        content="HEAD-CONTENT\n" + ("C" * 20000) + "\nTAIL-DIRECTOR-CONTENT",
        entity_registry={"characters": [{"name": "홍길동"}]},
        content_type="manuscript",
    )

    assert result["decision"] == "PASS"
    prompt = director.ask.call_args.args[0]
    assert "TAIL-DIRECTOR-CONTENT" in prompt
    assert "...(중간 생략)..." in prompt


def test_director_auditor_character_logic_preserves_tail_context():
    director = MagicMock()
    director._escape_braces.side_effect = lambda value: value
    director.ask.return_value = "raw"
    director._extract_json_robust.return_value = {
        "decision": "PASS",
        "score": 90,
        "violations": [],
        "severity": "NONE",
        "feedback": "",
    }
    auditor = DirectorQualityAuditor(director)

    result = auditor.assess_character_logic(
        ep_num=7,
        manuscript="HEAD-MS\n" + ("M" * 16000) + "\nTAIL-DIRECTOR-AUDITOR",
        npc_profiles={},
        character_traits={},
    )

    assert result["decision"] == "PASS"
    prompt = director.ask.call_args.args[0]
    assert "TAIL-DIRECTOR-AUDITOR" in prompt
    assert "...(중간 생략)..." in prompt


def test_self_reflector_reflect_preserves_tail_context(monkeypatch):
    reflector = SelfReflector(api_client=MagicMock())
    captured = {}

    def _fake_call(prompt, temperature=0.2):
        captured["prompt"] = prompt
        return '{"issues": [], "severity": "none", "overall_quality": 8}'

    monkeypatch.setattr(reflector, "_call_llm", _fake_call)

    result = reflector.reflect(
        output="HEAD-OUT\n" + ("O" * 12000) + "\nTAIL-SELF-OUT",
        context="HEAD-CTX\n" + ("C" * 5000) + "\nTAIL-SELF-CTX",
        target=ReflectionTarget.WRITER,
    )

    assert result["overall_quality"] == 8
    assert "TAIL-SELF-OUT" in captured["prompt"]
    assert "TAIL-SELF-CTX" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_self_reflector_improve_preserves_tail_context(monkeypatch):
    reflector = SelfReflector(api_client=MagicMock())
    captured = {}

    def _fake_call(prompt, temperature=0.4):
        captured["prompt"] = prompt
        return ("IMPROVED " * 2000) + "TAIL-IMPROVED"

    monkeypatch.setattr(reflector, "_call_llm", _fake_call)

    improved = reflector.improve(
        original="HEAD-ORIG\n" + ("R" * 16000) + "\nTAIL-SELF-ORIG",
        critique={"severity": "high", "issues": [{"type": "continuity", "problem": "x"}]},
        target=ReflectionTarget.WRITER,
    )

    assert improved.endswith("TAIL-IMPROVED")
    assert "TAIL-SELF-ORIG" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_adversarial_self_play_feedback_preserves_tail_context(monkeypatch):
    asp = AdversarialSelfPlay(api_client=MagicMock())
    captured = {}

    def _fake_call(prompt, temperature=0.3):
        captured["prompt"] = prompt
        return '{"decision": "PASS", "score": 90, "issues": [], "praise": [], "revision_guide": ""}'

    monkeypatch.setattr(asp, "_call_llm", _fake_call)

    feedback = asp._get_adversary_feedback(
        content="HEAD-ASP\n" + ("X" * 9000) + "\nTAIL-ASP-CONTENT",
        content_type="manuscript",
        context={"payload": "C" * 4000, "tail": "TAIL-ASP-CTX"},
    )

    assert feedback.decision == "PASS"
    assert "TAIL-ASP-CONTENT" in captured["prompt"]
    assert "TAIL-ASP-CTX" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_adversarial_self_play_revision_preserves_tail_context(monkeypatch):
    asp = AdversarialSelfPlay(api_client=MagicMock())
    captured = {}

    def _fake_call(prompt, temperature=0.5):
        captured["prompt"] = prompt
        return ("IMPROVED " * 1500) + "TAIL-ASP-REVISED"

    monkeypatch.setattr(asp, "_call_llm", _fake_call)

    revised = asp._revise_content(
        original="HEAD-ASP-ORIG\n" + ("Y" * 12000) + "\nTAIL-ASP-ORIG",
        feedback=AdversaryFeedback(
            decision="REVISE",
            score=70,
            issues=[{"severity": "major", "type": "continuity", "description": "fix me"}],
            praise=[],
            revision_guide="tail issue must be fixed",
        ),
        content_type="manuscript",
    )

    assert revised.endswith("TAIL-ASP-REVISED")
    assert "TAIL-ASP-ORIG" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_multi_agent_deliberation_opinion_preserves_tail_context(monkeypatch):
    mad = MultiAgentDeliberation(api_client=MagicMock())
    captured = {}

    def _fake_call(prompt, temperature=0.3):
        captured["prompt"] = prompt
        return '{"score": 88, "strengths": [], "concerns": [], "suggestions": [], "critical_issues": []}'

    monkeypatch.setattr(mad, "_call_llm", _fake_call)

    opinion = mad._get_agent_opinion(
        AgentRole.ANALYST,
        "HEAD-MAD\n" + ("M" * 8000) + "\nTAIL-MAD-CONTENT",
        {"payload": "C" * 4000, "tail": "TAIL-MAD-CTX"},
    )

    assert opinion.score == 88
    assert "TAIL-MAD-CONTENT" in captured["prompt"]
    assert "TAIL-MAD-CTX" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_multi_agent_deliberation_consensus_preserves_tail_context(monkeypatch):
    mad = MultiAgentDeliberation(api_client=MagicMock())
    captured = {}

    def _fake_call(prompt, temperature=0.5):
        captured["prompt"] = prompt
        return ("CONSENSUS " * 1200) + "TAIL-MAD-CONSENSUS"

    monkeypatch.setattr(mad, "_call_llm", _fake_call)

    consensus = mad._build_consensus(
        "HEAD-MAD-CONS\n" + ("Z" * 9000) + "\nTAIL-MAD-CONS",
        [
            AgentOpinion(AgentRole.ANALYST, 80, ["s1"], ["c1"], ["sg1"], []),
            AgentOpinion(AgentRole.ARCHITECT, 82, ["s2"], ["c2"], ["sg2"], []),
            AgentOpinion(AgentRole.WRITER, 85, ["s3"], ["c3"], ["sg3"], []),
        ],
    )

    assert consensus.endswith("TAIL-MAD-CONSENSUS")
    assert "TAIL-MAD-CONS" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


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

    with pytest.raises(StoryExpander.BibleGenerationError, match="protagonist generation failed"):
        expander.generate_bible()

    assert expander.bible == {}


def test_story_expander_generate_bible_raises_on_empty_core_identity(monkeypatch):
    expander = StoryExpander(genre="fantasy", llm_client=None)
    expander.extracted = {"protagonist": {"main_goal": "survive"}}
    expander.preset_registry = MagicMock()
    expander.preset_registry.build_initial_hud.return_value = {}
    monkeypatch.setattr(expander, "_generate_protagonist_detail", lambda: {"name": "주인공", "core": {}})
    monkeypatch.setattr(expander, "_generate_npcs", lambda: [{"name": "조연1"}, {"name": "조연2"}])

    with pytest.raises(StoryExpander.BibleGenerationError, match="CoreIdentity missing or empty"):
        expander.generate_bible()

    assert expander.bible == {}


def test_story_expander_run_returns_empty_when_bible_generation_raises(monkeypatch, tmp_path):
    expander = StoryExpander(genre="fantasy", llm_client=None)
    expander.treatment = [{"stale": True}]
    monkeypatch.setattr("modules.core.stage0.story_expander.SPINNER_AVAILABLE", False)
    monkeypatch.setattr(expander, "analyze_concept", lambda _concept: None)
    monkeypatch.setattr(
        expander,
        "generate_bible",
        lambda _config=None: (_ for _ in ()).throw(StoryExpander.BibleGenerationError("contract fail")),
    )
    monkeypatch.setattr(expander, "generate_treatment", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(expander, "save_all", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))

    bible, treatment = expander.run("컨셉", str(tmp_path))

    assert bible == {}
    assert treatment == []


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


def test_consensus_validator_validate_with_consensus_preserves_arc_tail_context():
    validator = ConsensusValidator.__new__(ConsensusValidator)
    validator.max_workers = 1
    validator.ENSEMBLE_TIMEOUT = 5
    validator.SINGLE_VOTE_TIMEOUT = 5
    validator.perspectives = [{"name": "continuity_focused", "role": "r", "focus": "f", "temperature": 0.1}]
    validator._generate_prev_summary = MagicMock(return_value="")
    validator._derive_consensus = MagicMock(return_value=("PASS", {"vote_summary": {}}))
    captured = {}

    def _validate_single(**kwargs):
        captured["arc_data"] = kwargs["arc_data"]
        return {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": [], "reasoning": ""}

    validator._validate_single = MagicMock(side_effect=_validate_single)

    verdict, _result = validator.validate_with_consensus(
        arc={"payload": "A" * 7000, "tail": "TAIL-ARC-DATA"},
        prev_arcs=[{"arc_no": 0}],
        constraints="constraint",
    )

    assert verdict == "PASS"
    assert "TAIL-ARC-DATA" in captured["arc_data"]
    assert "...(중간 생략)..." in captured["arc_data"]


def test_consensus_validator_validate_single_preserves_constraint_tail_context():
    validator = ConsensusValidator.__new__(ConsensusValidator)
    captured = {}

    def _ask(prompt, **_kwargs):
        captured["prompt"] = prompt
        return '{"verdict":"PASS","confidence":0.9,"issues_found":[],"passed_checks":[],"reasoning":"ok"}'

    validator.ask = MagicMock(side_effect=_ask)
    validator._extract_json_robust = MagicMock(
        return_value={
            "verdict": "PASS",
            "confidence": 0.9,
            "issues_found": [],
            "passed_checks": [],
            "reasoning": "ok",
        }
    )

    result = validator._validate_single(
        arc_data="ARC",
        prev_summary="PREV",
        constraints="HEAD-CONSTRAINT\n" + ("C" * 7000) + "\nTAIL-CONSTRAINT",
        perspective={"name": "continuity_focused", "role": "r", "focus": "f", "temperature": 0.1},
        python_advisory_text="(없음)",
    )

    assert result["verdict"] == "PASS"
    assert "TAIL-CONSTRAINT" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_arc_critic_critique_preserves_tail_context():
    critic = ArcCritic.__new__(ArcCritic)
    captured = {}

    def _ask(prompt, **_kwargs):
        captured["prompt"] = prompt
        return {
            "scores": {},
            "total_score": 70,
            "verdict": "PASS",
            "critical_issues": [],
            "warnings": [],
            "auto_fixes": {},
            "revision_priority": [],
        }

    critic.ask = MagicMock(side_effect=_ask)
    critic._generate_prev_summary = MagicMock(return_value="PREV")
    critic._apply_auto_fixes = MagicMock(return_value={"fixed": True})

    result, fixed_arc = critic.critique(
        generated_arc={"payload": "A" * 20000, "tail": "TAIL-ARC-CRITIC"},
        prev_arcs=[{"arc_no": 1}],
        constraints="HEAD-CONSTRAINT\n" + ("C" * 10000) + "\nTAIL-CRITIC-CONSTRAINT",
    )

    assert result["verdict"] == "PASS"
    assert fixed_arc == {"fixed": True}
    assert "TAIL-ARC-CRITIC" in captured["prompt"]
    assert "TAIL-CRITIC-CONSTRAINT" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


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
