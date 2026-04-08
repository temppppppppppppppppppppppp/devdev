# 000 Fresh Run Stage4 Ep1 Post-Run Merge Audit

Date: 2026-04-08
Status: audit_complete_historical (fresh `000_ㅇㅇㅇ` run reached Stage4 `ep1` persistence success; this pre-rerun audit correctly held closure pending, and the rerun question is now superseded by `docs/2026-04-08/0_0-stage4-ep1-sinkproof-r1-runtime-closure-audit.md`)
Canonical Path: `docs/2026-04-08/000-fresh-run-stage4-ep1-post-run-merge-audit.md`
Superseded By:
- `docs/2026-04-08/0_0-stage4-ep1-sinkproof-r1-runtime-closure-audit.md`
Related Queue Lanes:
- `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
Commit State:
- HEAD Commit: `eac3386c`
- Live Dirty Summary: `existing Stage0/Stage3/Stage4 tranche files plus the bounded Stage4 pass-side sink-alignment follow-up are present in the live workspace; this audit does not treat the dirty state itself as failure evidence`
Evidence Artifacts:
- `projects/000_ㅇㅇㅇ/logs/runtime_audit_summary.json`
- `projects/000_ㅇㅇㅇ/logs/episode_production.jsonl`
- `projects/000_ㅇㅇㅇ/logs/session/decisions.jsonl`
- `projects/000_ㅇㅇㅇ/drafts/ep_0001.txt`
- `projects/000_ㅇㅇㅇ/logs/artifacts/stage4/ep_0001/attempt_01/patched_after_fix__A_InPlace.txt`
- `projects/000_ㅇㅇㅇ/project_data.db`
Side-Effect Coverage: covered (`drafts/`, Stage4 artifact sink, DB `stage_attempts`, DB `manuscripts`, JSONL decision sink, JSONL episode-production sink, runtime proof digest)

## 1. Scope

Audit the completed fresh `000_ㅇㅇㅇ` run through Stage4 `ep1`, decide whether the evidence is good enough for closure, and record any bounded follow-up needed before queue or closure bookkeeping changes.

Excluded:

- broad Stage4 redesign
- new queue topic creation
- canary/live closure claim without fresh post-patch proof

## 2. Artifact Truth

- Stage2 is complete for this project: `stage_attempts` contains three Stage2 `PASS` rows.
- Stage3 is complete through `ep3`: `stage_attempts` contains three Stage3 `PASS` rows with scores `90`, `92`, and `95`.
- Stage4 `ep1` persisted successfully:
  - `stage_attempts` contains one Stage4 final row with `verdict=PASS`, `score=90`, `fix_scope=inplace`
  - the final Stage4 artifact path is `logs/artifacts/stage4/ep_0001/attempt_01/patched_after_fix__A_InPlace.txt`
  - the reader-facing local sink is `drafts/ep_0001.txt`
  - DB `manuscripts` contains the `ep1` row, and its content matches the normalized draft text
- therefore this run is not a manuscript-loss or DB-write failure

## 3. Proof Digest Result

`projects/000_ㅇㅇㅇ/logs/runtime_audit_summary.json` reports:

- `proof_digest.available = true`
- `proof_digest.status = warn`
- `proof_digest.stages.stage3.status = ok`
- `proof_digest.stages.stage4.status = warn`

Stage4 warning counts:

- `director_verdict_mismatches = 1`
- `gate_basis_mismatches = 1`
- `gate_repair_metadata_missing = 4`
- `selection_reason_mismatches = 1`
- `verdict_reason_mismatches = 1`

This means the completed run did reach persistence, but the completed evidence still fails the merged sink-alignment check needed for closure.

## 4. Sink Join Findings

Authoritative final row:

- `stage_attempts` already carries the correct final outcome:
  - `verdict = PASS`
  - `selection_reason` and `verdict_reason` both point at the post-patch rationale
  - `artifact_path = logs/artifacts/stage4/ep_0001/attempt_01/patched_after_fix__A_InPlace.txt`
  - `advisory_flags.gate_semantics.gate_basis = patch_reaudit_pass`
  - `advisory_flags.fix_pack.patch_target_records[]` and `repair_trace[]` are persisted

Intentional pre-final companion:

- `director_selections` still points at `selected_before_fix__A.txt` with `verdict = PASS_WITH_FIX`
- that is acceptable in this lane because the final-authority contract already treats `director_selections` as the pre-final selection companion rather than the final attempt truth

Drifting PASS-side sinks:

- `episode_production.jsonl` line 1 still records the attempt as:
  - `verdict = PASS_WITH_FIX`
  - `director_verdict = PASS_WITH_FIX`
  - `gate_basis = director_primary_pass_with_fix`
  - `selection_reason` and `verdict_reason` from the pre-fix selection step
- `logs/session/decisions.jsonl` already carries the final `PASS` / `patch_reaudit_pass` rationale, but its `meta.fix_pack` is `{}` instead of the full bounded repair payload

Result:

- the Stage4 proof digest is warning because the run's PASS-side JSONL/session sinks do not agree on the final patched truth
- this is a completed-run telemetry/finalization drift, not a failed manuscript production run

## 5. Bounded Follow-Up Landed

A bounded pass-side sink-alignment patch has now landed in `modules/core/stage4_interview_round.py`.

What changed:

- the pass logging payload now merges `director_result` with non-empty `trace_director_result` fields instead of letting a partial trace erase the original `fix_pack`
- the final pass log writer now forwards explicit final:
  - `selection_reason`
  - `verdict_reason`
  - `gate_semantics`
  - `fix_pack`
  - `runtime_advisory`
  - `retry_directives`
- the pass-side session decision writer now uses the same final `fix_pack` instead of rebuilding from a sometimes-partial trace payload

Touched files:

- `modules/core/stage4_interview_round.py`
- `tests/test_stage4_interview_round.py`

Focused regression coverage for the landed follow-up:

- pass result logging payload preserves `fix_pack` when trace payload is partial
- `episode_production` write path prefers explicit final sink metadata over stale selection metadata
- session decision logging uses the final `fix_pack`

## 6. Closure Decision

Closure is not justified yet.

Reasons:

1. the completed fresh run still ends with `proof_digest.status = warn`
2. the bounded sink-alignment patch landed after this run's JSONL/session sinks were emitted
3. execution-closure governance requires verification evidence, not only a plausible fix

Therefore:

- queue order stays unchanged
- the governing Stage4 lane remains `partially_realized`
- the next trustworthy closure attempt is a fresh rerun or bounded proof pass that exercises the patched Stage4 pass-side sink writers

## 7. Recommended Next Step

Run one bounded post-patch proof pass against `000_ㅇㅇㅇ` Stage4 `ep1` or an equivalent fresh Stage4 proof harness.

Pass condition:

- Stage4 still persists `PASS`
- `runtime_audit_summary.json` no longer reports the current Stage4 sink-alignment mismatches

Fail condition:

- the rerun still emits `episode_production` pre-fix authority or empty `fix_pack` in the session sink, in which case the next lane stays inside the same Stage4 pass-side finalization seam rather than opening a new queue topic

## 8. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this document as a post-run merge audit, not a closure note or a new execution SSOT
- separated artifact truth, proof-digest findings, sink-join diagnosis, and closure decision

Pass 2, evidence and consistency:

- every conclusion is tied to completed fresh-run evidence from DB, JSONL, runtime summary, and saved draft/artifact sinks
- did not treat `director_selections` pre-final state as failure because the current final-authority contract already classifies it as a selection companion
- bounded the live defect to PASS-side sink alignment instead of overstating it as manuscript or Stage4 generation failure

Pass 3, execution and readability:

- the next action is explicit: rerun proof on the landed bounded patch
- queue reorder and closure claims are intentionally withheld until rerun evidence exists

Confidence: `97%`
