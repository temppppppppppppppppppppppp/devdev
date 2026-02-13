"""
[Phase 4C-1a] Stage3Orchestrator — SovereignApp의 Stage 3 Blueprint 배치 생성 로직 캡슐화

원본: main_a.py:2855-3254 (_stage_3_batch_blueprinting, 400줄)

패턴: self.app = SovereignApp 인스턴스 (Stage2/4 Orchestrator와 동일)
V68 lazy init: state_tracker, world_state, fact_ledger를 self.app에 할당
"""

import sys as _sys
import traceback as _traceback

from modules.core.constants import Emojis, ErrorMessages

try:
    from modules.utils.notifier import notifier
except Exception:  # notifier 미설치 시 비차단
    notifier = None


class Stage3Orchestrator:
    """
    [Phase 4C-1a] SovereignApp의 Stage 3 Blueprint 배치 생성 로직 캡슐화

    패턴: self.app = SovereignApp 인스턴스
    """

    def __init__(self, app) -> None:
        """
        Args:
            app: SovereignApp 인스턴스 (모든 속성 접근용)
        """
        self.app = app
        # [V61.6] Entity Registry 캐시 (Arc 단위)
        self._entity_cache_arc_idx = -1
        self._cached_entity_registry = None

    # ─────────────────────────────────────────────────────────────
    # Stage 3 메인 진입점
    # ─────────────────────────────────────────────────────────────
    def stage_3_batch_blueprinting(self) -> None:
        """
        [V60.80] Stage 3 - Three Phase Blueprint Generator

        3단계 파이프라인: 제약수집 → 앙상블생성 → 통합검증
        - Phase 1: Constraint compilation (Arc 섹션 추출, 연속성, 정지선)
        - Phase 2: Ensemble generation (3개 후보 → 최적 선택)
        - Phase 3: Unified validation (Python + LLM)

        철학: "Arc를 충실히 따르는, 연속성 있는 Blueprint"
        """
        app = self.app

        if not app.current_project.arcs:
            app.ui.log(f"{Emojis.ERROR} {ErrorMessages.STAGE_PREREQUISITE_MISSING}")
            return

        # ═══════════════════════════════════════════════════════════════
        # [V60.96] StateTracker 초기화 (Stage 2에서 생성되지 않은 경우)
        # ═══════════════════════════════════════════════════════════════
        self._init_state_tracker_if_needed()

        # ═══════════════════════════════════════════════════════════════
        # [V68] WorldStateManager 초기화
        # ═══════════════════════════════════════════════════════════════
        self._init_world_state_if_needed()

        # ═══════════════════════════════════════════════════════════════
        # [V68] FactLedger 초기화
        # ═══════════════════════════════════════════════════════════════
        self._init_fact_ledger_if_needed()

        # ═══════════════════════════════════════════════════════════════
        # 1. 목표 범위 설정
        # ═══════════════════════════════════════════════════════════════
        total_planned_ep = app.current_project.arcs[-1].get("ep_end", 50)

        # [V60.80 FIX] Blueprint 테이블 기준으로 시작점 결정
        existing_bp_max = app.current_project.db.get_latest_blueprint_number()  # 0 if empty

        # [Smart Skip] 기존 원고가 있다면 원고 기준으로도 체크
        existing_ms_max_ep = app._get_max_episode_from_manuscripts()

        # 둘 중 큰 값을 기준으로 (Blueprint나 원고가 있는 화 다음부터)
        production_head = max(existing_bp_max, existing_ms_max_ep)

        if production_head > 0:
            app.ui.log(f"📂 [Detected] Blueprint {existing_bp_max}화, 원고 {existing_ms_max_ep}화까지 발견")
        else:
            app.ui.log("📂 [Fresh Start] 기존 데이터 없음 - 1화부터 시작")

        app.ui.log(f"📊 [V60.80] 현재 총 {total_planned_ep}화까지 설계가 가능합니다.")
        target_ep = app._get_int_input(
            f"👉 몇 화까지 설계도를 생성하시겠습니까? (현재 {production_head}화 / 최대 {total_planned_ep}화): ",
            default=total_planned_ep,
            min_val=production_head + 1,
            max_val=total_planned_ep,
        )

        # ═══════════════════════════════════════════════════════════════
        # 2. 메인 에피소드 루프
        # ═══════════════════════════════════════════════════════════════
        working_ep = production_head + 1
        success_count = 0
        fail_count = 0
        prev_blueprints = []  # 연속성 검증용

        # [V67] 이전 Blueprint들 로드 (최근 30개 — Gemini 대용량 컨텍스트 활용)
        for prev_ep in range(max(1, working_ep - 30), working_ep):
            prev_bp = app.current_project.get_blueprint(prev_ep)
            if prev_bp:
                prev_blueprints.append(prev_bp)

        app.ui.log(f"\n{'═' * 60}")
        app.ui.log("🎯 [V60.80] Three Phase Blueprint Generator 시작")
        app.ui.log(f"   범위: 제{working_ep}화 ~ 제{target_ep}화 ({target_ep - working_ep + 1}개)")
        app.ui.log(f"{'═' * 60}\n")

        while working_ep <= target_ep:
            result = self._process_single_episode(
                working_ep, target_ep, prev_blueprints, success_count, fail_count
            )
            working_ep = result["next_ep"]
            success_count = result["success_count"]
            fail_count = result["fail_count"]
            if result.get("break"):
                break

        # ═══════════════════════════════════════════════════════════════
        # 3. 완료 처리
        # ═══════════════════════════════════════════════════════════════
        app._write_audit_summary("stage3_complete")

        # 통계 출력
        app.ui.log(f"\n{'═' * 60}")
        app.ui.log("📊 [V60.80] Stage 3 완료 통계")
        app.ui.log(f"   성공: {success_count}개 | 실패: {fail_count}개")
        if hasattr(app.agents.get("three_phase_bp"), "get_stats"):
            stats = app.agents["three_phase_bp"].get_stats()
            app.ui.log(f"   통과율: {stats.get('pass_rate', 'N/A')}")
        app.ui.log(f"{'═' * 60}\n")

        # Slack 알림
        if success_count > 0 and notifier:
            try:
                notifier.send_notification(
                    title="✅ [V60.80 Blueprint] 설계도 생성 완료",
                    message=f"프로젝트: {app.current_project.name}\n성공: {success_count}개 | 실패: {fail_count}개",
                    key_metrics={"성공": f"{success_count}개", "실패": f"{fail_count}개"},
                )
            except Exception as slack_err:
                app.ui.log(f"⚠️ [Slack] 알림 전송 실패: {str(slack_err)[:50]}")

    # ─────────────────────────────────────────────────────────────
    # V68 Lazy Init 헬퍼
    # ─────────────────────────────────────────────────────────────
    def _init_state_tracker_if_needed(self) -> None:
        """[V60.96] StateTracker lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "state_tracker") or app.state_tracker is None:
            from modules.domain.agents.state_tracker import StateTracker

            app.state_tracker = StateTracker(preset_registry=app.preset_registry, llm_client=app.sys.api_client)
            all_arcs = app.current_project.db.load_anchor("arcs") or []
            for arc in all_arcs:
                app.state_tracker.extract_npc_deaths_from_arc(arc)
                app.state_tracker.extract_skill_acquisitions_from_arc(arc)
                _g = app.selected_genre.get("type", "") if app.selected_genre else ""
                app.state_tracker.extract_npc_info_from_arc(arc, genre=_g)
                app.state_tracker.extract_resolved_plots_from_arc(arc)
            if app.state_tracker.npc_registry:
                dead_count = sum(1 for info in app.state_tracker.npc_registry.values() if info.get("status") == "dead")
                app.ui.log(
                    f"      👤 [V60.96] StateTracker 초기화: NPC {len(app.state_tracker.npc_registry)}명 (사망: {dead_count}명)"
                )

    def _init_world_state_if_needed(self) -> None:
        """[V68] WorldStateManager lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "world_state") or app.world_state is None:
            try:
                from modules.core.world_state import WorldStateManager

                app.world_state = WorldStateManager(app.current_project.db)
                _ws_ep = app.world_state.last_updated_ep
                if _ws_ep > 0:
                    app.ui.log(f"      🌍 [V68] WorldStateManager 로드 완료 (제{_ws_ep}화 기준)")
                else:
                    app.ui.log("      🌍 [V68] WorldStateManager 초기화 (신규)")
            except Exception as _ws_err:
                app.ui.log(f"      ⚠️ [V68] WorldStateManager 초기화 실패 (비차단): {str(_ws_err)[:60]}")
                app.world_state = None

    def _init_fact_ledger_if_needed(self) -> None:
        """[V68] FactLedger lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "fact_ledger") or app.fact_ledger is None:
            try:
                from modules.core.fact_ledger import FactLedger

                app.fact_ledger = FactLedger(app.current_project.db)
                _fl_ep = app.fact_ledger.last_updated_ep
                if _fl_ep > 0:
                    _fl_stats = app.fact_ledger.get_stats()
                    app.ui.log(
                        f"      📋 [V68] 팩트 원장 로드 완료 (제{_fl_ep}화 기준, 인물 {_fl_stats.get('characters', 0)}명, 아이템 {_fl_stats.get('items', 0)}개)"
                    )
                else:
                    app.ui.log("      📋 [V68] 팩트 원장 초기화 (신규)")
            except Exception as _fl_err:
                app.ui.log(f"      ⚠️ [V68] 팩트 원장 초기화 실패 (비차단): {str(_fl_err)[:60]}")
                app.fact_ledger = None

    # ─────────────────────────────────────────────────────────────
    # 에피소드 단위 처리
    # ─────────────────────────────────────────────────────────────
    def _process_single_episode(
        self,
        working_ep: int,
        target_ep: int,
        prev_blueprints: list,
        success_count: int,
        fail_count: int,
    ) -> dict:
        """단일 에피소드 Blueprint 생성 처리. 루프 상태를 dict로 반환."""
        app = self.app

        # 이미 설계도가 존재하면 스킵
        if app.current_project.get_blueprint(working_ep):
            app.ui.log(f"   ⏭️  제{working_ep}화 - 기존 설계도 존재, 스킵")
            return {"next_ep": working_ep + 1, "success_count": success_count, "fail_count": fail_count}

        # [V60.83] 직전 화 Blueprint 필수 체크 (연속성 보장)
        if working_ep > 1:
            prev_bp_check = app.current_project.get_blueprint(working_ep - 1)
            if not prev_bp_check:
                app.ui.log(f"🚨 [V60.83] 제{working_ep - 1}화 Blueprint 없음! 연속성 보장 불가.")
                app.ui.log(f"   → 제{working_ep - 1}화를 먼저 생성하세요.")
                app._audit_event(
                    "continuity_block",
                    f"ep_{working_ep}_blocked_no_prev",
                    {"blocked_ep": working_ep, "missing_ep": working_ep - 1},
                )
                return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        # Arc 컨텍스트 확보
        arc_idx, arc_data = app._get_arc_context_for_episode(working_ep)
        if arc_idx is None or arc_data is None:
            app.ui.log(f"❌ [V60.80] 제{working_ep}화의 Arc 컨텍스트를 찾을 수 없습니다.")
            return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        ep_start_val = arc_data.get("ep_start")
        if ep_start_val is None or not isinstance(ep_start_val, int):
            app.ui.log(f"⚠️ [Stop] Arc ep_start 누락: arc_idx={arc_idx}")
            app._audit_event("data_missing", "arc ep_start missing", {"arc_idx": arc_idx})
            return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        # Arc 데이터 검증
        arc_data_validated = app._validate_arc_data_fields(arc_data, arc_idx)
        if arc_data_validated:
            arc_data = arc_data_validated

        arc_no = arc_data.get("arc_no", arc_idx + 1)

        # Entity Registry 추출/캐시
        entity_registry_for_stage3 = self._get_entity_registry(arc_idx)

        # 직전 Blueprint 로드
        prev_blueprint = self._load_prev_blueprint(working_ep)

        # 주인공 이름 추출
        protagonist_name_for_stage3 = self._get_protagonist_name_safe()

        # Three Phase Blueprint Generation
        app.ui.log(
            f"\n   📐 제{working_ep}화 Blueprint 생성 중... (Arc {arc_no}, 주인공: {protagonist_name_for_stage3})"
        )

        # [V67.1] protagonist_config 추출
        _bp_protagonist_config = {}
        try:
            _bp_bible_root = app.current_project.master_bible.get("MasterBible", app.current_project.master_bible)
            _bp_protagonist_config = _bp_bible_root.get("protagonist_config", {})
        except Exception:
            pass

        blueprint, pipeline_result = self._generate_blueprint(
            working_ep, arc_data, arc_idx, prev_blueprint, prev_blueprints,
            entity_registry_for_stage3, protagonist_name_for_stage3, _bp_protagonist_config,
        )

        # 결과 처리
        if blueprint and pipeline_result.get("final_verdict") == "PASS":
            return self._handle_success(
                working_ep, arc_no, blueprint, pipeline_result, prev_blueprints, success_count, fail_count
            )
        else:
            return self._handle_failure(working_ep, pipeline_result, success_count, fail_count)

    # ─────────────────────────────────────────────────────────────
    # Entity Registry 캐시
    # ─────────────────────────────────────────────────────────────
    def _get_entity_registry(self, arc_idx: int):
        """[V61.6] Arc 단위 Entity Registry 캐시 관리"""
        app = self.app

        if self._entity_cache_arc_idx != arc_idx:
            app.ui.log(f"      ⏳ Entity Registry 추출 중... (Arc {arc_idx}, 첫 호출)")
            try:
                if "state_extractor" in app.agents and app.current_project.arcs:
                    all_arcs_for_entity = list(app.current_project.arcs)[: arc_idx + 1]
                    if all_arcs_for_entity:
                        state_for_entity = app.agents["state_extractor"].extract_cumulative_state(
                            all_arcs_for_entity
                        )
                        self._cached_entity_registry = (
                            state_for_entity.get("entity_registry") if state_for_entity else None
                        )
                        if self._cached_entity_registry:
                            stage3_protag = app._get_protagonist_name()
                            self._cached_entity_registry = app._fix_entity_registry_protagonist(
                                self._cached_entity_registry, stage3_protag
                            )
                            total_entities = sum(
                                len(v) for v in self._cached_entity_registry.values() if isinstance(v, list)
                            )
                            app.ui.log(f"      📋 [V61] Entity Registry 추출: {total_entities}개 엔티티")
                    else:
                        self._cached_entity_registry = None
                else:
                    self._cached_entity_registry = None
                self._entity_cache_arc_idx = arc_idx
            except Exception as entity_err:
                app.ui.log(f"      ⚠️ [V61] Entity Registry 추출 실패: {str(entity_err)[:50]}")
                self._cached_entity_registry = None
                self._entity_cache_arc_idx = arc_idx
        else:
            app.ui.log(f"      ♻️ [V61.6] Entity Registry 캐시 재사용 (Arc {arc_idx})")

        return self._cached_entity_registry

    def _load_prev_blueprint(self, working_ep: int):
        """직전 Blueprint 로드 [V61.3 보호]"""
        prev_blueprint = None
        try:
            prev_blueprint = self.app.current_project.get_blueprint(working_ep - 1) if working_ep > 1 else None
        except Exception as prev_bp_err:
            print(f"🚨 [V61.3] prev_blueprint 로드 크래시: {str(prev_bp_err)[:100]}", file=_sys.stderr)
            _traceback.print_exc(file=_sys.stderr)
            _sys.stderr.flush()
            self.app.ui.log("      ⚠️ 직전 Blueprint 로드 실패, None으로 진행")
        return prev_blueprint

    def _get_protagonist_name_safe(self) -> str:
        """주인공 이름 추출 [V61.3 보호]"""
        protagonist_name = "주인공"
        try:
            protagonist_name = self.app._get_protagonist_name()
        except Exception as protag_err:
            print(f"🚨 [V61.3] protagonist_name 추출 크래시: {str(protag_err)[:100]}", file=_sys.stderr)
            _traceback.print_exc(file=_sys.stderr)
            _sys.stderr.flush()
            self.app.ui.log("      ⚠️ 주인공 이름 추출 실패, 기본값 사용")
        return protagonist_name

    # ─────────────────────────────────────────────────────────────
    # Blueprint 생성 (LLM 호출)
    # ─────────────────────────────────────────────────────────────
    def _generate_blueprint(
        self,
        working_ep, arc_data, arc_idx, prev_blueprint, prev_blueprints,
        entity_registry, protagonist_name, protagonist_config,
    ):
        """[V60.80] Three Phase Blueprint Generation — LLM 호출 + 스피너"""
        app = self.app
        from modules.core.spinners import StageSpinner

        try:
            _bp_semantic_ctx = ""

            with StageSpinner(3, f"제{working_ep}화"):
                # [V67] 이전 원고 로드 (Blueprint 모순 방지용)
                _prev_ms_for_bp = []
                for _ms_ep in range(max(1, working_ep - 30), working_ep):
                    _ms_data = app.current_project.db.get_manuscript(_ms_ep)
                    if _ms_data:
                        _ms_text = (
                            _ms_data.get("content", "") if isinstance(_ms_data, dict) else str(_ms_data)
                        )
                        if _ms_text:
                            _prev_ms_for_bp.append(f"━━━ 제{_ms_ep}화 원고 ━━━\n{_ms_text}")
                _prev_ms_text_for_bp = "\n\n".join(_prev_ms_for_bp) if _prev_ms_for_bp else ""
                if len(_prev_ms_text_for_bp) > 200000:
                    _prev_ms_text_for_bp = _prev_ms_text_for_bp[:200000] + "\n... (200K자 절삭)"
                if _prev_ms_for_bp:
                    print(
                        f"      📚 [V67] Blueprint용 이전 원고 {len(_prev_ms_for_bp)}개 로드 ({len(_prev_ms_text_for_bp):,}자)"
                    )

                blueprint, pipeline_result = app.agents["three_phase_bp"].generate(
                    ep_num=working_ep,
                    arc_data=arc_data,
                    prev_blueprint=prev_blueprint,
                    prev_blueprints=prev_blueprints[-30:] if prev_blueprints else None,
                    max_retries=4,
                    director=app.agents["director"],
                    arc_idx=arc_idx,
                    entity_registry=entity_registry,
                    protagonist_name=protagonist_name,
                    protagonist_config=protagonist_config,
                    state_tracker=getattr(app, "state_tracker", None),
                    db=app.current_project.db,
                    semantic_context=_bp_semantic_ctx,
                    prev_manuscripts_text=_prev_ms_text_for_bp,
                )

        except Exception as gen_err:
            print(f"🚨 [V61.3] 제{working_ep}화 Blueprint 생성 크래시: {str(gen_err)[:100]}", file=_sys.stderr)
            _traceback.print_exc(file=_sys.stderr)
            _sys.stderr.flush()

            app.ui.log(f"❌ [V60.80] 제{working_ep}화 생성 실패: {str(gen_err)[:100]}")
            app._audit_event("blueprint_gen_error", str(gen_err)[:200], {"ep_num": working_ep})
            blueprint = None
            pipeline_result = {"final_verdict": "ERROR", "error": str(gen_err)[:200]}

        return blueprint, pipeline_result

    # ─────────────────────────────────────────────────────────────
    # 결과 처리
    # ─────────────────────────────────────────────────────────────
    def _handle_success(
        self, working_ep, arc_no, blueprint, pipeline_result, prev_blueprints, success_count, fail_count
    ) -> dict:
        """Blueprint 생성 성공 시 저장 + 메트릭 기록"""
        app = self.app

        # 무결성 검증 후 저장
        if not app._validate_blueprint_integrity(blueprint):
            app.ui.log(f"   🚨 [Integrity] 제{working_ep}화 Blueprint 무결성 실패")
            app._audit_event("integrity_fail", "blueprint integrity check failed", {"ep_num": working_ep})
            return {"next_ep": working_ep + 1, "success_count": success_count, "fail_count": fail_count + 1}

        # DB에 저장
        app.current_project.save_episode_blueprint(working_ep, blueprint)
        app._safe_commit()

        # prev_blueprints 업데이트
        prev_blueprints.append(blueprint)
        if len(prev_blueprints) > 30:
            prev_blueprints[:] = prev_blueprints[-30:]

        # 메트릭 기록
        app._audit_event(
            "blueprint_success",
            f"ep_{working_ep}_blueprint_generated",
            {
                "ep_num": working_ep,
                "arc_no": arc_no,
                "strategy": pipeline_result.get("phases", {})
                .get("generate", {})
                .get("selected_strategy", "unknown"),
                "score": pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0),
            },
        )

        app.ui.log(f"   ✅ 제{working_ep}화 Blueprint 저장 완료")
        return {"next_ep": working_ep + 1, "success_count": success_count + 1, "fail_count": 0}

    def _handle_failure(self, working_ep, pipeline_result, success_count, fail_count) -> dict:
        """Blueprint 생성 실패 시 처리"""
        app = self.app

        app.ui.log(f"   ❌ 제{working_ep}화 Blueprint 생성 실패")
        app._audit_event(
            "blueprint_fail",
            f"ep_{working_ep}_all_retries_exhausted",
            {"ep_num": working_ep, "final_verdict": pipeline_result.get("final_verdict", "UNKNOWN")},
        )
        new_fail_count = fail_count + 1

        # 연속 실패 3회 시 중단
        if new_fail_count >= 3:
            app.ui.log(f"🛑 [Safety] 연속 {new_fail_count}회 실패로 공정을 중단합니다.")
            return {"next_ep": working_ep + 1, "success_count": success_count, "fail_count": new_fail_count, "break": True}

        return {"next_ep": working_ep + 1, "success_count": success_count, "fail_count": new_fail_count}
