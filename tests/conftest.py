"""
[V44] pytest 공통 fixtures

테스트 전역에서 사용되는 fixtures 정의
"""

import pytest
import tempfile
import sqlite3
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, Optional

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 기본 Fixtures
# ============================================================

@pytest.fixture
def temp_dir():
    """임시 디렉토리 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db(temp_dir):
    """임시 SQLite DB 생성"""
    db_path = temp_dir / "test.db"
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()


@pytest.fixture
def sample_bible():
    """테스트용 샘플 bible 데이터"""
    return {
        "title": "테스트 소설",
        "genre": "wuxia",
        "treatment": {
            "protagonist": {
                "name": "이청풍",
                "martial_root": 85,
                "internal_energy": 60,
                "techniques": ["청풍검법", "태극장"]
            },
            "setting": {
                "world": "중원 무림",
                "era": "명대 말기"
            },
            "themes": ["복수", "성장", "우정"]
        },
        "volumes": [
            {"volume": 1, "title": "강호입문", "episodes": 50}
        ]
    }


@pytest.fixture
def sample_blueprint():
    """테스트용 샘플 블루프린트"""
    return {
        "ep_num": 1,
        "title": "운명의 시작",
        "scenes": [
            {
                "scene_num": 1,
                "location": "청풍산장",
                "characters": ["이청풍", "노사부"],
                "action": "수련 장면",
                "beats": ["기상", "수련 시작", "내공 돌파 시도"]
            },
            {
                "scene_num": 2,
                "location": "산장 앞마당",
                "characters": ["이청풍", "암습자"],
                "action": "첫 전투",
                "beats": ["암습자 등장", "검법 대결", "승리"]
            }
        ],
        "required_elements": {
            "foreshadowing": ["검의 비밀"],
            "character_development": ["주인공 성장"]
        }
    }


@pytest.fixture
def sample_manuscript():
    """테스트용 샘플 원고 (최소 4000자)"""
    base_text = """
    청풍산 깊은 곳, 고요한 새벽이 밝아오고 있었다.

    이청풍은 눈을 감고 호흡을 가다듬었다. 스승에게 배운 태극심법의 첫 번째 구결이
    머릿속을 맴돌았다. '마음을 비우고, 기를 단전에 모으라.'

    차가운 아침 공기가 폐부 깊숙이 스며들었다. 그는 천천히 숨을 내쉬며
    내공을 끌어올리기 시작했다. 단전에서 미세한 열기가 피어오르더니,
    서서히 경맥을 따라 퍼져나갔다.

    "좋아, 바로 그거다."

    뒤에서 노사부의 목소리가 들려왔다. 백발이 성성한 노인은
    제자의 수련을 지켜보며 만족스러운 미소를 지었다.

    "하지만 아직 멀었다. 진정한 내공의 경지에 이르려면
    최소 십 년은 더 정진해야 할 것이야."

    이청풍은 고개를 끄덕였다. 조급해하지 않겠다고 마음먹었지만,
    가슴 한켠에서는 빨리 강해지고 싶은 욕망이 꿈틀거렸다.

    그때였다.

    "누구냐!"

    노사부가 갑자기 소리쳤다. 이청풍이 눈을 뜨자, 산장 입구에
    검은 옷을 입은 사내가 서 있었다.
    """
    # 4000자 이상 되도록 반복
    return (base_text * 8).strip()


@pytest.fixture
def sample_hud_wuxia():
    """테스트용 무협 HUD 데이터"""
    return {
        "character": "이청풍",
        "martial_root": 85,
        "internal_energy": 60,
        "lightness": 45,
        "sword_skill": 70,
        "palm_skill": 55,
        "equipment": ["청풍검", "경공화"],
        "techniques": ["청풍검법", "태극장"],
        "injuries": [],
        "relationships": {
            "노사부": {"affinity": 90, "type": "스승"},
            "암흑검": {"affinity": -50, "type": "적"}
        }
    }


@pytest.fixture
def sample_hud_hunter():
    """테스트용 헌터 HUD 데이터"""
    return {
        "character": "김현우",
        "awakening_grade": "A",
        "mana": 8500,
        "strength": 120,
        "agility": 95,
        "skills": ["화염검", "순간이동"],
        "equipment": ["마검 아스트라", "마법갑옷"],
        "guild": "레드드래곤",
        "cleared_gates": ["D급 3개", "C급 2개", "B급 1개"]
    }


@pytest.fixture
def sample_hud_investment():
    """테스트용 투자 HUD 데이터"""
    return {
        "character": "박재현",
        "total_assets": 5000000000,
        "cash": 1000000000,
        "stocks": {
            "삼성전자": {"shares": 10000, "avg_price": 70000},
            "네이버": {"shares": 500, "avg_price": 250000}
        },
        "real_estate": ["강남 아파트", "역삼 빌딩"],
        "connections": {
            "김회장": {"influence": 85, "type": "재벌"},
            "이기자": {"influence": 60, "type": "언론"}
        }
    }


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_api_client():
    """Mock Gemini API 클라이언트"""
    client = MagicMock()

    # 기본 응답 설정
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "status": "success",
        "content": "테스트 응답"
    })

    client.models.generate_content.return_value = mock_response
    return client


@pytest.fixture
def mock_db_manager(temp_dir):
    """Mock DBManager"""
    from modules.core.db_manager import DBManager

    db_path = temp_dir / "test_project.db"
    db = DBManager(db_path)
    yield db
    db.close()


@pytest.fixture
def mock_project_context(temp_dir, sample_bible):
    """Mock ProjectContext"""
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
                config=temp_dir / "config"
            )
            self.paths.drafts.mkdir(exist_ok=True)
            self.paths.memory.mkdir(exist_ok=True)
            self.paths.config.mkdir(exist_ok=True)

            self.bible = sample_bible
            self.ui = MagicMock()
            self.ui.log = MagicMock()

    return MockContext()


# ============================================================
# Validation Fixtures
# ============================================================

@pytest.fixture
def validation_context(sample_blueprint, sample_hud_wuxia):
    """검증용 컨텍스트"""
    return {
        "encyclopedia": {
            "characters": {
                "이청풍": {"alive": True, "location": "청풍산장"},
                "노사부": {"alive": True, "location": "청풍산장"},
                "암흑검": {"alive": True, "location": "불명"}
            },
            "items": {
                "청풍검": {"owner": "이청풍", "destroyed": False},
                "경공화": {"owner": "이청풍", "destroyed": False}
            },
            "locations": {
                "청풍산장": {"destroyed": False},
                "마교 본단": {"destroyed": False}
            }
        },
        "martial_hud": sample_hud_wuxia,
        "blueprint": sample_blueprint,
        "mode": "MANUSCRIPT",
        "history": [],
        "npc_profiles": {}
    }


@pytest.fixture
def blocking_validator_config():
    """BlockingValidator 설정"""
    return {
        "min_length_manuscript": 4000,
        "min_length_blueprint": 500
    }


@pytest.fixture
def scoring_validator_config():
    """ScoringValidator 설정"""
    return {
        "scoring_model": "gemini-2.5-flash",
        "scoring_threshold": 70,
        "use_self_consistency": False,
        "consistency_votes": 3
    }


# ============================================================
# Agent Fixtures
# ============================================================

@pytest.fixture
def agent_config(mock_api_client):
    """에이전트 공통 설정"""
    return {
        "project": MagicMock(),
        "api_client": mock_api_client,
        "martial": MagicMock(),
        "world": MagicMock(),
        "techniques": MagicMock(),
        "guard": MagicMock(),
        "karma": MagicMock(),
        "models": {
            "primary": "gemini-2.5-flash",
            "backup": "gemini-2.0-flash",
            "tier2": "gemini-2.5-pro",
            "tier3": "gemini-3-pro-preview"
        }
    }


# ============================================================
# Helper Functions
# ============================================================

def create_test_db_with_tables(db_path: Path) -> sqlite3.Connection:
    """테스트용 DB 생성 및 테이블 초기화"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # anchors 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anchors (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # blueprints 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blueprints (
            ep_num INTEGER PRIMARY KEY,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # manuscripts 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manuscripts (
            ep_num INTEGER PRIMARY KEY,
            text TEXT,
            hud_snapshot TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn


@pytest.fixture
def initialized_test_db(temp_dir):
    """초기화된 테스트 DB"""
    db_path = temp_dir / "initialized_test.db"
    conn = create_test_db_with_tables(db_path)
    yield conn, db_path
    conn.close()
