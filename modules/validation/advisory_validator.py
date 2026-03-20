"""
[V0128] TIER 3: ADVISORY Validator
개선 제안 (통과에 무영향)
"""

import logging

from modules.core.llm_generate import generate_content_via_router
from modules.validation.threshold_helper import _threshold  # [Phase 5-B-2c]


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
        "전개": ["기절했다 깨보니", "위기의 순간 각성", "숨겨진 혈통"],
    }

    def __init__(self, client=None, model="gemini-2.5-flash") -> None:
        self.client = client
        self.model = model

    @staticmethod
    def _fit_prompt_text(value: object, max_chars: int, head_ratio: float = 0.55) -> str:
        from modules.core.constants import smart_truncate

        text = str(value or "")
        if len(text) <= max_chars:
            return text
        return smart_truncate(text, max_chars=max_chars, head_chars=max(1, int(max_chars * head_ratio)))

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

        # 4. [S-07] 페이싱 검증 (advisory)
        pacing_suggestion = self._check_pacing(manuscript, validation_context)
        if pacing_suggestion:
            suggestions.append(pacing_suggestion)

        return {
            "tier": "ADVISORY",
            "passed": True,  # 항상 PASS
            "suggestions": suggestions[: _threshold("advisory.max_suggestions", 5)],
            "message": f"{len(suggestions)}개 개선 제안",
        }

    # [V44] 클리셰 확정을 위한 컨텍스트 키워드 (주변에 있어야 클리셰로 판정)
    CLICHE_CONTEXT_KEYWORDS = {
        "회귀물": ["과거", "전생", "다시", "두번째", "회귀", "돌아", "예전"],
        "천재물": ["천재", "재능", "각성", "능력", "숨겨", "진정한"],
        "복수물": ["복수", "원수", "피", "죽", "갚", "대가"],
        "가문물": ["가문", "가", "집안", "버림", "쫓겨", "상속"],
        "전개": ["각성", "위기", "혈통", "비밀", "정체"],
    }

    def _detect_cliches(self, manuscript: str) -> list[dict]:
        """[V44] 클리셰 감지 - 컨텍스트 기반 오탐 방지"""
        detected = []

        for category, patterns in self.COMMON_CLICHES.items():
            context_keywords = self.CLICHE_CONTEXT_KEYWORDS.get(category, [])

            for pattern in patterns:
                location = manuscript.find(pattern)
                if location == -1:
                    continue

                # [V44] 컨텍스트 윈도우 (패턴 전후 100자)에서 확인 키워드 검색
                context_start = max(0, location - 100)
                context_end = min(len(manuscript), location + len(pattern) + 100)
                context = manuscript[context_start:context_end].lower()

                # 컨텍스트 키워드가 있어야만 클리셰로 판정
                has_context = any(kw in context for kw in context_keywords)

                if has_context:
                    detected.append(
                        {
                            "type": "cliche_detection",
                            "category": category,
                            "pattern": pattern,
                            "suggestion": f"'{pattern}' 클리셰 감지. 더 신선한 전개 권장.",
                            "location": location,
                            "severity": "low",
                            "context_matched": True,
                        }
                    )
                # 컨텍스트 없으면 낮은 확신도로 기록 (선택적)
                # else:
                #     detected.append({...severity: "very_low"...})

        return detected

    def _suggest_expression_improvements(self, manuscript: str) -> list[dict]:
        """표현 개선 제안 (LLM 기반)"""
        if not self.client:
            return []

        try:
            excerpt = self._fit_prompt_text(manuscript, 1500)
            prompt = f"""
다음 원고에서 더 강렬하게 표현할 수 있는 부분 2-3곳을 지적하고,
개선 제안을 하십시오:

{excerpt}

JSON 형식으로 답하십시오:
[
    {{"location": "원문 구절", "suggestion": "개선 제안", "reason": "이유"}},
    ...
]
"""

            from google.genai import types

            config = types.GenerateContentConfig(temperature=0.5, response_mime_type="application/json")

            response = generate_content_via_router(client=self.client, model=self.model, contents=prompt, config=config)

            import json

            suggestions_raw = json.loads(response.text)

            # [V70] LLM 응답 타입 방어: list가 아닌 경우 처리
            if isinstance(suggestions_raw, dict):
                suggestions_raw = suggestions_raw.get("suggestions", [suggestions_raw])
            if not isinstance(suggestions_raw, list):
                suggestions_raw = []

            return [
                {
                    "type": "expression_enhancement",
                    "suggestion": s.get("suggestion", ""),
                    "location": s.get("location", ""),
                    "reason": s.get("reason", ""),
                    "severity": "low",
                }
                for s in suggestions_raw[:3]
                if isinstance(s, dict)  # [V70] non-dict 엔트리 스킵
            ]

        except Exception as e:
            logging.warning(f"[ADVISORY] 표현 개선 제안 실패: {e}")
            return []

    def _suggest_foreshadowing_opportunities(self, manuscript: str) -> list[dict]:
        """복선 기회 감지 (휴리스틱)"""
        suggestions = []

        # 간단한 휴리스틱: NPC 등장 시 복선 기회
        npc_patterns = ["노인이 나타나", "검은 옷을 입은", "눈빛이 예사롭지", "의미심장한 미소"]

        for pattern in npc_patterns:
            if pattern in manuscript:
                suggestions.append(
                    {
                        "type": "foreshadowing_opportunity",
                        "suggestion": f"'{pattern}' 지점: 복선 심기 좋은 타이밍",
                        "location": manuscript.find(pattern),
                        "severity": "low",
                    }
                )

        return suggestions[:2]  # 최대 2개

    def _check_pacing(self, manuscript: str, validation_context: dict) -> dict | None:
        """[S-07] 페이싱 advisory 검증 (기본 휴리스틱)."""
        if not manuscript or len(manuscript) < 1000:
            return None

        # 문단 분리 빈도 체크
        paragraphs = [p for p in manuscript.split("\n\n") if p.strip()]
        if len(paragraphs) < 3:
            return {
                "type": "pacing_advisory",
                "suggestion": "문단 분리가 부족합니다. 장면 전환·대화·서술 간 여백을 권장합니다.",
                "severity": "low",
            }

        # 평균 문단 길이 → 호흡 조절 권고
        avg_para_len = len(manuscript) / max(1, len(paragraphs))
        if avg_para_len > _threshold("advisory.pacing_para_limit", 2000):
            return {
                "type": "pacing_advisory",
                "suggestion": f"평균 문단 길이가 {int(avg_para_len)}자로 깁니다. 호흡 조절을 위해 문단 분리를 권장합니다.",
                "severity": "low",
            }

        # [TF-36] 줄 단위 문장 수 체크 (서술 3문장마다 줄바꿈)
        import re as _re

        _sentence_end = _re.compile(r"[.!?。]")
        lines = [ln for ln in manuscript.split("\n") if ln.strip()]
        _overlong = sum(1 for ln in lines if len(_sentence_end.findall(ln)) > 3)
        if _overlong > len(lines) * 0.3:
            return {
                "type": "pacing_advisory",
                "suggestion": f"줄 {_overlong}개가 4문장 이상입니다. 서술은 3문장마다 줄바꿈, 대사 앞뒤는 빈 줄로 끊어주세요.",
                "severity": "low",
            }

        return None
