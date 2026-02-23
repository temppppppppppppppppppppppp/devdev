from modules.core.constants import ManuscriptLimits
from modules.core.hud_utils import build_hud_context as _build_hud_context_shared

from .base_agent import BaseAgent
from .director_auditor import DirectorQualityAuditor
from .director_caching import DirectorCachingManager
from .director_continuity import DirectorContinuityValidator
from .director_ensemble import DirectorEnsembleSelector
from .director_grading import DirectorGradingSystem
from .director_prompts import ENSEMBLE_SELECTION_PROMPT as _ENSEMBLE_PROMPT
from .director_prompts import MANUSCRIPT_HISTORY_CONFLICT_PROMPT as _HISTORY_CONFLICT_PROMPT

# [V64 P2-1] ENSEMBLE_SELECTION_PROMPT → director_prompts.py에서 import
ENSEMBLE_SELECTION_PROMPT = _ENSEMBLE_PROMPT
# [V64 P2-1] MANUSCRIPT_HISTORY_CONFLICT_PROMPT → director_prompts.py에서 import
MANUSCRIPT_HISTORY_CONFLICT_PROMPT = _HISTORY_CONFLICT_PROMPT


class Director(BaseAgent):
    """
    [V0128] Director - 품질 검증 총괄
    [V59] 품질 등급화 A/B/C 및 구체적 수정 가이드 시스템 추가
    [V61] Entity 명칭 일관성 검증 - 최종 방어선 역할
    [V60.87] 원고 역사 충돌 검사 - 전체 원고 대비 연속성 검증

    [V61 NEW]
    - validate_entity_consistency(): Entity 명칭 일관성 LLM 검증
    - audit_manuscript(), audit_strategic_plan()에 entity_registry 파라미터 추가
    - entity_consistency_enabled 플래그로 기능 활성화/비활성화

    [V60.87 NEW]
    - check_manuscript_history_conflicts(): 전체 원고 역사 대비 충돌 검사
    - manuscript_history_check_enabled 플래그로 기능 활성화/비활성화
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.v0128_orchestrator = None  # Lazy initialization
        self.genre = "wuxia"  # 기본값, set_genre()로 변경 가능
        self.use_v0128 = False  # V0128 검증 시스템 사용 여부

        # [V49.3] Self-Consistency 설정 (Stage 1-3 감사에 적용)
        self.use_self_consistency = True  # Self-Consistency 활성화 여부
        self.consistency_votes = 3  # 투표 횟수
        self.ambiguous_lower = 50  # 애매한 점수 하한 (전략 감사는 0-100 스케일이 아님)
        self.ambiguous_upper = 60  # [V60.24] 애매한 점수 상한 (70→65)

        # [V60.24] 적응형 PASS 기준선 기본값 - 살짝 완화
        self.base_pass_threshold = 60  # 기본 PASS 기준 점수 (65→60)
        self.adaptive_thresholds_enabled = True

        # [V61] Entity 일관성 검증 설정
        self.entity_consistency_enabled = True  # Entity 일관성 검증 활성화

        # [V60.87] 원고 역사 충돌 검사 설정
        self.manuscript_history_check_enabled = True  # 전체 원고 대비 충돌 검사 활성화
        self.history_check_max_episodes = 30  # 최대 몇 화까지 역사 참조할지

        # [V64 P2-1] CachingManager 분리 — 원고 캐시, 역사 구성, protagonist_config 캐싱
        self._caching = DirectorCachingManager(self.client, self.primary_model, self.context)

        # [V64 P2-1] GradingSystem 분리 — 원고 품질 등급화, 수정 가이드, 적응형 기준선 [V65 C-5]
        self._grading = DirectorGradingSystem(self)

        # [V64 P2-1] EnsembleSelector 분리 — 후보 비교, 선택, 판정
        self._ensemble = DirectorEnsembleSelector(self)

        # [V64 P2-1] ContinuityValidator 분리 — Entity/원고/BP 연속성 검증
        self._continuity = DirectorContinuityValidator(self)

        # [V64 P2-1] QualityAuditor 분리 — 장르/캐릭터/V0128 검증
        self._auditor = DirectorQualityAuditor(self)

        # [V60.89] 주인공 설정 검증 (protagonist_config)
        self.protagonist_config_check_enabled = True

        # [V60.90] 장르별 Guard 연결 - 특화 검증 메서드 호출용
        self.guard = None  # main_a.py에서 set_guard()로 설정
        self.genre_validation_enabled = True  # 장르별 특화 검증 활성화

    def get_adaptive_threshold(
        self, arc_pos: int = 1, total_eps: int = 5, ep_type: str = "normal", retry_count: int = 0
    ) -> dict:
        """[V65 C-5] 위임 → DirectorGradingSystem"""
        return self._grading.get_adaptive_threshold(arc_pos, total_eps, ep_type, retry_count)

    def apply_adaptive_decision(
        self, score: int, original_decision: str, arc_pos: int = 1, total_eps: int = 5, retry_count: int = 0
    ) -> dict:
        """[V65 C-5] 위임 → DirectorGradingSystem"""
        return self._grading.apply_adaptive_decision(score, original_decision, arc_pos, total_eps, retry_count)

    def set_genre(self, genre: str):
        """장르 설정 (main_a.py에서 boot 시 호출)"""
        self.genre = genre
        # [Sweep46] auditor의 v0128_orchestrator도 리셋 (장르 변경 시 재초기화 필요)
        self.v0128_orchestrator = None
        self._auditor.v0128_orchestrator = None

    def set_guard(self, guard) -> None:
        """[V60.90] 장르 Guard 설정 (main_a.py에서 호출)"""
        self.guard = guard

    def invalidate_caches(self) -> None:
        """[I-16] 캐시 전량 무효화 (rollback/rewind 시 호출)."""
        if hasattr(self, "_caching"):
            self._caching.manuscript_cache_name = None
            self._caching._cached_manuscript_count = 0
        if hasattr(self, "_continuity"):
            self._continuity._cached_manuscript_ep = None
            self._continuity._cached_blueprint_ep = None

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """[V64 P2-7] 위임 → modules.core.hud_utils.build_hud_context (director variant)"""
        return _build_hud_context_shared(state_tracker, ep_num, variant="director")

    def _run_genre_specific_validation(self, manuscript: str, ep_num: int) -> dict:
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor._run_genre_specific_validation(manuscript, ep_num)

    def set_v0128_enabled(self, enabled: bool):
        """V0128 검증 시스템 활성화/비활성화"""
        self.use_v0128 = enabled

    def validate_entity_consistency(
        self, content: str, entity_registry: dict, content_type: str = "manuscript"
    ) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.validate_entity_consistency(content, entity_registry, content_type)

    def _format_entity_registry_for_director(self, entity_registry: dict) -> str:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity._format_entity_registry_for_director(entity_registry)

    def compare_and_select_blueprint(
        self, candidates, arc_data, ep_num, prev_blueprint=None, entity_registry=None, state_tracker=None
    ):
        """[V64] 위임 → DirectorEnsembleSelector"""
        return self._ensemble.compare_and_select_blueprint(
            candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
        )

    def audit_manuscript(
        self,
        ep_num,
        manuscript,
        arc_doc,
        history_summary,
        prev_full_text,
        arc_pos,
        total_eps=None,
        target_len=ManuscriptLimits.WARNING_LENGTH,
        retry_count=0,
        validation_context=None,
        entity_registry=None,
        manuscript_history=None,
        state_tracker=None,
    ):
        """[V65 C-5] 위임 → DirectorQualityAuditor"""
        return self._auditor.audit_manuscript(
            ep_num,
            manuscript,
            arc_doc,
            history_summary,
            prev_full_text,
            arc_pos,
            total_eps,
            target_len,
            retry_count,
            validation_context,
            entity_registry,
            manuscript_history,
            state_tracker,
        )

    def audit_strategic_plan(
        self,
        arc_plan,
        prev_arc_context,
        curr_block=None,
        protagonist_name=None,
        suspected_duplicates=None,
        entity_registry=None,
        story_context="",
    ):
        """[V67.1] 위임 → DirectorQualityAuditor (story_context 추가)"""
        return self._auditor.audit_strategic_plan(
            arc_plan,
            prev_arc_context,
            curr_block,
            protagonist_name,
            suspected_duplicates,
            entity_registry,
            story_context=story_context,
        )

    # =================================================================
    # ═══════════════════════════════════════════════════════════════
    # [V60] Blueprint 완전성 검증
    # ═══════════════════════════════════════════════════════════════

    def _validate_blueprint_completeness_v60(self, manuscript: str, blueprint: dict) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity._validate_blueprint_completeness_v60(manuscript, blueprint)

    # [V0128] 3-Tier Validation System
    # =================================================================

    def _audit_with_v0128(self, ep_num, manuscript, validation_context, target_len=ManuscriptLimits.WARNING_LENGTH):
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor._audit_with_v0128(ep_num, manuscript, validation_context, target_len)

    def audit_manuscript_v0128(self, ep_num, manuscript, validation_context, config=None, genre="wuxia"):
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor.audit_manuscript_v0128(ep_num, manuscript, validation_context, config, genre)

    def assess_character_logic(self, ep_num, manuscript, npc_profiles, character_traits):
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor.assess_character_logic(ep_num, manuscript, npc_profiles, character_traits)

    def on_approve_workflow(self, ep_num, state_updates, current_hud, martial_manager=None):
        """[V65 C-5] 위임 → DirectorGradingSystem"""
        return self._grading.on_approve_workflow(ep_num, state_updates, current_hud, martial_manager)

    # =================================================================
    # [V59] 품질 등급화 시스템 (A/B/C Grade)
    # =================================================================

    # [V64 P2-1] GradingSystem 위임 — 등급 관련 상수/메서드는 DirectorGradingSystem으로 이관
    QUALITY_GRADES = DirectorGradingSystem.QUALITY_GRADES
    QUALITY_WEIGHTS = DirectorGradingSystem.QUALITY_WEIGHTS

    def grade_manuscript_v59(self, ep_num: int, manuscript: str, validation_result: dict) -> dict:
        """[V64] 위임 → DirectorGradingSystem"""
        return self._grading.grade_manuscript_v59(ep_num, manuscript, validation_result)

    def generate_revision_guide_v59(
        self, grade: str, item_scores: dict, weaknesses: list, validation_result: dict
    ) -> dict:
        """[V64] 위임 → DirectorGradingSystem"""
        return self._grading.generate_revision_guide_v59(grade, item_scores, weaknesses, validation_result)

    def format_revision_report_v59(self, grade_result: dict) -> str:
        """[V64] 위임 → DirectorGradingSystem"""
        return self._grading.format_revision_report_v59(grade_result)

    # [V64 P2-1] EnsembleSelector 위임 — ENSEMBLE_SELECTION_PROMPT는 director_ensemble.py로 이관
    ENSEMBLE_SELECTION_PROMPT = _ENSEMBLE_PROMPT

    def select_and_judge_ensemble(
        self,
        ep_num,
        candidates,
        validation_results,
        blueprint,
        previous_ending,
        arc_pos=1,
        total_eps=5,
        retry_count=0,
        episode_digest="",
        mandatory_context="",
        prev_manuscripts_text="",
        story_context="",
    ):
        """[V67.1] 위임 → DirectorEnsembleSelector (story_context 추가)"""
        return self._ensemble.select_and_judge_ensemble(
            ep_num,
            candidates,
            validation_results,
            blueprint,
            previous_ending,
            arc_pos,
            total_eps,
            retry_count,
            episode_digest,
            mandatory_context=mandatory_context,
            prev_manuscripts_text=prev_manuscripts_text,
            story_context=story_context,
        )

    def quick_judge_single(self, ep_num, manuscript, blueprint, previous_ending, retry_count=0):
        """[V64] 위임 → DirectorEnsembleSelector"""
        return self._ensemble.quick_judge_single(ep_num, manuscript, blueprint, previous_ending, retry_count)

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.87] 원고 역사 충돌 검사 (Manuscript History Conflict Check)
    # ═══════════════════════════════════════════════════════════════════════

    def check_manuscript_history_conflicts(
        self,
        ep_num: int,
        current_manuscript: str,
        manuscript_history: list,
        use_summary: bool = True,
        story_context: str = "",
        memory_context: str = "",
    ) -> dict:
        """[V67.1] 위임 → DirectorContinuityValidator (story_context 추가)"""
        return self._continuity.check_manuscript_history_conflicts(
            ep_num,
            current_manuscript,
            manuscript_history,
            use_summary,
            story_context=story_context,
            memory_context=memory_context,
        )

    def build_manuscript_history_for_check(self, db_manager, ep_num: int) -> list:
        """[V64] 위임 → DirectorCachingManager"""
        return self._caching.build_manuscript_history_for_check(db_manager, ep_num)

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.88] 원고 컨텍스트 캐싱 (Manuscript Context Caching)
    # ═══════════════════════════════════════════════════════════════════════

    def create_manuscript_cache(self, db_manager, current_ep: int, ttl_seconds: int = 3600) -> str:
        """[V64] 위임 → DirectorCachingManager"""
        return self._caching.create_manuscript_cache(db_manager, current_ep, ttl_seconds)

    def check_manuscript_history_with_cache(self, ep_num: int, current_manuscript: str) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.check_manuscript_history_with_cache(ep_num, current_manuscript)

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.89] 주인공 설정 준수 검증 (Protagonist Config Compliance)
    # ═══════════════════════════════════════════════════════════════════════

    def _get_protagonist_config(self) -> dict:
        """[V64] 위임 → DirectorCachingManager"""
        return self._caching.get_protagonist_config()

    def validate_protagonist_config_compliance(self, manuscript: str, ep_num: int = 0) -> dict:
        """[V65 C-5] 위임 → DirectorQualityAuditor"""
        return self._auditor.validate_protagonist_config_compliance(manuscript, ep_num)

    def check_blueprint_continuity_with_cache(self, new_blueprint: dict, ep_num: int, db=None, limit: int = 10) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.check_blueprint_continuity_with_cache(new_blueprint, ep_num, db, limit)

    def check_manuscript_continuity_with_cache(
        self,
        new_manuscript: str,
        ep_num: int,
        db=None,
        limit: int = 10,
        story_context: str = "",
        memory_context: str = "",
    ) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.check_manuscript_continuity_with_cache(
            new_manuscript,
            ep_num,
            db,
            limit,
            story_context=story_context,
            memory_context=memory_context,
        )
