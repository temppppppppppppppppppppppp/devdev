# 0_0 Stage4 Post-Select Continuity Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: closed (fresh run runtime proof captured 2026-04-04; temp mirror cleanup eligible)
Canonical Path: `docs/2026-04-02/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-post-implementation-audit.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-evidence.json`
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-evidence.json`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-post-implementation-evidence.json`
Parent Lane:
- `0_0-stage2-stage3-stage4-readiness-remediation`

## 1. Answer First

The next bounded Stage4 lane should normalize one remaining final-round contract seam:

- post-select downgrade currently preserves too little contradiction subtype precision
- bounded `proper_noun/timeline` continuity cases are serialized too similarly to broader rewrite-class history collapse

This lane is not a canary wave and not a Stage2/3 reopening. It is a narrow Stage4 contract-normalization patch.

## 2. Scope

Included:

- `modules/core/stage4_interview_round.py`
- focused Stage4 tests
- roadmap/temp queue refresh

Excluded:

- Stage2/3 hierarchy changes
- fresh canary
- broad Stage4 redesign
- Director prompt redesign
- DB schema changes
- `Stage4 resume-ready` declaration

## 3. Execution Tranches

### Tranche 1. Enrich Post-Select Conflict Contract

Goal:

- when provisional `PASS/PASS_WITH_FIX` is downgraded by post-select checks, preserve contradiction subtype/fixability metadata instead of flattening everything into coarse continuity/history-only structure

Bounded target:

- `stage4_interview_round.py`

Acceptance shape:

- `conflict_contract` keeps structured `conflicts`
- it also preserves contradiction subtype metadata when the Director already surfaced it
- it preserves whether the originating fix hint was locally actionable

### Tranche 2. Propagate Typed Contradiction Metadata Across The Post-Select Downgrade

Goal:

- ensure `previous_attempt` and downstream retry lineage keep the relevant typed contradiction context for later policy and operator interpretation

Bounded target:

- `stage4_interview_round.py`

Acceptance shape:

- post-select downgrade path keeps contradiction subtype/detail context on the retry snapshot lineage
- existing coarse `continuity/history` categories remain, but no longer erase the finer contradiction view

### Tranche 3. Focused Regression Closure

Goal:

- add focused regressions for subtype-preserving post-select downgrade behavior

## 4. Non-Goals

- no canary in this turn
- no queue closure claims
- no Stage4 unpause
- no broad rewrite of continuity/history checkers
- no attempt to solve every remaining Stage4 seam in one lane

## 5. Verification Plan

- `pytest tests/test_stage4_interview_round.py -k "post_select_conflict" -q`
- `pytest tests/test_stage4_advisory_escalation_seam.py -k "post_select_conflict" -q`
- `ruff check modules/core/stage4_interview_round.py tests/test_stage4_interview_round.py tests/test_stage4_advisory_escalation_seam.py`
- `python -m py_compile modules/core/stage4_interview_round.py`
- `python scripts/check_utf8_hygiene.py docs/2026-04-02/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md docs/temp/0_0-stage4-post-select-continuity-contract-normalization-remediation-execution-ssot.md`

## 6. Guardrails

- keep `Stage4` paused
- do not widen this into another broad Stage4 wave
- do not reopen Stage2/3
- preserve Director final authority and existing fail-closed semantics
- preserve `full` rewrite routing for true post-select collapse; this lane is about metadata/contract precision, not patch-lane promotion

## 7. 3-Pass Audit Record

### Pass 1. Structure and Scope

- kept this as a bounded execution SSOT
- limited the lane to one final-round Stage4 contract family

### Pass 2. Evidence and Consistency

- lineage follows the new bounded survey and the last runtime closure audit
- scope matches the residual seam identified after fix-pack preservation landed

### Pass 3. Execution and Readability

- tranches are narrow and code-owner aligned
- runtime proof is explicitly deferred
- non-goals prevent Stage2/3 reopen or broad Stage4 inflation

Confidence: `96%`

## 8. Realization Update (2026-04-02)

Landed:

- `stage4_interview_round.py`
  - `post_select_conflict` contract now preserves contradiction subtype/detail context when the Director had already surfaced it
  - bounded local-fixability (`target_kind`, local-fix hint) now survives into the conflict contract instead of being erased by the final-round downgrade
  - post-select downgrade lineage now keeps contradiction subtype/detail context on `previous_attempt`
- focused regression added in:
  - `tests/test_stage4_interview_round.py`

Static validation closed:

- `python -m py_compile modules/core/stage4_interview_round.py`
- `ruff check modules/core/stage4_interview_round.py tests/test_stage4_interview_round.py tests/test_stage4_advisory_escalation_seam.py`
- `pytest tests/test_stage4_interview_round.py -k "post_select_conflict" -q`
- `pytest tests/test_stage4_advisory_escalation_seam.py -k "post_select_conflict" -q`

Complexity note:

- touched hotspot: `Stage4InterviewRound._run_post_select_checks()` remains a sink-boundary shell for final-round downgrade handling
- no new `180+ LOC` production hotspot introduced by this tranche

## 9. Closure Update (2026-04-04)

Runtime proof captured:

- `projects/__000403/logs/session/decisions.jsonl` recorded `s4:ep2:arc1:a4:20260403_224348` with `gate_basis=post_select_conflict`, `repair_scope=full`, `fix_pack.target_kind=local_sentence`, `repair_contract.subtype=아이템`, and widened `scope_authority`
- `projects/__000403/logs/episode_production.jsonl` recorded the same attempt as `STAGE4_RETRY_PATHOLOGY` with `post_select_conflict|contradiction:아이템|fix_pack_ready`
- the same fresh run later reached `s4:ep2:arc1:a9:20260403_224348` with final `PASS`

Sink/readback verification:

- local `FailureAnalyzer.sink_alignment_summary(stage=4, lookback=50, include_session_decisions=True)` shows `repair_contract_subtype_mismatches=[]`
- the same readback shows `repair_contract_provenance_mismatches=[]`, `gate_repair_metadata_missing=[]`, and `selection_companion_missing_rows=[]`
- remaining alignment warnings are limited to `director_selections` companion rows preserving pre-final semantics rather than loss in the authoritative Stage4 sinks

Residual risk:

- `projects/__000403/logs/runtime_audit_summary.json` still reports Stage4 `status=warn`, but the surviving counts are `gate_basis/fix_scope/repair_scope` companion-row mismatches and do not reopen this lane
- parent follow-up remains under `0_0-stage4-consumer-contract-normalization-remediation`, with the next held seam still `numeric asset authority / carryover owner-boundary`
