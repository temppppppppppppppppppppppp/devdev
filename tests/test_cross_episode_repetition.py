"""[Phase 3-B] 크로스 에피소드 반복 감지 테스트.

A. DB 계층 (4건): 테이블 생성, store/get, lookback, 빈 입력
B. Fingerprint (4건): 분리/정규화, min_length, 중복 제거, 포맷
C. Detection (4건): warning, below threshold, empty, keys
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager
from modules.core.repetition_guard import RepetitionGuard
from modules.core.stage4_orchestrator import _detect_cross_episode_repetition

# ══════════════════════════════════════════════════════════════
# A. DB 계층
# ══════════════════════════════════════════════════════════════


class TestSentenceHashDB:
    """episode_sentence_hashes 테이블 CRUD."""

    @pytest.fixture
    def db(self, tmp_path):
        d = DBManager(tmp_path / "test.db")
        yield d
        d.close()

    def test_table_and_index_created(self, db):
        """테이블 + 인덱스 자동 생성 확인."""
        cur = db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='episode_sentence_hashes'")
        assert cur.fetchone() is not None
        cur2 = db.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_episode_sentence_hashes_hash'"
        )
        assert cur2.fetchone() is not None

    def test_store_and_get_roundtrip(self, db):
        """store → get 왕복 확인."""
        hashes = [("abc123", "첫 번째 문장 미리보기"), ("def456", "두 번째 문장")]
        db.store_sentence_hashes(1, hashes)
        result = db.get_sentence_hashes(1)
        assert len(result) == 2
        assert result[0]["sentence_hash"] == "abc123"
        assert result[0]["sentence_preview"] == "첫 번째 문장 미리보기"

    def test_find_repeated_with_lookback(self, db):
        """lookback 범위 내 중복만 반환, 범위 밖은 제외."""
        db.store_sentence_hashes(1, [("hash_a", "문장A")])
        db.store_sentence_hashes(5, [("hash_a", "문장A"), ("hash_b", "문장B")])
        # current_ep=7, lookback=5 → ep 2~6만 포함 → ep5의 hash_a만 매칭
        result = db.find_repeated_sentence_hashes(["hash_a", "hash_b", "hash_c"], current_ep=7, lookback=5)
        # ep1은 lookback 밖(7-5=2), ep5는 범위 내
        ep_nums = [r["episode_number"] for r in result]
        assert 5 in ep_nums
        assert 1 not in ep_nums

    def test_empty_input_safe(self, db):
        """빈 입력 시 크래시 없음."""
        db.store_sentence_hashes(1, [])
        assert db.get_sentence_hashes(1) == []
        assert db.find_repeated_sentence_hashes([], current_ep=2, lookback=5) == []


# ══════════════════════════════════════════════════════════════
# B. Fingerprint
# ══════════════════════════════════════════════════════════════


class TestSentenceFingerprint:
    """RepetitionGuard.extract_sentence_fingerprints 검증."""

    def test_basic_extraction(self):
        """3문장 원고 → 핑거프린트 추출."""
        ms = "이청풍은 검을 높이 들어 창공을 향해 검기를 뿜어냈다. 노사부가 고개를 끄덕였다. 바람이 불어왔다."
        fps = RepetitionGuard.extract_sentence_fingerprints(ms, min_length=10)
        assert len(fps) >= 2
        # 각 원소는 (hash, preview) 튜플
        assert all(len(fp) == 2 for fp in fps)

    def test_min_length_filter(self):
        """min_length 미만 문장 제외."""
        ms = "짧다. 이것은 충분히 긴 문장이라서 통과해야 합니다. 또 짧다."
        fps = RepetitionGuard.extract_sentence_fingerprints(ms, min_length=15)
        # "짧다", "또 짧다" 제외, 긴 문장만 포함
        assert len(fps) == 1
        assert "충분히 긴 문장" in fps[0][1]

    def test_duplicate_sentences_deduplicated(self):
        """동일 문장 반복 시 중복 제거."""
        sent = "이청풍은 검을 높이 들어 창공을 향해 검기를 뿜어냈다"
        ms = f"{sent}. {sent}. {sent}."
        fps = RepetitionGuard.extract_sentence_fingerprints(ms, min_length=10)
        hashes = [h for h, _ in fps]
        assert len(hashes) == len(set(hashes))

    def test_normalization_whitespace(self):
        """공백 차이만 있는 문장 → 동일 해시."""
        s1 = "이청풍은  검을   높이  들어  창공을  향해  검기를  뿜어냈다"
        s2 = "이청풍은 검을 높이 들어 창공을 향해 검기를 뿜어냈다"
        fps1 = RepetitionGuard.extract_sentence_fingerprints(s1, min_length=10)
        fps2 = RepetitionGuard.extract_sentence_fingerprints(s2, min_length=10)
        assert len(fps1) > 0
        assert fps1[0][0] == fps2[0][0]


# ══════════════════════════════════════════════════════════════
# C. Detection (순수 함수)
# ══════════════════════════════════════════════════════════════


class TestCrossEpisodeDetection:
    """_detect_cross_episode_repetition 순수 함수 검증."""

    def _make_fps(self, n=10):
        return [(f"hash_{i}", f"preview_{i}") for i in range(n)]

    def _make_repeated(self, hashes, ep=3):
        return [{"sentence_hash": h, "episode_number": ep, "sentence_preview": f"prev_{h}"} for h in hashes]

    def test_overlap_warning(self):
        """overlap >= warning_threshold → severity='warning'."""
        fps = self._make_fps(20)
        repeated = self._make_repeated(["hash_0", "hash_1", "hash_2"])
        result = _detect_cross_episode_repetition(fps, repeated, warning_threshold=3, regression_threshold=6)
        assert result is not None
        assert result["detected"] is True
        assert result["severity"] == "warning"
        assert result["overlap_count"] == 3

    def test_overlap_regression(self):
        """overlap >= regression_threshold → severity='regression'."""
        fps = self._make_fps(20)
        repeated = self._make_repeated([f"hash_{i}" for i in range(7)])
        result = _detect_cross_episode_repetition(fps, repeated, warning_threshold=3, regression_threshold=6)
        assert result["severity"] == "regression"
        assert result["overlap_count"] == 7

    def test_below_threshold_returns_none(self):
        """overlap < warning_threshold → None."""
        fps = self._make_fps(20)
        repeated = self._make_repeated(["hash_0", "hash_1"])
        result = _detect_cross_episode_repetition(fps, repeated, warning_threshold=3, regression_threshold=6)
        assert result is None

    def test_empty_returns_none(self):
        """빈 입력 → None."""
        assert _detect_cross_episode_repetition([], [], warning_threshold=3) is None
        assert _detect_cross_episode_repetition(self._make_fps(5), [], warning_threshold=3) is None

    def test_result_keys_complete(self):
        """반환 dict에 필수 키 6개 존재."""
        fps = self._make_fps(20)
        repeated = self._make_repeated(["hash_0", "hash_1", "hash_2", "hash_3"])
        result = _detect_cross_episode_repetition(fps, repeated, warning_threshold=3, regression_threshold=6)
        assert result is not None
        expected_keys = {"detected", "severity", "overlap_count", "overlap_ratio", "top_repeated", "warning"}
        assert expected_keys == set(result.keys())
