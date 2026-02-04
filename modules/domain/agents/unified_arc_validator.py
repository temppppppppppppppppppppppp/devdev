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
import re
from typing import Dict, List, Any, Optional, Tuple
from .base_agent import BaseAgent
from modules.core.constants import Stage2Limits


# 통합 검증 프롬프트
UNIFIED_VALIDATION_PROMPT = """
[V60.75 UNIFIED ARC VALIDATOR - 통합 Arc 검증]

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

#### 1. 연속성 (CRITICAL 가능)
- **아이템**: items_acquired에 이미 획득한 아이템이 있으면 CRITICAL
- **수여물**: grants_received에 이미 수여받은 것이 있으면 CRITICAL
- **위치**: arc_start_state.location ≠ 이전 Arc 종료 위치면 MAJOR
- **상태**: 부상/내공이 급격히 변하면 MAJOR

#### 2. 구조 (MAJOR 최대)
- **분량**: tactical_doc이 ep_count × {min_chars}자 미만이면 MAJOR
- **화 구분**: "제N화" 형식이 ep_count개 미만이면 MAJOR
- **필수 필드**: state_constraints, joint_docs 누락 시 MAJOR

#### 3. 서사 (MINOR 최대)
- **개연성**: 캐릭터 행동이 동기와 맞지 않으면 MINOR
- **일관성**: 이전 복선/갈등이 무시되면 MINOR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### [판정 기준]
- **REJECT**: CRITICAL 이슈 1개 이상 OR MAJOR 이슈 3개 이상
- **PASS**: 그 외

### [출력 형식 - 반드시 JSON만 출력]

{{
    "verdict": "PASS 또는 REJECT",
    "issues": [
        {{
            "severity": "CRITICAL/MAJOR/MINOR",
            "category": "continuity/structure/narrative",
            "issue": "문제 설명",
            "evidence": "근거",
            "fix_hint": "수정 방향"
        }}
    ],
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

    def __init__(self, context, client, model_tier: str = "gemini-2.5-flash"):
        super().__init__(context, client, model_tier)
        self.min_chars_per_ep = Stage2Limits.MIN_CHARS_PER_EPISODE

    def validate(
        self,
        arc: Dict,
        prev_arcs: List[Dict],
        constraints: str = "",
        state_tracker=None  # [V60.94] StateTracker (죽은 NPC 검증용)
    ) -> Tuple[str, Dict]:
        """
        Arc 통합 검증

        Args:
            arc: 검증할 Arc
            prev_arcs: 이전 Arc 리스트
            constraints: 제약 조건 텍스트
            state_tracker: [V60.94] StateTracker (죽은 NPC 검증용)

        Returns:
            (verdict, result) - "PASS"/"REJECT", 상세 결과
        """
        # ═══════════════════════════════════════════════════════════════
        # Phase A: Python 즉시 검증 (무료)
        # ═══════════════════════════════════════════════════════════════
        python_result = self._python_validate(arc, prev_arcs, state_tracker)

        # Python에서 CRITICAL 발견 시 LLM 스킵 (비용 절감)
        if python_result["has_critical"]:
            print(f"      🚨 [UnifiedValidator] Python CRITICAL 발견 - LLM 스킵")
            return "REJECT", {
                "verdict": "REJECT",
                "phase": "python",
                "issues": python_result["issues"],
                "summary": f"Python 검증에서 CRITICAL 이슈 발견: {python_result['critical_summary']}",
                "confidence": 1.0,
                "feedback": self._generate_feedback(python_result["issues"])
            }

        # ═══════════════════════════════════════════════════════════════
        # Phase B: LLM 문맥 검증 (유료)
        # ═══════════════════════════════════════════════════════════════
        print(f"      🔍 [UnifiedValidator] LLM 검증 중...")

        llm_result = self._llm_validate(arc, prev_arcs, constraints, python_result)

        # 결과 병합
        all_issues = python_result["issues"] + llm_result.get("issues", [])

        # 최종 판정
        critical_count = sum(1 for i in all_issues if i.get("severity") == "CRITICAL")
        major_count = sum(1 for i in all_issues if i.get("severity") == "MAJOR")

        if critical_count > 0 or major_count >= 3:
            verdict = "REJECT"
        else:
            verdict = llm_result.get("verdict", "PASS")

        result = {
            "verdict": verdict,
            "phase": "llm",
            "issues": all_issues,
            "summary": llm_result.get("summary", ""),
            "confidence": llm_result.get("confidence", 0.5),
            "feedback": self._generate_feedback(all_issues),
            "python_issues": len(python_result["issues"]),
            "llm_issues": len(llm_result.get("issues", []))
        }

        status = "✅ PASS" if verdict == "PASS" else "❌ REJECT"
        print(f"      {status} [UnifiedValidator] (CRITICAL:{critical_count}, MAJOR:{major_count})")

        return verdict, result

    def _python_validate(self, arc: Dict, prev_arcs: List[Dict], state_tracker=None) -> Dict:
        """Python 즉시 검증 (무료, 빠름)"""
        issues = []

        # [V60.94] 0. 죽은 NPC 등장 체크 (CRITICAL - REJECT 대상)
        if state_tracker and prev_arcs:
            arc_no = arc.get("arc_no", 0)
            tactical = arc.get("tactical_doc", "")
            if not isinstance(tactical, str):
                tactical = str(tactical) if tactical else ""

            dead_npc_violations = state_tracker.check_dead_npc_appearance(tactical, arc_no)
            for v in dead_npc_violations:
                issues.append({
                    "severity": "CRITICAL",
                    "category": "npc_death",
                    "issue": f"💀 죽은 NPC 등장: '{v.get('npc_name', '?')}'",
                    "evidence": f"Arc {v.get('death_arc', '?')}에서 사망, Arc {arc_no}에서 다시 등장",
                    "fix_hint": f"'{v.get('npc_name', '?')}'을(를) 등장시키지 마세요 (사망 NPC)"
                })
                print(f"      💀 [V60.94] REJECT: 죽은 NPC '{v.get('npc_name')}' 등장!")

            # [V60.95] NPC 무장/수준 변경 체크 (WARNING - 정당화 사유 필요)
            npc_changes = state_tracker.check_npc_changes(tactical, arc_no)
            for change in npc_changes:
                change_type = "무장" if change.get("change_type") == "weapon" else "수준"
                issues.append({
                    "severity": "WARNING",
                    "category": "npc_change",
                    "issue": f"⚠️ NPC {change_type} 변경: '{change.get('npc_name', '?')}'",
                    "evidence": change.get("reason", ""),
                    "fix_hint": f"'{change.get('npc_name', '?')}'의 {change_type} 변경에 대한 정당화 사유 필요 (습득, 성장 등)"
                })
                print(f"      ⚠️ [V60.95] WARNING: NPC '{change.get('npc_name')}' {change_type} 변경 감지")

        # 1. 분량 체크
        ep_count = arc.get("ep_count", 5)
        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str):
            tactical = str(tactical) if tactical else ""

        min_length = ep_count * self.min_chars_per_ep
        if len(tactical) < min_length:
            issues.append({
                "severity": "MAJOR",
                "category": "structure",
                "issue": f"tactical_doc 분량 부족: {len(tactical)}자 < {min_length}자",
                "evidence": f"ep_count={ep_count}, 필요={min_length}자",
                "fix_hint": f"tactical_doc을 {min_length}자 이상으로 작성"
            })

        # 2. 화 구분 체크
        ep_pattern = re.findall(r'제\s*\d+\s*화', tactical)
        if len(ep_pattern) < ep_count:
            issues.append({
                "severity": "MAJOR",
                "category": "structure",
                "issue": f"화 구분 부족: {len(ep_pattern)}개 < {ep_count}개",
                "evidence": f"'제N화' 패턴 {len(ep_pattern)}개 발견",
                "fix_hint": f"'제1화', '제2화' 등 {ep_count}개 섹션 명시"
            })

        # 3. 필수 필드 체크
        required_fields = ["arc_no", "ep_count", "tactical_doc", "state_constraints", "joint_docs"]
        for field in required_fields:
            if field not in arc or not arc[field]:
                issues.append({
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"필수 필드 누락: {field}",
                    "evidence": f"{field} 필드가 없거나 비어있음",
                    "fix_hint": f"{field} 필드를 올바르게 작성"
                })

        # 4. 중복 아이템 체크 (CRITICAL)
        if prev_arcs:
            prev_items = set()
            for prev in prev_arcs:
                acquired = prev.get("state_constraints", {}).get("items_acquired", [])
                if isinstance(acquired, list):
                    prev_items.update(item.strip() for item in acquired if item)

            current_acquired = arc.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(current_acquired, list):
                for item in current_acquired:
                    item_str = item.strip() if isinstance(item, str) else str(item)
                    if item_str in prev_items:
                        issues.append({
                            "severity": "CRITICAL",
                            "category": "continuity",
                            "issue": f"중복 아이템 획득: '{item_str}'",
                            "evidence": f"이전 Arc에서 이미 획득한 아이템",
                            "fix_hint": f"items_acquired에서 '{item_str}' 제거"
                        })

        # 5. 중복 수여물 체크 (CRITICAL)
        if prev_arcs:
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
                        issues.append({
                            "severity": "CRITICAL",
                            "category": "continuity",
                            "issue": f"중복 수여물: '{grant_str}'",
                            "evidence": f"이전 Arc에서 이미 수여받은 것",
                            "fix_hint": f"grants_received에서 '{grant_str}' 제거"
                        })

        has_critical = any(i["severity"] == "CRITICAL" for i in issues)
        critical_items = [i["issue"] for i in issues if i["severity"] == "CRITICAL"]

        return {
            "issues": issues,
            "has_critical": has_critical,
            "critical_summary": "; ".join(critical_items) if critical_items else ""
        }

    def _llm_validate(
        self,
        arc: Dict,
        prev_arcs: List[Dict],
        constraints: str,
        python_result: Dict
    ) -> Dict:
        """LLM 문맥 검증 (유료, 정확)"""

        # 이전 Arc 요약 생성
        prev_summary = self._generate_prev_summary(prev_arcs)

        # Python 결과 포맷팅
        python_text = self._format_python_result(python_result)

        # 프롬프트 생성
        prompt = UNIFIED_VALIDATION_PROMPT.format(
            arc_data=self._escape_braces(json.dumps(arc, ensure_ascii=False, indent=2)[:6000]),
            prev_summary=self._escape_braces(prev_summary),
            constraints=self._escape_braces(constraints[:3000] if constraints else "(없음)"),
            python_result=self._escape_braces(python_text),
            min_chars=self.min_chars_per_ep
        )

        try:
            response = self.ask(prompt, temperature=0.1)
            result = self._extract_json_robust(response)

            if not isinstance(result, dict):
                print(f"      ⚠️ [UnifiedValidator] JSON 파싱 실패")
                return {"verdict": "PASS", "issues": [], "summary": "LLM 응답 파싱 실패", "confidence": 0.0}

            return result

        except Exception as e:
            print(f"      ⚠️ [UnifiedValidator] LLM 오류: {str(e)[:50]}")
            return {"verdict": "PASS", "issues": [], "summary": f"LLM 오류: {str(e)[:50]}", "confidence": 0.0}

    def _generate_prev_summary(self, prev_arcs: List[Dict]) -> str:
        """이전 Arc 요약 생성"""
        if not prev_arcs:
            return "첫 Arc (이전 Arc 없음)"

        lines = []
        for arc in prev_arcs[-3:]:  # 최근 3개만
            arc_no = arc.get("arc_no", "?")
            state = arc.get("state_constraints", {})
            joint = arc.get("joint_docs", {})
            shadow = arc.get("status_shadow", {})

            # arc_end_state 우선
            arc_end = state.get("arc_end_state", {})
            final_location = arc_end.get("location") or joint.get("final_location", "?")
            final_energy = arc_end.get("internal_energy")
            if final_energy is None:
                loss_str = shadow.get("internal_energy_loss", "0%")
                try:
                    loss = int(re.search(r'(\d+)', str(loss_str)).group(1))
                    final_energy = 100 - loss
                except:
                    final_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK

            lines.append(f"[Arc {arc_no}]")
            lines.append(f"  종료 위치: {final_location}")
            lines.append(f"  최종 내공: {final_energy}%")
            lines.append(f"  소지품: {joint.get('physical_inventory', [])}")
            lines.append(f"  획득 아이템: {state.get('items_acquired', [])}")
            lines.append(f"  수여물: {state.get('grants_received', [])}")

        return "\n".join(lines)

    def _format_python_result(self, python_result: Dict) -> str:
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

    def _generate_feedback(self, issues: List[Dict]) -> str:
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
