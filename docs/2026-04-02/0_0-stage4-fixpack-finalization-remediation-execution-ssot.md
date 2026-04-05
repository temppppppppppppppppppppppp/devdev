# 0_0 Stage4 FixPack Finalization Remediation Execution SSOT

Date: 2026-04-02
Status: closed (fresh run runtime proof captured 2026-04-04; temp mirror cleanup eligible)
Canonical Path: `docs/2026-04-02/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-post-implementation-audit.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-evidence.json`
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-evidence.json`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-post-implementation-evidence.json`
Parent Lane:
- `0_0-stage2-stage3-stage4-readiness-remediation`

## 1. Answer First

The next bounded Stage4 lane should fix one class of contract failure:

- runtime-created repair obligations that lack actionable local `fix_pack` targets
- final-round post-select downgrades that discard structured fix hints and later degrade into `missing_fix_pack`

This is not a Stage2/3 wave and not a broad Stage4 redesign.

## 2. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- focused Stage4 tests
- roadmap/temp queue refresh

Excluded:

- Director prompt redesign as the primary fix
- Stage2/3 context hierarchy changes
- Stage4 resume
- fresh canary in this turn
- DB schema changes

## 3. Execution Tranches

### Tranche 1. Runtime Fix-Pack Backfill For Strong Advisory Escalation

Goal:

- when runtime escalates Director `PASS` into a repair-bearing verdict, synthesize or backfill the missing local fix contract from already-available runtime evidence

Bounded target:

- `stage4_interview_round.py`

Acceptance shape:

- `strong_advisory_escalation_non_local_fix` should no longer fire merely because `patch_targets` were omitted on an otherwise local-fixable advisory result
- the backfill must stay bounded to local target kinds and must not permit `scene_model`

### Tranche 2. Selective Fix-Pack Preservation For Post-Select Conflict

Goal:

- stop losing structured fix hints when a provisional pass is downgraded by post-select continuity/history conflict

Bounded target:

- `stage4_reject_runtime.py`

Acceptance shape:

- full rewrite semantics remain available for broad continuity collapse
- but bounded proper-noun/timeline fix hints are not flattened into unconditional `missing_fix_pack`

### Tranche 3. Focused Regression Closure

Goal:

- add regression tests for the two branches above and keep the lane bounded

## 4. Non-Goals

- no Stage2/3 reopen
- no broad TruthGate or Director constitutional rewrite
- no canary execution in this document
- no `Stage4 resume-ready` declaration

## 5. Verification Plan

- `pytest tests/test_stage4_interview_round.py -k "fix_pack or post_select_conflict or strong_advisory" -q`
- `pytest tests/test_stage4_advisory_escalation_seam.py -q`
- `ruff check modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py tests/test_stage4_interview_round.py tests/test_stage4_advisory_escalation_seam.py`
- `python -m py_compile modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py`
- `python scripts/check_utf8_hygiene.py docs/2026-04-02/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md docs/temp/0_0-stage4-fixpack-finalization-remediation-execution-ssot.md`

## 6. Guardrails

- keep `Stage4` paused
- do not widen this into another broad Stage4 lane
- do not touch Stage2/3 hierarchy code
- preserve Director final authority
- preserve existing fail-closed behavior for truly non-local repairs

## 7. 3-Pass Audit Record

### Pass 1. Structure and Scope

- bounded to one Stage4 finalization family
- excluded canary and resume decisions

### Pass 2. Evidence and Consistency

- ep3 branch tied to runtime escalation evidence
- ep4 branch tied to reject snapshot/persistence evidence
- lineage consistent with the just-closed runtime closure audit

### Pass 3. Execution and Readability

- tranches are narrow and code-owner aligned
- next runtime proof is explicitly deferred
- non-goals prevent this from inflating into a broad redesign

Confidence: `96%`

## 8. Realization Update (2026-04-02)

Landed:

- `stage4_interview_round.py`
  - strong-advisory local-fix backfill now synthesizes bounded `patch_targets`/`must_fix` when runtime escalation is the first point a local repair contract becomes necessary
  - backfill remains limited to local target kinds and does not permit `scene_model`
- `stage4_reject_runtime.py`
  - bounded post-select fix hints can now survive into reject guidance and retry snapshotting when the fix pack is locally actionable
  - `full` rewrite routing remains authoritative; preservation is for continuity-guided traceability and downstream repair linkage, not patch-lane promotion
- focused regressions added in:
  - `tests/test_stage4_advisory_escalation_seam.py`
  - `tests/test_stage4_interview_round.py`

Static validation closed:

- `python -m py_compile modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py`
- `ruff check modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py tests/test_stage4_advisory_escalation_seam.py tests/test_stage4_interview_round.py`
- `pytest tests/test_stage4_advisory_escalation_seam.py -q`
- `pytest tests/test_stage4_interview_round.py -k "post_select_conflict or strong_advisory" -q`

Complexity note:

- touched hotspot: `Stage4InterviewRound._normalize_director_gate_semantics()` remains a bounded shell; new semantic logic was extracted into `_backfill_strong_advisory_fix_pack()`
- touched sink boundary: `Stage4RejectRuntime._build_reject_guidance_payload()` and `_build_reject_retry_snapshot()`
- no new `180+ LOC` production hotspot introduced by this tranche

## 9. Closure Update (2026-04-04)

Runtime proof captured:

- `projects/__000403/logs/session/decisions.jsonl` recorded `s4:ep2:arc1:a8:20260403_224348` with `gate_basis=patch_reaudit_fail`, `repair_scope=partial`, `fix_pack.target_kind=local_sentence`, `fix_pack.subtype=facing`, and `repair_contract.provenance=runtime_synthesized`
- `projects/__000403/logs/episode_production.jsonl` recorded the same attempt as `STAGE4_RETRY_PATHOLOGY` with `quality_issue|fix_pack_ready`
- the same fresh run later reached `s4:ep2:arc1:a9:20260403_224348` with final `PASS`

Sink/readback verification:

- local `FailureAnalyzer.sink_alignment_summary(stage=4, lookback=50, include_session_decisions=True)` shows `repair_contract_subtype_mismatches=[]`
- the same readback shows `repair_contract_provenance_mismatches=[]`, `gate_repair_metadata_missing=[]`, and `selection_companion_missing_rows=[]`
- authoritative Stage4 sinks preserve the runtime-synthesized local fix contract; the remaining warn surface is limited to `director_selections` companion rows

Residual risk:

- `projects/__000403/logs/runtime_audit_summary.json` still reports Stage4 `status=warn`, but the surviving mismatch counts reflect companion review history rather than lost fix-pack/finalization payloads in the authoritative sinks
- parent follow-up remains under `0_0-stage4-consumer-contract-normalization-remediation`, with the next held seam still `numeric asset authority / carryover owner-boundary`
