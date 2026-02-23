"""
[V64 P2-1] Director QualityAuditor — 품질 검증 전담 모듈
[V65 C-5] audit_manuscript, audit_strategic_plan, validate_protagonist_config_compliance 이관

Director God Object 분해의 다섯 번째 단계.
장르 검증, 캐릭터 논리 검증, V0128 3-Tier 검증 시스템,
원고 검수(audit_manuscript), 전략 감사(audit_strategic_plan),
주인공 설정 검증(validate_protagonist_config_compliance) 담당.
"""

import json
import logging
import re
import statistics
import time

from modules.core.constants import ManuscriptLimits
from modules.core.prompt_loader import PromptLoader
from modules.validation.threshold_helper import _threshold
from modules.validation.validation_orchestrator import ValidationOrchestrator

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_guard

    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


class DirectorQualityAuditor:
    """
    [V64 P2-1] Director에서 분리된 품질 검증 모듈
    [V65 C-5] audit_manuscript, audit_strategic_plan 등 4개 메서드 이관

    담당:
    - _run_genre_specific_validation(): 장르별 특화 검증 (Python)
    - assess_character_logic(): 캐릭터 논리성 적대적 검증 (LLM)
    - _audit_with_v0128(): V0128 검증 시스템 내부 헬퍼
    - audit_manuscript_v0128(): V0128 3-Tier 검증 시스템 원고 검수
    - audit_manuscript(): 원고 검수 총괄 (V0128 통합 + 캐릭터 논리 + Entity 일관성) [V65 C-5]
    - audit_strategic_plan(): Stage 2 전략적 무결성 검수 [V65 C-5]
    - _strategic_audit_with_self_consistency(): Self-Consistency 투표 전략 감사 [V65 C-5]
    - validate_protagonist_config_compliance(): 주인공 설정 준수 검증 [V65 C-5]
    """

    def __init__(self, director) -> None:
        """
        Args:
            director: Director 인스턴스 (BaseAgent 메서드 + 설정 접근용)
        """
        self._d = director
        self._prompt_loader = PromptLoader()

        # [V0128] Lazy initialization
        self.v0128_orchestrator = None

    def _run_genre_specific_validation(self, manuscript: str, ep_num: int) -> dict:
        """
        [V66] 장르별 특화 검증 실행 — Guard 다형성 단일 호출.
        기존 if/elif 체인 → guard.run_deep_validation() 위임.

        Returns:
            {
                'has_critical': bool,
                'violations': list,
                'summary': str,
                'feedback': str
            }
        """
        if not self._d.guard:
            return {"has_critical": False, "violations": [], "summary": "", "feedback": ""}

        try:
            # [V66] 다형성 진입: 각 Guard가 자체 override에서 장르별 검증 수행
            current_state = {}
            if hasattr(self._d, "context") and self._d.context:
                try:
                    current_state = getattr(self._d.context, "actual_truth", {}) or {}
                except Exception:
                    pass

            result = self._d.guard.run_deep_validation(manuscript, current_state)

            genre_name = self._d.guard.get_genre_name() if hasattr(self._d.guard, "get_genre_name") else self._d.genre
            v_count = len(result.get("violations", []))
            logging.warning(f"🔍 [V66] {genre_name} Guard 심층 검증: {v_count}개 이슈")

            return result

        except (ValueError, KeyError, IndexError) as e:
            logging.warning(f"⚠️ [V66] 장르 검증 오류: {str(e)[:50]}")
            return {
                "has_critical": False,
                "violations": [],
                "summary": f"장르 검증 실패: {str(e)[:100]}",
                "feedback": "장르 검증 중 오류 발생 - 수동 확인 권장",
                "degraded": True,
            }

    def assess_character_logic(self, ep_num, manuscript, npc_profiles, character_traits):
        """
        [V41 Red Team] 캐릭터 논리성 적대적 검증
        [V66.1] 원고 truncation 6000→12000자, 빈 프로필 시에도 원고 기반 검증 수행

        Args:
            ep_num: 에피소드 번호
            manuscript: 검수 대상 원고
            npc_profiles: 등장 NPC 프로필 (Master Bible에서 추출)
            character_traits: 캐릭터 특성 DB (성격, 지능, 무공 수준 등)

        Returns:
            dict: {decision, score, violations, severity, feedback}
        """
        safe_manuscript = self._d._escape_braces(manuscript[:12000])  # [V66.1] 6000→12000자 확대
        safe_npc = self._d._escape_braces(json.dumps(npc_profiles, ensure_ascii=False))
        safe_traits = self._d._escape_braces(json.dumps(character_traits, ensure_ascii=False))

        # [V66.1] NPC 정보가 비어있으면 WARNING 로그 후 원고 기반으로 검증 진행
        _profiles_empty = not npc_profiles and not character_traits
        if _profiles_empty:
            logging.warning(f"⚠️ [V66.1] NPC 프로필/특성 DB 비어있음 (ep {ep_num}) — 원고 기반 검증 진행")

        prompt = f"""
[Role] 레드팀 캐릭터 논리성 감사관 (Character Logic Auditor)
[Task] 원고 내 등장인물의 행동이 설정된 특성과 일치하는지 적대적으로 검증하라.

### 📋 검수 대상 데이터
- 현재 회차: 제 {ep_num}화
- 📝 원고 내용: {safe_manuscript}
- 👤 등장 NPC 프로필: {safe_npc}
- 🎭 캐릭터 특성 DB: {safe_traits}

### 🎯 적대적 검증 항목 (Red Team Criteria)
1. **지능적 캐릭터의 어리석은 결정**:
   - '교활한', '노회한', '간사한' 특성의 인물이 비합리적/어리석은 결정을 내리는가?
   - 예: 교활한 악당이 주인공을 함정에 빠뜨릴 수 있는 상황에서 정면대결을 선택

2. **강자의 급격한 약화**:
   - 설정상 강자가 설명 없이 쉽게 제압당하는가?
   - 예: 일류 고수가 삼류의 기습에 무력하게 당함

3. **성격 일관성 위반**:
   - 냉혹한 인물이 갑자기 자비를 베풀거나, 소심한 인물이 돌연 대담해지는가?
   - 성격 변화가 있다면 충분한 서사적 근거가 있는가?

4. **동기 불명 행동**:
   - 인물의 행동에 명확한 동기가 보이지 않는가?
   - 특히 주인공에게 유리한 방향으로 '우연히' 행동하는 조연

### [🚨 판정 기준]
- NPC 프로필이나 특성 DB가 비어있더라도, 원고 내부의 인물 묘사/대사/행동만으로 논리 검증을 수행하라
- 경미한 위반(MINOR)은 경고만 하고 PASS
- 중대한 위반(MAJOR) 2개 이상 또는 치명적 위반(CRITICAL) 1개 이상 시 REJECT
- NPC 프로필이 비어있으면 원고 내에서 스스로 모순되는 행동(앞에서 부상인데 뒤에서 멀쩡)만 검증

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "score": 0~100,
    "violations": [
        {{
            "character": "캐릭터명",
            "trait": "설정된 특성",
            "action": "문제 행동",
            "reason": "위반 사유"
        }}
    ],
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "feedback": "수정 지침 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""

        response = self._d.ask(prompt, temperature=0.1, thinking_level="low")
        return self._d._extract_json_robust(response)

    def _audit_with_v0128(self, ep_num, manuscript, validation_context, target_len=ManuscriptLimits.WARNING_LENGTH):
        """
        [V43 내부 헬퍼] V0128 검증 시스템 사용 (장르 자동 전달)

        audit_manuscript에서 use_v0128=True일 때 호출됨
        """
        mode = "BLUEPRINT" if target_len <= ManuscriptLimits.MIN_LENGTH else "MANUSCRIPT"
        validation_context["mode"] = mode

        return self.audit_manuscript_v0128(
            ep_num=ep_num, manuscript=manuscript, validation_context=validation_context, genre=self._d.genre
        )

    def audit_manuscript_v0128(self, ep_num, manuscript, validation_context, config=None, genre="wuxia") -> dict:
        """
        [V0128] 3-Tier 검증 시스템을 사용한 원고 검수

        Args:
            ep_num: 에피소드 번호
            manuscript: 검수 대상 원고
            validation_context: {
                'encyclopedia': {...},
                'martial_hud': {...},
                'blueprint': {...},
                'mode': 'BLUEPRINT' | 'MANUSCRIPT',
                'history': [...],
                'npc_profiles': {...}
            }
            config: 검증 설정 dict (선택적)
            genre: 장르 ('wuxia', 'hunter', 'investment')

        Returns:
            dict: {
                "final_decision": "PASS" | "CONDITIONAL_PASS" | "REJECT",
                "total_score": float,
                "blocking_result": {...},
                "scoring_result": {...},
                "advisory_result": {...},
                "feedback": str,
                "detailed_feedback": str,
                "self_consistency_used": bool
            }
        """
        # [P3-03] encyclopedia.npcs 누락 시 DEGRADED 경고
        _encyclopedia = validation_context.get("encyclopedia") or {} if isinstance(validation_context, dict) else {}
        _npcs = _encyclopedia.get("npcs") or {}
        _degraded = not bool(_npcs)
        if _degraded:
            logging.warning(
                "[V0128] encyclopedia.npcs 누락 — NPC 일관성 검증 DEGRADED. "
                "validation_context에 encyclopedia를 주입하세요."
            )

        # Lazy initialization of ValidationOrchestrator
        if self.v0128_orchestrator is None:
            default_config = {
                "scoring_model": self._d.primary_model,
                "advisory_model": "gemini-2.5-flash",
                "scoring_threshold": 70,  # [TF-I06] 65→70 YAML/코드 일치
                "use_self_consistency": True,
                "consistency_votes": 3,
            }
            # [TF7-P2-09] settings.json validation 키를 default_config에 병합
            try:
                import json as _json
                from pathlib import Path as _Path

                _sj_path = _Path("config/settings.json")
                if _sj_path.exists():
                    with open(_sj_path, encoding="utf-8") as _sj_f:
                        _sj = _json.load(_sj_f)
                    _sj_val = _sj.get("validation", {})
                    _SETTINGS_KEYS = {
                        "scoring_model",
                        "advisory_model",
                        "scoring_threshold",
                        "use_self_consistency",
                        "consistency_votes",
                        "use_retrospective",
                    }
                    for _k in _SETTINGS_KEYS:
                        if _k in _sj_val:
                            default_config[_k] = _sj_val[_k]
            except Exception:
                pass  # settings.json 읽기 실패 시 기본값 유지

            if config:
                default_config.update(config)

            self.v0128_orchestrator = ValidationOrchestrator(
                config=default_config,
                client=self._d.client,
                genre=genre,
                context=validation_context,  # [V70] POV 등 검증 컨텍스트 전달
            )

        # [V70] POV 동적 갱신 — lazy init 후에도 validation_context가 변경될 수 있으므로
        if self.v0128_orchestrator and self.v0128_orchestrator.pre_llm and validation_context:
            _ctx_pov = validation_context.get("pov", "") if isinstance(validation_context, dict) else ""
            if _ctx_pov:
                self.v0128_orchestrator.pre_llm.pov = _ctx_pov

        try:
            result = self.v0128_orchestrator.validate(
                ep_num=ep_num, manuscript=manuscript, validation_context=validation_context
            )

            # [Sweep45] KeyError 방지 — 부분 결과 시 False REJECT 방지
            legacy_result = {
                "decision": result.get("final_decision", "REJECT"),
                "score": result.get("total_score", 0),
                "reason": result.get("feedback", ""),
                "feedback": result.get("detailed_feedback", result.get("feedback", "")),
                "v0128_full_result": result,
                "degraded": _degraded,  # [P3-03]
            }

            final_decision = result.get("final_decision", "REJECT") if isinstance(result, dict) else "REJECT"
            if final_decision in ["PASS", "CONDITIONAL_PASS"]:
                legacy_result["decision"] = "PASS"
            else:
                legacy_result["decision"] = "REJECT"

            return legacy_result

        except Exception as e:
            logging.warning(f"🚨 [V0128 Error] 검증 중 예외 발생: {e}")
            return {
                "decision": "REJECT",
                "score": 0,
                "reason": f"V0128 검증 시스템 오류: {str(e)}",
                "feedback": "검증 시스템 오류 - 수동 검토 필요",
                "error": str(e),
                "degraded": _degraded,  # [P3-03]
            }

    # ═══════════════════════════════════════════════════════════════════════
    # [V67] prev_full_text 확대 — 최대 30화 이전 원고 로드 (하이엔드)
    # ═══════════════════════════════════════════════════════════════════════

    def _expand_prev_full_text(self, ep_num: int, prev_full_text: str) -> str:
        """
        [V67] 기존 prev_full_text를 최대 30화로 확대.

        DB에서 ep_num-30 ~ ep_num-1 원고를 전문 로드하여 에피소드 마커와 함께 결합.
        Gemini의 대용량 컨텍스트 윈도우를 활용하여 최대한 많은 이전 원고를 전달.
        DB 접근 실패 시 기존 prev_full_text를 그대로 반환 (graceful fallback).

        Returns:
            str: "[제N화]\n본문\n\n---\n\n[제N+1화]\n본문..." 형태의 결합 텍스트
        """
        try:
            db = self._d.context.db
            if not db:
                return prev_full_text or ""
        except (AttributeError, TypeError):
            return prev_full_text or ""

        loaded_parts = []
        for target_ep in range(max(1, ep_num - 30), ep_num):
            try:
                ms = db.get_manuscript(target_ep)
                if ms:
                    content = ms.get("content", "") if isinstance(ms, dict) else str(ms)
                    if content and len(content) > 100:
                        loaded_parts.append(f"[제{target_ep}화]\n{content}")
            except Exception as e:
                logging.warning(f"[V67] Director prev manuscript 조회 실패: {e}")

        if loaded_parts:
            result = "\n\n---\n\n".join(loaded_parts)
            logging.info(f"📖 [V67] Director 컨텍스트 확대: {len(loaded_parts)}화 이전 원고 로드 (ep {ep_num})")
            return result

        # 폴백: 기존 prev_full_text 사용
        return prev_full_text or ""

    # ═══════════════════════════════════════════════════════════════════════
    # [V65 C-5] audit_manuscript — Director에서 이관
    # ═══════════════════════════════════════════════════════════════════════

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
    ) -> dict:
        """
        [V65 C-5] 원고 검수 (V0128 통합 + V46 캐릭터 논리 검증 + V61 Entity 일관성 검증 + V60.87 원고 역사 충돌 검사)

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
        arc_no = 0
        if arc_doc and isinstance(arc_doc, dict):
            arc_no = arc_doc.get("arc_no", 0)
        elif arc_doc and isinstance(arc_doc, str):
            # [V61.5] string인 경우 "Arc N" 패턴에서 추출 시도
            arc_match = re.search(r"[Aa]rc\s*(\d+)", arc_doc[:200])
            if arc_match:
                arc_no = int(arc_match.group(1))
        if arc_no <= 0 and arc_pos:
            arc_no = arc_pos  # arc_pos가 있으면 사용

        # [V63.4] 죽은 NPC → LLM 경고로 전달 (기존: 즉시 REJECT)
        if state_tracker:
            dead_npc_violations = state_tracker.check_dead_npc_in_manuscript(manuscript, ep_num, arc_no)
            if dead_npc_violations:
                violation_names = [v["npc_name"] for v in dead_npc_violations]
                logging.warning(f"⚠️ [V63.4] 죽은 NPC 경고 → LLM 전달: {', '.join(violation_names)}")
                _pre_llm_warnings.append(
                    f"[CRITICAL 경고] 죽은 NPC 등장 의심: {', '.join(violation_names)}\n"
                    + "\n".join(f"  - {v['npc_name']}: Arc {v['death_arc']}에서 사망" for v in dead_npc_violations)
                    + "\n  ※ 회상/과거 언급만 허용. 살아있는 것처럼 대화/행동하면 REJECT 필요."
                )

        # [V63.4] 장르 위반 → LLM 경고로 전달 (기존: 즉시 REJECT)
        if self._d.genre_validation_enabled and self._d.guard:
            genre_violations = self._run_genre_specific_validation(manuscript, ep_num)
            if genre_violations.get("has_critical"):
                logging.warning(f"⚠️ [V63.4] 장르 위반 경고 → LLM 전달: {genre_violations.get('summary', '')}")
                _pre_llm_warnings.append(
                    f"[CRITICAL 경고] 장르 규칙 위반: {genre_violations.get('summary', '')}\n"
                    f"  {genre_violations.get('feedback', '')}"
                )

        # ═══════════════════════════════════════════════════════════════
        # [V60.88] 원고 역사 충돌 검사 - 캐시 우선, 폴백은 기존 방식
        # ═══════════════════════════════════════════════════════════════
        if self._d.manuscript_history_check_enabled:
            history_check = None

            # [V60.88] 캐시가 있으면 캐시 참조 검사 (전문 비교, 고품질)
            if self._d._caching.manuscript_cache_name:
                history_check = self._d.check_manuscript_history_with_cache(
                    ep_num=ep_num, current_manuscript=manuscript
                )
                if history_check.get("cache_used"):
                    logging.warning("⚡ [V60.88] 캐시 참조 충돌 검사 완료")

            # [V63.4 P0] 캐시 없거나 실패 시 기존 방식 폴백 (manuscript_history 사용)
            if not history_check or history_check.get("error") or history_check.get("needs_fallback"):
                if manuscript_history:
                    history_check = self._d.check_manuscript_history_conflicts(
                        ep_num=ep_num,
                        current_manuscript=manuscript,
                        manuscript_history=manuscript_history,
                        use_summary=True,  # 토큰 절약을 위해 요약본 우선 사용
                    )
                elif history_check and history_check.get("needs_fallback"):
                    logging.warning("⚠️ [V63.4] 캐시 폴백 필요하나 manuscript_history 없음 → 검증 스킵")

            if history_check and history_check.get("decision") == "CONFLICT":
                conflicts = history_check.get("conflicts", [])
                conflict_details = "; ".join(
                    [
                        f"[{c.get('type', '?')}] {c.get('prev_fact', '')} vs {c.get('current_violation', '')}"
                        for c in conflicts[:3]
                        if isinstance(c, dict)  # [Sweep64] LLM이 문자열 반환 시 방어
                    ]
                )
                return {
                    "decision": "REJECT",
                    "score": 25,
                    "error_category": "LOGIC_ERROR",
                    "diagnostic_report": f"원고 역사 충돌 {len(conflicts)}건 발견",
                    "current_beat_achieved": False,
                    "reason": f"이전 원고와 충돌: {conflict_details}",
                    "feedback": f"[V60.88] 이전 원고에서 확립된 사실과 모순됨. {history_check.get('summary', '')}",
                    "v60_87_history_check": history_check,
                }
            elif history_check and history_check.get("conflicts"):
                # 경고만 있는 경우 validation_context에 기록
                if validation_context is None:
                    validation_context = {}
                validation_context["v60_87_history_warnings"] = history_check.get("conflicts", [])

        # ═══════════════════════════════════════════════════════════════
        # [V60.89] 주인공 설정 준수 검증 (protagonist_config)
        # ═══════════════════════════════════════════════════════════════
        if self._d.protagonist_config_check_enabled:
            config_check = self.validate_protagonist_config_compliance(manuscript=manuscript, ep_num=ep_num)

            # [V63.4] Python REJECT → LLM 경고로 전달 (기존: 즉시 REJECT)
            if config_check.get("decision") == "REJECT":
                violations = config_check.get("violations", [])
                logging.warning(f"⚠️ [V63.4] 주인공 설정 위반 경고 → LLM 전달: {len(violations)}건")
                _pre_llm_warnings.append(
                    f"[CRITICAL 경고] 주인공 설정 위반 {len(violations)}건\n"
                    f"  {config_check.get('feedback', '주인공 설정 위반')}"
                )
            elif config_check.get("decision") == "WARNING":
                # WARNING은 기록만 하고 계속 진행
                if validation_context is None:
                    validation_context = {}
                validation_context["v60_89_config_warnings"] = config_check.get("violations", [])
                logging.warning(f"⚠️ [V60.89] 주인공 설정 경고: {len(config_check.get('violations', []))}건")

        # ═══════════════════════════════════════════════════════════════
        # [V61] Entity 일관성 검증 - Director의 최종 방어선
        # ═══════════════════════════════════════════════════════════════
        if entity_registry and self._d.entity_consistency_enabled:
            entity_check = self._d.validate_entity_consistency(
                content=manuscript, entity_registry=entity_registry, content_type="manuscript"
            )
            if entity_check.get("decision") == "REJECT":
                mismatches = entity_check.get("mismatches", [])
                return {
                    "decision": "REJECT",
                    "score": 40,
                    "error_category": "LOGIC_ERROR",
                    "diagnostic_report": f"Entity 명칭 불일치 {len(mismatches)}건 발견",
                    "current_beat_achieved": False,
                    "reason": entity_check.get("fix_instructions", "Entity 명칭을 통일하세요"),
                    "feedback": f"[V61] Entity 일관성 오류: {entity_check.get('fix_instructions', '')}",
                    "v61_entity_check": entity_check,
                }
            elif entity_check.get("decision") == "WARNING":
                # WARNING은 경고만 하고 계속 진행, 결과에 포함
                if validation_context is None:
                    validation_context = {}
                validation_context["v61_entity_warnings"] = entity_check.get("mismatches", [])
        # [V46] 캐릭터 논리성 검증 (assess_character_logic 활성화)
        # [V66.1] NPC 프로필 비어있어도 원고 기반 검증 수행 (auto-PASS 제거)
        if validation_context:
            npc_profiles = validation_context.get("npc_profiles", {})
            character_traits = validation_context.get("character_traits", {})

            # [V66.1] NPC 정보 유무와 무관하게 항상 캐릭터 논리 검증 수행
            char_logic_result = self.assess_character_logic(
                ep_num=ep_num, manuscript=manuscript, npc_profiles=npc_profiles, character_traits=character_traits
            )
            if not isinstance(char_logic_result, dict):
                char_logic_result = (
                    char_logic_result[0] if isinstance(char_logic_result, list) and char_logic_result else {}
                )

            # [FIX] CRITICAL 1개 또는 MAJOR 2개 이상일 때만 REJECT (주석과 코드 일치)
            if char_logic_result.get("decision") == "REJECT":
                severity = char_logic_result.get("severity", "NONE")
                violations = char_logic_result.get("violations", [])
                # [Sweep42] 프롬프트가 per-item severity 미요청 → violation 개수로 판정
                violation_count = len(violations)

                # CRITICAL은 1개라도 REJECT, MAJOR는 위반 2개 이상일 때만 REJECT
                should_reject = (severity == "CRITICAL") or (severity == "MAJOR" and violation_count >= 2)

                if should_reject:
                    logging.warning(f"🚨 [V46] 캐릭터 논리 위반 감지 ({severity}, 위반 {violation_count}개)")
                    return {
                        "decision": "REJECT",
                        "score": char_logic_result.get("score", 30),
                        "error_category": "LOGIC_ERROR",
                        "diagnostic_report": f"캐릭터 논리 위반: {violations}",
                        "current_beat_achieved": False,
                        "reason": char_logic_result.get("feedback", "캐릭터 행동이 설정과 불일치"),
                        "feedback": char_logic_result.get("feedback", ""),
                        "v46_character_logic": char_logic_result,
                    }
                else:
                    # MAJOR 1개 또는 MINOR는 경고만 하고 계속 진행
                    logging.warning(f"⚠️ [V46] 캐릭터 논리 이슈 ({severity}, 위반 {violation_count}개) - 계속 진행")

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
            validation_context["pre_llm_critical_warnings"] = (
                "\n\n[⚠️ Python 사전 검증 경고 — 문맥 확인 후 최종 판단 필요]\n" + "\n---\n".join(_pre_llm_warnings)
            )

        # [V66.1] prev_full_text 확대를 1회 수행 후 V0128/legacy 경로에서 공용 사용
        expanded_prev = self._expand_prev_full_text(ep_num, prev_full_text)
        if validation_context is None:
            validation_context = {}
        if expanded_prev:
            validation_context["expanded_prev_full_text"] = expanded_prev

        # [V43] V0128 검증 시스템 조건부 사용
        # [Sweep45] {} is falsy → is not None 으로 변경
        if self._d.use_v0128 and validation_context is not None:
            return self._audit_with_v0128(
                ep_num=ep_num, manuscript=manuscript, validation_context=validation_context, target_len=target_len
            )

        # 1. 검수 모드 자동 결정 (기존 로직)
        audit_mode = "BLUEPRINT" if target_len <= ManuscriptLimits.MIN_LENGTH else "MANUSCRIPT"  # [V64.P4]

        # 2. 데이터 안전 처리
        safe_ms = self._d._escape_braces(manuscript)
        # [V70] arc_doc dict 타입일 때 JSON 직렬화 후 이스케이프
        if isinstance(arc_doc, dict):
            import json as _json

            arc_doc = _json.dumps(arc_doc, ensure_ascii=False)
        safe_arc = self._d._escape_braces(arc_doc)
        safe_history = self._d._escape_braces(history_summary)

        # [V66.1] prev_full_text 확대 결과 재사용
        safe_prev = self._d._escape_braces(expanded_prev)

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
                "feedback": f"장면의 밀도를 높이고, 대사와 묘사를 추가하여 {ManuscriptLimits.TARGET_LENGTH}자 이상으로 확장하십시오.",
            }

        # 2-2. 🚫 [V40 Premium] 반복 구문 체크 (N-gram Deduplication)
        try:
            from modules.core.repetition_guard import RepetitionGuard

            # RepetitionGuard 초기화
            guard = RepetitionGuard(
                window_size=_threshold("premium.repetition.window_size", 5),
                threshold=_threshold("premium.repetition.threshold", 3),
            )

            # 이전 5화 원고 수집
            prev_manuscripts = []
            for i in range(max(1, ep_num - 5), ep_num):
                try:
                    ms = self._d.context.db.get_manuscript(i)
                    if ms and "content" in ms:
                        prev_manuscripts.append(ms["content"])
                except Exception:
                    # DB 조회 실패는 무시 (원고 없을 수 있음)
                    pass

            # 금지 구문 목록 구축
            if prev_manuscripts:
                guard.build_banned_list(prev_manuscripts)

                # 현재 원고 스캔
                violations, clean_score = guard.scan_manuscript(manuscript)

                # 위반 발견 시 REJECT (클린 점수 85% 미만)
                if clean_score < _threshold("premium.repetition.clean_score_min", 0.85):
                    correction_prompt = guard.generate_correction_prompt(violations)

                    return {
                        "decision": "REJECT",
                        "score": int(clean_score * 100),
                        "error_category": "QUALITY_ISSUE",
                        "diagnostic_report": f"반복 구문 과다 사용 ({len(violations)}개 발견)",
                        "current_beat_achieved": True,  # 내용은 맞지만 표현이 문제
                        "reason": f"최근 5화에서 반복 사용된 구문 {len(violations)}개 발견 (클린 점수: {clean_score:.0%}). 어휘 다양성 확보 필요.",
                        "feedback": correction_prompt,
                    }
        except ImportError as ie:
            logging.warning(f"⚠️ [Director] RepetitionGuard 모듈 로드 실패: {ie}")
        except AttributeError as ae:
            logging.warning(f"⚠️ [Director] DB 컨텍스트 오류 (RepetitionGuard): {ae}")
        except Exception as e:
            logging.warning(f"⚠️ [Director] RepetitionGuard 실행 중 예상치 못한 오류: {type(e).__name__}: {e}")

        # 3. [V60.95] 고밀도 HUD 컨텍스트 구축
        high_density_hud = self._d._build_hud_context(state_tracker, ep_num)
        safe_hud = self._d._escape_braces(high_density_hud)

        # 4. 프롬프트 조립 (모든 데이터 유실 없이 매핑)
        prompt = self._prompt_loader.load(
            "director",
            "DIRECTOR_AUDIT_PROMPT_V30",
            ep_num=ep_num,
            audit_mode=audit_mode,
            total_eps=total_eps if total_eps else "미정",
            arc_pos=arc_pos,
            arc_doc=safe_arc,
            target_len=target_len,
            history_summary=safe_history,
            prev_full_text=safe_prev,
            manuscript=safe_ms,
            retry_count=retry_count,  # [V40.3 추가] 재시도 횟수 전달
            high_density_hud_context=safe_hud,  # [V60.95] 고밀도 HUD 주입
        )
        if not prompt:
            return {
                "decision": "REJECT",
                "score": 0,
                "reason": "Prompt loading failed: DIRECTOR_AUDIT_PROMPT_V30",
                "feedback": "prompt_loader 설정 확인",
            }

        # [V63.4] Python 사전 경고를 LLM 프롬프트에 주입
        if _pre_llm_warnings:
            _warning_block = "\n\n[⚠️ Python 사전 검증 경고 — 문맥 확인 후 최종 판단 필요]\n" + "\n---\n".join(
                _pre_llm_warnings
            )
            prompt += self._d._escape_braces(_warning_block)

        response = self._d.ask(prompt, temperature=0.1, thinking_level="high")  # [V61.6] 원고 PASS/REJECT
        result = self._d._extract_json_robust(response)
        # [V70] 파싱 실패 시 안전한 REJECT 반환 (기본 PASS 방지)
        if not isinstance(result, dict) or result.get("parsing_error"):
            return {"decision": "REJECT", "score": 0, "reason": "Director 응답 파싱 실패", "feedback": "재시도 필요"}
        return result

    # ═══════════════════════════════════════════════════════════════════════
    # [V65 C-5] audit_strategic_plan — Director에서 이관
    # ═══════════════════════════════════════════════════════════════════════

    def audit_strategic_plan(
        self,
        arc_plan,
        prev_arc_context,
        curr_block=None,
        protagonist_name=None,
        suspected_duplicates=None,
        entity_registry=None,
        story_context="",
    ) -> dict:
        """
        [V67.1] [Stage 2] Analyst의 아크 설계안에 대한 전략적 무결성 검수 (루프/미래 오염 방지, story_context 추가)

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
        if entity_registry and self._d.entity_consistency_enabled:
            tactical_doc = arc_plan.get("tactical_doc", "")
            entity_check = self._d.validate_entity_consistency(
                content=tactical_doc, entity_registry=entity_registry, content_type="arc"
            )
            if entity_check.get("decision") == "REJECT":
                mismatches = entity_check.get("mismatches", [])
                return {
                    "decision": "REJECT",
                    "score": 40,
                    "loop_detected": False,
                    "reason": f"[V61] Entity 명칭 불일치 {len(mismatches)}건 발견",
                    "re_slice_instruction": entity_check.get("fix_instructions", "Entity 명칭을 통일하세요"),
                    "v61_entity_check": entity_check,
                }

        # 🔒 [V42 Hard Guard] 주인공 이름 일관성 검증
        if protagonist_name and len(protagonist_name) >= 2:
            # [V60.55 DEBUG] 주인공 이름 검색 디버깅
            tactical_doc = arc_plan.get("tactical_doc", "")
            name_in_tactical = protagonist_name in tactical_doc
            name_in_dump = protagonist_name in arc_dump
            logging.info(f"🔍 [V60.55 DEBUG] 주인공 이름 검증: '{protagonist_name}'")
            logging.info(f"- tactical_doc 내 존재: {name_in_tactical}")
            logging.info(f"- arc_dump 내 존재: {name_in_dump}")
            logging.info(f"- tactical_doc 앞 200자: {tactical_doc[:200]}...")

            if not name_in_dump:
                logging.warning(f"🚨 [V60.55] 주인공 이름 '{protagonist_name}' 미발견 → REJECT")
                return {
                    "decision": "REJECT",
                    "score": 0,
                    "loop_detected": False,
                    "reason": f"주인공 이름 '{protagonist_name}' 누락 감지 - 서사 무결성 파괴",
                    "re_slice_instruction": f"모든 주인공 서술에서 '{protagonist_name}'을 명시적으로 사용하라. 유사 명칭이나 다른 인물 이름으로 대체 금지.",
                }
            else:
                logging.info(f"✅ [V60.55] 주인공 이름 '{protagonist_name}' 확인됨")

        # 🔒 [Hard Guard] 미래 무구 조기 노출 차단 (V43: Bible 기반 동적 검증)
        pass

        # 데이터 안전화 처리
        safe_tactical = self._d._escape_braces(arc_plan.get("tactical_doc", ""))
        safe_beats = self._d._escape_braces(str(arc_plan.get("beat_sequence", [])))
        safe_prev = self._d._escape_braces(prev_arc_context)
        safe_curr = self._d._escape_braces(json.dumps(curr_block, ensure_ascii=False)) if curr_block else "없음"

        # [V60.76] Python 의심 아이템 포맷팅
        if suspected_duplicates:
            safe_suspected = "\n".join([f"- {item}" for item in suspected_duplicates])
        else:
            safe_suspected = "(없음 - Python 검사 통과)"

        prompt = self._prompt_loader.load(
            "director",
            "STRATEGIC_AUDIT_PROMPT_V30",
            arc_no=arc_plan.get("arc_no", "?"),
            ep_count=arc_plan.get("ep_count", 0),
            ep_start=arc_plan.get("ep_start", 0),
            ep_end=arc_plan.get("ep_end", 0),
            beat_sequence=safe_beats,
            tactical_doc=safe_tactical,
            prev_context=safe_prev,
            curr_block=safe_curr,
            suspected_duplicates=safe_suspected,
            story_context=self._d._escape_braces(story_context) if story_context else "(작품 설정 정보 없음)",
        )
        if not prompt:
            return {
                "decision": "REJECT",
                "score": 0,
                "reason": "Prompt loading failed: STRATEGIC_AUDIT_PROMPT_V30",
                "loop_detected": False,
            }

        # [V49.3] Self-Consistency 적용
        if self._d.use_self_consistency:
            return self._strategic_audit_with_self_consistency(prompt, arc_no)
        else:
            response = self._d.ask(prompt, temperature=0.1, thinking_level="medium")  # [V61.6] Arc 감사
            result = self._d._extract_json_robust(response)
            # [V70] 파싱 실패 시 안전한 REJECT 반환
            if not isinstance(result, dict) or result.get("parsing_error"):
                return {"decision": "REJECT", "score": 0, "reason": "Arc 감사 응답 파싱 실패", "loop_detected": False}
            return result

    # ═══════════════════════════════════════════════════════════════════════
    # [V65 C-5] _strategic_audit_with_self_consistency — Director에서 이관
    # ═══════════════════════════════════════════════════════════════════════

    def _strategic_audit_with_self_consistency(self, prompt: str, arc_no: int) -> dict:
        """
        [V65 C-5] [V49.3] 전략 감사에 Self-Consistency 투표 적용

        Stage 2/3에서 Director가 LLM 단일 호출의 환각을 방지하기 위해:
        1. 1차 평가 실행
        2. 결과가 애매하면 (PASS이지만 score가 낮거나 경고 포함) 추가 2회 평가
        3. 다수결로 최종 PASS/REJECT 결정

        Returns:
            dict: 감사 결과 (self_consistency 정보 포함)
        """
        # 1차 평가
        response = self._d.ask(prompt, temperature=0.1, thinking_level="medium")  # [V61.6] SC 1차
        first_eval = self._d._extract_json_robust(response)

        if not isinstance(first_eval, dict):
            first_eval = {"decision": "REJECT", "score": 0, "reason": "JSON 파싱 실패"}

        def _safe_int_score(value, default=50):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        first_decision = first_eval.get("decision", "REJECT")
        first_score = _safe_int_score(first_eval.get("score", 50), 50)

        # 명확한 REJECT → 추가 평가 없이 반환
        if first_decision == "REJECT" and first_score < self._d.ambiguous_lower:
            reject_reason = first_eval.get("reason", first_eval.get("re_slice_instruction", "사유 미상"))
            logging.warning(f"🎬 [Director] REJECT (score={first_score})")
            logging.info(f"⚖️ [SC-Skip] Clear REJECT (score={first_score} < ambiguous_lower={self._d.ambiguous_lower})")
            logging.warning(f"└─ 사유: {reject_reason[:80]}{'...' if len(str(reject_reason)) > 80 else ''}")
            first_eval["self_consistency"] = {"votes": 1, "reason": "clear_reject", "pass_votes": 0}
            return first_eval

        # 명확한 PASS (점수가 높음) → 추가 평가 없이 반환
        if first_decision == "PASS" and first_score > self._d.ambiguous_upper:
            pass_reason = first_eval.get("reason", first_eval.get("strengths", "판단 근거 미상"))
            logging.info(f"🎬 [Director] PASS (score={first_score})")
            logging.info(f"⚖️ [SC-Skip] Clear PASS (score={first_score} > ambiguous_upper={self._d.ambiguous_upper})")
            logging.info(f"└─ 근거: {str(pass_reason)[:80]}{'...' if len(str(pass_reason)) > 80 else ''}")
            first_eval["self_consistency"] = {"votes": 1, "reason": "clear_pass", "pass_votes": 1}
            return first_eval

        # 애매한 구간 → 추가 평가 진행
        logging.info(f"⚖️ [V49.3] 애매한 결과({first_decision}, score={first_score}) → Self-Consistency 활성화")

        evaluations = [first_eval]

        # [V60.68] Self-Consistency 병렬화
        # [V61.3] 타임아웃 임포트 추가
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from concurrent.futures import TimeoutError as FutureTimeoutError

        # [V61.3] 타임아웃 상수
        VOTE_ENSEMBLE_TIMEOUT = 150  # 전체 투표 타임아웃 (초) - thinking 오버헤드 반영
        SINGLE_VOTE_TIMEOUT = 90  # 개별 투표 타임아웃 (초)

        def _vote_task(vote_idx, temp) -> tuple:
            """단일 투표 작업"""
            response = self._d.ask(prompt, temperature=temp, thinking_level="low")  # [V61.6] SC 추가투표
            return vote_idx, self._d._extract_json_robust(response)

        vote_tasks = [(i, 0.1 + (i * 0.05)) for i in range(1, self._d.consistency_votes)]

        if not vote_tasks:
            # [G1] 추가 투표가 없으면 첫 평가만으로 결과 반환
            first_eval["self_consistency"] = {
                "votes": 1,
                "reason": "no_extra_votes",
                "pass_votes": 1 if first_decision == "PASS" else 0,
            }
            return first_eval

        # [Phase 3-Obs] 에이전트 레벨 ThreadPoolExecutor 계측
        _tp_t0 = time.monotonic()

        # [TF7-P1-01] 명시적 executor + finally shutdown(wait=False) — context manager의
        # wait=True 기본값으로 인한 타임아웃 후에도 running future 무한 대기 방지
        executor = ThreadPoolExecutor(max_workers=min(3, len(vote_tasks)))
        futures: dict = {}
        try:
            futures = {executor.submit(_vote_task, idx, temp): idx for idx, temp in vote_tasks}

            # [V61.3] 타임아웃 적용 - 야간 무인 운영 시 무한 대기 방지
            try:
                for future in as_completed(futures, timeout=VOTE_ENSEMBLE_TIMEOUT):
                    try:
                        vote_idx, eval_result = future.result(timeout=SINGLE_VOTE_TIMEOUT)
                        if isinstance(eval_result, dict):
                            evaluations.append(eval_result)
                            eval_decision = eval_result.get("decision", "REJECT")
                            eval_score = _safe_int_score(eval_result.get("score", 0), 0)
                            logging.info(f"Vote {vote_idx + 1}: {eval_decision} (score={eval_score})")
                    except FutureTimeoutError:
                        logging.warning("⏰ [V61.3] Vote 타임아웃")
                    except Exception as e:
                        logging.warning(f"⚠️ Vote 오류: {str(e)[:50]}")
            except FutureTimeoutError:
                logging.warning(f"⏰ [V61.3] Self-Consistency 전체 타임아웃 - 완료된 {len(evaluations)}개 투표 사용")
            except Exception as e:
                logging.warning(f"⚠️ [V61.3] Self-Consistency 루프 예외: {str(e)[:80]}")
        finally:
            # [TF7-P1-01] 어떤 경로에서도 실행 — cancel_futures=True로 대기 최소화
            for f in futures:
                f.cancel()
            executor.shutdown(wait=False, cancel_futures=True)

        # [Phase 3-Obs] 병렬 구간 소요 시간 기록
        try:
            logging.info(f"[PerfTimer:DirectorAuditor] director_sc_arc{arc_no}_voting={time.monotonic() - _tp_t0:.2f}s")
        except Exception as _e:
            logging.debug("[DirectorAuditor] PerfTimer 기록 실패 (무시): %s", _e)

        # 점수들의 중앙값
        scores = []
        for e in evaluations:
            if isinstance(e, dict):
                scores.append(_safe_int_score(e.get("score", 50), 50))
        median_score = int(round(statistics.median(scores))) if scores else 50

        # PASS/REJECT 다수결
        pass_votes = sum(1 for e in evaluations if e.get("decision") == "PASS")
        final_decision = "PASS" if pass_votes > (len(evaluations) // 2) else "REJECT"

        # 대표 결과 선택 (중앙값에 가장 가까운 것)
        representative = min(evaluations, key=lambda e: abs(_safe_int_score(e.get("score", 50), 50) - median_score))

        # 결과 병합
        result = representative.copy()
        result["decision"] = final_decision
        result["score"] = median_score
        result["self_consistency"] = {
            "votes": len(evaluations),
            "pass_votes": pass_votes,
            "scores": scores,
            "median_score": median_score,
            "reason": f"ambiguous_result ({first_decision}, score={first_score})",
        }

        logging.info(
            f"✅ [V49.3] Self-Consistency 완료: {final_decision} (PASS {pass_votes}/{len(evaluations)}, median={median_score})"
        )

        return result

    # ═══════════════════════════════════════════════════════════════════════
    # [V65 C-5] validate_protagonist_config_compliance — Director에서 이관
    # ═══════════════════════════════════════════════════════════════════════

    def validate_protagonist_config_compliance(self, manuscript: str, ep_num: int = 0) -> dict:
        """
        [V65 C-5] [V60.89] 원고가 protagonist_config 설정을 준수하는지 검증

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
        if not self._d.protagonist_config_check_enabled:
            return {"decision": "PASS", "violations": [], "feedback": ""}

        config = self._d._caching.get_protagonist_config()
        if not config:
            return {"decision": "PASS", "violations": [], "feedback": "설정 없음"}

        world_origin = config.get("world_origin", "현대인")  # [V61.5] 기본값: 느슨한 모드
        incarnation_type = config.get("incarnation_type", "기타")  # [V61.5] 기본값: 느슨한 모드

        # [V60.96] 장르 추출 (장르별 금지어 적용)
        genre = self._d.genre  # [V61.5] self._d.genre 사용
        try:
            if hasattr(self._d.context, "db"):
                bible = self._d.context.db.load_anchor("bible")
                if bible:
                    genre = bible.get("_genre", self._d.genre)
        except (AttributeError, KeyError, TypeError):  # [V64.P4]
            pass

        violations = []
        decision = "PASS"

        # ═══════════════════════════════════════════════════════════════
        # 1. 원시인 모드: 현대 용어 검사 (CRITICAL - REJECT)
        # [V60.96] 장르별 JSON 기반 PrimitiveGuard 사용
        # ═══════════════════════════════════════════════════════════════
        if world_origin == "원시인":
            if PRIMITIVE_GUARD_AVAILABLE:
                # 장르별 JSON 기반 검증 (primitive_forbidden.json)
                guard = get_primitive_guard()
                prim_decision, prim_violations = guard.validate(manuscript, genre)
                violations.extend(prim_violations)
                if prim_decision == "REJECT":
                    decision = "REJECT"
            else:
                # 폴백: 기본 패턴만 검사
                fallback_patterns = [
                    (r"헬스장|바벨|덤벨", "현대 운동기구"),
                    (r"시스템|프로세스|알고리즘", "현대 개념어"),
                    (r"병원|학교|은행", "현대 시설"),
                ]
                for pattern, category in fallback_patterns:
                    matches = re.findall(pattern, manuscript, re.IGNORECASE)
                    if matches:
                        violations.append(
                            {
                                "type": "MODERN_TERM",
                                "severity": "CRITICAL",
                                "category": category,
                                "found": list(set(matches))[:5],
                                "message": f"[원시인 모드] {category} 사용 금지: {matches[:3]}",
                            }
                        )
                        decision = "REJECT"

        # ═══════════════════════════════════════════════════════════════
        # 2. 회귀자 모드: 미래 지식 직접 노출 검사 (WARNING)
        # ═══════════════════════════════════════════════════════════════
        if incarnation_type == "회귀자":
            # 미래 예언 패턴 (직접적 스포일러)
            future_spoiler_patterns = [
                (r"(곧|머지않아|얼마 후면?)\s*.{0,20}(죽|망|멸|패)", "미래 예언"),
                (r"(전생|회귀)\s*[에의]서?\s*(알|봤|경험)", "직접적 회귀 언급"),
                (r"미래[에서의]?\s*.{0,10}(기억|지식)", "미래 지식 직접 언급"),
            ]

            for pattern, category in future_spoiler_patterns:
                matches = re.findall(pattern, manuscript)
                if matches:
                    violations.append(
                        {
                            "type": "FUTURE_KNOWLEDGE",
                            "severity": "WARNING",
                            "category": category,
                            "found": [str(m) for m in matches[:3]],
                            "message": f"[회귀자] {category} 감지 - 합리적 이유 확인 필요",
                        }
                    )
                    if decision == "PASS":
                        decision = "WARNING"

        # 피드백 생성
        feedback = ""
        if violations:
            critical_violations = [v for v in violations if v.get("severity") == "CRITICAL"]
            warning_violations = [v for v in violations if v.get("severity") == "WARNING"]

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
            "incarnation_type": incarnation_type,
        }
