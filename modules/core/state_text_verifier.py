"""[V75] State-Text Verifier — actual_truth ↔ 원고 교차 검증.

Manager가 추출한 actual_truth(수치·상태·장비 등)를 원고 텍스트와
LLM으로 교차 검증하여, 환각이나 오독에 의한 SSOT 오염을 방지한다.
Advisory 모드이므로 검증 실패 시에도 저장을 차단하지 않는다.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

_VERIFY_PROMPT_TEMPLATE = """당신은 웹소설 원고와 상태 추출 결과를 교차 검증하는 감사관입니다.

아래 "추출된 상태"는 별도 AI가 원고에서 추출한 주인공 상태입니다.
원고 본문과 비교하여, 추출된 상태 중 **원고에 근거가 없거나 모순되는 항목**을 찾아주세요.

### 추출된 상태 (actual_truth)
{actual_truth_json}

### 원고 본문
{manuscript}

### 응답 형식 (JSON)
{
  "mismatches": [
    {
      "field": "필드명 (예: capital, level)",
      "extracted": "추출된 값",
      "evidence": "원고에서 찾은 근거 (직접 인용 또는 '근거 없음')",
      "corrected": "원고 근거 기반 수정값 (수정 불가 시 null)"
    }
  ],
  "verified": true
}

규칙:
- 원고에 명시적으로 언급되지 않은 수치 변경은 "근거 없음"으로 보고
- 단, 맥락상 합리적 추론 가능한 경우(예: "두 배로 불렸다" → 수치 증가)는 허용
- mismatches가 없으면 verified: true, mismatches 배열은 빈 배열
- 반드시 위 JSON 형식으로만 응답"""

# 검증 대상 수치/상태 필드 목록
_VERIFIABLE_FIELDS = frozenset(
    {
        "capital",
        "total_assets",
        "level",
        "rank",
        "stage",
        "health",
        "internal_energy",
        "equipment",
        "martial_arts",
        "wins",
        "losses",
        "reputation",
        "fame",
        "wealth",
        "acting_skill",
        "box_office",
        "cooking_skill",
    }
)

# 원고 최대 길이 제한 (Flash 토큰 절약)
_MANUSCRIPT_LIMIT = 8000


class StateTextVerifier:
    """actual_truth ↔ manuscript 교차 검증기 (advisory + LLM)."""

    def __init__(self, agent=None, genre: str = "wuxia", critical_keys: list | None = None):
        """
        Args:
            agent: BaseAgent 인스턴스 (ask() 메서드 사용). None이면 LLM 검증 스킵.
            genre: 장르 코드 (TF-45).
            critical_keys: 장르별 필수 추적 키 (TF-45).
        """
        self._agent = agent
        self._genre = genre
        self._critical_keys = critical_keys or []

    def verify(self, manuscript: str, actual_truth: dict) -> dict:
        """actual_truth를 원고와 교차 검증.

        Returns:
            {
                "verified": bool,
                "mismatches": list[dict],
                "corrections": dict,  # field→corrected_value
                "blocking": False,    # advisory — 항상 False
            }
        """
        if not manuscript or not actual_truth or not self._agent:
            return {"verified": True, "mismatches": [], "corrections": {}, "blocking": False}

        _target = self._filter_verifiable_fields_genre(actual_truth)
        if not _target:
            return {"verified": True, "mismatches": [], "corrections": {}, "blocking": False}

        try:
            # head+tail 전략: 수치 정보는 원고 후반에 많음
            _ms_len = len(manuscript)
            if _ms_len <= _MANUSCRIPT_LIMIT:
                _ms_text = manuscript
            else:
                _half = _MANUSCRIPT_LIMIT // 2
                _ms_text = manuscript[:_half] + "\n...(중략)...\n" + manuscript[-_half:]

            prompt = _VERIFY_PROMPT_TEMPLATE.replace(
                "{actual_truth_json}", json.dumps(_target, ensure_ascii=False, indent=2)
            ).replace("{manuscript}", _ms_text)

            response = self._agent.ask(prompt, temperature=0.1)
            result = self._parse_response(response)

            if result.get("mismatches"):
                corrections = {}
                for mm in result["mismatches"]:
                    if not isinstance(mm, dict):
                        continue
                    _mm_field = mm.get("field")
                    if _mm_field and mm.get("corrected") is not None:
                        corrections[_mm_field] = mm["corrected"]
                    logger.warning(
                        "[V75] State-Text 불일치: %s — 추출=%s, 근거=%s",
                        _mm_field or "?",
                        mm.get("extracted", "?"),
                        mm.get("evidence", "?"),
                    )
                return {
                    "verified": False,
                    "mismatches": result["mismatches"],
                    "corrections": corrections,
                    "blocking": False,
                }

            return {"verified": True, "mismatches": [], "corrections": {}, "blocking": False}

        except Exception as e:
            logger.warning("[SilentPass:V75] State-Text 검증 실패: %s", e)
            return {"verified": True, "mismatches": [], "corrections": {}, "blocking": False}

    def _filter_verifiable_fields_genre(self, actual_truth: dict) -> dict:
        """[TF-45] 장르별 검증 가능 필드 추출."""
        # 공통 필드 + 장르별 critical_keys 합집합
        _common = frozenset({"level", "rank", "health", "reputation", "wealth", "fame", "equipment"})
        _effective = _common | frozenset(self._critical_keys) | _VERIFIABLE_FIELDS
        result = {}
        for k, v in actual_truth.items():
            if k in _effective and v is not None:
                result[k] = v
            elif isinstance(v, int | float):
                result[k] = v
            elif isinstance(v, str) and any(c.isdigit() for c in v):
                result[k] = v
        return result

    @staticmethod
    def _filter_verifiable_fields(actual_truth: dict) -> dict:
        """검증 가능한 필드만 추출 (수치, 상태, 장비 등). 하위 호환용."""
        result = {}
        for k, v in actual_truth.items():
            if k in _VERIFIABLE_FIELDS and v is not None:
                result[k] = v
            elif isinstance(v, int | float):
                result[k] = v
            elif isinstance(v, str) and any(c.isdigit() for c in v):
                result[k] = v
        return result

    @staticmethod
    def _parse_response(response: str) -> dict:
        """LLM 응답 파싱 (JSON 추출)."""
        _default = {"verified": True, "mismatches": []}
        if not response:
            return _default
        # 1차: 전체 응답을 직접 JSON 파싱 시도
        try:
            parsed = json.loads(response.strip())
            if isinstance(parsed, dict) and isinstance(parsed.get("mismatches"), list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        # 2차: 마크다운 코드블록 등에서 JSON 추출
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            try:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict) and isinstance(parsed.get("mismatches"), list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
        return _default

    def apply_corrections(self, actual_truth: dict, corrections: dict) -> dict:
        """corrections를 actual_truth에 적용하여 수정된 사본 반환."""
        if not corrections:
            return dict(actual_truth)
        corrected = dict(actual_truth)
        for field, value in corrections.items():
            if field in corrected:
                old = corrected[field]
                corrected[field] = value
                logger.info("[V75] actual_truth 수정: %s = %s → %s", field, old, value)
        return corrected
