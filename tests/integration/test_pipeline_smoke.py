"""E2E Smoke Tests — Stage2/4 파이프라인 핵심 흐름 검증

최근 변경 사항 대상:
- D1 Hybrid Retrieval (FTS5+RRF) — vec_memory.py
- DB 효율화 — character_voice/foreshadow DB 전환, episode_fts 테이블
- D2 Memory Observability — 경로별 logging
- TF-7/7R — 다수 컴포넌트 패치

Smoke Test 범위 (LLM 모킹 필수, 실제 API 호출 없음):
1. DB 초기화 + VecMemory 공유 모드
2. memorize + retrieve 흐름
3. character_voice + foreshadow DB 저장/로드
4. Stage2Context DI 슬롯 초기화
5. Stage4Context DI 슬롯 초기화
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.character_voice import CharacterVoiceTracker, VoiceStyle
from modules.core.db_manager import DBManager
from modules.core.foreshadow_tracker import ForeshadowCategory, ForeshadowTracker
from modules.core.stage2_context import Stage2Context
from modules.core.stage4_context import Stage4Context
from modules.core.vec_memory import EMBED_DIM, VecMemory

# ── 공통 헬퍼 ────────────────────────────────────────────────


def _make_vec(seed: float = 1.0) -> list:
    """테스트용 EMBED_DIM 차원 벡터 생성."""
    v = [0.0] * EMBED_DIM
    v[0] = seed
    v[1] = seed * 0.5
    return v


# ══════════════════════════════════════════════════════════════
# Smoke Test 1: DB 초기화 + VecMemory 공유 모드
# ══════════════════════════════════════════════════════════════


class TestDBInitAndVecMemorySharedMode:
    """DBManager 생성 시 필요 테이블이 모두 만들어지고,
    VecMemory shared 모드가 정상 초기화됨을 검증."""

    def test_db_creates_character_voice_table(self, tmp_path):
        """[DB-Eff-P1] character_voice 테이블 존재 확인."""
        db = DBManager(tmp_path / "smoke.db")
        try:
            cursor = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='character_voice'"
            )
            row = cursor.fetchone()
            assert row is not None, "character_voice 테이블이 생성되지 않았습니다"
        finally:
            db.close()

    def test_db_creates_foreshadow_table(self, tmp_path):
        """[DB-Eff-P1] foreshadow 테이블 존재 확인."""
        db = DBManager(tmp_path / "smoke.db")
        try:
            cursor = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='foreshadow'"
            )
            row = cursor.fetchone()
            assert row is not None, "foreshadow 테이블이 생성되지 않았습니다"
        finally:
            db.close()

    def test_db_creates_episode_fts_table(self, tmp_path):
        """[Hybrid-P2] episode_fts 가상 테이블 존재 확인."""
        db = DBManager(tmp_path / "smoke.db")
        try:
            cursor = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE (type='table' OR type='shadow') AND name='episode_fts'"
            )
            row = cursor.fetchone()
            assert row is not None, "episode_fts 테이블이 생성되지 않았습니다"
        finally:
            db.close()

    def test_db_creates_episode_meta_table(self, tmp_path):
        """episode_meta 테이블 존재 확인."""
        db = DBManager(tmp_path / "smoke.db")
        try:
            cursor = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='episode_meta'"
            )
            row = cursor.fetchone()
            assert row is not None, "episode_meta 테이블이 생성되지 않았습니다"
        finally:
            db.close()

    def test_vec_memory_shared_mode_init(self, tmp_path):
        """VecMemory shared 모드: DBManager 커넥션 공유 → 초기화 상태 확인."""
        db = DBManager(tmp_path / "smoke.db")
        try:
            mem = VecMemory(
                conn=db.conn,
                lock=db._lock,
                ui_log=lambda msg: None,
            )
            # shared 모드에서는 has_valid_memory 또는 initialization_error 중 하나는 존재
            assert isinstance(mem.has_valid_memory, bool)
            # initialization_error는 None이거나 str이어야 함
            assert mem.initialization_error is None or isinstance(mem.initialization_error, str)
        finally:
            db.close()

    def test_vec_memory_episode_fts_accessible(self, tmp_path):
        """shared 모드에서 episode_fts 테이블 접근 가능 확인."""
        db = DBManager(tmp_path / "smoke.db")
        try:
            # episode_fts에 직접 조회
            count_row = db.conn.execute("SELECT COUNT(*) FROM episode_fts").fetchone()
            assert count_row is not None
            assert count_row[0] == 0  # 초기 상태 빈 테이블
        finally:
            db.close()

    def test_vec_memory_shared_mode_backfills_episode_fts_from_meta(self, tmp_path):
        """shared 모드 초기화 시 episode_meta 기반으로 episode_fts 누락 행을 백필한다."""
        db = DBManager(tmp_path / "smoke.db")
        try:
            has_vec = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_episodes'"
            ).fetchone()
            if not has_vec:
                pytest.skip("sqlite-vec unavailable in this environment")

            db.conn.execute(
                "INSERT OR REPLACE INTO episode_meta (ep_num, summary, causal_data, arc_no, event_types, entity_names) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (99, "백필 대상 요약", "", 1, "회상", "장무기"),
            )
            db.conn.execute("DELETE FROM episode_fts WHERE rowid = 99")
            db.conn.commit()

            _ = VecMemory(conn=db.conn, lock=db._lock, ui_log=lambda _msg: None)
            row = db.conn.execute("SELECT summary FROM episode_fts WHERE rowid = 99").fetchone()

            assert row is not None
            assert "백필 대상 요약" in row[0]
        finally:
            db.close()


# ══════════════════════════════════════════════════════════════
# Smoke Test 2: memorize + retrieve 흐름
# ══════════════════════════════════════════════════════════════


class TestMemorizeAndRetrieve:
    """VecMemory.memorize_v20_episode() → retrieve_* 흐름 검증.
    임베딩 API는 모킹."""

    @pytest.fixture
    def mem_in_memory(self):
        """in-memory VecMemory — sqlite-vec 미설치 시 스킵."""
        try:
            m = VecMemory(":memory:", api_key="", ui_log=lambda msg: None)
            if not m.has_valid_memory:
                pytest.skip(f"VecMemory not operational: {m.initialization_error}")
            yield m
            m.close()
        except Exception as e:
            pytest.skip(f"VecMemory 초기화 실패: {e}")

    def test_memorize_writes_episode_meta(self, mem_in_memory):
        """memorize_v20_episode 후 episode_meta 행이 생성됨."""
        mem = mem_in_memory
        fake_vec = _make_vec(0.5)

        with patch.object(mem, "_embed_text", return_value=fake_vec):
            result = mem.memorize_v20_episode(
                ep_num=1,
                text="이청풍은 새벽에 수련을 시작했다.",
                summary="이청풍 수련 시작",
                causal_links=[],
                arc_no=1,
                event_types=["훈련"],
                entity_names=["이청풍"],
            )

        assert result is True
        row = mem._conn.execute(
            "SELECT summary FROM episode_meta WHERE ep_num = 1"
        ).fetchone()
        assert row is not None
        assert "이청풍" in row[0]

    def test_memorize_syncs_episode_fts(self, mem_in_memory):
        """memorize_v20_episode 후 episode_fts 행이 동기화됨."""
        mem = mem_in_memory
        fake_vec = _make_vec(0.3)

        with patch.object(mem, "_embed_text", return_value=fake_vec):
            mem.memorize_v20_episode(
                ep_num=2,
                text="흑풍이 나타났다.",
                summary="흑풍 등장",
                causal_links=[],
                arc_no=1,
                event_types=["조우"],
                entity_names=["흑풍"],
            )

        row = mem._conn.execute(
            "SELECT summary FROM episode_fts WHERE rowid = 2"
        ).fetchone()
        assert row is not None
        assert "흑풍" in row[0]

    def test_retrieve_high_res_context_returns_str(self, mem_in_memory):
        """retrieve_high_res_context → str 반환 확인."""
        mem = mem_in_memory
        fake_vec = _make_vec(1.0)

        with patch.object(mem, "_embed_text", return_value=fake_vec):
            mem.memorize_v20_episode(
                ep_num=3,
                text="노사부가 검법을 전수했다.",
                summary="검법 전수",
                causal_links=[],
                arc_no=1,
            )

        with patch.object(mem, "_embed_text", return_value=fake_vec):
            result = mem.retrieve_high_res_context(
                query="검법 배우기", current_ep=5, n_results=3
            )

        assert isinstance(result, str)

    def test_retrieve_hybrid_context_returns_str(self, mem_in_memory):
        """retrieve_hybrid_context → str 반환 확인."""
        mem = mem_in_memory
        fake_vec = _make_vec(0.7)

        with patch.object(mem, "_embed_text", return_value=fake_vec):
            mem.memorize_v20_episode(
                ep_num=4,
                text="이청풍이 첫 번째 관문을 통과했다.",
                summary="관문 통과",
                causal_links=[],
                arc_no=1,
                event_types=["성장"],
                entity_names=["이청풍"],
            )

        with patch.object(mem, "_embed_text", return_value=fake_vec):
            result = mem.retrieve_hybrid_context(
                query="이청풍 성장", current_ep=6
            )

        assert isinstance(result, str)

    def test_delete_episodes_from_syncs_fts(self, mem_in_memory):
        """delete_episodes_from 후 episode_fts 행도 삭제됨."""
        mem = mem_in_memory
        fake_vec = _make_vec(0.2)

        with patch.object(mem, "_embed_text", return_value=fake_vec):
            mem.memorize_v20_episode(
                ep_num=10,
                text="10화 내용.",
                summary="10화 요약",
                causal_links=[],
                arc_no=2,
            )
            mem.memorize_v20_episode(
                ep_num=11,
                text="11화 내용.",
                summary="11화 요약",
                causal_links=[],
                arc_no=2,
            )

        # 10화 이상 삭제
        deleted = mem.delete_episodes_from(10)
        assert deleted >= 1

        # episode_fts에서도 삭제 확인
        row = mem._conn.execute(
            "SELECT rowid FROM episode_fts WHERE rowid >= 10"
        ).fetchone()
        assert row is None, "episode_fts에서 삭제되지 않은 행이 남아 있습니다"

    def test_retrieve_high_res_fallback_no_embed(self, mem_in_memory):
        """임베딩 실패 시 키워드 폴백 → str 반환 확인."""
        mem = mem_in_memory

        # 먼저 에피소드 저장 (임베딩 성공)
        with patch.object(mem, "_embed_text", return_value=_make_vec(1.0)):
            mem.memorize_v20_episode(
                ep_num=5,
                text="수련 장면.",
                summary="수련",
                causal_links=[],
                arc_no=1,
                entity_names=["이청풍"],
            )

        # 검색 시 임베딩 실패 → 폴백
        with patch.object(mem, "_embed_text", return_value=None):
            result = mem.retrieve_high_res_context(
                query="이청풍 수련", current_ep=10
            )

        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════
# Smoke Test 3: character_voice + foreshadow DB 저장/로드
# ══════════════════════════════════════════════════════════════


class TestCharacterVoiceAndForeshadowDB:
    """CharacterVoiceTracker.save_to_db / load_from_db 및
    ForeshadowTracker.save_to_db / load_from_db 검증."""

    def test_character_voice_save_and_load(self, tmp_path):
        """[DB-Eff-P1] CharacterVoiceTracker: 저장 후 동일 데이터 복원 확인."""
        db = DBManager(tmp_path / "cv_smoke.db")
        try:
            tracker = CharacterVoiceTracker()

            # 프로필 직접 주입 (LLM 불필요)
            from modules.core.character_voice import CharacterVoiceProfile, VoicePattern

            tracker.profiles["이청풍"] = CharacterVoiceProfile(
                name="이청풍",
                style=VoiceStyle.INFORMAL,
                pattern=VoicePattern(endings=["해", "야"]),
                sample_dialogues=["그래, 알겠어."],
                dialogue_count=3,
                consistency_score=0.9,
                last_seen_episode=5,
            )

            # 저장
            tracker.save_to_db(db)

            # character_voice 테이블 행 수 확인
            row_count = db.conn.execute(
                "SELECT COUNT(*) FROM character_voice"
            ).fetchone()[0]
            assert row_count >= 1, "character_voice 테이블에 저장된 행이 없습니다"

            # 새 트래커로 로드
            tracker2 = CharacterVoiceTracker()
            loaded = tracker2.load_from_db(db)
            assert loaded >= 1
            assert "이청풍" in tracker2.profiles
            assert tracker2.profiles["이청풍"].dialogue_count == 3
        finally:
            db.close()

    def test_foreshadow_save_and_load(self, tmp_path):
        """[DB-Eff-P1] ForeshadowTracker: 저장 후 동일 데이터 복원 확인."""
        db = DBManager(tmp_path / "fs_smoke.db")
        try:
            tracker = ForeshadowTracker()

            # 복선 심기
            tracker.plant(
                ep_num=3,
                hook="비밀 편지",
                category=ForeshadowCategory.MYSTERY,
                deadline_ep=20,
                importance=8,
                description="노사부가 남긴 비밀 편지",
            )
            tracker.plant(
                ep_num=5,
                hook="봉인된 검",
                category=ForeshadowCategory.CHEKHOV,
                deadline_ep=30,
            )

            # 저장
            tracker.save_to_db(db)

            # foreshadow 테이블 행 수 확인
            row_count = db.conn.execute(
                "SELECT COUNT(*) FROM foreshadow"
            ).fetchone()[0]
            assert row_count == 2, f"foreshadow 테이블 행 수 불일치: {row_count}"

            # 새 트래커로 로드
            tracker2 = ForeshadowTracker()
            loaded = tracker2.load_from_db(db)
            assert loaded == 2
            # 키 정규화 후 확인
            normalized_key = tracker2._normalize_hook("비밀 편지")
            assert normalized_key in tracker2.hooks
            assert tracker2.hooks[normalized_key].importance == 8
        finally:
            db.close()

    def test_foreshadow_empty_save_load(self, tmp_path):
        """비어 있는 ForeshadowTracker 저장/로드 — 크래시 없음 확인."""
        db = DBManager(tmp_path / "fs_empty.db")
        try:
            tracker = ForeshadowTracker()
            tracker.save_to_db(db)  # 비어 있어도 크래시 없어야 함

            tracker2 = ForeshadowTracker()
            loaded = tracker2.load_from_db(db)
            assert loaded == 0
        finally:
            db.close()

    def test_character_voice_none_db_safe(self):
        """DB가 None일 때 save_to_db/load_from_db가 안전하게 처리됨."""
        tracker = CharacterVoiceTracker()
        tracker.save_to_db(None)  # 크래시 없어야 함
        result = tracker.load_from_db(None)
        assert result == 0

    def test_foreshadow_none_db_safe(self):
        """DB가 None일 때 save_to_db/load_from_db가 안전하게 처리됨."""
        tracker = ForeshadowTracker()
        tracker.save_to_db(None)  # 크래시 없어야 함
        result = tracker.load_from_db(None)
        assert result == 0


# ══════════════════════════════════════════════════════════════
# Smoke Test 4: Stage2Context DI 슬롯 초기화
# ══════════════════════════════════════════════════════════════


class TestStage2ContextDISlots:
    """Stage2Context 인스턴스화 → 주요 슬롯 AttributeError 없이 접근 가능."""

    @pytest.fixture
    def stage2_ctx(self):
        """Stage2Context 최소 조립 (필수 5종만 실제 mock, 나머지 None)."""
        mock_ui = MagicMock()
        mock_project = MagicMock()
        mock_agents = {}
        mock_sys = MagicMock()
        mock_state_tracker = MagicMock()

        ctx = Stage2Context(
            ui=mock_ui,
            current_project=mock_project,
            agents=mock_agents,
            sys=mock_sys,
            state_tracker=mock_state_tracker,
        )
        return ctx

    def test_required_slots_accessible(self, stage2_ctx):
        """필수 5종 슬롯 접근 가능 (AttributeError 없음)."""
        ctx = stage2_ctx
        assert ctx.ui is not None
        assert ctx.current_project is not None
        assert ctx.agents is not None
        assert ctx.sys is not None
        assert ctx.state_tracker is not None

    def test_optional_extension_slots_default_none(self, stage2_ctx):
        """확장 슬롯 기본값 None."""
        ctx = stage2_ctx
        assert ctx.memory is None
        assert ctx.failure_learner is None
        assert ctx.semantic_plot_guard is None
        assert ctx.stage2_optimizer is None
        assert ctx.arc_draft_validator is None
        assert ctx.pass_rate_monitor is None
        assert ctx.quality_dashboard is None

    def test_callback_slots_default_none(self, stage2_ctx):
        """콜백 슬롯 기본값 None."""
        ctx = stage2_ctx
        assert ctx.audit_event is None
        assert ctx.write_audit_summary is None
        assert ctx.validate_arc_mapping is None
        assert ctx.safe_commit_async is None
        assert ctx.get_int_input is None
        assert ctx.generate_structured_arc_feedback is None

    def test_use_arc_corrector_default_false(self, stage2_ctx):
        """use_arc_corrector 기본값 False."""
        ctx = stage2_ctx
        assert ctx.use_arc_corrector is False

    def test_context_advisor_slot_accessible(self, stage2_ctx):
        """context_advisor 슬롯 AttributeError 없이 접근 가능."""
        ctx = stage2_ctx
        _ = ctx.context_advisor  # AttributeError 없으면 OK

    def test_stage2_context_slot_count(self):
        """Stage2Context __slots__ 총 수 — 예상 범위 내 (44종 이상)."""
        slots = Stage2Context.__slots__
        # [4C-3] 필수 5 + 확장 19 + 콜백 22 = 46종 (context_advisor, adversarial_self_play, sync_cache_key_to_app 포함)
        assert len(slots) >= 44, f"슬롯 수 예상보다 적음: {len(slots)}"


# ══════════════════════════════════════════════════════════════
# Smoke Test 5: Stage4Context DI 슬롯 초기화
# ══════════════════════════════════════════════════════════════


class TestStage4ContextDISlots:
    """Stage4Context 인스턴스화 → 주요 슬롯 AttributeError 없이 접근 가능."""

    @pytest.fixture
    def stage4_ctx(self, tmp_path):
        """Stage4Context 최소 조립."""
        db = DBManager(tmp_path / "s4_smoke.db")
        mock_ui = MagicMock()
        mock_project = MagicMock()
        mock_project.db = db

        ctx = Stage4Context(
            ui=mock_ui,
            current_project=mock_project,
            agents={},
            sys=MagicMock(),
            state_tracker=MagicMock(),
            selected_genre={"type": "wuxia", "name": "무협"},
        )
        yield ctx
        db.close()

    def test_required_slots_accessible(self, stage4_ctx):
        """필수 5종 슬롯 접근 가능."""
        ctx = stage4_ctx
        assert ctx.ui is not None
        assert ctx.current_project is not None
        assert ctx.agents is not None
        assert ctx.sys is not None
        assert ctx.state_tracker is not None

    def test_selected_genre_set(self, stage4_ctx):
        """selected_genre 슬롯 값 정상 설정."""
        ctx = stage4_ctx
        assert ctx.selected_genre is not None
        assert ctx.selected_genre["type"] == "wuxia"

    def test_optional_slots_default_none(self, stage4_ctx):
        """확장 슬롯 기본값 None."""
        ctx = stage4_ctx
        assert ctx.memory is None
        assert ctx.world_state is None
        assert ctx.fact_ledger is None
        assert ctx.character_voice is None
        assert ctx.foreshadow_tracker is None
        assert ctx.failure_learner is None
        assert ctx.emotion_tracker is None

    def test_callback_slots_default_none(self, stage4_ctx):
        """콜백 슬롯 기본값 None."""
        ctx = stage4_ctx
        assert ctx.get_int_input is None
        assert ctx.flush_audit_buffer is None
        assert ctx.safe_commit is None
        assert ctx.generate_narrative_summary is None

    def test_conditional_modules_default_empty_dict(self, stage4_ctx):
        """conditional_modules 기본값 빈 dict."""
        ctx = stage4_ctx
        assert isinstance(ctx.conditional_modules, dict)
        assert len(ctx.conditional_modules) == 0

    def test_get_module_helper(self, stage4_ctx):
        """get_module() 헬퍼 — 없는 모듈은 None 반환."""
        ctx = stage4_ctx
        assert ctx.get_module("nonexistent") is None

    def test_context_advisor_slot_accessible(self, stage4_ctx):
        """context_advisor 슬롯 AttributeError 없이 접근 가능."""
        ctx = stage4_ctx
        _ = ctx.context_advisor  # AttributeError 없으면 OK

    def test_stage4_context_slot_count(self):
        """Stage4Context __slots__ 총 수 == 28."""
        slots = Stage4Context.__slots__
        assert len(slots) == 28, f"슬롯 수 불일치: {len(slots)}"

    def test_stage4_character_voice_slot_wiring(self, tmp_path):
        """character_voice 슬롯에 CharacterVoiceTracker 주입 후 접근 가능."""
        db = DBManager(tmp_path / "cv_wiring.db")
        try:
            tracker = CharacterVoiceTracker()
            ctx = Stage4Context(
                ui=MagicMock(),
                current_project=MagicMock(),
                agents={},
                sys=MagicMock(),
                state_tracker=MagicMock(),
                character_voice=tracker,
            )
            assert ctx.character_voice is tracker
        finally:
            db.close()

    def test_stage4_foreshadow_slot_wiring(self, tmp_path):
        """foreshadow_tracker 슬롯에 ForeshadowTracker 주입 후 접근 가능."""
        db = DBManager(tmp_path / "fs_wiring.db")
        try:
            tracker = ForeshadowTracker()
            ctx = Stage4Context(
                ui=MagicMock(),
                current_project=MagicMock(),
                agents={},
                sys=MagicMock(),
                state_tracker=MagicMock(),
                foreshadow_tracker=tracker,
            )
            assert ctx.foreshadow_tracker is tracker
        finally:
            db.close()
