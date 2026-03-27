# Multi-Provider Claude on Vertex Entry Wave 1 Execution SSOT

Date: 2026-03-26
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-26/multi-provider-claude-on-vertex-entry-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/multi-provider-claude-on-vertex-entry-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `eb7a41d8`
- Baseline Dirty Summary: `dirty: docs/2026-03-26/multi-provider-claude-on-vertex-entry-compact-survey.md`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-26/multi-provider-claude-on-vertex-entry-compact-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-a-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-b-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-c-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-d-survey.md`
- `docs/2026-03-26/llm-multi-provider-context-note.md`
Evidence Artifacts:
- `config/models.yaml`
- `modules/core/llm_router.py`
- `modules/core/llm_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- `modules/api/process_runner.py`
- `tests/test_llm_router.py`
Side-Effect Coverage: covered

## 1. Intent

- Admit `Claude on Vertex` without breaking the validated multi-provider spine.
- Keep Wave 1 bounded to:
  - `anthropic_vertex` identity admission
  - `AnthropicVertexProvider`
  - minimal non-Gemini runtime guard
  - minimal Claude observability correctness
- Avoid inflating this wave into full Claude-family capability parity.

## 2. Baseline Facts

- `LLMResponse` already has `provider`, `backend`, and `family`.
- `AnthropicProvider` already has the right Claude-family request/response shape, but only for direct API auth.
- `llm_router.py` has no `anthropic_vertex` slot, prefix, or provider registration.
- `BaseAgent` still assumes Gemini raw-response shape for thinking extraction.
- `BaseAgent` and `metrics_collector.py` still treat usage/cost as Gemini-shaped unless corrected.
- `ProcessRunner` now injects Vertex env vars, but still does not inject `ANTHROPIC_API_KEY`.

## 3. Scope

Included:
- `config/models.yaml`
- `modules/core/llm_router.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/anthropic_vertex_provider.py` if introduced
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- `modules/api/process_runner.py`
- bounded router/provider/runtime tests only

Excluded:
- `modules/core/response_schemas.py`
- broad provider-neutral request-config rewrite
- schema SSOT migration away from Gemini `types.Schema`
- full Claude structured-output rollout across all call sites
- full Claude thinking support
- prompt cache redesign
- broad OpenAI cleanup
- desktop/UI/DB work

## 4. Pass 1. Inventory Summary

- identity/config delta is small:
  - one provider registration lane
  - one prefix convention
  - one config section
- adapter delta is also small:
  - direct Anthropic and Vertex Anthropic share most request/response logic
  - main divergence is client construction + backend identity
- runtime correctness delta is narrow but important:
  - non-Gemini raw-response guard
  - Claude usage/pricing/metrics trustworthiness

## 5. Pass 2. Semantic Classification

- Class A: identity / routing admission
  - `anthropic_vertex` provider registration
  - routing prefix convention
  - config section
- Class B: adapter realization
  - `AnthropicVertexProvider`
  - minimal `AnthropicProvider` refactor so backend identity is not hardcoded
- Class C: minimal runtime/observability guard
  - non-Gemini raw-response safety
  - Claude usage/pricing/provider attribution

## 6. Side-Effect Map

- file writes / artifacts:
  - docs canonical + temp SSOT
  - no new narrative artifact path changes intended
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - metrics/runtime audit payloads may gain `anthropic_vertex` identity and Claude-correct cost behavior
- console / UI / operator output:
  - provider/backend distinction may become visible in metrics summaries or runtime logs
- rollback / recovery / retry:
  - retry policy should not change
- cache / global state:
  - no prompt cache redesign in this wave
- bootstrap fallback / config-env mutation:
  - `ProcessRunner._build_env()` may widen to include Anthropic direct credential passthrough

## 7. Realization Architecture

- Route `Claude on Vertex` as a distinct provider identity:
  - `provider=anthropic_vertex`
  - `backend=anthropic_vertex`
  - `family=claude`
- Do not force Claude through `VertexAIProvider`.
- Prefer one of:
  - `AnthropicVertexProvider` subclassing `AnthropicProvider`
  - or a thin parallel adapter reusing the same request/response contract
- Keep `BaseAgent` mostly untouched, except:
  - prevent non-Gemini responses from being parsed by Gemini-only thinking extraction
  - let Claude usage/cost/provider identity survive into metrics

## 8. Execution Tranches

1. Tranche A. Identity / routing admission
   - add `anthropic_vertex` provider registration in `llm_router.py`
   - add one explicit routing prefix convention
     - preferred survey outcome: `anthropic-vertex:claude-*`
   - add `anthropic_vertex` config section in `config/models.yaml`

2. Tranche B. Adapter boundary
   - refactor `AnthropicProvider` so backend identity is not hardcoded
   - add `AnthropicVertexProvider`
   - use `AnthropicVertex(project_id=..., region=...)` path

3. Tranche C. Minimal runtime guard
   - guard Gemini-only `response.raw` thinking extraction in `BaseAgent` for non-Gemini providers/families

4. Tranche D. Minimal Claude observability correctness
   - Claude usage key support in `BaseAgent` metric payload path
   - Claude pricing entries in `metrics_collector.py`
   - provider/backend/family propagation for Claude direct vs Claude on Vertex
   - bounded env passthrough adjustment in `ProcessRunner` only if required by the chosen runtime path

5. Tranche E. Bounded regression tests
   - router/provider resolution tests
   - Anthropic direct non-regression
   - Anthropic Vertex identity tests
   - BaseAgent non-Gemini raw guard tests
   - Claude usage/pricing attribution tests

## 9. Acceptance Criteria

- router/config can express `Claude on Vertex` without ambiguity
- `AnthropicVertexProvider` exists and emits coherent `provider/backend/family`
- `AnthropicProvider` direct path does not regress
- non-Gemini responses are no longer exposed to Gemini raw-shape thinking parsing
- Claude usage/cost path is no longer silently treated as Gemini-default
- wave stays bounded and does not reopen schema/config/caching redesign

## 10. Verification Plan

- `python -m py_compile modules/core/llm_router.py modules/core/providers/anthropic_provider.py modules/core/providers/anthropic_vertex_provider.py modules/domain/agents/base_agent.py modules/core/metrics_collector.py modules/api/process_runner.py`
- targeted pytest:
  - `tests/test_llm_router.py`
  - one tiny Anthropic Vertex/provider test file only if needed
- `python scripts/check_utf8_hygiene.py ...` over touched files plus canonical/temp SSOT
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails

- Do not touch `response_schemas.py` in this wave.
- Do not convert `BaseAgent` to provider-neutral config compilation in this wave.
- Do not implement full Claude structured-output support beyond what is strictly needed for safe entry.
- Do not implement prompt cache redesign in this wave.
- Do not broaden into OpenAI or general all-provider cleanup.

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition: remove temp mirror after implementation + closure audit passes
- roadmap dependency: none; single active execution item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Audit Note

- Closure Result: pass
- Closure Date: `2026-03-26`
- Canonical/temp coherence:
  - `docs/2026-03-26/multi-provider-claude-on-vertex-entry-wave1-execution-ssot.md`
  - `docs/temp/multi-provider-claude-on-vertex-entry-wave1-execution-ssot.md`
  - verified identical before temp cleanup
- Re-verified tranche realization:
  - Tranche A: `anthropic_vertex` config + routing admission present
  - Tranche B: `AnthropicVertexProvider` added, direct `AnthropicProvider` backend/family no longer hardcoded
  - Tranche C: non-Gemini raw-response guards present in `BaseAgent`
  - Tranche D: Claude usage normalization, pricing, provider/backend attribution, and `ANTHROPIC_API_KEY` passthrough present
  - Tranche E: bounded router/provider/runtime regression tests present in `tests/test_llm_router.py`
- Closure verification:
  - `python -m py_compile modules/core/llm_router.py modules/core/providers/anthropic_provider.py modules/core/providers/anthropic_vertex_provider.py modules/domain/agents/base_agent.py modules/core/metrics_collector.py modules/api/process_runner.py` -> pass
  - `pytest tests/test_llm_router.py -q` -> `36 passed`
  - `ruff check modules/core/llm_router.py modules/core/providers/anthropic_provider.py modules/core/providers/anthropic_vertex_provider.py modules/core/metrics_collector.py modules/api/process_runner.py tests/test_llm_router.py` -> pass
  - `python scripts/check_utf8_hygiene.py config/models.yaml modules/core/llm_router.py modules/core/providers/anthropic_provider.py modules/core/providers/anthropic_vertex_provider.py modules/domain/agents/base_agent.py modules/core/metrics_collector.py modules/api/process_runner.py tests/test_llm_router.py docs/2026-03-26/multi-provider-claude-on-vertex-entry-wave1-execution-ssot.md docs/temp/multi-provider-claude-on-vertex-entry-wave1-execution-ssot.md` -> pass
- Audit note:
  - the broader implementation report's `ruff clean` claim was not reproduced verbatim when `config/models.yaml` was passed to `ruff check`, because YAML is not a Ruff input
  - a pre-existing `I001` import-order warning remains at the top of `modules/domain/agents/base_agent.py`; it is outside the Wave 1 delta and did not block closure
  - previously reported unrelated `test_v75*` failures remain outside this wave scope and were not treated as closure blockers
- Residual risks:
  - full Claude structured-output parity remains deferred
  - full Claude thinking support remains deferred
  - prompt cache redesign remains deferred
  - broader provider-neutral request compilation remains deferred
