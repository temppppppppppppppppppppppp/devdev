from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ops_support import ROOT

TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

OLD_WORKSPACE_PATTERNS = (
    "C:/Users/wjjo/Desktop/글도비",
    r"C:\Users\wjjo\Desktop\글도비",
)

REFERENCE_BANK_RESIDUE_PATTERNS = (
    "narrative_ssot/10_reference_bank/source_corpora",
    r"narrative_ssot\10_reference_bank\source_corpora",
    "narrative_ssot/10_reference_bank/selection",
    r"narrative_ssot\10_reference_bank\selection",
    "narrative_ssot/10_reference_bank/idea_engine_db",
    r"narrative_ssot\10_reference_bank\idea_engine_db",
)

REQUIRED_PATHS = (
    "material_ssot/README.md",
    "material_ssot/00_governance/authority-map.md",
    "material_ssot/00_governance/legacy-map.md",
    "material_ssot/00_governance/stage-read-order.md",
    "material_ssot/00_governance/bootstrap-status.md",
    "material_ssot/00_governance/work-coverage-matrix.md",
    "material_ssot/00_governance/production-pair-operational-registry-v1.md",
    "material_ssot/00_governance/production-pair-operational-registry-v1.json",
    "material_ssot/00_governance/pre-new-pitch-operational-readiness-v1.md",
    "material_ssot/90_migration/pending-cuts.md",
    "material_ssot/10_research/source-map.md",
    "material_ssot/20_pitch/pitch-philosophy.md",
    "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/README.md",
    "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/collection_status.json",
    "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/README.md",
    "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/collection_status.json",
    "material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld/README.md",
    "material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld/ingest_status.json",
    "material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus/README.md",
    "material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus/manifest.json",
    "narrative_ssot/10_reference_bank/mirror_status.json",
    "scripts/build_platform_trend_corpus.py",
    "scripts/build_business_trend_slice.py",
    "scripts/build_youtube_channel_corpus.py",
    "scripts/export_youtube_idea_packets.py",
    "scripts/build_epub_sample_corpus.py",
    "scripts/sync_narrative_reference_bank.py",
    "scripts/pre_new_pitch_readiness_gate.py",
)

ACTIVE_PATH_SCOPE = (
    "material_ssot/README.md",
    "material_ssot/00_governance",
    "material_ssot/10_research/source-map.md",
    "material_ssot/10_research/00_registry",
    "material_ssot/10_research/10_reference_profiles",
    "material_ssot/10_research/20_fewshot_bank",
    "material_ssot/10_research/40_analysis/source_corpora",
    "material_ssot/10_research/50_corpus_curated",
    "material_ssot/20_pitch/pitch-philosophy.md",
    "material_ssot/20_pitch/canon",
    "material_ssot/30_stage0_preprocess",
    "material_ssot/40_phase0_design",
    "material_ssot/50_tr",
    "material_ssot/60_bi",
    "narrative_ssot/10_reference_bank",
    "docs/blockguide",
    "docs/narrative-router",
    "전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md",
    "전처리_ssot/docs/blockguide",
    "전처리_ssot/docs/30_ops/genre_pack_registry.md",
    "전처리_ssot/docs/30_ops/genre_decomposition_base_roadmap.md",
    "전처리_ssot/docs/30_ops/handoff_templates",
    "scripts/README.md",
    "scripts/build_platform_trend_corpus.py",
    "scripts/build_business_trend_slice.py",
    "scripts/build_youtube_channel_corpus.py",
    "scripts/export_youtube_idea_packets.py",
    "scripts/build_epub_sample_corpus.py",
    "scripts/sync_narrative_reference_bank.py",
    "scripts/pre_new_pitch_readiness_gate.py",
    "scripts/research_collectors",
)

ACTIVE_AUTHORITY_SCOPE = (
    "material_ssot/README.md",
    "material_ssot/00_governance",
    "material_ssot/10_research/00_registry",
    "material_ssot/10_research/10_reference_profiles",
    "material_ssot/10_research/20_fewshot_bank",
    "material_ssot/10_research/40_analysis/source_corpora",
    "material_ssot/10_research/50_corpus_curated",
    "material_ssot/20_pitch/pitch-philosophy.md",
    "material_ssot/20_pitch/canon",
    "material_ssot/30_stage0_preprocess",
    "material_ssot/40_phase0_design",
    "material_ssot/50_tr",
    "material_ssot/60_bi",
    "docs/blockguide",
    "docs/narrative-router",
    "전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md",
    "전처리_ssot/docs/blockguide",
    "전처리_ssot/docs/30_ops/genre_pack_registry.md",
    "전처리_ssot/docs/30_ops/genre_decomposition_base_roadmap.md",
    "전처리_ssot/docs/30_ops/handoff_templates",
    "scripts/README.md",
    "scripts/build_platform_trend_corpus.py",
    "scripts/build_business_trend_slice.py",
    "scripts/build_youtube_channel_corpus.py",
    "scripts/export_youtube_idea_packets.py",
    "scripts/build_epub_sample_corpus.py",
    "scripts/pre_new_pitch_readiness_gate.py",
    "scripts/research_collectors",
)


@dataclass(frozen=True)
class TextRule:
    relpath: str
    required: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    detail: str


TEXT_RULES = (
    TextRule(
        "material_ssot/README.md",
        required=(
            "`material_ssot` is the stage-axis SSOT for the material side order.",
            "- `narrative_ssot` = scaffold plus mirror/archive shell",
        ),
    ),
    TextRule(
        "material_ssot/00_governance/authority-map.md",
        required=(
            "| Stage axis | `material_ssot` | material-side stage SSOT |",
            "| Reference scaffold axis | `narrative_ssot` | scaffold plus cards mirror and archive residue shell |",
        ),
    ),
    TextRule(
        "material_ssot/00_governance/legacy-map.md",
        required=(
            "| `narrative_ssot/10_reference_bank` | `mirror` | cards mirror plus archive residue shell, not the primary authority |",
        ),
    ),
    TextRule(
        "material_ssot/00_governance/work-coverage-matrix.md",
        required=(
            "| `office_checkup_next_day` | `blockguide` | yes | yes | yes | yes | yes | yes | raw research path not yet pinned |",
            "| `wuxia_heavenly_physician` | `wuxguide` | yes | yes | yes | yes | yes | yes | raw research path not yet pinned |",
            "- bounded work-chain validation now runs through `python -X utf8 scripts/validate_material_ssot.py`",
            "- repo-level pre-new-pitch readiness now runs through `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`",
        ),
    ),
    TextRule(
        "material_ssot/00_governance/bootstrap-status.md",
        required=(
            "- repo-level pre-new-pitch readiness gate now exists at `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`",
            "- current live pair inventory and benchmark freshness now have a durable registry under `production-pair-operational-registry-v1.md`",
            "- all currently tracked schema-clean pairs now carry benchmark-fresh readings, including the previously unbenchmarked unslotted live pairs",
        ),
    ),
    TextRule(
        "material_ssot/00_governance/production-pair-operational-registry-v1.md",
        required=(
            "Scope: durable operational registry for current schema-clean production pairs",
            "| `manual_meridian_archivist` | `wuxguide` | `unslotted_live_pair` | `new_live_pair` | `pass` | `GREEN` | `current` | benchmark-fresh unslotted live pair; positive alias granted, still outside numbered-slot manifest |",
            "| `wuxia_heavenly_physician` | `wuxguide` | `numbered_live_pair` | `regenerated_pair` | `pass` | `GREENPLUS` | `current` | benchmark-fresh regenerated live pair; safe for current family baseline reading |",
        ),
    ),
    TextRule(
        "material_ssot/00_governance/pre-new-pitch-operational-readiness-v1.md",
        required=(
            "Scope: repo-level readiness gate before starting a fresh pitch wave",
            "- `python -X utf8 scripts/pre_new_pitch_readiness_gate.py`",
            "This means new pitch work is operationally unblocked, and pair-side fresh baseline claims can rely on the current registry so long as inventory-role distinctions and the `GREEN` vs `GREENPLUS` shelf split are respected.",
        ),
    ),
    TextRule(
        "material_ssot/20_pitch/pitch-philosophy.md",
        required=(
            "Status: active",
            "- default operating mode is `single`",
            "- the protagonist must want something concrete now",
            "Do not promote a pitch as canonical if any of these are missing or vague:",
        ),
    ),
    TextRule(
        "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/README.md",
        required=(
            "Status: active bounded corpus bundle",
            "- surface count: `61`",
            "- entry count: `2106`",
        ),
    ),
    TextRule(
        "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/README.md",
        required=(
            "Status: active bounded slice",
            "- entries: `116`",
            "- deduped works: `98`",
            "- this slice is machine-checked through `collection_status.json`",
        ),
    ),
    TextRule(
        "material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld/README.md",
        required=(
            "Status: active bounded corpus bundle",
            "- indexed video count: `2215`",
            "- caption saved count in the latest ingest snapshot: `30`",
        ),
    ),
    TextRule(
        "material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus/README.md",
        required=(
            "Status: active bounded sample corpus",
            "- sample_count: 10",
            "Fresh NAS rebuild verification for this sample corpus is intentionally deferred to the machine that can read the NAS path.",
        ),
    ),
    TextRule(
        "scripts/build_platform_trend_corpus.py",
        required=(
            '/ "material_ssot"',
            '/ "platform_trends"',
            '/ "kr_serial_platforms"',
        ),
        forbidden=("narrative_ssot/10_reference_bank/source_corpora",),
    ),
    TextRule(
        "scripts/build_business_trend_slice.py",
        required=(
            '/ "material_ssot"',
            '/ "platform_trends"',
            '/ "business_trend_slice"',
        ),
        forbidden=("narrative_ssot/10_reference_bank/source_corpora",),
    ),
    TextRule(
        "scripts/build_youtube_channel_corpus.py",
        required=(
            '/ "material_ssot"',
            '/ "youtube"',
            '/ "syukaworld"',
        ),
        forbidden=("narrative_ssot/10_reference_bank/source_corpora",),
    ),
    TextRule(
        "scripts/export_youtube_idea_packets.py",
        required=(
            '/ "material_ssot"',
            '/ "youtube"',
            '/ "syukaworld"',
        ),
        forbidden=("narrative_ssot/10_reference_bank/source_corpora",),
    ),
    TextRule(
        "scripts/build_epub_sample_corpus.py",
        required=(
            '/ "material_ssot"',
            '/ "medical_magical_surgeon_sample_corpus"',
        ),
    ),
    TextRule(
        "scripts/sync_narrative_reference_bank.py",
        required=(
            'SOURCE_ROOT = ROOT / "material_ssot" / "10_research" / "20_fewshot_bank"',
            'DEST_ROOT = ROOT / "narrative_ssot" / "10_reference_bank"',
            '"source_corpora, selection, and idea_engine_db are outside the live mirror scope"',
        ),
    ),
)

BOOTSTRAP_WORK_COVERAGE = (
    {
        "work_id": "office_checkup_next_day",
        "required_paths": (
            "material_ssot/10_research/30_work_materials/office_checkup_next_day/90_material_pack.json",
            "material_ssot/20_pitch/canon/office_checkup_next_day.md",
            "material_ssot/30_stage0_preprocess/work-index/office_checkup_next_day.md",
            "material_ssot/40_phase0_design/work-index/office_checkup_next_day.md",
            "material_ssot/50_tr/work-index/office_checkup_next_day.md",
            "material_ssot/60_bi/work-index/office_checkup_next_day.md",
            "treatments/phase0/office_checkup_next_day_phase0_design.json",
            "treatments/07_office_checkup_next_day_tr_block_070_draft.json",
            "bible/07_bi_office_checkup_next_day.json",
        ),
    },
    {
        "work_id": "wuxia_heavenly_physician",
        "required_paths": (
            "material_ssot/10_research/30_work_materials/wuxia_heavenly_physician/90_material_pack.json",
            "material_ssot/20_pitch/canon/wuxia_heavenly_physician.md",
            "material_ssot/30_stage0_preprocess/work-index/wuxia_heavenly_physician.md",
            "material_ssot/40_phase0_design/work-index/wuxia_heavenly_physician.md",
            "material_ssot/50_tr/work-index/wuxia_heavenly_physician.md",
            "material_ssot/60_bi/work-index/wuxia_heavenly_physician.md",
            "treatments/phase0/wuxia_heavenly_physician_phase0_design.json",
            "treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json",
            "bible/09_bi_wuxia_heavenly_physician.json",
        ),
    },
)

BOUND_CORPUS_METADATA = (
    {
        "relpath": "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/collection_status.json",
        "required_values": {
            "_schema_version": "platform_trend_collection_status.v1",
            "db_path": "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/platform_trends.sqlite3",
        },
        "positive_int_fields": ("surface_count", "entry_count"),
    },
    {
        "relpath": "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/collection_status.json",
        "required_values": {
            "_schema_version": "business_trend_slice_status.v1",
            "input_db": "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/platform_trends.sqlite3",
            "output_root": "material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice",
        },
        "positive_int_fields": ("entry_count", "work_count"),
    },
    {
        "relpath": "material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld/ingest_status.json",
        "required_values": {
            "_schema_version": "youtube_channel_ingest_status.v1",
            "channel_slug": "syukaworld",
        },
        "positive_int_fields": ("indexed_video_count",),
        "truthy_paths": (
            ("normalized_outputs", "db_path"),
            ("normalized_outputs", "query_jsonl_path"),
            ("normalized_outputs", "transcript_jsonl_path"),
        ),
        "truthy_flags": (("normalized_outputs", "fts_enabled"),),
    },
    {
        "relpath": "material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus/manifest.json",
        "required_values": {
            "sample_count": 10,
            "title_dir_name": "매지컬 써전(강산)",
        },
        "positive_int_fields": ("total_ssot_epubs", "sample_count"),
        "list_length_fields": (("samples", 10),),
    },
)


def _read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _iter_text_files(scope: tuple[str, ...]) -> list[Path]:
    files: dict[Path, None] = {}
    for relpath in scope:
        path = ROOT / relpath
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in TEXT_SUFFIXES:
                files[path] = None
            continue
        for candidate in path.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                files[candidate] = None
    return sorted(files)


def _scan_for_patterns(scope: tuple[str, ...], patterns: tuple[str, ...], kind: str) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_text_files(scope):
        try:
            text = _read_utf8(path)
        except UnicodeDecodeError as exc:
            findings.append(Finding("invalid_utf8", path.relative_to(ROOT).as_posix(), str(exc)))
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in patterns:
                if pattern in line:
                    findings.append(
                        Finding(
                            kind,
                            f"{path.relative_to(ROOT).as_posix()}:{line_no}",
                            line.strip()[:240],
                        )
                    )
    return findings


def _check_required_paths() -> list[Finding]:
    findings: list[Finding] = []
    for relpath in REQUIRED_PATHS:
        if not (ROOT / relpath).exists():
            findings.append(Finding("missing_path", relpath, "required material_ssot path is missing"))
    return findings


def _check_text_rules() -> list[Finding]:
    findings: list[Finding] = []
    for rule in TEXT_RULES:
        path = ROOT / rule.relpath
        if not path.exists():
            findings.append(Finding("missing_path", rule.relpath, "rule target is missing"))
            continue
        text = _read_utf8(path)
        for required in rule.required:
            if required not in text:
                findings.append(Finding("missing_text", rule.relpath, required))
        for forbidden in rule.forbidden:
            if forbidden in text:
                findings.append(Finding("forbidden_text", rule.relpath, forbidden))
    return findings


def _check_mirror_status() -> list[Finding]:
    findings: list[Finding] = []
    relpath = "narrative_ssot/10_reference_bank/mirror_status.json"
    data = json.loads(_read_utf8(ROOT / relpath))
    expected_values = {
        "authoritative_source": "material_ssot/10_research/20_fewshot_bank",
        "mirrored_manifest": "narrative_ssot/10_reference_bank/reference_card_manifest.json",
        "mirrored_cards_root": "narrative_ssot/10_reference_bank/cards",
    }
    for key, expected in expected_values.items():
        if data.get(key) != expected:
            findings.append(Finding("mirror_status_mismatch", relpath, f"{key} != {expected}"))
    notes = data.get("notes")
    if (
        not isinstance(notes, list)
        or "source_corpora, selection, and idea_engine_db are outside the live mirror scope" not in notes
    ):
        findings.append(
            Finding(
                "mirror_status_mismatch",
                relpath,
                "expected residue-scope note is missing",
            )
        )
    return findings


def _check_bootstrap_work_coverage() -> list[Finding]:
    findings: list[Finding] = []
    for spec in BOOTSTRAP_WORK_COVERAGE:
        work_id = spec["work_id"]
        for relpath in spec["required_paths"]:
            if not (ROOT / relpath).exists():
                findings.append(
                    Finding(
                        "bootstrap_work_missing_path",
                        relpath,
                        f"{work_id} expected path is missing",
                    )
                )
        for relpath in spec.get("forbidden_paths", ()):
            if (ROOT / relpath).exists():
                findings.append(
                    Finding(
                        "bootstrap_work_unexpected_path",
                        relpath,
                        f"{work_id} should still rely on the fallback path in the bounded slice",
                    )
                )
    return findings


def _resolve_nested(data: dict, path: tuple[str, ...]) -> object:
    current: object = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _check_bound_corpus_metadata() -> list[Finding]:
    findings: list[Finding] = []
    for spec in BOUND_CORPUS_METADATA:
        relpath = spec["relpath"]
        data = json.loads(_read_utf8(ROOT / relpath))
        for key, expected in spec.get("required_values", {}).items():
            if data.get(key) != expected:
                findings.append(
                    Finding(
                        "bound_corpus_value_mismatch",
                        relpath,
                        f"{key} != {expected}",
                    )
                )
        for key in spec.get("positive_int_fields", ()):
            value = data.get(key)
            if not isinstance(value, int) or value <= 0:
                findings.append(
                    Finding(
                        "bound_corpus_count_invalid",
                        relpath,
                        f"{key} should be a positive integer",
                    )
                )
        for path in spec.get("truthy_paths", ()):
            value = _resolve_nested(data, path)
            if not isinstance(value, str) or not value.strip():
                findings.append(
                    Finding(
                        "bound_corpus_path_missing",
                        relpath,
                        f"{'/'.join(path)} should be a non-empty string",
                    )
                )
        for path in spec.get("truthy_flags", ()):
            value = _resolve_nested(data, path)
            if value is not True:
                findings.append(
                    Finding(
                        "bound_corpus_flag_invalid",
                        relpath,
                        f"{'/'.join(path)} should be true",
                    )
                )
        for key, expected_len in spec.get("list_length_fields", ()):
            value = data.get(key)
            if not isinstance(value, list) or len(value) != expected_len:
                findings.append(
                    Finding(
                        "bound_corpus_list_length_invalid",
                        relpath,
                        f"{key} length should be {expected_len}",
                    )
                )
    return findings


def _format_finding(finding: Finding) -> str:
    return f"{finding.kind}: {finding.path}: {finding.detail}"


def main() -> int:
    findings: list[Finding] = []
    findings.extend(_check_required_paths())
    findings.extend(_check_text_rules())
    findings.extend(_check_mirror_status())
    findings.extend(_check_bootstrap_work_coverage())
    findings.extend(_check_bound_corpus_metadata())
    findings.extend(_scan_for_patterns(ACTIVE_PATH_SCOPE, OLD_WORKSPACE_PATTERNS, "old_workspace_path"))
    findings.extend(
        _scan_for_patterns(
            ACTIVE_AUTHORITY_SCOPE,
            REFERENCE_BANK_RESIDUE_PATTERNS,
            "reference_bank_residue_path",
        )
    )

    if findings:
        print("material_ssot validation failed:")
        for finding in findings:
            print(_format_finding(finding))
        return 1

    print("material_ssot validation passed.")
    print(f"checked required paths: {len(REQUIRED_PATHS)}")
    print(f"checked text rules: {len(TEXT_RULES)}")
    print(f"checked bootstrap work specs: {len(BOOTSTRAP_WORK_COVERAGE)}")
    print(f"checked bounded corpus metadata specs: {len(BOUND_CORPUS_METADATA)}")
    print(f"scanned active path scope files: {len(_iter_text_files(ACTIVE_PATH_SCOPE))}")
    print(f"scanned active authority scope files: {len(_iter_text_files(ACTIVE_AUTHORITY_SCOPE))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
