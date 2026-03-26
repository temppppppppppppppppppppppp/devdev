# Multi-Provider Vertex Runtime Entry Wave 1 Execution SSOT

Date: 2026-03-26
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-26/multi-provider-vertex-runtime-entry-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/multi-provider-vertex-runtime-entry-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `07e9aaf8`
- Baseline Dirty Summary: `dirty: config/models.yaml, modules/core/llm_generate.py, modules/core/llm_provider.py, modules/core/llm_router.py, modules/core/providers/vertex_provider.py, multi-provider survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-26/multi-provider-spine-vertex-entry-compact-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-a-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-b-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-c-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-d-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-operating-note.md`
Evidence Artifacts:
- `config/models.yaml`
- `modules/core/llm_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- `modules/api/process_runner.py`
- `tests/test_llm_router.py`
Side-Effect Coverage: covered

## 1. Intent

- Realize the smallest bounded Wave 1 needed to make today's `Gemini on Vertex` entry operationally correct.
- Carry multi-provider spine identity far enough into runtime observability that `Gemini direct` and `Gemini on Vertex` are distinguishable.
- Avoid spending Wave 1 on Claude/OpenAI abstraction work that is not required for today's Vertex entry.

## 2. Baseline Facts

- `vertex_ai` is already enabled in `config/models.yaml`; "enable Vertex" is no longer the real task.
- `LLMResponse` already has `provider`, `backend`, and `family` fields, but provider adapters do not populate the full identity set yet.
- `BaseAgent` still normalizes usage from Gemini-shaped keys only, but that is acceptable for Gemini+Vertex because both share the same Google SDK shape.
- `MetricsCollector` already accepts neutral token fields, but does not receive provider/backend/family attribution.
- `ProcessRunner._build_env()` still injects only `GOOGLE_API_KEY`, `GOOGLE_API_KEY_{i}`, and `SLACK_WEBHOOK_URL`.

## 3. Scope

Included:
- `modules/api/process_runner.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- bounded provider/runtime observability tests only

Excluded:
- `modules/core/response_schemas.py`
- broad `BaseAgent` config abstraction (`GenerateContentConfig -> provider-neutral dict`)
- Anthropic/OpenAI usage-key normalization rewrite
- capability negotiation system
- full provider-neutral content model
- broad pricing redesign beyond explicit Vertex handling
- desktop/UI rollout work
- DB schema changes

## 4. Pass 1. Inventory Summary

- identity substrate already exists:
  - router-level provider registration
  - router-level backend/family map
  - response envelope fields
- missing runtime handoff points:
  - provider adapters only emit `provider`
  - metrics path does not carry provider identity
  - subprocess env contract does not carry Vertex runtime env vars
- bounded touched execution surface is 7 production files max, plus targeted tests

## 5. Pass 2. Semantic Classification

- Class A: Vertex runtime activation correctness
  - subprocess env injection
  - Vertex credential/runtime handoff
- Class B: provider identity propagation
  - provider adapters populate `backend` and `family`
  - BaseAgent forwards identity into metrics/audit sink
- Class C: bounded observability correctness
  - explicit Vertex pricing path
  - tests proving direct-vs-Vertex attribution does not collapse

## 6. Side-Effect Map

- file writes / artifacts:
  - docs canonical + temp SSOT
  - no runtime artifact path changes intended
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - metrics/runtime audit payloads may gain provider identity fields
- console / UI / operator output:
  - may expose provider/backend distinction indirectly through metrics summaries or logs
- rollback / recovery / retry:
  - not intended to change retry policy
- cache / global state:
  - not applicable beyond existing metrics collector runtime state
- bootstrap fallback / config-env mutation:
  - `ProcessRunner._build_env()` will expand Vertex env passthrough

## 7. Realization Architecture

- Keep the existing multi-provider spine shape:
  - router owns provider resolution
  - provider adapters own provider-native response shaping
  - BaseAgent owns metric payload construction
  - metrics collector remains the neutral sink
- Wave 1 should not move request compilation ownership.
- Wave 1 should treat Vertex as "Gemini runtime backend with distinct operational identity" and wire only what is needed for:
  - subprocess runtime activation
  - provider/backend/family observability
  - explicit billing interpretation

## 8. Execution Tranches

1. Tranche A. Vertex runtime env passthrough
   - extend `ProcessRunner._build_env()` to pass:
     - `VERTEX_API_KEY` when provided
     - `VERTEX_PROJECT_ID`
     - `VERTEX_LOCATION`
     - `GOOGLE_APPLICATION_CREDENTIALS`
   - keep existing Google API key path intact

2. Tranche B. Provider identity propagation
   - update provider adapters to populate `backend` and `family` on `LLMResponse`
   - do not redesign `LLMResponse`; fields already exist

3. Tranche C. Metrics / runtime attribution wiring
   - extend `BaseAgent` metric payload construction to include provider identity
   - extend `MetricsCollector.end_call()` and related sinks in a bounded way so provider/backend/family can be recorded or surfaced
   - keep token accounting behavior unchanged

4. Tranche D. Explicit Vertex pricing normalization
   - make Vertex billing treatment explicit in `metrics_collector.py`
   - if Vertex pricing is intentionally same as Gemini, encode that clearly rather than relying on silent prefix stripping alone

5. Tranche E. Bounded regression tests
   - provider envelope identity tests
   - process_runner env passthrough tests
   - metrics attribution tests
   - preserve existing router/provider tests

## 9. Acceptance Criteria

- Vertex subprocess launches can receive required Vertex env vars through `ProcessRunner`
- `VertexAIProvider` emits `provider=vertex_ai`, `backend=google_vertex`, `family=gemini`
- sibling providers emit coherent backend/family identity as well
- runtime metrics/audit path can distinguish Gemini direct vs Gemini on Vertex
- existing Gemini direct flow does not regress
- no broad Claude/OpenAI abstraction work is introduced in Wave 1

## 10. Verification Plan

- `python -m py_compile modules/api/process_runner.py modules/core/providers/vertex_provider.py modules/core/providers/gemini_provider.py modules/core/providers/anthropic_provider.py modules/core/providers/openai_provider.py modules/domain/agents/base_agent.py modules/core/metrics_collector.py`
- targeted pytest for:
  - router/provider tests
  - new process_runner env passthrough tests
  - new metrics attribution tests
- `python scripts/check_utf8_hygiene.py ...` over touched files plus canonical/temp SSOT
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails

- Do not reopen provider-neutral request-config abstraction in this wave.
- Do not touch `response_schemas.py` in this wave.
- Do not widen `ProcessRunner` into a full all-provider env contract redesign.
- Do not rewrite token normalization for Anthropic/OpenAI yet.
- Do not silently change retry, cache, or thinking behavior.

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition: remove temp mirror after implementation + closure audit passes
- roadmap dependency: none; single active execution item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note

Closure Result: `closed (closure-audited)`

Verification Evidence:
- `python -m py_compile modules/api/process_runner.py modules/core/providers/vertex_provider.py modules/core/providers/gemini_provider.py modules/core/providers/anthropic_provider.py modules/core/providers/openai_provider.py modules/core/metrics_collector.py tests/test_llm_router.py` -> PASS
- `pytest tests/test_llm_router.py -q` -> `19 passed`
- `ruff check modules/api/process_runner.py modules/core/providers/vertex_provider.py modules/core/providers/gemini_provider.py modules/core/providers/anthropic_provider.py modules/core/providers/openai_provider.py modules/core/metrics_collector.py tests/test_llm_router.py` -> PASS
- `python scripts/check_utf8_hygiene.py ...` -> PASS

Acceptance Criteria Outcome:
- Vertex subprocess env passthrough: verified
- provider/backend/family identity emission: verified
- Gemini direct vs Vertex distinction in metrics path: verified via provider identity inference and regression tests
- Gemini direct non-regression: verified
- Claude/OpenAI abstraction expansion excluded: verified by touched-file scope

Residual Risks:
- Anthropic/OpenAI usage normalization is still deferred; this wave only makes Vertex runtime entry and identity observability correct
- Vertex pricing remains explicitly aligned to Gemini-equivalent pricing assumptions; if Google pricing diverges later, a follow-up pricing-only wave may be needed

Temp Queue Cleanup:
- temp mirror may be removed after closure
- queue should return to empty once temp mirror is deleted and queue state is refreshed
