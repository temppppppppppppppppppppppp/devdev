"""
[Phase2-L2] Evidence Retrieval 테스트
- dead code 버그 수정 (current_ep 키 사용) 검증
- manuscript_excerpt 슬롯 활성화 확인 (ep > 3)
- _fetch_manuscript_snippet 원문 발췌
- manuscripts 없을 때 빈 문자열 안전 반환
"""

import sqlite3
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# ── 헬퍼 ─────────────────────────────────────────────────────────────

def _make_db(tmp_path):
    from modules.core.db_manager import DBManager
    return DBManager(tmp_path / "test.db")


# ── 1. dead code 버그 수정 검증 ───────────────────────────────────────

def test_plan_stage4_retrieval_passes_current_ep(tmp_path):
    """[Phase2-L2] _build_stage4_slots에서 current_ep > 3이면 manuscript_excerpt 슬롯 생성.

    plan_stage4_retrieval의 enabled 상태와 무관하게 슬롯 빌더 로직을 직접 검사.
    """
    from modules.core.context_advisor import ContextAdvisor

    advisor = ContextAdvisor()
    # _build_stage4_slots를 직접 호출하여 YAML 설정 영향 우회
    context_data = {
        "arc_data": {},
        "blueprint": {},
        "prev_ending": "이전 화 엔딩",
        "current_ep": 5,
        "npc_roster": [],
        "genre": "wuxia",
        "is_arc_boundary": False,
        "is_reject_retry": False,
    }
    slots = advisor._build_stage4_slots(context_data)
    slot_names = [s.category for s in slots]
    assert "manuscript_excerpt" in slot_names, (
        f"manuscript_excerpt 슬롯 미생성 (current_ep=5). 슬롯: {slot_names}"
    )


def test_manuscript_excerpt_slot_not_activated_below_ep4(tmp_path):
    """ep <= 3이면 manuscript_excerpt 슬롯 생성 안 됨."""
    from modules.core.context_advisor import ContextAdvisor

    advisor = ContextAdvisor()
    context_data = {
        "arc_data": {},
        "blueprint": {},
        "prev_ending": "이전 화 엔딩",
        "current_ep": 3,
        "npc_roster": [],
        "genre": "wuxia",
        "is_arc_boundary": False,
        "is_reject_retry": False,
    }
    slots = advisor._build_stage4_slots(context_data)
    slot_names = [s.category for s in slots]
    assert "manuscript_excerpt" not in slot_names


# ── 2. _fetch_manuscript_snippet 원문 발췌 ───────────────────────────

def test_fetch_manuscript_snippet_returns_excerpt(tmp_path):
    """manuscripts 테이블에 원고가 있을 때 원문 발췌 반환."""
    from modules.core.vec_memory import VecMemory

    db_path = tmp_path / "vm_test.db"
    # sqlite-vec 없이도 돌아가는 in-memory conn 직접 사용
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS manuscripts (ep_num INTEGER PRIMARY KEY, title TEXT, content TEXT)"
    )
    conn.execute(
        "INSERT INTO manuscripts (ep_num, title, content) VALUES (?, ?, ?)",
        (10, "테스트", "가나다라마바사아자차카타파하" * 50),
    )
    conn.commit()

    vm = VecMemory.__new__(VecMemory)
    vm._conn = conn
    vm._shared_mode = True

    snippet = vm._fetch_manuscript_snippet(10, max_chars=30)
    assert len(snippet) == 30
    assert "가나다라" in snippet


def test_fetch_manuscript_snippet_safe_on_missing(tmp_path):
    """manuscripts 테이블에 ep_num이 없을 때 빈 문자열 반환."""
    from modules.core.vec_memory import VecMemory

    db_path = tmp_path / "vm_test2.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS manuscripts (ep_num INTEGER PRIMARY KEY, title TEXT, content TEXT)"
    )
    conn.commit()

    vm = VecMemory.__new__(VecMemory)
    vm._conn = conn
    vm._shared_mode = True

    snippet = vm._fetch_manuscript_snippet(999)
    assert snippet == ""


def test_fetch_manuscript_snippet_safe_when_no_table(tmp_path):
    """manuscripts 테이블 자체가 없을 때 빈 문자열 반환 (no crash)."""
    from modules.core.vec_memory import VecMemory

    conn = sqlite3.connect(":memory:")

    vm = VecMemory.__new__(VecMemory)
    vm._conn = conn
    vm._shared_mode = True

    snippet = vm._fetch_manuscript_snippet(1)
    assert snippet == ""


def test_fetch_manuscript_snippet_safe_when_no_conn():
    """conn이 None일 때 빈 문자열 반환."""
    from modules.core.vec_memory import VecMemory

    vm = VecMemory.__new__(VecMemory)
    vm._conn = None
    vm._shared_mode = True

    snippet = vm._fetch_manuscript_snippet(1)
    assert snippet == ""


# ── 3. RetrievalSources.MANUSCRIPT_DB 등록 확인 ──────────────────────

def test_retrieval_sources_has_manuscript_db():
    """RetrievalSources에 MANUSCRIPT_DB 상수가 있어야 함."""
    from modules.core.context_advisor import RetrievalSources
    assert hasattr(RetrievalSources, "MANUSCRIPT_DB")
    assert RetrievalSources.MANUSCRIPT_DB == "manuscript_db"
