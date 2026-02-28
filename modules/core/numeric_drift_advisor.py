"""[LM-C] 수치 누적 표류 감지기 — FactLedger 수치 이력의 표류를 LLM으로 감지.

TruthGate(structured data 검사)와 분리된 독립 클래스.
FactLedger numbers 이력 전체를 주기적으로 LLM에게 검토시켜
설명 없는 급변(자산 10만→300억 등)을 advisory로 감지.
Advisory-only: Director가 최종 판정.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

MAX_ITEMS = 20
MAX_HISTORY_POINTS = 15


class NumericDriftAdvisor:
    """FactLedger 수치 이력의 누적 표류를 LLM으로 감지 (advisory only)."""

    def __init__(self, llm_ask=None):
        """
        Args:
            llm_ask: Optional callable(prompt: str) -> str. None이면 검사 스킵.
        """
        self._llm_ask = llm_ask

    def check(self, numbers, *, ep_num=0, min_history=3):
        """수치 누적 표류 검사.

        Args:
            numbers: FactLedger.get_numbers() 반환값
                     {key: {"value", "unit", "last_ep", "history": [str]}}
            ep_num: 현재 에피소드 번호
            min_history: 이력이 이 수 이상인 항목만 검사

        Returns:
            list[dict]: [{"key", "issue", "history_snippet", "severity", "check"}]
        """
        if not numbers:
            return []

        history_text = self._format_history(numbers, min_history)
        if not history_text:
            return []

        if not self._llm_ask:
            return []

        return self._llm_check(history_text, ep_num)

    def _format_history(self, numbers, min_history):
        """수치별 이력 타임라인 포맷팅 (Python 수집만).

        Returns:
            str: 포맷된 이력 텍스트. 해당 항목 없으면 빈 문자열.
        """
        lines = []
        count = 0
        for key, entry in numbers.items():
            if count >= MAX_ITEMS:
                break
            if not isinstance(entry, dict):
                continue
            history = entry.get("history", [])
            if len(history) < min_history:
                continue

            unit = entry.get("unit", "")
            current = entry.get("value", "?")
            unit_suffix = f" ({unit})" if unit else ""

            # 최대 MAX_HISTORY_POINTS개만
            trimmed = history[:MAX_HISTORY_POINTS]
            history_str = " → ".join(str(h) for h in trimmed)
            if len(history) > MAX_HISTORY_POINTS:
                history_str += f" … (+{len(history) - MAX_HISTORY_POINTS}건)"

            lines.append(f"[{key}]{unit_suffix} 현재={current}\n  {history_str}")
            count += 1

        return "\n".join(lines)

    def _llm_check(self, history_text, ep_num):
        """LLM에게 수치 표류 판정을 요청."""
        prompt = (
            "다음은 웹소설의 수치 팩트 변동 이력입니다.\n"
            "서사적 근거 없이 비정상적으로 변동된 수치 표류를 찾아주세요.\n"
            "점진적 성장이나 작중 이유가 있는 변화는 정상입니다. "
            "설명 없는 급변만 지적하세요.\n\n"
            f"[수치 이력 — 현재 {ep_num}화]\n{history_text}\n\n"
            "반드시 JSON 배열로만 답하세요. 표류가 없으면 빈 배열 []을 반환하세요.\n"
            '형식: [{"key": "수치명", "issue": "문제 설명", "history_snippet": "관련 이력 발췌"}]\n'
        )

        try:
            response = self._llm_ask(prompt)
            if not response:
                return []
            return self._parse_llm_response(response, ep_num)
        except Exception as e:
            logger.warning("[LM-C] NumericDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
            return []

    @staticmethod
    def _parse_llm_response(response, ep_num=0):
        """LLM 응답에서 JSON 배열 파싱."""
        if not response:
            return []

        text = response.strip()
        # ```json 펜스 처리 — 정규식 기반 (다중 펜스 안전)
        m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if not m:
            m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
        text = text.strip()

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.debug("[LM-C] JSON 파싱 실패: %s", text[:100])
            return []

        if not isinstance(parsed, list):
            return []

        results = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            key = item.get("key", "")
            if not key:
                continue
            issue = item.get("issue", "")
            results.append(
                {
                    "key": key,
                    "issue": issue,
                    "history_snippet": item.get("history_snippet", ""),
                    "severity": "MAJOR",
                    "check": "numeric_drift",
                    "text": f"[수치 표류] {key}: {issue}" if issue else f"[수치 표류] {key}",
                }
            )

        return results
