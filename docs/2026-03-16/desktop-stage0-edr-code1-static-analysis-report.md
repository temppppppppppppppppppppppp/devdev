# Desktop Stage 0 `edr` Code 1 Static Analysis Report

- Date: 2026-03-16
- Scope: packaged desktop app `Stage 0 · 기존 방식 (key=0, sub_key=1)` failure on project `edr`
- Method: static codepath analysis plus already-captured workspace logs/screens only
- Fresh live run: not performed for this report

## Governance

- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary:
  - `projects/0_260316/project_data.db` modified
  - `projects/0_260316/0_temp.txt` untracked
  - prior survey docs under `docs/2026-03-16/` and `OPUS_*` docs already present
- Resume Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Resume Drift Summary:
  - documentation-only additions for this static report and its audit memo

## Sources

- Existing survey: `docs/2026-03-16/desktop-stage0-edr-code1-failure-full-survey.md`
- Existing evidence: `docs/2026-03-16/desktop-stage0-edr-code1-failure-evidence.txt`
- Existing audit: `docs/2026-03-16/desktop-stage0-edr-code1-failure-3pass-audit.md`
- Codepaths reviewed:
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/index.html`
  - `modules/api/process_runner.py`
  - `modules/api/bridge_server.py`
  - `modules/api/prompt_classifier.py`
  - `modules/core/services/ui_service.py`
  - `modules/core/stage01_helpers.py`
  - `main_a.py`
  - `modules/core/system.py`
  - `modules/core/project_manager.py`

## Conclusion

Confidence 95%: the dominant failure class is not "`edr` is empty so Stage 0 cannot start". The more likely static cause is an interactive prompt handoff gap in the packaged desktop Mode B path after `Stage 0 · 기존 방식` has already entered its post-boot prompt chain.

Stated more narrowly:

- `edr` starts as an empty shell by design.
- `Stage 0 · 기존 방식` requires more prompts than the boot-time stdin sequence covers.
- those later prompts depend on `ProcessRunner` Mode B prompt detection, `PromptBroker`, WebSocket delivery, and renderer prompt resolution
- if that chain drops, queues, or fails to resolve one of the later prompts, the user only sees `실행 실패 (code: 1)`

This report does not claim the exact final exception text. It claims the failure corridor and primary defect class.

## Findings

### 1. High: Stage 0 existing-mode requires additional interactive prompts beyond the boot sequence

Static basis:

- `ProcessRunner` Mode B only pre-injects genre, enter, project, key, and Stage 0 sub-key in `modules/api/process_runner.py:682`
- the boot sequence stops at `0 -> sub_key`; all later prompts must be handled in real time
- `Stage 0 · 기존 방식` then calls Bible selection, Treatment selection, enrichment confirm, world-origin choice, protagonist-type choice, POV choice, and more in `modules/core/stage01_helpers.py:162` and `modules/core/stage01_helpers.py:186`
- Bible and Treatment pickers themselves are interactive `Choice (...)` menus sourced from `Path("bible")` and `Path("treatments")` in `modules/core/services/ui_service.py:98` and `modules/core/services/ui_service.py:128`

Implication:

- the desktop app cannot finish Stage 0 by boot stdin alone
- successful completion depends on the prompt bridge surviving multiple follow-up prompts

### 2. High: the packaged desktop prompt bridge is the primary regression surface

Static basis:

- when a later prompt is detected, `bridge_server` classifies it, creates `PromptState(timeout_sec=300)`, waits on `broker.request_input(...)`, then writes the returned value back to stdin in `modules/api/bridge_server.py:1519`
- renderer receives `prompt_request` and opens the prompt UI in `geuldobi-desktop/src/index.html:6252` and `geuldobi-desktop/src/index.html:6278`
- renderer auto-resolves only a narrow subset:
  - `enter` prompts at `geuldobi-desktop/src/index.html:6425`
  - single-option enum prompts at `geuldobi-desktop/src/index.html:6382`
- any multi-option prompt requires a rendered prompt dialog plus explicit `_resolveCurrentPrompt(...)` submission at `geuldobi-desktop/src/index.html:6491`

Implication:

- if the WS prompt event is not surfaced, is delayed behind UI state, or is not explicitly answered, `Stage 0` stalls in the prompt corridor instead of advancing
- from the user side that can collapse into a plain `code: 1` failure even though the deeper problem is unresolved prompt flow

### 3. Medium: `edr` being an empty project directory is expected pre-boot state, not a sufficient static root cause

Static basis:

- desktop `project.create` only sanitizes the name and makes the directory with `mkdirSync(...)` in `geuldobi-desktop/src/main.js:867`
- the engine later performs the real bootstrap during boot:
  - `boot()` selects project then calls `_bind_selected_project(...)` in `main_a.py:1293`
  - `_bind_selected_project(...)` calls `boot_v20_project(...)` in `main_a.py:1182`
  - `boot_v20_project(...)` instantiates `ProjectContext(...)` in `modules/core/system.py:26`
  - `ProjectContext` creates `config/`, `drafts/`, `memory/`, `plans/`, and `project_data.db` in `modules/core/project_manager.py:69`, `modules/core/project_manager.py:72`, and `modules/core/project_manager.py:88`

Implication:

- a newly created project directory with no `project_data.db` is normal before first successful engine bind
- “`edr` is empty” explains why no durable state exists yet, but does not statically explain why the run returns `code: 1`

### 4. Medium: project selection remains index-authoritative in the run contract

Static basis:

- renderer sends both `project_index` and `project_name` from `_collectInputs()` in `geuldobi-desktop/src/index.html:5807`
- project index is derived from the lexical project list in `geuldobi-desktop/src/index.html:5870`
- `ProcessRunner` still feeds the engine with numeric `project_index` in `modules/api/process_runner.py:719`
- `_resolve_requested_project_name(...)` exists, but the engine-driving stdin path is still index-based in `modules/api/process_runner.py:142` and `modules/api/process_runner.py:682`

Implication:

- this is a real regression surface for future drift
- it is not the strongest static explanation for the present `edr` failure, but it remains a secondary contract risk

### 5. Medium: observability is not strong enough to expose the actual Stage 0 prompt that failed

Static basis:

- the backend does remember only `last_prompt_step` in runner diagnostics in `modules/api/process_runner.py:440`
- renderer handles `run_failed` and can mention the last prompt step, but manager logs shown by the user remained at `code: 1` only
- prompt classification currently normalizes many menus to generic `choice` in `modules/api/prompt_classifier.py:29`

Implication:

- even if the true break is “the third follow-up prompt was never answered”, the surfaced signal can still look like a generic process failure
- this makes the interactive-handoff defect class harder to distinguish from engine bootstrap failure unless logs are inspected deeply

## Ruled-Out or Deprioritized Hypotheses

### Empty `edr` shell as primary cause

Deprioritized. Static code says the empty directory is an expected artifact of desktop project creation and should be hydrated during project bind.

### Bible/Treatment source missing

Deprioritized. Existing evidence already established the workspace has the expected files, and `Stage 0 · 기존 방식` is explicitly designed to prompt for them rather than fail immediately.

### “Stage 0 inner generation logic is broken before any prompt”

Deprioritized. Static code shows several prompt steps must occur before the heavy generation path proceeds.

## Failure Corridor

1. renderer saves project name and 1-based lexical `project_index`
2. `/run` starts Mode B with only the boot sequence pre-seeded
3. engine enters `Stage 0 · 기존 방식`
4. engine asks Bible/Treatment and later follow-up prompts
5. each follow-up prompt must traverse:
   - `ProcessRunner` prompt detection
   - `PromptBroker`
   - WS event delivery
   - renderer prompt UI
   - `resolvePrompt(...)`
   - `runner.write_stdin(...)`
6. if one prompt in that chain is not resolved, the run terminates as `code: 1`

## Open Questions

- Which exact prompt in the post-boot chain failed first in the packaged app:
  - Bible selection
  - Treatment selection
  - enrichment confirm
  - world-origin choice
  - protagonist-type choice
  - POV choice
- Whether the packaged renderer failed to open the prompt overlay, or opened it but failed to resolve the response
- Whether the generic `choice` classification reduced useful failure telemetry enough to mask the exact break site

## Recommended Remediation Substrate

- make `project_name` authoritative for engine project selection; keep `project_index` only as fallback
- surface full `prompt_text`, `prompt_id`, and pending-prompt count into the visible manager log on `run_failed`
- add deterministic handling for known Stage 0 follow-up prompts, not only single-option enums
- preserve unresolved prompt state across renderer/UI refresh so `prompt_request` cannot disappear behind a stale view state

## Final Statement

Static analysis supports this answer:

`Stage 0` failed because packaged desktop execution depends on a real-time prompt bridge after boot, and `Stage 0 · 기존 방식` asks for additional follow-up selections that the current bridge/UI path is not robustly guaranteed to resolve. The empty `edr` directory is a normal pre-bootstrap state, not the primary static root cause.
