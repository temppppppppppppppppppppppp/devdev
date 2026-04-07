# -*- coding: utf-8 -*-
"""WG-V1 shape validator runner for material-side work_guard drafts.

Usage examples:
    python -X utf8 scripts/run_work_guard_v1.py --path docs/2026-04-06/work_guard_greenplus_batch01/gatekeeper_heir.work_guard.yaml
    python -X utf8 scripts/run_work_guard_v1.py --work-id gatekeeper_heir
    python -X utf8 scripts/run_work_guard_v1.py --project-dir projects/demo_project
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.genre_guards.work_guard import (  # noqa: E402
    WorkGuardConfigError,
    load_work_guard_config,
)
from modules.narrative_router.artifact_paths import resolve_work_guard_library_path  # noqa: E402

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_HOLD = 2

_REQUIRED_LIST_FIELDS = (
    "tracking_slots",
    "mandatory_scene_engines",
    "forbidden_flattenings",
    "protagonist_weapon",
)
_GENERIC_MARKERS = frozenset(
    {
        "성장",
        "성공",
        "열심히함",
        "generic",
        "placeholder",
        "todo",
        "tbd",
        "sample",
        "temp",
    }
)


def _normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = _normalize_scalar(item)
        if text:
            normalized.append(text)
    return normalized


def _is_generic_text(value: str) -> bool:
    compact = value.strip().lower().replace(" ", "")
    if not compact:
        return True
    if compact in _GENERIC_MARKERS:
        return True
    return any(marker in compact for marker in _GENERIC_MARKERS if len(marker) >= 4)


def _all_generic(entries: list[str]) -> bool:
    return bool(entries) and all(_is_generic_text(entry) for entry in entries)


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def resolve_target_path(
    *,
    path_value: str | None,
    work_id: str | None,
    project_dir: str | None,
) -> tuple[Path, str]:
    if path_value:
        return (Path(path_value).expanduser(), "path")
    if work_id:
        return (resolve_work_guard_library_path(work_id, root=ROOT), "work_id")
    project_root = Path(project_dir).expanduser()
    return (project_root / "config" / "work_guard.yaml", "project_dir")


def evaluate_work_guard_v1(path: Path, *, source: str) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    holds: list[dict[str, str]] = []
    notes: list[dict[str, str]] = []

    payload: dict[str, Any] = {
        "status": "fail",
        "exit_code": EXIT_FAIL,
        "path": str(path),
        "source": source,
        "work_id": "",
        "work_type": "",
        "counts": {
            "tracking_slots": 0,
            "mandatory_scene_engines": 0,
            "forbidden_flattenings": 0,
            "protagonist_weapon": 0,
            "admiration_axes": 0,
        },
        "failures": failures,
        "holds": holds,
        "notes": notes,
    }

    if not path.is_file():
        failures.append(_issue("missing_file", f"File not found: {path}"))
        return payload

    try:
        data = load_work_guard_config(path)
    except WorkGuardConfigError as exc:
        failures.append(_issue("config_error", str(exc)))
        return payload
    except Exception as exc:  # pragma: no cover - defensive only
        failures.append(
            _issue("unexpected_error", f"{path}: unexpected validation failure ({exc.__class__.__name__})")
        )
        return payload

    work_identity = data.get("work_identity")
    if not isinstance(work_identity, dict):
        failures.append(_issue("missing_work_identity", "work_identity mapping is required for WG-V1"))
        return payload

    payload["work_id"] = _normalize_scalar(work_identity.get("work_id"))
    payload["work_type"] = _normalize_scalar(work_identity.get("work_type"))

    one_line_truth = _normalize_scalar(work_identity.get("one_line_truth"))
    if not one_line_truth:
        failures.append(_issue("missing_one_line_truth", "work_identity.one_line_truth is required"))

    normalized_lists = {
        field_name: _normalize_str_list(work_identity.get(field_name))
        for field_name in _REQUIRED_LIST_FIELDS
    }
    for field_name, entries in normalized_lists.items():
        payload["counts"][field_name] = len(entries)
        if field_name not in work_identity:
            failures.append(
                _issue(f"missing_{field_name}", f"work_identity.{field_name} is required for WG-V1 freeze minimum"))

    protagonist_evaluation = work_identity.get("protagonist_evaluation")
    admiration_axes = []
    if isinstance(protagonist_evaluation, dict):
        admiration_axes = _normalize_str_list(protagonist_evaluation.get("admiration_axes"))
    payload["counts"]["admiration_axes"] = len(admiration_axes)

    if failures:
        return payload

    if not normalized_lists["tracking_slots"]:
        holds.append(_issue("empty_tracking_slots", "work_identity.tracking_slots is empty"))
    if not normalized_lists["mandatory_scene_engines"]:
        holds.append(_issue("empty_mandatory_scene_engines", "work_identity.mandatory_scene_engines is empty"))
    if not normalized_lists["forbidden_flattenings"]:
        holds.append(_issue("empty_forbidden_flattenings", "work_identity.forbidden_flattenings is empty"))
    elif len(normalized_lists["forbidden_flattenings"]) < 4:
        holds.append(
            _issue(
                "shallow_forbidden_flattenings",
                "work_identity.forbidden_flattenings is below the recommended minimum depth (4)",
            )
        )
    if not normalized_lists["protagonist_weapon"]:
        holds.append(_issue("empty_protagonist_weapon", "work_identity.protagonist_weapon is empty"))

    if _is_generic_text(one_line_truth):
        holds.append(_issue("generic_one_line_truth", "work_identity.one_line_truth looks too generic"))
    if _all_generic(normalized_lists["tracking_slots"]):
        holds.append(_issue("generic_tracking_slots", "tracking_slots looks too generic"))
    if _all_generic(normalized_lists["mandatory_scene_engines"]):
        holds.append(_issue("generic_scene_engines", "mandatory_scene_engines looks too generic"))
    if _all_generic(normalized_lists["protagonist_weapon"]):
        holds.append(_issue("generic_protagonist_weapon", "protagonist_weapon looks too generic"))

    required_text = "\n".join(
        [one_line_truth, *normalized_lists["tracking_slots"], *normalized_lists["mandatory_scene_engines"]]
    ).strip()
    if len(one_line_truth) > 280 or any(len(item) > 280 for item in normalized_lists["mandatory_scene_engines"]):
        holds.append(_issue("possible_longform_copy_paste", "some core fields look too long for a runtime rule draft"))
    elif len(required_text) > 3000:
        holds.append(_issue("possible_house_law_copy_paste", "core doctrine looks unusually long for WG-V1"))

    tracking_slot_count = payload["counts"]["tracking_slots"]
    if tracking_slot_count and not 2 <= tracking_slot_count <= 4:
        notes.append(
            _issue(
                "tracking_slot_count_recommendation",
                f"tracking_slots count {tracking_slot_count} is outside the recommended 2-4 band",
            )
        )

    scene_engine_count = payload["counts"]["mandatory_scene_engines"]
    if scene_engine_count and not 2 <= scene_engine_count <= 3:
        notes.append(
            _issue(
                "scene_engine_count_recommendation",
                f"mandatory_scene_engines count {scene_engine_count} is outside the recommended 2-3 band",
            )
        )

    admiration_axis_count = payload["counts"]["admiration_axes"]
    if admiration_axis_count and admiration_axis_count < 2:
        notes.append(
            _issue(
                "admiration_axis_count_recommendation",
                "admiration_axes count is below the recommended minimum of 2",
            )
        )

    if holds:
        payload["status"] = "hold"
        payload["exit_code"] = EXIT_HOLD
        return payload

    payload["status"] = "pass"
    payload["exit_code"] = EXIT_PASS
    return payload


def _render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"WG-V1 {str(report['status']).upper()}: {report['path']}",
        f"- source: {report['source']}",
        f"- work_id: {report['work_id'] or '(empty)'}",
        f"- work_type: {report['work_type'] or '(empty)'}",
        (
            "- counts: "
            f"tracking_slots={report['counts']['tracking_slots']}, "
            f"mandatory_scene_engines={report['counts']['mandatory_scene_engines']}, "
            f"forbidden_flattenings={report['counts']['forbidden_flattenings']}, "
            f"protagonist_weapon={report['counts']['protagonist_weapon']}, "
            f"admiration_axes={report['counts']['admiration_axes']}"
        ),
    ]

    failures = report.get("failures") or []
    holds = report.get("holds") or []
    notes = report.get("notes") or []

    if failures:
        lines.append("- failures:")
        for item in failures:
            lines.append(f"  - [{item['code']}] {item['message']}")
    if holds:
        lines.append("- holds:")
        for item in holds:
            lines.append(f"  - [{item['code']}] {item['message']}")
    if notes:
        lines.append("- notes:")
        for item in notes:
            lines.append(f"  - [{item['code']}] {item['message']}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WG-V1 shape validation on a work_guard YAML.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--path", help="Explicit YAML path to validate.")
    target_group.add_argument("--work-id", help="Resolve the library publish path for a work_id.")
    target_group.add_argument(
        "--project-dir",
        help="Project directory containing config/work_guard.yaml.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    target_path, source = resolve_target_path(
        path_value=args.path,
        work_id=args.work_id,
        project_dir=args.project_dir,
    )
    report = evaluate_work_guard_v1(target_path, source=source)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_render_text_report(report))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
