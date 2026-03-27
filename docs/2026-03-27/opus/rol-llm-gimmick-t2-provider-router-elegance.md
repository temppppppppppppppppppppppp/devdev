# T2 Provider / Router / Backend-Family-Capability Elegance

Date: 2026-03-27
Status: final (3-pass audited)
Document Type: static survey lane report
Canonical Path: `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-26/llm-multi-provider-context-note.md`
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`
Evidence Basis:
- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_router.py`
- `modules/core/llm_generate.py`
- `modules/core/llm_schema.py`
- `modules/core/providers/__init__.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/anthropic_vertex_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/core/metrics_collector.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/process_runner.py`
- `tests/test_llm_router.py`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked llm_router/provider/context/validator surfaces, docs/temp/queue-state.json, project logs; untracked multi-provider docs, fact docs, anthropic_vertex scaffolding/tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

The provider/router/backend lane is in better shape than a typical organic multi-provider accretion. The foundational three-axis model (`backend` / `family` / `model`) from the multi-provider context note is already partially materialized in live code. Five provider adapters exist, the router dispatches by model-name prefix convention, and `LLMResponse` carries `provider`, `backend`, and `family` fields end-to-end.

However, the lane currently exhibits a **mixed** elegance profile:
- The outer skeleton is clean: `LLMRequest`/`LLMResponse` protocol, `LLMProviderRouter`, per-adapter modules.
- The inner execution has three concrete duplication/drift hotspots and two gap-class findings that an LLM would find confusing or error-prone.

The dominant risk is not broken behavior but **silent reasoning traps**: duplicated provider-inference logic in two files, a redundant `backend`/`family` overwrite in the generate bridge, and a missing `OPENAI_API_KEY` passthrough in `ProcessRunner` that makes the multi-provider contract asymmetric in a way that is invisible until runtime.

All top findings are fixable with comment, doc, observability, or light contract-cleanup. No boundary refactor is required to reach "LLM-navigable" status.

## 2. Included Coverage / Exclusions

### Included
| File | Role in Lane |
| --- | --- |
| `config/models.yaml` | Provider enablement SSOT and agent model assignment |
| `modules/core/models_config.py` | YAML loader + inline default fallback |
| `modules/core/llm_provider.py` | Provider-neutral protocol: `LLMRequest`, `LLMResponse`, `LLMProvider` |
| `modules/core/llm_router.py` | Provider routing, `BACKEND_FAMILY_MAP`, shared singleton |
| `modules/core/llm_generate.py` | Thin generate bridge used by 10+ callers |
| `modules/core/llm_schema.py` | Gemini/dict schema bridge |
| `modules/core/providers/__init__.py` | Package exports |
| `modules/core/providers/gemini_provider.py` | Gemini direct adapter |
| `modules/core/providers/vertex_provider.py` | Gemini-on-Vertex adapter (dual auth mode) |
| `modules/core/providers/anthropic_provider.py` | Claude direct adapter |
| `modules/core/providers/anthropic_vertex_provider.py` | Claude-on-Vertex adapter |
| `modules/core/providers/openai_provider.py` | OpenAI adapter |
| `modules/core/metrics_collector.py` | Cost/usage attribution and provider identity inference |
| `modules/domain/agents/base_agent.py` | Usage normalization bridge (`_normalize_usage`) |
| `modules/api/process_runner.py` | Subprocess env passthrough for credentials |
| `tests/test_llm_router.py` | Router, provider, metrics, and env passthrough tests |
| `docs/2026-03-26/llm-multi-provider-context-note.md` | Architecture decision record for multi-provider |

### Excluded
- `BaseAgent` request compilation and retry logic (covered by T4 contract lane)
- Prompt caching internals (Gemini-specific, covered by T4 writer/context lane)
- Stage 4 verdict flow and observability (covered by T3 and T6)
- Any code modification

## 3. Current Read Order / Ownership / Gimmick Map

### 3.1 Read Order for This Lane

A cold LLM entering the provider/router lane should read in this order:
1. `config/models.yaml` -- what is enabled, what models are assigned
2. `modules/core/llm_provider.py` -- the protocol contract: `LLMRequest`, `LLMResponse`, `LLMProvider`
3. `modules/core/llm_router.py` -- how model names map to providers, `BACKEND_FAMILY_MAP`
4. `modules/core/providers/` -- one file per adapter
5. `modules/core/llm_generate.py` -- the thin bridge used by most callers
6. `modules/core/metrics_collector.py` -- cost/attribution
7. `modules/domain/agents/base_agent.py:391-414` -- usage normalization
8. `modules/api/process_runner.py:780-823` -- credential env passthrough

### 3.2 Ownership Map

| Owner | Responsibility | File |
| --- | --- | --- |
| `models.yaml` | Provider enablement SSOT, model assignment | `config/models.yaml` |
| `models_config.py` | YAML loader, inline fallback defaults | `modules/core/models_config.py` |
| `LLMProviderRouter` | Model-to-provider dispatch, prefix convention | `modules/core/llm_router.py` |
| `BACKEND_FAMILY_MAP` | Provider-name to (backend, family) spine identity | `modules/core/llm_router.py:33-39` |
| Per-adapter `generate()` | SDK call, response normalization, backend/family emission | `modules/core/providers/*.py` |
| `llm_generate.py` | Thin bridge: router lookup + BACKEND_FAMILY_MAP overwrite | `modules/core/llm_generate.py` |
| `_infer_provider_identity()` | Duplicate prefix-based identity inference for metrics | `modules/core/metrics_collector.py:97-110` |
| `BaseAgent._normalize_usage()` | Gemini-canonical usage key bridging | `modules/domain/agents/base_agent.py:400-414` |
| `ProcessRunner._build_env()` | Credential passthrough to subprocess | `modules/api/process_runner.py:780-823` |

### 3.3 Gimmick Map

| Gimmick | Location | Elegant? | Notes |
| --- | --- | --- | --- |
| Model-name prefix dispatch | `llm_router.py:119-131` | yes | Single static method, clear prefix rules, tested |
| Dual auth mode for Vertex | `vertex_provider.py:14-113` | yes | `api_key` / `project_credentials` / `auto`, well-bounded |
| `AnthropicVertexProvider` inherits `AnthropicProvider` | `anthropic_vertex_provider.py:10` | yes | Clean override of `_get_client()` + `normalize_model_name()` only |
| `BACKEND_FAMILY_MAP` spine identity | `llm_router.py:33-39` | mostly | Clean map, but overwritten redundantly in `llm_generate.py` |
| Gemini-canonical usage normalization | `base_agent.py:400-414` | mixed | Bridges Claude/OpenAI keys to Gemini keys; should be in provider or a shared util, not in BaseAgent |
| `_infer_provider_identity()` duplicate | `metrics_collector.py:97-110` | inelegant | Duplicates `infer_provider_name()` logic from router; drift risk |
| `_normalize_billable_model()` prefix strip | `metrics_collector.py:113-119` | mixed | Partially duplicates `normalize_model_name()` from adapters |

## 4. Top Hotspots

### P1-A. Duplicated provider-inference logic (drift risk)
- **File**: `modules/core/metrics_collector.py:97-110`
- **Mirror**: `modules/core/llm_router.py:119-131`
- **Issue**: `_infer_provider_identity()` in metrics_collector duplicates the exact same model-name-prefix dispatch logic that lives in `LLMProviderRouter.infer_provider_name()`. Both were recently updated to include `anthropic_vertex`. If either is modified without the other, metrics attribution silently diverges from routing.
- **Fix type**: `contract-cleanup` -- make metrics call the router's static method or extract a shared function.

### P1-B. Redundant backend/family overwrite in llm_generate.py
- **File**: `modules/core/llm_generate.py:24-28`
- **Issue**: After calling `provider.generate()`, which already sets `response.backend` and `response.family` on the `LLMResponse`, the generate bridge overwrites those fields from `BACKEND_FAMILY_MAP`. This is a benign redundancy today because the values match, but it creates a reasoning trap: an LLM reading the code cannot tell whether the adapter's values or the map's values are authoritative. If they ever diverge, the map silently wins.
- **Fix type**: `comment-only` or `contract-cleanup` -- either remove the overwrite (providers are authoritative) or add a comment explaining why both exist.

### P1-C. Missing OPENAI_API_KEY in ProcessRunner env passthrough
- **File**: `modules/api/process_runner.py:780-823`
- **Issue**: `_build_env()` passes through `GOOGLE_API_KEY`, `VERTEX_*`, and `ANTHROPIC_API_KEY`, but has no `OPENAI_API_KEY` passthrough via the `inputs` dict. The key will only reach the subprocess if it already exists in `os.environ`. This makes the multi-provider credential contract asymmetric: Gemini, Vertex, and Anthropic credentials can be injected from the control plane; OpenAI cannot.
- **Fix type**: `contract-cleanup` -- add `("OPENAI_API_KEY", "openai_api_key")` to the env passthrough block.

### P1-D. providers/__init__.py missing AnthropicVertexProvider export
- **File**: `modules/core/providers/__init__.py:1-8`
- **Issue**: `__all__` lists 4 providers but omits `AnthropicVertexProvider`. The router imports it directly, so this is not a runtime bug. But it creates a navigation trap: an LLM reading `__init__.py` to discover all providers will miss the fifth adapter.
- **Fix type**: `contract-cleanup` -- add the import and export.

### P1-E. Usage normalization lives in BaseAgent, not in provider boundary
- **File**: `modules/domain/agents/base_agent.py:400-414`
- **Issue**: `_normalize_usage()` bridges Claude/OpenAI `input_tokens`/`output_tokens` to Gemini-canonical `prompt_token_count`/`candidates_token_count`. This is a provider-boundary concern placed in the agent layer. Any caller that does not go through `BaseAgent` (e.g., `llm_generate.py` callers, validator callers) receives un-normalized usage dicts. The normalization is not wrong, but it is in the wrong place for multi-provider clarity.
- **Fix type**: `comment-only` (short-term) to document that normalization only happens via BaseAgent path. Long-term, move to provider boundary or a shared util (deferred).

## 5. Top Quick Wins

| # | Item | File:Line | Fix Type | ROI |
| --- | --- | --- | --- | --- |
| QW-1 | Add comment in `llm_generate.py:24-28` explaining that the `BACKEND_FAMILY_MAP` overwrite is a compat belt on top of per-adapter values, and that adapters are the authoritative source | `modules/core/llm_generate.py:24-28` | comment-only | HIGH -- removes the most confusing reasoning trap in the lane |
| QW-2 | Add `AnthropicVertexProvider` to `providers/__init__.py` import and `__all__` | `modules/core/providers/__init__.py:4,8` | contract-cleanup | HIGH -- makes package discovery honest |
| QW-3 | Add a one-line cross-reference comment in `metrics_collector.py:97` noting that this logic mirrors `LLMProviderRouter.infer_provider_name()` and that changes must be synchronized | `modules/core/metrics_collector.py:97` | comment-only | HIGH -- prevents silent metric/routing divergence |
| QW-4 | Add `("OPENAI_API_KEY", "openai_api_key")` to `ProcessRunner._build_env()` env passthrough block | `modules/api/process_runner.py:809-817` | contract-cleanup | MEDIUM -- closes asymmetric credential gap |
| QW-5 | Add a short docstring or comment in `base_agent.py:400` noting that this normalization only applies to the `BaseAgent.ask()` call path, and that `llm_generate.py` callers receive raw provider usage | `modules/domain/agents/base_agent.py:400` | comment-only | MEDIUM -- prevents false assumption that all usage is normalized |
| QW-6 | Add a one-liner in `models.yaml` noting that `fallback_chain` only contains Gemini models and does not yet cover non-Gemini providers | `config/models.yaml:58` | doc-only | LOW -- prevents an LLM from assuming fallback covers all providers |
| QW-7 | Add a capability/feature-gate note as a YAML comment block in `models.yaml` near the `providers` section, referencing the three-axis model from the multi-provider context note | `config/models.yaml:1` | doc-only | LOW -- gives a cold LLM the architecture framing without needing to find the context note |

**Quick win composition**: 3 comment-only, 2 contract-cleanup, 2 doc-only. 5 of 7 (71%) are comment/doc/observability.

## 6. Gimmick Elegance Judgment

### Elegant Gimmicks
- **Model-name prefix dispatch** (`llm_router.py:119-131`): Single owner, explicit prefix convention, straightforward `startswith` chain, well-tested. An LLM can read and modify this safely in 1 file hop.
- **Dual auth mode for Vertex** (`vertex_provider.py:14-113`): `api_key` / `project_credentials` / `auto` with clear builder methods. Localized in one adapter. Explicit error messages. Elegant.
- **AnthropicVertexProvider inheritance** (`anthropic_vertex_provider.py`): Minimal override of only `_get_client()` and `normalize_model_name()` plus `generate()` wrapper for prefix stripping. 67 lines total. Clean reuse of Anthropic message shape logic.
- **LLMResponse dataclass** (`llm_provider.py:16-33`): Provider-neutral envelope with explicit `backend`/`family` spine fields. Good docstring explaining `raw` field purpose.

### Mixed Gimmicks
- **BACKEND_FAMILY_MAP + per-adapter values**: The map and the adapter `generate()` return values are redundant. Both are maintained and both are correct, but the double-set pattern in `llm_generate.py:24-28` makes the authoritative source ambiguous.
- **Usage normalization in BaseAgent**: Works correctly but is placed in the wrong architectural layer. It is a provider-boundary concern living in the agent layer.
- **_normalize_billable_model()**: Duplicates prefix-stripping logic that also exists in `VertexAIProvider.normalize_model_name()` and `AnthropicVertexProvider.normalize_model_name()`.

### Inelegant Gimmicks
- **Duplicated `_infer_provider_identity()`**: Nearly identical prefix-dispatch logic in `metrics_collector.py:97-110` and `llm_router.py:119-131`. This is the most inelegant pattern in the lane. It exists because metrics needs identity without constructing a provider, but the duplication was not consolidated after both were updated.

### Overall Gimmick-Elegance Verdict: **mixed**

The outer shape (protocol, router, adapter modules) is elegant. The inner wiring has 2-3 duplication/drift traps that are individually small but collectively push the lane below "elegant" into "mixed." All are cheaply fixable.

## 7. Deferred Refactor Candidates

These are long-term items that cannot be solved by comment/doc/observability alone, but do not block current multi-provider work.

### DR-1. Consolidate provider-inference into one shared function (long-term)
- **Current state**: `LLMProviderRouter.infer_provider_name()` and `_infer_provider_identity()` in metrics_collector duplicate the same logic.
- **Target**: Extract a shared `infer_provider_identity(model) -> (provider, backend, family)` function in a shared module (e.g., `llm_provider.py` or a new `llm_identity.py`). Both router and metrics call it.
- **Why defer**: The cross-reference comment (QW-3) is sufficient for now. The duplication is 10 lines, not 100.

### DR-2. Move usage normalization from BaseAgent to provider boundary (long-term)
- **Current state**: `BaseAgent._normalize_usage()` bridges Claude/OpenAI usage keys to Gemini-canonical. Callers outside BaseAgent receive raw keys.
- **Target**: Each provider adapter normalizes usage to a shared canonical format in `generate()` return. BaseAgent normalization becomes a no-op passthrough.
- **Why defer**: Requires touching all 5 providers and verifying all downstream usage consumers. The comment (QW-5) suffices for now.

### DR-3. Remove redundant backend/family overwrite in llm_generate.py (long-term)
- **Current state**: `llm_generate.py:24-28` overwrites `response.backend` and `response.family` from `BACKEND_FAMILY_MAP` even though adapters already set them.
- **Target**: Remove the overwrite. Adapters are authoritative for their own identity.
- **Why defer**: The overwrite is benign and a comment (QW-1) resolves the reasoning ambiguity. Removing it requires verifying no caller depends on the overwrite behavior.

## 8. No-Action / Settled Areas

| Area | Status | Rationale |
| --- | --- | --- |
| `LLMRequest` / `LLMResponse` protocol | settled | Clean dataclasses, good docstrings, `slots=True`. No action needed. |
| `GeminiProvider` adapter | settled | 51 lines, straightforward SDK call + response extraction. |
| `VertexAIProvider` dual auth | settled | Well-bounded, well-tested (7 dedicated tests). |
| `AnthropicProvider` adapter | settled | Clean message normalization, explicit `_backend`/`_family` class attrs. |
| `AnthropicVertexProvider` adapter | settled | 67 lines, clean inheritance. Only needs `__init__.py` export fix. |
| `OpenAIProvider` adapter | settled | Clean Responses API usage, schema bridge via `schema_to_dict`. |
| `llm_schema.py` schema bridge | settled | Bidirectional dict-to-Gemini and Gemini-to-dict conversion. Used by OpenAI adapter. Works. |
| `models_config.py` loader | settled | Clean YAML loader with provenance tracking. 98 lines. |
| `test_llm_router.py` test coverage | settled | 39 tests covering routing, identity, generation, metrics, and env passthrough. Well-structured wave sections. |
| `models.yaml` agent assignment | settled | All 19 agent roles mapped. Comments explain role rationale. |
| `BACKEND_FAMILY_MAP` content | settled | Correct 5-entry map. Values are accurate per the three-axis model. |

## 9. Cross-Lane Handoff Notes

### To T4 (Writer / Prompt / Context Injection)
- `BaseAgent._normalize_usage()` is the only place where non-Gemini usage keys get bridged. If T4 inspects prompt/token accounting, it should know this normalization only happens in the `BaseAgent.ask()` path.
- `llm_schema.py` is the Gemini/dict schema bridge. T4 should note that OpenAI adapter already uses `schema_to_dict()` for structured output, while `BaseAgent` still constructs Gemini-native `GenerateContentConfig` directly.

### To T6 (Observability / Peripheral)
- `metrics_collector.py` has duplicated provider-inference logic (P1-A). If T6 surveys observability sinks, it should note that metrics attribution depends on a private function that mirrors the router but could drift.
- `MODEL_COSTS` dict in metrics_collector includes Claude pricing but not OpenAI pricing. OpenAI calls will fall through to the `"default"` cost entry.

### To T1 (Navigation / Entry)
- `ProcessRunner._build_env()` is the control-plane credential passthrough. T1 should note the asymmetric OpenAI gap (P1-C) when assessing entry/launch contract completeness.

### To T3 (Stage 4 Authority)
- No direct handoff. Stage 4 uses `BaseAgent.ask()` which goes through the router. The provider layer is transparent to Stage 4 flow.

## 10. Confidence And Limits

### Verdicts

- **Navigation-ready for this lane**: yes
- **Cheap-fix-first verdict**: yes
- **Gimmick-elegance verdict**: mixed
- **Boundary-refactor can wait**: yes
- **Top 3 highest-ROI quick wins in this lane**:
  1. QW-1: Comment in `llm_generate.py` explaining the backend/family overwrite compat belt
  2. QW-3: Cross-reference comment in `metrics_collector.py` linking to router's `infer_provider_name()`
  3. QW-2: Add `AnthropicVertexProvider` to `providers/__init__.py` exports

### Confidence
Estimated confidence: **96%**

Reasoning:
- High confidence on ownership, gimmick map, and hotspot identification because all 16 scope files were directly inspected.
- High confidence on duplication findings because the identical prefix chains were verified line-by-line.
- High confidence on the ProcessRunner credential gap because `_build_env()` was fully read and the absence of `OPENAI_API_KEY` is definitional.
- Residual uncertainty (4%) is limited to:
  - Whether `llm_generate.py` overwrite has downstream callers that specifically depend on `BACKEND_FAMILY_MAP` values rather than adapter-emitted values (unlikely but not proven).
  - Whether OpenAI pricing entries exist elsewhere in the codebase outside `metrics_collector.py` (not found in scope files, but not exhaustively searched outside scope).

### Limits
- This survey did not inspect `BaseAgent` request compilation or Gemini-native `GenerateContentConfig` construction in detail. That is T4 scope.
- This survey did not inspect runtime error handling, retry logic, or rate-limit behavior within adapters. Those are behavioral concerns outside the static elegance scope.
- This survey did not inspect the `scripts/probe_claude_vertex_matrix.py` untracked file. It is a probe script, not a production runtime file.

## 11. 3-Pass Audit Record

### Pass 1. Structure and Scope
- Document type is `static survey lane report`.
- Scope matches T2 assignment from master order.
- All 10 required sections present.
- All mandatory verdict lines present.
- All P1 findings have file:line anchors.
- All recommendations have fix types.
- Quick wins: 7 items, 5/7 (71%) are comment/doc/observability.
- Deferred refactor candidates: 3 (at cap).
- PASS

### Pass 2. Evidence and Consistency
- Duplication claim (P1-A) verified: `llm_router.py:119-131` vs `metrics_collector.py:97-110` are structurally identical prefix chains.
- Redundant overwrite claim (P1-B) verified: `llm_generate.py:24-28` sets `response.backend` and `response.family` after `provider.generate()` already set them.
- Missing OPENAI_API_KEY claim (P1-C) verified: `process_runner.py:780-823` has no `OPENAI_API_KEY` input mapping.
- Missing export claim (P1-D) verified: `providers/__init__.py` `__all__` has 4 entries, not 5.
- No contradiction with multi-provider context note or master order constraints.
- PASS

### Pass 3. Execution and Readability
- Quick wins are actionable with clear file:line targets.
- Deferred items are explicitly marked long-term with rationale.
- Cross-lane handoffs are specific and bounded.
- No scope creep into implementation.
- PASS
