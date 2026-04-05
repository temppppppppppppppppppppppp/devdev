"""Stage2 entity naming canonicalization helpers."""

from __future__ import annotations

import re
from copy import deepcopy


def _iter_registry_names(entity_registry: object) -> list[str]:
    if not isinstance(entity_registry, dict):
        return []

    names: list[str] = []
    for key in ("characters", "organizations", "locations", "objects", "concepts"):
        items = entity_registry.get(key, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                name = item.get("name") or item.get("canonical_name") or ""
            else:
                name = str(item or "")
            name = re.sub(r"\s+", " ", str(name).strip())
            if name and name not in names:
                names.append(name)
    return names


def _add_whitespace_variants(name: str, aliases: set[str]) -> None:
    squashed = re.sub(r"\s+", "", name)
    if squashed and squashed != name:
        aliases.add(squashed)


def _build_location_aliases(name: str, aliases: set[str]) -> None:
    location_terms = ("임시 오피스텔", "오피스텔", "오피스", "사무실", "집무실")
    if not any(term in name for term in location_terms):
        return

    base = name
    for term in location_terms:
        base = base.replace(term, "")
    base = re.sub(r"\s+", " ", base).strip(" ,")
    if not base:
        return

    for suffix in location_terms:
        aliases.add(f"{base} {suffix}".strip())
        aliases.add(f"{re.sub(r'\s+', '', base)} {suffix}".strip())
        aliases.add(f"{re.sub(r'\s+', '', base)}{suffix}".strip())


def _build_object_aliases(name: str, aliases: set[str]) -> None:
    if "개인용 PDA 단말기" in name:
        aliases.update({"PDA 단말기", "개인용 PDA", "PDA"})

    if "WTI 원유 선물 6월물" in name:
        aliases.update({"WTI 원유 6월물", "WTI 선물 6월물", "WTI 6월물"})
    elif "WTI 원유 선물" in name:
        aliases.update({"WTI 선물", "WTI 원유"})

    if "금(XAU/USD)" in name and "가격 차트" in name:
        aliases.update(
            {
                "금(XAU/USD) 가격 차트",
                "금(XAU/USD) 시세 차트",
                "금 가격 차트",
                "금 시세 차트",
            }
        )


def build_stage2_entity_alias_map(entity_registry: object) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for canonical in _iter_registry_names(entity_registry):
        aliases = {canonical}
        _add_whitespace_variants(canonical, aliases)
        _build_location_aliases(canonical, aliases)
        _build_object_aliases(canonical, aliases)
        for alias in aliases:
            alias = re.sub(r"\s+", " ", alias.strip())
            if alias and alias != canonical:
                alias_map[alias] = canonical
    return alias_map


def normalize_stage2_entity_text(text: object, entity_registry: object) -> str:
    raw_text = str(text or "")
    if not raw_text:
        return raw_text

    alias_map = build_stage2_entity_alias_map(entity_registry)
    if not alias_map:
        return raw_text

    placeholder_map: dict[str, str] = {}
    normalized = raw_text
    all_canonicals = list(dict.fromkeys(alias_map.values()))
    for idx, canonical in enumerate(sorted(all_canonicals, key=len, reverse=True)):
        placeholder = f"__S2_CANON_{idx}__"
        normalized = normalized.replace(canonical, placeholder)
        placeholder_map[placeholder] = canonical

    for alias, canonical in sorted(alias_map.items(), key=lambda item: len(item[0]), reverse=True):
        placeholder = next(
            (key for key, value in placeholder_map.items() if value == canonical),
            None,
        )
        if placeholder:
            normalized = normalized.replace(alias, placeholder)

    for placeholder, canonical in placeholder_map.items():
        normalized = normalized.replace(placeholder, canonical)
    return normalized


def normalize_stage2_entity_value(value: object, entity_registry: object) -> object:
    if isinstance(value, str):
        return normalize_stage2_entity_text(value, entity_registry)
    if isinstance(value, list):
        return [normalize_stage2_entity_value(item, entity_registry) for item in value]
    if isinstance(value, dict):
        normalized = deepcopy(value)
        for key, item in list(normalized.items()):
            normalized[key] = normalize_stage2_entity_value(item, entity_registry)
        return normalized
    return value


def normalize_stage2_arc_entity_contract(arc: dict, entity_registry: object) -> tuple[dict, bool]:
    if not isinstance(arc, dict) or not entity_registry:
        return arc, False

    normalized = deepcopy(arc)
    changed = False

    def _apply(path: list[str]) -> None:
        nonlocal changed
        cursor = normalized
        for key in path[:-1]:
            if not isinstance(cursor, dict):
                return
            cursor = cursor.get(key)
        if not isinstance(cursor, dict):
            return
        leaf = path[-1]
        if leaf not in cursor:
            return
        current = cursor.get(leaf)
        updated = normalize_stage2_entity_value(current, entity_registry)
        if updated != current:
            cursor[leaf] = updated
            changed = True

    for path in (
        ["tactical_doc"],
        ["joint_docs", "final_location"],
        ["joint_docs", "physical_inventory"],
        ["state_constraints", "arc_start_state", "location"],
        ["state_constraints", "arc_start_state", "equipment"],
        ["state_constraints", "arc_start_state", "portfolio_position"],
        ["state_constraints", "arc_end_state", "location"],
        ["state_constraints", "arc_end_state", "equipment"],
        ["state_constraints", "arc_end_state", "portfolio_position"],
        ["state_constraints", "protagonist_items"],
        ["state_constraints", "items_acquired"],
        ["episode_details"],
    ):
        _apply(path)

    return normalized, changed
