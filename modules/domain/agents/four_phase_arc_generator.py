"""
[V60.75] Three Phase Arc Generator (구 Four Phase)
3단계 Arc 생성 파이프라인 - 단순화 + 효율화

철학: "충분한 분량의, 상호 개연성 및 일관성 있는 Arc"

파이프라인:
1. Constraint: 제약 수집 (Preflight + Compiler + NegativeExamples)
2. Generate: Ensemble 생성 (3개 후보 → 최적 선택)
3. Validate: 통합 검증 (Python + LLM)

[V60.75 리팩토링]
- 기존: Preflight → Ensemble → Phase2.5 → Critic → Consensus (5단계, 8 LLM호출)
- 변경: Constraint → Generate → Validate (3단계, 4 LLM호출)
- 효과: 비용 50% 절감, 책임 명확화
"""

import json
import logging

from modules.core.constants import Stage2Limits

from .arc_ensemble import ArcEnsembleGenerator
from .base_agent import BaseAgent, _get_sub_component_models
from .constraint_compiler import ConstraintCompiler
from .negative_example_injector import NegativeExampleInjector
from .preflight_checker import PreflightChecker
from .unified_arc_validator import UnifiedArcValidator


class FourPhaseArcGenerator(BaseAgent):
    """
    [V60.75] Three Phase Arc Generator

    3단계 파이프라인: 제약수집 → 생성 → 검증
    (클래스명은 호환성을 위해 유지)
    """

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)

        # 서브 모듈
        sub_models = _get_sub_component_models("four_phase_arc_generator")
        self.preflight = PreflightChecker(context, client, sub_models.get("preflight", "gemini-3-flash-preview"))
        self.ensemble = ArcEnsembleGenerator(context, client, sub_models.get("ensemble", "gemini-2.5-pro"))
        self.validator = UnifiedArcValidator(context, client, sub_models.get("validator", "gemini-2.5-flash"))
        self.compiler = ConstraintCompiler()
        self.negative_injector = NegativeExampleInjector("wuxia")

        # 통계
        self.stats = {
            "total_attempts": 0,
            "phase1_complete": 0,
            "phase2_complete": 0,
            "phase3_pass": 0,
            "phase3_reject": 0,
        }

    def _determine_ep_count(self, curr_block: dict, arc_no: int, prev_arcs: list[dict]) -> tuple[int, str]:
        """
        [V66.1] Python 휴리스틱 기반 가변 페이싱 - ep_count 동적 결정 (정보량 기반)

        LLM 호출 없이 블록 텍스트 길이/문장 수로 적정 화수를 판단.
        기존 LLM 호출 대비 5-10s 절감.

        Args:
            curr_block: 현재 블록 DNA
            arc_no: Arc 번호
            prev_arcs: 이전 Arc 리스트

        Returns:
            (ep_count, reasoning) - 3~7 범위의 화수와 결정 이유
        """
        # 블록 내용 추출
        block_content = ""
        if isinstance(curr_block, dict):
            for key in ["context", "event_villain", "solution", "reward", "content"]:
                val = curr_block.get(key, "")
                if isinstance(val, str):
                    block_content += val + " "
                elif isinstance(val, dict):
                    block_content += json.dumps(val, ensure_ascii=False) + " "

        content_len = len(block_content.strip())

        # [V66.1] Python 휴리스틱: 텍스트 길이 + 문장 수 기반 판단
        if content_len < 500:
            ep_count = Stage2Limits.MIN_EP_COUNT  # 3화
            reasoning = f"블록 정보량 부족 ({content_len}자 < 500자) → 최소 화수"
        elif content_len > 1500:
            ep_count = Stage2Limits.MAX_EP_COUNT  # 7화
            reasoning = f"블록 정보량 풍부 ({content_len}자 > 1500자) → 최대 화수"
        else:
            # 500~1500자 구간: 문장 수 비례로 4~6화 결정
            import re

            sentence_count = len(re.split(r"[.。!?!\?\n]+", block_content))
            if sentence_count <= 8:
                ep_count = 4
                reasoning = f"보통 정보량 ({content_len}자, {sentence_count}문장) → 4화"
            elif sentence_count >= 15:
                ep_count = 6
                reasoning = f"높은 정보량 ({content_len}자, {sentence_count}문장) → 6화"
            else:
                ep_count = Stage2Limits.DEFAULT_EP_COUNT  # 5화
                reasoning = f"표준 정보량 ({content_len}자, {sentence_count}문장) → 기본 5화"

        # 범위 강제 (안전장치)
        ep_count = max(Stage2Limits.MIN_EP_COUNT, min(Stage2Limits.MAX_EP_COUNT, ep_count))

        return ep_count, reasoning

    def generate(
        self,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arcs: list[dict],
        assets: dict = None,
        max_internal_retries: int = 2,
        protagonist_name: str = "주인공",
        director_feedback: str = "",
        entity_registry: dict = None,  # [V60.92] Entity Registry (NPC 명칭 일관성)
        state_tracker=None,  # [V60.94] StateTracker (죽은 NPC 검증용)
        vector_context: str = "",  # [V63.3] 벡터 검색 결과
    ) -> tuple[dict | None, dict]:
        """
        3단계 Arc 생성

        Args:
            arc_no: Arc 번호
            ep_start: 시작 화수
            vol_strategy: Volume 전략
            curr_block: 현재 블록 DNA
            prev_arcs: 이전 Arc 리스트
            assets: AssetLibrary
            max_internal_retries: 내부 재시도 횟수
            protagonist_name: 주인공 이름
            director_feedback: [V60.77] Director REJECT 피드백 (재시도 시 반영)
            entity_registry: [V60.92] Entity Registry (NPC 명칭 일관성)
            state_tracker: [V60.94] StateTracker (죽은 NPC 검증용)
            vector_context: [V63.3] 벡터 검색 결과 (과거 유사 맥락)

        Returns:
            (generated_arc, pipeline_result)
        """
        self.stats["total_attempts"] += 1

        # [V60.88] protagonist_config 추출 (context에서 직접 로드)
        protagonist_config = {}
        try:
            master_bible = getattr(self.context, "master_bible", {})
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible)
                protagonist_config = bible_root.get("protagonist_config", {})
        except Exception:
            pass

        # [V61.1] LLM 기반 가변 페이싱 - ep_count 동적 결정
        ep_count, pacing_reason = self._determine_ep_count(curr_block, arc_no, prev_arcs)
        logging.info(f"📊 [V61.1] 가변 페이싱: {ep_count}화 결정 - {pacing_reason}")

        ep_end = ep_start + ep_count - 1

        pipeline_result = {"arc_no": arc_no, "phases": {}, "final_verdict": None, "retries": 0}

        # [V62.5] 이전 Arc 아이템/수여물 사전 수집 (UnifiedArcValidator 중복 스캔 방지)
        _pre_items = set()
        _pre_grants = set()
        for _prev in prev_arcs:
            _acq = _prev.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(_acq, list):
                _pre_items.update(i.strip() for i in _acq if i)
            _grt = _prev.get("state_constraints", {}).get("grants_received", [])
            if isinstance(_grt, list):
                _pre_grants.update(g.strip() for g in _grt if g)

        # Preflight 캐싱
        cached_constraint_block = None
        cached_preflight = None
        # [V60.77] Director 피드백이 있으면 우선 반영
        feedback = ""
        if director_feedback:
            feedback = f"[🎬 Director 피드백 - 반드시 반영할 것]\n{director_feedback}\n"
            logging.info(f"📢 [V60.77] Director 피드백 주입됨 ({len(director_feedback)}자)")

        for retry in range(max_internal_retries + 1):
            pipeline_result["retries"] = retry

            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: CONSTRAINT - 제약 수집
            # ═══════════════════════════════════════════════════════════════
            if cached_constraint_block and retry > 0:
                logging.info("📋 [Phase 1] 제약 캐시 사용")
                full_constraint_block = cached_constraint_block
                preflight_result = cached_preflight
            else:
                logging.info(f"📋 [Phase 1] 제약 수집 중... (이전 Arc {len(prev_arcs)}개)")

                preflight_result = self.preflight.analyze(prev_arcs)
                preflight_injection = self.preflight.generate_analyst_injection(preflight_result)
                compiled_constraints = self.compiler.compile(prev_arcs)
                negative_examples = self.negative_injector.generate_injection()
                self_check = self.negative_injector.generate_self_check_prompt()

                full_constraint_block = "\n".join(
                    [preflight_injection, compiled_constraints, negative_examples, self_check]
                )

                cached_preflight = preflight_result
                cached_constraint_block = full_constraint_block

            pipeline_result["phases"]["constraint"] = {
                "status": "complete" if retry == 0 else "cached",
                "constraint_block_length": len(full_constraint_block),
            }
            self.stats["phase1_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GENERATE - Ensemble 생성
            # ═══════════════════════════════════════════════════════════════
            logging.info("🎲 [Phase 2] Ensemble 생성 중 (3개 후보)...")

            prev_arc_context = self._generate_prev_context(prev_arcs, preflight_result)
            # [V63.3] 벡터 메모리 컨텍스트 주입
            if vector_context:
                prev_arc_context = f"{prev_arc_context}\n\n[과거 유사 맥락 (벡터 검색)]\n{vector_context}"

            best_arc, all_candidates = self.ensemble.generate_ensemble(
                arc_no=arc_no,
                ep_start=ep_start,
                vol_strategy=vol_strategy,
                curr_block=curr_block,
                prev_arc_context=prev_arc_context,
                constraint_block=full_constraint_block,
                assets=assets,
                feedback=feedback,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,  # [V60.88]
                entity_registry=entity_registry,  # [V60.92] Entity Registry
                ep_count=ep_count,  # [V61.1] 가변 페이싱
                retry=retry,  # [V61.5] 재시도 시 thinking 다운그레이드
            )

            if not best_arc:
                logging.warning("❌ [Phase 2] Ensemble 생성 실패")
                pipeline_result["phases"]["generate"] = {"status": "failed"}
                feedback = "Ensemble 생성 실패. 다시 시도하세요."
                continue

            pipeline_result["phases"]["generate"] = {
                "status": "complete",
                "candidates_count": len(all_candidates),
                "selected_strategy": best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown"),
            }
            self.stats["phase2_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2.5: AUTO-SANITIZE - 부상 에스컬레이션 자동 세정
            # ═══════════════════════════════════════════════════════════════
            best_arc = self._auto_sanitize_injuries(best_arc)

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: VALIDATE - 통합 검증
            # ═══════════════════════════════════════════════════════════════
            logging.info("🔍 [Phase 3] 통합 검증 중...")

            verdict, validation_result = self.validator.validate(
                arc=best_arc,
                prev_arcs=prev_arcs,
                constraints=full_constraint_block,
                state_tracker=state_tracker,  # [V60.94] 죽은 NPC 검증용
                pre_collected_items=_pre_items,  # [V62.5] 중복 스캔 방지
                pre_collected_grants=_pre_grants,  # [V62.5] 중복 스캔 방지
            )

            pipeline_result["phases"]["validate"] = {
                "status": "complete",
                "verdict": verdict,
                "issues_count": len(validation_result.get("issues", [])),
                "confidence": validation_result.get("confidence", 0),
            }

            if verdict == "PASS":
                self.stats["phase3_pass"] += 1
                pipeline_result["final_verdict"] = "PASS"
                logging.info(f"✅ [Phase 3] PASS - Arc {arc_no} 생성 완료")
                return best_arc, pipeline_result
            else:
                self.stats["phase3_reject"] += 1
                feedback = validation_result.get("feedback", "검증 실패")

                # REJECT 기록
                issues = validation_result.get("issues", [])
                if issues:
                    first_issue = issues[0]
                    self.negative_injector.record_rejection(
                        best_arc, first_issue.get("issue", "알 수 없음"), first_issue.get("category", "unknown")
                    )

                    # 이슈 출력
                    logging.warning("🚨 [Phase 3] REJECT - 주요 이슈:")
                    for issue in issues[:3]:
                        sev = issue.get("severity", "?")
                        cat = issue.get("category", "?")
                        text = issue.get("issue", "?")
                        logging.info(f"[{sev}][{cat}] {text}")

                logging.warning(f"❌ [Phase 3] REJECT - 재시도 {retry + 1}/{max_internal_retries + 1}")

        # 모든 재시도 실패
        pipeline_result["final_verdict"] = "FAILED"
        logging.warning(f"❌ [ThreePhase] Arc {arc_no} 모든 재시도 실패 ({max_internal_retries + 1}회)")
        if feedback:
            logging.info(f"마지막 피드백: {feedback[:200]}...")
        return None, pipeline_result

    def _generate_prev_context(self, prev_arcs: list[dict], preflight_result: dict) -> str:
        """[V67] 이전 Arc 컨텍스트 생성 - 전문 확장 (Gemini 대용량 컨텍스트 활용)"""
        if not prev_arcs:
            return "서사 시작점 (첫 Arc)"

        lines = []
        last_arc = prev_arcs[-1]
        last_arc_no = last_arc.get("arc_no", "?")

        state = last_arc.get("state_constraints", {})
        arc_end = state.get("arc_end_state", {})
        joint = last_arc.get("joint_docs", {})
        shadow = last_arc.get("status_shadow", {})

        # 상태 추출 (arc_end_state 우선) + [V62.2] 아크 간 자연 회복
        raw_energy = arc_end.get("internal_energy")
        if raw_energy is None:
            loss_str = shadow.get("internal_energy_loss", "0%")
            try:
                import re

                _m = re.search(r"(\d+)", str(loss_str))  # [V70] None 방어
                loss = int(_m.group(1)) if _m else 0
                raw_energy = max(0, 100 - loss)
            except Exception:
                raw_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK

        # [V62.2] 내공 자연 회복: 아크 간 시간 경과로 최소 100%로 회복
        final_energy = 100
        if isinstance(raw_energy, (int, float)) and raw_energy < 100:
            logging.info(f"🩹 [V62.2] 내공 자연 회복: {int(raw_energy)}% → 100% (아크 간 휴식)")

        raw_injuries = arc_end.get("injuries") or shadow.get("expected_injuries", "없음")
        final_injuries = self._sanitize_injuries(raw_injuries)
        final_location = arc_end.get("location") or joint.get("final_location", "알 수 없음")
        final_equipment = arc_end.get("equipment") or joint.get("physical_inventory", [])
        if isinstance(final_equipment, str):
            final_equipment = [i.strip() for i in final_equipment.split(",") if i.strip()]

        # 필수 계승 블록
        lines.append("=" * 50)
        lines.append(f"🔴 [Arc {last_arc_no} 종료 상태 → 다음 Arc 필수 시작 조건]")
        lines.append("=" * 50)
        lines.append(f"✅ 내공: {final_energy}%")
        lines.append(f"✅ 부상: {final_injuries}")
        lines.append(f"✅ 위치: {final_location}")
        lines.append(f"✅ 소지품: {final_equipment}")
        lines.append("=" * 50)
        lines.append("")

        # 보조 정보
        world = preflight_result.get("world_state", {})
        conflicts = world.get("ongoing_conflicts", [])
        if conflicts:
            lines.append(f"진행 중인 갈등: {', '.join(conflicts[:3])}")

        # [V62.7] 완결된 갈등 (재생성 금지)
        resolved = world.get("resolved_conflicts", [])
        if resolved:
            lines.append(f"완결된 갈등 (재생성 금지): {', '.join(resolved[:5])}")

        relationships = preflight_result.get("relationship_map", {})
        if relationships:
            rel_summary = ", ".join([f"{k}: {v.get('current_state', '?')}" for k, v in list(relationships.items())[:5]])
            lines.append(f"주요 관계: {rel_summary}")

        # ── [V67] 이전 Arc tactical_doc 전문 확장 (최대 30개) ──
        _prev_start = max(0, len(prev_arcs) - 30)
        _arc_history_lines = []
        for _pa in prev_arcs[_prev_start:]:
            _pa_no = _pa.get("arc_no", "?")
            _pa_ep_s = _pa.get("ep_start", "?")
            _pa_ep_e = _pa.get("ep_end", "?")
            _pa_td = _pa.get("tactical_doc", "")
            if isinstance(_pa_td, dict):
                import json

                _pa_td = json.dumps(_pa_td, ensure_ascii=False)
            if _pa_td:
                _arc_history_lines.append(f"━━━ Arc {_pa_no} (제{_pa_ep_s}화~제{_pa_ep_e}화) ━━━\n{_pa_td}")
        if _arc_history_lines:
            _full_history = "\n\n".join(_arc_history_lines)
            # 200K자 상한
            if len(_full_history) > 200000:
                _full_history = _full_history[:200000] + "\n... (200K자 절삭)"
            lines.append("")
            lines.append(f"[V67] ═══ 이전 Arc 전술서 전문 ({len(_arc_history_lines)}개) ═══")
            lines.append(_full_history)
            logging.info(
                f"📚 [V67] FourPhase prev_context 확장: {len(_arc_history_lines)}개 Arc 전술서 ({len(_full_history):,}자)"
            )

        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # [V62.2] Injury Escalation Guard
    # 부상 자기강화 루프 차단: 만성질환/에스컬레이션 필터
    # ──────────────────────────────────────────────
    CHRONIC_INJURY_KEYWORDS = [
        "성대 결절",
        "성대결절",
        "실명",
        "마비",
        "불구",
        "절단",
        "암",
        "종양",
        "만성",
        "대화 불가",
        "말 못함",
        "목소리 상실",
        "청력 상실",
        "시력 상실",
        "반신불수",
        "전신 탈진",
        "코피",
    ]

    def _sanitize_injuries(self, raw: str) -> str:
        """[V62.2] 이전 Arc → 다음 Arc 전파 시 부상은 항상 '없음'.
        소설 세계관: 아크 간 시간 경과로 자연 치유 가정 (힐링팩터).
        """
        if not raw or raw.strip() in ("없음", "정상", ""):
            return "없음"
        logging.info(f"🩹 [V62.2] 자연 치유: '{raw[:50]}' → '없음' (아크 간 회복)")
        return "없음"

    def _auto_sanitize_injuries(self, arc: dict) -> dict:
        """[V62.2] 생성된 Arc 종료 시 자연 회복 적용.
        - 부상: arc_end → '없음'
        - 내공: arc_end → 100% 복원
        """
        cleaned = 0

        sc = arc.get("state_constraints", {})
        end_state = sc.get("arc_end_state", {})
        if isinstance(end_state, dict):
            # 부상 → 없음
            inj = str(end_state.get("injuries", "없음"))
            if inj not in ("없음", "정상", ""):
                end_state["injuries"] = "없음"
                cleaned += 1
            # 내공 → 100%
            energy = end_state.get("internal_energy")
            if isinstance(energy, (int, float)) and energy < 100:
                end_state["internal_energy"] = 100
                cleaned += 1

        # status_shadow
        ss = arc.get("status_shadow", {})
        if isinstance(ss, dict):
            ei = str(ss.get("expected_injuries", "없음"))
            if ei not in ("없음", "정상", ""):
                ss["expected_injuries"] = "없음"
                cleaned += 1
            # energy_loss → 0%
            el = ss.get("internal_energy_loss", "")
            if el and el != "0%":
                ss["internal_energy_loss"] = "0%"
                cleaned += 1

        if cleaned:
            logging.info(f"🩹 [V62.2] 자연 회복 적용: {cleaned}건 (부상→없음, 내공→100%)")

        return arc

    def get_stats(self) -> dict:
        """통계 반환"""
        total = self.stats["total_attempts"]
        if total == 0:
            return self.stats

        return {**self.stats, "pass_rate": f"{(self.stats['phase3_pass'] / total * 100):.1f}%" if total > 0 else "N/A"}

    def print_stats(self) -> None:
        """통계 출력"""
        stats = self.get_stats()
        logging.info("\n[ThreePhaseArcGenerator 통계]")
        logging.info(f"총 시도: {stats['total_attempts']}")
        logging.info(f"Phase 1 완료: {stats['phase1_complete']}")
        logging.info(f"Phase 2 완료: {stats['phase2_complete']}")
        logging.info(f"Phase 3 PASS: {stats['phase3_pass']}")
        logging.warning(f"Phase 3 REJECT: {stats['phase3_reject']}")
        logging.info(f"최종 통과율: {stats.get('pass_rate', 'N/A')}")


def create_four_phase_generator(context, client, model_tier: str = "gemini-2.5-pro"):
    """FourPhaseArcGenerator 생성 헬퍼 (호환성 유지)"""
    return FourPhaseArcGenerator(context, client, model_tier)
