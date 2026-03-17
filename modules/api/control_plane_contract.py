"""Shared control-plane contract for public /run and desktop inventory.

Authority path:
    desktop renderer  ->  IPC (bridge:run)  ->  bridge_server /run
      ->  ProcessRunner  ->  main_a.py subprocess

Operator-truth surfaces:
    /status                  — live runner state snapshot (non-authoritative companion)
    /quality/dashboard       — read-only project metrics (non-authoritative companion)
    control-plane-provenance — append-only JSONL audit log (authoritative sink)

Compatibility residue:
    INTERNAL_STAGE0_SUB_KEYS — console-only cancel path, not public /run contract
    INTERNAL_UI_ACTION_KEYS  — exit_app, not routed through bridge
"""

from __future__ import annotations

from typing import Any

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

AUTHORITY_ROLE_AUTHORITATIVE_SINK = "authoritative_sink"
AUTHORITY_ROLE_COMPANION_SNAPSHOT = "companion_snapshot"


CONTROL_PLANE_AUTHORITY_CONTRACT = {
    "public_run_authority_path": [
        "desktop_renderer",
        "ipc_bridge_run",
        "bridge_server_/run",
        "ProcessRunner",
        "main_a.py",
    ],
    "authoritative_sinks": {
        "control_plane_provenance": "logs/control-plane-provenance.jsonl",
        "project_data_db": "{project}/project_data.db",
        "episode_production_log": "{project}/logs/episode_production.jsonl",
    },
    "companion_snapshots": {
        "/status": "live runner state, not durable authority",
        "/quality/dashboard": "read-only aggregation, not durable authority",
        "/quality/summary": "read-only subset, not durable authority",
        "runtime_health": "soft_failures.jsonl digest, not durable authority",
        "proof_status": "derived from sink_alignment + runtime_audit, not durable authority",
        "runtime_audit_summary": "point-in-time snapshot, not durable authority",
    },
    "compatibility_paths": {
        "INTERNAL_STAGE0_SUB_KEYS": "console-only cancel, not part of /run contract",
        "INTERNAL_UI_ACTION_KEYS": "exit_app, not routed through bridge",
    },
}


def get_control_plane_authority_role(surface: str) -> str:
    normalized = str(surface or "").strip()
    if normalized in CONTROL_PLANE_AUTHORITY_CONTRACT["authoritative_sinks"]:
        return AUTHORITY_ROLE_AUTHORITATIVE_SINK
    if normalized in CONTROL_PLANE_AUTHORITY_CONTRACT["companion_snapshots"]:
        return AUTHORITY_ROLE_COMPANION_SNAPSHOT
    return ""


def build_control_plane_authority_summary() -> dict[str, Any]:
    return {
        "public_run_authority_path": list(
            CONTROL_PLANE_AUTHORITY_CONTRACT.get("public_run_authority_path") or []
        ),
        "authoritative_sinks": dict(
            CONTROL_PLANE_AUTHORITY_CONTRACT.get("authoritative_sinks") or {}
        ),
        "companion_snapshots": dict(
            CONTROL_PLANE_AUTHORITY_CONTRACT.get("companion_snapshots") or {}
        ),
        "compatibility_paths": dict(
            CONTROL_PLANE_AUTHORITY_CONTRACT.get("compatibility_paths") or {}
        ),
    }
