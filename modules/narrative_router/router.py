from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .contracts import NarrativeFamilyContract
from .families import get_builtin_families
from .families.base import NarrativeFamilyPlugin

ROOT = Path(__file__).resolve().parents[2]


def _normalize_token(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", "-")


def detect_stage(*, phase0_exists: bool, tr_exists: bool, bi_exists: bool) -> str:
    if bi_exists:
        return "audit_or_repair"
    if tr_exists:
        return "bi"
    if phase0_exists:
        return "production"
    return "planning"


def _get_nested_flag(payload: object, path: tuple[str, ...]) -> object | None:
    current = payload
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


@dataclass(frozen=True)
class NarrativeArtifactState:
    work_id: str
    preprocess_dir: str
    preprocess_files_present: dict[str, bool]
    preprocess_ready: bool
    manual_audit_pass: bool | None
    phase0_path: str
    phase0_exists: bool
    tr_path: str
    tr_exists: bool
    bi_path: str
    bi_exists: bool


def inspect_artifacts(*, work_id: str, contract: NarrativeFamilyContract) -> NarrativeArtifactState:
    preprocess_dir = ROOT / "treatments" / "preprocess" / work_id
    preprocess_files_present = {
        name: (preprocess_dir / name).exists()
        for name in contract.planning.required_preprocess_files
    }
    readiness_path = preprocess_dir / contract.planning.readiness_flag_file
    manual_audit_pass: bool | None = None
    if readiness_path.exists():
        try:
            payload = json.loads(readiness_path.read_text(encoding="utf-8-sig"))
            flag = _get_nested_flag(payload, contract.planning.readiness_flag_path)
            manual_audit_pass = bool(flag) if flag is not None else None
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            manual_audit_pass = None

    phase0_path = ROOT / contract.planning.phase0_output_pattern.format(work_id=work_id)
    tr_path = ROOT / f"treatments/{work_id}_tr_block_070_draft.json"
    bi_path = ROOT / f"bible/0_bi_{work_id}.json"
    preprocess_ready = all(preprocess_files_present.values()) and manual_audit_pass is True

    return NarrativeArtifactState(
        work_id=work_id,
        preprocess_dir=preprocess_dir.as_posix(),
        preprocess_files_present=preprocess_files_present,
        preprocess_ready=preprocess_ready,
        manual_audit_pass=manual_audit_pass,
        phase0_path=phase0_path.as_posix(),
        phase0_exists=phase0_path.exists(),
        tr_path=tr_path.as_posix(),
        tr_exists=tr_path.exists(),
        bi_path=bi_path.as_posix(),
        bi_exists=bi_path.exists(),
    )


@dataclass(frozen=True)
class NarrativeRoute:
    family: str
    display_name: str
    description: str
    integrated_order_path: str
    planning_path: str
    production_path: str
    bi_path: str
    extra_paths: list[str]
    contract: NarrativeFamilyContract
    stage: str | None = None
    artifact_state: NarrativeArtifactState | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _select_family(genre: str | None, family_hint: str | None) -> NarrativeFamilyPlugin:
    families = get_builtin_families()

    for family in families:
        if family.matches_family_hint(family_hint):
            return family

    for family in families:
        if family.matches_genre(genre):
            return family

    for family in families:
        if family.key == "blockguide":
            return family

    raise RuntimeError("No narrative family plugins are registered.")


def resolve_family_plugin(*, genre: str | None = None, family_hint: str | None = None) -> NarrativeFamilyPlugin:
    return _select_family(genre, family_hint)


def resolve_route(
    *,
    genre: str | None = None,
    family_hint: str | None = None,
    work_id: str | None = None,
    phase0_exists: bool = False,
    tr_exists: bool = False,
    bi_exists: bool = False,
) -> NarrativeRoute:
    family = _select_family(genre, family_hint)
    normalized_genre = _normalize_token(genre)
    extras: list[str] = []
    if family.key == "blockguide" and normalized_genre in {"alt-history", "alt_history", "대체역사"}:
        alt_history_path = family.extra_paths.get("alt-history")
        if alt_history_path:
            extras.append(alt_history_path)

    stage = None
    artifact_state = None
    if work_id:
        artifact_state = inspect_artifacts(work_id=work_id, contract=family.contract)
        stage = detect_stage(
            phase0_exists=artifact_state.phase0_exists,
            tr_exists=artifact_state.tr_exists,
            bi_exists=artifact_state.bi_exists,
        )
    elif phase0_exists or tr_exists or bi_exists:
        stage = detect_stage(phase0_exists=phase0_exists, tr_exists=tr_exists, bi_exists=bi_exists)

    return NarrativeRoute(
        family=family.key,
        display_name=family.display_name,
        description=family.description,
        integrated_order_path=family.integrated_order_path,
        planning_path=family.planning_path,
        production_path=family.production_path,
        bi_path=family.bi_path,
        extra_paths=extras,
        contract=family.contract,
        stage=stage,
        artifact_state=artifact_state,
    )
