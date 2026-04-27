"""Automated Frontier Lag N-arc harness with terminal-owned watchdog."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main_a import SovereignApp  # noqa: E402
from modules.core.continuity_canary import read_continuity_canary_report  # noqa: E402
from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.failure_analyzer import FailureAnalyzer  # noqa: E402
from modules.core.pass_rate_monitor import PassRateMonitor  # noqa: E402
from modules.core.project_support import (  # noqa: E402
    EXTERNAL_POV_INSERT_POLICY_OPTIONS,
    INCARNATION_TYPE_OPTIONS,
    POV_OPTIONS,
    WORLD_ORIGIN_OPTIONS,
)

DEFAULT_SEED_PROFILE = "00_20260314"
DEFAULT_BIBLE_FILE = "0_bi_golden_canary_deepclone_probe_a_fullblock_v1.json"
DEFAULT_ROADMAP_FILE = "golden_canary_deepclone_probe_a_fullblock_v1_tr_block_070_draft.json"
DEFAULT_BATCH_SIZE = 1
DEFAULT_POLL_INTERVAL_SECONDS = 30 * 60
PROCESS_CHECK_INTERVAL_SECONDS = 5
DEFAULT_STALL_IDLE_WINDOWS = 2
ACTIVE_FRONTIER_STALL_IDLE_WINDOWS = 10
DEFAULT_OPERATIONAL_ATTEMPT_CAP = 5
DEFAULT_MAX_RUNTIME_SECONDS = 0
DEFAULT_MAX_TOTAL_TOKENS = 0
DEFAULT_MAX_TOTAL_COST_USD = 0.0
DEFAULT_MAX_PROJECT_BYTES = 0
DEFAULT_STAGE3_FAILURE_POLICY = "strict"
STAGE3_FAILURE_POLICIES = ("strict", "skip", "quarantine")
SUCCESS_STAGE_VERDICTS = ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING")
MANUAL_PROFILE_DOC = "docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md"
HARNESS_SSOT_DOC = "docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md"
PROMPT_WAIT_MARKERS = (
    "건너뛰고 다음 Arc로?",
    "계속하시겠습니까?",
    "[Enter] 메뉴로 돌아가기",
    "👉 Choice",
    "선택 (기본:",
)
ATTEMPT_OVERFLOW_PATTERNS = (
    ("stage2", re.compile(r"\[Stage 2\].*?attempt\s+(\d+)/(\d+)", re.IGNORECASE)),
    ("stage3", re.compile(r"\[Retry\s+(\d+)/(\d+)\]", re.IGNORECASE)),
    ("stage4", re.compile(r"\[Round\s+(\d+)/(\d+)\]", re.IGNORECASE)),
)
FATAL_TAIL_MARKERS = (
    "Traceback (most recent call last)",
    "crash_dump.log",
    "AUTO_FRONTIER_LAG_FATAL",
)
PROVIDER_RESPONSE_WAIT_STARTED_MARKER = "receive_response_headers.started"
PROVIDER_RESPONSE_WAIT_END_MARKERS = (
    "receive_response_headers.complete",
    "HTTP Request:",
    "response_closed.complete",
)
ACTIVE_FRONTIER_WAIT_MARKERS = (
    "[Preflight] 병렬 분석 시작",
    "[Preflight] arc_drive 완료",
    "[Stage 2] Arc",
    "전술 설계 중",
)


@dataclass(slots=True)
class HarnessProfile:
    seed_profile: str
    genre_type: str
    genre_name: str
    bible_file: str
    roadmap_file: str
    treatment_auto_condense: str
    protagonist_config: dict[str, str]
    style_analysis_mode: str
    style_analysis_confirm: str


def default_profile(seed_profile: str = DEFAULT_SEED_PROFILE) -> HarnessProfile:
    return HarnessProfile(
        seed_profile=seed_profile,
        genre_type="investment",
        genre_name="투자 (Investment Fiction)",
        bible_file=DEFAULT_BIBLE_FILE,
        roadmap_file=DEFAULT_ROADMAP_FILE,
        treatment_auto_condense="n",
        protagonist_config={
            "world_origin": "원시인",
            "incarnation_type": "회귀자",
            "pov": "혼합",
            "external_pov_insert_policy": "적극 허용",
        },
        style_analysis_mode="use",
        style_analysis_confirm="y",
    )


KNOWN_SOAK_PROFILES = ("soak",)

# Heavy-path toggle keys with their application points.
# False = skip the path during soak runs.
HEAVY_PATH_TOGGLE_REGISTRY: dict[str, str] = {
    "post_pass_advisories": "Stage4PostPassRuntime._run_post_pass_advisories",
}


@dataclass(slots=True)
class SoakProfile:
    """Harness-local override contract for bounded soak canary runs.

    All fields are optional — ``None`` means "keep production default".
    ``heavy_path_toggles`` maps toggle names from HEAVY_PATH_TOGGLE_REGISTRY
    to booleans: ``True`` = run as normal, ``False`` = skip.
    """

    stage2_model: str | None = None
    stage4_model: str | None = None
    manuscript_min_length: int | None = None
    manuscript_target_length: int | None = None
    heavy_path_toggles: dict[str, bool] = field(default_factory=dict)


def default_soak_profile() -> SoakProfile:
    """Return a standard soak profile: effective flash models, reduced lengths.

    The model is resolved through the runtime models config instead of the
    inline default so high-rigor runs can pin Gemini to a stricter floor via
    ``GEULDOBI_FORCE_GOOGLE_MODEL`` without the soak profile silently downgrading.
    """
    from modules.core.models_config import DEFAULT_FLASH_MODEL, load_model_name

    effective_flash_model = load_model_name(
        section="role_constants",
        key="flash_main",
        fallback=DEFAULT_FLASH_MODEL,
    )

    return SoakProfile(
        stage2_model=effective_flash_model,
        stage4_model=effective_flash_model,
        manuscript_min_length=1000,
        manuscript_target_length=1500,
        heavy_path_toggles={"post_pass_advisories": False},
    )


def resolve_soak_profile(name: str | None) -> SoakProfile | None:
    """Resolve a named soak profile.  Returns ``None`` if *name* is falsy."""
    if not name:
        return None
    if name == "soak":
        return default_soak_profile()
    raise ValueError(f"unknown soak profile: {name!r}  (known: {KNOWN_SOAK_PROFILES})")


@contextlib.contextmanager
def apply_soak_overrides(soak: SoakProfile | None):
    """Temporarily patch global constants for the lifetime of a soak run.

    Restores every patched value on exit so global state is never polluted.
    When *soak* is ``None``, yields immediately with no side effects.
    """
    if soak is None:
        yield
        return

    from modules.core.constants import AIModels, ManuscriptLimits

    originals: dict[str, Any] = {}
    mock_patches: list[Any] = []

    try:
        # ── Model tier overrides ──────────────────────────────────────
        if soak.stage2_model is not None:
            originals["s2_model"] = AIModels.STAGE2_MAIN_MODEL
            AIModels.STAGE2_MAIN_MODEL = soak.stage2_model
        if soak.stage4_model is not None:
            originals["s4_model"] = AIModels.STAGE4_FIXED_WRITER_MODEL
            AIModels.STAGE4_FIXED_WRITER_MODEL = soak.stage4_model

        # ── Manuscript length overrides ───────────────────────────────
        # Force lazy evaluation so the cache attrs exist, then override.
        if soak.manuscript_min_length is not None:
            _ = int(ManuscriptLimits.MIN_LENGTH)
            originals["min_len"] = ManuscriptLimits._lazy_MIN_LENGTH  # noqa: SLF001
            ManuscriptLimits._lazy_MIN_LENGTH = soak.manuscript_min_length  # noqa: SLF001
        if soak.manuscript_target_length is not None:
            _ = int(ManuscriptLimits.TARGET_LENGTH)
            originals["target_len"] = ManuscriptLimits._lazy_TARGET_LENGTH  # noqa: SLF001
            ManuscriptLimits._lazy_TARGET_LENGTH = soak.manuscript_target_length  # noqa: SLF001

        # ── Heavy-path toggle set ─────────────────────────────────────
        for toggle_name, enabled in soak.heavy_path_toggles.items():
            if toggle_name not in HEAVY_PATH_TOGGLE_REGISTRY:
                raise ValueError(f"unknown heavy-path toggle: {toggle_name!r}")
            if not enabled and toggle_name == "post_pass_advisories":
                from modules.core.stage4_post_pass_runtime import Stage4PostPassRuntime

                p = patch.object(
                    Stage4PostPassRuntime,
                    "_run_post_pass_advisories",
                    lambda self, **_kw: None,
                )
                p.start()
                mock_patches.append(p)

        yield
    finally:
        # Reverse order: patches first, then constants.
        for p in reversed(mock_patches):
            p.stop()
        if "s2_model" in originals:
            AIModels.STAGE2_MAIN_MODEL = originals["s2_model"]
        if "s4_model" in originals:
            AIModels.STAGE4_FIXED_WRITER_MODEL = originals["s4_model"]
        if "min_len" in originals:
            ManuscriptLimits._lazy_MIN_LENGTH = originals["min_len"]  # noqa: SLF001
        if "target_len" in originals:
            ManuscriptLimits._lazy_TARGET_LENGTH = originals["target_len"]  # noqa: SLF001


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto Frontier-Lag N-arc harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="render a resolved harness execution plan")
    plan.add_argument("--arc-count", type=int)
    plan.add_argument("--trigger", default="")
    plan.add_argument("--seed-profile", default=DEFAULT_SEED_PROFILE)
    plan.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    plan.add_argument("--target-project", default="")
    plan.add_argument("--reuse-existing-project", action="store_true")
    plan.add_argument("--reuse-reset-after-ep", type=int)
    plan.add_argument("--operational-attempt-cap", type=int, default=DEFAULT_OPERATIONAL_ATTEMPT_CAP)
    plan.add_argument("--max-runtime-seconds", type=int, default=DEFAULT_MAX_RUNTIME_SECONDS)
    plan.add_argument("--max-total-tokens", type=int, default=DEFAULT_MAX_TOTAL_TOKENS)
    plan.add_argument("--max-total-cost-usd", type=float, default=DEFAULT_MAX_TOTAL_COST_USD)
    plan.add_argument("--max-project-bytes", type=int, default=DEFAULT_MAX_PROJECT_BYTES)
    plan.add_argument("--soak-profile", default="", help="named soak profile (e.g. 'soak')")
    plan.add_argument("--stage3-failure-policy", choices=STAGE3_FAILURE_POLICIES, default=DEFAULT_STAGE3_FAILURE_POLICY)

    worker = subparsers.add_parser("worker", help="internal worker that boots app and runs the pipeline")
    worker.add_argument("--target-project", required=True)
    worker.add_argument("--arc-count", type=int, required=True)
    worker.add_argument("--seed-profile", default=DEFAULT_SEED_PROFILE)
    worker.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    worker.add_argument("--reuse-existing-project", action="store_true")
    worker.add_argument("--reuse-reset-after-ep", type=int)
    worker.add_argument("--soak-profile", default="", help="named soak profile (e.g. 'soak')")
    worker.add_argument(
        "--stage3-failure-policy", choices=STAGE3_FAILURE_POLICIES, default=DEFAULT_STAGE3_FAILURE_POLICY
    )
    worker.add_argument("--run-id", default="")

    run = subparsers.add_parser("run", help="spawn worker, watchdog it, analyze outputs, write SSOT")
    run.add_argument("--arc-count", type=int)
    run.add_argument("--trigger", default="")
    run.add_argument("--seed-profile", default=DEFAULT_SEED_PROFILE)
    run.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    run.add_argument("--poll-interval-seconds", type=int, default=DEFAULT_POLL_INTERVAL_SECONDS)
    run.add_argument("--target-project", default="")
    run.add_argument("--reuse-existing-project", action="store_true")
    run.add_argument("--reuse-reset-after-ep", type=int)
    run.add_argument("--operational-attempt-cap", type=int, default=DEFAULT_OPERATIONAL_ATTEMPT_CAP)
    run.add_argument("--max-runtime-seconds", type=int, default=DEFAULT_MAX_RUNTIME_SECONDS)
    run.add_argument("--max-total-tokens", type=int, default=DEFAULT_MAX_TOTAL_TOKENS)
    run.add_argument("--max-total-cost-usd", type=float, default=DEFAULT_MAX_TOTAL_COST_USD)
    run.add_argument("--max-project-bytes", type=int, default=DEFAULT_MAX_PROJECT_BYTES)
    run.add_argument("--soak-profile", default="", help="named soak profile (e.g. 'soak')")
    run.add_argument("--stage3-failure-policy", choices=STAGE3_FAILURE_POLICIES, default=DEFAULT_STAGE3_FAILURE_POLICY)

    analyze = subparsers.add_parser("analyze", help="analyze an existing harness run and write SSOT")
    analyze.add_argument("--project", required=True)
    analyze.add_argument("--arc-count", type=int)

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    soak = resolve_soak_profile(getattr(args, "soak_profile", "") or "")

    if args.command == "plan":
        payload = build_execution_plan(
            arc_count=resolve_arc_count(args.arc_count, args.trigger),
            seed_profile=args.seed_profile,
            batch_size=args.batch_size,
            target_project=args.target_project or "",
            trigger=args.trigger,
            reuse_existing_project=bool(getattr(args, "reuse_existing_project", False)),
            reuse_reset_after_ep=getattr(args, "reuse_reset_after_ep", None),
            operational_attempt_cap=max(
                1, int(getattr(args, "operational_attempt_cap", DEFAULT_OPERATIONAL_ATTEMPT_CAP))
            ),
            max_runtime_seconds=max(0, int(getattr(args, "max_runtime_seconds", DEFAULT_MAX_RUNTIME_SECONDS) or 0)),
            max_total_tokens=max(0, int(getattr(args, "max_total_tokens", DEFAULT_MAX_TOTAL_TOKENS) or 0)),
            max_total_cost_usd=max(0.0, float(getattr(args, "max_total_cost_usd", DEFAULT_MAX_TOTAL_COST_USD) or 0.0)),
            max_project_bytes=max(0, int(getattr(args, "max_project_bytes", DEFAULT_MAX_PROJECT_BYTES) or 0)),
            soak_profile=soak,
            stage3_failure_policy=args.stage3_failure_policy,
        )
        _print_json(payload)
        return 0

    if args.command == "worker":
        payload = run_worker(
            target_project=args.target_project,
            arc_count=int(args.arc_count),
            seed_profile=args.seed_profile,
            batch_size=int(args.batch_size),
            reuse_existing_project=bool(getattr(args, "reuse_existing_project", False)),
            reuse_reset_after_ep=getattr(args, "reuse_reset_after_ep", None),
            soak_profile=soak,
            stage3_failure_policy=args.stage3_failure_policy,
            run_id=getattr(args, "run_id", "") or "",
        )
        _print_json(payload)
        return 0 if payload.get("status") == "success" else 1

    if args.command == "analyze":
        payload = analyze_project(args.project, arc_count=args.arc_count)
        _print_json(payload)
        return 0

    payload = run_harness(
        arc_count=resolve_arc_count(args.arc_count, args.trigger),
        seed_profile=args.seed_profile,
        batch_size=int(args.batch_size),
        poll_interval_seconds=max(1, int(args.poll_interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS)),
        target_project=args.target_project or "",
        trigger=args.trigger,
        reuse_existing_project=bool(getattr(args, "reuse_existing_project", False)),
        reuse_reset_after_ep=getattr(args, "reuse_reset_after_ep", None),
        operational_attempt_cap=max(1, int(getattr(args, "operational_attempt_cap", DEFAULT_OPERATIONAL_ATTEMPT_CAP))),
        max_runtime_seconds=max(0, int(getattr(args, "max_runtime_seconds", DEFAULT_MAX_RUNTIME_SECONDS) or 0)),
        max_total_tokens=max(0, int(getattr(args, "max_total_tokens", DEFAULT_MAX_TOTAL_TOKENS) or 0)),
        max_total_cost_usd=max(0.0, float(getattr(args, "max_total_cost_usd", DEFAULT_MAX_TOTAL_COST_USD) or 0.0)),
        max_project_bytes=max(0, int(getattr(args, "max_project_bytes", DEFAULT_MAX_PROJECT_BYTES) or 0)),
        soak_profile=soak,
        stage3_failure_policy=args.stage3_failure_policy,
    )
    _print_json(payload)
    return 0 if payload.get("analysis", {}).get("judgment") == "success" else 1


def resolve_arc_count(arc_count: int | None, trigger: str) -> int:
    if arc_count is not None:
        normalized = int(arc_count)
        if normalized <= 0:
            raise ValueError("arc_count must be a positive integer")
        return normalized

    parsed = parse_arc_count_from_trigger(trigger)
    if parsed is None:
        raise ValueError("arc_count is required when trigger does not contain an N-arc phrase")
    return parsed


def parse_arc_count_from_trigger(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)\s*아크", str(text))
    if not match:
        return None
    value = int(match.group(1))
    return value if value > 0 else None


def build_target_project_name(seed_profile: str, arc_count: int, *, now: datetime | None = None) -> str:
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    return f"auto_test_{stamp}_{seed_profile}_{int(arc_count)}arc"


def build_run_id(*, target_project: str, arc_count: int, now: datetime | None = None) -> str:
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    seed = f"{stamp}:{target_project}:{int(arc_count)}"
    suffix = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:10]
    return f"{stamp}_{suffix}"


def normalize_budget_caps(
    *,
    max_runtime_seconds: int | float = DEFAULT_MAX_RUNTIME_SECONDS,
    max_total_tokens: int | float = DEFAULT_MAX_TOTAL_TOKENS,
    max_total_cost_usd: int | float = DEFAULT_MAX_TOTAL_COST_USD,
    max_project_bytes: int | float = DEFAULT_MAX_PROJECT_BYTES,
) -> dict[str, float | int]:
    def _int_cap(value: int | float) -> int:
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

    def _float_cap(value: int | float) -> float:
        try:
            return max(0.0, float(value or 0.0))
        except (TypeError, ValueError):
            return 0.0

    return {
        "max_runtime_seconds": _int_cap(max_runtime_seconds),
        "max_total_tokens": _int_cap(max_total_tokens),
        "max_total_cost_usd": _float_cap(max_total_cost_usd),
        "max_project_bytes": _int_cap(max_project_bytes),
    }


def detect_budget_breach(snapshot: dict[str, Any], caps: dict[str, Any]) -> dict[str, Any]:
    checks = (
        (
            "runtime_seconds",
            float(snapshot.get("runtime_elapsed_seconds", 0) or 0),
            float(caps.get("max_runtime_seconds", 0) or 0),
        ),
        (
            "total_tokens",
            float(snapshot.get("metrics_total_tokens", 0) or 0),
            float(caps.get("max_total_tokens", 0) or 0),
        ),
        (
            "total_cost_usd",
            float(snapshot.get("metrics_total_cost_usd", 0) or 0),
            float(caps.get("max_total_cost_usd", 0) or 0),
        ),
        ("project_bytes", float(snapshot.get("project_bytes", 0) or 0), float(caps.get("max_project_bytes", 0) or 0)),
    )
    for kind, observed, cap in checks:
        if cap > 0 and observed > cap:
            return {
                "exceeded": True,
                "kind": kind,
                "observed": observed,
                "cap": cap,
            }
    return {"exceeded": False}


def build_execution_plan(
    *,
    arc_count: int,
    seed_profile: str,
    batch_size: int,
    target_project: str,
    trigger: str,
    reuse_existing_project: bool = False,
    reuse_reset_after_ep: int | None = None,
    operational_attempt_cap: int = DEFAULT_OPERATIONAL_ATTEMPT_CAP,
    max_runtime_seconds: int = DEFAULT_MAX_RUNTIME_SECONDS,
    max_total_tokens: int = DEFAULT_MAX_TOTAL_TOKENS,
    max_total_cost_usd: float = DEFAULT_MAX_TOTAL_COST_USD,
    max_project_bytes: int = DEFAULT_MAX_PROJECT_BYTES,
    soak_profile: SoakProfile | None = None,
    stage3_failure_policy: str = DEFAULT_STAGE3_FAILURE_POLICY,
) -> dict[str, Any]:
    profile = default_profile(seed_profile)
    target_name = target_project or build_target_project_name(seed_profile, arc_count)
    stage3_failure_policy = normalize_stage3_failure_policy(stage3_failure_policy)
    run_id = build_run_id(target_project=target_name, arc_count=arc_count)
    plan: dict[str, Any] = {
        "summary_role": "auto_frontier_lag_harness_plan",
        "created_at": _now_iso(),
        "run_id": run_id,
        "operator_trigger": trigger,
        "arc_count": int(arc_count),
        "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
        "seed_profile": seed_profile,
        "target_project": target_name,
        "reuse_existing_project": bool(reuse_existing_project),
        "reuse_reset_after_ep": reuse_reset_after_ep,
        "operational_attempt_cap": max(1, int(operational_attempt_cap or DEFAULT_OPERATIONAL_ATTEMPT_CAP)),
        "budget_caps": normalize_budget_caps(
            max_runtime_seconds=max_runtime_seconds,
            max_total_tokens=max_total_tokens,
            max_total_cost_usd=max_total_cost_usd,
            max_project_bytes=max_project_bytes,
        ),
        "stage3_failure_policy": stage3_failure_policy,
        "project_locator": f"projects/{target_name}",
        "manual_profile_doc": MANUAL_PROFILE_DOC,
        "harness_ssot_doc": HARNESS_SSOT_DOC,
        "profile": asdict(profile),
    }
    if soak_profile is not None:
        plan["soak_profile"] = asdict(soak_profile)
    return plan


def run_harness(
    *,
    arc_count: int,
    seed_profile: str,
    batch_size: int,
    poll_interval_seconds: int,
    target_project: str,
    trigger: str,
    reuse_existing_project: bool = False,
    reuse_reset_after_ep: int | None = None,
    operational_attempt_cap: int = DEFAULT_OPERATIONAL_ATTEMPT_CAP,
    max_runtime_seconds: int = DEFAULT_MAX_RUNTIME_SECONDS,
    max_total_tokens: int = DEFAULT_MAX_TOTAL_TOKENS,
    max_total_cost_usd: float = DEFAULT_MAX_TOTAL_COST_USD,
    max_project_bytes: int = DEFAULT_MAX_PROJECT_BYTES,
    soak_profile: SoakProfile | None = None,
    stage3_failure_policy: str = DEFAULT_STAGE3_FAILURE_POLICY,
) -> dict[str, Any]:
    stage3_failure_policy = normalize_stage3_failure_policy(stage3_failure_policy)
    budget_caps = normalize_budget_caps(
        max_runtime_seconds=max_runtime_seconds,
        max_total_tokens=max_total_tokens,
        max_total_cost_usd=max_total_cost_usd,
        max_project_bytes=max_project_bytes,
    )
    plan = build_execution_plan(
        arc_count=arc_count,
        seed_profile=seed_profile,
        batch_size=batch_size,
        target_project=target_project,
        trigger=trigger,
        reuse_existing_project=reuse_existing_project,
        reuse_reset_after_ep=reuse_reset_after_ep,
        operational_attempt_cap=operational_attempt_cap,
        max_runtime_seconds=budget_caps["max_runtime_seconds"],
        max_total_tokens=budget_caps["max_total_tokens"],
        max_total_cost_usd=budget_caps["max_total_cost_usd"],
        max_project_bytes=budget_caps["max_project_bytes"],
        soak_profile=soak_profile,
        stage3_failure_policy=stage3_failure_policy,
    )
    project_name = str(plan["target_project"])
    project_root = PROJECT_ROOT / "projects" / project_name
    if project_root.exists() and not reuse_existing_project:
        raise FileExistsError(f"target project already exists: {project_root}")

    command = build_worker_command(
        target_project=project_name,
        arc_count=arc_count,
        seed_profile=seed_profile,
        batch_size=batch_size,
        reuse_existing_project=reuse_existing_project,
        reuse_reset_after_ep=reuse_reset_after_ep,
        soak_profile_name="soak" if soak_profile is not None else "",
        stage3_failure_policy=stage3_failure_policy,
        run_id=str(plan.get("run_id", "") or ""),
    )
    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        creationflags=_worker_creationflags(),
    )

    poll_history: list[dict[str, Any]] = []
    previous = capture_poll_snapshot(project_root, process=process, operational_attempt_cap=operational_attempt_cap)
    poll_history.append(previous)
    _write_poll_history(project_root, poll_history)
    idle_windows = 0
    watchdog_status = "progressing"
    termination_reason = ""
    poll_interval_seconds = max(1, int(poll_interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS))
    next_poll_deadline = time.monotonic() + poll_interval_seconds
    run_started_monotonic = time.monotonic()
    runtime_cap_seconds = float(budget_caps.get("max_runtime_seconds", 0) or 0)

    while True:
        if process.poll() is not None:
            break
        now = time.monotonic()
        runtime_elapsed_seconds = max(0.0, now - run_started_monotonic)
        if runtime_cap_seconds > 0 and runtime_elapsed_seconds > runtime_cap_seconds:
            current = capture_poll_snapshot(
                project_root, process=process, operational_attempt_cap=operational_attempt_cap
            )
            current["runtime_elapsed_seconds"] = round(runtime_elapsed_seconds, 1)
            current["budget_breach"] = detect_budget_breach(current, budget_caps)
            poll_history.append(current)
            _write_poll_history(project_root, poll_history)
            watchdog_status = "failed"
            termination_reason = "budget_runtime_seconds_exceeded"
            _terminate_process_tree(process)
            break
        if now >= next_poll_deadline:
            current = capture_poll_snapshot(
                project_root, process=process, operational_attempt_cap=operational_attempt_cap
            )
            current["runtime_elapsed_seconds"] = round(runtime_elapsed_seconds, 1)
            current["budget_breach"] = detect_budget_breach(current, budget_caps)
            poll_history.append(current)
            _write_poll_history(project_root, poll_history)
            budget_breach = current.get("budget_breach") or {}
            if budget_breach.get("exceeded"):
                watchdog_status = "failed"
                termination_reason = f"budget_{budget_breach.get('kind', 'unknown')}_exceeded"
                _terminate_process_tree(process)
                break
            overflow = current.get("attempt_overflow") or {}
            if overflow.get("exceeded"):
                watchdog_status = "failed"
                termination_reason = "operational_attempt_cap_exceeded"
                _terminate_process_tree(process)
                break
            watchdog_status, idle_windows = classify_poll_transition(previous, current, idle_windows)
            if watchdog_status in {"stalled", "failed"}:
                termination_reason = watchdog_status
                _terminate_process_tree(process)
                break
            previous = current
            next_poll_deadline = now + poll_interval_seconds
            continue
        sleep_for = min(PROCESS_CHECK_INTERVAL_SECONDS, max(0.1, next_poll_deadline - now))
        if runtime_cap_seconds > 0:
            runtime_remaining = runtime_cap_seconds - runtime_elapsed_seconds
            sleep_for = min(sleep_for, max(0.1, runtime_remaining))
        time.sleep(sleep_for)

    exit_code = process.wait()
    final_snapshot = capture_poll_snapshot(
        project_root, process=process, operational_attempt_cap=operational_attempt_cap
    )
    final_snapshot["process_exit_code"] = exit_code
    final_snapshot["runtime_elapsed_seconds"] = round(max(0.0, time.monotonic() - run_started_monotonic), 1)
    final_snapshot["budget_breach"] = detect_budget_breach(final_snapshot, budget_caps)
    poll_history.append(final_snapshot)
    _write_poll_history(project_root, poll_history)

    analysis = analyze_project(
        project_name,
        arc_count=arc_count,
        watchdog_status=watchdog_status,
        termination_reason=termination_reason,
        poll_history=poll_history,
        expected_run_id=str(plan.get("run_id", "") or ""),
    )
    return {
        "summary_role": "auto_frontier_lag_harness_run",
        "plan": plan,
        "worker_command": command,
        "watchdog_status": watchdog_status,
        "termination_reason": termination_reason,
        "process_exit_code": exit_code,
        "analysis": analysis,
    }


def build_worker_command(
    *,
    target_project: str,
    arc_count: int,
    seed_profile: str,
    batch_size: int,
    reuse_existing_project: bool = False,
    reuse_reset_after_ep: int | None = None,
    soak_profile_name: str = "",
    stage3_failure_policy: str = DEFAULT_STAGE3_FAILURE_POLICY,
    run_id: str = "",
) -> list[str]:
    stage3_failure_policy = normalize_stage3_failure_policy(stage3_failure_policy)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "worker",
        "--target-project",
        str(target_project),
        "--arc-count",
        str(int(arc_count)),
        "--seed-profile",
        str(seed_profile),
        "--batch-size",
        str(max(1, int(batch_size or DEFAULT_BATCH_SIZE))),
        "--stage3-failure-policy",
        stage3_failure_policy,
    ]
    if run_id:
        cmd.extend(["--run-id", str(run_id)])
    if reuse_existing_project:
        cmd.append("--reuse-existing-project")
    if reuse_reset_after_ep is not None:
        cmd.extend(["--reuse-reset-after-ep", str(max(1, int(reuse_reset_after_ep)))])
    if soak_profile_name:
        cmd.extend(["--soak-profile", str(soak_profile_name)])
    return cmd


def _worker_creationflags() -> int:
    return int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))


def _menu_choice_for_value(options: tuple[str, ...] | list[str], expected: str) -> str:
    expected_text = str(expected).strip()
    for index, option in enumerate(options, 1):
        if str(option).strip() == expected_text:
            return str(index)
    raise ValueError(f"semantic option not found: {expected_text!r}")


def normalize_stage3_failure_policy(value: str | None) -> str:
    policy = str(value or DEFAULT_STAGE3_FAILURE_POLICY).strip().lower()
    if policy not in STAGE3_FAILURE_POLICIES:
        raise ValueError(f"unknown stage3 failure policy: {policy!r}")
    return policy


def derive_objective_status(frontier_result: dict[str, Any], *, arc_count: int) -> dict[str, Any]:
    arcs_advanced = int(frontier_result.get("arcs_advanced", 0) or 0)
    arcs_skipped = int(frontier_result.get("arcs_skipped", 0) or 0)
    requested_limit_hit = bool(frontier_result.get("requested_limit_hit"))
    stop_reason = str(frontier_result.get("stop_reason", "") or "")
    requested_clean_arc_count = max(0, int(arc_count or 0))

    if arcs_skipped > 0:
        return {
            "objective_status": "failed",
            "objective_success": False,
            "objective_root_cause": "stage3_arc_skipped",
        }
    if arcs_advanced >= requested_clean_arc_count and (requested_limit_hit or requested_clean_arc_count == 0):
        return {
            "objective_status": "success",
            "objective_success": True,
            "objective_root_cause": "",
        }
    if stop_reason and stop_reason not in {"completed", "requested_arc_limit_reached"}:
        return {
            "objective_status": "failed",
            "objective_success": False,
            "objective_root_cause": stop_reason,
        }
    return {
        "objective_status": "failed",
        "objective_success": False,
        "objective_root_cause": "requested_arc_boundary_not_reached",
    }


def run_worker(
    *,
    target_project: str,
    arc_count: int,
    seed_profile: str,
    batch_size: int,
    reuse_existing_project: bool = False,
    reuse_reset_after_ep: int | None = None,
    soak_profile: SoakProfile | None = None,
    stage3_failure_policy: str = DEFAULT_STAGE3_FAILURE_POLICY,
    run_id: str = "",
) -> dict[str, Any]:
    stage3_failure_policy = normalize_stage3_failure_policy(stage3_failure_policy)
    run_id = str(run_id or "").strip() or build_run_id(target_project=target_project, arc_count=arc_count)
    profile = default_profile(seed_profile)
    selected_genre = {"type": profile.genre_type, "name": profile.genre_name}

    with apply_soak_overrides(soak_profile):
        app = _boot_app(target_project, selected_genre)
        project_root = Path(app.current_project.paths.root)
        manifest: dict[str, Any] = {
            "summary_role": "auto_frontier_lag_harness_manifest",
            "created_at": _now_iso(),
            "run_id": run_id,
            "status": "booted",
            "target_project": target_project,
            "project_locator": f"projects/{target_project}",
            "arc_count": int(arc_count),
            "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
            "seed_profile": seed_profile,
            "reuse_existing_project": bool(reuse_existing_project),
            "reuse_reset_after_ep": reuse_reset_after_ep,
            "stage3_failure_policy": stage3_failure_policy,
            "manual_profile_doc": MANUAL_PROFILE_DOC,
            "harness_ssot_doc": HARNESS_SSOT_DOC,
            "profile": asdict(profile),
        }
        if soak_profile is not None:
            manifest["soak_profile"] = asdict(soak_profile)
        _update_manifest(project_root, manifest)

        try:
            if reuse_existing_project:
                reuse_report = _assert_existing_project_frontier_ready(
                    app,
                    reuse_reset_after_ep=reuse_reset_after_ep,
                )
                _update_manifest(
                    project_root,
                    {
                        "status": "existing_project_reuse_checked",
                        "updated_at": _now_iso(),
                        **reuse_report,
                    },
                )
                if not reuse_report.get("reuse_allowed", False):
                    failed_count = int(reuse_report.get("reuse_failed_state_count", 0) or 0)
                    raise RuntimeError(f"existing project reuse refused: {failed_count} failed Stage3/4 row(s)")
                _update_manifest(project_root, {"status": "existing_project_ready", "updated_at": _now_iso()})
            else:
                _apply_stage0_existing_profile(app, profile)
                _update_manifest(project_root, {"status": "stage0_existing_complete", "updated_at": _now_iso()})

                _apply_stage0_style_profile(app, profile)
                _update_manifest(project_root, {"status": "stage0_style_complete", "updated_at": _now_iso()})

            _ensure_pass_rate_monitor(app, project_root)
            _update_manifest(project_root, {"status": "frontier_running", "updated_at": _now_iso()})

            with patch("builtins.input", side_effect=_worker_runtime_input):
                frontier_result = app._one_stop_pipeline_frontier_lag(
                    max_arc_advances=int(arc_count),
                    batch_size_override=max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
                    wait_for_menu_return=False,
                    stage3_failure_policy=stage3_failure_policy,
                )
            if getattr(app, "pass_rate_monitor", None):
                app.pass_rate_monitor.save()
            if hasattr(app, "_flush_audit_buffer"):
                app._flush_audit_buffer()

            objective = derive_objective_status(frontier_result or {}, arc_count=int(arc_count))
            payload: dict[str, Any] = {
                "summary_role": "auto_frontier_lag_worker_result",
                "created_at": _now_iso(),
                "run_id": run_id,
                "status": "success",
                "process_status": "success",
                "process_success": True,
                **objective,
                "project": target_project,
                "project_locator": f"projects/{target_project}",
                "arc_count": int(arc_count),
                "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
                "stage3_failure_policy": stage3_failure_policy,
                "frontier_result": frontier_result,
            }
            _write_json(project_root / "logs" / "auto_frontier_lag_worker_result.json", payload)
            _update_manifest(project_root, {"status": "worker_success", "updated_at": _now_iso()})
            return payload
        except Exception as exc:
            payload = {
                "summary_role": "auto_frontier_lag_worker_result",
                "created_at": _now_iso(),
                "run_id": run_id,
                "status": "failed",
                "process_status": "failed",
                "process_success": False,
                "objective_status": "not_evaluated_process_failed",
                "objective_success": False,
                "objective_root_cause": str(exc) or "worker_failed",
                "project": target_project,
                "project_locator": f"projects/{target_project}",
                "arc_count": int(arc_count),
                "batch_size": max(1, int(batch_size or DEFAULT_BATCH_SIZE)),
                "stage3_failure_policy": stage3_failure_policy,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            _write_json(project_root / "logs" / "auto_frontier_lag_worker_result.json", payload)
            _update_manifest(project_root, {"status": "worker_failed", "updated_at": _now_iso(), "error": str(exc)})
            return payload
        finally:
            _shutdown_worker_app(app)


def _boot_app(project_name: str, selected_genre: dict[str, Any]) -> SovereignApp:
    with (
        patch.object(SovereignApp, "_select_genre", return_value=selected_genre),
        patch.object(SovereignApp, "_select_project", return_value=project_name),
        patch.object(SovereignApp, "_run_main_process", lambda self: None),
    ):
        app = SovereignApp()
        app.boot()
        return app


def _apply_stage0_existing_profile(app: SovereignApp, profile: HarnessProfile) -> None:
    protagonist = profile.protagonist_config
    responses = [
        "1",
        profile.treatment_auto_condense,
        _menu_choice_for_value(WORLD_ORIGIN_OPTIONS, protagonist["world_origin"]),
        _menu_choice_for_value(INCARNATION_TYPE_OPTIONS, protagonist["incarnation_type"]),
        _menu_choice_for_value(POV_OPTIONS, protagonist["pov"]),
        _menu_choice_for_value(
            EXTERNAL_POV_INSERT_POLICY_OPTIONS,
            protagonist["external_pov_insert_policy"],
        ),
        "",
    ]
    with (
        patch.object(app, "_ui_select_bible", return_value=profile.bible_file),
        patch.object(app, "_ui_select_treatment", return_value=profile.roadmap_file),
        patch("builtins.input", side_effect=_iter_input_responses(responses)),
    ):
        app._phase_0_recovery()

    saved_bible = app.current_project.db.load_anchor("bible") or {}
    plot_roadmap = (
        saved_bible.get("MasterBible", saved_bible).get("plot_roadmap", []) if isinstance(saved_bible, dict) else []
    )
    if not saved_bible or not plot_roadmap:
        raise RuntimeError("stage0 existing-file replay did not persist bible/plot_roadmap")


def _apply_stage0_style_profile(app: SovereignApp, profile: HarnessProfile) -> None:
    cache_choice = {
        "use": "1",
        "refresh": "2",
        "reset": "3",
    }.get(profile.style_analysis_mode, "1")
    responses = [
        profile.style_analysis_confirm,
        cache_choice,
        "",
        "",
    ]
    with patch("builtins.input", side_effect=_iter_input_responses(responses)):
        app._stage_0_extended(mode=5)

    style_anchor = app.current_project.db.load_anchor("style_guide") or {}
    style_file = Path(app.current_project.paths.root) / "stage0_output" / "style_guide.json"
    if not style_anchor and not style_file.exists():
        raise RuntimeError("stage0 style-analysis replay did not persist style_guide")


def _hash_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _derive_existing_project_frontier_ep(app: SovereignApp, plot_roadmap: list[Any]) -> int:
    arcs = app.current_project.db.load_anchor("arcs") or []
    try:
        plan = app._resolve_one_stop_frontier_lag_plan(total_arcs=len(plot_roadmap), designed_arcs=arcs)
    except Exception:
        plan = {}
    if isinstance(plan, dict):
        for key in ("frontier_ep_start", "stage3_target", "stage4_target"):
            try:
                value = int(plan.get(key) or 0)
            except (TypeError, ValueError):
                value = 0
            if value > 0:
                return value
    if arcs and isinstance(arcs[-1], dict):
        try:
            return max(1, int(arcs[-1].get("ep_start") or arcs[-1].get("ep_end") or 1))
        except (TypeError, ValueError):
            return 1
    return 1


def _episode_number_from_frontier_artifact_name(name: str) -> int | None:
    match = re.match(r"(?:ep|emergency_ep|blueprint)_(\d{1,6})(?:\..+)?$", str(name or ""))
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def _archive_reuse_reset_filesystem_frontier(project_root: Path, *, reset_target_ep: int) -> dict[str, Any]:
    """Move stale file-based frontier evidence out of scanner paths after DB reset."""
    reset_target = max(1, int(reset_target_ep or 1))
    archive_root = (
        project_root
        / "logs"
        / "reset_archives"
        / f"reuse_reset_ge_ep{reset_target:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    candidates: list[Path] = []

    drafts_root = project_root / "drafts"
    if drafts_root.exists():
        for pattern in ("ep_*.*", "emergency_ep_*.txt"):
            for path in drafts_root.glob(pattern):
                ep_num = _episode_number_from_frontier_artifact_name(path.name)
                if ep_num is not None and ep_num >= reset_target:
                    candidates.append(path)

    blueprints_root = project_root / "plans" / "blueprints"
    if blueprints_root.exists():
        for pattern in ("blueprint_*.*", "ep_*.json"):
            for path in blueprints_root.glob(pattern):
                ep_num = _episode_number_from_frontier_artifact_name(path.name)
                if ep_num is not None and ep_num >= reset_target:
                    candidates.append(path)

    for stage_dir in (project_root / "logs" / "artifacts" / "stage3", project_root / "logs" / "artifacts" / "stage4"):
        if not stage_dir.exists():
            continue
        for path in stage_dir.glob("ep_*"):
            ep_num = _episode_number_from_frontier_artifact_name(path.name)
            if ep_num is not None and ep_num >= reset_target:
                candidates.append(path)

    moved: list[str] = []
    for path in sorted(candidates, key=lambda item: str(item)):
        if not path.exists():
            continue
        rel = path.relative_to(project_root)
        destination = archive_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
        moved.append(str(rel).replace("\\", "/"))

    return {
        "reuse_reset_filesystem_archive_applied": bool(moved),
        "reuse_reset_filesystem_archive_root": str(archive_root.relative_to(project_root)).replace("\\", "/")
        if moved
        else "",
        "reuse_reset_filesystem_archived_count": len(moved),
        "reuse_reset_filesystem_archived_paths": moved[:50],
    }


def _read_reuse_failed_stage_state(db: Any, *, min_ep: int, limit: int = 20) -> list[dict[str, Any]]:
    conn = getattr(db, "conn", None)
    if conn is None:
        return []
    placeholders = ", ".join("?" for _ in SUCCESS_STAGE_VERDICTS)
    query = f"""
        SELECT id, stage, ep_num, arc_num, attempt_num, verdict,
               failure_category, reject_reason, primary_failure_layer
          FROM stage_attempts
         WHERE stage IN (3, 4)
           AND (ep_num IS NULL OR ep_num >= ?)
           AND UPPER(COALESCE(verdict, '')) NOT IN ({placeholders})
         ORDER BY id DESC
         LIMIT ?
    """
    try:
        rows = conn.execute(query, (int(min_ep), *SUCCESS_STAGE_VERDICTS, max(1, int(limit or 20)))).fetchall()
    except Exception:
        return []
    columns = (
        "id",
        "stage",
        "ep_num",
        "arc_num",
        "attempt_num",
        "verdict",
        "failure_category",
        "reject_reason",
        "primary_failure_layer",
    )
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if hasattr(row, "keys"):
            parsed.append(dict(row))
        else:
            parsed.append(dict(zip(columns, row, strict=False)))
    return parsed


def _assert_existing_project_frontier_ready(
    app: SovereignApp,
    *,
    reuse_reset_after_ep: int | None = None,
) -> dict[str, Any]:
    saved_bible = app.current_project.db.load_anchor("bible") or {}
    plot_roadmap = (
        saved_bible.get("MasterBible", saved_bible).get("plot_roadmap", []) if isinstance(saved_bible, dict) else []
    )
    if not saved_bible or not plot_roadmap:
        raise RuntimeError("existing project is not frontier-ready: bible/plot_roadmap anchor missing")

    style_anchor = app.current_project.db.load_anchor("style_guide") or {}
    style_file = Path(app.current_project.paths.root) / "stage0_output" / "style_guide.json"
    if not style_anchor and not style_file.exists():
        raise RuntimeError("existing project is not frontier-ready: style_guide missing")

    project_root = Path(app.current_project.paths.root)
    db_path = project_root / "project_data.db"
    frontier_ep = _derive_existing_project_frontier_ep(app, plot_roadmap)
    pre_hash = _hash_file(db_path)
    pre_failed_rows = _read_reuse_failed_stage_state(app.current_project.db, min_ep=frontier_ep)
    reset_target = max(1, int(reuse_reset_after_ep)) if reuse_reset_after_ep is not None else None
    reset_applied = False
    reset_result = "not_requested"
    reset_filesystem_report: dict[str, Any] = {
        "reuse_reset_filesystem_archive_applied": False,
        "reuse_reset_filesystem_archive_root": "",
        "reuse_reset_filesystem_archived_count": 0,
        "reuse_reset_filesystem_archived_paths": [],
    }

    if reset_target is not None:
        app.current_project.db.reset_after(reset_target)
        reset_filesystem_report = _archive_reuse_reset_filesystem_frontier(
            project_root,
            reset_target_ep=reset_target,
        )
        reset_applied = True
        reset_result = "applied"

    post_hash = _hash_file(db_path)
    post_failed_rows = _read_reuse_failed_stage_state(app.current_project.db, min_ep=frontier_ep)
    failed_rows = post_failed_rows if reset_applied else pre_failed_rows
    reuse_allowed = not failed_rows
    if failed_rows and reset_applied:
        reset_result = "applied_but_failed_state_remains"

    return {
        "reuse_policy": "reset_after" if reset_target is not None else "refuse_failed_state",
        "reuse_allowed": reuse_allowed,
        "reuse_failed_state_detected": bool(failed_rows),
        "reuse_failed_state_count": len(failed_rows),
        "reuse_failed_state_rows": failed_rows,
        "reuse_frontier_min_ep": frontier_ep,
        "reuse_reset_after_ep": reset_target,
        "reuse_reset_applied": reset_applied,
        "reuse_reset_result": reset_result,
        "reuse_pre_failed_state_count": len(pre_failed_rows),
        "reuse_post_failed_state_count": len(post_failed_rows),
        "reuse_db_hash_before": pre_hash,
        "reuse_db_hash_after": post_hash,
        **reset_filesystem_report,
    }


def _worker_runtime_input(prompt: str = "") -> str:
    text = str(prompt or "")
    if "건너뛰고 다음 Arc로?" in text:
        return "2"
    if "[Enter] 메뉴로 돌아가기" in text:
        return ""
    return ""


def _iter_input_responses(responses: list[str]) -> Any:
    iterator = iter(responses)

    def _next_response(*_args, **_kwargs) -> str:
        return next(iterator, "")

    return _next_response


def _shutdown_worker_app(app: SovereignApp) -> None:
    shutdown = getattr(app, "_shutdown_app", None)
    if callable(shutdown):
        try:
            shutdown()
            return
        except Exception:
            pass
    _close_app_handles(app)


def _read_latest_metrics_summary(project_root: Path) -> dict[str, Any]:
    metrics_root = project_root / "logs" / "metrics"
    if not metrics_root.exists():
        return {}
    try:
        candidates = sorted(metrics_root.glob("metrics_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    except OSError:
        return {}
    if not candidates:
        return {}
    return _read_json(candidates[0])


def _compute_project_bytes(project_root: Path) -> int:
    if not project_root.exists():
        return 0
    total = 0
    try:
        for path in project_root.rglob("*"):
            if path.is_file():
                try:
                    total += path.stat().st_size
                except OSError:
                    continue
    except OSError:
        return total
    return int(total)


def capture_poll_snapshot(
    project_root: Path,
    *,
    process: subprocess.Popen[Any] | None = None,
    operational_attempt_cap: int = DEFAULT_OPERATIONAL_ATTEMPT_CAP,
) -> dict[str, Any]:
    session_log = resolve_active_session_log(project_root)
    log_tail = _tail_text(session_log, max_lines=20)
    stage3_attempts, stage4_attempts, director_stage3_rows, director_stage4_rows = _read_attempt_counts(project_root)
    runtime_summary = _read_json(project_root / "logs" / "runtime_audit_summary.json")
    manifest = _read_json(project_root / "logs" / "auto_frontier_lag_harness_manifest.json")
    metrics_summary = _read_latest_metrics_summary(project_root)
    snapshot = {
        "captured_at": _now_iso(),
        "process_alive": bool(process is not None and process.poll() is None),
        "process_exit_code": process.poll() if process is not None else None,
        "session_log": str(session_log) if session_log else "",
        "session_log_size": session_log.stat().st_size if session_log and session_log.exists() else 0,
        "session_log_tail": log_tail,
        "blueprint_count": len(list((project_root / "plans" / "blueprints").glob("*.json")))
        if project_root.exists()
        else 0,
        "draft_count": len(list((project_root / "drafts").glob("ep_*.txt"))) if project_root.exists() else 0,
        "stage3_attempts": stage3_attempts,
        "stage4_attempts": stage4_attempts,
        "director_stage3_rows": director_stage3_rows,
        "director_stage4_rows": director_stage4_rows,
        "runtime_audit_tag": str(runtime_summary.get("tag", "") or ""),
        "runtime_audit_total_events": int(runtime_summary.get("total_events", 0) or 0),
        "metrics_session_id": str(metrics_summary.get("session_id", "") or ""),
        "metrics_total_tokens": int(metrics_summary.get("total_tokens", 0) or 0),
        "metrics_total_cost_usd": float(metrics_summary.get("total_cost_usd", 0.0) or 0.0),
        "project_bytes": _compute_project_bytes(project_root),
        "harness_phase": str(manifest.get("status", "") or ""),
        "prompt_blocked": detect_prompt_blocked(log_tail),
        "attempt_overflow": detect_attempt_overflow(
            log_tail, max(1, int(operational_attempt_cap or DEFAULT_OPERATIONAL_ATTEMPT_CAP))
        ),
    }
    return snapshot


def resolve_active_session_log(project_root: Path) -> Path | None:
    if not project_root.exists():
        return None
    logs_root = project_root / "logs"
    candidates = sorted(logs_root.glob("session_*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _tail_text(path: Path | None, *, max_lines: int) -> list[str]:
    if path is None or not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8").splitlines()[-max_lines:]
    except OSError:
        return []


def detect_prompt_blocked(log_tail: list[str]) -> bool:
    merged = "\n".join(str(line) for line in log_tail[-8:])
    return any(marker in merged for marker in PROMPT_WAIT_MARKERS)


def detect_provider_response_wait(log_tail: list[str]) -> bool:
    """Return true when the session tail is inside a provider HTTP response wait."""
    last_start_index = -1
    last_end_index = -1
    for index, raw_line in enumerate(log_tail[-20:]):
        line = str(raw_line or "")
        if PROVIDER_RESPONSE_WAIT_STARTED_MARKER in line:
            last_start_index = index
        if any(marker in line for marker in PROVIDER_RESPONSE_WAIT_END_MARKERS):
            last_end_index = index
    return last_start_index >= 0 and last_start_index > last_end_index


def detect_active_frontier_wait(snapshot: dict[str, Any]) -> bool:
    """Return true for known long-running frontier phases that can be quiet between logs."""
    if not snapshot.get("process_alive"):
        return False
    if str(snapshot.get("harness_phase", "") or "") != "frontier_running":
        return False
    merged = "\n".join(str(line or "") for line in snapshot.get("session_log_tail", [])[-20:])
    return any(marker in merged for marker in ACTIVE_FRONTIER_WAIT_MARKERS)


def detect_attempt_overflow(log_tail: list[str], cap: int) -> dict[str, Any]:
    for raw_line in reversed(log_tail):
        line = str(raw_line or "")
        for stage_name, pattern in ATTEMPT_OVERFLOW_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            attempt = int(match.group(1))
            total = int(match.group(2))
            if attempt > cap:
                return {
                    "exceeded": True,
                    "stage": stage_name,
                    "attempt": attempt,
                    "total": total,
                    "cap": int(cap),
                    "line": line,
                }
    return {"exceeded": False, "cap": int(cap)}


def classify_poll_transition(previous: dict[str, Any], current: dict[str, Any], idle_windows: int) -> tuple[str, int]:
    if current.get("process_exit_code") not in (None, 0):
        return "failed", idle_windows
    overflow = current.get("attempt_overflow") or {}
    if overflow.get("exceeded"):
        return "failed", idle_windows

    merged_tail = "\n".join(str(line) for line in current.get("session_log_tail", []))
    if any(token in merged_tail for token in FATAL_TAIL_MARKERS):
        return "failed", idle_windows

    progress_keys = (
        "session_log_size",
        "blueprint_count",
        "draft_count",
        "stage3_attempts",
        "stage4_attempts",
        "director_stage3_rows",
        "director_stage4_rows",
        "runtime_audit_total_events",
        "harness_phase",
    )
    progressed = any(current.get(key) != previous.get(key) for key in progress_keys)
    if progressed:
        return "progressing", 0
    if current.get("prompt_blocked"):
        return "waiting_prompt", 0
    if detect_provider_response_wait(current.get("session_log_tail", [])):
        return "provider_wait", 0
    if current.get("process_alive"):
        idle_windows += 1
        idle_limit = (
            ACTIVE_FRONTIER_STALL_IDLE_WINDOWS if detect_active_frontier_wait(current) else DEFAULT_STALL_IDLE_WINDOWS
        )
        if idle_windows >= idle_limit:
            return "stalled", idle_windows
        return "stall-candidate", idle_windows
    return "idle", idle_windows


def analyze_project(
    project_name: str,
    *,
    arc_count: int | None = None,
    watchdog_status: str = "",
    termination_reason: str = "",
    poll_history: list[dict[str, Any]] | None = None,
    expected_run_id: str = "",
) -> dict[str, Any]:
    project_root = PROJECT_ROOT / "projects" / project_name
    worker_result = _read_json(project_root / "logs" / "auto_frontier_lag_worker_result.json")
    manifest = _read_json(project_root / "logs" / "auto_frontier_lag_harness_manifest.json")
    runtime_summary = _read_json(project_root / "logs" / "runtime_audit_summary.json")
    pass_rate_monitor = _read_json(project_root / "logs" / "pass_rate_monitor.json")
    poll_history_path = project_root / "logs" / "auto_frontier_lag_poll_history.jsonl"
    poll_history = poll_history or _read_jsonl(poll_history_path)

    if arc_count is None:
        arc_count = int(worker_result.get("arc_count") or manifest.get("arc_count") or 0)
    manifest_run_id = str(manifest.get("run_id", "") or "")
    worker_run_id = str(worker_result.get("run_id", "") or "")
    expected_run_id = str(expected_run_id or "").strip()
    run_id_mismatch = bool(
        (expected_run_id and worker_run_id and worker_run_id != expected_run_id)
        or (manifest_run_id and worker_run_id and worker_run_id != manifest_run_id)
    )

    stage3_latest_session_id = ""
    stage4_latest_session_id = ""
    shared_session_id = ""
    stage3_summary: dict[str, Any] = {}
    stage4_summary: dict[str, Any] = {}
    stage3_attempts = 0
    stage4_attempts = 0
    continuity_canary_report: dict[str, Any] = read_continuity_canary_report(project_root)

    db_path = project_root / "project_data.db"
    if db_path.exists():
        db = DBManager(db_path)
        try:
            analyzer = FailureAnalyzer(db, project_path=project_root)
            stage3_rows = db.conn.execute(
                "SELECT session_id FROM stage_attempts WHERE stage = 3 ORDER BY id ASC"
            ).fetchall()
            stage4_rows = db.conn.execute(
                "SELECT session_id FROM stage_attempts WHERE stage = 4 ORDER BY id ASC"
            ).fetchall()
            stage3_attempts = len(stage3_rows)
            stage4_attempts = len(stage4_rows)
            stage3_latest_session_id = latest_session_id_from_rows(stage3_rows)
            stage4_latest_session_id = latest_session_id_from_rows(stage4_rows)
            session_filter = stage4_latest_session_id or stage3_latest_session_id
            if (
                stage3_latest_session_id
                and stage4_latest_session_id
                and stage3_latest_session_id == stage4_latest_session_id
            ):
                shared_session_id = stage3_latest_session_id
            stage3_summary = analyzer.sink_alignment_summary(
                stage=3,
                include_session_decisions=True,
                session_id=session_filter or None,
            )
            stage4_summary = analyzer.sink_alignment_summary(
                stage=4,
                include_session_decisions=True,
                session_id=session_filter or None,
            )
        finally:
            db.close()

    frontier_result = worker_result.get("frontier_result", {}) if isinstance(worker_result, dict) else {}
    boundary_reached = bool(frontier_result.get("requested_limit_hit")) or (
        int(frontier_result.get("arcs_advanced", 0) or 0) >= int(arc_count or 0)
    )
    derived_objective = derive_objective_status(frontier_result or {}, arc_count=int(arc_count or 0))
    process_status = str(worker_result.get("process_status") or worker_result.get("status", "") or "")
    process_success = bool(worker_result.get("process_success", process_status == "success"))
    objective_status = str(worker_result.get("objective_status") or derived_objective["objective_status"])
    objective_success = bool(worker_result.get("objective_success", derived_objective["objective_success"]))
    objective_root_cause = str(
        worker_result.get("objective_root_cause") or derived_objective["objective_root_cause"] or ""
    )
    strict_evidence_gaps = derive_strict_success_evidence_gaps(
        project_root=project_root,
        frontier_result=frontier_result,
        boundary_reached=boundary_reached,
        objective_success=objective_success,
        stage3_attempts=stage3_attempts,
        stage4_attempts=stage4_attempts,
        stage3_summary=stage3_summary,
        stage4_summary=stage4_summary,
        continuity_canary_report=continuity_canary_report,
    )
    if objective_success and strict_evidence_gaps:
        objective_status = "failed"
        objective_success = False
        objective_root_cause = "strict_evidence_missing"
    if run_id_mismatch:
        process_status = "failed"
        process_success = False
        objective_status = "failed"
        objective_success = False
        objective_root_cause = "stale_worker_result_run_id_mismatch"
    root_cause = derive_root_cause(
        worker_result=worker_result,
        watchdog_status=watchdog_status,
        termination_reason=termination_reason,
        stage3_summary=stage3_summary,
        stage4_summary=stage4_summary,
        boundary_reached=boundary_reached,
        process_success=process_success,
        objective_success=objective_success,
        objective_root_cause=objective_root_cause,
    )
    judgment = derive_judgment(
        worker_result=worker_result,
        watchdog_status=watchdog_status,
        boundary_reached=boundary_reached,
        stage3_summary=stage3_summary,
        stage4_summary=stage4_summary,
        root_cause=root_cause,
        process_success=process_success,
        objective_success=objective_success,
    )
    audit_summary = run_three_pass_audit(
        worker_result=worker_result,
        boundary_reached=boundary_reached,
        stage3_summary=stage3_summary,
        stage4_summary=stage4_summary,
        judgment=judgment,
        root_cause=root_cause,
        poll_history=poll_history,
    )

    payload = {
        "summary_role": "auto_frontier_lag_runtime_analysis",
        "generated_at": _now_iso(),
        "project": project_name,
        "project_locator": f"projects/{project_name}",
        "arc_count": int(arc_count or 0),
        "run_id": worker_run_id or manifest_run_id or expected_run_id,
        "manifest_run_id": manifest_run_id,
        "worker_run_id": worker_run_id,
        "expected_run_id": expected_run_id,
        "run_id_mismatch": run_id_mismatch,
        "watchdog_status": watchdog_status,
        "termination_reason": termination_reason,
        "worker_status": str(worker_result.get("status", "") or ""),
        "process_status": process_status,
        "process_success": process_success,
        "objective_status": objective_status,
        "objective_success": objective_success,
        "objective_root_cause": objective_root_cause,
        "strict_evidence_gaps": strict_evidence_gaps,
        "boundary_reached": boundary_reached,
        "frontier_result": frontier_result,
        "runtime_audit_summary": runtime_summary,
        "pass_rate_monitor_exists": bool(pass_rate_monitor),
        "stage3_attempts": stage3_attempts,
        "stage4_attempts": stage4_attempts,
        "stage3_latest_session_id": stage3_latest_session_id,
        "stage4_latest_session_id": stage4_latest_session_id,
        "shared_session_id": shared_session_id,
        "stage3_current_session_sink_alignment_summary": stage3_summary,
        "stage4_current_session_sink_alignment_summary": stage4_summary,
        "continuity_canary_report": continuity_canary_report,
        "judgment": judgment,
        "root_cause": root_cause,
        "poll_count": len(poll_history),
        "poll_history_path": str(poll_history_path) if poll_history else "",
        "three_pass_audit": audit_summary,
    }
    analysis_path = project_root / "logs" / "auto_frontier_lag_analysis.json"
    failure_digest_path = project_root / "logs" / "auto_frontier_lag_failure_digest.json"
    if judgment != "success":
        _write_json(
            failure_digest_path,
            {
                "generated_at": _now_iso(),
                "project_locator": payload["project_locator"],
                "judgment": judgment,
                "root_cause": root_cause,
                "watchdog_status": watchdog_status,
                "process_status": process_status,
                "objective_status": objective_status,
                "objective_root_cause": objective_root_cause,
                "strict_evidence_gaps": strict_evidence_gaps,
                "continuity_canary_status": str(continuity_canary_report.get("status", "") or ""),
                "continuity_canary_findings": continuity_canary_report.get("findings", []),
                "run_id_mismatch": run_id_mismatch,
                "manifest_run_id": manifest_run_id,
                "worker_run_id": worker_run_id,
                "expected_run_id": expected_run_id,
            },
        )
    elif failure_digest_path.exists():
        failure_digest_path.unlink()
    ssot_path = write_execution_ssot(payload)
    payload["ssot_path"] = str(ssot_path)
    _write_json(analysis_path, payload)
    return payload


def derive_strict_success_evidence_gaps(
    *,
    project_root: Path,
    frontier_result: dict[str, Any],
    boundary_reached: bool,
    objective_success: bool,
    stage3_attempts: int,
    stage4_attempts: int,
    stage3_summary: dict[str, Any],
    stage4_summary: dict[str, Any],
    continuity_canary_report: dict[str, Any] | None = None,
) -> list[str]:
    if not boundary_reached or not objective_success:
        return []
    gaps: list[str] = []
    if not (project_root / "project_data.db").exists():
        gaps.append("project_data_db_missing")
    if stage3_attempts <= 0:
        gaps.append("stage3_attempts_missing")
    if stage4_attempts <= 0:
        gaps.append("stage4_attempts_missing")
    if not stage3_summary:
        gaps.append("stage3_sink_alignment_summary_missing")
    if not stage4_summary:
        gaps.append("stage4_sink_alignment_summary_missing")
    gaps.extend(_strict_success_continuity_canary_gaps(continuity_canary_report))
    gaps.extend(_strict_success_artifact_gaps(project_root=project_root, frontier_result=frontier_result))
    return gaps


def _strict_success_continuity_canary_gaps(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return []
    status = str(report.get("status", "") or "").strip()
    if status not in {"review_required", "failed"}:
        return []
    try:
        finding_count = int(report.get("finding_count") or len(report.get("findings") or []))
    except (TypeError, ValueError):
        finding_count = 0
    return [f"continuity_canary_{status}:{finding_count}"]


def _strict_success_artifact_gaps(*, project_root: Path, frontier_result: dict[str, Any]) -> list[str]:
    try:
        total_manuscripts = int((frontier_result or {}).get("total_manuscripts", 0) or 0)
    except (TypeError, ValueError):
        total_manuscripts = 0
    if total_manuscripts <= 0:
        return []
    gaps: list[str] = []
    drafts_root = project_root / "drafts"
    for ep_num in range(1, total_manuscripts + 1):
        txt_path = drafts_root / f"ep_{ep_num:04d}.txt"
        settlement_path = drafts_root / f"ep_{ep_num:04d}.settlement.json"
        if not txt_path.is_file() or txt_path.stat().st_size <= 0:
            gaps.append(f"draft_txt_missing_or_empty:ep_{ep_num:04d}")
        if not settlement_path.is_file() or settlement_path.stat().st_size <= 0:
            gaps.append(f"settlement_packet_missing_or_empty:ep_{ep_num:04d}")
    return gaps


def derive_root_cause(
    *,
    worker_result: dict[str, Any],
    watchdog_status: str,
    stage3_summary: dict[str, Any],
    stage4_summary: dict[str, Any],
    boundary_reached: bool,
    termination_reason: str = "",
    process_success: bool | None = None,
    objective_success: bool | None = None,
    objective_root_cause: str = "",
) -> str:
    worker_status = str(worker_result.get("status", "") or "")
    if process_success is None:
        process_success = worker_status == "success"
    if termination_reason.startswith("budget_"):
        return termination_reason
    if termination_reason == "operational_attempt_cap_exceeded":
        return termination_reason
    if objective_root_cause == "stale_worker_result_run_id_mismatch":
        return objective_root_cause
    if watchdog_status == "stalled":
        return "watchdog_stalled_after_two_idle_windows"
    if watchdog_status == "failed":
        return "watchdog_observed_runtime_failure"
    if not process_success or worker_status == "failed":
        return str(worker_result.get("error", "") or "worker_failed")
    if objective_success is False:
        return objective_root_cause or "objective_failed"
    if not boundary_reached:
        return "requested_arc_boundary_not_reached"
    if stage3_summary and str(stage3_summary.get("status", "") or "") != "ok":
        return "stage3_current_session_sink_alignment_not_ok"
    if stage4_summary and str(stage4_summary.get("status", "") or "") != "ok":
        return "stage4_current_session_sink_alignment_not_ok"
    return ""


def derive_judgment(
    *,
    worker_result: dict[str, Any],
    watchdog_status: str,
    boundary_reached: bool,
    stage3_summary: dict[str, Any],
    stage4_summary: dict[str, Any],
    root_cause: str,
    process_success: bool | None = None,
    objective_success: bool | None = None,
) -> str:
    if watchdog_status == "stalled":
        return "stalled"
    if watchdog_status == "failed":
        return "failed"
    if process_success is None:
        process_success = str(worker_result.get("status", "") or "") == "success"
    if not process_success:
        return "failed"
    if objective_success is False:
        return "failed"
    if not boundary_reached:
        return "failed"
    if stage3_summary and str(stage3_summary.get("status", "") or "") != "ok":
        return "failed"
    if stage4_summary and str(stage4_summary.get("status", "") or "") != "ok":
        return "failed"
    return "success" if not root_cause else "failed"


def run_three_pass_audit(
    *,
    worker_result: dict[str, Any],
    boundary_reached: bool,
    stage3_summary: dict[str, Any],
    stage4_summary: dict[str, Any],
    judgment: str,
    root_cause: str,
    poll_history: list[dict[str, Any]],
) -> dict[str, Any]:
    pass1 = bool(worker_result) and bool(poll_history)
    pass2 = (judgment == "success") == (
        boundary_reached
        and str(stage3_summary.get("status", "") or "ok") == "ok"
        and str(stage4_summary.get("status", "") or "ok") == "ok"
        and not bool(root_cause)
    )
    pass3 = bool(judgment) and (
        (judgment == "success" and not root_cause) or (judgment != "success" and bool(root_cause))
    )
    passed = sum(1 for item in (pass1, pass2, pass3) if item)
    confidence = 60 + passed * 10
    if judgment == "success":
        confidence = 95 if passed == 3 else min(confidence, 90)
    else:
        confidence = min(confidence, 90)
    return {
        "passes": {
            "pass1_fact_extraction": pass1,
            "pass2_contradiction_check": pass2,
            "pass3_decision_audit": pass3,
        },
        "confidence": confidence,
        "finalized": confidence >= 95,
    }


def write_execution_ssot(analysis: dict[str, Any]) -> Path:
    dt = datetime.now()
    doc_dir = PROJECT_ROOT / "docs" / dt.strftime("%Y-%m-%d")
    doc_dir.mkdir(parents=True, exist_ok=True)
    arc_count = int(analysis.get("arc_count", 0) or 0)
    path = doc_dir / f"auto-frontier-lag-{arc_count}arc-runtime-analysis-ssot.md"
    lines = [
        f"# Auto Frontier Lag {arc_count}Arc Runtime Analysis SSOT",
        "",
        f"- generated_at: {analysis.get('generated_at', '')}",
        f"- project_locator: {analysis.get('project_locator', '')}",
        f"- judgment: {analysis.get('judgment', '')}",
        f"- root_cause: {analysis.get('root_cause', '') or 'none'}",
        f"- watchdog_status: {analysis.get('watchdog_status', '') or 'n/a'}",
        f"- shared_session_id: {analysis.get('shared_session_id', '') or '-'}",
        "",
        "## Input Profile",
        "",
        f"- manual_profile_doc: `{MANUAL_PROFILE_DOC}`",
        f"- harness_ssot_doc: `{HARNESS_SSOT_DOC}`",
        f"- arc_count: {analysis.get('arc_count', 0)}",
        "- worker_model: subprocess-owned Python worker booting `SovereignApp` via direct seams",
        "",
        "## Terminal Watchdog",
        "",
        "- review cadence: every 30 minutes from the terminal-owned watchdog",
        "- hard runtime cap: enforced when `max_runtime_seconds` is set; disabled when the cap is 0",
        f"- responsive process check interval: {PROCESS_CHECK_INTERVAL_SECONDS}s",
        "- graceful stop path: CTRL_BREAK / Ctrl+C first, terminate/kill only as fallback",
        f"- poll_count: {analysis.get('poll_count', 0)}",
        f"- poll_history_path: `{analysis.get('poll_history_path', '')}`",
        "",
        "## Evidence",
        "",
        f"- worker_status: {analysis.get('worker_status', '')}",
        f"- process_status: {analysis.get('process_status', '')}",
        f"- process_success: {analysis.get('process_success', False)}",
        f"- objective_status: {analysis.get('objective_status', '')}",
        f"- objective_success: {analysis.get('objective_success', False)}",
        f"- objective_root_cause: {analysis.get('objective_root_cause', '') or 'none'}",
        f"- continuity_canary_status: {((analysis.get('continuity_canary_report') or {}).get('status', 'not_available'))}",
        f"- continuity_canary_findings: {((analysis.get('continuity_canary_report') or {}).get('finding_count', 0))}",
        f"- boundary_reached: {analysis.get('boundary_reached', False)}",
        f"- pass_rate_monitor_exists: {analysis.get('pass_rate_monitor_exists', False)}",
        f"- stage3_current_session_status: {((analysis.get('stage3_current_session_sink_alignment_summary') or {}).get('status', 'missing'))}",
        f"- stage4_current_session_status: {((analysis.get('stage4_current_session_sink_alignment_summary') or {}).get('status', 'missing'))}",
        "",
        "## 3-Pass Audit",
        "",
        f"- pass1_fact_extraction: {analysis['three_pass_audit']['passes']['pass1_fact_extraction']}",
        f"- pass2_contradiction_check: {analysis['three_pass_audit']['passes']['pass2_contradiction_check']}",
        f"- pass3_decision_audit: {analysis['three_pass_audit']['passes']['pass3_decision_audit']}",
        f"- confidence: {analysis['three_pass_audit']['confidence']}%",
        f"- finalized: {analysis['three_pass_audit']['finalized']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def latest_session_id_from_rows(rows: list[Any]) -> str:
    for row in reversed(rows):
        if isinstance(row, dict):
            value = row.get("session_id")
        elif hasattr(row, "keys") and "session_id" in row.keys():
            value = row["session_id"]
        else:
            value = getattr(row, "session_id", None)
            if value is None and isinstance(row, list | tuple) and row:
                value = row[0]
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _read_attempt_counts(project_root: Path) -> tuple[int, int, int, int]:
    db_path = project_root / "project_data.db"
    if not db_path.exists():
        return (0, 0, 0, 0)
    db = DBManager(db_path)
    try:
        stage3_attempts = db.conn.execute("SELECT COUNT(*) FROM stage_attempts WHERE stage = 3").fetchone()[0]
        stage4_attempts = db.conn.execute("SELECT COUNT(*) FROM stage_attempts WHERE stage = 4").fetchone()[0]
        director_stage3 = db.conn.execute(
            "SELECT COUNT(*) FROM director_selections WHERE " + DBManager._director_stage_predicate(3)
        ).fetchone()[0]
        director_stage4 = db.conn.execute(
            "SELECT COUNT(*) FROM director_selections WHERE " + DBManager._director_stage_predicate(4)
        ).fetchone()[0]
        return (int(stage3_attempts), int(stage4_attempts), int(director_stage3), int(director_stage4))
    finally:
        db.close()


def _ensure_pass_rate_monitor(app: SovereignApp, project_root: Path) -> None:
    if getattr(app, "pass_rate_monitor", None):
        return
    app.pass_rate_monitor = PassRateMonitor(project_root)


def _terminate_process_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
    if ctrl_break is not None:
        try:
            process.send_signal(ctrl_break)
        except Exception:
            pass
        else:
            for _ in range(10):
                if process.poll() is not None:
                    return
                time.sleep(1)
    try:
        process.terminate()
    except Exception:
        return
    for _ in range(10):
        if process.poll() is not None:
            return
        time.sleep(1)
    try:
        process.kill()
    except Exception:
        pass


def _write_poll_history(project_root: Path, history: list[dict[str, Any]]) -> None:
    if not project_root.exists():
        return
    log_path = project_root / "logs" / "auto_frontier_lag_poll_history.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(item, ensure_ascii=False) for item in history]
    log_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _update_manifest(project_root: Path, payload: dict[str, Any]) -> None:
    path = project_root / "logs" / "auto_frontier_lag_harness_manifest.json"
    current = _read_json(path)
    current.update(payload)
    _write_json(path, current)


def _close_app_handles(app: SovereignApp) -> None:
    current_project = getattr(app, "current_project", None)
    if getattr(app, "memory", None):
        try:
            app.memory.close()
        except Exception:
            pass
        app.memory = None
    if current_project is not None and hasattr(current_project, "db"):
        try:
            current_project.db.conn.commit()
        except Exception:
            pass
        try:
            current_project.db.close()
        except Exception:
            pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
