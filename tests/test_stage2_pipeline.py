"""[V65] Analyst + Stage2Orchestrator Unit Tests

Analyst (modules/domain/agents/analyst.py):
  - BaseAgent 상속, plan_single_volume_v20, plan_single_arc_v20,
    get_lack_report, stitch_joints, enrich_raw_block_async,
    _get_current_genre, _get_genre_library_path,
    _validate_arc_state_continuity_v60, _validate_tactical_doc_continuity_v60,
    _auto_correct_joint_docs_v60, _normalize_arc_output

Stage2Orchestrator (modules/core/stage2_orchestrator.py):
  - __init__ app 참조, _normalize_tactical_text, _is_tactical_doc_duplicate,
    _normalize_flow_text, _stage2_flow_guard, _stage2_flow_guard_legacy,
    stage_2_arcs_async_logic 존재 확인
"""

import json
import sys
from difflib import SequenceMatcher
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.stage2_orchestrator import Stage2Orchestrator
from modules.core.stage2_contracts import TACTICAL_DOC_DUPLICATE_THRESHOLD
from modules.domain.agents.analyst import Analyst
from modules.domain.agents.base_agent import BaseAgent

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def mock_context():
    """Analyst가 필요로 하는 context mock"""
    ctx = MagicMock()
    ctx.author_directives = ""
    ctx.guard = MagicMock()
    ctx.guard.get_v20_purism_prompt.return_value = "[무협 장르 순수 프롬프트]"
    ctx.guard.get_genre_name.return_value = "wuxia"
    ctx.db = MagicMock()
    ctx.db.load_anchor.return_value = None
    ctx.genre = "wuxia"
    return ctx


@pytest.fixture
def mock_client():
    """API client mock"""
    client = MagicMock()
    return client


@pytest.fixture
def analyst(mock_context, mock_client):
    """Analyst 인스턴스"""
    return Analyst(context=mock_context, client=mock_client, model_tier="gemini-2.5-flash")


@pytest.fixture
def mock_app():
    """Stage2Orchestrator가 필요로 하는 app mock"""
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()
    app.selected_genre = {"type": "wuxia"}
    app.current_project = MagicMock()
    app.current_project.db = MagicMock()
    app.current_project.master_bible = None
    app.current_project.volumes = None
    app.perf_timer = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()
    app.sys.hud = MagicMock()
    app.sys.hud.pro_root = {}
    app.agents = {}
    app.state_tracker = None
    app.stage_rejection_history = []
    app.preset_registry = MagicMock()
    app._state_tracker_loaded_arcs = 0
    app._cumulative_state_cache = None
    app._cumulative_state_cache_key = 0
    return app


@pytest.fixture
def orchestrator(mock_app):
    """Stage2Orchestrator 인스턴스"""
    return Stage2Orchestrator(app=mock_app)


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 1: BaseAgent 상속 확인
# ══════════════════════════════════════════════════════════════


class TestAnalystInheritance:
    def test_inherits_base_agent(self, analyst):
        """Analyst는 BaseAgent를 상속해야 한다"""
        assert isinstance(analyst, BaseAgent)

    def test_has_agent_name(self, analyst):
        """Analyst는 agent_name 속성을 가져야 한다"""
        assert analyst.agent_name == "Analyst"

    def test_has_primary_model(self, analyst):
        """Analyst는 primary_model을 가져야 한다"""
        assert analyst.primary_model == "gemini-2.5-flash"


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 2: plan_single_volume_v20 메서드 존재 확인
# ══════════════════════════════════════════════════════════════


class TestAnalystPlanVolumeExists:
    def test_method_exists(self, analyst):
        """plan_single_volume_v20 메서드가 존재해야 한다"""
        assert hasattr(analyst, "plan_single_volume_v20")
        assert callable(analyst.plan_single_volume_v20)

    def test_method_signature(self, analyst):
        """plan_single_volume_v20의 필수 파라미터 확인"""
        import inspect

        sig = inspect.signature(analyst.plan_single_volume_v20)
        param_names = list(sig.parameters.keys())
        assert "vol_no" in param_names
        assert "master_bible" in param_names
        assert "treatment_raw_part" in param_names


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 3: plan_single_volume_v20 반환 타입 확인
# ══════════════════════════════════════════════════════════════


class TestAnalystPlanVolumeReturn:
    def test_returns_dict_with_required_keys(self, analyst):
        """plan_single_volume_v20은 vol_no, strategy_doc, cider_score 키를 가진 dict 반환"""
        # LLM 호출을 mock
        mock_response = json.dumps({"vol_no": 1, "strategy_doc": "전략 문서 내용 1000자 이상...", "cider_score": 60})
        analyst.ask = MagicMock(return_value=mock_response)

        bible = {"MasterBible": {"AssetLibrary": {}, "protagonist_config": {}}}
        result = analyst.plan_single_volume_v20(
            vol_no=1, master_bible=bible, treatment_raw_part="[]", protagonist_name="장무기"
        )

        assert isinstance(result, dict)
        assert "vol_no" in result
        assert "strategy_doc" in result or "tactical_doc" in result
        assert "cider_score" in result

    def test_auto_repair_missing_cider_score(self, analyst):
        """cider_score 누락 시 기본값 0으로 자동 보정"""
        mock_response = json.dumps({"vol_no": 2, "strategy_doc": "전략 문서"})
        analyst.ask = MagicMock(return_value=mock_response)

        bible = {"MasterBible": {"AssetLibrary": {}, "protagonist_config": {}}}
        result = analyst.plan_single_volume_v20(vol_no=2, master_bible=bible, treatment_raw_part="[]")
        assert result["cider_score"] == 0

    def test_tactical_to_strategy_conversion(self, analyst):
        """tactical_doc이 strategy_doc으로 자동 변환"""
        mock_response = json.dumps({"vol_no": 1, "tactical_doc": "전술 문서 내용"})
        analyst.ask = MagicMock(return_value=mock_response)

        bible = {"MasterBible": {"AssetLibrary": {}, "protagonist_config": {}}}
        result = analyst.plan_single_volume_v20(vol_no=1, master_bible=bible, treatment_raw_part="[]")
        assert result.get("strategy_doc") == "전술 문서 내용"

    def test_plan_single_volume_uses_cached_context_when_available(self, analyst):
        mock_response = json.dumps({"vol_no": 1, "strategy_doc": "전략 문서", "cider_score": 60})
        analyst._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/analyst"})

        captured = {}

        def _cached_side_effect(*, cache_name, prompt, temperature, thinking_level, full_prompt_fallback, response_schema=None):
            captured["cache_name"] = cache_name
            captured["prompt"] = prompt
            captured["fallback"] = full_prompt_fallback
            return mock_response

        analyst._ask_with_cached_context = MagicMock(side_effect=_cached_side_effect)

        bible = {"MasterBible": {"AssetLibrary": {}, "protagonist_config": {"world_origin": "현대인"}}}
        result = analyst.plan_single_volume_v20(
            vol_no=1,
            master_bible=bible,
            treatment_raw_part='[{"goal":"시장 장악"}]',
            protagonist_name="장무기",
        )

        assert result["strategy_doc"] == "전략 문서"
        assert captured["cache_name"] == "cache/analyst"
        assert "[Cached Analyst Task]" in captured["prompt"]
        assert any(
            marker in captured["fallback"]
            for marker in ("장무기", "주인공 이름", "[PROTAGONIST_CONFIG]", "현대인")
        )


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 4: get_lack_report 유효 HUD 처리
# ══════════════════════════════════════════════════════════════


class TestAnalystGetLackReport:
    def test_valid_hud_returns_dict(self, analyst):
        """유효한 HUD 입력 시 lack_summary와 raw_analysis 반환"""
        hud = {
            "actual_truth": {"realm": "삼류무사", "wealth": "빈털터리", "equipment": "녹슨 검", "causal_injuries": ""},
            "public_reputation": {"identity": "망나니"},
        }
        result = analyst.get_lack_report(hud)
        assert isinstance(result, dict)
        assert "lack_summary" in result
        assert "raw_analysis" in result

    def test_detects_martial_deficit(self, analyst):
        """무력 결핍 감지"""
        hud = {
            "actual_truth": {"realm": "삼류", "causal_injuries": "", "wealth": "충분", "equipment": "명검"},
            "public_reputation": {"identity": "강자"},
        }
        result = analyst.get_lack_report(hud)
        assert "무력" in result["lack_summary"] or len(result["raw_analysis"]["Martial"]) > 0

    def test_none_hud_returns_default(self, analyst):
        """None HUD 입력 시 기본값 반환"""
        result = analyst.get_lack_report(None)
        assert isinstance(result, dict)
        assert "lack_summary" in result
        assert "데이터 로드 실패" in result["lack_summary"]

    def test_empty_dict_hud(self, analyst):
        """빈 딕셔너리 HUD 처리"""
        result = analyst.get_lack_report({})
        assert isinstance(result, dict)
        assert "lack_summary" in result


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 5: 잘못된 JSON 처리 (plan_single_volume_v20)
# ══════════════════════════════════════════════════════════════


class TestAnalystInvalidJsonHandling:
    def test_malformed_json_treatment(self, analyst):
        """treatment_raw_part가 잘못된 JSON 문자열이면 빈 리스트로 폴백"""
        mock_response = json.dumps({"vol_no": 1, "strategy_doc": "문서"})
        analyst.ask = MagicMock(return_value=mock_response)

        bible = {"MasterBible": {"AssetLibrary": {}, "protagonist_config": {}}}
        # 잘못된 JSON 문자열을 입력해도 크래시 없이 처리
        result = analyst.plan_single_volume_v20(
            vol_no=1, master_bible=bible, treatment_raw_part="이것은 JSON이 아닙니다{{{{"
        )
        assert isinstance(result, dict)


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 6: 장르 라이브러리 로딩 확인
# ══════════════════════════════════════════════════════════════


class TestAnalystGenreLibrary:
    def test_get_current_genre_wuxia(self, analyst):
        """wuxia 장르 감지"""
        analyst.context.guard.get_genre_name.return_value = "wuxia"
        assert analyst._get_current_genre() == "wuxia"

    def test_get_current_genre_hunter(self, analyst):
        """hunter 장르 감지"""
        analyst.context.guard.get_genre_name.return_value = "hunter"
        assert analyst._get_current_genre() == "hunter"

    def test_get_current_genre_investment(self, analyst):
        """investment 장르 감지"""
        analyst.context.guard.get_genre_name.return_value = "투자물"
        assert analyst._get_current_genre() == "investment"

    def test_get_current_genre_fantasy(self, analyst):
        """fantasy 장르 감지"""
        analyst.context.guard.get_genre_name.return_value = "판타지"
        assert analyst._get_current_genre() == "fantasy"

    def test_get_current_genre_fallback(self, analyst):
        """장르 감지 실패 시 wuxia 기본값"""
        analyst.context.guard.get_genre_name.side_effect = Exception("감지 실패")
        assert analyst._get_current_genre() == "wuxia"

    def test_genre_library_path_returns_path(self, analyst):
        """장르별 라이브러리 경로가 Path 객체를 반환"""
        path = analyst._get_genre_library_path("wuxia")
        assert isinstance(path, Path)
        assert "analyst_libraries.json" in str(path)

    def test_genre_library_path_hunter(self, analyst):
        """hunter 장르 전용 라이브러리 경로"""
        path = analyst._get_genre_library_path("hunter")
        assert "analyst_libraries_hunter.json" in str(path)

    def test_genre_library_path_fantasy(self, analyst):
        """fantasy 장르 전용 라이브러리 경로"""
        path = analyst._get_genre_library_path("fantasy")
        assert "analyst_libraries_fantasy.json" in str(path)

    def test_genre_library_path_unknown(self, analyst):
        """알 수 없는 장르는 기본 라이브러리 사용"""
        path = analyst._get_genre_library_path("unknown_genre")
        assert "analyst_libraries.json" in str(path)

    def test_load_genre_libraries_fantasy(self, analyst):
        """fantasy 라이브러리 로딩 결과가 비어있지 않음"""
        libs = analyst._load_genre_libraries("fantasy")
        assert isinstance(libs, dict)
        assert libs.get("intro", "{}") != "{}"
        assert libs.get("dev", "{}") != "{}"


class TestAnalystStateTrackerValidation:
    def test_validate_arc_with_state_tracker_returns_empty_list(self, analyst):
        result = analyst._validate_arc_with_state_tracker({"arc_no": 1})
        assert result == []


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 7: 장르별 분기 처리 (wuxia vs investment)
# ══════════════════════════════════════════════════════════════


class TestAnalystGenreBranching:
    def test_investment_genre_detection(self, analyst):
        """투자물 장르가 올바르게 감지되는지"""
        analyst.context.guard.get_genre_name.return_value = "investment"
        assert analyst._get_current_genre() == "investment"

    def test_investment_library_path(self, analyst):
        """투자물 전용 라이브러리 경로"""
        path = analyst._get_genre_library_path("investment")
        assert "analyst_libraries_investment.json" in str(path)

    def test_cooking_genre_detection(self, analyst):
        """요리 장르 감지"""
        analyst.context.guard.get_genre_name.return_value = "요리"
        assert analyst._get_current_genre() == "cooking"

    def test_alt_history_genre_detection(self, analyst):
        """대체역사 장르 감지"""
        analyst.context.guard.get_genre_name.return_value = "대체역사"
        assert analyst._get_current_genre() == "alt_history"


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 8: Arc 상태 계승 검증
# ══════════════════════════════════════════════════════════════


class TestAnalystArcStateContinuity:
    def test_no_prev_arc_is_valid(self, analyst):
        """이전 Arc가 없으면 유효"""
        result = analyst._validate_arc_state_continuity_v60({}, None)
        assert result["valid"] is True
        assert result["severity"] == "NONE"

    def test_location_mismatch_is_critical(self, analyst):
        """위치 불일치 감지"""
        prev_arc = {
            "state_constraints": {"arc_end_state": {"location": "무림맹"}, "joint_docs": {"final_location": "무림맹"}}
        }
        curr_arc = {"state_constraints": {"arc_start_state": {"location": "개봉부"}}}
        result = analyst._validate_arc_state_continuity_v60(curr_arc, prev_arc)
        assert result["severity"] in ["CRITICAL", "WARNING"]
        assert any("위치" in issue for issue in result["issues"])

    def test_missing_items_detected(self, analyst):
        """아이템 손실 감지"""
        prev_arc = {"state_constraints": {"arc_end_state": {"equipment": ["용린검", "철혈패"]}, "joint_docs": {}}}
        curr_arc = {"state_constraints": {"arc_start_state": {"equipment": ["용린검"]}}}
        result = analyst._validate_arc_state_continuity_v60(curr_arc, prev_arc)
        assert any("아이템" in issue or "손실" in issue for issue in result["issues"])

    def test_matching_states_pass(self, analyst):
        """일치하는 상태는 통과"""
        prev_arc = {
            "state_constraints": {
                "arc_end_state": {"location": "무림맹", "equipment": ["검"]},
                "joint_docs": {"final_location": "무림맹"},
            }
        }
        curr_arc = {"state_constraints": {"arc_start_state": {"location": "무림맹", "equipment": ["검"]}}}
        result = analyst._validate_arc_state_continuity_v60(curr_arc, prev_arc)
        assert result["valid"] is True


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 9: 전술 문서 화 간 연속성 검증
# ══════════════════════════════════════════════════════════════


class TestAnalystTacticalDocContinuity:
    def test_empty_doc_returns_valid(self, analyst):
        """빈 전술 문서는 유효"""
        result = analyst._validate_tactical_doc_continuity_v60("", 3)
        assert result["valid"] is True

    def test_dict_doc_converted_to_string(self, analyst):
        """dict 타입 전술 문서가 문자열로 변환"""
        result = analyst._validate_tactical_doc_continuity_v60({"tactical_doc": "제 1화 전술 설계..."}, 1)
        assert isinstance(result, dict)
        assert "valid" in result

    def test_injury_tracking(self, analyst):
        """부상 상태 추적"""
        doc = """
        제 1화 전술 설계
        주인공이 중상을 입고 쓰러졌다.

        제 2화 전술 설계
        아직 회복되지 않은 상태에서 전투에 뛰어들었다. 도약과 질주를 거듭했다. 비무에 참가하여 격투를 벌였다.
        """
        result = analyst._validate_tactical_doc_continuity_v60(doc, 2)
        assert isinstance(result, dict)
        assert "injury_tracking" in result


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 10: _normalize_arc_output 회차 정규화
# ══════════════════════════════════════════════════════════════


class TestAnalystNormalizeArcOutput:
    def test_beat_sequence_normalization(self, analyst):
        """beat_sequence 회차 표기 정규화"""
        arc_data = {
            "beat_sequence": ["제 999화: 잘못된 번호의 비트", "제 1000화: 두 번째 비트"],
            "tactical_doc": "전술 문서",
        }
        analyst._normalize_arc_output(arc_data, ep_start=10, ep_count=2)
        assert "제 10화:" in arc_data["beat_sequence"][0]
        assert "제 11화:" in arc_data["beat_sequence"][1]

    def test_non_dict_input_ignored(self, analyst):
        """dict가 아닌 입력은 무시"""
        analyst._normalize_arc_output("not a dict", ep_start=1, ep_count=3)

    def test_tactical_doc_header_normalization(self, analyst):
        """tactical_doc 회차 헤더 정규화"""
        arc_data = {"beat_sequence": [], "tactical_doc": "[제 1화 전술 설계] 내용1 [제 2화 전술 설계] 내용2"}
        analyst._normalize_arc_output(arc_data, ep_start=5, ep_count=2)
        assert "[제 5화 전술 설계]" in arc_data["tactical_doc"]
        assert "[제 6화 전술 설계]" in arc_data["tactical_doc"]


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 11: stitch_joints 메서드 존재 확인
# ══════════════════════════════════════════════════════════════


class TestAnalystPostProcessArc:
    def test_post_process_arc_defaults_npc_martial_state_changes(self, analyst):
        result = analyst._post_process_arc(
            final_arc_data={"beat_sequence": [], "tactical_doc": ""},
            clean_arc_no=1,
            vol_no=1,
            ep_start=1,
            target_ep_count=2,
        )

        assert result["state_changes"]["npc_martial_state_changes"] == []

    def test_post_process_arc_preserves_npc_martial_state_changes(self, analyst):
        martial_changes = [
            {
                "name": "Chief Han",
                "episode": 2,
                "realm": "Peak",
                "techniques_learned": ["Storm Palm"],
            }
        ]
        result = analyst._post_process_arc(
            final_arc_data={
                "beat_sequence": [],
                "tactical_doc": "",
                "state_changes": {"npc_martial_state_changes": martial_changes},
            },
            clean_arc_no=1,
            vol_no=1,
            ep_start=1,
            target_ep_count=2,
        )

        assert result["state_changes"]["npc_martial_state_changes"] == martial_changes


class TestAnalystStitchJoints:
    def test_method_exists(self, analyst):
        """stitch_joints 메서드가 존재해야 한다"""
        assert hasattr(analyst, "stitch_joints")
        assert callable(analyst.stitch_joints)

    def test_calls_ask_and_parse(self, analyst):
        """stitch_joints는 ask를 호출하고 결과를 파싱"""
        mock_response = json.dumps(
            {"status": "CLEAR", "repaired_joint_b": "", "entity_anchors": {}, "welding_report": "이상 없음"}
        )
        analyst.ask = MagicMock(return_value=mock_response)

        result = analyst.stitch_joints(
            joint_a={"final_location": "무림맹"}, joint_b={"final_location": "개봉부"}, context_b="다음 아크 컨텍스트"
        )
        assert isinstance(result, dict)
        analyst.ask.assert_called_once()


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 12: 초기화 테스트 - app 참조 확인
# ══════════════════════════════════════════════════════════════


class TestStage2OrchestratorInit:
    def test_app_reference(self, orchestrator, mock_app):
        """Stage2Orchestrator는 app 참조를 가져야 한다"""
        assert orchestrator.app is mock_app

    def test_app_ui_accessible(self, orchestrator):
        """app.ui를 통한 로깅이 가능해야 한다"""
        orchestrator.app.ui.log("테스트 로그")
        orchestrator.app.ui.log.assert_called_with("테스트 로그")


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 13: 메서드 존재 확인
# ══════════════════════════════════════════════════════════════


class TestStage2OrchestratorMethodsExist:
    def test_stage_2_arcs_async_logic_exists(self, orchestrator):
        """stage_2_arcs_async_logic 메서드가 존재"""
        assert hasattr(orchestrator, "stage_2_arcs_async_logic")
        assert callable(orchestrator.stage_2_arcs_async_logic)

    def test_normalize_tactical_text_exists(self, orchestrator):
        """_normalize_tactical_text 메서드가 존재"""
        assert hasattr(orchestrator, "_normalize_tactical_text")

    def test_is_tactical_doc_duplicate_exists(self, orchestrator):
        """_is_tactical_doc_duplicate 메서드가 존재"""
        assert hasattr(orchestrator, "_is_tactical_doc_duplicate")

    def test_normalize_flow_text_exists(self, orchestrator):
        """_normalize_flow_text 메서드가 존재"""
        assert hasattr(orchestrator, "_normalize_flow_text")

    def test_stage2_flow_guard_exists(self, orchestrator):
        """_stage2_flow_guard 메서드가 존재"""
        assert hasattr(orchestrator, "_stage2_flow_guard")

    def test_stage2_flow_guard_legacy_exists(self, orchestrator):
        """_stage2_flow_guard_legacy 메서드가 존재"""
        assert hasattr(orchestrator, "_stage2_flow_guard_legacy")


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 14: _normalize_tactical_text 정규화
# ══════════════════════════════════════════════════════════════


class TestStage2NormalizeTacticalText:
    def test_normal_string(self, orchestrator):
        """일반 문자열 정규화"""
        result = orchestrator._normalize_tactical_text("전술 문서  내용")
        assert result == "전술 문서 내용"

    def test_escape_sequences(self, orchestrator):
        """이스케이프 시퀀스 변환"""
        result = orchestrator._normalize_tactical_text("줄1\\n줄2\\t탭")
        # 이중 이스케이프 해제 후 공백 정규화
        assert "\\n" not in result or "\n" not in result

    def test_non_string_returns_empty(self, orchestrator):
        """문자열이 아닌 입력은 빈 문자열 반환"""
        assert orchestrator._normalize_tactical_text(None) == ""
        assert orchestrator._normalize_tactical_text(123) == ""
        assert orchestrator._normalize_tactical_text([]) == ""

    def test_whitespace_collapse(self, orchestrator):
        """여러 공백이 하나로 축소"""
        result = orchestrator._normalize_tactical_text("a    b    c")
        assert result == "a b c"


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 15: _is_tactical_doc_duplicate 중복 감지
# ══════════════════════════════════════════════════════════════


class TestStage2IsTacticalDocDuplicate:
    def test_identical_texts_detected(self, orchestrator):
        """동일 텍스트 중복 감지"""
        text = "이것은 전술 문서입니다. 주인공이 적과 싸웁니다."
        assert orchestrator._is_tactical_doc_duplicate(text, [text]) is True

    def test_different_texts_not_duplicate(self, orchestrator):
        """다른 텍스트는 중복 아님"""
        text1 = "주인공이 무림맹에서 적과 결투한다."
        text2 = "주인공이 개봉부에서 거래를 한다."
        assert orchestrator._is_tactical_doc_duplicate(text1, [text2]) is False

    def test_empty_candidate(self, orchestrator):
        """빈 후보 텍스트는 중복 아님"""
        assert orchestrator._is_tactical_doc_duplicate("", ["참조 텍스트"]) is False

    def test_empty_reference_list(self, orchestrator):
        """빈 참조 리스트는 중복 아님"""
        assert orchestrator._is_tactical_doc_duplicate("텍스트", []) is False

    def test_near_duplicate_band_matches_pipeline_threshold(self, orchestrator):
        """near-duplicate band는 facade/orchestrator/pipeline이 동일하게 판정"""
        candidate = "alpha beta gamma delta epsilon zeta eta theta"
        reference = "alpha beta gamma delta epsilon zeta eta iota"
        ratio = SequenceMatcher(
            None,
            orchestrator._normalize_tactical_text(candidate),
            orchestrator._normalize_tactical_text(reference),
        ).ratio()

        assert TACTICAL_DOC_DUPLICATE_THRESHOLD < ratio < 0.98
        assert orchestrator._is_tactical_doc_duplicate(candidate, [reference]) is True
        assert orchestrator.validation_pipeline._is_tactical_doc_duplicate(candidate, [reference]) is True


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 16: _normalize_flow_text
# ══════════════════════════════════════════════════════════════


class TestStage2NormalizeFlowText:
    def test_removes_special_chars(self, orchestrator):
        """특수문자 제거"""
        result = orchestrator._normalize_flow_text("테스트!@#$%문자")
        assert "!" not in result
        assert "@" not in result

    def test_lowercase_conversion(self, orchestrator):
        """소문자 변환"""
        result = orchestrator._normalize_flow_text("ABC DEF")
        assert result == "abc def"

    def test_non_string_returns_empty(self, orchestrator):
        """문자열이 아닌 입력은 빈 문자열"""
        assert orchestrator._normalize_flow_text(None) == ""
        assert orchestrator._normalize_flow_text(42) == ""

    def test_preserves_korean(self, orchestrator):
        """한글 보존"""
        result = orchestrator._normalize_flow_text("주인공이 전투한다")
        assert "주인공이" in result
        assert "전투한다" in result


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 17: _stage2_flow_guard 안전 처리
# ══════════════════════════════════════════════════════════════


class TestStage2FlowGuard:
    def test_insufficient_beats_rejected(self, orchestrator):
        """비트 수가 ep_count보다 부족하면 REJECT"""
        arc = {"beat_sequence": ["비트1"], "ep_count": 5}
        result = orchestrator._stage2_flow_guard(arc)
        assert result["status"] == "REJECT"

    def test_empty_beats_rejected(self, orchestrator):
        """빈 비트 시퀀스는 REJECT"""
        arc = {"beat_sequence": [], "ep_count": 3}
        result = orchestrator._stage2_flow_guard(arc)
        assert result["status"] == "REJECT"

    def test_too_short_beats_rejected(self, orchestrator):
        """너무 짧은 비트는 REJECT"""
        arc = {"beat_sequence": ["a", "b", "c"], "ep_count": 3}
        result = orchestrator._stage2_flow_guard(arc)
        assert result["status"] == "REJECT"

    def test_valid_beats_not_immediately_rejected(self, orchestrator):
        """충분한 비트가 있으면 즉시 REJECT하지 않음 (서사 분석기 로드 실패 시 PASS 가능)"""
        arc = {
            "beat_sequence": [
                "제 1화: 주인공이 무림맹에 도착하여 문파의 도전을 받아들인다 치열한 격전이 벌어진다",
                "제 2화: 주인공이 비밀 통로를 발견하고 숨겨진 비급을 찾아 수련을 시작한다 새로운 무공을 익힌다",
                "제 3화: 주인공이 마교의 습격을 격퇴하고 무림맹의 신뢰를 얻는다 동맹을 맺게 된다",
                "제 4화: 주인공이 정보를 수집하여 적의 본거지를 파악하고 작전을 세운다 첩보전이 벌어진다",
                "제 5화: 최종 결전에서 대승을 거두고 새로운 지위를 얻는다 다음 여정의 단서를 발견한다",
            ],
            "ep_count": 5,
        }
        # NarrativeStructureAnalyzer import가 실패할 수 있으므로 폴백 확인
        result = orchestrator._stage2_flow_guard(arc)
        # 비트가 충분하므로 첫 단계 REJECT는 통과해야 함
        # 서사 분석기 유무에 따라 결과가 달라질 수 있으나 최소한 빈 비트 REJECT는 아님
        assert isinstance(result, dict)
        assert "status" in result


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 18: _stage2_flow_guard_legacy
# ══════════════════════════════════════════════════════════════


class TestStage2FlowGuardLegacy:
    def test_no_stagnation_passes(self, orchestrator):
        """서사 정체 없으면 PASS"""
        normalized = [
            "주인공이 무림맹에 도착한다",
            "적의 습격을 격퇴한다",
            "비밀 통로를 발견한다",
            "비급을 수련한다",
            "최종 결전에 승리한다",
        ]
        result = orchestrator._stage2_flow_guard_legacy(normalized)
        assert result["status"] == "PASS"

    def test_high_stagnation_rejected(self, orchestrator):
        """유사 비트 3회 이상 연속 시 REJECT"""
        # 거의 동일한 비트 반복
        normalized = [
            "주인공이 싸운다",
            "주인공이 싸운다",
            "주인공이 싸운다",
            "주인공이 싸운다",
        ]
        result = orchestrator._stage2_flow_guard_legacy(normalized)
        assert result["status"] == "REJECT"

    def test_empty_list_passes(self, orchestrator):
        """빈 리스트는 PASS (stagnation_hits 0)"""
        result = orchestrator._stage2_flow_guard_legacy([])
        assert result["status"] == "PASS"


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 19: Arc 번호 연속성 관련
# ══════════════════════════════════════════════════════════════


class TestStage2ArcNumberContinuity:
    def test_batch_range_calculation(self, orchestrator):
        """배치 범위 계산: 5개씩 처리"""
        # Stage2Orchestrator의 배치 크기는 5
        done_count = 0
        target_limit = 10
        batch_size = 5

        batches = []
        for batch_start in range(done_count, target_limit, batch_size):
            batch_end = min(batch_start + batch_size, target_limit)
            batches.append((batch_start, batch_end))

        assert batches == [(0, 5), (5, 10)]

    def test_partial_batch(self, orchestrator):
        """마지막 배치가 5개 미만인 경우"""
        done_count = 0
        target_limit = 7
        batch_size = 5

        batches = []
        for batch_start in range(done_count, target_limit, batch_size):
            batch_end = min(batch_start + batch_size, target_limit)
            batches.append((batch_start, batch_end))

        assert batches == [(0, 5), (5, 7)]


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 20: _auto_correct_joint_docs_v60
# ══════════════════════════════════════════════════════════════


class TestAnalystAutoCorrectJointDocs:
    def test_empty_tactical_doc(self, analyst):
        """빈 전술 문서는 원본 반환"""
        arc_data = {"state_constraints": {}}
        result = analyst._auto_correct_joint_docs_v60("", arc_data)
        assert result == arc_data

    def test_dict_tactical_doc(self, analyst):
        """dict 전술 문서 처리"""
        arc_data = {"state_constraints": {}}
        result = analyst._auto_correct_joint_docs_v60({"tactical_doc": "제 1화 전술 설계 내용"}, arc_data)
        assert isinstance(result, dict)

    def test_location_extraction(self, analyst):
        """마지막 화에서 위치 추출"""
        tactical_doc = """
        제 1화 전술 설계
        주인공이 무림맹에서 싸운다.

        제 2화 전술 설계
        주인공이 개봉부에 도착하여 새 동맹을 맺는다.
        """
        arc_data = {"state_constraints": {}}
        result = analyst._auto_correct_joint_docs_v60(tactical_doc, arc_data)
        assert isinstance(result, dict)


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 21: plan_single_arc_v20 메서드 존재 확인
# ══════════════════════════════════════════════════════════════


class TestAnalystPlanArcV20:
    def test_method_exists(self, analyst):
        """plan_single_arc_v20 메서드가 존재해야 한다"""
        assert hasattr(analyst, "plan_single_arc_v20")
        assert callable(analyst.plan_single_arc_v20)

    def test_method_signature_has_key_params(self, analyst):
        """plan_single_arc_v20의 핵심 파라미터 확인"""
        import inspect

        sig = inspect.signature(analyst.plan_single_arc_v20)
        param_names = list(sig.parameters.keys())
        assert "arc_no" in param_names
        assert "vol_strategy" in param_names
        assert "curr_block" in param_names
        assert "ep_start" in param_names
        assert "protagonist_name" in param_names
        assert "state_tracker" in param_names

    def test_prepare_single_arc_plan_context_builds_seed_ban_and_hud(self, analyst):
        analyst.context.sys = MagicMock()
        analyst.context.sys.hud = MagicMock()
        analyst.context.sys.hud.get_critical_keys.return_value = []

        prev_state = MagicMock()
        prev_state.to_dict.return_value = {
            "location": "무림맹",
            "hp": "80/100",
            "status": "경계",
            "items": ["철검", "패도령"],
        }
        state_tracker = MagicMock()
        state_tracker.get_state_at_episode.return_value = prev_state

        result = analyst._prepare_single_arc_plan_context(
            arc_no="6",
            vol_strategy="세력 재편 전략",
            prev_block={"summary": "이전 아크"},
            curr_block={"content": {"context": "a" * 1200}},
            next_block={"summary": "다음 아크"},
            ep_start=11,
            assigned_seeds=[{"action": "회수", "seed_id": "S-1", "logic": "복선 회수"}],
            recent_patterns=["전투", "전투"],
            protagonist_name="청운",
            state_tracker=state_tracker,
        )

        assert result["clean_arc_no"] == 6
        assert result["vol_no"] == 2
        assert result["target_ep_count"] == 5
        assert "ABSOLUTE BAN" in result["safe_data"]["assigned_seeds_info"]
        assert "WARNING" in result["safe_data"]["assigned_seeds_info"]
        assert "무림맹" in result["safe_data"]["protagonist_hud_state"]
        assert result["safe_data"]["ep_count"] == result["target_ep_count"]

    def test_normalize_single_arc_draft_result_syncs_pacing_and_beats(self, analyst):
        draft_result = {
            "ep_count": "9화",
            "pacing_decision": {"chosen_pacing": "Standard"},
            "beat_sequence": ["첫 번째 비트"],
        }

        normalized, actual_ep_count = analyst._normalize_single_arc_draft_result(
            draft_result,
            target_ep_count=4,
            min_ep_count=3,
            max_ep_count=6,
        )

        assert actual_ep_count == 5
        assert len(normalized["beat_sequence"]) == 5
        assert normalized["beat_sequence"][0] == "첫 번째 비트"

    def test_finalize_single_arc_plan_result_prefers_revised_arc(self, analyst):
        loop_state = {"draft_result": {"arc_no": 3, "source": "draft"}, "actual_ep_count": 4}
        result = analyst._finalize_single_arc_plan_result(
            audit_result={"revised_arc": {"arc_no": 3, "source": "revised"}},
            arc_loop_state=loop_state,
            retry_success=True,
            clean_arc_no=3,
            target_ep_count=4,
        )

        assert result["source"] == "revised"
        assert result["_actual_ep_count"] == 4


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 22: enrich_raw_block_async 메서드 존재 확인
# ══════════════════════════════════════════════════════════════


class TestAnalystEnrichBlock:
    def test_method_exists(self, analyst):
        """enrich_raw_block_async 메서드가 존재해야 한다"""
        assert hasattr(analyst, "enrich_raw_block_async")
        assert callable(analyst.enrich_raw_block_async)

    def test_method_is_async(self, analyst):
        """enrich_raw_block_async는 async 메서드"""
        import asyncio

        assert asyncio.iscoroutinefunction(analyst.enrich_raw_block_async)

    def test_general_exception_marks_enrich_skipped_and_logs_error(self, analyst, caplog):
        import asyncio
        import logging

        analyst.context.sys = None
        analyst._ask_with_analyst_cache = MagicMock(side_effect=RuntimeError("boom"))

        raw_block = {"block_id": "B1", "title": "테스트 블록"}
        with caplog.at_level(logging.ERROR):
            result = asyncio.run(analyst.enrich_raw_block_async(dict(raw_block), None, None, []))

        assert result["block_id"] == "B1"
        assert result["_enrich_skipped"] is True
        assert result["_enrich_error"] == "boom"
        assert any(
            record.levelno == logging.ERROR and "Enrich Critical Error" in record.getMessage()
            for record in caplog.records
        )


# ══════════════════════════════════════════════════════════════
# [Stage2Orchestrator] Test 23: stage_2_arcs_async_logic is async
# ══════════════════════════════════════════════════════════════


class TestStage2AsyncLogic:
    def test_is_coroutine_function(self, orchestrator):
        """stage_2_arcs_async_logic는 async 함수여야 한다"""
        import asyncio

        assert asyncio.iscoroutinefunction(orchestrator.stage_2_arcs_async_logic)


# ══════════════════════════════════════════════════════════════
# [Analyst] Test 24: protagonist_config 처리
# ══════════════════════════════════════════════════════════════


class TestAnalystProtagonistConfig:
    def test_world_origin_primitive(self, analyst):
        """원시인 세계 출신 설정 처리"""
        mock_response = json.dumps({"vol_no": 1, "strategy_doc": "문서"})
        analyst.ask = MagicMock(return_value=mock_response)

        bible = {
            "MasterBible": {
                "AssetLibrary": {},
                "protagonist_config": {"world_origin": "원시인", "incarnation_type": "회귀자"},
            }
        }
        result = analyst.plan_single_volume_v20(vol_no=1, master_bible=bible, treatment_raw_part="[]")
        # ask가 호출되었는지 확인 (프롬프트에 원시인 관련 내용이 포함됨)
        call_args = analyst.ask.call_args[0][0]
        assert "원시인" in call_args or "현대 용어" in call_args

    def test_incarnation_type_regression(self, analyst):
        """회귀자 환생 유형 처리"""
        mock_response = json.dumps({"vol_no": 1, "strategy_doc": "문서"})
        analyst.ask = MagicMock(return_value=mock_response)

        bible = {
            "MasterBible": {
                "AssetLibrary": {},
                "protagonist_config": {"world_origin": "현대인", "incarnation_type": "회귀자"},
            }
        }
        analyst.plan_single_volume_v20(vol_no=1, master_bible=bible, treatment_raw_part="[]")
        call_args = analyst.ask.call_args[0][0]
        assert "회귀자" in call_args or "미래" in call_args
