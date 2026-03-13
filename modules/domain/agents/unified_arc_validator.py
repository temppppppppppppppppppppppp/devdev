"""
[V60.75] Unified Arc Validator
Stage 2 통합 검증기 - Python + LLM 단일 검증

철학: "충분한 분량의, 상호 개연성 및 일관성 있는 Arc"

구조:
1. Python 즉시 검증 (무료, 빠름)
   - 분량 체크
   - 필수 필드 체크
   - 중복 아이템 패턴 매칭
2. LLM 문맥 검증 (유료, 정확)
   - 연속성 (위치, 상태, 아이템)
   - 개연성 (서사 논리)
   - 일관성 (캐릭터, 복선)

기존 대체:
- ArcCritic
- ConsensusValidator
- ArcDraftValidator (Stage 2용)
- ContinuityInspector.inspect_arc() (Stage 2용)
"""

import json
import logging
import re

from modules.core.arc_summary_utils import generate_prev_arc_summary  # [V64.P4]
from modules.core.constants import Stage2Limits
from modules.core.prompt_loader import SafeDict

from .base_agent import BaseAgent

# 통합 검증 프롬프트
UNIFIED_VALIDATION_PROMPT = """
[UNIFIED ARC VALIDATOR - 통합 Arc 검증]

당신은 Arc 품질 검증 전문가입니다.
생성된 Arc를 다음 기준으로 검증하세요.

### [검증 대상 Arc]
{arc_data}

### [이전 Arc 요약]
{prev_summary}

### [제약 조건]
{constraints}

### [Python 사전 검증 결과]
{python_result}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### [검증 기준]

#### 0. 🔍 모순·일관성 검사 (CRITICAL/MAJOR — 능동적으로 반드시 검사)
이전 Arc 요약과 제약 조건을 기준으로 다음 항목을 하나씩 직접 대조하라:
- **사망·부재 NPC 활동**: 이전 Arc에서 사망하거나 퇴장한 NPC가 이번 Arc에서 활동하면 CRITICAL
- **수치·사실 모순**: 이전 Arc에서 확립된 금액·지분율·날짜·회사명·직함 등과 충돌하면 CRITICAL
- **인물 관계·설정 모순**: 기존 확립된 인물 관계·직함·성격과 다른 서술이 있으면 MAJOR
- **장소·시간 모순**: 이전 Arc 종료 위치·상황과 이어질 수 없는 공간적·시간적 비약이 있으면 MAJOR
- **내부 모순**: Arc 내 화수별 사건이 서로 인과적으로 충돌하면 MAJOR

#### 1. 연속성 (CRITICAL 가능)
- **아이템**: items_acquired에 이미 획득한 아이템이 있으면 CRITICAL
- **수여물**: grants_received에 이미 수여받은 것이 있으면 CRITICAL
- **위치**: arc_start_state.location ≠ 이전 Arc 종료 위치면 MAJOR
- **상태**: 부상/내공이 급격히 변하면 MAJOR

#### 2. 구조 (MAJOR 최대)
- **분량**: tactical_doc이 ep_count × {min_chars}자 미만이면 MAJOR
- **화 구분**: "제N화" 형식이 ep_count개 미만이면 MAJOR
- **필수 필드**: state_constraints, joint_docs 누락 시 MAJOR

#### 3. 서사 (MAJOR 최대)
- **개연성**: 캐릭터 행동이 확립된 동기와 명백히 맞지 않으면 MAJOR
- **복선·갈등 무시**: 이전 Arc에서 설정된 복선·갈등이 아무 설명 없이 무시되면 MAJOR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### [판정 기준]
- **REJECT**: CRITICAL 이슈 1개 이상인 경우만
- **PASS**: 그 외 (MAJOR는 경고로 기록하되 PASS 처리 → Director가 최종 판정)

### [출력 형식 - 반드시 JSON만 출력]

{{
    "verdict": "PASS 또는 REJECT",
    "issues": [
        {{
            "severity": "CRITICAL/MAJOR/MINOR",
            "category": "contradiction/continuity/structure/narrative",
            "issue": "문제 설명",
            "evidence": "근거 (이전 Arc의 어떤 사실과 충돌하는지 구체적으로)",
            "fix_hint": "수정 방향"
        }}
    ],
    "contradictions": ["모순 요약 (구체적)", ...],
    "summary": "전체 평가 요약 (1-2문장)",
    "confidence": 0.85
}}

반드시 유효한 JSON만 출력하세요.
"""


class UnifiedArcValidator(BaseAgent):
    """
    [V60.75] 통합 Arc 검증기

    Python + LLM 단일 검증으로 Stage 2 검증 단순화
    """

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)
        self.min_chars_per_ep = Stage2Limits.MIN_CHARS_PER_EPISODE

    def validate(
        self,
        arc: dict,
        prev_arcs: list[dict],
        constraints: str = "",
        state_tracker=None,  # [V60.94] StateTracker (죽은 NPC 검증용)
        pre_collected_items: set | None = None,  # [V62.5] ConstraintCompiler에서 수집된 아이템
        pre_collected_grants: set | None = None,  # [V62.5] ConstraintCompiler에서 수집된 수여물
        genre: str = "",
    ) -> tuple[str, dict]:
        """
        Arc 통합 검증

        Args:
            arc: 검증할 Arc
            prev_arcs: 이전 Arc 리스트
            constraints: 제약 조건 텍스트
            state_tracker: [V60.94] StateTracker (죽은 NPC 검증용)
            pre_collected_items: [V62.5] 이미 수집된 이전 Arc 아이템 set (중복 스캔 방지)
            pre_collected_grants: [V62.5] 이미 수집된 이전 Arc 수여물 set (중복 스캔 방지)

        Returns:
            (verdict, result) - "PASS"/"REJECT", 상세 결과
        """
        # ═══════════════════════════════════════════════════════════════
        # Phase A: Python 즉시 검증 (무료)
        # ═══════════════════════════════════════════════════════════════
        python_result = self._python_validate(arc, prev_arcs, state_tracker, pre_collected_items, pre_collected_grants)

        # [V63.4] Python CRITICAL도 LLM에 전달 (Python은 정보 제공만, 최종 판단은 LLM)
        if python_result["has_critical"]:
            logging.warning(f" [V63.4] Python CRITICAL {len(python_result.get('critical_summary', ''))}자 → LLM 검증으로 전달"
            )

        # ═══════════════════════════════════════════════════════════════
        # Phase B: LLM 문맥 검증 (유료)
        # ═══════════════════════════════════════════════════════════════
        logging.warning(" [UnifiedValidator] LLM 검증 중...")
        print("      🔍 [ArcValidator] LLM 검증 중...")

        llm_result = self._llm_validate(arc, prev_arcs, constraints, python_result, genre=genre)

        # 결과 병합
        all_issues = python_result["issues"] + llm_result.get("issues", [])

        # 최종 판정
        critical_count = sum(1 for i in all_issues if i.get("severity") == "CRITICAL")
        major_count = sum(1 for i in all_issues if i.get("severity") == "MAJOR")

        # [V61.9] Director 주권주의: CRITICAL만 REJECT, MAJOR는 경고로 Director에게 넘김
        if critical_count > 0:
            verdict = "REJECT"
        else:
            # MAJOR가 있어도 PASS → Director가 최종 판정
            verdict = "PASS"
            if major_count > 0:
                logging.warning(f" [UnifiedValidator] MAJOR {major_count}건 경고 → Director에게 위임")

        result = {
            "verdict": verdict,
            "phase": "llm",
            "issues": all_issues,
            "summary": llm_result.get("summary", ""),
            "confidence": llm_result.get("confidence", 0.5),
            "feedback": self._generate_feedback(all_issues),
            "python_issues": len(python_result["issues"]),
            "llm_issues": len(llm_result.get("issues", [])),
        }

        status = "✅ PASS" if verdict == "PASS" else "❌ REJECT"
        logging.warning(f"{status} [UnifiedValidator] (CRITICAL:{critical_count}, MAJOR:{major_count})")
        print(f"      {status} [ArcValidator] CRITICAL:{critical_count}, MAJOR:{major_count}")

        return verdict, result

    # [V63.4 P1] _python_validate → 8개 독립 체크 메서드로 분할

    def _check_dead_npc(self, arc: dict, state_tracker, prev_arcs: list[dict]) -> list[dict]:
        """[#0] 죽은 NPC 등장 + NPC 변경 체크"""
        issues = []
        if not prev_arcs:
            logging.info("[UnifiedValidator] no previous arcs — dead NPC check skipped")
            return issues
        if not state_tracker:
            logging.warning("[UnifiedValidator] state_tracker missing with previous arcs — dead NPC check skipped")
            return issues

        arc_no = arc.get("arc_no", 0)
        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str):
            tactical = str(tactical) if tactical else ""

        dead_npc_violations = state_tracker.check_dead_npc_appearance(tactical, arc_no)
        for v in dead_npc_violations:
            issues.append(
                {
                    "severity": "CRITICAL",
                    "category": "npc_death",
                    "issue": f"💀 죽은 NPC 등장: '{v.get('npc_name', '?')}'",
                    "evidence": f"Arc {v.get('death_arc', '?')}에서 사망, Arc {arc_no}에서 다시 등장",
                    "fix_hint": f"'{v.get('npc_name', '?')}'을(를) 등장시키지 마세요 (사망 NPC)",
                }
            )
            logging.warning(f" [V60.94] REJECT: 죽은 NPC '{v.get('npc_name')}' 등장!")

        npc_changes = state_tracker.check_npc_changes(tactical, arc_no)
        for change in npc_changes:
            change_type = "무장" if change.get("change_type") == "weapon" else "수준"
            issues.append(
                {
                    "severity": "WARNING",
                    "category": "npc_change",
                    "issue": f"⚠️ NPC {change_type} 변경: '{change.get('npc_name', '?')}'",
                    "evidence": change.get("reason", ""),
                    "fix_hint": f"'{change.get('npc_name', '?')}'의 {change_type} 변경에 대한 정당화 사유 필요 (습득, 성장 등)",
                }
            )
            logging.warning(f" [V60.95] WARNING: NPC '{change.get('npc_name')}' {change_type} 변경 감지")

        return issues

    def _check_length(self, arc: dict) -> list[dict]:
        """[#1] 분량 체크"""
        issues = []
        try:
            ep_count = int(arc.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT))
        except (TypeError, ValueError):
            ep_count = Stage2Limits.DEFAULT_EP_COUNT
        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str):
            tactical = str(tactical) if tactical else ""

        min_length = ep_count * self.min_chars_per_ep
        if len(tactical) < min_length:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"tactical_doc 분량 부족: {len(tactical)}자 < {min_length}자",
                    "evidence": f"ep_count={ep_count}, 필요={min_length}자",
                    "fix_hint": f"tactical_doc을 {min_length}자 이상으로 작성",
                }
            )

        ep_pattern = re.findall(r"제\s*\d+\s*화", tactical)
        if len(ep_pattern) < ep_count:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"화 구분 부족: {len(ep_pattern)}개 < {ep_count}개",
                    "evidence": f"'제N화' 패턴 {len(ep_pattern)}개 발견",
                    "fix_hint": f"'제1화', '제2화' 등 {ep_count}개 섹션 명시",
                }
            )
        return issues

    def _check_required_fields(self, arc: dict) -> list[dict]:
        """[#3] 필수 필드 + state_changes 형식 검증"""
        issues = []
        required_fields = ["arc_no", "ep_count", "tactical_doc", "state_constraints", "joint_docs", "state_changes"]
        for field in required_fields:
            if field not in arc or not arc[field]:
                severity = "WARNING" if field == "state_changes" else "MAJOR"
                issues.append(
                    {
                        "severity": severity,
                        "category": "structure",
                        "issue": f"필수 필드 누락: {field}",
                        "evidence": f"{field} 필드가 없거나 비어있음",
                        "fix_hint": f"{field} 필드를 올바르게 작성",
                    }
                )

        state_changes = arc.get("state_changes", {})
        if state_changes and isinstance(state_changes, dict):
            timeline = state_changes.get("timeline", {})
            if not timeline or not isinstance(timeline, dict):
                fallback_timeline = (arc.get("state_constraints", {}) or {}).get("timeline", {})
                timeline = fallback_timeline if isinstance(fallback_timeline, dict) else {}
            if not timeline or not isinstance(timeline, dict):
                issues.append(
                    {
                        "severity": "WARNING",
                        "category": "state_changes",
                        "issue": "state_changes.timeline 필드 누락",
                        "evidence": "timeline 필드가 없고 state_constraints.timeline 폴백도 사용할 수 없음",
                        "fix_hint": "timeline: {start: {...}, end: {...}} 형식으로 작성하세요",
                    }
                )
            else:
                start = timeline.get("start", {})
                end = timeline.get("end", {})
                if not start or not isinstance(start, dict):
                    issues.append(
                        {
                            "severity": "MINOR",
                            "category": "state_changes",
                            "issue": "timeline.start 필드 비어있음",
                            "evidence": f"start: {start}",
                            "fix_hint": "Arc 시작 시점을 명시하세요 (예: {year: 2000, month: 3})",
                        }
                    )
                if not end or not isinstance(end, dict):
                    issues.append(
                        {
                            "severity": "MINOR",
                            "category": "state_changes",
                            "issue": "timeline.end 필드 비어있음",
                            "evidence": f"end: {end}",
                            "fix_hint": "Arc 종료 시점을 명시하세요",
                        }
                    )

            npc_deaths = state_changes.get("npc_deaths", [])
            if isinstance(npc_deaths, list):
                for death in npc_deaths:
                    if isinstance(death, dict) and not death.get("name"):
                        issues.append(
                            {
                                "severity": "MINOR",
                                "category": "state_changes",
                                "issue": "npc_deaths에 name 필드 누락",
                                "evidence": str(death)[:100],
                                "fix_hint": "사망 NPC 이름을 명시하세요",
                            }
                        )
            skill_acq = state_changes.get("skill_acquisitions", [])
            if isinstance(skill_acq, list):
                for skill in skill_acq:
                    if isinstance(skill, dict) and not skill.get("name"):
                        issues.append(
                            {
                                "severity": "MINOR",
                                "category": "state_changes",
                                "issue": "skill_acquisitions에 name 필드 누락",
                                "evidence": str(skill)[:100],
                                "fix_hint": "습득 무공 이름을 명시하세요",
                            }
                        )
        return issues

    def _check_duplicate_items(
        self, arc: dict, prev_arcs: list[dict], pre_collected_items: set | None = None
    ) -> list[dict]:
        """[#4] 중복 아이템 획득 체크"""
        issues = []
        if not prev_arcs:
            return issues

        if pre_collected_items is not None:
            prev_items = pre_collected_items
        else:
            prev_items = set()
            for prev in prev_arcs:
                # [BUG-F] protagonist_items 우선 폴백
                _psc = prev.get("state_constraints", {})
                acquired = _psc.get("protagonist_items") or _psc.get("items_acquired", [])
                if isinstance(acquired, list):
                    # [Sweep-Codex] dict 아이템 방어 (unhashable type 방지)
                    prev_items.update(
                        (item.get("name", item.get("item", "")) if isinstance(item, dict) else str(item).strip())
                        for item in acquired
                        if item
                    )

        # [BUG-F] protagonist_items 우선 폴백
        _csc = arc.get("state_constraints", {})
        current_acquired = _csc.get("protagonist_items") or _csc.get("items_acquired", [])
        if isinstance(current_acquired, list):
            for item in current_acquired:
                item_str = item.strip() if isinstance(item, str) else str(item)
                if item_str in prev_items:
                    issues.append(
                        {
                            "severity": "CRITICAL",
                            "category": "continuity",
                            "issue": f"중복 아이템 획득: '{item_str}'",
                            "evidence": "이전 Arc에서 이미 획득한 아이템",
                            "fix_hint": f"items_acquired에서 '{item_str}' 제거",
                        }
                    )
        return issues

    def _check_duplicate_grants(
        self, arc: dict, prev_arcs: list[dict], pre_collected_grants: set | None = None
    ) -> list[dict]:
        """[#5] 중복 수여물 체크"""
        issues = []
        if not prev_arcs:
            return issues

        if pre_collected_grants is not None:
            prev_grants = pre_collected_grants
        else:
            prev_grants = set()
            for prev in prev_arcs:
                grants = prev.get("state_constraints", {}).get("grants_received", [])
                if isinstance(grants, list):
                    prev_grants.update(g.strip() for g in grants if g)

        current_grants = arc.get("state_constraints", {}).get("grants_received", [])
        if isinstance(current_grants, list):
            for grant in current_grants:
                grant_str = grant.strip() if isinstance(grant, str) else str(grant)
                if grant_str in prev_grants:
                    issues.append(
                        {
                            "severity": "CRITICAL",
                            "category": "continuity",
                            "issue": f"중복 수여물: '{grant_str}'",
                            "evidence": "이전 Arc에서 이미 수여받은 것",
                            "fix_hint": f"grants_received에서 '{grant_str}' 제거",
                        }
                    )
        return issues

    def _check_injury_escalation(self, arc: dict) -> list[dict]:
        """[#6] 부상 에스컬레이션 체크"""
        issues = []
        CHRONIC_KEYWORDS = [
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
        ]
        end_state = arc.get("state_constraints", {}).get("arc_end_state", {})
        end_injuries = str(end_state.get("injuries", "없음"))
        shadow_injuries = str(arc.get("status_shadow", {}).get("expected_injuries", "없음"))

        for inj_text in [end_injuries, shadow_injuries]:
            for kw in CHRONIC_KEYWORDS:
                if kw in inj_text:
                    issues.append(
                        {
                            "severity": "ADVISORY",
                            "category": "injury_escalation",
                            "issue": f"부상 에스컬레이션 잔여: '{kw}' (자동 세정 대상)",
                            "evidence": inj_text[:60],
                            "fix_hint": "Phase 2.5 자동 세정에서 처리됨",
                        }
                    )
                    break
        return issues

    def _check_resolved_plots(self, arc: dict, state_tracker) -> list[dict]:
        """[#7] 완결된 플롯 재생성 체크"""
        issues = []
        if not state_tracker or not hasattr(state_tracker, "resolved_plots") or not state_tracker.resolved_plots:
            return issues
        if not isinstance(state_tracker.resolved_plots, list):  # [V70] 타입 방어
            return issues

        tactical_str = arc.get("tactical_doc", "")
        if not isinstance(tactical_str, str):
            tactical_str = str(tactical_str) if tactical_str else ""
        for resolved in state_tracker.resolved_plots:
            plot_name = resolved.get("plot", "")
            if plot_name and len(plot_name) >= 5 and plot_name in tactical_str:  # [V63.4] 3→5자 (오탐 방지)
                issues.append(
                    {
                        "severity": "MAJOR",
                        "category": "resolved_plot",
                        "issue": f"완결된 플롯 재등장 의심: '{plot_name}'",
                        "evidence": f"Arc {resolved.get('arc_no', '?')}에서 완결: {resolved.get('resolution', '')}",
                        "fix_hint": f"'{plot_name}'은 이미 해결된 사건입니다. 새로운 갈등을 설계하세요.",
                    }
                )
        return issues

    def _check_entity_consistency(self, arc: dict, state_tracker) -> list[dict]:
        """[#8] 비-NPC 엔티티 명칭 일관성 체크"""
        issues = []
        if not state_tracker or not hasattr(state_tracker, "check_entity_name_consistency"):
            return issues

        arc_no = arc.get("arc_no", 0)
        tactical_str = arc.get("tactical_doc", "")
        if not isinstance(tactical_str, str):
            tactical_str = str(tactical_str) if tactical_str else ""
        entity_warnings = state_tracker.check_entity_name_consistency(tactical_str, arc_no)
        for ew in entity_warnings:
            issues.append(
                {
                    "severity": "WARNING",
                    "category": "entity_consistency",
                    "issue": f"엔티티 명칭 불일치: '{ew.get('entity', '')}' vs '{ew.get('variant', '')}'",
                    "evidence": f"'{ew.get('entity', '')}' (Arc {ew.get('first_arc', '?')}에서 등록)과 유사",
                    "fix_hint": f"'{ew.get('entity', '')}'로 통일하세요.",
                }
            )
        return issues

    def _check_episode_details_type(self, arc: dict) -> list[dict]:
        """[TF10-3-1] episode_details 타입 정합성 체크 (ADVISORY — 비차단)"""
        issues = []
        ep_details = arc.get("episode_details")
        if ep_details is None:
            return issues  # 선택 필드 — 없어도 OK
        if not isinstance(ep_details, list):
            issues.append(
                {
                    "severity": "ADVISORY",
                    "issue": f"episode_details 타입 오류: list 기대, {type(ep_details).__name__} 수신 — downstream 폴백 발동",
                    "detail": str(ep_details)[:100],
                }
            )
            return issues
        for i, item in enumerate(ep_details):
            if not isinstance(item, dict):
                issues.append(
                    {
                        "severity": "ADVISORY",
                        "issue": f"episode_details[{i}] 타입 오류: dict 기대, {type(item).__name__} 수신",
                        "detail": str(item)[:80],
                    }
                )
            elif not isinstance(item.get("ep_num"), int):
                issues.append(
                    {
                        "severity": "ADVISORY",
                        "issue": f"episode_details[{i}].ep_num 타입 오류: int 기대, {type(item.get('ep_num')).__name__} 수신",
                        "detail": str(item.get("ep_num"))[:40],
                    }
                )
        return issues

    def _python_validate(
        self,
        arc: dict,
        prev_arcs: list[dict],
        state_tracker=None,
        pre_collected_items: set | None = None,
        pre_collected_grants: set | None = None,
    ) -> dict:
        """[V63.4 P1] Python 즉시 검증 — 9개 독립 체크 조합"""
        issues = []
        issues.extend(self._check_dead_npc(arc, state_tracker, prev_arcs))
        issues.extend(self._check_length(arc))
        issues.extend(self._check_required_fields(arc))
        issues.extend(self._check_duplicate_items(arc, prev_arcs, pre_collected_items))
        issues.extend(self._check_duplicate_grants(arc, prev_arcs, pre_collected_grants))
        issues.extend(self._check_injury_escalation(arc))
        issues.extend(self._check_resolved_plots(arc, state_tracker))
        issues.extend(self._check_entity_consistency(arc, state_tracker))
        issues.extend(self._check_episode_details_type(arc))

        has_critical = any(i["severity"] == "CRITICAL" for i in issues)
        critical_items = [i["issue"] for i in issues if i["severity"] == "CRITICAL"]

        return {
            "issues": issues,
            "has_critical": has_critical,
            "critical_summary": "; ".join(critical_items) if critical_items else "",
        }

    def _llm_validate(
        self, arc: dict, prev_arcs: list[dict], constraints: str, python_result: dict, *, genre: str = ""
    ) -> dict:
        """LLM 문맥 검증 (유료, 정확)"""

        # 이전 Arc 요약 생성
        prev_summary = self._generate_prev_summary(prev_arcs)

        # Python 결과 포맷팅
        python_text = self._format_python_result(python_result)

        # 프롬프트 생성
        prompt = UNIFIED_VALIDATION_PROMPT.format_map(
            SafeDict(
                arc_data=self._escape_braces(json.dumps(arc, ensure_ascii=False, indent=2)[:18000]),
                prev_summary=self._escape_braces(prev_summary),
                constraints=self._escape_braces(constraints[:9000] if constraints else "(없음)"),
                python_result=self._escape_braces(python_text),
                min_chars=self.min_chars_per_ep,
            )
        )

        if genre and genre not in ("wuxia", "무협"):
            prompt += "\n\n⚠️ [장르 안내] 이 작품은 비무협 장르입니다. internal_energy와 injuries 필드의 불일치는 무시하세요. 부상/내공 관련 MAJOR 판정을 내리지 마세요."

        try:
            response = self.ask(prompt, temperature=0.1, thinking_level="low")  # [V61.6] Arc 검증
            result = self._extract_json_robust(response)

            if not isinstance(result, dict):
                logging.warning(" [UnifiedValidator] JSON 파싱 실패 → REJECT")
                # [V61.5] fail-open → fail-closed: 파싱 실패 시 REJECT
                return {
                    "verdict": "REJECT",
                    "issues": [
                        {
                            "severity": "CRITICAL",
                            "category": "system",
                            "issue": "LLM 응답 파싱 실패",
                            "evidence": "JSON 파싱 불가",
                            "fix_hint": "재시도",
                        }
                    ],
                    "summary": "LLM 응답 파싱 실패로 REJECT",
                    "confidence": 0.0,
                }

            _contradictions = result.get("contradictions", [])
            if isinstance(_contradictions, list) and _contradictions:
                logging.warning(f" [ArcValidator] 모순 {len(_contradictions)}건 발견:")
                print(f"      🚨 [ArcValidator] 모순 {len(_contradictions)}건 발견")
                for _c in _contradictions[:5]:
                    logging.warning(f" {str(_c)[:150]}")
            else:
                logging.info("✅ [ArcValidator] 모순·일관성 이상 없음")
                print("      ✅ [ArcValidator] 모순 없음")

            return result

        except Exception as e:
            logging.warning(f" [UnifiedValidator] LLM 오류: {str(e)[:50]} → REJECT")
            # [V61.5] fail-open → fail-closed: LLM 오류 시 REJECT
            return {
                "verdict": "REJECT",
                "issues": [
                    {
                        "severity": "CRITICAL",
                        "category": "system",
                        "issue": f"LLM 오류: {str(e)[:50]}",
                        "evidence": "API 호출 실패",
                        "fix_hint": "재시도",
                    }
                ],
                "summary": f"LLM 오류로 REJECT: {str(e)[:50]}",
                "confidence": 0.0,
            }

    def _generate_prev_summary(self, prev_arcs: list[dict]) -> str:
        """[V64.P4] 위임 → modules.core.arc_summary_utils.generate_prev_arc_summary"""
        return generate_prev_arc_summary(prev_arcs, include_energy=True)

    def _format_python_result(self, python_result: dict) -> str:
        """Python 검증 결과 포맷팅"""
        issues = python_result.get("issues", [])
        if not issues:
            return "✅ Python 사전 검증 통과 (이슈 없음)"

        lines = [f"⚠️ Python 사전 검증 이슈 {len(issues)}건:"]
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "?")
            text = issue.get("issue", "?")
            lines.append(f"  {i}. [{sev}] {text}")

        return "\n".join(lines)

    def _generate_feedback(self, issues: list[dict]) -> str:
        """재생성용 피드백 생성"""
        if not issues:
            return ""

        lines = ["[검증 실패 - 다음 문제 해결 필요]", ""]

        # CRITICAL 먼저
        critical = [i for i in issues if i.get("severity") == "CRITICAL"]
        if critical:
            lines.append("🚨 CRITICAL (필수 수정):")
            for c in critical:
                lines.append(f"  - {c.get('issue', '?')}")
                if c.get("fix_hint"):
                    lines.append(f"    → {c['fix_hint']}")

        # MAJOR
        major = [i for i in issues if i.get("severity") == "MAJOR"]
        if major:
            lines.append("")
            lines.append("⚠️ MAJOR (수정 권장):")
            for m in major[:3]:  # 최대 3개
                lines.append(f"  - {m.get('issue', '?')}")

        return "\n".join(lines)


def create_unified_validator(context, client, model_tier: str = "gemini-2.5-flash"):
    """UnifiedArcValidator 생성 헬퍼"""
    return UnifiedArcValidator(context, client, model_tier)
