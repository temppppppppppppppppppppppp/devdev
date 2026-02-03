"""
[V60.12] Four Phase Arc Generator
4단계 Arc 생성 파이프라인 - 초기 통과율 극대화

파이프라인:
1. Preflight: 완벽한 제약 맵 구축
2. Generate: Ensemble 생성 (3개 후보)
3. Critique: 즉시 비평 + 자동 수정
4. Validate: 3-LLM 합의 검증

비용: ~$0.15-0.20/Arc (기존 대비 약 5x)
예상 초기 통과율: 90%+
"""

import json
from typing import Dict, List, Any, Optional, Tuple

from .base_agent import BaseAgent
from .preflight_checker import PreflightChecker
from .arc_ensemble import ArcEnsembleGenerator
from .arc_critic import ArcCritic
from .consensus_validator import ConsensusValidator
from .constraint_compiler import ConstraintCompiler
from .negative_example_injector import NegativeExampleInjector


class FourPhaseArcGenerator(BaseAgent):
    """
    [V60.12] Four Phase Arc Generator

    4단계 파이프라인으로 Arc 생성 품질 극대화
    """

    def __init__(self, context, client, model_tier: str = "gemini-3-pro-preview"):
        # [V60.24] Gemini 3로 변경
        super().__init__(context, client, model_tier)

        # [V60.53] 서브 모듈 모델 최적화 - Critic/Consensus는 Flash로 비용 절감
        self.preflight = PreflightChecker(context, client, "gemini-3-flash-preview")
        self.ensemble = ArcEnsembleGenerator(context, client, "gemini-3-pro-preview")
        self.critic = ArcCritic(context, client, "gemini-2.5-flash")
        self.consensus = ConsensusValidator(context, client, "gemini-2.5-flash")
        self.compiler = ConstraintCompiler()
        self.negative_injector = NegativeExampleInjector("wuxia")

        # 통계
        self.stats = {
            "total_attempts": 0,
            "phase1_complete": 0,
            "phase2_complete": 0,
            "phase3_complete": 0,
            "phase4_pass": 0,
            "phase4_reject": 0
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
        protagonist_name: str = "주인공"  # [V60.18] 주인공 이름 (필수!)
    ) -> Tuple[Optional[Dict], Dict]:
        """
        4단계 Arc 생성

        Args:
            arc_no: Arc 번호
            ep_start: 시작 화수
            vol_strategy: Volume 전략
            curr_block: 현재 블록 DNA
            prev_arcs: 이전 Arc 리스트
            assets: AssetLibrary
            max_internal_retries: 내부 재시도 횟수

        Returns:
            (generated_arc, pipeline_result)
        """
        self.stats["total_attempts"] += 1
        ep_end = ep_start + 4

        pipeline_result = {
            "arc_no": arc_no,
            "phases": {},
            "final_verdict": None,
            "retries": 0
        }

        # [V60.17] Preflight 캐싱 - 재시도 시 재사용으로 속도 향상
        cached_preflight = None
        cached_constraint_block = None

        for retry in range(max_internal_retries + 1):
            pipeline_result["retries"] = retry

            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: PREFLIGHT - 완벽한 제약 맵 구축 (캐싱 적용)
            # ═══════════════════════════════════════════════════════════════
            if cached_constraint_block and retry > 0:
                # [V60.17] 재시도 시 캐시 사용 (Preflight 스킵)
                print(f"      📋 [Phase 1] Preflight 캐시 사용 (스킵)")
                full_constraint_block = cached_constraint_block
                preflight_result = cached_preflight
            else:
                print(f"      📋 [Phase 1] Preflight 분석 중...")

                preflight_result = self.preflight.analyze(prev_arcs)
                preflight_injection = self.preflight.generate_analyst_injection(preflight_result)

                # Constraint Compiler 추가
                compiled_constraints = self.compiler.compile(prev_arcs)

                # Negative Examples 추가
                negative_examples = self.negative_injector.generate_injection()
                self_check = self.negative_injector.generate_self_check_prompt()

                # 통합 제약 블록
                full_constraint_block = "\n".join([
                    preflight_injection,
                    compiled_constraints,
                    negative_examples,
                    self_check
                ])

                # [V60.17] 캐시 저장
                cached_preflight = preflight_result
                cached_constraint_block = full_constraint_block

            pipeline_result["phases"]["preflight"] = {
                "status": "complete" if retry == 0 else "cached",
                "prohibitions_count": len(preflight_result.get("absolute_prohibitions", {}).get("items_cannot_acquire", [])),
                "constraint_block_length": len(full_constraint_block)
            }
            self.stats["phase1_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GENERATE - Ensemble 생성
            # ═══════════════════════════════════════════════════════════════
            print(f"      🎲 [Phase 2] Ensemble 생성 중 (3개 후보)...")

            # 이전 Arc 컨텍스트 생성
            prev_arc_context = self._generate_prev_context(prev_arcs, preflight_result)

            best_arc, all_candidates = self.ensemble.generate_ensemble(
                arc_no=arc_no,
                ep_start=ep_start,
                vol_strategy=vol_strategy,
                curr_block=curr_block,
                prev_arc_context=prev_arc_context,
                constraint_block=full_constraint_block,
                assets=assets,
                feedback="" if retry == 0 else pipeline_result.get("last_feedback", ""),
                protagonist_name=protagonist_name  # [V60.18] 주인공 이름 전달
            )

            if not best_arc:
                print(f"      ❌ [Phase 2] Ensemble 생성 실패")
                pipeline_result["phases"]["generate"] = {"status": "failed"}
                continue

            pipeline_result["phases"]["generate"] = {
                "status": "complete",
                "candidates_count": len(all_candidates),
                "selected_strategy": best_arc.get("_strategy", "unknown")
            }
            self.stats["phase2_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2.5: QUICK DUPLICATE CHECK (V60.28) - API 비용 절감
            # ═══════════════════════════════════════════════════════════════
            duplicate_issues = self._quick_duplicate_check(best_arc, prev_arcs, preflight_result)
            if duplicate_issues:
                print(f"      ⚠️ [Phase 2.5] 중복 아이템 발견 - Ensemble 재시도")
                for issue in duplicate_issues:
                    print(f"         - {issue}")
                pipeline_result["last_feedback"] = f"중복 획득 금지: {', '.join(duplicate_issues)}"
                continue  # Phase 3/4 스킵하고 재시도

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: CRITIQUE - 즉시 비평 + 자동 수정
            # ═══════════════════════════════════════════════════════════════
            print(f"      🔍 [Phase 3] Critic 비평 중...")

            critique_result, fixed_arc = self.critic.critique(
                generated_arc=best_arc,
                prev_arcs=prev_arcs,
                constraints=full_constraint_block
            )

            critic_verdict = critique_result.get("verdict", "NEEDS_REVISION")

            pipeline_result["phases"]["critique"] = {
                "status": "complete",
                "verdict": critic_verdict,
                "score": critique_result.get("total_score", 0),
                "critical_issues": len(critique_result.get("critical_issues", [])),
                "auto_fixes_applied": bool(critique_result.get("auto_fixes"))
            }
            self.stats["phase3_complete"] += 1

            # Critic이 REJECT하면 재시도
            if self.critic.should_regenerate(critique_result):
                print(f"      ⚠️ [Phase 3] Critic REJECT - 재생성 필요")
                pipeline_result["last_feedback"] = self.critic.get_revision_feedback(critique_result)
                # REJECT 기록
                self.negative_injector.record_rejection(
                    best_arc,
                    critique_result.get("critical_issues", [{}])[0].get("issue", "알 수 없음"),
                    critique_result.get("critical_issues", [{}])[0].get("category", "unknown")
                )
                continue

            # 자동 수정 적용
            if self.critic.should_apply_fixes(critique_result):
                print(f"      🔧 [Phase 3] 자동 수정 적용")
                best_arc = fixed_arc

            # ═══════════════════════════════════════════════════════════════
            # PHASE 4: VALIDATE - 3-LLM 합의 검증
            # ═══════════════════════════════════════════════════════════════
            print(f"      🗳️ [Phase 4] Consensus 검증 중 (3 LLM)...")

            final_verdict, consensus_result = self.consensus.validate_with_consensus(
                arc=best_arc,
                prev_arcs=prev_arcs,
                constraints=full_constraint_block
            )

            pipeline_result["phases"]["validate"] = {
                "status": "complete",
                "verdict": final_verdict,
                "vote_pass": consensus_result.get("vote_summary", {}).get("pass", 0),
                "vote_reject": consensus_result.get("vote_summary", {}).get("reject", 0),
                "critical_issues": len(consensus_result.get("critical_issues", [])),
                "critical_issues_detail": consensus_result.get("critical_issues", [])[:5],  # 상세 이슈 저장
                "all_issues": consensus_result.get("all_issues", [])[:10]  # 모든 이슈 저장
            }

            if final_verdict == "PASS":
                self.stats["phase4_pass"] += 1
                pipeline_result["final_verdict"] = "PASS"
                print(f"      ✅ [Phase 4] PASS - Arc {arc_no} 생성 완료")
                return best_arc, pipeline_result
            else:
                self.stats["phase4_reject"] += 1
                pipeline_result["last_feedback"] = self.consensus.get_rejection_feedback(consensus_result)
                # REJECT 기록
                critical = consensus_result.get("critical_issues", [])

                # [V60.33] CRITICAL 이슈 상세 출력
                if critical:
                    print(f"      🚨 [Phase 4] CRITICAL 이슈 상세:")
                    for i, issue in enumerate(critical[:3], 1):  # 최대 3개만 출력
                        category = issue.get("category", "unknown")
                        issue_text = issue.get("issue", "알 수 없음")
                        evidence = issue.get("evidence", "")[:80]  # 80자 제한
                        print(f"         {i}. [{category}] {issue_text}")
                        if evidence:
                            print(f"            └─ 근거: {evidence}...")

                    self.negative_injector.record_rejection(
                        best_arc,
                        critical[0].get("issue", "합의 실패"),
                        critical[0].get("category", "consensus")
                    )
                else:
                    # CRITICAL 아닌 경우 일반 이슈 출력
                    all_issues = consensus_result.get("all_issues", [])
                    if all_issues:
                        print(f"      ⚠️ [Phase 4] 주요 이슈:")
                        for issue in all_issues[:2]:
                            print(f"         - [{issue.get('severity', '?')}] {issue.get('issue', '?')}")

                print(f"      ❌ [Phase 4] REJECT - 재시도 {retry + 1}/{max_internal_retries + 1}")

        # 모든 재시도 실패
        pipeline_result["final_verdict"] = "FAILED"
        print(f"      ❌ [FourPhase] 모든 재시도 실패")
        return None, pipeline_result

    def _quick_duplicate_check(
        self,
        arc: Dict,
        prev_arcs: List[Dict],
        preflight_result: Dict
    ) -> List[str]:
        """
        [V60.28] 빠른 중복 아이템 체크 (Python, LLM 비용 0)

        Returns:
            중복된 아이템 목록 (빈 리스트면 OK)
        """
        if not prev_arcs:
            return []  # 첫 Arc는 중복 불가

        # 1. 이전 Arc들에서 획득한 모든 아이템 수집
        prev_items = set()
        for prev_arc in prev_arcs:
            acquired = prev_arc.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(acquired, list):
                prev_items.update(item.strip() for item in acquired if item)

            inventory = prev_arc.get("joint_docs", {}).get("physical_inventory", [])
            if isinstance(inventory, list):
                prev_items.update(item.strip() for item in inventory if item)
            elif isinstance(inventory, str):
                prev_items.update(item.strip() for item in inventory.split(",") if item.strip())

        # Preflight에서 추출한 금지 아이템도 추가
        forbidden = preflight_result.get("absolute_prohibitions", {}).get("items_cannot_acquire", [])
        for item in forbidden:
            item_name = item.get("item", item) if isinstance(item, dict) else item
            if item_name:
                prev_items.add(item_name.strip())

        # 2. 현재 Arc에서 획득하려는 아이템 추출
        current_acquired = arc.get("state_constraints", {}).get("items_acquired", [])
        if not isinstance(current_acquired, list):
            current_acquired = []

        # 3. 중복 체크
        duplicates = []
        for item in current_acquired:
            item = item.strip() if isinstance(item, str) else str(item)
            if not item:
                continue

            # 정확 매칭
            if item in prev_items:
                duplicates.append(f"'{item}' (정확 매칭)")
                continue

            # 부분 매칭 (긴 아이템명에 포함되는 경우)
            for prev_item in prev_items:
                if len(item) >= 3 and len(prev_item) >= 3:
                    if item in prev_item or prev_item in item:
                        # 길이 비율 체크 (V60.20 로직 적용)
                        ratio = len(item) / len(prev_item) if len(prev_item) > 0 else 0
                        if 0.5 <= ratio <= 2.0:  # 2배 이내 차이만 중복으로 인정
                            duplicates.append(f"'{item}' (유사: '{prev_item}')")
                            break

        return duplicates

    def _generate_prev_context(self, prev_arcs: List[Dict], preflight_result: Dict) -> str:
        """이전 Arc 컨텍스트 생성 - arc_end_state 직접 추출"""
        if not prev_arcs:
            return "서사 시작점 (첫 Arc)"

        lines = []

        # [V60.13 FIX] 마지막 Arc의 arc_end_state에서 직접 추출 (가장 정확)
        last_arc = prev_arcs[-1]
        last_arc_no = last_arc.get("arc_no", "?")
        state_constraints = last_arc.get("state_constraints", {})
        arc_end = state_constraints.get("arc_end_state", {})
        joint = last_arc.get("joint_docs", {})
        shadow = last_arc.get("status_shadow", {})

        # arc_end_state 우선, 없으면 joint_docs/shadow에서 폴백
        final_energy = arc_end.get("internal_energy")
        if final_energy is None:
            loss_str = shadow.get("internal_energy_loss", "0%")
            try:
                loss = int(str(loss_str).replace("%", "").strip())
                final_energy = max(0, 100 - loss)
            except:
                final_energy = 100

        final_injuries = arc_end.get("injuries") or shadow.get("expected_injuries", "없음")
        final_location = arc_end.get("location") or joint.get("final_location", "알 수 없음")
        final_equipment = arc_end.get("equipment") or joint.get("physical_inventory", [])
        if isinstance(final_equipment, str):
            final_equipment = [i.strip() for i in final_equipment.split(",") if i.strip()]

        # 강조된 필수 계승 블록
        lines.append("=" * 50)
        lines.append(f"🔴 [Arc {last_arc_no} 종료 상태 → 다음 Arc 필수 시작 조건]")
        lines.append("=" * 50)
        lines.append(f"✅ 내공: {final_energy}% ← 이 수치로 시작해야 함")
        lines.append(f"✅ 부상: {final_injuries} ← 이 상태로 시작해야 함")
        lines.append(f"✅ 위치: {final_location}")
        lines.append(f"✅ 소지품: {final_equipment}")
        lines.append("=" * 50)
        lines.append("")

        # 보조 정보 (preflight_result에서)
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
            "phase4_pass_rate": f"{(self.stats['phase4_pass'] / total * 100):.1f}%" if total > 0 else "N/A"
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_stats()
        print("\n[FourPhaseArcGenerator 통계]")
        print(f"  총 시도: {stats['total_attempts']}")
        print(f"  Phase 1 완료: {stats['phase1_complete']}")
        print(f"  Phase 2 완료: {stats['phase2_complete']}")
        print(f"  Phase 3 완료: {stats['phase3_complete']}")
        print(f"  Phase 4 PASS: {stats['phase4_pass']}")
        print(f"  Phase 4 REJECT: {stats['phase4_reject']}")
        print(f"  최종 통과율: {stats.get('phase4_pass_rate', 'N/A')}")


def create_four_phase_generator(context, client, model_tier: str = "gemini-3-pro-preview"):
    """[V60.24] FourPhaseArcGenerator 생성 헬퍼 - Gemini 3 사용"""
    return FourPhaseArcGenerator(context, client, model_tier)
