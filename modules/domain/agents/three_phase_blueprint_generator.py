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

import logging

from modules.models.blueprint import validate_blueprint

from .base_agent import BaseAgent, _get_sub_component_models
from .blueprint_constraint_compiler import BlueprintConstraintCompiler
from .blueprint_ensemble import BlueprintEnsembleGenerator
from .unified_blueprint_validator import UnifiedBlueprintValidator


class ThreePhaseBlueprintGenerator(BaseAgent):
    """
    [V60.80] Three Phase Blueprint Generator

    3단계 파이프라인: 제약수집 → 생성 → 검증 (Director 최종 판정)
    """

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)

        # 서브 모듈
        self.constraint_compiler = BlueprintConstraintCompiler()
        sub_models = _get_sub_component_models("three_phase_blueprint_generator")
        self.ensemble = BlueprintEnsembleGenerator(context, client, sub_models.get("ensemble", "gemini-3-pro-preview"))
        self.validator = UnifiedBlueprintValidator(context, client, sub_models.get("validator", "gemini-2.5-flash"))

        # 통계
        self.stats = {
            "total_attempts": 0,
            "phase1_complete": 0,
            "phase2_complete": 0,
            "phase3_pass": 0,
            "phase3_reject": 0,
        }

    def generate(
        self,
        ep_num: int,
        arc_data: dict,
        prev_blueprint: dict | None = None,
        prev_blueprints: list[dict] | None = None,
        max_retries: int = 2,  # [V60.80] 2 = 총 3번 시도 (0, 1, 2)
        external_feedback: str = "",
        director=None,  # [V60.80] Director 인스턴스 (최종 판정용)
        arc_idx: int = 0,  # Arc 인덱스
        entity_registry: dict | None = None,  # [V61] Entity 일관성 검증용
        protagonist_name: str = "주인공",  # [V61] 주인공 이름 (필수!)
        protagonist_config: dict | None = None,  # [V60.90] 주인공 설정 {world_origin, incarnation_type}
        state_tracker=None,  # [V60.96] StateTracker (죽은 NPC 검증용)
        db=None,  # [V61.5] DBManager (캐시 연속성 검사용)
        semantic_context: str = "",  # [V63.3] 벡터 시맨틱 검색 결과
        prev_manuscripts_text: str = "",  # [V67] 이전 원고 전문 (모순 방지)
    ) -> tuple[dict | None, dict]:
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
                master_bible = getattr(self.context, "master_bible", {})
                if master_bible:
                    bible_root = master_bible.get("MasterBible", master_bible)
                    protagonist_config = bible_root.get("protagonist_config", {})
            except Exception:
                protagonist_config = {}

        pipeline_result = {
            "ep_num": ep_num,
            "arc_no": arc_data.get("arc_no", 0),
            "phases": {},
            "final_verdict": None,
            "retries": 0,
        }

        # 피드백 초기화
        feedback = ""
        if semantic_context:
            feedback = f"[과거 유사 블루프린트 참조 (시맨틱 검색)]\n{semantic_context}\n"
        if external_feedback:
            feedback += f"[Director 외부 피드백 - 반드시 반영]\n{external_feedback}\n"
            logging.info(f"📢 [V60.80] 외부 피드백 주입됨 ({len(external_feedback)}자)")

        # 제약 블록 캐싱
        cached_constraint_block = None

        # [Patch Mode] 이전 REJECT 결과 추적
        _previous_best = None
        _prev_reject_score = 0
        _prev_reject_feedback = ""

        for retry in range(max_retries + 1):  # max_retries=2 → 3번 시도
            pipeline_result["retries"] = retry

            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: CONSTRAINT - 제약 수집
            # ═══════════════════════════════════════════════════════════════
            if cached_constraint_block and retry > 0:
                logging.info("📋 [Phase 1] 제약 캐시 사용")
                constraint_block = cached_constraint_block
            else:
                logging.info("📋 [Phase 1] 제약 수집 중...")

                constraint_block = self.constraint_compiler.compile(
                    arc_data=arc_data, ep_num=ep_num, prev_blueprint=prev_blueprint, prev_blueprints=prev_blueprints
                )

                cached_constraint_block = constraint_block

            pipeline_result["phases"]["constraint"] = {
                "status": "complete" if retry == 0 else "cached",
                "must_focus_length": len(str(constraint_block.get("must_focus", {}).get("content", ""))),
                "has_stop_line": bool(constraint_block.get("stop_line", {}).get("content")),
            }
            self.stats["phase1_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GENERATE - Ensemble 생성
            # ═══════════════════════════════════════════════════════════════
            logging.info("🎲 [Phase 2] Ensemble 생성 중 (3개 후보)...")

            # [Patch Mode] 점수 기반 분기: 패치 모드 vs 전면 재생성
            from modules.core.constants import PatchModeThresholds

            _use_patch = _previous_best is not None and _prev_reject_score >= PatchModeThresholds.REWRITE

            if _use_patch:
                logging.info(f"[Patch Mode] Blueprint 패치 모드 진입 (score={_prev_reject_score}, retry={retry})")
                best_blueprint, all_candidates = self._patch_blueprint_with_feedback(
                    original_blueprint=_previous_best,
                    director_feedback=_prev_reject_feedback,
                    attempt_number=retry + 1,
                    ep_num=ep_num,
                    arc_data=arc_data,
                    constraint_block=constraint_block,
                    prev_blueprint=prev_blueprint,
                    protagonist_name=protagonist_name,
                    protagonist_config=protagonist_config,
                    state_tracker=state_tracker,
                    prev_blueprints=prev_blueprints,
                    prev_manuscripts_text=prev_manuscripts_text,
                )
                if not best_blueprint:
                    logging.info("[Patch Mode] Blueprint 패치 실패 → 전면 재생성 폴백")
                    best_blueprint, all_candidates = self.ensemble.generate_ensemble(
                        ep_num=ep_num,
                        arc_data=arc_data,
                        constraint_block=constraint_block,
                        prev_blueprint=prev_blueprint,
                        feedback=feedback,
                        protagonist_name=protagonist_name,
                        protagonist_config=protagonist_config,
                        state_tracker=state_tracker,
                        prev_blueprints=prev_blueprints,
                        prev_manuscripts_text=prev_manuscripts_text,
                    )
            else:
                best_blueprint, all_candidates = self.ensemble.generate_ensemble(
                    ep_num=ep_num,
                    arc_data=arc_data,
                    constraint_block=constraint_block,
                    prev_blueprint=prev_blueprint,
                    feedback=feedback,
                    protagonist_name=protagonist_name,
                    protagonist_config=protagonist_config,
                    state_tracker=state_tracker,
                    prev_blueprints=prev_blueprints,
                    prev_manuscripts_text=prev_manuscripts_text,
                )

            if not best_blueprint:
                logging.warning("❌ [Phase 2] Ensemble 생성 실패")
                pipeline_result["phases"]["generate"] = {"status": "failed"}
                feedback = "Blueprint 생성 실패. 다시 시도하세요."
                continue

            pipeline_result["phases"]["generate"] = {
                "status": "complete",
                "candidates_count": len(all_candidates),
                "qualified_candidates": len(all_candidates),  # [V60.85] 최소 기준 통과 후보 수
                "selection_by": "director",  # [V60.85] Director가 선택
            }
            self.stats["phase2_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: VALIDATE - Director 비교 선택 + 최종 판정
            # ═══════════════════════════════════════════════════════════════
            logging.info("🔍 [Phase 3] Director 비교 선택 + 판정 중...")

            # [V61.5] 캐시 기반 연속성 검사 (ep_num 바뀔 때만 캐시 갱신)
            continuity_feedback = ""
            if director and db and ep_num > 1:
                continuity_result = director.check_blueprint_continuity_with_cache(
                    new_blueprint=best_blueprint, ep_num=ep_num, db=db, limit=10
                )
                if continuity_result.get("decision") == "REJECT":
                    # 연속성 REJECT면 피드백에 추가하고 재시도
                    continuity_feedback = continuity_result.get("feedback", "")
                    feedback += f"\n[연속성 오류]\n{continuity_feedback}"
                    logging.warning("⚠️ [V61.5] 연속성 검사 REJECT")
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
                all_candidates=all_candidates,  # [V60.85] 전체 후보 리스트
            )

            # [V60.85] Director가 선택한 Blueprint로 교체
            if validation_result.get("selected_blueprint"):
                best_blueprint = validation_result["selected_blueprint"]
                selected_idx = validation_result.get("selected_index", 0)
                logging.info(f"🎯 [V60.85] Director 선택: 후보 {selected_idx + 1}")

            pipeline_result["phases"]["validate"] = {
                "status": "complete",
                "verdict": verdict,
                "issues_count": len(validation_result.get("issues", [])),
                "confidence": validation_result.get("confidence", 0),
                "score": validation_result.get("score", 0),
                "phase": validation_result.get("phase", "unknown"),  # pre_validate/director/director_compare
                "selected_index": validation_result.get("selected_index", 0),  # [V60.85] Director 선택 인덱스
                "comparison_notes": validation_result.get("comparison_notes", ""),  # [V60.85] 비교 근거
            }

            if verdict == "PASS":
                self.stats["phase3_pass"] += 1
                pipeline_result["final_verdict"] = "PASS"
                logging.info(f"✅ [Phase 3] PASS - 제{ep_num}화 Blueprint 생성 완료")

                # [Step2] Pydantic ingress+egress
                best_blueprint = validate_blueprint(best_blueprint)
                return best_blueprint, pipeline_result
            else:
                self.stats["phase3_reject"] += 1
                feedback = validation_result.get("feedback", "검증 실패")

                # [Patch Mode] REJECT 결과 추적
                _prev_reject_score = validation_result.get("score", 0)
                if _prev_reject_score >= PatchModeThresholds.REWRITE and best_blueprint:
                    _previous_best = best_blueprint
                    _prev_reject_feedback = feedback
                else:
                    _previous_best = None

                # 이슈 출력
                issues = validation_result.get("issues", [])
                if issues:
                    logging.warning("🚨 [Phase 3] REJECT - 주요 이슈:")
                    for issue in issues[:3]:
                        sev = issue.get("severity", "?")
                        cat = issue.get("category", "?")
                        text = issue.get("issue", "?")
                        logging.info(f"[{sev}][{cat}] {text}")

                logging.warning(f"❌ [Phase 3] REJECT - 재시도 {retry + 1}/{max_retries + 1}")

        # 모든 재시도 실패
        pipeline_result["final_verdict"] = "FAILED"
        logging.warning(f"❌ [ThreePhase] 제{ep_num}화 모든 재시도 실패 ({max_retries + 1}회)")
        if feedback:
            logging.info(f"마지막 피드백: {feedback[:200]}...")
        return None, pipeline_result

    # =========================================================================
    # [Patch Mode] Blueprint 원본 보존 + Director 피드백 지적사항만 수정
    # =========================================================================

    def _patch_blueprint_with_feedback(
        self,
        *,
        original_blueprint: dict,
        director_feedback: str,
        attempt_number: int,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None = None,
        protagonist_name: str = "주인공",
        protagonist_config: dict | None = None,
        state_tracker=None,
        prev_blueprints: list[dict] | None = None,
        prev_manuscripts_text: str = "",
    ) -> tuple[dict | None, list]:
        """[Patch Mode] 원본 Blueprint를 보존하며 Director 피드백 지적사항만 수정.

        패치 전용 프롬프트(BLUEPRINT_PATCH_MODE_PROMPT)를 로드하여 원본 Blueprint +
        Director 피드백을 enhanced_feedback으로 조립한 뒤, ensemble.generate_ensemble()을
        호출하여 후보를 생성한다.

        실패 시 (None, []) 반환 → 호출측에서 full regenerate 폴백.
        """
        import json

        # 1) YAML 프롬프트 로드
        try:
            from modules.core.prompt_loader import PromptLoader

            _patch_template = PromptLoader().load("blueprint_generator", "BLUEPRINT_PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[SilentPass:BlueprintGen] BLUEPRINT_PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            _patch_template = None

        # 2) 원본 Blueprint 직렬화
        _original_text = json.dumps(original_blueprint, ensure_ascii=False, indent=2)[:30000]

        # 3) 패치 프롬프트 포맷
        if _patch_template:
            _patch_section = _patch_template.format(
                feedback_text=director_feedback,
                original_blueprint=_original_text,
            )
        else:
            _patch_section = (
                f"[패치 모드: Blueprint 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## 원본 Blueprint\n{_original_text}\n\n"
                f"전면 재설계하지 마세요. 지적된 부분만 고치세요."
            )

        enhanced_feedback = (
            f"[🔧 {attempt_number}차 수정 - 패치 모드: Blueprint 원본 보존 + 지적사항만 수정]\n\n"
            f"{_patch_section}\n\n"
            f"⚠️ 원본 Blueprint의 씬 배분, 감정 곡선, 핵심 장면을 보존하면서 피드백 지적사항만 수정하세요.\n"
            f"⚠️ 수정하지 않는 부분은 원본을 그대로 유지하세요."
        )

        # 4) Ensemble 생성 (패치 피드백 주입)
        try:
            best_blueprint, all_candidates = self.ensemble.generate_ensemble(
                ep_num=ep_num,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                feedback=enhanced_feedback,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                state_tracker=state_tracker,
                prev_blueprints=prev_blueprints,
                prev_manuscripts_text=prev_manuscripts_text,
            )
        except Exception as e:
            logging.warning(f"[Patch Mode] Blueprint ensemble 생성 실패: {e!s:.200}")
            return None, []

        if not best_blueprint:
            logging.warning("[Patch Mode] Blueprint ensemble 후보 없음 → 폴백 필요")
            return None, []

        logging.info(f"✅ [Patch Mode] Blueprint 제{ep_num}화 패치 후보 생성 완료")
        return best_blueprint, all_candidates

    def get_stats(self) -> dict:
        """통계 반환"""
        total = self.stats["total_attempts"]
        if total == 0:
            return self.stats

        return {**self.stats, "pass_rate": f"{(self.stats['phase3_pass'] / total * 100):.1f}%" if total > 0 else "N/A"}

    def print_stats(self) -> None:
        """통계 출력"""
        stats = self.get_stats()
        logging.info("\n[ThreePhaseBlueprintGenerator 통계]")
        logging.info(f"총 시도: {stats['total_attempts']}")
        logging.info(f"Phase 1 완료: {stats['phase1_complete']}")
        logging.info(f"Phase 2 완료: {stats['phase2_complete']}")
        logging.info(f"Phase 3 PASS: {stats['phase3_pass']}")
        logging.warning(f"Phase 3 REJECT: {stats['phase3_reject']}")
        logging.info(f"최종 통과율: {stats.get('pass_rate', 'N/A')}")


def create_three_phase_blueprint_generator(context, client, model_tier: str = "gemini-3-pro-preview"):
    """ThreePhaseBlueprintGenerator 생성 헬퍼"""
    return ThreePhaseBlueprintGenerator(context, client, model_tier)
