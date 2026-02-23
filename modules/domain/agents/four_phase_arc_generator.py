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

from modules.core.constants import ContextLimits, Stage2Limits

from .arc_ensemble import ArcEnsembleGenerator
from .base_agent import BaseAgent, _get_sub_component_models
from .constraint_compiler import ConstraintCompiler
from .negative_example_injector import NegativeExampleInjector
from .preflight_checker import PreflightChecker
from .unified_arc_validator import UnifiedArcValidator

# 장르 Guard 이름 → NegativeExampleInjector 장르 키 매핑
_NEI_GENRE_DETECT_MAP: dict[str, str] = {
    "wuxia": "wuxia",
    "무협": "wuxia",
    "hunter": "hunter",
    "헌터": "hunter",
    "investment": "investment",
    "투자": "investment",
    "fantasy": "fantasy",
    "판타지": "fantasy",
}


class FourPhaseArcGenerator(BaseAgent):
    """
    [V60.75] Three Phase Arc Generator

    3단계 파이프라인: 제약수집 → 생성 → 검증
    (클래스명은 호환성을 위해 유지)
    """

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)
        # DI 후보: context.master_bible (getattr fallback 2회: L177, L545 — protagonist_config 추출)
        # DI 후보: context.guard (hasattr 패턴 — 장르 감지용, L63)

        # 서브 모듈
        sub_models = _get_sub_component_models("four_phase_arc_generator")
        self.preflight = PreflightChecker(context, client, sub_models.get("preflight", "gemini-3-flash-preview"))
        self.ensemble = ArcEnsembleGenerator(context, client, sub_models.get("ensemble", "gemini-2.5-pro"))
        self.validator = UnifiedArcValidator(context, client, sub_models.get("validator", "gemini-2.5-flash"))
        self.compiler = ConstraintCompiler()
        # [S2#1] 장르 Guard에서 장르 감지 → NegativeExampleInjector에 전달
        _detected_genre = "wuxia"
        try:
            if hasattr(context, "guard") and context.guard:
                _guard_name = context.guard.get_genre_name().lower()
                for _key, _genre in _NEI_GENRE_DETECT_MAP.items():
                    if _key in _guard_name:
                        _detected_genre = _genre
                        break
        except Exception:
            pass
        self.negative_injector = NegativeExampleInjector(_detected_genre)

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
        adversarial_self_play=None,
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

        ep_start + ep_count - 1

        pipeline_result = {
            "arc_no": arc_no,
            "phases": {},
            "final_verdict": None,
            "retries": 0,
            "patch_used": False,
            "patch_fallback": False,
        }

        # [V62.5] 이전 Arc 아이템/수여물 사전 수집 (UnifiedArcValidator 중복 스캔 방지)
        _pre_items = set()
        _pre_grants = set()
        for _prev in prev_arcs:
            _acq = _prev.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(_acq, list):
                _pre_items.update(
                    (i.get("name", i.get("item", "")) if isinstance(i, dict) else str(i)).strip() for i in _acq if i
                )
            _grt = _prev.get("state_constraints", {}).get("grants_received", [])
            if isinstance(_grt, list):
                _pre_grants.update(
                    (g.get("name", g.get("item", "")) if isinstance(g, dict) else str(g)).strip() for g in _grt if g
                )

        # Preflight 캐싱
        cached_constraint_block = None
        cached_preflight = None
        # [V60.77] Director 피드백이 있으면 우선 반영
        feedback = ""
        _base_director_feedback = ""
        if director_feedback:
            _base_director_feedback = f"[🎬 Director 피드백 - 반드시 반영할 것]\n{director_feedback}\n"
            feedback = _base_director_feedback
            logging.info(f"📢 [V60.77] Director 피드백 주입됨 ({len(director_feedback)}자)")

        # [Patch Mode] 내부 retry용 이전 REJECT 추적
        _prev_rejected_arc = None
        _prev_reject_feedback = ""
        _prev_selected_strategy = ""  # [EnsembleFB] REJECT된 당선 전략 이름

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

            # [Patch Mode] 내부 retry: 이전 REJECT arc가 있으면 패치 시도
            best_arc = None
            all_candidates = []
            if _prev_rejected_arc and retry >= 1:
                pipeline_result["patch_used"] = True
                logging.info(f"[Patch Mode] FourPhase 내부 패치 시도 (retry={retry})")
                try:
                    best_arc, _patch_result = self.patch_arc_with_feedback(
                        original_arc=_prev_rejected_arc,
                        director_feedback=_prev_reject_feedback,
                        attempt_number=retry + 1,
                        arc_no=arc_no,
                        ep_start=ep_start,
                        vol_strategy=vol_strategy,
                        curr_block=curr_block,
                        prev_arcs=prev_arcs,
                        assets=assets,
                        protagonist_name=protagonist_name,
                        entity_registry=entity_registry,
                        state_tracker=state_tracker,
                        vector_context=vector_context,
                        adversarial_self_play=adversarial_self_play,
                    )
                    if best_arc and _patch_result.get("final_verdict") == "PASS":
                        # 패치 + 검증 모두 성공 → Phase 3 스킵하고 바로 반환
                        pipeline_result["phases"]["generate"] = {
                            "status": "patch_pass",
                            "candidates_count": 1,
                            "selected_strategy": "patch",
                        }
                        pipeline_result["final_verdict"] = "PASS"
                        pipeline_result["retries"] = retry
                        self.stats["phase3_pass"] += 1
                        logging.info(f"✅ [Patch Mode] FourPhase 내부 패치 성공 (retry={retry})")
                        return best_arc, pipeline_result
                    # 패치 검증 실패 → 폴백
                    if not best_arc:
                        pipeline_result["patch_fallback"] = True
                        logging.info("[Patch Mode] FourPhase 내부 패치 실패 → 전면 재생성 폴백")
                except Exception as _patch_err:
                    logging.warning(f"[Patch Mode] FourPhase 내부 패치 오류: {str(_patch_err)[:80]}")
                    pipeline_result["patch_fallback"] = True
                    best_arc = None

            if not best_arc:
                best_arc, all_candidates = self.ensemble.generate_ensemble(
                    arc_no=arc_no,
                    ep_start=ep_start,
                    vol_strategy=vol_strategy,
                    curr_block=curr_block,
                    prev_arc_context=prev_arc_context,
                    constraint_block=full_constraint_block,
                    assets=assets,
                    feedback=feedback,
                    strategy_specific_feedback=_prev_reject_feedback if retry > 0 else "",  # [EnsembleFB]
                    rejected_strategy=_prev_selected_strategy if retry > 0 else "",  # [EnsembleFB]
                    protagonist_name=protagonist_name,
                    protagonist_config=protagonist_config,  # [V60.88]
                    entity_registry=entity_registry,  # [V60.92] Entity Registry
                    ep_count=ep_count,  # [V61.1] 가변 페이싱
                    retry=retry,  # [V61.5] 재시도 시 thinking 다운그레이드
                )

            if not best_arc:
                logging.warning("❌ [Phase 2] Ensemble 생성 실패")
                pipeline_result["phases"]["generate"] = {"status": "failed"}
                # [Sweep55] Director 원래 피드백 보존 (Sweep53 패턴과 동일)
                _gen_fail_msg = "Ensemble 생성 실패. 다시 시도하세요."
                feedback = f"{_base_director_feedback}\n{_gen_fail_msg}" if _base_director_feedback else _gen_fail_msg
                continue

            if retry >= 2 and adversarial_self_play and best_arc:
                try:
                    _asp_ctx = {
                        "arc_no": arc_no,
                        "ep_start": ep_start,
                        "director_feedback": feedback,
                    }
                    _asp_input = json.dumps(best_arc, ensure_ascii=False)
                    _asp_result = adversarial_self_play.generate_with_adversary(
                        initial_content=_asp_input,
                        content_type="arc",
                        context=_asp_ctx,
                    )
                    _asp_output = getattr(_asp_result, "final_output", "") if _asp_result else ""
                    if _asp_output:
                        _asp_arc = self._extract_json_robust(_asp_output)
                        if not isinstance(_asp_arc, dict) or not _asp_arc:
                            try:
                                _asp_arc = json.loads(_asp_output)
                            except (json.JSONDecodeError, ValueError):
                                _asp_arc = {}
                        if isinstance(_asp_arc, dict) and _asp_arc.get("tactical_doc"):
                            best_arc = _asp_arc
                            pipeline_result["asp_used"] = True
                            logging.info(f"✅ [ASP] Stage2 Arc 교정 적용 (retry={retry})")
                except Exception as e:
                    logging.warning(f"[SilentPass:Stage2:ASP] {e!s:.120}")

            # [EnsembleFB] 당선 전략 이름 기록 (REJECT 시 다음 retry에 전달)
            _current_strategy = best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown")
            pipeline_result["phases"]["generate"] = {
                "status": "complete",
                "candidates_count": len(all_candidates),
                "selected_strategy": _current_strategy,
            }
            self.stats["phase2_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2.5: AUTO-SANITIZE - 부상 에스컬레이션 자동 세정
            # ═══════════════════════════════════════════════════════════════
            best_arc = self._check_arc_end_state(best_arc)

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
                # [Sweep53] Director 원래 피드백 보존 + 검증 피드백 결합
                _validator_feedback = validation_result.get("feedback", "검증 실패")
                feedback = (
                    f"{_base_director_feedback}\n[검증 피드백]\n{_validator_feedback}"
                    if _base_director_feedback
                    else _validator_feedback
                )

                # [Patch Mode] REJECT된 arc 보존 (다음 retry에서 패치 시도용)
                if best_arc:
                    _prev_rejected_arc = best_arc
                    _prev_reject_feedback = feedback
                    _prev_selected_strategy = _current_strategy  # [EnsembleFB]

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

    # =========================================================================
    # [Patch Mode] Arc 원본 보존 + Director 피드백 지적사항만 수정
    # =========================================================================

    def patch_arc_with_feedback(
        self,
        *,
        original_arc: dict,
        director_feedback: str,
        attempt_number: int,
        # generate()와 동일 파라미터
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arcs: list[dict],
        assets: dict = None,
        protagonist_name: str = "주인공",
        entity_registry: dict = None,
        state_tracker=None,
        vector_context: str = "",
        adversarial_self_play=None,
    ) -> tuple[dict | None, dict]:
        """[Patch Mode] 원본 Arc를 보존하며 Director 피드백 지적사항만 수정.

        패치 전용 프롬프트(ARC_PATCH_MODE_PROMPT)를 로드하여 원본 Arc + Director
        피드백을 enhanced_feedback으로 조립한 뒤, generate()의 Phase 2 ensemble을
        호출하여 후보를 생성한다.

        실패 시 (None, pipeline_result) 반환 → 호출측에서 full regenerate 폴백.
        """
        pipeline_result = {
            "arc_no": arc_no,
            "phases": {},
            "final_verdict": None,
            "retries": 0,
            "patch_mode": True,
            "patch_used": True,
            "patch_fallback": False,
        }

        # 1) YAML 프롬프트 로드
        try:
            from modules.core.prompt_loader import PromptLoader

            _patch_template = PromptLoader().load("arc_generator", "ARC_PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[SilentPass:ArcGen] ARC_PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            _patch_template = None

        # 2) 원본 Arc 직렬화
        _original_text = json.dumps(original_arc, ensure_ascii=False, indent=2)[:30000]

        # 3) 패치 프롬프트 포맷
        if _patch_template:
            # [Sweep55] .format()에 json.dumps의 {}가 있으면 KeyError/ValueError 크래시 방지
            # WARNING: _esc()는 str.format() 호출 전에 반드시 적용해야 합니다.
            # JSON 문자열 내 {/}가 format placeholder로 해석되어 KeyError 발생 방지.
            def _esc(s):
                """Escape braces for str.format() — {→{{ }→}}"""
                return s.replace("{", "{{").replace("}", "}}")

            _patch_section = _patch_template.format(
                feedback_text=_esc(director_feedback),
                original_arc=_esc(_original_text),
            )
        else:
            _patch_section = (
                f"[패치 모드: Arc 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## 원본 Arc\n{_original_text}\n\n"
                f"전면 재설계하지 마세요. 지적된 부분만 고치세요."
            )

        enhanced_feedback = (
            f"[🔧 {attempt_number}차 수정 - 패치 모드: Arc 원본 보존 + 지적사항만 수정]\n\n"
            f"{_patch_section}\n\n"
            f"⚠️ 원본 Arc의 전체 구조, 에피소드 배분, 서사 흐름을 보존하면서 피드백 지적사항만 수정하세요.\n"
            f"⚠️ 수정하지 않는 부분은 원본을 그대로 유지하세요."
        )

        # 4) Phase 1: Constraint (generate()와 동일)
        preflight_result = self.preflight.analyze(prev_arcs)
        preflight_injection = self.preflight.generate_analyst_injection(preflight_result)
        compiled_constraints = self.compiler.compile(prev_arcs)
        negative_examples = self.negative_injector.generate_injection()
        self_check = self.negative_injector.generate_self_check_prompt()
        full_constraint_block = "\n".join([preflight_injection, compiled_constraints, negative_examples, self_check])

        # 5) Phase 2: Ensemble 생성 (패치 피드백 주입)
        ep_count, _ = self._determine_ep_count(curr_block, arc_no, prev_arcs)
        protagonist_config = {}
        try:
            master_bible = getattr(self.context, "master_bible", {})
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible)
                protagonist_config = bible_root.get("protagonist_config", {})
        except Exception:
            pass

        prev_arc_context = self._generate_prev_context(prev_arcs, preflight_result)
        if vector_context:
            prev_arc_context = f"{prev_arc_context}\n\n[과거 유사 맥락 (벡터 검색)]\n{vector_context}"

        try:
            best_arc, all_candidates = self.ensemble.generate_ensemble(
                arc_no=arc_no,
                ep_start=ep_start,
                vol_strategy=vol_strategy,
                curr_block=curr_block,
                prev_arc_context=prev_arc_context,
                constraint_block=full_constraint_block,
                assets=assets,
                feedback=enhanced_feedback,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                entity_registry=entity_registry,
                ep_count=ep_count,
                retry=0,
            )
        except Exception as e:
            logging.warning(f"[Patch Mode] Arc ensemble 생성 실패: {e!s:.200}")
            pipeline_result["final_verdict"] = "FAILED"
            return None, pipeline_result

        if not best_arc:
            logging.warning("[Patch Mode] Arc ensemble 후보 없음 → 폴백 필요")
            pipeline_result["final_verdict"] = "FAILED"
            return None, pipeline_result

        # 6) Phase 2.5: Auto-sanitize
        best_arc = self._check_arc_end_state(best_arc)

        # 7) Phase 3: Validate
        _pre_items = set()
        _pre_grants = set()
        for _prev in prev_arcs:
            _acq = _prev.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(_acq, list):
                _pre_items.update(
                    (i.get("name", i.get("item", "")) if isinstance(i, dict) else str(i)).strip() for i in _acq if i
                )
            _grt = _prev.get("state_constraints", {}).get("grants_received", [])
            if isinstance(_grt, list):
                _pre_grants.update(
                    (g.get("name", g.get("item", "")) if isinstance(g, dict) else str(g)).strip() for g in _grt if g
                )

        verdict, validation_result = self.validator.validate(
            arc=best_arc,
            prev_arcs=prev_arcs,
            constraints=full_constraint_block,
            state_tracker=state_tracker,
            pre_collected_items=_pre_items,
            pre_collected_grants=_pre_grants,
        )

        pipeline_result["phases"]["validate"] = {
            "status": "complete",
            "verdict": verdict,
            "issues_count": len(validation_result.get("issues", [])),
        }

        if verdict == "PASS":
            # [OpusTF] ASP 교정 — generate() L338-349 패턴 재사용
            if adversarial_self_play and best_arc:
                try:
                    _asp_ctx = {
                        "arc_no": arc_no,
                        "ep_start": ep_start,
                        "director_feedback": director_feedback,
                    }
                    _asp_input = json.dumps(best_arc, ensure_ascii=False)
                    _asp_result = adversarial_self_play.generate_with_adversary(
                        initial_content=_asp_input,
                        content_type="arc",
                        context=_asp_ctx,
                    )
                    _asp_output = getattr(_asp_result, "final_output", "") if _asp_result else ""
                    if _asp_output:
                        _asp_arc = self._extract_json_robust(_asp_output)
                        if not isinstance(_asp_arc, dict) or not _asp_arc:
                            try:
                                _asp_arc = json.loads(_asp_output)
                            except (json.JSONDecodeError, ValueError):
                                _asp_arc = {}
                        if isinstance(_asp_arc, dict) and _asp_arc.get("tactical_doc"):
                            best_arc = _asp_arc
                            pipeline_result["asp_used"] = True
                            logging.info(f"✅ [Patch+ASP] Arc {arc_no} ASP 교정 적용")
                except Exception as e:
                    logging.warning(f"[SilentPass:PatchMode:ASP] {e!s:.120}")

            pipeline_result["final_verdict"] = "PASS"
            logging.info(f"✅ [Patch Mode] Arc {arc_no} 패치 성공")
            return best_arc, pipeline_result

        logging.warning(f"⚠️ [Patch Mode] Arc {arc_no} 패치 검증 실패 → 폴백 필요")
        pipeline_result["final_verdict"] = "FAILED"
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
        final_equipment = arc_end.get("equipment")
        if final_equipment is None:
            final_equipment = joint.get("physical_inventory", [])
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
            if len(_full_history) > ContextLimits.MAX_CONTEXT_CHARS:
                _full_history = _full_history[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (200K자 절삭)"
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

    def _check_arc_end_state(self, arc: dict) -> dict:
        """[I-12] 아크 종료 상태 점검 (advisory only — 대원칙 #1 준수).

        자동 덮어쓰기 대신 WARNING 로깅으로 LLM에 판단을 위임합니다.
        부상 회복 여부, 내공 복원 여부는 LLM이 아크 생성 시 결정합니다.
        """
        warnings = []

        sc = arc.get("state_constraints", {})
        end_state = sc.get("arc_end_state", {})
        if isinstance(end_state, dict):
            inj = str(end_state.get("injuries", "없음"))
            if inj not in ("없음", "정상", ""):
                warnings.append(f"부상 미회복: '{inj}' (아크 간 자연 치유 고려)")
            energy = end_state.get("internal_energy")
            if isinstance(energy, (int, float)) and energy < 100:
                warnings.append(f"내공 미복원: {energy}% (아크 간 회복 고려)")

        ss = arc.get("status_shadow", {})
        if isinstance(ss, dict):
            ei = str(ss.get("expected_injuries", "없음"))
            if ei not in ("없음", "정상", ""):
                warnings.append(f"status_shadow 부상 잔류: '{ei}'")

        if warnings:
            logging.warning(f"[I-12] 아크 종료 상태 점검: {warnings}")

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
