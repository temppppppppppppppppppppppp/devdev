"""Prompt wrapper API for Analyst with PromptLoader fallback."""

import logging

from modules.core.prompt_loader import PromptLoader

from . import analyst_prompts as legacy

_PROMPT_LOADER = PromptLoader()


def _load_prompt(key: str, fallback: str, **kwargs) -> str:
    loaded = _PROMPT_LOADER.load("analyst", key, **kwargs)
    if loaded is not None:
        return loaded
    if not kwargs:
        return fallback
    try:

        class _SafeDict(dict):
            def __missing__(self, k):
                return "{" + k + "}"

        return fallback.format_map(_SafeDict(**kwargs))
    except Exception:
        return fallback


def get_post_stitch_repair_prompt(*, arc_a_joint: str, arc_b_joint: str) -> str:
    return _load_prompt(
        "POST_STITCH_REPAIR_PROMPT",
        legacy.POST_STITCH_REPAIR_PROMPT,
        arc_a_joint=arc_a_joint,
        arc_b_joint=arc_b_joint,
    )


def get_enrich_block_prompt_v30(**kwargs) -> str:
    return _load_prompt("ENRICH_BLOCK_PROMPT_V30", legacy.ENRICH_BLOCK_PROMPT_V30, **kwargs)


def get_plan_volume_prompt_v25(**kwargs) -> str:
    return _load_prompt("PLAN_VOLUME_PROMPT_V25", legacy.PLAN_VOLUME_PROMPT_V25, **kwargs)


def get_plan_arc_prompt_v25(**kwargs) -> str:
    # Return raw template to avoid brace-collapse across multi-pass formatting.
    raw = _PROMPT_LOADER.get_raw("analyst", "PLAN_ARC_PROMPT_V25")
    if raw is not None:
        return raw

    if not kwargs:
        return legacy.PLAN_ARC_PROMPT_V25
    try:

        class _SafeDict(dict):
            def __missing__(self, k):
                return "{" + k + "}"

        return legacy.PLAN_ARC_PROMPT_V25.format_map(_SafeDict(**kwargs))
    except Exception:
        return legacy.PLAN_ARC_PROMPT_V25


def get_analyst_self_critic_prompt() -> str:
    return _load_prompt("ANALYST_SELF_CRITIC_PROMPT", legacy.ANALYST_SELF_CRITIC_PROMPT)


def get_recovery_prompt() -> str:
    # [TF7-P2-10] YAML 외부화 완결 — fallback 본문 제거, YAML 미존재 시 경고
    prompt = _PROMPT_LOADER.load("analyst", "RECOVERY_PROMPT")
    if prompt is not None:
        return prompt
    logging.warning("[PromptLoader] RECOVERY_PROMPT not found in analyst.yaml — returning empty string")
    return ""


def get_volume_strategy_prompt() -> str:
    # [TF7-P2-10] YAML 외부화 완결 — fallback 본문 제거, YAML 미존재 시 경고
    prompt = _PROMPT_LOADER.load("analyst", "VOLUME_STRATEGY_PROMPT")
    if prompt is not None:
        return prompt
    logging.warning("[PromptLoader] VOLUME_STRATEGY_PROMPT not found in analyst.yaml — returning empty string")
    return ""


def get_surgery_prompt(*, prev_arc_json: str, curr_arc_json: str, next_arc_json: str, feedback: str) -> str:
    return legacy.get_surgery_prompt(
        prev_arc_json=prev_arc_json,
        curr_arc_json=curr_arc_json,
        next_arc_json=next_arc_json,
        feedback=feedback,
    )


def get_calibration_prompt(*, calibration_msg: str, current_hud_json: str, arc_tactical: str) -> str:
    return legacy.get_calibration_prompt(
        calibration_msg=calibration_msg,
        current_hud_json=current_hud_json,
        arc_tactical=arc_tactical,
    )
