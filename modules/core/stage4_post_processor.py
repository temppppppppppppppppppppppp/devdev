"""
[B-1-1] Stage4 Post-Processor — PASS 후처리 및 세션 종료 로직 분리
"""

import json
import logging
import os

_PROJECTS_DIR = "projects"


class Stage4PostProcessor:
    """[B-1-1] Stage4 PASS 후처리 전담 모듈"""

    def __init__(self, ctx) -> None:
        self.ctx = ctx

    def process_pass_result(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        final_state_updates: dict,
        blueprint: dict,
        arc_data: dict,
        output_dir,
        v50_modules_available: bool,
        extract_chain_link_fn=None,
        detect_npc_overexposure_fn=None,
        detect_cross_episode_repetition_fn=None,
    ) -> bool:
        """[4-R1-c] Pass result post-processing. Returns False on DB save failure."""
        self.ctx.ui.log(f"\n📦 제{next_ep}화 데이터 정산 중...")

        # HUD 업데이트
        if final_state_updates and hasattr(self.ctx.sys, "hud"):
            try:
                approved = self.ctx.agents["director"].on_approve_workflow(
                    ep_num=next_ep,
                    state_updates=final_state_updates,
                    current_hud=self.ctx.sys.hud.snapshot() if hasattr(self.ctx.sys.hud, "snapshot") else {},
                )
                if approved.get("applied_updates"):
                    if hasattr(self.ctx.sys.hud, "bulk_update"):
                        self.ctx.sys.hud.bulk_update(approved["applied_updates"])
                        self.ctx.ui.log("   ✅ HUD 업데이트 완료")
                    else:
                        self.ctx.sys.hud.update_physical_status(approved["applied_updates"])
                        self.ctx.ui.log("   ✅ HUD 업데이트 완료 (fallback)")
            except Exception as hud_err:
                self.ctx.ui.log(f"   ⚠️ HUD 업데이트 실패: {hud_err}")

        # DB 저장
        try:
            self.ctx.current_project.db.save_manuscript(ep_num=next_ep, title=final_title, content=final_manuscript)

            if final_state_updates:
                self.ctx.current_project.db.update_martial_tracker(next_ep, final_state_updates)
                self.ctx.ui.log(f"      📊 제 {next_ep}화 15대 지표 트래커 저장 완료")

            self.ctx.current_project.db.conn.commit()
            self.ctx.ui.log("   ✅ DB 저장 완료")
        except Exception as db_err:
            self.ctx.ui.log(f"   🚨 DB 저장 실패: {db_err}")
            return False

        # 파일 저장
        try:
            file_path = output_dir / f"ep_{next_ep:04d}.txt"
            file_path.write_text(f"# {final_title}\n\n{final_manuscript}", encoding="utf-8")
            self.ctx.ui.log(f"   ✅ 파일 저장: {file_path.name}")
        except Exception as file_err:
            self.ctx.ui.log(f"   ⚠️ 파일 저장 실패: {file_err}")

        # [V63.3] 벡터 메모리 즉시 저장
        try:
            _mem_arc_no = arc_data.get("arc_no") if arc_data else None
            _mem_event_types = set()
            _mem_entity_names = set()
            if arc_data and arc_data.get("state_changes"):
                _sc = arc_data["state_changes"]
                if _sc.get("npc_deaths"):
                    _mem_event_types.add("death")
                    for d in _sc["npc_deaths"]:
                        _mem_entity_names.add(d.get("name", ""))
                if _sc.get("skill_acquisitions"):
                    _mem_event_types.add("skill")
                    for s in _sc["skill_acquisitions"]:
                        _mem_entity_names.add(s.get("name", ""))
                if _sc.get("relationship_changes"):
                    _mem_event_types.add("relationship")
                    for r in _sc["relationship_changes"]:
                        _mem_entity_names.add(r.get("npc", ""))
                if _sc.get("major_items"):
                    _mem_event_types.add("item")
                    for i in _sc["major_items"]:
                        _mem_entity_names.add(i.get("name", ""))
                if _sc.get("npc_injuries"):
                    _mem_event_types.add("injury")
                if _sc.get("npc_movements"):
                    _mem_event_types.add("movement")
                if _sc.get("resolved_plots"):
                    _mem_event_types.add("resolved_plot")
            _mem_entity_names.discard("")
            if self.ctx.memory and self.ctx.memory.is_operational():
                self.ctx.memory.memorize_v20_episode(
                    ep_num=next_ep,
                    text=final_manuscript,
                    summary=final_title[:100] if final_title else f"제{next_ep}화",
                    causal_links=[],
                    arc_no=_mem_arc_no,
                    event_types=list(_mem_event_types),
                    entity_names=list(_mem_entity_names),
                )
                self.ctx.ui.log(f"   ✅ 벡터 메모리 저장 (arc={_mem_arc_no}, events={_mem_event_types})")
        except Exception as _mem_err:
            self.ctx.ui.log(f"   ⚠️ [V63.3] 벡터 메모리 저장 실패 (비차단): {str(_mem_err)[:60]}")

        # [V66] 5화 단위 내러티브 요약 생성 (V63.2 10→5 단축)
        if next_ep % 5 == 0:
            try:
                self.ctx.generate_narrative_summary(next_ep)
            except Exception as _ns_err:
                self.ctx.ui.log(f"   ⚠️ [V63.2] 내러티브 요약 생성 실패: {str(_ns_err)[:60]}")

        # [V60.87 C] 로그 파일 저장
        try:
            logs_dir = os.path.join(_PROJECTS_DIR, self.ctx.current_project.name, "logs")
            os.makedirs(logs_dir, exist_ok=True)

            if v50_modules_available and self.ctx.failure_learner:
                self.ctx.failure_learner.save_to_json(os.path.join(logs_dir, "failure_learning.json"))

            if v50_modules_available and self.ctx.character_voice:
                try:
                    self.ctx.character_voice.analyze_manuscript(next_ep, final_manuscript)
                    self.ctx.character_voice.save_to_json(os.path.join(logs_dir, "character_voice.json"))
                except Exception as e:
                    logging.warning(f"⚠️ [V64.P4-fix] character_voice 분석/저장 실패: {e}")

            if v50_modules_available and self.ctx.foreshadow_tracker:
                # [V66] 원고에서 복선 자동 감지
                try:
                    self.ctx.foreshadow_tracker.auto_detect_from_manuscript(next_ep, final_manuscript)
                    self.ctx.foreshadow_tracker.save_to_json(os.path.join(logs_dir, "foreshadow.json"))
                except Exception as e:
                    logging.warning(f"⚠️ [V66-fix] foreshadow 감지/저장 실패: {e}")

            self.ctx.ui.log("   💾 [V60.87] 로그 파일 저장 완료")
        except Exception as log_err:
            self.ctx.ui.log(f"   ⚠️ 로그 저장 실패: {log_err}")

        # ===== [V60.82] Episode Bible 저장 =====
        bible_delta = None  # [V70] NameError 방지 사전 초기화
        try:
            self.ctx.ui.log("   📖 [V60.82] Manager 정산 시작...")

            audit = {}
            try:
                current_state = (
                    self.ctx.current_project.latest_state if hasattr(self.ctx.current_project, "latest_state") else {}
                )
                if not current_state and hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
                    current_state = {"actual_truth": self.ctx.sys.hud.pro_data}

                lore_list = []
                active_seeds = []
                causal_history = ""

                if hasattr(self.ctx.current_project, "master_bible"):
                    bible_root = self.ctx.current_project.master_bible.get(
                        "MasterBible", self.ctx.current_project.master_bible
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

                raw_audit = self.ctx.agents["manager"].update_state_and_lore_v20(
                    ep_num=next_ep,
                    manuscript=final_manuscript,
                    current_state=current_state,
                    lore_list=lore_list,
                    active_seeds=active_seeds,
                    causal_history=causal_history,
                )

                if raw_audit and not raw_audit.get("parsing_error"):
                    audit = raw_audit
                    self.ctx.ui.log("      ✅ Manager 정산 완료")
                else:
                    self.ctx.ui.log("      ⚠️ Manager 파싱 실패, 기본 추출 사용")
            except Exception as mgr_err:
                self.ctx.ui.log(f"      ⚠️ Manager 호출 실패: {str(mgr_err)[:50]}")

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

            prev_equipment = set(
                prev_actual.get("equipment", []) if isinstance(prev_actual.get("equipment"), list) else []
            )
            curr_equipment = set(
                actual_truth.get("equipment", []) if isinstance(actual_truth.get("equipment"), list) else []
            )
            prev_martial = set(
                prev_actual.get("martial_arts", []) if isinstance(prev_actual.get("martial_arts"), list) else []
            )
            curr_martial = set(
                actual_truth.get("martial_arts", []) if isinstance(actual_truth.get("martial_arts"), list) else []
            )

            new_items_from_equip = list(curr_equipment - prev_equipment)
            lost_items_from_equip = list(prev_equipment - curr_equipment)
            new_martial_arts = list(curr_martial - prev_martial)

            key_items = new_lore.get("Key_Items", []) if isinstance(new_lore.get("Key_Items"), list) else []
            key_item_names = [i.get("name", str(i)) if isinstance(i, dict) else str(i) for i in key_items]

            key_npcs = new_lore.get("Key_NPCs", []) if isinstance(new_lore.get("Key_NPCs"), list) else []
            new_npc_names = [npc.get("name", str(npc)) if isinstance(npc, dict) else str(npc) for npc in key_npcs]

            npc_deaths = []
            for npc in key_npcs:
                if isinstance(npc, dict):
                    status = npc.get("NPC_Martial_HUD", {}).get("current_status", "")
                    if "사망" in str(status) or "죽" in str(status) or "절명" in str(status):
                        npc_deaths.append(npc.get("name", ""))

            relationship_changes = []
            if isinstance(knowledge_map, dict):
                witnesses = knowledge_map.get("new_witnesses", [])
                misled = knowledge_map.get("new_misled", [])
                if witnesses:
                    relationship_changes.extend([f"목격: {w}" for w in witnesses if w])
                if misled:
                    relationship_changes.extend([f"오해: {m}" for m in misled if m])

            karma_matrix = state_updates_from_audit.get("karma_matrix", [])
            if isinstance(karma_matrix, list):
                for karma in karma_matrix:
                    if isinstance(karma, dict) and karma.get("target"):
                        obs = karma.get("obsession", 0)
                        val = karma.get("value", 0)
                        if obs > 50 or val > 50:
                            relationship_changes.append(f"{karma['target']}: 집착{obs}/오해{val}")

            reveal_list = []
            if isinstance(recovered, list):
                for seed in recovered:
                    if isinstance(seed, dict):
                        reveal_list.append(seed.get("seed_id", seed.get("description", str(seed))))
                    else:
                        reveal_list.append(str(seed))

            all_new_items = list(set(new_items_from_equip + key_item_names + new_martial_arts))

            bible_delta = {
                "new_items": all_new_items,
                "lost_items": lost_items_from_equip,
                "new_npcs": new_npc_names,
                "npc_deaths": npc_deaths,
                "relationship_changes": relationship_changes,
                "state_changes": actual_truth if actual_truth else final_state_updates,
                "time_passed": state_updates_from_audit.get("location", ""),
                "reveals": reveal_list,
                "causal_links": causal_links,
                "karma_matrix": karma_matrix,
                "knowledge_map": knowledge_map,
            }

            self.ctx.current_project.db.save_episode_bible(next_ep, bible_delta)

            if actual_truth or state_updates_from_audit:
                state_log_data = {
                    "actual_truth": actual_truth if actual_truth else final_state_updates,
                    "karma_matrix": karma_matrix,
                    "knowledge_map": knowledge_map,
                    "public_reputation": state_updates_from_audit.get("public_reputation", {}),
                }
                try:
                    summary = f"제{next_ep}화 정산: {', '.join(all_new_items[:3]) if all_new_items else '변화없음'}"
                    self.ctx.current_project.db.save_state_log_with_summary(next_ep, state_log_data, summary)
                except Exception as state_err:
                    self.ctx.ui.log(f"      ⚠️ state_logs 저장 실패: {str(state_err)[:30]}")

            changes_count = (
                len(all_new_items)
                + len(lost_items_from_equip)
                + len(new_npc_names)
                + len(npc_deaths)
                + len(relationship_changes)
                + len(reveal_list)
            )
            if changes_count > 0:
                self.ctx.ui.log(f"   📖 Episode Bible 저장: {changes_count}개 변화 기록")
                if all_new_items:
                    self.ctx.ui.log(f"      • 신규 아이템/무공: {', '.join(all_new_items[:5])}")
                if new_npc_names:
                    self.ctx.ui.log(f"      • 신규/갱신 NPC: {', '.join(new_npc_names[:5])}")
                if npc_deaths:
                    self.ctx.ui.log(f"      • NPC 사망: {', '.join(npc_deaths)}")
                if reveal_list:
                    self.ctx.ui.log(f"      • 복선 회수: {', '.join(reveal_list[:3])}")
            else:
                self.ctx.ui.log("   📖 Episode Bible 저장 완료 (변화 없음)")

        except Exception as bible_err:
            self.ctx.ui.log(f"   ⚠️ Episode Bible 저장 실패 (비차단): {str(bible_err)[:50]}")
            import traceback

            traceback.print_exc()

        # ===== [V68] 에피소드 연결고리 추출 및 저장 =====
        try:
            _chain_link = {}
            if extract_chain_link_fn:
                _chain_link = extract_chain_link_fn(next_ep, final_manuscript, blueprint)
            if _chain_link:
                self.ctx.current_project.db.save_anchor(f"chain_link_{next_ep}", _chain_link)
                _cl_cliff = _chain_link.get("cliffhanger", "")
                self.ctx.ui.log(
                    f"   [V68] 연결고리 저장 완료 (cliffhanger: {_cl_cliff[:50]}{'...' if len(_cl_cliff) > 50 else ''})"
                )
            else:
                self.ctx.ui.log("   [V68] 연결고리 추출 결과 없음 (비차단)")
        except Exception as _cl_err:
            self.ctx.ui.log(f"   [V68] 연결고리 저장 실패 (비차단): {str(_cl_err)[:50]}")

        # ===== [V68] WorldState 갱신 =====
        if self.ctx.world_state:
            try:
                # state_changes 추출 (arc_data에서)
                _ws_sc = arc_data.get("state_changes", {}) if arc_data else {}
                if _ws_sc:
                    self.ctx.world_state.update_from_state_changes(next_ep, _ws_sc)

                # 주인공 이름 갱신
                _ws_prot_name = ""
                try:
                    _ws_bible_root = self.ctx.current_project.master_bible.get(
                        "MasterBible", self.ctx.current_project.master_bible
                    )
                    _ws_prot_name = _ws_bible_root.get("protagonist_config", {}).get("name", "")
                except Exception as e:
                    logging.warning(f"[SilentPass:PostProcessor] 주인공 이름 추출 실패: {e!s:.100}")
                self.ctx.world_state.update_protagonist_state(
                    ep_num=next_ep,
                    name=_ws_prot_name if _ws_prot_name else None,
                )

                # DB 저장
                self.ctx.world_state.save()
                self.ctx.ui.log(f"   🌍 [V68] 세계 상태 갱신 완료 (제{next_ep}화)")
            except Exception as _ws_upd_err:
                self.ctx.ui.log(f"   ⚠️ [V68] 세계 상태 갱신 실패 (비차단): {str(_ws_upd_err)[:60]}")

        # ===== [V68] 팩트 원장 갱신 =====
        if self.ctx.fact_ledger:
            try:
                # 1) Arc state_changes에서 갱신
                _fl_sc = arc_data.get("state_changes", {}) if arc_data else {}
                if _fl_sc:
                    self.ctx.fact_ledger.update_from_state_changes(next_ep, _fl_sc)

                # 2) bible_delta에서 추가 갱신 (new_npcs, new_items, lost_items 등)
                if bible_delta:
                    try:
                        self.ctx.fact_ledger.update_from_bible_delta(next_ep, bible_delta)
                    except Exception as _bd_err:
                        logging.warning("[V70] bible_delta 갱신 실패 (비차단): %s", _bd_err)

                # 3) DB 저장
                self.ctx.fact_ledger.save()
                _fl_stats = self.ctx.fact_ledger.get_stats()
                self.ctx.ui.log(
                    f"   📋 [V68] 팩트 원장 갱신 완료 (인물 {_fl_stats.get('characters', 0)}명, 아이템 {_fl_stats.get('items', 0)}개)"
                )
            except Exception as _fl_err:
                self.ctx.ui.log(f"   ⚠️ [V68] 팩트 원장 갱신 실패 (비차단): {str(_fl_err)[:50]}")

        # ===== [D Step 3] 에피소드 만족도 태깅 (비차단) =====
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

        # ===== [Phase 3-QR] 품질 회귀 감지 (advisory-only) =====
        if self.ctx.quality_dashboard:
            try:
                _regression = self.ctx.quality_dashboard.detect_score_regression(stage=2)
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

        # ===== [Phase 3-5C] NPC 과잉 등장 경고 (advisory-only, extras only) =====
        if self.ctx.state_tracker and getattr(self.ctx.state_tracker, "npc_registry", None):
            try:
                from modules.validation.threshold_helper import _threshold

                _max_m = _threshold("npc_exposure.max_mentions_per_episode", 15)
                _min_len = _threshold("npc_exposure.min_name_length", 2)
                _npc_names = list(self.ctx.state_tracker.npc_registry.keys())
                _prot_name = self.ctx.get_protagonist_name() if self.ctx.get_protagonist_name else ""
                # Bible KeyNPCs → core set (핵심 NPC 제외 대상)
                _core = set()
                try:
                    _bible_root = self.ctx.current_project.master_bible.get(
                        "MasterBible", self.ctx.current_project.master_bible
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

        # ===== [Phase 3-B] 크로스 에피소드 문장 반복 감지 (advisory-only) =====
        try:
            from modules.validation.threshold_helper import _threshold

            _cr_enabled = _threshold("cross_episode_repetition.enabled", True)
            if _cr_enabled:
                from modules.core.repetition_guard import RepetitionGuard

                _cr_lookback = _threshold("cross_episode_repetition.lookback_episodes", 5)
                _cr_min_len = _threshold("cross_episode_repetition.min_sentence_length", 15)
                _cr_warn = _threshold("cross_episode_repetition.overlap_warning", 3)
                _cr_regr = _threshold("cross_episode_repetition.overlap_regression", 6)

                _fps = RepetitionGuard.extract_sentence_fingerprints(final_manuscript, min_length=_cr_min_len)
                _db = getattr(self.ctx.current_project, "db", None)
                if _fps and _db:
                    _repeated = _db.find_repeated_sentence_hashes(
                        [h for h, _ in _fps], current_ep=next_ep, lookback=_cr_lookback
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
                    # 현재 에피소드 핑거프린트 저장 (감지 후 저장 → 자기 자신과 비교 방지)
                    _db.store_sentence_hashes(next_ep, _fps)
        except Exception as _cr_err:
            logging.warning("[Phase 3-B] 크로스 에피소드 반복 감지 실패 (비차단): %s", _cr_err)

        self.ctx.ui.log(f"\n✅ 제{next_ep}화 '{final_title}' 생산 완료! ({len(final_manuscript)}자)")

        # [V66.1] B-3: 에피소드 완료 시 audit 버퍼 flush
        self.ctx.flush_audit_buffer()

        # [V65] PerfTimer: 에피소드 완료 시 요약 로그
        try:
            self.ctx.perf_timer.log_summary()
            self.ctx.perf_timer.reset()
        except Exception:
            pass
        return True

    def run_post_episode_tasks(self) -> None:
        """[4-R1-d] Session wrap-up: logs, vector sync."""
        # [V62.3] Stage 4 루프 종료
        self.ctx.ui.log(f"\n{'=' * 50}")
        self.ctx.ui.log("📋 Stage 4 집필 세션 종료.")
        try:
            input("   ⏎ Enter를 누르면 메뉴로 돌아갑니다...")
        except EOFError:
            pass

        # [V62.3] 벡터 메모리 일괄 동기화
        # [V66.3] 벡터 메모리 비활성화 시 스킵
        if self.ctx.memory and self.ctx.memory.is_operational():
            try:
                self.ctx.ui.log("   🔄 벡터 메모리 일괄 동기화 중...")
                self.ctx.memory.sync_v20_drafts()
                self.ctx.ui.log("   ✅ 벡터 메모리 동기화 완료")
            except Exception as vec_err:
                self.ctx.ui.log(f"   ⚠️ 벡터 메모리 동기화 실패 (비차단): {vec_err}")
