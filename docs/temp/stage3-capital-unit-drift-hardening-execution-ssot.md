# Stage 3 Capital Unit Drift Hardening - Execution SSOT

Date: 2026-03-30
Status: ready-for-execution
Confidence: 96%
Canonical Path: `docs/2026-03-30/stage3-capital-unit-drift-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md`
Baseline Commit: `9ad4efcc`
Source Survey Doc: `docs/2026-03-30/stage3-capital-unit-drift-bounded-survey.md`
Related Docs:
- `docs/2026-03-30/stage3-blueprint-validator-hardening-execution-ssot.md`
- `docs/2026-03-30/0_1-stage3-blueprint-ep16-20-integrity-bounded-survey.md`

## 1. Bug Statement

Stage 3 still has a missing validator contract for one investment-genre family:

- authoritative arc/state packet is KRW-dominant
- blueprint introduces a USD-denominated capital deployment amount
- plain `PASS` can still survive because no binding invariant covers this unit mismatch

Current live `EP17` no longer contains the bad literal because the artifact was manually repaired.
This SSOT is therefore preventive, not restorative.

## 2. Authoritative Contract

### 2.1 What already exists

- `blueprint_constraint_compiler.py`
  - emits `[CAPITAL-LOCK]`
  - includes `capital_continuity_packet`
- `unified_blueprint_validator.py`
  - already checks:
    - `capital_state`
    - `phantom_capital`
  - already has a binding contract for:
    - `scene_completeness`
    - `arc_timeline`

### 2.2 What is missing

Missing invariant:

- `capital_unit`

Definition:

- if the authoritative capital packet is clearly KRW-dominant
- and the blueprint introduces a USD-denominated amount in capital/deployment context
- the validator must emit a `MAJOR` issue

Missing verdict binding:

- plain `PASS` must not survive this issue unchanged
- it should enter the existing `PASS_WITH_FIX` repair lane

## 3. Root Cause Chain

1. The generator already receives capital continuity guidance.
2. The current validator only detects continuity contradictions and phantom reappearance of deployed capital.
3. It does not check cross-unit capital deployment drift.
4. The binding contract currently excludes that family.
5. Therefore a wrong-unit deployment amount can still emerge and pass if Director scores the narrative favorably.

## 4. Tranche Scope

### In scope

- Stage 3 validator hardening for `capital_unit`
- binding escalation for that category
- focused tests

### Out of scope

- empty `scene content` hardening
- relationship `from_state` regression hardening
- generator prompt rewrite
- broad `quality_risk => REJECT` policy
- DB or runtime orchestration changes

## 5. Recommended Implementation

## 5.1 V-4 capital unit drift collector

Add a new collector in `unified_blueprint_validator.py`.

Suggested shape:

- name:
  - `_collect_capital_unit_alignment_issues()`
- inputs:
  - `integrated`
  - `constraint_block`
- output:
  - bounded list of issues

Behavior:

1. Read `constraint_block["capital_continuity_packet"]["fields"]`.
2. Infer the authoritative capital unit regime.
   - `KRW-dominant` if packet contains at least two KRW-style capital entries and no strong competing USD capital regime.
3. Scan blueprint text for currency-denominated amounts in deployment context.
4. Flag `MAJOR` when:
   - amount is USD-denominated
   - context implies deployment/capital use
   - authoritative packet is KRW-dominant

Recommended category:

- `capital_unit`

Recommended issue text:

- `자본 단위 불일치: KRW 기준 arc/state에 USD 투입 금액이 등장`

Recommended fix hint:

- `capital_continuity_packet 기준 단위를 유지하고, 투입/증거금/총자산 수치를 arc/state packet과 정합시킬 것`

## 5.2 Context classification

The collector should be narrow.

Positive capital/deployment contexts:

- `증거금`
- `투입`
- `추가 증거금`
- `예치`
- `잔고`
- `가용 현금`
- `자산`
- `총자산`
- `유동성`
- `자본`
- `청산 대금`

Negative / do-not-flag contexts:

- commodity price quotes such as `700달러`
- `온스당`
- `호가`
- `가격`
- `지표`
- `FOMC`
- generic macro text like `달러 유동성`

Practical heuristic:

- require both:
  - USD-denominated amount token
  - nearby capital/deployment keyword
- skip if nearby context is clearly price-quote oriented

## 5.3 Binding contract

Extend `_BINDING_PREVALIDATION_CATEGORIES` to include:

- `capital_unit`

Behavior:

1. Single-candidate path
   - if Director says `PASS` and `capital_unit` is `MAJOR/CRITICAL`
   - coerce to `PASS_WITH_FIX`

2. Compare path
   - if selected candidate result is `PASS` and selected prevalidation contains `capital_unit`
   - coerce to `PASS_WITH_FIX`

3. Preserve stronger outcomes
   - `PASS_WITH_FIX` stays `PASS_WITH_FIX`
   - `REJECT` stays `REJECT`

## 6. Touched File Set

Production:

- `modules/domain/agents/unified_blueprint_validator.py`

Tests:

- `tests/test_unified_blueprint_validator_lane_c.py`

No other production file should be required in this tranche.

## 7. Validation Matrix

1. Positive direct prevalidation case
   - KRW-dominant packet
   - blueprint text contains `500만 달러` in `추가 증거금` context
   - expect `capital_unit` `MAJOR`

2. Negative price-only case
   - same KRW-dominant packet
   - blueprint text contains only `700달러` commodity price
   - expect no `capital_unit`

3. Binding single-candidate case
   - Director returns `PASS`
   - prevalidation contains `capital_unit`
   - expect final verdict `PASS_WITH_FIX`

4. Binding compare-path case
   - compare result returns `PASS`
   - selected candidate contains `capital_unit`
   - expect returned verdict `PASS_WITH_FIX`

5. Non-binding preservation
   - `capital_state` or generic advisory remains non-binding
   - no broad escalation regression

## 8. Closure Criteria

This lane closes only if all are true:

1. `capital_unit` issue is emitted for USD deployment drift under KRW authority
2. commodity price mentions do not false-positive
3. single-candidate `PASS` becomes `PASS_WITH_FIX`
4. compare-path `PASS` becomes `PASS_WITH_FIX`
5. focused pytest, `ruff`, `py_compile`, and UTF-8 hygiene all pass

## 9. Non-Goals / Guardrails

- do not convert all money mentions into hard validation
- do not bind all `capital_state` findings
- do not rewrite Director prompt contracts in this tranche
- do not couple this fix to EP18/19 scene-content work
- do not couple this fix to Stage 4 or Stage 2 code

## 10. Implementation Order

1. re-read survey + this SSOT
2. add `capital_unit` collector
3. wire collector into `_python_pre_validate()`
4. extend binding category set
5. add focused tests
6. run focused validation

## 11. 3-Pass Audit

### Pass 1 - Fact verification

- confirmed capital packet is already built and prompt-visible
- confirmed current validator lacks a capital-unit invariant
- confirmed current binding set excludes capital-unit drift

### Pass 2 - Logic completeness

- verified this tranche fills a real blind spot left by the prior Stage 3 hardening wave
- verified the existing `PASS_WITH_FIX` lane is the correct bounded repair target

### Pass 3 - Side effects / omissions

- kept scope to validator-only plus binding extension
- intentionally deferred scene-content and relationship semantics
- avoided a global policy escalation

Final judgment:

- execution-ready
- single-file production patch remains the lowest-risk path
