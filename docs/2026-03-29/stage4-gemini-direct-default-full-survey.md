# Stage4 Gemini Direct Default - Full Survey

Date: 2026-03-29
Status: final
Track: system
Topic Slug: stage4-gemini-direct-default
Canonical Path: `docs/2026-03-29/stage4-gemini-direct-default-full-survey.md`
Source Order: `docs/2026-03-29/stage4-gemini-direct-default-full-survey-audit-order.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `tracked drift in stage4/provider code/tests, narrative docs, temp queue, and canary artifacts; no new Gemini-default implementation started before this survey`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; live workspace still Claude-first in config/models.yaml for Stage4 core roles and still lacks a first-class Gemini-direct canary/process seam`
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

---

## 1. Scope and Intent

This survey answers one bounded question:

> What is the smallest safe way to make Geuldobi runtime and Stage 4 canary default to Gemini Developer API direct while demoting Claude and Vertex to explicit opt-in paths?

This is not a provider redesign.
This is a default-selection and operator-discipline survey.

The target operating posture is:

- normal Geuldobi runtime defaults to Gemini direct
- Stage 4 canary defaults to Gemini direct
- Claude is no longer a default path
- Vertex is no longer a default path
- clean Gemini canaries do not require `models.yaml` backup/restore hacks

---

## 2. Baseline Evidence

### 2.1 Router defaults are already Gemini-first in code

`modules/core/llm_router.py` ships with:

- `gemini.enabled = True`
- `anthropic.enabled = False`
- `vertex_ai.enabled = False`

So the inline router defaults are already conservative and Gemini direct-friendly.

### 2.2 Repo-authoritative config overrides those safe defaults

`config/models.yaml` currently overrides the runtime into a mixed multi-provider posture:

- `providers.anthropic.enabled: true`
- `providers.vertex_ai.enabled: true`
- `agents.analyst: "claude-sonnet-4-6"`
- `agents.chief_writer: "claude-sonnet-4-6"`
- `agents.director: "claude-opus-4-6"`

That means the router default is not the effective default.
The effective default is `config/models.yaml`.

### 2.3 Main app bootstrap consumes `models.yaml` directly

`main_a.py::_get_agent_model_map()` loads `config/models.yaml` and returns its `agents` block.

`modules/core/sovereign_bootstrap_runtime.py::_build_core_llm_agents()` then wires:

- `analyst`
- `writer`
- `director`
- `manager`
- `weaver`

from that model map.

So Stage 4 core runtime does not merely "allow" Claude.
It explicitly boots Claude-first core roles because `models.yaml` tells it to.

### 2.4 Some non-core runtime surfaces are already Gemini

`modules/core/models_config.py` and `modules/core/constants.py` still default many constants and role constants to Gemini models:

- `DEFAULT_PRO_MODEL = "gemini-3.1-pro-preview"`
- `DEFAULT_PRO_FALLBACK_MODEL = "gemini-2.5-pro"`
- `DEFAULT_FLASH_MODEL = "gemini-2.5-flash"`

and `AIModels` role constants resolve to Gemini values by default.

So the repo is not globally Claude-first.
It is split:

- Stage 4 core roles are Claude-first through `config/models.yaml`
- many helper and constant surfaces are already Gemini-first

### 2.5 BaseAgent fallback chain is config-driven

`modules/domain/agents/base_agent.py` loads fallback chain from `config/models.yaml` when available.

That means:

- if primary roles are changed to Gemini in config
- BaseAgent fallback behavior will follow that config

without a router redesign.

### 2.6 Stage 4 canary runner has no provider/mode seam

`scripts/run_stage4_canary.py` only exposes:

- `prepare`
- `run`
- `analyze`
- `branch-inventory`
- `full`

It does not expose:

- `--provider-mode`
- `--model-profile`
- `--gemini-direct`

It just boots the live app with whatever current workspace config and ambient env happen to be present.

### 2.7 Desktop/process launches inherit ambient provider credentials

`modules/api/process_runner.py::_build_env()` starts from `os.environ.copy()`.

It then adds:

- `GOOGLE_API_KEY`
- `VERTEX_*`
- `ANTHROPIC_API_KEY`
- `CLAUDE_API`
- `OPENAI_API_KEY`

when present in `inputs`.

Crucially, it does not scrub ambient provider credentials by default.

So even if operator intent is "Gemini only", subprocess launches can still inherit:

- `ANTHROPIC_API_KEY`
- `CLAUDE_API`
- `VERTEX_API_KEY`
- `VERTEX_PROJECT_ID`
- `VERTEX_LOCATION`
- `GOOGLE_APPLICATION_CREDENTIALS`

from the parent environment.

This is an operator contamination risk.

---

## 3. Current Default Routing Map

### 3.1 Effective runtime truth

Current effective default selection is:

1. `config/models.yaml` agent role values
2. `main_a.py::_get_agent_model_map()`
3. `sovereign_bootstrap_runtime` explicit `model_tier=` wiring
4. `BaseAgent.primary_model`
5. `LLMProviderRouter.get_provider_for_model(model)`

For Stage 4 core roles today, that resolves to:

- `analyst -> claude-sonnet-4-6 -> anthropic`
- `chief_writer -> claude-sonnet-4-6 -> anthropic`
- `director -> claude-opus-4-6 -> anthropic`

### 3.2 Effective canary truth

Current canary truth is:

1. `scripts/run_stage4_canary.py` boots the real app
2. app loads current workspace config
3. provider credentials come from current process env
4. no first-class canary profile exists

Therefore a "Gemini canary" today is only reliable if the operator manually:

- mutates `config/models.yaml`, or
- carefully scrubs env, or
- both

### 3.3 Effective desktop/process truth

Current desktop/process truth is:

1. subprocess env starts from full ambient parent env
2. explicit inputs may add Gemini/Vertex/Claude credentials
3. no default Gemini-direct scrub mode exists

So default process hygiene is weaker than desired.

---

## 4. Findings

### F-1. The real default problem is config authority, not router capability

`llm_router.py` is not the main blocker.

The main blocker is that `config/models.yaml` overrides the safer inline router defaults and makes Stage 4 core roles Claude-first.

Severity: High
Confidence: High

### F-2. Config-only swap is necessary but not sufficient

Changing only `config/models.yaml` would fix the core role default path.

But it would not solve:

- canary ergonomics
- first-class Gemini-direct operator intent
- ambient provider contamination in subprocess launches

Severity: High
Confidence: High

### F-3. Stage 4 canary lacks a first-class clean-run seam

`run_stage4_canary.py` currently has no direct way to say:

- use Gemini Developer API direct only
- scrub Claude/Vertex env
- preserve current config file contents

This is why recent clean Gemini canaries required temporary workspace mutation or manual shell discipline.

Severity: High
Confidence: High

### F-4. ProcessRunner ambient env inheritance is the main operator contamination seam

`ProcessRunner._build_env()` inherits parent env wholesale.

That means a "default Gemini" desktop run can still carry non-Gemini credentials unless the child env is explicitly scrubbed.

Severity: High
Confidence: High

### F-5. A large provider-policy overhaul is unnecessary

Because:

- Gemini direct path already exists
- router already understands provider prefixes
- defaults can be shifted by config and env discipline

this does not require a router rewrite or provider abstraction redesign.

Severity: Medium
Confidence: High

---

## 5. Option Review

### Option A. Config-only default swap

Change only:

- `config/models.yaml` core Stage 4 role defaults
- `config/models.yaml` provider enablement defaults

Pros:

- smallest config diff
- immediately flips Stage 4 core default away from Claude

Cons:

- does not give canary a first-class Gemini-direct mode
- does not solve ambient env contamination in desktop/process launches
- still leaves clean-run discipline partly manual

Verdict:

- necessary
- insufficient alone

### Option B. Config + canary/process Gemini-direct seam

Do Option A, plus:

- add explicit Gemini-direct mode to `run_stage4_canary.py`
- add default Gemini-direct child-env scrubbing in `ProcessRunner`
- keep Claude/Vertex as explicit opt-in paths instead of ambient defaults

Pros:

- fixes actual default runtime
- fixes canary ergonomics
- fixes operator contamination risk
- keeps provider redesign out of scope

Cons:

- slightly broader than config-only
- requires targeted tests across runner/process surfaces

Verdict:

- best ROI
- recommended

### Option C. Larger provider-policy overhaul

Would involve router/provider redesign, schema expansion, or broader runtime policy work.

Pros:

- theoretically more comprehensive

Cons:

- overkill for the current problem
- mixes default routing with observability and provider architecture

Verdict:

- reject for this wave

---

## 6. Recommended First Move

Recommend Option B:

1. Make `config/models.yaml` Gemini-direct by default
   - switch Stage 4 core Claude roles to Gemini
   - default-disable `anthropic`
   - default-disable `vertex_ai`

2. Add a first-class Gemini-direct seam to `run_stage4_canary.py`
   - a per-run provider mode, not ad hoc `models.yaml` mutation

3. Make `ProcessRunner` default child env Gemini-direct clean
   - preserve `GOOGLE_API_KEY`
   - scrub Claude/Vertex creds unless the operator explicitly opts in

This is the smallest change that actually matches the user's operating goal:

> Geuldobi and canary should both default to Gemini Developer API direct.

---

## 7. Proposed Implementation Boundary

Likely execution surface:

- `config/models.yaml`
- `scripts/run_stage4_canary.py`
- `modules/api/process_runner.py`
- targeted tests only

Likely test surface:

- `tests/test_llm_router.py`
- `tests/test_process_runner.py`
- `tests/test_run_stage4_canary.py`

Likely excluded even in execution:

- `llm_router.py` structural rewrite
- provider SDK changes
- `.env` edits
- Stage 4 prompt/gate logic
- canary summary schema redesign

---

## 8. Deferred Items

Explicitly defer:

- provider observability schema expansion
- `attempted_model / served_model` new sink fields
- `model_tier` fallback awareness
- general multi-provider UX redesign
- removing Claude/Vertex support entirely

These are lower ROI than establishing a clean Gemini-direct default.

---

## 9. Operating Conclusion

The repo does not need a provider overhaul.

It needs a default-authority correction:

- `config/models.yaml` currently makes Stage 4 core runtime Claude-first
- `run_stage4_canary.py` lacks a first-class Gemini-direct seam
- `ProcessRunner` inherits ambient non-Gemini credentials by default

The smallest safe correction is:

- config default swap
- canary provider-mode seam
- process child-env Gemini-direct default scrub

That is enough to make Gemini Developer API direct the real default for both Geuldobi and Stage 4 canary without widening into a larger provider-policy rewrite.

---

## 10. 3-Pass Audit Record

### Pass 1. Scope and Evidence

- survey stayed bounded to default model/provider routing and operator contamination seams
- evidence remained inside config, router, bootstrap, runner, and process env surfaces
- PASS

### Pass 2. Consistency and Overclaim Control

- router defaults, config overrides, bootstrap wiring, canary boot path, and process env inheritance all align
- no prompt/runtime quality claims were mixed into this provider-default survey
- PASS

### Pass 3. Actionability

- the recommended move maps cleanly to one config file, two runtime surfaces, and targeted tests
- broader provider-policy redesign remains explicitly deferred
- PASS

Estimated confidence: `97%`
