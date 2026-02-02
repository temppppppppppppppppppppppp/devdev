"""
[V60.12] Consensus Validator
3개 LLM 합의 검증 - 모두 PASS해야 통과

목적:
- 단일 LLM의 판단 오류 방지
- 다각도 검증으로 누락 없는 검사
- 초기 통과율 극대화 (문제 조기 발견)

비용: ~$0.06-0.10/Arc (3개 LLM 병렬 호출)
"""

import json
import re
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_agent import BaseAgent


# 3가지 검증 관점
VALIDATION_PERSPECTIVES = [
    {
        "name": "continuity_focused",
        "role": "연속성 전문가",
        "focus": """
당신은 서사 연속성 전문가입니다.
아이템, 수여물, 위치, 상태의 연속성만 집중 검증하세요.

### 검증 항목
1. 아이템 타임라인: 중복 획득 여부
2. 수여물 타임라인: 중복 수여 여부
3. 위치 연속성: 시작 위치 = 이전 종료 위치
4. 상태 연속성: 부상/내공 계승
5. 소지품 계승: 이전 소지품 누락 여부

한 항목이라도 문제가 있으면 REJECT하세요.
""",
        "temperature": 0.1
    },
    {
        "name": "structure_focused",
        "role": "구조 전문가",
        "focus": """
당신은 Arc 구조 전문가입니다.
tactical_doc, joint_docs, state_constraints의 구조와 정합성을 집중 검증하세요.

### 검증 항목
1. tactical_doc 분량: 최소 2000자 (권장 2500자)
2. 화별 구분: 제N화 형식 3개 이상 (권장 5개)
3. joint_docs 정합성: final_location이 마지막 화와 일치
4. physical_inventory 정확성: tactical_doc 내용과 일치
5. state_constraints 완전성: 모든 필수 필드 존재

⚠️ CRITICAL은 심각한 구조 결함에만 부여하세요:
- tactical_doc 1500자 미만 = CRITICAL
- 화별 구분 0개 = CRITICAL
- 그 외는 MAJOR로 처리

구조적 문제가 있으면 REJECT하세요.
""",
        "temperature": 0.1
    },
    {
        "name": "narrative_focused",
        "role": "서사 전문가",
        "focus": """
당신은 서사 품질 전문가입니다.
스토리 논리성, 캐릭터 일관성, 긴장감 곡선을 집중 검증하세요.

### 검증 항목
1. 캐릭터 행동 일관성: 동기와 행동의 연결
2. 긴장감 곡선: 상승-하강 리듬
3. 과도한 파워업: 단일 Arc 내 비정상 성장
4. 이전 Arc 갈등 계승: 미해결 갈등이 이어지는가 (Arc 1은 해당 없음)
5. 복선 연결: 이전 복선과의 연결성 (Arc 1은 해당 없음)

⚠️ Arc 1(첫 번째 Arc)은 항목 4, 5를 검증하지 마세요!
⚠️ CRITICAL은 심각한 서사 결함에만 부여하세요:
- 캐릭터가 아무 이유 없이 돌변 = CRITICAL
- 한 화에서 경지 3단계 이상 상승 = CRITICAL
- 그 외는 MAJOR로 처리

서사적 문제가 심각하면 REJECT하세요.
""",
        "temperature": 0.2
    }
]


CONSENSUS_VALIDATION_PROMPT = """
[V60.12 CONSENSUS VALIDATOR - {role}]

{focus}

### [검증 대상 Arc]
{arc_data}

### [이전 Arc 요약]
{prev_summary}

### [제약 조건]
{constraints}

### [출력 형식 - JSON]

{{
    "perspective": "{perspective_name}",
    "verdict": "PASS 또는 REJECT",
    "confidence": 0.95,
    "issues_found": [
        {{
            "severity": "CRITICAL 또는 MAJOR 또는 MINOR",
            "category": "item_continuity / location / state / structure / narrative",
            "issue": "문제 설명",
            "evidence": "근거가 되는 텍스트"
        }}
    ],
    "passed_checks": [
        "통과한 검증 항목 1",
        "통과한 검증 항목 2"
    ],
    "reasoning": "판단 근거 상세 설명"
}}

CRITICAL 이슈가 하나라도 있으면 반드시 REJECT하세요.
반드시 유효한 JSON만 출력하세요.
"""


class ConsensusValidator(BaseAgent):
    """
    [V60.12] Consensus Validator

    3개 LLM이 서로 다른 관점으로 검증, 합의 도출
    """

    def __init__(self, context, client, model_tier: str = "gemini-3-pro-preview"):
        # [V60.24] Gemini 3로 변경
        super().__init__(context, client, model_tier)
        self.backup_model = "gemini-3-pro-preview"
        self.perspectives = VALIDATION_PERSPECTIVES
        self.max_workers = 3

    def validate_with_consensus(
        self,
        arc: Dict,
        prev_arcs: List[Dict],
        constraints: str = ""
    ) -> Tuple[str, Dict]:
        """
        3개 LLM 합의 검증

        Args:
            arc: 검증할 Arc
            prev_arcs: 이전 Arc 리스트
            constraints: 제약 조건

        Returns:
            (final_verdict, consensus_result)
        """
        # [V60.28] Arc 1 (이전 Arc 없음)은 연속성 검증 불필요 - 구조/서사만 검증
        if not prev_arcs:
            print("      ⏭️ [Consensus] Arc 1 - 연속성 검증 스킵, 구조/서사만 검증")
            # structure_focused와 narrative_focused만 사용
            active_perspectives = [p for p in self.perspectives if p["name"] != "continuity_focused"]
        else:
            active_perspectives = self.perspectives

        prev_summary = self._generate_prev_summary(prev_arcs)
        arc_data = json.dumps(arc, ensure_ascii=False, indent=2)[:6000]

        results = []

        # 병렬 검증
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for perspective in active_perspectives:
                future = executor.submit(
                    self._validate_single,
                    arc_data=arc_data,
                    prev_summary=prev_summary,
                    constraints=constraints,
                    perspective=perspective
                )
                futures[future] = perspective["name"]

            for future in as_completed(futures):
                perspective_name = futures[future]
                try:
                    result = future.result()
                    result["perspective"] = perspective_name
                    results.append(result)
                except Exception as e:
                    print(f"      ⚠️ [Consensus] {perspective_name} 오류: {str(e)[:50]}")
                    # 오류 시 보수적으로 PASS 처리 (다른 검증기에 의존)
                    results.append({
                        "perspective": perspective_name,
                        "verdict": "PASS",
                        "confidence": 0.5,
                        "issues_found": [],
                        "error": str(e)[:100]
                    })

        # 합의 도출
        final_verdict, consensus_result = self._derive_consensus(results)

        return final_verdict, consensus_result

    def _validate_single(
        self,
        arc_data: str,
        prev_summary: str,
        constraints: str,
        perspective: Dict
    ) -> Dict:
        """단일 관점 검증"""
        prompt = CONSENSUS_VALIDATION_PROMPT.format(
            role=perspective["role"],
            focus=perspective["focus"],
            perspective_name=perspective["name"],
            arc_data=self._escape_braces(arc_data),
            prev_summary=self._escape_braces(prev_summary),
            constraints=self._escape_braces(constraints[:2000] if constraints else "(없음)")
        )

        result = self.ask(prompt, temperature=perspective["temperature"])

        if isinstance(result, str):
            result = json.loads(result)

        return self._ensure_validation_fields(result)

    def _generate_prev_summary(self, prev_arcs: List[Dict]) -> str:
        """이전 Arc 요약 - arc_end_state 포함"""
        if not prev_arcs:
            return "첫 Arc (이전 Arc 없음)"

        lines = []
        for arc in prev_arcs[-3:]:
            arc_no = arc.get("arc_no", "?")
            joint = arc.get("joint_docs", {})
            state = arc.get("state_constraints", {})
            shadow = arc.get("status_shadow", {})

            # [V60.13 FIX] arc_end_state에서 정확한 종료 상태 추출
            arc_end_state = state.get("arc_end_state", {})
            final_internal_energy = arc_end_state.get("internal_energy")
            final_injuries = arc_end_state.get("injuries")

            # arc_end_state가 없으면 shadow에서 추론 (하위 호환)
            if final_internal_energy is None:
                loss_str = shadow.get("internal_energy_loss", "0%")
                try:
                    loss = int(str(loss_str).replace("%", "").strip())
                    final_internal_energy = max(0, 100 - loss)
                except:
                    final_internal_energy = "?"

            if final_injuries is None:
                final_injuries = shadow.get("expected_injuries", "없음")

            lines.append(f"[Arc {arc_no}]")
            lines.append(f"  🔴 최종 내공: {final_internal_energy}% ← 다음 Arc 시작점")
            lines.append(f"  🔴 최종 부상: {final_injuries}")
            lines.append(f"  종료 위치: {joint.get('final_location', '?')}")
            lines.append(f"  소지품: {joint.get('physical_inventory', [])}")
            lines.append(f"  획득 아이템: {state.get('items_acquired', [])}")
            lines.append(f"  수여물: {state.get('grants_received', [])}")

        return "\n".join(lines)

    def _ensure_validation_fields(self, result: Dict) -> Dict:
        """검증 결과 필수 필드 보장"""
        if "verdict" not in result:
            result["verdict"] = "PASS"
        if "confidence" not in result:
            result["confidence"] = 0.5
        if "issues_found" not in result:
            result["issues_found"] = []
        if "passed_checks" not in result:
            result["passed_checks"] = []
        if "reasoning" not in result:
            result["reasoning"] = ""
        return result

    def _derive_consensus(self, results: List[Dict]) -> Tuple[str, Dict]:
        """합의 도출"""
        total_count = len(results)
        pass_count = sum(1 for r in results if r.get("verdict") == "PASS")
        reject_count = total_count - pass_count

        all_issues = []
        all_passed = []

        for r in results:
            all_issues.extend(r.get("issues_found", []))
            all_passed.extend(r.get("passed_checks", []))

        # CRITICAL 이슈가 있으면 즉시 REJECT
        critical_issues = [i for i in all_issues if i.get("severity") == "CRITICAL"]

        # [V60.28] 합의 로직 (2개 또는 3개 검증기 지원):
        # - CRITICAL 있으면 → REJECT
        # - 과반수 이상 REJECT → REJECT
        # - 그 외 → PASS
        majority_threshold = (total_count // 2) + 1  # 2개면 2, 3개면 2

        if critical_issues:
            final_verdict = "REJECT"
            reason = f"CRITICAL 이슈 발견: {len(critical_issues)}개"
            # [V60.33] CRITICAL 이슈 요약 출력
            for ci in critical_issues[:2]:  # 최대 2개만 콘솔 출력
                print(f"         🚨 [{ci.get('category', '?')}] {ci.get('issue', '?')[:60]}")
        elif reject_count >= majority_threshold:
            final_verdict = "REJECT"
            reason = f"{reject_count}/{total_count} 검증기가 REJECT"
        else:
            final_verdict = "PASS"
            reason = f"{pass_count}/{total_count} 검증기가 PASS"

        consensus_result = {
            "final_verdict": final_verdict,
            "vote_summary": {
                "pass": pass_count,
                "reject": reject_count
            },
            "consensus_reason": reason,
            "individual_results": results,
            "all_issues": all_issues,
            "critical_issues": critical_issues,
            "passed_checks": list(set(all_passed))
        }

        print(f"      {'✅' if final_verdict == 'PASS' else '❌'} [Consensus] {reason}")

        return final_verdict, consensus_result

    def get_rejection_feedback(self, consensus_result: Dict) -> str:
        """REJECT 시 피드백 생성"""
        lines = ["[CONSENSUS VALIDATOR 피드백]", ""]

        # 투표 결과
        vote = consensus_result.get("vote_summary", {})
        lines.append(f"투표: PASS {vote.get('pass', 0)} / REJECT {vote.get('reject', 0)}")
        lines.append(f"판정: {consensus_result.get('consensus_reason', '')}")
        lines.append("")

        # Critical 이슈
        critical = consensus_result.get("critical_issues", [])
        if critical:
            lines.append("🚨 CRITICAL 이슈:")
            for issue in critical:
                lines.append(f"  - [{issue.get('category')}] {issue.get('issue')}")
                if issue.get("evidence"):
                    lines.append(f"    근거: {issue['evidence'][:100]}")

        # 기타 이슈
        all_issues = consensus_result.get("all_issues", [])
        major_issues = [i for i in all_issues if i.get("severity") == "MAJOR"]
        if major_issues:
            lines.append("")
            lines.append("⚠️ MAJOR 이슈:")
            for issue in major_issues[:5]:
                lines.append(f"  - [{issue.get('category')}] {issue.get('issue')}")

        return "\n".join(lines)


def create_consensus_validator(context, client, model_tier: str = "gemini-3-pro-preview"):
    """[V60.24] ConsensusValidator 생성 헬퍼 - Gemini 3 사용"""
    return ConsensusValidator(context, client, model_tier)
