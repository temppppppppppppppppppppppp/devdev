"""
[V0128] TIER 3: ADVISORY Validator
개선 제안 (통과에 무영향)
"""
from typing import Dict, List, Any


class AdvisoryValidator:
    """
    TIER 3: 개선 권고 (통과에 영향 없음)

    더 나은 원고를 위한 제안 제공
    로그로 기록하여 추후 분석/학습용
    """

    COMMON_CLICHES = {
        "회귀물": ["다시 눈을 떴다", "과거로 돌아왔다", "알고 있는 미래"],
        "천재물": ["숨겨진 재능", "알고보니 천재", "각성"],
        "복수물": ["반드시 복수", "피의 대가", "잊지 않겠다"],
        "가문물": ["쫓겨난", "버림받은", "폐가문", "재건"],
        "전개": ["기절했다 깨보니", "위기의 순간 각성", "숨겨진 혈통"]
    }

    def __init__(self, client=None, model="gemini-2.5-flash"):
        self.client = client
        self.model = model

    def validate(self, manuscript: str, validation_context: dict) -> dict:
        """
        ADVISORY 검증 실행

        Returns:
            {
                "tier": "ADVISORY",
                "passed": True,  # 항상 PASS
                "suggestions": [...],
                "message": "N개 개선 제안"
            }
        """
        suggestions = []

        # 1. 클리셰 감지
        cliche_suggestions = self._detect_cliches(manuscript)
        suggestions.extend(cliche_suggestions)

        # 2. 표현 개선 제안 (LLM 기반, 선택적)
        if self.client and len(suggestions) < 3:
            expression_suggestions = self._suggest_expression_improvements(manuscript)
            suggestions.extend(expression_suggestions)

        # 3. 복선 기회 감지 (간단한 휴리스틱)
        foreshadowing_suggestions = self._suggest_foreshadowing_opportunities(manuscript)
        suggestions.extend(foreshadowing_suggestions)

        return {
            "tier": "ADVISORY",
            "passed": True,  # 항상 PASS
            "suggestions": suggestions[:5],  # 상위 5개만
            "message": f"{len(suggestions)}개 개선 제안"
        }

    def _detect_cliches(self, manuscript: str) -> List[dict]:
        """클리셰 감지"""
        detected = []

        for category, patterns in self.COMMON_CLICHES.items():
            for pattern in patterns:
                if pattern in manuscript:
                    detected.append({
                        "type": "cliche_detection",
                        "category": category,
                        "pattern": pattern,
                        "suggestion": f"'{pattern}' 클리셰 감지. 더 신선한 전개 권장.",
                        "location": manuscript.find(pattern),
                        "severity": "low"
                    })

        return detected

    def _suggest_expression_improvements(self, manuscript: str) -> List[dict]:
        """표현 개선 제안 (LLM 기반)"""
        if not self.client:
            return []

        try:
            prompt = f"""
다음 원고에서 더 강렬하게 표현할 수 있는 부분 2-3곳을 지적하고,
개선 제안을 하십시오:

{manuscript[:1500]}

JSON 형식으로 답하십시오:
[
    {{"location": "원문 구절", "suggestion": "개선 제안", "reason": "이유"}},
    ...
]
"""

            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.5,
                response_mime_type="application/json"
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            import json
            suggestions_raw = json.loads(response.text)

            return [
                {
                    "type": "expression_enhancement",
                    "suggestion": s.get('suggestion', ''),
                    "location": s.get('location', ''),
                    "reason": s.get('reason', ''),
                    "severity": "low"
                }
                for s in suggestions_raw[:3]
            ]

        except Exception as e:
            print(f"[ADVISORY] 표현 개선 제안 실패: {e}")
            return []

    def _suggest_foreshadowing_opportunities(self, manuscript: str) -> List[dict]:
        """복선 기회 감지 (휴리스틱)"""
        suggestions = []

        # 간단한 휴리스틱: NPC 등장 시 복선 기회
        npc_patterns = [
            "노인이 나타나",
            "검은 옷을 입은",
            "눈빛이 예사롭지",
            "의미심장한 미소"
        ]

        for pattern in npc_patterns:
            if pattern in manuscript:
                suggestions.append({
                    "type": "foreshadowing_opportunity",
                    "suggestion": f"'{pattern}' 지점: 복선 심기 좋은 타이밍",
                    "location": manuscript.find(pattern),
                    "severity": "low"
                })

        return suggestions[:2]  # 최대 2개
