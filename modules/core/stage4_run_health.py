"""Stage4 run-health classification helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

STAGE4_RUN_HEALTH_SCHEMA_VERSION = "stage4_run_health_v1"
RETRY_HEAVY_ATTEMPT_THRESHOLD = 4
RUN_HEALTH_CLASS_KEYS = ("pure_pass", "repaired_pass", "retry_heavy_pass")


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _artifact_class(path: object) -> str:
    value = str(path or "").strip()
    if not value:
        return ""
    return Path(value).name.split("__", 1)[0]


def _attempt_num_from_path(path: object) -> int:
    match = re.search(r"(?:^|[/\\])attempt_(\d+)(?:[/\\]|$)", str(path or ""))
    return _safe_int(match.group(1), 0) if match else 0


def classify_stage4_run_health(
    *,
    attempt_artifact_meta: dict[str, Any] | None = None,
    threshold: int = RETRY_HEAVY_ATTEMPT_THRESHOLD,
) -> dict[str, Any]:
    """Classify how costly a settled Stage4 PASS was without judging prose quality."""

    meta = dict(attempt_artifact_meta or {}) if isinstance(attempt_artifact_meta, dict) else {}
    metadata_present = bool(meta)
    artifact_path = str(meta.get("artifact_path") or "").strip()
    artifact_class = str(meta.get("artifact_class") or "").strip() or _artifact_class(artifact_path)
    attempt_num = _safe_int(meta.get("attempt_num"), 0) or _attempt_num_from_path(artifact_path)
    initial_verdict = str(meta.get("initial_verdict") or "").strip().upper()
    final_verdict = str(meta.get("final_verdict") or "").strip().upper()
    patch_strategy = str(meta.get("patch_strategy") or "").strip()
    structural_attempted = bool(meta.get("structural_attempted"))
    retry_heavy = metadata_present and attempt_num >= max(1, int(threshold or RETRY_HEAVY_ATTEMPT_THRESHOLD))
    repaired = metadata_present and (
        artifact_class == "patched_after_fix"
        or initial_verdict == "PASS_WITH_FIX"
        or final_verdict == "PASS_WITH_FIX"
        or bool(meta.get("is_patch"))
        or bool(meta.get("is_patch_fallback"))
        or bool(patch_strategy)
        or structural_attempted
    )
    pure = metadata_present and not repaired and not retry_heavy
    classes: list[str] = []
    if pure:
        classes.append("pure_pass")
    if repaired:
        classes.append("repaired_pass")
    if retry_heavy:
        classes.append("retry_heavy_pass")
    if not classes:
        classes.append("accepted_pass")

    return {
        "schema_version": STAGE4_RUN_HEALTH_SCHEMA_VERSION,
        "success_class": classes[0],
        "success_classes": classes,
        "pure_pass": pure,
        "repaired_pass": repaired,
        "retry_heavy_pass": retry_heavy,
        "attempt_num": attempt_num,
        "retry_heavy_threshold": max(1, int(threshold or RETRY_HEAVY_ATTEMPT_THRESHOLD)),
        "artifact_class": artifact_class,
        "artifact_path": artifact_path,
        "attempt_key": str(meta.get("attempt_key") or "").strip(),
        "initial_verdict": initial_verdict,
        "final_verdict": final_verdict,
    }


def extract_stage4_run_health(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    summary = value.get("signal_summary") if "signal_summary" in value else value
    if not isinstance(summary, dict):
        return {}
    run_health = summary.get("run_health")
    return dict(run_health) if isinstance(run_health, dict) else {}


def summarize_stage4_run_health_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {key: 0 for key in RUN_HEALTH_CLASS_KEYS}
    for row in rows:
        run_health = extract_stage4_run_health(row)
        classes = run_health.get("success_classes")
        if isinstance(classes, list):
            class_names = {str(item) for item in classes}
        else:
            class_names = {str(run_health.get("success_class") or "")}
        for key in RUN_HEALTH_CLASS_KEYS:
            if bool(run_health.get(key)) or key in class_names:
                counts[key] += 1
    return counts
