"""Validation test suite for tiered validators."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _minimal_blocking_context(mode: str = "MANUSCRIPT") -> dict:
    return {
        "mode": mode,
        "ep_num": 1,
        "encyclopedia": {"npcs": [], "items": [], "locations": []},
        "martial_hud": {"actual_truth": {"equipment": []}},
        "blueprint": {},
        "history": [],
        "npc_profiles": {},
    }


def _to_blocking_context(base_context: dict, mode: str = "MANUSCRIPT") -> dict:
    """Normalize legacy fixture schema to current BlockingValidator schema."""
    ctx = copy.deepcopy(base_context)

    encyclopedia = ctx.get("encyclopedia")
    if not isinstance(encyclopedia, dict):
        encyclopedia = {}

    npcs = []
    characters = encyclopedia.get("characters")
    if isinstance(characters, dict):
        for name, payload in characters.items():
            info = payload if isinstance(payload, dict) else {}
            npcs.append(
                {
                    "name": str(name),
                    "status": "dead" if info.get("alive") is False else "alive",
                    "relationship_state": info.get("relationship_state", "중립"),
                }
            )
    if isinstance(encyclopedia.get("npcs"), list):
        for npc in encyclopedia["npcs"]:
            if isinstance(npc, dict):
                npcs.append(npc)

    items = []
    raw_items = encyclopedia.get("items")
    if isinstance(raw_items, dict):
        for name, payload in raw_items.items():
            info = payload if isinstance(payload, dict) else {}
            aliases = info.get("aliases", [])
            if not isinstance(aliases, list):
                aliases = []
            items.append(
                {
                    "name": str(name),
                    "owner": info.get("owner", ""),
                    "status": "destroyed" if info.get("destroyed") else "normal",
                    "aliases": aliases,
                }
            )
    elif isinstance(raw_items, list):
        items = [item for item in raw_items if isinstance(item, dict)]

    locations = []
    raw_locations = encyclopedia.get("locations")
    if isinstance(raw_locations, dict):
        for name, payload in raw_locations.items():
            info = payload if isinstance(payload, dict) else {}
            locations.append({"name": str(name), "status": "destroyed" if info.get("destroyed") else "active"})
    elif isinstance(raw_locations, list):
        locations = [loc for loc in raw_locations if isinstance(loc, dict)]

    martial_hud = ctx.get("martial_hud")
    if not isinstance(martial_hud, dict):
        martial_hud = {}
    actual_truth = martial_hud.get("actual_truth")
    if not isinstance(actual_truth, dict):
        actual_truth = {}
    if "equipment" not in actual_truth:
        actual_truth["equipment"] = [item["name"] for item in items if item.get("owner")]
    martial_hud["actual_truth"] = actual_truth

    ctx["mode"] = mode
    ctx["ep_num"] = ctx.get("ep_num", 1)
    ctx["encyclopedia"] = {"npcs": npcs, "items": items, "locations": locations}
    ctx["martial_hud"] = martial_hud
    ctx["blueprint"] = {}
    return ctx


class TestBlockingValidator:
    """TIER 1: BlockingValidator tests."""

    def test_minimum_length_manuscript_pass(self):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        validation_context = _minimal_blocking_context(mode="MANUSCRIPT")
        manuscript = "충분한 원고 분량입니다. " * 500

        result = validator.validate(manuscript, validation_context)

        assert len(manuscript) >= 4000
        assert result["passed"] is True
        assert result["failure_count"] == 0

    def test_minimum_length_manuscript_fail(self, validation_context):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        normalized_context = _to_blocking_context(validation_context, mode="MANUSCRIPT")
        short_text = "짧은 원고"

        result = validator.validate(short_text, normalized_context)

        assert result["passed"] is False
        assert any(failure.get("check") == "minimum_length" for failure in result.get("failures", []))

    def test_dead_npc_resurrection_detection(self):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        validation_context = _minimal_blocking_context(mode="MANUSCRIPT")
        validation_context["encyclopedia"]["npcs"] = [{"name": "인사부", "status": "dead"}]
        manuscript = "인사부가 말했다. 그는 문을 열고 공격했다. " * 500

        result = validator.validate(manuscript, validation_context)

        assert any(failure.get("check") == "dead_npc_resurrection" for failure in result.get("failures", []))

    def test_destroyed_location_visit_detection(self):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        validation_context = _minimal_blocking_context(mode="MANUSCRIPT")
        validation_context["encyclopedia"]["locations"] = [{"name": "천무수련장", "status": "destroyed"}]
        manuscript = "이청운은 천무수련장에 들어갔다. 문이 열렸다. " * 500

        result = validator.validate(manuscript, validation_context)

        assert any(failure.get("check") == "destroyed_location_visit" for failure in result.get("failures", []))

    def test_unowned_item_usage_detection(self):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        validation_context = _minimal_blocking_context(mode="MANUSCRIPT")
        validation_context["encyclopedia"]["items"] = [{"name": "천무검", "owner": "다른사람", "aliases": []}]
        validation_context["martial_hud"]["actual_truth"]["equipment"] = []
        manuscript = "이청운이 천무검을 사용했다. 검에서 빛이 났다. " * 500

        result = validator.validate(manuscript, validation_context)

        assert any(failure.get("check") == "unowned_item_usage" for failure in result.get("failures", []))

    def test_blueprint_mode_validation(self, sample_blueprint):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        normalized_context = _minimal_blocking_context(mode="BLUEPRINT")

        blueprint_text = json.dumps(sample_blueprint, ensure_ascii=False)
        if len(blueprint_text) < 600:
            blueprint_text = blueprint_text + "\n" + blueprint_text

        result = validator.validate(blueprint_text, normalized_context)

        assert len(blueprint_text) >= 500
        assert result["passed"] is True


class TestContinuityCountAwareInventory:
    def test_extract_inventory_counts_prefers_structured_snapshot(self):
        from modules.validation.continuity_validator import ContinuityValidator

        validator = ContinuityValidator()
        counts = validator._extract_inventory_counts(
            {
                "inventory_counts": {"트레이딩용 컴퓨터": 3},
                "equipment": ["트레이딩용 컴퓨터 2대"],
            }
        )

        assert counts == {"트레이딩용 컴퓨터": 3}

    def test_inventory_count_drift_warning_when_opening_count_drops(self):
        from modules.validation.continuity_validator import ContinuityValidator

        validator = ContinuityValidator()
        validation_context = _minimal_blocking_context(mode="MANUSCRIPT")
        validation_context["prev_hud"] = {
            "inventory_counts": {"트레이딩용 컴퓨터": 3},
            "location": "개인 오피스",
        }
        validation_context["history"] = [{"text": "직전 화 사무실에는 트레이딩용 컴퓨터 3대가 놓여 있었다."}]

        manuscript = "개인 오피스 안에는 트레이딩용 컴퓨터 2대만 켜져 있었다. 모니터 불빛이 흔들렸다."
        result = validator.validate(2, manuscript, validation_context, prev_hud=validation_context["prev_hud"])

        warnings = [w for w in result["warnings"] if isinstance(w, dict) and w.get("type") == "inventory_count_drift"]
        assert len(warnings) == 1
        assert warnings[0]["item"] == "트레이딩용 컴퓨터"
        assert warnings[0]["prev_count"] == 3
        assert warnings[0]["current_count"] == 2

    def test_threat_carryover_warning_when_opening_drops_pressure_cues(self):
        from modules.validation.continuity_validator import ContinuityValidator

        validator = ContinuityValidator()
        validation_context = _minimal_blocking_context(mode="MANUSCRIPT")
        validation_context["prev_hud"] = {
            "actual_truth": {
                "active_pressure_vectors": [
                    {
                        "text": "해독제를 찾지 못하면 독이 전신으로 퍼진다.",
                        "cue_terms": ["해독제", "전신", "퍼진다"],
                    }
                ]
            },
            "location": "지하실",
        }

        manuscript = "새벽 공기가 차갑게 식어 있었다. 그는 창문 틈의 빛만 바라보며 숨을 골랐다."
        result = validator.validate(2, manuscript, validation_context, prev_hud=validation_context["prev_hud"])

        warnings = [w for w in result["warnings"] if isinstance(w, dict) and w.get("type") == "threat_carryover_drift"]
        assert len(warnings) == 1
        assert warnings[0]["pressure_text"] == "해독제를 찾지 못하면 독이 전신으로 퍼진다."


class TestScoringValidator:
    """TIER 2: ScoringValidator tests."""

    def test_scoring_sanitize_window_defaults_to_target_length(self):
        from modules.core.constants import ManuscriptLimits
        from modules.validation.scoring_validator import _SANITIZE_MAX_CHARS

        assert _SANITIZE_MAX_CHARS == int(ManuscriptLimits.TARGET_LENGTH)

    def test_validate_exposes_scoring_input_meta_when_truncated(self, validation_context):
        from modules.validation.scoring_validator import ScoringValidator

        validator = ScoringValidator(client=None, model="gemini-2.5-flash")
        long_text = "긴원고" * 2000

        result = validator.validate(long_text, validation_context)

        assert result["scoring_input_meta"]["limit"] == 5000
        assert result["scoring_input_meta"]["original_length"] == len(long_text)
        assert result["scoring_input_meta"]["final_length"] == 5000
        assert result["scoring_input_meta"]["truncated"] is True

    def test_prose_rhythm_calculation(self, sample_manuscript):
        from modules.validation.scoring_validator import ScoringValidator

        validator = ScoringValidator(client=MagicMock(), model="gemini-2.5-flash")

        if hasattr(validator, "_evaluate_prose_rhythm"):
            score = validator._evaluate_prose_rhythm(sample_manuscript)
            assert 0 <= score["score"] <= 5

    def test_vocabulary_diversity_calculation(self, sample_manuscript):
        from modules.validation.scoring_validator import ScoringValidator

        validator = ScoringValidator(client=MagicMock(), model="gemini-2.5-flash")

        if hasattr(validator, "_evaluate_vocabulary_diversity"):
            score = validator._evaluate_vocabulary_diversity(sample_manuscript)
            assert 0 <= score["score"] <= 5

    def test_sensory_balance_check(self):
        visual_heavy = "그는 보이는 것만 보며 하늘을 봤다."
        balanced = "검 끝의 금속 소리와 차가운 바람, 매캐한 냄새가 섞였다."

        visual_keywords = ["보", "빛", "보이", "색"]

        visual_count = sum(1 for kw in visual_keywords if kw in visual_heavy)
        balanced_count = sum(1 for kw in visual_keywords if kw in balanced)

        assert visual_count > balanced_count

    def test_show_dont_tell_detection(self):
        telling = "그는 화가 났다. 그는 슬펐다. 그는 기뻤다."
        showing = "그의 주먹이 떨렸다. 숨이 거칠어졌다."

        direct_emotions = ["화가", "슬펐", "기뻤", "무서웠", "행복"]

        telling_count = sum(1 for e in direct_emotions if e in telling)
        showing_count = sum(1 for e in direct_emotions if e in showing)

        assert telling_count > showing_count

    def test_scoring_threshold_pass(self, sample_manuscript, validation_context):
        from modules.validation.scoring_validator import ScoringValidator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "character_consistency": {"score": 15, "max": 15, "reason": "ok"},
                "emotion_arc": {"score": 15, "max": 15, "reason": "ok"},
                "dialogue_quality": {"score": 15, "max": 15, "reason": "ok"},
                "commercial_appeal": {"score": 15, "max": 15, "reason": "ok"},
                "pattern_diversity": {"score": 10, "max": 10, "reason": "ok"},
                "reader_satisfaction": {"score": 10, "max": 10, "reason": "ok"},
            }
        )
        mock_client.models.generate_content.return_value = mock_response

        validator = ScoringValidator(client=mock_client, model="gemini-2.5-flash", pass_threshold=70)
        result = validator.validate(sample_manuscript, validation_context)

        assert result["passed"] is True
        assert result["total_score"] >= 70

    def test_scoring_threshold_fail(self, validation_context):
        from modules.validation.scoring_validator import ScoringValidator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "character_consistency": {"score": 1, "max": 15, "reason": "low"},
                "emotion_arc": {"score": 1, "max": 15, "reason": "low"},
                "dialogue_quality": {"score": 1, "max": 15, "reason": "low"},
                "commercial_appeal": {"score": 1, "max": 15, "reason": "low"},
                "pattern_diversity": {"score": 1, "max": 10, "reason": "low"},
                "reader_satisfaction": {"score": 1, "max": 10, "reason": "low"},
            }
        )
        mock_client.models.generate_content.return_value = mock_response

        validator = ScoringValidator(client=mock_client, model="gemini-2.5-flash", pass_threshold=70)
        result = validator.validate("짧은 텍스트", validation_context)

        assert result["passed"] is False
        assert result["total_score"] < 70

    def test_generate_dynamic_context_skips_live_hud_for_blueprint_mode(self):
        from modules.validation.scoring_validator import ScoringValidator

        validator = ScoringValidator(client=None, genre="investment")
        validator.guard = MagicMock()
        validator.guard.get_impossible_actions.return_value = [{"reason": "유동성 부족"}]
        validator.guard.get_justification_patterns.return_value = [r"미래.*기억"]

        context = {
            "mode": "BLUEPRINT",
            "martial_hud": {
                "actual_truth": {
                    "rank": "SW인베스트먼트 패밀리오피스 수장 / 글로벌 투자자",
                    "status": "late-stage",
                }
            },
        }

        dynamic_context = validator._generate_dynamic_context(context)

        assert "[V46] 주인공 현재 상태" not in dynamic_context
        assert "SW인베스트먼트 패밀리오피스 수장 / 글로벌 투자자" not in dynamic_context
        validator.guard.get_impossible_actions.assert_not_called()

    def test_generate_dynamic_context_uses_explicit_blueprint_scoring_hud_when_provided(self):
        from modules.validation.scoring_validator import ScoringValidator

        validator = ScoringValidator(client=None, genre="investment")
        validator.guard = MagicMock()
        validator.guard.get_impossible_actions.return_value = [{"reason": "유동성 부족"}]
        validator.guard.get_justification_patterns.return_value = [r"미래.*기억"]

        context = {
            "mode": "BLUEPRINT",
            "martial_hud": {
                "actual_truth": {
                    "rank": "late-stage should not leak",
                    "status": "late-stage",
                }
            },
            "blueprint_scoring_hud": {
                "actual_truth": {
                    "status": "투자 준비 단계",
                    "equipment": ["경제사 정보"],
                }
            },
        }

        dynamic_context = validator._generate_dynamic_context(context)

        assert "[V46] 주인공 현재 상태" in dynamic_context
        assert "투자 준비 단계" in dynamic_context
        assert "late-stage should not leak" not in dynamic_context
        validator.guard.get_impossible_actions.assert_called_once()


class TestAdvisoryValidator:
    """TIER 3: AdvisoryValidator tests."""

    def test_cliche_detection(self):
        cliche_keywords = ["과거로 돌아", "복수", "천재", "모든 것을"]
        regression_text = "그는 과거로 돌아와 복수를 꿈꿨다."

        has_cliche = any(kw in regression_text for kw in cliche_keywords)
        assert has_cliche

    def test_advisory_always_passes(self, sample_manuscript, validation_context):
        from modules.validation.advisory_validator import AdvisoryValidator

        validator = AdvisoryValidator(client=MagicMock(), model="gemini-2.5-flash")

        if hasattr(validator, "validate"):
            result = validator.validate(sample_manuscript, validation_context)

            assert result.get("passed") is True
            assert result.get("tier") == "ADVISORY"

    def test_foreshadowing_opportunity_detection(self):
        text_with_opportunity = "그는 이상한 문양을 발견했다. 이유를 알 수 없었다."
        foreshadowing_hints = ["이상", "이유", "불길", "의문", "예감"]

        has_hint = any(kw in text_with_opportunity for kw in foreshadowing_hints)
        assert has_hint

    def test_expression_improvement_prompt_preserves_tail_context(self, monkeypatch):
        from modules.validation.advisory_validator import AdvisoryValidator

        validator = AdvisoryValidator(client=MagicMock(), model="gemini-2.5-flash")
        captured = {}

        class _FakeResponse:
            text = "[]"

        def _fake_generate_content_via_router(**kwargs):
            captured["prompt"] = kwargs["contents"]
            return _FakeResponse()

        monkeypatch.setattr(
            "modules.validation.advisory_validator.generate_content_via_router",
            _fake_generate_content_via_router,
        )

        suggestions = validator._suggest_expression_improvements("HEAD-ADV\n" + ("A" * 3000) + "\nTAIL-ADVISORY")

        assert suggestions == []
        assert "TAIL-ADVISORY" in captured["prompt"]
        assert "...(중간 생략)..." in captured["prompt"]


class TestValidationOrchestrator:
    """ValidationOrchestrator integration tests."""

    def test_orchestrator_initialization(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_model": "gemini-2.5-pro",
            "advisory_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False,
            "consistency_votes": 3,
        }

        orchestrator = ValidationOrchestrator(config, MagicMock(), genre="wuxia")

        assert orchestrator.blocking is not None
        assert orchestrator.scoring is not None
        assert orchestrator.advisory is not None

    def test_tier_order_execution(self, sample_manuscript, validation_context):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_model": "gemini-2.5-pro",
            "advisory_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False,
        }

        orchestrator = ValidationOrchestrator(config, MagicMock(), genre="wuxia")
        validation_context = _minimal_blocking_context(mode="MANUSCRIPT")

        short_text = "짧은 텍스트"
        result = orchestrator.validate(1, short_text, validation_context)

        # [TF-36] 대원칙 1: BLOCKING 실패 → advisory + 감점 → REJECT (점수 기반)
        assert result["final_decision"] == "REJECT"

    def test_final_decision_mapping(self):
        score_mappings = [
            (90, "PASS"),
            (85, "PASS"),
            (75, "CONDITIONAL_PASS"),
            (70, "CONDITIONAL_PASS"),
            (65, "REJECT"),
            (50, "REJECT"),
        ]

        for score, expected_status in score_mappings:
            if score >= 85:
                actual = "PASS"
            elif score >= 70:
                actual = "CONDITIONAL_PASS"
            else:
                actual = "REJECT"

            assert actual == expected_status

    def test_self_consistency_mode(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_model": "gemini-2.5-pro",
            "advisory_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": True,
            "consistency_votes": 3,
        }

        orchestrator = ValidationOrchestrator(config, MagicMock(), genre="wuxia")

        assert orchestrator.use_self_consistency is True
        assert orchestrator.consistency_votes == 3

    def test_genre_specific_validation(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {"scoring_model": "gemini-2.5-pro", "advisory_model": "gemini-2.5-flash", "scoring_threshold": 70}

        for genre in ["wuxia", "hunter", "investment"]:
            orchestrator = ValidationOrchestrator(config, MagicMock(), genre=genre)
            assert orchestrator.genre == genre

    def test_consistency_unjustifiable_flows_to_advisory_instead_of_early_reject(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        orchestrator = ValidationOrchestrator(
            {"scoring_model": "gemini-2.5-pro", "advisory_model": "gemini-2.5-flash", "scoring_threshold": 70},
            MagicMock(),
            genre="wuxia",
        )
        orchestrator.continuity.validate = MagicMock(
            return_value={"passed": True, "warning_count": 0, "violations": []}
        )
        orchestrator.blocking.validate = MagicMock(return_value={"passed": True, "failure_count": 0, "failures": []})
        orchestrator.consistency.validate = MagicMock(
            return_value={
                "unjustifiable_violations": [{"type": "timeline", "severity": "CRITICAL"}],
                "justifiable_violations": [],
                "score_penalty": -5,
                "feedback": "정당화 불가 타임라인 모순",
            }
        )
        orchestrator.pre_llm.validate = MagicMock(return_value={"passed": True, "warnings": [], "score_deduction": 0})
        orchestrator.scoring.validate_v59 = MagicMock(return_value={"total_score": 90, "message": "ok", "passed": True})
        orchestrator.advisory.validate = MagicMock(return_value={"suggestions": []})
        orchestrator.catharsis_timer.check_catharsis_timing = MagicMock(return_value={"status": "ok"})
        orchestrator.action_evaluator.evaluate = MagicMock(return_value={"action_scene_count": 0})

        result = orchestrator.validate(4, "충분한 원고 분량입니다. " * 500, _minimal_blocking_context())

        assert result["final_decision"] == "PASS"
        assert result["total_score"] == 85
        assert result["_consistency_advisory"]["severity"] == "CRITICAL"

    def test_retrospective_critical_becomes_advisory_penalty(self, monkeypatch):
        from modules.validation import validation_orchestrator as vo_mod
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        monkeypatch.setattr(vo_mod, "RETROSPECTIVE_AVAILABLE", True)
        orchestrator = ValidationOrchestrator(
            {
                "scoring_model": "gemini-2.5-pro",
                "advisory_model": "gemini-2.5-flash",
                "scoring_threshold": 70,
                "use_retrospective": True,
            },
            MagicMock(),
            genre="wuxia",
        )
        orchestrator.continuity.validate = MagicMock(
            return_value={"passed": True, "warning_count": 0, "violations": []}
        )
        orchestrator.blocking.validate = MagicMock(return_value={"passed": True, "failure_count": 0, "failures": []})
        orchestrator.consistency.validate = MagicMock(
            return_value={
                "unjustifiable_violations": [],
                "justifiable_violations": [],
                "score_penalty": 0,
                "feedback": "",
            }
        )
        orchestrator.pre_llm.validate = MagicMock(return_value={"passed": True, "warnings": [], "score_deduction": 0})
        orchestrator.scoring.validate_v59 = MagicMock(return_value={"total_score": 95, "message": "ok", "passed": True})
        orchestrator.advisory.validate = MagicMock(return_value={"suggestions": []})
        orchestrator.catharsis_timer.check_catharsis_timing = MagicMock(return_value={"status": "ok"})
        orchestrator.action_evaluator.evaluate = MagicMock(return_value={"action_scene_count": 0})
        orchestrator.retrospective = MagicMock()
        orchestrator.retrospective.validate_long_term_consistency.return_value = {
            "passed": False,
            "severity_level": "CRITICAL",
            "total_violations": 1,
            "message": "장기 드리프트",
            "violations": [{"type": "drift", "description": "장기 상태 불일치"}],
        }

        result = orchestrator.validate(
            4,
            "충분한 원고 분량입니다. " * 500,
            {**_minimal_blocking_context(), "_context": MagicMock()},
        )

        assert result["final_decision"] == "CONDITIONAL_PASS"
        assert result["total_score"] == 80
        assert result["_retrospective_advisory"]["severity"] == "CRITICAL"


class TestValidationEdgeCases:
    """Validation edge case tests."""

    def test_empty_manuscript(self, validation_context):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        normalized_context = _to_blocking_context(validation_context, mode="MANUSCRIPT")

        result = validator.validate("", normalized_context)
        assert result["passed"] is False
        assert any(failure.get("check") == "minimum_length" for failure in result.get("failures", []))

    def test_unicode_special_characters(self, validation_context):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        normalized_context = _to_blocking_context(validation_context, mode="MANUSCRIPT")

        special_text = "이청운과 응룡검이 천무검을 휘둘렀다." * 500
        result = validator.validate(special_text, normalized_context)

        assert isinstance(result, dict)
        assert "passed" in result

    def test_very_long_manuscript(self, validation_context):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        normalized_context = _to_blocking_context(validation_context, mode="MANUSCRIPT")

        long_text = "무협 소설 내용입니다. " * 10000
        result = validator.validate(long_text, normalized_context)

        assert isinstance(result, dict)
        assert "passed" in result

    def test_missing_context_fields(self):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        incomplete_context = {
            "mode": "MANUSCRIPT"
            # encyclopedia, martial_hud intentionally omitted
        }

        manuscript = "테스트용 원고 " * 500

        try:
            result = validator.validate(manuscript, incomplete_context)
            assert isinstance(result, dict)
            assert "passed" in result
        except KeyError:
            pytest.fail("Should handle missing context fields gracefully")

    def test_null_values_in_context(self, validation_context):
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        validation_context["encyclopedia"] = None
        validation_context["martial_hud"] = None

        manuscript = "테스트용 원고 " * 500

        sanitized_context = _to_blocking_context(validation_context, mode="MANUSCRIPT")
        result = validator.validate(manuscript, sanitized_context)

        assert isinstance(result, dict)
        assert "passed" in result
