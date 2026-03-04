"""[LM-D] NPC 관계도 장기 표류 감지기 — 관계 변경 이력의 표류를 LLM으로 감지.

npc_relationship_history 테이블(append-only)에 쌓인 관계 변경 이력을
주기적으로 LLM에게 검토시켜, 서사적 근거 없는 관계 역전을 advisory로 감지.
Advisory-only: Director가 최종 판정.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

MAX_PAIRS = 20
MAX_TIMELINE_CHARS = 5000


class RelationshipDriftAdvisor:
    """NPC 관계 장기 표류 LLM advisory (advisory only)."""

    def __init__(self, llm_ask=None):
        """
        Args:
            llm_ask: Optional callable(prompt: str) -> str. None이면 검사 스킵.
        """
        self._llm_ask = llm_ask

    @staticmethod
    def build_relationship_timeline(db, min_changes=2, max_pairs=MAX_PAIRS) -> str:
        """DB에서 관계 변경 이력을 타임라인 텍스트로 포맷팅 (Python 수집만).

        Args:
            db: DBManager 인스턴스
            min_changes: 최소 변경 횟수 필터
            max_pairs: 최대 NPC 쌍 수

        Returns:
            str: 포맷된 타임라인 텍스트. 해당 이력 없으면 빈 문자열.
        """
        if not db or not hasattr(db, "get_all_relationship_pairs_with_history"):
            return ""

        pairs = db.get_all_relationship_pairs_with_history(min_changes)
        if not pairs:
            return ""

        lines = []
        total_len = 0
        for npc1, npc2 in pairs[:max_pairs]:
            history = db.get_relationship_history(npc1, npc2)
            if not history:
                continue

            # 타임라인: "1화: 원수 → 23화: 중립 → 45화: 협력"
            transitions = []
            # 첫 기록의 old_relation으로 시작
            first = history[0]
            if first.get("old_relation"):
                ep_label = f"{first.get('change_ep', '?')}화 이전"
                transitions.append(f"{ep_label}: {first['old_relation']}")

            for h in history:
                ep = h.get("change_ep", "?")
                transitions.append(f"{ep}화: {h.get('new_relation', '?')}")

            timeline_str = " → ".join(transitions)
            line = f"[{npc1} ↔ {npc2}]\n  {timeline_str}"

            if total_len + len(line) > MAX_TIMELINE_CHARS:
                break
            lines.append(line)
            total_len += len(line)

        return "\n".join(lines)

    def check(self, manuscript, *, ep_num=0, relationship_timeline=""):
        """관계도 장기 표류 검사.

        Args:
            manuscript: 원고 텍스트
            ep_num: 현재 에피소드 번호
            relationship_timeline: build_relationship_timeline() 반환값

        Returns:
            list[dict]: [{"npc_pair", "old_relation", "new_relation",
                         "why_drift", "severity", "check"}]
        """
        if not manuscript or not relationship_timeline:
            return []

        if not self._llm_ask:
            return []

        return self._llm_check(manuscript, relationship_timeline, ep_num)

    def _llm_check(self, manuscript, relationship_timeline, ep_num):
        """LLM에게 관계 표류 판정을 요청."""
        ms_snippet = manuscript[:4000]

        prompt = (
            "다음은 웹소설 NPC 쌍의 관계 변경 이력(타임라인)과 현재 원고입니다.\n"
            "서사적 근거 없이 설명 없는 관계 역전이 있는지 확인하세요.\n"
            "서사적 근거가 있는 변화(사건, 배신, 화해, 오해 해소 등 작중 이유가 있는 변화)는 "
            "표류가 아닙니다. 설명 없이 관계가 바뀐 것만 지적하세요.\n\n"
            f"[관계 변경 이력 — 현재 {ep_num}화]\n{relationship_timeline}\n\n"
            f"[원고 (최대 4000자)]\n{ms_snippet}\n\n"
            "반드시 JSON 배열로만 답하세요. 표류가 없으면 빈 배열 []을 반환하세요.\n"
            '형식: [{"npc_pair": "A ↔ B", "old_relation": "이전 관계", '
            '"new_relation": "현재 관계", "why_drift": "표류 설명"}]\n'
        )

        try:
            response = self._llm_ask(prompt)
            if not response:
                return []
            return self._parse_llm_response(response, ep_num)
        except Exception as e:
            logger.warning("[LM-D] RelationshipDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
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
            logger.debug("[LM-D] JSON 파싱 실패: %s", text[:100])
            return []

        if not isinstance(parsed, list):
            return []

        results = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            npc_pair = item.get("npc_pair", "")
            if not npc_pair:
                continue
            old_rel = item.get("old_relation", "")
            new_rel = item.get("new_relation", "")
            results.append(
                {
                    "npc_pair": npc_pair,
                    "old_relation": old_rel,
                    "new_relation": new_rel,
                    "why_drift": item.get("why_drift", ""),
                    "severity": "MAJOR",
                    "check": "relationship_drift",
                    "text": f"[관계 표류] {npc_pair}: {old_rel} → {new_rel}",
                }
            )

        return results
