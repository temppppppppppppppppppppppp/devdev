# Auto Frontier Lag 1Arc Runtime Analysis SSOT

- generated_at: 2026-04-28T14:34:45
- project_locator: projects/auto_frontier_post107_probe_20260428_2arc
- judgment: stalled
- root_cause: watchdog_stalled_after_two_idle_windows
- watchdog_status: stalled
- shared_session_id: 20260428_130354
- status: draft evidence only

## Input Profile

- manual_profile_doc: `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`
- harness_ssot_doc: `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md`
- arc_count: 1
- worker_model: subprocess-owned Python worker booting `SovereignApp` via direct seams

## Terminal Watchdog

- review cadence: every 30 minutes from the terminal-owned watchdog
- hard runtime cap: enforced when `max_runtime_seconds` is set; disabled when the cap is 0
- responsive process check interval: 5s
- graceful stop path: CTRL_BREAK / Ctrl+C first, terminate/kill only as fallback
- poll_count: 17
- poll_history_path: local evidence archive manifest entry for `auto_frontier_post107_probe_20260428_2arc`

## Evidence

- worker_status:
- process_status:
- process_success: False
- objective_status: failed
- objective_success: False
- objective_root_cause: requested_arc_boundary_not_reached
- continuity_canary_status: not_available
- continuity_canary_findings: 0
- boundary_reached: False
- pass_rate_monitor_exists: True
- stage3_current_session_status: ok
- stage4_current_session_status: ok

## 3-Pass Audit

- pass1_fact_extraction: False
- pass2_contradiction_check: True
- pass3_decision_audit: True
- confidence: 80%
- finalized: False

## Handling

This file records the raw 1-arc watchdog evidence observed during the frontier proof wave.
It is intentionally not promoted to a finalized closure claim because pass1 confidence was below the 95% document-save threshold.
