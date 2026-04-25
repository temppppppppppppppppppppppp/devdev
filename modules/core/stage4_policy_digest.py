from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_POLICY_PATH = ROOT / "config" / "settings" / "stage4_policy_digest.json"


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


@lru_cache(maxsize=1)
def load_stage4_policy_digest() -> dict[str, Any]:
    default_digest: dict[str, Any] = {
        "interview_round": {
            "accepted_verdicts": ["PASS", "PASS_WITH_FIX"],
            "max_rounds": None,
        },
        "exhaustion": {
            "allow_best_manuscript_adoption": False,
            "default_operator_choice": 2,
        },
        "shadow_mode": {
            "enabled": False,
            "max_rounds": None,
            "log_all_episodes": False,
        },
        "retry_escalation": {
            "quality_risk_inplace_threshold": 1,
            "default_inplace_threshold": 2,
            "blueprint_regeneration_after_inplace_streak": 2,
            "treat_post_select_conflict_as_logic_like": True,
        },
    }

    if not _POLICY_PATH.exists():
        return default_digest

    try:
        payload = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        logging.warning("[stage4_policy_digest] load failed, defaults preserved: %s", exc)
        return default_digest

    if not isinstance(payload, dict):
        return default_digest
    return _deep_merge_dict(default_digest, payload)


def resolve_stage4_policy_value(*path: str, default: Any = None) -> Any:
    payload: Any = load_stage4_policy_digest()
    for key in path:
        if not isinstance(payload, dict):
            return default
        payload = payload.get(key)
    return default if payload is None else payload
