# OPUS Remaining High/ROI Screening 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: 121 entries`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `same working session; no new governing-doc reset required`
Source Governing Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Source OPUS Survey Docs:
- `docs/2026-03-18/OPUS/geuldobi-stage23-deepdive-hidden-areas-survey.md`
- `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md`
- `docs/2026-03-18/OPUS/react 도입/react-adoption-deepdive-full-survey.md`
- `docs/2026-03-18/OPUS/react 도입/react-migration-execution-roadmap.md`
Evidence Basis:
- live code spot-checks on `base_agent.py`, `blueprint_ensemble.py`, `three_phase_blueprint_generator.py`, `unified_blueprint_validator.py`, `response_schemas.py`
- current 2026-03-19 remediation status docs
- no active temp execution mirrors under `docs/temp/` (`README.md` only)
Scope:
- bounded screening of OPUS-derived remaining high or high-ROI candidates
- decide whether another bounded remediation pass is warranted before React migration
- non-goal: full re-audit of all OPUS claims

---

## Pass 1. Structure and Decision Frame

This document is not a new execution SSOT.

It answers one bounded question:

- after the completed 2026-03-19 remediation stream, are there still any OPUS-derived items that are both live and high-ROI enough to do before React?

The screening frame is:

1. ignore items already fixed or policy-locked in current status docs
2. ignore project-specific artifact truth that remains outside code-patching authority
3. separate narrow live defects from large migration programs
4. prefer candidates that are:
   - still live in code
   - narrow in scope
   - low-to-moderate blast radius
   - likely to improve runtime trust or operator confidence quickly

Decision classes used here:

- `DO NOW`: narrow remaining item with clear ROI
- `DO LATER`: real issue, but not the next best remediation move
- `SEPARATE PROGRAM`: not a bounded defect-remediation item
- `SEPARATE SURVEY`: needs fresh project/live survey rather than immediate patching

---

## Pass 2. Remaining Candidate Screening

### 1. `blueprint_ensemble.last_error_type` shared-state race

Source claim:
- `docs/2026-03-18/OPUS/geuldobi-stage23-deepdive-hidden-areas-survey.md`

Live code basis:
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`

Live shape:
- `BlueprintEnsemble` still resets `self.last_error_type` once before 3-strategy fan-out.
- each strategy still shares the same ensemble/base-agent instance.
- `ThreePhaseBlueprintGenerator.generate()` still reads `self.ensemble.last_error_type` to decide `schema_incompatible` fast-fail.

Current classification:
- `DONE`

Result:
- fixed in `docs/2026-03-19/blueprint-ensemble-last-error-type-race-3pass-audit.md`
- worker error types are now aggregated
- caller fast-fail now prefers aggregated `schema_incompatible` evidence over stale single-field state

Screened priority:
- `Priority 1`

---

### 2. ambiguous `429` classification in `BaseAgent`

Source claim:
- `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md`

Live code basis:
- `modules/domain/agents/base_agent.py`

Live shape:
- code still classifies:
  - `rate limit`
  - `quota exhausted`
  - ambiguous `429`
- ambiguous `429` still falls into the rate-limit backoff path

Current classification:
- `DONE`

Result:
- fixed in `docs/2026-03-19/base-agent-ambiguous-429-classification-3pass-audit.md`
- bare ambiguous `429` now prefers immediate fallback instead of same-model backoff
- explicit rate-limit wording still keeps the backoff lane

Screened priority:
- `Priority 2`

---

### 3. API-key exhaustion with weak explicit operator signal

Source claim:
- `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md`

Live code basis:
- `modules/domain/agents/base_agent.py`

Live shape:
- `_try_rotate_key()` still returns `None` when all keys are exhausted or rotation cannot continue
- the operator signal remains weaker than ideal

Current classification:
- `DONE`

Result:
- fixed in `docs/2026-03-19/base-agent-key-exhaustion-operator-signal-3pass-audit.md`
- key-rotation exhaustion states are now surfaced explicitly at the operator layer
- fallback behavior itself was preserved

Screened priority:
- `Priority 4`

---

### 4. `PASS_WITH_WARNING` verdict enum drift

Live code basis:
- `modules/core/response_schemas.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/db_manager.py`

Current classification:
- `DONE`

Result:
- fixed in `docs/2026-03-19/pass-with-warning-verdict-enum-drift-3pass-audit.md`
- schema enums now admit `PASS_WITH_WARNING`
- Stage 3/DB/schema contract is aligned

Screened priority:
- `Priority 4.5`

---

### 5. Preflight hollow previous-arc input gap

Live code basis:
- `modules/core/stage2_preflight.py`
- `modules/domain/agents/preflight_checker.py`

Current classification:
- `DONE`

Result:
- fixed in `docs/2026-03-19/preflight-hollow-prev-arcs-input-gap-3pass-audit.md`
- hollow previous Arcs are skipped before `PreflightChecker.analyze()`
- skip facts now emit audit/log signal and `_input_hygiene` metadata

Screened priority:
- `Priority 5`

---

### 6. QualityDashboard persistence failure remains warning-only

Live code basis:
- `modules/core/quality_dashboard.py`
- `modules/api/bridge_server.py`

Current classification:
- `DONE`

Result:
- fixed in `docs/2026-03-19/quality-dashboard-persistence-operator-signal-3pass-audit.md`
- metric sink write failure now emits soft-failure operator signal
- dashboard runtime-health path can now surface `quality_dashboard.save_record`

Screened priority:
- `Priority 5.5`

---

### 7. dead-NPC CRITICAL remains advisory-only in blueprint prevalidation

Source claim:
- `docs/2026-03-18/OPUS/geuldobi-stage23-deepdive-hidden-areas-survey.md`

Live code basis:
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/validation/blocking_validator.py`

Live shape:
- blueprint-side dead-NPC finding is still wrapped as advisory input to Director
- manuscript-side blocking validator still has a real hard block for dead-NPC resurrection

Current classification:
- `DO LATER`

Why it is real:
- principle-level seriousness is high under AGENTS rule 4

Why it is not the next best bounded pass:
- this is not a simple bugfix
- it touches policy boundary between Python blocking and Director sovereignty
- manuscript-level hard block already exists, which lowers immediate ROI

Screened priority:
- `Priority 5`

---

### 8. Stage 3 emergency fallback returns `PASS_WITH_WARNING`

Source claim:
- `docs/2026-03-18/OPUS/geuldobi-stage23-deepdive-hidden-areas-survey.md`

Live code basis:
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`

Live shape:
- after all retries fail, a previous best Blueprint can still return as `PASS_WITH_WARNING`
- `quality_gate_failed` and `quality_risk` are attached

Current classification:
- `DO LATER`

Why it is not first:
- still partly a policy problem rather than a pure bug
- any change here must be coordinated with Stage 3/4 risk-routing semantics
- higher blast radius than `last_error_type` or `429` classification

Bounded follow-up completed:
- `docs/2026-03-19/stage3-pass-with-warning-dashboard-observability-3pass-audit.md`
- dashboard ingestion now preserves `PASS_WITH_WARNING`
- `quality_gate_failed` and `quality_risk` now survive in dashboard warning payloads
- semantic fallback policy itself remains intentionally unchanged

Screened priority:
- `Priority 6`

---

### 9. `anyOf` response-schema design

Source claim:
- `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md`

Live code basis:
- `modules/core/response_schemas.py`

Live shape:
- compatibility-oriented `anyOf` schema design still exists in multiple Blueprint fields

Current classification:
- `DO LATER`

Why it is not next:
- this is cross-cutting schema design work
- it is wider than a narrow remediation item
- downstream compatibility and provider behavior must be re-audited together

Screened priority:
- `Priority 7`

---

### 10. React migration

Source docs:
- `docs/2026-03-18/OPUS/react 도입/react-adoption-deepdive-full-survey.md`
- `docs/2026-03-18/OPUS/react 도입/react-migration-execution-roadmap.md`

Live interpretation:
- React is not the next bugfix in the current remediation stream
- it is a large migration program with documented estimate around `160-220h`

Current classification:
- `SEPARATE PROGRAM`

Why:
- much broader scope
- different success criteria
- not comparable to a final narrow high-ROI defect pass

---

## Pass 3. Recommended Next Move

### Main conclusion

Do not jump to React merely because the current remediation stream is nearing closure.

There are still a few OPUS-derived candidates worth a final bounded high-ROI pass, but the set is now small.

### Recommended order

1. `Priority 1`: fresh focused audit of `blueprint_ensemble.last_error_type` shared-state race
   - status: completed in `docs/2026-03-19/blueprint-ensemble-last-error-type-race-3pass-audit.md`
2. `Priority 2`: fresh focused audit and likely fix for ambiguous `429` handling in `BaseAgent`
   - status: completed in `docs/2026-03-19/base-agent-ambiguous-429-classification-3pass-audit.md`
3. `Priority 4`: explicit operator signal for API-key exhaustion
   - status: completed in `docs/2026-03-19/base-agent-key-exhaustion-operator-signal-3pass-audit.md`
4. `Priority 4.5`: schema alignment for `PASS_WITH_WARNING`
   - status: completed in `docs/2026-03-19/pass-with-warning-verdict-enum-drift-3pass-audit.md`
5. `Priority 5`: Stage 2 preflight hollow previous-arc input gap
   - status: completed in `docs/2026-03-19/preflight-hollow-prev-arcs-input-gap-3pass-audit.md`
6. `Priority 5.5`: quality-dashboard persistence operator signal
   - status: completed in `docs/2026-03-19/quality-dashboard-persistence-operator-signal-3pass-audit.md`
7. then decide whether to:
   - stop the bounded remediation stream, or
   - leave the remaining items as policy/program boundaries
8. only after that, open React as a separate migration program
9. Stage 3 degraded-success observability follow-up is complete without reopening the semantic policy boundary

### Why this order is better than jumping straight to React

- it closes the last plausible narrow live highs first
- it avoids mixing remediation work with a large UI architecture program
- it keeps the current OPUS-derived stream bounded instead of sprawling

### Operational consequence

If the operator wants one more bounded pass before React, the correct next execution target is:

- `last_error_type race` first
- `ambiguous 429 classification` second

If the operator does not want any more bounded risk burn-down, then React should be opened explicitly as a new, separate program rather than as continuation of the current remediation stream.

---

## Confidence Gate

Estimated confidence for this bounded screening purpose: **95%**

Why this clears the gate:
- current 2026-03-19 status docs were cross-checked first
- React was separated from defect-remediation scope using live roadmap text
- remaining candidates were narrowed by direct code spot-check, not OPUS wording alone

Residual uncertainty:
- `last_error_type` still deserves a fresh focused code audit before direct patching
- some LLM-deepdive items remain deliberately un-exhaustive in this screening because this document is triage, not full re-audit
