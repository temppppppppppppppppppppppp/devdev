"""[Phase 4D-1] VecMemory 단위 테스트

sqlite-vec 기반 벡터 메모리 엔진 검증.
임베딩 API는 모킹하여 외부 의존 없이 테스트.
"""

import struct
from unittest.mock import MagicMock, patch

import pytest

from modules.core.vec_memory import EMBED_DIM, VecMemory, _serialize_f32

# ── Helpers ──────────────────────────────────────────────────


def _make_vec(seed: float = 1.0) -> list:
    """테스트용 768차원 벡터 생성 (seed 기반)."""
    v = [0.0] * EMBED_DIM
    v[0] = seed
    v[1] = seed * 0.5
    return v


def _make_similar_vec(seed: float = 1.0, delta: float = 0.01) -> list:
    """seed 벡터와 유사한 벡터."""
    v = _make_vec(seed)
    v[2] = delta
    return v


def _make_distant_vec() -> list:
    """seed=1.0과 거리가 먼 벡터."""
    v = [0.0] * EMBED_DIM
    v[EMBED_DIM - 1] = 1.0
    return v


@pytest.fixture
def mem():
    """in-memory VecMemory — genai 없이."""
    m = VecMemory(":memory:", api_key="", ui_log=MagicMock())
    yield m
    m.close()


@pytest.fixture
def mem_with_embed():
    """in-memory VecMemory — _embed_text 모킹."""
    m = VecMemory(":memory:", api_key="", ui_log=MagicMock())
    yield m
    m.close()


# ── 초기화 ───────────────────────────────────────────────────


class TestInit:
    def test_in_memory_operational(self, mem):
        assert mem.is_operational()
        assert mem.has_valid_memory

    def test_status_fields(self, mem):
        status = mem.get_status()
        assert status["engine"] == "sqlite-vec"
        assert status["has_valid_memory"] is True
        assert status["db_available"] is True
        assert status["episode_count"] == 0
        assert status["initialization_error"] is None

    def test_no_sqlite_vec_graceful(self):
        """sqlite-vec 없으면 비활성화."""
        with patch("modules.core.vec_memory._VEC_AVAILABLE", False):
            m = VecMemory(":memory:", ui_log=MagicMock())
            assert not m.is_operational()
            assert "not installed" in m.initialization_error
            m.close()

    def test_close_cleans_up(self, mem):
        mem.close()
        assert not mem.is_operational()
        assert mem._conn is None


# ── _serialize_f32 ───────────────────────────────────────────


class TestSerialize:
    def test_roundtrip(self):
        original = [1.0, 2.0, 3.0]
        blob = _serialize_f32(original)
        assert isinstance(blob, bytes)
        assert len(blob) == 12  # 3 * 4 bytes
        unpacked = list(struct.unpack("3f", blob))
        assert unpacked == pytest.approx(original)

    def test_embed_dim(self):
        v = _make_vec()
        blob = _serialize_f32(v)
        assert len(blob) == EMBED_DIM * 4


# ── 앵커 저장소 ─────────────────────────────────────────────


class TestAnchors:
    def test_save_load_dict(self, mem):
        data = {"key1": "value1", "nested": {"a": 1}}
        assert mem.save_v20_anchor("test_key", data)
        loaded = mem.load_v20_anchor("test_key")
        assert loaded == data

    def test_save_load_list(self, mem):
        data = [1, 2, 3]
        assert mem.save_v20_anchor("list_key", data)
        assert mem.load_v20_anchor("list_key") == data

    def test_save_load_string(self, mem):
        assert mem.save_v20_anchor("str_key", "hello")
        assert mem.load_v20_anchor("str_key") == "hello"

    def test_overwrite(self, mem):
        mem.save_v20_anchor("k", "v1")
        mem.save_v20_anchor("k", "v2")
        assert mem.load_v20_anchor("k") == "v2"

    def test_missing_key(self, mem):
        assert mem.load_v20_anchor("nonexistent") is None

    def test_save_after_close(self, mem):
        mem.close()
        assert not mem.save_v20_anchor("k", "v")


# ── 에피소드 저장 (직접 벡터 삽입) ──────────────────────────


class TestMemorizeEpisode:
    def test_memorize_with_mock_embed(self, mem_with_embed):
        m = mem_with_embed
        vec = _make_vec(1.0)
        m._embed_text = MagicMock(return_value=vec)

        result = m.memorize_v20_episode(
            ep_num=1,
            text="테스트 원고 텍스트",
            summary="테스트 요약",
            causal_links={"cause": "effect"},
            arc_no=1,
            event_types=["전투", "각성"],
            entity_names=["장무기", "조민"],
        )
        assert result is True
        m._embed_text.assert_called_once()

        # 메타데이터 확인
        status = m.get_status()
        assert status["episode_count"] == 1

    def test_memorize_upsert(self, mem_with_embed):
        """같은 ep_num 재저장 시 덮어쓰기."""
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec(1.0))

        m.memorize_v20_episode(1, "text1", "summary1", {})
        m._embed_text.return_value = _make_vec(2.0)
        m.memorize_v20_episode(1, "text2", "summary2", {})

        assert m.get_status()["episode_count"] == 1

    def test_memorize_embed_fail(self, mem_with_embed):
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=None)
        result = m.memorize_v20_episode(1, "text", "summary", {})
        assert result is False

    def test_memorize_not_operational(self):
        with patch("modules.core.vec_memory._VEC_AVAILABLE", False):
            m = VecMemory(":memory:", ui_log=MagicMock())
            m._embed_text = MagicMock(return_value=_make_vec())
            assert m.memorize_v20_episode(1, "text", "sum", {}) is False
            m.close()

    def test_sync_status_updated(self, mem_with_embed):
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec())
        m.memorize_v20_episode(5, "text", "sum", {})
        assert m.get_sync_status(5) == 1
        assert m.get_sync_status(99) == 0


# ── KNN 검색 ────────────────────────────────────────────────


class TestKNNSearch:
    def _populate(self, m, count=5):
        """ep 1~count 삽입."""
        for i in range(1, count + 1):
            vec = _make_vec(float(i))
            m._embed_text = MagicMock(return_value=vec)
            m.memorize_v20_episode(i, f"text_{i}", f"요약_{i}", {}, arc_no=1)

    def test_retrieve_high_res_context(self, mem_with_embed):
        m = mem_with_embed
        self._populate(m, 5)

        # 쿼리: ep1과 유사한 벡터 → ep1 반환 기대
        m._embed_text = MagicMock(return_value=_make_similar_vec(1.0))
        result = m.retrieve_high_res_context("query", current_ep=5, n_results=2)
        assert "제 1 화의 기억" in result
        assert "요약_1" in result

    def test_retrieve_excludes_future(self, mem_with_embed):
        m = mem_with_embed
        self._populate(m, 5)

        # current_ep=3 → ep3, ep4, ep5 제외
        m._embed_text = MagicMock(return_value=_make_vec(5.0))
        result = m.retrieve_high_res_context("query", current_ep=3, n_results=10)
        assert "제 3 화" not in result
        assert "제 4 화" not in result
        assert "제 5 화" not in result

    def test_retrieve_empty_db(self, mem_with_embed):
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec())
        result = m.retrieve_high_res_context("query", current_ep=1)
        assert result == ""

    def test_retrieve_embed_fail(self, mem_with_embed):
        m = mem_with_embed
        self._populate(m, 3)
        m._embed_text = MagicMock(return_value=None)
        result = m.retrieve_high_res_context("query", current_ep=5)
        assert result == ""

    def test_retrieve_not_operational(self):
        with patch("modules.core.vec_memory._VEC_AVAILABLE", False):
            m = VecMemory(":memory:", ui_log=MagicMock())
            assert m.retrieve_high_res_context("q", 5) == ""
            m.close()


class TestMultiQuerySearch:
    def _populate(self, m, count=5):
        for i in range(1, count + 1):
            m._embed_text = MagicMock(return_value=_make_vec(float(i)))
            m.memorize_v20_episode(i, f"text_{i}", f"요약_{i}", {})

    def test_multi_query_basic(self, mem_with_embed):
        m = mem_with_embed
        self._populate(m, 5)

        call_count = [0]
        vecs = [_make_similar_vec(1.0), _make_similar_vec(3.0)]

        def side_effect(text):
            idx = min(call_count[0], len(vecs) - 1)
            call_count[0] += 1
            return vecs[idx]

        m._embed_text = MagicMock(side_effect=side_effect)
        result = m.retrieve_multi_query_context(["q1", "q2"], current_ep=5, max_results=3)
        assert "화의 기억" in result

    def test_multi_query_empty(self, mem_with_embed):
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec())
        assert m.retrieve_multi_query_context([], current_ep=5) == ""

    def test_multi_query_skips_blank(self, mem_with_embed):
        m = mem_with_embed
        self._populate(m, 3)
        m._embed_text = MagicMock(return_value=_make_vec(1.0))
        result = m.retrieve_multi_query_context(["", None, "valid"], current_ep=5)
        # None and "" should be skipped, only "valid" processed
        assert m._embed_text.call_count == 1


# ── 동기화 상태 ─────────────────────────────────────────────


class TestSyncStatus:
    def test_initial_status_zero(self, mem):
        assert mem.get_sync_status(1) == 0

    def test_status_after_memorize(self, mem):
        mem._embed_text = MagicMock(return_value=_make_vec())
        mem.memorize_v20_episode(1, "text", "sum", {})
        assert mem.get_sync_status(1) == 1

    def test_status_closed(self, mem):
        mem.close()
        assert mem.get_sync_status(1) == 0


# ── sync_v20_drafts ─────────────────────────────────────────


class TestSyncDrafts:
    def test_sync_skips_when_not_operational(self):
        with patch("modules.core.vec_memory._VEC_AVAILABLE", False):
            m = VecMemory(":memory:", ui_log=MagicMock())
            m.sync_v20_drafts()  # should not raise
            m.close()

    def test_sync_skips_none_path(self, mem):
        mem.sync_v20_drafts(drafts_path=None)  # should not raise

    def test_sync_with_mock_files(self, mem, tmp_path):
        """임시 파일로 동기화 테스트."""
        mem._embed_text = MagicMock(return_value=_make_vec())

        # 테스트 파일 생성
        (tmp_path / "0001_test.txt").write_text("에피소드 1 내용", encoding="utf-8")
        (tmp_path / "0002_test.txt").write_text("에피소드 2 내용", encoding="utf-8")
        (tmp_path / "readme.txt").write_text("비에피소드", encoding="utf-8")

        mem.sync_v20_drafts(drafts_path=tmp_path)

        assert mem.get_sync_status(1) == 1
        assert mem.get_sync_status(2) == 1
        assert mem._embed_text.call_count == 2  # readme 스킵

    def test_sync_skips_already_synced(self, mem, tmp_path):
        mem._embed_text = MagicMock(return_value=_make_vec())
        (tmp_path / "0001_test.txt").write_text("text", encoding="utf-8")

        mem.sync_v20_drafts(drafts_path=tmp_path)
        call_count_1 = mem._embed_text.call_count

        mem.sync_v20_drafts(drafts_path=tmp_path)  # 2nd call
        assert mem._embed_text.call_count == call_count_1  # no new embeds

    def test_sync_force_repair(self, mem, tmp_path):
        mem._embed_text = MagicMock(return_value=_make_vec())
        (tmp_path / "0001_test.txt").write_text("text", encoding="utf-8")

        mem.sync_v20_drafts(drafts_path=tmp_path)
        call_count_1 = mem._embed_text.call_count

        mem.sync_v20_drafts(drafts_path=tmp_path, force_repair=True)
        assert mem._embed_text.call_count > call_count_1


# ── LongTermMemory 인터페이스 호환 ──────────────────────────


class TestInterfaceCompat:
    """VecMemory가 LongTermMemory의 공개 인터페이스를 모두 제공하는지 검증."""

    REQUIRED_METHODS = [
        "retrieve_high_res_context",
        "retrieve_multi_query_context",
        "memorize_v20_episode",
        "sync_v20_drafts",
        "is_operational",
        "save_v20_anchor",
        "load_v20_anchor",
        "get_status",
        "close",
        "ui_log",
    ]

    def test_all_methods_exist(self, mem):
        for method_name in self.REQUIRED_METHODS:
            assert hasattr(mem, method_name), f"Missing method: {method_name}"
            assert callable(getattr(mem, method_name)), f"Not callable: {method_name}"

    def test_has_valid_memory_attr(self, mem):
        assert hasattr(mem, "has_valid_memory")

    def test_initialization_error_attr(self, mem):
        assert hasattr(mem, "initialization_error")
