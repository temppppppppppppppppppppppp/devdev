"""[V65] Director + Sub-modules Unit Tests

Comprehensive unit tests for the Director facade and its 5 sub-modules:
- DirectorCachingManager (director_caching.py)
- DirectorGradingSystem (director_grading.py)
- DirectorEnsembleSelector (director_ensemble.py)
- DirectorContinuityValidator (director_continuity.py)
- DirectorQualityAuditor (director_auditor.py)
"""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def mock_context():
    """Minimal ProjectContext mock."""
    context = MagicMock()
    context.author_directives = ""
    context.master_bible = {
        "MasterBible": {"protagonist_config": {"world_origin": "현대인", "incarnation_type": "기타"}}
    }
    context.project_name = "test_project"
    # DB mock
    context.db = MagicMock()
    context.db.get_manuscript = MagicMock(return_value=None)
    context.db.load_anchor = MagicMock(return_value=None)
    return context


@pytest.fixture
def mock_client():
    """Minimal Google GenAI client mock."""
    client = MagicMock()
    return client


@pytest.fixture
def director(mock_context, mock_client):
    """Create Director instance with mocked dependencies."""
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key-123"}):
        from modules.domain.agents.director import Director

        d = Director(context=mock_context, client=mock_client, model_tier="gemini-2.5-flash")
        return d


@pytest.fixture
def grading_system():
    """Standalone DirectorGradingSystem instance."""
    from modules.domain.agents.director_grading import DirectorGradingSystem

    return DirectorGradingSystem()


@pytest.fixture
def caching_manager(mock_client, mock_context):
    """Standalone DirectorCachingManager instance."""
    from modules.domain.agents.director_caching import DirectorCachingManager

    return DirectorCachingManager(client=mock_client, primary_model="gemini-2.5-flash", context=mock_context)


# ═══════════════════════════════════════════════════════════════
# 1. DirectorCaching Tests
# ═══════════════════════════════════════════════════════════════


class TestDirectorCaching:
    """Tests for DirectorCachingManager."""

    def test_initial_cache_state(self, caching_manager):
        """1. Cache starts with no active cache."""
        assert caching_manager.manuscript_cache_name is None
        assert caching_manager.manuscript_cache_enabled is True
        assert caching_manager._cached_manuscript_count == 0

    def test_build_manuscript_history_empty_db(self, caching_manager):
        """2. build_manuscript_history_for_check returns empty when no manuscripts exist."""
        db = MagicMock()
        db.get_manuscript = MagicMock(return_value=None)
        history = caching_manager.build_manuscript_history_for_check(db, ep_num=1)
        assert history == []

    def test_build_manuscript_history_with_data(self, caching_manager):
        """3. build_manuscript_history_for_check returns structured history from DB."""
        db = MagicMock()
        db.get_manuscript = MagicMock(
            side_effect=lambda ep: (
                {"content": f"Episode {ep} content", "summary": f"Summary of ep {ep}"} if ep < 3 else None
            )
        )

        history = caching_manager.build_manuscript_history_for_check(db, ep_num=3)
        assert len(history) == 2
        assert history[0]["ep_num"] == 1
        assert history[0]["text"] == "Episode 1 content"
        assert history[1]["ep_num"] == 2
        assert history[1]["summary"] == "Summary of ep 2"

    def test_get_protagonist_config_caching(self, caching_manager):
        """4. get_protagonist_config caches result on repeated calls."""
        config = caching_manager.get_protagonist_config()
        assert config.get("world_origin") == "현대인"

        # Second call should use cached value (no context access)
        caching_manager.context = None  # would crash if accessed
        config2 = caching_manager.get_protagonist_config()
        assert config2.get("world_origin") == "현대인"

    def test_get_protagonist_config_empty_bible(self, mock_client):
        """5. get_protagonist_config returns empty dict when no bible."""
        from modules.domain.agents.director_caching import DirectorCachingManager

        context = MagicMock()
        context.master_bible = {}
        cm = DirectorCachingManager(client=mock_client, primary_model="test", context=context)
        config = cm.get_protagonist_config()
        assert config == {}

    def test_create_manuscript_cache_disabled(self, caching_manager):
        """6. create_manuscript_cache returns None when disabled."""
        caching_manager.manuscript_cache_enabled = False
        result = caching_manager.create_manuscript_cache(MagicMock(), current_ep=5)
        assert result is None

    def test_create_manuscript_cache_no_previous(self, caching_manager):
        """7. create_manuscript_cache returns None with no prior manuscripts."""
        db = MagicMock()
        db.get_manuscript = MagicMock(return_value=None)
        result = caching_manager.create_manuscript_cache(db, current_ep=1)
        assert result is None


# ═══════════════════════════════════════════════════════════════
# 2. DirectorGrading Tests
# ═══════════════════════════════════════════════════════════════


class TestDirectorGrading:
    """Tests for DirectorGradingSystem."""

    def test_quality_weights_sum_to_one(self, grading_system):
        """8. QUALITY_WEIGHTS must sum to 1.0."""
        total = sum(grading_system.QUALITY_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"

    def test_quality_grades_ordering(self, grading_system):
        """9. Grade thresholds are in descending order (A > B > C > D)."""
        grades = grading_system.QUALITY_GRADES
        assert grades["A"]["min_score"] > grades["B"]["min_score"]
        assert grades["B"]["min_score"] > grades["C"]["min_score"]
        assert grades["C"]["min_score"] > grades["D"]["min_score"]
        assert grades["D"]["min_score"] == 0

    def test_grade_manuscript_high_score(self, grading_system):
        """10. grade_manuscript_v59 assigns grade A for high total_score."""
        validation_result = {
            "total_score": 90,
            "breakdown": {
                "scene_completeness": {"score": 9, "max": 10},
                "prose_rhythm": {"score": 9, "max": 10},
                "character_consistency": {"score": 9, "max": 10},
                "emotion_arc": {"score": 9, "max": 10},
                "commercial_appeal": {"score": 9, "max": 10},
            },
        }
        result = grading_system.grade_manuscript_v59(1, "dummy manuscript", validation_result)
        assert result["grade"] == "A"
        assert result["label"] == "출판 수준"
        assert result["action"] == "PUBLISH_READY"

    def test_grade_manuscript_low_score(self, grading_system):
        """11. grade_manuscript_v59 assigns grade D for very low scores."""
        validation_result = {
            "total_score": 20,
            "breakdown": {
                "scene_completeness": {"score": 2, "max": 10},
                "prose_rhythm": {"score": 2, "max": 10},
                "character_consistency": {"score": 2, "max": 10},
                "emotion_arc": {"score": 2, "max": 10},
                "commercial_appeal": {"score": 2, "max": 10},
            },
        }
        result = grading_system.grade_manuscript_v59(1, "weak manuscript", validation_result)
        assert result["grade"] == "D"
        assert result["action"] == "REWRITE"

    def test_extract_category_score_missing(self, grading_system):
        """12. _extract_category_score returns 50 for unknown categories."""
        score = grading_system._extract_category_score({}, "nonexistent")
        assert score == 50  # default fallback

    def test_generate_revision_guide_grade_d(self, grading_system):
        """13. generate_revision_guide_v59 returns CRITICAL priority for grade D."""
        guide = grading_system.generate_revision_guide_v59(
            grade="D", item_scores={}, weaknesses=[], validation_result={}
        )
        assert guide["priority"] == "CRITICAL"
        assert guide["grade"] == "D"
        assert any(t["type"] == "rewrite" for t in guide["tasks"])

    def test_generate_revision_guide_grade_a(self, grading_system):
        """14. generate_revision_guide_v59 returns LOW priority for grade A."""
        guide = grading_system.generate_revision_guide_v59(
            grade="A", item_scores={}, weaknesses=[], validation_result={}
        )
        assert guide["priority"] == "LOW"
        assert any(t["type"] == "polish" for t in guide["tasks"])

    def test_format_revision_report(self, grading_system):
        """15. format_revision_report_v59 produces readable text."""
        grade_result = {
            "grade": "B",
            "score": 75.0,
            "label": "게재 가능",
            "description": "경미한 수정 후 게재 가능",
            "ep_num": 5,
            "strengths": [{"category": "prose", "score": 82, "note": "문장력이 유려합니다"}],
            "weaknesses": [{"category": "consistency", "score": 55, "note": "설정 모순"}],
            "revision_guide": {
                "priority": "MEDIUM",
                "estimated_effort": "30분-1시간 소요 예상",
                "tasks": [{"type": "minor_revision", "description": "경미한 수정"}],
                "examples": [],
            },
        }
        report = grading_system.format_revision_report_v59(grade_result)
        assert "제5화" in report
        assert "B" in report
        assert "게재 가능" in report

    def test_weakness_descriptions(self, grading_system):
        """16. Strength/weakness descriptions cover all weight categories."""
        for category in grading_system.QUALITY_WEIGHTS:
            strength = grading_system._get_strength_description(category)
            weakness = grading_system._get_weakness_description(category)
            assert isinstance(strength, str) and len(strength) > 0
            assert isinstance(weakness, str) and len(weakness) > 0


# ═══════════════════════════════════════════════════════════════
# 3. DirectorEnsemble Tests
# ═══════════════════════════════════════════════════════════════


class TestDirectorEnsemble:
    """Tests for DirectorEnsembleSelector."""

    def test_select_and_judge_ensemble_method_exists(self, director):
        """17. select_and_judge_ensemble method is accessible on Director facade."""
        assert hasattr(director, "select_and_judge_ensemble")
        assert callable(director.select_and_judge_ensemble)

    def test_compare_and_select_blueprint_no_candidates(self, director):
        """18. compare_and_select_blueprint returns REJECT with empty candidates."""
        result = director.compare_and_select_blueprint(candidates=[], arc_data={}, ep_num=1)
        assert result["decision"] == "REJECT"
        assert result["selected_index"] == -1
        assert result["selected_blueprint"] is None

    def test_compare_and_select_single_candidate_pass(self, director):
        """19. Single candidate with sufficient content gets PASS."""
        candidate = {
            "integrated_scenario": "A" * 1000,
            "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
            "start_location": "서울",
            "end_location": "부산",
            "ending_hook": "다음에 계속",
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서 내용"}, ep_num=1
        )
        assert result["decision"] == "PASS"
        assert result["selected_index"] == 0
        assert result["selected_blueprint"] is not None

    def test_compare_and_select_single_candidate_reject_short(self, director):
        """20. Single candidate with short integrated_scenario gets REJECT."""
        candidate = {
            "integrated_scenario": "짧은 내용",
            "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서"}, ep_num=1
        )
        assert result["decision"] == "REJECT"
        assert "분량 부족" in result["reason"]
        assert result["selected_blueprint"] == candidate

    def test_compare_and_select_single_candidate_reject_few_scenes(self, director):
        """21. Single candidate with fewer than 4 scenes gets REJECT."""
        candidate = {
            "integrated_scenario": "A" * 1000,
            "scene_breakdown": {"scene1": "x", "scene2": "y"},
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서"}, ep_num=1
        )
        assert result["decision"] == "REJECT"
        assert "씬 개수 부족" in result["reason"]

    def test_compare_and_select_multi_candidate_reject_keeps_selected_blueprint(self, director):
        candidates = [
            {
                "integrated_scenario": "A" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
            },
            {
                "integrated_scenario": "B" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
            },
        ]
        director._ensemble._d.ask = MagicMock(return_value="{}")
        director._ensemble._d._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 1,
                "decision": "REJECT",
                "score": 48,
                "reason": "insufficient quality",
                "feedback": "revise blueprint",
            }
        )

        result = director.compare_and_select_blueprint(candidates=candidates, arc_data={"tactical_doc": "x"}, ep_num=2)

        assert result["decision"] == "REJECT"
        assert result["selected_index"] == 1
        assert result["selected_blueprint"] == candidates[1]

    def test_ensemble_all_short_manuscripts_reject(self, director):
        """22. select_and_judge_ensemble returns REJECT when all candidates are too short."""
        candidates = [
            {"strategy": "A", "strategy_name": "긴장감", "manuscript": "짧은", "title": "t", "state_updates": {}},
            {"strategy": "B", "strategy_name": "서정적", "manuscript": "짧은", "title": "t", "state_updates": {}},
            {"strategy": "C", "strategy_name": "역동적", "manuscript": "짧은", "title": "t", "state_updates": {}},
        ]
        result = director._ensemble.select_and_judge_ensemble(
            ep_num=1,
            candidates=candidates,
            validation_results=[{}, {}, {}],
            blueprint={"scenes": []},
            previous_ending="이전 화 끝",
        )
        assert result["verdict"] == "REJECT"
        assert result.get("length_violation") is True

    def test_quick_judge_single_short_manuscript(self, director):
        """23. quick_judge_single returns REJECT for very short manuscript."""
        result = director.quick_judge_single(
            ep_num=1, manuscript="너무 짧은 원고", blueprint={"scenes": []}, previous_ending=""
        )
        assert result["verdict"] == "REJECT"
        assert result["score"] == 20


# ═══════════════════════════════════════════════════════════════
# 4. DirectorContinuity Tests
# ═══════════════════════════════════════════════════════════════


class TestDirectorContinuity:
    """Tests for DirectorContinuityValidator."""

    def test_validate_entity_consistency_disabled(self, director):
        """24. validate_entity_consistency returns PASS when disabled."""
        director.entity_consistency_enabled = False
        result = director.validate_entity_consistency(content="some text", entity_registry={"characters": []})
        assert result["decision"] == "PASS"

    def test_validate_entity_consistency_empty_registry(self, director):
        """25. validate_entity_consistency returns PASS for empty registry."""
        result = director.validate_entity_consistency(content="some text", entity_registry={})
        assert result["decision"] == "PASS"

    def test_format_entity_registry_empty(self, director):
        """26. _format_entity_registry_for_director returns placeholder for empty."""
        result = director._format_entity_registry_for_director({})
        assert result == "(등록된 Entity 없음)"

    def test_format_entity_registry_with_characters(self, director):
        """27. _format_entity_registry_for_director formats characters correctly."""
        registry = {
            "characters": [{"name": "팽무진", "aliases": ["무진"]}, {"name": "흑도"}],
            "organizations": [{"name": "철혈문"}],
        }
        result = director._format_entity_registry_for_director(registry)
        assert "팽무진" in result
        assert "별칭: 무진" in result
        assert "흑도" in result
        assert "철혈문" in result
        assert "[캐릭터]" in result
        assert "[조직/문파]" in result

    def test_validate_blueprint_completeness_empty_blueprint(self, director):
        """28. _validate_blueprint_completeness_v60 returns valid=True for empty blueprint."""
        result = director._validate_blueprint_completeness_v60("원고 텍스트", {})
        assert result["valid"] is True
        assert result["scene_coverage"] == 100

    def test_validate_blueprint_completeness_good_coverage(self, director):
        """29. Blueprint completeness with matching keywords returns valid."""
        blueprint = {
            "scene_breakdown": {
                "scene1": "[Core] 주인공이 시장에서 무기를 구매한다",
                "scene2": "[Buffer] 주인공이 여관에서 쉰다",
                "scene3": "[Core] 주인공이 적과 전투한다",
                "scene4": "[Cliffhanger] 갑자기 새로운 적이 나타난다",
            },
            "integrated_scenario": "...",
        }
        manuscript = "주인공이 시장에서 무기를 구매하고, 여관에서 쉬다가, 적과 전투하고, 갑자기 새로운 적이 나타났다."
        result = director._validate_blueprint_completeness_v60(manuscript, blueprint)
        assert result["valid"] is True
        assert result["expected_scenes"] == 4

    def test_check_manuscript_history_conflicts_disabled(self, director):
        """30. check_manuscript_history_conflicts returns PASS when disabled."""
        director.manuscript_history_check_enabled = False
        result = director.check_manuscript_history_conflicts(
            ep_num=5, current_manuscript="새 원고", manuscript_history=[{"ep_num": 1, "text": "이전 원고"}]
        )
        assert result["decision"] == "PASS"

    def test_check_manuscript_history_conflicts_no_history(self, director):
        """31. check_manuscript_history_conflicts returns PASS with empty history."""
        result = director.check_manuscript_history_conflicts(
            ep_num=1, current_manuscript="새 원고", manuscript_history=[]
        )
        assert result["decision"] == "PASS"

    def test_check_blueprint_continuity_ep1(self, director):
        """32. check_blueprint_continuity_with_cache returns PASS for ep 1."""
        result = director.check_blueprint_continuity_with_cache(
            new_blueprint={"start_location": "서울"}, ep_num=1, db=MagicMock()
        )
        assert result["decision"] == "PASS"

    def test_check_manuscript_continuity_ep1(self, director):
        """33. check_manuscript_continuity_with_cache returns PASS for ep 1."""
        result = director.check_manuscript_continuity_with_cache(new_manuscript="원고 내용", ep_num=1, db=MagicMock())
        assert result["decision"] == "PASS"

    def test_check_manuscript_history_with_cache_no_cache(self, director):
        """34. check_manuscript_history_with_cache returns PASS skip when no cache."""
        director._caching.manuscript_cache_name = None
        result = director.check_manuscript_history_with_cache(ep_num=5, current_manuscript="원고")
        assert result["decision"] == "PASS"
        assert "캐시 미생성" in result.get("summary", "")


# ═══════════════════════════════════════════════════════════════
# 5. DirectorAuditor Tests
# ═══════════════════════════════════════════════════════════════


class TestDirectorContinuitySweep21:
    def test_check_manuscript_continuity_reuses_cached_context_name(self, director):
        """Sweep21 A-1: same episode second call should reuse stored manuscript cache_name."""
        db = MagicMock()
        db.get_recent_manuscripts.return_value = [{"ep_num": 4, "content": "prev manuscript"}]

        director.merge_contexts_for_caching = MagicMock(return_value="merged context")
        director._get_or_create_context_cache = MagicMock(return_value={"cached": True, "cache_name": "test_cache"})
        director._ask_with_cached_context = MagicMock(return_value='{"decision":"PASS","conflicts":[],"summary":"ok"}')
        director.ask = MagicMock(return_value='{"decision":"PASS","conflicts":[],"summary":"ok"}')
        director._extract_json_robust = MagicMock(return_value={"decision": "PASS", "conflicts": [], "summary": "ok"})
        director._continuity._prompt_loader.load = MagicMock(return_value="prompt")

        first = director.check_manuscript_continuity_with_cache("new manuscript", ep_num=5, db=db)
        assert first["decision"] == "PASS"

        director._ask_with_cached_context.reset_mock()
        director.ask.reset_mock()

        second = director.check_manuscript_continuity_with_cache("new manuscript", ep_num=5, db=db)
        assert second["decision"] == "PASS"
        assert director._ask_with_cached_context.call_count == 1
        director.ask.assert_not_called()
        assert db.get_recent_manuscripts.call_count == 1

    def test_validate_entity_consistency_logs_warning_on_mismatch(self, director, caplog):
        """Sweep21 B-1: mismatches should be warning level."""
        director.entity_consistency_enabled = True
        director.ask = MagicMock(return_value="raw")
        director._extract_json_robust = MagicMock(
            return_value={
                "decision": "WARNING",
                "mismatches": [
                    {"category": "character", "registered_name": "A", "found_variant": "B", "severity": "MAJOR"}
                ],
                "fix_instructions": "fix",
            }
        )

        with caplog.at_level(logging.WARNING):
            result = director.validate_entity_consistency(
                content="A가 등장하는 원고",
                entity_registry={"characters": [{"name": "A"}]},
            )

        assert result["decision"] == "WARNING"
        assert any(r.levelno == logging.WARNING and "Entity" in r.message for r in caplog.records)


class TestDirectorAuditor:
    """Tests for DirectorQualityAuditor."""

    def test_audit_manuscript_method_exists(self, director):
        """35. audit_manuscript method exists on Director facade."""
        assert hasattr(director, "audit_manuscript")
        assert callable(director.audit_manuscript)

    def test_genre_validation_no_guard(self, director):
        """36. _run_genre_specific_validation returns empty when no guard set."""
        director.guard = None
        result = director._run_genre_specific_validation("원고 내용", ep_num=1)
        assert result["has_critical"] is False
        assert result["violations"] == []

    def test_assess_character_logic_no_profiles(self, director):
        """37. [V66.1] assess_character_logic proceeds even with empty profiles (no auto-PASS)."""
        # [V66.1] F-5: 빈 프로필이어도 LLM 검증 진행 (auto-PASS 제거)
        with patch.object(
            director,
            "ask",
            return_value='{"decision":"PASS","score":90,"violations":[],"severity":"NONE","feedback":""}',
        ):
            result = director._auditor.assess_character_logic(
                ep_num=1, manuscript="원고 내용", npc_profiles={}, character_traits={}
            )
            assert result["decision"] == "PASS"

    def test_audit_with_v0128_delegation(self, director):
        """38. _audit_with_v0128 sets mode and delegates to audit_manuscript_v0128."""
        mock_result = {"final_decision": "PASS", "total_score": 80, "feedback": "good", "detailed_feedback": "all good"}
        director._auditor.v0128_orchestrator = MagicMock()
        director._auditor.v0128_orchestrator.validate = MagicMock(return_value=mock_result)

        result = director._auditor._audit_with_v0128(
            ep_num=1, manuscript="A" * 5000, validation_context={"test": True}, target_len=5000
        )
        assert result["decision"] == "PASS"

    def test_audit_manuscript_v0128_error_handling(self, director):
        """39. audit_manuscript_v0128 returns REJECT on orchestrator error."""
        director._auditor.v0128_orchestrator = MagicMock()
        director._auditor.v0128_orchestrator.validate = MagicMock(side_effect=Exception("API error"))
        result = director._auditor.audit_manuscript_v0128(
            ep_num=1, manuscript="원고", validation_context={}, genre="wuxia"
        )
        assert result["decision"] == "REJECT"
        assert "오류" in result["reason"]

    def test_audit_manuscript_legacy_expand_prev_called_once(self, director):
        """legacy 경로(use_v0128=False)에서는 _expand_prev_full_text가 1회만 호출된다."""
        director.use_v0128 = False
        director.genre_validation_enabled = False
        director.guard = None
        director.manuscript_history_check_enabled = False
        director.protagonist_config_check_enabled = False
        director.entity_consistency_enabled = False
        director._escape_braces = lambda x: x if isinstance(x, str) else ""

        director._auditor._expand_prev_full_text = MagicMock(return_value="")

        result = director._auditor.audit_manuscript(
            ep_num=5,
            manuscript="짧은 원고",
            arc_doc="",
            history_summary="",
            prev_full_text="",
            arc_pos=1,
            target_len=5000,
            validation_context=None,
        )

        assert result["decision"] == "REJECT"
        director._auditor._expand_prev_full_text.assert_called_once_with(5, "")


# ═══════════════════════════════════════════════════════════════
# 6. Director Facade Delegation Tests
# ═══════════════════════════════════════════════════════════════


class TestDirectorFacade:
    """Tests that Director facade correctly delegates to sub-modules."""

    def test_facade_has_all_submodules(self, director):
        """40. Director __init__ creates all 5 sub-module instances."""
        assert director._caching is not None
        assert director._grading is not None
        assert director._ensemble is not None
        assert director._continuity is not None
        assert director._auditor is not None

    def test_facade_grade_manuscript_delegates(self, director):
        """41. grade_manuscript_v59 delegates to _grading sub-module."""
        mock_result = {"grade": "B", "score": 75}
        director._grading.grade_manuscript_v59 = MagicMock(return_value=mock_result)
        result = director.grade_manuscript_v59(1, "ms", {"total_score": 75, "breakdown": {}})
        director._grading.grade_manuscript_v59.assert_called_once()
        assert result == mock_result

    def test_facade_ensemble_select_delegates(self, director):
        """42. select_and_judge_ensemble delegates to _ensemble sub-module."""
        mock_result = {"selected": "A", "verdict": "PASS", "score": 80}
        director._ensemble.select_and_judge_ensemble = MagicMock(return_value=mock_result)
        result = director.select_and_judge_ensemble(
            ep_num=1, candidates=[], validation_results=[], blueprint={}, previous_ending=""
        )
        director._ensemble.select_and_judge_ensemble.assert_called_once()
        assert result == mock_result

    def test_facade_history_conflicts_delegates(self, director):
        """43. check_manuscript_history_conflicts delegates to _continuity."""
        mock_result = {"decision": "PASS", "conflicts": []}
        director._continuity.check_manuscript_history_conflicts = MagicMock(return_value=mock_result)
        result = director.check_manuscript_history_conflicts(ep_num=5, current_manuscript="ms", manuscript_history=[])
        director._continuity.check_manuscript_history_conflicts.assert_called_once()
        assert result == mock_result

    def test_facade_quick_judge_delegates(self, director):
        """44. quick_judge_single delegates to _ensemble sub-module."""
        mock_result = {"verdict": "PASS", "score": 70}
        director._ensemble.quick_judge_single = MagicMock(return_value=mock_result)
        result = director.quick_judge_single(ep_num=1, manuscript="ms", blueprint={}, previous_ending="")
        director._ensemble.quick_judge_single.assert_called_once()
        assert result == mock_result

    def test_facade_create_cache_delegates(self, director):
        """45. create_manuscript_cache delegates to _caching sub-module."""
        director._caching.create_manuscript_cache = MagicMock(return_value="cache_name_123")
        result = director.create_manuscript_cache(MagicMock(), current_ep=5)
        director._caching.create_manuscript_cache.assert_called_once()
        assert result == "cache_name_123"

    def test_facade_format_revision_delegates(self, director):
        """46. format_revision_report_v59 delegates to _grading sub-module."""
        director._grading.format_revision_report_v59 = MagicMock(return_value="report text")
        result = director.format_revision_report_v59({"grade": "B"})
        director._grading.format_revision_report_v59.assert_called_once()
        assert result == "report text"


# ═══════════════════════════════════════════════════════════════
# 7. Director Core Logic Tests
# ═══════════════════════════════════════════════════════════════


class TestDirectorCoreMethods:
    """Tests for Director's own methods (not delegated)."""

    def test_set_genre(self, director):
        """47. set_genre updates genre and resets orchestrator."""
        director.v0128_orchestrator = MagicMock()
        director.set_genre("hunter")
        assert director.genre == "hunter"
        assert director.v0128_orchestrator is None  # reset

    def test_set_guard(self, director):
        """48. set_guard stores guard reference."""
        guard = MagicMock()
        director.set_guard(guard)
        assert director.guard is guard

    def test_get_adaptive_threshold_disabled(self, director):
        """49. get_adaptive_threshold returns base when disabled."""
        director.adaptive_thresholds_enabled = False
        result = director.get_adaptive_threshold()
        assert result["pass_threshold"] == director.base_pass_threshold
        assert result["strictness_level"] == "standard"

    def test_get_adaptive_threshold_intro_episode(self, director):
        """50. Intro position (arc_pos=1, total_eps=5) lowers threshold."""
        result = director.get_adaptive_threshold(arc_pos=1, total_eps=5)
        # 1/5 = 0.2 <= 0.2 → 도입부(-5점)
        assert result["pass_threshold"] < director.base_pass_threshold
        assert "도입부" in result["reason"]

    def test_get_adaptive_threshold_climax_episode(self, director):
        """51. Climax position (arc_pos=5, total_eps=5) raises threshold."""
        result = director.get_adaptive_threshold(arc_pos=5, total_eps=5)
        # 5/5 = 1.0 >= 0.8 → 절정부(+10점)
        assert result["pass_threshold"] > director.base_pass_threshold
        assert "절정부" in result["reason"]

    def test_get_adaptive_threshold_genre_investment(self, director):
        """52. Investment genre adds +3 to threshold."""
        director.genre = "investment"
        result = director.get_adaptive_threshold(arc_pos=3, total_eps=5)
        assert "투자장르" in result["reason"]

    def test_get_adaptive_threshold_retry_relaxation(self, director):
        """53. High retry_count relaxes the threshold."""
        result_no_retry = director.get_adaptive_threshold(arc_pos=3, total_eps=5, retry_count=0)
        result_with_retry = director.get_adaptive_threshold(arc_pos=3, total_eps=5, retry_count=3)
        assert result_with_retry["pass_threshold"] < result_no_retry["pass_threshold"]

    def test_get_adaptive_threshold_clamped(self, director):
        """54. Threshold is clamped to [45, 85] range."""
        # Force extreme conditions
        director.base_pass_threshold = 100
        result = director.get_adaptive_threshold(arc_pos=5, total_eps=5, ep_type="climax")
        assert result["pass_threshold"] <= 85

        director.base_pass_threshold = 10
        result = director.get_adaptive_threshold(arc_pos=1, total_eps=5, retry_count=5)
        assert result["pass_threshold"] >= 45

    def test_apply_adaptive_decision_pass_above_threshold(self, director):
        """55. apply_adaptive_decision keeps PASS when score >= threshold."""
        result = director.apply_adaptive_decision(
            score=80, original_decision="PASS", arc_pos=3, total_eps=5, retry_count=0
        )
        assert result["decision"] == "PASS"
        assert result["adjusted"] is False

    def test_apply_adaptive_decision_reject_overridden(self, director):
        """56. apply_adaptive_decision upgrades REJECT to CONDITIONAL_PASS when score >= threshold."""
        result = director.apply_adaptive_decision(
            score=80, original_decision="REJECT", arc_pos=3, total_eps=5, retry_count=0
        )
        assert result["decision"] == "CONDITIONAL_PASS"
        assert result["adjusted"] is True

    def test_apply_adaptive_decision_pass_below_threshold(self, director):
        """57. apply_adaptive_decision downgrades PASS to CONDITIONAL_PASS when score < threshold."""
        result = director.apply_adaptive_decision(
            score=30, original_decision="PASS", arc_pos=3, total_eps=5, retry_count=0
        )
        assert result["decision"] == "CONDITIONAL_PASS"
        assert result["adjusted"] is True

    def test_on_approve_workflow_empty_updates(self, director):
        """58. on_approve_workflow returns approved=True with empty updates."""
        result = director.on_approve_workflow(ep_num=1, state_updates={}, current_hud={})
        assert result["approved"] is True
        assert "Writer가 state_updates를 제출하지 않음" in result["warnings"][0]

    def test_on_approve_workflow_valid_updates(self, director):
        """59. on_approve_workflow accepts valid state changes."""
        result = director.on_approve_workflow(
            ep_num=1, state_updates={"realm": "화경", "wealth": "+500"}, current_hud={"realm": "통천경"}
        )
        assert result["approved"] is True
        assert "realm" in result["applied_updates"]
        assert "wealth" in result["applied_updates"]

    def test_on_approve_workflow_rejects_excessive_increase(self, director):
        """60. on_approve_workflow rejects internal_energy increase beyond max."""
        result = director.on_approve_workflow(ep_num=1, state_updates={"internal_energy": "+999"}, current_hud={})
        assert "internal_energy" in result["rejected_updates"]

    def test_audit_manuscript_too_short(self, director):
        """61. audit_manuscript hard-rejects manuscripts below MIN_LENGTH."""
        result = director.audit_manuscript(
            ep_num=1,
            manuscript="A" * 100,  # way too short
            arc_doc="Arc 1 전술서",
            history_summary="",
            prev_full_text="",
            arc_pos=1,
            total_eps=5,
            target_len=5000,
        )
        assert result["decision"] == "REJECT"
        assert "분량" in result.get("reason", "") or "미달" in result.get("diagnostic_report", "")

    def test_validate_protagonist_config_modern_origin_pass(self, director):
        """62. Protagonist config check passes for 현대인 origin."""
        result = director.validate_protagonist_config_compliance(
            manuscript="헬스장에서 바벨을 들었다. 시스템을 확인했다.", ep_num=1
        )
        assert result["decision"] == "PASS"

    def test_protagonist_config_disabled(self, director):
        """63. Protagonist config check returns PASS when disabled."""
        director.protagonist_config_check_enabled = False
        result = director.validate_protagonist_config_compliance(manuscript="anything", ep_num=1)
        assert result["decision"] == "PASS"

    def test_quality_grades_constant_accessible(self, director):
        """64. Director exposes QUALITY_GRADES and QUALITY_WEIGHTS from GradingSystem."""
        assert "A" in director.QUALITY_GRADES
        assert "structure" in director.QUALITY_WEIGHTS
        assert director.QUALITY_GRADES == director._grading.QUALITY_GRADES

    def test_ensemble_prompt_constant_accessible(self, director):
        """65. Director exposes ENSEMBLE_SELECTION_PROMPT from EnsembleSelector."""
        assert director.ENSEMBLE_SELECTION_PROMPT is not None
        assert len(director.ENSEMBLE_SELECTION_PROMPT) > 100
