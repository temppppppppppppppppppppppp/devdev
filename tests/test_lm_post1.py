"""[LM-post-1] Retrospective lookback YAML 연동 + causal_graph Read 연결 테스트."""

import os
import tempfile
from pathlib import Path

import yaml

from modules.core.db_manager import DBManager
from modules.validation.retrospective_validator import RetrospectiveValidator


def test_retrospective_lookback_reads_yaml():
    """validation.yaml retrospective.lookback_episodes가 10 이상인지 확인."""
    val_yaml = Path("config/settings/validation.yaml")
    with open(val_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    lookback = cfg.get("retrospective", {}).get("lookback_episodes", 5)
    assert lookback >= 10, f"lookback_episodes should be >=10, got {lookback}"


def test_validation_orchestrator_uses_retrospective_threshold_key():
    """ValidationOrchestrator가 retrospective.lookback_episodes 키를 사용하는지 확인."""
    src = Path("modules/validation/validation_orchestrator.py").read_text(encoding="utf-8")
    assert '_threshold("retrospective.lookback_episodes", 10)' in src


def test_retrospective_validator_accepts_lookback():
    """RetrospectiveValidator가 lookback_episodes 인자를 self.lookback에 반영하는지 확인."""
    from unittest.mock import MagicMock

    rv = RetrospectiveValidator(MagicMock(), lookback_episodes=10)
    assert rv.lookback == 10


def test_get_recent_causal_links_empty_db():
    """DB에 데이터가 없을 때 빈 리스트 반환."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    db = None
    try:
        db = DBManager(tmpdb)
        result = db.get_recent_causal_links(current_ep=5, lookback=10)
        assert result == [], f"expected [], got {result}"
    finally:
        if db is not None:
            db.close()
        os.unlink(tmpdb)


def test_get_recent_causal_links_returns_data():
    """저장된 causal_links를 정상 반환하는지 확인."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    db = None
    try:
        db = DBManager(tmpdb)
        links = [
            {"cause": "사업 실패", "effect": "자본 급감", "ep": 3},
            {"cause": "신규 투자", "effect": "자본 회복", "ep": 4},
        ]
        db.save_causal_links(links, current_ep=5)
        result = db.get_recent_causal_links(current_ep=6, lookback=5)
        assert len(result) == 2, f"expected 2, got {len(result)}"
        causes = [r.get("cause") for r in result]
        assert "사업 실패" in causes
    finally:
        if db is not None:
            db.close()
        os.unlink(tmpdb)


def test_get_recent_causal_links_range_filter():
    """lookback 범위 밖 링크는 반환하지 않는지 확인."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    db = None
    try:
        db = DBManager(tmpdb)
        old_links = [{"cause": "오래된 사건", "effect": "결과", "ep": 1}]
        new_links = [{"cause": "최근 사건", "effect": "결과", "ep": 10}]
        db.save_causal_links(old_links, current_ep=1)
        db.save_causal_links(new_links, current_ep=10)
        result = db.get_recent_causal_links(current_ep=15, lookback=5)
        causes = [r.get("cause") for r in result]
        assert "최근 사건" in causes
        assert "오래된 사건" not in causes, f"오래된 사건이 포함됨: {result}"
    finally:
        if db is not None:
            db.close()
        os.unlink(tmpdb)


def test_get_recent_causal_links_malformed_json():
    """malformed JSON row는 skip하고 정상 row만 반환."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    db = None
    try:
        db = DBManager(tmpdb)
        db.save_causal_links([{"cause": "정상", "effect": "결과", "ep": 3}], current_ep=3)
        with db._lock:
            db.cursor.execute("INSERT INTO causal_graph (ep_num, data) VALUES (?, ?)", (4, "NOT_JSON{{{"))
            db.conn.commit()
        result = db.get_recent_causal_links(current_ep=10, lookback=10)
        assert len(result) == 1
        assert result[0].get("cause") == "정상"
    finally:
        if db is not None:
            db.close()
        os.unlink(tmpdb)


def test_get_recent_causal_links_default_lookback_covers_30_episodes():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    db = None
    try:
        db = DBManager(tmpdb)
        db.save_causal_links([{"cause": "오래된 사건", "effect": "결과", "ep": 200}], current_ep=200)
        db.save_causal_links([{"cause": "유효 사건", "effect": "결과", "ep": 220}], current_ep=220)
        result = db.get_recent_causal_links(current_ep=250)
        causes = [r.get("cause") for r in result]
        assert "유효 사건" in causes
        assert "오래된 사건" not in causes
    finally:
        if db is not None:
            db.close()
        os.unlink(tmpdb)


def test_get_causal_links_by_entities_filters_target_names():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    db = None
    try:
        db = DBManager(tmpdb)
        db.save_causal_links(
            [
                {"cause": "노사부의 경고", "effect": "진우 각성", "ep": 15},
                {"cause": "상인의 배신", "effect": "시장 붕괴", "ep": 18},
            ],
            current_ep=20,
        )
        result = db.get_causal_links_by_entities(["노사부", "진우"], before_ep=20, lookback=10, limit=5)
        assert len(result) == 1
        assert result[0]["cause"] == "노사부의 경고"
    finally:
        if db is not None:
            db.close()
        os.unlink(tmpdb)
