"""Shared pytest fixtures for tests."""

from __future__ import annotations

import gc
import json
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_dir():
    """Create and aggressively clean a temporary directory for tests."""
    tmpdir = Path(tempfile.mkdtemp())
    try:
        yield tmpdir
    finally:
        gc.collect()
        time.sleep(0.1)
        for _ in range(5):
            try:
                shutil.rmtree(tmpdir)
                break
            except FileNotFoundError:
                break
            except PermissionError:
                gc.collect()
                time.sleep(0.1)


@pytest.fixture
def sample_bible():
    """Sample bible data."""
    return {
        "title": "테스트 무협소설",
        "genre": "wuxia",
        "treatment": {
            "protagonist": {
                "name": "이청운",
                "martial_root": 85,
                "internal_energy": 60,
                "techniques": ["천무검법", "경공술"],
            },
            "setting": {"world": "중원 무림", "era": "명말"},
            "themes": ["복수", "성장", "우정"],
        },
        "volumes": [{"volume": 1, "title": "강호입문", "episodes": 50}],
    }


@pytest.fixture
def sample_blueprint():
    """Sample blueprint data."""
    return {
        "ep_num": 1,
        "title": "운명의 시작",
        "scene_breakdown": {
            "scene_1": "수련장 입장",
            "scene_2": "스승의 조언",
            "scene_3": "첫 대련",
            "scene_4": "의문의 등장",
        },
        "scenes": [
            {
                "scene_num": 1,
                "location": "천무수련장",
                "characters": ["이청운", "인사부"],
                "action": "수련",
                "beats": ["기상", "수련 시작", "내공 운용"],
            },
            {
                "scene_num": 2,
                "location": "수련장 앞마당",
                "characters": ["이청운", "유섬"],
                "action": "첫 대련",
                "beats": ["유섬 등장", "검법 대결", "승리"],
            },
        ],
        "required_elements": {
            "foreshadowing": ["검의 비밀"],
            "character_development": ["주인공 성장"],
        },
    }


@pytest.fixture
def sample_manuscript():
    """Sample manuscript over minimum length."""
    base_text = (
        "천무문 수련장은 고요했다. "
        "이청운은 호흡을 가다듬고 검을 들었다. "
        "인사부가 멀리서 지켜보며 조언했다. "
        "검끝이 떨리고 공기가 갈라졌다. "
    )
    return (base_text * 300).strip()


@pytest.fixture
def sample_hud_wuxia():
    """Sample wuxia HUD."""
    return {
        "character": "이청운",
        "martial_root": 85,
        "internal_energy": 60,
        "lightness": 45,
        "sword_skill": 70,
        "palm_skill": 55,
        "equipment": ["천무검", "경공서"],
        "techniques": ["천무검법", "경공술"],
        "injuries": [],
        "relationships": {
            "인사부": {"affinity": 90, "type": "스승"},
            "유섬": {"affinity": -50, "type": "적"},
        },
        "actual_truth": {
            "equipment": ["천무검", "경공서"],
            "physical_tags": [],
            "status_tags": [],
            "reputation": 10,
        },
    }


@pytest.fixture
def sample_hud_hunter():
    """Sample hunter HUD."""
    return {
        "character": "김현우",
        "awakening_grade": "A",
        "mana": 8500,
        "strength": 120,
        "agility": 95,
        "skills": ["섀도우검", "순간이동"],
        "equipment": ["마검 아스트랄", "마력갑옷"],
        "guild": "레드드래곤",
        "cleared_gates": ["D급 3개", "C급 2개", "B급 1개"],
    }


@pytest.fixture
def sample_hud_investment():
    """Sample investment HUD."""
    return {
        "character": "박재민",
        "total_assets": 5_000_000_000,
        "cash": 1_000_000_000,
        "stocks": {
            "삼성전자": {"shares": 10000, "avg_price": 70000},
            "네이버": {"shares": 500, "avg_price": 250000},
        },
        "real_estate": ["강남 아파트", "역삼 빌딩"],
        "connections": {
            "김부장": {"influence": 85, "type": "협력"},
            "정기자": {"influence": 60, "type": "언론"},
        },
    }


@pytest.fixture
def mock_api_client():
    """Mock Gemini API client."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({"status": "success", "content": "테스트 응답"}, ensure_ascii=False)
    client.models.generate_content.return_value = mock_response
    return client


@pytest.fixture
def mock_db_manager(temp_dir):
    """Mock DBManager instance backed by temp DB."""
    from modules.core.db_manager import DBManager

    db_path = temp_dir / "test_project.db"
    db = DBManager(db_path)
    try:
        yield db
    finally:
        db.close()
        gc.collect()
        time.sleep(0.1)


@pytest.fixture
def mock_project_context(temp_dir, sample_bible):
    """Mock ProjectContext."""

    @dataclass
    class MockPaths:
        root: Path
        drafts: Path
        memory: Path
        config: Path

    class MockContext:
        def __init__(self):
            self.name = "test_project"
            self.paths = MockPaths(
                root=temp_dir,
                drafts=temp_dir / "drafts",
                memory=temp_dir / "memory",
                config=temp_dir / "config",
            )
            self.paths.drafts.mkdir(exist_ok=True)
            self.paths.memory.mkdir(exist_ok=True)
            self.paths.config.mkdir(exist_ok=True)

            self.bible = sample_bible
            self.ui = MagicMock()
            self.ui.log = MagicMock()

    return MockContext()


@pytest.fixture
def validation_context(sample_blueprint, sample_hud_wuxia):
    """Validation context fixture with backward/forward compatible schema."""
    return {
        "encyclopedia": {
            "characters": {
                "이청운": {"alive": True, "location": "천무수련장"},
                "인사부": {"alive": True, "location": "천무수련장"},
                "유섬": {"alive": True, "location": "불명"},
            },
            "items": {
                "천무검": {"owner": "이청운", "destroyed": False},
                "경공서": {"owner": "이청운", "destroyed": False},
            },
            "locations": {
                "천무수련장": {"destroyed": False},
                "마교 본단": {"destroyed": False},
            },
            "npcs": [
                {"name": "이청운", "status": "alive", "relationship_state": "중립"},
                {"name": "인사부", "status": "alive", "relationship_state": "중립"},
                {"name": "유섬", "status": "alive", "relationship_state": "적대"},
            ],
        },
        "martial_hud": sample_hud_wuxia,
        "blueprint": sample_blueprint,
        "mode": "MANUSCRIPT",
        "history": [],
        "npc_profiles": {},
    }
