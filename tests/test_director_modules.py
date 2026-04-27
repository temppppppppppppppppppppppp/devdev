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
import types
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

    @staticmethod
    def _install_fake_genai(monkeypatch):
        fake_google = types.ModuleType("google")
        fake_genai = types.ModuleType("google.genai")
        fake_genai.types = types.SimpleNamespace(CreateCachedContentConfig=lambda **kwargs: kwargs)
        fake_google.genai = fake_genai
        monkeypatch.setitem(sys.modules, "google", fake_google)
        monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    @staticmethod
    def _manuscript_db(manuscripts: dict[int, dict]):
        db = MagicMock()
        db.get_manuscript.side_effect = lambda ep_num: manuscripts.get(ep_num)
        return db

    def test_initial_cache_state(self, caching_manager):
        """1. Cache starts with no active cache."""
        assert caching_manager.manuscript_cache_name is None
        assert caching_manager.manuscript_cache_enabled is True
        assert caching_manager._cached_manuscript_count == 0
        assert caching_manager._cached_manuscript_content_hash == ""
        assert caching_manager._cached_manuscript_model == ""
        assert caching_manager._cached_manuscript_provider == ""

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

    def test_invalidate_caches_clears_protagonist_config_cache(self, director):
        """6. invalidate_caches must clear protagonist_config cache for updated bible reads."""
        first = director._get_protagonist_config()
        assert first.get("world_origin") == "현대인"

        director.context.master_bible = {
            "MasterBible": {"protagonist_config": {"world_origin": "원시인", "incarnation_type": "회귀자"}}
        }

        director.invalidate_caches()

        refreshed = director._get_protagonist_config()
        assert refreshed.get("world_origin") == "원시인"
        assert refreshed.get("incarnation_type") == "회귀자"
        assert director._caching._cached_manuscript_content_hash == ""
        assert director._caching._cached_manuscript_model == ""
        assert director._caching._cached_manuscript_provider == ""

    def test_create_manuscript_cache_disabled(self, caching_manager):
        """7. create_manuscript_cache returns None when disabled."""
        caching_manager.manuscript_cache_enabled = False
        result = caching_manager.create_manuscript_cache(MagicMock(), current_ep=5)
        assert result is None

    def test_create_manuscript_cache_no_previous(self, caching_manager):
        """8. create_manuscript_cache returns None with no prior manuscripts."""
        db = MagicMock()
        db.get_manuscript = MagicMock(return_value=None)
        result = caching_manager.create_manuscript_cache(db, current_ep=1)
        assert result is None

    def test_create_manuscript_cache_skips_vertex_api_key_mode(self, caching_manager):
        db = MagicMock()
        db.get_manuscript = MagicMock(
            side_effect=[
                {"content": "A" * 2000, "title": "제1화"},
                {"content": "B" * 2000, "title": "제2화"},
            ]
        )
        caching_manager.client._geuldobi_provider_mode = "vertex_ai"
        caching_manager.client._geuldobi_vertex_auth_mode = "api_key"

        result = caching_manager.create_manuscript_cache(db, current_ep=3)

        assert result is None
        caching_manager.client.caches.create.assert_not_called()

    def test_create_manuscript_cache_reuses_when_count_content_and_model_match(
        self, caching_manager, monkeypatch
    ):
        self._install_fake_genai(monkeypatch)
        db = self._manuscript_db(
            {
                1: {"content": "A" * 2000, "title": "제1화"},
                2: {"content": "B" * 2000, "title": "제2화"},
            }
        )
        caching_manager.client.caches.create.return_value = types.SimpleNamespace(name="cache/v1")

        first = caching_manager.create_manuscript_cache(db, current_ep=3)
        second = caching_manager.create_manuscript_cache(db, current_ep=3)

        assert first == "cache/v1"
        assert second == "cache/v1"
        assert caching_manager.client.caches.create.call_count == 1
        assert caching_manager._cached_manuscript_count == 2
        assert caching_manager._cached_manuscript_content_hash
        assert caching_manager._cached_manuscript_model == "gemini-2.5-flash"
        assert caching_manager._cached_manuscript_provider

    def test_create_manuscript_cache_registers_base_agent_lineage(self, caching_manager, monkeypatch):
        from modules.domain.agents.base_agent import BaseAgent

        self._install_fake_genai(monkeypatch)
        db = self._manuscript_db(
            {
                1: {"content": "A" * 2000, "title": "제1화"},
                2: {"content": "B" * 2000, "title": "제2화"},
            }
        )
        caching_manager.client.caches.create.return_value = types.SimpleNamespace(name="cache/lineage")

        try:
            cache_name = caching_manager.create_manuscript_cache(db, current_ep=3)
            lineage = BaseAgent._context_cache_lineage_by_name(cache_name)

            assert lineage["cache_name"] == "cache/lineage"
            assert lineage["content_hash"] == caching_manager._cached_manuscript_content_hash
            assert lineage["model"] == caching_manager.primary_model
            assert lineage["provider"] == caching_manager._cached_manuscript_provider
        finally:
            BaseAgent._context_caches.clear()

    def test_create_manuscript_cache_rebuilds_when_content_changes_with_same_count(
        self, caching_manager, monkeypatch
    ):
        self._install_fake_genai(monkeypatch)
        manuscripts = {
            1: {"content": "A" * 2000, "title": "제1화"},
            2: {"content": "B" * 2000, "title": "제2화"},
        }
        db = self._manuscript_db(manuscripts)
        caching_manager.client.caches.create.side_effect = [
            types.SimpleNamespace(name="cache/v1"),
            types.SimpleNamespace(name="cache/v2"),
        ]

        first = caching_manager.create_manuscript_cache(db, current_ep=3)
        first_hash = caching_manager._cached_manuscript_content_hash
        manuscripts[2] = {"content": "C" * 2000, "title": "제2화"}
        second = caching_manager.create_manuscript_cache(db, current_ep=3)

        assert first == "cache/v1"
        assert second == "cache/v2"
        assert caching_manager.client.caches.create.call_count == 2
        assert caching_manager._cached_manuscript_content_hash != first_hash

    def test_create_manuscript_cache_rebuilds_when_model_changes_with_same_content(
        self, caching_manager, monkeypatch
    ):
        self._install_fake_genai(monkeypatch)
        db = self._manuscript_db(
            {
                1: {"content": "A" * 2000, "title": "제1화"},
                2: {"content": "B" * 2000, "title": "제2화"},
            }
        )
        caching_manager.client.caches.create.side_effect = [
            types.SimpleNamespace(name="cache/v1"),
            types.SimpleNamespace(name="cache/v2"),
        ]

        first = caching_manager.create_manuscript_cache(db, current_ep=3)
        caching_manager.primary_model = "vertex:gemini-2.5-pro"
        second = caching_manager.create_manuscript_cache(db, current_ep=3)

        assert first == "cache/v1"
        assert second == "cache/v2"
        assert caching_manager.client.caches.create.call_count == 2
        assert caching_manager._cached_manuscript_model == "gemini-2.5-pro"

    def test_create_manuscript_cache_rebuilds_when_provider_changes_with_same_content(
        self, caching_manager, monkeypatch
    ):
        self._install_fake_genai(monkeypatch)
        db = self._manuscript_db(
            {
                1: {"content": "A" * 2000, "title": "제1화"},
                2: {"content": "B" * 2000, "title": "제2화"},
            }
        )
        caching_manager.client._geuldobi_provider_mode = "google_genai"
        caching_manager.client.caches.create.side_effect = [
            types.SimpleNamespace(name="cache/v1"),
            types.SimpleNamespace(name="cache/v2"),
        ]

        first = caching_manager.create_manuscript_cache(db, current_ep=3)
        caching_manager.client._geuldobi_provider_mode = "vertex_ai"
        caching_manager.client._geuldobi_vertex_auth_mode = "adc"
        second = caching_manager.create_manuscript_cache(db, current_ep=3)

        assert first == "cache/v1"
        assert second == "cache/v2"
        assert caching_manager.client.caches.create.call_count == 2
        assert caching_manager._cached_manuscript_provider == "vertex_ai.adc"


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

    def test_extract_category_score_uses_non_overlapping_metric_groups(self, grading_system):
        breakdown = {
            "emotion_arc": {"score": 7, "max": 10},
            "cliffhanger": {"score": 7, "max": 10},
            "commercial_appeal": {"score": 7, "max": 10},
            "pattern_diversity": {"score": 7, "max": 10},
            "reader_satisfaction": {"score": 7, "max": 10},
        }

        assert grading_system._extract_category_score(breakdown, "engagement") == 70
        assert grading_system._extract_category_score(breakdown, "commercial") == 70
        assert grading_system._extract_category_score(breakdown, "satisfaction") == 70

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

    def test_compare_and_select_single_candidate_fail_closed_without_director_llm(self, director):
        """19. 단일 후보는 Director LLM 없이 자동 PASS하지 않는다."""
        candidate = {
            "integrated_scenario": "A" * 1000,
            "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
            "start_location": "서울",
            "end_location": "부산",
            "opening_transition": {"type": "direct_continuation"},
            "protagonist_state": {"mood": "냉정", "equipment": ["서류가방"]},
            "ending_hook": "다음에 계속",
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서 내용"}, ep_num=1
        )
        assert result["decision"] == "REJECT"
        assert "Director LLM" in result["reason"]
        assert result["selected_index"] == 0
        assert result["selected_blueprint"] is not None
        assert result["selection_reason"] == result["reason"]
        assert "단일 후보" in result["comparison_notes"]
        assert "opening_transition.type=direct_continuation" in result["comparison_notes"]
        assert "protagonist_state shape=mood:set, equipment:list[1]" in result["comparison_notes"]
        assert "binding_advisories=none" in result["comparison_notes"]
        assert result["selected_candidate_advisory"]["quality_risk"] is False
        assert len(result["candidate_advisories"]) == 1

    def test_compare_and_select_single_candidate_surfaces_binding_advisory_context(self, director):
        candidate = {
            "integrated_scenario": "A" * 1000,
            "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {"mood": "긴장", "injuries": "없음"},
            "_ensemble_meta": {
                "strategy": "steady",
                "python_warnings": [
                    {
                        "severity": "CRITICAL",
                        "category": "episode_progression",
                        "message": "replayed scene family from previous episode",
                    }
                ],
                "quality_risk": True,
            },
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서 내용"}, ep_num=9
        )
        assert result["decision"] == "REJECT"
        assert "binding_advisories=episode_progression" in result["comparison_notes"]
        assert result["selection_reason"] == result["reason"]
        assert result["selected_candidate_advisory"]["quality_risk"] is True
        assert result["selected_candidate_advisory"]["python_warnings"][0]["category"] == "episode_progression"

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
        """21. Sparse low-scene candidate still gets REJECT before Director LLM."""
        candidate = {
            "integrated_scenario": "A" * 1000,
            "scene_breakdown": {"scene1": "x", "scene2": "y"},
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서"}, ep_num=1
        )
        assert result["decision"] == "REJECT"
        assert "씬 밀도 부족" in result["reason"]

    def test_compare_and_select_single_candidate_dense_three_scenes_reaches_fail_closed_llm_gate(self, director):
        candidate = {
            "integrated_scenario": "A" * 1000,
            "scene_breakdown": {
                "scene_1": {"goal": "주인공이 PB센터에서 첫 매수 버튼을 누른다", "key_events": ["매수"]},
                "scene_2": {"summary": "리스크 경고와 담보 압박이 즉시 몰려온다", "key_events": ["경고", "압박"]},
                "scene_3": {"goal": "마감 직전 체결 뒤 다음 위기를 남긴다"},
            },
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서"}, ep_num=1
        )
        assert result["decision"] == "REJECT"
        assert "씬 개수 부족" not in result["reason"]
        assert "Director LLM" in result["reason"]

    def test_compare_and_select_single_candidate_dense_two_scenes_reaches_fail_closed_llm_gate(self, director):
        candidate = {
            "integrated_scenario": "A" * 1000,
            "scene_breakdown": {
                "scene_1": {"goal": "주인공이 PB센터에서 첫 매수 버튼을 누른다", "key_events": ["매수"]},
                "scene_2": {"summary": "레버리지 경고와 담보 압박이 동시에 몰려온다", "key_events": ["경고", "압박"]},
            },
        }
        result = director.compare_and_select_blueprint(
            candidates=[candidate], arc_data={"tactical_doc": "전술서"}, ep_num=1
        )
        assert result["decision"] == "REJECT"
        assert "씬 개수 부족" not in result["reason"]
        assert "Director LLM" in result["reason"]

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

    def test_build_blueprint_compare_prompt_includes_prev_ending_and_advisory_block(self, director):
        prompt = director._ensemble._build_blueprint_compare_prompt(
            candidates=[
                {
                    "integrated_scenario": "A" * 1200,
                    "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                    "start_location": "서울",
                    "end_location": "부산",
                    "time_flow": "하루",
                    "opening_transition": {"type": "direct_continuation"},
                    "protagonist_state": {"mood": "냉정", "equipment": ["서류가방", "주문표"]},
                    "ending_hook": "다음 화 떡밥",
                    "_ensemble_meta": {
                        "strategy": "steady",
                        "python_warnings": [
                            {
                                "severity": "MINOR",
                                "category": "fidelity",
                                "message": "Need stronger carry-over",
                            }
                        ],
                    },
                }
            ],
            arc_data={"tactical_doc": "전술서 본문"},
            ep_num=2,
            prev_blueprint={"end_location": "인천", "ending_hook": "이전 훅"},
        )

        assert "전술서 본문" in prompt
        assert "위치: 인천, 훅: 이전 훅" in prompt
        assert "[Python Advisory]" in prompt
        assert "Need stronger carry-over" in prompt
        assert "opening_transition.type: direct_continuation" in prompt
        assert "protagonist_state shape: mood:set, equipment:list[2]" in prompt
        assert "binding_advisories: none" in prompt
        assert "[시나리오 전문]" in prompt

    def test_build_blueprint_compare_prompt_includes_binding_advisory_badges(self, director):
        prompt = director._ensemble._build_blueprint_compare_prompt(
            candidates=[
                {
                    "integrated_scenario": "A" * 1200,
                    "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                    "opening_transition": {"type": "explicit_transition"},
                    "protagonist_state": {"mood": "긴장", "injuries": "없음", "equipment": ["서류가방"]},
                    "_ensemble_meta": {
                        "strategy": "steady",
                        "python_warnings": [
                            {
                                "severity": "MAJOR",
                                "category": "opening_transition",
                                "message": "opening_transition.type mismatch",
                            },
                            {
                                "severity": "MAJOR",
                                "category": "protagonist_state",
                                "message": "protagonist_state placeholder shell",
                            },
                            {
                                "severity": "CRITICAL",
                                "category": "episode_progression",
                                "message": "replayed scene family from previous episode",
                            },
                        ],
                    },
                }
            ],
            arc_data={"tactical_doc": "전술서 본문"},
            ep_num=9,
            prev_blueprint={"end_location": "VIP룸", "ending_hook": "이전 훅"},
        )

        assert "binding_advisories: opening_transition, protagonist_state, episode_progression" in prompt

    def test_build_blueprint_compare_result_payload_normalizes_advisories_and_revision_required(self, director):
        candidates = [
            {
                "integrated_scenario": "A" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "_ensemble_meta": {"strategy": "steady", "python_warnings": [], "quality_risk": False},
            },
            {
                "integrated_scenario": "B" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "_ensemble_meta": {
                    "strategy": "sharp",
                    "python_warnings": [{"severity": "MINOR", "message": "flag"}],
                    "quality_risk": True,
                },
            },
        ]

        payload = director._ensemble._build_blueprint_compare_result_payload(
            result={
                "selected_index": 9,
                "decision": "PASS_WITH_WARNING",
                "score": 82,
                "reason": "usable",
                "comparison_notes": "notes",
                "feedback": "surface advisory",
                "contradictions": "not-a-list",
            },
            candidates=candidates,
            ep_num=2,
        )

        assert payload["selected_index"] == 0
        assert payload["selected_blueprint"] is candidates[0]
        assert payload["contradictions"] == []
        assert payload["decision"] == "PASS_WITH_WARNING"
        assert payload["revision_required"] is True
        assert payload["quality_risk"] is False
        assert len(payload["candidate_advisories"]) == 2

    def test_build_blueprint_compare_result_payload_promotes_selected_advisory_fix_pack_to_contract(self, director):
        candidates = [
            {
                "integrated_scenario": "A" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "_ensemble_meta": {
                    "strategy": "steady",
                    "prevalidation_issue_count": 1,
                    "quality_risk": False,
                    "advisory_fix_pack": {
                        "patch_targets": ["integrated_scenario"],
                        "patch_target_records": [
                            {
                                "summary": "integrated_scenario",
                                "field_path": "integrated_scenario",
                                "target_kind": "local_sentence",
                            }
                        ],
                        "target_kind": "local_sentence",
                        "must_fix": ["tighten one awkward style sentence"],
                        "success_condition": "integrated_scenario removes the awkward style phrasing",
                        "evidence_summary": "python_style_warning",
                    },
                },
            }
        ]

        payload = director._ensemble._build_blueprint_compare_result_payload(
            result={
                "selected_index": 0,
                "decision": "PASS_WITH_FIX",
                "score": 100,
                "reason": "usable",
                "comparison_notes": "notes",
                "feedback": "tighten one awkward style sentence",
                "contradictions": [],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "local style cleanup only",
            },
            candidates=candidates,
            ep_num=8,
        )

        assert payload["fix_scope"] == "inplace"
        assert payload["authoritative_fix_scope"] == "inplace"
        assert payload["repair_scope"] == "inplace"
        assert payload["advisory_fix_pack"]["target_kind"] == "local_sentence"
        assert payload["fix_pack"]["patch_targets"] == ["integrated_scenario"]
        assert payload["repair_contract"]["authoritative_fix_scope"] == "inplace"
        assert payload["scope_authority"]["authoritative_fix_scope"] == "inplace"

    def test_build_blueprint_compare_prompt_marks_episode_progression_advisory_as_hard_gate(self, director):
        prompt = director._ensemble._build_blueprint_compare_prompt(
            candidates=[
                {
                    "integrated_scenario": "A" * 1200,
                    "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                    "_ensemble_meta": {
                        "strategy": "steady",
                        "python_warnings": [
                            {
                                "severity": "CRITICAL",
                                "category": "episode_progression",
                                "message": "replayed scene family from previous episode",
                            }
                        ],
                        "quality_risk": True,
                    },
                },
                {
                    "integrated_scenario": "B" * 1200,
                    "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                    "_ensemble_meta": {"strategy": "forward", "python_warnings": [], "quality_risk": False},
                },
            ],
            arc_data={"tactical_doc": "arc tactical"},
            ep_num=9,
            prev_blueprint={"end_location": "VIP룸", "ending_hook": "문이 열린다"},
        )

        assert "[CRITICAL/episode_progression]" in prompt
        assert "hard_gate" in prompt
        assert "replays prior-episode scene families" in prompt
        assert "전진 후보가 있으면 그 후보를 우선 선택" in prompt

    def test_compare_and_select_multi_candidate_pass_with_fix_preserves_advisory(self, director):
        candidates = [
            {
                "integrated_scenario": "A" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "_ensemble_meta": {
                    "strategy": "steady",
                    "python_warnings": [],
                    "quality_risk": False,
                },
            },
            {
                "integrated_scenario": "B" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "_ensemble_meta": {
                    "strategy": "sharp",
                    "python_warnings": [
                        {
                            "severity": "MINOR",
                            "category": "fidelity",
                            "message": "Arc NPC mention is thin",
                            "focus": "keep Yeonhwa visible in the scenario",
                        }
                    ],
                    "quality_risk": True,
                    "prevalidation_issue_count": 1,
                },
            },
        ]
        director._ensemble._d.ask = MagicMock(return_value="{}")
        director._ensemble._d._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 1,
                "decision": "PASS_WITH_FIX",
                "score": 84,
                "reason": "best candidate with local fixes",
                "comparison_notes": "candidate 2 wins on arc coverage",
                "feedback": "tighten scene 3 and restate Yeonhwa's leverage",
                "fix_scope": "inplace",
                "fix_scope_reasoning": "local continuity cleanup is sufficient",
                "contradictions": [],
            }
        )

        result = director.compare_and_select_blueprint(candidates=candidates, arc_data={"tactical_doc": "x"}, ep_num=2)

        assert result["decision"] == "PASS_WITH_FIX"
        assert result["feedback"] == "tighten scene 3 and restate Yeonhwa's leverage"
        assert result["selected_candidate_advisory"]["quality_risk"] is True
        assert result["candidate_advisories"][1]["python_warnings"][0]["message"] == "Arc NPC mention is thin"

    def test_compare_and_select_pass_with_warning_sets_revision_required_only(self, director):
        candidates = [
            {
                "integrated_scenario": "A" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "_ensemble_meta": {
                    "strategy": "steady",
                    "python_warnings": [],
                    "quality_risk": False,
                },
            },
            {
                "integrated_scenario": "B" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "_ensemble_meta": {
                    "strategy": "sharp",
                    "python_warnings": [],
                    "quality_risk": False,
                },
            },
        ]
        director._ensemble._d.ask = MagicMock(return_value="{}")
        director._ensemble._d._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 1,
                "decision": "PASS_WITH_WARNING",
                "score": 81,
                "reason": "usable with advisory",
                "comparison_notes": "candidate 2 wins but still needs operator attention",
                "feedback": "surface the weak continuity edge as an advisory",
                "contradictions": [],
            }
        )

        result = director.compare_and_select_blueprint(candidates=candidates, arc_data={"tactical_doc": "x"}, ep_num=2)

        assert result["decision"] == "PASS_WITH_WARNING"
        assert result["quality_risk"] is False
        assert result["revision_required"] is True
        assert result["selected_candidate_advisory"]["quality_risk"] is False

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

    def test_quick_judge_single_preserves_tail_context(self, director):
        captured = {}

        def _ask(prompt, **_kwargs):
            captured["prompt"] = prompt
            return '{"verdict":"PASS","score":88,"reason":"ok","critical_issues":[]}'

        director._ensemble._d.ask = MagicMock(side_effect=_ask)
        director._ensemble._d._extract_json_robust = MagicMock(
            return_value={"verdict": "PASS", "score": 88, "reason": "ok", "critical_issues": []}
        )

        manuscript = "HEAD-MANUSCRIPT\n" + ("M" * 7000) + "\nTAIL-MANUSCRIPT"
        blueprint = {"payload": "B" * 6000, "tail": "TAIL-BLUEPRINT"}

        result = director._ensemble.quick_judge_single(
            ep_num=1,
            manuscript=manuscript,
            blueprint=blueprint,
            previous_ending="",
        )

        assert result["verdict"] == "PASS"
        assert "TAIL-MANUSCRIPT" in captured["prompt"]
        assert "TAIL-BLUEPRINT" in captured["prompt"]
        assert "...(중간 생략)..." in captured["prompt"]


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


def test_check_manuscript_history_with_cache_preserves_tail_context(director):
    from modules.domain.agents.base_agent import BaseAgent

    director._caching.manuscript_cache_name = "cache-token"
    BaseAgent._register_context_cache_lineage(
        cache_type="director_manuscript_history",
        project_name="test_project_director_manuscript_ep_5",
        cache_name="cache-token",
        content_hash="hash-director-history",
        client=director.client,
        primary_model=director.primary_model,
    )
    director._extract_json_robust = MagicMock(return_value={"decision": "PASS", "conflicts": [], "summary": "ok"})

    captured = {}

    def _fake_cached_context(cache_name, prompt, **kwargs):
        captured["cache_name"] = cache_name
        captured["prompt"] = prompt
        captured["kwargs"] = kwargs
        return '{"decision":"PASS","conflicts":[],"summary":"ok"}'

    director._ask_with_cached_context = MagicMock(side_effect=_fake_cached_context)

    try:
        result = director.check_manuscript_history_with_cache(
            ep_num=5,
            current_manuscript="HEAD-CACHED-MS\n" + ("M" * 40000) + "\nTAIL-CACHED-MS",
        )
    finally:
        BaseAgent._context_caches.clear()

    assert result["decision"] == "PASS"
    assert captured["cache_name"] == "cache-token"
    assert captured["kwargs"]["thinking_level"] == "low"
    assert "HEAD-CACHED-MS" in captured["prompt"]
    assert "TAIL-CACHED-MS" in captured["prompt"]
    assert captured["prompt"].count("M") < 40000


def test_check_manuscript_history_with_cache_missing_lineage_requests_fallback(director):
    director._caching.manuscript_cache_name = "cache-token-without-lineage"
    director._ask_with_cached_context = MagicMock()

    result = director.check_manuscript_history_with_cache(ep_num=5, current_manuscript="원고")

    assert result["needs_fallback"] is True
    assert result["cache_used"] is False
    assert result["cache_bypass_reason"] == "missing_lineage"
    director._ask_with_cached_context.assert_not_called()


def test_check_manuscript_history_with_cache_source_has_no_legacy_head_cut():
    src = Path("modules/domain/agents/director_continuity.py").read_text(encoding="utf-8")
    assert "current_manuscript[:36000]" not in src
    assert "generate_content_via_router(" not in src


def test_check_manuscript_history_conflicts_summary_fallback_preserves_tail_context(director):
    director.ask = MagicMock(return_value="raw")
    director._extract_json_robust = MagicMock(return_value={"decision": "PASS", "conflicts": [], "summary": "ok"})
    captured = {}

    def _load(_role, _prompt_name, **kwargs):
        captured["history"] = kwargs["manuscript_history"]
        return "prompt"

    director._continuity._prompt_loader.load = MagicMock(side_effect=_load)

    result = director.check_manuscript_history_conflicts(
        ep_num=5,
        current_manuscript="current manuscript",
        manuscript_history=[
            {
                "ep_num": 4,
                "summary": "",
                "text": "HEAD-HISTORY\n" + ("H" * 800) + "\nTAIL-HISTORY",
            }
        ],
        use_summary=True,
    )

    assert result["decision"] == "PASS"
    assert "HEAD-HISTORY" in captured["history"]
    assert "TAIL-HISTORY" in captured["history"]
    assert captured["history"].count("H") < 800


def test_check_manuscript_history_conflicts_source_has_no_summary_fallback_head_cut():
    src = Path("modules/domain/agents/director_continuity.py").read_text(encoding="utf-8")
    assert 'h.get("text", "")[:500]' not in src


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

    def test_resolve_manuscript_audit_arc_no_prefers_arc_string_then_fallback(self, director):
        assert director._auditor._resolve_manuscript_audit_arc_no("Arc 12 tactical note", 3) == 12
        assert director._auditor._resolve_manuscript_audit_arc_no("", 3) == 3

    def test_finalize_manuscript_validation_context_routes_v0128_with_enriched_context(self, director):
        director.use_v0128 = True
        director._auditor._expand_prev_full_text = MagicMock(return_value="expanded-prev")
        director._auditor._audit_with_v0128 = MagicMock(return_value={"decision": "PASS", "score": 90})

        result = director._auditor._finalize_manuscript_validation_context(
            ep_num=5,
            manuscript="본문",
            prev_full_text="prev",
            validation_context={"seed": "value"},
            pre_llm_warnings=["critical warning"],
            pre_llm_advisories=["advisory"],
            target_len=5000,
        )

        assert result["early_result"]["decision"] == "PASS"
        _, kwargs = director._auditor._audit_with_v0128.call_args
        assert kwargs["validation_context"]["expanded_prev_full_text"] == "expanded-prev"
        assert "pre_llm_critical_warnings" in kwargs["validation_context"]
        assert "pre_llm_advisories" in kwargs["validation_context"]

    def test_audit_manuscript_history_conflict_returns_before_llm(self, director):
        director.use_v0128 = False
        director.genre_validation_enabled = False
        director.guard = None
        director.manuscript_history_check_enabled = True
        director.protagonist_config_check_enabled = False
        director.entity_consistency_enabled = False
        director._caching.manuscript_cache_name = None
        director.check_manuscript_history_conflicts = MagicMock(
            return_value={
                "decision": "CONFLICT",
                "conflicts": [{"type": "fact", "prev_fact": "A", "current_violation": "B"}],
                "summary": "conflict summary",
            }
        )
        director.ask = MagicMock()

        result = director._auditor.audit_manuscript(
            ep_num=3,
            manuscript="충돌 본문",
            arc_doc="Arc 3",
            history_summary="",
            prev_full_text="",
            arc_pos=3,
            target_len=5000,
            manuscript_history=[{"ep_num": 2, "summary": "old"}],
        )

        assert result["decision"] == "REJECT"
        assert result["error_category"] == "LOGIC_ERROR"
        director.ask.assert_not_called()

    def test_log_manuscript_audit_result_preserves_full_operator_reasoning(self, director):
        long_reason = "reason " * 40
        long_feedback = "feedback " * 35
        long_review = "open review " * 32
        director._operator_log = MagicMock()

        director._auditor._log_manuscript_audit_result(
            {
                "decision": "REJECT",
                "score": 41,
                "reason": long_reason,
                "feedback": long_feedback,
                "open_review": long_review,
            },
            "legacy",
        )

        operator_lines = [call.args[0] for call in director._operator_log.call_args_list]
        assert any(long_reason.strip() in line for line in operator_lines)
        assert any(long_feedback.strip() in line for line in operator_lines)
        assert any(long_review.strip() in line for line in operator_lines)


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
            ep_num=1,
            candidates=[],
            validation_results=[],
            blueprint={},
            previous_ending="",
            decision_core="core",
            candidate_evidence="evidence",
            reference_appendix="appendix",
        )
        director._ensemble.select_and_judge_ensemble.assert_called_once()
        _, kwargs = director._ensemble.select_and_judge_ensemble.call_args
        assert kwargs["decision_core"] == "core"
        assert kwargs["candidate_evidence"] == "evidence"
        assert kwargs["reference_appendix"] == "appendix"
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
        director.set_genre("wuxia")  # internal_energy limits are wuxia-specific
        result = director.on_approve_workflow(ep_num=1, state_updates={"internal_energy": "+999"}, current_hud={})
        assert "internal_energy" in result["rejected_updates"]

    def test_on_approve_workflow_mixed_updates_fail_closed(self, director):
        director.set_genre("wuxia")  # internal_energy limits are wuxia-specific
        result = director.on_approve_workflow(
            ep_num=1,
            state_updates={"realm": "새 경지", "internal_energy": "+999"},
            current_hud={"realm": "현 경지"},
        )
        assert result["approved"] is False
        assert "realm" in result["applied_updates"]
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

    def test_director_prompt_contract_prefers_yaml_source(self, director):
        from modules.domain.agents.director_prompts import get_director_prompt_contract

        contract = get_director_prompt_contract("ENSEMBLE_SELECTION_PROMPT")

        assert contract["available"] is True
        assert contract["used_fallback"] is False
        assert contract["effective_source"].startswith("config/prompts/director.yaml:")
        assert "Blueprint 장면화 충실도" in director.ENSEMBLE_SELECTION_PROMPT


# ═══════════════════════════════════════════════════════════════
# 6. DirectorEnsembleCaching Tests (TF-5)
# ═══════════════════════════════════════════════════════════════


_LONG_MANUSCRIPT = "가나다라마바사아자차카타파하" * 300  # ~4200자, 분량 통과


class TestDirectorEnsembleCaching:
    """TF-5: Director 캐시 경로 / fallback 경로 / variable_prompt 보존 검증."""

    @pytest.fixture
    def ensemble(self, mock_context, mock_client):
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key-123"}):
            from modules.domain.agents.director import Director
            from modules.domain.agents.director_ensemble import DirectorEnsembleSelector as DirectorEnsemble

            d = Director(context=mock_context, client=mock_client, model_tier="gemini-2.5-flash")
            return DirectorEnsemble(director=d)

    def test_cache_hit_uses_cached_context(self, ensemble):
        """cache_name 있을 때 _ask_with_cached_context 호출, ask() 미호출."""
        ensemble._d._get_or_create_context_cache = MagicMock(
            return_value={"cache_name": "cached_name_abc", "cached": True, "content_hash": "abc"}
        )
        ensemble._d._ask_with_cached_context = MagicMock(return_value='{"selected":"A","verdict":"PASS","score":80}')
        ensemble._d.ask = MagicMock()
        ensemble._d._extract_json_robust = MagicMock(
            return_value={"selected": "A", "verdict": "PASS", "score": 80, "feedback": {}}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(return_value="stable_context_text" * 4000)

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        ensemble.select_and_judge_ensemble(
            ep_num=5,
            candidates=candidates,
            validation_results=[],
            blueprint={},
            previous_ending="",
        )

        ensemble._d._ask_with_cached_context.assert_called_once()
        ensemble._d.ask.assert_not_called()

    def test_cache_miss_still_uses_cached_name(self, ensemble):
        """cache_name 있으면 cached=False(신규)여도 _ask_with_cached_context 경로 사용."""
        ensemble._d._get_or_create_context_cache = MagicMock(
            return_value={"cache_name": "new_cache_name", "cached": False, "content_hash": "xyz"}
        )
        ensemble._d._ask_with_cached_context = MagicMock(return_value='{"selected":"B","verdict":"PASS","score":75}')
        ensemble._d.ask = MagicMock()
        ensemble._d._extract_json_robust = MagicMock(
            return_value={"selected": "B", "verdict": "PASS", "score": 75, "feedback": {}}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(return_value="stable_context_text" * 4000)

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        ensemble.select_and_judge_ensemble(
            ep_num=7,
            candidates=candidates,
            validation_results=[],
            blueprint={},
            previous_ending="",
        )

        ensemble._d._ask_with_cached_context.assert_called_once()
        ensemble._d.ask.assert_not_called()

    def test_cache_exception_falls_back_to_ask(self, ensemble):
        """_get_or_create_context_cache 예외 → ask(full_fallback) 호출."""
        ensemble._d._get_or_create_context_cache = MagicMock(side_effect=RuntimeError("cache error"))
        ensemble._d._ask_with_cached_context = MagicMock()
        ensemble._d.ask = MagicMock(return_value='{"selected":"A","verdict":"PASS","score":60}')
        ensemble._d._extract_json_robust = MagicMock(
            return_value={"selected": "A", "verdict": "PASS", "score": 60, "feedback": {}}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(return_value="stable_context_text" * 4000)

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        ensemble.select_and_judge_ensemble(
            ep_num=3,
            candidates=candidates,
            validation_results=[],
            blueprint={},
            previous_ending="",
        )

        ensemble._d._ask_with_cached_context.assert_not_called()
        ensemble._d.ask.assert_called_once()

    def test_variable_prompt_preserved_in_fallback(self, ensemble):
        """stable 선제 절삭되어도 variable_prompt 말미 내용이 full_fallback에 보존됨 (핵심)."""
        stable = "S" * 800_000  # 800K 짜리 stable
        variable = "VARIABLE_CONTENT_END"

        captured_fallback = {}

        def fake_ask(prompt, **kwargs):
            captured_fallback["prompt"] = prompt
            return '{"selected":"A","verdict":"PASS","score":70}'

        ensemble._d._get_or_create_context_cache = MagicMock(
            return_value={"cache_name": None, "cached": False, "content_hash": "h"}
        )
        ensemble._d._ask_with_cached_context = MagicMock()
        ensemble._d.ask = MagicMock(side_effect=fake_ask)
        ensemble._d._extract_json_robust = MagicMock(
            return_value={"selected": "A", "verdict": "PASS", "score": 70, "feedback": {}}
        )
        ensemble._prompt_loader = MagicMock()
        # load() 첫 번째 호출 = stable, 두 번째 = variable
        ensemble._prompt_loader.load = MagicMock(side_effect=[stable, variable])

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        ensemble.select_and_judge_ensemble(
            ep_num=9,
            candidates=candidates,
            validation_results=[],
            blueprint={},
            previous_ending="",
        )

        assert "prompt" in captured_fallback
        full_fb = captured_fallback["prompt"]
        assert variable in full_fb, "variable_prompt이 full_fallback에 보존되어야 함"

    def test_full_fallback_ends_with_variable(self, ensemble):
        """full_fallback[-len(variable):] == variable (정확히 말미 보존)."""
        stable = "X" * 100
        variable = "TAIL_VARIABLE"

        captured_args = {}

        def fake_ask(prompt, **kwargs):
            captured_args["prompt"] = prompt
            return '{"selected":"A","verdict":"PASS","score":65}'

        ensemble._d._get_or_create_context_cache = MagicMock(
            return_value={"cache_name": None, "cached": False, "content_hash": "h2"}
        )
        ensemble._d._ask_with_cached_context = MagicMock()
        ensemble._d.ask = MagicMock(side_effect=fake_ask)
        ensemble._d._extract_json_robust = MagicMock(
            return_value={"selected": "A", "verdict": "PASS", "score": 65, "feedback": {}}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(side_effect=[stable, variable])

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        ensemble.select_and_judge_ensemble(
            ep_num=2,
            candidates=candidates,
            validation_results=[],
            blueprint={},
            previous_ending="",
        )

        full_fb = captured_args["prompt"]
        assert full_fb.endswith(variable), (
            f"full_fallback이 variable_prompt로 끝나야 함. actual tail: {full_fb[-len(variable) - 5 :]!r}"
        )

    def test_normalize_ensemble_candidates_pads_and_marks_qualified(self, ensemble):
        envelope = ensemble._normalize_ensemble_candidates(
            candidates=[{"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "state_updates": {}}],
            validation_results=[{"warnings": ["warn-a"]}],
        )

        assert len(envelope.candidates) == 3
        assert len(envelope.validation_results) == 3
        assert envelope.qualified_indices == [0]
        assert envelope.scm_single_candidate is True

    def test_request_ensemble_selection_response_returns_prompt_error_without_fallback(self, ensemble):
        from modules.domain.agents.director_ensemble import _EnsemblePromptRequest

        response = ensemble._request_ensemble_selection_response(
            ep_num=1,
            prompt_request=_EnsemblePromptRequest(
                combined_context="",
                stable_context="",
                variable_prompt=None,
                fallback_prompt=None,
            ),
        )

        assert response.prompt_error is True
        assert response.response == ""


# ═══════════════════════════════════════════════════════════════
# [TF-47] Arc 후보 Director 비교 선택 테스트
# ═══════════════════════════════════════════════════════════════


class TestDirectorArcComparison:
    """[TF-47] compare_and_select_arc 테스트."""

    @pytest.fixture
    def director(self, mock_context, mock_client):
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key-123"}):
            from modules.domain.agents.director import Director

            d = Director(context=mock_context, client=mock_client, model_tier="gemini-2.5-flash")
            return d

    def test_compare_and_select_arc_empty(self, director):
        """빈 후보 → REJECT 반환."""
        result = director.compare_and_select_arc(candidates=[], arc_no=1, curr_block={}, prev_arc_context="")
        assert result["decision"] == "REJECT"
        assert result["selected_index"] == -1
        assert result["selected_arc"] is None

    def test_compare_and_select_arc_single_fallback(self, director):
        """단일 후보 + LLM 파싱 실패 → fail-closed REJECT."""
        director.ask = MagicMock(return_value="invalid json response")
        director._extract_json_robust = MagicMock(return_value=None)

        arc = {"tactical_doc": "A" * 3000, "arc_no": 1, "ep_count": 5, "_strategy": "balanced"}
        result = director.compare_and_select_arc(candidates=[arc], arc_no=1, curr_block={}, prev_arc_context="")
        # 단일 후보도 compare_and_select_arc 내부 호출됨 → LLM 실패 시 폴백
        assert result["decision"] == "REJECT"
        assert result["selected_index"] == 0
        assert result["selected_arc"] is arc
        assert result["quality_gate_triggered"] is True

    def test_compare_and_select_arc_multi_pass(self, director):
        """다중 후보 + LLM PASS → 올바른 선택 반환."""
        director.ask = MagicMock(return_value='{"selected_index":1,"decision":"PASS","score":92}')
        director._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 1,
                "decision": "PASS",
                "score": 92,
                "contradictions": [],
                "reason": "balanced 전략이 더 밀도 높음",
                "comparison_notes": "conservative vs balanced 비교",
                "feedback": "",
                "fix_scope": "inplace",
            }
        )
        director._escape_braces = MagicMock(side_effect=lambda x: x)

        arcs = [
            {
                "tactical_doc": "A" * 3000,
                "arc_no": 1,
                "ep_count": 5,
                "_strategy": "conservative",
                "joint_docs": {},
                "state_constraints": {},
            },
            {
                "tactical_doc": "B" * 4000,
                "arc_no": 1,
                "ep_count": 5,
                "_strategy": "balanced",
                "joint_docs": {},
                "state_constraints": {},
            },
        ]
        result = director.compare_and_select_arc(
            candidates=arcs, arc_no=1, curr_block={"title": "test"}, prev_arc_context="이전 Arc 정보"
        )
        assert result["decision"] == "PASS"
        assert result["selected_index"] == 1
        assert result["selected_arc"] is arcs[1]
        assert result["score"] == 92

    def test_build_arc_compare_prompt_includes_ctx_and_diversity_warning(self, director):
        prompt = director._ensemble._build_arc_compare_prompt(
            candidates=[
                {
                    "tactical_doc": "A" * 1200,
                    "ep_count": 4,
                    "_strategy": "balanced",
                    "joint_docs": {"joint": "doc"},
                    "state_constraints": {"rule": "keep order"},
                    "_ensemble_meta": {"diversity": {"warning": "avoid repetitive openings"}},
                }
            ],
            arc_no=2,
            curr_block={"title": "block"},
            prev_arc_context="previous arc context",
            constraint_block="constraint text",
            advisory="advisory text",
        )

        assert "Arc 2번 후보 1개" in prompt
        assert "previous arc context" in prompt
        assert "constraint text" in prompt
        assert "advisory text" in prompt
        assert "다양성 경고: avoid repetitive openings" in prompt
        assert "[tactical_doc 전문]" in prompt

    def test_build_arc_compare_result_payload_normalizes_index_and_applies_quality_gate(self, director):
        arcs = [
            {"tactical_doc": "A" * 3000, "_strategy": "conservative", "joint_docs": {}, "state_constraints": {}},
            {"tactical_doc": "B" * 3000, "_strategy": "balanced", "joint_docs": {}, "state_constraints": {}},
        ]
        result = director._ensemble._build_arc_compare_result_payload(
            result={
                "selected_index": 9,
                "decision": "PASS",
                "score": 96,
                "contradictions": "not-a-list",
                "reason": "picked",
                "comparison_notes": "notes",
                "feedback": "",
                "fix_scope": "inplace",
            },
            candidates=arcs,
            arc_no=1,
            candidate_quality_flags=[
                {
                    "force_pass_with_fix": True,
                    "score_cap": 88,
                    "reasons": ["arc-major:mismatch"],
                    "feedback": "Major advisory requires PASS_WITH_FIX.",
                },
                {},
            ],
        )

        assert result["selected_index"] == 0
        assert result["selected_arc"] is arcs[0]
        assert result["decision"] == "PASS_WITH_FIX"
        assert result["score"] == 88
        assert result["contradictions"] == []
        assert result["quality_gate_triggered"] is True
        assert result["quality_gate_reasons"] == ["arc-major:mismatch"]

    def test_compare_and_select_arc_preserves_director_pass_with_fix_when_adaptive_adjusts(self, director):
        director.ask = MagicMock(return_value="json")
        director._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 0,
                "decision": "PASS_WITH_FIX",
                "score": 84,
                "contradictions": [],
                "reason": "경미한 수정만 필요",
                "comparison_notes": "후보 1이 가장 안정적",
                "feedback": "장면 연결만 다듬으면 됨",
                "fix_scope": "inplace",
            }
        )
        director._escape_braces = MagicMock(side_effect=lambda x: x)
        director.apply_adaptive_decision = MagicMock(
            return_value={"decision": "CONDITIONAL_PASS", "adjusted": True, "threshold_used": 85, "reason": "strict"}
        )

        arcs = [
            {
                "tactical_doc": "A" * 3000,
                "arc_no": 1,
                "ep_count": 5,
                "_strategy": "balanced",
                "joint_docs": {},
                "state_constraints": {},
            },
            {
                "tactical_doc": "B" * 3000,
                "arc_no": 1,
                "ep_count": 5,
                "_strategy": "dense",
                "joint_docs": {},
                "state_constraints": {},
            },
        ]

        result = director.compare_and_select_arc(candidates=arcs, arc_no=1, curr_block={}, prev_arc_context="")

        assert result["decision"] == "PASS_WITH_FIX"
        assert result["fix_scope"] == "inplace"

    def test_compare_and_select_arc_quality_gate_downgrades_pass(self, director):
        director.ask = MagicMock(return_value="json")
        director._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 1,
                "decision": "PASS",
                "score": 95,
                "contradictions": [],
                "reason": "picked",
                "comparison_notes": "quality gate check",
                "feedback": "",
                "fix_scope": "inplace",
            }
        )
        director._escape_braces = MagicMock(side_effect=lambda x: x)

        arcs = [
            {"tactical_doc": "A" * 3000, "_strategy": "conservative", "joint_docs": {}, "state_constraints": {}},
            {"tactical_doc": "B" * 3000, "_strategy": "balanced", "joint_docs": {}, "state_constraints": {}},
        ]
        result = director.compare_and_select_arc(
            candidates=arcs,
            arc_no=1,
            curr_block={},
            prev_arc_context="",
            candidate_quality_flags=[
                {},
                {
                    "force_pass_with_fix": True,
                    "score_cap": 89,
                    "reasons": ["investment-major:mismatch"],
                    "feedback": "Major investment advisory requires at least PASS_WITH_FIX.",
                },
            ],
        )

        assert result["decision"] == "PASS_WITH_FIX"
        assert result["score"] == 89
        assert result["quality_gate_triggered"] is True
        assert result["quality_gate_reasons"] == ["investment-major:mismatch"]
        assert "PASS_WITH_FIX" in result["feedback"]

    def test_compare_and_select_arc_multi_reject(self, director):
        """다중 후보 + LLM REJECT → feedback 포함."""
        director.ask = MagicMock(return_value="json")
        director._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 0,
                "decision": "REJECT",
                "score": 55,
                "contradictions": ["사망 NPC 등장"],
                "reason": "모순 발견",
                "comparison_notes": "둘 다 문제 있음",
                "feedback": "사망한 NPC '김철수'를 제거하세요",
                "fix_scope": "partial",
            }
        )
        director._escape_braces = MagicMock(side_effect=lambda x: x)

        arcs = [
            {"tactical_doc": "A" * 3000, "_strategy": "conservative", "joint_docs": {}, "state_constraints": {}},
            {"tactical_doc": "B" * 3000, "_strategy": "creative", "joint_docs": {}, "state_constraints": {}},
        ]
        result = director.compare_and_select_arc(candidates=arcs, arc_no=2, curr_block={}, prev_arc_context="")
        assert result["decision"] == "REJECT"
        assert result["score"] == 55
        assert len(result["contradictions"]) == 1
        assert "사망" in result["contradictions"][0]
        assert result["feedback"] != ""
        assert result["fix_scope"] == "partial"

    def test_fourphase_director_none_uses_validator(self, mock_context, mock_client):
        """director=None → 기존 Validator 경로 사용 확인 (하위 호환)."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key-123"}):
            from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator

            gen = FourPhaseArcGenerator(context=mock_context, client=mock_client)
            # generate() 시그니처에 director=None 기본값이 있는지 확인
            import inspect

            sig = inspect.signature(gen.generate)
            assert "director" in sig.parameters
            assert sig.parameters["director"].default is None

    def test_fourphase_patch_arc_with_feedback_no_director_param(self, mock_context, mock_client):
        """patch_arc_with_feedback에는 director 파라미터가 없음 (패치 모드는 단일 후보)."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key-123"}):
            from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator

            gen = FourPhaseArcGenerator(context=mock_context, client=mock_client)
            import inspect

            sig = inspect.signature(gen.patch_arc_with_feedback)
            assert "director" not in sig.parameters

    def test_compare_and_select_arc_multi_pass_with_fix(self, director):
        """다중 후보 + LLM PASS_WITH_FIX → fix_scope/feedback 포함."""
        director.ask = MagicMock(return_value="json")
        director._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 0,
                "decision": "PASS_WITH_FIX",
                "score": 85,
                "contradictions": [],
                "reason": "경미한 수치 오류",
                "comparison_notes": "conservative가 안정적",
                "feedback": "arc_end_state 내공 수치를 95로 수정하세요",
                "fix_scope": "inplace",
            }
        )
        director._escape_braces = MagicMock(side_effect=lambda x: x)

        arcs = [
            {"tactical_doc": "A" * 3000, "_strategy": "conservative", "joint_docs": {}, "state_constraints": {}},
            {"tactical_doc": "B" * 3000, "_strategy": "balanced", "joint_docs": {}, "state_constraints": {}},
        ]
        result = director.compare_and_select_arc(candidates=arcs, arc_no=1, curr_block={}, prev_arc_context="")
        assert result["decision"] == "PASS_WITH_FIX"
        assert result["score"] == 85
        assert result["fix_scope"] == "inplace"
        assert "내공" in result["feedback"]
        assert result["selected_arc"] is arcs[0]


class TestLane2DirectorEnsembleSemantics:
    @pytest.fixture
    def ensemble(self, mock_context, mock_client):
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key-123"}):
            from modules.domain.agents.director import Director
            from modules.domain.agents.director_ensemble import DirectorEnsembleSelector as DirectorEnsemble

            director = Director(context=mock_context, client=mock_client, model_tier="gemini-2.5-flash")
            return DirectorEnsemble(director=director)

    def test_prompt_packs_forward_and_gate_semantics_surface(self, ensemble):
        load_calls = []

        def _load(*args, **kwargs):
            load_calls.append((args, kwargs))
            prompt_name = args[1]
            if prompt_name == "ENSEMBLE_STABLE_CONTEXT":
                return "stable context"
            if prompt_name == "ENSEMBLE_VARIABLE_PROMPT":
                return "variable prompt"
            return "fallback prompt"

        ensemble._d._get_or_create_context_cache = MagicMock(side_effect=RuntimeError("cache error"))
        ensemble._d._ask_with_cached_context = MagicMock()
        ensemble._d.ask = MagicMock(return_value='{"selected":"A","verdict":"PASS_WITH_FIX","score":91}')
        ensemble._d._extract_json_robust = MagicMock(
            return_value={
                "selected": "A",
                "verdict": "PASS_WITH_FIX",
                "score": 91,
                "selection_reason": "picked",
                "feedback": {"issues": [], "action_items": ["tighten ending"]},
                "fix_scope": "partial",
            }
        )
        ensemble._d.apply_adaptive_decision = MagicMock(
            return_value={"decision": "PASS_WITH_FIX", "adjusted": False, "threshold_used": 65, "reason": ""}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(side_effect=_load)

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        result = ensemble.select_and_judge_ensemble(
            ep_num=4,
            candidates=candidates,
            validation_results=[{}, {}, {}],
            blueprint={},
            previous_ending="",
            decision_core="### [Decision Core]\ncore",
            candidate_evidence="### [Candidate Evidence]\nevidence",
            reference_appendix="### [Reference Appendix]\nappendix",
        )

        variable_call = next(call for call in load_calls if call[0][1] == "ENSEMBLE_VARIABLE_PROMPT")
        assert variable_call[1]["decision_core"] == "### [Decision Core]\ncore"
        assert variable_call[1]["candidate_evidence"] == "### [Candidate Evidence]\nevidence"
        assert variable_call[1]["reference_appendix"] == "### [Reference Appendix]\nappendix"
        assert result["director_verdict"] == "PASS_WITH_FIX"
        assert result["final_verdict"] == "PASS_WITH_FIX"
        assert result["gate_basis"] == "director_primary_pass_with_fix"
        assert result["repair_scope"] == "partial"

    def test_fix_pack_is_normalized_and_forwarded(self, ensemble):
        ensemble._d._get_or_create_context_cache = MagicMock(side_effect=RuntimeError("cache error"))
        ensemble._d._ask_with_cached_context = MagicMock()
        ensemble._d.ask = MagicMock(return_value='{"selected":"A","verdict":"PASS_WITH_FIX","score":93}')
        ensemble._d._extract_json_robust = MagicMock(
            return_value={
                "selected": "A",
                "verdict": "PASS_WITH_FIX",
                "score": 93,
                "selection_reason": "picked",
                "feedback": {"issues": [], "action_items": ["fix the location labels"]},
                "fix_scope": "inplace",
                "fix_pack": {
                    "patch_targets": ["opening_location_name", "ending_location_name"],
                    "must_fix": ["replace both labels with the approved venue"],
                    "do_not_regress": ["scene mood", "timeline"],
                    "success_condition": "Only the listed anchors are corrected.",
                    "target_kind": "entity_ref",
                },
            }
        )
        ensemble._d.apply_adaptive_decision = MagicMock(
            return_value={"decision": "PASS_WITH_FIX", "adjusted": False, "threshold_used": 65, "reason": ""}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(return_value="prompt")

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        result = ensemble.select_and_judge_ensemble(
            ep_num=4,
            candidates=candidates,
            validation_results=[{}, {}, {}],
            blueprint={},
            previous_ending="",
        )

        assert result["fix_pack"]["target_kind"] == "entity_ref"
        assert result["fix_pack"]["patch_targets"] == ["opening_location_name", "ending_location_name"]
        assert result["fix_pack"]["must_fix"] == ["replace both labels with the approved venue"]

    def test_build_ensemble_decision_payload_preserves_full_firewall_lists(self, ensemble):
        from modules.domain.agents.director_ensemble import _EnsembleSelectionState

        state = _EnsembleSelectionState(
            selected_letter="A",
            selected_idx=0,
            selected_candidate={"manuscript": _LONG_MANUSCRIPT, "state_updates": {}},
            original_verdict="PASS_WITH_FIX",
            score=58,
            pre_firewall_score=58,
            score_breakdown_raw={"story": 40},
            contradiction_check={},
            numeric_consistency_review=[],
            consistency_checklist={},
            v60_97_swapped=False,
            contradiction_details=[
                {
                    "severity": "MAJOR",
                    "type": f"kind-{idx}",
                    "current_violation": f"violation-{idx}",
                    "fix_suggestion": f"repair-{idx}",
                }
                for idx in range(6)
            ],
        )
        state.firewall_fixable = True
        state.firewall_reason = "fixable contradiction cluster"

        payload = ensemble._build_ensemble_decision_payload(
            ep_num=7,
            result={
                "selection_reason": "picked",
                "feedback": {"issues": ["seed-issue"], "action_items": ["seed-action"]},
                "fix_scope": "partial",
            },
            state=state,
            final_verdict="PASS_WITH_FIX",
            adaptive_result={"decision": "PASS_WITH_FIX"},
        )

        assert len(payload["feedback"]["action_items"]) == 7
        assert "repair-5" in payload["feedback"]["action_items"]
        assert any("repair-5" in item for item in payload["feedback"]["issues"])

    def test_log_director_frame_preserves_full_reasoning_and_all_contradictions(self, caplog):
        from modules.domain.agents.director_ensemble import _log_director_frame

        long_selection_reason = "selection reason " * 24
        long_thinking = "thinking trail " * 30

        with caplog.at_level(logging.DEBUG):
            _log_director_frame(
                stage="stage4",
                ep_num=8,
                decision="PASS_WITH_FIX",
                score=71,
                selected_label="A",
                director_verdict="PASS_WITH_FIX",
                gate_basis="firewall_fixable",
                selection_reason=long_selection_reason,
                verdict_reason="verdict reason",
                comparison_notes="comparison notes",
                contradictions=["contradiction-1", "contradiction-2", "contradiction-3"],
                fix_scope="partial",
                repair_scope="partial",
                open_review="review note",
                thinking=long_thinking,
            )

        messages = [record.getMessage() for record in caplog.records]
        assert any(long_selection_reason.strip() in message for message in messages)
        assert any("contradiction_3=contradiction-3" in message for message in messages)
        assert any(long_thinking.strip() in message for message in messages)

    def test_select_and_judge_ensemble_forwards_ep_type_to_adaptive_decision(self, ensemble):
        ensemble._d._get_or_create_context_cache = MagicMock(side_effect=RuntimeError("cache error"))
        ensemble._d._ask_with_cached_context = MagicMock()
        ensemble._d.ask = MagicMock(return_value='{"selected":"A","verdict":"PASS","score":88}')
        ensemble._d._extract_json_robust = MagicMock(
            return_value={
                "selected": "A",
                "verdict": "PASS",
                "score": 88,
                "selection_reason": "picked",
                "feedback": {"issues": [], "action_items": []},
                "fix_scope": "none",
            }
        )
        ensemble._d.apply_adaptive_decision = MagicMock(
            return_value={"decision": "PASS", "adjusted": False, "threshold_used": 60, "reason": ""}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(return_value="prompt")

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]

        result = ensemble.select_and_judge_ensemble(
            ep_num=4,
            candidates=candidates,
            validation_results=[{}, {}, {}],
            blueprint={},
            previous_ending="",
            ep_type="climax",
        )

        assert result["final_verdict"] == "PASS"
        ensemble._d.apply_adaptive_decision.assert_called_once()
        assert ensemble._d.apply_adaptive_decision.call_args.kwargs["ep_type"] == "climax"

    def test_fallback_prompt_preserves_stable_context_tail(self, ensemble):
        captured = {}

        def _load(*args, **kwargs):
            prompt_name = args[1]
            if prompt_name == "ENSEMBLE_STABLE_CONTEXT":
                return "HEAD-STABLE\n" + ("S" * 420) + "\nTAIL-STABLE"
            if prompt_name == "ENSEMBLE_VARIABLE_PROMPT":
                return "VARIABLE-ANCHOR\n" + ("V" * 170)
            return "fallback prompt"

        def _ask(prompt, **_kwargs):
            captured["prompt"] = prompt
            return '{"selected":"A","verdict":"PASS","score":90}'

        ensemble._d.MAX_CONTEXT_CHARS = 360
        ensemble._d._get_or_create_context_cache = MagicMock(side_effect=RuntimeError("cache error"))
        ensemble._d._ask_with_cached_context = MagicMock()
        ensemble._d.ask = MagicMock(side_effect=_ask)
        ensemble._d._extract_json_robust = MagicMock(
            return_value={
                "selected": "A",
                "verdict": "PASS",
                "score": 90,
                "selection_reason": "picked",
                "feedback": {"issues": [], "action_items": []},
                "fix_scope": "none",
            }
        )
        ensemble._d.apply_adaptive_decision = MagicMock(
            return_value={"decision": "PASS", "adjusted": False, "threshold_used": 65, "reason": ""}
        )
        ensemble._prompt_loader = MagicMock()
        ensemble._prompt_loader.load = MagicMock(side_effect=_load)

        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "B", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
            {"strategy": "C", "manuscript": _LONG_MANUSCRIPT, "warnings": "", "state_updates": {}},
        ]
        result = ensemble.select_and_judge_ensemble(
            ep_num=4,
            candidates=candidates,
            validation_results=[{}, {}, {}],
            blueprint={},
            previous_ending="",
            decision_core="### [Decision Core]\ncore",
            candidate_evidence="### [Candidate Evidence]\nevidence",
            reference_appendix="### [Reference Appendix]\nappendix",
        )

        assert result["final_verdict"] == "PASS"
        assert "TAIL-STABLE" in captured["prompt"]
        assert "VARIABLE-ANCHOR" in captured["prompt"]

    def test_resolve_ensemble_selection_state_swaps_unqualified_choice(self, ensemble):
        candidates = [
            {"strategy": "A", "manuscript": _LONG_MANUSCRIPT, "state_updates": {"lane": "a"}},
            {"strategy": "B", "manuscript": "short", "state_updates": {}},
            {"strategy": "C", "manuscript": "", "state_updates": {}},
        ]
        result = {
            "selected": "B",
            "verdict": "PASS",
            "score": 88,
            "selection_reason": "picked B",
        }

        state = ensemble._resolve_ensemble_selection_state(
            result=result,
            candidates=candidates,
            qualified_indices=[0],
        )

        assert state.selected_letter == "A"
        assert state.selected_idx == 0
        assert state.selected_candidate is candidates[0]
        assert state.v60_97_swapped is True
        assert state.original_verdict == "CONDITIONAL_PASS"
        assert state.score == 50
        assert "[V60.97 자동 교체: B→A" in result["selection_reason"]

    def test_apply_ensemble_quality_gates_rejects_critical_contradiction(self, ensemble):
        from modules.domain.agents.director_ensemble import _EnsembleSelectionState

        ensemble._d.apply_adaptive_decision = MagicMock(
            return_value={"decision": "CONDITIONAL_PASS", "adjusted": True, "threshold_used": 65, "reason": "adaptive"}
        )
        state = _EnsembleSelectionState(
            selected_letter="A",
            selected_idx=0,
            selected_candidate={"manuscript": _LONG_MANUSCRIPT, "state_updates": {}},
            original_verdict="PASS",
            score=92,
            pre_firewall_score=92,
            score_breakdown_raw={"story": 50, "python_warnings": 10},
            contradiction_check={
                "found_contradictions": [
                    {
                        "type": "timeline",
                        "severity": "CRITICAL",
                        "reason": "sequence mismatch",
                        "fix_suggestion": "repair the timeline only",
                    }
                ]
            },
            numeric_consistency_review=[],
            consistency_checklist={},
            v60_97_swapped=False,
            contradiction_details=[],
        )

        final_verdict, adaptive_result = ensemble._apply_ensemble_quality_gates(
            result={"score_breakdown": state.score_breakdown_raw.copy()},
            state=state,
            scm_single_candidate=False,
            combined_context="",
            mandatory_context="",
            arc_pos=1,
            total_eps=5,
            retry_count=0,
        )

        assert state.firewall_triggered is True
        assert state.firewall_fixable is False
        assert state.original_verdict == "REJECT"
        assert state.pre_firewall_score == 92
        assert state.score == 44
        assert state.firewall_reason.startswith("Contradiction Firewall:")
        assert final_verdict == "REJECT"
        assert adaptive_result["decision"] == "CONDITIONAL_PASS"

    def test_apply_ensemble_quality_gates_applies_nc3_penalty_and_preserves_breakdown(self, ensemble):
        from modules.domain.agents.director_ensemble import _EnsembleSelectionState

        ensemble._d.apply_adaptive_decision = MagicMock(
            return_value={"decision": "PASS", "adjusted": False, "threshold_used": 60, "reason": "stable"}
        )
        state = _EnsembleSelectionState(
            selected_letter="A",
            selected_idx=0,
            selected_candidate={"manuscript": _LONG_MANUSCRIPT, "state_updates": {}},
            original_verdict="PASS",
            score=90,
            pre_firewall_score=90,
            score_breakdown_raw={"story": 40, "python_warnings": 10},
            contradiction_check={},
            numeric_consistency_review=[],
            consistency_checklist={
                "numeric_accuracy": "ISSUE",
                "arithmetic": "ISSUE",
                "title_consistency": "ISSUE",
            },
            v60_97_swapped=False,
            contradiction_details=[],
        )
        result = {"score_breakdown": state.score_breakdown_raw.copy()}

        final_verdict, adaptive_result = ensemble._apply_ensemble_quality_gates(
            result=result,
            state=state,
            scm_single_candidate=False,
            combined_context="",
            mandatory_context="",
            arc_pos=1,
            total_eps=5,
            retry_count=0,
        )

        assert state.score_breakdown_raw["python_warnings"] == 3
        assert result["score_breakdown"]["python_warnings"] == 3
        assert state.score == 43
        assert final_verdict == "PASS"
        assert adaptive_result["decision"] == "PASS"

    def test_compare_and_select_arc_ask_exception_fallback(self, director):
        """LLM ask() 예외 → _fallback_arc_selection으로 PASS 폴백."""
        director.ask = MagicMock(side_effect=RuntimeError("API 장애"))
        director._escape_braces = MagicMock(side_effect=lambda x: x)

        arcs = [
            {"tactical_doc": "A" * 3000, "_strategy": "conservative", "joint_docs": {}, "state_constraints": {}},
            {"tactical_doc": "B" * 3000, "_strategy": "creative", "joint_docs": {}, "state_constraints": {}},
        ]
        result = director.compare_and_select_arc(candidates=arcs, arc_no=1, curr_block={}, prev_arc_context="")
        # 예외 시 Python 폴백 → PASS, 첫 번째 후보 선택
        assert result["decision"] == "REJECT"
        assert result["selected_index"] == 0
        assert result["selected_arc"] is arcs[0]
        assert result["quality_gate_triggered"] is True
        assert "Fallback" in result["comparison_notes"]

    def test_compare_and_select_blueprint_ask_exception_fallback_preserves_advisory_surface(self, director):
        candidates = [
            {
                "integrated_scenario": "A" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "opening_transition": {"type": "explicit_transition"},
                "protagonist_state": {"mood": "긴장", "injuries": "없음"},
                "_ensemble_meta": {
                    "strategy": "steady",
                    "python_warnings": [
                        {
                            "severity": "CRITICAL",
                            "category": "episode_progression",
                            "message": "replayed scene family from previous episode",
                        }
                    ],
                    "quality_risk": True,
                },
            },
            {
                "integrated_scenario": "B" * 1000,
                "scene_breakdown": {"scene1": "x", "scene2": "y", "scene3": "z", "scene4": "w"},
                "opening_transition": {"type": "direct_continuation"},
                "protagonist_state": {"mood": "냉정"},
            },
        ]
        director._ensemble._d.ask = MagicMock(side_effect=RuntimeError("API 장애"))

        result = director.compare_and_select_blueprint(candidates=candidates, arc_data={"tactical_doc": "x"}, ep_num=9)

        assert result["decision"] == "REJECT"
        assert result["selected_index"] == 0
        assert result["selected_blueprint"] == candidates[0]
        assert result["selection_reason"] == result["reason"]
        assert "폴백 선택 (비교 실패)" in result["comparison_notes"]
        assert "binding_advisories=episode_progression" in result["comparison_notes"]
        assert result["selected_candidate_advisory"]["quality_risk"] is True

    def test_compare_and_select_arc_index_clamping(self, director):
        """LLM이 selected_index 범위 초과 → 0으로 클램프."""
        director.ask = MagicMock(return_value="json")
        director._extract_json_robust = MagicMock(
            return_value={
                "selected_index": 99,
                "decision": "PASS",
                "score": 90,
                "contradictions": [],
                "reason": "OK",
                "comparison_notes": "",
                "feedback": "",
                "fix_scope": "inplace",
            }
        )
        director._escape_braces = MagicMock(side_effect=lambda x: x)

        arcs = [
            {"tactical_doc": "A" * 3000, "_strategy": "conservative", "joint_docs": {}, "state_constraints": {}},
            {"tactical_doc": "B" * 3000, "_strategy": "balanced", "joint_docs": {}, "state_constraints": {}},
        ]
        result = director.compare_and_select_arc(candidates=arcs, arc_no=1, curr_block={}, prev_arc_context="")
        assert result["selected_index"] == 0  # 99 → 0으로 클램프
        assert result["selected_arc"] is arcs[0]


# ═══════════════════════════════════════════════════════════════
# Operator Parity Tests — director_auditor residual
# ═══════════════════════════════════════════════════════════════


class TestDirectorAuditorOperatorParity:
    """Director auditor must show full violations, not capped subsets."""

    def test_protagonist_config_shows_all_critical_violations(self, director):
        """All critical violations appear in feedback, not just first 3."""
        bible = director.context.master_bible
        bible["MasterBible"]["protagonist_config"] = {
            "world_origin": "원시인",
            "incarnation_type": "기타",
        }
        director.invalidate_caches()
        director.protagonist_config_check_enabled = True

        manuscript = (
            "그는 핸드폰을 꺼내 시스템을 확인했다. "
            "인터넷으로 검색해보니 컴퓨터가 나왔고 "
            "TV에서 자동차 광고가 나오고 있었다. "
            "엘리베이터를 타고 올라가 에어컨을 켰다."
        )

        result = director.validate_protagonist_config_compliance(manuscript=manuscript, ep_num=1)

        critical_violations = [v for v in result["violations"] if v.get("severity") == "CRITICAL"]
        feedback = result.get("feedback", "")

        if len(critical_violations) > 3:
            for v in critical_violations:
                msg = v.get("message", "")
                if msg:
                    assert msg in feedback, f"Violation '{msg}' missing from feedback"

    def test_protagonist_config_shows_all_warning_violations(self, director):
        """All warning violations appear in feedback, not just first 2."""
        bible = director.context.master_bible
        bible["MasterBible"]["protagonist_config"] = {
            "world_origin": "현대인",
            "incarnation_type": "회귀자",
        }
        director.invalidate_caches()
        director.protagonist_config_check_enabled = True

        manuscript = (
            "곧 그 남자가 죽을 것이다. "
            "전생에서 알고 있었다. "
            "미래에서의 기억이 떠올랐다. "
            "얼마 후면 멸망할 것이다. "
            "회귀에서 경험한 일이었다."
        )

        result = director.validate_protagonist_config_compliance(manuscript=manuscript, ep_num=1)

        warning_violations = [v for v in result["violations"] if v.get("severity") == "WARNING"]
        feedback = result.get("feedback", "")

        if len(warning_violations) > 2:
            for v in warning_violations:
                msg = v.get("message", "")
                if msg:
                    assert msg in feedback, f"Warning '{msg}' missing from feedback"

    def test_genre_validation_error_message_not_truncated(self, director):
        """Genre validation error message must not be truncated."""
        long_error_msg = "장르 검증에서 발생한 상세한 오류 메시지 " * 10

        guard_mock = MagicMock()
        guard_mock.run_deep_validation.side_effect = ValueError(long_error_msg)
        director._auditor._d.guard = guard_mock

        result = director._auditor._run_genre_specific_validation(manuscript="원고", ep_num=1)

        assert result["summary"] == f"장르 검증 실패: {long_error_msg}"

    def test_genre_validation_type_error_degrades_instead_of_crashing(self, director):
        """Genre validation TypeError should degrade instead of aborting the audit."""
        guard_mock = MagicMock()
        guard_mock.run_deep_validation.side_effect = TypeError(
            "'in <string>' requires string as left operand, not dict"
        )
        director._auditor._d.guard = guard_mock

        result = director._auditor._run_genre_specific_validation(manuscript="원고", ep_num=1)

        assert result["degraded"] is True
        assert "requires string as left operand" in result["summary"]

    def test_warning_violations_not_capped_at_5(self, director):
        """Warning violations list must show all items, not first 5."""
        auditor = director._auditor

        genre_violations = {
            "has_critical": False,
            "warning_violations": [{"message": f"warning_{i}"} for i in range(10)],
            "violations": [],
        }

        director.genre_validation_enabled = True
        director.guard = MagicMock()

        with patch.object(auditor, "_run_genre_specific_validation", return_value=genre_violations):
            result = auditor._collect_genre_pre_llm_findings(
                manuscript="원고" * 100,
                ep_num=1,
            )

        advisory_text = "\n".join(result.get("advisories", []))
        for i in range(10):
            assert f"warning_{i}" in advisory_text
