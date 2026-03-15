"""Shared helpers for project support assets and style/work contracts."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from modules.core.constants import smart_truncate
from modules.core.genre_guards.work_guard import WorkGuardConfigError, load_work_guard_config

logger = logging.getLogger(__name__)

WORLD_ORIGIN_OPTIONS = ("현대인", "원시인")
INCARNATION_TYPE_OPTIONS = ("회귀자", "빙의자", "환생자", "일반")
POV_OPTIONS = ("1인칭", "3인칭", "전지적", "혼합")
EXTERNAL_POV_INSERT_POLICY_OPTIONS = ("금지", "제한적 허용", "적극 허용")


def resolve_indexed_menu_choice(
    options: tuple[str, ...] | list[str],
    raw_choice: str = "",
    *,
    default: str,
) -> str:
    normalized = str(raw_choice or "").strip()
    if not normalized:
        return default

    try:
        index = int(normalized) - 1
    except ValueError:
        return default

    if 0 <= index < len(options):
        return str(options[index])
    return default


def default_external_pov_insert_policy(primary_pov: str = "", *, genre: str = "") -> str:
    normalized_pov = str(primary_pov or "").strip()
    normalized_genre = str(genre or "").strip().lower()

    if normalized_genre in {"investment", "투자물"}:
        return "제한적 허용"
    if normalized_pov == "1인칭":
        return "금지"
    if normalized_pov == "3인칭":
        return "제한적 허용"
    if normalized_pov in {"전지적", "혼합"}:
        return "적극 허용"
    return "제한적 허용"


def normalize_external_pov_insert_policy(value: str = "", *, primary_pov: str = "", genre: str = "") -> str:
    normalized = str(value or "").strip()
    aliases = {
        "없음": "금지",
        "불가": "금지",
        "허용 안 함": "금지",
        "허용": "제한적 허용",
        "부분 허용": "제한적 허용",
        "제한 허용": "제한적 허용",
        "제한적": "제한적 허용",
        "자유 허용": "적극 허용",
        "자유": "적극 허용",
        "적극": "적극 허용",
    }
    resolved = aliases.get(normalized, normalized)
    if resolved in EXTERNAL_POV_INSERT_POLICY_OPTIONS:
        return resolved
    return default_external_pov_insert_policy(primary_pov, genre=genre)


def resolve_external_pov_insert_policy_choice(
    raw_choice: str = "",
    *,
    primary_pov: str = "",
    genre: str = "",
) -> str:
    default_policy = default_external_pov_insert_policy(primary_pov, genre=genre)
    selected = resolve_indexed_menu_choice(
        EXTERNAL_POV_INSERT_POLICY_OPTIONS,
        raw_choice,
        default=default_policy,
    )
    return normalize_external_pov_insert_policy(
        selected,
        primary_pov=primary_pov,
        genre=genre,
    )


def load_style_guide_anchor(project) -> dict[str, Any]:
    if project is None:
        return {}

    try:
        loader = getattr(project, "load_v20_anchor", None)
        raw_style = loader("style_guide") if callable(loader) else None
    except Exception as exc:
        logger.debug("style_guide anchor load failed: %s", exc)
        return {}

    return raw_style if isinstance(raw_style, dict) else {}


def resolve_project_bible_pov(project) -> str:
    if project is None:
        return ""

    try:
        master_bible = getattr(project, "master_bible", None)
    except Exception:
        master_bible = None

    if not isinstance(master_bible, dict):
        return ""

    bible_root = master_bible.get("MasterBible", master_bible)
    if not isinstance(bible_root, dict):
        return ""

    protagonist_config = bible_root.get("protagonist_config", {})
    if not isinstance(protagonist_config, dict):
        return ""

    return str(protagonist_config.get("pov", "") or "").strip()


def resolve_project_external_pov_insert_policy(project) -> str:
    if project is None:
        return ""

    try:
        master_bible = getattr(project, "master_bible", None)
    except Exception:
        master_bible = None

    if not isinstance(master_bible, dict):
        return ""

    bible_root = master_bible.get("MasterBible", master_bible)
    if not isinstance(bible_root, dict):
        return ""

    protagonist_config = bible_root.get("protagonist_config", {})
    if not isinstance(protagonist_config, dict):
        return ""

    raw_policy = str(protagonist_config.get("external_pov_insert_policy", "") or "").strip()
    if not raw_policy:
        return ""

    primary_pov = str(protagonist_config.get("pov", "") or "").strip()
    return normalize_external_pov_insert_policy(raw_policy, primary_pov=primary_pov)


def resolve_project_pov_contract(project) -> dict[str, str]:
    style_data = load_style_guide_anchor(project)
    primary_pov = resolve_project_bible_pov(project)
    selected_primary_pov = str(style_data.get("selected_primary_pov", "") or "").strip() or primary_pov
    extracted_pov = str(style_data.get("extracted_pov", "") or "").strip() or str(style_data.get("pov", "") or "").strip()
    effective_pov = (
        str(style_data.get("effective_primary_pov", "") or "").strip()
        or selected_primary_pov
        or extracted_pov
    )
    external_policy = normalize_external_pov_insert_policy(
        str(style_data.get("external_pov_insert_policy", "") or "").strip()
        or resolve_project_external_pov_insert_policy(project),
        primary_pov=selected_primary_pov or effective_pov,
    )
    return {
        "primary_pov": primary_pov,
        "selected_primary_pov": selected_primary_pov,
        "style_guide_extracted_pov": extracted_pov,
        "effective_pov": effective_pov,
        "external_pov_insert_policy": external_policy,
    }


def build_style_guide_summary(
    project,
    *,
    heading: str,
    max_chars: int,
    include_dialogue_ratio: bool = False,
    secondary_style_key: str = "",
    secondary_style_label: str = "",
    anti_ai_limit: int = 5,
    forbidden_limit: int = 5,
) -> str:
    style_data = load_style_guide_anchor(project)
    pov_contract = resolve_project_pov_contract(project)

    tone = str(style_data.get("tone", "") or "").strip()
    pov = pov_contract.get("effective_pov", "")
    external_policy = pov_contract.get("external_pov_insert_policy", "")
    sentence_length = str(style_data.get("sentence_length", "") or "").strip()
    dialogue_ratio = style_data.get("dialogue_ratio")
    secondary_style = str(style_data.get(secondary_style_key, "") or "").strip() if secondary_style_key else ""
    anti_ai_patterns = [str(item).strip() for item in (style_data.get("anti_ai_patterns") or []) if str(item).strip()]
    forbidden_expr = [
        str(item).strip() for item in (style_data.get("forbidden_expressions") or []) if str(item).strip()
    ]

    if not any([tone, pov, external_policy, sentence_length, secondary_style, anti_ai_patterns, forbidden_expr]):
        return ""

    core_bits: list[str] = []
    if tone:
        core_bits.append(f"톤={tone}")
    if pov:
        core_bits.append(f"시점={pov}")
    if external_policy:
        core_bits.append(f"타자 시점 삽입={external_policy}")
    if include_dialogue_ratio and isinstance(dialogue_ratio, (int, float)):
        core_bits.append(f"대화 비율={dialogue_ratio:.0%}")
    if sentence_length:
        core_bits.append(f"문장 길이={sentence_length}")
    if secondary_style and secondary_style_label:
        core_bits.append(f"{secondary_style_label}={secondary_style}")

    lines = [heading]
    if core_bits:
        lines.append("- " + ", ".join(core_bits))
    if anti_ai_patterns:
        lines.append("- anti-AI 금지: " + ", ".join(anti_ai_patterns[:anti_ai_limit]))
    if forbidden_expr:
        lines.append("- 금지 표현: " + ", ".join(forbidden_expr[:forbidden_limit]))

    text = "\n".join(lines).strip()
    return smart_truncate(text, max_chars=max_chars, head_chars=max_chars // 2)


def load_work_guard_summary(project_dir: Path) -> dict[str, Any]:
    payload = {
        "work_guard_exists": False,
        "work_guard_valid": True,
        "work_guard_error": "",
        "work_type": "",
        "tracking_slots": 0,
        "registry_profiles": 0,
        "role_fit_constraints": 0,
    }
    work_guard_path = project_dir / "config" / "work_guard.yaml"
    if not work_guard_path.exists():
        return payload

    payload["work_guard_exists"] = True
    try:
        data = load_work_guard_config(work_guard_path)
    except WorkGuardConfigError as exc:
        payload["work_guard_valid"] = False
        payload["work_guard_error"] = str(exc)
        logger.debug("work_guard load failed for %s: %s", work_guard_path, exc)
        return payload
    except Exception as exc:
        payload["work_guard_valid"] = False
        payload["work_guard_error"] = f"{work_guard_path}: unexpected load failure ({exc.__class__.__name__})"
        logger.debug("work_guard load failed for %s: %s", work_guard_path, exc)
        return payload

    work_identity = data.get("work_identity", data) if isinstance(data, dict) else {}
    if isinstance(work_identity, dict):
        payload["work_type"] = str(work_identity.get("work_type", "") or "").strip()
        for key in ("tracking_slots", "registry_profiles", "role_fit_constraints"):
            value = work_identity.get(key) or []
            if isinstance(value, list):
                payload[key] = len(value)
    return payload


def inspect_project_support_assets(project_dir: Path) -> dict[str, dict[str, Any]]:
    config_dir = project_dir / "config"
    stage0_dir = project_dir / "stage0_output"

    author_directives = config_dir / "author_directives.txt"
    work_guard = config_dir / "work_guard.yaml"
    style_guide = stage0_dir / "style_guide.json"

    style_payload: dict[str, Any] = {}
    if style_guide.exists():
        try:
            parsed = json.loads(style_guide.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                style_payload = parsed
        except Exception as exc:
            logger.debug("style_guide file load failed for %s: %s", style_guide, exc)

    work_guard_summary = load_work_guard_summary(project_dir)
    author_ready = author_directives.exists() and author_directives.stat().st_size > 0
    style_ready = style_guide.exists()
    effective_pov = str(style_payload.get("effective_primary_pov", "") or "").strip() or str(
        style_payload.get("pov", "") or ""
    ).strip()
    extracted_pov = str(style_payload.get("extracted_pov", "") or "").strip()
    external_policy = normalize_external_pov_insert_policy(
        str(style_payload.get("external_pov_insert_policy", "") or "").strip(),
        primary_pov=str(style_payload.get("selected_primary_pov", "") or effective_pov),
    )

    return {
        "author_directives": {
            "path": author_directives,
            "exists": author_directives.exists(),
            "ready": author_ready,
            "size_bytes": author_directives.stat().st_size if author_directives.exists() else 0,
        },
        "work_guard": {
            "path": work_guard,
            "exists": work_guard.exists(),
            "ready": work_guard.exists()
            and work_guard.stat().st_size > 0
            and bool(work_guard_summary.get("work_guard_valid", True)),
            **work_guard_summary,
        },
        "style_guide": {
            "path": style_guide,
            "exists": style_guide.exists(),
            "ready": style_ready,
            "tone": str(style_payload.get("tone", "") or "").strip(),
            "pov": str(style_payload.get("pov", "") or "").strip(),
            "extracted_pov": extracted_pov,
            "effective_pov": effective_pov,
            "external_pov_insert_policy": external_policy,
        },
    }
