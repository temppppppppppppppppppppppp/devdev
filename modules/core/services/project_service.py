"""[Phase 4B-3] ProjectService — 프로젝트 데이터 관리 서비스

원본: main_a.py:3765-4014 (4개 메서드, ~247줄)
Protocol 참조: modules/protocols/app_services.py ProjectRepositoryProtocol
"""

from __future__ import annotations

import json
import logging
import re as _re_rollback
from collections.abc import Callable
from typing import Any

from modules.core.constants import HUDKeys


class ProjectService:
    """프로젝트 데이터 리셋/되감기/롤백/소거 서비스.

    Args:
        project_fn: () -> current_project 또는 None (lazy 접근)
        ui: StudioVisualizer 인스턴스
        safe_commit_fn: _safe_commit 콜백
        genre_fn: () -> selected_genre dict 또는 None
        memory_fn: () -> memory (VectorDB) 또는 None
        state_tracker_invalidator: 롤백 성공 후 state tracker 무효화 콜백
        world_state_fn: () -> WorldStateManager 또는 None (롤백 후 stale 차단)
        fact_ledger_fn: () -> FactLedger 또는 None (롤백 후 stale 차단)
        preset_registry_restorer: 롤백 후 preset_registry 복원 콜백
    """

    def __init__(
        self,
        project_fn: Callable[[], Any],
        ui: Any,
        safe_commit_fn: Callable[[], bool],
        genre_fn: Callable[[], Any],
        memory_fn: Callable[[], Any],
        state_tracker_invalidator: Callable[[], None] | None = None,
        world_state_fn: Callable[[], Any] | None = None,
        fact_ledger_fn: Callable[[], Any] | None = None,
        preset_registry_restorer: Callable[[], None] | None = None,
        emotion_tracker_fn: Callable[[], Any] | None = None,
        state_delta_tracker_fn: Callable[[], Any] | None = None,
    ) -> None:
        self._project_fn = project_fn
        self._ui = ui
        self._safe_commit = safe_commit_fn
        self._genre_fn = genre_fn
        self._memory_fn = memory_fn
        self._invalidate_tracker = state_tracker_invalidator
        self._world_state_fn = world_state_fn
        self._fact_ledger_fn = fact_ledger_fn
        self._preset_registry_restorer = preset_registry_restorer
        self._emotion_tracker_fn = emotion_tracker_fn
        self._state_delta_tracker_fn = state_delta_tracker_fn

    # ── reset_stage_2 ────────────────────────────────────────────
    def reset_stage_2(self) -> None:
        """Stage 2(Arcs) SQL DB에서 삭제. 원본: main_a.py:3765"""
        project = self._project_fn()
        confirm = input("\n🚨 정말로 Stage 2(Arcs) 설계 데이터를 삭제하시겠습니까? (y/n): ").strip().lower()
        if confirm == "y":
            project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")
            if not self._safe_commit():
                self._ui.log("❌ DB 커밋 실패 — Stage 2 리셋 중단")
                return
            project.arcs = []
            self._ui.log("✅ Stage 2 데이터가 삭제되었습니다. 이제 메뉴에서 2번 [❌] 상태로 보일 것입니다.")
            input("\n[Enter] 메뉴로 돌아가기")

    # ── rewind_stage_2 ───────────────────────────────────────────
    def rewind_stage_2(self) -> None:
        """특정 아크 번호부터 이후를 전부 삭제 (정밀 되감기). 원본: main_a.py:3779"""
        project = self._project_fn()
        if not hasattr(project, "arcs") or not project.arcs:
            self._ui.log("❌ 삭제할 아크 데이터가 없습니다.")
            return

        total_arcs = len(project.arcs)
        self._ui.log(f"📊 현재 총 {total_arcs}개의 아크가 설계되어 있습니다.")

        target_input = input(
            f"\n👉 몇 번 아크부터 새로 시작하시겠습니까? (1~{total_arcs} 입력) [한 번에 5개까지만 해라 웬만하면]: "
        ).strip()

        if not target_input.isdigit():
            self._ui.log("❌ 숫자만 입력 가능합니다.")
            return

        target_no = int(target_input)

        updated_arcs = [a for a in project.arcs if isinstance(a, dict) and a.get("arc_no", 0) < target_no]

        confirm = input(f"⚠️ Arc {target_no}번부터 {total_arcs}번까지 삭제합니다. 계속할까요? (y/n): ").strip().lower()
        if confirm == "y":
            project.save_v20_anchor("arcs", updated_arcs)
            project.arcs = updated_arcs
            self._ui.log(f"✨ Arc {target_no}번 이후 데이터가 삭제되었습니다.")
            self._ui.log(f"🔄 이제 2번 메뉴를 실행하면 {target_no}번부터 다시 설계를 시작합니다.")
            input("\n[Enter] 메뉴로 돌아가기")

    # ── rollback_episode ─────────────────────────────────────────
    def rollback_episode(self) -> bool:
        """특정 회차로 되감기 (HUD, DB, Vector DB, 파일 모두 롤백). 원본: main_a.py:3815"""
        project = self._project_fn()
        latest_ep = project.get_latest_episode_number() - 1

        if latest_ep <= 0:
            self._ui.log("❌ 롤백할 에피소드가 없습니다.")
            return False

        self._ui.log(f"📊 현재 최신 에피소드: {latest_ep}화")
        target_input = input(f"\n👉 몇 화로 되감기하시겠습니까? (1~{latest_ep} 입력, 1 입력 시 전체 삭제): ").strip()

        if not target_input.isdigit():
            self._ui.log("❌ 숫자만 입력 가능합니다.")
            return False

        target_ep = int(target_input)

        if target_ep < 1 or target_ep > latest_ep:
            self._ui.log(f"❌ 1~{latest_ep} 범위 내에서 입력해주세요.")
            return False

        confirm = (
            input(
                f"\n⚠️ [{target_ep}화 이후 삭제] 모든 데이터가 {target_ep}화 직전 상태로 되돌아갑니다. 계속할까요? (y/n): "
            )
            .strip()
            .lower()
        )
        if confirm != "y":
            self._ui.log("❌ 취소되었습니다.")
            return False

        try:
            _pending_bible = None
            # 1. HUD 롤백
            if target_ep > 1:
                project.db.cursor.execute("SELECT data FROM state_logs WHERE ep_num = ?", (target_ep - 1,))
                row = project.db.cursor.fetchone()
                if row:
                    past_data = json.loads(row["data"]) if row["data"] else {}
                    past_actual = past_data.get("state_updates", {}).get("actual_truth")

                    if past_actual:
                        project.db.cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
                        bible_row = project.db.cursor.fetchone()
                        if bible_row:
                            bible_data = json.loads(bible_row["data"]) if bible_row["data"] else {}
                            if "MasterBible" in bible_data:
                                selected_genre = self._genre_fn()
                                genre = selected_genre.get("type", "") if selected_genre else ""
                                hud_key = HUDKeys.get_hud_root(genre)
                                for hk in [hud_key, "MartialHUD", "FinanceHUD", "HunterHUD"]:
                                    if hk in bible_data["MasterBible"]:
                                        hud_key = hk
                                        break
                                if hud_key in bible_data["MasterBible"]:
                                    bible_data["MasterBible"][hud_key].setdefault("Protagonist", {})["actual_truth"] = (
                                        past_actual
                                    )
                                project.db.cursor.execute(
                                    "UPDATE anchors SET data = ? WHERE key = 'bible'",
                                    (json.dumps(bible_data, ensure_ascii=False),),
                                )
                                self._ui.log(f"   📉 [Rollback] HUD를 {target_ep - 1}화 시점으로 복구했습니다.")
                                _pending_bible = bible_data  # [TF-A-1] 커밋 성공 후 인메모리 반영

            # 2. SQL DB 데이터 삭제
            ALLOWED_EP_TABLES = frozenset(
                ["manuscripts", "blueprints", "state_logs", "martial_tracker", "sync_status", "causal_graph"]
            )
            ep_tables = ["manuscripts", "blueprints", "state_logs", "martial_tracker", "sync_status", "causal_graph"]

            for t in ep_tables:
                if t not in ALLOWED_EP_TABLES:
                    self._ui.log(f"🚨 [Security] 허용되지 않은 테이블: {t}")
                    continue
                project.db.cursor.execute(f"DELETE FROM {t} WHERE ep_num >= ?", (target_ep,))
                self._ui.log(f"   ✂️  '{t}' 테이블: {target_ep}화 이후 삭제 완료")

            # 3. 로어, 카르마, 씨드 처리
            project.db.cursor.execute("DELETE FROM encyclopedia")
            project.db.cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
            project.db.cursor.execute("DELETE FROM npc_history WHERE episode_no >= ?", (target_ep,))
            project.db.cursor.execute(
                "UPDATE seeds SET status = 'active', recovered_ep = NULL WHERE recovered_ep >= ?", (target_ep,)
            )
            # [TF7-P1-07] director_selections 롤백 대상 누락 수정 (reset_after와 동일 패턴)
            project.db.cursor.execute("DELETE FROM director_selections WHERE ep_num >= ?", (target_ep,))
            self._ui.log("   ✂️  'director_selections' 테이블: 롤백 대상 삭제 완료")
            self._ui.log("   📚 [Lore/Seeds] 인과 관계 초기화 완료")

            # 3.5 Episode Bibles 롤백
            deleted_bibles = project.db.delete_episode_bibles_after(target_ep - 1)
            self._ui.log(f"   📖 [Episode Bibles] {deleted_bibles}개 에피소드 설정 변화 삭제 완료")

            # 4. ID 카운터 초기화
            seq_targets = (
                "('manuscripts', 'blueprints', 'state_logs', 'martial_tracker', 'causal_graph', 'sync_status')"
            )
            project.db.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN {seq_targets}")
            self._ui.log("   🔢 [Sequence] 테이블 ID 카운터 초기화 완료")

            # 커밋
            if not self._safe_commit():
                self._ui.log("❌ DB 커밋 실패 — 롤백 중단 (파일/벡터 보존)")
                return False
            if _pending_bible is not None:
                project.master_bible = _pending_bible

            # 5. 물리 파일 삭제 [TF-11-07] 실패 시 logging.error (DB·파일 불일치 추적)
            import logging as _logging
            for f in project.paths.drafts.glob("*.txt"):
                try:
                    _m = _re_rollback.match(r"(?:ep_)?(\d{1,5})\.txt", f.name)
                    if _m and int(_m.group(1)) >= target_ep:
                        f.unlink()
                except OSError as _fe:
                    _logging.error("[ProjectService] 롤백 파일 삭제 실패 %s: %s", f.name, _fe)
                except (ValueError, IndexError):
                    pass
            self._ui.log("   📂 원고 파일 삭제 완료")

            # 6. 벡터 DB 소거
            memory = self._memory_fn()
            try:
                if memory and hasattr(memory, "delete_episodes_from"):
                    deleted = memory.delete_episodes_from(target_ep)
                    self._ui.log(f"   🌌 벡터 메모리 소거 완료 ({deleted}건)")
                else:
                    self._ui.log("   ⚠️ [VectorDB] 메모리 미초기화로 벡터 소거 생략")
            except Exception as e:
                self._ui.log(f"   ⚠️ [VectorDB] 소거 실패: {e}")

            # 7. 데이터 리로드
            project._load_from_db()
            if self._invalidate_tracker:
                self._invalidate_tracker()

            # [TF-7-P0-01] world_state / fact_ledger stale 차단 — rollback_to 호출
            _ws = self._world_state_fn() if self._world_state_fn else None
            if _ws is not None and hasattr(_ws, "rollback_to"):
                try:
                    _ws.rollback_to(target_ep)
                    self._ui.log(f"   🌐 [WorldState] {target_ep}화 이전으로 롤백 완료")
                except Exception as _ws_err:
                    self._ui.log(f"   ⚠️ [WorldState] rollback_to 실패: {_ws_err}")
            _fl = self._fact_ledger_fn() if self._fact_ledger_fn else None
            if _fl is not None and hasattr(_fl, "rollback_to"):
                try:
                    _fl.rollback_to(target_ep)
                    self._ui.log(f"   📋 [FactLedger] {target_ep}화 이전으로 롤백 완료")
                except Exception as _fl_err:
                    self._ui.log(f"   ⚠️ [FactLedger] rollback_to 실패: {_fl_err}")

            if self._emotion_tracker_fn and callable(self._emotion_tracker_fn):
                _et = self._emotion_tracker_fn()
                if _et is not None and hasattr(_et, "rollback_to"):
                    _et.rollback_to(target_ep)

            if self._state_delta_tracker_fn and callable(self._state_delta_tracker_fn):
                _sdt = self._state_delta_tracker_fn()
                if _sdt is not None and hasattr(_sdt, "rollback_to"):
                    _sdt.rollback_to(target_ep)

            # [TF-7-P0-03] preset_registry 복원 (rollback 후 _preset_state_raw 갱신됨)
            if self._preset_registry_restorer:
                try:
                    self._preset_registry_restorer()
                except Exception as _pr_err:
                    self._ui.log(f"   ⚠️ [PresetRegistry] 복원 실패 (무시): {_pr_err}")

            self._ui.log(f"\n✅ [Success] {target_ep}화 직전 상태로 롤백 완료!")
            self._ui.log(f"👉 이제 Stage 4를 실행하면 {target_ep}화부터 새로 집필합니다.")
            input("\n[Enter] 메뉴로 돌아가기")
            self._assert_rollback_invariants(target_ep)
            return True

        except Exception as e:
            self._ui.log(f"❌ 롤백 실패: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _assert_rollback_invariants(self, target_ep: int) -> None:
        """롤백 완료 후 post-invariant 검사 — 트래커 ep가 target_ep를 초과하면 WARNING."""
        if self._emotion_tracker_fn and callable(self._emotion_tracker_fn):
            _et = self._emotion_tracker_fn()
            if _et is not None and hasattr(_et, "history") and _et.history:
                max_ep = max(entry[0] for entry in _et.history)
                if max_ep >= target_ep:
                    logging.warning("[RollbackInvariant] EmotionArcTracker max ep=%d >= target_ep=%d after rollback",
                        max_ep,
                        target_ep,
                    )
                else:
                    logging.debug("[RollbackInvariant] EmotionArcTracker OK (max ep=%d < target_ep=%d)",
                        max_ep,
                        target_ep,
                    )

        if self._state_delta_tracker_fn and callable(self._state_delta_tracker_fn):
            _sdt = self._state_delta_tracker_fn()
            if _sdt is not None and hasattr(_sdt, "energy_history") and _sdt.energy_history:
                max_ep = max(e.episode for e in _sdt.energy_history)
                if max_ep >= target_ep:
                    logging.warning("[RollbackInvariant] StateDeltaTracker max ep=%d >= target_ep=%d after rollback",
                        max_ep,
                        target_ep,
                    )
                else:
                    logging.debug("[RollbackInvariant] StateDeltaTracker OK (max ep=%d < target_ep=%d)",
                        max_ep,
                        target_ep,
                    )

    # ── wipe_production_data ─────────────────────────────────────
    def wipe_production_data(self) -> None:
        """설계도 유지, 실제 집필 기록만 소거. 원본: main_a.py:3959"""
        confirm = input("\n🚨 [WIPE] 설계도는 남기고 '실제 원고' 기록만 모두 삭제할까요? (y/n): ").strip().lower()
        if confirm != "y":
            return

        project = self._project_fn()
        try:
            ALLOWED_TABLES = frozenset(
                [
                    "manuscripts",
                    "state_logs",
                    "martial_tracker",
                    "causal_graph",
                    "sync_status",
                    "karma_status",
                ]
            )
            production_tables = [
                "manuscripts",
                "state_logs",
                "martial_tracker",
                "causal_graph",
                "sync_status",
                "karma_status",
            ]

            for t in production_tables:
                if t not in ALLOWED_TABLES:
                    self._ui.log(f"🚨 [Security] 허용되지 않은 테이블: {t}")
                    continue
                project.db.cursor.execute(f"DELETE FROM {t}")

            project.db.cursor.execute("UPDATE seeds SET status = 'active', recovered_ep = NULL")
            if not self._safe_commit():  # [TF-11-06] rollback 보장
                self._ui.log("❌ [Wipe] DB 커밋 실패 — 리셋 중단")
                return

            for f in project.paths.drafts.glob("*.txt"):
                f.unlink()

            memory = self._memory_fn()
            try:
                if memory and hasattr(memory, "delete_all_episodes"):
                    memory.delete_all_episodes()
            except Exception as e:
                self._ui.log(f"⚠️ [VectorDB] 컬렉션 초기화 실패: {e}")

            self._ui.log("✅ [Wipe] 원고 기록이 청소되었습니다. 이제 1화부터 다시 생산 가능합니다.")
            input("\n[Enter] 메뉴로 돌아가기")
        except Exception as e:
            self._ui.log(f"❌ 리셋 실패: {e}")
