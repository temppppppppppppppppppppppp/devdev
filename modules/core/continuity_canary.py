from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

CONTINUITY_CANARY_VERSION = "continuity-canary-v1"
CONTINUITY_CANARY_REPORT = "continuity_canary_report.json"

_DATE_PATTERNS = (
    re.compile(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b"),
    re.compile(r"\b(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\b"),
    re.compile(r"\b(\d{1,2})월\s*(\d{1,2})일\b"),
    re.compile(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?\s+(\d{1,2})\b",
        re.IGNORECASE,
    ),
)
_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}
_EXPLICIT_TRANSITION_MARKERS = (
    "* * *",
    "scene cut",
    "transition",
    "cut to",
    "meanwhile",
    "장면 전환",
    "한편",
    "잠시 후",
    "며칠 뒤",
    "이동",
    "옮겼",
)
_ACTIVE_ROLE_KEYS = {
    "active_characters",
    "characters",
    "participants",
    "npcs",
    "speakers",
    "actors",
}


def _compact(value: Any, *, limit: int = 240) -> str:
    text = " ".join(str(value or "").split()).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if value not in (None, "", [], {}):
        return [value]
    return []


def _safe_json(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_safe_json(item) for item in value]
    return str(value)


def _iter_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        text = value.strip()
        if text:
            strings.append(text)
    elif isinstance(value, Mapping):
        for item in value.values():
            strings.extend(_iter_strings(item))
    elif isinstance(value, list | tuple):
        for item in value:
            strings.extend(_iter_strings(item))
    return strings


def _candidate_text(candidate: Any) -> str:
    if isinstance(candidate, str):
        return candidate
    return "\n".join(_iter_strings(candidate))


def _candidate_field(candidate: Any, *keys: str) -> str:
    if not isinstance(candidate, Mapping):
        return ""
    for key in keys:
        value = candidate.get(key)
        if isinstance(value, Mapping):
            nested = _candidate_field(value, *keys)
            if nested:
                return nested
        text = _compact(value, limit=240)
        if text:
            return text
    return ""


def _normalize_date_token(*groups: str) -> str:
    parts = [str(group or "").strip() for group in groups if str(group or "").strip()]
    if len(parts) == 3:
        year, month, day = parts
        if year.isdigit():
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        month_num = _MONTHS.get(year.lower()[:3], 0) or _MONTHS.get(year.lower(), 0)
        if month_num:
            return f"{month_num:02d}-{int(day):02d}"
    if len(parts) == 2:
        month, day = parts
        if month.isdigit():
            return f"{int(month):02d}-{int(day):02d}"
        month_num = _MONTHS.get(month.lower()[:3], 0) or _MONTHS.get(month.lower(), 0)
        if month_num:
            return f"{month_num:02d}-{int(day):02d}"
    return "-".join(parts)


def _extract_date_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for pattern in _DATE_PATTERNS:
        for match in pattern.findall(str(text or "")):
            groups = match if isinstance(match, tuple) else (match,)
            normalized = _normalize_date_token(*groups)
            if normalized:
                tokens.add(normalized)
                if re.match(r"\d{4}-\d{2}-\d{2}", normalized):
                    tokens.add(normalized[5:])
    return tokens


def _has_explicit_transition(candidate_text: str) -> bool:
    lowered = str(candidate_text or "").lower()
    return any(marker.lower() in lowered for marker in _EXPLICIT_TRANSITION_MARKERS)


def _flatten_active_role_names(candidate: Any) -> set[str]:
    names: set[str] = set()

    def visit(value: Any, *, parent_key: str = "") -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_text = str(key or "").strip()
                if key_text in _ACTIVE_ROLE_KEYS:
                    for raw in _as_list(item):
                        if isinstance(raw, Mapping):
                            name = _compact(raw.get("name") or raw.get("npc") or raw.get("character"), limit=80)
                        else:
                            name = _compact(raw, limit=80)
                        if name:
                            names.add(name)
                visit(item, parent_key=key_text)
        elif isinstance(value, list | tuple):
            for item in value:
                visit(item, parent_key=parent_key)

    visit(candidate)
    return names


def _make_finding(
    *,
    canary_id: str,
    severity: str,
    expected: Any,
    observed: Any,
    evidence: str,
) -> dict[str, Any]:
    return {
        "canary_id": canary_id,
        "severity": severity,
        "requires_director_review": True,
        "judgment_authority": "director_llm",
        "expected": _safe_json(expected),
        "observed": _safe_json(observed),
        "evidence": _compact(evidence, limit=320),
    }


def evaluate_continuity_canaries(
    *,
    projection: Mapping[str, Any] | None,
    candidate: Any,
    dead_characters: Sequence[str] | None = None,
    prior_failure_signatures: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Evaluate deterministic tripwires without making a narrative verdict."""
    packet = _as_dict(projection)
    accepted_state = _as_dict(packet.get("accepted_source_state"))
    text = _candidate_text(candidate)
    findings: list[dict[str, Any]] = []

    expected_time = _compact(accepted_state.get("time_flow"), limit=160)
    observed_time = _candidate_field(candidate, "time_flow", "time_context", "timeline")
    expected_dates = _extract_date_tokens(expected_time)
    observed_dates = _extract_date_tokens(observed_time or text)
    if expected_dates and observed_dates and expected_dates.isdisjoint(observed_dates):
        findings.append(
            _make_finding(
                canary_id="date_drift",
                severity="review_required",
                expected=sorted(expected_dates),
                observed=sorted(observed_dates),
                evidence=observed_time or text,
            )
        )

    expected_location = _compact(
        accepted_state.get("end_location") or accepted_state.get("start_location"),
        limit=120,
    )
    observed_location = _candidate_field(candidate, "start_location", "location", "end_location")
    if (
        expected_location
        and observed_location
        and expected_location not in observed_location
        and observed_location not in expected_location
        and not _has_explicit_transition(text)
    ):
        findings.append(
            _make_finding(
                canary_id="location_drift",
                severity="review_required",
                expected=expected_location,
                observed=observed_location,
                evidence="structured candidate location without explicit transition",
            )
        )

    active_names = _flatten_active_role_names(candidate)
    dead_hits = sorted(
        {
            str(name or "").strip()
            for name in dead_characters or []
            if str(name or "").strip() and str(name or "").strip() in active_names
        }
    )
    if dead_hits:
        findings.append(
            _make_finding(
                canary_id="dead_character_active_role",
                severity="review_required",
                expected="deceased characters may be recalled or mentioned only",
                observed=dead_hits,
                evidence="structured active role field contains deceased character",
            )
        )

    normalized_text = " ".join(text.lower().split())
    replay_hits = []
    for signature in prior_failure_signatures or []:
        sig = " ".join(str(signature or "").lower().split()).strip()
        if sig and sig in normalized_text:
            replay_hits.append(signature)
    if replay_hits:
        findings.append(
            _make_finding(
                canary_id="prior_failure_replay",
                severity="review_required",
                expected="previous failure signature should not reappear unchanged",
                observed=replay_hits[:5],
                evidence="candidate text repeats prior failure signature",
            )
        )

    status = "review_required" if findings else "ok"
    return {
        "schema_version": CONTINUITY_CANARY_VERSION,
        "status": status,
        "authority_role": "objective_tripwire_not_director_verdict",
        "judgment_authority": "director_llm",
        "canary_ids": [
            "date_drift",
            "location_drift",
            "dead_character_active_role",
            "prior_failure_replay",
        ],
        "finding_count": len(findings),
        "findings": findings,
    }


def merge_continuity_canary_reports(reports: Sequence[Mapping[str, Any] | None]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    evaluated = 0
    for report in reports:
        payload = _as_dict(report)
        if not payload:
            continue
        evaluated += 1
        for finding in _as_list(payload.get("findings")):
            if isinstance(finding, Mapping):
                findings.append(dict(finding))
    status = "review_required" if findings else ("ok" if evaluated else "not_available")
    return {
        "schema_version": CONTINUITY_CANARY_VERSION,
        "status": status,
        "authority_role": "objective_tripwire_not_director_verdict",
        "judgment_authority": "director_llm",
        "evaluated_reports": evaluated,
        "finding_count": len(findings),
        "findings": findings,
    }


def read_continuity_canary_report(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root) / "logs" / CONTINUITY_CANARY_REPORT
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "schema_version": CONTINUITY_CANARY_VERSION,
            "status": "not_available",
            "finding_count": 0,
            "findings": [],
        }
    return payload if isinstance(payload, dict) else {}


def write_continuity_canary_report(project_root: str | Path, report: Mapping[str, Any]) -> Path:
    path = Path(project_root) / "logs" / CONTINUITY_CANARY_REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_safe_json(report), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
