# Auto Frontier Lag 2Arc Runtime Analysis SSOT

- generated_at: 2026-04-28T00:01:53
- project_locator: projects/auto_frontier_reaudit_probe_20260427_2arc
- judgment: stalled
- root_cause: watchdog_stalled_after_two_idle_windows
- watchdog_status: stalled
- shared_session_id: -

## Input Profile

- manual_profile_doc: `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`
- harness_ssot_doc: `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md`
- arc_count: 2
- worker_model: subprocess-owned Python worker booting `SovereignApp` via direct seams

## Terminal Watchdog

- review cadence: every 30 minutes from the terminal-owned watchdog
- hard runtime cap: enforced when `max_runtime_seconds` is set; disabled when the cap is 0
- responsive process check interval: 5s
- graceful stop path: CTRL_BREAK / Ctrl+C first, terminate/kill only as fallback
- poll_count: 21
- poll_history_path: `projects/auto_frontier_reaudit_probe_20260427_2arc/logs/auto_frontier_lag_poll_history.jsonl`

## Evidence

- worker_status: n/a
- process_status: n/a
- process_success: False
- objective_status: failed
- objective_success: False
- objective_root_cause: requested_arc_boundary_not_reached
- continuity_canary_status: not_available
- continuity_canary_findings: 0
- boundary_reached: False
- pass_rate_monitor_exists: True
- stage3_current_session_status: ok
- stage4_current_session_status: missing

## 3-Pass Audit

- pass1_fact_extraction: False
- pass2_contradiction_check: True
- pass3_decision_audit: True
- confidence: 80%
- finalized: False
