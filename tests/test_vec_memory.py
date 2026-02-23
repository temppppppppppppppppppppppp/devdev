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


# ── P0-1: distance-first selection ──────────────────────────


class TestMultiQueryDistanceFirst:
    """[OpusTF-P0-1] distance가 낮은(관련도 높은) 결과가 에피소드 번호 순보다 우선 선택된다."""

    def _populate(self, m, count: int = 6) -> None:
        for i in range(1, count + 1):
            m._embed_text = MagicMock(return_value=_make_vec(float(i)))
            m.memorize_v20_episode(i, f"text_{i}", f"요약_{i}", {})

    def test_multi_query_distance_first(self, mem_with_embed):
        """낮은 distance(고관련도) 에피소드가 높은 번호 에피소드보다 우선 선택된다."""
        m = mem_with_embed
        self._populate(m, 6)

        # ep1과 매우 유사한 쿼리 벡터(delta 0.001) → ep1이 distance 최소여야 함
        # ep6과 유사한 쿼리 벡터 → ep6이 distance 최소여야 함
        # 두 쿼리를 날려 ep1, ep6이 모두 선택되는지 확인
        call_count = [0]
        vecs = [_make_similar_vec(1.0, 0.001), _make_similar_vec(6.0, 0.001)]

        def side_effect(text):
            idx = min(call_count[0], len(vecs) - 1)
            call_count[0] += 1
            return vecs[idx]

        m._embed_text = MagicMock(side_effect=side_effect)
        result = m.retrieve_multi_query_context(
            ["q_ep1", "q_ep6"], current_ep=10, max_results=2
        )
        # ep1과 ep6 모두 최상위 관련도 → 둘 다 포함되어야 함
        assert "제 1 화의 기억" in result
        assert "제 6 화의 기억" in result

    def test_distance_ranked_before_episode_order(self, mem_with_embed):
        """동일 쿼리에서 낮은 distance 에피소드(ep1)가 높은 distance 에피소드(ep5)보다 우선."""
        m = mem_with_embed
        self._populate(m, 5)

        # ep1과 매우 유사한 쿼리 → ep1이 distance 최소, ep5가 최대
        m._embed_text = MagicMock(return_value=_make_similar_vec(1.0, 0.001))
        result = m.retrieve_multi_query_context(
            ["q1"], current_ep=10, max_results=1
        )
        # 가장 관련도 높은 ep1이 선택되어야 함
        assert "제 1 화의 기억" in result

    def test_diversity_correction_skips_adjacent_episodes(self, mem_with_embed):
        """연속 에피소드(±1)는 더 먼 것을 제거해 다양성을 보장한다."""
        m = mem_with_embed
        self._populate(m, 6)

        # ep3과 ep4는 연속 — 더 가까운 ep3만 남아야 함
        call_count = [0]
        # ep3과 매우 유사한 벡터 두 번 → ep3, ep4 모두 top에 오지만 ep4는 제거
        vecs = [_make_similar_vec(3.0, 0.001), _make_similar_vec(3.0, 0.001)]

        def side_effect(text):
            idx = min(call_count[0], len(vecs) - 1)
            call_count[0] += 1
            return vecs[idx]

        m._embed_text = MagicMock(side_effect=side_effect)
        result = m.retrieve_multi_query_context(
            ["q1", "q2"], current_ep=10, max_results=5
        )
        # ep3과 ep4가 모두 후보이지만 연속이라 ep4(높은 distance)는 제거됨
        assert "제 3 화의 기억" in result
        # ep4는 ep3과 adjacent(±1)이므로 제거
        assert "제 4 화의 기억" not in result


# ── P0-2: embedding failure keyword SQL fallback ──────────


class TestEmbeddingKeywordFallback:
    """[OpusTF-P0-2] 임베딩 실패 시 빈 문자열 대신 keyword SQL fallback이 작동한다."""

    def _populate_with_keywords(self, m) -> None:
        """키워드가 포함된 요약으로 에피소드 저장."""
        data = [
            (1, "장무기가 구양신공을 익히기 시작했다", "수련,성장", "장무기,구양신공"),
            (2, "조민이 장무기를 배신했다", "배신,갈등", "조민,장무기"),
            (3, "주지약과 장무기가 결혼식을 올렸다", "결혼,의식", "주지약,장무기"),
        ]
        for ep, summary, evt, ent in data:
            m._embed_text = MagicMock(return_value=_make_vec(float(ep)))
            m.memorize_v20_episode(
                ep, f"text_{ep}", summary, {}, event_types=[evt], entity_names=[ent]
            )

    def test_embedding_failure_uses_keyword_fallback(self, mem_with_embed):
        """임베딩 생성 실패 시 빈 문자열 대신 keyword SQL fallback 결과가 반환된다."""
        m = mem_with_embed
        self._populate_with_keywords(m)

        # 임베딩 실패 시뮬레이션
        m._embed_text = MagicMock(return_value=None)

        # 요약에 포함된 키워드로 쿼리
        result = m.retrieve_high_res_context("장무기", current_ep=10, n_results=3)

        # 빈 문자열이 아니라 fallback 결과가 반환되어야 함
        assert result != ""
        assert "키워드" in result  # 키워드 fallback 헤더
        assert "장무기" in result or "화의 기억" in result

    def test_embedding_fallback_returns_empty_on_no_match(self, mem_with_embed):
        """DB에 키워드 매칭 항목이 없으면 fallback도 빈 문자열을 안전하게 반환한다."""
        m = mem_with_embed
        self._populate_with_keywords(m)

        m._embed_text = MagicMock(return_value=None)
        # 존재하지 않는 키워드
        result = m.retrieve_high_res_context("xyzzyqqqnotexist", current_ep=10)
        assert result == ""

    def test_embedding_fallback_empty_query_returns_empty(self, mem_with_embed):
        """키워드 없는 빈 쿼리는 fallback에서 빈 결과를 안전하게 반환한다."""
        m = mem_with_embed
        self._populate_with_keywords(m)

        m._embed_text = MagicMock(return_value=None)
        # 빈 쿼리 — _embed_text도 None 반환, 키워드도 없음
        result = m.retrieve_high_res_context("", current_ep=10)
        assert result == ""

    def test_multi_query_all_embed_fail_uses_fallback(self, mem_with_embed):
        """멀티쿼리에서 모든 임베딩 실패 시 첫 번째 매칭 쿼리의 fallback이 반환된다."""
        m = mem_with_embed
        self._populate_with_keywords(m)

        m._embed_text = MagicMock(return_value=None)
        result = m.retrieve_multi_query_context(
            ["조민", "주지약"], current_ep=10, max_results=3
        )
        # 임베딩 실패 → keyword fallback 동작
        assert result != ""
        assert "화의 기억" in result

    def test_multi_query_all_embed_fail_no_match_returns_empty(self, mem_with_embed):
        """멀티쿼리 임베딩 전량 실패 + 키워드 불일치 → 빈 문자열 반환."""
        m = mem_with_embed
        self._populate_with_keywords(m)

        m._embed_text = MagicMock(return_value=None)
        result = m.retrieve_multi_query_context(
            ["xyzzynotexist1", "xyzzynotexist2"], current_ep=10
        )
        assert result == ""

    def test_keyword_fallback_excludes_future_episodes(self, mem_with_embed):
        """keyword fallback도 current_ep 이상의 에피소드를 제외한다."""
        m = mem_with_embed
        self._populate_with_keywords(m)

        m._embed_text = MagicMock(return_value=None)
        # current_ep=2 → ep2, ep3 제외
        result = m.retrieve_high_res_context("장무기", current_ep=2, n_results=5)
        # ep2, ep3 제외, ep1만 포함 가능
        assert "제 3 화" not in result
        assert "제 2 화" not in result


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


# ── P0-3: 4-slot summary normalization storage ──────────────


class TestSummaryNormalizationStorage:
    """[OpusTF-P0-3] memorize_v20_episode가 전달된 summary를 변형 없이 저장한다.

    4-slot 정규화는 stage4_post_processor._rich_summary 생성 단계에서 이미 완료된다.
    VecMemory는 이를 그대로 episode_meta에 저장해야 한다.
    """

    def test_pipe_separated_summary_stored_verbatim(self, mem_with_embed):
        """파이프 구분자가 포함된 4-slot 요약이 그대로 저장된다."""
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec(1.0))

        four_slot = "사건: 결투 발생 | 인물: 장무기 | 장소: 무당산 | 결말: 적 제압"
        m.memorize_v20_episode(
            ep_num=1,
            text="원고 텍스트",
            summary=four_slot,
            causal_links=[],
        )

        meta = m._load_episode_meta(1)
        assert meta is not None
        assert meta["summary"] == four_slot

    def test_summary_with_all_four_slots_is_retrievable(self, mem_with_embed):
        """4-slot 요약에 포함된 키워드로 keyword fallback 검색이 작동한다."""
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec(1.0))

        four_slot = "사건: 독공 각성 | 인물: 조민, 장무기 | 장소: 비무대 | 결말: 승리"
        m.memorize_v20_episode(ep_num=5, text="원고", summary=four_slot, causal_links=[])

        # 임베딩 실패 → keyword fallback
        m._embed_text = MagicMock(return_value=None)
        result = m.retrieve_high_res_context("조민", current_ep=10, n_results=3)

        assert result != ""
        assert "조민" in result or "화의 기억" in result

    def test_empty_summary_stored_as_empty(self, mem_with_embed):
        """빈 summary는 그대로 빈 문자열로 저장된다."""
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec(2.0))

        m.memorize_v20_episode(ep_num=2, text="원고", summary="", causal_links=[])

        meta = m._load_episode_meta(2)
        assert meta is not None
        assert meta["summary"] == ""

    def test_passthrough_already_formatted_summary(self, mem_with_embed):
        """이미 4-slot 포맷인 summary는 변경 없이 저장된다."""
        m = mem_with_embed
        m._embed_text = MagicMock(return_value=_make_vec(3.0))

        formatted = "사건: 정파 회맹 | 인물: 장무기, 주지약 | 장소: 광명정 | 결말: 동맹 성사"
        m.memorize_v20_episode(ep_num=3, text="원고", summary=formatted, causal_links=[])

        meta = m._load_episode_meta(3)
        assert meta["summary"] == formatted


# ── P0-4: retrieval count config tuning ─────────────────────


class TestRetrievalCountConfig:
    """[P0-4] validation.yaml의 vector_max_results 값이 적정 수준 이상인지 검증.

    _threshold() 싱글톤 캐시 오염을 피하기 위해 YAML 파일을 직접 파싱한다.
    """

    @staticmethod
    def _load_yaml_direct() -> dict:
        """validation.yaml을 직접 로드한다 (cwd 의존성 없음)."""
        from pathlib import Path

        import yaml

        yaml_path = Path(__file__).parent.parent / "config" / "settings" / "validation.yaml"
        with yaml_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_stage4_max_results_at_least_16(self):
        """S4 검색 개수가 16 이상 (P0-4 이후 20)으로 설정되어 있다."""
        data = self._load_yaml_direct()
        val = int(data["context"]["vector_max_results_s4"])
        assert val >= 16, f"vector_max_results_s4={val} < 16 — 검색 개수 너무 낮음"

    def test_stage2_max_results_at_least_12(self):
        """S2 검색 개수가 12 이상 (P0-4 이후 16)으로 설정되어 있다."""
        data = self._load_yaml_direct()
        val = int(data["context"]["vector_max_results_s2"])
        assert val >= 12, f"vector_max_results_s2={val} < 12 — 검색 개수 너무 낮음"

    def test_stage4_max_results_yaml_exceeds_hardcoded_default(self):
        """YAML 설정값이 Python 하드코드 기본값(16)보다 크다 — P0-4 업그레이드 확인."""
        data = self._load_yaml_direct()
        val = int(data["context"]["vector_max_results_s4"])
        # P0-4 이후 YAML은 20, 하드코드 기본값은 16
        assert val > 16, (
            f"vector_max_results_s4={val} — YAML이 하드코드 기본값(16)을 초과해야 함 (P0-4 미적용)"
        )

    def test_stage2_max_results_yaml_exceeds_hardcoded_default(self):
        """YAML 설정값이 Python 하드코드 기본값(12)보다 크다 — P0-4 업그레이드 확인."""
        data = self._load_yaml_direct()
        val = int(data["context"]["vector_max_results_s2"])
        # P0-4 이후 YAML은 16, 하드코드 기본값은 12
        assert val > 12, (
            f"vector_max_results_s2={val} — YAML이 하드코드 기본값(12)을 초과해야 함 (P0-4 미적용)"
        )


class TestDenseBaselineRegression:
    """Phase 0: dense-only 동작 회귀 기준선."""

    def _make_vec(self, db_conn):
        """VecMemory 공유 모드 인스턴스 생성."""
        import threading

        lock = threading.RLock()
        from modules.core.vec_memory import VecMemory

        return VecMemory(conn=db_conn, lock=lock)

    def test_retrieve_high_res_returns_str(self, tmp_path):
        """retrieve_high_res_context()는 항상 str을 반환한다."""
        import sqlite3

        conn = sqlite3.connect(":memory:")
        vm = self._make_vec(conn)
        result = vm.retrieve_high_res_context("test query", current_ep=5)
        assert isinstance(result, str)

    def test_retrieve_multi_query_returns_str(self, tmp_path):
        """retrieve_multi_query_context()는 항상 str을 반환한다."""
        import sqlite3

        conn = sqlite3.connect(":memory:")
        vm = self._make_vec(conn)
        result = vm.retrieve_multi_query_context(
            queries=["query1", "query2"],
            current_ep=5,
            max_results=3,
        )
        assert isinstance(result, str)

    def test_no_memory_returns_empty(self, tmp_path):
        """벡터 데이터 없을 때 빈 문자열 반환."""
        import sqlite3

        conn = sqlite3.connect(":memory:")
        vm = self._make_vec(conn)
        assert vm.retrieve_high_res_context("any query", current_ep=3) == ""
        assert vm.retrieve_multi_query_context(["any"], current_ep=3) == ""


class TestHybridRetrieval:
    """Phase 5: hybrid retrieval 경로 검증."""

    def _make_vm(self):
        import sqlite3
        import threading

        from modules.core.vec_memory import VecMemory

        conn = sqlite3.connect(":memory:")
        vm = VecMemory(conn=conn, lock=threading.RLock())
        return vm, conn

    def test_retrieve_hybrid_returns_str(self):
        """retrieve_hybrid_context()는 항상 str을 반환한다."""
        vm, _ = self._make_vm()
        result = vm.retrieve_hybrid_context("test query", current_ep=5)
        assert isinstance(result, str)

    def test_retrieve_hybrid_empty_db_returns_empty(self):
        """벡터 데이터 없을 때 빈 문자열 반환."""
        vm, _ = self._make_vm()
        assert vm.retrieve_hybrid_context("query", current_ep=3) == ""

    def test_rrf_score_both_ranks(self):
        """RRF 점수: dense+sparse 모두 있으면 각 단독보다 크다."""
        from modules.core.vec_memory import VecMemory

        score_both = VecMemory._rrf_score(0, 0, k=60)
        score_dense_only = VecMemory._rrf_score(0, None, k=60)
        score_sparse_only = VecMemory._rrf_score(None, 0, k=60)
        assert score_both > score_dense_only
        assert score_both > score_sparse_only

    def test_rrf_score_none_rank_excluded(self):
        """RRF 점수: rank None은 해당 항 제외."""
        from modules.core.vec_memory import VecMemory

        score = VecMemory._rrf_score(None, None, k=60)
        assert score == 0.0

    def test_fts_table_exists_after_init(self):
        """VecMemory 초기화 후 episode_fts 테이블이 존재한다."""
        vm, conn = self._make_vm()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','shadow')"
        ).fetchall()
        names = [t[0] for t in tables]
        assert any("episode_fts" in n for n in names), f"episode_fts not in {names}"

    def test_fts_search_empty_db_returns_empty_list(self):
        """FTS 검색: 빈 DB에서 빈 리스트 반환."""
        vm, _ = self._make_vm()
        result = vm._fts_search("이준혁", current_ep=10, n_results=5)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_fts_search_handles_quoted_keyword(self):
        """따옴표가 포함된 쿼리도 FTS 구문 오류 없이 검색된다."""
        vm, conn = self._make_vm()
        conn.execute(
            "INSERT INTO episode_fts(rowid, summary, event_types, entity_names) VALUES (?, ?, ?, ?)",
            (1, "장무기 수련", "수련", "장무기"),
        )
        conn.commit()

        result = vm._fts_search('장무기 "수련"', current_ep=10, n_results=5)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["ep_num"] == 1

    def test_knn_search_raw_arc_bonus_reorders_dense_rank(self):
        """arc bonus 적용 후 dense_rank는 보정된 distance 순서를 반영한다."""
        vm, _ = self._make_vm()

        class _Rows:
            def __init__(self, rows):
                self._rows = rows

            def fetchall(self):
                return self._rows

        class _FakeConn:
            def __init__(self, rows):
                self._rows = rows

            def execute(self, *_args, **_kwargs):
                return _Rows(self._rows)

        # base distance 기준으로는 ep2(0.10)가 먼저지만, ep1은 같은 arc bonus(0.11*0.9)로 역전
        vm._conn = _FakeConn(
            [
                (2, 0.10, "ep2", "", "", 2),
                (1, 0.11, "ep1", "", "", 1),
            ]
        )
        result = vm._knn_search_raw([0.1, 0.2], current_ep=10, n_results=2, current_arc_no=1)

        assert [item["ep_num"] for item in result] == [1, 2]
        assert [item["dense_rank"] for item in result] == [0, 1]

    def test_retrieval_mode_dense_uses_existing_api(self):
        """retrieval_mode=dense일 때 retrieve_hybrid_context가 str을 반환한다."""
        vm, _ = self._make_vm()
        result = vm.retrieve_hybrid_context(
            "query", current_ep=5, dense_k=5, sparse_k=5, max_results=3
        )
        assert isinstance(result, str)
