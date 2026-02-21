"""SC-2 NPC-aware retrieval tests."""

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
