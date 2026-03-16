# investment-stage0-ui-hints-and-style-cache-visibility Full Survey

Date: 2026-03-16
Status: survey-complete
Canonical Path: `docs/2026-03-16/investment-stage0-ui-hints-and-style-cache-visibility-full-survey.md`
Commit State:
- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary: `dirty: tracked(main_a.py, projects/0_260316/project_data.db, deleted docs/2026-03-11/*.pdf); untracked docs/2026-03-16/*, docs/temp/*, projects/0_260316/0_temp.txt, tests/test_main_a_packaged_bootstrap_contract.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- packaged desktop UI and runtime behavior only
- investment genre only
- no code edits in this survey turn
Source Evidence:
- `docs/2026-03-16/investment-stage0-ui-hints-and-style-cache-visibility-evidence.txt`

## Findings

### High - Recommendation tags must not be merged into the existing `.label` text

Why this matters:
- the renderer reuses `.label.textContent` as execution-facing UI text
- if `(추천)` or `(비추천)` is appended directly into `.label`, click telemetry and `최근 클릭:` UI text will inherit the tag text

Evidence:
- `geuldobi-desktop/src/index.html:2781-2831` defines the visible button labels
- `geuldobi-desktop/src/index.html:6719-6727` reads `button.querySelector(".label").textContent`

Assessment:
- the safe implementation path is badge-only markup adjacent to `.label`
- recommendation chips should be visual metadata, not part of the action label contract

### High - Stage 0 style analysis already honors the desktop cache selection; the defect is visibility, not cache propagation

Why this matters:
- the current operator complaint is not that cache mode is missing from the request
- the code already propagates default `캐시 사용` end-to-end

Evidence:
- renderer default:
  - `geuldobi-desktop/src/index.html:2804-2808`
- renderer request payload:
  - `geuldobi-desktop/src/index.html:5833-5835`
- Mode B stdin injection:
  - `modules/api/process_runner.py:114-118`
  - `modules/api/process_runner.py:723-730`
  - `modules/api/process_runner.py:754-761`
- backend cache-mode resolution and success logging:
  - `modules/core/stage0/__init__.py:672-690`
  - `modules/core/stage0/__init__.py:723-730`
- extractor default and cache semantics:
  - `modules/core/stage0/style_extractor.py:942-999`

Assessment:
- default cache mode is genuinely `use`
- when the operator leaves the dropdown untouched, desktop still injects cache mode `1`
- therefore `[System] 실행 완료` alone is a visibility problem, not proof that cache mode was ignored

### High - Fresh packaged investment workspaces are missing the exact reference folder that style analysis reads

Why this matters:
- investment style analysis expects reference works in workspace-relative `config/style_references/investment`
- packaged workspace seeding never creates that folder
- this can turn style analysis into a silent no-op or a warning path with poor operator feedback

Evidence:
- packaged workspace sync copies only `bible`, `treatments`, `projects`
  - `geuldobi-desktop/src/main.js:191-214`
- build-time seed also stages only those surfaces
  - `geuldobi-desktop/scripts/build_workspace_seed.py:69-107`
- extractor reads workspace-relative path only
  - `modules/core/stage0/style_extractor.py:916-918`
  - `modules/core/stage0/style_extractor.py:961-962`
- live filesystem state:
  - missing:
    - `C:\Users\wjjo\Documents\글도비\config\style_references\investment`
  - present in repo root:
    - `C:\Users\wjjo\Desktop\글도비\config\style_references\investment`
  - present in packaged engine:
    - `C:\Users\wjjo\AppData\Local\Programs\Geuldobi\resources\engine\config\style_references\investment`

Assessment:
- UI-only copy changes are not sufficient if the goal is to make Stage 0 style-analysis behavior trustworthy in packaged investment runs
- some bounded investment-only reference-availability strategy is required

### Medium - `_bootPhase` hides the exact lines that would confirm cache behavior or missing-reference warnings

Why this matters:
- style analysis emits meaningful summary lines in the backend
- the renderer currently hides those lines for many Stage 0 runs

Evidence:
- Stage 0 always enters `_bootPhase`
  - `geuldobi-desktop/src/index.html:6859-6863`
- stdout is hidden while `_bootPhase` is true
  - `geuldobi-desktop/src/index.html:6532-6537`
- `_bootPhase` ends only on first visible prompt or run completion
  - `geuldobi-desktop/src/index.html:6282-6295`
  - `geuldobi-desktop/src/index.html:6178-6197`
- style-analysis route can receive its confirm/cache inputs without needing a visible prompt
  - `modules/api/process_runner.py:723-730`
  - `modules/api/process_runner.py:754-761`
- live run evidence confirms Stage 0 `sub_key=6` actually ran
  - `docs/2026-03-16/investment-stage0-ui-hints-and-style-cache-visibility-evidence.txt`

Assessment:
- the user-observed `Stage 0 · 스타일 레퍼런스 / [System] 실행 완료` state is consistent with the current renderer suppression logic
- the operator currently cannot distinguish:
  - cache hit
  - refresh/reset re-analysis
  - missing investment references
  - successful output materialization

### Medium - Success for style analysis should be defined by both visible confirmation and durable outputs

Why this matters:
- `[System] 실행 완료` only confirms process completion
- it does not prove style-analysis outputs were saved

Evidence:
- DB anchor save path:
  - `modules/core/stage01_helpers.py:583-594`
- project output write:
  - `modules/core/stage0/__init__.py:734-741`
- workspace cache write:
  - `modules/core/stage0/style_extractor.py:1024-1029`

Assessment:
- acceptance needs to check:
  - operator-visible cache/result message
  - project-local `style_guide` materialization
  - investment reference availability outcome

## Side-Effect Sweep

- file writes
  - UI badge-only work will touch `geuldobi-desktop/src/index.html`
  - style-analysis visibility/fallback work may also touch packaged workspace `config/style_references/investment` and project-local `stage0_output/style_guide.json`
- DB writes
  - successful style analysis writes `style_guide` anchor into the current project DB
- JSONL/log/audit sinks
  - control-plane provenance and `electron-main.log` already capture the run envelope
  - current operator-visible log is insufficiently specific for cache/result state
- console/UI output
  - main issue is renderer suppression of Stage 0 stdout summaries
- rollback/retry/recovery
  - repeated style-analysis runs can legitimately switch between cache hit, refresh, and reset behavior
  - operator needs explicit visibility of which mode actually executed
- cache/global state
  - current default is `use`
  - future changes must not silently mutate that default
- config/env/bootstrap fallback
  - investment references currently exist in packaged engine resources but not in seeded workspace
  - any remediation must keep this bounded to investment scope for this task

## Remediation Substrate

Primary substrate:
- `geuldobi-desktop/src/index.html`

Secondary substrate:
- `modules/core/stage0/__init__.py`
- `modules/core/stage0/style_extractor.py`
- possibly packaged workspace sync path in `geuldobi-desktop/src/main.js` or an equivalent investment-only runtime fallback path

Recommended execution split:
1. Add visual recommendation badges as adjacent markup, not as label mutations.
2. Make Stage 0 style-analysis cache mode and result visibly explicit in the desktop log.
3. Add bounded investment-only handling for missing packaged workspace references so the operator does not get a silent or ambiguous completion.

## Open Questions

- The exact project name used during the operator's `14:45` style-analysis run is not fully materialized in the control-plane evidence gathered here.
- Because of that, project-local absence/presence of `stage0_output/style_guide.json` should not be treated as the governing evidence for that single run.
- This does not weaken the two key conclusions:
  - cache mode propagation already exists
  - packaged investment workspace reference availability is currently incomplete

## Final Assessment

- UI recommendation-tag work is low-risk if it is kept badge-only.
- The style-analysis concern is not just UX polish. For packaged investment runs it also intersects with missing workspace reference availability.
- The correct execution document therefore needs both:
  - a low-risk UI tranche
  - a bounded runtime visibility/reference-availability tranche

Confidence:
- 98% that direct label mutation would be the wrong implementation shape
- 98% that desktop already propagates default cache mode `use`
- 96% that `_bootPhase` suppression is the main reason operators see only `실행 완료`
- 96% that fresh packaged investment workspaces lack the required reference folder
- overall survey confidence: `97%`
