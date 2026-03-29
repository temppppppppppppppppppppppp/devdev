# Stage4 Decision Contract Matrix Execution SSOT

Date: 2026-03-28
Status: execution-ready
Canonical Path: `docs/2026-03-28/stage4-decision-contract-matrix-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-decision-contract-matrix-execution-ssot.md`
Commit State:
- Baseline Commit: `33acf349ce3e1559c06338ef88f7da7c8d50db0f`
- Baseline Dirty Summary: `dirty: stage4 code/tests, narrative docs/json, temp queue state, canary logs, stage4 survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at SSOT creation time`
Source Survey Docs:
- `docs/2026-03-28/stage4-decision-contract-matrix-full-survey.md`
- `docs/2026-03-28/why-fix-pack-is-empty-full-survey.md`
- `docs/2026-03-28/why-fix-pack-is-empty-execution-ssot.md`
Evidence Artifacts:
- `projects/canary_0328_fixpack_contract_check_v2/logs/session/decisions.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/episode_production.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/session/ui_events.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/session/llm_io.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe next correction after the already-landed controls:

- fake patch lane fail-closed
- narrow IFC bridge
- REJECT-side fix-pack prompt tightening

The next highest-risk remaining defect is:

> authoritative Director decisions can still emit blank `fix_scope`, while downstream retry/pathology layers later show derived `partial` scope.

This wave is about contract ownership and evidence clarity, not broad escalation redesign.

## 2. Baseline Facts

- latest authoritative canary decisions show:
  - `verdict = REJECT`
  - `score = 50`
  - `fix_scope = ""`
  - `repair_scope = "none"`
  - `fix_pack = {}`
- later pathology rows in the same run show:
  - `fix_scope = "partial"`
  - `fix_pack_reason = "missing_fix_pack"`
  - patch-style repair intent appearing in retry metadata
- therefore the current family is not explained by `fix_pack` alone
- it is explained by incomplete authoritative decision output plus downstream scope drift
- `TF-PATCH-GATE` remains correct and should stay unchanged in this wave
- provider contamination exists, but blank authoritative `fix_scope` is still visible in clean decision sinks and is therefore not reducible to the provider issue

## 3. Scope

Included:

- `config/prompts/director.yaml`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_interview_round.py`
- targeted Stage4 prompt/runtime tests
- canonical execution SSOT and temp mirror maintenance

Excluded:

- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- round ceiling changes
- feedback windowing rollout
- fallback provider redesign
- canary runner changes
- broad lane transition table refactor

## 4. Pass 1. Inventory Summary

- one authoritative contract row is still under-specified:
  - `REJECT x fix_scope`
- one evidence seam is misleading:
  - authoritative `fix_scope` vs derived retry/pathology `fix_scope`
- one downstream symptom is already well understood:
  - `missing_fix_pack`

Main hotspot lane:

- Director output normalization and the first Stage4 gate semantics layer

## 5. Pass 2. Semantic Classification

- Class A: already-correct behavior
  - patch lanes require ready fix-pack
  - narrow IFC bridge stays bounded
  - REJECT-side fix-pack prompt language already exists

- Class B: next bounded correction
  - blank authoritative `fix_scope` must become an explicit contract violation
  - authoritative scope and derived retry scope must stop sharing the same operator meaning

- Class C: deferred follow-up
  - feedback snowball mitigation
  - fallback observability repair
  - escalation redesign

## 6. Side-Effect Map

- file writes / artifacts:
  - `config/prompts/director.yaml`
  - `modules/domain/agents/director_ensemble.py`
  - `modules/core/stage4_interview_round.py`
  - targeted tests
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - no DB schema change intended

- JSONL / log / audit sinks:
  - decision/pathology payloads may gain a sharper separation between authoritative scope and derived retry scope
  - sink additions must remain backward-compatible

- console / UI / operator output:
  - may gain a narrow contract-violation notice for blank/invalid authoritative `fix_scope`

- rollback / recovery / retry:
  - lane behavior should remain materially unchanged in this wave
  - this wave is for contract surfacing, not retry-policy redesign

- cache / global state:
  - not applicable

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### 7.1 Prompt Boundary

Strengthen the Director contract so that:

- `REJECT` must emit one of `inplace`, `partial`, or `full`
- `PASS_WITH_FIX` must emit `inplace`
- blank scope is forbidden
- invalid scope strings are forbidden

This is not a new judgment rule. It is a contract completeness rule.

### 7.2 Normalization Boundary

Immediately after Director output normalization:

- validate `fix_scope` against the allowed enum
- if `REJECT` or `PASS_WITH_FIX` arrives with blank/invalid `fix_scope`, surface an explicit contract-violation state
- do not silently pretend that the authoritative Director emitted `partial` later

### 7.3 Evidence Boundary

Operator evidence must distinguish:

- authoritative Director scope
- derived retry or repair scope

Minimal acceptable outcome:

- sinks no longer make a later derived `partial` look indistinguishable from a Director-authored `partial`

This can be done by:

- preserving the authoritative field as-is
- using a separate derived field name in retry/pathology evidence

## 8. Execution Tranches

1. Tranche 1: prompt hardening
   - strengthen `director.yaml` so blank `fix_scope` is explicitly invalid for REJECT and PASS_WITH_FIX

2. Tranche 2: authoritative scope validation
   - add a narrow contract check in Director output normalization / first Stage4 gate semantics
   - emit explicit contract-violation metadata for blank/invalid scope
   - do not invent a fake authoritative value

3. Tranche 3: sink separation
   - distinguish authoritative scope from derived retry scope in decision/pathology evidence
   - keep compatibility with current operator logs where possible

4. Tranche 4: regression coverage
   - blank `fix_scope` on REJECT becomes a visible violation
   - blank `fix_scope` on PASS_WITH_FIX becomes a visible violation
   - downstream derived scope can no longer be confused with authoritative scope

## 9. Acceptance Criteria

- REJECT cannot remain silently blank-scope at the authoritative decision layer
- PASS_WITH_FIX cannot remain silently blank-scope at the authoritative decision layer
- operator evidence can distinguish:
  - Director-authored scope
  - derived retry scope
- `TF-PATCH-GATE` behavior remains unchanged in this wave
- no round ceiling or escalation policy changes are bundled into this wave

## 10. Verification Plan

- targeted pytest for:
  - prompt contract coverage
  - Director output normalization / gate semantics coverage
  - decision/pathology evidence separation
- `python scripts/check_utf8_hygiene.py` on touched config/code/tests/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Fresh canary validation should happen only after this wave lands.

## 11. Guardrails

- do not teach Python to decide whether a manuscript is good
- do not auto-upgrade blank REJECT scope to `full` unless the wave explicitly chooses that as a documented contract policy
- do not redesign retry routing in this wave
- do not bundle fallback observability work unless a touched sink needs a minimal compatibility fix
- do not change the 10-round ceiling

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - remove `docs/temp/stage4-decision-contract-matrix-execution-ssot.md` after realization and closure
- roadmap dependency:
  - current temp roadmap remains `docs/temp/execution-roadmap.md`

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- queue sync command: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least 95% confidence against the current workspace state before patching from it

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- the execution slice is narrower than the full survey
- already-landed fixes are treated as baseline, not re-opened work
- PASS

### Pass 2. Evidence and Consistency

- latest canary evidence was re-checked against decision, pathology, UI, and LLM I/O sinks
- the execution target matches the strongest newly confirmed seam: blank authoritative scope plus downstream drift
- PASS

### Pass 3. Actionability and Overclaim Control

- the wave does not overreach into escalation redesign
- the document preserves LLM decision authority and uses Python only for contract enforcement and evidence clarity
- PASS

Estimated confidence: `96%`

