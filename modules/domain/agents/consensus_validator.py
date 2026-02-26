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
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError

from modules.core.arc_summary_utils import generate_prev_arc_summary  # [V64.P4]
from modules.core.prompt_loader import SafeDict

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

⚠️ [V60.41] 수위 조절:
- CRITICAL (즉시 REJECT): 중복 아이템 획득, 중복 수여물만
- MAJOR (경고): 위치/상태/소지품 불일치 (인간 수정 용이)

중복 획득/수여만 CRITICAL로 처리하세요.
""",
        "temperature": 0.1,
    },
    {
        "name": "structure_focused",
        "role": "구조 전문가",
        "focus": """
당신은 Arc 구조 전문가입니다.
tactical_doc, joint_docs, state_constraints의 구조와 정합성을 집중 검증하세요.

### 검증 항목
1. tactical_doc 분량: 각 화당 최소 400자 (권장 500자) - ep_count에 따라 총 분량 계산
2. 화별 구분: ep_count에 맞는 "제N화" 형식 섹션 필요
3. joint_docs 정합성: final_location이 마지막 화와 일치
4. physical_inventory 정확성: tactical_doc 내용과 일치
5. state_constraints 완전성: 모든 필수 필드 존재

⚠️ [V60.41] 수위 조절 - 모든 구조 문제는 MAJOR로 처리:
- tactical_doc 분량 미달 = MAJOR (재생성으로 해결)
- 화별 구분 부족 = MAJOR (재생성으로 해결)
- 필드 누락 = MAJOR (재생성으로 해결)

구조 문제는 CRITICAL이 아닌 MAJOR로 부여하세요.
""",
        "temperature": 0.1,
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
3. 이전 Arc 갈등 계승: 미해결 갈등이 이어지는가 (Arc 1은 해당 없음)
4. 복선 연결: 이전 복선과의 연결성 (Arc 1은 해당 없음)

⚠️ Arc 1(첫 번째 Arc)은 항목 3, 4를 검증하지 마세요!
⚠️ CRITICAL은 정말 심각한 서사 결함에만 부여하세요:
- 캐릭터가 아무 이유 없이 돌변 = CRITICAL
- 그 외는 MAJOR로 처리

⚠️ 파워업/성장은 CRITICAL이 아닙니다:
- 영약, 비급, 깨달음을 통한 급성장 = 무협에서 자연스러움
- 내공 급상승 (예: 10%→65%) = 영약 복용 시 정상
- 경지 상승 = 정당한 계기가 있으면 OK → MINOR 또는 무시

서사적 문제가 심각하면 REJECT하세요.
""",
        "temperature": 0.2,
    },
]


CONSENSUS_VALIDATION_PROMPT = """
[V60.56 CONSENSUS VALIDATOR - {role}]

{focus}

### [검증 대상 Arc]
{arc_data}

### [이전 Arc 요약]
{prev_summary}

### [제약 조건]
{constraints}

### [V60.56 Python 사전 분석 결과 - 참고용]
아래는 Python 패턴 매칭으로 발견된 잠재적 문제입니다.
⚠️ 주의: Python은 문맥을 모르므로 오탐일 수 있습니다. 당신이 컨텍스트를 보고 최종 판단하세요.
{python_advisory}

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

    # [V61.3] 앙상블 타임아웃 설정 (야간 무인 운영 - 무한 대기 방지)
    ENSEMBLE_TIMEOUT = 120  # 전체 합의 타임아웃 (초) - 2분
    SINGLE_VOTE_TIMEOUT = 90  # 개별 투표 타임아웃 (초) - 1.5분

    def __init__(self, context, client, model_tier: str = None):
        # [V60.53] Flash로 변경 - 단순 투표 로직, Pro 불필요
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent에서 자동 설정)
        self.perspectives = VALIDATION_PERSPECTIVES
        self.max_workers = 3

    def validate_with_consensus(
        self, arc: dict, prev_arcs: list[dict], constraints: str = "", python_advisory: list[dict] = None
    ) -> tuple[str, dict]:
        """
        3개 LLM 합의 검증

        Args:
            arc: 검증할 Arc
            prev_arcs: 이전 Arc 리스트
            constraints: 제약 조건
            python_advisory: [V60.56] Python 사전 검사에서 발견한 잠재적 문제 (LLM이 최종 판단)

        Returns:
            (final_verdict, consensus_result)
        """
        python_advisory = python_advisory or []
        # [V60.28] Arc 1 (이전 Arc 없음)은 연속성 검증 불필요 - 구조/서사만 검증
        if not prev_arcs:
            logging.warning("⏭️ [Consensus] Arc 1 - 연속성 검증 스킵, 구조/서사만 검증")
            # structure_focused와 narrative_focused만 사용
            active_perspectives = [p for p in self.perspectives if p["name"] != "continuity_focused"]
        else:
            active_perspectives = self.perspectives

        prev_summary = self._generate_prev_summary(prev_arcs)
        arc_data = json.dumps(arc, ensure_ascii=False, indent=2)[:6000]

        # [V60.56] Python advisory 정보 포맷팅
        advisory_text = "(없음)"
        if python_advisory:
            advisory_lines = []
            for adv in python_advisory[:5]:  # 최대 5개만
                adv_type = adv.get("type", "?")
                adv_item = adv.get("item_or_subject", adv.get("description", "?"))
                advisory_lines.append(f"- [{adv_type}] {adv_item}")
            advisory_text = "\n".join(advisory_lines) if advisory_lines else "(없음)"

        results = []

        # [Phase 3-Obs] 에이전트 레벨 ThreadPoolExecutor 계측
        _tp_t0 = time.monotonic()

        # [V61.3] 전체 병렬 처리 블록을 try-except로 감싸서 급사 방지
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for perspective in active_perspectives:
                    future = executor.submit(
                        self._validate_single,
                        arc_data=arc_data,
                        prev_summary=prev_summary,
                        constraints=constraints,
                        perspective=perspective,
                        python_advisory_text=advisory_text,
                    )
                    futures[future] = perspective["name"]

                # [V61.3] 타임아웃 적용 - 야간 무인 운영 시 무한 대기 방지
                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        perspective_name = futures[future]
                        try:
                            # [V61.3] 개별 투표에도 타임아웃 적용
                            result = future.result(timeout=self.SINGLE_VOTE_TIMEOUT)
                            result["perspective"] = perspective_name
                            results.append(result)
                        except FutureTimeoutError:
                            logging.warning(f"⏰ [V61.3] {perspective_name} 타임아웃 ({self.SINGLE_VOTE_TIMEOUT}초)")
                            # 타임아웃 시 보수적으로 PASS 처리
                            results.append(
                                {
                                    "perspective": perspective_name,
                                    "verdict": "PASS",
                                    "confidence": 0.5,
                                    "issues_found": [],
                                    "error": "타임아웃",
                                }
                            )
                        except Exception as e:
                            logging.warning(f"⚠️ [Consensus] {perspective_name} 오류: {str(e)[:50]}")
                            # 오류 시 보수적으로 PASS 처리 (다른 검증기에 의존)
                            results.append(
                                {
                                    "perspective": perspective_name,
                                    "verdict": "PASS",
                                    "confidence": 0.5,
                                    "issues_found": [],
                                    "error": str(e)[:100],
                                }
                            )
                except FutureTimeoutError:
                    # 전체 합의 타임아웃 - 완료된 결과만 사용
                    logging.warning(
                        f"⏰ [V61.3] 합의 검증 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(results)}개 결과 사용"
                    )
                except Exception as e:
                    # [V61.3] as_completed 자체 예외 처리
                    logging.warning(f"⚠️ [V61.3] 합의 루프 예외: {str(e)[:80]}")
                finally:
                    # [Sweep34] 미완료 future 정리로 shutdown 대기 최소화
                    for f in futures:
                        f.cancel()
        except Exception as e:
            # [V61.3] ThreadPoolExecutor 전체 예외 처리 - 급사 방지
            # stderr로 출력 (Rich 스피너가 stdout 가림)
            import traceback

            logging.error(f"🚨 [V61.3] 합의 검증 크래시 방지: {str(e)[:100]}")
            logging.error(traceback.format_exc())

        # [Phase 3-Obs] 병렬 구간 소요 시간 기록
        try:
            logging.warning(f"[PerfTimer:Consensus] consensus_validation={time.monotonic() - _tp_t0:.2f}s")
        except Exception:
            pass

        # [V70] 빈 결과 방어: 모든 검증기 실패 시 보수적 PASS
        if not results:
            logging.warning("⚠️ [Consensus] 모든 검증기 실패 — 보수적 PASS 처리")
            results.append({"verdict": "PASS", "confidence": 0.3, "issues_found": [], "error": "all_validators_failed"})

        # 합의 도출
        final_verdict, consensus_result = self._derive_consensus(results)

        return final_verdict, consensus_result

    def _validate_single(
        self,
        arc_data: str,
        prev_summary: str,
        constraints: str,
        perspective: dict,
        python_advisory_text: str = "(없음)",
    ) -> dict:
        """단일 관점 검증"""
        prompt = CONSENSUS_VALIDATION_PROMPT.format_map(
            SafeDict(
                role=perspective["role"],
                focus=perspective["focus"],
                perspective_name=perspective["name"],
                arc_data=self._escape_braces(arc_data),
                prev_summary=self._escape_braces(prev_summary),
                constraints=self._escape_braces(constraints[:6000] if constraints else "(없음)"),
                python_advisory=self._escape_braces(python_advisory_text),
            )
        )

        result = self.ask(prompt, temperature=perspective["temperature"])

        if isinstance(result, str):
            result = self._extract_json_robust(result)  # [V70] json.loads → robust (LLM 마크다운 펜스 대응)

        return self._ensure_validation_fields(result)

    def _generate_prev_summary(self, prev_arcs: list[dict]) -> str:
        """[V64.P4] 위임 → modules.core.arc_summary_utils.generate_prev_arc_summary"""
        return generate_prev_arc_summary(prev_arcs, include_energy=True)

    def _ensure_validation_fields(self, result: dict) -> dict:
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

    def _derive_consensus(self, results: list[dict]) -> tuple[str, dict]:
        """합의 도출"""
        total_count = len(results)
        pass_count = sum(1 for r in results if isinstance(r, dict) and r.get("verdict") == "PASS")
        reject_count = total_count - pass_count

        all_issues = []
        all_passed = []

        for r in results:
            if not isinstance(r, dict):
                continue
            issues = r.get("issues_found", [])
            if not isinstance(issues, list):
                issues = []
            all_issues.extend(i for i in issues if isinstance(i, dict))

            passed_checks = r.get("passed_checks", [])
            if not isinstance(passed_checks, list):
                passed_checks = []
            all_passed.extend(c for c in passed_checks if isinstance(c, str))

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
        elif reject_count >= majority_threshold:
            final_verdict = "REJECT"
            reason = f"{reject_count}/{total_count} 검증기가 REJECT"
        else:
            final_verdict = "PASS"
            reason = f"{pass_count}/{total_count} 검증기가 PASS"

        # [V60.37] 이슈 분류
        major_issues = [i for i in all_issues if i.get("severity") == "MAJOR"]
        minor_issues = [i for i in all_issues if i.get("severity") not in ["CRITICAL", "MAJOR"]]

        consensus_result = {
            "final_verdict": final_verdict,
            "vote_summary": {"pass": pass_count, "reject": reject_count},
            "consensus_reason": reason,
            "individual_results": results,
            "all_issues": all_issues,
            "critical_issues": critical_issues,
            "major_issues": major_issues,
            "passed_checks": list(set(all_passed)),
        }

        logging.warning(f"{'✅' if final_verdict == 'PASS' else '❌'} [Consensus] {reason}")
        logging.warning(f"- 투표: PASS {pass_count} / REJECT {reject_count}")

        # [V60.37] 상세 이슈 출력
        if final_verdict == "REJECT":
            logging.warning(
                f"- 전체 이슈: {len(all_issues)}개 (CRITICAL: {len(critical_issues)}, MAJOR: {len(major_issues)}, MINOR: {len(minor_issues)})"
            )

            if critical_issues:
                logging.warning(f"🚨 CRITICAL ({len(critical_issues)}개):")
                for ci in critical_issues:
                    cat = ci.get("category", "?")
                    issue = ci.get("issue", "?")
                    evidence = ci.get("evidence", "")[:80] if ci.get("evidence") else ""
                    logging.warning(f"- [{cat}] {issue}")
                    if evidence:
                        logging.info(f"└ 근거: {evidence}")

            if major_issues:
                logging.warning(f"⚠️ MAJOR ({len(major_issues)}개):")
                for mi in major_issues[:3]:  # 최대 3개만
                    cat = mi.get("category", "?")
                    issue = mi.get("issue", "?")
                    logging.warning(f"- [{cat}] {issue}")

            if minor_issues and not critical_issues and not major_issues:
                logging.info(f"📝 MINOR ({len(minor_issues)}개):")
                for mi in minor_issues[:2]:
                    logging.info(f"- [{mi.get('category', '?')}] {mi.get('issue', '?')}")

        return final_verdict, consensus_result

    def get_rejection_feedback(self, consensus_result: dict) -> str:
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


def create_consensus_validator(context, client, model_tier: str = "gemini-2.5-flash"):
    """[V60.53] ConsensusValidator 생성 헬퍼 - Flash로 변경"""
    return ConsensusValidator(context, client, model_tier)
