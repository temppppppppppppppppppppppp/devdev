# Stage4 Gemini Direct Default - Execution SSOT

Date: 2026-03-29
Status: execution-ready
Canonical Path: `docs/2026-03-29/stage4-gemini-direct-default-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-gemini-direct-default-execution-ssot.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `tracked drift in stage4/provider code/tests, narrative docs, temp queue, and canary artifacts; no Gemini-default implementation has landed yet`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; survey re-audit confirms current runtime remains Claude-first via config/models.yaml and still lacks first-class Gemini-direct canary/process launch seams`
Source Survey Docs:
- `docs/2026-03-29/stage4-gemini-direct-default-full-survey-audit-order.md`
- `docs/2026-03-29/stage4-gemini-direct-default-full-survey.md`
Evidence Artifacts:
- `config/models.yaml`
- `modules/core/llm_router.py`
- `modules/core/models_config.py`
- `modules/core/constants.py`
- `modules/core/sovereign_bootstrap_runtime.py`
- `modules/domain/agents/base_agent.py`
- `main_a.py`
- `scripts/run_stage4_canary.py`
- `modules/api/process_runner.py`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe change that makes:

- Geuldobi runtime default to Gemini Developer API direct
- Stage 4 canary default to Gemini Developer API direct

while demoting:

- Claude
- Vertex

to explicit opt-in paths.

This is a default-routing wave.
It is not a provider redesign.

## 2. Baseline Facts

- `config/models.yaml` currently makes Stage 4 core roles Claude-first:
  - `analyst`
  - `chief_writer`
  - `director`
- `config/models.yaml` also enables `anthropic` and `vertex_ai`, overriding safer inline router defaults
- `run_stage4_canary.py` has no first-class provider mode or Gemini-direct execution seam
- `ProcessRunner._build_env()` inherits ambient env wholesale, so non-Gemini credentials can contaminate child runs unless explicitly scrubbed
- router/provider infrastructure already supports Gemini direct without redesign

## 3. Scope

Included:

- `config/models.yaml`
- `scripts/run_stage4_canary.py`
- `modules/api/process_runner.py`
- targeted tests:
  - `tests/test_llm_router.py`
  - `tests/test_process_runner.py`
  - `tests/test_run_stage4_canary.py`

Excluded:

- `llm_router.py` redesign
- provider SDK changes
- `.env` edits
- Stage 4 prompt/gate/escalation logic
- fallback observability schema changes
- desktop UI redesign beyond existing input passthrough contract
- live canary execution in this wave

## 4. Execution Goals

1. Core runtime default roles stop booting Claude by default
2. Gemini Developer API direct becomes the default operational path
3. Stage 4 canary gains a first-class Gemini-direct run mode
4. ProcessRunner child env defaults to Gemini-direct clean unless operator explicitly opts in to broader provider passthrough

## 5. Realization Architecture

### 5.1 Config Default Swap

Update `config/models.yaml` so the effective default no longer points Stage 4 core roles at Claude.

Bounded requirements:

- switch `agents.analyst` to `gemini-2.5-pro`
- switch `agents.chief_writer` to `gemini-2.5-pro`
- switch `agents.director` to `gemini-2.5-pro`
- keep already-Gemini roles unchanged unless needed for consistency
- set `providers.anthropic.enabled` to `false`
- set `providers.vertex_ai.enabled` to `false`

Do not remove provider sections entirely.
They remain available for later explicit opt-in use.

### 5.2 Stage 4 Canary Provider Mode

Add a small explicit provider mode seam to `scripts/run_stage4_canary.py`.

Minimum acceptable shape:

- default mode: `gemini_direct`
- explicit opt-out mode allowed, e.g. `ambient`

Gemini-direct mode must:

- preserve `GOOGLE_API_KEY`
- preserve `GOOGLE_API_KEY_2..9`
- remove `ANTHROPIC_API_KEY`
- remove `CLAUDE_API`
- remove `VERTEX_API_KEY`
- remove `VERTEX_PROJECT_ID`
- remove `VERTEX_LOCATION`
- remove `GOOGLE_APPLICATION_CREDENTIALS`

This mode must be process-local only.
It must not rewrite `.env`.

### 5.3 ProcessRunner Default Child-Env Hygiene

`modules/api/process_runner.py::_build_env()` should stop blindly inheriting non-Gemini provider credentials as the default runtime posture.

Minimum acceptable behavior:

- default behavior becomes Gemini-direct clean
- existing explicit Gemini key injection remains supported
- existing explicit Anthropic/Vertex/OpenAI inputs remain possible only when operator explicitly opts in to a broader provider mode

The implementation may use a small new input contract such as:

- `provider_mode="gemini_direct"` as default
- `provider_mode="ambient"` or equivalent explicit override

This wave must not redesign the full UI.
Keep the contract additive and backward-compatible where practical.

## 6. Tranches

### Tranche 1. Config authority correction

- update `config/models.yaml` core role defaults
- update provider enabled flags

### Tranche 2. Canary Gemini-direct seam

- add provider mode arg / seam in `scripts/run_stage4_canary.py`
- ensure Gemini-direct mode scrubs non-Gemini credentials process-locally

### Tranche 3. ProcessRunner Gemini-direct default hygiene

- add default child-env scrub mode
- keep explicit opt-in passthrough possible

### Tranche 4. Regression coverage

- prove default enabled providers match the new config posture
- prove ProcessRunner default env no longer leaks Claude/Vertex credentials
- prove explicit opt-in still passes those credentials when requested
- prove canary runner exposes and uses Gemini-direct mode without workspace mutation

## 7. Acceptance Criteria

- Stage 4 core roles no longer default to Claude in `config/models.yaml`
- `anthropic` and `vertex_ai` are disabled by default in `config/models.yaml`
- `run_stage4_canary.py` supports a first-class Gemini-direct run mode
- Gemini-direct canary mode scrubs Claude/Vertex env from the child process
- `ProcessRunner._build_env()` defaults to Gemini-direct clean behavior
- explicit opt-in provider passthrough remains possible
- no `.env` edits
- no provider SDK rewrite
- no Stage 4 quality-policy change

## 8. Verification Plan

- targeted pytest:
  - `tests/test_llm_router.py`
  - `tests/test_process_runner.py`
  - `tests/test_run_stage4_canary.py`
- `python -m py_compile` on touched files/tests
- `ruff check` on touched files/tests
- `python scripts/check_utf8_hygiene.py` on touched files/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Fresh Gemini smoke/canary validation should happen after this wave lands.

## 9. Guardrails

- do not redesign `LLMProviderRouter`
- do not remove Claude or Vertex support entirely
- do not touch `.env`
- do not add Stage 4 contract logic
- do not widen into provider observability or schema work
- do not change prompt contracts
- do not mutate canary projects during this execution-doc phase

## 10. Deferred Items

Still deferred after this wave:

- explicit `attempted_model / served_model` schema expansion
- provider fallback observability polish beyond the prior bounded wave
- `model_tier` artifact awareness
- broader multi-provider desktop UX
- role-by-role model optimization outside the default-switch goal

## 11. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - remove `docs/temp/stage4-gemini-direct-default-execution-ssot.md` after realization and closure
- roadmap dependency:
  - refresh the aggregate temp execution roadmap before code realization because the active temp queue already contains multiple execution items

## 12. 3-Pass Audit Record

### Pass 1. Structure and Scope

- execution remains bounded to config default swap, canary seam, and process child-env hygiene
- broader provider redesign stays excluded
- PASS

### Pass 2. Evidence and Consistency

- each tranche maps directly to a survey-confirmed default-routing or contamination seam
- config, runner, and process env findings are mutually consistent
- PASS

### Pass 3. Actionability and Overclaim Control

- execution can land in three production files and three targeted test files
- live canary validation remains explicitly post-implementation
- PASS

Estimated confidence: `97%`
