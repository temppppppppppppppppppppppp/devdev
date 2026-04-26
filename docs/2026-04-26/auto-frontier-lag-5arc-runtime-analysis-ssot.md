# Auto Frontier Lag 5Arc Runtime Analysis SSOT

- generated_at: 2026-04-26T18:49:03
- project_locator: projects/0_골든카나리아
- judgment: failed
- root_cause: requested_arc_boundary_not_reached
- watchdog_status: progressing
- shared_session_id: 20260426_171126

## Input Profile

- manual_profile_doc: `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`
- harness_ssot_doc: `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md`
- arc_count: 5
- worker_model: subprocess-owned Python worker booting `SovereignApp` via direct seams

## Terminal Watchdog

- review cadence: every 30 minutes from the terminal-owned watchdog
- no hard process timeout was part of the contract
- responsive process check interval: 5s
- graceful stop path: CTRL_BREAK / Ctrl+C first, terminate/kill only as fallback
- poll_count: 21
- poll_history_path: `C:\Users\PC\Desktop\글도비\projects\0_골든카나리아\logs\auto_frontier_lag_poll_history.jsonl`

## Evidence

- worker_status: success
- boundary_reached: False
- pass_rate_monitor_exists: True
- stage3_current_session_status: warn
- stage4_current_session_status: warn

## 3-Pass Audit

- pass1_fact_extraction: True
- pass2_contradiction_check: True
- pass3_decision_audit: True
- confidence: 90%
- finalized: False
