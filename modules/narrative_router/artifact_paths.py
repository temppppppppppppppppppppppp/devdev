from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

LIVE_ARTIFACT_PREFIXES: dict[str, str] = {
    "투자물_골든_카나리아 테스트_canonical_v1": "01",
    "chaebol_allowance_zero": "02",
    "chaebol_ent_empire": "03",
    "defense_defect_engineer": "04",
    "failed_future_ceo_intern": "05",
    "gatekeeper_heir": "06",
    "office_checkup_next_day": "07",
    "pantech_cyworld_reborn": "08",
    "wuxia_heavenly_physician": "09",
}


def _root(root: Path | None = None) -> Path:
    return (root or ROOT).resolve()


def _dedupe(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    ordered: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(path)
    return tuple(ordered)


def _prefixed_matches(folder: Path, pattern: str) -> tuple[Path, ...]:
    return tuple(sorted(folder.glob(pattern), key=lambda path: path.name))


def _direct_subfolder_matches(folder: Path, pattern: str) -> tuple[Path, ...]:
    return tuple(sorted(folder.glob(f"*/{pattern}"), key=lambda path: path.as_posix()))


def canonical_phase0_path(work_id: str, *, root: Path | None = None) -> Path:
    return _root(root) / "treatments" / "phase0" / f"{work_id}_phase0_design.json"


def legacy_phase0_path(work_id: str, *, root: Path | None = None) -> Path:
    return _root(root) / "treatments" / f"{work_id}_phase0_design.json"


def phase0_candidate_paths(work_id: str, *, root: Path | None = None) -> tuple[Path, ...]:
    return (
        canonical_phase0_path(work_id, root=root),
        legacy_phase0_path(work_id, root=root),
    )


def resolve_phase0_path(work_id: str, *, root: Path | None = None) -> Path:
    for path in phase0_candidate_paths(work_id, root=root):
        if path.exists():
            return path
    return canonical_phase0_path(work_id, root=root)


def legacy_tr_path(work_id: str, *, root: Path | None = None) -> Path:
    return _root(root) / "treatments" / f"{work_id}_tr_block_070_draft.json"


def canonical_tr_path(work_id: str, *, root: Path | None = None) -> Path:
    prefix = LIVE_ARTIFACT_PREFIXES.get(work_id)
    if not prefix:
        return legacy_tr_path(work_id, root=root)
    return _root(root) / "treatments" / f"{prefix}_{work_id}_tr_block_070_draft.json"


def tr_candidate_paths(work_id: str, *, root: Path | None = None) -> tuple[Path, ...]:
    base = _root(root) / "treatments"
    return _dedupe(
        (
            canonical_tr_path(work_id, root=root),
            *_prefixed_matches(base, f"[0-9][0-9]_{work_id}_tr_block_070_draft.json"),
            legacy_tr_path(work_id, root=root),
        )
    )


def resolve_tr_path(work_id: str, *, root: Path | None = None) -> Path:
    for path in tr_candidate_paths(work_id, root=root):
        if path.exists():
            return path
    return canonical_tr_path(work_id, root=root)


def legacy_bi_path(work_id: str, *, root: Path | None = None) -> Path:
    return _root(root) / "bible" / f"0_bi_{work_id}.json"


def canonical_bi_path(work_id: str, *, root: Path | None = None) -> Path:
    prefix = LIVE_ARTIFACT_PREFIXES.get(work_id)
    if not prefix:
        return legacy_bi_path(work_id, root=root)
    return _root(root) / "bible" / f"{prefix}_bi_{work_id}.json"


def bi_candidate_paths(work_id: str, *, root: Path | None = None) -> tuple[Path, ...]:
    base = _root(root) / "bible"
    return _dedupe(
        (
            canonical_bi_path(work_id, root=root),
            *_prefixed_matches(base, f"[0-9][0-9]_bi_{work_id}.json"),
            legacy_bi_path(work_id, root=root),
        )
    )


def resolve_bi_path(work_id: str, *, root: Path | None = None) -> Path:
    for path in bi_candidate_paths(work_id, root=root):
        if path.exists():
            return path
    return canonical_bi_path(work_id, root=root)


def legacy_work_guard_path(work_id: str, *, root: Path | None = None) -> Path:
    return _root(root) / "work_guards" / f"{work_id}.yaml"


def canonical_work_guard_path(work_id: str, *, root: Path | None = None) -> Path:
    prefix = LIVE_ARTIFACT_PREFIXES.get(work_id)
    if not prefix:
        return legacy_work_guard_path(work_id, root=root)
    return _root(root) / "work_guards" / f"{prefix}_{work_id}.yaml"


def work_guard_candidate_paths(work_id: str, *, root: Path | None = None) -> tuple[Path, ...]:
    base = _root(root) / "work_guards"
    return _dedupe(
        (
            canonical_work_guard_path(work_id, root=root),
            *_prefixed_matches(base, f"[0-9][0-9]_{work_id}.yaml"),
            *_direct_subfolder_matches(base, f"[0-9][0-9]_{work_id}.yaml"),
            legacy_work_guard_path(work_id, root=root),
            *_direct_subfolder_matches(base, f"{work_id}.yaml"),
        )
    )


def resolve_work_guard_library_path(work_id: str, *, root: Path | None = None) -> Path:
    for path in work_guard_candidate_paths(work_id, root=root):
        if path.exists():
            return path
    return canonical_work_guard_path(work_id, root=root)
