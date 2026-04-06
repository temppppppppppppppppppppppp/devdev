#!/usr/bin/env python3
"""Batch harness for wuxia-family treatment block generation."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.stage0_handoff import canonicalize_treatment_payload
from modules.narrative_router.harness_digest import load_harness_digest, render_harness_digest_lines

BLOCK_REF_RE = re.compile(r"Block\s*(\d+)", re.IGNORECASE)
META_REF_RE = re.compile(
    r"(?<![A-Za-z])(?:" 
    r"B\d{1,3}(?:\s*[~→\-]\s*B?\d{1,3})*|"
    r"Block\s+\d{1,3}|블록\s*\d{1,3}|"
    r"ARC[-\s]?\d{1,3}|Arc\s+\d{1,3}|아크\s*\d{1,3}|"
    r"Phase\s+\d{1,3}|페이즈\s*\d{1,3}|"
    r"Stage\s+\d{1,3}|스테이지\s*\d{1,3}"
    r")(?:에서의|에서|와의|과의|와|과|보다|의|으로|로|은|는|이|가|를|을|에|도|만)?(?![A-Za-z])",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
KOREAN_RE = re.compile(r"[\uac00-\ud7a3]")
LATIN_RE = re.compile(r"[A-Za-z]")
CODE_TOKEN_RE = re.compile(r"(?:_\d+|type_\d+|plan_\d+|anomaly_\d+|protocol_\d+|_B\d+)", re.IGNORECASE)
BANNED_TEMPLATE_RES = (
    re.compile(r"Write Korean prose", re.IGNORECASE),
    re.compile(r"current realm before this block", re.IGNORECASE),
    re.compile(r"What weakness was used", re.IGNORECASE),
    re.compile(r"Payoff or echo of an earlier seed", re.IGNORECASE),
)
GENERIC_CALLBACK_RE = re.compile(r"(previous block|earlier seed|callback|payoff)", re.IGNORECASE)

MANDATORY_CONTENT_FIELDS = ("context", "event_villain", "solution", "reward")
MANDATORY_MARTIAL_FIELDS = (
    "realm_before",
    "realm_after",
    "internal_energy_before",
    "internal_energy_after",
    "faction_position",
    "jianghu_reputation",
    "enemy_pressure",
)
LOW_INTELLIGENCE_OPEN_FORESHADOW_LIMIT = 10
BLANKISH_VALUES = {"", "none", "null", "n/a", "na", "-", "unknown"}
LANGUAGE_PATHS = (
    "stakes",
    "content.context",
    "content.event_villain",
    "content.solution",
    "content.reward",
    "genre_ext.enemy_pressure",
    "genre_ext.martial_art_gain",
    "genre_ext.artifact_or_manual_gain",
    "genre_ext.jianghu_reputation",
    "genre_ext.success_pattern",
    "regression_ext.execution_doctrine",
)
CODE_PATHS = (
    "genre_ext.martial_art_gain",
    "genre_ext.artifact_or_manual_gain",
    "genre_ext.enemy_pressure",
    "genre_ext.opponent.weakness_exploited",
    "genre_ext.success_pattern",
    "regression_ext.execution_doctrine",
)
ALLOWED_META_PATH_PREFIXES = (
    "block_id",
    "arc_id",
    "arc_no",
    "phase_no",
    "stage_no",
    "foreshadow_targets",
    "callback_sources",
)
LABEL_META_PATH_PREFIXES = (
    "section_rotation",
    "genre_ext.section_rotation",
    "arc_section",
    "phase",
    "phase_label",
)


@dataclass
class Finding:
    severity: str
    rule: str
    block: str
    message: str
    fixed: bool = False


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def ensure_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if isinstance(value, dict):
        return value
    parent[key] = {}
    return parent[key]


def get_nested(obj: Any, path: str, default: Any = "") -> Any:
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
    return current if current is not None else default


def parse_block_no(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    match = re.search(r"(\d+)", as_text(value))
    return int(match.group(1)) if match else None


def format_block_id(number: int) -> str:
    return f"Block {number}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_canonical_treatment_payload(data: Any, *, schema: str = "tr.v1") -> Any:
    if not isinstance(data, list):
        return data

    blocks: list[dict[str, Any]] = []
    for index, block in enumerate(data, start=1):
        if not isinstance(block, dict):
            continue
        entry = copy.deepcopy(block)
        entry["block_no"] = parse_block_no(entry.get("block_no")) or parse_block_no(entry.get("block_id")) or index
        blocks.append(entry)

    return {
        "_schema": schema,
        "_total_blocks": len(blocks),
        "blocks": blocks,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload, _warnings = canonicalize_treatment_payload(data)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_blankish(value: Any) -> bool:
    return as_text(value).lower() in BLANKISH_VALUES


def parse_energy(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    text = as_text(value).replace("%", "").replace(",", "")
    if text.lstrip("+-").isdigit():
        return int(text)
    return None


def korean_ratio(text: Any) -> float:
    raw = as_text(text)
    if not raw:
        return 1.0
    korean = len(KOREAN_RE.findall(raw))
    latin = len(LATIN_RE.findall(raw))
    if korean == 0 and latin == 0:
        return 1.0
    return korean / max(korean + latin, 1)


def token_set(text: Any) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(as_text(text)) if len(token) >= 2}


def normalize_tail(text: Any, length: int = 20) -> str:
    raw = re.sub(r"\s+", " ", as_text(text))
    return raw[-length:] if len(raw) >= length else raw


def sentence_like_count(text: Any) -> int:
    raw = as_text(text)
    if not raw:
        return 0
    parts = [part for part in re.split(r"[.!?]+", raw) if part.strip()]
    return len(parts) if parts else 1


def bundle_size(block: dict[str, Any]) -> int:
    content = block.get("content", {}) if isinstance(block, dict) else {}
    return (
        len(as_text(content.get("context")))
        + len(as_text(content.get("event_villain")))
        + len(as_text(content.get("solution")))
        + len(as_text(content.get("reward")))
        + len(as_text(block.get("stakes")))
    )


def normalize_solution_stakes_signature(block: dict[str, Any]) -> str:
    content = block.get("content", {}) if isinstance(block, dict) else {}
    raw = f"{as_text(content.get('solution'))} {as_text(block.get('stakes'))}".strip()
    if not raw:
        return ""
    text = BLOCK_REF_RE.sub("[BLOCK]", raw)
    text = re.sub(r"\d+", "[N]", text)
    entity_names = [as_text(get_nested(block, "genre_ext.opponent.name"))]
    entity_names.extend(
        as_text(relation.get("target"))
        for relation in ensure_list(block.get("relationship_delta"))
        if isinstance(relation, dict)
    )
    for name in entity_names:
        if name:
            text = re.sub(re.escape(name), "[ENT]", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_text_signature(text: Any) -> str:
    raw = as_text(text)
    if not raw:
        return ""
    text = BLOCK_REF_RE.sub("[BLOCK]", raw)
    text = re.sub(r"\d+", "[N]", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def relation_target_signature(block: dict[str, Any]) -> tuple[str, ...]:
    targets = {
        as_text(relation.get("target"))
        for relation in ensure_list(block.get("relationship_delta"))
        if isinstance(relation, dict) and as_text(relation.get("target"))
    }
    return tuple(sorted(targets))


def relation_before_signature(relation: dict[str, Any]) -> str:
    return as_text(
        relation.get("anchor_before")
        or relation.get("continuity_anchor_before")
        or relation.get("state_before")
        or relation.get("before")
    )


def relation_after_signature(relation: dict[str, Any]) -> str:
    return as_text(
        relation.get("anchor_after")
        or relation.get("continuity_anchor_after")
        or relation.get("state_after")
        or relation.get("after")
    )


def is_allowed_meta_path(path: str) -> bool:
    for prefix in ALLOWED_META_PATH_PREFIXES:
        if path == prefix or path.startswith(f"{prefix}[") or path.startswith(f"{prefix}."):
            return True
    return False


def is_label_meta_path(path: str) -> bool:
    for prefix in LABEL_META_PATH_PREFIXES:
        if path == prefix or path.startswith(f"{prefix}[") or path.startswith(f"{prefix}.") or path.endswith(f".{prefix}"):
            return True
    return False


def collect_meta_leaks(value: Any, *, path: str = "") -> list[tuple[str, str]]:
    leaks: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            leaks.extend(collect_meta_leaks(item, path=child_path))
        return leaks
    if isinstance(value, list):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            leaks.extend(collect_meta_leaks(item, path=child_path))
        return leaks
    if isinstance(value, str) and not is_allowed_meta_path(path) and META_REF_RE.search(value):
        leaks.append((path, value.strip()))
    return leaks


def split_meta_leaks(leaks: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    diegetic: list[tuple[str, str]] = []
    label: list[tuple[str, str]] = []
    for path, raw in leaks:
        if is_label_meta_path(path):
            label.append((path, raw))
        else:
            diegetic.append((path, raw))
    return diegetic, label


def extract_numeric_refs(value: Any) -> list[int]:
    refs: list[int] = []
    for item in ensure_list(value):
        number = parse_block_no(item)
        if number is not None and number not in refs:
            refs.append(number)
    return refs


def extract_foreshadow_targets(block: dict[str, Any], seed: str = "") -> list[int]:
    targets = extract_numeric_refs(block.get("foreshadow_targets"))
    if targets:
        return targets
    return [int(match.group(1)) for match in BLOCK_REF_RE.finditer(seed)]


def extract_callback_sources(block: dict[str, Any], text: str = "") -> list[int]:
    sources = extract_numeric_refs(block.get("callback_sources"))
    if sources:
        return sources
    return [int(match.group(1)) for match in BLOCK_REF_RE.finditer(text)]


def compute_npc_continuity_mismatches(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state: dict[str, str] = {}
    issues: list[dict[str, Any]] = []
    for block in blocks:
        block_no = parse_block_no(block.get("block_id")) or 0
        for relation in ensure_list(block.get("relationship_delta")):
            if not isinstance(relation, dict):
                continue
            target = as_text(relation.get("target"))
            if not target:
                continue
            before_sig = relation_before_signature(relation)
            after_sig = relation_after_signature(relation)
            prev_sig = state.get(target, "")
            if prev_sig and before_sig and before_sig != prev_sig:
                issues.append(
                    {
                        "block_no": block_no,
                        "target": target,
                        "prev_after": prev_sig,
                        "current_before": before_sig,
                        "current_after": after_sig,
                    }
                )
            if after_sig:
                state[target] = after_sig
    return issues


def same_location_change_axes(prev_block: dict[str, Any], curr_block: dict[str, Any]) -> list[str]:
    prev_place = as_text(get_nested(prev_block, "location.place"))
    curr_place = as_text(get_nested(curr_block, "location.place"))
    if not prev_place or prev_place != curr_place:
        return []

    changed: list[str] = []

    if as_text(get_nested(prev_block, "emotional_beat.type")) != as_text(get_nested(curr_block, "emotional_beat.type")):
        changed.append("scene_function_proxy")

    prev_opp = (
        as_text(get_nested(prev_block, "genre_ext.opponent.name")),
        as_text(get_nested(prev_block, "genre_ext.opponent.weakness_exploited")),
    )
    curr_opp = (
        as_text(get_nested(curr_block, "genre_ext.opponent.name")),
        as_text(get_nested(curr_block, "genre_ext.opponent.weakness_exploited")),
    )
    if prev_opp != curr_opp:
        changed.append("opponent/front")

    if normalize_text_signature(get_nested(prev_block, "stakes")) != normalize_text_signature(get_nested(curr_block, "stakes")):
        changed.append("stakes")

    if relation_target_signature(prev_block) != relation_target_signature(curr_block):
        changed.append("evaluator_proxy")

    if as_text(get_nested(prev_block, "location.type")) != as_text(get_nested(curr_block, "location.type")):
        changed.append("sub_location")

    return changed


def callback_matches(seed: str, callbacks: list[str]) -> bool:
    seed_tokens = token_set(seed)
    if not seed_tokens:
        return False
    for callback in callbacks:
        if len(seed_tokens & token_set(callback)) >= 2:
            return True
    return False


def extract_blocks(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("treatments", "blocks", "plot_roadmap"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        master = payload.get("MasterBible")
        if isinstance(master, dict) and isinstance(master.get("plot_roadmap"), list):
            return master["plot_roadmap"]
    raise ValueError("Unsupported JSON shape. Expected list / treatments / plot_roadmap.")


def extract_project_meta(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    master = payload.get("MasterBible", payload)
    project = master.get("ProjectData", {})
    meta = project.get("MetaInfo", {})
    core = project.get("CoreIdentity", {})
    protagonist = as_text(core.get("protagonist"))
    if not protagonist:
        protagonist = as_text(master.get("MartialHUD", {}).get("Protagonist", {}).get("actual_truth", {}).get("name"))
    return {
        "title": as_text(meta.get("title")),
        "genre": as_text(meta.get("genre_archetype")),
        "logline": as_text(meta.get("logline")),
        "protagonist": protagonist,
    }


def normalize_candidate_slice(blocks: list[dict[str, Any]], start: int, batch_size: int) -> list[dict[str, Any]]:
    if not blocks:
        return []
    first_no = parse_block_no(blocks[0].get("block_id"))
    if len(blocks) == batch_size and first_no == start:
        return copy.deepcopy(blocks)
    if len(blocks) >= start + batch_size - 1:
        sliced = blocks[start - 1 : start - 1 + batch_size]
        if sliced and parse_block_no(sliced[0].get("block_id")) == start:
            return copy.deepcopy(sliced)
    return copy.deepcopy(blocks)


def build_npc_state(blocks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for block in blocks:
        block_no = parse_block_no(block.get("block_id")) or 0
        for relation in ensure_list(block.get("relationship_delta")):
            if not isinstance(relation, dict):
                continue
            target = as_text(relation.get("target"))
            if not target:
                continue
            state[target] = {"after": relation_after_signature(relation), "last_block": block_no}
    return state


def build_due_foreshadows(blocks: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    due: dict[int, list[dict[str, Any]]] = {}
    for block in blocks:
        plant_no = parse_block_no(block.get("block_id")) or 0
        for text in ensure_list(block.get("foreshadow")):
            seed = as_text(text)
            if not seed:
                continue
            for target in extract_foreshadow_targets(block, seed):
                due.setdefault(target, []).append({"plant_block": plant_no, "text": seed})
    return due


def build_open_foreshadow_ledger(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    for block in blocks:
        plant_no = parse_block_no(block.get("block_id")) or 0
        for text in ensure_list(block.get("foreshadow")):
            seed = as_text(text)
            if not seed:
                continue
            targets = extract_foreshadow_targets(block, seed)
            callbacks: list[str] = []
            resolved = False
            if targets:
                for target in targets:
                    if 1 <= target <= len(blocks):
                        target_block = blocks[target - 1]
                        callbacks.extend(as_text(item) for item in ensure_list(target_block.get("callback")))
                        callback_sources = extract_callback_sources(target_block)
                        if plant_no in callback_sources:
                            resolved = True
            if not targets and not resolved:
                for later_block in blocks[plant_no:]:
                    callbacks.extend(as_text(item) for item in ensure_list(later_block.get("callback")))
            if not resolved and callbacks:
                resolved = callback_matches(seed, callbacks)
            if not resolved:
                overdue = bool(targets) and any(target <= len(blocks) for target in targets)
                ledger.append(
                    {
                        "text": seed,
                        "plant_block": plant_no,
                        "target_block": ",".join(str(item) for item in targets) if targets else "-",
                        "status": "OVERDUE" if overdue else "OPEN",
                    }
                )
    return ledger


def count_unresolved_foreshadows(blocks: list[dict[str, Any]]) -> int:
    return len(build_open_foreshadow_ledger(blocks))


def has_recognition_signal(block: dict[str, Any]) -> bool:
    regression = block.get("regression_ext", {}) if isinstance(block.get("regression_ext"), dict) else {}
    regression_hint = regression.get("regression_hint", {}) if isinstance(regression.get("regression_hint"), dict) else {}
    if not is_blankish(regression_hint.get("recognition_from")):
        return True
    candidates = [get_nested(block, "genre_ext.jianghu_reputation"), get_nested(block, "content.reward")]
    candidates.extend(ensure_list(block.get("callback")))
    candidates.extend(
        relation.get("after", "")
        for relation in ensure_list(block.get("relationship_delta"))
        if isinstance(relation, dict)
    )
    return any("title" in as_text(item).lower() or "reputation" in as_text(item).lower() for item in candidates)


def truncate(text: Any, limit: int = 88) -> str:
    raw = as_text(text)
    if len(raw) <= limit:
        return raw
    return f"{raw[: limit - 3]}..."


def recent_block_summary(blocks: list[dict[str, Any]], limit: int = 3) -> str:
    if not blocks:
        return "- No previous blocks yet."
    lines: list[str] = []
    for block in blocks[-limit:]:
        lines.append(
            f"- {block.get('block_id')}: {truncate(block.get('title'), 36)} | "
            f"realm {as_text(get_nested(block, 'genre_ext.realm_before'))} -> {as_text(get_nested(block, 'genre_ext.realm_after'))} | "
            f"energy {as_text(get_nested(block, 'genre_ext.internal_energy_before'))} -> {as_text(get_nested(block, 'genre_ext.internal_energy_after'))} | "
            f"opponent {as_text(get_nested(block, 'genre_ext.opponent.name'))}"
        )
    return "\n".join(lines)


def npc_tracker_table(blocks: list[dict[str, Any]]) -> str:
    state = build_npc_state(blocks)
    if not state:
        return "| NPC | Last block | Current relation |\n|---|---:|---|\n| (none) | - | clean start |"
    rows = ["| NPC | Last block | Current relation |", "|---|---:|---|"]
    for idx, (name, data) in enumerate(state.items(), start=1):
        if idx > 12:
            break
        rows.append(f"| {name} | {data.get('last_block', '?')} | {truncate(data['after'], 64)} |")
    return "\n".join(rows)


def foreshadow_table(blocks: list[dict[str, Any]]) -> str:
    ledger = build_open_foreshadow_ledger(blocks)
    if not ledger:
        return "| # | Status | Seed | Plant | Target |\n|---|---|---|---:|---:|\n| (none) | clean | clean | - | - |"
    rows = ["| # | Status | Seed | Plant | Target |", "|---|---|---|---:|---:|"]
    for idx, item in enumerate(ledger[:LOW_INTELLIGENCE_OPEN_FORESHADOW_LIMIT], start=1):
        rows.append(
            f"| {idx} | {item.get('status', 'OPEN')} | {truncate(item['text'], 42)} | {item['plant_block']} | {item['target_block']} |"
        )
    return "\n".join(rows)


def batch_target_lines(roadmap_blocks: list[dict[str, Any]] | None, start: int, batch_size: int) -> str:
    lines: list[str] = []
    for number in range(start, start + batch_size):
        title = f"Block {number}"
        extras: list[str] = []
        if roadmap_blocks and len(roadmap_blocks) >= number:
            source = roadmap_blocks[number - 1]
            title = as_text(source.get("title")) or title
            opponent = as_text(get_nested(source, "genre_ext.opponent.name"))
            target_realm = as_text(get_nested(source, "genre_ext.realm_after"))
            reward = as_text(get_nested(source, "content.reward"))
            if opponent:
                extras.append(f"opponent={opponent}")
            if target_realm:
                extras.append(f"target_realm={target_realm}")
            if reward:
                extras.append(f"reward={truncate(reward, 28)}")
        extra_text = f" ({', '.join(extras)})" if extras else ""
        lines.append(f"- Block {number}: {title}{extra_text}")
    return "\n".join(lines)


def compute_treatment_metrics(blocks: Any) -> dict[str, Any]:
    blocks = extract_blocks(blocks)
    if not blocks:
        return {
            "block_count": 0,
            "production_density_gate": False,
            "avg_bundle_chars": 0.0,
            "avg_solution_chars": 0.0,
            "foreshadow_total": 0,
            "callback_total": 0,
            "callback_ratio": 0.0,
            "unresolved_foreshadow_count": 0,
            "opponent_unique": 0,
            "weakness_unique": 0,
            "top_opponent_name": "",
            "top_opponent_repetition": 0,
            "top_opponent_share": 0.0,
            "top_weakness_repetition": 0,
            "solution_tail20_top_repetition": 0,
            "one_sentence_like_solution_blocks": 0,
            "faction_position_missing": 0,
            "jianghu_reputation_missing": 0,
            "enemy_pressure_missing": 0,
            "critical_thin_blocks": [],
            "thin_blocks": [],
            "short_stakes_blocks": [],
            "same_location_clone_blocks": [],
            "same_location_clone_count": 0,
            "diegetic_meta_ref_examples": [],
            "diegetic_meta_ref_count": 0,
            "label_meta_ref_examples": [],
            "label_meta_ref_count": 0,
            "diegetic_block_ref_examples": [],
            "diegetic_block_ref_count": 0,
            "npc_continuity_mismatch_examples": [],
            "npc_continuity_mismatch_count": 0,
            "martial_progress_blocks": [],
            "no_progress_blocks": [],
            "recognition_signal_blocks": 0,
            "max_recognition_gap_streak": 0,
            "late_blank_opponent_blocks": [],
            "endgame_low_stakes_blocks": [],
            "normalized_solution_stakes_repeat_max": 0,
            "is_regressor_treatment": False,
            "hard_gate_checks": {},
            "hard_gate_failures": [],
            "window_10_opponent_unique_counts": [],
            "pattern_feedback_snapshot": {
                "top_opponents": [],
                "top_weaknesses": [],
                "solution_pattern_warnings": [],
                "structural_gate_failures": [],
                "same_location_clone_blocks": [],
                "diegetic_meta_ref_examples": [],
                "label_meta_ref_examples": [],
                "diegetic_block_ref_examples": [],
                "npc_continuity_mismatch_examples": [],
            },
        }

    npc_continuity_mismatches = compute_npc_continuity_mismatches(blocks)
    diegetic_meta_ref_examples: list[dict[str, Any]] = []
    diegetic_meta_ref_count = 0
    label_meta_ref_examples: list[dict[str, Any]] = []
    label_meta_ref_count = 0
    opponent_names: list[str] = []
    weaknesses: list[str] = []
    solution_tails: list[str] = []
    normalized_solution_stakes: list[str] = []
    bundle_sizes: list[int] = []
    solution_sizes: list[int] = []
    one_sentence_like = 0
    faction_position_missing = 0
    jianghu_reputation_missing = 0
    enemy_pressure_missing = 0
    critical_thin_blocks: list[int] = []
    thin_blocks: list[int] = []
    short_stakes_blocks: list[int] = []
    martial_progress_blocks: list[int] = []
    no_progress_blocks: list[int] = []
    recognition_signal_blocks = 0
    recognition_gap_streak = 0
    max_recognition_gap_streak = 0
    is_regressor_treatment = False
    foreshadow_total = 0
    callback_total = 0
    same_location_clone_blocks: list[dict[str, Any]] = []
    prev_block_for_location: dict[str, Any] | None = None

    for block_no, block in enumerate(blocks, start=1):
        meta_leaks = collect_meta_leaks(block)
        diegetic_meta_leaks, label_meta_leaks = split_meta_leaks(meta_leaks)
        diegetic_meta_ref_count += len(diegetic_meta_leaks)
        label_meta_ref_count += len(label_meta_leaks)
        for path, raw in diegetic_meta_leaks[: max(0, 10 - len(diegetic_meta_ref_examples))]:
            diegetic_meta_ref_examples.append({"block_no": block_no, "path": path, "text": raw})
        for path, raw in label_meta_leaks[: max(0, 10 - len(label_meta_ref_examples))]:
            label_meta_ref_examples.append({"block_no": block_no, "path": path, "text": raw})

        genre = (block.get("martial_ext") or block.get("genre_ext") or {}) if isinstance(block, dict) else {}
        content = block.get("content", {}) if isinstance(block, dict) else {}
        opponent = genre.get("opponent", {}) if isinstance(genre.get("opponent", {}), dict) else {}
        regression = block.get("regression_ext", {}) if isinstance(block.get("regression_ext"), dict) else {}
        is_regressor = bool(regression.get("is_regressor")) or as_text(regression.get("regression_type")).lower() not in {"", "none"}
        if is_regressor:
            is_regressor_treatment = True

        opponent_names.append(as_text(opponent.get("name")))
        weaknesses.append(as_text(opponent.get("weakness_exploited")))

        solution = as_text(content.get("solution"))
        solution_sizes.append(len(solution))
        solution_tails.append(normalize_tail(solution, 20))
        normalized_solution_stakes.append(normalize_solution_stakes_signature(block))
        if sentence_like_count(solution) <= 1:
            one_sentence_like += 1

        current_bundle = bundle_size(block)
        bundle_sizes.append(current_bundle)
        if current_bundle < 300:
            critical_thin_blocks.append(block_no)
        elif current_bundle < 350:
            thin_blocks.append(block_no)

        if len(as_text(block.get("stakes"))) < 35:
            short_stakes_blocks.append(block_no)
        # Support both blockguide (faction_position) and wuxguide (faction_status) field names
        faction_val = genre.get("faction_position") or genre.get("faction_status")
        if isinstance(faction_val, dict):
            faction_val = faction_val.get("affiliation") or faction_val.get("rank")
        if is_blankish(faction_val):
            faction_position_missing += 1
        rep_val = genre.get("jianghu_reputation")
        if isinstance(rep_val, dict):
            rep_val = rep_val.get("after") or rep_val.get("before")
        if is_blankish(rep_val):
            jianghu_reputation_missing += 1
        # enemy_pressure: blockguide uses direct field; wuxguide infers from opponent presence
        enemy_pressure_val = genre.get("enemy_pressure")
        if enemy_pressure_val is None:
            # Wuxia fallback: opponent dict with a non-blank name implies active pressure
            opp = genre.get("opponent")
            if isinstance(opp, dict):
                opp_name = as_text(opp.get("name"))
                enemy_pressure_val = "active" if (opp_name and opp_name.lower() not in {"없음", "n/a", "none", ""}) else ""
        if is_blankish(enemy_pressure_val):
            enemy_pressure_missing += 1

        foreshadow_total += len([text for text in ensure_list(block.get("foreshadow")) if as_text(text)])
        callback_total += len([text for text in ensure_list(block.get("callback")) if as_text(text)])

        if prev_block_for_location is not None:
            changed_axes = same_location_change_axes(prev_block_for_location, block)
            prev_place = as_text(get_nested(prev_block_for_location, "location.place"))
            curr_place = as_text(get_nested(block, "location.place"))
            if prev_place and prev_place == curr_place and len(changed_axes) < 2:
                same_location_clone_blocks.append(
                    {
                        "block_no": block_no,
                        "location": curr_place,
                        "changed_axes": changed_axes,
                    }
                )

        realm_before = as_text(genre.get("realm_before"))
        realm_after = as_text(genre.get("realm_after"))
        energy_before = parse_energy(genre.get("internal_energy_before"))
        energy_after = parse_energy(genre.get("internal_energy_after"))
        artifact_gain = as_text(genre.get("artifact_or_manual_gain"))
        # Support both blockguide (martial_art_gain) and wuxguide (martial_arts_acquired) field names
        martial_art_gain_raw = genre.get("martial_art_gain") or genre.get("martial_arts_acquired")
        has_martial_art_gain = False
        if isinstance(martial_art_gain_raw, list):
            has_martial_art_gain = any(not is_blankish(item) for item in martial_art_gain_raw)
        else:
            has_martial_art_gain = not is_blankish(martial_art_gain_raw)
        martial_progress = (
            (realm_before and realm_after and realm_before != realm_after)
            or (energy_before is not None and energy_after is not None and energy_after > energy_before)
            or has_martial_art_gain
            or (artifact_gain and not is_blankish(artifact_gain) and artifact_gain.lower() not in {"none", "no", "none."})
        )
        if martial_progress:
            martial_progress_blocks.append(block_no)
        else:
            no_progress_blocks.append(block_no)

        if is_regressor:
            if has_recognition_signal(block):
                recognition_signal_blocks += 1
                recognition_gap_streak = 0
            else:
                recognition_gap_streak += 1
                max_recognition_gap_streak = max(max_recognition_gap_streak, recognition_gap_streak)

        prev_block_for_location = block

    opponent_counter = Counter(name for name in opponent_names if name and not is_blankish(name))
    weakness_counter = Counter(value for value in weaknesses if value and not is_blankish(value))
    solution_tail_counter = Counter(value for value in solution_tails if value)

    top_opponent_name, top_opponent_repetition = opponent_counter.most_common(1)[0] if opponent_counter else ("", 0)
    top_weakness_repetition = weakness_counter.most_common(1)[0][1] if weakness_counter else 0
    solution_tail20_top_repetition = solution_tail_counter.most_common(1)[0][1] if solution_tail_counter else 0

    window_10 = []
    for index in range(0, len(opponent_names), 10):
        chunk = [name for name in opponent_names[index : index + 10] if name and not is_blankish(name)]
        window_10.append(len(set(chunk)))

    callback_ratio = round(callback_total / max(foreshadow_total, 1), 2)
    unresolved_foreshadow_count = count_unresolved_foreshadows(blocks)
    late_blank_opponent_blocks = [
        idx
        for idx in range(max(1, len(blocks) - 9), len(blocks) + 1)
        if is_blankish(opponent_names[idx - 1])
    ]
    endgame_low_stakes_blocks = [
        idx for idx in range(max(1, len(blocks) - 4), len(blocks) + 1) if idx in short_stakes_blocks
    ]

    normalized_solution_stakes_repeat_max = 0
    for index in range(0, len(normalized_solution_stakes), 10):
        chunk = [value for value in normalized_solution_stakes[index : index + 10] if value]
        if chunk:
            normalized_solution_stakes_repeat_max = max(
                normalized_solution_stakes_repeat_max,
                Counter(chunk).most_common(1)[0][1],
            )

    thin_ratio_limit = len(blocks) * 0.10
    required_progress_blocks = max(1, (len(blocks) * 3 + 4) // 5)
    required_recognition_blocks = max(4, (len(blocks) + 9) // 10) if is_regressor_treatment else 0
    hard_gate_checks = {
        "critical_thin_blocks_zero": len(critical_thin_blocks) == 0,
        "thin_blocks_ratio_ok": len(thin_blocks) <= thin_ratio_limit,
        "late_thin_blocks_zero": not any(block_no > len(blocks) - 10 for block_no in thin_blocks),
        "short_stakes_blocks_total_ok": len(short_stakes_blocks) <= 2,
        "endgame_low_stakes_zero": len(endgame_low_stakes_blocks) == 0,
        "callback_ratio_ok": callback_ratio >= 0.55,
        "unresolved_foreshadow_count_ok": unresolved_foreshadow_count <= (foreshadow_total * 0.40),
        "faction_position_present": faction_position_missing == 0,
        "jianghu_reputation_present": jianghu_reputation_missing == 0,
        "enemy_pressure_present": enemy_pressure_missing == 0,
        "late_blank_opponent_ok": len(late_blank_opponent_blocks) <= 1,
        "normalized_solution_stakes_repeat_ok": normalized_solution_stakes_repeat_max <= 4,
        "martial_progress_ratio_ok": len(martial_progress_blocks) >= required_progress_blocks,
        "diegetic_meta_ref_zero": diegetic_meta_ref_count == 0,
        "label_meta_ref_zero": label_meta_ref_count == 0,
        "diegetic_block_ref_zero": diegetic_meta_ref_count == 0,
    }
    if is_regressor_treatment:
        hard_gate_checks["regressor_recognition_count_ok"] = recognition_signal_blocks >= required_recognition_blocks
        hard_gate_checks["regressor_recognition_gap_ok"] = max_recognition_gap_streak <= 15

    pattern_warnings: list[str] = []
    if solution_tail20_top_repetition >= 50:
        pattern_warnings.append(f"solution tail-20 repeats {solution_tail20_top_repetition} times")
    if top_opponent_repetition / max(len(blocks), 1) > 0.30:
        pattern_warnings.append(
            f"top opponent {top_opponent_name} share is {round(top_opponent_repetition / len(blocks) * 100, 1)}%"
        )
    if same_location_clone_blocks:
        pattern_warnings.append(f"same-location under-differentiated reuse {len(same_location_clone_blocks)}회")
    if diegetic_meta_ref_count:
        pattern_warnings.append(f"diegetic meta leak {diegetic_meta_ref_count}건")
    if label_meta_ref_count:
        pattern_warnings.append(f"label meta leak {label_meta_ref_count}건")
    if npc_continuity_mismatches:
        pattern_warnings.append(f"npc continuity mismatch {len(npc_continuity_mismatches)}건")
    structural_gate_failures = [key for key, ok in hard_gate_checks.items() if not ok]

    return {
        "block_count": len(blocks),
        "production_density_gate": all(hard_gate_checks.values()),
        "avg_bundle_chars": round(sum(bundle_sizes) / len(bundle_sizes), 2),
        "avg_solution_chars": round(sum(solution_sizes) / len(solution_sizes), 2),
        "foreshadow_total": foreshadow_total,
        "callback_total": callback_total,
        "callback_ratio": callback_ratio,
        "unresolved_foreshadow_count": unresolved_foreshadow_count,
        "opponent_unique": len(set(name for name in opponent_names if name and not is_blankish(name))),
        "weakness_unique": len(set(value for value in weaknesses if value and not is_blankish(value))),
        "top_opponent_name": top_opponent_name,
        "top_opponent_repetition": top_opponent_repetition,
        "top_opponent_share": round(top_opponent_repetition / len(blocks) * 100, 1) if blocks else 0.0,
        "top_weakness_repetition": top_weakness_repetition,
        "solution_tail20_top_repetition": solution_tail20_top_repetition,
        "one_sentence_like_solution_blocks": one_sentence_like,
        "faction_position_missing": faction_position_missing,
        "jianghu_reputation_missing": jianghu_reputation_missing,
        "enemy_pressure_missing": enemy_pressure_missing,
        "critical_thin_blocks": critical_thin_blocks,
        "thin_blocks": thin_blocks,
        "short_stakes_blocks": short_stakes_blocks,
        "same_location_clone_blocks": same_location_clone_blocks,
        "same_location_clone_count": len(same_location_clone_blocks),
        "diegetic_meta_ref_examples": diegetic_meta_ref_examples,
        "diegetic_meta_ref_count": diegetic_meta_ref_count,
        "label_meta_ref_examples": label_meta_ref_examples,
        "label_meta_ref_count": label_meta_ref_count,
        "diegetic_block_ref_examples": diegetic_meta_ref_examples,
        "diegetic_block_ref_count": diegetic_meta_ref_count,
        "npc_continuity_mismatch_examples": npc_continuity_mismatches[:10],
        "npc_continuity_mismatch_count": len(npc_continuity_mismatches),
        "martial_progress_blocks": martial_progress_blocks,
        "no_progress_blocks": no_progress_blocks,
        "recognition_signal_blocks": recognition_signal_blocks,
        "max_recognition_gap_streak": max_recognition_gap_streak,
        "late_blank_opponent_blocks": late_blank_opponent_blocks,
        "endgame_low_stakes_blocks": endgame_low_stakes_blocks,
        "normalized_solution_stakes_repeat_max": normalized_solution_stakes_repeat_max,
        "is_regressor_treatment": is_regressor_treatment,
        "hard_gate_checks": hard_gate_checks,
        "hard_gate_failures": structural_gate_failures,
        "window_10_opponent_unique_counts": window_10,
        "pattern_feedback_snapshot": {
            "top_opponents": opponent_counter.most_common(3),
            "top_weaknesses": weakness_counter.most_common(3),
            "solution_pattern_warnings": pattern_warnings,
            "structural_gate_failures": structural_gate_failures,
            "same_location_clone_blocks": same_location_clone_blocks,
            "diegetic_meta_ref_examples": diegetic_meta_ref_examples,
            "label_meta_ref_examples": label_meta_ref_examples,
            "diegetic_block_ref_examples": diegetic_meta_ref_examples,
            "npc_continuity_mismatch_examples": npc_continuity_mismatches[:10],
        },
    }


def prompt_json_skeleton(start: int, batch_size: int, protagonist: str) -> str:
    block = {
        "block_id": format_block_id(start),
        "title": "Block title",
        "content": {
            "context": "Write Korean prose. Establish the situation and martial pressure.",
            "event_villain": "Write Korean prose. Describe the opponent move or external threat.",
            "solution": "Write Korean prose. Show the protagonist response and martial logic.",
            "reward": "Write Korean prose. Show the gain, shift, or new opening.",
        },
        "stakes": "What is lost if this block fails",
        "power_shift": {
            "protagonist": "How the protagonist status changes",
            "antagonist": "How the opposing side status changes",
        },
        "relationship_delta": [
            {
                "target": "NPC name",
                "anchor_before": "previous state anchor",
                "before": "previous relation",
                "anchor_after": "new state anchor",
                "after": "new relation"
            }
        ],
        "foreshadow": ["Natural-language seed for a later payoff"],
        "foreshadow_targets": [start + 2],
        "callback": ["Natural-language payoff or echo of an earlier seed"],
        "callback_sources": [max(1, start - 1)],
        "emotional_beat": {"type": "resolve", "intensity": 7},
        "tension_level": 8,
        "pov_character": protagonist or "Protagonist",
        "location": {"place": "Martial location", "type": "sect, inn, market, training ground"},
        "time_span": {"duration": "2 days", "in_story_time": "spring month 1"},
        "genre_ext": {
            "realm_before": "current realm before this block",
            "realm_after": "current realm after this block",
            "internal_energy_before": 40,
            "internal_energy_after": 46,
            "martial_art_gain": "new move, insight, or refinement",
            "artifact_or_manual_gain": "manual, token, herb, weapon, clue, or none",
            "faction_position": "current faction standing",
            "jianghu_reputation": "current jianghu reputation",
            "enemy_pressure": "how danger escalates",
            "opponent": {
                "name": "Opponent name",
                "sect_or_faction": "Opponent faction",
                "weakness_exploited": "What weakness was used",
            },
            "success_pattern": "How this block delivers wuxia satisfaction",
        },
        "regression_ext": {
            "is_regressor": False,
            "regression_type": "none",
            "execution_doctrine": "The current operating doctrine of the protagonist",
        },
    }
    sample = []
    for offset in range(batch_size):
        current = copy.deepcopy(block)
        current["block_id"] = format_block_id(start + offset)
        sample.append(current)
    return json.dumps(sample, ensure_ascii=False, indent=2)


def build_prompt(
    draft_blocks: list[dict[str, Any]],
    roadmap_blocks: list[dict[str, Any]] | None,
    meta: dict[str, Any],
    start: int,
    batch_size: int,
    mode: str,
) -> str:
    completed = draft_blocks[: start - 1]
    protagonist = as_text(meta.get("protagonist"))
    digest_lines = render_harness_digest_lines(load_harness_digest(family="wuxguide", stage="tr_batch"))
    if mode == "flash":
        predeclare = [
            "1. Cite the previous realm_after and internal_energy_after before the JSON.",
            "2. State which wuxia axis each block advances.",
            "3. After JSON, output a short continuity diff.",
        ]
        batch_rule = "Return predeclare, JSON array, and a short continuity diff only."
    elif mode == "pro":
        predeclare = [
            "1. Summarize continuity anchors and open foreshadow debt before the JSON.",
            "2. After JSON, output continuity diff, NPC tracker delta, and foreshadow debt update.",
            "3. Flag any block that is intentionally political or recovery-heavy instead of realm growth.",
        ]
        batch_rule = "Return predeclare, JSON array, continuity diff, NPC tracker delta, and foreshadow debt update."
    else:
        predeclare = [
            "1. Explain the batch cadence and why the block order is correct.",
            "2. After JSON, audit title sequence, martial progress, and callback debt in separate bullets.",
            "3. End with one operator note about the riskiest continuity seam.",
        ]
        batch_rule = "Return predeclare, JSON array, then all requested operator review artifacts."
    lines = [
        "# Wuxia TR Batch Harness Prompt",
        "",
        "Write Korean narrative prose inside all story fields.",
        "Keep the outer JSON shape exactly as requested.",
        "",
        "## Project Context",
        f"- title: {as_text(meta.get('title')) or '(unknown)'}",
        f"- genre: {as_text(meta.get('genre')) or '(unknown)'}",
        f"- protagonist: {protagonist or '(unknown)'}",
        f"- logline: {as_text(meta.get('logline')) or '(unknown)'}",
        "",
        "## Current Batch",
        f"- start block: {start}",
        f"- end block: {start + batch_size - 1}",
        f"- mode: {mode}",
        "",
        "## Batch Targets",
        batch_target_lines(roadmap_blocks, start, batch_size),
        "",
        "## Recent Blocks",
        recent_block_summary(completed),
        "",
        "## NPC Tracker",
        npc_tracker_table(completed),
        "",
        "## Open Foreshadows",
        foreshadow_table(completed),
        "",
        "## NPC Continuity Rule",
        "- For recurring NPCs, write `anchor_before` / `anchor_after` inside relationship_delta.",
        "- Natural-language `before` / `after` may vary, but anchors must chain from the previous anchor_after.",
        "- If anchors are omitted, the harness treats the prose itself as continuity truth.",
        "",
        *digest_lines,
        "",
        "## Rules",
        "1. Preserve title sequence if roadmap titles are provided.",
        "2. genre_ext.realm_before must equal the previous block realm_after.",
        "3. genre_ext.internal_energy_before must equal the previous block internal_energy_after.",
        "4. Each block must advance at least one wuxia axis: realm, internal energy, martial art, faction standing, reputation, revenge, or sect politics.",
        "5. Do not use capital, deal, business-sector, or starter-company language.",
        "6. Opponent pressure must remain concrete, not generic.",
        "7. Callback lines must resolve or echo earlier seeds when due.",
        "8. If the place repeats from the previous block, change at least two among scene function, opponent/front, stakes, relation targets, or sub-location.",
        "9. `Block/ARC/Phase/Stage` 번호 메타는 자연어 필드에 금지. 복선/회수 번호는 `foreshadow_targets` / `callback_sources`에만 적을 것.",
        "10. `section_rotation`, `arc_section`, `phase` 같은 라벨 필드는 번호 없이 자연어 제목만 적을 것.",
        "",
        "## Predeclare",
        *predeclare,
        "",
        "## Output Order",
        "1. short predeclare",
        "2. JSON array only",
        "3. short continuity note",
        "4. NPC tracker delta",
        "5. foreshadow debt update",
        "",
        "## Batch Rule",
        batch_rule,
        "",
        "## JSON Skeleton",
        "```json",
        prompt_json_skeleton(start, batch_size, protagonist),
        "```",
    ]
    return "\n".join(lines)


def append_finding(findings: list[Finding], severity: str, rule: str, block: str, message: str, fixed: bool = False) -> None:
    findings.append(Finding(severity=severity, rule=rule, block=block, message=message, fixed=fixed))


def render_metrics_snapshot(metrics: dict[str, Any]) -> list[str]:
    return [
        "## Draft Projection",
        f"- production_density_gate: {metrics.get('production_density_gate')}",
        f"- avg_bundle_chars: {metrics.get('avg_bundle_chars')}",
        f"- avg_solution_chars: {metrics.get('avg_solution_chars')}",
        f"- callback_ratio: {metrics.get('callback_ratio')}",
        f"- unresolved_foreshadow_count: {metrics.get('unresolved_foreshadow_count')}",
        f"- diegetic_meta_ref_count: {metrics.get('diegetic_meta_ref_count')}",
        f"- label_meta_ref_count: {metrics.get('label_meta_ref_count')}",
        f"- opponent_unique: {metrics.get('opponent_unique')}",
        f"- top_opponent_share: {metrics.get('top_opponent_share')}",
        f"- martial_progress_blocks: {len(metrics.get('martial_progress_blocks', []))}/{metrics.get('block_count', 0)}",
        f"- same_location_clone_count: {metrics.get('same_location_clone_count')}",
        f"- hard_gate_failures: {metrics.get('hard_gate_failures', [])}",
        "",
    ]


def validate_candidate(
    candidate_blocks: list[dict[str, Any]],
    history_blocks: list[dict[str, Any]],
    start: int,
    batch_size: int,
    roadmap_blocks: list[dict[str, Any]] | None,
    autofix: bool,
) -> tuple[list[Finding], list[dict[str, Any]]]:
    blocks = copy.deepcopy(candidate_blocks)
    findings: list[Finding] = []
    npc_state = build_npc_state(history_blocks)
    due_foreshadows = build_due_foreshadows(history_blocks)
    all_locations = [as_text(get_nested(block, "location.place")) for block in history_blocks]
    all_beats = [as_text(get_nested(block, "emotional_beat.type")) for block in history_blocks]
    prev_block_for_location = history_blocks[-1] if history_blocks else None
    opponent_counter = Counter(
        as_text(get_nested(block, "genre_ext.opponent.name"))
        for block in history_blocks
        if as_text(get_nested(block, "genre_ext.opponent.name"))
    )
    prev_realm = as_text(get_nested(history_blocks[-1], "genre_ext.realm_after")) if history_blocks else ""
    prev_energy = parse_energy(get_nested(history_blocks[-1], "genre_ext.internal_energy_after")) if history_blocks else None
    martial_progress_flags: list[bool] = []

    for offset in range(batch_size):
        expected_no = start + offset
        label = format_block_id(expected_no)
        if offset >= len(blocks):
            append_finding(findings, "P0", "STRUCT-000", label, "Missing block in candidate batch.")
            break
        block = blocks[offset]
        if not isinstance(block, dict):
            append_finding(findings, "P0", "STRUCT-001", label, "Block must be a dict.")
            continue

        if parse_block_no(block.get("block_id")) != expected_no:
            fixed = False
            if autofix:
                block["block_id"] = label
                fixed = True
            append_finding(findings, "P0", "STRUCT-002", label, "block_id does not match expected order.", fixed=fixed)

        planned_title = as_text(roadmap_blocks[expected_no - 1].get("title")) if roadmap_blocks and len(roadmap_blocks) >= expected_no else ""
        if planned_title and as_text(block.get("title")) != planned_title:
            append_finding(findings, "P1", "TITLE-001", label, f"title differs from roadmap title {planned_title!r}")

        content = ensure_dict(block, "content")
        for field in MANDATORY_CONTENT_FIELDS:
            if not as_text(content.get(field)):
                append_finding(findings, "P0", "CONTENT-001", label, f"content.{field} is blank.")

        genre = ensure_dict(block, "genre_ext")
        for field in MANDATORY_MARTIAL_FIELDS:
            if is_blankish(genre.get(field)):
                append_finding(findings, "P1", "MARTIAL-001", label, f"genre_ext.{field} is blank.")

        realm_before = as_text(genre.get("realm_before"))
        realm_after = as_text(genre.get("realm_after"))
        energy_before = parse_energy(genre.get("internal_energy_before"))
        energy_after = parse_energy(genre.get("internal_energy_after"))

        if prev_realm and realm_before != prev_realm:
            fixed = False
            if autofix:
                genre["realm_before"] = prev_realm
                realm_before = prev_realm
                fixed = True
            append_finding(findings, "P0", "REALM-001", label, "realm_before does not match previous realm_after.", fixed=fixed)

        if prev_energy is not None and energy_before != prev_energy:
            fixed = False
            if autofix:
                genre["internal_energy_before"] = prev_energy
                energy_before = prev_energy
                fixed = True
            append_finding(findings, "P0", "ENERGY-001", label, "internal_energy_before does not match previous internal_energy_after.", fixed=fixed)

        if energy_before is None:
            append_finding(findings, "P0", "ENERGY-002", label, "internal_energy_before is not numeric.")
        if energy_after is None:
            append_finding(findings, "P0", "ENERGY-003", label, "internal_energy_after is not numeric.")
        if energy_after is not None and energy_after < 0:
            append_finding(findings, "P0", "ENERGY-004", label, "internal_energy_after cannot be negative.")

        opponent_name = as_text(get_nested(block, "genre_ext.opponent.name"))
        if not opponent_name:
            append_finding(findings, "P1", "OPP-001", label, "genre_ext.opponent.name is blank.")
        else:
            opponent_counter[opponent_name] += 1
            if opponent_counter[opponent_name] >= 3:
                append_finding(findings, "P2", "OPP-002", label, f"same opponent repeated 3+ times in sequence: {opponent_name}")

        relation_deltas = [item for item in ensure_list(block.get("relationship_delta")) if isinstance(item, dict)]
        if not relation_deltas:
            append_finding(findings, "P1", "REL-000", label, "relationship_delta is blank.")
        for relation in relation_deltas:
            target = as_text(relation.get("target"))
            before_text = as_text(relation.get("before"))
            after_text = as_text(relation.get("after"))
            before_sig = relation_before_signature(relation)
            after_sig = relation_after_signature(relation)
            if target and target in npc_state and before_sig != as_text(npc_state[target]["after"]):
                fixed = False
                if autofix:
                    if relation.get("anchor_before"):
                        relation["anchor_before"] = as_text(npc_state[target]["after"])
                        before_sig = as_text(npc_state[target]["after"])
                    else:
                        relation["before"] = as_text(npc_state[target]["after"])
                        before_text = as_text(npc_state[target]["after"])
                        before_sig = as_text(npc_state[target]["after"])
                    fixed = True
                append_finding(findings, "P0", "REL-001", label, f"{target} relation.before/anchor_before does not match previous after/anchor_after.", fixed=fixed)
            if target and before_text == after_text:
                append_finding(findings, "P1", "REL-002", label, f"{target} relationship does not change in this block.")
            if target:
                npc_state[target] = {"after": after_sig, "last_block": expected_no}

        callbacks = [as_text(item) for item in ensure_list(block.get("callback")) if as_text(item)]
        callback_sources = extract_callback_sources(block)
        for due in due_foreshadows.get(expected_no, []):
            if not callbacks:
                append_finding(findings, "P1", "FS-001", label, "A due foreshadow exists but callback is blank.")
                continue
            if due["plant_block"] not in callback_sources and not callback_matches(due["text"], callbacks):
                append_finding(findings, "P1", "FS-002", label, f"Due foreshadow not matched by callback: {truncate(due['text'], 48)}")

        for pattern in BANNED_TEMPLATE_RES:
            for field_path in ("content.context", "content.event_villain", "content.solution", "content.reward"):
                raw = as_text(get_nested(block, field_path))
                if raw and pattern.search(raw):
                    append_finding(findings, "P1", "TPL-001", label, f"{field_path} contains prompt skeleton text.")
            for item in callbacks:
                if pattern.search(item):
                    append_finding(findings, "P1", "TPL-002", label, "callback contains prompt skeleton text.")
        for item in callbacks:
            if GENERIC_CALLBACK_RE.search(item):
                append_finding(findings, "P1", "CALL-001", label, "callback is too generic to prove continuity.")

        meta_leaks = collect_meta_leaks(block)
        diegetic_meta_leaks, label_meta_leaks = split_meta_leaks(meta_leaks)
        for path, raw in diegetic_meta_leaks[:5]:
            append_finding(
                findings,
                "P0",
                "META-001",
                label,
                f"{path}에 Block/ARC/Phase/Stage 메타 참조가 새었다. 자연어 필드에서는 금지: {truncate(raw, 60)}",
            )
        for path, raw in label_meta_leaks[:5]:
            append_finding(
                findings,
                "P0",
                "META-002",
                label,
                f"{path} 라벨에 번호 메타가 들어 있다. section_rotation/arc_section/phase는 자연어 라벨만 허용: {truncate(raw, 60)}",
            )

        beat_type = as_text(get_nested(block, "emotional_beat.type"))
        if beat_type and all_beats and beat_type == all_beats[-1]:
            append_finding(findings, "P2", "BEAT-001", label, f"emotional_beat.type repeated from previous block: {beat_type}")
        if beat_type:
            all_beats.append(beat_type)

        location = as_text(get_nested(block, "location.place"))
        if location and location in all_locations[-9:]:
            append_finding(findings, "P2", "LOC-001", label, f"location repeated within recent 10 blocks: {location}")
        if prev_block_for_location is not None:
            changed_axes = same_location_change_axes(prev_block_for_location, block)
            prev_place = as_text(get_nested(prev_block_for_location, "location.place"))
            if location and prev_place == location and len(changed_axes) < 2:
                append_finding(
                    findings,
                    "P2",
                    "LOC-002",
                    label,
                    f"same-location consecutive reuse lacks differentiation: {location} / changed={changed_axes or ['none']}",
                )
        if location:
            all_locations.append(location)
        prev_block_for_location = block

        language_values: list[tuple[str, str]] = [(path, as_text(get_nested(block, path))) for path in LANGUAGE_PATHS]
        for idx, item in enumerate(ensure_list(block.get("foreshadow"))):
            language_values.append((f"foreshadow[{idx}]", as_text(item)))
        for idx, item in enumerate(callbacks):
            language_values.append((f"callback[{idx}]", as_text(item)))
        for idx, relation in enumerate(relation_deltas):
            language_values.append((f"relationship_delta[{idx}].before", as_text(relation.get("before"))))
            language_values.append((f"relationship_delta[{idx}].after", as_text(relation.get("after"))))
        for path, raw in language_values:
            if raw and korean_ratio(raw) < 0.6:
                append_finding(findings, "P2", "LANG-001", label, f"{path} is not Korean-dominant.")

        for path in CODE_PATHS:
            raw = as_text(get_nested(block, path))
            if raw and CODE_TOKEN_RE.search(raw):
                append_finding(findings, "P2", "CODE-001", label, f"{path} contains code-like placeholder text.")

        martial_progress = (
            (realm_before and realm_after and realm_before != realm_after)
            or (energy_before is not None and energy_after is not None and energy_after > energy_before)
            or bool(as_text(genre.get("martial_art_gain")))
            or bool(as_text(genre.get("artifact_or_manual_gain")))
        )
        martial_progress_flags.append(bool(martial_progress))
        prev_realm = realm_after
        prev_energy = energy_after

    if martial_progress_flags and not any(martial_progress_flags):
        append_finding(findings, "P2", "MARTIAL-010", f"{start}-{start + batch_size - 1}", "No clear martial progress exists in the entire batch.")

    open_after_merge = len(build_open_foreshadow_ledger(history_blocks + blocks[:batch_size]))
    if open_after_merge > LOW_INTELLIGENCE_OPEN_FORESHADOW_LIMIT:
        append_finding(findings, "P2", "FS-003", f"{start}-{start + batch_size - 1}", f"Open foreshadows exceed limit: {open_after_merge}")
    return findings, blocks[:batch_size]


def render_report(findings: list[Finding], title: str) -> str:
    summary = Counter(f.severity for f in findings if not f.fixed)
    fixed_count = sum(1 for f in findings if f.fixed)
    lines = [
        f"# {title}",
        "",
        "## Summary",
        f"- unresolved P0: {summary.get('P0', 0)}",
        f"- unresolved P1: {summary.get('P1', 0)}",
        f"- unresolved P2: {summary.get('P2', 0)}",
        f"- autofixed: {fixed_count}",
        "",
    ]
    for severity in ("P0", "P1", "P2"):
        section = [f for f in findings if f.severity == severity]
        if not section:
            continue
        lines.append(f"## {severity}")
        for finding in section:
            suffix = " [fixed]" if finding.fixed else ""
            lines.append(f"- {finding.block} `{finding.rule}`{suffix}: {finding.message}")
        lines.append("")
    if not findings:
        lines.append("## Result")
        lines.append("- no findings")
    return "\n".join(lines).rstrip() + "\n"


def has_blocking_findings(findings: list[Finding]) -> bool:
    return any(f.severity in {"P0", "P1"} and not f.fixed for f in findings)


def load_blocks_from_path(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return extract_blocks(read_json(path))


def command_prompt(args: argparse.Namespace) -> int:
    draft_blocks = load_blocks_from_path(args.draft)
    roadmap_payload = read_json(args.roadmap) if args.roadmap else None
    roadmap_blocks = extract_blocks(roadmap_payload) if roadmap_payload is not None else None
    meta = extract_project_meta(roadmap_payload) if roadmap_payload is not None else {}
    prompt = build_prompt(draft_blocks, roadmap_blocks, meta, args.start, args.batch_size, args.mode)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(prompt, encoding="utf-8")
    else:
        sys.stdout.write(prompt)
        if not prompt.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def command_check(args: argparse.Namespace) -> int:
    history_blocks = load_blocks_from_path(args.draft)[: args.start - 1] if args.draft and args.draft.exists() else []
    roadmap_blocks = extract_blocks(read_json(args.roadmap)) if args.roadmap else None
    candidate_all = extract_blocks(read_json(args.candidate))
    candidate_blocks = normalize_candidate_slice(candidate_all, args.start, args.batch_size)
    findings, fixed_blocks = validate_candidate(candidate_blocks, history_blocks, args.start, args.batch_size, roadmap_blocks, args.autofix)
    report_lines = [render_report(findings, f"Wuxia TR Batch Check {args.start}-{args.start + args.batch_size - 1}").rstrip()]
    report_lines.extend(render_metrics_snapshot(compute_treatment_metrics(history_blocks + fixed_blocks)))
    report = "\n".join(report_lines).rstrip() + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    if args.fixed_output:
        write_json(args.fixed_output, fixed_blocks)
    return 1 if has_blocking_findings(findings) else 0


def command_merge(args: argparse.Namespace) -> int:
    draft_blocks = load_blocks_from_path(args.draft)
    if not draft_blocks and args.start > 1:
        print("draft is missing but start is not 1", file=sys.stderr)
        return 2
    if draft_blocks and len(draft_blocks) < args.start - 1:
        print("draft does not contain enough previous blocks", file=sys.stderr)
        return 2
    roadmap_blocks = extract_blocks(read_json(args.roadmap)) if args.roadmap else None
    candidate_all = extract_blocks(read_json(args.candidate))
    candidate_blocks = normalize_candidate_slice(candidate_all, args.start, args.batch_size)
    findings, fixed_blocks = validate_candidate(candidate_blocks, draft_blocks[: args.start - 1], args.start, args.batch_size, roadmap_blocks, True)
    report_lines = [render_report(findings, f"Wuxia TR Batch Merge Check {args.start}-{args.start + args.batch_size - 1}").rstrip()]
    report_lines.extend(render_metrics_snapshot(compute_treatment_metrics(draft_blocks[: args.start - 1] + fixed_blocks)))
    report = "\n".join(report_lines).rstrip() + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    if has_blocking_findings(findings) and not args.force:
        sys.stdout.write(report)
        print("Unresolved P0/P1 findings remain. Use --force to merge anyway.", file=sys.stderr)
        return 1
    merged = copy.deepcopy(draft_blocks)
    insert_pos = args.start - 1
    for offset, block in enumerate(fixed_blocks):
        pos = insert_pos + offset
        if pos < len(merged):
            merged[pos] = block
        else:
            merged.append(block)
    output_path = args.output or args.draft
    write_json(output_path, merged)
    print(f"merged blocks {args.start}-{args.start + len(fixed_blocks) - 1} -> {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch harness for wuxia treatment block production")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prompt_parser = subparsers.add_parser("prompt", help="Generate wuxia batch prompt bundle")
    prompt_parser.add_argument("--draft", type=Path, help="Existing treatment draft JSON")
    prompt_parser.add_argument("--roadmap", type=Path, help="Roadmap or BI JSON for titles/context")
    prompt_parser.add_argument("--start", type=int, required=True, help="Start block number (1-based)")
    prompt_parser.add_argument("--batch-size", type=int, default=3, help="Batch size")
    prompt_parser.add_argument("--mode", choices=["flash", "pro", "sonnet"], default="flash", help="Prompt operating mode")
    prompt_parser.add_argument("--output", type=Path, help="Write prompt to file")
    prompt_parser.set_defaults(func=command_prompt)

    check_parser = subparsers.add_parser("check", help="Validate a wuxia candidate batch")
    check_parser.add_argument("--candidate", type=Path, required=True, help="Candidate batch JSON or full treatment JSON")
    check_parser.add_argument("--draft", type=Path, help="Existing treatment draft JSON for continuity checks")
    check_parser.add_argument("--roadmap", type=Path, help="Roadmap or BI JSON for title checks")
    check_parser.add_argument("--start", type=int, required=True, help="Start block number (1-based)")
    check_parser.add_argument("--batch-size", type=int, default=3, help="Batch size")
    check_parser.add_argument("--autofix", action="store_true", help="Apply safe continuity autofixes in memory")
    check_parser.add_argument("--fixed-output", type=Path, help="Write autofixed candidate batch JSON")
    check_parser.add_argument("--report", type=Path, help="Write report markdown")
    check_parser.set_defaults(func=command_check)

    merge_parser = subparsers.add_parser("merge", help="Validate and merge a wuxia candidate batch into a draft")
    merge_parser.add_argument("--draft", type=Path, required=True, help="Draft JSON to update")
    merge_parser.add_argument("--candidate", type=Path, required=True, help="Candidate batch JSON or full treatment JSON")
    merge_parser.add_argument("--roadmap", type=Path, help="Roadmap or BI JSON for title checks")
    merge_parser.add_argument("--start", type=int, required=True, help="Start block number (1-based)")
    merge_parser.add_argument("--batch-size", type=int, default=3, help="Batch size")
    merge_parser.add_argument("--output", type=Path, help="Output path. Default: overwrite draft")
    merge_parser.add_argument("--report", type=Path, help="Write merge report markdown")
    merge_parser.add_argument("--force", action="store_true", help="Merge even when unresolved P0/P1 findings remain")
    merge_parser.set_defaults(func=command_merge)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
