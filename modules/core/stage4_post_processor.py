"""
[B-1-1] Stage4 Post-Processor — PASS 후처리 및 세션 종료 로직 분리
"""

import json
import logging
import os
import re
from contextlib import nullcontext as _nullcontext

from modules.core.metrics_collector import get_metrics_collector

_PROJECTS_DIR = "projects"


class Stage4PostProcessor:
    """[B-1-1] Stage4 PASS 후처리 전담 모듈"""

    def __init__(self, ctx) -> None:
        self.ctx = ctx

    def _truth_gate_llm_ask(self, prompt: str) -> str:
        """[TF-30-1] TruthGate 세계법칙 검사용 LLM 콜백."""
        try:
            director = getattr(self.ctx, "agents", {}).get("director")
            if director and hasattr(director, "ask"):
                return director.ask(prompt, temperature=0.1) or ""
        except Exception as e:
            logging.debug("[TruthGate:POST] llm_ask fail: %s", e)
        return ""

    @staticmethod
    def _extract_state_change_info(state_changes) -> dict:
        """[TF-T5] state_changes에서 event_types, entity_names, summary_parts 추출.

        벡터 메모리 저장(Block 1)과 rich_summary 구성(Block 2)에서 동일 데이터를
        이중 순회하던 것을 단일 패스로 통합.
        """
        event_types: set[str] = set()
        entity_names: set[str] = set()
        summary_parts: list[str] = []

        if not isinstance(state_changes, dict):
            return {"event_types": event_types, "entity_names": entity_names, "summary_parts": summary_parts}

        # npc_deaths
        npc_deaths = state_changes.get("npc_deaths", [])
        if npc_deaths:
            event_types.add("death")
            death_names = []
            for d in npc_deaths:
                name = d.get("name", "") if isinstance(d, dict) else str(d)
                if name:
                    entity_names.add(name)
                    death_names.append(name)
            if death_names:
                summary_parts.append("사망: " + ", ".join(death_names)[:60])

        # skill_acquisitions
        skill_acqs = state_changes.get("skill_acquisitions", [])
        if skill_acqs:
            event_types.add("skill")
            for s in skill_acqs:
                entity_names.add(s.get("name", "") if isinstance(s, dict) else str(s))

        # relationship_changes
        rel_changes = state_changes.get("relationship_changes", [])
        if isinstance(rel_changes, list) and rel_changes:
            event_types.add("relationship")
            rel_texts = []
            for r in rel_changes:
                if isinstance(r, dict):
                    who = r.get("npc", "") or r.get("target", "")
                    entity_names.add(who)
                    delta = r.get("change", "")
                    rel_texts.append(f"{who}-{delta}")
                else:
                    rel_texts.append(str(r))
            if rel_texts:
                summary_parts.append("관계: " + ", ".join(rel_texts)[:80])

        # major_items
        major_items = state_changes.get("major_items", [])
        if isinstance(major_items, list) and major_items:
            event_types.add("item")
            item_names = []
            for i in major_items:
                name = i.get("name", "") if isinstance(i, dict) else str(i)
                if name:
                    entity_names.add(name)
                    item_names.append(name)
            if item_names:
                summary_parts.append("아이템: " + ", ".join(item_names)[:60])

        # npc_injuries / npc_movements
        if state_changes.get("npc_injuries"):
            event_types.add("injury")
        if state_changes.get("npc_movements"):
            event_types.add("movement")

        # resolved_plots
        resolved_plots = state_changes.get("resolved_plots", [])
        if isinstance(resolved_plots, list) and resolved_plots:
            event_types.add("resolved_plot")
            summary_parts.append("해결: " + ", ".join(str(p)[:30] for p in resolved_plots[:2]))

        entity_names.discard("")
        return {"event_types": event_types, "entity_names": entity_names, "summary_parts": summary_parts}

    # ------------------------------------------------------------------
    # [V73] 확정 원고 기준 자본금 역동기화
    # ------------------------------------------------------------------
    _CAPITAL_PATTERNS = [
        # "잔고 131억", "자본금 80억", "현금 57억"
        re.compile(r"(?:잔고|자본금?|현금|자산|실탄|예수금)[이가은는:의]?\s*(?:약?\s*)?(\d[\d,.]*)\s*(억|만)"),
        # "80억의 자본", "130억 원의 잔고"
        re.compile(r"(\d[\d,.]*)\s*(억|만)\s*(?:원)?[의이가]?\s*(?:잔고|자본|현금|자산|실탄|예수금)"),
    ]

    @staticmethod
    def _parse_hud_capital_to_eok(raw) -> float:
        """HUD 한국어 복합 금액을 억 단위 float로 변환.

        Examples:
            "38억 3,154만 200원" → 38.3154
            "131억 원" → 131.0
            "5000만원" → 0.5
            "3831540200" (원 단위 정수) → 38.3154
        """
        s = str(raw).replace(",", "").strip()
        if not s:
            return 0.0

        eok = 0.0
        # 억 부분
        m_eok = re.search(r"(\d+(?:\.\d+)?)\s*억", s)
        if m_eok:
            eok += float(m_eok.group(1))
        # 만 부분
        m_man = re.search(r"(\d+(?:\.\d+)?)\s*만", s)
        if m_man:
            eok += float(m_man.group(1)) / 10000
        # 억·만 모두 없으면 순수 숫자 → 원 단위로 간주
        if not m_eok and not m_man:
            digits = re.sub(r"[^\d.]", "", s)
            try:
                eok = float(digits) / 1_0000_0000 if digits else 0.0
            except (ValueError, TypeError):
                eok = 0.0
        return eok

    @staticmethod
    def _extract_capital_from_manuscript(manuscript: str) -> float | None:
        """확정 원고에서 마지막으로 언급된 자본금(억 단위)을 추출. 없으면 None."""
        # 모든 패턴의 매치를 (문서 내 위치, 값) 튜플로 수집 후 위치순 정렬
        candidates: list[tuple[int, float]] = []
        for pat in Stage4PostProcessor._CAPITAL_PATTERNS:
            for m in pat.finditer(manuscript):
                raw = m.group(1).replace(",", "")  # 천 단위 콤마만 제거, 소수점 유지
                try:
                    num = float(raw)
                except (ValueError, TypeError):
                    continue
                unit = m.group(2)
                if unit == "만":
                    num /= 10000  # 만 → 억 환산
                candidates.append((m.start(), num))
        if not candidates:
            return None
        # 문서에서 가장 뒤에 나온 값 반환
        candidates.sort(key=lambda x: x[0])
        return candidates[-1][1]

    def _reconcile_capital(self, final_manuscript: str, ep_num: int) -> None:
        """확정 원고의 자본금과 HUD를 비교하여 불일치 시 경고 + 보정. 투자물 전용."""
        if not hasattr(self.ctx.sys, "hud") or not self.ctx.sys.hud:
            return

        hud = self.ctx.sys.hud
        # [V73] 투자물(FinanceHUD)에서만 실행 — 다른 장르는 단위 체계가 달라 오탐 위험
        from modules.core.genre_hud_manager import FinanceHUDManager

        if not isinstance(hud, FinanceHUDManager):
            return

        confirmed = self._extract_capital_from_manuscript(final_manuscript)
        if confirmed is None:
            return  # 금융 언급 없음 — 스킵

        capital_key = "capital"

        current_raw = hud.pro_data.get(capital_key, "0")
        current_value = self._parse_hud_capital_to_eok(current_raw)

        diff = abs(confirmed - current_value)
        if diff <= 5:  # 5억 이하 차이는 허용
            return

        logging.warning(
            "[V73] 자본금 불일치 감지 (ep%d): HUD %s=%s(→%.0f억), 원고=%.0f억 → 원고 기준 보정",
            ep_num,
            capital_key,
            current_raw,
            current_value,
            confirmed,
        )
        # [V73-B] Advisory — HUD 수정은 Director state_updates에 위임
        self.ctx.ui.log(
            f"   ⚠️ [V73] 자본금 불일치 감지: HUD {current_value:.0f}억 vs 원고 {confirmed:.0f}억"
            " (Director state_updates 반영 대기)"
        )

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

        # DB 저장 (HUD보다 먼저 — DB 실패 시 HUD 오염 방지) [Sweep56]
        # [P0-D1/D4] lock 보호 + 원자적 트랜잭션으로 부분 저장 방지
        _db = self.ctx.current_project.db
        try:
            with _db._lock:
                _db.conn.execute("BEGIN")
                try:
                    _db.save_manuscript(ep_num=next_ep, title=final_title, content=final_manuscript)
                    if final_state_updates:
                        _db.update_martial_tracker(next_ep, final_state_updates)
                        self.ctx.ui.log(f"      📊 제 {next_ep}화 15대 지표 트래커 저장 완료")
                    _db.conn.commit()
                except Exception:
                    _db.conn.rollback()
                    raise
            self.ctx.ui.log("   ✅ DB 저장 완료")
        except Exception as db_err:
            self.ctx.ui.log(f"   🚨 DB 저장 실패 (롤백 완료): {db_err}")
            return False

        # HUD 업데이트 (DB 커밋 성공 후에만 실행)
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

        # 파일 저장
        try:
            file_path = output_dir / f"ep_{next_ep:04d}.txt"
            file_path.write_text(f"# {final_title}\n\n{final_manuscript}", encoding="utf-8")
            self.ctx.ui.log(f"   ✅ 파일 저장: {file_path.name}")
        except Exception as file_err:
            self.ctx.ui.log(f"   ⚠️ 파일 저장 실패: {file_err}")

        # [V73] 확정 원고 기준 자본금 역동기화
        try:
            self._reconcile_capital(final_manuscript, next_ep)
        except Exception as _cap_err:
            logging.warning("[V73] 자본금 역동기화 실패 (비차단): %s", _cap_err)

        # ===== [S4-N-P1-1][S4-I6] Manager LLM 비동기 제출 (먼저 submit → 독립 작업 → result 회수) =====
        bible_delta = None  # [V70] NameError 방지 사전 초기화
        _bible_future = None
        audit = {}
        actual_truth = {}  # [V75] NameError 방지 사전 초기화
        # 동기 폴백에 필요한 변수 사전 초기화
        current_state = {}
        lore_list = []
        active_seeds = []
        causal_history = ""
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

            _manager_agent = self.ctx.agents["manager"]
            _bible_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bible_settle")
            _bible_future = _bible_executor.submit(
                _manager_agent.update_state_and_lore_v20,
                ep_num=next_ep,
                manuscript=final_manuscript,
                current_state=current_state,
                lore_list=lore_list,
                active_seeds=active_seeds,
                causal_history=causal_history,
            )
            _bible_executor.shutdown(wait=False, cancel_futures=False)
            self.ctx.ui.log("      ⏳ [S4-I6] Manager 정산 비동기 실행 중...")
        except Exception as _submit_err:
            logging.warning("[S4-I6] 비동기 제출 실패, 동기 폴백 예정: %s", _submit_err)
            _bible_future = None

        # ===== [S4-N-P1-1] Bible LLM 실행 중 독립 작업 병렬 수행 =====

        # [V63.3] 벡터 메모리 즉시 저장
        try:
            _mem_arc_no = arc_data.get("arc_no") if arc_data else None
            # [TF-T5] state_changes 단일 패스 추출
            _sc_raw = final_state_updates if final_state_updates else {}  # [TF-R2-S4-01] 실제 산출물 사용
            _sc_info = self._extract_state_change_info(_sc_raw)
            _mem_event_types = _sc_info["event_types"]
            _mem_entity_names = _sc_info["entity_names"]

            # [TF-17] Truth Gate — 메모리 오염 방지 advisory 검증
            try:
                from modules.core.truth_gate import TruthGate

                _truth_gate = TruthGate(
                    world_state=getattr(self.ctx, "world_state", None),
                    fact_ledger=getattr(self.ctx, "fact_ledger", None),
                    llm_ask=self._truth_gate_llm_ask,  # [TF-30-1] 세계법칙 검사 활성화
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
                    # [Phase4] structured_warnings severity 로깅
                    for _sw in _tg_result.get("structured_warnings", []):
                        logging.warning(
                            "[TruthGate:POST] [%s] %s",
                            _sw.get("severity", "?"),
                            _sw.get("text", ""),
                        )
            except Exception as _tg_err:
                logging.debug("[TruthGate] 검증 실패 (비차단): %s", _tg_err)

            # [OpusTF-P0-3] 4-슬롯 정규화 요약: 사건 | 인물 | 장소 | 결말
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

            # [DB-Eff-P2] failure_learner: 세션 종료 시 main_a.py가 reflexion_memory DB에 저장.
            # 매 화 중간 저장 불필요 — 누적 학습 이력은 세션 내 메모리 유지로 충분.

            if v50_modules_available and self.ctx.character_voice:
                try:
                    self.ctx.character_voice.analyze_manuscript(next_ep, final_manuscript)
                except Exception as e:
                    logging.warning("[CharacterVoice] analyze_manuscript 실패 (비치명): %s", e)
                try:
                    self.ctx.character_voice.save_to_db(self.ctx.current_project.db)  # [DB-Eff-P1] JSON->DB
                except Exception as e:
                    logging.warning("[CharacterVoice] save_to_db 실패 (비치명): %s", e)

            if v50_modules_available and self.ctx.foreshadow_tracker:
                # [V66] 원고에서 복선 자동 감지
                try:
                    self.ctx.foreshadow_tracker.auto_detect_from_manuscript(next_ep, final_manuscript)
                except Exception as e:
                    logging.warning("[ForeshadowTracker] auto_detect_from_manuscript 실패 (비치명): %s", e)
                try:
                    self.ctx.foreshadow_tracker.save_to_db(self.ctx.current_project.db)  # [DB-Eff-P1] JSON->DB
                except Exception as e:
                    logging.warning("[ForeshadowTracker] save_to_db 실패 (비치명): %s", e)

            # [TF7-P2-06] EmotionArcTracker: 에피소드 감정 기록 + DB 저장
            if v50_modules_available and getattr(self.ctx, "emotion_tracker", None):
                try:
                    _et = self.ctx.emotion_tracker
                    _et.add_episode_emotion(next_ep, "neutral", 0.5)
                    if hasattr(self.ctx, "current_project") and hasattr(self.ctx.current_project, "db"):
                        _et.save_to_db(self.ctx.current_project.db)
                except Exception as _et_err:
                    logging.warning(f"⚠️ [TF7-P2-06] emotion_tracker 저장 실패: {_et_err}")

            self.ctx.ui.log("   💾 [V60.87] 로그 파일 저장 완료")
        except Exception as log_err:
            self.ctx.ui.log(f"   ⚠️ 로그 저장 실패: {log_err}")

        # ===== [S4-N-P1-1] Manager LLM Future 회수 (독립 작업 완료 후) =====
        _manager_failed = False  # [XC-002] Manager 완전 실패 추적 플래그
        try:
            # [S4-I6] Future 회수: 결과를 기다린 후 audit에 반영
            try:
                if _bible_future is not None:
                    raw_audit = _bible_future.result(timeout=120)  # 최대 2분 대기
                else:
                    # 동기 폴백
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
                    logging.error(
                        "[XC-002] Manager LLM 파싱 실패 — bible_delta 미생성으로 FactLedger 갱신 불완전할 수 있음"
                    )
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event("manager_parse_failure", "Manager LLM 파싱 실패", {"ep": next_ep})
                    _manager_failed = True
            except Exception as mgr_err:
                # [P0-D2] 타임아웃 시 비동기 future 취소 후 동기 재시도
                if _bible_future is not None and hasattr(_bible_future, "cancel"):
                    _bible_future.cancel()
                self.ctx.ui.log(f"      ⚠️ Manager 호출 실패: {str(mgr_err)[:50]}")
                logging.warning("[B-1] Manager 정산 실패 — 동기 재시도: %s", mgr_err)
                try:
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
                        self.ctx.ui.log("      ✅ Manager 동기 재시도 성공")
                except Exception as retry_err:
                    logging.error("[XC-002] Manager 동기 재시도도 실패: %s", retry_err)
                    logging.error("[XC-002] Manager LLM 완전 실패 — bible_delta=None, FactLedger 갱신 건너뜀")
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event("manager_complete_failure", "Manager LLM 완전 실패", {"ep": next_ep})
                    _manager_failed = True

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
                    status = (npc.get("NPC_Martial_HUD") or {}).get("current_status", "")  # [TF-R3-S4-02] None 방어
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

            # [V75] State-Text 교차 검증 — actual_truth ↔ 원고 (advisory)
            try:
                _stv_enabled = False
                try:
                    from modules.validation.threshold_helper import _threshold

                    _stv_enabled = _threshold("feature_flags.enable_state_text_verifier", False)
                except Exception:
                    pass

                if _stv_enabled and actual_truth and final_manuscript:
                    from modules.core.state_text_verifier import StateTextVerifier

                    _stv_agent = self.ctx.agents.get("manager") if self.ctx.agents else None
                    _stv = StateTextVerifier(agent=_stv_agent)
                    _stv_result = _stv.verify(final_manuscript, actual_truth)
                    if not _stv_result["verified"] and _stv_result["corrections"]:
                        actual_truth = _stv.apply_corrections(actual_truth, _stv_result["corrections"])
                        self.ctx.ui.log(
                            f"      🔍 [V75] State-Text 검증: {len(_stv_result['mismatches'])}건 불일치 → "
                            f"{len(_stv_result['corrections'])}건 수정"
                        )
                    elif not _stv_result["verified"]:
                        self.ctx.ui.log(
                            f"      ⚠️ [V75] State-Text 검증: {len(_stv_result['mismatches'])}건 불일치 발견 (수정 불가)"
                        )
            except Exception as _stv_err:
                logging.warning("[SilentPass:V75] State-Text 검증 모듈 실패: %s", _stv_err)

            all_new_items = list(set(new_items_from_equip + key_item_names + new_martial_arts))

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
            }

            logging.debug(
                "[P2] bible_delta ep=%d: items=%d, npcs=%d, deaths=%d",
                next_ep,
                len(all_new_items),
                len(new_npc_names),
                len(npc_deaths),
            )

            # [S4-P1-5] save_episode_bible 실패가 후속 처리(state_log, FactLedger)를 차단하지 않도록 격리
            _meta_save_failed = False  # [S4-001] 에피소드 메타 저장 실패 추적 플래그
            try:
                self.ctx.current_project.db.save_episode_bible(next_ep, bible_delta)
            except Exception as _bible_save_err:
                self.ctx.ui.log(
                    f"      ⚠️ Episode Bible DB 저장 실패 (bible_delta 구성은 성공): {str(_bible_save_err)[:50]}"
                )
                logging.error("[S4-001] save_episode_bible 실패 ep=%d: %s", next_ep, _bible_save_err)
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("episode_bible_save_failed", "save_episode_bible 실패", {"ep": next_ep})
                _meta_save_failed = True

            # [Graph-Layer] causal_links → causal_graph dual-write (경로 확보)
            if causal_links:
                try:
                    self.ctx.current_project.db.save_causal_links(causal_links, next_ep)
                except Exception as _cg_err:
                    logging.debug("[Stage4] causal_graph dual-write 실패 (비치명): %s", _cg_err)

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

        except Exception as bible_err:  # [V64.P4] OPTIONAL: 비차단 — bible 저장 실패 시 에피소드 진행 유지
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

        # ===== [TF-C10] WorldState + FactLedger 원자적 갱신 =====
        # 원고(핵심 산출물)는 이미 저장 완료 — 메타데이터만 트랜잭션으로 묶어 반쪽 커밋 방지
        _meta_db = getattr(self.ctx.current_project, "db", None)
        try:
            _txn = _meta_db.transaction() if _meta_db and hasattr(_meta_db, "transaction") else None
            _ctx_mgr = _txn if _txn is not None else _nullcontext()
            with _ctx_mgr:
                # ── WorldState 갱신 ──
                if self.ctx.world_state:
                    _ws_sc = final_state_updates or {}
                    if _ws_sc:
                        self.ctx.world_state.update_from_state_changes(next_ep, _ws_sc)

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
                    self.ctx.world_state.save()
                    self.ctx.ui.log(f"   🌍 [V68] 세계 상태 갱신 완료 (제{next_ep}화)")

                    # [LOG-1] 상태 변경 세션 로깅 — WorldState
                    _sl = getattr(self.ctx, "session_logger", None)
                    if _sl and _ws_sc:
                        try:
                            _sl.log_state_change(
                                ep_num=next_ep,
                                change_type="world_state",
                                after=_ws_sc,
                                source="stage4_post_processor",
                            )
                        except Exception:
                            pass

                # ── FactLedger 갱신 ──
                if self.ctx.fact_ledger:
                    _fl_sc = final_state_updates or {}
                    if _fl_sc:
                        self.ctx.fact_ledger.update_from_state_changes(next_ep, _fl_sc)
                    if bible_delta:
                        try:
                            self.ctx.fact_ledger.update_from_bible_delta(next_ep, bible_delta)
                        except Exception as _bd_err:
                            logging.warning("[V70] bible_delta 갱신 실패 (비차단): %s", _bd_err)
                    self.ctx.fact_ledger.save()
                    _fl_stats = self.ctx.fact_ledger.get_stats()
                    self.ctx.ui.log(
                        f"   📋 [V68] 팩트 원장 갱신 완료 (인물 {_fl_stats.get('characters', 0)}명, 아이템 {_fl_stats.get('items', 0)}개)"
                    )

                    # [LOG-1] 상태 변경 세션 로깅 — FactLedger
                    _sl = getattr(self.ctx, "session_logger", None)
                    if _sl and _fl_sc:
                        try:
                            _sl.log_state_change(
                                ep_num=next_ep,
                                change_type="fact_ledger",
                                after=_fl_sc,
                                source="stage4_post_processor",
                            )
                        except Exception:
                            pass
        except Exception as _meta_err:
            self.ctx.ui.log(f"   ⚠️ [TF-C10] 메타데이터 원자적 저장 실패 (비차단): {str(_meta_err)[:60]}")

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

        # ===== [TF-I24] 호흡 분석 DB 저장 (비차단) =====
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

        # ===== [Phase 3-QR] 품질 회귀 감지 (advisory-only) =====
        if self.ctx.quality_dashboard:
            try:
                _stage4_score = 0
                if isinstance(final_state_updates, dict):
                    _cand_score = final_state_updates.get("director_score", 0)
                    if isinstance(_cand_score, int | float):
                        _stage4_score = int(_cand_score)
                self.ctx.quality_dashboard.record_validation(
                    ep_num=next_ep,
                    result={"decision": "PASS", "score": _stage4_score},
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

        # ===== [Phase 3-5C] NPC 과잉 등장 경고 (advisory-only, extras only) =====
        if self.ctx.state_tracker and getattr(self.ctx.state_tracker, "npc_registry", None):
            try:
                from modules.validation.threshold_helper import _threshold

                _max_m = _threshold("npc_exposure.max_mentions_per_episode", 15)
                _min_len = _threshold("npc_exposure.min_name_length", 2)
                _npc_names = list(self.ctx.state_tracker.npc_registry.keys())
                _prot_name = (self.ctx.get_protagonist_name() or "") if self.ctx.get_protagonist_name else ""
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

        # [Phase 6] Episode 단위 비용 스냅샷 저장 (비차단)
        try:
            collector = get_metrics_collector()
            _db = getattr(self.ctx.current_project, "db", None)
            if collector and _db and hasattr(_db, "save_cost_record"):
                scope = collector.snapshot_and_reset_scope()
                if (
                    scope.get("total_calls", 0) > 0
                    or scope.get("total_tokens", 0) > 0
                    or scope.get("total_cost_usd", 0.0) > 0
                ):
                    _db.save_cost_record(
                        session_id=collector.session_id,
                        scope_type="episode",
                        scope_id=next_ep,
                        total_calls=scope.get("total_calls", 0),
                        total_tokens=scope.get("total_tokens", 0),
                        total_cost_usd=scope.get("total_cost_usd", 0.0),
                        model_breakdown=scope.get("model_breakdown", "{}"),
                    )
                    self.ctx.ui.log(
                        f"   💰 [Cost] Episode {next_ep} 비용: ${scope.get('total_cost_usd', 0.0):.4f} "
                        f"({scope.get('total_tokens', 0):,} tokens)"
                    )
        except Exception as _cost_err:
            logging.warning("[Phase 6] Episode 비용 기록 실패 (비차단): %s", _cost_err)

        self.ctx.ui.log(f"\n✅ 제{next_ep}화 '{final_title}' 생산 완료! ({len(final_manuscript)}자)")

        # [V66.1] B-3: 에피소드 완료 시 audit 버퍼 flush
        if callable(getattr(self.ctx, "flush_audit_buffer", None)):
            self.ctx.flush_audit_buffer()

        # [V65] PerfTimer: 에피소드 완료 시 요약 로그
        try:
            self.ctx.perf_timer.log_summary()
            self.ctx.perf_timer.reset()
        except Exception as e:
            logging.debug(f"[PerfTimer] s4 summary/reset: {e}")

        # [S4-001] Episode Bible 저장 실패 시 오케스트레이터에 실패 신호 전달
        if locals().get("_meta_save_failed", False):
            logging.error("[S4-001] _meta_save_failed=True → process_pass_result 반환 False")
            return False

        return True

    def run_post_episode_tasks(self) -> None:
        """[4-R1-d] Session wrap-up: logs, vector sync."""
        # [V62.3] Stage 4 루프 종료
        self.ctx.ui.log(f"\n{'=' * 50}")
        self.ctx.ui.log("📋 Stage 4 집필 세션 종료.")
        try:
            # [S4-P2-3] 자동화 환경에서 blocking input() 방지
            import sys

            if sys.stdin and sys.stdin.isatty():
                input("   ⏎ Enter를 누르면 메뉴로 돌아갑니다...")
            else:
                self.ctx.ui.log("   (비대화 모드 — 자동 진행)")
        except (EOFError, OSError):
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
