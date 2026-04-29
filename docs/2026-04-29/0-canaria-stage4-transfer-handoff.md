# 0 Canaria Stage4 Transfer Handoff

Date: 2026-04-29
Status: transfer handoff
Track: system pipeline / live-run follow-up

Commit State:
- Baseline Commit: `8a1463b237499b2aa0d56ea95a67eac54d2cefb9`
- Baseline Dirty Summary: `dirty: mixed system code/docs, active temp SSOT mirror, generated 0_카나리아 project snapshot, and unrelated material-side work`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at document creation`

## Purpose

This document freezes the operator context for moving the current pipeline state through GitHub main before resuming on another PC.

The intended operating decision is:

1. Save and publish the current system-pipeline context.
2. Merge the transfer PR to `main`.
3. Pull `main` on the other PC.
4. Address the pipeline issues in priority order.
5. Only after the frontier is corrected, resume the canary toward episode 15.

## Current Run State

Project:
- `projects/0_카나리아`

Observed terminal state:
- Stage4 was stopped by the operator after episode 5 completed.
- No active run process should be assumed.
- Episode 5 final manuscript and settlement were written.

Episode 5 accepted branch:
- total capital/assets: `20억`
- active WTI position: `15억`
- remaining cash/deposit: `5억`
- contract month: `3월물`
- location: `한미증권 VIP룸`

Important caveat:
- Stage4 recovered episode 5 by creating a retroactive bridge from episode 4's full `20억 전액` order into a `15억 locked + 5억 remaining` broker/system-cap state.
- This branch is usable only if the Director accepts it as canon and the downstream frontier is regenerated or realigned.

## Stop Condition

Do not resume Stage4 episode 6 directly from the current Stage3 frontier.

Reason:
- Current `blueprint_0006` still repeats or depends on stale events that episode 5 already handled.
- Continuing directly risks duplicate order execution, stale `가승인` surfaces, duplicate hotline/priority-line beats, and rejected/provisional attempt facts leaking back into the run.

## Pipeline Priority

### P1-1. Issue #121

`[P1][Stage3/Stage4] Frontier blueprint staleness after Stage4 completes prior event`

URL:
- https://github.com/temppppppppppppppppppppppp/devdev/issues/121

Priority:
- highest pipeline blocker

Required before episode 6 resume:
- detect stale Stage3/Arc frontier after prior Stage4 manuscript acceptance
- pass actual prior manuscript context into Stage4-triggered blueprint regeneration
- expand completed-event replay checks to actual prior manuscript evidence
- decide whether downstream ep6+ blueprints are refreshed together or explicitly marked contaminated

### P1-2. Issue #120

`[Stage3] Genre strategy contract not applied when project genre lives outside bible._genre`

URL:
- https://github.com/temppppppppppppppppppppppp/devdev/issues/120

Priority:
- second pipeline fix

Reason:
- genre contract exists in code but did not apply for the current investment project shape
- current canary survived mostly because the investment material gravity was strong
- weaker projects may drift harder if `action_focused` is not genre-normalized

### P2. Issue #113

`[Stage4] Harden initial draft transitions, headers, and scene structure`

URL:
- https://github.com/temppppppppppppppppppppppp/devdev/issues/113

Priority:
- quality hardening after the frontier and genre-contract blockers

### Measurement Follow-Ups

Use after stabilization, not before:
- #64: context-cache and session-memory impact on recovery
- #62: early-April vs current Stage4 reject/attempt rates
- #63: runtime, token, and cost efficiency

## Transfer Scope Recommendation

Include in the transfer PR:
- system code fixes already made for network/transient failure classification
- targeted tests for those fixes
- dated system docs from 2026-04-29 that describe the current pipeline findings
- the `docs/temp/` mirror for the active Stage3 genre-contract execution SSOT
- this handoff document
- optionally, the generated `projects/0_카나리아` snapshot if the other PC must resume from the exact local run state

Exclude from the transfer PR unless explicitly intended:
- unrelated `material_ssot` changes
- `healthy_heir_group_succession` treatment/BI/work_guard artifacts
- unrelated root scratch changes such as `0_temp.txt`
- cardnews HTML/PDF/PNG presentation artifacts unless the PR is meant to publish those docs too

Project snapshot note:
- local `projects/0_카나리아` is about 36.8 MB across 160 files at handoff inspection
- it is not currently tracked in git
- if exact other-PC resume is required via `main` alone, this snapshot must be included or separately transferred

## Other-PC Resume Checklist

After pulling `main` on the other PC:

1. Confirm the branch includes the intended transfer PR.
2. Confirm whether `projects/0_카나리아/project_data.db` exists locally.
3. If the project snapshot is absent, do not claim exact run resume from git alone.
4. Treat episode 5 as the latest accepted Stage4 output.
5. Decide Director canon for the `15억 3월물 + 5억 remaining` branch.
6. Resolve #121 before any episode 6 production run.
7. Resolve or stage #120 before relying on further investment-action Stage3 ensemble output.
8. Re-run or regenerate the downstream frontier before continuing to episode 15.

## Guardrails

- Python may detect, route, collect, and format evidence; it must not overwrite narrative facts by judgment.
- Director remains the final owner of canon acceptance, especially for the episode 5 branch.
- Final accepted artifacts and post-pass contracts outrank rejected/provisional attempt surfaces.
- Rejected attempt logs with PASS-like intermediate metadata must not be used as downstream truth.

## Document 3-Pass Audit

Pass 1, structure and scope:
- document type is transfer handoff
- scope is limited to pipeline transfer and resume control
- included and excluded PR surfaces are explicit

Pass 2, evidence and consistency:
- issue priority matches the GitHub issue inventory reviewed on 2026-04-29
- episode 5 state matches the final manuscript/settlement survey
- project snapshot size and tracked state are bounded to inspection-time evidence

Pass 3, execution and readability:
- next actions are ordered
- stop condition is explicit
- other-PC checklist is actionable
- no code or fact mutation is authorized by this document

Estimated Confidence:
- `96%`
