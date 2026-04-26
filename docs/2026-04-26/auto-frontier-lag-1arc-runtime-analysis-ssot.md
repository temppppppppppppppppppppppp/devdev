# Auto Frontier Lag 1Arc Runtime Analysis SSOT

- generated_at: 2026-04-26T22:24:23
- project_locator: projects/auto_t8_smoke_20260426_214331_1arc
- judgment: success
- root_cause: none
- watchdog_status: n/a
- shared_session_id: 20260426_214335

## Input Profile

- manual_profile_doc: `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`
- harness_ssot_doc: `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md`
- arc_count: 1
- worker_model: subprocess-owned Python worker booting `SovereignApp` via direct seams

## Terminal Watchdog

- review cadence: every 30 minutes from the terminal-owned watchdog
- no hard process timeout was part of the contract
- responsive process check interval: 5s
- graceful stop path: CTRL_BREAK / Ctrl+C first, terminate/kill only as fallback
- poll_count: 36
- poll_history_path: `C:\Users\PC\Desktop\글도비\projects\auto_t8_smoke_20260426_214331_1arc\logs\auto_frontier_lag_poll_history.jsonl`

## Evidence

- worker_status: success
- process_status: success
- process_success: True
- objective_status: success
- objective_success: True
- objective_root_cause: none
- boundary_reached: True
- pass_rate_monitor_exists: True
- stage3_current_session_status: ok
- stage4_current_session_status: ok

## 3-Pass Audit

- pass1_fact_extraction: True
- pass2_contradiction_check: True
- pass3_decision_audit: True
- confidence: 95%
- finalized: True
