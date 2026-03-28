#!/usr/bin/env python3
"""Batch harness for high-quality treatment block generation."""

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

from modules.narrative_router.harness_digest import load_harness_digest, render_harness_digest_lines

BLOCK_REF_RE = re.compile(r"Block\s*(\d+)", re.IGNORECASE)
HANGUL_RE = re.compile(r"[가-힣]")
LATIN_RE = re.compile(r"[A-Za-z]")
TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]{2,}")
CODE_TOKEN_RE = re.compile(r"(?:_\d+|type_\d+|plan_\d+|anomaly_\d+|protocol_\d+|_B\d+)", re.IGNORECASE)

BANNED_TEMPLATE_RES = [
    re.compile(r"Deferred setup for Block", re.IGNORECASE),
    re.compile(r"carry-over was converted into leverage", re.IGNORECASE),
    re.compile(r"Capital moved from", re.IGNORECASE),
]
GENERIC_CALLBACK_RE = re.compile(r"직전 블록의 .* 성과가 이번 .* 발판이 되었다")
AMOUNT_RE = re.compile(r"\d[\d,.]*\s*(?:억|조|만|원|%|달러|위안|배)?")  # utf8-hygiene: allow-line -- regex uses literal ? quantifier.
ORG_RE = re.compile(
    r"[가-힣A-Za-z0-9]{2,}(?:사|그룹|회사|공장|호텔|병원|은행|연합|센터|재단|증권|캐피탈|인베스트먼트|파트너스|자산운용)"  # utf8-hygiene: allow-line -- regex uses literal ? quantifier.
)
RECOGNITION_RE = re.compile(
    r"(대단|인정|재평가|경탄|감탄|존중|신뢰|의지|믿게|다시\s*봤|경외|감복|수긍|고개를 숙|격이 다르)"
)

MANDATORY_CONTENT_FIELDS = ("context", "event_villain", "solution", "reward")
LANGUAGE_PATHS = [
    "stakes",
    "content.reward",
    "genre_ext.method",
    "genre_ext.success_pattern",
    "regression_ext.regression_hint.slip_up",
]
CODE_PATHS = [
    "genre_ext.method",
    "genre_ext.success_pattern",
    "genre_ext.opponent.weakness_exploited",
    "regression_ext.execution_doctrine",
    "regression_ext.death_flag.avoided",
    "regression_ext.death_flag.method",
    "regression_ext.regression_hint.slip_up",
]
LOW_INTELLIGENCE_OPEN_FORESHADOW_LIMIT = 10
BLANKISH_PREFIXES = ("없음", "해당 없음")
BLANKISH_VALUES = {
    "",
    "없다",
    "무",
    "none",
    "n/a",
    "na",
    "null",
}
ENTITY_TOKEN_STOPWORDS = {
    "그리고",
    "하지만",
    "그러나",
    "이번",
    "블록",
    "자본",
    "상대",
    "주인공",
    "시장",
    "가문",
    "회사",
    "그룹",
    "운영",
    "계약",
    "정산",
}


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
    text = as_text(value)
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def format_block_id(number: int) -> str:
    return f"Block {number}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_tail(text: Any, length: int = 20) -> str:
    raw = re.sub(r"\s+", " ", as_text(text))
    return raw[-length:] if len(raw) >= length else raw


def sentence_like_count(text: Any) -> int:
    raw = as_text(text)
    if not raw:
        return 0
    parts = [part for part in re.split(r"[.!?]+", raw) if part.strip()]
    return len(parts) if parts else 1


def is_blankish(value: Any) -> bool:
    text = re.sub(r"\s+", " ", as_text(value)).strip()
    if not text:
        return True
    lowered = text.lower()
    if lowered in BLANKISH_VALUES:
        return True
    return any(text.startswith(prefix) for prefix in BLANKISH_PREFIXES)


def bundle_size(block: dict[str, Any]) -> int:
    content = block.get("content", {}) if isinstance(block, dict) else {}
    return (
        len(as_text(content.get("context")))
        + len(as_text(content.get("event_villain")))
        + len(as_text(content.get("solution")))
        + len(as_text(content.get("reward")))
        + len(as_text(block.get("stakes")))
    )


def iter_entity_tokens(block: dict[str, Any]) -> list[str]:
    genre = block.get("genre_ext", {}) if isinstance(block, dict) else {}
    opponent = genre.get("opponent", {}) if isinstance(genre.get("opponent", {}), dict) else {}
    names = [
        block.get("title"),
        opponent.get("name"),
        (genre.get("global_partner") or {}).get("name") if isinstance(genre.get("global_partner"), dict) else "",
    ]
    for rel in ensure_list(block.get("relationship_delta")):
        if isinstance(rel, dict):
            names.append(rel.get("target"))

    tokens: set[str] = set()
    for text in names:
        for token in re.findall(r"[가-힣A-Za-z]{2,}", as_text(text)):
            if token not in ENTITY_TOKEN_STOPWORDS:
                tokens.add(token)
    return sorted(tokens, key=len, reverse=True)


def normalize_solution_stakes_signature(block: dict[str, Any]) -> str:
    content = block.get("content", {}) if isinstance(block, dict) else {}
    raw = f"{as_text(content.get('solution'))} {as_text(block.get('stakes'))}".strip()
    if not raw:
        return ""

    text = BLOCK_REF_RE.sub("[BLOCK]", raw)
    text = AMOUNT_RE.sub("[N]", text)
    text = ORG_RE.sub("[ORG]", text)
    for token in iter_entity_tokens(block):
        text = re.sub(re.escape(token), "[ENT]", text, flags=re.IGNORECASE)
    text = re.sub(r"[A-Za-z]{2,}", "[ENG]", text)
    text = re.sub(r"[가-힣]{2,5}", "[K]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_unresolved_foreshadows(blocks: list[dict[str, Any]]) -> int:
    unresolved = 0
    for foreshadow_source in blocks:
        for foreshadow in ensure_list(foreshadow_source.get("foreshadow")):
            text = as_text(foreshadow)
            if not text:
                continue
            targets = [int(match.group(1)) for match in BLOCK_REF_RE.finditer(text)]
            if not targets:
                continue
            source_tokens = set(TOKEN_RE.findall(text.lower()))
            for target in targets:
                if target < 1 or target > len(blocks):
                    unresolved += 1
                    continue
                callbacks = ensure_list(blocks[target - 1].get("callback"))
                resolved = False
                for callback in callbacks:
                    callback_tokens = set(TOKEN_RE.findall(as_text(callback).lower()))
                    if len(source_tokens & callback_tokens) >= 2:
                        resolved = True
                        break
                if not resolved:
                    unresolved += 1
    return unresolved


def has_recognition_signal(block: dict[str, Any]) -> bool:
    regression = block.get("regression_ext", {}) if isinstance(block.get("regression_ext"), dict) else {}
    regression_hint = regression.get("regression_hint", {}) if isinstance(regression.get("regression_hint"), dict) else {}

    explicit = regression_hint.get("recognition_from")
    if not is_blankish(explicit):
        return True

    candidates = [block.get("content", {}).get("reward", "")]
    candidates.extend(as_text(item) for item in ensure_list(block.get("callback")))
    for rel in ensure_list(block.get("relationship_delta")):
        if isinstance(rel, dict):
            candidates.append(rel.get("after", ""))
    power_shift = block.get("power_shift", {})
    if isinstance(power_shift, dict):
        candidates.append(power_shift.get("antagonist", ""))
        candidates.append(power_shift.get("protagonist", ""))

    return any(RECOGNITION_RE.search(as_text(text)) for text in candidates)


def compute_treatment_metrics(blocks: list[dict[str, Any]]) -> dict[str, Any]:
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
            "deal_unique": 0,
            "method_unique": 0,
            "top_opponent_name": "",
            "top_opponent_repetition": 0,
            "top_opponent_share": 0.0,
            "top_weakness_repetition": 0,
            "deal_top_repetition": 0,
            "method_top_repetition": 0,
            "solution_tail20_top_repetition": 0,
            "one_sentence_like_solution_blocks": 0,
            "business_sector_missing": 0,
            "section_rotation_missing": 0,
            "critical_thin_blocks": [],
            "thin_blocks": [],
            "short_stakes_blocks": [],
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
                "forbidden_pattern_reuse": [],
                "structural_gate_failures": [],
            },
        }

    opponent_names: list[str] = []
    weaknesses: list[str] = []
    deals: list[str] = []
    methods: list[str] = []
    solution_tails: list[str] = []
    normalized_solution_stakes: list[str] = []
    bundle_sizes: list[int] = []
    solution_sizes: list[int] = []
    one_sentence_like = 0
    business_sector_missing = 0
    section_rotation_missing = 0
    critical_thin_blocks: list[int] = []
    thin_blocks: list[int] = []
    short_stakes_blocks: list[int] = []
    recognition_signal_blocks = 0
    recognition_gap_streak = 0
    max_recognition_gap_streak = 0
    is_regressor_treatment = False
    foreshadow_total = 0
    callback_total = 0

    for block_no, block in enumerate(blocks, start=1):
        genre = block.get("genre_ext", {}) if isinstance(block, dict) else {}
        content = block.get("content", {}) if isinstance(block, dict) else {}
        opponent = genre.get("opponent", {}) if isinstance(genre.get("opponent", {}), dict) else {}
        regression = block.get("regression_ext", {}) if isinstance(block.get("regression_ext"), dict) else {}
        regression_hint = regression.get("regression_hint", {}) if isinstance(regression.get("regression_hint"), dict) else {}
        is_regressor = bool(regression.get("is_regressor")) or as_text(regression.get("regression_type")) in {"빙의", "회귀"}
        if is_regressor:
            is_regressor_treatment = True

        opponent_names.append(as_text(opponent.get("name")))
        weaknesses.append(as_text(opponent.get("weakness_exploited")))
        deals.append(as_text(genre.get("deal_type")))
        methods.append(as_text(genre.get("method")))

        solution = as_text(content.get("solution"))
        solution_sizes.append(len(solution))
        solution_tails.append(normalize_tail(solution, 20))
        normalized_solution_stakes.append(normalize_solution_stakes_signature(block))
        if sentence_like_count(solution) <= 2:
            one_sentence_like += 1

        current_bundle = bundle_size(block)
        bundle_sizes.append(current_bundle)
        if current_bundle < 300:
            critical_thin_blocks.append(block_no)
        elif current_bundle < 350:
            thin_blocks.append(block_no)

        stakes_len = len(as_text(block.get("stakes")))
        if stakes_len < 35:
            short_stakes_blocks.append(block_no)

        if is_blankish(genre.get("business_sector")):
            business_sector_missing += 1
        if is_blankish(genre.get("section_rotation")):
            section_rotation_missing += 1

        foreshadow_total += len([text for text in ensure_list(block.get("foreshadow")) if as_text(text)])
        callback_total += len([text for text in ensure_list(block.get("callback")) if as_text(text)])

        if is_regressor:
            if has_recognition_signal(block):
                recognition_signal_blocks += 1
                recognition_gap_streak = 0
            else:
                recognition_gap_streak += 1
                max_recognition_gap_streak = max(max_recognition_gap_streak, recognition_gap_streak)

    opponent_counter = Counter(name for name in opponent_names if name and not is_blankish(name))
    weakness_counter = Counter(value for value in weaknesses if value and not is_blankish(value))
    deal_counter = Counter(value for value in deals if value and not is_blankish(value))
    method_counter = Counter(value for value in methods if value and not is_blankish(value))
    solution_tail_counter = Counter(value for value in solution_tails if value)

    top_opponent_name, top_opponent_repetition = opponent_counter.most_common(1)[0] if opponent_counter else ("", 0)
    top_weakness_repetition = weakness_counter.most_common(1)[0][1] if weakness_counter else 0
    deal_top_repetition = deal_counter.most_common(1)[0][1] if deal_counter else 0
    method_top_repetition = method_counter.most_common(1)[0][1] if method_counter else 0
    solution_tail20_top_repetition = solution_tail_counter.most_common(1)[0][1] if solution_tail_counter else 0

    window_10 = []
    for start in range(0, len(opponent_names), 10):
        chunk = [name for name in opponent_names[start : start + 10] if name and not is_blankish(name)]
        window_10.append(len(set(chunk)))

    unresolved_foreshadow_count = count_unresolved_foreshadows(blocks)
    callback_ratio = round(callback_total / max(foreshadow_total, 1), 2)
    late_blank_opponent_blocks = [
        idx
        for idx in range(max(1, len(blocks) - 9), len(blocks) + 1)
        if is_blankish(opponent_names[idx - 1])
    ]
    endgame_low_stakes_blocks = [
        idx for idx in range(max(1, len(blocks) - 4), len(blocks) + 1) if idx in short_stakes_blocks
    ]

    normalized_solution_stakes_repeat_max = 0
    for start in range(0, len(normalized_solution_stakes), 10):
        chunk = [value for value in normalized_solution_stakes[start : start + 10] if value]
        if not chunk:
            continue
        normalized_solution_stakes_repeat_max = max(
            normalized_solution_stakes_repeat_max,
            Counter(chunk).most_common(1)[0][1],
        )

    thin_ratio_limit = len(blocks) * 0.10
    required_recognition_blocks = max(6, (len(blocks) + 9) // 10) if is_regressor_treatment else 0
    hard_gate_checks = {
        "critical_thin_blocks_zero": len(critical_thin_blocks) == 0,
        "thin_blocks_ratio_ok": len(thin_blocks) <= thin_ratio_limit,
        "late_thin_blocks_zero": not any(block_no > len(blocks) - 10 for block_no in thin_blocks),
        "short_stakes_blocks_total_ok": len(short_stakes_blocks) <= 2,
        "endgame_low_stakes_zero": len(endgame_low_stakes_blocks) == 0,
        "callback_ratio_ok": callback_ratio >= 0.65,
        "unresolved_foreshadow_count_ok": unresolved_foreshadow_count <= (foreshadow_total * 0.35),
        "section_rotation_present": section_rotation_missing == 0,
        "late_blank_opponent_ok": len(late_blank_opponent_blocks) <= 1,
        "normalized_solution_stakes_repeat_ok": normalized_solution_stakes_repeat_max <= 3,
    }
    if is_regressor_treatment:
        hard_gate_checks["regressor_recognition_count_ok"] = recognition_signal_blocks >= required_recognition_blocks
        hard_gate_checks["regressor_recognition_gap_ok"] = max_recognition_gap_streak <= 15

    pattern_warnings: list[str] = []
    forbidden_reuse: list[str] = []
    if solution_tail20_top_repetition >= 50:
        pattern_warnings.append(f"solution tail-20 repeats {solution_tail20_top_repetition} times")
    if top_weakness_repetition >= 3:
        forbidden_reuse.append(f"same weakness repeats {top_weakness_repetition} times")
    if top_opponent_repetition / max(len(blocks), 1) > 0.30:
        pattern_warnings.append(
            f"top opponent {top_opponent_name} share is {round(top_opponent_repetition / len(blocks) * 100, 1)}%"
        )
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
        "deal_unique": len(set(value for value in deals if value and not is_blankish(value))),
        "method_unique": len(set(value for value in methods if value and not is_blankish(value))),
        "top_opponent_name": top_opponent_name,
        "top_opponent_repetition": top_opponent_repetition,
        "top_opponent_share": round(top_opponent_repetition / len(blocks) * 100, 1) if blocks else 0.0,
        "top_weakness_repetition": top_weakness_repetition,
        "deal_top_repetition": deal_top_repetition,
        "method_top_repetition": method_top_repetition,
        "solution_tail20_top_repetition": solution_tail20_top_repetition,
        "one_sentence_like_solution_blocks": one_sentence_like,
        "business_sector_missing": business_sector_missing,
        "section_rotation_missing": section_rotation_missing,
        "critical_thin_blocks": critical_thin_blocks,
        "thin_blocks": thin_blocks,
        "short_stakes_blocks": short_stakes_blocks,
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
            "forbidden_pattern_reuse": forbidden_reuse,
            "structural_gate_failures": structural_gate_failures,
        },
    }


def extract_blocks(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        treatments = payload.get("treatments")
        if isinstance(treatments, list):
            return treatments
        blocks = payload.get("blocks")
        if isinstance(blocks, list):
            return blocks
        roadmap = payload.get("plot_roadmap")
        if isinstance(roadmap, list):
            return roadmap
        master = payload.get("MasterBible")
        if isinstance(master, dict):
            roadmap = master.get("plot_roadmap")
            if isinstance(roadmap, list):
                return roadmap
    raise ValueError("지원하지 않는 JSON 구조입니다. list / treatments / plot_roadmap 중 하나가 필요합니다.")


def extract_project_meta(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    master = payload.get("MasterBible", payload)
    if not isinstance(master, dict):
        return {}

    project = master.get("ProjectData", {})
    meta = project.get("MetaInfo", {})
    core = project.get("CoreIdentity", {})
    npcs = master.get("AssetLibrary", {}).get("KeyNPCs", [])

    protagonist = as_text(core.get("protagonist"))
    if not protagonist:
        protagonist = as_text(
            master.get("FinanceHUD", {})
            .get("Protagonist", {})
            .get("actual_truth", {})
            .get("name")
        )

    return {
        "title": as_text(meta.get("title")),
        "genre": as_text(meta.get("genre_archetype")),
        "logline": as_text(meta.get("logline")),
        "protagonist": protagonist,
        "npcs": [n for n in npcs if isinstance(n, dict)],
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


def capital_to_eok(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return int(round(raw))

    text = as_text(raw).replace(",", "").replace(" ", "")
    if not text:
        return None

    if re.fullmatch(r"[+-]?\d+", text):
        return int(text)

    if re.fullmatch(r"[+-]?\d+억", text):  # utf8-hygiene: allow-line -- regex uses literal ? quantifier.
        return int(text[:-1])

    jo_match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)조(?:(\d+)억)?", text)  # utf8-hygiene: allow-line -- regex uses literal ? quantifier.
    if jo_match:
        jo = float(jo_match.group(1))
        eok = int(jo_match.group(2) or 0)
        return int(round(jo * 10_000)) + eok

    return None


def use_eok_only(*values: Any) -> bool:
    return not any("조" in as_text(value) for value in values if as_text(value))


def format_eok(value: int, eok_only: bool = False) -> str:
    sign = "-" if value < 0 else ""
    number = abs(value)

    if eok_only or number < 10_000:
        return f"{sign}{number:,}억"

    jo = number // 10_000
    rest = number % 10_000
    if rest:
        return f"{sign}{jo}조 {rest:,}억"
    return f"{sign}{jo}조"


def format_profit_loss(delta: int, eok_only: bool = False) -> str:
    direction = "증가" if delta >= 0 else "감소"
    return f"{format_eok(abs(delta), eok_only=eok_only)} {direction}"


def korean_ratio(text: Any) -> float:
    raw = as_text(text)
    if not raw:
        return 1.0
    hangul = len(HANGUL_RE.findall(raw))
    latin = len(LATIN_RE.findall(raw))
    if hangul == 0 and latin == 0:
        return 1.0
    return hangul / max(hangul + latin, 1)


def token_set(text: Any) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(as_text(text))
        if token.lower() not in {"block", "이번", "다음", "직전", "성과", "발판"}
    }


def callback_matches(seed: str, callbacks: list[str]) -> bool:
    seed_tokens = token_set(seed)
    if not seed_tokens:
        return False
    for callback in callbacks:
        if len(seed_tokens & token_set(callback)) >= 2:
            return True
    return False


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
            state[target] = {
                "last_block": block_no,
                "before": as_text(relation.get("before")),
                "after": as_text(relation.get("after")),
            }
    return state


def build_due_foreshadows(blocks: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    due: dict[int, list[dict[str, Any]]] = {}
    for block in blocks:
        plant_no = parse_block_no(block.get("block_id")) or 0
        for text in ensure_list(block.get("foreshadow")):
            seed = as_text(text)
            if not seed:
                continue
            for match in BLOCK_REF_RE.finditer(seed):
                target = int(match.group(1))
                if target <= len(blocks):
                    target_callbacks = [as_text(item) for item in ensure_list(blocks[target - 1].get("callback"))]
                    if callback_matches(seed, target_callbacks):
                        continue
                due.setdefault(target, []).append(
                    {
                        "plant_block": plant_no,
                        "target_block": target,
                        "text": seed,
                    }
                )
    return due


def build_open_foreshadow_ledger(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    completed_callbacks: list[tuple[int, list[str]]] = []
    for block in blocks:
        block_no = parse_block_no(block.get("block_id")) or 0
        callbacks = [as_text(item) for item in ensure_list(block.get("callback")) if as_text(item)]
        completed_callbacks.append((block_no, callbacks))

    for block in blocks:
        plant_no = parse_block_no(block.get("block_id")) or 0
        for text in ensure_list(block.get("foreshadow")):
            seed = as_text(text)
            if not seed:
                continue

            targets = [int(match.group(1)) for match in BLOCK_REF_RE.finditer(seed)]
            if targets:
                status = "OPEN"
                for target in targets:
                    if target <= len(blocks):
                        callbacks = [cb for no, cb in completed_callbacks if no == target]
                        flat = callbacks[0] if callbacks else []
                        if callback_matches(seed, flat):
                            status = "CLOSED"
                            break
                        status = "OVERDUE"
                if status != "CLOSED":
                    ledger.append(
                        {
                            "text": seed,
                            "plant_block": plant_no,
                            "target_block": ",".join(str(t) for t in targets),
                            "status": status,
                        }
                    )
                continue

            resolved = False
            for block_no, callbacks in completed_callbacks:
                if block_no <= plant_no:
                    continue
                if callback_matches(seed, callbacks):
                    resolved = True
                    break
            if not resolved:
                ledger.append(
                    {
                        "text": seed,
                        "plant_block": plant_no,
                        "target_block": "-",
                        "status": "OPEN",
                    }
                )

    return ledger


def truncate(text: Any, limit: int = 90) -> str:
    raw = as_text(text)
    if len(raw) <= limit:
        return raw
    return f"{raw[:limit - 1]}…"


def recent_block_summary(blocks: list[dict[str, Any]], limit: int = 3) -> str:
    if not blocks:
        return "- 첫 배치이므로 이전 블록이 없다."

    lines: list[str] = []
    for block in blocks[-limit:]:
        genre = block.get("genre_ext", {}) if isinstance(block.get("genre_ext"), dict) else {}
        beat = block.get("emotional_beat", {}) if isinstance(block.get("emotional_beat"), dict) else {}
        location = block.get("location", {}) if isinstance(block.get("location"), dict) else {}
        lines.append(
            f"- {block.get('block_id')}: {truncate(block.get('title'), 40)} | "
            f"자본 {as_text(genre.get('capital_before'))} -> {as_text(genre.get('capital_after'))} | "
            f"beat {as_text(beat.get('type'))}/{as_text(beat.get('intensity'))} | "
            f"deal {as_text(genre.get('deal_type'))} | 장소 {as_text(location.get('place'))}"
        )
        lines.append(f"  reward: {truncate(get_nested(block, 'content.reward'), 110)}")
    return "\n".join(lines)


def npc_tracker_table(blocks: list[dict[str, Any]]) -> str:
    state = build_npc_state(blocks)
    if not state:
        return "| NPC | 마지막 블록 | 현재 관계 |\n|---|---:|---|\n| (없음) | - | 첫 배치 |"

    rows = ["| NPC | 마지막 블록 | 현재 관계 |", "|---|---:|---|"]
    for name, data in sorted(state.items(), key=lambda item: (item[1]["last_block"], item[0]), reverse=True)[:12]:
        rows.append(f"| {name} | {data['last_block']} | {truncate(data['after'], 70)} |")
    return "\n".join(rows)


def foreshadow_table(blocks: list[dict[str, Any]]) -> str:
    ledger = build_open_foreshadow_ledger(blocks)
    if not ledger:
        return "| # | 내용 | 심기 | 회수 예정 | 상태 |\n|---|---|---:|---:|---|\n| (없음) | - | - | - | CLEAN |"

    rows = ["| # | 내용 | 심기 | 회수 예정 | 상태 |", "|---|---|---:|---:|---|"]
    for idx, item in enumerate(ledger[:LOW_INTELLIGENCE_OPEN_FORESHADOW_LIMIT], start=1):
        rows.append(
            f"| {idx} | {truncate(item['text'], 42)} | {item['plant_block']} | {item['target_block']} | {item['status']} |"
        )
    return "\n".join(rows)


def batch_target_lines(
    roadmap_blocks: list[dict[str, Any]] | None,
    start: int,
    batch_size: int,
) -> str:
    lines: list[str] = []
    for number in range(start, start + batch_size):
        title = f"Block {number}"
        summary = ""
        if roadmap_blocks and len(roadmap_blocks) >= number:
            source = roadmap_blocks[number - 1]
            title = as_text(source.get("title")) or title
            summary = as_text(source.get("summary"))
        line = f"- Block {number}: {title}"
        if summary:
            line += f" | skeleton summary: {summary}"
        lines.append(line)
    return "\n".join(lines)


def prompt_json_skeleton(start: int, batch_size: int, protagonist: str) -> str:
    first = {
        "block_id": format_block_id(start),
        "title": "제목",
        "content": {
            "context": "상황과 배경",
            "event_villain": "적대 행동",
            "solution": "주인공 해결",
            "reward": "결과와 보상",
        },
        "stakes": "이번 블록 실패 시 손실",
        "power_shift": {
            "protagonist": "주인공 위상 변화",
            "antagonist": "적대자 위상 변화",
        },
        "relationship_delta": [
            {"target": "NPC 이름", "before": "직전 after 복사", "after": "이번 변화"}
        ],
        "foreshadow": ["향후 회수할 복선"],
        "callback": ["이번 블록에서 회수한 복선"],
        "emotional_beat": {"type": "resolve", "intensity": 7},
        "tension_level": 8,
        "pov_character": protagonist or "주인공",
        "location": {"place": "장소", "type": "사업 거점"},
        "time_span": {"duration": "2주", "in_story_time": "2006년 1월"},
        "genre_ext": {
            "capital_before": "120억",
            "capital_after": "135억",
            "capital_delta": "+15억",
            "profit_loss": "15억 증가",
            "method": "한국어 서사 문장",
            "investment_type": "거래 유형 설명",
            "deal_type": "직전 2블록과 다른 딜 형태",
            "leverage_used": ["신규 레버리지 1", "신규 레버리지 2"],
            "opponent": {"name": "적대자", "type": "경쟁 세력", "weakness_exploited": "한국어 약점 설명"},
            "historical_event": "이번 블록 사건명",
            "time_pressure": "시간 압박",
            "knowledge_used": "판단 근거",
            "risk_level": "중상",
            "business_sector": "섹터명",
            "section_rotation": "대단원 내 역할",
            "global_partner": {"name": "파트너", "cadence": "비정형", "objective": "목적"},
            "success_pattern": "한국어 결과 패턴",
        },
        "regression_ext": {
            "is_regressor": True,
            "regression_type": "빙의",
            "timeline_knowledge": {"info_used": "사용 정보", "accuracy": "상", "source": "출처"},
            "butterfly_effect": {"original_event": "원래 사건", "changed_event": "바뀐 사건", "ripple_effect": "파급"},
            "death_flag": {"avoided": "회피한 위기", "method": "회피 방법"},
            "regression_hint": {
                "slip_up": "너무 정확한 타이밍이 드러난 실수",
                "recognition_from": "주인공의 비범함을 인정한 인물 또는 세력",
                "suspicion_from": "선택: 이상함을 눈치챈 인물 또는 세력",
            },
            "future_prep": {"action": "다음 준비", "target_event": "다음 목표"},
            "single_heir_policy": "승계 정책",
            "incarnation_type": "빙의자",
            "execution_doctrine": "이번 블록 시점 전략 문장",
        },
    }
    sample = []
    for offset in range(batch_size):
        block = copy.deepcopy(first)
        block["block_id"] = format_block_id(start + offset)
        sample.append(block)
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
    digest_lines = render_harness_digest_lines(load_harness_digest(family="blockguide", stage="tr_batch"))

    if mode == "flash":
        predeclare = """1. 직전 상태 인용: 직전 블록의 capital_after, emotional_beat, 관계 after를 인용하라.
2. 자본 계산: capital_before = 직전 capital_after. 이번 변화 근거와 계산식을 적어라.
3. 차별화 1줄: 직전 블록과 가장 크게 달라진 지점을 1문장으로 써라."""
        batch_rule = "배치는 3블록이며, JSON 뒤에 3블록 차이 행렬과 OPEN 복선 원장만 출력하라."
    else:
        predeclare = """1. 이전 블록 잔향
2. 이번 블록의 고유 사건
3. 5필드 차별화 증명
4. 자본 계산 과정
5. NPC 관계 이월
6. 언어·형식 체크"""
        batch_rule = "배치가 끝나면 차이 행렬, NPC 추적표, 복선 원장, 자본 곡선을 출력하라."

    lines = [
        "# Treatment Batch Harness Prompt",
        "",
        "이 프롬프트는 저지능 모델 기준으로 작성되었다. 절대로 한 번에 70블록을 만들지 마라.",
        "",
        "## 작품 컨텍스트",
        f"- 제목: {as_text(meta.get('title')) or '(미지정)'}",
        f"- 장르: {as_text(meta.get('genre')) or '(미지정)'}",
        f"- 주인공: {protagonist or '(미지정)'}",
        f"- 로그라인: {as_text(meta.get('logline')) or '(미지정)'}",
        "",
        "## 이번 배치",
        f"- 시작 블록: {start}",
        f"- 종료 블록: {start + batch_size - 1}",
        f"- 모드: {mode}",
        "",
        "## 이번 배치 목표",
        batch_target_lines(roadmap_blocks, start, batch_size),
        "",
        "## 직전 3블록 요약",
        recent_block_summary(completed),
        "",
        "## NPC 추적표",
        npc_tracker_table(completed),
        "",
        "## OPEN 복선 원장",
        foreshadow_table(completed),
        "",
        *digest_lines,
        "",
        "## 출력 순서",
        "1. 사전 선언",
        "2. JSON",
        "3. 차이 행렬",
        "4. 복선 원장 업데이트",
        "",
        "## 사전 선언 항목",
        predeclare,
        "",
        "## 절대 금지",
        "- 70블록 단일 출력 금지",
        "- 한국어 대신 영문 템플릿 사용 금지",
        "- `plan_01`, `type_1`, `_B01` 같은 코드형 값 금지",
        "- callback을 `직전 블록의 성과가 발판` 한 문장으로 때우는 것 금지",
        "- deal_type 3블록 이내 재등장 금지",
        "- emotional_beat.type 2연속 동일 금지",
        "- location 15블록 이내 재등장 금지",
        "- `capital_before != 직전 capital_after` 금지",
        "- `relationship_delta.before != 직전 after` 금지",
        "- leverage_used 동일 세트 3회 반복 금지",
        "",
        "## 배치 운영 규칙",
        batch_rule,
        "",
        "## JSON 스켈레톤",
        "```json",
        prompt_json_skeleton(start, batch_size, protagonist),
        "```",
        "",
        "## 추가 지시",
        "- title은 위 배치 목표의 title을 그대로 사용하라.",
        "- roadmap 내용이 이미 존재하더라도 그대로 베끼지 말고, title만 고정점으로 사용하라.",
        "- 모델이 확신이 없으면 빈칸 대신 보수적인 한국어 서사 문장을 작성하라.",
    ]
    return "\n".join(lines)


def append_finding(
    findings: list[Finding],
    severity: str,
    rule: str,
    block: str,
    message: str,
    fixed: bool = False,
) -> None:
    findings.append(Finding(severity=severity, rule=rule, block=block, message=message, fixed=fixed))


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
    all_deal_types = [as_text(get_nested(block, "genre_ext.deal_type")) for block in history_blocks]
    all_beats = [as_text(get_nested(block, "emotional_beat.type")) for block in history_blocks]
    leverage_counter = Counter(
        tuple(sorted(as_text(item) for item in ensure_list(get_nested(block, "genre_ext.leverage_used")) if as_text(item)))
        for block in history_blocks
    )

    prev_after_raw = as_text(get_nested(history_blocks[-1], "genre_ext.capital_after")) if history_blocks else ""
    prev_after_value = capital_to_eok(prev_after_raw) if prev_after_raw else None

    for offset in range(batch_size):
        expected_no = start + offset
        label = format_block_id(expected_no)

        if offset >= len(blocks):
            append_finding(findings, "P0", "STRUCT-000", label, "후보 블록 수가 batch_size보다 적다.")
            break

        block = blocks[offset]
        if not isinstance(block, dict):
            append_finding(findings, "P0", "STRUCT-001", label, "블록이 dict 형식이 아니다.")
            continue

        original_block_id = as_text(block.get("block_id"))
        actual_no = parse_block_no(block.get("block_id"))
        if actual_no != expected_no:
            fixed = False
            if autofix:
                block["block_id"] = label
                fixed = True
            append_finding(findings, "P0", "STRUCT-002", label, f"block_id가 {original_block_id!r}라서 순서가 틀렸다.", fixed=fixed)

        planned_title = ""
        if roadmap_blocks and len(roadmap_blocks) >= expected_no:
            planned_title = as_text(roadmap_blocks[expected_no - 1].get("title"))
        if planned_title and as_text(block.get("title")) != planned_title:
            append_finding(findings, "P1", "TITLE-001", label, f"title이 roadmap title과 다르다. expected={planned_title!r}")

        content = ensure_dict(block, "content")
        for field in MANDATORY_CONTENT_FIELDS:
            if not as_text(content.get(field)):
                append_finding(findings, "P0", "CONTENT-001", label, f"content.{field}가 비어 있다.")

        genre = ensure_dict(block, "genre_ext")
        before_raw = as_text(genre.get("capital_before"))
        after_raw = as_text(genre.get("capital_after"))
        delta_raw = as_text(genre.get("capital_delta"))
        before_value = capital_to_eok(before_raw)
        after_value = capital_to_eok(after_raw)

        if prev_after_raw:
            matches = before_value is not None and prev_after_value is not None and before_value == prev_after_value
            if not matches:
                fixed = False
                if autofix and prev_after_raw:
                    genre["capital_before"] = prev_after_raw
                    before_raw = prev_after_raw
                    before_value = prev_after_value
                    fixed = True
                append_finding(
                    findings,
                    "P0",
                    "CAP-001",
                    label,
                    f"capital_before가 직전 capital_after와 이어지지 않는다. prev={prev_after_raw!r}, current={before_raw!r}",
                    fixed=fixed,
                )

        if before_value is None:
            append_finding(findings, "P0", "CAP-002", label, f"capital_before를 파싱할 수 없다: {before_raw!r}")
        if after_value is None:
            append_finding(findings, "P0", "CAP-003", label, f"capital_after를 파싱할 수 없다: {after_raw!r}")

        if before_value is not None and after_value is not None:
            actual_delta = after_value - before_value
            parsed_delta = capital_to_eok(delta_raw)
            fixed = False
            if parsed_delta != actual_delta:
                if autofix:
                    eok_only = use_eok_only(before_raw, after_raw, delta_raw, prev_after_raw)
                    genre["capital_delta"] = format_eok(actual_delta, eok_only=eok_only)
                    genre["profit_loss"] = format_profit_loss(actual_delta, eok_only=eok_only)
                    fixed = True
                append_finding(
                    findings,
                    "P0",
                    "CAP-004",
                    label,
                    f"capital_delta가 계산식과 다르다. before={before_raw}, after={after_raw}, delta={delta_raw}",
                    fixed=fixed,
                )

        reg = ensure_dict(block, "regression_ext")
        reg_type = as_text(reg.get("regression_type"))
        is_regressor = reg.get("is_regressor")
        if reg_type in {"빙의", "회귀"} and is_regressor is not True:
            fixed = False
            if autofix:
                reg["is_regressor"] = True
                fixed = True
            append_finding(findings, "P0", "REG-001", label, f"regression_type={reg_type!r}인데 is_regressor가 true가 아니다.", fixed=fixed)

        relation_deltas = [item for item in ensure_list(block.get("relationship_delta")) if isinstance(item, dict)]
        if not relation_deltas:
            append_finding(findings, "P1", "REL-000", label, "relationship_delta가 비어 있다.")

        for relation in relation_deltas:
            target = as_text(relation.get("target"))
            before_text = as_text(relation.get("before"))
            after_text = as_text(relation.get("after"))
            if target and target in npc_state:
                expected_before = as_text(npc_state[target]["after"])
                if before_text != expected_before:
                    fixed = False
                    if autofix:
                        relation["before"] = expected_before
                        before_text = expected_before
                        fixed = True
                    append_finding(findings, "P0", "REL-001", label, f"{target} before가 직전 after와 다르다.", fixed=fixed)
            if target and before_text == after_text:
                append_finding(findings, "P1", "REL-002", label, f"{target} 관계가 이번 블록에서 변하지 않았다.")
            if target:
                npc_state[target] = {
                    "last_block": expected_no,
                    "before": before_text,
                    "after": after_text,
                }

        due_items = due_foreshadows.get(expected_no, [])
        callbacks = [as_text(item) for item in ensure_list(block.get("callback")) if as_text(item)]
        if due_items and not callbacks:
            append_finding(findings, "P1", "FS-001", label, "이번 블록에서 회수해야 할 복선이 있는데 callback이 비어 있다.")
        for item in due_items:
            if callbacks and not callback_matches(item["text"], callbacks):
                append_finding(findings, "P1", "FS-002", label, f"지정 회수 복선을 callback에서 찾지 못했다: {truncate(item['text'], 50)}")

        for pattern in BANNED_TEMPLATE_RES:
            for field_path in ["content.context", "content.event_villain", "content.solution", "content.reward"]:
                raw = as_text(get_nested(block, field_path))
                if raw and pattern.search(raw):
                    append_finding(findings, "P1", "TPL-001", label, f"{field_path}에 금지 템플릿이 들어 있다.")
            for item in callbacks:
                if pattern.search(item):
                    append_finding(findings, "P1", "TPL-002", label, "callback에 금지 템플릿이 들어 있다.")
        for item in callbacks:
            if GENERIC_CALLBACK_RE.search(item):
                append_finding(findings, "P1", "CALL-001", label, "callback이 기계식 carry-over 패턴이다.")

        language_values: list[tuple[str, str]] = []
        for path in LANGUAGE_PATHS:
            language_values.append((path, as_text(get_nested(block, path))))
        for idx, item in enumerate(ensure_list(block.get("foreshadow"))):
            language_values.append((f"foreshadow[{idx}]", as_text(item)))
        for idx, item in enumerate(callbacks):
            language_values.append((f"callback[{idx}]", as_text(item)))
        for idx, relation in enumerate(relation_deltas):
            language_values.append((f"relationship_delta[{idx}].before", as_text(relation.get("before"))))
            language_values.append((f"relationship_delta[{idx}].after", as_text(relation.get("after"))))
        for path, raw in language_values:
            if raw and korean_ratio(raw) < 0.8:
                append_finding(findings, "P1", "LANG-001", label, f"{path}의 한국어 비율이 낮다.")

        for path in CODE_PATHS:
            raw = as_text(get_nested(block, path))
            if raw and CODE_TOKEN_RE.search(raw):
                append_finding(findings, "P2", "CODE-001", label, f"{path}에 코드형 값이 들어 있다.")

        beat_type = as_text(get_nested(block, "emotional_beat.type"))
        if beat_type and all_beats and beat_type == all_beats[-1]:
            append_finding(findings, "P1", "BEAT-001", label, f"emotional_beat.type가 직전 블록과 동일하다: {beat_type}")
        if beat_type:
            all_beats.append(beat_type)

        deal_type = as_text(get_nested(block, "genre_ext.deal_type"))
        if deal_type and deal_type in all_deal_types[-2:]:
            append_finding(findings, "P1", "DEAL-001", label, f"deal_type가 최근 3블록 이내에 재등장했다: {deal_type}")
        if deal_type:
            all_deal_types.append(deal_type)

        location = as_text(get_nested(block, "location.place"))
        if location and location in all_locations[-14:]:
            append_finding(findings, "P2", "LOC-001", label, f"location이 최근 15블록 이내에 재등장했다: {location}")
        if location:
            all_locations.append(location)

        leverage = tuple(
            sorted(as_text(item) for item in ensure_list(get_nested(block, "genre_ext.leverage_used")) if as_text(item))
        )
        if leverage:
            leverage_counter[leverage] += 1
            if leverage_counter[leverage] >= 3:
                append_finding(findings, "P1", "LEV-001", label, "leverage_used 동일 세트가 3회 이상 반복되었다.")

        prev_after_raw = as_text(genre.get("capital_after"))
        prev_after_value = capital_to_eok(prev_after_raw)

    deltas = []
    for block in blocks[:batch_size]:
        before = capital_to_eok(get_nested(block, "genre_ext.capital_before"))
        after = capital_to_eok(get_nested(block, "genre_ext.capital_after"))
        if before is not None and after is not None:
            deltas.append(after - before)
    if deltas and all(delta > 0 for delta in deltas):
        append_finding(findings, "P2", "CAP-005", f"{start}-{start + batch_size - 1}", "이번 배치에 패배/하락 블록이 없다.")

    open_after_merge = len(build_open_foreshadow_ledger(history_blocks + blocks[:batch_size]))
    if open_after_merge > LOW_INTELLIGENCE_OPEN_FORESHADOW_LIMIT:
        append_finding(
            findings,
            "P2",
            "FS-003",
            f"{start}-{start + batch_size - 1}",
            f"OPEN 복선이 {open_after_merge}개라서 저지능 모델 관리 한도를 넘는다.",
        )

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

    for severity in ["P0", "P1", "P2"]:
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
        lines.append("- 위반 사항 없음")

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

    prompt = build_prompt(
        draft_blocks=draft_blocks,
        roadmap_blocks=roadmap_blocks,
        meta=meta,
        start=args.start,
        batch_size=args.batch_size,
        mode=args.mode,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(prompt, encoding="utf-8")
    else:
        sys.stdout.write(prompt)
        if not prompt.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def command_check(args: argparse.Namespace) -> int:
    history_blocks = []
    if args.draft and args.draft.exists():
        history_blocks = load_blocks_from_path(args.draft)[: args.start - 1]

    roadmap_blocks = None
    if args.roadmap:
        roadmap_blocks = extract_blocks(read_json(args.roadmap))

    candidate_all = extract_blocks(read_json(args.candidate))
    candidate_blocks = normalize_candidate_slice(candidate_all, args.start, args.batch_size)
    findings, fixed_blocks = validate_candidate(
        candidate_blocks=candidate_blocks,
        history_blocks=history_blocks,
        start=args.start,
        batch_size=args.batch_size,
        roadmap_blocks=roadmap_blocks,
        autofix=args.autofix,
    )

    report = render_report(findings, f"TR Batch Check {args.start}-{args.start + args.batch_size - 1}")
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
        print("draft가 없는데 start가 1이 아니다. 순차 생성만 지원한다.", file=sys.stderr)
        return 2
    if draft_blocks and len(draft_blocks) < args.start - 1:
        print("draft에 필요한 선행 블록이 부족하다.", file=sys.stderr)
        return 2

    roadmap_blocks = None
    if args.roadmap:
        roadmap_blocks = extract_blocks(read_json(args.roadmap))

    candidate_all = extract_blocks(read_json(args.candidate))
    candidate_blocks = normalize_candidate_slice(candidate_all, args.start, args.batch_size)
    findings, fixed_blocks = validate_candidate(
        candidate_blocks=candidate_blocks,
        history_blocks=draft_blocks[: args.start - 1],
        start=args.start,
        batch_size=args.batch_size,
        roadmap_blocks=roadmap_blocks,
        autofix=True,
    )

    report = render_report(findings, f"TR Batch Merge Check {args.start}-{args.start + args.batch_size - 1}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")

    if has_blocking_findings(findings) and not args.force:
        sys.stdout.write(report)
        print("P0/P1 위반이 남아 있어 merge를 중단한다. --force로만 강행 가능.", file=sys.stderr)
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
    parser = argparse.ArgumentParser(description="Batch harness for treatment block production")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prompt_parser = subparsers.add_parser("prompt", help="Generate batch prompt bundle")
    prompt_parser.add_argument("--draft", type=Path, help="Existing treatment draft JSON")
    prompt_parser.add_argument("--roadmap", type=Path, help="Roadmap or BI JSON for titles/context")
    prompt_parser.add_argument("--start", type=int, required=True, help="Start block number (1-based)")
    prompt_parser.add_argument("--batch-size", type=int, default=3, help="Batch size")
    prompt_parser.add_argument("--mode", choices=["flash", "pro", "sonnet"], default="flash", help="Prompt operating mode")
    prompt_parser.add_argument("--output", type=Path, help="Write prompt to file")
    prompt_parser.set_defaults(func=command_prompt)

    check_parser = subparsers.add_parser("check", help="Validate a candidate batch")
    check_parser.add_argument("--candidate", type=Path, required=True, help="Candidate batch JSON or full treatment JSON")
    check_parser.add_argument("--draft", type=Path, help="Existing treatment draft JSON for continuity checks")
    check_parser.add_argument("--roadmap", type=Path, help="Roadmap or BI JSON for title checks")
    check_parser.add_argument("--start", type=int, required=True, help="Start block number (1-based)")
    check_parser.add_argument("--batch-size", type=int, default=3, help="Batch size")
    check_parser.add_argument("--autofix", action="store_true", help="Apply safe continuity autofixes in memory")
    check_parser.add_argument("--fixed-output", type=Path, help="Write autofixed candidate batch JSON")
    check_parser.add_argument("--report", type=Path, help="Write report markdown")
    check_parser.set_defaults(func=command_check)

    merge_parser = subparsers.add_parser("merge", help="Validate and merge a candidate batch into a draft")
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
