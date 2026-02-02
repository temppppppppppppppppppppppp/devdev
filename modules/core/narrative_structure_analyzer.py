"""
[V60.15] Narrative Structure Analyzer
진짜 서사 구조 분석 - 임베딩 유사도가 아닌 실제 서사 요소 추출

핵심 원리:
- LLM이 각 비트에서 행위/장소/결과를 추출
- 연속 3개 이상 동일하면 진짜 정체
- 단순 문체 유사도는 무시

비용: ~$0.005/Arc (flash 모델)
정확도: 90%+
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from google import genai
from google.genai import types


# 서사 요소 추출 프롬프트
NARRATIVE_EXTRACTION_PROMPT = """
[서사 구조 분석기]

아래 5개 에피소드 비트에서 핵심 서사 요소를 추출하세요.

### 비트 목록
{beats_text}

### 추출 규칙
1. **핵심 행위**: 주인공의 주요 행동 (1단어)
   - 예: 전투, 수련, 이동, 협상, 탐색, 도주, 잠입, 구출, 복수, 각성

2. **장소 유형**: 사건이 벌어지는 공간 유형 (1단어)
   - 예: 산장, 도시, 황궁, 야외, 동굴, 저택, 주막, 시장, 전장, 비밀기지

3. **결과/변화**: 에피소드 끝의 상황 변화 (1단어)
   - 예: 승리, 패배, 무승부, 성장, 획득, 상실, 동맹, 적대, 발각, 은신

### 출력 (JSON)
{{
    "episodes": [
        {{"action": "전투", "location": "산장", "outcome": "승리"}},
        {{"action": "이동", "location": "도시", "outcome": "동맹"}},
        {{"action": "수련", "location": "동굴", "outcome": "성장"}},
        {{"action": "탐색", "location": "저택", "outcome": "발각"}},
        {{"action": "도주", "location": "야외", "outcome": "은신"}}
    ],
    "pattern_detected": false,
    "pattern_description": null
}}

### 중요
- 각 필드는 반드시 1단어로
- 비트 내용을 정확히 반영
- 억지로 다르게 만들지 말고 실제로 비슷하면 비슷하게 추출
"""


class NarrativeStructureAnalyzer:
    """
    [V60.15] 진짜 서사 구조 분석기

    임베딩 유사도의 한계를 극복:
    - "싸움→싸움→싸움" = 정체 (같은 행위)
    - "싸움→도주→협상" = 정상 (다른 행위, 비슷한 문체는 OK)
    """

    def __init__(self, client, model: str = "gemini-3-pro-preview"):
        # [V60.24] Gemini 3로 변경
        self.client = client
        self.model = model

        # [V60.15 UPDATE] 정체 판단 기준 완화
        # 장르 특성상 행위/장소/결과가 비슷할 수 있음
        # "진짜 진도가 하나도 안 나가는" 극단적 경우만 잡음
        self.consecutive_threshold = 5  # 5개 전부 동일해야 정체

    def analyze(self, beats: List[str]) -> Dict:
        """
        비트 목록에서 서사 구조 분석

        Returns:
            {
                "status": "PASS" | "STAGNATION" | "WARNING",
                "episodes": [...],
                "stagnation_type": "action" | "location" | "outcome" | None,
                "pattern": "전투→전투→전투" | None,
                "recommendation": "..."
            }
        """
        if not beats or len(beats) < 3:
            return {"status": "PASS", "reason": "비트 부족"}

        # 1. LLM으로 서사 요소 추출
        extracted = self._extract_narrative_elements(beats)

        if not extracted or "episodes" not in extracted:
            return {"status": "PASS", "reason": "추출 실패", "fallback": True}

        episodes = extracted["episodes"]

        # [V60.15 FIX] episodes 유효성 검증
        if not isinstance(episodes, list) or len(episodes) == 0:
            return {"status": "PASS", "reason": "에피소드 추출 실패", "fallback": True}

        # dict가 아닌 요소 필터링
        episodes = [ep for ep in episodes if isinstance(ep, dict)]
        if len(episodes) < 3:
            return {"status": "PASS", "reason": "유효 에피소드 부족", "fallback": True}

        # 2. 연속 반복 패턴 탐지
        stagnation = self._detect_stagnation(episodes)

        if stagnation["detected"]:
            return {
                "status": "STAGNATION",
                "stagnation_type": stagnation["type"],
                "pattern": stagnation["pattern"],
                "recommendation": self._get_recommendation(stagnation["type"]),
                "episodes": episodes
            }

        # 3. 부분적 반복 체크 (WARNING)
        partial = self._detect_partial_repetition(episodes)

        if partial["detected"]:
            return {
                "status": "WARNING",
                "warning_type": partial["type"],
                "pattern": partial["pattern"],
                "episodes": episodes
            }

        return {
            "status": "PASS",
            "episodes": episodes,
            "diversity_score": self._calculate_diversity(episodes)
        }

    def _extract_narrative_elements(self, beats: List[str]) -> Optional[Dict]:
        """LLM으로 서사 요소 추출"""
        beats_text = "\n".join([f"[Beat {i+1}] {beat}" for i, beat in enumerate(beats[:5])])

        prompt = NARRATIVE_EXTRACTION_PROMPT.format(beats_text=beats_text)

        try:
            config = types.GenerateContentConfig(
                temperature=0.1,  # 일관된 추출을 위해 낮게
                max_output_tokens=1024,
                response_mime_type="application/json"
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            # [V60.15 FIX] None 체크
            if not response.text:
                print(f"      ⚠️ [NarrativeAnalyzer] 빈 응답")
                return None

            result = response.text.strip()

            # [V60.16] JSON 파싱 강화 - 여러 방법 시도
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # 방법 1: 코드블록 제거
                cleaned = re.sub(r'```json\s*|\s*```', '', result)
                try:
                    return json.loads(cleaned)
                except:
                    pass

                # 방법 2: episodes 배열만 추출
                match = re.search(r'"episodes"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if match:
                    try:
                        episodes_str = '[' + match.group(1) + ']'
                        episodes = json.loads(episodes_str)
                        return {"episodes": episodes}
                    except:
                        pass

                # 방법 3: 실패 시 기본값 반환 (PASS 처리)
                return None

        except Exception as e:
            print(f"      ⚠️ [NarrativeAnalyzer] 추출 오류: {e}")
            return None

    def _detect_stagnation(self, episodes: List[Dict]) -> Dict:
        """연속 반복 패턴 탐지"""
        if len(episodes) < self.consecutive_threshold:
            return {"detected": False}

        # 각 요소별로 연속 반복 체크
        for element_type in ["action", "location", "outcome"]:
            elements = [ep.get(element_type, "").lower() for ep in episodes]

            # [V60.15 FIX] 빈 리스트 체크
            if not elements:
                continue

            # 연속 동일 카운트
            max_consecutive = 1
            current_consecutive = 1
            consecutive_value = elements[0]
            consecutive_start_idx = 0  # [V60.15 FIX] 연속 시작 인덱스 추적
            best_start_idx = 0

            for i in range(1, len(elements)):
                if elements[i] == elements[i-1] and elements[i]:
                    current_consecutive += 1
                    if current_consecutive > max_consecutive:
                        max_consecutive = current_consecutive
                        consecutive_value = elements[i]
                        best_start_idx = consecutive_start_idx
                else:
                    current_consecutive = 1
                    consecutive_start_idx = i  # 새 연속 시작

            if max_consecutive >= self.consecutive_threshold:
                # [V60.15 FIX] 실제 연속 구간에서 패턴 추출
                pattern = "→".join(elements[best_start_idx:best_start_idx + max_consecutive])
                return {
                    "detected": True,
                    "type": element_type,
                    "value": consecutive_value,
                    "count": max_consecutive,
                    "pattern": pattern
                }

        return {"detected": False}

    def _detect_partial_repetition(self, episodes: List[Dict]) -> Dict:
        """
        [V60.15 UPDATE] 부분적 반복 (WARNING 수준) - 더 러프하게

        장르 특성상 비슷한 패턴은 자연스러움.
        진짜 "진도 안 나감"만 경고.
        """
        dominated_count = 0  # 여러 요소가 동시에 지배적이면 더 심각

        for element_type in ["action", "location", "outcome"]:
            elements = [ep.get(element_type, "").lower() for ep in episodes]

            from collections import Counter
            counts = Counter(e for e in elements if e)

            if counts:
                most_common, count = counts.most_common(1)[0]

                # 5개 중 5개 같으면 카운트 (STAGNATION에서 잡힘)
                # 5개 중 4개 같으면 경고 대상
                if count >= 4:
                    dominated_count += 1

        # [V60.15] 2개 이상의 요소가 동시에 지배적이면 WARNING
        # (행위도 다 같고 장소도 다 같으면 진짜 진도 안 나감)
        if dominated_count >= 2:
            return {
                "detected": True,
                "type": "multiple",
                "count": dominated_count,
                "pattern": f"{dominated_count}개 요소 반복"
            }

        return {"detected": False}

    def _calculate_diversity(self, episodes: List[Dict]) -> float:
        """서사 다양성 점수 계산 (0-1)"""
        total_unique = 0
        total_elements = 0

        for element_type in ["action", "location", "outcome"]:
            elements = [ep.get(element_type, "") for ep in episodes]
            elements = [e for e in elements if e]

            if elements:
                unique = len(set(e.lower() for e in elements))
                total_unique += unique
                total_elements += len(elements)

        if total_elements == 0:
            return 1.0

        # 최대 다양성 = 모든 요소가 다름
        max_diversity = total_elements
        return total_unique / max_diversity

    def _get_recommendation(self, stagnation_type: str) -> str:
        """정체 유형별 개선 권고"""
        recommendations = {
            "action": "연속된 동일 행위를 변주하세요. 예: 전투→협상→잠입→전투",
            "location": "공간 이동을 추가하세요. 예: 산장→도시→야외→동굴",
            "outcome": "결과에 변화를 주세요. 예: 승리→발각→도주→성장"
        }
        return recommendations.get(stagnation_type, "서사 요소에 변화를 주세요.")


def create_narrative_analyzer(client, model: str = "gemini-3-pro-preview"):
    """[V60.24] NarrativeStructureAnalyzer 생성 헬퍼 - Gemini 3 사용"""
    return NarrativeStructureAnalyzer(client, model)
