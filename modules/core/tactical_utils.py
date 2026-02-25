"""[TTE] Tactical Doc Episode Extraction — 에피소드별 전술 추출 공유 유틸"""

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
) -> str:
    """tactical_doc에서 특정 에피소드의 전술 내용만 추출.

    Priority: episode_details > regex > full tactical_doc(fallback)

    Args:
        tactical_doc: 전술서 (str/dict/None)
        ep_num: 에피소드 번호
        episode_details: Arc의 episode_details 리스트
        fallback_full: True면 추출 실패 시 전체 반환, False면 빈 문자열
    """
    # 1. episode_details 우선
    content = ""
    if episode_details and isinstance(episode_details, list):
        for item in episode_details:
            if isinstance(item, dict) and item.get("ep_num") == ep_num:
                details = item.get("details") or []
                if isinstance(details, list) and details:
                    content = "\n".join(f"- {d}" for d in details if isinstance(d, str))
                break

    # 2. regex 패턴 매칭
    if not content:
        tactical_str = _safe_tactical_str(tactical_doc)
        if tactical_str:
            for tmpl in _EPISODE_HEADER_PATTERNS:
                match = re.search(tmpl.format(ep=ep_num), tactical_str, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if content:
                        break

    # 3. fallback
    if not content:
        return _safe_tactical_str(tactical_doc) if fallback_full else ""

    return content
