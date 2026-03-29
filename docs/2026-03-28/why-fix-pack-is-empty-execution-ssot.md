# Why Fix Pack Is Empty Execution SSOT

Date: 2026-03-28
Status: execution-ready
Canonical Path: `docs/2026-03-28/why-fix-pack-is-empty-execution-ssot.md`
Temp Mirror Path: `docs/temp/why-fix-pack-is-empty-execution-ssot.md`
Commit State:
- Baseline Commit: `33acf349ce3e1559c06338ef88f7da7c8d50db0f`
- Baseline Dirty Summary: `dirty: stage4 runtime/tests, narrative BI/docs, temp queue state, canary logs, stage4 survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at SSOT creation time`
Source Survey Docs:
- `docs/2026-03-28/why-fix-pack-is-empty-full-survey-audit-order.md`
- `docs/2026-03-28/why-fix-pack-is-empty-full-survey.md`
Evidence Artifacts:
- `projects/canary_0328_golden_new2_s4/logs/runtime_audit.jsonl`
- `projects/canary_0328_golden_new2_s4/logs/session/llm_io.jsonl`
- `projects/canary_0328_stage4_ifc_bridge_check/logs/session/ui_events.jsonl`
- `projects/canary_0328_golden_new_s4/logs/runtime_audit.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe correction implied by the audited survey:

> tighten the Director prompt contract so `REJECT + fix_scope in {"inplace", "partial"}` must also emit a fully structured `fix_pack`.

This wave is prompt-boundary work, not retry-policy redesign.

## 2. Baseline Facts

- `config/prompts/director.yaml` currently makes fully structured `fix_pack` language strongest and explicit in `PASS_WITH_FIX` sections
- the same prompt also enforces `[TF-25-02]`: score `< 90` must be `REJECT`
- Stage 4 retry now correctly requires `fix_pack_contract.ready` before patch-style repair lanes
- failing canaries show:
  - `gate_basis = director_primary_reject`
  - `score = 50`
  - `fix_pack_reason = missing_fix_pack`
  - `fix_scope` eventually reaches `partial`
  - `TF-PATCH-GATE` repeatedly blocks the fake patch lane
- comparison canary shows partial fix-pack payloads can survive normalization, so the problem is not normalizer destruction

## 3. Scope

Included:

- `config/prompts/director.yaml`
- one narrow prompt regression test file
- prompt-loader based verification if needed
- canonical execution SSOT and temp mirror maintenance

Excluded:

- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_interview_round.py`
- score floor changes
- retry ceiling changes
- IFC bridge policy changes
- Director feedback-snowball remediation
- canary runner changes

## 4. Pass 1. Inventory Summary

- one prompt/runtime contract mismatch is proven
- one historical masker is already removed by TF-PATCH-GATE
- the next move does not require new Python judgment
- the most conservative fix point is the Director prompt boundary

## 5. Pass 2. Semantic Classification

- Class A: prompt contract gap
  - `REJECT + inplace/partial` can currently occur without an equally explicit `fix_pack` requirement

- Class B: bounded prompt correction
  - require the same five fix-pack fields when a REJECT still claims bounded or partial repair scope

- Class C: deferred follow-up
  - `missing_patch_targets` after prompt tightening
  - feedback snowball control
  - retry/escalation redesign

## 6. Side-Effect Map

- file writes / artifacts:
  - prompt text in `config/prompts/director.yaml`
  - one narrow prompt regression test
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - not applicable

- JSONL / log / audit sinks:
  - no sink schema changes
  - later canaries may begin recording non-empty or contract-insufficient fix-pack results instead of `missing_fix_pack`

- console / UI / operator output:
  - no direct logging change in this wave

- rollback / recovery / retry:
  - runtime retry policy is unchanged in this wave

- cache / global state:
  - not applicable

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- preserve `[TF-25-02]` exactly as-is
- preserve current `PASS_WITH_FIX` semantics
- do not teach Python to invent or backfill `fix_pack`
- do make the Director prompt explicitly say:
  - if verdict is `REJECT`
  - and `fix_scope` is `inplace` or `partial`
  - then `fix_pack` is also mandatory
  - and must include `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`
- keep `fix_scope="full"` as the one REJECT case that may legitimately omit a bounded local fix pack

This keeps decision authority on the LLM side while aligning prompt output with runtime expectations.

## 8. Execution Tranches

1. Tranche 1: prompt contract tightening
   - update both duplicated Stage 4 Director prompt blocks in `config/prompts/director.yaml`
   - make the REJECT contract explicit for `inplace` and `partial`

2. Tranche 2: bounded regression coverage
   - add one narrow prompt-content regression test
   - verify the prompt text now contains the REJECT-side fix-pack mandate without disturbing existing PASS_WITH_FIX clauses

3. Tranche 3: validation
   - prompt loader / targeted pytest
   - UTF-8 hygiene
   - ops validator after temp mirror refresh

## 9. Acceptance Criteria

- `config/prompts/director.yaml` explicitly requires structured `fix_pack` for `REJECT + fix_scope in {"inplace", "partial"}`
- both relevant duplicated prompt sections are updated
- `[TF-25-02]` remains unchanged
- no Stage 4 Python runtime behavior changes are bundled into this wave
- one regression test locks the new prompt requirement

## 10. Verification Plan

- targeted pytest for the new prompt regression test
- targeted prompt loader check if touched by the test
- `python scripts/check_utf8_hygiene.py` on touched docs/tests/config
- `python scripts/ops_validator.py --strict` after temp mirror refresh

Fresh canary validation is deferred to the next turn after implementation.

## 11. Guardrails

- do not lower the 90-point floor
- do not change retry ceilings
- do not relax Python fix-pack readiness rules in this wave
- do not bundle feedback-snowball mitigation into this wave
- do not redesign escalation thresholds
- do not change canary tooling in this wave

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - remove `docs/temp/why-fix-pack-is-empty-execution-ssot.md` after realization and closure
- roadmap dependency:
  - current temp roadmap remains `docs/temp/execution-roadmap.md`

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run this document's 3-pass audit against the current workspace state before patching code from it

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- execution doc type matches the next move after the audited survey
- included and excluded surfaces are explicit
- scope is bounded to prompt-side contract tightening
- PASS

### Pass 2. Evidence and Consistency

- commit state and dirty summary were captured from the live workspace
- source survey and evidence artifacts were rechecked
- the document stays aligned with the survey's causality finding: exposure, not bug creation
- PASS

### Pass 3. Execution and Readability

- tranches are concrete
- acceptance criteria are narrow
- guardrails block scope creep into retry and escalation redesign
- PASS

Estimated confidence: `96%`

