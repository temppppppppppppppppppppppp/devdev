# Material-Side Block / Arc Harness Normalization Execution SSOT

Date: 2026-03-30
Status: closed (3-pass audited, realized)
Canonical Path: `docs/2026-03-30/material-side-block-arc-harness-normalization-execution-ssot.md`
Temp Mirror Path: `docs/temp/material-side-block-arc-harness-normalization-execution-ssot.md`
Commit State:
- Baseline Commit: `e52c061ac1f3fdb95a4b1149b4ea66243961656a`
- Baseline Dirty Summary: `dirty: tracked narrative docs and stage0 harness docs, tracked chaebol TR/BI artifacts, many pre-existing untracked temp/reference assets`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-30/material-side-block-arc-harness-semantics-survey.md`
Evidence Artifacts:
- inline source evidence only
Side-Effect Coverage: covered
Confidence: 96%

## 1. Intent

`재료 사이드 하네스`만 대상으로 `block / macro arc / episode checkpoint` 의미를 정규화한다.

이번 SSOT의 목적은 code patch가 아니다.

목적은 다음 셋이다.

1. Stage 0 문서가 `block != episode`를 먼저 선언하게 만들기
2. material 수집 문서가 `source checkpoint -> block-scale extraction` 번역 규칙을 갖게 만들기
3. source manifest handoff가 `opening representative spike`와 downstream `TR Block 1 spike`를 구분하게 만들기

## 2. Baseline Facts

- `what-how`는 이미 `1 block ~= 5화`라고 본다.
- blockguide planning/production은 `7대단원`, `각 10블록` 구조를 canonical로 쓴다.
- Stage 0 하네스는 현재 이 의미를 부정하지는 않지만, dedicated semantics table이 없다.
- `stage0_material_collection_harness.md`는 `ep1`과 `Block 1`을 같은 문장에 병치한다.
- `stage0_source_manifest_harness.md`는 `Block 1 spike` extraction을 요구하지만 source checkpoint translation rule을 먼저 선언하지 않는다.
- 현재 operator-side Phase 0 설계 감각은 이미 `ARC-01 대표 스파이크` 쪽이 더 안정적이라는 방향을 보여 준다.

## 3. Scope

Included:
- `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
- `전처리_ssot/docs/stage0_material_collection_harness.md`
- `전처리_ssot/docs/stage0_source_manifest_harness.md`

Excluded:
- `modules/`, `scripts/`, `tests/`
- runtime arc math or validation logic
- work-level `phase0_design`, `TR`, `BI` 본문 수정
- `docs/blockguide/*.md` 본문 수정
- family-wide terminology redesign

## 4. Pass 1. Inventory Summary

- primary harness targets: `3`
- downstream reference-only docs: `3`
  - `docs/narrative-router/what-how-craft-harness.md`
  - `docs/blockguide/treatment-planning-harness.md`
  - `docs/blockguide/treatment-production-harness-v2.md`
- confirmed drift classes: `3`
  - missing semantics table
  - mixed source checkpoint vs block extraction wording
  - ambiguous spike vocabulary at Stage 0 handoff

## 5. Pass 2. Semantic Classification

- Class A. Stage 0 entry semantics
  - goal: define `block`, `macro arc`, `episode checkpoint`
  - file: `SSOT_stage0_preprocess_integrated_order.md`
- Class B. Material collection translation contract
  - goal: separate source sampling anchors from extracted design units
  - file: `stage0_material_collection_harness.md`
- Class C. Source manifest handoff contract
  - goal: normalize `opening representative spike`, `first reward`, `authority gain route`
  - file: `stage0_source_manifest_harness.md`

## 6. Side-Effect Map

- file writes / artifacts:
  - yes; harness docs only
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - not applicable
- console / UI / operator output:
  - operator-facing semantics and future authoring behavior will change
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

Substrate:

- no code substrate
- no schema work
- no runtime contract migration

Contract strategy:

1. add one authoritative semantics table at Stage 0 entry
2. propagate that table downstream as wording constraints, not as a second competing definition set
3. normalize collection/manifests around translation language:
   - `episode checkpoint`
   - `block-scale extraction`
   - `opening representative spike`
4. keep downstream blockguide docs as reference authority, not edit surface, for this wave

## 8. Execution Tranches

1. `Stage 0 entry contract`
   - add a short semantics section that explicitly defines:
     - `block`
     - `macro arc`
     - `episode checkpoint`
   - add a rule that Stage 0 never treats episode checkpoints as direct design units

2. `Material collection translation rule`
   - replace any wording that treats `ep1` and `Block 1` as interchangeable
   - add a conversion note:
     - source evidence may come from `ep1/ep5/ep10/...`
     - extracted fuel must be restated in block-scale language

3. `Source manifest extraction rule`
   - distinguish:
     - `opening representative spike`
     - `first reward retention`
     - `authority gain route`
   - reserve `TR Block 1 spike` phrasing for downstream planning/production use only

4. `Final doc audit`
   - run 3-pass adversarial re-audit on the touched harness docs
   - refresh this execution SSOT against live workspace before any harness edits begin

## 9. Acceptance Criteria

- `전처리_ssot` entry docs explicitly separate:
  - `block`
  - `macro arc`
  - `episode checkpoint`
- Stage 0 docs no longer leave `ep1` and `Block 1` as an unqualified equivalence
- Stage 0 docs use block-scale extraction vocabulary for opening payoff design
- no runtime code files are touched
- touched docs pass UTF-8 hygiene

## 10. Verification Plan

- `rg -n "ep1|Block 1 spike|macro arc|대단원|episode checkpoint" 전처리_ssot/docs/*.md`
- `python scripts/check_utf8_hygiene.py 전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md 전처리_ssot/docs/stage0_material_collection_harness.md 전처리_ssot/docs/stage0_source_manifest_harness.md`
- document 3-pass adversarial audit before saving the harness edits

## 11. Guardrails

- do not patch `modules/`, `scripts/`, or `tests/`
- do not patch work-level TR/BI artifacts in this wave
- do not redefine blockguide `10블록 대단원` structure
- do not import runtime `arc` semantics into Stage 0 wording
- do not leave parallel vocabularies that compete with downstream blockguide authority

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition:
  - completed; temp mirror removed after canonical closure update, roadmap refresh, queue-state sync, and validator pass
- roadmap dependency:
  - reflected in the active temp execution roadmap and then closed out of the temp queue

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before editing the harness docs from this document

## 14. Closure Note

Realization date:

- `2026-03-30`

Touched harness docs:

- `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
- `전처리_ssot/docs/stage0_material_collection_harness.md`
- `전처리_ssot/docs/stage0_source_manifest_harness.md`

What landed:

- Stage 0 entry now carries an explicit semantics table for `block`, `macro arc`, `episode checkpoint`, and `opening representative spike`
- material collection now distinguishes source checkpoints from block-scale extraction
- source manifest now reserves `TR Block 1 spike` for downstream planning / production and uses Stage 0 extraction wording instead

Verification:

- `rg -n "episode checkpoint|macro arc|opening representative spike|TR Block 1 spike|ep1|Block 1" 전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md 전처리_ssot/docs/stage0_material_collection_harness.md 전처리_ssot/docs/stage0_source_manifest_harness.md`
- `python scripts/check_utf8_hygiene.py 전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md 전처리_ssot/docs/stage0_material_collection_harness.md 전처리_ssot/docs/stage0_source_manifest_harness.md`

Residual risk:

- downstream blockguide planning / production docs still intentionally use `Block 1 spike` phrasing; that is not a Stage 0 defect
- no runtime semantics were changed in this wave by design
