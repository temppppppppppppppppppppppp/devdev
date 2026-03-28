from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_DIGEST_DIR = ROOT / "config" / "treatments" / "harness_digests"


def _digest_path(*, family: str, stage: str) -> Path:
    normalized_family = str(family or "").strip().lower().replace("_", "-")
    normalized_stage = str(stage or "").strip().lower().replace("_", "-")
    return _DIGEST_DIR / f"{normalized_family}-{normalized_stage}-digest.json"


def load_harness_digest(*, family: str, stage: str) -> dict[str, Any]:
    path = _digest_path(family=family, stage=stage)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def render_harness_digest_lines(digest: dict[str, Any]) -> list[str]:
    if not isinstance(digest, dict) or not digest:
        return []

    lines = ["## Harness Digest"]
    family = str(digest.get("family") or "").strip()
    stage = str(digest.get("stage") or "").strip()
    if family:
        lines.append(f"- family: {family}")
    if stage:
        lines.append(f"- stage: {stage}")

    for label, key in (
        ("Hard Prohibitions", "hard_prohibitions"),
        ("Continuity Equalities", "continuity_equalities"),
        ("Family Axis Requirements", "family_axis_requirements"),
        ("Lexicon Bans", "lexicon_bans"),
        ("Output Contract", "output_contract"),
        ("Acceptance Gates", "acceptance_gates"),
    ):
        values = digest.get(key)
        if not isinstance(values, list):
            continue
        cleaned = [str(item).strip() for item in values if str(item).strip()]
        if not cleaned:
            continue
        lines.append("")
        lines.append(f"### {label}")
        lines.extend(f"- {item}" for item in cleaned)

    lines.append("")
    lines.append("Use this digest as a strict operator contract. Prefer the digest over vague generalization.")
    return lines
