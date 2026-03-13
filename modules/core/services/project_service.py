"""ProjectService for destructive project operations."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import Any

from modules.core.constants import HUDKeys

_DRAFT_EP_RE = re.compile(r"(?:ep_)?(\d{1,5})\.txt")


class ProjectService:
    """Manage destructive project operations such as rollback and rewind."""

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

    def _delete_draft_files_from_episode(self, project: Any, target_ep: int) -> None:
        for draft_file in project.paths.drafts.glob("*.txt"):
            try:
                match = _DRAFT_EP_RE.match(draft_file.name)
                if match and int(match.group(1)) >= target_ep:
                    draft_file.unlink()
            except OSError as exc:
                logging.error("[ProjectService] Failed to delete draft %s: %s", draft_file.name, exc)
            except (ValueError, IndexError):
                continue

    def _delete_all_draft_files(self, project: Any) -> None:
        for draft_file in project.paths.drafts.glob("*.txt"):
            try:
                draft_file.unlink()
            except OSError as exc:
                logging.error("[ProjectService] Failed to delete draft %s: %s", draft_file.name, exc)

    def _restore_runtime_state(self, target_ep: int) -> None:
        project = self._project_fn()
        if hasattr(project, "_load_from_db"):
            project._load_from_db()
        if self._invalidate_tracker:
            self._invalidate_tracker()

        world_state = self._world_state_fn() if self._world_state_fn else None
        if world_state is not None and hasattr(world_state, "rollback_to"):
            try:
                world_state.rollback_to(target_ep)
            except Exception as exc:  # pragma: no cover - non-blocking UI path
                self._ui.log(f"   [WorldState] rollback_to failed: {exc}")

        fact_ledger = self._fact_ledger_fn() if self._fact_ledger_fn else None
        if fact_ledger is not None and hasattr(fact_ledger, "rollback_to"):
            try:
                fact_ledger.rollback_to(target_ep)
            except Exception as exc:  # pragma: no cover - non-blocking UI path
                self._ui.log(f"   [FactLedger] rollback_to failed: {exc}")

        if self._emotion_tracker_fn and callable(self._emotion_tracker_fn):
            tracker = self._emotion_tracker_fn()
            if tracker is not None and hasattr(tracker, "rollback_to"):
                tracker.rollback_to(target_ep)

        if self._state_delta_tracker_fn and callable(self._state_delta_tracker_fn):
            tracker = self._state_delta_tracker_fn()
            if tracker is not None and hasattr(tracker, "rollback_to"):
                tracker.rollback_to(target_ep)

        if self._preset_registry_restorer:
            try:
                self._preset_registry_restorer()
            except Exception as exc:  # pragma: no cover - non-blocking UI path
                self._ui.log(f"   [PresetRegistry] restore failed (ignored): {exc}")

    def _clear_stage2_summary_anchors(self, project: Any, from_arc_no: int | None = None) -> None:
        project.db.cursor.execute("DELETE FROM anchors WHERE key = 'volumes'")
        project.db.cursor.execute("DELETE FROM anchors WHERE key = 'series_summary'")
        project.db.cursor.execute("DELETE FROM anchors WHERE key LIKE 'volume_summary_%'")
        if from_arc_no is None:
            project.db.cursor.execute("DELETE FROM anchors WHERE key LIKE 'arc_summary_%'")
        else:
            project.db.cursor.execute(
                """
                DELETE FROM anchors
                WHERE key GLOB 'arc_summary_[0-9]*'
                  AND CAST(SUBSTR(key, 13) AS INTEGER) >= ?
                """,
                (from_arc_no,),
            )

    def _clear_narrative_summary_anchors(self, project: Any, from_episode: int | None = None) -> None:
        if from_episode is None:
            project.db.cursor.execute("DELETE FROM anchors WHERE key LIKE 'narrative_summary_ep_%'")
            return

        project.db.cursor.execute(
            """
            DELETE FROM anchors
            WHERE key GLOB 'narrative_summary_ep_[0-9]*'
              AND CAST(SUBSTR(key, 22) AS INTEGER) >= ?
            """,
            (from_episode,),
        )

    def _clear_stage2_metadata(self, project: Any, from_arc_no: int | None = None) -> None:
        if from_arc_no is None:
            project.db.cursor.execute("DELETE FROM arc_dependencies")
            project.db.cursor.execute("DELETE FROM stage_attempts WHERE stage = 2")
            project.db.cursor.execute(
                "DELETE FROM director_selections WHERE stage = 2 OR (stage IS NULL AND COALESCE(selected_label, '') = '')"
            )
            return

        project.db.cursor.execute(
            "DELETE FROM arc_dependencies WHERE from_arc_no >= ? OR to_arc_no >= ?",
            (from_arc_no, from_arc_no),
        )
        project.db.cursor.execute(
            "DELETE FROM stage_attempts WHERE stage = 2 AND arc_num >= ?",
            (from_arc_no,),
        )
        project.db.cursor.execute(
            """
            DELETE FROM director_selections
            WHERE ep_num >= ?
              AND (stage = 2 OR (stage IS NULL AND COALESCE(selected_label, '') = ''))
            """,
            (from_arc_no,),
        )

    def _infer_rewind_target_ep(self, removed_arcs: list[dict], target_no: int) -> int:
        candidate_episodes: list[int] = []
        for arc in removed_arcs:
            if not isinstance(arc, dict):
                continue
            for key in ("ep_start", "start_ep", "episode_start", "start_episode", "ep_num"):
                value = arc.get(key)
                if isinstance(value, int) and value > 0:
                    candidate_episodes.append(value)
                    break
        return min(candidate_episodes) if candidate_episodes else target_no

    def _rollback_open_transaction(self, project: Any) -> None:
        conn = getattr(getattr(project, "db", None), "conn", None)
        if conn is None or not getattr(conn, "in_transaction", False):
            return
        try:
            conn.rollback()
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logging.warning("[ProjectService] rollback cleanup failed: %s", exc)

    def reset_stage_2(self) -> bool:
        """Clear all Stage 2 arc design and every downstream episode artifact."""
        project = self._project_fn()
        confirm = input("\nReally reset Stage 2 arcs and all downstream production data? (y/n): ").strip().lower()
        if confirm != "y":
            return False

        try:
            project.db.reset_after(1, commit=False)
            self._clear_stage2_metadata(project)
            self._clear_stage2_summary_anchors(project)
            self._clear_narrative_summary_anchors(project)
            project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")
            if not self._safe_commit():
                self._rollback_open_transaction(project)
                self._ui.log("DB commit failed during Stage 2 reset")
                return False

            project.arcs = []
            if hasattr(project, "volumes"):
                project.volumes = []

            self._delete_all_draft_files(project)

            memory = self._memory_fn()
            try:
                if memory and hasattr(memory, "delete_all_episodes"):
                    memory.delete_all_episodes()
            except Exception as exc:  # pragma: no cover - non-blocking UI path
                self._ui.log(f"   [VectorDB] delete_all_episodes failed: {exc}")

            self._restore_runtime_state(1)
            self._ui.log("Stage 2 reset complete. Arc design and downstream artifacts were cleared.")
            input("\n[Enter] Return to menu")
            return True
        except Exception as exc:
            self._rollback_open_transaction(project)
            self._ui.log(f"Stage 2 reset failed: {exc}")
            return False

    def rewind_stage_2(self) -> bool:
        """Rewind arc design from a target arc number and purge downstream artifacts."""
        project = self._project_fn()
        if not getattr(project, "arcs", None):
            self._ui.log("No arc data is available.")
            return False

        total_arcs = len(project.arcs)
        self._ui.log(f"Current arcs: {total_arcs}")

        target_input = input(f"\nRewind from which arc? (1-{total_arcs}): ").strip()
        if not target_input.isdigit():
            self._ui.log("Only numeric input is allowed.")
            return False

        target_no = int(target_input)
        if target_no < 1 or target_no > total_arcs:
            self._ui.log(f"Please enter a value between 1 and {total_arcs}.")
            return False

        updated_arcs = [arc for arc in project.arcs if isinstance(arc, dict) and arc.get("arc_no", 0) < target_no]
        removed_arcs = [arc for arc in project.arcs if isinstance(arc, dict) and arc.get("arc_no", 0) >= target_no]
        target_ep = self._infer_rewind_target_ep(removed_arcs, target_no)

        confirm = input(
            f"Delete arc {target_no} through arc {total_arcs} and purge downstream data from episode {target_ep}? (y/n): "
        ).strip().lower()
        if confirm != "y":
            return False

        try:
            project.db.reset_after(target_ep, commit=False)
            self._clear_stage2_metadata(project, from_arc_no=target_no)
            self._clear_stage2_summary_anchors(project, from_arc_no=target_no)
            self._clear_narrative_summary_anchors(project, from_episode=target_ep)
            if not project.db.save_anchor("arcs", updated_arcs):
                raise RuntimeError("failed to save arcs anchor during rewind")
            if not self._safe_commit():
                self._rollback_open_transaction(project)
                self._ui.log("DB commit failed during Stage 2 rewind")
                return False

            project.arcs = updated_arcs
            if hasattr(project, "volumes"):
                project.volumes = []
            if hasattr(project, "_save_arcs_to_txt"):
                try:
                    project._save_arcs_to_txt(updated_arcs)
                except Exception as exc:  # pragma: no cover - non-blocking UI path
                    logging.debug("[ProjectService] arc txt sync skipped: %s", exc)

            self._delete_draft_files_from_episode(project, target_ep)

            memory = self._memory_fn()
            try:
                if memory and hasattr(memory, "delete_episodes_from"):
                    memory.delete_episodes_from(target_ep)
            except Exception as exc:  # pragma: no cover - non-blocking UI path
                self._ui.log(f"   [VectorDB] delete_episodes_from failed: {exc}")

            self._restore_runtime_state(target_ep)
            self._ui.log(f"Arc rewind complete. Arc {target_no}+ and downstream episode data were removed.")
            input("\n[Enter] Return to menu")
            return True
        except Exception as exc:
            self._rollback_open_transaction(project)
            self._ui.log(f"Stage 2 rewind failed: {exc}")
            return False

    def rollback_episode(self) -> bool:
        """Rollback to the state immediately before a target episode."""
        project = self._project_fn()
        latest_ep = project.get_latest_episode_number() - 1

        if latest_ep <= 0:
            self._ui.log("No episode is available for rollback.")
            return False

        self._ui.log(f"Latest episode: {latest_ep}")
        target_input = input(f"\nRollback from which episode? (1-{latest_ep}): ").strip()

        if not target_input.isdigit():
            self._ui.log("Only numeric input is allowed.")
            return False

        target_ep = int(target_input)
        if target_ep < 1 or target_ep > latest_ep:
            self._ui.log(f"Please enter a value between 1 and {latest_ep}.")
            return False

        confirm = input(
            f"\nDelete every artifact for episode >= {target_ep} and return to the state before episode {target_ep}? (y/n): "
        ).strip().lower()
        if confirm != "y":
            self._ui.log("Cancelled.")
            return False

        try:
            pending_bible = None
            if target_ep > 1:
                project.db.cursor.execute("SELECT data FROM state_logs WHERE ep_num = ?", (target_ep - 1,))
                row = project.db.cursor.fetchone()
                if row:
                    past_data = json.loads(row["data"]) if row["data"] else {}
                    past_actual = past_data.get("state_updates", {}).get("actual_truth")
                    if past_actual:
                        bible_data = project.db.load_anchor("bible") or {}
                        if "MasterBible" in bible_data:
                            selected_genre = self._genre_fn()
                            genre = selected_genre.get("type", "") if selected_genre else ""
                            hud_key = HUDKeys.get_hud_root(genre)
                            for candidate in (hud_key, "MartialHUD", "FinanceHUD", "HunterHUD"):
                                if candidate in bible_data["MasterBible"]:
                                    hud_key = candidate
                                    break
                            if hud_key in bible_data["MasterBible"]:
                                protagonist = bible_data["MasterBible"][hud_key].setdefault("Protagonist", {})
                                protagonist["actual_truth"] = past_actual
                                pending_bible = bible_data

            project.db.reset_after(target_ep, commit=False)
            self._clear_narrative_summary_anchors(project, from_episode=target_ep)
            project.db.cursor.execute(
                "UPDATE seeds SET status = 'active', recovered_ep = NULL WHERE recovered_ep >= ?",
                (target_ep,),
            )
            if pending_bible is not None:
                if not project.db.save_anchor("bible", pending_bible):
                    raise RuntimeError("failed to save bible anchor during rollback")
            if not self._safe_commit():
                self._rollback_open_transaction(project)
                self._ui.log("DB commit failed during rollback")
                return False

            if pending_bible is not None:
                project.master_bible = pending_bible
                self._ui.log(f"   [Rollback] HUD restored from episode {target_ep - 1}.")

            self._delete_draft_files_from_episode(project, target_ep)

            memory = self._memory_fn()
            try:
                if memory and hasattr(memory, "delete_episodes_from"):
                    deleted = memory.delete_episodes_from(target_ep)
                    self._ui.log(f"   [VectorDB] Deleted {deleted} episode embeddings.")
                else:
                    self._ui.log("   [VectorDB] delete skipped because memory is not initialized.")
            except Exception as exc:  # pragma: no cover - non-blocking UI path
                self._ui.log(f"   [VectorDB] delete failed: {exc}")

            self._restore_runtime_state(target_ep)
            self._ui.log(f"\n[Success] Rollback completed to the state before episode {target_ep}.")
            input("\n[Enter] Return to menu")
            self._assert_rollback_invariants(target_ep)
            return True
        except Exception as exc:
            self._rollback_open_transaction(project)
            self._ui.log(f"Rollback failed: {exc}")
            return False

    def _assert_rollback_invariants(self, target_ep: int) -> None:
        """Warn if runtime trackers still carry events at or after target_ep."""
        if self._emotion_tracker_fn and callable(self._emotion_tracker_fn):
            tracker = self._emotion_tracker_fn()
            if tracker is not None and hasattr(tracker, "history") and tracker.history:
                max_ep = max(entry[0] for entry in tracker.history)
                if max_ep >= target_ep:
                    logging.warning(
                        "[RollbackInvariant] EmotionArcTracker max ep=%d >= target_ep=%d after rollback",
                        max_ep,
                        target_ep,
                    )

        if self._state_delta_tracker_fn and callable(self._state_delta_tracker_fn):
            tracker = self._state_delta_tracker_fn()
            if tracker is not None and hasattr(tracker, "energy_history") and tracker.energy_history:
                max_ep = max(entry.episode for entry in tracker.energy_history)
                if max_ep >= target_ep:
                    logging.warning(
                        "[RollbackInvariant] StateDeltaTracker max ep=%d >= target_ep=%d after rollback",
                        max_ep,
                        target_ep,
                    )

    def wipe_production_data(self) -> bool:
        """Delete every episode-derived production artifact while keeping setup data."""
        confirm = input("\nReally wipe manuscripts, blueprints, logs, and episode-derived memory? (y/n): ").strip().lower()
        if confirm != "y":
            return False

        project = self._project_fn()
        try:
            project.db.reset_after(1, commit=False)
            self._clear_narrative_summary_anchors(project)
            project.db.cursor.execute("UPDATE seeds SET status = 'active', recovered_ep = NULL")
            if not self._safe_commit():
                self._rollback_open_transaction(project)
                self._ui.log("DB commit failed during production wipe")
                return False

            self._delete_all_draft_files(project)

            memory = self._memory_fn()
            try:
                if memory and hasattr(memory, "delete_all_episodes"):
                    memory.delete_all_episodes()
            except Exception as exc:  # pragma: no cover - non-blocking UI path
                self._ui.log(f"   [VectorDB] full delete failed: {exc}")

            self._restore_runtime_state(1)
            self._ui.log("[Wipe] Production artifacts were cleared. Setup data remains intact.")
            input("\n[Enter] Return to menu")
            return True
        except Exception as exc:
            self._rollback_open_transaction(project)
            self._ui.log(f"Wipe failed: {exc}")
            return False
