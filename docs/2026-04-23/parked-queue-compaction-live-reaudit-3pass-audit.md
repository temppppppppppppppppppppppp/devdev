# Parked Queue Compaction Live Re-Audit

Date: 2026-04-23
Status: final (3-pass compaction re-audit; queue visibility is now limited to live, still-actionable lanes, while candidate-only, missing-anchor, and already-landed historical items are retired from the temp queue)
Canonical Path: `docs/2026-04-23/parked-queue-compaction-live-reaudit-3pass-audit.md`
Baseline Commit: `30b9436fc3a5c3fcc3f6397bf23bfe45d24af918`
Baseline Dirty Summary: `dirty: prior queue-refresh docs/temp deltas still present; untracked docs/2026-04-23/; unrelated project/test log drift left untouched`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`

## 1. Intent

Re-audit the remaining parked and blocked temp queue items against the live workspace, then keep only lanes that are still honest current execution debt.

This is a codebase-centered compaction pass, not a fresh realization wave.

## 2. Evidence Base

Live workspace checks used in this pass:

- `Stage4InterviewRound` still exists in `modules/core/stage4_interview_round.py`
- current AST recount for `Stage4InterviewRound`: `170` methods, `6` methods at `120+ LOC`, `3` methods at `180+ LOC`
- `main_a.py` still contains the non-canonical Stage0 treatment-enrichment utility path:
  - `_collect_treatment_enrichment_candidates`
  - `_confirm_treatment_enrichment_plan`
  - `_run_treatment_block_parallel_enrichment`
  - `_save_enriched_treatment_blocks`
  - `_enrich_treatment_blocks`
- Stage0 BI/TR runtime-handoff contract surfaces still exist in:
  - `modules/core/stage0_handoff.py`
  - `modules/core/project_manager.py`
  - `modules/core/stage2_orchestrator.py`
  - `scripts/build_bi_from_phase0_and_tr.py`
- `scripts/run_auto_frontier_lag_harness.py` now has soak-profile support, reduced manuscript-length overrides, and heavy-path toggles
- the same soak harness still does not audit `episode_bibles`, `state_logs`, or `world_state`
- `npc_martial_state_changes` is now visibly wired through:
  - `modules/models/arc.py`
  - `modules/core/response_schemas.py`
  - `modules/domain/agents/analyst.py`
  - `modules/domain/agents/state_tracker.py`
  - `modules/domain/agents/state_tracker_npc.py`
  - `modules/core/stage4_post_pass_runtime.py`
  - `modules/core/world_state.py`
- targeted pytest verification passed for npc-martial and frontier-soak surfaces:
  - `11 passed` for npc-martial schema/preserve/bridge/world-state/rollback coverage
  - `12 passed` for soak-profile override coverage
- `projects/00_0420` is absent
- only `projects/_manual_backup/00_0420_*` trees remain for that lane
- `projects/00_260421` exists, but it is only a shallow draft tree and not a trustworthy one-to-one successor anchor
- `projects/0_0` is absent
- only disposable `_canary/canary_0_0_*` trees remain for the old `0_0` readiness lane
- root `.env` still exists and `modules/api/bridge_server.py` still lacks in-file auth/CORS middleware, so the audit-report candidate memo remains factually relevant even though it is not a bounded current execution order

## 3. Classification

Keep on the visible queue:

1. `stage234-session-memory-max-utilization`
   - fresh 2026-04-23 lane, still code-grounded, not stale
2. `0_0-stage4-interview-round-owner-surface-reduction-remediation`
   - honest parked architecture debt; the owner surface is still large enough to justify a future lane
3. `stage0-treatment-enrich-retirement-remediation`
   - honest parked hygiene debt; the non-canonical enrich utility is still present
4. `stage0-bi-tr-production-harness-normalization-remediation`
   - honest parked source-of-truth debt; runtime handoff normalization is still not closed
Retire from the visible queue and preserve as canonical historical backing only:

1. `audit-report-candidate-revalidation-remediation`
   - candidate-only memo, not a bounded implementation order
   - surviving concerns remain either unaccepted for realization or better represented by more specific lanes
2. `00_0420-s2-s3-s4-authority-alignment-remediation`
   - original live project anchor is gone
   - manual backups remain, but the lane is no longer an honest visible blocked item
3. `0_0-stage2-stage3-stage4-readiness-remediation`
   - original run-specific anchor is gone
   - disposable canary residue is not enough to justify keeping the old blocked item on the board
4. `npc-martial-state-substrate-wave1`
   - wave1 storage substrate is now code-visible and test-backed across the intended path
   - the old blocked queue item is therefore landed history, not current blocked work
5. `frontier-lag-soak-canary-wave1`
   - soak-profile overrides already landed
   - the remaining durability-surface audit block is low ROI for the current board and is intentionally deactivated

## 4. Pass 1

- rechecked every remaining parked or blocked item against live code or live project-anchor evidence
- separated live implementation debt from candidate-only or missing-anchor residue
- required a code-visible or anchor-visible reason for anything that remained on the board

## 5. Pass 2

- refused to keep candidate-only governance memos on the visible queue unless they still represented a bounded implementation order
- refused to keep missing-anchor blocked items merely because backup directories still existed
- refused to keep the npc-martial substrate as blocked once the intended schema-to-world-state path was clearly landed and test-backed

## 6. Pass 3

- the compacted queue now represents only live, still-actionable parked debt
- closed items remain preserved canonically, but their temp mirrors should be removed
- ClickUp should reflect the same split: five parked items remain visible, four items move to `Closed`

Confidence: 98/100
