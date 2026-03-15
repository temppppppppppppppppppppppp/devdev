"""Mode B 프롬프트 분류기 — stdout 텍스트 → 구조화된 프롬프트 메타데이터.

역할:
- stdout 부분 라인(입력 대기 상태)을 프롬프트로 판별
- input_type, default, options 자동 추출
- step_id 분류 (UI 렌더링용)
"""

from __future__ import annotations

import re
from typing import Any

# ─── 프롬프트 감지 패턴 (순서 중요: 먼저 매칭된 것 우선) ─────────────────────

_PROMPT_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # (regex, input_type, step_id_hint)
    # Yes/No 확인
    (re.compile(r"\([yY][/|][nN]\)\s*[:：]?\s*$"), "bool", "confirm"),
    (re.compile(r"\([Yy]es[/|][Nn]o\)\s*[:：]?\s*$"), "bool", "confirm"),
    # [Enter] 계속
    (re.compile(r"\[Enter\]"), "enter", "continue"),
    # 다중 줄 입력 (컨셉 입력 등)
    (re.compile(r"빈\s*줄로\s*종료"), "multiline", "concept_input"),
    # 경로 입력 (> 프롬프트)
    (re.compile(r"^>\s*$"), "string", "path_input"),
    (re.compile(r"경로\s*입력"), "string", "path_input"),
    # 숫자 범위 + 기본값 (예: "1~5, 기본: 3")
    (re.compile(r"(\d+)\s*[~\-]\s*(\d+).*기본"), "int", "range_input"),
    # 숫자 범위 입력 (예: "1~5 입력")
    (re.compile(r"(\d+)\s*[~\-]\s*(\d+).*입력"), "int", "range_input"),
    # Choice / 선택 (괄호 내 옵션 포함, 예: "Choice (1.무협 / 2.헌터):")
    (re.compile(r"(?:👉\s*)?(?:Choice|선택)\s*(?:\(.*\))?\s*[:：]\s*$"), "enum", "choice"),
    # 선택 프롬프트 (기본값 있음)
    (re.compile(r"선택\s*\(?\s*기본\s*[:：]?\s*(\d+)\s*\)?\s*[:：]\s*$"), "enum", "choice"),
    # 일반 프롬프트 (: 로 끝남)
    (re.compile(r"[:：]\s*$"), "string", "generic_input"),
]

# ─── 옵션 추출 패턴 ──────────────────────────────────────────────────────────

_OPTION_LINE_RE = re.compile(
    r"^\s*\[(\d+)\]\s+(.+?)(?:\s*←.*)?$"      # [1] 무협
    r"|^\s*(\d+)\s*[.)\-:]\s*(.+?)(?:\s*←.*)?$"  # 1. 무협 / 1) 무협
)

# 기본값 추출
_DEFAULT_RE = re.compile(r"기본\s*[:：]?\s*(\d+)")


def is_prompt(text: str) -> bool:
    """주어진 텍스트가 사용자 입력을 기다리는 프롬프트인지 판별."""
    stripped = text.strip()
    if not stripped:
        return False
    for pattern, _, _ in _PROMPT_PATTERNS:
        if pattern.search(stripped):
            return True
    return False


def classify(text: str, context_lines: list[str] | None = None) -> dict:
    """프롬프트 텍스트를 구조화된 메타데이터로 분류.

    Args:
        text: 프롬프트 텍스트 (stdin 대기 중인 부분 라인).
        context_lines: 프롬프트 직전 stdout 라인들 (옵션 추출용).

    Returns:
        {
            "input_type": "enum" | "int" | "string" | "bool" | "enter" | "multiline",
            "step_id": str,
            "default": Any,
            "options": [{"key": "1", "label": "..."}, ...],
            "prompt_text": str,
        }
    """
    stripped = text.strip()
    context_lines = context_lines or []

    input_type = "string"
    step_id = "generic_input"
    default: Any = None

    for pattern, itype, sid in _PROMPT_PATTERNS:
        m = pattern.search(stripped)
        if m:
            input_type = itype
            step_id = sid
            break

    # 기본값 추출
    dm = _DEFAULT_RE.search(stripped)
    if dm:
        default = dm.group(1)

    # bool 타입 기본값
    if input_type == "bool":
        if re.search(r"\(Y[/|]n\)", stripped):
            default = "y"
        elif re.search(r"\(y[/|]N\)", stripped):
            default = "n"
        else:
            default = "y"

    # enter 타입 기본값
    if input_type == "enter":
        default = ""

    # 컨텍스트 라인에서 옵션 추출 (프롬프트 직전 연속 블록만 — 이전 메뉴 유입 차단)
    options = []
    for line in reversed(context_lines):
        stripped_line = line.strip()
        if not stripped_line:
            continue  # 빈 줄 건너뜀
        om = _OPTION_LINE_RE.match(stripped_line)
        if om:
            key = om.group(1) or om.group(3)
            label = om.group(2) or om.group(4)
            if key and label:
                options.insert(0, {"key": key, "label": label.strip()})
        else:
            break  # 비옵션 라인에서 중단

    # 컨텍스트에서 옵션 못 찾았으면 프롬프트 텍스트 자체에서 인라인 추출
    # 예: "Choice (1.무협 / 2.헌터 / 3.투자): "
    if not options and input_type == "enum":
        for m in re.finditer(r"(\d+)\s*[.·]\s*([^\s/,)]+)", stripped):
            options.append({"key": m.group(1), "label": m.group(2).strip()})

    # int 타입인데 범위가 감지되면 step_id 보강
    if input_type == "int" and not default:
        dm2 = _DEFAULT_RE.search(stripped)
        if dm2:
            default = dm2.group(1)

    return {
        "input_type": input_type,
        "step_id": step_id,
        "default": default,
        "options": options,
        "prompt_text": stripped,
    }
