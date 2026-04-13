# Stage3 Cross-PC Proof Rerun Handoff Context

Date: 2026-04-13
Status: handoff context after tranche-3 static closure; the later same-day live rerun plus bounded producer-side landings are now superseded by one bounded tactical-authority synonym parity tranche before the `ep7/ep8` proof rerun
Audience: next operator continuing on another PC

## Purpose

- preserve the exact Stage3 context after the three-tranche safe route
- let the next operator continue from `pull -> context load -> bounded next action` without losing the tranche baseline
- avoid re-mixing unrelated live-run/material dirt into the Stage3 proof wave

## 2026-04-13 Late Update

- a later local rerun captured in `0_temp.txt` already exercised the post-tranche-3 `ep7/ep8` path on the live workspace
- the newer authoritative next-step note is now:
  - `docs/2026-04-13/stage3-ep8-cw-director-root-cause-parallel-survey.md`
  - `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
  - `docs/2026-04-01/active-temp-execution-roadmap.md`
- read this document as tranche-context preservation, not as the newest queue controller
- the bounded producer-side contract-alignment / route-honest failure-surface slice called for by that survey is now landed on current `main`
- the later same-day `P2/P3` producer follow-up slice is now also landed on current `main`:
  - Stage2 shortlist now prefers actionable mission-packet candidates when available
  - Stage3 placeholder `protagonist_state` shells now fail cheap admission
  - Stage4 degraded fallback order now prefers the least-bad manuscript contract trace explicitly
- the newer bounded opening-transition producer-parity support slice is now also landed on current `main`:
  - Stage3 request/sanitize flow now threads `prev_blueprint` into cheap admission
  - declared alias forms now normalize into canonical `opening_transition.type`
  - missing `opening_transition` payloads can now be inferred before cheap admission when local opening-scene continuity is already sufficient
- the newer bounded tactical-authority / scene-completeness producer support slice is now also landed on current `main`:
  - Stage3 cheap admission now rejects scene shells that still lack actionable `key_events`
  - Stage3 sanitize now rejects obvious unauthorized tactical intrusion events before validator spend when the current episode authority does not already include them
  - the Stage3 producer prompt/checklist now makes both contracts explicit
- the later adversarial audits are now the newer queue controller for the front residual:
  - `docs/2026-04-13/stage3-producer-contract-tightening-3pass-audit-and-adversarial-review.md`
  - `docs/2026-04-13/stage3-producer-adversarial-followup-x3-addendum.md`
- those audits promote one stronger parent-owned blocker:
  - Korean synonym tactical-intrusion phrasing can still survive producer sanitize and validator Python prevalidation outside the current marker lexicon
- current next step is therefore no longer the paid rerun itself:
  1. one bounded tactical-authority synonym parity tranche
  2. then one bounded paid `ep7/ep8` rerun

## Authoritative Code Baseline

- branch: `main`
- code baseline for the next proof rerun: `6e66021f96a545df1072030aab90c9388bccab26`
- commit title: `refactor: introduce stage3 blueprint patch ir`

Recent Stage3 tranche chain:

1. `765132d8` `chore: snapshot stage3 safe-routing baseline`
2. `7b0961e8` `refactor: extract stage3 repair router`
3. `e30808a3` `fix: enforce stage3 local repair contract gate`
4. `6e66021f` `refactor: introduce stage3 blueprint patch ir`

Meaning:

- tranche 1 consolidated Stage3 repair routing authority
- tranche 2 made local patch entry fail closed without a ready contract
- tranche 3 opened the first bounded Stage3 patch-IR lane for leaf/path-scoped targets

## What Landed

### Tranche 1

- `Stage3RepairRouter` is now the single routing surface for retry reopen and `PASS_WITH_FIX` repair decisions
- file anchor: [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:181)

### Tranche 2

- Stage3 local patch entry now fails closed without a ready local-fix contract
- missing `authoritative_fix_scope`, `patch_target_records`, `must_fix`, or `success_condition` routes back to regenerate
- file anchor: [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:601)

### Tranche 3

- first bounded patch-IR lane added for Stage3 leaf/path-scoped targets
- supported target kinds:
  - `dialogue`
  - `entity_ref`
  - `field_value`
  - `local_phrase`
  - `local_sentence`
- target snapshots must resolve against the original blueprint before the local patch call
- unresolved or malformed patch payloads fail closed
- broader `scene_block`-style repair intentionally remains on the legacy whole-blueprint lane for now
- file anchors:
  - [stage3_blueprint_patch_ir.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/stage3_blueprint_patch_ir.py:1)
  - [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:143)
  - [blueprint_generator.yaml](/c:/Users/wjjo/Desktop/글도비/config/prompts/blueprint_generator.yaml:1)

## What Did Not Change

- no broad `DecisionKernel` migration
- no new queue compaction wave
- no fresh live rerun after tranche 3 yet
- no broader generator redesign beyond the bounded patch-IR lane

## Static Validation Status

These passed on the tranche-3 code baseline:

1. `python -m pytest -q tests/test_blueprint_patch_mode.py`
   - result: `72 passed`
2. `python -m pytest -q tests/test_unified_blueprint_validator_lane_c.py`
   - result: `29 passed`
3. `python -m pytest -q tests/test_stage3_orchestrator_handle_success_lane_c.py`
   - result: `3 passed`
4. `python -m pytest -q tests/chaos/test_stage3_metrics.py`
   - result: `5 passed`
5. `py_compile`
   - touched Stage3 files compiled successfully
6. `python scripts/check_utf8_hygiene.py ...`
   - passed for touched code/config/doc files
7. `python scripts/ops_validator.py --strict`
   - passed with canonical/temp mirror integrity intact

## Immediate Next Action

The earlier proof-first reading was temporarily superseded while one bounded producer-side tranche landed.

That tranche is now landed on the current live workspace.

The current next action is:

1. one bounded tactical-authority synonym parity tranche across producer and validator
2. then one bounded `ep7/ep8` proof rerun
3. only after that rerun, closure bookkeeping or the next longer-horizon refactor lane

## Important Environment Notes For Another PC

- `main` is SSOT
- use `git switch main` then `git pull --ff-only`
- root `.env` is not tracked; make sure the new PC has the required model/provider keys locally
- previous failures on this machine were caused by missing Anthropic credentials in root `.env`
- previous vector-memory errors on this machine were caused by running a Python interpreter without `sqlite-vec`

Minimum local readiness checks on the next PC:

1. confirm the intended Python interpreter
2. confirm local env contains the needed provider keys
3. confirm `sqlite-vec` imports on that interpreter
4. only then start the bounded proof rerun

## Dirty Worktree Warning

This workspace currently contains unrelated local dirt that was intentionally kept outside the Stage3 tranche commits.

Main categories:

- live-run evidence and generated artifacts under `projects/000_260412_a/`
- `0_temp.txt`
- material/clickup sync files
- material queue helper scripts/tests

Do not fold those into the Stage3 proof follow-up unless you are making a separate evidence or material-side commit on purpose.

## Canonical Reading Order On The Next PC

1. [stage3-three-tranche-safe-sequencing-plan.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-three-tranche-safe-sequencing-plan.md:175)
2. [0_0-stage3-contract-tightening-remediation-execution-ssot.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md:709)
3. [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:1)
4. this handoff note

## Operator Intent To Preserve

- move slowly
- keep tranche boundaries explicit
- prefer static safety over extra token spend
- do not widen scope during the next proof rerun
- keep commits narrow on `main`
