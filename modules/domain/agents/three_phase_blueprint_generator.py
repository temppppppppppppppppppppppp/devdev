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
import logging

from modules.models.blueprint import validate_blueprint
from modules.validation.threshold_helper import _threshold

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
        adversarial_self_play=None,
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
        _prev_reject_strategy = ""
        _prev_score_breakdown = {}
        _prev_selection_reason = ""
        _prev_validation_warnings = []

        def _build_strategy_feedback() -> str:
            _parts = []
            if _prev_selection_reason:
                _parts.append(f"[이전 선택/거절 사유]\n{_prev_selection_reason}")
            if isinstance(_prev_score_breakdown, dict) and _prev_score_breakdown:
                _sb = ", ".join(f"{k}={v}" for k, v in _prev_score_breakdown.items() if isinstance(v, int | float))
                if _sb:
                    _parts.append(f"[이전 점수 분해]\n{_sb}")
            if isinstance(_prev_validation_warnings, list) and _prev_validation_warnings:
                _parts.append(
                    "[이전 검증 경고]\n"
                    + "\n".join(f"- {w}" for w in _prev_validation_warnings[:10] if isinstance(w, str))
                )
            return "\n\n".join(_parts)

        for retry in range(max_retries + 1):  # max_retries=2 → 3번 시도
            pipeline_result["retries"] = retry
            _attempt_feedback = feedback
            _strategy_feedback = _build_strategy_feedback()
            if _strategy_feedback:
                _attempt_feedback = (
                    f"{_attempt_feedback}\n\n{_strategy_feedback}" if _attempt_feedback else _strategy_feedback
                )

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
                    rejected_strategy=_prev_reject_strategy,
                    selection_reason=_prev_selection_reason,
                    score_breakdown=_prev_score_breakdown,
                    validation_warnings=_prev_validation_warnings,
                )
                if not best_blueprint:
                    logging.info("[Patch Mode] Blueprint 패치 실패 → 전면 재생성 폴백")
                    best_blueprint, all_candidates = self.ensemble.generate_ensemble(
                        ep_num=ep_num,
                        arc_data=arc_data,
                        constraint_block=constraint_block,
                        prev_blueprint=prev_blueprint,
                        feedback=_attempt_feedback,
                        strategy_specific_feedback=_strategy_feedback,
                        rejected_strategy=_prev_reject_strategy,
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
                    feedback=_attempt_feedback,
                    strategy_specific_feedback=_strategy_feedback,
                    rejected_strategy=_prev_reject_strategy,
                    protagonist_name=protagonist_name,
                    protagonist_config=protagonist_config,
                    state_tracker=state_tracker,
                    prev_blueprints=prev_blueprints,
                    prev_manuscripts_text=prev_manuscripts_text,
                )

            if retry >= 2 and adversarial_self_play and best_blueprint:
                try:
                    _asp_ctx = {
                        "arc_data": arc_data,
                        "constraint_block": constraint_block,
                        "director_feedback": _attempt_feedback,
                    }
                    _asp_input = json.dumps(best_blueprint, ensure_ascii=False)
                    _asp_result = adversarial_self_play.generate_with_adversary(
                        initial_content=_asp_input,
                        content_type="blueprint",
                        context=_asp_ctx,
                    )
                    _asp_output = getattr(_asp_result, "final_output", "") if _asp_result else ""
                    if _asp_output:
                        _asp_bp = self._extract_json_robust(_asp_output)
                        if not isinstance(_asp_bp, dict) or not _asp_bp:
                            try:
                                _asp_bp = json.loads(_asp_output)
                            except (json.JSONDecodeError, ValueError):
                                _asp_bp = {}
                        if (
                            isinstance(_asp_bp, dict)
                            and _asp_bp.get("scene_breakdown")
                            and _asp_bp.get("integrated_scenario")
                        ):
                            _asp_bp["_ensemble_meta"] = {
                                "strategy": "asp_correction",
                                "scene_count": len(_asp_bp.get("scene_breakdown", {}))
                                if isinstance(_asp_bp.get("scene_breakdown"), dict)
                                else 0,
                                "length": len(_asp_bp.get("integrated_scenario", "") or ""),
                            }
                            if not isinstance(all_candidates, list):
                                all_candidates = []
                            all_candidates.append(_asp_bp)
                            pipeline_result["asp_used"] = True
                            logging.info(f"✅ [ASP] Stage3 후보 추가 (retry={retry})")
                except Exception as e:
                    logging.warning(f"[SilentPass:Stage3:ASP] {e!s:.120}")

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

            _selected_meta = best_blueprint.get("_ensemble_meta", {}) if isinstance(best_blueprint, dict) else {}
            _selected_strategy = _selected_meta.get("strategy", "")
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

            _quality_gate_score = _threshold("scoring.quality_gate_score", 90)
            _score_raw = validation_result.get("score", 0)
            try:
                _score = int(_score_raw)
            except (ValueError, TypeError):
                _score = 0
            pipeline_result["phases"]["generate"]["selected_strategy"] = _selected_strategy or "unknown"
            pipeline_result["phases"]["generate"]["selected_score"] = _score

            if verdict == "PASS" and _score < _quality_gate_score:
                logging.warning(f"[QualityGate] Stage3 PASS이나 score={_score} < {_quality_gate_score} → REJECT 전환")
                verdict = "REJECT"
                feedback = (feedback or "") + f"\n[Quality Gate] score {_score}점으로 {_quality_gate_score}점 미달."

            if verdict == "PASS":
                self.stats["phase3_pass"] += 1
                pipeline_result["final_verdict"] = "PASS"
                logging.info(f"✅ [Phase 3] PASS - 제{ep_num}화 Blueprint 생성 완료")

                # [Step2] Pydantic ingress+egress
                best_blueprint = validate_blueprint(best_blueprint)
                return best_blueprint, pipeline_result

            self.stats["phase3_reject"] += 1
            feedback = validation_result.get("feedback", "검증 실패")

            _prev_reject_score = _score
            _prev_reject_feedback = feedback
            _prev_reject_strategy = _selected_strategy or ""
            _prev_score_breakdown = (
                validation_result.get("score_breakdown", {})
                if isinstance(validation_result.get("score_breakdown", {}), dict)
                else {}
            )
            _prev_selection_reason = (
                validation_result.get("summary")
                or validation_result.get("comparison_notes", "")
                or str(validation_result.get("feedback", ""))
            )
            _issues = validation_result.get("issues", [])
            _prev_validation_warnings = []
            if isinstance(_issues, list):
                for _iss in _issues[:10]:
                    if isinstance(_iss, dict):
                        _cat = _iss.get("category", "issue")
                        _msg = _iss.get("issue", "")
                        _prev_validation_warnings.append(f"{_cat}: {_msg}".strip(": "))
                    elif _iss:
                        _prev_validation_warnings.append(str(_iss))

            if _prev_reject_score >= PatchModeThresholds.REWRITE and best_blueprint:
                _previous_best = best_blueprint
            else:
                _previous_best = None

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
        _last_score = validation_result.get("score", 0) if "validation_result" in locals() else 0
        if best_blueprint and director:
            logging.warning(
                f"[ThreePhase] 제{ep_num}화 모든 재시도 실패이나 마지막 최선 blueprint 존재 (score={_last_score})"
            )
            pipeline_result["final_verdict"] = "PASS_WITH_WARNING"
            pipeline_result["quality_gate_failed"] = True
            pipeline_result["quality_risk"] = True
            pipeline_result["last_score"] = _last_score
            return best_blueprint, pipeline_result

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
        rejected_strategy: str = "",
        selection_reason: str = "",
        score_breakdown: dict | None = None,
        validation_warnings: list[str] | None = None,
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
            # [Sweep55] .format()에 json.dumps의 {}가 있으면 KeyError/ValueError 크래시 방지
            def _esc(s):
                return s.replace("{", "{{").replace("}", "}}")

            _patch_section = _patch_template.format(
                feedback_text=_esc(director_feedback),
                original_blueprint=_esc(_original_text),
            )
        else:
            _patch_section = (
                f"[패치 모드: Blueprint 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## 원본 Blueprint\n{_original_text}\n\n"
                f"전면 재설계하지 마세요. 지적된 부분만 고치세요."
            )

        _strategy_parts = []
        if selection_reason:
            _strategy_parts.append(f"[선택/거절 사유]\n{selection_reason}")
        if isinstance(score_breakdown, dict) and score_breakdown:
            _sb = ", ".join(f"{k}={v}" for k, v in score_breakdown.items() if isinstance(v, int | float))
            if _sb:
                _strategy_parts.append(f"[점수 분해]\n{_sb}")
        if isinstance(validation_warnings, list) and validation_warnings:
            _strategy_parts.append("[검증 경고]\n" + "\n".join(f"- {w}" for w in validation_warnings[:10]))
        _strategy_feedback = "\n\n".join(_strategy_parts)

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
                strategy_specific_feedback=_strategy_feedback,
                rejected_strategy=rejected_strategy,
                single_strategy=rejected_strategy,
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
