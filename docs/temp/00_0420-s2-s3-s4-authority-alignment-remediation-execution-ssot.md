# 00_0420 S2-S3-S4 Authority Alignment Remediation Execution SSOT

Date: 2026-04-21
Status: active (3-pass audited; formal authority survey completed; tranche A/B implementation authorized in the same turn)
Canonical Path: `docs/2026-04-21/00_0420-s2-s3-s4-authority-alignment-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/00_0420-s2-s3-s4-authority-alignment-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `e9b45933c1e0ba1b61528f466e6b7415494a698b`
- Baseline Dirty Summary: `dirty workspace with existing canary/manual-backup/runtime/docs-temp drift; Stage4 rerun frozen before this SSOT; no unrelated cleanup performed`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD with canonical audit + execution SSOT creation in this lane; no temp roadmap rewrite because this was a user-directed immediate remediation lane`
Source Survey Docs:
- `docs/2026-04-21/00_0420-s2-s3-s4-authority-alignment-3pass-audit.md`
- `docs/2026-04-21/stage3-authority-alignment-post-run-merge-audit.md`
Evidence Artifacts:
- `projects/00_0420/plans/arcs/arc_001.txt`
- `projects/00_0420/plans/blueprints/blueprint_0004.txt`
- `projects/00_0420/drafts/ep_0003.txt`
- `projects/00_0420/logs/session/decisions.jsonl`
- `projects/00_0420/logs/session/llm_io.jsonl`
- `projects/00_0420/logs/session_20260421_070730.log`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/core/stage4_retry_runtime.py`
Side-Effect Coverage: covered

## 1. Intent

Realize the minimum structural fixes that will buy real forward motion on `projects/00_0420`:

- reduce Stage3 false-pass probability for under-surfaced early-episode blueprints
- reduce Stage4 post-select retry looping on contaminated near-pass baselines
- preserve the ability to rerun `S3 ep4` and `S4 ep4` on a cleaner authority surface

This wave is not:

- a full Stage2 redesign
- a manual artifact rewrite-only band-aid
- a whole-project rerun before code changes land

## 2. Baseline Facts

- `ep1~3` manuscript truth exists.
- `ep4` is the first blocked frontier.
- `Stage4` currently rejects for continuity/history/PB-role drift more than for numeric carryover.
- `Stage3` already contains work-identity opening doctrine, but the current heuristic remains too lenient for multi-location early-episode setups.
- `Stage4` already has strong post-select truth detection, but retry still over-preserves bad near-pass baselines.

## 3. Scope

Included:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage4_retry_runtime.py`
- bounded supporting tests in:
  - `tests/test_unified_blueprint_validator_lane_c.py`
  - `tests/test_stage4_interview_round.py`
- canonical audit / execution SSOT / temp mirror updates

Deferred but tracked:

- `modules/core/stage4_context_builder.py` carryover prompt dedupe for stale `pending_actions`
- Stage2 authority packet / arc regeneration policy
- settlement/world-state PB role relabel normalization

Excluded in this wave:

- DB schema changes
- large Stage4 retry-architecture redesign
- project artifact hand-edits as the primary fix
- Stage4 rerun before tranche verification passes

## 4. Remediation Thesis

The next useful fix is not “make Stage4 more persuasive.”

The next useful fix is:

1. stop a weak ep4 blueprint from passing so easily
2. stop Stage4 from reusing that weak path once post-select truth has already proved it wrong

## 5. Execution Tranches

### Tranche A. Stage3 early-opening doctrine hardening

Goal:

- make `work_identity_opening` binding stricter for early-episode multi-location setups

Realization:

- remove or narrow the current multi-location escape hatch in `UnifiedBlueprintValidator._collect_work_identity_opening_issues()`
- require stronger visible evidence of `private receipt / observer shift / next gate` instead of treating spatial movement alone as sufficient

Acceptance target:

- a blueprint shaped like current `blueprint_0004.txt` should no longer glide through purely because it spans several rooms

### Tranche B. Stage4 post-select reuse/duplicate-suppression hardening

Goal:

- stop rewrite-required `post_select_conflict` attempts from auto-bypassing duplicate suppression just because a reuse contract exists

Realization:

- keep reuse contracts for observability and bounded local-fix paths
- but only let reuse bypass duplicate suppression when the conflict contract still qualifies as bounded/local and non-rewrite

Acceptance target:

- continuity/history-heavy post-select conflicts should no longer encourage same-track retries by default

### Tranche C. Verification and rerun gate

Goal:

- prove the bounded fixes with tests before any new live rerun

Realization:

- targeted pytest shards
- compile checks on touched production files
- then rerun sequence:
  - `Stage3 ep4`
  - if improved, `Stage4 ep4`

## 6. Pass 1. Inventory Summary

Owners in this wave:

- Stage3 doctrine owner:
  - `UnifiedBlueprintValidator._collect_work_identity_opening_issues()`
- Stage4 retry owner:
  - `Stage4RetryRuntime.suppress_equivalent_retry_candidates()`

Test surfaces:

- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_stage4_interview_round.py`

## 7. Pass 2. Semantic Classification

- Class A. Realize now
  - Stage3 doctrine hardening
  - Stage4 duplicate-suppression bypass hardening

- Class B. Queue immediately after rerun evidence
  - Stage4 carryover `pending_actions` dedupe

- Class C. Defer unless the lane still stalls
  - Stage2 handoff regeneration / doctrine refresh
  - PB role label normalization across settlement/world-state

## 8. Side-Effect Map

- file writes / artifacts:
  - future Stage3 blueprints and Stage4 retries will change behavior
  - no direct project artifact rewrite in this tranche

- DB / schema:
  - none planned

- JSONL / log / sink behavior:
  - Stage3 prevalidation may emit stronger `work_identity_opening` binding issues
  - Stage4 retry path may suppress repeated identical candidates more often on post-select conflicts

- retry / recovery:
  - intended behavioral change; this is the point of the wave

- config / env:
  - none

## 9. Acceptance Criteria

- Stage3 flags early-episode work-identity drift even when the blueprint uses several locations without actually surfacing the required authority ladder
- Stage4 duplicate suppression is no longer bypassed for rewrite-required continuity/history post-select conflicts
- targeted tests cover both changes
- no new large-function complexity regression is introduced

## 10. Verification Plan

- `pytest tests/test_unified_blueprint_validator_lane_c.py -q`
- `pytest tests/test_stage4_interview_round.py -q -k "duplicate suppression or work_identity_opening"`
- `python -m compileall modules/domain/agents/unified_blueprint_validator.py modules/core/stage4_retry_runtime.py`

Post-patch live gate:

1. rerun `Stage3 ep4`
2. inspect whether `blueprint_0004`-class PB procedural replay still passes
3. if improved, rerun `Stage4 ep4`

## 11. Guardrails

- do not rerun Stage4 first
- do not convert this wave into a general Stage2 redesign
- do not hand-edit `projects/00_0420` artifacts as the primary fix path
- keep Director authority intact; these are pre-Director / retry-lane contract hardenings, not Director bypasses

## 12. Temp Queue Notes

- temp queue status: redirected sibling lane; no parked temp execution artifact was realized in this turn
- this SSOT is an immediate user-directed lane and should not be blocked on the parked roadmap
- temp mirror removal condition:
  - after code patch + verification + closure audit + rerun proof

## 13. Execution-Start Rule

This document is already 3-pass audited against the live workspace state observed in this turn.

Because implementation begins immediately in the same turn, the effective confirmation rule is:

- use this SSOT as the bounded patch contract for tranche A/B only
- if scope expands beyond those owners, rerun the 3-pass audit first
