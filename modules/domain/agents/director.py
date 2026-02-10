import json
import statistics
from .base_agent import BaseAgent
from .director_caching import DirectorCachingManager
from .director_grading import DirectorGradingSystem
from .director_ensemble import DirectorEnsembleSelector, ENSEMBLE_SELECTION_PROMPT as _ENSEMBLE_PROMPT
from .director_continuity import DirectorContinuityValidator, MANUSCRIPT_HISTORY_CONFLICT_PROMPT as _HISTORY_CONFLICT_PROMPT
from .director_auditor import DirectorQualityAuditor
# [V64.P4] 프롬프트 외부화 — director_prompts.py에서 import
from .director_prompts import STRATEGIC_AUDIT_PROMPT_V30, DIRECTOR_AUDIT_PROMPT_V30
from modules.validation.validation_orchestrator import ValidationOrchestrator
from modules.core.hud_utils import build_hud_context as _build_hud_context_shared
from modules.core.constants import ManuscriptLimits  # [V64.P4]

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_guard, validate_primitive_compliance
    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


# [V64.P4] STRATEGIC_AUDIT_PROMPT_V30, DIRECTOR_AUDIT_PROMPT_V30 → director_prompts.py 이관

# [V64 P2-1] MANUSCRIPT_HISTORY_CONFLICT_PROMPT → director_continuity.py → director_prompts.py 이관
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.v0128_orchestrator = None  # Lazy initialization
        self.genre = 'wuxia'  # 기본값, set_genre()로 변경 가능
        self.use_v0128 = False  # V0128 검증 시스템 사용 여부

        # [V49.3] Self-Consistency 설정 (Stage 1-3 감사에 적용)
        self.use_self_consistency = True  # Self-Consistency 활성화 여부
        self.consistency_votes = 3  # 투표 횟수
        self.ambiguous_lower = 40  # 애매한 점수 하한 (전략 감사는 0-100 스케일이 아님)
        self.ambiguous_upper = 65  # [V60.24] 애매한 점수 상한 (70→65)

        # [V60.24] 적응형 PASS 기준선 기본값 - 살짝 완화
        self.base_pass_threshold = 60  # 기본 PASS 기준 점수 (65→60)
        self.adaptive_thresholds_enabled = True

        # [V61] Entity 일관성 검증 설정
        self.entity_consistency_enabled = True  # Entity 일관성 검증 활성화

        # [V60.87] 원고 역사 충돌 검사 설정
        self.manuscript_history_check_enabled = True  # 전체 원고 대비 충돌 검사 활성화
        self.history_check_max_episodes = 10  # 최대 몇 화까지 역사 참조할지 (너무 많으면 토큰 초과)

        # [V64 P2-1] CachingManager 분리 — 원고 캐시, 역사 구성, protagonist_config 캐싱
        self._caching = DirectorCachingManager(self.client, self.primary_model, self.context)

        # [V64 P2-1] GradingSystem 분리 — 원고 품질 등급화, 수정 가이드
        self._grading = DirectorGradingSystem()

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
        self,
        arc_pos: int = 1,
        total_eps: int = 5,
        ep_type: str = "normal",
        retry_count: int = 0
    ) -> dict:
        """
        [V60.6] 적응형 PASS 기준선 계산

        Arc 위치, 장르, 에피소드 타입별로 동적 기준 적용.

        Args:
            arc_pos: Arc 내 위치 (1-based)
            total_eps: Arc 내 총 에피소드 수
            ep_type: 에피소드 타입 ("intro", "transition", "climax", "normal")
            retry_count: 재시도 횟수 (많을수록 관대해짐)

        Returns:
            {
                'pass_threshold': int,
                'length_threshold': int,
                'strictness_level': str,
                'reason': str
            }
        """
        if not self.adaptive_thresholds_enabled:
            return {
                'pass_threshold': self.base_pass_threshold,
                'length_threshold': ManuscriptLimits.WARNING_LENGTH,  # [V64.P4]
                'strictness_level': 'standard',
                'reason': 'adaptive thresholds disabled'
            }

        base = self.base_pass_threshold
        length_base = ManuscriptLimits.WARNING_LENGTH  # [V64.P4]
        reason_parts = []

        # 1. Arc 위치 기반 조정
        arc_position_ratio = arc_pos / total_eps if total_eps > 0 else 0.5

        if arc_position_ratio <= 0.2:
            # 도입부 (Arc 첫 1-2화): 관대
            base -= 5
            length_base -= 300
            reason_parts.append("도입부(-5점)")
        elif arc_position_ratio >= 0.8:
            # 절정/결말 (Arc 마지막 1-2화): 엄격
            base += 10
            length_base += 300
            reason_parts.append("절정부(+10점)")
        elif 0.4 <= arc_position_ratio <= 0.6:
            # 중반 전환점: 약간 엄격
            base += 3
            reason_parts.append("전환점(+3점)")

        # 2. 장르별 조정
        if self.genre == 'wuxia':
            # 무협: 액션 밀도 중시
            base += 0  # 기본
        elif self.genre == 'hunter':
            # 헌터: 시스템 일관성 중시
            base += 2
            reason_parts.append("헌터장르(+2점)")
        elif self.genre == 'investment':
            # 투자: 논리성 중시
            base += 3
            reason_parts.append("투자장르(+3점)")
        elif self.genre == 'actor':
            # 배우물: 연기/업계 묘사 중시
            base += 2
            reason_parts.append("배우장르(+2점)")
        elif self.genre == 'sports':
            # 스포츠: 경기/훈련 역동성 중시
            base += 2
            reason_parts.append("스포츠장르(+2점)")
        elif self.genre == 'medical':
            # 의학: 의학 정확성/긴장감 중시
            base += 2
            reason_parts.append("의학장르(+2점)")

        # 3. 에피소드 타입별 조정
        if ep_type == "climax":
            base += 10
            length_base += 500
            reason_parts.append("클라이맥스(+10점)")
        elif ep_type == "intro":
            base -= 5
            length_base -= 200
            reason_parts.append("도입부(-5점)")
        elif ep_type == "transition":
            base -= 3
            reason_parts.append("전환(-3점)")

        # 4. 재시도 횟수별 완화 (너무 엄격하면 무한 루프)
        if retry_count >= 3:
            base -= 10
            reason_parts.append("3+회재시도(-10점)")
        elif retry_count >= 2:
            base -= 5
            reason_parts.append("2회재시도(-5점)")

        # 5. 범위 제한
        base = max(45, min(85, base))
        length_base = max(3500, min(6000, length_base))

        # 엄격도 레벨 결정
        if base >= 75:
            strictness = 'strict'
        elif base >= 60:
            strictness = 'standard'
        else:
            strictness = 'lenient'

        return {
            'pass_threshold': base,
            'length_threshold': length_base,
            'strictness_level': strictness,
            'reason': ', '.join(reason_parts) if reason_parts else 'standard'
        }

    def apply_adaptive_decision(
        self,
        score: int,
        original_decision: str,
        arc_pos: int = 1,
        total_eps: int = 5,
        retry_count: int = 0
    ) -> dict:
        """
        [V60.6] 적응형 기준에 따라 PASS/REJECT 재결정

        Args:
            score: 평가 점수
            original_decision: 원래 결정 ("PASS" or "REJECT")
            arc_pos: Arc 내 위치
            total_eps: Arc 내 총 에피소드 수
            retry_count: 재시도 횟수

        Returns:
            {
                'decision': str,
                'adjusted': bool,
                'threshold_used': int,
                'reason': str
            }
        """
        threshold_info = self.get_adaptive_threshold(
            arc_pos=arc_pos,
            total_eps=total_eps,
            retry_count=retry_count
        )

        threshold = threshold_info['pass_threshold']
        adjusted = False
        new_decision = original_decision

        # 점수 기반 재결정
        if score >= threshold:
            if original_decision == 'REJECT':
                # 기준보다 높은데 REJECT였으면 PASS로 변경 고려
                # (단, 심각한 논리 오류가 아닐 때만)
                new_decision = 'CONDITIONAL_PASS'
                adjusted = True
        else:
            if original_decision == 'PASS':
                # 기준보다 낮은데 PASS였으면 주의 필요
                # REJECT까지는 아니지만 경고
                new_decision = 'CONDITIONAL_PASS'
                adjusted = True

        return {
            'decision': new_decision,
            'adjusted': adjusted,
            'threshold_used': threshold,
            'strictness': threshold_info['strictness_level'],
            'reason': threshold_info['reason']
        }

    def set_genre(self, genre: str):
        """장르 설정 (main_a.py에서 boot 시 호출)"""
        self.genre = genre
        # 기존 orchestrator 리셋 (장르 변경 시 재초기화 필요)
        self.v0128_orchestrator = None

    def set_guard(self, guard):
        """[V60.90] 장르 Guard 설정 (main_a.py에서 호출)"""
        self.guard = guard

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """[V64 P2-7] 위임 → modules.core.hud_utils.build_hud_context (director variant)"""
        return _build_hud_context_shared(state_tracker, ep_num, variant="director")

    def _run_genre_specific_validation(self, manuscript: str, ep_num: int) -> dict:
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor._run_genre_specific_validation(manuscript, ep_num)

    def set_v0128_enabled(self, enabled: bool):
        """V0128 검증 시스템 활성화/비활성화"""
        self.use_v0128 = enabled

    def validate_entity_consistency(self, content: str, entity_registry: dict,
                                     content_type: str = "manuscript") -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.validate_entity_consistency(content, entity_registry, content_type)

    def _format_entity_registry_for_director(self, entity_registry: dict) -> str:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity._format_entity_registry_for_director(entity_registry)

    def compare_and_select_blueprint(self, candidates, arc_data, ep_num, prev_blueprint=None, entity_registry=None, state_tracker=None):
        """[V64] 위임 → DirectorEnsembleSelector"""
        return self._ensemble.compare_and_select_blueprint(candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker)

    def audit_manuscript(self, ep_num, manuscript, arc_doc, history_summary, prev_full_text, arc_pos, total_eps=None, target_len=4500, retry_count=0, validation_context=None, entity_registry=None, manuscript_history=None, state_tracker=None):
        """
        원고 검수 (V0128 통합 + V46 캐릭터 논리 검증 + V61 Entity 일관성 검증 + V60.87 원고 역사 충돌 검사)

        V0128 활성화 시 3-Tier 검증 시스템 사용
        비활성화 시 기존 LLM 기반 검증 사용

        [V61 NEW] entity_registry 파라미터 추가 - Entity 명칭 일관성 최종 검증
        [V60.87 NEW] manuscript_history 파라미터 추가 - 전체 원고 역사 대비 충돌 검사
        [V60.96 NEW] state_tracker 파라미터 추가 - 죽은 NPC 등장 검증
        """
        # ═══════════════════════════════════════════════════════════════
        # [V63.4] Python 사전 검증 → 경고 수집 (최종 판단은 LLM)
        # ═══════════════════════════════════════════════════════════════
        _pre_llm_warnings = []

        # [V60.97] arc_no 추출 (타임라인 비교용)
        # NOTE: main_a.py에서 arc_doc은 보통 string(tactical_doc)으로 전달됨 → dict 분기 거의 미진입
        arc_no = 0
        if arc_doc and isinstance(arc_doc, dict):
            arc_no = arc_doc.get("arc_no", 0)
        elif arc_doc and isinstance(arc_doc, str):
            # [V61.5] string인 경우 "Arc N" 패턴에서 추출 시도
            import re
            arc_match = re.search(r'[Aa]rc\s*(\d+)', arc_doc[:200])
            if arc_match:
                arc_no = int(arc_match.group(1))
        if arc_no <= 0 and arc_pos:
            arc_no = arc_pos  # arc_pos가 있으면 사용

        # [V63.4] 죽은 NPC → LLM 경고로 전달 (기존: 즉시 REJECT)
        if state_tracker:
            dead_npc_violations = state_tracker.check_dead_npc_in_manuscript(manuscript, ep_num, arc_no)
            if dead_npc_violations:
                violation_names = [v["npc_name"] for v in dead_npc_violations]
                print(f"      ⚠️ [V63.4] 죽은 NPC 경고 → LLM 전달: {', '.join(violation_names)}")
                _pre_llm_warnings.append(
                    f"[CRITICAL 경고] 죽은 NPC 등장 의심: {', '.join(violation_names)}\n" +
                    "\n".join(f"  - {v['npc_name']}: Arc {v['death_arc']}에서 사망" for v in dead_npc_violations) +
                    "\n  ※ 회상/과거 언급만 허용. 살아있는 것처럼 대화/행동하면 REJECT 필요."
                )

        # [V63.4] 장르 위반 → LLM 경고로 전달 (기존: 즉시 REJECT)
        if self.genre_validation_enabled and self.guard:
            genre_violations = self._run_genre_specific_validation(manuscript, ep_num)
            if genre_violations.get('has_critical'):
                print(f"      ⚠️ [V63.4] 장르 위반 경고 → LLM 전달: {genre_violations.get('summary', '')}")
                _pre_llm_warnings.append(
                    f"[CRITICAL 경고] 장르 규칙 위반: {genre_violations.get('summary', '')}\n"
                    f"  {genre_violations.get('feedback', '')}"
                )

        # ═══════════════════════════════════════════════════════════════
        # [V60.88] 원고 역사 충돌 검사 - 캐시 우선, 폴백은 기존 방식
        # ═══════════════════════════════════════════════════════════════
        if self.manuscript_history_check_enabled:
            history_check = None

            # [V60.88] 캐시가 있으면 캐시 참조 검사 (전문 비교, 고품질)
            if self._caching.manuscript_cache_name:
                history_check = self.check_manuscript_history_with_cache(
                    ep_num=ep_num,
                    current_manuscript=manuscript
                )
                if history_check.get('cache_used'):
                    print(f"      ⚡ [V60.88] 캐시 참조 충돌 검사 완료")

            # [V63.4 P0] 캐시 없거나 실패 시 기존 방식 폴백 (manuscript_history 사용)
            if not history_check or history_check.get('error') or history_check.get('needs_fallback'):
                if manuscript_history:
                    history_check = self.check_manuscript_history_conflicts(
                        ep_num=ep_num,
                        current_manuscript=manuscript,
                        manuscript_history=manuscript_history,
                        use_summary=True  # 토큰 절약을 위해 요약본 우선 사용
                    )
                elif history_check and history_check.get('needs_fallback'):
                    print(f"      ⚠️ [V63.4] 캐시 폴백 필요하나 manuscript_history 없음 → 검증 스킵")

            if history_check and history_check.get('decision') == 'CONFLICT':
                conflicts = history_check.get('conflicts', [])
                conflict_details = "; ".join([
                    f"[{c.get('type', '?')}] {c.get('prev_fact', '')} vs {c.get('current_violation', '')}"
                    for c in conflicts[:3]  # 최대 3개만 표시
                ])
                return {
                    "decision": "REJECT",
                    "score": 25,
                    "error_category": "LOGIC_ERROR",
                    "diagnostic_report": f"원고 역사 충돌 {len(conflicts)}건 발견",
                    "current_beat_achieved": False,
                    "reason": f"이전 원고와 충돌: {conflict_details}",
                    "feedback": f"[V60.88] 이전 원고에서 확립된 사실과 모순됨. {history_check.get('summary', '')}",
                    "v60_87_history_check": history_check
                }
            elif history_check and history_check.get('conflicts'):
                # 경고만 있는 경우 validation_context에 기록
                if validation_context is None:
                    validation_context = {}
                validation_context['v60_87_history_warnings'] = history_check.get('conflicts', [])

        # ═══════════════════════════════════════════════════════════════
        # [V60.89] 주인공 설정 준수 검증 (protagonist_config)
        # ═══════════════════════════════════════════════════════════════
        if self.protagonist_config_check_enabled:
            config_check = self.validate_protagonist_config_compliance(
                manuscript=manuscript,
                ep_num=ep_num
            )

            # [V63.4] Python REJECT → LLM 경고로 전달 (기존: 즉시 REJECT)
            if config_check.get('decision') == 'REJECT':
                violations = config_check.get('violations', [])
                print(f"      ⚠️ [V63.4] 주인공 설정 위반 경고 → LLM 전달: {len(violations)}건")
                _pre_llm_warnings.append(
                    f"[CRITICAL 경고] 주인공 설정 위반 {len(violations)}건\n"
                    f"  {config_check.get('feedback', '주인공 설정 위반')}"
                )
            elif config_check.get('decision') == 'WARNING':
                # WARNING은 기록만 하고 계속 진행
                if validation_context is None:
                    validation_context = {}
                validation_context['v60_89_config_warnings'] = config_check.get('violations', [])
                print(f"      ⚠️ [V60.89] 주인공 설정 경고: {len(config_check.get('violations', []))}건")

        # ═══════════════════════════════════════════════════════════════
        # [V61] Entity 일관성 검증 - Director의 최종 방어선
        # ═══════════════════════════════════════════════════════════════
        if entity_registry and self.entity_consistency_enabled:
            entity_check = self.validate_entity_consistency(
                content=manuscript,
                entity_registry=entity_registry,
                content_type="manuscript"
            )
            if entity_check.get('decision') == 'REJECT':
                mismatches = entity_check.get('mismatches', [])
                return {
                    "decision": "REJECT",
                    "score": 40,
                    "error_category": "LOGIC_ERROR",
                    "diagnostic_report": f"Entity 명칭 불일치 {len(mismatches)}건 발견",
                    "current_beat_achieved": False,
                    "reason": entity_check.get('fix_instructions', 'Entity 명칭을 통일하세요'),
                    "feedback": f"[V61] Entity 일관성 오류: {entity_check.get('fix_instructions', '')}",
                    "v61_entity_check": entity_check
                }
            elif entity_check.get('decision') == 'WARNING':
                # WARNING은 경고만 하고 계속 진행, 결과에 포함
                if validation_context is None:
                    validation_context = {}
                validation_context['v61_entity_warnings'] = entity_check.get('mismatches', [])
        # [V46] 캐릭터 논리성 검증 (assess_character_logic 활성화)
        if validation_context:
            npc_profiles = validation_context.get('npc_profiles', {})
            character_traits = validation_context.get('character_traits', {})

            # NPC 정보가 있을 때만 캐릭터 논리 검증 수행
            if npc_profiles or character_traits:
                char_logic_result = self.assess_character_logic(
                    ep_num=ep_num,
                    manuscript=manuscript,
                    npc_profiles=npc_profiles,
                    character_traits=character_traits
                )

                # [FIX] CRITICAL 1개 또는 MAJOR 2개 이상일 때만 REJECT (주석과 코드 일치)
                if char_logic_result.get('decision') == 'REJECT':
                    severity = char_logic_result.get('severity', 'NONE')
                    violations = char_logic_result.get('violations', [])
                    major_count = sum(1 for v in violations if isinstance(v, dict) and v.get('severity') == 'MAJOR')

                    # CRITICAL은 1개라도 REJECT, MAJOR는 2개 이상일 때만 REJECT
                    should_reject = (severity == 'CRITICAL') or (severity == 'MAJOR' and major_count >= 2)

                    if should_reject:
                        print(f"      🚨 [V46] 캐릭터 논리 위반 감지 ({severity}, MAJOR {major_count}개)")
                        return {
                            "decision": "REJECT",
                            "score": char_logic_result.get('score', 30),
                            "error_category": "LOGIC_ERROR",
                            "diagnostic_report": f"캐릭터 논리 위반: {violations}",
                            "current_beat_achieved": False,
                            "reason": char_logic_result.get('feedback', '캐릭터 행동이 설정과 불일치'),
                            "feedback": char_logic_result.get('feedback', ''),
                            "v46_character_logic": char_logic_result
                        }
                    else:
                        # MAJOR 1개 또는 MINOR는 경고만 하고 계속 진행
                        print(f"      ⚠️ [V46] 캐릭터 논리 이슈 ({severity}, MAJOR {major_count}개) - 계속 진행")

        # ═══════════════════════════════════════════════════════════════
        # [V60] Blueprint 완전성 검증 - main_a.py에서 사전 검증하므로 여기서는 스킵
        # [V60.1 FIX] 중복 검증 제거 - main_a.py에서 이미 검증 완료
        # ═══════════════════════════════════════════════════════════════
        # Note: validation_context.get('bp_completeness_done', False)가 True면 이미 검증됨
        # main_a.py에서 _validate_blueprint_completeness_v60()을 먼저 호출하므로 여기서 재검증하지 않음

        # [V63.4] Python 경고를 validation_context에 주입 (V0128 경로 포함)
        if _pre_llm_warnings:
            if validation_context is None:
                validation_context = {}
            validation_context['pre_llm_critical_warnings'] = (
                "\n\n[⚠️ Python 사전 검증 경고 — 문맥 확인 후 최종 판단 필요]\n"
                + "\n---\n".join(_pre_llm_warnings)
            )

        # [V43] V0128 검증 시스템 조건부 사용
        if self.use_v0128 and validation_context:
            return self._audit_with_v0128(
                ep_num=ep_num,
                manuscript=manuscript,
                validation_context=validation_context,
                target_len=target_len
            )

        # 1. 검수 모드 자동 결정 (기존 로직)
        audit_mode = "BLUEPRINT" if target_len <= ManuscriptLimits.MIN_LENGTH else "MANUSCRIPT"  # [V64.P4]

        # 2. 데이터 안전 처리
        safe_ms = self._escape_braces(manuscript)
        safe_arc = self._escape_braces(arc_doc)
        safe_history = self._escape_braces(history_summary)
        safe_prev = self._escape_braces(prev_full_text) # 👈 수혈 준비
        current_len = len(manuscript)

        # 2-1. 🔒 [V40 Fix] 분량 강제 체크 (AI 판단 이전에 Python 레벨에서 검증)
        if audit_mode == "MANUSCRIPT" and current_len < ManuscriptLimits.MIN_LENGTH:  # [V64.P4]
            return {
                "decision": "REJECT",
                "score": 0,
                "error_category": "QUALITY_ISSUE",
                "diagnostic_report": f"분량 절대 미달: {current_len}자",
                "current_beat_achieved": False,
                "reason": f"공백 포함 {current_len}자로 최소 기준({ManuscriptLimits.MIN_LENGTH}자) 미달. 목표는 {ManuscriptLimits.TARGET_LENGTH}자 이상입니다.",
                "feedback": f"장면의 밀도를 높이고, 대사와 묘사를 추가하여 {ManuscriptLimits.TARGET_LENGTH}자 이상으로 확장하십시오."
            }

        # 2-2. 🚫 [V40 Premium] 반복 구문 체크 (N-gram Deduplication)
        repetition_check_passed = True
        try:
            from modules.core.repetition_guard import RepetitionGuard

            # RepetitionGuard 초기화
            guard = RepetitionGuard(window_size=5, threshold=3)

            # 이전 5화 원고 수집
            prev_manuscripts = []
            for i in range(max(1, ep_num-5), ep_num):
                try:
                    ms = self.context.db.get_manuscript(i)
                    if ms and 'content' in ms:
                        prev_manuscripts.append(ms['content'])
                except Exception as ms_err:
                    # DB 조회 실패는 무시 (원고 없을 수 있음)
                    pass

            # 금지 구문 목록 구축
            if prev_manuscripts:
                banned_phrases = guard.build_banned_list(prev_manuscripts)

                # 현재 원고 스캔
                violations, clean_score = guard.scan_manuscript(manuscript)

                # 위반 발견 시 REJECT (클린 점수 85% 미만)
                if clean_score < 0.85:
                    correction_prompt = guard.generate_correction_prompt(violations)

                    return {
                        "decision": "REJECT",
                        "score": int(clean_score * 100),
                        "error_category": "QUALITY_ISSUE",
                        "diagnostic_report": f"반복 구문 과다 사용 ({len(violations)}개 발견)",
                        "current_beat_achieved": True,  # 내용은 맞지만 표현이 문제
                        "reason": f"최근 5화에서 반복 사용된 구문 {len(violations)}개 발견 (클린 점수: {clean_score:.0%}). 어휘 다양성 확보 필요.",
                        "feedback": correction_prompt
                    }
        except ImportError as ie:
            print(f"      ⚠️ [Director] RepetitionGuard 모듈 로드 실패: {ie}")
            repetition_check_passed = False
        except AttributeError as ae:
            print(f"      ⚠️ [Director] DB 컨텍스트 오류 (RepetitionGuard): {ae}")
            repetition_check_passed = False
        except Exception as e:
            print(f"      ⚠️ [Director] RepetitionGuard 실행 중 예상치 못한 오류: {type(e).__name__}: {e}")
            repetition_check_passed = False

        # 3. [V60.95] 고밀도 HUD 컨텍스트 구축
        high_density_hud = self._build_hud_context(state_tracker, ep_num)
        safe_hud = self._escape_braces(high_density_hud)

        # 4. 프롬프트 조립 (모든 데이터 유실 없이 매핑)
        prompt = DIRECTOR_AUDIT_PROMPT_V30.format(
            ep_num=ep_num,
            audit_mode=audit_mode,
            total_eps=total_eps if total_eps else "미정",
            arc_pos=arc_pos,
            arc_doc=safe_arc,
            current_len=current_len,
            target_len=target_len,
            history_summary=safe_history,
            prev_full_text=safe_prev, # 👈 뚫려있던 구멍을 메움
            manuscript=safe_ms,
            retry_count=retry_count,  # [V40.3 추가] 재시도 횟수 전달
            high_density_hud_context=safe_hud  # [V60.95] 고밀도 HUD 주입
        )

        # [V63.4] Python 사전 경고를 LLM 프롬프트에 주입
        if _pre_llm_warnings:
            _warning_block = "\n\n[⚠️ Python 사전 검증 경고 — 문맥 확인 후 최종 판단 필요]\n" + "\n---\n".join(_pre_llm_warnings)
            prompt += self._escape_braces(_warning_block)

        response = self.ask(prompt, temperature=0.1, thinking_level="high")  # [V61.6] 원고 PASS/REJECT
        return self._extract_json_robust(response)


    def audit_strategic_plan(self, arc_plan, prev_arc_context, curr_block=None, protagonist_name=None, suspected_duplicates=None, entity_registry=None):
        """
        [Stage 2] Analyst의 아크 설계안에 대한 전략적 무결성 검수 (루프/미래 오염 방지)

        [V49.3] Self-Consistency 투표 적용:
        - 1차 평가 후 애매한 결과면 추가 평가 진행
        - 중앙값 + 다수결로 최종 결정

        [V60.76] suspected_duplicates: Python이 의심하는 중복 아이템 목록 (LLM 재검증용)
        [V61 NEW] entity_registry: Entity 명칭 일관성 검증용 레지스트리
        """
        arc_no = arc_plan.get("arc_no")
        arc_dump = json.dumps(arc_plan, ensure_ascii=False)

        # ═══════════════════════════════════════════════════════════════
        # [V61] Entity 일관성 검증 - Director의 최종 방어선
        # ═══════════════════════════════════════════════════════════════
        if entity_registry and self.entity_consistency_enabled:
            tactical_doc = arc_plan.get('tactical_doc', '')
            entity_check = self.validate_entity_consistency(
                content=tactical_doc,
                entity_registry=entity_registry,
                content_type="arc"
            )
            if entity_check.get('decision') == 'REJECT':
                mismatches = entity_check.get('mismatches', [])
                return {
                    "decision": "REJECT",
                    "score": 40,
                    "loop_detected": False,
                    "reason": f"[V61] Entity 명칭 불일치 {len(mismatches)}건 발견",
                    "re_slice_instruction": entity_check.get('fix_instructions', 'Entity 명칭을 통일하세요'),
                    "v61_entity_check": entity_check
                }

        # 🔒 [V42 Hard Guard] 주인공 이름 일관성 검증
        if protagonist_name and len(protagonist_name) >= 2:
            # [V60.55 DEBUG] 주인공 이름 검색 디버깅
            tactical_doc = arc_plan.get('tactical_doc', '')
            name_in_tactical = protagonist_name in tactical_doc
            name_in_dump = protagonist_name in arc_dump
            print(f"      🔍 [V60.55 DEBUG] 주인공 이름 검증: '{protagonist_name}'")
            print(f"         - tactical_doc 내 존재: {name_in_tactical}")
            print(f"         - arc_dump 내 존재: {name_in_dump}")
            print(f"         - tactical_doc 앞 200자: {tactical_doc[:200]}...")

            if not name_in_dump:
                print(f"      🚨 [V60.55] 주인공 이름 '{protagonist_name}' 미발견 → REJECT")
                return {
                    "decision": "REJECT",
                    "score": 0,
                    "loop_detected": False,
                    "reason": f"주인공 이름 '{protagonist_name}' 누락 감지 - 서사 무결성 파괴",
                    "re_slice_instruction": f"모든 주인공 서술에서 '{protagonist_name}'을 명시적으로 사용하라. 유사 명칭이나 다른 인물 이름으로 대체 금지."
                }
            else:
                print(f"      ✅ [V60.55] 주인공 이름 '{protagonist_name}' 확인됨")

        # 🔒 [Hard Guard] 미래 무구 조기 노출 차단 (V43: Bible 기반 동적 검증)
        # 특정 아이템 하드코딩 제거 - Bible의 'future_items' 또는 블록별 보상 데이터로 검증
        # 이 검증은 BlockingValidator의 unowned_item_usage 체크로 대체됨
        pass

        # 데이터 안전화 처리
        safe_tactical = self._escape_braces(arc_plan.get('tactical_doc', ''))
        safe_beats = self._escape_braces(str(arc_plan.get('beat_sequence', [])))
        safe_prev = self._escape_braces(prev_arc_context)
        safe_curr = self._escape_braces(json.dumps(curr_block, ensure_ascii=False)) if curr_block else "없음"

        # [V60.76] Python 의심 아이템 포맷팅
        if suspected_duplicates:
            safe_suspected = "\n".join([f"- {item}" for item in suspected_duplicates])
        else:
            safe_suspected = "(없음 - Python 검사 통과)"

        prompt = STRATEGIC_AUDIT_PROMPT_V30.format(
            arc_no=arc_plan.get('arc_no', '?'),
            ep_count=arc_plan.get('ep_count', 0),
            ep_start=arc_plan.get('ep_start', 0),
            ep_end=arc_plan.get('ep_end', 0),
            beat_sequence=safe_beats,
            tactical_doc=safe_tactical,
            prev_context=safe_prev,
            curr_block=safe_curr,
            suspected_duplicates=safe_suspected
        )

        # [V49.3] Self-Consistency 적용
        if self.use_self_consistency:
            return self._strategic_audit_with_self_consistency(prompt, arc_no)
        else:
            response = self.ask(prompt, temperature=0.1, thinking_level="medium")  # [V61.6] Arc 감사
            return self._extract_json_robust(response)

    def _strategic_audit_with_self_consistency(self, prompt: str, arc_no: int) -> dict:
        """
        [V49.3] 전략 감사에 Self-Consistency 투표 적용

        Stage 2/3에서 Director가 LLM 단일 호출의 환각을 방지하기 위해:
        1. 1차 평가 실행
        2. 결과가 애매하면 (PASS이지만 score가 낮거나 경고 포함) 추가 2회 평가
        3. 다수결로 최종 PASS/REJECT 결정

        Returns:
            dict: 감사 결과 (self_consistency 정보 포함)
        """
        # 1차 평가
        response = self.ask(prompt, temperature=0.1, thinking_level="medium")  # [V61.6] SC 1차
        first_eval = self._extract_json_robust(response)

        if not isinstance(first_eval, dict):
            first_eval = {"decision": "REJECT", "score": 0, "reason": "JSON 파싱 실패"}

        first_decision = first_eval.get('decision', 'REJECT')
        first_score = first_eval.get('score', 50)

        # 명확한 REJECT → 추가 평가 없이 반환
        if first_decision == 'REJECT' and first_score < self.ambiguous_lower:
            reject_reason = first_eval.get('reason', first_eval.get('re_slice_instruction', '사유 미상'))
            print(f"         🎬 [Director] REJECT (score={first_score})")
            print(f"            └─ 사유: {reject_reason[:80]}{'...' if len(str(reject_reason)) > 80 else ''}")
            first_eval['self_consistency'] = {
                'votes': 1,
                'reason': 'clear_reject',
                'pass_votes': 0
            }
            return first_eval

        # 명확한 PASS (점수가 높음) → 추가 평가 없이 반환
        if first_decision == 'PASS' and first_score > self.ambiguous_upper:
            pass_reason = first_eval.get('reason', first_eval.get('strengths', '판단 근거 미상'))
            print(f"         🎬 [Director] PASS (score={first_score})")
            print(f"            └─ 근거: {str(pass_reason)[:80]}{'...' if len(str(pass_reason)) > 80 else ''}")
            first_eval['self_consistency'] = {
                'votes': 1,
                'reason': 'clear_pass',
                'pass_votes': 1
            }
            return first_eval

        # 애매한 구간 → 추가 평가 진행
        print(f"         ⚖️ [V49.3] 애매한 결과({first_decision}, score={first_score}) → Self-Consistency 활성화")

        evaluations = [first_eval]

        # [V60.68] Self-Consistency 병렬화
        # [V61.3] 타임아웃 임포트 추가
        from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError

        # [V61.3] 타임아웃 상수
        VOTE_ENSEMBLE_TIMEOUT = 150  # 전체 투표 타임아웃 (초) - thinking 오버헤드 반영
        SINGLE_VOTE_TIMEOUT = 90     # 개별 투표 타임아웃 (초)

        def _vote_task(vote_idx, temp):
            """단일 투표 작업"""
            response = self.ask(prompt, temperature=temp, thinking_level="low")  # [V61.6] SC 추가투표
            return vote_idx, self._extract_json_robust(response)

        vote_tasks = [(i, 0.1 + (i * 0.05)) for i in range(1, self.consistency_votes)]

        with ThreadPoolExecutor(max_workers=min(3, len(vote_tasks))) as executor:
            futures = {executor.submit(_vote_task, idx, temp): idx for idx, temp in vote_tasks}

            # [V61.3] 타임아웃 적용 - 야간 무인 운영 시 무한 대기 방지
            try:
                for future in as_completed(futures, timeout=VOTE_ENSEMBLE_TIMEOUT):
                    try:
                        vote_idx, eval_result = future.result(timeout=SINGLE_VOTE_TIMEOUT)
                        if isinstance(eval_result, dict):
                            evaluations.append(eval_result)
                            eval_decision = eval_result.get('decision', 'REJECT')
                            eval_score = eval_result.get('score', 0)
                            print(f"            Vote {vote_idx+1}: {eval_decision} (score={eval_score})")
                    except FutureTimeoutError:
                        print(f"            ⏰ [V61.3] Vote 타임아웃")
                    except Exception as e:
                        print(f"            ⚠️ Vote 오류: {str(e)[:50]}")
            except FutureTimeoutError:
                print(f"         ⏰ [V61.3] Self-Consistency 전체 타임아웃 - 완료된 {len(evaluations)}개 투표 사용")

        # 점수들의 중앙값
        scores = [e.get('score', 50) for e in evaluations if isinstance(e, dict)]
        median_score = statistics.median(scores) if scores else 50

        # PASS/REJECT 다수결
        pass_votes = sum(1 for e in evaluations if e.get('decision') == 'PASS')
        final_decision = 'PASS' if pass_votes > (len(evaluations) // 2) else 'REJECT'

        # 대표 결과 선택 (중앙값에 가장 가까운 것)
        representative = min(evaluations, key=lambda e: abs(e.get('score', 50) - median_score))

        # 결과 병합
        result = representative.copy()
        result['decision'] = final_decision
        result['score'] = median_score
        result['self_consistency'] = {
            'votes': len(evaluations),
            'pass_votes': pass_votes,
            'scores': scores,
            'median_score': median_score,
            'reason': f'ambiguous_result ({first_decision}, score={first_score})'
        }

        print(f"         ✅ [V49.3] Self-Consistency 완료: {final_decision} (PASS {pass_votes}/{len(evaluations)}, median={median_score})")

        return result    

    # [V63.4 P1] audit_timeline_logic() 삭제 — Dead Code (코드베이스 전체에서 미호출)

    # =================================================================
    # ═══════════════════════════════════════════════════════════════
    # [V60] Blueprint 완전성 검증
    # ═══════════════════════════════════════════════════════════════

    def _validate_blueprint_completeness_v60(self, manuscript: str, blueprint: dict) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity._validate_blueprint_completeness_v60(manuscript, blueprint)

    # [V0128] 3-Tier Validation System
    # =================================================================

    def _audit_with_v0128(self, ep_num, manuscript, validation_context, target_len=4500):
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor._audit_with_v0128(ep_num, manuscript, validation_context, target_len)

    def audit_manuscript_v0128(self, ep_num, manuscript, validation_context, config=None, genre='wuxia'):
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor.audit_manuscript_v0128(ep_num, manuscript, validation_context, config, genre)


    def assess_character_logic(self, ep_num, manuscript, npc_profiles, character_traits):
        """[V64] 위임 → DirectorQualityAuditor"""
        return self._auditor.assess_character_logic(ep_num, manuscript, npc_profiles, character_traits)

    def on_approve_workflow(self, ep_num, state_updates, current_hud, martial_manager=None):
        """
        [V41 Director Sovereignty] 상태 업데이트 검증 및 적용

        Writer가 제안한 state_updates를 검증하고, 승인된 항목만 반환합니다.

        Args:
            ep_num: 에피소드 번호
            state_updates: Writer가 제안한 상태 변화 dict
            current_hud: 현재 HUD 상태 dict
            martial_manager: MartialManager 인스턴스 (선택적)

        Returns:
            dict: {
                "approved": True/False,
                "applied_updates": {...},  # 실제 적용할 업데이트
                "rejected_updates": {...}, # 거부된 업데이트 (이유 포함)
                "warnings": [...]          # 경고 메시지
            }
        """
        if not state_updates or not isinstance(state_updates, dict):
            return {
                "approved": True,
                "applied_updates": {},
                "rejected_updates": {},
                "warnings": ["Writer가 state_updates를 제출하지 않음 - 상태 변경 없음"]
            }

        applied = {}
        rejected = {}
        warnings = []

        # 검증 규칙 정의
        LIMITS = {
            "internal_energy": {"max_increase": 200, "max_decrease": -500},
            "misunderstanding": {"max_change": 30},
            "obsession": {"max_change": 30},
            "wealth": {"max_change": 10000}
        }

        for key, value in state_updates.items():
            # "현상 유지" 처리
            if value in ["현상 유지", "유지", "변화 없음", None, ""]:
                continue

            # 수치 변화 파싱 시도
            if isinstance(value, str) and (value.startswith("+") or value.startswith("-")):
                try:
                    # [V44 Fix] 정규식으로 안전한 숫자 추출 ("+100" → 100, "-50냥" → -50)
                    import re
                    numeric_match = re.match(r'^([+-]?\d+)', value)
                    if numeric_match:
                        change = int(numeric_match.group(1))

                        # 범위 검증
                        if key in LIMITS:
                            limits = LIMITS[key]
                            if "max_increase" in limits and change > limits["max_increase"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"증가량 초과 (최대 +{limits['max_increase']})"
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 비합리적 증가량")
                                continue
                            if "max_decrease" in limits and change < limits["max_decrease"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"감소량 초과 (최대 {limits['max_decrease']})"
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 비합리적 감소량")
                                continue
                            if "max_change" in limits and abs(change) > limits["max_change"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"변화량 초과 (최대 ±{limits['max_change']})"
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 변화량 초과")
                                continue
                except ValueError:
                    pass  # 숫자가 아닌 경우 그대로 진행

            # 경지(realm) 변화 검증 - 한 단계 이상 점프 시 경고
            if key == "realm" and current_hud:
                current_realm = current_hud.get("realm", "")
                if value != current_realm:
                    # 경지 변화는 허용하되 경고 기록
                    warnings.append(f"[INFO] 경지 변화 감지: {current_realm} → {value}")

            # 부상(causal_injuries) 검증 - 회복 시 경고
            if key == "causal_injuries" and current_hud:
                current_injury = current_hud.get("causal_injuries", "")
                if current_injury and "중상" in str(current_injury) and "정상" in str(value):
                    warnings.append(f"[WARN] 부상 급회복: {current_injury} → {value} (서사적 근거 필요)")

            # 승인된 업데이트 추가
            applied[key] = value

        # 최종 결과 구성
        is_approved = len(rejected) == 0 or len(applied) > 0

        return {
            "approved": is_approved,
            "applied_updates": applied,
            "rejected_updates": rejected,
            "warnings": warnings
        }

    # =================================================================
    # [V59] 품질 등급화 시스템 (A/B/C Grade)
    # =================================================================

    # [V64 P2-1] GradingSystem 위임 — 등급 관련 상수/메서드는 DirectorGradingSystem으로 이관
    QUALITY_GRADES = DirectorGradingSystem.QUALITY_GRADES
    QUALITY_WEIGHTS = DirectorGradingSystem.QUALITY_WEIGHTS

    def grade_manuscript_v59(self, ep_num: int, manuscript: str, validation_result: dict) -> dict:
        """[V64] 위임 → DirectorGradingSystem"""
        return self._grading.grade_manuscript_v59(ep_num, manuscript, validation_result)

    def generate_revision_guide_v59(self, grade: str, item_scores: dict,
                                     weaknesses: list, validation_result: dict) -> dict:
        """[V64] 위임 → DirectorGradingSystem"""
        return self._grading.generate_revision_guide_v59(grade, item_scores, weaknesses, validation_result)

    def format_revision_report_v59(self, grade_result: dict) -> str:
        """[V64] 위임 → DirectorGradingSystem"""
        return self._grading.format_revision_report_v59(grade_result)

    # [V64 P2-1] EnsembleSelector 위임 — ENSEMBLE_SELECTION_PROMPT는 director_ensemble.py로 이관
    ENSEMBLE_SELECTION_PROMPT = _ENSEMBLE_PROMPT

    def select_and_judge_ensemble(self, ep_num, candidates, validation_results, blueprint, previous_ending,
                                   arc_pos=1, total_eps=5, retry_count=0, episode_digest=""):
        """[V64] 위임 → DirectorEnsembleSelector"""
        return self._ensemble.select_and_judge_ensemble(
            ep_num, candidates, validation_results, blueprint, previous_ending,
            arc_pos, total_eps, retry_count, episode_digest
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
        use_summary: bool = True
    ) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.check_manuscript_history_conflicts(ep_num, current_manuscript, manuscript_history, use_summary)

    def build_manuscript_history_for_check(self, db_manager, ep_num: int) -> list:
        """[V64] 위임 → DirectorCachingManager"""
        return self._caching.build_manuscript_history_for_check(db_manager, ep_num)

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.88] 원고 컨텍스트 캐싱 (Manuscript Context Caching)
    # ═══════════════════════════════════════════════════════════════════════

    def create_manuscript_cache(self, db_manager, current_ep: int, ttl_seconds: int = 3600) -> str:
        """[V64] 위임 → DirectorCachingManager"""
        return self._caching.create_manuscript_cache(db_manager, current_ep, ttl_seconds)

    def check_manuscript_history_with_cache(
        self,
        ep_num: int,
        current_manuscript: str
    ) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.check_manuscript_history_with_cache(ep_num, current_manuscript)

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.89] 주인공 설정 준수 검증 (Protagonist Config Compliance)
    # ═══════════════════════════════════════════════════════════════════════

    def _get_protagonist_config(self) -> dict:
        """[V64] 위임 → DirectorCachingManager"""
        return self._caching.get_protagonist_config()

    def validate_protagonist_config_compliance(
        self,
        manuscript: str,
        ep_num: int = 0
    ) -> dict:
        """
        [V60.89] 원고가 protagonist_config 설정을 준수하는지 검증

        검증 항목:
        1. world_origin == '원시인': 현대 용어 사용 여부 (CRITICAL)
        2. world_origin == '현대인': 검증 없음 (제약 없음)
        3. incarnation_type == '회귀자': 미래 지식 직접 노출 여부 (WARNING)
        4. incarnation_type == '빙의자': 검증 없음 (인지 목적)
        5. incarnation_type == '환생자': 검증 없음 (인지 목적)

        Returns:
            {
                "decision": "PASS" | "WARNING" | "REJECT",
                "violations": [...],
                "feedback": "..."
            }
        """
        if not self.protagonist_config_check_enabled:
            return {"decision": "PASS", "violations": [], "feedback": ""}

        config = self._caching.get_protagonist_config()
        if not config:
            return {"decision": "PASS", "violations": [], "feedback": "설정 없음"}

        world_origin = config.get('world_origin', '현대인')  # [V61.5] 기본값: 느슨한 모드 (기존 '원시인' → '현대인')
        incarnation_type = config.get('incarnation_type', '기타')  # [V61.5] 기본값: 느슨한 모드 (기존 '회귀자' → '기타')

        # [V60.96] 장르 추출 (장르별 금지어 적용)
        genre = self.genre  # [V61.5] self.genre 사용 (기존 "wuxia" 하드코딩 버그 수정)
        try:
            if hasattr(self.context, 'db'):
                bible = self.context.db.load_anchor('bible')
                if bible:
                    genre = bible.get('_genre', self.genre)
        except (AttributeError, KeyError, TypeError):  # [V64.P4] IMPORTANT: genre extraction with safe default
            pass

        violations = []
        decision = "PASS"

        # ═══════════════════════════════════════════════════════════════
        # 1. 원시인 모드: 현대 용어 검사 (CRITICAL - REJECT)
        # [V60.96] 장르별 JSON 기반 PrimitiveGuard 사용
        # ═══════════════════════════════════════════════════════════════
        if world_origin == '원시인':
            if PRIMITIVE_GUARD_AVAILABLE:
                # 장르별 JSON 기반 검증 (primitive_forbidden.json)
                guard = get_primitive_guard()
                prim_decision, prim_violations = guard.validate(manuscript, genre)
                violations.extend(prim_violations)
                if prim_decision == "REJECT":
                    decision = "REJECT"
            else:
                # 폴백: 기본 패턴만 검사
                import re
                fallback_patterns = [
                    (r'헬스장|바벨|덤벨', '현대 운동기구'),
                    (r'시스템|프로세스|알고리즘', '현대 개념어'),
                    (r'병원|학교|은행', '현대 시설'),
                ]
                for pattern, category in fallback_patterns:
                    matches = re.findall(pattern, manuscript, re.IGNORECASE)
                    if matches:
                        violations.append({
                            "type": "MODERN_TERM",
                            "severity": "CRITICAL",
                            "category": category,
                            "found": list(set(matches))[:5],
                            "message": f"[원시인 모드] {category} 사용 금지: {matches[:3]}"
                        })
                        decision = "REJECT"

        # ═══════════════════════════════════════════════════════════════
        # 2. 회귀자 모드: 미래 지식 직접 노출 검사 (WARNING)
        # ═══════════════════════════════════════════════════════════════
        if incarnation_type == '회귀자':
            # 미래 예언 패턴 (직접적 스포일러)
            future_spoiler_patterns = [
                (r'(곧|머지않아|얼마 후면?)\s*.{0,20}(죽|망|멸|패)', '미래 예언'),
                (r'(전생|회귀)\s*[에의]서?\s*(알|봤|경험)', '직접적 회귀 언급'),
                (r'미래[에서의]?\s*.{0,10}(기억|지식)', '미래 지식 직접 언급'),
            ]

            import re
            for pattern, category in future_spoiler_patterns:
                matches = re.findall(pattern, manuscript)
                if matches:
                    # 내면 독백인지 확인 (작은따옴표, '~라고 생각했다' 등)
                    # 여기서는 단순 경고만 (합리적 이유 허용)
                    violations.append({
                        "type": "FUTURE_KNOWLEDGE",
                        "severity": "WARNING",
                        "category": category,
                        "found": [str(m) for m in matches[:3]],
                        "message": f"[회귀자] {category} 감지 - 합리적 이유 확인 필요"
                    })
                    if decision == "PASS":
                        decision = "WARNING"

        # 피드백 생성
        feedback = ""
        if violations:
            critical_violations = [v for v in violations if v.get('severity') == 'CRITICAL']
            warning_violations = [v for v in violations if v.get('severity') == 'WARNING']

            if critical_violations:
                feedback = f"[V60.89 CRITICAL] 주인공 설정 위반 {len(critical_violations)}건:\n"
                for v in critical_violations[:3]:
                    feedback += f"  - {v.get('message', '')}\n"

            if warning_violations:
                feedback += f"[V60.89 WARNING] 확인 필요 {len(warning_violations)}건:\n"
                for v in warning_violations[:2]:
                    feedback += f"  - {v.get('message', '')}\n"

        return {
            "decision": decision,
            "violations": violations,
            "feedback": feedback,
            "world_origin": world_origin,
            "incarnation_type": incarnation_type
        }

    def check_blueprint_continuity_with_cache(
        self,
        new_blueprint: dict,
        ep_num: int,
        db=None,
        limit: int = 10
    ) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.check_blueprint_continuity_with_cache(new_blueprint, ep_num, db, limit)

    def check_manuscript_continuity_with_cache(
        self,
        new_manuscript: str,
        ep_num: int,
        db=None,
        limit: int = 10
    ) -> dict:
        """[V64] 위임 → DirectorContinuityValidator"""
        return self._continuity.check_manuscript_continuity_with_cache(new_manuscript, ep_num, db, limit)

