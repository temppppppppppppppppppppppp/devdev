"""Shared dialogue extraction helpers for telemetry and advisory checks."""

from __future__ import annotations

import re

_DIALOGUE_PATTERNS = (
    r'"[^"\n]+?"',
    r"“[^”\n]+”",
    r"‘[^’\n]{5,}’",
    r"'[^'\n]{5,}'",
    r"「[^」\n]+」",
    r"『[^』\n]+』",
)

_DIALOGUE_REGEXES = tuple(re.compile(pattern, re.MULTILINE) for pattern in _DIALOGUE_PATTERNS)


def extract_dialogue_segments(text: str) -> list[str]:
    if not text:
        return []
    segments: list[str] = []
    for regex in _DIALOGUE_REGEXES:
        segments.extend(match.group(0) for match in regex.finditer(text))
    return segments


def count_dialogue_segments(text: str) -> int:
    return len(extract_dialogue_segments(text))


def count_dialogue_characters(text: str) -> int:
    return sum(len(segment) for segment in extract_dialogue_segments(text))
