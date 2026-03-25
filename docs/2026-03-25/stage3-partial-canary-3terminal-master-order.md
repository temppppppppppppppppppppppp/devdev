# Stage3 Partial Canary 3-Terminal Master Order

Date: 2026-03-25
Status: survey-master-order
Document Type: system-track survey master order
Canonical Path: `docs/2026-03-25/stage3-partial-canary-3terminal-master-order.md`
Temp Mirror Path: none (survey-only)
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: active canary runtime/log artifacts plus prior dated docs; no active temp execution queue`

## 1. Intent

Stop the current canary after Stage 3 evidence is sufficient, and run a bounded 3-lane survey on the Stage 3 partial canary only.

This is not a full canary closure.

This is a Stage 3 partial-canary re-audit answering:

- did the recently closed Stage 3 waves actually suppress the old Stage 3 culprit family in a fresh live run?
- what exactly is the remaining meaning of the EP7 `inventory gap` mention and EP8 temporal-deictic warning?

## 2. Scope

Included:
- `projects/canary_0325/` Stage 3 logs and Stage 3 blueprint artifacts
- console evidence for the current canary up through Stage 3 completion
- Stage 3 code paths for:
  - fact-lock / capital-lock
  - inventory gap synthesis
  - temporal-deictic prevalidation
  - Director compare / Stage 3 PASS rationale

Excluded:
- Stage 4 manuscript generation
- Stage 4 retry / rescue-round behavior
- full canary completion or closure
- new execution SSOT creation
- temp queue manipulation
- code changes

## 3. Governing Question

The 3 lanes together must determine:

1. whether the old Stage 3 residual family is now suppressed in the fresh canary
2. whether the `한미증권`-class institution drift has actually disappeared from Stage 3 artifacts
3. whether stale / phantom capital carry-forward has disappeared from Stage 3 artifacts
4. whether `inventory gap` is only advisory noise in this run
5. whether the EP8 temporal-deictic warning is a healthy catch or a new blocker

## 4. Shared Guardrails

- Survey only. No code changes.
- Do not continue Stage 4 analysis for this order.
- Do not create or update execution SSOTs.
- Do not touch `docs/temp/`.
- Do not overwrite shared canonical reports.
- Save only lane docs under `docs/2026-03-25/opus-stage3-partial-canary/`.
- Use file/line anchors.
- Prefer artifact truth over console paraphrase.
- Distinguish:
  - clean suppression
  - reduced but still present
  - replaced by a new Stage 3 issue
- If the canary was stopped mid-Stage 4, do not treat missing Stage 4 evidence as a regression.

## 5. Shared Evidence Surfaces

Required:
- `docs/2026-03-24/console.txt`
- `projects/canary_0325/logs/episode_production.jsonl`
- `projects/canary_0325/logs/artifacts/stage3/`
- `projects/canary_0325/plans/blueprints/`
- `projects/000000/` prior truth only when needed for comparison
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage3_orchestrator.py`

Optional:
- `projects/canary_0325/project_data.db`
- `projects/canary_0325/logs/session/llm_io.jsonl`

## 6. Lane Assignment

### T1. Stage3 Canary Chronology

Purpose:
- reconstruct the Stage 3 canary run only
- produce per-episode PASS matrix and watchlist summary

Focus:
- EP1-EP9 blueprint verdict flow
- Stage 3 scores / strategies / warnings
- first appearance of EP7 inventory gap mention
- first appearance of EP8 temporal-deictic warning

Save paths:
- `docs/2026-03-25/opus-stage3-partial-canary/t1-stage3-canary-chronology.md`
- optional: `docs/2026-03-25/opus-stage3-partial-canary/t1-stage3-canary-chronology-evidence.md`

### T2. Blueprint Artifact Truth

Purpose:
- inspect the actual Stage 3 blueprint artifacts for EP5-EP9
- confirm whether the old culprit family is really gone on disk

Focus:
- institution names / venue names
- capital state / deployed vs available language
- inventory gap mentions and whether they are advisory-only
- temporal-deictic final blueprint output at EP8

Comparison targets:
- prior known failure family from `0324_00_`
- prior accepted canon only when required to prove suppression

Save paths:
- `docs/2026-03-25/opus-stage3-partial-canary/t2-blueprint-artifact-truth.md`
- optional: `docs/2026-03-25/opus-stage3-partial-canary/t2-blueprint-artifact-truth-evidence.md`

### T3. Stage3 Code / Mechanism Audit

Purpose:
- explain which Stage 3 mechanisms likely produced the observed partial-canary result

Focus:
- fact-lock packet behavior
- capital continuity packet behavior
- `inventory_gaps` synthesis and operator visibility
- temporal-deictic prevalidation behavior
- how Stage 3 can PASS all episodes while still surfacing bounded warnings

Save paths:
- `docs/2026-03-25/opus-stage3-partial-canary/t3-stage3-mechanism-audit.md`
- optional: `docs/2026-03-25/opus-stage3-partial-canary/t3-stage3-mechanism-audit-evidence.md`

## 7. Required Output Shape

Each lane must:
- list findings first
- avoid merged conclusions
- avoid execution proposals beyond bounded notes
- include confidence and limits

Mandatory final lines for every lane:
- Old Stage 3 culprit family in this lane: `suppressed / reduced / unchanged / not-applicable`
- New Stage 3 concern in this lane: `none / <short label>`
- Should this lane alone trigger a new SSOT: `yes / no`

## 8. Merge Target

After all 3 lanes return, Codex will decide whether to create:
- no new SSOT
- a tiny follow-up survey
- or a bounded new execution SSOT

The lanes must not do this themselves.

## 9. Common Opus Order

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-25/stage3-partial-canary-3terminal-master-order.md
6. docs/2026-03-24/console.txt

Task:
Survey the Stage 3 partial canary only.
Do not continue into Stage 4 analysis.

Primary goal:
Determine whether the old Stage 3 culprit family is actually suppressed in `projects/canary_0325`, and classify the remaining meaning of the EP7 inventory-gap mention and EP8 temporal-deictic warning.

Hard constraints:
- Survey only. No code changes.
- Ignore Stage 4 for this order.
- Do not create execution SSOTs.
- Do not touch docs/temp.
- Do not overwrite shared reports.
- Save only your lane report under docs/2026-03-25/opus-stage3-partial-canary/.
- Prefer artifact truth over console paraphrase.

Mandatory final lines:
- Old Stage 3 culprit family in this lane: suppressed / reduced / unchanged / not-applicable
- New Stage 3 concern in this lane: none / <short label>
- Should this lane alone trigger a new SSOT: yes / no
```

## 10. Terminal Overrides

### T1 Override

```text
docs/2026-03-25/stage3-partial-canary-3terminal-master-order.md + 넌 1번 터미널.
저장:
- docs/2026-03-25/opus-stage3-partial-canary/t1-stage3-canary-chronology.md
- 필요시 docs/2026-03-25/opus-stage3-partial-canary/t1-stage3-canary-chronology-evidence.md
Stage 3 canary chronology만 정리해. EP1-EP9 PASS matrix, strategy, score, warning watchlist 위주로.
```

### T2 Override

```text
docs/2026-03-25/stage3-partial-canary-3terminal-master-order.md + 넌 2번 터미널.
저장:
- docs/2026-03-25/opus-stage3-partial-canary/t2-blueprint-artifact-truth.md
- 필요시 docs/2026-03-25/opus-stage3-partial-canary/t2-blueprint-artifact-truth-evidence.md
EP5-EP9 stage3 final_blueprint 실물만 보고 old institution/capital culprit family가 정말 사라졌는지 조사해.
```

### T3 Override

```text
docs/2026-03-25/stage3-partial-canary-3terminal-master-order.md + 넌 3번 터미널.
저장:
- docs/2026-03-25/opus-stage3-partial-canary/t3-stage3-mechanism-audit.md
- 필요시 docs/2026-03-25/opus-stage3-partial-canary/t3-stage3-mechanism-audit-evidence.md
fact_lock / capital_lock / inventory_gaps / temporal-deictic prevalidation이 이번 partial canary 결과를 어떻게 만들었는지 code-mechanism만 조사해.
```
