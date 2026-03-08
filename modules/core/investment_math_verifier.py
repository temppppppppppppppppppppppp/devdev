"""[Codex F-2] 투자물 수치 Flash LLM 검산 에이전트."""

from __future__ import annotations

import json
import logging
import re
from typing import Callable

from modules.core.prompt_loader import PromptLoader

_SEVERITY = {"CRITICAL", "MAJOR", "MINOR"}
_CATEGORY = {"leverage_calc", "cash_flow", "total_assets", "narrative_mismatch", "python_fp"}

_FALLBACK_PROMPT = """당신은 투자 소설의 수치 검산 전문가입니다.

[Arc 전문]
{tactical_doc}

[Python 검산 결과]
{python_results}

다음을 수행하세요:
1) 수치 추출(자산명/진입가/청산가/레버리지/원금/서술 수익)
2) 산술 검산: 수익 = 원금 x (청산가 - 진입가) / 진입가 x 레버리지배수
3) 현금 흐름 추적: 이전 현금 + 회수액 - 신규 투자 = 다음 현금
4) 서술-수치 정합성 모순 탐지
5) Python 결과 확인(FP면 category=python_fp)

JSON 배열만 반환하세요. 오류가 없으면 []를 반환하세요.
"""


class InvestmentMathVerifier:
    """
    [Codex F-2] 투자물 수치 Flash LLM 검산 에이전트.

    Flash 1회 호출. advisory-only.
    """

    def __init__(self, llm_ask: Callable[[str], str] | None = None) -> None:
        self._llm_ask = llm_ask
        self._prompt_loader = PromptLoader()

    def verify(
        self,
        tactical_doc: str,
        python_results: list[dict],
        arc_no: int,
        *,
        genre: str = "investment",
    ) -> list[dict]:
        """
        Flash LLM 1회 호출로 종합 검산.

        Returns:
            list[dict]: [{"check": "investment_math_llm", "severity": ..., "text": ...}]
        """
        if genre != "investment":
            return []
        if self._llm_ask is None:
            return []

        python_json = json.dumps(python_results or [], ensure_ascii=False, indent=2)
        prompt = self._prompt_loader.load(
            "investment_math_verifier",
            "VERIFY_PROMPT",
            tactical_doc=tactical_doc or "",
            python_results=python_json,
        )
        if not prompt:
            prompt = _FALLBACK_PROMPT.format(tactical_doc=tactical_doc or "", python_results=python_json)

        try:
            raw = self._llm_ask(prompt)
        except Exception as e:
            logging.warning("[InvestmentMathVerifier] llm_ask 실패: %s", str(e)[:120])
            return []

        parsed = self._parse_json_array(raw)
        results: list[dict] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue

            severity = str(item.get("severity", "MINOR")).upper()
            if severity not in _SEVERITY:
                severity = "MINOR"

            category = str(item.get("category", "leverage_calc")).strip().lower()
            if category not in _CATEGORY:
                category = "leverage_calc"

            issue = str(item.get("issue", "")).strip() or "수치 정합성 이슈"
            ep_no = item.get("ep_no")
            expected = str(item.get("expected", "")).strip()
            stated = str(item.get("stated", "")).strip()

            details = []
            if expected:
                details.append(f"expected={expected}")
            if stated:
                details.append(f"stated={stated}")
            detail_suffix = f" ({', '.join(details)})" if details else ""

            ep_text = f" Ep.{ep_no}" if isinstance(ep_no, int | float) else ""
            text = f"[F-2] Arc {arc_no}{ep_text}: {issue}{detail_suffix}"
            results.append(
                {
                    "check": "investment_math_llm",
                    "severity": severity,
                    "category": category,
                    "text": text,
                }
            )

        return results

    def _parse_json_array(self, raw: str) -> list[dict]:
        """3-step JSON 파싱 폴백."""
        if not raw:
            return []

        # 1) 전체 파싱
        try:
            obj = json.loads(raw)
            if isinstance(obj, list):
                return obj
        except Exception:
            pass

        # 2) [...] 범위 추출 파싱
        m = re.search(r"\[[\s\S]*\]", raw)
        if m:
            try:
                obj = json.loads(m.group(0))
                if isinstance(obj, list):
                    return obj
            except Exception:
                pass

        # 3) 실패 → 빈 리스트 (비치명)
        return []
