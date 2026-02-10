"""
[V60.80] Three Phase Blueprint Generator
Stage 3 통합 파이프라인 - 단순화 + 효율화

철학:
- "Arc를 충실히 따르는, 연속성 있는 Blueprint"
- "디렉터주권주의" - 최종 결정권은 Director에게 있다

파이프라인:
1. Constraint: 제약 수집 (Arc 섹션 추출, 연속성, 정지선)
2. Generate: Ensemble 생성 (3개 후보 → 최적 선택)
3. Validate: 사전검사 (Python) + Director 최종 판정

[V60.80 리팩토링]
- 기존: 6개 검증 레이어, 10+ LLM 호출
- 변경: 3단계 파이프라인, Director 최종 판정
- 효과: 비용 50% 절감, 디렉터주권주의 유지
"""

import json
from typing import Dict, List, Any, Optional, Tuple

from .base_agent import BaseAgent
from .blueprint_constraint_compiler import BlueprintConstraintCompiler
from .blueprint_ensemble import BlueprintEnsembleGenerator
from .unified_blueprint_validator import UnifiedBlueprintValidator


class ThreePhaseBlueprintGenerator(BaseAgent):
    """
    [V60.80] Three Phase Blueprint Generator

    3단계 파이프라인: 제약수집 → 생성 → 검증 (Director 최종 판정)
    """

    def __init__(self, context, client, model_tier: str = "gemini-3-pro-preview"):
        super().__init__(context, client, model_tier)

        # 서브 모듈
        self.constraint_compiler = BlueprintConstraintCompiler()
        self.ensemble = BlueprintEnsembleGenerator(context, client, "gemini-3-pro-preview")
        self.validator = UnifiedBlueprintValidator(context, client, "gemini-2.5-flash")

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
        ep_num: int,
        arc_data: Dict,
        prev_blueprint: Optional[Dict] = None,
        prev_blueprints: Optional[List[Dict]] = None,
        max_retries: int = 2,  # [V60.80] 2 = 총 3번 시도 (0, 1, 2)
        external_feedback: str = "",
        director=None,  # [V60.80] Director 인스턴스 (최종 판정용)
        arc_idx: int = 0,  # Arc 인덱스
        entity_registry: Optional[Dict] = None,  # [V61] Entity 일관성 검증용
        protagonist_name: str = "주인공",  # [V61] 주인공 이름 (필수!)
        protagonist_config: Optional[Dict] = None,  # [V60.90] 주인공 설정 {world_origin, incarnation_type}
        state_tracker=None,  # [V60.96] StateTracker (죽은 NPC 검증용)
        db=None,  # [V61.5] DBManager (캐시 연속성 검사용)
        semantic_context: str = ""  # [V63.3] BlueprintMemory 시맨틱 검색 결과
    ) -> Tuple[Optional[Dict], Dict]:
        """
        3단계 Blueprint 생성 (ToT 방식: 3전략 × 3시도 = 최대 9회 생성)

        Args:
            ep_num: 에피소드 번호
            arc_data: 현재 Arc 데이터
            prev_blueprint: 직전 Blueprint
            prev_blueprints: 이전 Blueprint 리스트 (연속성 검증용)
            max_retries: 재시도 횟수 (기본 2 = 총 3번 시도, 3전략×3시도=9회 생성 기회)
            external_feedback: 외부 피드백 (Director REJECT 등)
            director: Director 에이전트 (최종 판정용) - 디렉터주권주의
            arc_idx: Arc 인덱스
            entity_registry: [V61] Entity 일관성 검증용
            protagonist_name: [V61] 주인공 이름
            protagonist_config: [V60.90] 주인공 설정
            state_tracker: [V60.96] StateTracker (죽은 NPC 검증용)

        Returns:
            (generated_blueprint, pipeline_result)

        [V60.80] 기회 구조:
        - 매 시도: 3개 전략으로 병렬 생성 (Ensemble)
        - 총 시도: 3번 (max_retries=2 → retry 0,1,2)
        - 최대 생성: 3×3 = 9개 Blueprint
        - Director 판정: 시도당 1회, 최대 3회
        """
        self.stats["total_attempts"] += 1

        # [V60.90] protagonist_config 추출 (context에서 직접 로드, 파라미터 우선)
        if not protagonist_config:
            try:
                master_bible = getattr(self.context, 'master_bible', {})
                if master_bible:
                    bible_root = master_bible.get('MasterBible', master_bible)
                    protagonist_config = bible_root.get('protagonist_config', {})
            except Exception:
                protagonist_config = {}

        pipeline_result = {
            "ep_num": ep_num,
            "arc_no": arc_data.get("arc_no", 0),
            "phases": {},
            "final_verdict": None,
            "retries": 0
        }

        # 피드백 초기화
        feedback = ""
        if semantic_context:
            feedback = f"[과거 유사 블루프린트 참조 (시맨틱 검색)]\n{semantic_context}\n"
        if external_feedback:
            feedback += f"[Director 외부 피드백 - 반드시 반영]\n{external_feedback}\n"
            print(f"      📢 [V60.80] 외부 피드백 주입됨 ({len(external_feedback)}자)")

        # 제약 블록 캐싱
        cached_constraint_block = None

        for retry in range(max_retries + 1):  # max_retries=2 → 3번 시도
            pipeline_result["retries"] = retry

            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: CONSTRAINT - 제약 수집
            # ═══════════════════════════════════════════════════════════════
            if cached_constraint_block and retry > 0:
                print(f"      📋 [Phase 1] 제약 캐시 사용")
                constraint_block = cached_constraint_block
            else:
                print(f"      📋 [Phase 1] 제약 수집 중...")

                constraint_block = self.constraint_compiler.compile(
                    arc_data=arc_data,
                    ep_num=ep_num,
                    prev_blueprint=prev_blueprint,
                    prev_blueprints=prev_blueprints
                )

                cached_constraint_block = constraint_block

            pipeline_result["phases"]["constraint"] = {
                "status": "complete" if retry == 0 else "cached",
                "must_focus_length": len(str(constraint_block.get("must_focus", {}).get("content", ""))),
                "has_stop_line": bool(constraint_block.get("stop_line", {}).get("content"))
            }
            self.stats["phase1_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GENERATE - Ensemble 생성
            # ═══════════════════════════════════════════════════════════════
            print(f"      🎲 [Phase 2] Ensemble 생성 중 (3개 후보)...")

            best_blueprint, all_candidates = self.ensemble.generate_ensemble(
                ep_num=ep_num,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                feedback=feedback,
                protagonist_name=protagonist_name,  # [V61] 주인공 이름 전달
                protagonist_config=protagonist_config,  # [V60.90] 주인공 설정 전달
                state_tracker=state_tracker  # [V60.95] 고밀도 HUD 전달
            )

            if not best_blueprint:
                print(f"      ❌ [Phase 2] Ensemble 생성 실패")
                pipeline_result["phases"]["generate"] = {"status": "failed"}
                feedback = "Blueprint 생성 실패. 다시 시도하세요."
                continue

            pipeline_result["phases"]["generate"] = {
                "status": "complete",
                "candidates_count": len(all_candidates),
                "qualified_candidates": len(all_candidates),  # [V60.85] 최소 기준 통과 후보 수
                "selection_by": "director"  # [V60.85] Director가 선택
            }
            self.stats["phase2_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: VALIDATE - Director 비교 선택 + 최종 판정
            # ═══════════════════════════════════════════════════════════════
            print(f"      🔍 [Phase 3] Director 비교 선택 + 판정 중...")

            # [V61.5] 캐시 기반 연속성 검사 (ep_num 바뀔 때만 캐시 갱신)
            continuity_feedback = ""
            if director and db and ep_num > 1:
                continuity_result = director.check_blueprint_continuity_with_cache(
                    new_blueprint=best_blueprint,
                    ep_num=ep_num,
                    db=db,
                    limit=10
                )
                if continuity_result.get("decision") == "REJECT":
                    # 연속성 REJECT면 피드백에 추가하고 재시도
                    continuity_feedback = continuity_result.get("feedback", "")
                    feedback += f"\n[연속성 오류]\n{continuity_feedback}"
                    print(f"      ⚠️ [V61.5] 연속성 검사 REJECT")
                    continue  # 다음 재시도로

            # [V60.85] 전체 후보를 Director에게 전달하여 비교 선택
            verdict, validation_result = self.validator.validate(
                blueprint=best_blueprint,  # 대표 후보 (폴백용)
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                director=director,  # Director 비교 선택 + 최종 판정
                working_ep=ep_num,
                arc_idx=arc_idx,
                entity_registry=entity_registry,  # [V61] Entity 일관성 검증
                state_tracker=state_tracker,  # [V60.96] 죽은 NPC 검증
                all_candidates=all_candidates  # [V60.85] 전체 후보 리스트
            )

            # [V60.85] Director가 선택한 Blueprint로 교체
            if validation_result.get("selected_blueprint"):
                best_blueprint = validation_result["selected_blueprint"]
                selected_idx = validation_result.get("selected_index", 0)
                print(f"      🎯 [V60.85] Director 선택: 후보 {selected_idx + 1}")

            pipeline_result["phases"]["validate"] = {
                "status": "complete",
                "verdict": verdict,
                "issues_count": len(validation_result.get("issues", [])),
                "confidence": validation_result.get("confidence", 0),
                "score": validation_result.get("score", 0),
                "phase": validation_result.get("phase", "unknown"),  # pre_validate/director/director_compare
                "selected_index": validation_result.get("selected_index", 0),  # [V60.85] Director 선택 인덱스
                "comparison_notes": validation_result.get("comparison_notes", "")  # [V60.85] 비교 근거
            }

            if verdict == "PASS":
                self.stats["phase3_pass"] += 1
                pipeline_result["final_verdict"] = "PASS"
                print(f"      ✅ [Phase 3] PASS - 제{ep_num}화 Blueprint 생성 완료")

                # 메타데이터 정리 (_ensemble_meta 유지)
                return best_blueprint, pipeline_result
            else:
                self.stats["phase3_reject"] += 1
                feedback = validation_result.get("feedback", "검증 실패")

                # 이슈 출력
                issues = validation_result.get("issues", [])
                if issues:
                    print(f"      🚨 [Phase 3] REJECT - 주요 이슈:")
                    for issue in issues[:3]:
                        sev = issue.get("severity", "?")
                        cat = issue.get("category", "?")
                        text = issue.get("issue", "?")
                        print(f"         [{sev}][{cat}] {text}")

                print(f"      ❌ [Phase 3] REJECT - 재시도 {retry + 1}/{max_retries + 1}")

        # 모든 재시도 실패
        pipeline_result["final_verdict"] = "FAILED"
        print(f"      ❌ [ThreePhase] 제{ep_num}화 모든 재시도 실패 ({max_retries + 1}회)")
        if feedback:
            print(f"         마지막 피드백: {feedback[:200]}...")
        return None, pipeline_result

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
        print("\n[ThreePhaseBlueprintGenerator 통계]")
        print(f"  총 시도: {stats['total_attempts']}")
        print(f"  Phase 1 완료: {stats['phase1_complete']}")
        print(f"  Phase 2 완료: {stats['phase2_complete']}")
        print(f"  Phase 3 PASS: {stats['phase3_pass']}")
        print(f"  Phase 3 REJECT: {stats['phase3_reject']}")
        print(f"  최종 통과율: {stats.get('pass_rate', 'N/A')}")


def create_three_phase_blueprint_generator(context, client, model_tier: str = "gemini-3-pro-preview"):
    """ThreePhaseBlueprintGenerator 생성 헬퍼"""
    return ThreePhaseBlueprintGenerator(context, client, model_tier)
