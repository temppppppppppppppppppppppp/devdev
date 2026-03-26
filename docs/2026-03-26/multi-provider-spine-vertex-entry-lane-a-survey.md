# Lane A Survey: Identity / Config / Routing

Date: 2026-03-26
Status: final (3-pass audited, lane-local survey reconstructed during merge audit)
Type: system-track parallel survey lane
Lane Owner: Terminal 1
Canonical Path: `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-a-survey.md`
Source Master Order: `docs/2026-03-26/multi-provider-spine-vertex-entry-parallel-survey-master-order.md`

Evidence Basis:
- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- `tests/test_llm_router.py`

Commit State:
- Baseline Commit: `07e9aaf8`
- Resume Drift Summary: dirty workspace (`config/models.yaml`, `modules/core/llm_provider.py`, `modules/core/llm_router.py`, `modules/core/providers/vertex_provider.py`, survey docs)

## 1. Lane A Core Question

Does the current model identity shape cleanly separate `backend`, `family`, and `capability`, or is it still too flat for Vertex, Claude, and OpenAI?

## 2. Findings

### 2.1 Router Identity Is Already Two-Axis Aware

- `llm_router.py:10-23` defines `DEFAULT_PROVIDER_CONFIGS` for `gemini`, `anthropic`, `openai`, and `vertex_ai`
- `llm_router.py:25-29` defines `BACKEND_FAMILY_MAP`
  - `gemini -> (google_direct, gemini)`
  - `vertex_ai -> (google_vertex, gemini)`
  - `anthropic -> (anthropic_direct, claude)`
  - `openai -> (openai_direct, gpt)`

This means the codebase is no longer purely flat at the router layer. `vertex` is already modeled as a backend distinction under the Gemini family.

### 2.2 Prefix Routing Is Clean and Explicit

- `llm_router.py:104-114` routes `vertexai:` / `vertex:` / `vertex/` to `vertex_ai`
- `llm_router.py:106-113` routes `gemini*`, `claude*`, `gpt*` / `o1/o3/o4*` to their provider families
- `llm_router.py:116-129` enforces enabled-provider checks before dispatch

This is good enough for today's Vertex entry. No new router shape is needed just to admit Vertex.

### 2.3 Vertex Is Already Enabled in Canonical Config

- `config/models.yaml:1-16` already has:
  - `providers.vertex_ai.enabled: true`
  - `project_id_env`
  - `location_env`
  - `credentials_env`

This is important drift from the earlier merged survey text. Vertex activation is no longer blocked on flipping `enabled: false` to `true`; that part is already done in the live workspace.

### 2.4 Provider Registration and Tests Are Ready

- `llm_router.py:50-66` already registers `VertexAIProvider(...)`
- `tests/test_llm_router.py:30-41` checks that enabled non-Gemini providers resolve correctly
- `tests/test_llm_router.py:146-203` includes a dedicated Vertex provider smoke test

The config/routing lane is therefore not the current bottleneck.

### 2.5 Identity Still Flattens Above the Router

The remaining flatness is higher in the stack:

- `config/models.yaml:18-40` agent assignments are still plain model strings
- `models_config.py:11-41` inline defaults are still Gemini-only
- no capability metadata is carried in YAML yet
- router-level `BACKEND_FAMILY_MAP` is not yet propagated through downstream metrics/observability paths

So the identity layer is partially modernized, but the rest of runtime still mostly treats model choice as a string.

## 3. Must-Answer Questions

### Q1. How is `vertex` currently represented?

As `provider_name = vertex_ai`, with router-level identity `backend=google_vertex`, `family=gemini`.

### Q2. Is `vertex` treated as backend or flat provider peer?

At the router identity layer it is treated as a backend distinction under Gemini, not just another flat string peer. The flatness problem survives mostly outside the router.

### Q3. Can today's Vertex entry be done without distorting future identity shape?

Yes. The router/config layer already admits Vertex cleanly. Today's Wave 1 should not spend scope "re-enabling Vertex" or redesigning provider identity from scratch.

## 4. Lane A Verdict

### Already Multi-Provider-Friendly

1. Provider registry exists for all 4 providers
2. `BACKEND_FAMILY_MAP` already separates backend from family
3. Prefix inference is explicit and tested
4. Vertex is already enabled in `models.yaml`

### Still Flat or Gemini-Centric

1. Agent model assignment is still string-only
2. Inline defaults in `models_config.py` are Gemini-only
3. Capability metadata is absent
4. Router identity does not yet flow into metrics/observability as first-class fields

### What Vertex Wave 1 Should Not Waste Scope On

1. Re-enabling `vertex_ai`
2. Full YAML metadata redesign
3. Full capability matrix introduction

## 5. 3-Pass Audit Record

Pass 1. Structure and Scope
- Lane-local survey only
- Bounded to identity/config/routing
- PASS

Pass 2. Evidence and Consistency
- `models.yaml`, `models_config.py`, `llm_router.py`, `test_llm_router.py` rechecked against live workspace
- Earlier stale claim (`vertex_ai.enabled: false`) explicitly corrected
- PASS

Pass 3. Execution and Readability
- Clear distinction between "already solved" and "still flat above router"
- Actionable consequence for merge survey preserved
- PASS

Estimated confidence: 97%
