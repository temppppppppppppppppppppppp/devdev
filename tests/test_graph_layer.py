"""[Graph-Layer] npc_relationship_edges + arc_dependencies 테이블 round-trip 테스트."""

from unittest.mock import MagicMock

import pytest

from modules.core.db_manager import DBManager
from modules.domain.agents.state_tracker import StateTracker
from modules.domain.agents.state_tracker_npc import StateTrackerNPC


@pytest.fixture
def db(tmp_path):
    d = DBManager(tmp_path / "test.db")
    try:
        yield d
    finally:
        d.close()


# ─── npc_relationship_edges ──────────────────────────────────────────────────

def test_upsert_and_get_npc_relationship_edge(db):
    db.upsert_npc_relationship_edge("알파", "베타", "동맹", arc_no=1, ep_no=5)
    edges = db.get_npc_relationship_edges()
    assert len(edges) == 1
    e = edges[0]
    assert e["relation"] == "동맹"
    assert e["arc_no"] == 1
    assert e["updated_ep"] == 5


def test_npc_relationship_edge_sorted_key(db):
    """npc1/npc2 정렬 보장 — 입력 순서와 무관하게 동일 row."""
    db.upsert_npc_relationship_edge("Z", "A", "적대", arc_no=2, ep_no=3)
    edges = db.get_npc_relationship_edges()
    assert len(edges) == 1
    # 정렬 순서: A < Z
    assert edges[0]["npc1"] == "A"
    assert edges[0]["npc2"] == "Z"

    # 역순 입력해도 같은 row 갱신
    db.upsert_npc_relationship_edge("A", "Z", "우호", arc_no=3, ep_no=10)
    edges2 = db.get_npc_relationship_edges()
    assert len(edges2) == 1
    assert edges2[0]["relation"] == "우호"


def test_get_npc_relationship_edges_filter_by_npc(db):
    db.upsert_npc_relationship_edge("홍길동", "이순신", "동맹", arc_no=1, ep_no=1)
    db.upsert_npc_relationship_edge("홍길동", "임꺽정", "적대", arc_no=1, ep_no=2)
    db.upsert_npc_relationship_edge("이순신", "임꺽정", "중립", arc_no=1, ep_no=3)

    result = db.get_npc_relationship_edges(npc_name="홍길동")
    assert len(result) == 2
    npcs_in_result = {(r["npc1"], r["npc2"]) for r in result}
    assert any("홍길동" in pair for pair in npcs_in_result)


# ─── arc_dependencies ────────────────────────────────────────────────────────

def test_upsert_and_get_arc_dependency(db):
    db.upsert_arc_dependency(1, 2, "causes", "1Arc→2Arc 인과")
    deps = db.get_arc_dependencies(1)
    assert len(deps) == 1
    d = deps[0]
    assert d["from_arc_no"] == 1
    assert d["to_arc_no"] == 2
    assert d["dep_type"] == "causes"
    assert "인과" in d["description"]


def test_arc_dependency_upsert_overwrites(db):
    """ON CONFLICT — dep_type 갱신."""
    db.upsert_arc_dependency(2, 3, "causes", "초기")
    db.upsert_arc_dependency(2, 3, "requires", "갱신")
    deps = db.get_arc_dependencies(2)
    assert len(deps) == 1
    assert deps[0]["dep_type"] == "requires"
    assert deps[0]["description"] == "갱신"


def test_get_arc_dependencies_bidirectional(db):
    """arc_no가 from이든 to든 모두 조회."""
    db.upsert_arc_dependency(1, 5, "causes", "")
    db.upsert_arc_dependency(5, 9, "causes", "")

    deps_5 = db.get_arc_dependencies(5)
    assert len(deps_5) == 2
    arc_pairs = {(d["from_arc_no"], d["to_arc_no"]) for d in deps_5}
    assert (1, 5) in arc_pairs
    assert (5, 9) in arc_pairs


# ─── G3: write path 종단 테스트 ──────────────────────────────────────────────

def test_register_npc_npc_relationship_writes_to_db(tmp_path):
    """G3-1: _db 수정 후 write path 종단(end-to-end) 확인."""
    real_db = DBManager(tmp_path / "test.db")
    try:
        tracker = StateTracker()
        tracker.bind_db(real_db)
        npc_mod = StateTrackerNPC(tracker)
        npc_mod.register_npc_npc_relationship("캐릭A", "캐릭B", "동맹", arc_no=1)
        edges = real_db.get_npc_relationship_edges()
        assert len(edges) == 1
        assert edges[0]["relation"] == "동맹"
    finally:
        real_db.close()


def test_register_npc_npc_relationship_no_db_does_not_raise():
    """G3-2: bind_db 미호출 시 예외 없이 메모리에만 저장."""
    tracker = StateTracker()
    npc_mod = StateTrackerNPC(tracker)
    npc_mod.register_npc_npc_relationship("A", "B", "적대", 1)
    key = tuple(sorted(["A", "B"]))
    assert key in tracker.npc_npc_relationships


def test_stage4_causal_links_dual_write_called(tmp_path):
    """G3-3: causal_links → causal_graph dual-write 경로 확인."""
    db = DBManager(tmp_path / "test.db")
    try:
        db.save_causal_links_mock = MagicMock(wraps=db.save_causal_links)
        causal_links = [{"cause": "A", "effect": "B", "ep_no": 5}]
        ep_num = 5
        # dual-write 로직 직접 실행
        import logging
        if causal_links:
            try:
                db.save_causal_links(causal_links, ep_num)
            except Exception as _cg_err:
                logging.debug("[Stage4] causal_graph dual-write 실패 (비치명): %s", _cg_err)
        # DB에 실제로 저장됐는지 확인
        rows = db.conn.execute("SELECT * FROM causal_graph").fetchall()
        assert len(rows) >= 1
    finally:
        db.close()
