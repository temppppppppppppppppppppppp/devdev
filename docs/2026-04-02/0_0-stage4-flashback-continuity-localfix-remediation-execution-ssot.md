# 0_0 Stage4 Flashback Continuity LocalFix Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (code landed, static validation closed, fresh full-run positive proof captured; residual replay/repetition warning and final-sink closure still open)
Canonical Path: `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5ef5f7ab2f2bbd36c2e8168cfd6d9b096caadc0f`
- Baseline Dirty Summary: `dirty: 0_temp.txt modified, 0_tempdd.tz untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `structured flashback metadata persistence and zero-to-local fix synthesis landed; static validation closed; fresh full-run proof in projects/00_20260403 now shows ep2 can PASS, but replay/repetition warning evidence and final-sink gaps remain`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/2026-04-03/0_0-stage34-ep2-fresh-run-post-run-merge-audit.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-evidence.json`
- `docs/2026-04-03/0_0-stage34-ep2-fresh-run-post-run-merge-evidence.json`
Parent Lane:
- `0_0-stage4-consumer-contract-normalization-remediation`
- `0_0-stage2-stage3-stage4-readiness-remediation`

## 1. Answer First

The fresh full run changed the status of this seam:

- Stage4 can now get `ep2` through a bounded `PASS_WITH_FIX -> inplace patch -> PASS` path
- but replay/repetition warning evidence still survives the final ep2 opening and the final-sink proof surfaces are still incomplete

This lane therefore remains justified as one bounded residual contract:

`Flashback continuity contradiction -> structured metadata -> bounded local fix_pack`

This is not a Stage2 change, not a Stage3 change, and not a broad Flashback rewrite.

## 2. Scope

Included:

- `modules/core/flashback_verifier.py`
- `modules/core/stage4_interview_round.py`
- focused Stage4 / Flashback regression tests
- roadmap/temp queue refresh

Excluded:

- broad FlashbackVerifier redesign
- Stage2 contract normalization
- Stage3 contract tightening realization
- fresh canary in this document
- Stage4 resume declaration
- DB schema redesign
- artifact rewrites in `projects/`

## 3. Execution Tranches

### Tranche 1. Structured Flashback Contradiction Metadata

Goal:

- let `FlashbackVerifier` emit structured optional metadata that Stage4 can reuse for bounded repair routing

Bounded targets:

- `flashback_verifier.py`

Acceptance shape:

- parsed payload may preserve optional fields such as:
  - contradiction subtype
  - local-fix eligibility
  - patch anchor
  - expected truth / repair hint
- legacy flat payload remains backward-compatible

### Tranche 2. Flashback Metadata Persistence Into Stage4

Goal:

- retain per-candidate flashback metadata in Stage4 instead of flattening it into display-only text

Bounded targets:

- `stage4_interview_round.py`

Acceptance shape:

- `_advisory_flashback()` still returns Director-facing advisory text
- but it also stores structured flashback metadata into `_last_advisory_metadata`
- candidate index linkage survives

### Tranche 3. Zero-to-Local Fix Synthesis For Bounded Flashback Contradictions

Goal:

- when a Flashback contradiction is clearly local and the round is otherwise `PASS_WITH_FIX`-eligible, synthesize a bounded `fix_pack` instead of collapsing into `strong_advisory_escalation_non_local_fix`

Bounded targets:

- `stage4_interview_round.py`

Acceptance shape:

- local Flashback contradictions can synthesize bounded:
  - `patch_targets`
  - `must_fix`
  - `do_not_regress`
  - `success_condition`
- target kind remains bounded to `local_phrase` or `local_sentence`
- non-local / scene-model-class cases still fail closed

### Tranche 4. Focused Regression Closure

Goal:

- add only the regressions required to lock the three contracts above

## 4. Non-Goals

- no global Flashback taxonomy rewrite
- no weakening of Director authority
- no Stage2/3 reopen
- no canary execution in this document
- no `resolved` or `resume-ready` declaration

## 5. Acceptance Criteria

- FlashbackVerifier payload can preserve optional structured contradiction metadata without breaking existing flat consumers
- Stage4 persists flashback metadata per candidate
- Flashback strong-advisory cases that are locally repairable can synthesize bounded local fix contracts from zero
- broader or non-local flashback contradiction classes still route to REJECT
- no new `180+ LOC` production function is introduced

## 6. Verification Plan

- `pytest tests/test_flashback_verifier.py -q`
- `pytest tests/test_stage4_advisory_escalation_seam.py -k "flashback or strong_advisory" -q`
- `pytest tests/test_stage4_interview_round.py -k "flashback" -q`
- `ruff check modules/core/flashback_verifier.py modules/core/stage4_interview_round.py tests/test_flashback_verifier.py tests/test_stage4_advisory_escalation_seam.py tests/test_stage4_interview_round.py`
- `python -m py_compile modules/core/flashback_verifier.py modules/core/stage4_interview_round.py`
- `python scripts/check_utf8_hygiene.py docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-bounded-survey.md docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md docs/2026-04-01/active-temp-execution-roadmap.md docs/temp/execution-roadmap.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 7. Guardrails

- keep `Stage4` paused
- keep this lane bounded to Flashback continuity local-fix routing
- do not widen into broad Flashback policy redesign unless later runtime evidence requires it
- preserve fail-close semantics for scene-wide or structurally non-local contradictions

## 8. Temp Queue Notes

- temp status: `partial`
- cleanup condition:
  - keep the temp mirror while this remains an active child seam under the aggregate Stage4 consumer-contract wave
- roadmap dependency:
  - this lane should sit directly under `0_0-stage4-consumer-contract-normalization-remediation`
  - it should outrank the contaminated Stage4-only ep2 interpretation because the fresh full run is higher-authority evidence

## 9. 3-Pass Audit Record

Pass 1, structure and scope:

- bounded the lane to one fresh-run Stage4 blocker
- kept Stage2/3 and broad Flashback redesign out of scope

Pass 2, evidence and consistency:

- runtime watch evidence matches the fix-pack gate failure chain
- artifact and code references support that this is a real continuity contradiction path
- lineage to the aggregate Stage4 contract wave is explicit

Pass 3, execution and readability:

- tranches are code-owner aligned and bounded
- operator consequence is clear: structured flashback metadata plus local-fix synthesis
- focused static validation is closed
- runtime proof is now partially captured, but closure is still deferred because residual replay/repetition warning evidence remains

Confidence: `96%`
