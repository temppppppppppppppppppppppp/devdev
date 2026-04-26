# Frontier Lag 5Arc Live Run Watchlist

Date: 2026-04-26
Status: draft-live-run-pending
Mode: live-run evidence watchlist, not a final audit
Project: `projects/0_골든카나리아`
Command:

```powershell
python scripts/run_auto_frontier_lag_harness.py run --arc-count 5 --target-project "0_골든카나리아" --reuse-existing-project --poll-interval-seconds 300
```

## 1. Purpose

Prepare the post-run audit checklist while the 5-arc Frontier Lag run is still active.

This document must not be used as a final success/failure judgment until the run reaches a terminal state. Mid-run DB, JSONL, dashboard, and log state are provisional evidence only.

## 2. Current Live Run Anchor

Observed at approximately 2026-04-26 17:18 KST:

- Harness PID: `18212`
- Worker PID: `3788`
- Manifest status: `frontier_running`
- Main session log: `projects/0_골든카나리아/logs/session_20260426_171125.log`
- Harness manifest: `projects/0_골든카나리아/logs/auto_frontier_lag_harness_manifest.json`
- Harness poll history: `projects/0_골든카나리아/logs/auto_frontier_lag_poll_history.jsonl`
- Worker result, after terminal state: `projects/0_골든카나리아/logs/auto_frontier_lag_worker_result.json`
- Runtime analysis, after terminal state: `projects/0_골든카나리아/logs/auto_frontier_lag_analysis.json`

Encoding note:
- Terminal rendering is navigational only.
- Do not classify Korean/CJK mojibake from PowerShell output as file corruption without byte-level UTF-8 readback.

## 3. Quick Monitor Commands

Process liveness:

```powershell
Get-Process python | Select Id, CPU, StartTime
```

Session log tail:

```powershell
Get-Content .\projects\0_골든카나리아\logs\session_20260426_171125.log -Tail 100
```

Live tail:

```powershell
Get-Content .\projects\0_골든카나리아\logs\session_20260426_171125.log -Tail 80 -Wait
```

Harness manifest:

```powershell
Get-Content .\projects\0_골든카나리아\logs\auto_frontier_lag_harness_manifest.json
```

Post-run analysis rerun, only after terminal state:

```powershell
python scripts/run_auto_frontier_lag_harness.py analyze --project "0_골든카나리아" --arc-count 5
```

## 4. Frontier Lag Contract To Verify

Source behavior in `main_a.py`:

- If the designed frontier is not the true final arc:
  - Stage3 target is `ep_end - 1`, bounded below by `ep_start`.
  - Stage4 target is `ep_end - 2`, bounded below by `ep_start`.
- If the designed frontier is the true final arc:
  - Stage3 target is `ep_end`.
  - Stage4 target is `ep_end`.
- This run requests `max_arc_advances=5`, so the expected boundary is 5 designed frontier advances unless the run fails, is stopped, or hits a guarded stop condition first.

## 5. Arc Progress Fill-In Table

Fill after the run or during periodic observation. Do not treat blanks as failures while the run is active.

| Arc | Stage2 design | Stage3 target/result | Stage4 target/result | Retry/skip/guard notes | Evidence paths |
| --- | --- | --- | --- | --- | --- |
| 1 | pending live evidence | pending live evidence | pending live evidence | pending live evidence | pending live evidence |
| 2 | pending live evidence | pending live evidence | pending live evidence | pending live evidence | pending live evidence |
| 3 | pending live evidence | pending live evidence | pending live evidence | pending live evidence | pending live evidence |
| 4 | pending live evidence | pending live evidence | pending live evidence | pending live evidence | pending live evidence |
| 5 | pending live evidence | pending live evidence | pending live evidence | pending live evidence | pending live evidence |

## 6. Authority Alignment Regression Checklist

These are the checks tied to the merged authority-alignment work.

- Stage4 truth-store fail-closed:
  - Look for `stage4_pass_settlement_status` evidence.
  - `fully_settled` must appear only when primary DB, WorldState, FactLedger, settlement packet, and human export are accepted by the settlement path.
  - Any `primary_persisted_meta_failed`, `settlement_packet_failed`, or `human_export_failed` must not be summarized as full PASS settlement.

- Manager-to-Bible fact boundary:
  - Existing `MasterBible.AssetLibrary.KeyNPCs` fields must not be blindly overwritten by Manager `new_lore`.
  - Existing-NPC differences should appear as `MasterBible.FactCommitProposals.ManagerKeyNPCDeltas`.
  - Truly new NPC entries may be appended.

- Verdict layer contract:
  - Stage2/Stage3/Stage4 payloads should distinguish `director_verdict` from `runtime_route_verdict`.
  - `final_judgment_authority` should remain `director_llm`.
  - `runtime_gate_authority` should remain `python_runtime_routing_gate`.
  - `verdict_contract_version` should be `verdict-layer-v1` where the new contract applies.

- Bridge/dashboard authority labels:
  - `run_completed` means subprocess lifecycle success, not canonical semantic completion.
  - Dashboard `proof_status` means proof artifact alignment only, not canonical PASS settlement authority.

## 7. Failure Or Pause Triage Triggers

If one of these appears, stop making success assumptions and preserve evidence first:

- Harness manifest changes to `worker_failed`.
- Worker result has `status` other than `success`.
- `frontier_result.stop_reason` is neither expected completion nor requested boundary.
- Stage3 skip prompt or exception skip path appears.
- Stage4 `stage4_zero_progress_blocked` or no manuscript progress while `stage4_alignment=backlog`.
- Repeated attempt overflow beyond the configured operational attempt cap.
- Python worker process exits before `auto_frontier_lag_worker_result.json` is written.
- Runtime logs show settlement failure after a PASS candidate.

## 8. Post-Run Merge Audit Steps

Run these only after terminal state:

1. Read `auto_frontier_lag_worker_result.json`.
2. Read `auto_frontier_lag_analysis.json`, or regenerate it with the analyze command above.
3. Read `auto_frontier_lag_poll_history.jsonl`.
4. Read `runtime_audit_summary.json`, `pass_rate_monitor.json`, and `runtime_audit.jsonl`.
5. Inspect DB counts for Stage2, Stage3, Stage4 attempts and director selections.
6. Inspect produced artifacts, not just logs:
   - `plans/blueprints`
   - `drafts`
   - `logs/artifacts`
   - settlement packets when present
7. Merge live evidence with this watchlist.
8. Only then write a post-run merged 3-pass audit.
9. Create execution SSOT and `docs/temp` mirror only if the merged audit finds action-bearing issues.

## 9. Provisional Non-Conclusions

- This document does not claim the run succeeded.
- This document does not claim the run failed.
- This document does not close any issue.
- This document does not create or update the active temp execution queue.
- This document only prepares the evidence lanes for post-run interpretation.

## 10. Document 3-Pass Audit

Pass 1 - structure and scope:
- PASS. The document is a watchlist/template for an active live run, not a final survey or closure note.

Pass 2 - evidence and consistency:
- PASS. Live evidence anchors are limited to observed liveness, manifest status, log paths, and source-level Frontier Lag contract.
- PASS. No mid-run state is promoted to final success/failure truth.

Pass 3 - operational safety:
- PASS. The document preserves the live-run merge rule: final conclusions wait for terminal state and post-run merged audit.
- PASS. No `docs/temp` execution mirror is created.

Confidence:
- Estimated confidence for the watchlist shape: 96%.
- Estimated confidence for run outcome: not applicable while live-run is active.
