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
from typing import Dict, List, Any, Optional, Tuple

from .base_agent import BaseAgent
from .preflight_checker import PreflightChecker
from .arc_ensemble import ArcEnsembleGenerator
from .unified_arc_validator import UnifiedArcValidator
from .constraint_compiler import ConstraintCompiler
from .negative_example_injector import NegativeExampleInjector
from modules.core.constants import Stage2Limits


class FourPhaseArcGenerator(BaseAgent):
    """
    [V60.75] Three Phase Arc Generator

    3단계 파이프라인: 제약수집 → 생성 → 검증
    (클래스명은 호환성을 위해 유지)
    """

    def __init__(self, context, client, model_tier: str = "gemini-3-pro-preview"):
        super().__init__(context, client, model_tier)

        # 서브 모듈
        self.preflight = PreflightChecker(context, client, "gemini-3-flash-preview")
        self.ensemble = ArcEnsembleGenerator(context, client, "gemini-3-pro-preview")
        self.validator = UnifiedArcValidator(context, client, "gemini-2.5-flash")
        self.compiler = ConstraintCompiler()
        self.negative_injector = NegativeExampleInjector("wuxia")

        # 통계
        self.stats = {
            "total_attempts": 0,
            "phase1_complete": 0,
            "phase2_complete": 0,
            "phase3_pass": 0,
            "phase3_reject": 0
        }

    def generate(
        self,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: Dict,
        prev_arcs: List[Dict],
        assets: Dict = None,
        max_internal_retries: int = 2,
        protagonist_name: str = "주인공",
        director_feedback: str = "",
        entity_registry: Dict = None,  # [V60.92] Entity Registry (NPC 명칭 일관성)
        state_tracker=None  # [V60.94] StateTracker (죽은 NPC 검증용)
    ) -> Tuple[Optional[Dict], Dict]:
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

        Returns:
            (generated_arc, pipeline_result)
        """
        self.stats["total_attempts"] += 1

        # [V60.88] protagonist_config 추출 (context에서 직접 로드)
        protagonist_config = {}
        try:
            master_bible = getattr(self.context, 'master_bible', {})
            if master_bible:
                bible_root = master_bible.get('MasterBible', master_bible)
                protagonist_config = bible_root.get('protagonist_config', {})
        except Exception:
            pass

        # ep_count 추출 및 검증
        if isinstance(curr_block, dict):
            ep_count = curr_block.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)
        else:
            print(f"      ⚠️ [V60.75] curr_block 타입 오류 → ep_count={Stage2Limits.DEFAULT_EP_COUNT}")
            ep_count = Stage2Limits.DEFAULT_EP_COUNT

        # 범위 강제 (3~7)
        if not isinstance(ep_count, int) or ep_count < Stage2Limits.MIN_EP_COUNT or ep_count > Stage2Limits.MAX_EP_COUNT:
            print(f"      ⚠️ [V60.75] ep_count 범위 오류: {ep_count} → {Stage2Limits.DEFAULT_EP_COUNT}")
            ep_count = Stage2Limits.DEFAULT_EP_COUNT

        ep_end = ep_start + ep_count - 1

        pipeline_result = {
            "arc_no": arc_no,
            "phases": {},
            "final_verdict": None,
            "retries": 0
        }

        # Preflight 캐싱
        cached_constraint_block = None
        cached_preflight = None
        # [V60.77] Director 피드백이 있으면 우선 반영
        feedback = ""
        if director_feedback:
            feedback = f"[🎬 Director 피드백 - 반드시 반영할 것]\n{director_feedback}\n"
            print(f"      📢 [V60.77] Director 피드백 주입됨 ({len(director_feedback)}자)")

        for retry in range(max_internal_retries + 1):
            pipeline_result["retries"] = retry

            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: CONSTRAINT - 제약 수집
            # ═══════════════════════════════════════════════════════════════
            if cached_constraint_block and retry > 0:
                print(f"      📋 [Phase 1] 제약 캐시 사용")
                full_constraint_block = cached_constraint_block
                preflight_result = cached_preflight
            else:
                print(f"      📋 [Phase 1] 제약 수집 중...")

                preflight_result = self.preflight.analyze(prev_arcs)
                preflight_injection = self.preflight.generate_analyst_injection(preflight_result)
                compiled_constraints = self.compiler.compile(prev_arcs)
                negative_examples = self.negative_injector.generate_injection()
                self_check = self.negative_injector.generate_self_check_prompt()

                full_constraint_block = "\n".join([
                    preflight_injection,
                    compiled_constraints,
                    negative_examples,
                    self_check
                ])

                cached_preflight = preflight_result
                cached_constraint_block = full_constraint_block

            pipeline_result["phases"]["constraint"] = {
                "status": "complete" if retry == 0 else "cached",
                "constraint_block_length": len(full_constraint_block)
            }
            self.stats["phase1_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GENERATE - Ensemble 생성
            # ═══════════════════════════════════════════════════════════════
            print(f"      🎲 [Phase 2] Ensemble 생성 중 (3개 후보)...")

            prev_arc_context = self._generate_prev_context(prev_arcs, preflight_result)

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
                entity_registry=entity_registry  # [V60.92] Entity Registry
            )

            if not best_arc:
                print(f"      ❌ [Phase 2] Ensemble 생성 실패")
                pipeline_result["phases"]["generate"] = {"status": "failed"}
                feedback = "Ensemble 생성 실패. 다시 시도하세요."
                continue

            pipeline_result["phases"]["generate"] = {
                "status": "complete",
                "candidates_count": len(all_candidates),
                "selected_strategy": best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown")
            }
            self.stats["phase2_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: VALIDATE - 통합 검증
            # ═══════════════════════════════════════════════════════════════
            print(f"      🔍 [Phase 3] 통합 검증 중...")

            verdict, validation_result = self.validator.validate(
                arc=best_arc,
                prev_arcs=prev_arcs,
                constraints=full_constraint_block,
                state_tracker=state_tracker  # [V60.94] 죽은 NPC 검증용
            )

            pipeline_result["phases"]["validate"] = {
                "status": "complete",
                "verdict": verdict,
                "issues_count": len(validation_result.get("issues", [])),
                "confidence": validation_result.get("confidence", 0)
            }

            if verdict == "PASS":
                self.stats["phase3_pass"] += 1
                pipeline_result["final_verdict"] = "PASS"
                print(f"      ✅ [Phase 3] PASS - Arc {arc_no} 생성 완료")
                return best_arc, pipeline_result
            else:
                self.stats["phase3_reject"] += 1
                feedback = validation_result.get("feedback", "검증 실패")

                # REJECT 기록
                issues = validation_result.get("issues", [])
                if issues:
                    first_issue = issues[0]
                    self.negative_injector.record_rejection(
                        best_arc,
                        first_issue.get("issue", "알 수 없음"),
                        first_issue.get("category", "unknown")
                    )

                    # 이슈 출력
                    print(f"      🚨 [Phase 3] REJECT - 주요 이슈:")
                    for issue in issues[:3]:
                        sev = issue.get("severity", "?")
                        cat = issue.get("category", "?")
                        text = issue.get("issue", "?")
                        print(f"         [{sev}][{cat}] {text}")

                print(f"      ❌ [Phase 3] REJECT - 재시도 {retry + 1}/{max_internal_retries + 1}")

        # 모든 재시도 실패
        pipeline_result["final_verdict"] = "FAILED"
        print(f"      ❌ [ThreePhase] Arc {arc_no} 모든 재시도 실패 ({max_internal_retries + 1}회)")
        if feedback:
            print(f"         마지막 피드백: {feedback[:200]}...")
        return None, pipeline_result

    def _generate_prev_context(self, prev_arcs: List[Dict], preflight_result: Dict) -> str:
        """이전 Arc 컨텍스트 생성"""
        if not prev_arcs:
            return "서사 시작점 (첫 Arc)"

        lines = []
        last_arc = prev_arcs[-1]
        last_arc_no = last_arc.get("arc_no", "?")

        state = last_arc.get("state_constraints", {})
        arc_end = state.get("arc_end_state", {})
        joint = last_arc.get("joint_docs", {})
        shadow = last_arc.get("status_shadow", {})

        # 상태 추출 (arc_end_state 우선)
        final_energy = arc_end.get("internal_energy")
        if final_energy is None:
            loss_str = shadow.get("internal_energy_loss", "0%")
            try:
                import re
                loss = int(re.search(r'(\d+)', str(loss_str)).group(1))
                final_energy = max(0, 100 - loss)
            except:
                final_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK

        final_injuries = arc_end.get("injuries") or shadow.get("expected_injuries", "없음")
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

        relationships = preflight_result.get("relationship_map", {})
        if relationships:
            rel_summary = ", ".join([f"{k}: {v.get('current_state', '?')}" for k, v in list(relationships.items())[:5]])
            lines.append(f"주요 관계: {rel_summary}")

        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """통계 반환"""
        total = self.stats["total_attempts"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "pass_rate": f"{(self.stats['phase3_pass'] / total * 100):.1f}%" if total > 0 else "N/A"
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_stats()
        print("\n[ThreePhaseArcGenerator 통계]")
        print(f"  총 시도: {stats['total_attempts']}")
        print(f"  Phase 1 완료: {stats['phase1_complete']}")
        print(f"  Phase 2 완료: {stats['phase2_complete']}")
        print(f"  Phase 3 PASS: {stats['phase3_pass']}")
        print(f"  Phase 3 REJECT: {stats['phase3_reject']}")
        print(f"  최종 통과율: {stats.get('pass_rate', 'N/A')}")


def create_four_phase_generator(context, client, model_tier: str = "gemini-3-pro-preview"):
    """FourPhaseArcGenerator 생성 헬퍼 (호환성 유지)"""
    return FourPhaseArcGenerator(context, client, model_tier)
