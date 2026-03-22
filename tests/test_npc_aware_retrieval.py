"""SC-2 NPC-aware retrieval tests."""

from contextlib import nullcontext
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from modules.core.db_manager import DBManager
from modules.core.vec_memory import EMBED_DIM, VecMemory


def _make_vec(seed: float) -> list[float]:
    vec = [0.0] * EMBED_DIM
    vec[0] = seed
    vec[1] = seed * 0.5
    return vec


def _memorize_episode(mem: VecMemory, ep_num: int, seed: float, entity_names: list[str]) -> None:
    mem._embed_text = MagicMock(return_value=_make_vec(seed))
    assert mem.memorize_v20_episode(
        ep_num=ep_num,
        text=f"text_{ep_num}",
        summary=f"summary_{ep_num}",
        causal_links={},
        arc_no=1,
        event_types=["event"],
        entity_names=entity_names,
    )


@pytest.fixture
def vec_mem():
    mem = VecMemory(":memory:", api_key="", ui_log=MagicMock())
    if not mem.is_operational():
        pytest.skip("sqlite-vec is unavailable in this environment")
    yield mem
    mem.close()


@pytest.fixture
def db(tmp_path: Path):
    manager = DBManager(tmp_path / "sc2_test.db")
    yield manager
    manager.close()


def _insert_episode_meta(db: DBManager, ep_num: int, entity_names: str) -> None:
    db.cursor.execute(
        """INSERT OR REPLACE INTO episode_meta
           (ep_num, summary, causal_data, arc_no, event_types, entity_names)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (ep_num, f"summary_{ep_num}", "{}", 1, "event", entity_names),
    )
    db.conn.commit()


class _FetchAllResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)


def _make_stub_memory(
    *,
    entity_rows=None,
    vector_rows=None,
    embed_side_effect=None,
    meta_by_ep=None,
    fallback="",
):
    mem = VecMemory.__new__(VecMemory)
    mem.has_valid_memory = True
    mem._ui_log = MagicMock()
    mem._db_lock = lambda: nullcontext()
    mem._keyword_fallback_search = MagicMock(return_value=fallback)
    mem._load_episode_meta = MagicMock(side_effect=lambda ep_num: (meta_by_ep or {}).get(ep_num))
    mem._embed_text = MagicMock(side_effect=embed_side_effect or [[0.1]])

    remaining_vector_rows = list(vector_rows or [])

    def _execute(sql, _params):
        if "FROM episode_meta" in sql:
            return _FetchAllResult(entity_rows or [])
        if "FROM vec_episodes" in sql:
            rows = remaining_vector_rows.pop(0) if remaining_vector_rows else []
            return _FetchAllResult(rows)
        raise AssertionError(f"Unexpected SQL: {sql}")

    mem._conn = MagicMock()
    mem._conn.execute = MagicMock(side_effect=_execute)
    return mem


class TestVecMemoryNpcAware:
    def test_retrieve_npc_context_entity_match(self, vec_mem: VecMemory):
        _memorize_episode(vec_mem, ep_num=1, seed=1.0, entity_names=["alice", "bob"])
        _memorize_episode(vec_mem, ep_num=2, seed=2.0, entity_names=["carol"])
        _memorize_episode(vec_mem, ep_num=3, seed=3.0, entity_names=["alice"])

        # Force vector path to skip and validate entity_names LIKE path.
        vec_mem._embed_text = MagicMock(return_value=None)
        result = vec_mem.retrieve_npc_context(["alice"], current_ep=4, max_results=5)

        assert "EP3" in result
        assert "EP1" in result
        assert "EP2" not in result

    def test_retrieve_npc_context_vector_fallback_when_entity_not_found(self, vec_mem: VecMemory):
        _memorize_episode(vec_mem, ep_num=1, seed=1.0, entity_names=["nobody"])
        _memorize_episode(vec_mem, ep_num=2, seed=2.0, entity_names=["nobody2"])

        # No entity match for "alice", but vector retrieval should still provide context.
        vec_mem._embed_text = MagicMock(return_value=_make_vec(1.0))
        result = vec_mem.retrieve_npc_context(["alice"], current_ep=3, max_results=2)

        assert result != ""
        assert "EP1" in result

    def test_retrieve_npc_context_empty_names(self, vec_mem: VecMemory):
        assert vec_mem.retrieve_npc_context([], current_ep=10) == ""
        assert vec_mem.retrieve_npc_context(["", "   "], current_ep=10) == ""

    def test_retrieve_npc_context_caps_vector_queries_for_many_npcs(self, vec_mem: VecMemory):
        _memorize_episode(vec_mem, ep_num=1, seed=1.0, entity_names=["npc_01"])
        _memorize_episode(vec_mem, ep_num=2, seed=2.0, entity_names=["npc_02"])
        _memorize_episode(vec_mem, ep_num=3, seed=3.0, entity_names=["npc_03"])

        many_npcs = [f"npc_{i:02d}" for i in range(1, 21)]
        vec_mem._embed_text = MagicMock(return_value=_make_vec(1.0))
        result = vec_mem.retrieve_npc_context(many_npcs, current_ep=10, max_results=3)

        # core(5) + core aggregate(1) + overflow aggregate(1) = 7
        assert vec_mem._embed_text.call_count == 7
        assert result != ""

    def test_retrieve_npc_context_prefers_dual_hits_and_keeps_entity_meta(self):
        mem = _make_stub_memory(
            entity_rows=[
                (30, "entity summary 30", 1, "evt30", "alice,bob"),
                (20, "entity summary 20", 1, "evt20", "bob"),
            ],
            vector_rows=[
                [(30, 0.10), (10, 0.30)],
                [(10, 0.25)],
                [],
            ],
            embed_side_effect=[[0.1], [0.2], [0.3]],
            meta_by_ep={
                30: {"summary": "vector summary 30", "event_types": "vec30", "entity_names": "alice,bob"},
                10: {"summary": "vector summary 10", "event_types": "vec10", "entity_names": "carol"},
            },
        )

        result = mem.retrieve_npc_context([" alice ", "bob"], current_ep=40, max_results=3)
        blocks = result.split("\n\n")

        assert blocks[0].startswith("### [EP30 NPC context similarity 0.90] (entity/vector)")
        assert "summary: entity summary 30" in blocks[0]
        assert "vector summary 30" not in blocks[0]
        assert blocks[1].startswith("### [EP20 NPC context] (entity)")
        assert blocks[2].startswith("### [EP10 NPC context similarity 0.75] (vector)")

    def test_retrieve_npc_context_fallback_uses_cleaned_names_and_bounded_max(self):
        mem = _make_stub_memory(
            entity_rows=[],
            vector_rows=[],
            embed_side_effect=[None],
            fallback="fallback block",
        )

        result = mem.retrieve_npc_context([" alice ", "alice", "   "], current_ep=4, max_results=0)

        assert result == "fallback block"
        mem._keyword_fallback_search.assert_called_once_with("alice", 4, 1)
        mem._conn.execute.assert_called_once()


class TestDBManagerNpcAware:
    def test_get_npc_recent_episodes_basic(self, db: DBManager):
        _insert_episode_meta(db, 1, "alice,bob")
        _insert_episode_meta(db, 2, "carol")
        _insert_episode_meta(db, 3, "alice,dan")
        _insert_episode_meta(db, 4, "alice")

        assert db.get_npc_recent_episodes("alice", before_ep=4, limit=5) == [3, 1]
        assert db.get_npc_recent_episodes("alice", before_ep=10, limit=2) == [4, 3]

    def test_get_npc_recent_episodes_token_boundary(self, db: DBManager):
        _insert_episode_meta(db, 1, "alice,bob")
        _insert_episode_meta(db, 2, "ali,bob")

        assert db.get_npc_recent_episodes("alice", before_ep=10, limit=5) == [1]
        assert db.get_npc_recent_episodes("ali", before_ep=10, limit=5) == [2]

    def test_get_npc_recent_episodes_empty_name(self, db: DBManager):
        _insert_episode_meta(db, 1, "alice,bob")
        assert db.get_npc_recent_episodes("", before_ep=10, limit=5) == []
        assert db.get_npc_recent_episodes("   ", before_ep=10, limit=5) == []


class TestNpcNameEscape:
    """P0-2: LIKE 와일드카드 이스케이프 검증."""

    def test_npc_name_with_percent_escaped(self, vec_mem: VecMemory):
        _memorize_episode(vec_mem, ep_num=1, seed=1.0, entity_names=["alice%bob"])
        _memorize_episode(vec_mem, ep_num=2, seed=2.0, entity_names=["carol"])

        vec_mem._embed_text = MagicMock(return_value=None)
        result = vec_mem.retrieve_npc_context(["alice%bob"], current_ep=3, max_results=5)
        assert "EP1" in result
        assert "EP2" not in result

    def test_npc_name_with_underscore_escaped(self, vec_mem: VecMemory):
        _memorize_episode(vec_mem, ep_num=1, seed=1.0, entity_names=["alice_bob"])
        _memorize_episode(vec_mem, ep_num=2, seed=2.0, entity_names=["aliceXbob"])

        vec_mem._embed_text = MagicMock(return_value=None)
        result = vec_mem.retrieve_npc_context(["alice_bob"], current_ep=3, max_results=5)
        assert "EP1" in result
        # Without ESCAPE, _  would match any char and EP2 would also match
        assert "EP2" not in result
