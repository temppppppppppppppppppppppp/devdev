# desktop-stage0-edr-code1-failure Execution SSOT

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/desktop-stage0-edr-code1-failure-execution-ssot.md`
Temp Mirror Path: `removed during closure (was docs/temp/desktop-stage0-edr-code1-failure-execution-ssot.md)`
Queue Disposition: `closed after packaged runtime verification and queue cleanup`
Commit State:
- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary: `dirty: 1 tracked, 13 untracked; hotspots: projects/0_260316/project_data.db, docs/2026-03-16/OPUS_*, docs/2026-03-16/desktop-stage0-edr-code1-*`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `main_a.py already contained the import-bootstrap and boot-traceback fixes; this turn revalidated them against installed packaged resources, confirmed bounded closure evidence, and removed the temp mirror from the active queue`
Source Survey Docs:
- `docs/2026-03-16/desktop-stage0-edr-code1-failure-full-survey.md`
- `docs/2026-03-16/desktop-stage0-edr-code1-static-analysis-report.md`
- `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-full-survey.md`
- `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-03-16/desktop-stage0-edr-code1-failure-evidence.txt`
- `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-evidence.txt`
- `docs/2026-03-16/desktop-stage0-edr-code1-failure-synthesis-evidence.txt`
Side-Effect Coverage: covered
Supersedes Temp Mirror:
- `docs/temp/OPUS_desktop-stage0-edr-code1-failure-execution-ssot.md`

## 1. Intent

- Create one governing execution document for the packaged desktop `Stage 0 · 기존 방식` failure on project `edr`.
- Lower false positives by reconciling the earlier Codex pre-bind hypothesis with the stronger OPUS embedded-Python evidence.
- Sequence work so the confirmed current blocker is fixed first, observability is hardened second, and only then is the latent prompt-bridge risk addressed if it still reproduces.

## 2. Baseline Facts

- The packaged desktop app accepted `/run` for `key=0`, `sub_key=1`, then surfaced `실행 실패 (code: 1)`.
- `projects/edr` exists only as the shallow directory created by desktop project creation; no `config/`, `drafts/`, `memory/`, `plans/`, `logs/`, or `project_data.db` exist there.
- `process_runner._resolve_launch_command()` launches the packaged engine as:
  - `resources/python-embed/python.exe -u resources/engine/main_a.py`
- `backend_entry.py` bootstraps `sys.path` for the backend process itself, but that bootstrap is not inherited by the child engine subprocess.
- The packaged embedded Python distribution is constrained by `python312._pth`.
- Synthesis evidence now proves that setting `PYTHONPATH` does not add `resources/engine` to `sys.path` in this environment and does not make `import modules` succeed.
- `main_a.py` imports `modules.core.spinners` at module import time, before `boot()` can reach `_select_genre()`, `_select_project()`, or `_bind_selected_project()`.
- Therefore the current incident root cause is:
  - packaged child engine import bootstrap failure
  - not empty-project bootstrap failure
  - not Stage 0 inner-generation failure
- Secondary fact retained from Codex static analysis:
  - once the import blocker is removed, `Stage 0 · 기존 방식` still has a multi-prompt Mode B corridor that may need hardening.

## 3. Scope

Included:
- packaged desktop `/run` child-engine launch contract
- embedded Python import bootstrap for `main_a.py`
- pre-boot failure observability for packaged runs
- post-unblock verification of Stage 0 existing-mode prompt handling

Excluded:
- narrative pipeline outputs
- direct CLI `python main_a.py` source-tree usage
- previously fixed preload/runtime-contract issues unless they reproduce again after the import blocker is fixed
- provider package gaps (`anthropic`, `openai`, etc.) until the packaged app actually reaches those call sites after the current blocker is removed

## 4. Pass 1. Inventory Summary

- Runtime hotspots:
  - `modules/api/process_runner.py`
  - `main_a.py`
  - `build/backend_entry.py`
  - `modules/api/bridge_server.py`
  - `modules/api/prompt_classifier.py`
  - `modules/core/stage01_helpers.py`
  - `modules/core/services/ui_service.py`
  - `geuldobi-desktop/src/index.html`
- Live packaged runtime surfaces:
  - `%LOCALAPPDATA%\\Geuldobi\\electron-main.log`
  - `C:\\Users\\wjjo\\Documents\\글도비\\logs\\control-plane-provenance.jsonl`
  - `C:\\Users\\wjjo\\Documents\\글도비\\projects\\edr`
  - `C:\\Users\\wjjo\\AppData\\Local\\Programs\\Geuldobi\\resources\\python-embed`
  - `C:\\Users\\wjjo\\AppData\\Local\\Programs\\Geuldobi\\resources\\engine`
- Authoritative synthesis outcome:
  - OPUS direct embedded-Python reproduction plus local `PYTHONPATH` rejection evidence overrule the earlier weaker “pre-bind corridor only” explanation.

## 5. Pass 2. Semantic Classification

- Class A — authoritative current blocker:
  - packaged engine subprocess dies at module import time because `resources/engine` is not on `sys.path`
  - `PYTHONPATH` injection is not a reliable fix in this embedded `. _pth` runtime
- Class B — observability gap:
  - boot-time failures can exit with `code: 1` before project-local or workspace-root traceback persistence becomes durable
- Class C — contingent post-unblock risk:
  - Stage 0 existing-mode requires additional prompt round-trips after boot
  - current renderer only auto-resolves `enter` and single-option enums
- Class D — non-governing or deferred:
  - preload-contract bundling and provider package inventory are not the governing incident blocker for this SSOT

## 6. Side-Effect Map

- file writes / artifacts:
  - current failure writes only the shallow project directory and `/run` provenance
  - after fix, expected writes include `config/`, `drafts/`, `memory/`, `plans/`, `project_data.db`, and session logs
- DB / schema / transaction boundaries:
  - current failure never reaches `ProjectContext` DB creation
  - after fix, `project_data.db` bootstrap becomes the first durable sign of successful bind
- JSONL / log / audit sinks:
  - current durable sinks: `control-plane-provenance.jsonl`, `electron-main.log`
  - missing sink today: deterministic traceback sink for pre-boot engine failure
- console / UI / operator output:
  - today the operator sees only `code: 1`
  - target state is a bounded but informative run-failure surface with prompt/phase context
- rollback / recovery / retry:
  - current retries leave an empty ghost project directory but no runtime artifacts
  - after fix, retry behavior must be checked against partially bootstrapped projects
- cache / global state:
  - prompt queue state and lexical project-index state remain relevant only after boot succeeds
- bootstrap fallback / config-env mutation:
  - backend sets `GEULDOBI_ENGINE_ROOT` and `GEULDOBI_PYTHON_PATH`
  - embedded `. _pth` still blocks env-based path injection from being sufficient

## 7. Realization Architecture

- Governing fix path:
  - bootstrap `main_a.py` so its own directory is inserted into `sys.path` before any `import modules.*`
- Rejected fix path:
  - do not rely on `PYTHONPATH` in `process_runner._build_env()` as the primary fix
  - synthesis evidence shows embedded Python ignores it in the current packaged runtime
- Observability hardening:
  - add a top-level failure persistence wrapper so boot-time import or bootstrap errors leave a deterministic traceback sink
  - keep runner diagnostics visible enough for packaged UI failure triage
- Post-unblock gate:
  - only after the import blocker is fixed should prompt-bridge hardening be evaluated as an active remediation tranche

## 8. Execution Tranches

1. Tranche 1 — CRITICAL: child-engine import bootstrap fix
   - File: `main_a.py`
   - Insert engine-root self-bootstrap immediately after `import os` / `import sys` and before any `import modules.*`
   - Required behavior:
     - derive `_script_dir = os.path.dirname(os.path.abspath(__file__))`
     - prepend `_script_dir` to `sys.path` when absent
   - Rationale:
     - works in packaged embedded Python
     - does not depend on `. _pth` honoring environment variables
     - also protects direct packaged `python.exe -u engine/main_a.py` invocations

2. Tranche 2 — HIGH: boot-time traceback persistence and failure diagnostics
   - File: `main_a.py`
   - Wrap `SovereignApp().boot()` in a top-level `try/except` that writes a deterministic UTF-8 traceback sink before exit
   - Candidate sink:
     - workspace-root `logs/error.log` when project is not yet bound
   - Complement:
     - ensure packaged `run_failed` payload preserves `failure_phase`, `last_prompt_step`, and stderr/stdout tail when available
   - Rationale:
     - prevents future `code: 1` incidents from degenerating into no-traceback failures

3. Tranche 3 — CONDITIONAL: Stage 0 prompt-bridge hardening after unblock
   - Activate only if packaged Stage 0 still fails after Tranche 1
   - Targets:
     - `modules/api/prompt_classifier.py`
     - `modules/api/bridge_server.py`
     - `geuldobi-desktop/src/index.html`
   - Focus:
     - preserve pending prompt state
     - improve visibility of prompt text / prompt id / last prompt step
     - harden known Stage 0 follow-up menus beyond single-option auto-select
   - Rationale:
     - this is supported by static analysis, but is not the authoritative current incident blocker

4. Tranche 4 — DEFERRED: provider package inventory after packaged run reaches LLM providers
   - Do not execute in the same pass unless post-T1 validation proves the packaged app now reaches provider import paths

## 9. Acceptance Criteria

- Tranche 1
  - packaged embedded Python can execute `resources/engine/main_a.py` without `ModuleNotFoundError: No module named 'modules'`
  - packaged `/run` no longer dies before `ProjectContext` bootstrap
  - `projects/edr` (or a fresh canary project) gains `config/`, `drafts/`, `memory/`, `plans/`, and `project_data.db`
- Tranche 2
  - any future boot-time failure writes a deterministic traceback sink
  - packaged UI failure diagnostics expose enough phase context to distinguish import/bootstrap failure from prompt-runtime failure
- Tranche 3
  - packaged `Stage 0 · 기존 방식` reaches and resolves its follow-up prompts without unexpected `code: 1`
  - prompt-related failures, if any remain, identify the exact prompt or pending prompt state

## 10. Verification Plan

- Verification 1
  - run packaged embedded Python smoke:
    - `resources/python-embed/python.exe -u resources/engine/main_a.py`
  - confirm the previous `ModuleNotFoundError` is gone
- Verification 2
  - run packaged desktop `Stage 0 · 기존 방식` on a fresh canary project
  - confirm project bootstrap artifacts are created
- Verification 3
  - if packaged Stage 0 still fails, inspect whether the failure is now in the prompt corridor rather than module import
  - only then execute Tranche 3
- Verification 4
  - re-run `projects/test` or equivalent healthy comparison path to ensure no regression in existing project boot

## 11. Guardrails

- Do not ship an execution patch that relies on `PYTHONPATH` as the only packaged fix; synthesis evidence disproves that path in this embedded runtime.
- Do not treat the empty `edr` directory as the governing root cause; it is a consequence of failing before durable bootstrap.
- Do not mix older preload-contract incidents into this SSOT unless they reproduce again after Tranche 1.
- Do not patch Tranche 3 prompt hardening before verifying that Tranche 1 actually moves the packaged run past module import.

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition:
  - remove the temp mirror only after remediation is implemented, validated, and closed through the execution-closure flow
- roadmap dependency:
  - `docs/2026-03-16/active-temp-queue-execution-roadmap.md`
  - this document supersedes the prior OPUS temp mirror and is now closed as the governing queue artifact for this topic

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit
  - refresh `Resume Commit` and `Resume Drift Summary`
  - confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Notes

- Implemented state at re-audit:
  - `main_a.py` now self-bootstraps the engine directory into `sys.path` before any `import modules.*`
  - `main_a.py` now persists a pre-project traceback sink through `_persist_boot_failure_traceback()` and the top-level `__main__` wrapper
  - `modules/api/process_runner.py` and `modules/api/bridge_server.py` now preserve `failure_phase`, `last_prompt_step`, `stdout_tail`, and `stderr_tail` in runtime diagnostics
- Verification:
  - packaged embedded import smoke on installed resources:
    - `%LOCALAPPDATA%\\Programs\\Geuldobi\\resources\\python-embed\\python.exe -c "import runpy; runpy.run_path(...main_a.py..., run_name='packaged_smoke')"`
    - result: `PACKAGED_IMPORT_OK`
  - targeted regression tests:
    - `python -m pytest -q tests/test_main_a_packaged_bootstrap_contract.py tests/test_process_runner.py tests/test_bridge_server_http_contract.py tests/test_desktop_transport_contract.py tests/test_desktop_packaging_contract.py`
    - result: `52 passed`
  - packaged runner canary with installed engine/python plus a shallow temp workspace project:
    - keyed canary run exited `0`
    - durable bootstrap artifacts were created: `config/`, `drafts/`, `memory/`, `plans/`, `logs/`, `project_data.db`
  - negative canary with no API key:
    - boot failed for provider auth, not import bootstrap
    - workspace-root `logs/error.log` was written and runtime diagnostics preserved stderr/failure metadata
- Closure decision:
  - Tranche 1 is closed
  - Tranche 2 is closed
  - Tranche 3 was not activated because the authoritative blocker no longer reproduces and no fresh prompt-corridor failure was observed in this lane
- Residual risk:
  - full Electron renderer click-through was not rerun in this turn; closure is based on installed packaged engine/python verification, the real runner contract, and targeted regression coverage
  - the conditional Stage 0 multi-prompt corridor remains a latent watch item, but it is not an active blocker for this closed lane
