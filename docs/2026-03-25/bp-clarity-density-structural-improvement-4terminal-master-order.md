# BP Clarity + Density Structural Improvement 4-Terminal Master Order

Date: 2026-03-25
Status: survey-master-order
Document Type: system-track survey master order
Canonical Path: `docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md`
Temp Mirror Path: none (survey-only)
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: recent live-run artifacts, closed Stage 3 docs, survey docs, no active temp execution queue`

## 1. Intent

Run a 4-lane parallel survey on one topic:

- structural and root-cause improvement options for blueprint clarity and density

This survey is intentionally independent from the current canary runtime.

Canary findings may later be used as supporting evidence, but they are not required for this order to proceed.

## 2. Core Question

If blueprint quality is currently limited by vagueness, mixed authority, thin per-episode guidance, or weak self-checking, where is the highest-ROI structural fix surface?

This master order must help answer:

1. is blueprint clarity/density mainly limited upstream by Stage 2 inputs?
2. is it mainly limited inside Stage 3 authority layering and output schema?
3. is it mainly limited by weak prevalidation / quality signals?
4. is prompt-level self-audit the right next move, or only a secondary amplifier?

## 3. Scope

Included:
- Stage 2 arc payloads that feed Stage 3
- Stage 3 prompt assembly, authority layering, and blueprint schema
- Stage 3 prevalidation / quality-risk / structure checks
- historical good/bad blueprint artifacts when needed for evidence
- bounded structural improvement options for clarity and density

Excluded:
- Stage 4 manuscript generation redesign
- Director policy redesign
- retry semantics redesign
- DB schema redesign
- temp queue / execution SSOT creation
- immediate code changes

## 4. Shared Guardrails

- Survey only. No code changes.
- Do not create execution SSOTs.
- Do not modify `docs/temp/`.
- Do not overwrite shared canonical reports.
- Save only lane outputs under `docs/2026-03-25/opus-bp-clarity-density/`.
- Findings first.
- Prefer live code and artifact truth over prior survey rhetoric.
- Distinguish:
  - upstream input insufficiency
  - Stage 3 authority ambiguity
  - validation blind spot
  - prompt/self-audit opportunity
- Do not overclaim density as the culprit unless the lane positively proves it.
- Do not default to broad refactor proposals. Keep options bounded and operational.

## 5. Shared Evidence Surfaces

Required code surfaces:
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/arc_draft_validator.py`
- `modules/domain/agents/unified_arc_validator.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/tactical_utils.py`
- `modules/core/response_schemas.py`

Optional evidence surfaces:
- `projects/00_001/` Stage 2 and Stage 3 artifacts
- `projects/0324_00_/` Stage 2 and Stage 3 artifacts
- `projects/canary_0325/` Stage 3 artifacts if already available
- dated merge audits / survey docs from `docs/2026-03-24/`

## 6. Lane Assignment

### T1. Stage2 Upstream Specificity

Purpose:
- determine whether Stage 3 clarity/density is capped by Stage 2 payload quality

Focus:
- `episode_details`
- `tactical_doc`
- `beat_sequence`
- allocation / per-episode specificity
- whether Stage 2 currently emits enough concrete material for a crisp blueprint without overreaching

Questions:
- Is `episode_details` still too sparse or only secondary?
- Does `tactical_doc` carry the real specificity while `episode_details` stays too compressed?
- Which Stage 2 field actually dominates downstream blueprint clarity?

Save paths:
- `docs/2026-03-25/opus-bp-clarity-density/t1-stage2-upstream-specificity.md`
- optional: `docs/2026-03-25/opus-bp-clarity-density/t1-stage2-upstream-specificity-evidence.md`

### T2. Stage3 Authority + Schema Bands

Purpose:
- determine whether blueprint blur comes from Stage 3 mixing too many coequal authority surfaces

Focus:
- `must_focus`
- `arc_focus`
- `scene_breakdown`
- `integrated_scenario`
- `fact_lock_packet`
- `capital_continuity_packet`
- schema contracts in `response_schemas.py`

Questions:
- Which surfaces are treated as authoritative vs advisory in practice?
- Does `integrated_scenario` still overtake structured scene authority anywhere?
- Is the current blueprint schema itself too loose to preserve clarity and density cleanly?

Save paths:
- `docs/2026-03-25/opus-bp-clarity-density/t2-stage3-authority-schema.md`
- optional: `docs/2026-03-25/opus-bp-clarity-density/t2-stage3-authority-schema-evidence.md`

### T3. Stage3 Prevalidation + Quality Signal Coverage

Purpose:
- determine whether blueprint clarity/density problems survive because the Stage 3 quality gate cannot see them

Focus:
- `unified_blueprint_validator.py`
- `quality_risk`
- `python_warnings`
- structure / fidelity / continuity / temporal checks
- any existing density / scene-specificity / authority-drift checks

Questions:
- What clarity/density failures can current prevalidation already catch?
- What materially important blueprint blur is still invisible?
- Is the current `quality_risk` signal too generic for operator action?

Save paths:
- `docs/2026-03-25/opus-bp-clarity-density/t3-stage3-prevalidation-coverage.md`
- optional: `docs/2026-03-25/opus-bp-clarity-density/t3-stage3-prevalidation-coverage-evidence.md`

### T4. Bounded Structural Improvement Option Ledger

Purpose:
- produce bounded improvement options without implementing them

Focus:
- prompt-level self-audit
- schema tightening
- authority re-banding
- advisory vs hard-lock separation
- upstream specificity floor
- operator-facing quality signal sharpening

Questions:
- If we wanted one small next wave for blueprint clarity/density, what are the best bounded candidates?
- Which options are structural/root-cause, and which are cosmetic or secondary?
- Which options pair naturally, and which should stay separated for clean canary interpretation?

Guardrail:
- This lane must not act like final merge owner.
- It can propose bounded options, not choose the final wave.

Save paths:
- `docs/2026-03-25/opus-bp-clarity-density/t4-bounded-improvement-option-ledger.md`
- optional: `docs/2026-03-25/opus-bp-clarity-density/t4-bounded-improvement-option-ledger-evidence.md`

## 7. Required Output Shape

Each lane must:
- list findings first
- avoid merged cross-lane conclusions
- avoid implementation claims
- include confidence and limits

Mandatory final lines for every lane:
- Dominant limiter in this lane: `upstream specificity / authority mixing / validation blind spot / self-audit opportunity / mixed / none`
- Best bounded improvement candidate in this lane: `<short label>`
- Should this lane alone trigger a new SSOT: `yes / no`

## 8. Merge Rule

After all 4 lanes return, Codex will decide:
- whether a bounded execution SSOT should be opened
- whether the next wave should be Stage 2, Stage 3, or prompt/self-audit focused
- whether the canary evidence changes that decision

The lanes must not do this themselves.

## 9. Common Opus Order

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md
6. docs/2026-03-24/console.txt

Task:
Survey structural and root-cause improvement options for blueprint clarity and density.
Survey only. No code changes.

Primary goal:
Determine whether the highest-ROI next improvement for blueprint clarity/density lives in:
- Stage 2 upstream specificity
- Stage 3 authority/schema structure
- Stage 3 prevalidation coverage
- or prompt/self-audit reinforcement

Hard constraints:
- Survey only. No code changes.
- Do not create execution SSOTs.
- Do not touch docs/temp.
- Do not overwrite shared reports.
- Save only your lane output under docs/2026-03-25/opus-bp-clarity-density/.
- Keep conclusions bounded and evidence-led.
- Do not default to broad refactor proposals.
- Distinguish root-cause improvement from secondary polish.

Mandatory final lines:
- Dominant limiter in this lane: upstream specificity / authority mixing / validation blind spot / self-audit opportunity / mixed / none
- Best bounded improvement candidate in this lane: <short label>
- Should this lane alone trigger a new SSOT: yes / no
```

## 10. Terminal Overrides

### T1 Override

```text
docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md + 넌 1번 터미널.
저장:
- docs/2026-03-25/opus-bp-clarity-density/t1-stage2-upstream-specificity.md
- 필요시 docs/2026-03-25/opus-bp-clarity-density/t1-stage2-upstream-specificity-evidence.md
Stage 2 입력이 blueprint 선명도/밀도를 어디까지 결정하는지 조사해. episode_details, tactical_doc, beat_sequence, per-episode specificity 위주로.
```

### T2 Override

```text
docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md + 넌 2번 터미널.
저장:
- docs/2026-03-25/opus-bp-clarity-density/t2-stage3-authority-schema.md
- 필요시 docs/2026-03-25/opus-bp-clarity-density/t2-stage3-authority-schema-evidence.md
Stage 3에서 blueprint authority band가 어떻게 섞이는지 조사해. must_focus, arc_focus, scene_breakdown, integrated_scenario, fact/capital lock, schema contract 위주로.
```

### T3 Override

```text
docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md + 넌 3번 터미널.
저장:
- docs/2026-03-25/opus-bp-clarity-density/t3-stage3-prevalidation-coverage.md
- 필요시 docs/2026-03-25/opus-bp-clarity-density/t3-stage3-prevalidation-coverage-evidence.md
Stage 3 prevalidation과 quality_risk가 blueprint 선명도/밀도 문제를 얼마나 실제로 볼 수 있는지 조사해.
```

### T4 Override

```text
docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md + 넌 4번 터미널.
저장:
- docs/2026-03-25/opus-bp-clarity-density/t4-bounded-improvement-option-ledger.md
- 필요시 docs/2026-03-25/opus-bp-clarity-density/t4-bounded-improvement-option-ledger-evidence.md
구조적/근원적 개선 옵션을 bounded하게 정리해. prompt self-audit, schema tightening, authority re-banding, upstream specificity floor 중 무엇이 next wave 후보인지 option ledger로만 적어.
```

## 11. Short Dispatch

```text
docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md 읽고 survey-only로 진행. BP 선명도/밀도의 구조적 개선 방안만 조사하고, 코드수정/SSOT/temp queue는 건드리지 마.
```
