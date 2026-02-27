"""[LM-F] 정보 역설 감지기 — 1인칭 시점 화자의 불가능한 정보 사용을 LLM으로 감지.

episode_bibles의 reveals + knowledge_map을 누적하여 "주인공이 아는 것" 목록을 구성한 뒤,
원고에서 화자가 해당 목록에 없는 정보를 사용하는 정보 역설을 LLM으로 감지.
Advisory-only: Director가 최종 판정. 1인칭 시점 전용.
"""

import json
import logging

logger = logging.getLogger(__name__)

MAX_REVEALS = 200
MAX_KNOWLEDGE_CHARS = 3000


class InfoParadoxChecker:
    """1인칭 시점 정보 역설 LLM advisory (advisory only)."""

    def __init__(self, llm_ask=None):
        """
        Args:
            llm_ask: Optional callable(prompt: str) -> str. None이면 검사 스킵.
        """
        self._llm_ask = llm_ask

    @staticmethod
    def build_knowledge_summary(db, up_to_ep, protagonist_name):
        """episode_bibles에서 주인공 지식 목록을 누적 구성 (Python 수집만).

        Args:
            db: DBManager 인스턴스 (get_all_episode_bibles 필요)
            up_to_ep: 현재 화 번호 (이 화 미만의 데이터만 사용)
            protagonist_name: 주인공 이름

        Returns:
            str: 포맷된 지식 요약. 이전 데이터 없으면 빈 문자열.
        """
        if not db or not hasattr(db, "get_all_episode_bibles"):
            return ""
        if up_to_ep <= 1:
            return ""

        try:
            all_bibles = db.get_all_episode_bibles()
        except Exception as e:
            logger.warning("[LM-F] episode_bibles 조회 실패: %s", str(e)[:80])
            return ""

        if not all_bibles:
            return ""

        reveals_list = []
        witnesses_list = []
        misled_list = []

        for bible in all_bibles:
            ep = bible.get("ep_num", 0)
            if ep >= up_to_ep:
                continue

            # reveals: 밝혀진 사실
            reveals = bible.get("reveals", [])
            if isinstance(reveals, list):
                for r in reveals:
                    if isinstance(r, str) and r.strip():
                        reveals_list.append(f"{r.strip()} ({ep}화)")
                    elif isinstance(r, dict):
                        desc = r.get("description", r.get("reveal", ""))
                        if desc:
                            reveals_list.append(f"{str(desc).strip()} ({ep}화)")

            # knowledge_map: 목격/오해
            km = bible.get("knowledge_map", {})
            if isinstance(km, dict):
                for w in km.get("new_witnesses", []):
                    if isinstance(w, str) and w.strip():
                        witnesses_list.append(f"{w.strip()} ({ep}화)")
                    elif isinstance(w, dict):
                        desc = w.get("event", w.get("description", ""))
                        if desc:
                            witnesses_list.append(f"{str(desc).strip()} ({ep}화)")
                for m in km.get("new_misled", []):
                    if isinstance(m, str) and m.strip():
                        misled_list.append(f"{m.strip()} ({ep}화)")
                    elif isinstance(m, dict):
                        desc = m.get("belief", m.get("description", ""))
                        if desc:
                            misled_list.append(f"{str(desc).strip()} ({ep}화)")

        # 상한 적용
        if len(reveals_list) > MAX_REVEALS:
            reveals_list = reveals_list[-MAX_REVEALS:]

        # 섹션 구성
        sections = []
        if reveals_list:
            reveals_text = "\n".join(f"  - {r}" for r in reveals_list)
            sections.append(f"밝혀진 사실:\n{reveals_text}")
        if witnesses_list:
            witnesses_text = "\n".join(f"  - {w}" for w in witnesses_list)
            sections.append(f"직접 목격:\n{witnesses_text}")
        if misled_list:
            misled_text = "\n".join(f"  - {m}" for m in misled_list)
            sections.append(f"오해/잘못된 믿음:\n{misled_text}")

        if not sections:
            return ""

        summary = f"[{protagonist_name}이(가) 알고 있는 정보]\n" + "\n".join(sections)

        # MAX_KNOWLEDGE_CHARS 상한
        if len(summary) > MAX_KNOWLEDGE_CHARS:
            summary = summary[:MAX_KNOWLEDGE_CHARS] + "\n  … (이하 생략)"

        return summary

    def check(self, manuscript, *, ep_num=0, pov_character="", knowledge_summary=""):
        """정보 역설 검사.

        Args:
            manuscript: 원고 텍스트
            pov_character: 1인칭 화자(주인공) 이름
            knowledge_summary: build_knowledge_summary() 반환값
            ep_num: 현재 에피소드 번호

        Returns:
            list[dict]: [{"character", "info_used", "why_paradox", "severity", "check"}]
        """
        if not manuscript or not pov_character or not knowledge_summary:
            return []
        if not self._llm_ask:
            return []
        return self._llm_check(manuscript, pov_character, knowledge_summary, ep_num)

    def _llm_check(self, manuscript, pov_character, knowledge_summary, ep_num):
        """LLM에게 정보 역설 판정을 요청."""
        ms_snippet = manuscript[:4000]

        prompt = (
            f"다음은 1인칭 시점 웹소설의 {ep_num}화 원고입니다. "
            f"화자는 '{pov_character}'입니다.\n\n"
            "아래 '알고 있는 정보' 목록에 없는 정보를 화자가 사용하는 경우를 찾아주세요.\n"
            "단, 다음은 정보 역설이 아닙니다:\n"
            "- 상식이나 일반적 추론으로 알 수 있는 정보\n"
            "- 감각 묘사 (보이는 것, 들리는 것, 느끼는 것)\n"
            "- 화자가 직접 경험하거나 관찰한 것\n"
            "- 이전 화에서 습득했을 법한 일상적 지식\n\n"
            "진짜 역설만 지적하세요: 참석하지 않은 비밀 회의 내용, "
            "아직 공개되지 않은 비밀, 물리적으로 알 수 없는 타인의 내면 등.\n\n"
            f"[{pov_character}이(가) 알고 있는 정보]\n{knowledge_summary}\n\n"
            f"[원고 (최대 4000자)]\n{ms_snippet}\n\n"
            "반드시 JSON 배열로만 답하세요. 역설이 없으면 빈 배열 []을 반환하세요.\n"
            '형식: [{"character": "화자이름", "info_used": "사용된 정보", '
            '"why_paradox": "왜 알 수 없는지 설명"}]\n'
        )

        try:
            response = self._llm_ask(prompt)
            if not response:
                return []
            return self._parse_llm_response(response, ep_num)
        except Exception as e:
            logger.warning("[LM-F] InfoParadoxChecker LLM 호출 실패 (비치명): %s", str(e)[:80])
            return []

    @staticmethod
    def _parse_llm_response(response, ep_num=0):
        """LLM 응답에서 JSON 배열 파싱."""
        if not response:
            return []

        text = response.strip()
        # ```json 펜스 처리
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        text = text.strip()

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.debug("[LM-F] JSON 파싱 실패: %s", text[:100])
            return []

        if not isinstance(parsed, list):
            return []

        results = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            info_used = item.get("info_used", "")
            if not info_used:
                continue
            results.append(
                {
                    "character": item.get("character", ""),
                    "info_used": info_used,
                    "why_paradox": item.get("why_paradox", ""),
                    "severity": "MAJOR",
                    "check": "info_paradox",
                }
            )

        return results
