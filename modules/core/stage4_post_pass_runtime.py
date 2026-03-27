"""
Stage 4 post-pass runtime authority.
"""

from __future__ import annotations

import json
import logging
from contextlib import nullcontext as _nullcontext
from typing import TYPE_CHECKING

from modules.core.genre_schema_builder import is_wuxia
from modules.core.inventory_state import compute_inventory_count_deltas, normalize_inventory_counts

if TYPE_CHECKING:
    from modules.core.stage4_post_processor import Stage4PostProcessor


class Stage4PostPassRuntime:
    """Bounded runtime authority for Stage 4 post-pass settlement."""

    def __init__(self, owner: "Stage4PostProcessor") -> None:
        self.owner = owner
        self.ctx = owner.ctx

    # -- [THIN DELEGATE] forwarding to owner -- (8 methods)
    def _report_soft_failure(self, **kwargs) -> None:
        self.owner._report_soft_failure(**kwargs)

    def _raise_if_save_failed(self, **kwargs) -> None:
        self.owner._raise_if_save_failed(**kwargs)

    def _extract_state_change_info(self, state_changes) -> dict:
        return self.owner._extract_state_change_info(state_changes)

    def _truth_gate_llm_ask(self, prompt: str) -> str:
        return self.owner._truth_gate_llm_ask(prompt)

    def _build_active_pressure_vectors(self, blueprint):
        return self.owner._build_active_pressure_vectors(blueprint)

    def _normalize_active_pressure_vectors(self, vectors):
        return self.owner._normalize_active_pressure_vectors(vectors)

    def _persist_karma_status(self, *, karma_matrix, next_ep: int) -> int:
        return self.owner._persist_karma_status(karma_matrix=karma_matrix, next_ep=next_ep)

    def _best_effort_rollback_manager(self, *, manager, label: str, target_ep: int) -> bool:
        return self.owner._best_effort_rollback_manager(
            manager=manager,
            label=label,
            target_ep=target_ep,
        )

    # -- [AUTHORITY] post-pass settlement runtime starts here --
    def _submit_manager_async(self, *, next_ep, final_manuscript, genre_type, critical_keys):
        """[B-1-9a:A1] Manager LLM 비동기 제출 (ThreadPoolExecutor setup).

        Returns dict with bible_future, current_state, lore_list, active_seeds, causal_history.
        """
        current_state = {}
        lore_list = []
        active_seeds = []
        causal_history = ""
        bible_future = None

        try:
            self.ctx.ui.log("   📖 [V60.82] Manager 정산 비동기 제출...")
            from concurrent.futures import ThreadPoolExecutor

            current_state = (
                self.ctx.current_project.latest_state if hasattr(self.ctx.current_project, "latest_state") else {}
            )
            if not current_state and hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
                current_state = {"actual_truth": self.ctx.sys.hud.pro_data}

            if hasattr(self.ctx.current_project, "master_bible"):
                bible_root = self.ctx.current_project.master_bible.get(
                    "MasterBible",
                    self.ctx.current_project.master_bible,
                )
                assets = bible_root.get("AssetLibrary", {})
                lore_list = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])

            if hasattr(self.ctx.current_project, "db"):
                try:
                    seeds_data = self.ctx.current_project.db.load_anchor("active_seeds")
                    if seeds_data:
                        active_seeds = seeds_data if isinstance(seeds_data, list) else []
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logging.warning(f"[V66.3] active_seeds 로드 실패: {e}")

            _manager_agent = self.ctx.agents["manager"]
            _bible_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bible_settle")
            bible_future = _bible_executor.submit(
                _manager_agent.update_state_and_lore_v20,
                ep_num=next_ep,
                manuscript=final_manuscript,
                current_state=current_state,
                lore_list=lore_list,
                active_seeds=active_seeds,
                causal_history=causal_history,
                genre=genre_type,
                critical_keys=critical_keys,
            )
            _bible_executor.shutdown(wait=False, cancel_futures=False)
            self.ctx.ui.log("      ⏳ [S4-I6] Manager 정산 비동기 실행 중...")
        except Exception as _submit_err:
            logging.warning("[S4-I6] 비동기 제출 실패, 동기 폴백 예정: %s", _submit_err)
            bible_future = None

        return {
            "bible_future": bible_future,
            "current_state": current_state,
            "lore_list": lore_list,
            "active_seeds": active_seeds,
            "causal_history": causal_history,
        }

    def _memorize_and_validate(
        self,
        *,
        next_ep,
        final_manuscript,
        final_title,
        final_state_updates,
        arc_data,
        blueprint,
    ):
        """[B-1-9a:A2] VecMemory 저장 + TruthGate advisory 검증."""
        try:
            _mem_arc_no = arc_data.get("arc_no") if arc_data else None
            _sc_raw = final_state_updates if final_state_updates else {}
            _sc_info = self._extract_state_change_info(_sc_raw)
            _mem_event_types = _sc_info["event_types"]
            _mem_entity_names = _sc_info["entity_names"]

            try:
                from modules.core.truth_gate import TruthGate

                _truth_gate = TruthGate(
                    world_state=getattr(self.ctx, "world_state", None),
                    fact_ledger=getattr(self.ctx, "fact_ledger", None),
                    llm_ask=self._truth_gate_llm_ask,
                )
                _npc_reg = None
                if hasattr(self.ctx, "state_tracker") and self.ctx.state_tracker:
                    _npc_reg = getattr(self.ctx.state_tracker, "npc_registry", None)
                _tg_result = _truth_gate.validate(
                    manuscript=final_manuscript,
                    state_updates=_sc_raw,
                    npc_registry=_npc_reg,
                )
                if not _tg_result["passed"]:
                    for _tg_w in _tg_result["warnings"]:
                        self.ctx.ui.log(f"   ⚠️ [TruthGate] {_tg_w}")
                        logging.warning("[TruthGate] %s", _tg_w)
                    for _sw in _tg_result.get("structured_warnings", []):
                        logging.warning(
                            "[TruthGate:POST] [%s] %s",
                            _sw.get("severity", "?"),
                            _sw.get("text", ""),
                        )
            except Exception as _tg_err:
                logging.debug("[TruthGate] 검증 실패 (비차단): %s", _tg_err)

            _slot_event = (
                ", ".join(_sc_info["summary_parts"])[:120]
                if _sc_info["summary_parts"]
                else (final_title or f"제{next_ep}화")
            )
            _slot_chars = ", ".join(sorted(_mem_entity_names)[:5])[:80] if _mem_entity_names else ""
            _slot_place = ""
            _slot_ending = ""
            if isinstance(blueprint, dict):
                _slot_place = str(blueprint.get("end_location", "") or blueprint.get("start_location", "") or "")[:80]
                _slot_ending = str(blueprint.get("ending_hook", "") or blueprint.get("cliffhanger", "") or "")[:80]
            _rich_summary = " | ".join(
                f"{label}: {val}"
                for label, val in [
                    ("사건", _slot_event),
                    ("인물", _slot_chars),
                    ("장소", _slot_place),
                    ("결말", _slot_ending),
                ]
                if val
            )[:500]
            if self.ctx.memory and self.ctx.memory.is_operational():
                _mem_saved = self.ctx.memory.memorize_v20_episode(
                    ep_num=next_ep,
                    text=final_manuscript,
                    summary=_rich_summary,
                    causal_links=[],
                    arc_no=_mem_arc_no,
                    event_types=list(_mem_event_types),
                    entity_names=list(_mem_entity_names),
                )
                if _mem_saved:
                    self.ctx.ui.log(f"   ✅ 벡터 메모리 저장 (arc={_mem_arc_no}, events={_mem_event_types})")
                else:
                    self.ctx.ui.log(f"   ⚠️ [CO-002] 벡터 메모리 저장 실패 ep={next_ep}")
                    logging.warning("[CO-002] memorize_v20_episode ep=%d returned False", next_ep)
        except Exception as _mem_err:
            self.ctx.ui.log(f"   ⚠️ [V63.3] 벡터 메모리 저장 실패 (비차단): {str(_mem_err)[:60]}")

    def _collect_manager_and_build_delta(
        self,
        *,
        next_ep,
        final_manuscript,
        bible_future,
        current_state,
        lore_list,
        active_seeds,
        causal_history,
        genre_type,
        critical_keys,
        final_state_updates,
        blueprint,
    ):
        """[B-1-9a:A3] Manager Future 회수 + bible_delta 조립 + state_log 저장.

        Returns dict with bible_delta, actual_truth, meta_save_failed.
        """
        bible_delta = None
        actual_truth = {}
        _meta_save_failed = False

        try:
            audit = self._resolve_manager_audit(
                next_ep=next_ep,
                final_manuscript=final_manuscript,
                bible_future=bible_future,
                current_state=current_state,
                lore_list=lore_list,
                active_seeds=active_seeds,
                causal_history=causal_history,
                genre_type=genre_type,
                critical_keys=critical_keys,
            )
            manager_delta_context = self._prepare_manager_delta_context(audit=audit, genre_type=genre_type)
            new_lore = manager_delta_context["new_lore"]
            knowledge_map = manager_delta_context["knowledge_map"]
            recovered = manager_delta_context["recovered"]
            state_updates_from_audit = manager_delta_context["state_updates_from_audit"]
            causal_links = manager_delta_context["causal_links"]
            actual_truth = manager_delta_context["actual_truth"]
            prev_actual = manager_delta_context["prev_actual"]
            prev_pressure_vectors = manager_delta_context["prev_pressure_vectors"]
            prev_inventory_counts = manager_delta_context["prev_inventory_counts"]
            curr_inventory_counts = manager_delta_context["curr_inventory_counts"]
            inventory_count_deltas = manager_delta_context["inventory_count_deltas"]

            prev_equipment = set(prev_inventory_counts)
            curr_equipment = set(curr_inventory_counts)
            if is_wuxia(genre_type):
                prev_martial = set(
                    prev_actual.get("martial_arts", []) if isinstance(prev_actual.get("martial_arts"), list) else []
                )
                curr_martial = set(
                    actual_truth.get("martial_arts", []) if isinstance(actual_truth.get("martial_arts"), list) else []
                )
            else:
                prev_martial = set()
                curr_martial = set()

            new_items_from_equip = list(curr_equipment - prev_equipment)
            lost_items_from_equip = list(prev_equipment - curr_equipment)
            new_martial_arts = list(curr_martial - prev_martial)

            key_items = new_lore.get("Key_Items", []) if isinstance(new_lore.get("Key_Items"), list) else []
            key_item_names = [i.get("name", str(i)) if isinstance(i, dict) else str(i) for i in key_items]

            key_npcs = new_lore.get("Key_NPCs", []) if isinstance(new_lore.get("Key_NPCs"), list) else []
            delta_collections = self._build_manager_delta_collections(
                next_ep=next_ep,
                key_npcs=key_npcs,
                knowledge_map=knowledge_map,
                state_updates_from_audit=state_updates_from_audit,
                recovered=recovered,
            )
            new_npc_names = delta_collections["new_npc_names"]
            npc_deaths = delta_collections["npc_deaths"]
            relationship_changes = delta_collections["relationship_changes"]
            karma_matrix = delta_collections["karma_matrix"]
            reveal_list = delta_collections["reveal_list"]
            pressure_payload = self._apply_state_text_and_pressure_vectors(
                actual_truth=actual_truth,
                final_manuscript=final_manuscript,
                genre_type=genre_type,
                critical_keys=critical_keys,
                blueprint=blueprint,
                prev_pressure_vectors=prev_pressure_vectors,
            )
            actual_truth = pressure_payload["actual_truth"]
            active_pressure_vectors = pressure_payload["active_pressure_vectors"]
            pressure_vectors_changed = pressure_payload["pressure_vectors_changed"]

            all_new_items = list(set(new_items_from_equip + key_item_names + new_martial_arts))
            persist_payload = self._persist_manager_delta_outputs(
                next_ep=next_ep,
                key_npcs=key_npcs,
                actual_truth=actual_truth,
                final_state_updates=final_state_updates,
                state_updates_from_audit=state_updates_from_audit,
                knowledge_map=knowledge_map,
                karma_matrix=karma_matrix,
                curr_inventory_counts=curr_inventory_counts,
                inventory_count_deltas=inventory_count_deltas,
                relationship_changes=relationship_changes,
                active_pressure_vectors=active_pressure_vectors,
                pressure_vectors_changed=pressure_vectors_changed,
                causal_links=causal_links,
                all_new_items=all_new_items,
                lost_items_from_equip=lost_items_from_equip,
                new_npc_names=new_npc_names,
                npc_deaths=npc_deaths,
                reveal_list=reveal_list,
            )
            bible_delta = persist_payload["bible_delta"]
            _meta_save_failed = persist_payload["meta_save_failed"]

        except Exception as bible_err:
            self.ctx.ui.log(f"   ⚠️ Episode Bible 저장 실패 (비차단): {str(bible_err)[:50]}")
            import traceback

            traceback.print_exc()

        return {
            "bible_delta": bible_delta,
            "actual_truth": actual_truth,
            "meta_save_failed": _meta_save_failed,
        }

    def _apply_state_text_and_pressure_vectors(
        self,
        *,
        actual_truth,
        final_manuscript,
        genre_type,
        critical_keys,
        blueprint,
        prev_pressure_vectors,
    ) -> dict:
        try:
            stv_enabled = False
            try:
                from modules.validation.threshold_helper import _threshold

                stv_enabled = _threshold("feature_flags.enable_state_text_verifier", False)
            except Exception:
                pass

            if stv_enabled and actual_truth and final_manuscript:
                from modules.core.state_text_verifier import StateTextVerifier

                stv_agent = self.ctx.agents.get("manager") if self.ctx.agents else None
                stv = StateTextVerifier(agent=stv_agent, genre=genre_type, critical_keys=critical_keys)
                stv_result = stv.verify(final_manuscript, actual_truth)
                if not stv_result["verified"] and stv_result["corrections"]:
                    actual_truth = stv.apply_corrections(actual_truth, stv_result["corrections"])
                    self.ctx.ui.log(
                        f"      🧪 [V75] State-Text 검증 {len(stv_result['mismatches'])}건 불일치 →"
                        f"{len(stv_result['corrections'])}건 수정"
                    )
                elif not stv_result["verified"]:
                    self.ctx.ui.log(
                        f"      ⚠️ [V75] State-Text 검증 {len(stv_result['mismatches'])}건 불일치 발견 (수정 불가)"
                    )
        except Exception as stv_err:
            logging.warning("[SilentPass:V75] State-Text 검증 모듈 실패: %s", stv_err)

        active_pressure_vectors = self._build_active_pressure_vectors(blueprint)
        pressure_vectors_changed = prev_pressure_vectors != active_pressure_vectors
        if active_pressure_vectors or pressure_vectors_changed:
            if not isinstance(actual_truth, dict):
                actual_truth = {}
            actual_truth["active_pressure_vectors"] = list(active_pressure_vectors)

        return {
            "actual_truth": actual_truth,
            "active_pressure_vectors": active_pressure_vectors,
            "pressure_vectors_changed": pressure_vectors_changed,
        }

    def _resolve_manager_audit(
        self,
        *,
        next_ep,
        final_manuscript,
        bible_future,
        current_state,
        lore_list,
        active_seeds,
        causal_history,
        genre_type,
        critical_keys,
    ) -> dict:
        try:
            if bible_future is not None:
                self.ctx.ui.log(
                    "      ⏳ Manager 정산 대기: 비동기 audit future 완료를 기다리는 중...",
                    stage="stage4",
                    component="post_pass_manager",
                    ep_num=next_ep,
                    event_kind="heartbeat",
                    meta={"wait_state": "manager_future_result", "timeout_seconds": 120},
                )
                raw_audit = bible_future.result(timeout=120)
            else:
                raw_audit = self.ctx.agents["manager"].update_state_and_lore_v20(
                    ep_num=next_ep,
                    manuscript=final_manuscript,
                    current_state=current_state,
                    lore_list=lore_list,
                    active_seeds=active_seeds,
                    causal_history=causal_history,
                    genre=genre_type,
                    critical_keys=critical_keys,
                )

            if raw_audit and not raw_audit.get("parsing_error"):
                self.ctx.ui.log("      ✅ Manager 정산 완료")
                return raw_audit

            self.ctx.ui.log("      ⚠️ Manager 파싱 실패, 기본 추출 사용")
            logging.error("[XC-002] Manager LLM 파싱 실패 — bible_delta 미생성으로 FactLedger 갱신 불완전할 수 있음")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("manager_parse_failure", "Manager LLM 파싱 실패", {"ep": next_ep})
            return {}
        except Exception as mgr_err:
            if bible_future is not None and hasattr(bible_future, "cancel"):
                bible_future.cancel()
            self.ctx.ui.log(f"      ⚠️ Manager 호출 실패: {str(mgr_err)[:50]}")
            if bible_future is not None:
                self.ctx.ui.log(
                    "      ↪ Manager future 대기 실패로 동기 재시도 전환",
                    stage="stage4",
                    component="post_pass_manager",
                    ep_num=next_ep,
                    event_kind="summary",
                    meta={"fallback_mode": "sync_retry"},
                )
            logging.warning("[B-1] Manager 정산 실패 — 동기 재시도: %s", mgr_err)
            try:
                raw_audit = self.ctx.agents["manager"].update_state_and_lore_v20(
                    ep_num=next_ep,
                    manuscript=final_manuscript,
                    current_state=current_state,
                    lore_list=lore_list,
                    active_seeds=active_seeds,
                    causal_history=causal_history,
                    genre=genre_type,
                    critical_keys=critical_keys,
                )
                if raw_audit and not raw_audit.get("parsing_error"):
                    self.ctx.ui.log("      ✅ Manager 동기 재시도 성공")
                    return raw_audit
            except Exception as retry_err:
                logging.error("[XC-002] Manager 동기 재시도도 실패: %s", retry_err)
                logging.error("[XC-002] Manager LLM 완전 실패 — bible_delta=None, FactLedger 갱신 건너뜀")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("manager_complete_failure", "Manager LLM 완전 실패", {"ep": next_ep})
            return {}

    def _prepare_manager_delta_context(self, *, audit, genre_type) -> dict:
        new_lore = audit.get("new_lore", {}) if isinstance(audit, dict) else {}
        knowledge_map = audit.get("knowledge_map_updates", {}) if isinstance(audit, dict) else {}
        recovered = audit.get("recovered_seeds", []) if isinstance(audit, dict) else []
        state_updates_from_audit = audit.get("state_updates", {}) if isinstance(audit, dict) else {}
        causal_links = audit.get("causal_links", []) if isinstance(audit, dict) else []

        actual_truth = (
            state_updates_from_audit.get("actual_truth", {}) if isinstance(state_updates_from_audit, dict) else {}
        )

        prev_actual = {}
        if hasattr(self.ctx.current_project, "latest_state"):
            prev_actual = self.ctx.current_project.latest_state.get("actual_truth", {})
        prev_pressure_vectors = self._normalize_active_pressure_vectors(
            prev_actual.get("active_pressure_vectors", []) if isinstance(prev_actual, dict) else []
        )

        prev_inventory_counts = normalize_inventory_counts(
            prev_actual.get("inventory_counts") if isinstance(prev_actual, dict) else {}
        )
        if not prev_inventory_counts and isinstance(prev_actual, dict):
            prev_inventory_counts = normalize_inventory_counts(prev_actual.get("equipment", []))

        curr_inventory_counts = normalize_inventory_counts(
            actual_truth.get("inventory_counts") if isinstance(actual_truth, dict) else {}
        )
        if not curr_inventory_counts and isinstance(actual_truth, dict):
            curr_inventory_counts = normalize_inventory_counts(actual_truth.get("equipment", []))
        if curr_inventory_counts and isinstance(actual_truth, dict):
            actual_truth["inventory_counts"] = curr_inventory_counts

        inventory_count_deltas = compute_inventory_count_deltas(prev_inventory_counts, curr_inventory_counts)

        return {
            "new_lore": new_lore,
            "knowledge_map": knowledge_map,
            "recovered": recovered,
            "state_updates_from_audit": state_updates_from_audit,
            "causal_links": causal_links,
            "actual_truth": actual_truth,
            "prev_actual": prev_actual,
            "prev_pressure_vectors": prev_pressure_vectors,
            "prev_inventory_counts": prev_inventory_counts,
            "curr_inventory_counts": curr_inventory_counts,
            "inventory_count_deltas": inventory_count_deltas,
        }

    def _merge_manager_key_npcs_into_master_bible(self, *, next_ep: int, key_npcs: list) -> None:
        try:
            master_bible = getattr(self.ctx.current_project, "master_bible", None)
            if not master_bible or not isinstance(master_bible, dict) or not key_npcs:
                return

            master_bible_root = master_bible.get("MasterBible", master_bible)
            assets = master_bible_root.setdefault("AssetLibrary", {})
            existing_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])
            if not existing_npcs:
                existing_npcs = []

            npc_by_name = {}
            for index, existing_npc in enumerate(existing_npcs):
                if isinstance(existing_npc, dict):
                    existing_name = existing_npc.get("name", "") or existing_npc.get("Name", "")
                    if existing_name:
                        npc_by_name[existing_name] = index

            merged_count = 0
            for new_npc in key_npcs:
                if not isinstance(new_npc, dict):
                    continue
                npc_name = new_npc.get("name", "") or new_npc.get("Name", "")
                if not npc_name:
                    continue
                if npc_name in npc_by_name:
                    existing_index = npc_by_name[npc_name]
                    for key, value in new_npc.items():
                        if key in ("name", "Name"):
                            continue
                        if value and (
                            not existing_npcs[existing_index].get(key)
                            or str(value) != str(existing_npcs[existing_index].get(key))
                        ):
                            existing_npcs[existing_index][key] = value
                    merged_count += 1
                else:
                    existing_npcs.append(new_npc)
                    npc_by_name[npc_name] = len(existing_npcs) - 1
                    merged_count += 1

            if merged_count > 0:
                assets["KeyNPCs"] = existing_npcs
                logging.debug("[CON-2-FIX] master_bible.KeyNPCs 병합: %d건 (ep=%d)", merged_count, next_ep)
        except Exception as master_bible_merge_err:
            logging.warning(
                "[CON-2-FIX] master_bible NPC 병합 실패 (비치명): %s",
                str(master_bible_merge_err)[:80],
            )

    def _build_manager_delta_collections(
        self,
        *,
        next_ep: int,
        key_npcs: list,
        knowledge_map,
        state_updates_from_audit,
        recovered,
    ) -> dict:
        new_npc_names = [npc.get("name", str(npc)) if isinstance(npc, dict) else str(npc) for npc in key_npcs]
        self._merge_manager_key_npcs_into_master_bible(next_ep=next_ep, key_npcs=key_npcs)

        npc_deaths = []
        for npc in key_npcs:
            if isinstance(npc, dict):
                status = (npc.get("NPC_Martial_HUD") or {}).get("current_status", "")
                if "사망" in str(status) or "죽" in str(status) or "절명" in str(status):
                    npc_deaths.append(npc.get("name", ""))

        relationship_changes = []
        if isinstance(knowledge_map, dict):
            witnesses = knowledge_map.get("new_witnesses", [])
            misled = knowledge_map.get("new_misled", [])
            if witnesses:
                relationship_changes.extend([{"npc": witness, "to": "목격자", "from": ""} for witness in witnesses if witness])
            if misled:
                relationship_changes.extend([{"npc": misled_npc, "to": "오해 대상", "from": ""} for misled_npc in misled if misled_npc])

        karma_matrix = state_updates_from_audit.get("karma_matrix", [])
        if isinstance(karma_matrix, list):
            for karma in karma_matrix:
                if isinstance(karma, dict) and karma.get("target"):
                    obsession = karma.get("obsession", 0)
                    misunderstanding = karma.get("value", 0)
                    if obsession > 50 or misunderstanding > 50:
                        relationship_changes.append(
                            {
                                "npc": karma["target"],
                                "to": f"집착{obsession}/오해{misunderstanding}",
                                "from": "",
                            }
                        )

        reveal_list = []
        if isinstance(recovered, list):
            for seed in recovered:
                if isinstance(seed, dict):
                    reveal_list.append(seed.get("seed_id", seed.get("description", str(seed))))
                else:
                    reveal_list.append(str(seed))

        # [IFC] Producer-side normalization: scalarize actor references before persistence
        try:
            from modules.core.stage4_immutable_fact_contract import normalize_relationship_changes

            relationship_changes = normalize_relationship_changes(relationship_changes)
        except Exception as _exc:
            logging.debug("[IFC] relationship normalization non-blocking: %s", _exc)

        return {
            "new_npc_names": new_npc_names,
            "npc_deaths": npc_deaths,
            "relationship_changes": relationship_changes,
            "karma_matrix": karma_matrix,
            "reveal_list": reveal_list,
        }

    def _persist_manager_delta_outputs(
        self,
        *,
        next_ep: int,
        key_npcs: list,
        actual_truth,
        final_state_updates,
        state_updates_from_audit,
        knowledge_map,
        karma_matrix,
        curr_inventory_counts,
        inventory_count_deltas,
        relationship_changes,
        active_pressure_vectors,
        pressure_vectors_changed: bool,
        causal_links,
        all_new_items: list,
        lost_items_from_equip: list,
        new_npc_names: list,
        npc_deaths: list,
        reveal_list: list,
    ) -> dict:
        bible_delta = {
            "new_items": all_new_items,
            "lost_items": lost_items_from_equip,
            "new_npcs": new_npc_names,
            "npc_deaths": npc_deaths,
            "relationship_changes": relationship_changes,
            "state_changes": actual_truth if actual_truth else final_state_updates,
            "time_passed": state_updates_from_audit.get("time_passed", ""),
            "reveals": reveal_list,
            "causal_links": causal_links,
            "karma_matrix": karma_matrix,
            "knowledge_map": knowledge_map,
            "inventory_counts": curr_inventory_counts,
            "inventory_count_deltas": inventory_count_deltas,
        }
        if active_pressure_vectors or pressure_vectors_changed:
            bible_delta["active_pressure_vectors"] = list(active_pressure_vectors)

        logging.debug(
            "[P2] bible_delta ep=%d: items=%d, npcs=%d, deaths=%d",
            next_ep,
            len(all_new_items),
            len(new_npc_names),
            len(npc_deaths),
        )

        meta_save_failed = False
        try:
            self.ctx.current_project.db.save_episode_bible(next_ep, bible_delta)
        except Exception as bible_save_err:
            self.ctx.ui.log(f"      ⚠️ Episode Bible DB 저장 실패 (bible_delta 구성은 성공): {str(bible_save_err)[:50]}")
            logging.error("[S4-001] save_episode_bible 실패 ep=%d: %s", next_ep, bible_save_err)
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("episode_bible_save_failed", "save_episode_bible 실패", {"ep": next_ep})
            meta_save_failed = True

        self._sync_world_state_positions(next_ep=next_ep, key_npcs=key_npcs)
        self._persist_manager_causal_side_effects(next_ep=next_ep, causal_links=causal_links)
        self._persist_manager_state_log(
            next_ep=next_ep,
            actual_truth=actual_truth,
            final_state_updates=final_state_updates,
            state_updates_from_audit=state_updates_from_audit,
            knowledge_map=knowledge_map,
            karma_matrix=karma_matrix,
            curr_inventory_counts=curr_inventory_counts,
            inventory_count_deltas=inventory_count_deltas,
            relationship_changes=relationship_changes,
            active_pressure_vectors=active_pressure_vectors,
            pressure_vectors_changed=pressure_vectors_changed,
            all_new_items=all_new_items,
        )
        self._persist_karma_status(karma_matrix=karma_matrix, next_ep=next_ep)
        self._log_manager_delta_summary(
            all_new_items=all_new_items,
            lost_items_from_equip=lost_items_from_equip,
            new_npc_names=new_npc_names,
            npc_deaths=npc_deaths,
            relationship_changes=relationship_changes,
            active_pressure_vectors=active_pressure_vectors,
            reveal_list=reveal_list,
        )

        return {
            "bible_delta": bible_delta,
            "meta_save_failed": meta_save_failed,
        }

    def _sync_world_state_positions(self, *, next_ep: int, key_npcs: list) -> None:
        try:
            world_state = getattr(self.ctx, "world_state", None)
            if world_state and key_npcs:
                for npc in key_npcs:
                    if not isinstance(npc, dict):
                        continue
                    npc_name = npc.get("name", "") or npc.get("Name", "")
                    npc_position = npc.get("position", "") or npc.get("role", "")
                    if npc_name and npc_position:
                        alive_npcs = world_state._state.get("alive_npcs", {})
                        if npc_name not in alive_npcs:
                            alive_npcs[npc_name] = {
                                "first_seen_ep": next_ep,
                                "role_at_intro": npc_position,
                                "known_attrs": {},
                            }
                        npc_entry = alive_npcs[npc_name]
                        known_attrs = npc_entry.setdefault("known_attrs", {})
                        old_position = ""
                        if isinstance(known_attrs.get("position"), dict):
                            old_position = known_attrs["position"].get("value", "")
                        if old_position != npc_position:
                            known_attrs["position"] = {
                                "value": npc_position,
                                "prev": old_position,
                                "changed_ep": next_ep,
                            }
                            if old_position:
                                logging.info(
                                    "[CON-2-FIX] NPC '%s' 직함 변경 감지: '%s' -> '%s' (ep=%d)",
                                    npc_name,
                                    old_position,
                                    npc_position,
                                    next_ep,
                                )
        except Exception as world_state_position_err:
            logging.warning(
                "[CON-2-FIX] WorldState NPC position 전파 실패 (비치명): %s",
                str(world_state_position_err)[:80],
            )

    def _persist_manager_causal_side_effects(self, *, next_ep: int, causal_links) -> None:
        if causal_links:
            try:
                self.ctx.current_project.db.save_causal_links(causal_links, next_ep)
            except Exception as causal_graph_write_err:
                logging.debug("[Stage4] causal_graph dual-write 실패 (비치명): %s", causal_graph_write_err)

        try:
            recent_causal_links = self.ctx.current_project.db.get_recent_causal_links(next_ep, lookback=30)
            if recent_causal_links:
                causal_lines = ["[결과 관계 요약]"]
                for link in recent_causal_links[:8]:
                    cause = link.get("cause", "") or link.get("trigger", "")
                    effect = link.get("effect", "") or link.get("consequence", "")
                    ep_num = link.get("ep", "?")
                    if cause and effect:
                        causal_lines.append(f"- ep{ep_num}: {cause} -> {effect}")
                if len(causal_lines) > 1:
                    director_mc_parts = getattr(self.ctx, "_director_mc_parts", None)
                    if isinstance(director_mc_parts, list):
                        director_mc_parts.append("\n".join(causal_lines))
                    logging.debug("[causal_graph] Director MC 결과 컨텍스트 주입: %d건", len(causal_lines) - 1)
        except Exception as causal_graph_read_err:
            logging.debug("[causal_graph] Director MC 주입 실패 (비치명): %s", causal_graph_read_err)

    def _persist_manager_state_log(
        self,
        *,
        next_ep: int,
        actual_truth,
        final_state_updates,
        state_updates_from_audit,
        knowledge_map,
        karma_matrix,
        curr_inventory_counts,
        inventory_count_deltas,
        relationship_changes,
        active_pressure_vectors,
        pressure_vectors_changed: bool,
        all_new_items: list,
    ) -> None:
        should_persist_state_log = any(
            [
                actual_truth,
                state_updates_from_audit,
                knowledge_map,
                karma_matrix,
                curr_inventory_counts,
                inventory_count_deltas,
                relationship_changes,
                active_pressure_vectors,
                pressure_vectors_changed,
            ]
        )
        if not should_persist_state_log:
            return

        state_log_data = {
            "actual_truth": actual_truth if actual_truth else final_state_updates,
            "karma_matrix": karma_matrix,
            "knowledge_map": knowledge_map,
            "public_reputation": state_updates_from_audit.get("public_reputation", {}),
            "inventory_counts": curr_inventory_counts,
            "inventory_count_deltas": inventory_count_deltas,
            "relationship_changes": relationship_changes,
            "active_pressure_vectors": list(active_pressure_vectors),
        }
        try:
            summary = f"제{next_ep}화 정산: {', '.join(all_new_items[:3]) if all_new_items else '변화없음'}"
            self.ctx.current_project.db.save_state_log_with_summary(next_ep, state_log_data, summary)
        except Exception as state_err:
            self._report_soft_failure(
                operation="save_state_log_with_summary",
                message="state_logs summary save failed after episode bible update",
                exc=state_err,
                ep_num=next_ep,
                extra={"table": "state_logs"},
            )
            self.ctx.ui.log(f"      ⚠️ state_logs 저장 실패: {str(state_err)[:30]}")

    def _log_manager_delta_summary(
        self,
        *,
        all_new_items: list,
        lost_items_from_equip: list,
        new_npc_names: list,
        npc_deaths: list,
        relationship_changes: list,
        active_pressure_vectors: list,
        reveal_list: list,
    ) -> None:
        changes_count = (
            len(all_new_items)
            + len(lost_items_from_equip)
            + len(new_npc_names)
            + len(npc_deaths)
            + len(relationship_changes)
            + len(active_pressure_vectors)
            + len(reveal_list)
        )
        if changes_count > 0:
            self.ctx.ui.log(f"   📖 Episode Bible 저장 {changes_count}개 변화 기록")
            if all_new_items:
                self.ctx.ui.log(f"      • 신규 아이템/무공: {', '.join(all_new_items[:5])}")
            if new_npc_names:
                self.ctx.ui.log(f"      • 신규/갱신 NPC: {', '.join(new_npc_names[:5])}")
            if npc_deaths:
                self.ctx.ui.log(f"      • NPC 사망: {', '.join(npc_deaths)}")
            if active_pressure_vectors:
                self.ctx.ui.log(
                    "      • 지속 압박/위협: "
                    + ", ".join(vector.get("text", "")[:40] for vector in active_pressure_vectors[:2])
                )
            if reveal_list:
                self.ctx.ui.log(f"      • 복선 회수: {', '.join(reveal_list[:3])}")
        else:
            self.ctx.ui.log("   📖 Episode Bible 저장 완료 (변화 없음)")

    def _build_atomic_state_payloads(self, *, final_state_updates, bible_delta):
        inventory_payload = {}
        relationship_payload = {}
        pressure_payload = {}

        if isinstance(bible_delta, dict):
            inventory_counts = bible_delta.get("inventory_counts")
            inventory_count_deltas = bible_delta.get("inventory_count_deltas")
            if isinstance(inventory_counts, dict) and inventory_counts:
                inventory_payload["inventory_counts"] = dict(inventory_counts)
            if isinstance(inventory_count_deltas, list) and inventory_count_deltas:
                inventory_payload["inventory_count_deltas"] = list(inventory_count_deltas)

            relationship_changes = bible_delta.get("relationship_changes")
            if isinstance(relationship_changes, list) and relationship_changes:
                relationship_payload["relationship_changes"] = list(relationship_changes)

            state_changes = bible_delta.get("state_changes")
            pressure_vectors = None
            if "active_pressure_vectors" in bible_delta:
                pressure_vectors = bible_delta.get("active_pressure_vectors")
            elif isinstance(state_changes, dict) and "active_pressure_vectors" in state_changes:
                pressure_vectors = state_changes.get("active_pressure_vectors")
            if isinstance(pressure_vectors, list):
                pressure_payload["active_pressure_vectors"] = list(pressure_vectors)

        world_state_changes = dict(final_state_updates or {})
        if inventory_payload:
            world_state_changes.update(inventory_payload)
        if relationship_payload:
            world_state_changes.update(relationship_payload)
        if pressure_payload:
            world_state_changes.update(pressure_payload)

        fact_ledger_changes = dict(final_state_updates or {})
        if inventory_payload:
            fact_ledger_changes.update(inventory_payload)
        if relationship_payload:
            fact_ledger_changes.update(relationship_payload)

        return {
            "world_state_changes": world_state_changes,
            "fact_ledger_changes": fact_ledger_changes,
        }

    def _capture_atomic_metadata_snapshots(self):
        import copy as _copy

        try:
            world_state_snapshot = _copy.deepcopy(self.ctx.world_state._state) if self.ctx.world_state else None
        except Exception:
            world_state_snapshot = None
        try:
            fact_ledger_snapshot = _copy.deepcopy(self.ctx.fact_ledger._ledger) if self.ctx.fact_ledger else None
        except Exception:
            fact_ledger_snapshot = None

        return {
            "world_state_snapshot": world_state_snapshot,
            "fact_ledger_snapshot": fact_ledger_snapshot,
        }

    def _persist_atomic_world_state(self, *, next_ep, world_state_changes) -> bool:
        if not self.ctx.world_state:
            return False

        if world_state_changes:
            self.ctx.world_state.update_from_state_changes(next_ep, world_state_changes)

        world_state_protagonist_name = ""
        try:
            world_state_bible_root = self.ctx.current_project.master_bible.get(
                "MasterBible",
                self.ctx.current_project.master_bible,
            )
            world_state_protagonist_name = world_state_bible_root.get("protagonist_config", {}).get("name", "")
        except Exception as e:
            logging.warning(f"[SilentPass:PostProcessor] 주인공 이름 추출 실패: {e!s:.100}")

        self.ctx.world_state.update_protagonist_state(
            ep_num=next_ep,
            name=world_state_protagonist_name if world_state_protagonist_name else None,
        )
        world_state_saved = self.ctx.world_state.save()
        self._raise_if_save_failed(manager=self.ctx.world_state, label="WorldState", save_result=world_state_saved)

        try:
            self.ctx.ui.log(f"   🌍 [V68] 세계 상태 갱신 완료 (제{next_ep}화)")
        except Exception as ui_err:
            logging.warning("[TF-C10] WorldState post-save UI log 실패: %s", ui_err)

        session_logger = getattr(self.ctx, "session_logger", None)
        if session_logger and world_state_changes:
            try:
                session_logger.log_state_change(
                    ep_num=next_ep,
                    change_type="world_state",
                    after=world_state_changes,
                    source="stage4_post_processor",
                )
            except Exception:
                pass

        return True

    def _persist_atomic_fact_ledger(self, *, next_ep, fact_ledger_changes, bible_delta) -> bool:
        if not self.ctx.fact_ledger:
            return False

        if fact_ledger_changes:
            self.ctx.fact_ledger.update_from_state_changes(next_ep, fact_ledger_changes)
        if bible_delta:
            try:
                self.ctx.fact_ledger.update_from_bible_delta(next_ep, bible_delta)
            except Exception as bible_delta_err:
                logging.warning("[V70] bible_delta 갱신 실패 (비차단): %s", bible_delta_err)

        fact_ledger_saved = self.ctx.fact_ledger.save()
        self._raise_if_save_failed(manager=self.ctx.fact_ledger, label="FactLedger", save_result=fact_ledger_saved)

        try:
            fact_ledger_stats = self.ctx.fact_ledger.get_stats()
        except Exception as stats_err:
            logging.warning("[TF-C10] FactLedger post-save stats 조회 실패: %s", stats_err)
            fact_ledger_stats = {}

        try:
            self.ctx.ui.log(
                f"   📋 [V68] 팩트 원장 갱신 완료 (인물 {fact_ledger_stats.get('characters', 0)}명, 아이템 {fact_ledger_stats.get('items', 0)}개)"
            )
        except Exception as ui_err:
            logging.warning("[TF-C10] FactLedger post-save UI log 실패: %s", ui_err)

        session_logger = getattr(self.ctx, "session_logger", None)
        if session_logger and fact_ledger_changes:
            try:
                session_logger.log_state_change(
                    ep_num=next_ep,
                    change_type="fact_ledger",
                    after=fact_ledger_changes,
                    source="stage4_post_processor",
                )
            except Exception:
                pass

        return True

    def _handle_atomic_metadata_failure(
        self,
        *,
        next_ep,
        meta_err,
        sequential_mode,
        world_state_persisted,
        fact_ledger_persisted,
        world_state_snapshot,
        fact_ledger_snapshot,
    ) -> None:
        persisted_rollbacks = []
        world_state_restored_via_rollback = False
        fact_ledger_restored_via_rollback = False

        if sequential_mode:
            if fact_ledger_persisted and self.ctx.fact_ledger:
                fact_ledger_restored_via_rollback = self._best_effort_rollback_manager(
                    manager=self.ctx.fact_ledger,
                    label="FactLedger",
                    target_ep=next_ep,
                )
                if fact_ledger_restored_via_rollback:
                    persisted_rollbacks.append("FactLedger")
            if world_state_persisted and self.ctx.world_state:
                world_state_restored_via_rollback = self._best_effort_rollback_manager(
                    manager=self.ctx.world_state,
                    label="WorldState",
                    target_ep=next_ep,
                )
                if world_state_restored_via_rollback:
                    persisted_rollbacks.append("WorldState")

        if world_state_snapshot is not None and self.ctx.world_state and not world_state_restored_via_rollback:
            self.ctx.world_state._state = world_state_snapshot
        if fact_ledger_snapshot is not None and self.ctx.fact_ledger and not fact_ledger_restored_via_rollback:
            self.ctx.fact_ledger._ledger = fact_ledger_snapshot

        self._report_soft_failure(
            operation="save_world_state_atomic",
            message="world state/fact ledger atomic save failed and was rolled back",
            exc=meta_err,
            ep_num=next_ep,
            extra={
                "rolled_back": True,
                "sequential_mode": sequential_mode,
                "persisted_rollbacks": persisted_rollbacks,
            },
        )
        self.ctx.ui.log(f"   ⚠️ [TF-C10] 메타데이터 원자적 저장 실패 (비차단): {str(meta_err)[:60]}")

    def _save_world_state_atomic(self, *, next_ep, final_state_updates, bible_delta):
        """[B-1-9a:A4] WorldState + FactLedger 원자적 갱신 + 롤백.

        Void return. On failure raises → caught by caller's
        _handle_atomic_metadata_failure which sets meta_save_failed.
        """
        meta_db = getattr(self.ctx.current_project, "db", None)
        payloads = self._build_atomic_state_payloads(
            final_state_updates=final_state_updates,
            bible_delta=bible_delta,
        )
        snapshots = self._capture_atomic_metadata_snapshots()

        sequential_mode = False
        world_state_persisted = False
        fact_ledger_persisted = False

        try:
            txn = meta_db.transaction() if meta_db and hasattr(meta_db, "transaction") else None
            sequential_mode = txn is None
            context_manager = txn if txn is not None else _nullcontext()
            if sequential_mode and (self.ctx.world_state or self.ctx.fact_ledger):
                logging.warning("[TF-C10] metadata transaction unavailable; using sequential save recovery mode")
                try:
                    self.ctx.ui.log("   ⚠️ [TF-C10] 메타데이터 트랜잭션 없음: 순차 저장 복구 모드")
                except Exception:
                    pass

            with context_manager:
                world_state_persisted = self._persist_atomic_world_state(
                    next_ep=next_ep,
                    world_state_changes=payloads["world_state_changes"],
                )
                fact_ledger_persisted = self._persist_atomic_fact_ledger(
                    next_ep=next_ep,
                    fact_ledger_changes=payloads["fact_ledger_changes"],
                    bible_delta=bible_delta,
                )
        except Exception as meta_err:
            self._handle_atomic_metadata_failure(
                next_ep=next_ep,
                meta_err=meta_err,
                sequential_mode=sequential_mode,
                world_state_persisted=world_state_persisted,
                fact_ledger_persisted=fact_ledger_persisted,
                world_state_snapshot=snapshots["world_state_snapshot"],
                fact_ledger_snapshot=snapshots["fact_ledger_snapshot"],
            )

    def _run_post_pass_satisfaction_and_pacing(
        self,
        *,
        next_ep,
        final_manuscript,
    ) -> None:
        try:
            _sat_db = getattr(self.ctx.current_project, "db", None)
            _sat_extractor = self.ctx.agents.get("state_extractor") if self.ctx.agents else None
            if _sat_db and _sat_extractor:
                _sat_tag = _sat_extractor.extract_satisfaction_tag(final_manuscript, next_ep)
                if _sat_tag:
                    _sat_db.save_satisfaction_tag(next_ep, _sat_tag)
                    self.ctx.ui.log(
                        f"   🏷️ 만족도 태그: {_sat_tag['primary_tag']} "
                        f"({_sat_tag['satisfaction_score']}/10, {_sat_tag['protagonist_agency']})"
                    )
        except Exception as _sat_err:
            logging.warning("[D Step 3] 만족도 태깅 실패 (비차단): %s", _sat_err)

        try:
            _pace_db = getattr(self.ctx.current_project, "db", None)
            _pace_analyzer = self.ctx.pacing_analyzer if hasattr(self.ctx, "pacing_analyzer") else None
            if _pace_db and _pace_analyzer and final_manuscript and len(final_manuscript) >= 100:
                _pacing_result = _pace_analyzer.analyze(final_manuscript)
                _pace_db.save_pacing_record(
                    next_ep,
                    {
                        "pacing_score": _pacing_result.pacing_score,
                        "dialogue_ratio": round(_pacing_result.dialogue_ratio, 3),
                        "scene_break_count": _pacing_result.scene_break_count,
                        "avg_sentence_length": round(_pacing_result.avg_sentence_length, 1),
                        "short_sentence_ratio": round(_pacing_result.short_sentence_ratio, 3),
                        "long_sentence_ratio": round(_pacing_result.long_sentence_ratio, 3),
                        "issues": _pacing_result.issues[:5],
                    },
                )
                self.ctx.ui.log(
                    f"   📊 [TF-I24] 호흡 분석 저장: 점수 {_pacing_result.pacing_score}/100, "
                    f"대화 {_pacing_result.dialogue_ratio:.0%}, 장면전환 {_pacing_result.scene_break_count}회"
                )
        except Exception as _pace_err:
            logging.warning("[TF-I24] 호흡 분석 저장 실패 (비차단): %s", _pace_err)

    def _record_post_pass_quality_dashboard(
        self,
        *,
        next_ep,
        final_manuscript,
        blueprint,
        final_state_updates,
        quality_labels=None,
        quality_signals=None,
    ) -> None:
        if not self.ctx.quality_dashboard:
            return

        try:
            _director = self.ctx.agents.get("director") if self.ctx.agents else None
            _coverage_validator = getattr(_director, "_validate_blueprint_completeness_v60", None)
            if callable(_coverage_validator) and final_manuscript and isinstance(blueprint, dict):
                _coverage_result = _coverage_validator(final_manuscript, blueprint)
                if isinstance(_coverage_result, dict):
                    self.ctx.quality_dashboard.record_blueprint_coverage(
                        ep_num=next_ep,
                        coverage_result=_coverage_result,
                    )
        except Exception as _bp_cov_err:
            logging.warning("[TF-LP] blueprint coverage instrumentation 실패 (비차단): %s", _bp_cov_err)

        try:
            _stage4_score = 0
            if isinstance(quality_labels, dict):
                _cand_score = quality_labels.get("score", 0)
                if isinstance(_cand_score, int | float):
                    _stage4_score = int(_cand_score)
            elif isinstance(final_state_updates, dict):
                _cand_score = final_state_updates.get("director_score", 0)
                if isinstance(_cand_score, int | float):
                    _stage4_score = int(_cand_score)
            self.ctx.quality_dashboard.record_validation(
                ep_num=next_ep,
                result={
                    "decision": "PASS",
                    "score": _stage4_score,
                    "quality_signals": quality_signals or {},
                },
                stage=4,
            )
            _regression = self.ctx.quality_dashboard.detect_score_regression(stage=4)
            if _regression.get("is_regression"):
                logging.warning(
                    "[Phase 3-QR] 품질 회귀 감지 — 제%d화: delta=%s, severity=%s",
                    next_ep,
                    _regression.get("delta"),
                    _regression.get("severity"),
                )
                self.ctx.ui.log(
                    f"   ⚠️ [품질 회귀] 직전 Arc 대비 {_regression.get('delta')}점 하락 "
                    f"(severity: {_regression.get('severity')})"
                )
            elif _regression.get("severity") == "warning":
                self.ctx.ui.log(f"   📊 [품질 경고] 직전 Arc 대비 {_regression.get('delta')}점 하락")
        except Exception as _qr_err:
            logging.warning("[Phase 3-QR] 품질 회귀 감지 실패 (비차단): %s", _qr_err)

    def _run_post_pass_npc_and_repetition_guards(
        self,
        *,
        next_ep,
        final_manuscript,
        detect_npc_overexposure_fn,
        detect_cross_episode_repetition_fn,
    ) -> None:
        if self.ctx.state_tracker and getattr(self.ctx.state_tracker, "npc_registry", None):
            try:
                from modules.validation.threshold_helper import _threshold

                _max_m = _threshold("npc_exposure.max_mentions_per_episode", 15)
                _min_len = _threshold("npc_exposure.min_name_length", 2)
                _npc_names = list(self.ctx.state_tracker.npc_registry.keys())
                _prot_name = (self.ctx.get_protagonist_name() or "") if self.ctx.get_protagonist_name else ""
                _core = set()
                try:
                    _bible_root = self.ctx.current_project.master_bible.get(
                        "MasterBible",
                        self.ctx.current_project.master_bible,
                    )
                    _assets = _bible_root.get("AssetLibrary", {})
                    for _npc in _assets.get("KeyNPCs", []) or _assets.get("Key_NPCs", []):
                        if isinstance(_npc, dict) and _npc.get("name"):
                            _core.add(_npc["name"])
                except Exception as e:
                    logging.warning(f"[SilentPass:PostProcessor] Core NPC 목록 추출 실패 (전수 검사 폴백): {e!s:.100}")
                _overexposure = None
                if detect_npc_overexposure_fn:
                    _overexposure = detect_npc_overexposure_fn(
                        final_manuscript,
                        _npc_names,
                        _prot_name,
                        max_mentions=_max_m,
                        core_npc_names=frozenset(_core),
                        min_name_length=_min_len,
                    )
                if _overexposure:
                    logging.warning(
                        "[Phase 3-5C] NPC 과잉 등장 — 제%d화: %s",
                        next_ep,
                        _overexposure["warning"],
                    )
                    self.ctx.ui.log(f"   ⚠️ {_overexposure['warning']}")
            except Exception as _npc_err:
                logging.warning("[Phase 3-5C] NPC 과잉 등장 감지 실패 (비차단): %s", _npc_err)

        try:
            from modules.validation.threshold_helper import _threshold
            from modules.core.repetition_guard import RepetitionGuard

            _cr_enabled = _threshold("cross_episode_repetition.enabled", True)
            if _cr_enabled:
                _cr_lookback = _threshold("cross_episode_repetition.lookback_episodes", 5)
                _cr_min_len = _threshold("cross_episode_repetition.min_sentence_length", 15)
                _cr_warn = _threshold("cross_episode_repetition.overlap_warning", 3)
                _cr_regr = _threshold("cross_episode_repetition.overlap_regression", 6)

                _fps = RepetitionGuard.extract_sentence_fingerprints(final_manuscript, min_length=_cr_min_len)
                _db = getattr(self.ctx.current_project, "db", None)
                if _fps and _db:
                    _repeated = _db.find_repeated_sentence_hashes(
                        [h for h, _ in _fps],
                        current_ep=next_ep,
                        lookback=_cr_lookback,
                    )
                    _cr_result = None
                    if detect_cross_episode_repetition_fn:
                        _cr_result = detect_cross_episode_repetition_fn(
                            _fps,
                            _repeated,
                            warning_threshold=_cr_warn,
                            regression_threshold=_cr_regr,
                        )
                    if _cr_result:
                        logging.warning(
                            "[Phase 3-B] 크로스 에피소드 반복 — 제%d화: %s",
                            next_ep,
                            _cr_result["warning"],
                        )
                        self.ctx.ui.log(f"   ⚠️ {_cr_result['warning']}")
                    _db.store_sentence_hashes(next_ep, _fps)
        except Exception as _cr_err:
            logging.warning("[Phase 3-B] 크로스 에피소드 반복 감지 실패 (비차단): %s", _cr_err)

    def _run_post_pass_advisories(
        self,
        *,
        next_ep,
        final_manuscript,
        blueprint,
        final_state_updates,
        quality_labels=None,
        quality_signals=None,
        detect_npc_overexposure_fn,
        detect_cross_episode_repetition_fn,
        v50_modules_available,
    ):
        """[B-1-9a:A5] 만족도 태깅 + 호흡 분석 + 품질 회귀 + NPC 과잉 + 크로스 에피소드 반복."""
        self._run_post_pass_satisfaction_and_pacing(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
        )
        self._record_post_pass_quality_dashboard(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            blueprint=blueprint,
            final_state_updates=final_state_updates,
            quality_labels=quality_labels,
            quality_signals=quality_signals,
        )
        self._run_post_pass_npc_and_repetition_guards(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            detect_npc_overexposure_fn=detect_npc_overexposure_fn,
            detect_cross_episode_repetition_fn=detect_cross_episode_repetition_fn,
        )
