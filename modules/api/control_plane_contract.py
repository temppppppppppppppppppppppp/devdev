"""Shared control-plane contract for public /run and desktop inventory."""

from __future__ import annotations

PUBLIC_RUN_KEYS: frozenset[str] = frozenset(
    {"0", "1", "2", "3", "4", "6", "7", "44", "77", "88", "99"}
)
KEYS_REQUIRING_SUB_KEY: frozenset[str] = frozenset({"0"})
PUBLIC_STAGE0_SUB_KEYS: frozenset[str] = frozenset({"1", "2", "3", "4", "5", "6", "7"})
# Stage 0 sub_key=0 remains a console-only cancel path in main_a.py, but it is
# not part of the public /run or desktop-renderer contract.
INTERNAL_STAGE0_SUB_KEYS: dict[str, str] = {"0": "cancel_stage0"}
ALLOWED_STAGE0_SUB_KEYS: frozenset[str] = PUBLIC_STAGE0_SUB_KEYS
RISK_KEYS: frozenset[str] = frozenset({"44", "77", "88", "99"})
INTERNAL_UI_ACTION_KEYS: dict[str, str] = {"5": "exit_app"}

# All public /run keys take the interactive runner path. Stage 0 still uses sub_key
# prompts, and safe-op keys continue to use Mode B for brokered confirmation flow.
MODE_B_KEYS: frozenset[str] = PUBLIC_RUN_KEYS
