"""[Phase 6-B] E2E 테스트 전용 fixtures

실제 DBManager(tmp_path 파일 DB) + Mock LLM + 고정 샘플 데이터.
프로덕션 코드 수정 없이 Stage 4 파이프라인 검증용.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager
from modules.core.stage4_context import Stage4Context
from modules.domain.agents.state_tracker import StateTracker

# ══════════════════════════════════════════════════════════════
# 상수: Mock 원고 (~5100자, >MIN 4000)
# ══════════════════════════════════════════════════════════════

MOCK_MANUSCRIPT = "이청풍은 새벽녘에 눈을 떴다. " * 300  # ~5100자

MOCK_ENSEMBLE = [
    {"text": MOCK_MANUSCRIPT, "strategy_name": "balanced", "title": "운명의 시작"},
    {"text": MOCK_MANUSCRIPT, "strategy_name": "narrative", "title": "운명의 시작"},
    {"text": MOCK_MANUSCRIPT, "strategy_name": "tension", "title": "운명의 시작"},
]

MOCK_DIRECTOR_PASS = {
    "selected": "A",
    "verdict": "PASS",
    "score": 85,
    "selection_reason": "좋은 원고입니다.",
    "feedback": {},
    "action_items": [],
    "selected_candidate": {"manuscript": MOCK_MANUSCRIPT, "title": "운명의 시작"},
    "state_updates": {},
}

MOCK_DIRECTOR_REJECT = {
    "selected": "A",
    "verdict": "REJECT",
    "score": 45,
    "selection_reason": "분량 부족",
    "feedback": {"issues": ["전투 장면 부족"]},
    "action_items": ["전투 장면 보강"],
    "selected_candidate": {"manuscript": MOCK_MANUSCRIPT, "title": "운명의 시작"},
    "state_updates": {},
}

MOCK_CHAIN_LINK = {
    "cliffhanger": "흑풍이 다시 나타났다",
    "pending_actions": ["이청풍의 반격"],
    "emotional_state": "긴장",
    "plot_threads": ["수련 완료"],
}


# ══════════════════════════════════════════════════════════════
# Fixtures: DB
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def e2e_db(tmp_path):
    """실제 DBManager (tmp_path 파일 DB)"""
    db = DBManager(tmp_path / "e2e.db")
    yield db
    db.close()


# ══════════════════════════════════════════════════════════════
# Fixtures: 샘플 데이터
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def e2e_bible():
    return {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {
                "KeyNPCs": [
                    {"name": "노사부", "role": "mentor", "status": "alive"},
                    {"name": "흑풍", "role": "villain", "status": "alive"},
                ],
                "Key_Items": [{"name": "청풍검", "status": "소지"}],
            },
            "protagonist_config": {
                "name": "이청풍",
                "world_origin": "현대인",
                "incarnation_type": "회귀자",
            },
        }
    }


@pytest.fixture
def e2e_arc():
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 10,
        "ep_count": 10,
        "tactical_doc": "이청풍이 청풍산장에서 수련을 시작하고...",
        "state_changes": {
            "npc_deaths": [],
            "relationship_changes": [],
            "npc_personality_changes": [],
        },
        "constraint_summary": "사망 NPC 없음",
    }


@pytest.fixture
def e2e_blueprint():
    return {
        "ep_number": 1,
        "title": "운명의 시작",
        "scene_breakdown": [
            {"scene_num": 1, "location": "청풍산장", "characters": ["이청풍", "노사부"]},
            {"scene_num": 2, "location": "연무장", "characters": ["이청풍"]},
            {"scene_num": 3, "location": "뒤산", "characters": ["이청풍", "흑풍"]},
        ],
        "integrated_scenario": "이청풍이 노사부에게 검을 배우고, 흑풍과 조우한다.",
    }


# ══════════════════════════════════════════════════════════════
# Fixtures: Stage4Context 수동 조립
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def e2e_stage4_ctx(e2e_db):
    """Stage4Context — 필수 5종 실제, 나머지 MagicMock/None"""
    mock_ui = MagicMock()
    mock_ui.log = MagicMock()
    mock_ui.console = MagicMock()

    mock_project = MagicMock()
    mock_project.db = e2e_db
    mock_project.name = "e2e_test_project"
    mock_project.master_bible = {}
    mock_project.arcs = []
    mock_project.paths = MagicMock()
    mock_project.paths.drafts = Path("/tmp/e2e_drafts")

    mock_sys = MagicMock()
    mock_sys.api_client = MagicMock()
    mock_sys.hud = MagicMock()

    state_tracker = StateTracker()
    state_tracker.bind_db(e2e_db)

    mock_agents = {
        "chief_writer": MagicMock(),
        "director": MagicMock(),
        "writer": MagicMock(),
        "manager": MagicMock(),
    }

    ctx = Stage4Context(
        ui=mock_ui,
        current_project=mock_project,
        agents=mock_agents,
        sys=mock_sys,
        state_tracker=state_tracker,
        selected_genre={"type": "wuxia", "name": "무협"},
    )
    return ctx
