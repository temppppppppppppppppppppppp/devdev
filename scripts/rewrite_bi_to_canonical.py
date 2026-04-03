#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.project_support import default_external_pov_insert_policy, normalize_external_pov_insert_policy
from modules.core.response_schemas import validate_bible_canonical_structure
from modules.core.stage0_handoff import (
    build_plot_roadmap_from_treatment,
    get_effective_bible_root,
    normalize_bible_to_canonical_view,
    validate_plot_roadmap_entries,
)

RUNTIME_PROTAGONIST_KEYS = ("world_origin", "incarnation_type", "pov", "external_pov_insert_policy")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_work_key(value: str) -> str:
    value = re.sub(r"^\d+_", "", value)
    return value.strip("_").lower()


def infer_bible_work_key(path: Path) -> str:
    stem = path.stem
    for pattern in (r"^\d+_bi_(.+)$", r"^\d+_(.+)_bi$", r"^(.+)_bi$"):
        match = re.match(pattern, stem)
        if match:
            return _normalize_work_key(match.group(1))
    return _normalize_work_key(stem)


def _extract_genre_hint(payload: dict[str, Any]) -> str:
    master = get_effective_bible_root(payload)
    project_data = master.get("ProjectData", {}) if isinstance(master, dict) else {}
    meta = project_data.get("MetaInfo", {}) if isinstance(project_data, dict) else {}
    candidates = (
        payload.get("_genre"),
        meta.get("genre"),
        meta.get("genre_archetype"),
        meta.get("subgenre"),
    )
    for candidate in candidates:
        text = _as_text(candidate)
        if text:
            return text
    return ""


def _normalize_contract_genre(raw_genre: str) -> str:
    genre = _as_text(raw_genre).lower()
    if "wuxia" in genre or "무협" in genre:
        return "wuxia"
    if "investment" in genre or "투자" in genre or "chaebol" in genre or "재벌" in genre:
        return "investment"
    return genre


def _discover_sibling_pov_contract(input_path: Path) -> tuple[str, str]:
    work_key = infer_bible_work_key(input_path)
    best_score = (-1, -1)
    best_contract = ("", "")
    for candidate in sorted(input_path.parent.glob("*.json")):
        if candidate == input_path or infer_bible_work_key(candidate) != work_key:
            continue
        try:
            payload = load_json(candidate)
        except Exception:
            continue
        protagonist = get_effective_bible_root(payload).get("protagonist_config", {})
        if not isinstance(protagonist, dict):
            continue
        pov = _as_text(protagonist.get("pov"))
        external_policy = _as_text(protagonist.get("external_pov_insert_policy"))
        score = (int(bool(pov)) + int(bool(external_policy)), len(protagonist))
        if score > best_score:
            best_score = score
            best_contract = (pov, external_policy)
    return best_contract


def _infer_world_origin_and_incarnation(
    protagonist_config: dict[str, Any],
    *,
    genre_hint: str,
) -> tuple[str, str]:
    world_origin = _as_text(protagonist_config.get("world_origin"))
    incarnation_type = _as_text(protagonist_config.get("incarnation_type"))
    if world_origin and incarnation_type:
        return world_origin, incarnation_type

    is_regressor = bool(protagonist_config.get("is_regressor"))
    has_regression_marker = any(
        protagonist_config.get(key)
        for key in ("regression_origin", "regression_point", "regression_mechanic")
    )
    normalized_genre = _normalize_contract_genre(genre_hint)

    if not world_origin:
        if normalized_genre == "wuxia":
            world_origin = "원시인"
        else:
            world_origin = "현대인"

    if not incarnation_type:
        if is_regressor or has_regression_marker:
            incarnation_type = "회귀자"
        elif normalized_genre == "wuxia":
            incarnation_type = "일반"
        else:
            incarnation_type = "일반"

    return world_origin, incarnation_type


def _repair_runtime_protagonist_contract(
    payload: dict[str, Any],
    *,
    input_path: Path | None,
) -> list[str]:
    warnings: list[str] = []
    master = get_effective_bible_root(payload)
    protagonist = master.get("protagonist_config")
    if protagonist is None or not isinstance(protagonist, dict):
        master["protagonist_config"] = {}
        protagonist = master["protagonist_config"]
        warnings.append("created protagonist_config dict for BI rewrite")

    genre_hint = _extract_genre_hint(payload)
    sibling_pov = sibling_external_policy = ""
    if input_path is not None:
        sibling_pov, sibling_external_policy = _discover_sibling_pov_contract(input_path)

    world_origin, incarnation_type = _infer_world_origin_and_incarnation(
        protagonist,
        genre_hint=genre_hint,
    )
    if not protagonist.get("world_origin") and world_origin:
        protagonist["world_origin"] = world_origin
        warnings.append(f"filled protagonist_config.world_origin='{world_origin}'")
    if not protagonist.get("incarnation_type") and incarnation_type:
        protagonist["incarnation_type"] = incarnation_type
        warnings.append(f"filled protagonist_config.incarnation_type='{incarnation_type}'")

    pov = _as_text(protagonist.get("pov")) or sibling_pov or "3인칭"
    if not protagonist.get("pov"):
        protagonist["pov"] = pov
        if sibling_pov:
            warnings.append(f"borrowed protagonist_config.pov from sibling BI '{pov}'")
        else:
            warnings.append(f"filled protagonist_config.pov='{pov}'")

    external_policy = _as_text(protagonist.get("external_pov_insert_policy")) or sibling_external_policy
    if not external_policy:
        external_policy = default_external_pov_insert_policy(pov, genre=_normalize_contract_genre(genre_hint))
    external_policy = normalize_external_pov_insert_policy(
        external_policy,
        primary_pov=pov,
        genre=_normalize_contract_genre(genre_hint),
    )
    if not protagonist.get("external_pov_insert_policy"):
        protagonist["external_pov_insert_policy"] = external_policy
        if sibling_external_policy:
            warnings.append(
                "borrowed protagonist_config.external_pov_insert_policy from sibling BI"
            )
        else:
            warnings.append(
                f"filled protagonist_config.external_pov_insert_policy='{external_policy}'"
            )

    return warnings


def _repair_plot_roadmap(
    payload: dict[str, Any],
    *,
    treatment: Any | None,
    force_treatment_roadmap: bool = False,
) -> list[str]:
    if treatment is None:
        return []

    warnings: list[str] = []
    master = get_effective_bible_root(payload)
    current = master.get("plot_roadmap")
    current_warnings = validate_plot_roadmap_entries(current) if current is not None else ["plot_roadmap missing"]

    projected = build_plot_roadmap_from_treatment(treatment)
    projected_warnings = validate_plot_roadmap_entries(projected)
    if not projected:
        return warnings

    should_replace = force_treatment_roadmap
    if not should_replace:
        if not isinstance(current, list) or not current:
            should_replace = True
        elif current_warnings and len(projected_warnings) < len(current_warnings):
            should_replace = True

    if should_replace:
        master["plot_roadmap"] = projected
        if force_treatment_roadmap:
            warnings.append("force-replaced plot_roadmap with treatment-projected canonical roadmap")
        elif current_warnings:
            warnings.append("replaced weak plot_roadmap with treatment-projected canonical roadmap")
    return warnings


def canonicalize_bible_payload(
    bible: Any,
    *,
    treatment: Any | None = None,
    input_path: Path | None = None,
    force_treatment_roadmap: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    payload, warnings = normalize_bible_to_canonical_view(bible, treatment=treatment)
    warnings.extend(_repair_runtime_protagonist_contract(payload, input_path=input_path))
    warnings.extend(
        _repair_plot_roadmap(
            payload,
            treatment=treatment,
            force_treatment_roadmap=force_treatment_roadmap,
        )
    )
    master = payload.get("MasterBible")
    if isinstance(master, dict):
        if "plot_roadmap" in payload and isinstance(master.get("plot_roadmap"), list):
            payload.pop("plot_roadmap", None)
            warnings.append("removed root-level plot_roadmap sidecar from canonical BI copy")

        project_data = master.get("ProjectData")
        if isinstance(project_data, dict) and "protagonist_config" in project_data and isinstance(master.get("protagonist_config"), dict):
            project_data.pop("protagonist_config", None)
            warnings.append("removed ProjectData.protagonist_config sidecar from canonical BI copy")

    valid, errors, _warnings = validate_bible_canonical_structure(payload)
    if not valid:
        raise ValueError(f"canonical BI validation failed: {errors}")
    return payload, warnings


def derive_output_path(
    input_path: Path,
    *,
    in_place: bool,
    output_dir: Path | None,
    suffix: str,
) -> Path:
    if in_place:
        return input_path
    target_dir = output_dir or input_path.parent
    return target_dir / f"{input_path.stem}{suffix}{input_path.suffix}"


def rewrite_file(
    input_path: Path,
    *,
    treatment_path: Path | None,
    in_place: bool,
    output_dir: Path | None,
    suffix: str,
    force_treatment_roadmap: bool = False,
) -> dict[str, Any]:
    original = load_json(input_path)
    treatment = load_json(treatment_path) if treatment_path else None
    payload, warnings = canonicalize_bible_payload(
        original,
        treatment=treatment,
        input_path=input_path,
        force_treatment_roadmap=force_treatment_roadmap,
    )
    output_path = derive_output_path(input_path, in_place=in_place, output_dir=output_dir, suffix=suffix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "input": str(input_path),
        "output": str(output_path),
        "treatment": str(treatment_path) if treatment_path else None,
        "warnings": warnings,
        "in_place": in_place,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rewrite legacy BI JSON files into canonical BI payloads.")
    parser.add_argument("inputs", nargs="+", type=Path, help="Input BI JSON file(s)")
    parser.add_argument("--treatment", type=Path, help="Optional TR JSON used to project plot_roadmap")
    parser.add_argument("--in-place", action="store_true", help="Rewrite each file in place")
    parser.add_argument("--output-dir", type=Path, help="Destination directory for rewritten copies")
    parser.add_argument(
        "--suffix",
        default="_canonical_v1",
        help="Suffix for copied files when not using --in-place",
    )
    parser.add_argument(
        "--force-treatment-roadmap",
        action="store_true",
        help="Force replace BI plot_roadmap with the treatment-projected canonical roadmap",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    results = [
        rewrite_file(
            input_path=input_path,
            treatment_path=args.treatment,
            in_place=args.in_place,
            output_dir=args.output_dir,
            suffix=args.suffix,
            force_treatment_roadmap=args.force_treatment_roadmap,
        )
        for input_path in args.inputs
    ]

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        for result in results:
            warn_count = len(result["warnings"])
            print(
                f"[OK] {result['input']} -> {result['output']} "
                f"(warnings={warn_count}, treatment={result['treatment'] or 'none'})"
            )
            if result["warnings"]:
                print(f"       warnings: {' | '.join(result['warnings'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
