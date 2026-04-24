"""
[V0128] ValidationOrchestrator
[V56] 6-Tier 검증 통합 실행 (PRE_LLM → CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY)
+ Self-Consistency + CatharsisTimer + ActionSceneEvaluator

[V56 업데이트]
- TIER 0.25: PreLLMValidator 추가 (Python 기반 사전검증, LLM 비용 0원)
- 9가지 검사로 명백한 오류 조기 차단

[V47 업데이트]
- TIER 0.5: ContinuityValidator 추가 (에피소드 간 연속성 검증)
- 아이템 중복 획득, 무기 상태 리셋, 부상 연속성 검증

[V59 업데이트]
- 병렬 검증: asyncio 기반 독립 검증 동시 실행 (최대 40% 시간 단축)
- 적응형 임계값: 에피소드 히스토리/패턴 기반 동적 임계값 조정
- 장르별/아크별 임계값 프로파일
"""

import asyncio
import concurrent.futures
import logging
import threading
from functools import partial

from modules.core.soft_failure import report_soft_failure, resolve_db_log_dir, resolve_logs_dir, resolve_project_log_dir
from modules.core.models_config import DEFAULT_FLASH_MODEL, DEFAULT_PRO_MODEL

from .action_scene_evaluator import ActionSceneEvaluator
from .advisory_validator import AdvisoryValidator
from .blocking_validator import BlockingValidator
from .catharsis_timer import CatharsisTimer
from .consistency_validator import ConsistencyValidator
from .continuity_validator import ContinuityValidator
from .scoring_validator import ScoringValidator
from .threshold_helper import _threshold

# [V56] Pre-LLM Validator (Python 기반 사전검증)
try:
    from .pre_llm_validator import PreLLMValidator

    PRE_LLM_AVAILABLE = True
except ImportError:
    PRE_LLM_AVAILABLE = False
    logging.warning(" [ValidationOrchestrator] PreLLMValidator 로드 실패 - 사전검증 비활성화")

# [V59.1] 선택적 모듈 가용성 확인 (Lazy Import 안전성 강화)
RETROSPECTIVE_AVAILABLE = False
REFLEXION_AVAILABLE = False
CONSTITUTION_AVAILABLE = False

try:
    from .retrospective_validator import RetrospectiveValidator

    RETROSPECTIVE_AVAILABLE = True
except ImportError:
    logging.warning(" [V60.1] RetrospectiveValidator 미설치 - 회고적 검증 비활성화")

try:
    from modules.core.reflexion_manager import ReflexionManager

    REFLEXION_AVAILABLE = True
except ImportError:
    logging.warning(" [V60.1] ReflexionManager 미설치 - Reflexion 기반 개선 비활성화")

try:
    from modules.core.quality_constitution import get_constitution_for_genre

    CONSTITUTION_AVAILABLE = True
except ImportError:
    logging.warning(" [V60.1] QualityConstitution 미설치 - 품질 헌법 비활성화")


# [V44] Constitution 캐시 (모듈 레벨에서 관리)
_CONSTITUTION_CACHE: dict[str, str] = {}
_CONSTITUTION_LOCK = threading.Lock()
_VALIDATION_HISTORY_MAX = 50

# ═══════════════════════════════════════════════════════════════
# [V59] 적응형 임계값 상수
# ═══════════════════════════════════════════════════════════════

# [V59] 장르별 기본 임계값 프로파일
GENRE_THRESHOLD_PROFILES = {
    "wuxia": {
        "base_threshold": 70,
        "action_weight": 1.2,  # 액션씬 중시
        "dialogue_weight": 1.0,
        "emotion_weight": 1.1,
        "commercial_weight": 1.0,
    },
    "hunter": {
        "base_threshold": 68,
        "action_weight": 1.3,  # 액션씬 더 중시
        "dialogue_weight": 0.9,
        "emotion_weight": 1.0,
        "commercial_weight": 1.2,  # 상업성 중시
    },
    "investment": {
        "base_threshold": 72,
        "action_weight": 0.8,  # 액션씬 덜 중요
        "dialogue_weight": 1.2,  # 대화 중시
        "emotion_weight": 1.2,  # 감정선 중시
        "commercial_weight": 1.1,
    },
    "fantasy": {
        "base_threshold": 69,
        "action_weight": 1.2,  # 전투·마법 액션
        "dialogue_weight": 0.9,
        "emotion_weight": 1.0,
        "commercial_weight": 1.2,  # 성장 쾌감 상업성
    },
    "composer": {
        "base_threshold": 71,
        "action_weight": 0.7,  # 액션 비중 낮음
        "dialogue_weight": 1.0,
        "emotion_weight": 1.3,  # 음악과 감정 연결 핵심
        "commercial_weight": 0.9,
    },
    "cooking": {
        "base_threshold": 70,
        "action_weight": 0.8,  # 요리 대결 외 액션 적음
        "dialogue_weight": 1.0,
        "emotion_weight": 1.1,
        "commercial_weight": 1.0,
    },
    "alt_history": {
        "base_threshold": 72,
        "action_weight": 1.0,
        "dialogue_weight": 1.2,  # 정치 대화·협상 중시
        "emotion_weight": 1.1,
        "commercial_weight": 0.9,
    },
    "actor": {
        "base_threshold": 70,
        "action_weight": 0.7,  # 물리적 액션 적음
        "dialogue_weight": 1.3,  # 대사·연기 품질 핵심
        "emotion_weight": 1.2,  # 감정 연기·성장
        "commercial_weight": 1.0,
    },
    "sports": {
        "base_threshold": 69,
        "action_weight": 1.3,  # 경기 장면 핵심
        "dialogue_weight": 0.8,  # 경기 중 대사 적음
        "emotion_weight": 1.1,  # 승부 감정선
        "commercial_weight": 1.1,
    },
    "medical": {
        "base_threshold": 73,
        "action_weight": 0.9,  # 수술 장면 긴장감
        "dialogue_weight": 1.2,  # 진단·상담 대화
        "emotion_weight": 1.2,  # 환자·의사 감정선
        "commercial_weight": 0.9,
    },
    "_default": {
        "base_threshold": 70,
        "action_weight": 1.0,
        "dialogue_weight": 1.0,
        "emotion_weight": 1.0,
        "commercial_weight": 1.0,
    },
}

# [V59] 에피소드 유형별 임계값 조정
EPISODE_TYPE_ADJUSTMENTS = {
    "opening": {"threshold_delta": +5, "episodes": [1, 2, 3]},  # 오프닝: 높은 기준
    "climax": {"threshold_delta": +3, "episode_pattern": lambda ep: ep % 50 in [48, 49, 0]},  # 클라이막스
    "transition": {"threshold_delta": -3, "episode_pattern": lambda ep: ep % 10 in [4, 5]},  # 전환부
    "arc_finale": {"threshold_delta": +5, "episode_pattern": lambda ep: ep % 5 == 0},  # 아크 마무리
    "volume_finale": {"threshold_delta": +7, "episode_pattern": lambda ep: ep % 50 == 0},  # 권 마무리
}

# [V59] 연속 통과/실패에 따른 동적 조정
STREAK_ADJUSTMENTS = {
    "consecutive_pass_5": -2,  # 5연속 통과 시 임계값 살짝 낮춤 (안정적 품질)
    "consecutive_pass_10": -3,  # 10연속 통과
    "consecutive_fail_2": +3,  # 2연속 실패 시 임계값 높임 (품질 문제)
    "consecutive_fail_3": +5,  # 3연속 실패 시 더 높임
}

# [V59] 패턴 감지에 따른 조정
_UNCONDITIONAL_PASS_FLOOR = 85  # [TF-XC-14] 무조건 PASS 최소 점수

PATTERN_ADJUSTMENTS = {
    "high_repetition": +3,  # 높은 반복 패턴 시 더 엄격
    "low_diversity": +2,  # 낮은 다양성 시 더 엄격
    "declining_quality": +4,  # 품질 하락 추세 시 더 엄격
    "improving_quality": -2,  # 품질 상승 추세 시 완화
}


class ValidationOrchestrator:
    """
    글도비 V47 통합 검증 오케스트레이터

    5-Tier 검증을 순차적으로 실행하고 최종 결과를 반환합니다.
    TIER 0.5: CONTINUITY → TIER 1: BLOCKING → TIER 1.5: CONSISTENCY → TIER 2: SCORING → TIER 3: ADVISORY
    Self-Consistency (다수결 투표) 적용 가능.
    """

    def __init__(self, config: dict, client=None, genre=None, context=None):
        self.config = config
        self.client = client
        self.genre = genre
        self.context = context  # [Phase 5.2.2] Reflexion용 context
        if not genre:
            logging.warning("[genre-guardrail] ValidationOrchestrator: genre unresolved, using neutral defaults")

        # [V44] Constitution 로드 (캐싱 + 장르별 fallback 강화)
        self.constitution = self._load_constitution_cached(genre)

        # [V56] TIER 0.25: PRE-LLM (Python 기반 사전검증)
        # [V70] pov 전달: context에서 추출
        _pov = ""
        _protagonist_name = ""
        if context and isinstance(context, dict):
            _pov = context.get("pov", "")
            _protagonist_name = context.get("protagonist_name", "")  # [TF-PLV-1]
        self.pre_llm = (
            PreLLMValidator(genre=genre, pov=_pov, protagonist_name=_protagonist_name)
            if PRE_LLM_AVAILABLE else None
        )
        self.use_pre_llm = config.get("use_pre_llm", _threshold("orchestrator.use_pre_llm", True))

        # [V47] TIER 0.5: CONTINUITY (에피소드 간 연속성)
        # [C4-P1-2] context는 dict (ProjectContext가 아님).
        # DB 기반 prev_hud 조회 불가 — 호출자가 validation_context dict에 prev_hud를 미리 채워야 함.
        self.continuity = ContinuityValidator(context=context)

        # TIER 1: BLOCKING
        self.blocking = BlockingValidator()

        # [V46] TIER 1.5: CONSISTENCY (새로 추가)
        self.consistency = ConsistencyValidator(genre=genre)

        # TIER 2: SCORING
        scoring_model = config.get("scoring_model", DEFAULT_PRO_MODEL)
        self.scoring = ScoringValidator(client=client, model=scoring_model, constitution=self.constitution, genre=genre)
        self.scoring.pass_threshold = config.get(
            "scoring_threshold",
            _threshold("scoring.default_pass_threshold", 60),
        )

        # TIER 3: ADVISORY
        advisory_model = config.get("advisory_model", DEFAULT_FLASH_MODEL)
        self.advisory = AdvisoryValidator(client=client, model=advisory_model)

        # Self-Consistency 설정
        self.use_self_consistency = config.get(
            "use_self_consistency", _threshold("orchestrator.use_self_consistency", True)
        )
        self.consistency_votes = config.get("consistency_votes", _threshold("orchestrator.consistency_votes", 3))

        # [V43] 추가 품질 평가 모듈
        catharsis_max_gap = config.get("catharsis_max_gap", _threshold("orchestrator.catharsis_max_gap", 3))
        self.catharsis_timer = CatharsisTimer(max_frustration=catharsis_max_gap, genre=genre)
        self.action_evaluator = ActionSceneEvaluator(genre=genre)

        # [Phase 3] 장기 일관성 검증 — [TF-C04] 기본 활성화
        self.use_retrospective = config.get("use_retrospective", _threshold("orchestrator.use_retrospective", True))
        self.retrospective = None  # Lazy initialization

        # [Phase 5.2.2] Reflexion 시스템 (선택적)
        self.use_reflexion = config.get("use_reflexion", _threshold("orchestrator.use_reflexion", True))
        self.reflexion = None  # Lazy initialization

        # ═══════════════════════════════════════════════════════════════
        # [V59] 병렬 검증 + 적응형 임계값 설정
        # ═══════════════════════════════════════════════════════════════
        self.use_adaptive_threshold = config.get(
            "use_adaptive_threshold", _threshold("orchestrator.use_adaptive_threshold", True)
        )
        self.max_parallel_workers = config.get(
            "max_parallel_workers", _threshold("orchestrator.max_parallel_workers", 3)
        )

        # 적응형 임계값 히스토리 추적
        self.validation_history: list[dict] = []  # [{ep_num, score, passed, timestamp}]
        self.consecutive_passes = 0
        self._consecutive_floor_hits = 0  # [I-01] 바닥 연속 도달 카운터
        self.consecutive_fails = 0
        self.current_threshold = config.get(
            "scoring_threshold",
            _threshold("scoring.default_pass_threshold", 60),
        )

        # 장르별 프로파일 로드 — 미결정 장르는 _default 프로파일 사용
        self.threshold_profile = GENRE_THRESHOLD_PROFILES.get(genre or "", GENRE_THRESHOLD_PROFILES["_default"])

    def _report_soft_failure(
        self,
        validation_context: dict | None,
        operation: str,
        exc: Exception,
        *,
        ep_num: int | None = None,
        stage: int | str = 4,
        message: str,
        extra: dict | None = None,
    ) -> None:
        audit_event = None
        if isinstance(validation_context, dict):
            candidate = validation_context.get("_audit_event") or validation_context.get("audit_event")
            if callable(candidate):
                audit_event = candidate
        log_dir = self._resolve_soft_failure_log_dir(validation_context)
        report_soft_failure(
            component="validation_orchestrator",
            operation=operation,
            message=message,
            exc=exc,
            stage=stage,
            ep_num=ep_num,
            degraded=True,
            user_visible=False,
            learnable=True,
            extra=extra,
            log_dir=log_dir,
            audit_event=audit_event,
            warning_window_sec=180.0,
        )

    def _resolve_soft_failure_log_dir(self, validation_context: dict | None):
        if isinstance(validation_context, dict):
            for key in ("log_dir", "project_dir"):
                resolved = resolve_logs_dir(validation_context.get(key))
                if resolved is not None:
                    return resolved
            from_ctx = resolve_project_log_dir(validation_context.get("current_project"))
            if from_ctx is not None:
                return from_ctx
            resolved_db = resolve_db_log_dir(validation_context.get("db_path"))
            if resolved_db is not None:
                return resolved_db

        return resolve_project_log_dir(getattr(self.context, "current_project", None))

    def validate(self, ep_num: int, manuscript: str, validation_context: dict) -> dict:
        """
        전체 검증 실행 (5-Tier sequential).

        Args:
            ep_num: 에피소드 번호
            manuscript: 검증 대상 원고
            validation_context: {
                'encyclopedia': {...},
                'martial_hud': {...},
                'blueprint': {...},
                'mode': 'BLUEPRINT' | 'MANUSCRIPT',
                'history': [...],
                'npc_profiles': {...}
            }

        Returns:
            Public surface (authoritative):
                final_decision : "PASS" | "CONDITIONAL_PASS" | "REJECT"
                blocking_result : dict   — TIER 1 blocking validator output
                scoring_result  : dict   — TIER 2 scoring validator output
                advisory_result : dict   — TIER 3 advisory summary
                continuity_result : dict — TIER 0.5 continuity output
                total_score     : int
                feedback        : str    — human-readable composite feedback
                detailed_feedback : str  — per-tier breakdown
                adaptive_threshold : int
                self_consistency_used : bool

            Advisory side-channel keys (underscore-prefixed, consumed by
            Director for context enrichment — NOT adjudication truth):
                _continuity_advisory  : dict | absent
                _blocking_advisory    : dict | absent
                _consistency_advisory : dict | absent
                _retrospective_advisory : dict | absent
            These keys carry source, violations/failures, feedback, and
            severity. They feed Director thinking but do not override
            the authoritative final_decision.
        """
        results = {}

        # [TF-R2-XC-01] 적응형 임계값 (async validate와 동일 패턴)
        # [V-I5] try/finally로 예외 발생 시에도 복원 보장
        _original_threshold = self.scoring.pass_threshold
        try:
            if self.use_adaptive_threshold:
                adaptive_threshold = self.calculate_adaptive_threshold_v59(ep_num, validation_context)
                self.scoring.pass_threshold = adaptive_threshold
                logging.warning(f"[V59-Sync] 적응형 임계값: {adaptive_threshold}점")
            else:
                adaptive_threshold = self.current_threshold

            return self._validate_sync_body(ep_num, manuscript, validation_context, results, adaptive_threshold)
        finally:
            self.scoring.pass_threshold = _original_threshold

    def _validate_sync_body(self, ep_num, manuscript, validation_context, results, adaptive_threshold):
        """[V-I5] validate_v59 body extracted from try/finally wrapper."""
        consistency_penalty = self._run_sync_pre_scoring_validators(
            ep_num,
            manuscript,
            validation_context,
            results,
        )
        total_score = self._run_sync_scoring_phase(
            ep_num,
            manuscript,
            validation_context,
            results,
            consistency_penalty,
        )
        total_score = self._apply_retrospective_validation(
            ep_num,
            manuscript,
            validation_context,
            results,
            total_score,
        )
        total_score = self._apply_advisory_penalties(total_score, results)
        return self._finalize_validation_result(
            ep_num,
            total_score,
            results,
            adaptive_threshold,
            pass_threshold=self.scoring.pass_threshold,
        )

    def _run_pre_llm_validation(
        self,
        manuscript,
        validation_context,
        results,
        *,
        stage_prefix: str,
        reject_on_failure: bool = False,
    ):
        if not self.use_pre_llm or not self.pre_llm:
            return None

        logging.info(f"{stage_prefix} TIER 0.25: PRE-LLM validation...")
        pre_llm_result = self.pre_llm.validate(manuscript, validation_context)
        results["pre_llm_result"] = pre_llm_result

        if reject_on_failure and not pre_llm_result["passed"]:
            return self._build_reject_result_v59(
                "PRE-LLM",
                pre_llm_result,
                self._generate_pre_llm_feedback(pre_llm_result),
            )

        warning_count = len(pre_llm_result.get("warnings", []))
        if warning_count > 0:
            logging.warning(
                f" PRE-LLM warnings: {warning_count} (deduction {pre_llm_result.get('score_deduction', 0)})"
            )
        else:
            logging.info(" PRE-LLM passed")
        return None

    def _run_continuity_validation(
        self,
        ep_num,
        manuscript,
        validation_context,
        results,
        *,
        stage_prefix: str,
        advisory_log_suffix: str = "",
    ) -> None:
        logging.info(f"{stage_prefix} TIER 0.5: CONTINUITY validation...")
        continuity_result = self.continuity.validate(ep_num, manuscript, validation_context)
        results["continuity_result"] = continuity_result

        if not continuity_result["passed"]:
            violations = continuity_result.get("violations", [])
            logging.warning(
                f" [TF-36] CONTINUITY {len(violations)} violations forwarded as Director advisory{advisory_log_suffix}"
            )
            self._record_failure_to_reflexion(ep_num, "continuity", violations)
            results["_continuity_advisory"] = {
                "source": "ContinuityValidator",
                "violations": violations,
                "feedback": self._generate_continuity_feedback(continuity_result),
                "severity": "HIGH",
            }

        warning_count = continuity_result.get("warning_count", 0)
        if warning_count > 0:
            logging.warning(f" CONTINUITY warnings: {warning_count} (continue)")
        else:
            logging.info(" CONTINUITY passed")

    def _record_blocking_failure_learner_failures(
        self,
        ep_num,
        validation_context,
        failures,
        *,
        event_name: str,
        message: str,
        extra: dict,
    ) -> None:
        failure_learner = validation_context.get("_failure_learner") if isinstance(validation_context, dict) else None
        if failure_learner is None or not hasattr(failure_learner, "record_failure"):
            return

        for failure in failures:
            try:
                failure_learner.record_failure(
                    stage=4,
                    failure_type=failure.get("type", "BLOCKING") if isinstance(failure, dict) else "BLOCKING",
                    description=str(failure.get("description", failure.get("reason", "")))[:200]
                    if isinstance(failure, dict)
                    else str(failure)[:200],
                )
            except Exception as exc:
                self._report_soft_failure(
                    validation_context,
                    event_name,
                    exc,
                    ep_num=ep_num,
                    message=message,
                    extra=extra,
                )
                logging.debug("[ValidationOrchestrator] FailureLearner record failed (ignored): %s", exc)

    def _run_blocking_validation(
        self,
        ep_num,
        manuscript,
        validation_context,
        results,
        *,
        stage_prefix: str,
        advisory_log_suffix: str = "",
        failure_event_name: str = "failure_learner_record_failure",
        failure_message: str = "FailureLearner.record_failure failed during blocking advisory collection",
        failure_extra: dict | None = None,
    ) -> None:
        logging.info(f"{stage_prefix} TIER 1: BLOCKING validation...")
        blocking_result = self.blocking.validate(manuscript, validation_context)
        results["blocking_result"] = blocking_result

        if not blocking_result["passed"]:
            failures = blocking_result.get("failures", [])
            logging.warning(
                f" [TF-36] BLOCKING {len(failures)} failures forwarded as Director advisory{advisory_log_suffix}"
            )
            self._record_failure_to_reflexion(ep_num, "blocking", failures)
            self._record_blocking_failure_learner_failures(
                ep_num,
                validation_context,
                failures,
                event_name=failure_event_name,
                message=failure_message,
                extra=failure_extra or {"validator": "BlockingValidator"},
            )

        blocking_advisory = self._build_blocking_advisory(blocking_result)
        if blocking_advisory is not None:
            results["_blocking_advisory"] = blocking_advisory

        if blocking_result["passed"]:
            logging.info(f" BLOCKING passed (0/{blocking_result.get('failure_count', 0)} failures)")

    def _store_consistency_result(self, results, consistency_result) -> int:
        results["consistency_result"] = consistency_result
        unjustifiable = consistency_result.get("unjustifiable_violations", [])
        if unjustifiable:
            logging.warning(f" CONSISTENCY failed: {len(unjustifiable)} unjustifiable violations")
            results["_consistency_advisory"] = {
                "source": "ConsistencyValidator",
                "violations": unjustifiable,
                "feedback": consistency_result.get("feedback", ""),
                "severity": "CRITICAL",
            }

        consistency_penalty = consistency_result.get("score_penalty", 0)
        justifiable_count = len(consistency_result.get("justifiable_violations", []))
        if unjustifiable:
            pass
        elif justifiable_count > 0:
            logging.warning(f" CONSISTENCY warnings: {justifiable_count} (penalty {consistency_penalty})")
        else:
            logging.info(" CONSISTENCY passed")
        return consistency_penalty

    def _run_sync_pre_scoring_validators(self, ep_num, manuscript, validation_context, results) -> int:
        self._run_pre_llm_validation(
            manuscript,
            validation_context,
            results,
            stage_prefix="[V56]",
        )
        self._run_continuity_validation(
            ep_num,
            manuscript,
            validation_context,
            results,
            stage_prefix="[V47]",
        )
        self._run_blocking_validation(
            ep_num,
            manuscript,
            validation_context,
            results,
            stage_prefix="[V0128]",
        )
        logging.info("[V46] TIER 1.5: CONSISTENCY validation...")
        consistency_result = self.consistency.validate(manuscript, validation_context)
        return self._store_consistency_result(results, consistency_result)

    def _apply_refine_recommendation(self, ep_num, total_score, results) -> None:
        refine_applied = False
        refine_reason = ""

        if 88 <= total_score <= 90:
            refine_applied = True
            refine_reason = f"edge score ({total_score})"

        important_episodes = [1] + [i for i in range(25, 251, 25)]
        if ep_num in important_episodes:
            refine_applied = True
            refine_reason = (
                f"important episode ({ep_num})"
                if not refine_reason
                else refine_reason + " + important episode"
            )

        if refine_applied:
            logging.warning(f" [Self-Refine] recommended ({refine_reason})")
            results["refine_recommended"] = True
            results["refine_reason"] = refine_reason
        else:
            results["refine_recommended"] = False

    def _apply_base_score_adjustments(
        self,
        ep_num,
        manuscript,
        validation_context,
        results,
        total_score,
        consistency_penalty,
    ) -> int:
        catharsis_history = validation_context.get("catharsis_history", [])
        catharsis_result = self.catharsis_timer.check_catharsis_timing(ep_num, manuscript, catharsis_history)
        results["catharsis_result"] = catharsis_result

        if catharsis_result.get("status") in {"warning", "critical"}:
            logging.warning(f" CATHARSIS: {catharsis_result.get('message')}")
        else:
            logging.info(" CATHARSIS steady")

        action_context = {
            "technique_effects": validation_context.get("technique_effects", {}),
            "martial_hud": validation_context.get("martial_hud", {}),
        }
        action_result = self.action_evaluator.evaluate(manuscript, action_context)
        results["action_result"] = action_result

        if action_result.get("action_scene_count", 0) > 0:
            logging.info(
                f" ACTION: {action_result.get('total_score', 0)}/10 ({action_result['action_scene_count']} scenes)"
            )

        catharsis_adjustment = 0
        if catharsis_result.get("status") == "critical":
            catharsis_adjustment = -5
        elif catharsis_result.get("status") == "warning":
            catharsis_adjustment = -2

        action_adjustment = 0
        if action_result.get("action_scene_count", 0) > 0:
            action_score = action_result.get("total_score", 6)
            if action_score < 5:
                action_adjustment = -3
            elif action_score >= 8:
                action_adjustment = 2

        pre_llm_adjustment = 0
        pre_llm_result = results.get("pre_llm_result")
        if pre_llm_result and pre_llm_result.get("score_deduction", 0) > 0:
            pre_llm_adjustment = -1

        adjusted_total = (
            total_score + catharsis_adjustment + action_adjustment + consistency_penalty + pre_llm_adjustment
        )
        adjusted_total = max(0, min(100, adjusted_total))

        if catharsis_adjustment != 0 or action_adjustment != 0 or consistency_penalty != 0 or pre_llm_adjustment != 0:
            logging.info(f" Score adjusted: {total_score} -> {adjusted_total}")
            return adjusted_total

        return total_score

    def _run_sync_scoring_phase(
        self,
        ep_num,
        manuscript,
        validation_context,
        results,
        consistency_penalty,
    ) -> int:
        logging.info("[V0128] TIER 2: SCORING evaluation...")
        if self.use_self_consistency and self.client:
            scoring_result = self._evaluate_with_self_consistency(manuscript, validation_context)
            results["self_consistency_used"] = True
        else:
            scoring_result = self.scoring.validate_v59(manuscript, validation_context)
            results["self_consistency_used"] = False

        results["scoring_result"] = scoring_result
        total_score = scoring_result.get("total_score", 0)
        logging.info(f" SCORING: {total_score}/100 (threshold {self.scoring.pass_threshold})")

        self._apply_refine_recommendation(ep_num, total_score, results)

        logging.info("[V0128] TIER 3: ADVISORY generation...")
        advisory_result = self.advisory.validate(manuscript, validation_context)
        results["advisory_result"] = advisory_result
        logging.info(f" ADVISORY: {len(advisory_result.get('suggestions', []))} suggestions")

        return self._apply_base_score_adjustments(
            ep_num,
            manuscript,
            validation_context,
            results,
            total_score,
            consistency_penalty,
        )

    def _apply_retrospective_validation(self, ep_num, manuscript, validation_context, results, total_score) -> int:
        if not (self.use_retrospective and ep_num > 3 and RETROSPECTIVE_AVAILABLE):
            return total_score

        logging.info("[Phase 3] RETROSPECTIVE validation...")
        if self.retrospective is None:
            context_obj = validation_context.get("_context")
            if context_obj:
                retro_lookback = _threshold("retrospective.lookback_episodes", 10)
                try:
                    retro_lookback = int(retro_lookback)
                except (TypeError, ValueError):
                    retro_lookback = 10
                self.retrospective = RetrospectiveValidator(context_obj, lookback_episodes=retro_lookback)

        if not self.retrospective:
            return total_score

        retrospective_result = self.retrospective.validate_long_term_consistency(
            current_ep=ep_num,
            manuscript=manuscript,
            validation_context=validation_context,
        )
        results["retrospective_result"] = retrospective_result

        if retrospective_result["passed"]:
            logging.info(" RETROSPECTIVE passed")
            return total_score

        severity = retrospective_result.get("severity_level", "NONE")
        violation_count = retrospective_result.get("total_violations", 0)
        logging.warning(f" RETROSPECTIVE: {violation_count} violations ({severity})")

        penalty = 0
        if severity == "CRITICAL":
            penalty = 15
        elif severity == "HIGH":
            penalty = 10
        elif severity == "MEDIUM":
            penalty = 5

        if penalty <= 0:
            return total_score

        results["_retrospective_advisory"] = {
            "source": "RetrospectiveValidator",
            "violations": retrospective_result.get("violations", []),
            "feedback": self._format_retrospective_feedback(retrospective_result),
            "severity": severity,
        }
        total_score = max(0, total_score - penalty)
        logging.warning(f" RETROSPECTIVE penalty: -{penalty} (new total {total_score})")
        return total_score

    def _apply_advisory_penalties(self, total_score, results) -> int:
        continuity_advisory = results.get("_continuity_advisory")
        if continuity_advisory:
            continuity_penalty = min(15, len(continuity_advisory.get("violations", [])) * 5)
            total_score = max(0, total_score - continuity_penalty)
            logging.warning(f" [TF-36] CONTINUITY advisory penalty: -{continuity_penalty} (new total {total_score})")

        blocking_advisory = results.get("_blocking_advisory")
        if blocking_advisory:
            blocking_penalty = min(20, len(blocking_advisory.get("failures", [])) * 5)
            total_score = max(0, total_score - blocking_penalty)
            logging.warning(f" [TF-36] BLOCKING advisory penalty: -{blocking_penalty} (new total {total_score})")
        return total_score

    def _finalize_validation_result(
        self,
        ep_num,
        total_score,
        results,
        adaptive_threshold,
        *,
        pass_threshold,
    ):
        results["total_score"] = total_score

        unconditional_pass = max(_UNCONDITIONAL_PASS_FLOOR, pass_threshold)
        if total_score >= unconditional_pass:
            final_decision = "PASS"
            feedback = f"score strong ({total_score})"
        elif total_score >= pass_threshold:
            final_decision = "CONDITIONAL_PASS"
            feedback = f"pass ({total_score}) - see improvement guidance"
        else:
            final_decision = "REJECT"
            feedback = f"below threshold ({total_score}) - revision needed"

        advisory_parts = []
        continuity_advisory = results.get("_continuity_advisory")
        if continuity_advisory:
            advisory_parts.append(f"[CONTINUITY] {continuity_advisory['feedback']}")
        blocking_advisory = results.get("_blocking_advisory")
        if blocking_advisory:
            advisory_parts.append(f"[BLOCKING] {blocking_advisory['feedback']}")
        consistency_advisory = results.get("_consistency_advisory")
        if consistency_advisory:
            advisory_parts.append(f"[CONSISTENCY] {consistency_advisory['feedback']}")
        retrospective_advisory = results.get("_retrospective_advisory")
        if retrospective_advisory:
            advisory_parts.append(f"[RETROSPECTIVE] {retrospective_advisory['feedback']}")
        if advisory_parts:
            feedback = feedback + " | Director advisory: " + " / ".join(advisory_parts)

        results["final_decision"] = final_decision
        results["feedback"] = feedback
        results["adaptive_threshold"] = adaptive_threshold
        results["detailed_feedback"] = self._generate_detailed_feedback(results)

        passed = final_decision in ("PASS", "CONDITIONAL_PASS")
        self._record_validation_history_v59(ep_num, total_score, passed)
        return results

    def _run_parallel_stage1_validators(self, ep_num, manuscript, validation_context, results):
        early_result = self._run_pre_llm_validation(
            manuscript,
            validation_context,
            results,
            stage_prefix="[V59-Parallel]",
            reject_on_failure=True,
        )
        if early_result is not None:
            return early_result

        self._run_continuity_validation(
            ep_num,
            manuscript,
            validation_context,
            results,
            stage_prefix="[V59-Parallel]",
            advisory_log_suffix=" (parallel)",
        )
        self._run_blocking_validation(
            ep_num,
            manuscript,
            validation_context,
            results,
            stage_prefix="[V59-Parallel]",
            advisory_log_suffix=" (parallel)",
            failure_event_name="failure_learner_record_failure_parallel",
            failure_message="FailureLearner.record_failure failed during blocking advisory collection (parallel)",
            failure_extra={"validator": "BlockingValidator", "mode": "parallel"},
        )
        logging.info(" Stage 1 passed (PRE-LLM, CONTINUITY, BLOCKING)")
        return None

    async def _run_parallel_stage2_validators(self, manuscript, validation_context, results):
        logging.info("[V59-Parallel] Stage 2: starting parallel validators...")

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_workers) as executor:
            consistency_task = loop.run_in_executor(
                executor,
                partial(self.consistency.validate, manuscript, validation_context),
            )
            if self.use_self_consistency and self.client:
                scoring_task = loop.run_in_executor(
                    executor,
                    partial(self._evaluate_with_self_consistency, manuscript, validation_context),
                )
            else:
                scoring_task = loop.run_in_executor(
                    executor,
                    partial(self.scoring.validate_v59, manuscript, validation_context),
                )
            advisory_task = loop.run_in_executor(
                executor,
                partial(self.advisory.validate, manuscript, validation_context),
            )
            parallel_results = await asyncio.gather(
                consistency_task,
                scoring_task,
                advisory_task,
                return_exceptions=True,
            )

        task_names = ["consistency", "scoring", "advisory"]
        for idx, result in enumerate(parallel_results):
            if not isinstance(result, Exception):
                continue
            logging.warning("[Sweep7-A] parallel validation %s failed: %s", task_names[idx], result)
            if idx == 0:
                parallel_results[idx] = {
                    "unjustifiable_violations": [
                        {
                            "type": "consistency_validator_runtime_error",
                            "severity": "CRITICAL",
                            "reason": f"consistency validator failed: {type(result).__name__}",
                        }
                    ],
                    "score_penalty": 0,
                    "feedback": f"consistency validator runtime error: {result}",
                }
            elif idx == 1:
                parallel_results[idx] = {"total_score": 0, "feedback": "scoring validator failed"}
            else:
                parallel_results[idx] = {"suggestions": []}

        consistency_result, scoring_result, advisory_result = parallel_results
        if not isinstance(consistency_result, dict):
            consistency_result = {"unjustifiable_violations": [], "score_penalty": 0, "feedback": ""}
        if not isinstance(scoring_result, dict):
            scoring_result = {"total_score": 0, "feedback": "scoring validator failed"}
        if not isinstance(advisory_result, dict):
            advisory_result = {"suggestions": []}

        consistency_penalty = self._store_consistency_result(results, consistency_result)
        results["scoring_result"] = scoring_result
        results["advisory_result"] = advisory_result
        results["self_consistency_used"] = self.use_self_consistency and self.client is not None

        logging.info(" Stage 2 complete (parallel validators)")
        return scoring_result, consistency_penalty

    def _evaluate_with_self_consistency(self, manuscript: str, context: dict) -> dict:
        """
        [Phase 5.1.2] Conditional Self-Consistency: 조건부 다수결 투표

        - 1차 평가 먼저 실행
        - 70-85점 구간 (애매한 점수): 3-vote 실행
        - 그 외 (명확한 점수): 1-vote로 종료

        목적: 비용 60% 절감, 품질 유지
        """
        # 1차 평가 — [TF-C02] validate_v59 장르 가중치 (±1점 캡)
        logging.info(" Self-Consistency (Conditional): 1차 평가 중...")
        first_eval = self.scoring.validate_v59(manuscript, context)
        first_score = first_eval["total_score"]

        logging.info(f"Vote 1: {first_score}점, {first_eval['message']}")

        # [I-05] 조건부 판단: 경계값을 validation.yaml에서 로드 + 소프트마진
        ambiguous_lower = int(_threshold("adaptive_threshold.ambiguous_lower", 70))
        ambiguous_upper = int(_threshold("adaptive_threshold.ambiguous_upper", 85))
        soft_margin = int(_threshold("adaptive_threshold.soft_margin", 2))

        # 소프트 마진: 경계 ±N점 구간에서 50% 확률로 멀티보팅 확대
        import random

        effective_lower = ambiguous_lower
        effective_upper = ambiguous_upper
        if ambiguous_lower - soft_margin <= first_score < ambiguous_lower:
            if random.random() < 0.5:
                effective_lower = ambiguous_lower - soft_margin
        if ambiguous_upper < first_score <= ambiguous_upper + soft_margin:
            if random.random() < 0.5:
                effective_upper = ambiguous_upper + soft_margin

        if effective_lower <= first_score <= effective_upper:
            # 애매한 구간 → 추가 2회 평가
            logging.info(f" 애매한 점수({first_score}) → 추가 평가 활성화")

            evaluations = [first_eval]
            for i in range(1, self.consistency_votes):
                result = self.scoring.validate_v59(manuscript, context)
                evaluations.append(result)
                logging.info(f"Vote {i + 1}: {result['total_score']}점, {result['message']}")

            # 점수 중앙값
            import statistics

            scores = [e["total_score"] for e in evaluations]
            median_score = statistics.median(scores)

            # PASS/REJECT 다수결
            pass_votes = sum(1 for e in evaluations if e["passed"])
            final_passed = pass_votes > (self.consistency_votes // 2)

            # 대표 결과 (중앙값에 가장 가까운 것)
            representative = min(evaluations, key=lambda e: abs(e["total_score"] - median_score))

            # 결과 병합
            result = representative.copy()
            result["total_score"] = median_score
            result["passed"] = final_passed
            result["self_consistency"] = {
                "votes": self.consistency_votes,
                "pass_votes": pass_votes,
                "scores": scores,
                "median_score": median_score,
                "conditional": True,
                "reason": f"ambiguous_score ({first_score})",
            }

            logging.info(f"✅ Self-Consistency 완료: {median_score}점 (PASS {pass_votes}/{self.consistency_votes})")

        else:
            # 명확한 구간 → 1-vote로 종료
            logging.info(f" 명확한 점수({first_score}) → 1-vote로 종료 (비용 절감)")

            result = first_eval.copy()
            result["self_consistency"] = {
                "votes": 1,
                "pass_votes": 1 if first_eval["passed"] else 0,
                "scores": [first_score],
                "median_score": first_score,
                "conditional": True,
                "reason": f"clear_score ({first_score})",
                "cost_saved": True,
            }

        return result

    def _generate_pre_llm_feedback(self, pre_llm_result: dict) -> str:
        """[V56] PRE-LLM 실패 시 피드백 생성"""
        issues = pre_llm_result.get("critical_issues", [])
        warnings = pre_llm_result.get("warnings", [])

        feedback_parts = ["## PRE-LLM 사전검증 실패 (명백한 오류 감지)\n"]
        feedback_parts.append("LLM 호출 전 Python 기반 검증에서 문제가 발견되었습니다.\n")

        for issue in issues:
            category = issue.get("category", "unknown")
            desc = issue.get("description", "")
            severity = issue.get("severity", "CRITICAL")

            feedback_parts.append(f"- [{severity}] {category}: {desc}")

            # 수정 가이드 추가
            if category == "대사_부족":
                feedback_parts.append("  → 대화 장면을 추가하세요. 캐릭터 간 상호작용 필요.")
            elif category == "과다_반복_단어":
                items = issue.get("items", [])
                if items:
                    feedback_parts.append(f"  → '{items[0][0]}' 등의 단어를 동의어로 대체하세요.")
            elif category == "신체_물리학_오류":
                feedback_parts.append("  → 신체적으로 불가능한 행동을 수정하세요.")

        if warnings:
            feedback_parts.append("\n### 추가 경고 (점수 감점):")
            for warning in warnings[:3]:
                desc = warning.get("description", warning.get("category", ""))
                feedback_parts.append(f"- {desc}")

        return "\n".join(feedback_parts)

    def _generate_continuity_feedback(self, continuity_result: dict) -> str:
        """[V47] CONTINUITY 실패 시 피드백 생성"""
        violations = continuity_result.get("violations", [])
        warnings = continuity_result.get("warnings", [])

        feedback_parts = ["## CONTINUITY 검증 실패 (에피소드 간 연속성 위반)\n"]

        for violation in violations:
            reason = violation.get("reason", "")
            severity = violation.get("severity", "CRITICAL")
            fix = violation.get("fix_suggestion", "")

            feedback_parts.append(f"- [{severity}] {reason}")
            if fix:
                feedback_parts.append(f"  → 수정 방법: {fix}")

        if warnings:
            feedback_parts.append("\n### 추가 경고:")
            for warning in warnings[:3]:
                if isinstance(warning, dict):  # [V70] dict/str 혼합 방어
                    feedback_parts.append(f"- {warning.get('reason', warning.get('message', str(warning)))}")
                else:
                    feedback_parts.append(f"- {warning}")

        feedback_parts.append("\n위 문제를 수정 후 재제출하십시오.")
        feedback_parts.append("직전 에피소드의 상태를 확인하고 연속성을 유지해주세요.")

        return "\n".join(feedback_parts)

    @staticmethod
    def _collect_blocking_warning_lines(blocking_result: dict) -> list[str]:
        warning_lines: list[str] = []
        seen: set[str] = set()

        for raw_warning in blocking_result.get("warnings", []) or []:
            warning_text = str(raw_warning or "").strip()
            if warning_text and warning_text not in seen:
                warning_lines.append(warning_text)
                seen.add(warning_text)

        for raw_check in blocking_result.get("degraded_checks", []) or []:
            check_name = str(raw_check or "").strip()
            synthesized = f"degraded: {check_name}" if check_name else ""
            if synthesized and synthesized not in seen:
                warning_lines.append(synthesized)
                seen.add(synthesized)

        return warning_lines

    def _build_blocking_advisory(self, blocking_result: dict) -> dict | None:
        failures = blocking_result.get("failures", []) or []
        warning_lines = self._collect_blocking_warning_lines(blocking_result)
        degraded_checks = [
            str(raw_check).strip()
            for raw_check in (blocking_result.get("degraded_checks", []) or [])
            if str(raw_check).strip()
        ]

        if not failures and not warning_lines and not degraded_checks:
            return None

        return {
            "source": "BlockingValidator",
            "failures": failures,
            "warnings": warning_lines,
            "degraded_checks": degraded_checks,
            "feedback": self._generate_blocking_feedback(blocking_result),
            "severity": "HIGH" if failures else "MEDIUM",
        }

    def _generate_blocking_feedback(self, blocking_result: dict) -> str:
        """BLOCKING advisory 피드백 생성"""
        failures = blocking_result.get("failures", []) or []
        warning_lines = self._collect_blocking_warning_lines(blocking_result)

        if failures:
            feedback_parts = ["## BLOCKING 검증 실패\n"]

            for failure in failures:
                reason = failure.get("reason", "")
                severity = failure.get("severity", "UNKNOWN")
                feedback_parts.append(f"- [{severity}] {reason}")

            if warning_lines:
                feedback_parts.append("\n### 추가 경고")
                for warning in warning_lines:
                    feedback_parts.append(f"- {warning}")

            feedback_parts.append("\n위 문제를 수정 후 재제출하십시오.")
            return "\n".join(feedback_parts)

        if warning_lines:
            feedback_parts = ["## BLOCKING 검증 경고\n"]
            for warning in warning_lines:
                feedback_parts.append(f"- {warning}")
            feedback_parts.append("\n즉시 REJECT는 아니지만 Director 검토가 필요합니다.")
            return "\n".join(feedback_parts)

        return ""

    def _generate_detailed_feedback(self, results: dict) -> str:
        """상세 피드백 생성"""
        feedback_parts = []

        # 점수 요약
        total_score = results.get("total_score", 0)
        feedback_parts.append(f"## 총점: {total_score}/100")

        # SCORING 세부 점수
        scoring_result = results.get("scoring_result", {})
        if not isinstance(scoring_result, dict):
            scoring_result = {}
        breakdown = scoring_result.get("breakdown", {})
        if not isinstance(breakdown, dict):
            breakdown = {}

        if breakdown:
            feedback_parts.append("\n### 세부 점수")
            for category, data in breakdown.items():
                if isinstance(data, dict):
                    score = data.get("score", 0)
                    max_score = data.get("max", 0)
                    reason = data.get("reason", "")
                    feedback_parts.append(f"- {category}: {score}/{max_score}점 - {reason}")

        # 강점
        strengths = self._identify_strengths(breakdown)
        if strengths:
            feedback_parts.append("\n### 강점")
            for s in strengths:
                feedback_parts.append(f"- {s}")

        # 개선 필요
        weaknesses = self._identify_weaknesses(breakdown)
        if weaknesses:
            feedback_parts.append("\n### 개선 필요")
            for w in weaknesses:
                feedback_parts.append(f"- {w}")

        # ADVISORY 제안
        advisory_result = results.get("advisory_result", {})
        suggestions = advisory_result.get("suggestions", [])
        if suggestions:
            feedback_parts.append("\n### 추가 제안 (ADVISORY)")
            for s in suggestions[:3]:
                suggestion_text = s.get("suggestion", "")
                feedback_parts.append(f"- {suggestion_text}")

        return "\n".join(feedback_parts)

    def _identify_strengths(self, breakdown: dict) -> list[str]:
        """강점 식별 (높은 점수 항목)"""
        strengths = []
        if not isinstance(breakdown, dict):
            return strengths

        for category, data in breakdown.items():
            if isinstance(data, dict):
                score = data.get("score", 0)
                max_score = data.get("max", 1)
                percentage = (score / max_score) * 100 if max_score > 0 else 0

                if percentage >= 80:
                    reason = data.get("reason", category)
                    strengths.append(f"{category}: {reason}")

        return strengths

    def _identify_weaknesses(self, breakdown: dict) -> list[str]:
        """약점 식별 (낮은 점수 항목)"""
        weaknesses = []
        if not isinstance(breakdown, dict):
            return weaknesses

        for category, data in breakdown.items():
            if isinstance(data, dict):
                score = data.get("score", 0)
                max_score = data.get("max", 1)
                percentage = (score / max_score) * 100 if max_score > 0 else 0

                if percentage < 60:
                    reason = data.get("reason", category)
                    weaknesses.append(f"{category}: {reason}")

        return weaknesses

    def _load_constitution_cached(self, genre: str) -> str:
        """
        [V44] Constitution 로드 (캐싱 + 장르별 fallback 강화)

        Args:
            genre: 장르 (wuxia, hunter, investment)

        Returns:
            str: Constitution 텍스트
        """
        # 캐시 확인
        with _CONSTITUTION_LOCK:
            if genre in _CONSTITUTION_CACHE:
                return _CONSTITUTION_CACHE[genre]

        # [V59.1] Constitution 로드 시도 (사전 검증된 플래그 사용)
        if CONSTITUTION_AVAILABLE:
            try:
                constitution = get_constitution_for_genre(genre)
                with _CONSTITUTION_LOCK:
                    _CONSTITUTION_CACHE[genre] = constitution
                return constitution
            except Exception as e:
                logging.warning(f"[WARNING] Constitution 로드 실패 ({genre}): {e}")
        else:
            logging.warning("[WARNING] quality_constitution 모듈 미설치")

        logging.warning("[WARNING] 기본 Constitution 사용 - 검증 품질 저하 가능")

        # [V44] 장르별 fallback Constitution
        fallback = self._get_fallback_constitution(genre)
        with _CONSTITUTION_LOCK:
            _CONSTITUTION_CACHE[genre] = fallback
        return fallback

    def _get_fallback_constitution(self, genre: str) -> str:
        """[V44] 장르별 Fallback Constitution 생성"""
        base = """
# 글도비 품질 헌법 (Fallback Mode)

## TIER 1: BLOCKING
### Article 1: 설정 일관성
1.1 사망한 NPC는 등장할 수 없다.
1.2 소유하지 않은 아이템은 사용할 수 없다.
1.3 파괴된 장소는 방문할 수 없다.
1.4 능력치 초과 기술 사용 불가.
1.5 최소 분량: MANUSCRIPT 4000자, BLUEPRINT 500자.

## TIER 2: SCORING (70점 이상 통과)
### Article 2: 캐릭터 일관성 [15점]
### Article 3: 문장 품질 [20점]
### Article 4: 감정선 [20점]
### Article 5: 대화 품질 [15점]
### Article 6: 상업성 [20점]
### Article 7: 패턴 다양성 [10점]

## TIER 3: ADVISORY
### Article 8: 클리셰 감지, 표현 개선, 복선 기회
"""

        # 장르별 Amendment 추가
        genre_amendments = {
            "wuxia": """
### Wuxia-Specific (Fallback)
- 무공 위계 준수 (후천 → 선천 → 절정 → 화경)
- 강호 예법 존중
- 내공 운용 묘사 권장
""",
            "hunter": """
### Hunter-Specific (Fallback)
- 게이트 등급 준수 (E-D-C-B-A-S)
- 미획득 스킬 사용 불가
- 각성 전 능력 사용 불가
""",
            "investment": """
### Investment-Specific (Fallback)
- 투자 수익률 현실성 (연 100% 이상은 근거 필요)
- 자금 출처 명확
- 정보 획득 경로 명시
""",
        }

        amendment = genre_amendments.get(genre, "")
        return base + amendment

    def _format_retrospective_feedback(self, retrospective_result: dict) -> str:
        """[Phase 3] Retrospective 검증 결과를 피드백 형식으로 변환"""
        feedback_parts = ["## 장기 일관성 위반\n"]

        violations = retrospective_result.get("violations", [])
        severity = retrospective_result.get("severity_level", "NONE")

        feedback_parts.append(f"심각도: {severity}")
        feedback_parts.append(f"총 {len(violations)}개 위반 감지\n")

        for violation in violations:
            reason = violation.get("reason", "")
            severity = violation.get("severity", "LOW")

            feedback_parts.append(f"- [{severity}] {reason}")

            if "required_fix" in violation:
                feedback_parts.append(f"  수정 방법: {violation['required_fix']}")

        return "\n".join(feedback_parts)

    def _record_failure_to_reflexion(self, ep_num: int, failure_type: str, failures: list):
        """
        [Phase 5.2.2] 실패 패턴을 Reflexion에 기록

        Args:
            ep_num: 에피소드 번호
            failure_type: 실패 유형
            failures: 실패 목록
        """
        # [V59.1] Reflexion 가용성 및 설정 확인
        if not self.use_reflexion or not REFLEXION_AVAILABLE:
            return

        try:
            # Lazy initialization (모듈은 이미 import됨)
            if self.reflexion is None:
                # context가 필요한데, ValidationOrchestrator에는 없을 수 있음
                # 이 경우 기록 스킵
                if not hasattr(self, "context") or self.context is None:
                    return
                if isinstance(self.context, dict) or not hasattr(self.context, "db"):
                    return

                self.reflexion = ReflexionManager(self.context)

            # 각 실패 항목 기록
            for failure in failures:
                description = failure.get("reason", "알 수 없는 실패")
                solution = failure.get("required_fix", "")

                self.reflexion.record_failure(
                    ep_num=ep_num, failure_type=failure_type, description=description, solution=solution
                )

        except Exception as e:
            # Reflexion 실패해도 검증은 계속 진행
            logging.warning(f" [Reflexion] 실패 기록 실패: {e}")

    # ═══════════════════════════════════════════════════════════════
    # [V59] 병렬 검증 메서드
    # ═══════════════════════════════════════════════════════════════

    async def validate_parallel_v59(self, ep_num: int, manuscript: str, validation_context: dict) -> dict:
        """
        [V59] 병렬 검증 실행 - 독립적인 검증을 동시에 실행하여 시간 단축

        실행 전략:
        - Stage 1 (순차): PRE_LLM → CONTINUITY → BLOCKING (의존성 있음, 실패 시 조기 종료)
        - Stage 2 (병렬): CONSISTENCY + SCORING + ADVISORY (독립적)
        - Stage 3 (순차): 추가 평가 (CatharsisTimer, ActionEvaluator, Retrospective)

        Args:
            ep_num: 에피소드 번호
            manuscript: 검증 대상 원고
            validation_context: 검증 컨텍스트

        Returns:
            validate()와 동일한 결과 구조
        """
        results = {}

        # [V-I5] try/finally로 예외 발생 시에도 임계값 복원 보장
        _original_threshold = self.scoring.pass_threshold
        try:
            if self.use_adaptive_threshold:
                adaptive_threshold = self.calculate_adaptive_threshold_v59(ep_num, validation_context)
                self.scoring.pass_threshold = adaptive_threshold
                logging.warning(f"[V59] 적응형 임계값: {adaptive_threshold}점 (기본: {self.threshold_profile['base_threshold']})"
                )
            else:
                adaptive_threshold = self.current_threshold

            return await self._validate_parallel_body(
                ep_num, manuscript, validation_context, results, adaptive_threshold
            )
        finally:
            self.scoring.pass_threshold = _original_threshold

    async def _validate_parallel_body(self, ep_num, manuscript, validation_context, results, adaptive_threshold):
        """[V-I5] validate_parallel_v59 body extracted from try/finally wrapper."""
        early_result = self._run_parallel_stage1_validators(
            ep_num,
            manuscript,
            validation_context,
            results,
        )
        if early_result is not None:
            return early_result

        scoring_result, consistency_penalty = await self._run_parallel_stage2_validators(
            manuscript,
            validation_context,
            results,
        )
        total_score = scoring_result.get("total_score", 0)
        total_score = self._apply_base_score_adjustments(
            ep_num,
            manuscript,
            validation_context,
            results,
            total_score,
            consistency_penalty,
        )
        total_score = self._apply_advisory_penalties(total_score, results)
        return self._finalize_validation_result(
            ep_num,
            total_score,
            results,
            adaptive_threshold,
            pass_threshold=adaptive_threshold,
        )
    def validate_parallel_sync_v59(self, ep_num: int, manuscript: str, validation_context: dict) -> dict:
        """
        [V59] 병렬 검증 동기 래퍼 - 기존 동기 코드에서 호출 가능

        Args:
            ep_num: 에피소드 번호
            manuscript: 검증 대상 원고
            validation_context: 검증 컨텍스트

        Returns:
            validate()와 동일한 결과 구조
        """
        # [V59.1] Python 3.10+ 호환성 개선
        try:
            # 이미 실행 중인 이벤트 루프 확인 (Python 3.10+ 안전한 방식)
            try:
                loop = asyncio.get_running_loop()
                # 이벤트 루프가 실행 중인 경우 (Jupyter, Streamlit 등)
                try:
                    import nest_asyncio

                    nest_asyncio.apply()
                    return loop.run_until_complete(self.validate_parallel_v59(ep_num, manuscript, validation_context))
                except ImportError:
                    # nest_asyncio 없으면 동기 버전으로 fallback
                    logging.warning(" [V59] nest_asyncio 미설치 - 순차 검증으로 전환")
                    return self.validate(ep_num, manuscript, validation_context)
            except RuntimeError:
                # 실행 중인 루프 없음 - 새로 생성
                pass
        except Exception as e:
            logging.warning(f" [V59] asyncio 초기화 실패: {e} - 순차 검증으로 전환")
            return self.validate(ep_num, manuscript, validation_context)

        # 새 이벤트 루프에서 실행
        try:
            return asyncio.run(self.validate_parallel_v59(ep_num, manuscript, validation_context))
        except Exception as e:
            logging.warning(f" [V59] 병렬 검증 실패: {e} - 순차 검증으로 전환")
            return self.validate(ep_num, manuscript, validation_context)

    def _build_reject_result_v59(self, stage: str, result: dict, feedback: str) -> dict:
        """[V59] 조기 종료용 REJECT 결과 빌드"""
        return {
            "final_decision": "REJECT",
            "reason": f"{stage} 검증 실패",
            f"{stage.lower().replace('-', '_')}_result": result,  # [V70] PRE-LLM → pre_llm (하이픈→언더스코어)
            "total_score": 0,
            "feedback": feedback,
            "self_consistency_used": False,
            "early_exit_stage": stage,
        }

    # ═══════════════════════════════════════════════════════════════
    # [V59] 적응형 임계값 메서드
    # ═══════════════════════════════════════════════════════════════

    def calculate_adaptive_threshold_v59(self, ep_num: int, validation_context: dict) -> int:
        """
        [V59] 적응형 임계값 계산

        Args:
            ep_num: 에피소드 번호
            validation_context: 검증 컨텍스트

        Returns:
            계산된 임계값 (정수)
        """
        # 기본 임계값 (장르별)
        base_threshold = self.threshold_profile["base_threshold"]

        # 1. 에피소드 유형별 조정
        episode_adjustment = self._get_episode_type_adjustment_v59(ep_num)

        # 2. 연속 통과/실패 조정
        streak_adjustment = self._get_streak_adjustment_v59()

        # 3. 패턴 기반 조정
        pattern_adjustment = self._get_pattern_adjustment_v59(validation_context)

        # 4. 아크 위치 조정
        arc_adjustment = self._get_arc_position_adjustment_v59(ep_num)

        # 최종 계산
        final_threshold = base_threshold + episode_adjustment + streak_adjustment + pattern_adjustment + arc_adjustment

        # [I-01] 범위 제한 — 바닥값을 validation.yaml에서 로드
        floor = int(_threshold("adaptive_threshold.floor", 60))
        final_threshold = max(floor, min(90, final_threshold))

        # [I-01] 바닥 연속 도달 시 리셋
        floor_hit_reset = int(_threshold("adaptive_threshold.floor_hit_reset", 3))
        if final_threshold <= floor:
            self._consecutive_floor_hits += 1
            if self._consecutive_floor_hits >= floor_hit_reset:
                logging.warning(f"[I-01] 임계값 바닥({floor}) {self._consecutive_floor_hits}회 연속 → consecutive_passes 리셋"
                )
                self.consecutive_passes = 0
                self._consecutive_floor_hits = 0
        else:
            self._consecutive_floor_hits = 0

        return int(final_threshold)

    def _get_episode_type_adjustment_v59(self, ep_num: int) -> int:
        """[V59] 에피소드 유형에 따른 임계값 조정"""
        positive_adj = 0
        negative_adj = 0

        for ep_type, config in EPISODE_TYPE_ADJUSTMENTS.items():
            matched = False
            if "episodes" in config:
                matched = ep_num in config["episodes"]
            elif "episode_pattern" in config:
                matched = config["episode_pattern"](ep_num)

            if matched:
                delta = config["threshold_delta"]
                if delta >= 0:
                    positive_adj = max(positive_adj, delta)
                else:
                    negative_adj = min(negative_adj, delta)

        return positive_adj + negative_adj

    def _get_streak_adjustment_v59(self) -> int:
        """[V59] 연속 통과/실패에 따른 임계값 조정"""
        if self.consecutive_fails >= 3:
            return STREAK_ADJUSTMENTS["consecutive_fail_3"]
        elif self.consecutive_fails >= 2:
            return STREAK_ADJUSTMENTS["consecutive_fail_2"]
        elif self.consecutive_passes >= 10:
            return STREAK_ADJUSTMENTS["consecutive_pass_10"]
        elif self.consecutive_passes >= 5:
            return STREAK_ADJUSTMENTS["consecutive_pass_5"]
        return 0

    def _get_pattern_adjustment_v59(self, validation_context: dict) -> int:
        """[V59] 패턴 분석 기반 임계값 조정"""
        adjustment = 0

        # PatternTracker 결과 확인
        pattern_analysis = validation_context.get("pattern_analysis", {})

        if pattern_analysis:
            # 높은 반복 패턴
            repetition_score = pattern_analysis.get("repetition_score", 0)
            if repetition_score > 70:
                adjustment += PATTERN_ADJUSTMENTS["high_repetition"]

            # 낮은 다양성
            diversity_score = pattern_analysis.get("diversity_score", 100)
            if diversity_score < 40:
                adjustment += PATTERN_ADJUSTMENTS["low_diversity"]

        # 최근 점수 트렌드 분석
        if len(self.validation_history) >= 5:
            recent_scores = [h["score"] for h in self.validation_history[-5:]]
            if len(recent_scores) >= 3:
                # 하락 추세 감지
                if recent_scores[-1] < recent_scores[-3] - 5:
                    adjustment += PATTERN_ADJUSTMENTS["declining_quality"]
                # 상승 추세 감지 [I-01] cascade cap 적용
                elif recent_scores[-1] > recent_scores[-3] + 5:
                    cascade_cap = int(_threshold("adaptive_threshold.cascade_cap_passes", 10))
                    if self.consecutive_passes < cascade_cap:
                        adjustment += PATTERN_ADJUSTMENTS["improving_quality"]

        return adjustment

    def _get_arc_position_adjustment_v59(self, ep_num: int) -> int:
        """[V59] 아크 내 위치에 따른 임계값 조정"""
        arc_position = ep_num % 5  # 5화 = 1아크 기준

        if arc_position == 1:  # 아크 시작
            return +2  # 시작은 중요
        elif arc_position == 0:  # 아크 마무리 (5의 배수)
            return +3  # 마무리도 중요
        elif arc_position in [2, 3]:  # 중간
            return -1  # 중간은 살짝 관대
        return 0

    def _record_validation_history_v59(self, ep_num: int, score: float, passed: bool):
        """[V59] 검증 히스토리 기록 + 연속 카운트 업데이트"""
        import time

        # [R6-P1-1] 재시도 여부 판별 — 같은 ep_num이 이미 기록돼 있으면 retry
        was_retry = any(h.get("ep_num") == ep_num for h in self.validation_history)

        # [E5c-P2-5] Remove previous entries for same ep_num so retries overwrite, not accumulate
        self.validation_history = [h for h in self.validation_history if h.get("ep_num") != ep_num]

        self.validation_history.append({"ep_num": ep_num, "score": score, "passed": passed, "timestamp": time.time()})

        # 히스토리 크기 제한 (최근 N개)
        if len(self.validation_history) > _VALIDATION_HISTORY_MAX:
            self.validation_history = self.validation_history[-_VALIDATION_HISTORY_MAX:]

        # [R6-P1-1] 연속 카운트는 새 에피소드일 때만 업데이트 (재시도 시 drift 방지)
        if not was_retry:
            if passed:
                self.consecutive_passes += 1
                self.consecutive_fails = 0
            else:
                self.consecutive_fails += 1
                self.consecutive_passes = 0

    def set_manual_threshold_v59(self, threshold: int, duration_episodes: int = 0):
        """
        [V59] 수동 임계값 설정 (일시적 오버라이드)

        Args:
            threshold: 설정할 임계값
            duration_episodes: 적용 기간 (0=영구, N=N화 동안)
        """
        self.current_threshold = max(60, min(90, threshold))
        self.use_adaptive_threshold = duration_episodes != 0  # 영구(0)면 적응형 비활성화

        if duration_episodes > 0:
            logging.info(f"[V59] 임계값 {threshold}점으로 {duration_episodes}화 동안 고정")
        else:
            logging.info(f"[V59] 임계값 {threshold}점으로 고정 (적응형 비활성화)")
