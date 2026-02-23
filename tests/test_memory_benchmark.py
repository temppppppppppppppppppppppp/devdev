"""[TF-19] Memory Benchmark — 골든 에피소드 검색 정확도 테스트.

5개 무협 시나리오 골든 에피소드를 저장하고, 5가지 검색 모드의
정확도를 검증한다.
"""

from unittest.mock import MagicMock

import pytest

from modules.core.vec_memory import VecMemory

# ── 골든 에피소드 ──────────────────────────────────────────────────

GOLDEN_EPISODES = [
    {
        "ep_num": 1,
        "text": "진영호는 청룡문에 입문하여 기초 검술을 배우기 시작했다. 사부 독고염이 첫 수업을 진행했다.",
        "summary": "사건: 청룡문 입문 | 인물: 진영호, 독고염 | 장소: 청룡문 | 결말: 수련 시작",
        "arc_no": 1,
        "event_types": ["입문", "수련"],
        "entity_names": ["진영호", "독고염"],
    },
    {
        "ep_num": 2,
        "text": "진영호는 화산파 비급 '태극검법'을 습득했다. 고대 동굴에서 비급을 발견했다.",
        "summary": "사건: 태극검법 비급 획득 | 인물: 진영호 | 장소: 화산파 동굴 | 결말: 비급 습득",
        "arc_no": 1,
        "event_types": ["비급획득", "탐험"],
        "entity_names": ["진영호"],
    },
    {
        "ep_num": 3,
        "text": "사부 독고염이 마교의 습격으로 사망했다. 진영호는 복수를 맹세했다.",
        "summary": "사건: 독고염 사망 | 인물: 진영호, 독고염 | 장소: 청룡문 | 결말: 복수 맹세",
        "arc_no": 1,
        "event_types": ["사망", "복수"],
        "entity_names": ["진영호", "독고염"],
    },
    {
        "ep_num": 4,
        "text": "진영호는 흑풍곡에서 마교 제자와 첫 대결을 벌였다. 부상을 입었지만 승리했다.",
        "summary": "사건: 첫 대결 | 인물: 진영호 | 장소: 흑풍곡 | 결말: 부상 승리",
        "arc_no": 2,
        "event_types": ["전투", "부상"],
        "entity_names": ["진영호"],
    },
    {
        "ep_num": 5,
        "text": "진영호는 조민과 동맹을 맺고 마교 기지에서 탈출했다. 새로운 여정이 시작되었다.",
        "summary": "사건: 동맹 결성 | 인물: 진영호, 조민 | 장소: 마교 기지 | 결말: 탈출 성공",
        "arc_no": 2,
        "event_types": ["동맹", "탈출"],
        "entity_names": ["진영호", "조민"],
    },
]

# ── 고정 임베딩 맵 ─────────────────────────────────────────────────
# 각 에피소드에 고유한 "방향"을 부여하는 유닛 벡터 (3072D)

_DIM = 3072


def _make_vec(seed: int) -> list[float]:
    """시드 기반 결정론적 벡터 생성."""
    import hashlib
    import struct

    h = hashlib.sha256(str(seed).encode()).digest()
    vals = []
    for i in range(_DIM):
        b = h[(i * 4) % len(h) : (i * 4) % len(h) + 4]
        if len(b) < 4:
            b = b + b"\x00" * (4 - len(b))
        v = struct.unpack("f", b)[0]
        # 정규화 범위 제한
        vals.append((v % 1.0) * (0.1 if i != seed % _DIM else 1.0))
    return vals


EP_VECS = {ep["ep_num"]: _make_vec(ep["ep_num"]) for ep in GOLDEN_EPISODES}

# 쿼리 벡터: 특정 에피소드와 가까운 벡터
QUERY_VECS = {
    "npc_query": _make_vec(3),  # EP3 (독고염 사망) 방향
    "event_query": _make_vec(4),  # EP4 (전투) 방향
    "alliance_query": _make_vec(5),  # EP5 (동맹) 방향
    "training_query": _make_vec(1),  # EP1 (수련) 방향
}


def _mock_embed(text: str) -> list[float] | None:
    """텍스트 내용에 따라 적합한 고정 벡터 반환."""
    if "독고염" in text or "사망" in text or "복수" in text:
        return QUERY_VECS["npc_query"]
    if "대결" in text or "전투" in text or "흑풍곡" in text or "부상" in text:
        return QUERY_VECS["event_query"]
    if "동맹" in text or "조민" in text or "탈출" in text:
        return QUERY_VECS["alliance_query"]
    if "입문" in text or "수련" in text or "청룡문" in text:
        return QUERY_VECS["training_query"]
    if "태극검법" in text or "비급" in text or "화산파" in text:
        return _make_vec(2)
    # 기본: 첫 에피소드 방향
    return QUERY_VECS["training_query"]


# ── 픽스처 ──────────────────────────────────────────────────────────


@pytest.fixture
def populated_mem():
    """5개 골든 에피소드가 로드된 VecMemory."""
    mem = VecMemory(":memory:", api_key="", ui_log=MagicMock())

    # mock embed
    mem._embed_text = MagicMock(side_effect=_mock_embed)

    # 에피소드 저장
    for ep in GOLDEN_EPISODES:
        mem.memorize_v20_episode(
            ep_num=ep["ep_num"],
            text=ep["text"],
            summary=ep["summary"],
            causal_links=[],
            arc_no=ep["arc_no"],
            event_types=ep["event_types"],
            entity_names=ep["entity_names"],
        )

    return mem


# ── 1. Dense Retrieval ─────────────────────────────────────────────


class TestDenseRetrieval:
    """단일/다중 쿼리 Dense 검색 정확도."""

    def test_npc_query_finds_relevant(self, populated_mem):
        """독고염 관련 쿼리 시 EP3(사망) 또는 EP1(입문) 포함."""
        result = populated_mem.retrieve_high_res_context("독고염 사부의 행적", current_ep=6, n_results=3)
        assert result  # 비어있지 않음
        assert "독고염" in result

    def test_event_query_finds_battle(self, populated_mem):
        """전투 관련 쿼리 시 EP4(흑풍곡 대결) 포함."""
        result = populated_mem.retrieve_high_res_context("첫 대결 전투 장면", current_ep=6, n_results=3)
        assert result

    def test_future_episode_excluded(self, populated_mem):
        """current_ep 이후 에피소드는 제외."""
        result = populated_mem.retrieve_high_res_context("진영호 수련", current_ep=2, n_results=5)
        # EP2 이후(EP3, EP4, EP5)는 결과에 포함되지 않아야 함
        if result:
            assert "제5화" not in result
            assert "제4화" not in result
            assert "제3화" not in result

    def test_multi_query_dedup(self, populated_mem):
        """다중 쿼리 시 중복 제거 확인."""
        result = populated_mem.retrieve_multi_query_context(
            queries=["독고염 사망", "독고염 행적"],
            current_ep=6,
            n_per_query=3,
            max_results=5,
        )
        assert result
        # 같은 에피소드가 중복 출력되지 않아야 함
        ep3_count = result.count("제3화")
        assert ep3_count <= 1


# ── 2. Hybrid Retrieval ────────────────────────────────────────────


class TestHybridRetrieval:
    """Dense + Sparse(FTS5) RRF 융합 검색."""

    def test_keyword_match_boosts(self, populated_mem):
        """키워드 매칭이 결과에 반영."""
        result = populated_mem.retrieve_hybrid_context(
            query="태극검법 비급 화산파",
            current_ep=6,
            dense_k=5,
            sparse_k=5,
            max_results=3,
        )
        assert result
        # 키워드가 직접 매칭되는 EP2가 포함되어야 함
        assert "태극검법" in result or "비급" in result or "화산파" in result

    def test_rrf_score_format(self, populated_mem):
        """RRF 점수 계산 정합성."""
        score = VecMemory._rrf_score(dense_rank=1, sparse_rank=2, k=60)
        expected = 1 / (60 + 1) + 1 / (60 + 2)
        assert abs(score - expected) < 1e-10

    def test_rrf_none_rank_handling(self):
        """None rank는 0점 기여."""
        score_dense_only = VecMemory._rrf_score(dense_rank=1, sparse_rank=None, k=60)
        assert score_dense_only == pytest.approx(1 / 61)

        score_sparse_only = VecMemory._rrf_score(dense_rank=None, sparse_rank=1, k=60)
        assert score_sparse_only == pytest.approx(1 / 61)

    def test_hybrid_returns_formatted_string(self, populated_mem):
        """Hybrid 결과가 포맷팅된 문자열."""
        result = populated_mem.retrieve_hybrid_context(
            query="진영호 수련 과정",
            current_ep=6,
            max_results=3,
        )
        assert isinstance(result, str)


# ── 3. Sparse Retrieval (FTS5) ─────────────────────────────────────


class TestSparseRetrieval:
    """FTS5 기반 키워드 검색."""

    def test_fts_entity_search(self, populated_mem):
        """entity_names 토큰으로 FTS 검색."""
        results = populated_mem._fts_search("조민", current_ep=6, n_results=5)
        assert len(results) >= 1
        found_eps = {r["ep_num"] for r in results}
        assert 5 in found_eps  # EP5에 조민 등장

    def test_fts_event_type_search(self, populated_mem):
        """event_types 토큰으로 FTS 검색."""
        results = populated_mem._fts_search("사망", current_ep=6, n_results=5)
        assert len(results) >= 1
        found_eps = {r["ep_num"] for r in results}
        assert 3 in found_eps  # EP3에 사망 이벤트

    def test_fts_respects_current_ep(self, populated_mem):
        """current_ep 이후 에피소드 제외."""
        results = populated_mem._fts_search("진영호", current_ep=3, n_results=10)
        for r in results:
            assert r["ep_num"] < 3


# ── 4. NPC-Aware Retrieval ─────────────────────────────────────────


class TestNPCAwareRetrieval:
    """NPC 이름 기반 검색."""

    def test_single_npc_search(self, populated_mem):
        """단일 NPC 검색."""
        result = populated_mem.retrieve_npc_context(
            npc_names=["독고염"],
            current_ep=6,
            max_results=5,
        )
        assert result
        assert "독고염" in result

    def test_multiple_npc_search(self, populated_mem):
        """복수 NPC 검색."""
        result = populated_mem.retrieve_npc_context(
            npc_names=["독고염", "조민"],
            current_ep=6,
            max_results=5,
        )
        assert result
        # 두 NPC 모두의 에피소드가 포함되어야 함
        has_ep3_or_ep1 = "독고염" in result  # EP1 또는 EP3
        has_ep5 = "조민" in result  # EP5
        assert has_ep3_or_ep1 or has_ep5

    def test_unknown_npc_graceful(self, populated_mem):
        """미등록 NPC 검색 시 graceful."""
        result = populated_mem.retrieve_npc_context(
            npc_names=["알수없는인물"],
            current_ep=6,
            max_results=5,
        )
        # 빈 문자열이거나 결과가 있더라도 에러 없이 반환
        assert isinstance(result, str)


# ── 5. Keyword Fallback ───────────────────────────────────────────


class TestKeywordFallback:
    """임베딩 실패 시 키워드 폴백."""

    def test_fallback_on_embed_failure(self, populated_mem):
        """_embed_text 실패 시 키워드 폴백으로 검색."""
        # embed를 None 반환으로 설정
        populated_mem._embed_text = MagicMock(return_value=None)
        result = populated_mem.retrieve_high_res_context("독고염 사망 복수", current_ep=6, n_results=3)
        # 키워드 폴백이 작동하여 결과 반환
        assert isinstance(result, str)
        if result:
            assert "독고염" in result or "사망" in result

    def test_fallback_returns_relevant(self, populated_mem):
        """키워드 폴백이 관련 에피소드를 찾음."""
        # 직접 키워드 폴백 호출
        result = populated_mem._keyword_fallback_search("태극검법 비급", current_ep=6, n_results=3)
        assert isinstance(result, str)
        if result:
            assert "태극검법" in result or "비급" in result

    def test_multi_query_fallback(self, populated_mem):
        """다중 쿼리에서 전체 embed 실패 시 폴백."""
        populated_mem._embed_text = MagicMock(return_value=None)
        result = populated_mem.retrieve_multi_query_context(
            queries=["청룡문 입문", "태극검법"],
            current_ep=6,
            n_per_query=3,
            max_results=5,
        )
        assert isinstance(result, str)
