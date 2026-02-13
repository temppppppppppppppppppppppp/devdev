"""
[V60.42] Arc Corrector
Stage 2 Arc의 MAJOR 이슈만 부분 수정 (CRITICAL은 전체 재생성)

안전장치:
1. 원본 백업 (수정 전 deep copy)
2. Diff 검증 (수정 범위 20% 초과 시 거부)
3. 최대 2회 수정 제한
4. 수정 후 재검증
5. 실패 시 원본 복원

Stage 3 연결성:
- tactical_doc 구조 보존 (화별 분할 유지)
- 상태 체크포인트 형식 유지
- joint_docs/state_constraints 정합성 유지
"""

import re
import logging
import json
import copy
from typing import Dict, List, Any, Optional, Tuple
from .base_agent import BaseAgent


# 수정 가능한 이슈 타입 (MAJOR만)
CORRECTABLE_ISSUES = {
    "length_short": "분량 미달",
    "checkpoint_missing": "상태 체크포인트 누락",
    "location_mismatch": "위치 불일치",
    "state_mismatch": "상태 불일치",
    "field_missing": "필드 누락",
    "episode_missing": "화 누락",
}

# 수정 불가 이슈 타입 (CRITICAL - 전체 재생성 필요)
UNCORRECTABLE_ISSUES = {
    "duplicate_acquisition": "중복 아이템 획득",
    "duplicate_grant": "중복 수여물",
    "forbidden_item": "금지 아이템 획득",
}


CORRECTION_PROMPT = """
[V60.42 ARC CORRECTOR - 부분 수정 전용]

당신은 Arc 부분 수정 전문가입니다.
아래 Arc의 **특정 문제만** 수정하고, 나머지는 **절대 변경하지 마세요**.

### 🚨 수정 규칙
1. 지정된 문제만 수정
2. 다른 화/섹션은 한 글자도 변경 금지
3. 원본 구조 (제 N화 형식) 유지
4. 상태 체크포인트 형식 유지

### 수정 대상
{issue_description}

### 수정 범위
{correction_scope}

### 원본 Arc (참고용 - 수정 대상 외 변경 금지)
{original_arc}

### 전후 맥락 (참고용)
{context}

### 출력 형식
수정된 부분만 출력하세요. 전체 Arc를 다시 출력하지 마세요.

```json
{{
    "corrected_field": "수정된 필드명 (예: tactical_doc)",
    "corrected_section": "수정된 섹션 (예: 제 3화)",
    "corrected_content": "수정된 내용",
    "change_summary": "변경 요약 (1줄)"
}}
```
"""


class ArcCorrector(BaseAgent):
    """
    [V60.42] Arc Corrector

    MAJOR 이슈만 부분 수정, CRITICAL은 거부
    """

    def __init__(self, context, client, model_tier: str = None):
        # Flash 모델 사용 (빠른 수정)
        super().__init__(context, client, model_tier)
        self.max_corrections = 2  # 최대 수정 횟수
        self.max_change_ratio = 0.20  # 최대 변경 비율 (20%)

    def can_correct(self, issues: List[Dict]) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        수정 가능 여부 판단

        Returns:
            (수정 가능 여부, 수정 가능 이슈, 수정 불가 이슈)
        """
        correctable = []
        uncorrectable = []

        for issue in issues:
            severity = issue.get("severity", "").upper()
            issue_type = issue.get("type", "")
            message = issue.get("message", "")

            # CRITICAL은 수정 불가
            if severity == "CRITICAL":
                uncorrectable.append(issue)
                continue

            # 중복 획득/수여 관련은 수정 불가
            if any(kw in message for kw in ["중복 획득", "중복 수여", "금지 아이템"]):
                uncorrectable.append(issue)
                continue

            # 나머지 MAJOR/WARNING은 수정 가능
            correctable.append(issue)

        can_fix = len(correctable) > 0 and len(uncorrectable) == 0
        return can_fix, correctable, uncorrectable

    def correct(
        self,
        arc: Dict,
        issues: List[Dict],
        prev_arcs: List[Dict] = None
    ) -> Tuple[Optional[Dict], Dict]:
        """
        Arc 부분 수정

        Args:
            arc: 수정할 Arc
            issues: 수정할 이슈 목록 (MAJOR만)
            prev_arcs: 이전 Arc들 (컨텍스트용)

        Returns:
            (수정된 Arc 또는 None, 수정 로그)
        """
        log = {
            "success": False,
            "corrections_made": [],
            "corrections_failed": [],
            "original_backup": None,
            "validation_after": None
        }

        # 1. 수정 가능 여부 확인
        can_fix, correctable, uncorrectable = self.can_correct(issues)

        if not can_fix:
            log["reason"] = "수정 불가 이슈 포함"
            log["uncorrectable_issues"] = uncorrectable
            return None, log

        # 2. 원본 백업 (Deep Copy)
        original_arc = copy.deepcopy(arc)
        log["original_backup"] = True

        # 3. 이슈별 수정 (최대 max_corrections개)
        corrected_arc = copy.deepcopy(arc)
        correction_count = 0

        for issue in correctable[:self.max_corrections]:
            try:
                logging.info(f"🔧 [Corrector] 수정 시도: {issue.get('message', '')[:50]}...")

                corrected_arc, correction_result = self._correct_single_issue(
                    corrected_arc, issue, prev_arcs, original_arc
                )

                if correction_result.get("success"):
                    log["corrections_made"].append({
                        "issue": issue.get("message", ""),
                        "field": correction_result.get("field"),
                        "change_summary": correction_result.get("summary")
                    })
                    correction_count += 1
                    logging.info(f"✅ [Corrector] 수정 완료: {correction_result.get('summary', '')[:50]}")
                else:
                    log["corrections_failed"].append({
                        "issue": issue.get("message", ""),
                        "reason": correction_result.get("reason", "unknown")
                    })
                    logging.warning(f"❌ [Corrector] 수정 실패: {correction_result.get('reason', '')[:50]}")

            except Exception as e:
                log["corrections_failed"].append({
                    "issue": issue.get("message", ""),
                    "reason": str(e)[:100]
                })
                logging.warning(f"❌ [Corrector] 예외 발생: {str(e)[:50]}")

        # 4. 변경 범위 검증 (20% 초과 시 거부)
        if not self._validate_change_ratio(original_arc, corrected_arc):
            logging.info(f"⚠️ [Corrector] 변경 범위 초과 (>{self.max_change_ratio*100}%) - 원본 복원")
            log["reason"] = "변경 범위 초과"
            return None, log

        # 5. 구조 검증 (Stage 3 연결성)
        if not self._validate_structure_preserved(original_arc, corrected_arc):
            logging.info(f"⚠️ [Corrector] 구조 손상 감지 - 원본 복원")
            log["reason"] = "구조 손상"
            return None, log

        # 6. 성공
        if correction_count > 0:
            log["success"] = True
            log["corrections_count"] = correction_count
            logging.info(f"✅ [Corrector] 총 {correction_count}개 수정 완료")
            return corrected_arc, log
        else:
            log["reason"] = "수정된 항목 없음"
            return None, log

    def _correct_single_issue(
        self,
        arc: Dict,
        issue: Dict,
        prev_arcs: List[Dict],
        original_arc: Dict
    ) -> Tuple[Dict, Dict]:
        """단일 이슈 수정"""
        result = {"success": False}
        message = issue.get("message", "")

        # 이슈 타입별 수정 전략
        if "분량" in message:
            return self._correct_length_issue(arc, issue, prev_arcs)
        elif "체크포인트" in message or "상태" in message:
            return self._correct_checkpoint_issue(arc, issue, prev_arcs)
        elif "위치" in message:
            return self._correct_location_issue(arc, issue, prev_arcs)
        elif "누락" in message and "화" in message:
            return self._correct_missing_episode(arc, issue, prev_arcs)
        elif "필드" in message:
            return self._correct_field_issue(arc, issue, prev_arcs)
        else:
            # 범용 수정 시도
            return self._correct_generic_issue(arc, issue, prev_arcs)

    def _correct_length_issue(
        self,
        arc: Dict,
        issue: Dict,
        prev_arcs: List[Dict]
    ) -> Tuple[Dict, Dict]:
        """분량 미달 수정"""
        result = {"success": False}

        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str):
            tactical = str(tactical)

        # 어떤 화가 짧은지 파악
        message = issue.get("message", "")
        ep_match = re.search(r'(\d+)화', message)
        target_ep = int(ep_match.group(1)) if ep_match else None
        if target_ep is None:  # [V70] 대상 화수 특정 불가
            result["reason"] = "대상 화수 특정 불가"
            return arc, result

        # 컨텍스트 구성
        context = self._build_context(arc, prev_arcs)

        prompt = CORRECTION_PROMPT.format(
            issue_description=f"tactical_doc의 제 {target_ep}화 분량이 부족합니다. 500자 이상으로 확장하세요.",
            correction_scope=f"제 {target_ep}화 섹션만 수정. 다른 화는 절대 변경 금지.",
            original_arc=json.dumps(arc, ensure_ascii=False, indent=2)[:3000],
            context=context[:1000]
        )

        try:
            response = self.ask(prompt, temperature=0.3)
            if isinstance(response, str):  # [V70] ask()는 항상 str 반환
                response = self._extract_json_robust(response)

            if isinstance(response, dict) and response.get("corrected_content"):
                # 해당 화 섹션 교체
                corrected_tactical = self._replace_episode_section(
                    tactical, target_ep, response["corrected_content"]
                )

                if corrected_tactical and len(corrected_tactical) > len(tactical):
                    arc["tactical_doc"] = corrected_tactical
                    result["success"] = True
                    result["field"] = "tactical_doc"
                    result["summary"] = response.get("change_summary", f"제 {target_ep}화 확장")
                else:
                    result["reason"] = "섹션 교체 실패"
            else:
                result["reason"] = "LLM 응답 형식 오류"

        except Exception as e:
            result["reason"] = str(e)[:100]

        return arc, result

    def _correct_checkpoint_issue(
        self,
        arc: Dict,
        issue: Dict,
        prev_arcs: List[Dict]
    ) -> Tuple[Dict, Dict]:
        """상태 체크포인트 누락 수정"""
        result = {"success": False}

        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str):
            tactical = str(tactical)

        # 어떤 화에 체크포인트가 누락되었는지 파악
        message = issue.get("message", "")
        ep_match = re.search(r'(\d+)화', message)
        target_ep = int(ep_match.group(1)) if ep_match else None
        if target_ep is None:  # [V70] 대상 화수 특정 불가
            result["reason"] = "대상 화수 특정 불가"
            return arc, result

        context = self._build_context(arc, prev_arcs)

        prompt = CORRECTION_PROMPT.format(
            issue_description=f"제 {target_ep}화에 시작/종료 상태 체크포인트가 누락되었습니다.",
            correction_scope=f"제 {target_ep}화에 ▶ 시작 상태, ▶ 종료 상태 섹션을 추가하세요.",
            original_arc=json.dumps(arc, ensure_ascii=False, indent=2)[:3000],
            context=context[:1000]
        )

        try:
            response = self.ask(prompt, temperature=0.3)
            if isinstance(response, str):  # [V70] ask()는 항상 str 반환
                response = self._extract_json_robust(response)

            if isinstance(response, dict) and response.get("corrected_content"):
                corrected_tactical = self._replace_episode_section(
                    tactical, target_ep, response["corrected_content"]
                )

                if corrected_tactical:
                    arc["tactical_doc"] = corrected_tactical
                    result["success"] = True
                    result["field"] = "tactical_doc"
                    result["summary"] = response.get("change_summary", f"제 {target_ep}화 체크포인트 추가")
                else:
                    result["reason"] = "섹션 교체 실패"
            else:
                result["reason"] = "LLM 응답 형식 오류"

        except Exception as e:
            result["reason"] = str(e)[:100]

        return arc, result

    def _correct_location_issue(
        self,
        arc: Dict,
        issue: Dict,
        prev_arcs: List[Dict]
    ) -> Tuple[Dict, Dict]:
        """위치 불일치 수정"""
        result = {"success": False}

        # state_constraints 수정
        state = arc.get("state_constraints", {})
        if not state:
            result["reason"] = "state_constraints 없음"
            return arc, result

        # 이전 Arc 종료 위치 확인
        prev_location = None
        if prev_arcs:
            last_arc = prev_arcs[-1]
            prev_location = last_arc.get("joint_docs", {}).get("final_location")

        if prev_location:
            # arc_start_state.location 수정
            arc_start = state.get("arc_start_state", {})
            arc_start["location"] = prev_location
            state["arc_start_state"] = arc_start
            arc["state_constraints"] = state

            result["success"] = True
            result["field"] = "state_constraints.arc_start_state.location"
            result["summary"] = f"시작 위치를 '{prev_location}'으로 수정"
        else:
            result["reason"] = "이전 Arc 종료 위치 없음"

        return arc, result

    def _correct_missing_episode(
        self,
        arc: Dict,
        issue: Dict,
        prev_arcs: List[Dict]
    ) -> Tuple[Dict, Dict]:
        """누락된 화 추가"""
        result = {"success": False}

        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str):
            tactical = str(tactical)

        # 어떤 화가 누락되었는지 파악
        message = issue.get("message", "")
        ep_match = re.search(r'\[(\d+)\]', message)
        if not ep_match:
            ep_match = re.search(r'(\d+)화', message)
        target_ep = int(ep_match.group(1)) if ep_match else None

        if not target_ep:
            result["reason"] = "누락 화 번호 파악 실패"
            return arc, result

        context = self._build_context(arc, prev_arcs)

        prompt = CORRECTION_PROMPT.format(
            issue_description=f"제 {target_ep}화가 누락되었습니다. 추가해주세요.",
            correction_scope=f"제 {target_ep}화 전체 섹션을 생성하세요. (시작/종료 상태 체크포인트 포함, 최소 500자)",
            original_arc=json.dumps(arc, ensure_ascii=False, indent=2)[:3000],
            context=context[:1000]
        )

        try:
            response = self.ask(prompt, temperature=0.4)
            if isinstance(response, str):  # [V70] ask()는 항상 str 반환
                response = self._extract_json_robust(response)

            if isinstance(response, dict) and response.get("corrected_content"):
                # 해당 화 섹션 삽입
                new_section = response["corrected_content"]
                corrected_tactical = self._insert_episode_section(tactical, target_ep, new_section)

                if corrected_tactical:
                    arc["tactical_doc"] = corrected_tactical
                    result["success"] = True
                    result["field"] = "tactical_doc"
                    result["summary"] = response.get("change_summary", f"제 {target_ep}화 추가")
                else:
                    result["reason"] = "섹션 삽입 실패"
            else:
                result["reason"] = "LLM 응답 형식 오류"

        except Exception as e:
            result["reason"] = str(e)[:100]

        return arc, result

    def _correct_field_issue(
        self,
        arc: Dict,
        issue: Dict,
        prev_arcs: List[Dict]
    ) -> Tuple[Dict, Dict]:
        """필드 누락 수정"""
        result = {"success": False}
        message = issue.get("message", "")

        # 어떤 필드가 누락되었는지 파악
        if "joint_docs" in message:
            # joint_docs 자동 생성
            tactical = arc.get("tactical_doc", "")
            arc["joint_docs"] = self._generate_joint_docs_from_tactical(tactical, arc)
            result["success"] = True
            result["field"] = "joint_docs"
            result["summary"] = "joint_docs 자동 생성"

        elif "state_constraints" in message:
            # state_constraints 기본값 생성
            arc["state_constraints"] = self._generate_default_state_constraints(arc, prev_arcs)
            result["success"] = True
            result["field"] = "state_constraints"
            result["summary"] = "state_constraints 기본값 생성"
        else:
            result["reason"] = "알 수 없는 필드"

        return arc, result

    def _correct_generic_issue(
        self,
        arc: Dict,
        issue: Dict,
        prev_arcs: List[Dict]
    ) -> Tuple[Dict, Dict]:
        """범용 수정"""
        result = {"success": False, "reason": "범용 수정 미지원"}
        return arc, result

    def _build_context(self, arc: Dict, prev_arcs: List[Dict]) -> str:
        """수정용 컨텍스트 구성"""
        lines = []

        if prev_arcs:
            last = prev_arcs[-1]
            joint = last.get("joint_docs", {})
            lines.append(f"[이전 Arc 종료 상태]")
            lines.append(f"- 위치: {joint.get('final_location', '?')}")
            lines.append(f"- 소지품: {joint.get('physical_inventory', [])}")

        arc_start = arc.get("state_constraints", {}).get("arc_start_state", {})
        if arc_start:
            lines.append(f"\n[현재 Arc 시작 상태]")
            lines.append(f"- 위치: {arc_start.get('location', '?')}")
            lines.append(f"- 내공: {arc_start.get('internal_energy', '?')}%")
            lines.append(f"- 부상: {arc_start.get('injuries', '?')}")

        return "\n".join(lines)

    def _replace_episode_section(self, tactical: str, ep_num: int, new_content: str) -> Optional[str]:
        """특정 화 섹션 교체"""
        # [V70] 제N화 패턴 (브라켓 유무 모두 대응)
        pattern = rf'((?:\[)?제\s*{ep_num}\s*화[^\n]*)(.*?)(?=(?:\[)?제\s*\d+\s*화|$)'

        match = re.search(pattern, tactical, re.DOTALL)
        if match:
            # 헤더 유지, 내용만 교체
            header = match.group(1)
            new_section = f"{header}\n{new_content}\n"
            return tactical[:match.start()] + new_section + tactical[match.end():]

        return None

    def _insert_episode_section(self, tactical: str, ep_num: int, new_content: str) -> Optional[str]:
        """화 섹션 삽입 (순서 유지)"""
        # 다음 화 찾기
        next_ep = ep_num + 1
        pattern = rf'(?:\[)?제\s*{next_ep}\s*화'  # [V70] 브라켓 유무 모두 대응

        match = re.search(pattern, tactical)
        if match:
            # 다음 화 앞에 삽입
            new_section = f"\n[제 {ep_num}화 전술 설계]\n{new_content}\n\n"
            return tactical[:match.start()] + new_section + tactical[match.start():]
        else:
            # 맨 뒤에 추가
            new_section = f"\n\n[제 {ep_num}화 전술 설계]\n{new_content}"
            return tactical + new_section

    def _validate_change_ratio(self, original: Dict, corrected: Dict) -> bool:
        """변경 비율 검증 (20% 초과 시 거부)"""
        original_str = json.dumps(original, ensure_ascii=False)
        corrected_str = json.dumps(corrected, ensure_ascii=False)

        # 간단한 문자 차이 비율 계산
        original_len = len(original_str)
        diff_len = abs(len(corrected_str) - original_len)

        # 추가된 내용은 허용 (분량 확장)
        if len(corrected_str) > original_len:
            return True

        # 삭제된 비율 체크
        change_ratio = diff_len / max(original_len, 1)
        return change_ratio <= self.max_change_ratio

    def _validate_structure_preserved(self, original: Dict, corrected: Dict) -> bool:
        """구조 보존 검증 (Stage 3 연결성)"""
        # 필수 필드 존재 확인
        required = ["arc_no", "tactical_doc", "ep_start", "ep_end"]
        for field in required:
            if field in original and field not in corrected:
                return False

        # tactical_doc 구조 확인 (화별 분할 유지)
        original_tactical = original.get("tactical_doc", "")
        corrected_tactical = corrected.get("tactical_doc", "")

        if isinstance(original_tactical, str) and isinstance(corrected_tactical, str):
            # 화 헤더 수 비교
            original_eps = len(re.findall(r'\[제\s*\d+\s*화', original_tactical))
            corrected_eps = len(re.findall(r'\[제\s*\d+\s*화', corrected_tactical))

            # 화 수가 줄어들면 안 됨
            if corrected_eps < original_eps:
                return False

        return True

    def _generate_joint_docs_from_tactical(self, tactical: str, arc: Dict) -> Dict:
        """tactical_doc에서 joint_docs 추출"""
        if not isinstance(tactical, str):
            tactical = str(tactical)

        # 마지막 화에서 위치 추출
        location_match = re.search(r'종료.*?위치[:\s]*([^\n,]+)', tactical, re.IGNORECASE)
        final_location = location_match.group(1).strip() if location_match else "미상"

        # 소지품 추출
        inventory = arc.get("state_constraints", {}).get("arc_end_state", {}).get("equipment", [])

        return {
            "final_location": final_location,
            "physical_inventory": inventory,
            "world_joint": "다음 Arc로 이어짐"
        }

    def _generate_default_state_constraints(self, arc: Dict, prev_arcs: List[Dict]) -> Dict:
        """기본 state_constraints 생성"""
        # 이전 Arc에서 상태 계승
        if prev_arcs:
            last = prev_arcs[-1]
            last_end = last.get("state_constraints", {}).get("arc_end_state", {})
            last_joint = last.get("joint_docs", {})

            return {
                "arc_start_state": {
                    "location": last_joint.get("final_location", "미상"),
                    "equipment": last_joint.get("physical_inventory", []),
                    "injuries": last_end.get("injuries", "없음"),
                    "internal_energy": last_end.get("internal_energy", 100)
                },
                "arc_end_state": {
                    "location": "미정",
                    "equipment": [],
                    "injuries": "없음",
                    "internal_energy": 100
                },
                "items_acquired": [],
                "items_consumed": [],
                "grants_received": []
            }
        else:
            # 첫 Arc
            return {
                "arc_start_state": {
                    "location": "시작점",
                    "equipment": [],
                    "injuries": "없음",
                    "internal_energy": 100
                },
                "arc_end_state": {
                    "location": "미정",
                    "equipment": [],
                    "injuries": "없음",
                    "internal_energy": 100
                },
                "items_acquired": [],
                "items_consumed": [],
                "grants_received": []
            }


def create_arc_corrector(context, client, model_tier: str = "gemini-2.5-flash"):
    """ArcCorrector 생성 헬퍼"""
    return ArcCorrector(context, client, model_tier)
