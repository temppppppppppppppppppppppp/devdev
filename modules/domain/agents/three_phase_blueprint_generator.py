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

from modules.core.constants import AIModels
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
from modules.models.blueprint import validate_blueprint

from .base_agent import BaseAgent, _get_sub_component_models
from .blueprint_constraint_compiler import BlueprintConstraintCompiler
from .blueprint_ensemble import BlueprintEnsembleGenerator
from .stage3_blueprint_patch_ir import (
    apply_blueprint_patch_ir,
    build_blueprint_patch_packet,
    explain_blueprint_patch_packet_failure,
    supports_blueprint_patch_ir,
)
from .three_phase_blueprint_runtime import ThreePhaseBlueprintRuntime
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
        self.ensemble = BlueprintEnsembleGenerator(
            context, client, sub_models.get("ensemble", AIModels.DEFAULT_ARCHITECT)
        )
        self.validator = UnifiedBlueprintValidator(
            context, client, sub_models.get("validator", AIModels.FLASH_ANALYSIS_MODEL)
        )
        self.runtime = ThreePhaseBlueprintRuntime(self)

        # 통계
        self.stats = {
            "total_attempts": 0,
            "phase1_complete": 0,
            "phase2_complete": 0,
            "phase3_pass": 0,
            "phase3_reject": 0,
        }

    def _record_intermediate_reject(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        retry: int,
        max_retries: int,
        reject_reason: str,
        event_tag: str,
        candidate_key: str = "",
    ) -> None:
        """Record retry-loop rejects that would otherwise vanish before the next attempt."""
        if retry >= max_retries:
            return

        monitor = getattr(self.context, "pass_rate_monitor", None)
        recorder = getattr(monitor, "record_attempt", None)
        if not callable(recorder):
            return

        try:
            arc_num = int((arc_data or {}).get("arc_no", 0) or 0)
        except (TypeError, ValueError, AttributeError):
            arc_num = 0

        attempt_num = max(1, int(retry or 0) + 1)
        session_id = resolve_logging_session_id(getattr(self.context, "current_project", None))
        base_attempt_key = build_attempt_key(
            stage=3,
            ep_num=ep_num,
            arc_num=arc_num,
            attempt_num=attempt_num,
            session_id=session_id,
        )
        recorder(
            stage=3,
            episode=ep_num,
            arc=arc_num,
            attempt_num=attempt_num,
            success=False,
            reject_reason=str(reject_reason or event_tag),
            generation_method="blueprint_intermediate",
            attempt_key=f"{base_attempt_key}:intermediate:{event_tag}",
            final_verdict="REJECT",
            error_category=str(event_tag or ""),
            candidate_key=str(candidate_key or ""),
        )

    def generate(
        self,
        ep_num: int,
        arc_data: dict,
        prev_blueprint: dict | None = None,
        prev_blueprints: list[dict] | None = None,
        max_retries: int = 9,  # [TF-23b] 9 = ? 10? ?? (0~9)
        external_feedback: str = "",
        director=None,
        arc_idx: int = 0,
        entity_registry: dict | None = None,
        protagonist_name: str = "\uc8fc\uc778\uacf5",
        protagonist_config: dict | None = None,
        state_tracker=None,
        db=None,
        semantic_context: str = "",
        prev_manuscripts_text: str = "",
        adversarial_self_play=None,
        prev_hud: dict | None = None,
    ) -> tuple[dict | None, dict]:
        """Thin owner shell over the bounded three-phase runtime."""
        return self.runtime.generate(
            ep_num=ep_num,
            arc_data=arc_data,
            prev_blueprint=prev_blueprint,
            prev_blueprints=prev_blueprints,
            max_retries=max_retries,
            external_feedback=external_feedback,
            director=director,
            arc_idx=arc_idx,
            entity_registry=entity_registry,
            protagonist_name=protagonist_name,
            protagonist_config=protagonist_config,
            state_tracker=state_tracker,
            db=db,
            semantic_context=semantic_context,
            prev_manuscripts_text=prev_manuscripts_text,
            adversarial_self_play=adversarial_self_play,
            prev_hud=prev_hud,
        )

    # =========================================================================
    # [InPlace] Blueprint 단일 LLM 1회 호출로 in-place 수정
    # =========================================================================

    def _inplace_patch_blueprint(
        self,
        *,
        original_blueprint: dict,
        director_feedback: str,
        ep_num: int,
        arc_data: dict,
        normalized_fix_pack: dict | None = None,
    ) -> dict | None:
        """score >= 60: 단일 LLM 1회 호출로 Blueprint in-place 수정.

        실패 시 None 반환 → 호출측에서 전면 재생성 폴백.
        """
        from modules.core.prompt_loader import PromptLoader
        from modules.core.response_schemas import BLUEPRINT_SCHEMA

        _full_json = json.dumps(original_blueprint, ensure_ascii=False, indent=2)
        if len(_full_json) > 30000:
            logging.warning(
                "[TRUNCATION] _inplace_patch_blueprint: Blueprint JSON %d자 > 30KB 상한 → InPlace 불가", len(_full_json)
            )
            return None  # 절단 시 깨진 JSON → full rewrite 폴백
        original_json = _full_json

        # [TF-49b] Arc tactical excerpt 추출 → 프롬프트에 prepend
        _arc_tactical_prefix = ""
        try:
            from modules.core.tactical_utils import extract_episode_tactical

            _arc_tactical = extract_episode_tactical(
                arc_data.get("tactical_doc", ""),
                ep_num,
                episode_details=arc_data.get("episode_details"),
            )[:3000]
            if _arc_tactical:
                _arc_tactical_prefix = f"## Arc 전술서 — 제{ep_num}화 목표\n{_arc_tactical}\n\n"
        except Exception:
            pass

        try:
            patch_template = PromptLoader().load("blueprint_generator", "BLUEPRINT_PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[InPlace] BLUEPRINT_PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            patch_template = None

        patch_contract = normalized_fix_pack if isinstance(normalized_fix_pack, dict) else {}
        patch_packet: dict = {}
        use_patch_ir = False
        self._last_blueprint_patch_failure_reason = ""
        self._last_blueprint_patch_failure_meta = {}
        if normalized_fix_pack is not None and isinstance(normalized_fix_pack, dict) and not patch_contract:
            logging.info("[InPlace] empty Stage3 fix_pack -> full regenerate fallback")
            self._last_blueprint_patch_failure_reason = "empty_fix_pack"
            return None
        if supports_blueprint_patch_ir(patch_contract):
            patch_packet = build_blueprint_patch_packet(
                original_blueprint=original_blueprint,
                normalized_fix_pack=patch_contract,
            )
            if not patch_packet:
                failure_reason = explain_blueprint_patch_packet_failure(
                    original_blueprint=original_blueprint,
                    normalized_fix_pack=patch_contract,
                )
                self._last_blueprint_patch_failure_reason = failure_reason or "unknown_packet_failure"
                self._last_blueprint_patch_failure_meta = {
                    "reason": self._last_blueprint_patch_failure_reason,
                    "target_kind": str(patch_contract.get("target_kind", "") or "").strip().lower(),
                    "patch_targets": list(patch_contract.get("patch_targets") or [])[:6],
                }
                logging.info(
                    "[InPlace] Blueprint structured patch packet unavailable (%s); full regenerate fallback",
                    self._last_blueprint_patch_failure_reason,
                )
                return None
            use_patch_ir = True

        patch_contract_json = json.dumps(patch_contract or {}, ensure_ascii=False, indent=2)
        patch_packet_json = json.dumps(patch_packet or {}, ensure_ascii=False, indent=2)

        if patch_template:

            def _esc(s):
                return s.replace("{", "{{").replace("}", "}}")

            prompt = patch_template.format(
                feedback_text=_esc(director_feedback),
                patch_contract=_esc(patch_contract_json),
                patch_packet=_esc(patch_packet_json),
                original_blueprint=_esc(original_json),
            )
        else:
            prompt = (
                f"[Blueprint 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## Patch Contract\n{patch_contract_json}\n\n"
                f"## Patch Packet\n{patch_packet_json}\n\n"
                f"## 원본 Blueprint\n{original_json}\n\n"
                f"전면 재설계하지 마세요. 지적된 부분만 고치세요."
            )

        # [TF-49b] Arc 컨텍스트를 프롬프트 앞에 추가
        if _arc_tactical_prefix:
            prompt = _arc_tactical_prefix + prompt

        try:
            if use_patch_ir:
                response = self.ensemble.ask(prompt, temperature=0.2, thinking_level="medium")
                patch_payload = self.ensemble._extract_json_robust(response)
                if not isinstance(patch_payload, dict):
                    self._last_blueprint_patch_failure_reason = "invalid_patch_payload"
                    return None
                result = apply_blueprint_patch_ir(
                    original_blueprint=original_blueprint,
                    patch_packet=patch_packet,
                    patch_payload=patch_payload,
                )
                if not isinstance(result, dict):
                    self._last_blueprint_patch_failure_reason = "patch_ir_apply_failed"
                    return None
                result.setdefault("episode_number", ep_num)
                result = validate_blueprint(result)
                logging.info(f"✅ [InPlace] Blueprint 제{ep_num}화 patch-IR 수정 완료")
                return result

            response = self.ensemble.ask(
                prompt, temperature=0.3, response_schema=BLUEPRINT_SCHEMA, thinking_level="medium"
            )
            result = self.ensemble._extract_json_robust(response)
            if not isinstance(result, dict):
                return None
            result.setdefault("episode_number", ep_num)
            # [TF-49b] 원본 필드 보존 + scene_breakdown 씬 키 복원 — 1-depth deep merge
            _orig_sb = original_blueprint.get("scene_breakdown", {})
            _result_sb = result.get("scene_breakdown")
            for key, val in original_blueprint.items():
                if key not in result:
                    result[key] = val
                elif isinstance(val, dict) and isinstance(result[key], dict):
                    for sub_key, sub_val in val.items():
                        if sub_key not in result[key]:
                            result[key][sub_key] = sub_val
            if isinstance(_orig_sb, dict) and isinstance(_result_sb, dict):
                _lost = set(_orig_sb) - set(_result_sb)
                if _lost:
                    logging.info("[InPlace] LLM이 씬 %d개 누락 → 원본에서 복원: %s", len(_lost), _lost)
                    for sk in _lost:
                        _result_sb[sk] = _orig_sb[sk]
            result = validate_blueprint(result)  # [감리] Pydantic 정규화 (ep_num↔episode_number 동기 등)
            logging.info(f"✅ [InPlace] Blueprint 제{ep_num}화 in-place 수정 완료")
            return result
        except Exception as e:
            logging.warning(f"[InPlace] Blueprint in-place 패치 실패: {e!s:.200}")
            return None

    def get_stats(self) -> dict:
        """통계 반환"""
        # denominator = terminal outcomes (pass + reject), not generate() calls
        terminal = self.stats["phase3_pass"] + self.stats["phase3_reject"]
        if terminal == 0:
            return self.stats

        rate = self.stats["phase3_pass"] / terminal * 100
        return {**self.stats, "pass_rate": f"{rate:.1f}%"}

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


def create_three_phase_blueprint_generator(context, client, model_tier: str = AIModels.DEFAULT_ARCHITECT):
    """ThreePhaseBlueprintGenerator 생성 헬퍼"""
    return ThreePhaseBlueprintGenerator(context, client, model_tier)
