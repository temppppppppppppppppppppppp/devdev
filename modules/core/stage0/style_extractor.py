"""
Style Extractor - 문체/톤 추출기
================================
기존 원고에서 작문 스타일을 추출하여 이후 생성 시 일관성 보장
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class StyleGuide:
    """스타일 가이드"""
    tone: str = "중립"  # 냉소적/유머/진지/가벼움
    pov: str = "1인칭"  # 1인칭/3인칭/전지적
    sentence_length: str = "medium"  # short/medium/long
    dialogue_ratio: float = 0.3  # 대화 비율
    description_style: str = "균형"  # 간결/균형/묘사적
    vocabulary_level: str = "medium"  # easy/medium/hard
    paragraph_style: str = "mixed"  # short/mixed/long
    action_style: str = "dynamic"  # static/dynamic/cinematic

    sample_sentences: List[str] = None  # 대표 문장들
    sample_dialogues: List[str] = None  # 대표 대화들
    signature_expressions: List[str] = None  # 자주 쓰는 표현
    forbidden_expressions: List[str] = None  # 피해야 할 표현

    def __post_init__(self):
        if self.sample_sentences is None:
            self.sample_sentences = []
        if self.sample_dialogues is None:
            self.sample_dialogues = []
        if self.signature_expressions is None:
            self.signature_expressions = []
        if self.forbidden_expressions is None:
            self.forbidden_expressions = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StyleGuide":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_prompt(self) -> str:
        """프롬프트용 스타일 가이드 문자열"""
        lines = [
            "## 작문 스타일 가이드 (반드시 준수)",
            f"- 톤: {self.tone}",
            f"- 시점: {self.pov}",
            f"- 문장 길이: {self.sentence_length}",
            f"- 대화 비율: {self.dialogue_ratio:.0%}",
            f"- 묘사 스타일: {self.description_style}",
            f"- 어휘 수준: {self.vocabulary_level}",
        ]

        if self.sample_sentences:
            lines.append("\n### 참고 문장 스타일:")
            for s in self.sample_sentences[:3]:
                lines.append(f'  "{s[:100]}"')

        if self.signature_expressions:
            lines.append(f"\n### 자주 사용하는 표현: {', '.join(self.signature_expressions[:5])}")

        if self.forbidden_expressions:
            lines.append(f"\n### 사용 금지 표현: {', '.join(self.forbidden_expressions[:5])}")

        return "\n".join(lines)


class StyleExtractor:
    """문체 추출기"""

    def __init__(self, llm_client=None):
        self.client = llm_client

    def extract_from_drafts(self, drafts: List[str]) -> StyleGuide:
        """원고들에서 스타일 추출"""
        combined_text = "\n\n".join(drafts[:5])  # 최대 5개 에피소드

        # 1. 기본 통계 분석 (Python)
        stats = self._analyze_statistics(combined_text)

        # 2. LLM으로 정성 분석
        if self.client:
            qualitative = self._analyze_with_llm(combined_text)
            stats.update(qualitative)

        return StyleGuide(**stats)

    def _analyze_statistics(self, text: str) -> Dict[str, Any]:
        """통계 기반 분석"""
        result = {}

        # 문장 분리
        sentences = re.split(r'[.!?]\s*', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 대화 추출
        dialogues = re.findall(r'"([^"]+)"', text)

        # 문장 길이 분석
        if sentences:
            avg_len = sum(len(s) for s in sentences) / len(sentences)
            if avg_len < 30:
                result["sentence_length"] = "short"
            elif avg_len < 60:
                result["sentence_length"] = "medium"
            else:
                result["sentence_length"] = "long"

        # 대화 비율
        dialogue_chars = sum(len(d) for d in dialogues)
        total_chars = len(text)
        if total_chars > 0:
            result["dialogue_ratio"] = round(dialogue_chars / total_chars, 2)

        # 시점 감지
        first_person = len(re.findall(r'\b(나는|나의|내가|나를)\b', text))
        third_person = len(re.findall(r'\b(그는|그녀는|그의|그녀의)\b', text))
        if first_person > third_person * 2:
            result["pov"] = "1인칭"
        elif third_person > first_person * 2:
            result["pov"] = "3인칭"
        else:
            result["pov"] = "혼합"

        # 샘플 문장/대화 추출
        result["sample_sentences"] = [s for s in sentences if 20 < len(s) < 80][:5]
        result["sample_dialogues"] = [d for d in dialogues if 10 < len(d) < 100][:5]

        return result

    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """LLM으로 정성 분석"""
        prompt = f"""다음 원고의 문체를 분석하세요.

## 원고 샘플
{text[:4000]}

## 분석 항목 (JSON)
```json
{{
  "tone": "냉소적/유머/진지/가벼움/어두움 중 하나",
  "description_style": "간결/균형/묘사적 중 하나",
  "vocabulary_level": "easy/medium/hard 중 하나",
  "action_style": "static/dynamic/cinematic 중 하나",
  "signature_expressions": ["자주 쓰는 표현들"],
  "forbidden_expressions": ["이 작품에서 안 쓰는 표현들"]
}}
```
JSON만 출력.
"""
        try:
            from google import genai
            from google.genai import types
            import os

            if not self.client:
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
                if api_key:
                    self.client = genai.Client(api_key=api_key)

            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=2000)
                )
                return self._parse_json(response.text)
        except Exception as e:
            print(f"[!] LLM 분석 실패: {e}")

        return {}

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """JSON 파싱"""
        if not text:
            return {}
        try:
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except:
            return {}

    def compare_styles(self, guide1: StyleGuide, guide2: StyleGuide) -> Dict[str, Any]:
        """두 스타일 비교"""
        differences = {}

        for field in ["tone", "pov", "sentence_length", "description_style", "vocabulary_level"]:
            v1 = getattr(guide1, field)
            v2 = getattr(guide2, field)
            if v1 != v2:
                differences[field] = {"original": v1, "current": v2}

        ratio_diff = abs(guide1.dialogue_ratio - guide2.dialogue_ratio)
        if ratio_diff > 0.1:
            differences["dialogue_ratio"] = {
                "original": guide1.dialogue_ratio,
                "current": guide2.dialogue_ratio,
                "diff": ratio_diff
            }

        return differences
