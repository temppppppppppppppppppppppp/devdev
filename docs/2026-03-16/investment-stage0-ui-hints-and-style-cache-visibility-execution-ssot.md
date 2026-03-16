# investment-stage0-ui-hints-and-style-cache-visibility Execution SSOT

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/investment-stage0-ui-hints-and-style-cache-visibility-execution-ssot.md`
Temp Mirror Path: removed during closure (`docs/temp/investment-stage0-ui-hints-and-style-cache-visibility-execution-ssot.md`)
Commit State:
- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary: `dirty: tracked(main_a.py, projects/0_260316/project_data.db, deleted docs/2026-03-11/*.pdf); untracked docs/2026-03-16/*, docs/temp/*, projects/0_260316/0_temp.txt, tests/test_main_a_packaged_bootstrap_contract.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `live code already contained the intended UI/style-cache/reference changes; this loop revalidated them with targeted tests plus a fresh packaged style-analysis canary and then closed the item`
Source Survey Docs:
- `docs/2026-03-16/investment-stage0-ui-hints-and-style-cache-visibility-full-survey.md`
Evidence Artifacts:
- `docs/2026-03-16/investment-stage0-ui-hints-and-style-cache-visibility-evidence.txt`
Side-Effect Coverage: covered
Queue Disposition: closed after runtime proof and queue cleanup

## 1. Intent

- Add operator-facing recommendation tags to the packaged desktop product-production menu for investment workflows.
- Keep the visual hint work low-risk by preserving the existing action-label contract.
- Make Stage 0 `스타일 레퍼런스 분석` visibly prove which cache path ran and whether investment references were actually available.

## 2. Governing Facts

- The visible menu labels are static button markup in `geuldobi-desktop/src/index.html`.
- The renderer reuses `.label.textContent` for run-facing UI text, so recommendation tags must not be merged into the `.label` node.
- Stage 0 style-analysis cache mode already propagates from the dropdown to the backend, and the default is already `use`.
- The current operator ambiguity comes from renderer log suppression during `_bootPhase`, not from missing cache-mode plumbing.
- Packaged investment workspaces do not currently contain `config/style_references/investment`, even though packaged engine resources do.

## 3. Scope

Included:
- packaged desktop investment UI menu labels and visual affordances
- Stage 0 style-analysis cache visibility for investment runs
- investment-only missing-reference handling for packaged workspaces

Excluded:
- non-investment genre UX
- prompt-bridge redesign outside the style-analysis path
- Stage 0 classic-mode Bible/Treatment auto-selection logic
- narrative output quality or story-design policy

## 4. Realization Rules

- Preserve the literal action label text inside `.label`.
- Add recommendation text as separate badge/chip markup adjacent to `.label`.
- Keep the current default cache mode as `use`.
- Do not ship a style-analysis UX patch that can still end in silent `[System] 실행 완료` without clarifying whether:
  - cache was used
  - investment references were missing
  - analysis outputs were written

## 5. Execution Tranches

### Tranche 1 - UI Recommendation Badges

Files:
- `geuldobi-desktop/src/index.html`

Requirements:
- Add `(추천)` badge to:
  - `Frontier Lag`
  - `스타일 레퍼런스 분석`
- Add `(비추천)` badge to:
  - `Arc 설계`
  - `Blueprint`
  - `원고 생산`
  - `One-Stop`
  - `컨셉 → Bible 생성`
  - `역설계 — 기존 원고에서 추출`
  - `Bible JSON 임포트`
  - `Block 확장 — Treatment에 블록 추가`
- Make `Frontier Lag` visually strongest among the product-production buttons.
- Implement with badge spans/classes next to `.label`, not by mutating `.label` text.

Acceptance:
- the rendered buttons visibly show the requested recommendation tags
- `최근 클릭:` and any other logic reading `.label.textContent` still show the original bare action labels

### Tranche 2 - Stage 0 Style Cache Visibility

Files:
- `geuldobi-desktop/src/index.html`
- `modules/core/stage0/__init__.py`

Requirements:
- Before or at run start for `Stage 0 · 스타일 레퍼런스`, append a manager-visible log showing the selected cache mode:
  - `캐시 사용`
  - `캐시 무시 후 재분석`
  - `캐시 삭제 후 재분석`
- Ensure the operator sees the backend result summary for style analysis even when the run uses pre-injected inputs.
- The visible completion path must distinguish at least:
  - cache hit
  - refresh/reset re-analysis
  - missing investment references
  - success with output save

Governing implementation shape:
- keep `_bootPhase` suppression for generic Stage 0 runs if needed
- carve out a bounded style-analysis path so cache/result summaries are not swallowed
- do not change the existing cache-mode contract between renderer and backend

Acceptance:
- packaged investment run of `스타일 레퍼런스 분석` no longer ends with only `[System] 실행 완료`
- the visible log explicitly states the selected cache mode and the actual cache/result outcome

### Tranche 3 - Investment Reference Availability Guard

Files:
- `modules/core/stage0/style_extractor.py`
- `geuldobi-desktop/src/main.js` or equivalent bounded packaged-runtime helper, only if required by the chosen implementation path

Requirements:
- Handle the packaged investment case where workspace `config/style_references/investment` is missing.
- Keep scope bounded to investment for this task.
- Preferred operational outcome:
  - if workspace references are missing but packaged engine investment references exist, initialize the missing workspace investment reference tree from the packaged bundle and log that initialization
- Minimum acceptable outcome:
  - if bounded initialization is not taken, show an explicit visible warning that style-analysis references are missing and that no style-analysis result was produced

Guardrails:
- do not generalize to all genres in this pass
- do not silently fall back in a way that still hides whether workspace references were absent

Acceptance:
- fresh packaged investment workspace can no longer reach a silent ambiguous completion state for style analysis
- either:
  - the investment reference tree is initialized and analysis proceeds visibly
  - or the operator receives a clear blocking warning

## 6. Side-Effect Expectations

- file writes
  - UI-only badge work changes renderer HTML/CSS only
  - style-analysis success may write:
    - project DB `style_guide` anchor
    - project `stage0_output/style_guide.json`
    - workspace `config/style_references/investment/style_guide.json`
  - bounded investment initialization may create:
    - `C:\Users\wjjo\Documents\글도비\config\style_references\investment\...`
- DB writes
  - style-analysis success path writes project anchor `style_guide`
- JSONL/log sinks
  - no control-plane contract changes required
  - user-visible desktop log should become more specific
- rollback/retry
  - repeated `캐시 사용` runs should visibly report cache hit after the first successful materialization

## 7. Verification Plan

1. Static UI verification
- confirm badges render next to target labels
- confirm `.label` text remains unchanged in DOM queries used by runtime code

2. Packaged desktop investment style-analysis run
- use default cache dropdown `캐시 사용`
- confirm visible manager log shows chosen cache mode
- confirm visible result log shows cache outcome or missing-reference warning

3. Durable output verification
- on success, verify:
  - project DB anchor save
  - project `stage0_output/style_guide.json`
  - workspace cache file under `config/style_references/investment/style_guide.json`

4. Fresh packaged workspace verification
- remove or isolate workspace `config/style_references/investment`
- rerun style analysis
- confirm bounded initialization or explicit blocking warning occurs

## 8. Regression Surface

- `geuldobi-desktop/src/index.html`
  - button markup
  - badge styling
  - Stage 0 boot/log visibility behavior
- `modules/core/stage0/__init__.py`
  - style-analysis result summary path
- `modules/core/stage0/style_extractor.py`
  - investment reference path resolution and cache writes

## 9. Guardrails

- Do not change `.label` strings to include recommendation tags.
- Do not change the default style cache mode away from `use`.
- Do not land a visibility-only patch that still leaves fresh packaged investment workspaces without any clear reference-availability handling.
- Do not widen the investment-reference fix into a generic all-genre migration in this pass.

## 10. Temp Queue Notes

- temp status: completed
- queue interaction:
  - this item was closed after canonical verification and then removed from the active temp execution queue
- cleanup condition:
  - temp mirror removed during closure after canonical verification and queue refresh

## 11. Validation Hook

- validator command: `python scripts/ops_validator.py`
- execution-start rule:
  - re-run 3-pass audit against the live workspace state before patching

## 12. Closure Notes

### Implemented State

- `geuldobi-desktop/src/index.html` already exposes recommendation badges adjacent to `.label`, leaving the runtime-facing label text unchanged.
- `geuldobi-desktop/src/index.html` already exposes `stage0StyleCacheMode` selection plus bounded style-analysis boot-log visibility.
- `modules/core/stage0/style_extractor.py` already performs bounded packaged investment-reference sync into the workspace when the investment reference tree is missing.
- `modules/core/stage0/__init__.py` already logs cache-mode/result summaries and writes project-local style-analysis output.

### Verification

- targeted regressions passed:
  - `python -m pytest -q tests/test_frontend_stage0_connectivity.py tests/test_process_runner_stage0_inputs.py tests/test_stage0_work_guard_style_cache.py`
  - result: `19 passed in 1.20s`
- fresh packaged style-analysis canary passed against installed resources and a fresh temp workspace:
  - `returncode = 0`
  - workspace investment references materialized
  - workspace style cache file materialized
  - project-local `stage0_output/style_guide.json` materialized
  - project `project_data.db` materialized

### Closure Decision

- Tranche 1 is closed because the packaged renderer exposes the intended recommendation badges without mutating `.label`.
- Tranche 2 is closed because the style-analysis path now surfaces cache-mode/cache-result information instead of ending in an ambiguous silent completion.
- Tranche 3 is closed in bounded investment scope because a fresh packaged workspace now materializes the missing investment reference tree and completes style analysis successfully.

### Residual Risk

- no full Electron click-through rerun was performed in this loop; closure rests on renderer/static tests plus an installed packaged runtime canary
- bounded reference initialization is intentionally investment-only in this lane
