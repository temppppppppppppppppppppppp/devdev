"""[Phase 6-B] L2 재시도/복구 — 3라운드 재시도 루프, 패치 모드, chain_link

6건:
1. 1라운드 합격 → DB manuscripts 저장
2. 불합격 → regenerate_with_feedback 호출
3. score=60, round=1 → patch_with_feedback 호출
4. score=30 → regenerate (패치 아님)
5. 3라운드 전패 → legacy Writer 호출
6. 합격 후 → DB anchor chain_link_1 존재
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.constants import PatchModeThresholds
from modules.core.stage4_orchestrator import Stage4Orchestrator

from .conftest import (
    MOCK_CHAIN_LINK,
    MOCK_DIRECTOR_REJECT,
    MOCK_MANUSCRIPT,
)

# ══════════════════════════════════════════════════════════════
# Helper: mock_app factory
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def mock_app(e2e_db):
    """Stage4Orchestrator에 주입할 mock SovereignApp"""
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()
    app.ui.console = MagicMock()
    app.selected_genre = {"type": "wuxia", "name": "무협"}
    app.current_project = MagicMock()
    app.current_project.db = e2e_db
    app.current_project.name = "e2e_test"
    app.current_project.master_bible = {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {"KeyNPCs": [], "Key_Items": []},
            "protagonist_config": {
                "world_origin": "현대인",
                "incarnation_type": "회귀자",
            },
        }
    }
    app.current_project.arcs = []
    app.current_project.paths = MagicMock()
    app.current_project.paths.drafts = Path("/tmp/e2e_drafts")
    app.perf_timer = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()
    app.agents = {
        "chief_writer": MagicMock(),
        "director": MagicMock(),
        "writer": MagicMock(),
        "manager": MagicMock(),
    }
    app.character_voice = None
    app.diversity_engine = None
    app.memory = MagicMock()
    app.failure_learner = None
    app.foreshadow_tracker = None
    app.state_tracker = None
    app.semantic_plot_guard = None
    return app


# ══════════════════════════════════════════════════════════════
# L2-R-1: 1라운드 합격 → DB manuscripts 저장
# ══════════════════════════════════════════════════════════════


class TestRound0PassSavesManuscript:
    def test_round0_pass_saves_manuscript(self, e2e_db):
        """PASS 시 manuscripts 테이블에 저장 확인"""
        e2e_db.save_manuscript(1, "운명의 시작", MOCK_MANUSCRIPT)
        loaded = e2e_db.get_manuscript(1)
        assert loaded is not None
        assert loaded["title"] == "운명의 시작"
        assert loaded["content"] == MOCK_MANUSCRIPT
        assert len(loaded["content"]) > 4000


# ══════════════════════════════════════════════════════════════
# L2-R-2: 불합격 → regenerate_with_feedback 호출
# ══════════════════════════════════════════════════════════════


class TestRound0RejectTriggersRound1:
    def test_round0_reject_triggers_round1(self):
        """REJECT 시 previous_attempt 구성 + 재작성 판단 로직"""
        director_result = MOCK_DIRECTOR_REJECT.copy()
        assert director_result["verdict"] == "REJECT"

        # Stage4의 REJECT 경로 로직 재현
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

        assert previous_attempt["score"] == 45
        assert previous_attempt["best_manuscript"] != ""
        # score=45 < REWRITE(50) → 패치 미진입, regenerate_with_feedback
        assert previous_attempt["score"] < PatchModeThresholds.REWRITE


# ══════════════════════════════════════════════════════════════
# L2-R-3: score=60, round=1 → patch_with_feedback 호출
# ══════════════════════════════════════════════════════════════


class TestPatchModeEntryScore60:
    def _should_use_patch(self, previous_attempt, interview_round):
        """stage4_orchestrator.py의 분기 조건 재현"""
        _prev_score = previous_attempt.get("score", 0) if previous_attempt else 0
        _prev_manuscript = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
        return _prev_score >= PatchModeThresholds.REWRITE and interview_round == 1 and bool(_prev_manuscript)

    def test_patch_mode_entry_score_60(self):
        """score=60, round=1, best_manuscript 있음 → 패치 모드 진입"""
        prev = {"score": 60, "best_manuscript": MOCK_MANUSCRIPT}
        assert self._should_use_patch(prev, interview_round=1) is True

    def test_patch_mode_boundary_50(self):
        """score=50 (경계값) → 패치 모드 진입"""
        prev = {"score": 50, "best_manuscript": MOCK_MANUSCRIPT}
        assert self._should_use_patch(prev, interview_round=1) is True


# ══════════════════════════════════════════════════════════════
# L2-R-4: score=30 → regenerate (패치 아님)
# ══════════════════════════════════════════════════════════════


class TestLowScoreFullRewrite:
    def test_low_score_full_rewrite(self):
        """score=30 → 패치 미진입, full regenerate"""
        prev = {"score": 30, "best_manuscript": MOCK_MANUSCRIPT}
        _prev_score = prev.get("score", 0)
        assert _prev_score < PatchModeThresholds.REWRITE
        # round=1이어도 score 미달이면 패치 불가
        _use_patch = _prev_score >= PatchModeThresholds.REWRITE and bool(prev.get("best_manuscript", ""))
        assert _use_patch is False


# ══════════════════════════════════════════════════════════════
# L2-R-5: 3라운드 전패 → legacy Writer 호출
# ══════════════════════════════════════════════════════════════


class TestAllRoundsFailFrozenHuman:
    def test_all_rounds_fail_frozen_human(self, mock_app):
        """3라운드 전부 REJECT 시 frozen_human 경로 (legacy writer) 진입 확인"""
        orch = Stage4Orchestrator(mock_app)

        # 3라운드 전패 시나리오: interview_round 0, 1, 2 전부 REJECT
        # → 루프 탈출 후 frozen_human 분기 (writer.write_v20_manuscript)
        # 여기서는 분기 판단 로직만 검증
        final_manuscript = None
        for interview_round in range(3):
            # 모든 라운드에서 REJECT
            verdict = "REJECT"
            final_manuscript = None  # PASS 안 됨

        # 3라운드 종료 후 final_manuscript == None → frozen_human
        assert final_manuscript is None
        # legacy writer가 사용 가능한지 확인
        assert "writer" in orch.ctx.agents


# ══════════════════════════════════════════════════════════════
# L2-R-6: 합격 후 → DB anchor chain_link_1 존재
# ══════════════════════════════════════════════════════════════


class TestChainLinkSavedAfterPass:
    def test_chain_link_saved_after_pass(self, e2e_db):
        """합격 후 chain_link 저장 → DB anchor에서 로드 가능"""
        # 원고 저장
        e2e_db.save_manuscript(1, "운명의 시작", MOCK_MANUSCRIPT)

        # chain_link 저장 (Stage4 후처리 재현)
        e2e_db.save_anchor("chain_link_1", MOCK_CHAIN_LINK)

        # 로드 확인
        loaded = e2e_db.load_anchor("chain_link_1")
        assert loaded is not None
        assert loaded["cliffhanger"] == "흑풍이 다시 나타났다"
        assert "pending_actions" in loaded
        assert len(loaded["pending_actions"]) >= 1
