from __future__ import annotations

from typing import Any


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        cleaned = as_text(item)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        out.append(cleaned)
    return out


def resolve_phase0_work_identity_surface(phase0_payload: dict[str, Any]) -> dict[str, Any]:
    project = phase0_payload.get("project") if isinstance(phase0_payload.get("project"), dict) else {}
    direct_surface = phase0_payload.get("work_identity_surface")
    if not isinstance(direct_surface, dict):
        direct_surface = {}

    planning_surface: dict[str, Any] = {}
    phase0_design = phase0_payload.get("phase0_design")
    if isinstance(phase0_design, dict):
        planning_seed_authority = phase0_design.get("planning_seed_authority")
        if isinstance(planning_seed_authority, dict):
            candidate = planning_seed_authority.get("work_identity_surface")
            if isinstance(candidate, dict):
                planning_surface = candidate

    work_identity_surface = direct_surface or planning_surface
    project_title_ko = as_text(project.get("title_ko"))
    project_title = as_text(project.get("title"))
    canonical_title = (
        as_text(work_identity_surface.get("title"))
        or project_title_ko
        or project_title
    )
    commercial_label = as_text(work_identity_surface.get("commercial_label"))
    slug_aliases_raw = work_identity_surface.get("slug_aliases")
    slug_aliases = unique_preserve_order(slug_aliases_raw if isinstance(slug_aliases_raw, list) else [])
    allowed_titles = unique_preserve_order(
        [canonical_title, commercial_label, *slug_aliases, project_title_ko, project_title]
    )
    resolution = (
        "phase0.work_identity_surface"
        if as_text(work_identity_surface.get("title"))
        else "phase0.project.title_ko/title"
    )
    return {
        "canonical_title": canonical_title,
        "commercial_label": commercial_label,
        "slug_aliases": [alias for alias in slug_aliases if alias != canonical_title],
        "allowed_titles": allowed_titles,
        "resolution": resolution,
    }
