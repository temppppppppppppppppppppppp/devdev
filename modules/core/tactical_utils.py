"""
utf8-hygiene: allow-file -- _EPISODE_HEADER_PATTERNS contains literal Korean episode-header regex strings (`\\[제\\s*{ep}\\s*화...`) where Python non-greedy `(.*?)` and lookahead `(?=...)` syntax sits adjacent to Korean tokens; the hygiene scanner flags `?` next to non-ASCII as suspicious_question_token even though these are valid regex quantifiers, not mojibake.
[TTE] Tactical Doc Episode Extraction — 에피소드별 전술 추출 공유 유틸
"""

import json
import re

_EPISODE_HEADER_PATTERNS = [
    # [제 N화 ...]
    r"\[제\s*{ep}\s*화[^\]]*\](.*?)(?=\[제\s*\d+\s*화|\Z)",
    # ### 제N화, ## 제N화 (마크다운 헤더)
    r"#{{2,3}}\s*제\s*{ep}\s*화[^\n]*(.*?)(?=#{{2,3}}\s*제\s*\d+\s*화|\Z)",
    # **제N화** (마크다운 볼드)
    r"\*\*제\s*{ep}\s*화[^*]*\*\*(.*?)(?=\*\*제\s*\d+\s*화|\Z)",
    # 제N화: 또는 제N화 - (콜론/대시 구분)
    r"제\s*{ep}\s*화\s*[:\-\u2013\u2014]\s*(.*?)(?=제\s*\d+\s*화\s*[:\-\u2013\u2014]|\Z)",
    # 제N화) 또는 (제N화) (괄호 구분)
    r"[\(]?제\s*{ep}\s*화[\)]\s*(.*?)(?=[\(]?제\s*\d+\s*화[\)]|\Z)",
    # Beat N: (영문 형식)
    r"Beat\s*{ep}\s*:\s*(.*?)(?=Beat\s*\d+\s*:|\Z)",
]


def _safe_tactical_str(tactical_doc) -> str:
    """tactical_doc를 안전하게 문자열로 변환 (None/dict/기타 타입 방어)."""
    if not tactical_doc:
        return ""
    if isinstance(tactical_doc, dict):
        return json.dumps(tactical_doc, ensure_ascii=False, indent=2)
    return str(tactical_doc) if not isinstance(tactical_doc, str) else tactical_doc


def extract_episode_tactical(
    tactical_doc,
    ep_num: int,
    *,
    episode_details=None,
    fallback_full: bool = True,
    prefer_full_doc: bool = False,
    full_doc_budget_chars: int = 2000,
) -> str:
    """tactical_doc에서 특정 에피소드의 전술 내용만 추출.

    Default priority: episode_details > regex > full tactical_doc(fallback)

    When ``prefer_full_doc=True`` (Stage3 producer-input only):
      - episode_details(있으면) + regex/per-ep slice 본문을 함께 결합한다
      - 결합 결과는 ``full_doc_budget_chars`` 한도 안에서 잘린다
      - 13개 다른 호출자(Stage4/Director/continuity/ToT/prompt_builder 등)는
        파라미터 default가 False이므로 영향을 받지 않는다

    Args:
        tactical_doc: 전술서 (str/dict/None)
        ep_num: 에피소드 번호
        episode_details: Arc의 episode_details 리스트
        fallback_full: True면 추출 실패 시 전체 반환, False면 빈 문자열
        prefer_full_doc: Stage3 producer 전용 - bullet TL;DR + per-ep prose 결합
        full_doc_budget_chars: prefer_full_doc 모드 결합 결과 최대 길이
    """
    # 1. episode_details 우선
    bullet_content = ""
    if episode_details and isinstance(episode_details, list):
        for item in episode_details:
            if isinstance(item, dict) and item.get("ep_num") == ep_num:
                details = item.get("details") or []
                if isinstance(details, list) and details:
                    bullet_content = "\n".join(f"- {d}" for d in details if isinstance(d, str))
                break

    # 2. regex 패턴 매칭으로 per-ep slice 추출
    slice_content = ""
    tactical_str = _safe_tactical_str(tactical_doc)
    if tactical_str:
        for tmpl in _EPISODE_HEADER_PATTERNS:
            match = re.search(tmpl.format(ep=ep_num), tactical_str, re.DOTALL)
            if match:
                slice_content = match.group(1).strip()
                if slice_content:
                    break

    # Stage3 producer-input 결합 모드: TL;DR + per-ep prose
    if prefer_full_doc and (bullet_content or slice_content):
        parts: list[str] = []
        if bullet_content:
            parts.append(f"[TL;DR — episode_details]\n{bullet_content}")
        if slice_content:
            parts.append(f"[Tactical doc — 제{ep_num}화]\n{slice_content}")
        combined = "\n\n".join(parts)
        if full_doc_budget_chars > 0 and len(combined) > full_doc_budget_chars:
            return combined[:full_doc_budget_chars].rstrip() + "\n…[truncated]"
        return combined

    # Default mode: episode_details > regex > fallback
    if bullet_content:
        return bullet_content
    if slice_content:
        return slice_content

    # 3. fallback
    return tactical_str if fallback_full else ""
