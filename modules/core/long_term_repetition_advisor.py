"""[P1-5] 장기 반복 감지 — 20화+ 윈도우의 구조적 반복 패턴 LLM advisory.

RepetitionGuard(3-B)가 5화 윈도우의 문장 수준 반복을 감지하는 반면,
이 모듈은 20화 이상 윈도우에서 **플롯 구조·씬 유형·전개 패턴**의
반복을 Python으로 사전 감지하고, LLM에게 최종 판정을 위임한다.

Advisory-only: Director가 최종 판정.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# 씬 유형 키워드 매핑 (장르 무관 공통)
SCENE_KEYWORDS: dict[str, list[str]] = {
    "전투": ["전투", "싸움", "대결", "교전", "비무", "혈전", "격돌"],
    "수련": ["수련", "훈련", "깨달음", "돌파", "각성", "수행", "연마"],
    "위기": ["위기", "위험", "함정", "포위", "독", "절체절명", "궁지"],
    "도발": ["도발", "모욕", "시비", "도전", "경멸", "조롱"],
    "구출": ["구출", "구원", "해방", "탈출", "도주"],
    "갈등": ["갈등", "대립", "충돌", "불화", "반목"],
    "화해": ["화해", "용서", "이해", "동맹", "협력"],
    "발견": ["발견", "비밀", "단서", "보물", "유산", "진실"],
    "이별": ["이별", "작별", "떠남", "파문", "추방"],
    "재회": ["재회", "만남", "귀환", "복귀", "조우"],
}

# 반복 임계값
MIN_LOOKBACK = 20  # 최소 분석 윈도우
REPEAT_THRESHOLD = 3  # 패턴 3회+ 반복 시 경고
SEQUENCE_LENGTH = 2  # 2-gram 씬 시퀀스


class LongTermRepetitionAdvisor:
    """20화+ 장기 반복 패턴 감지 (advisory only)."""

    def __init__(self, llm_ask=None):
        self._llm_ask = llm_ask

    def check(self, manuscript: str, *, ep_num: int = 0, pattern_summary: str = "") -> list[dict]:
        """현재 원고의 장기 반복 여부를 LLM에게 판정 요청.

        Args:
            manuscript: 현재 원고 텍스트
            ep_num: 현재 에피소드 번호
            pattern_summary: build_pattern_summary()가 생성한 패턴 요약

        Returns:
            list[dict]: [{"pattern", "issue", "severity", "check", "text"}]
        """
        if not manuscript or not pattern_summary:
            return []

        # 현재 원고의 씬 유형 추출
        current_scenes = self._extract_scene_types(manuscript)
        if not current_scenes:
            return []

        current_label = "→".join(current_scenes[:6])

        if not self._llm_ask:
            return []

        return self._llm_check(manuscript[:3000], current_label, pattern_summary, ep_num)

    @staticmethod
    def build_pattern_summary(db, current_ep: int, lookback: int = 20) -> str:
        """최근 N화의 블루프린트에서 씬 패턴 요약 생성 (Python only).

        Returns:
            str: 패턴 빈도 요약 텍스트. 반복 패턴 없으면 빈 문자열.
        """
        if current_ep < MIN_LOOKBACK:
            return ""

        scene_sequences: list[list[str]] = []
        start_ep = max(1, current_ep - lookback)

        for ep in range(start_ep, current_ep):
            try:
                bp = db.get_blueprint(ep)
                if not bp:
                    continue
                content = bp.get("content", "") if isinstance(bp, dict) else str(bp)
                if not content:
                    continue
                scenes = LongTermRepetitionAdvisor._extract_scene_types(content)
                if scenes:
                    scene_sequences.append(scenes)
            except Exception:
                continue

        if len(scene_sequences) < 5:
            return ""

        # 2-gram 씬 시퀀스 빈도 계산
        bigram_counter: Counter[str] = Counter()
        for scenes in scene_sequences:
            for i in range(len(scenes) - SEQUENCE_LENGTH + 1):
                bigram = "→".join(scenes[i : i + SEQUENCE_LENGTH])
                bigram_counter[bigram] += 1

        # 전체 씬 유형 빈도
        scene_counter: Counter[str] = Counter()
        for scenes in scene_sequences:
            scene_counter.update(scenes)

        # 반복 패턴 필터
        repeated_bigrams = [(bg, cnt) for bg, cnt in bigram_counter.most_common(10) if cnt >= REPEAT_THRESHOLD]
        dominant_scenes = [(sc, cnt) for sc, cnt in scene_counter.most_common(5) if cnt >= lookback * 0.4]

        if not repeated_bigrams and not dominant_scenes:
            return ""

        lines = [f"[P1-5] 최근 {len(scene_sequences)}화 패턴 분석 (ep {start_ep}~{current_ep - 1})"]

        if repeated_bigrams:
            lines.append("  반복 시퀀스:")
            for bg, cnt in repeated_bigrams:
                lines.append(f"    - '{bg}' × {cnt}회")

        if dominant_scenes:
            total_scenes = sum(scene_counter.values())
            lines.append("  편중 씬 유형:")
            for sc, cnt in dominant_scenes:
                pct = int(cnt / total_scenes * 100) if total_scenes > 0 else 0
                lines.append(f"    - '{sc}' {cnt}회 ({pct}%)")

        return "\n".join(lines)

    @staticmethod
    def _extract_scene_types(text: str) -> list[str]:
        """텍스트에서 씬 유형 키워드 추출 (출현 순서 유지).

        Returns:
            list[str]: 씬 유형 라벨 리스트 (최대 10개, 중복 허용)
        """
        if not text:
            return []

        found: list[tuple[int, str]] = []
        for label, keywords in SCENE_KEYWORDS.items():
            for kw in keywords:
                for m in re.finditer(re.escape(kw), text):
                    found.append((m.start(), label))

        # 위치 순 정렬 → 연속 중복 제거
        found.sort(key=lambda x: x[0])
        result: list[str] = []
        prev = ""
        for _, label in found:
            if label != prev:
                result.append(label)
                prev = label
            if len(result) >= 10:
                break

        return result

    def _llm_check(self, manuscript_snippet: str, current_label: str, pattern_summary: str, ep_num: int) -> list[dict]:
        """LLM에게 장기 반복 판정을 요청."""
        prompt = (
            "다음은 웹소설의 장기 패턴 분석 결과와 현재 원고 일부입니다.\n"
            "독자 이탈을 유발할 수 있는 **구조적 반복**을 찾아주세요.\n"
            "정상적 서사 진행(갈등→해결 등)은 제외하고, "
            "동일한 전개가 반복되어 독자가 '또 이 패턴이야'라고 느낄 수 있는 경우만 지적하세요.\n\n"
            f"[현재 {ep_num}화 씬 구조] {current_label}\n\n"
            f"{pattern_summary}\n\n"
            f"[현재 원고 발췌]\n{manuscript_snippet}\n\n"
            "반드시 JSON 배열로만 답하세요. 반복이 없으면 빈 배열 []을 반환하세요.\n"
            '형식: [{"pattern": "반복 패턴명", "issue": "문제 설명"}]\n'
        )

        try:
            response = self._llm_ask(prompt)
            if not response:
                return []
            return self._parse_llm_response(response)
        except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
            logger.warning("[P1-5] LongTermRepetitionAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
            return []

    @staticmethod
    def _parse_llm_response(response: str) -> list[dict]:
        """LLM 응답에서 JSON 배열 파싱."""
        if not response:
            return []

        text = response.strip()
        m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if not m:
            m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
        text = text.strip()

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.debug("[P1-5] JSON 파싱 실패: %s", text[:100])
            return []

        if not isinstance(parsed, list):
            return []

        results = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            pattern = item.get("pattern", "")
            if not pattern:
                continue
            issue = item.get("issue", "")
            results.append(
                {
                    "pattern": pattern,
                    "issue": issue,
                    "severity": "MAJOR",
                    "check": "long_term_repetition",
                    "text": f"[장기 반복] {pattern}: {issue}" if issue else f"[장기 반복] {pattern}",
                }
            )

        return results
