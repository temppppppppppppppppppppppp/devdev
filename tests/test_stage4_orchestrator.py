"""[Phase 3-5B] Stage4Orchestrator 패치 모드 단위 테스트

검증 대상:
- 패치 모드 진입 (score 50~79, round 1)
- 패치 실패 시 full rewrite 폴백
- 저점(score < 50) → 기존 regenerate_with_feedback
- round 2 → score 무관 full rewrite
- round 0 → generate_ensemble (변경 없음)
- REJECT 시 best_manuscript 저장
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.constants import PatchModeThresholds

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def mock_app():
    """SovereignApp mock"""
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()
    app.ui.console = MagicMock()
    app.selected_genre = {"type": "wuxia", "name": "무협"}
    app.current_project = MagicMock()
    app.current_project.db = MagicMock()
    app.current_project.master_bible = {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {"KeyNPCs": [], "Key_Items": []},
            "protagonist_config": {"world_origin": "현대인", "incarnation_type": "회귀자"},
        }
    }
    app.current_project.arcs = []
    app.current_project.name = "test_project"
    app.current_project.paths = MagicMock()
    app.current_project.paths.drafts = Path("/tmp/test_drafts")
    app.perf_timer = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()
    app.agents = {"director": MagicMock(), "writer": MagicMock(), "manager": MagicMock()}
    app.character_voice = None
    app.diversity_engine = None
    app.memory = MagicMock()
    app.failure_learner = None
    app.foreshadow_tracker = None
    app.state_tracker = None
    return app


@pytest.fixture
def mock_chief_writer():
    """ChiefWriter mock"""
    cw = MagicMock()
    cw.generate_ensemble = MagicMock(
        return_value=[
            {"text": "후보A 원고", "strategy_name": "balanced"},
            {"text": "후보B 원고", "strategy_name": "narrative"},
            {"text": "후보C 원고", "strategy_name": "tension"},
        ]
    )
    cw.regenerate_with_feedback = MagicMock(
        return_value=[
            {"text": "재작성A", "strategy_name": "balanced"},
            {"text": "재작성B", "strategy_name": "narrative"},
            {"text": "재작성C", "strategy_name": "tension"},
        ]
    )
    cw.patch_with_feedback = MagicMock(
        return_value=[
            {"text": "패치A", "strategy_name": "balanced"},
            {"text": "패치B", "strategy_name": "narrative"},
            {"text": "패치C", "strategy_name": "tension"},
        ]
    )
    return cw


# ══════════════════════════════════════════════════════════════
# Test: PatchModeThresholds 상수 확인
# ══════════════════════════════════════════════════════════════


class TestPatchModeThresholds:
    def test_rewrite_threshold(self):
        assert PatchModeThresholds.REWRITE == 50

    def test_patch_threshold(self):
        assert PatchModeThresholds.PATCH == 80

    def test_rewrite_less_than_patch(self):
        assert PatchModeThresholds.REWRITE < PatchModeThresholds.PATCH


# ══════════════════════════════════════════════════════════════
# Test: 패치 모드 분기 로직 (stage4_orchestrator.py 핵심)
# ══════════════════════════════════════════════════════════════


class TestPatchModeBranching:
    """Stage4의 interview loop 내 분기 로직을 직접 테스트.

    실제 Stage4Orchestrator의 전체 루프를 돌리지 않고,
    분기 조건 로직만 검증한다.
    """

    def _should_use_patch(self, previous_attempt, interview_round):
        """stage4_orchestrator.py의 분기 조건 재현"""
        _prev_score = previous_attempt.get("score", 0) if previous_attempt else 0
        _prev_manuscript = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
        return _prev_score >= PatchModeThresholds.REWRITE and interview_round == 1 and bool(_prev_manuscript)

    def test_patch_mode_entry(self):
        """score=65, round=1, best_manuscript 있음 → 패치 모드 진입"""
        prev = {"score": 65, "best_manuscript": "원본 원고 텍스트"}
        assert self._should_use_patch(prev, interview_round=1) is True

    def test_patch_mode_boundary_50(self):
        """score=50 (경계값) → 패치 모드 진입"""
        prev = {"score": 50, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is True

    def test_patch_mode_boundary_79(self):
        """score=79 → 패치 모드 진입 (80 미만은 Director REJECT 가능)"""
        prev = {"score": 79, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is True

    def test_low_score_full_rewrite(self):
        """score=30 → 패치 모드 미진입 (full rewrite)"""
        prev = {"score": 30, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is False

    def test_low_score_boundary_49(self):
        """score=49 (경계값 미만) → 패치 미진입"""
        prev = {"score": 49, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is False

    def test_round0_always_generate(self):
        """round=0 → 패치 미진입 (generate_ensemble 사용)"""
        prev = {"score": 70, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=0) is False

    def test_round2_always_rewrite(self):
        """round=2 → score 무관 패치 미진입"""
        prev = {"score": 70, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=2) is False

    def test_no_manuscript_no_patch(self):
        """best_manuscript 없으면 패치 미진입"""
        prev = {"score": 70, "best_manuscript": ""}
        assert self._should_use_patch(prev, interview_round=1) is False

    def test_empty_previous_attempt(self):
        """previous_attempt={} → 패치 미진입"""
        assert self._should_use_patch({}, interview_round=1) is False

    def test_none_previous_attempt(self):
        """previous_attempt=None → 패치 미진입"""
        assert self._should_use_patch(None, interview_round=1) is False


# ══════════════════════════════════════════════════════════════
# Test: ChiefWriter.patch_with_feedback 호출 계약
# ══════════════════════════════════════════════════════════════


class TestPatchWithFeedbackContract:
    """patch_with_feedback()의 호출 규약과 반환값 검증."""

    def test_patch_returns_3_candidates(self, mock_chief_writer):
        """패치 모드 3후보 반환 확인"""
        result = mock_chief_writer.patch_with_feedback(
            ep_num=10,
            blueprint={},
            prev_manuscript="",
            hud_report="",
            arc_doc="",
            master_bible={},
            style_guide="",
            original_manuscript="원본 원고",
            director_feedback="피드백",
            previous_attempt={"score": 65, "action_items": []},
            attempt_number=2,
        )
        assert len(result) == 3
        mock_chief_writer.patch_with_feedback.assert_called_once()

    def test_patch_fallback_on_empty(self, mock_chief_writer):
        """패치 빈 리스트 → 폴백 판정"""
        mock_chief_writer.patch_with_feedback.return_value = []
        result = mock_chief_writer.patch_with_feedback(
            ep_num=10,
            blueprint={},
            prev_manuscript="",
            hud_report="",
            arc_doc="",
            master_bible={},
            style_guide="",
            original_manuscript="원본",
            director_feedback="피드백",
            previous_attempt={"score": 65, "action_items": []},
            attempt_number=2,
        )
        assert result == []
        # 호출측에서 빈 리스트 감지 후 regenerate_with_feedback 폴백
        assert not result  # falsy → 폴백 트리거

    def test_patch_has_original_manuscript_param(self, mock_chief_writer):
        """patch_with_feedback에 original_manuscript 파라미터 전달 확인"""
        mock_chief_writer.patch_with_feedback(
            ep_num=5,
            blueprint={},
            prev_manuscript="",
            hud_report="",
            arc_doc="",
            master_bible={},
            style_guide="",
            original_manuscript="패치 대상 원고 전문",
            director_feedback="3번 문단 수정",
            previous_attempt={"score": 55},
            attempt_number=2,
        )
        call_kwargs = mock_chief_writer.patch_with_feedback.call_args
        assert call_kwargs.kwargs.get("original_manuscript") == "패치 대상 원고 전문"


# ══════════════════════════════════════════════════════════════
# Test: REJECT 경로에서 best_manuscript 저장
# ══════════════════════════════════════════════════════════════


class TestRejectPathBestManuscript:
    """REJECT 시 previous_attempt에 best_manuscript 저장 검증."""

    def test_previous_attempt_stores_manuscript(self):
        """director_result에서 selected_candidate.manuscript 추출"""
        director_result = {
            "verdict": "REJECT",
            "score": 65,
            "selected": "A",
            "feedback": {"issues": ["3번 문단 연속성 오류"]},
            "action_items": ["3번 문단 수정"],
            "selected_candidate": {"manuscript": "선택된 원고 전문", "title": "테스트"},
        }
        # REJECT 경로 로직 재현
        feedback = director_result.get("feedback", {})
        action_items = director_result.get("action_items", [])
        score = director_result.get("score", 0)
        selected = director_result.get("selected", "A")
        director_feedback = "\n".join(action_items) if action_items else str(feedback.get("issues", []))

        previous_attempt = {
            "strategy": selected,
            "rejection_reason": director_feedback,
            "action_items": action_items,
            "score": score,
            "best_manuscript": director_result.get("selected_candidate", {}).get("manuscript", ""),
        }

        assert previous_attempt["best_manuscript"] == "선택된 원고 전문"
        assert previous_attempt["score"] == 65

    def test_missing_selected_candidate(self):
        """selected_candidate 없을 때 빈 문자열"""
        director_result = {"verdict": "REJECT", "score": 30, "selected": "B"}
        best = director_result.get("selected_candidate", {}).get("manuscript", "")
        assert best == ""

    def test_empty_manuscript_in_candidate(self):
        """selected_candidate.manuscript 빈 문자열"""
        director_result = {
            "verdict": "REJECT",
            "score": 55,
            "selected_candidate": {"manuscript": "", "title": ""},
        }
        best = director_result.get("selected_candidate", {}).get("manuscript", "")
        assert best == ""


# ══════════════════════════════════════════════════════════════
# Test: _handle_round_outcome 에러 경로 반환 구조 (4-R2-b-hotfix)
# ══════════════════════════════════════════════════════════════


class TestHandleRoundOutcomeErrorPaths:
    """_handle_round_outcome의 에러 경로에서 올바른 _RoundOutcome을 반환하는지 검증.

    회귀 대상: 9ade2db 핫픽스 (return {{...}} → return {...})
    + 4-R2-d: dict → _RoundOutcome dataclass 전환
    """

    @pytest.fixture
    def orch_with_ctx(self, mock_app):
        """Stage4Orchestrator + ctx mock 조립"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        # ctx mock 설정
        orch._ctx = MagicMock()
        orch._ctx.ui = MagicMock()
        orch._ctx.ui.log = MagicMock()
        orch._ctx.agents = {
            "director": MagicMock(),
            "writer": MagicMock(),
        }
        orch._ctx.current_project = MagicMock()
        orch._ctx.current_project.master_bible = {"MasterBible": {}}
        orch._ctx.get_protagonist_name = MagicMock(return_value="이청풍")
        orch._ctx.get_int_input = MagicMock(return_value=1)  # abort (not 4)
        return orch

    @pytest.fixture
    def minimal_round_ctx(self):
        """_RoundContext 최소 구성"""
        from modules.core.stage4_orchestrator import _RoundContext

        return _RoundContext(
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            next_ep=1,
            blueprint={"integrated_scenario": "테스트 시나리오"},
            arc_data={"arc_no": 1},
            arc_pos=1,
            total_ep_in_arc=10,
            arc_tactical="전술 문서",
            prev_text="이전 원고",
            prev_ending="이전 결말",
            prev_manuscripts_text="",
            episode_digest="",
            hud_report="HUD",
            current_inventory="",
            current_martial_arts="",
            dead_npcs=[],
            item_acquisition_timeline="",
            chain_link_section="",
            world_state_summary="",
            purism_prompt="",
            genre_name="무협",
            npc_equipment_summary="",
            effective_anti_trope="",
            intro_dna="CYNICAL",
            story_context="",
            style_guide="표준",
            reference_anchor_prompt="",
            mandatory_context="",
            justification_prompt="",
            reflexion_prompt="",
        )

    def test_user_abort_returns_dict(self, orch_with_ctx, minimal_round_ctx, monkeypatch):
        """user abort (메뉴 선택 != 4) → _RoundOutcome 반환, TypeError 없음"""
        from modules.core.stage4_orchestrator import _InterviewRoundResult

        orch = orch_with_ctx

        # 3라운드 모두 REJECT
        orch._run_interview_round = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="REJECT",
                director_feedback="피드백",
                previous_attempt={"score": 30},
            )
        )

        # 냉동인간 원고 반환 + Director REJECT
        orch.ctx.agents["writer"].write_v20_manuscript.return_value = {
            "content": "냉동 원고",
            "title": "제1화",
        }
        orch.ctx.agents["director"].quick_judge_single.return_value = {
            "verdict": "REJECT",
            "reason": "품질 미달",
        }
        # get_int_input → 1 (abort, not 4)
        orch.ctx.get_int_input.return_value = 1

        # StageSpinner is locally imported inside _handle_round_outcome
        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        # Core assertion: returns _RoundOutcome, not dict or set
        from modules.core.stage4_orchestrator import _RoundOutcome

        assert isinstance(result, _RoundOutcome), f"Expected _RoundOutcome, got {type(result).__name__}"
        assert result.should_return is True
        assert result.final_manuscript is None
        assert result.final_title is None
        assert result.final_state_updates == {}

    def test_frozen_human_exception_returns_dict(self, orch_with_ctx, minimal_round_ctx, monkeypatch):
        """frozen human 호출 실패 except → _RoundOutcome 반환, TypeError 없음"""
        from modules.core.stage4_orchestrator import _InterviewRoundResult

        orch = orch_with_ctx

        # 3라운드 모두 REJECT
        orch._run_interview_round = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="REJECT",
                director_feedback="피드백",
                previous_attempt={"score": 30},
            )
        )

        # 냉동인간 호출 시 Exception 발생
        orch.ctx.agents["writer"].write_v20_manuscript.side_effect = RuntimeError("API 실패")

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        # Core assertion: returns _RoundOutcome, not dict or set
        from modules.core.stage4_orchestrator import _RoundOutcome

        assert isinstance(result, _RoundOutcome), f"Expected _RoundOutcome, got {type(result).__name__}"
        assert result.should_return is True
        assert result.final_manuscript is None
        assert result.final_title is None
        assert result.final_state_updates == {}


# ══════════════════════════════════════════════════════════════
# Test: Stage4Orchestrator 초기화 + import
# ══════════════════════════════════════════════════════════════


class TestStage4OrchestratorImport:
    def test_import_succeeds(self):
        """Stage4Orchestrator import 성공"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        assert Stage4Orchestrator is not None

    def test_patch_threshold_imported(self):
        """_PATCH_REWRITE_THRESHOLD 모듈 상수 존재"""
        from modules.core.stage4_orchestrator import _PATCH_REWRITE_THRESHOLD

        assert _PATCH_REWRITE_THRESHOLD == PatchModeThresholds.REWRITE

    def test_init_with_mock_app(self, mock_app):
        """mock_app으로 초기화 성공"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        assert orch.app is mock_app
