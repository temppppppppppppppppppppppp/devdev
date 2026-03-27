# Multi-Provider Vertex Auth-Mode Split Wave 1 Execution SSOT

Date: 2026-03-26
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-26/multi-provider-vertex-auth-mode-split-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/multi-provider-vertex-auth-mode-split-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: multi-provider runtime/provider files, local live-smoke logs, Claude-on-Vertex probe script`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-26/multi-provider-spine-vertex-entry-compact-survey.md`
- `docs/2026-03-26/multi-provider-vertex-runtime-entry-wave1-execution-ssot.md`
- `docs/2026-03-26/multi-provider-vertex-live-operator-check-report.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-entry-wave1-canary-report.md`
Evidence Artifacts:
- `docs/2026-03-26/multi-provider-vertex-auth-mode-split-wave1-evidence.json`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_vertex_provider.py`
- `modules/core/llm_router.py`
- `config/models.yaml`
- `tests/test_llm_router.py`
Side-Effect Coverage: covered

## 1. Intent

- Realize the smallest bounded fix that lets `Gemini on Vertex` and `Claude on Vertex` coexist in the same environment without auth-mode collision.
- Remove the current `VertexAIProvider` mutual-exclusion failure where Express-mode Gemini inherits unrelated `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` values intended for Claude-on-Vertex project-credential mode.
- Keep Wave 1 focused on provider/env contract correctness, not a broad multi-provider auth redesign.

## 2. Baseline Facts

- `VertexAIProvider` currently treats `VERTEX_API_KEY` as the highest-priority path, but still passes `project` and `location` into `genai.Client(...)` when those env vars are present.
- In the current Google client, `api_key` and `project/location` are mutually exclusive initializer modes.
- Live runtime proof shows:
  - `vertexai:gemini-3.1-pro-preview` fails under shared env with `ValueError: Project/location and API key are mutually exclusive in the client initializer.`
  - the same model passes when `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` are removed and only `VERTEX_API_KEY` is used.
- `AnthropicVertexProvider` already uses the opposite contract:
  - `VERTEX_PROJECT_ID`
  - `VERTEX_LOCATION`
  - ADC or `GOOGLE_APPLICATION_CREDENTIALS`
  - and does not use `VERTEX_API_KEY`
- Therefore the bug is not "Vertex impossible"; it is a provider-local auth contract collision in our runtime.

## 3. Scope

Included:
- `modules/core/providers/vertex_provider.py`
- `modules/core/llm_router.py`
- `config/models.yaml`
- `tests/test_llm_router.py`
- one tiny provider-focused test file only if `tests/test_llm_router.py` becomes too crowded

Excluded:
- `modules/core/providers/anthropic_vertex_provider.py` behavioral redesign
- `modules/api/process_runner.py`
- `modules/core/metrics_collector.py`
- `modules/domain/agents/base_agent.py`
- broad provider-neutral auth abstraction
- desktop/UI changes
- Claude partner-model access workflow
- quota/request-access automation

## 4. Pass 1. Inventory Summary

- Current auth-mode split is conceptually already present:
  - `vertex_ai` wants Express/API-key mode
  - `anthropic_vertex` wants project-credentials mode
- The implementation gap is narrow:
  - `VertexAIProvider` still leaks project/location into the API-key branch
- The bounded touched production surface can stay at 3 files or fewer unless test organization justifies one extra test file.

## 5. Pass 2. Semantic Classification

- Class A: provider-local auth-mode correction
  - ensure `vertex_ai` API-key mode does not consume unrelated project/location env
- Class B: explicit contract declaration
  - make the intended mode split visible in config/router defaults rather than implicit operator folklore
- Class C: regression protection
  - prove shared env works for Gemini Vertex Express mode
  - prove project-credentials mode still exists as fallback when no API key is present

## 6. Side-Effect Map

- file writes / artifacts:
  - canonical + temp SSOT
  - no runtime artifact naming changes intended
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - not applicable in Wave 1
- console / UI / operator output:
  - may surface a clearer auth-mode contract in config comments or error messages
- rollback / recovery / retry:
  - not intended to change
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - `VertexAIProvider._get_client()` auth branch selection is the main mutation surface

## 7. Realization Architecture

- Keep provider ownership local:
  - `vertex_ai` owns its own auth-mode decision
  - `anthropic_vertex` remains independent and project-credential-based
- Prefer an explicit bounded contract over hidden env collision behavior.
- Recommended Wave 1 contract:
  - `vertex_ai.auth_mode = api_key | project_credentials | auto`
  - default for `vertex_ai`: `api_key`
  - default for `anthropic_vertex`: unchanged; still project/location + ADC
- `auto` may remain as a bounded compatibility fallback, but it must never construct a client with both `api_key` and `project/location`.

## 8. Execution Tranches

1. Tranche A. Vertex provider auth split
   - update `VertexAIProvider` so the API-key branch passes only:
     - `vertexai=True`
     - `api_key`
   - do not include `project` / `location` in the API-key branch
   - preserve project-credentials fallback when no API key is present

2. Tranche B. Explicit router/config contract
   - add bounded `auth_mode` support for `vertex_ai` provider config
   - wire `auth_mode` through `llm_router.py` into `VertexAIProvider`
   - set a clear default in `config/models.yaml`

3. Tranche C. Bounded regression tests
   - prove `VERTEX_API_KEY + VERTEX_PROJECT_ID + VERTEX_LOCATION` no longer breaks Gemini Vertex
   - prove API-key mode ignores project/location
   - prove project-credentials mode still requires project/location when no API key exists
   - preserve existing Vertex routing tests

## 9. Acceptance Criteria

- `vertexai:gemini-*` can run in Express/API-key mode even when `VERTEX_PROJECT_ID` and `VERTEX_LOCATION` are also present in the process env
- `VertexAIProvider` no longer constructs a mutually-exclusive client initializer
- `vertex_ai` auth intent is explicit in config/router contract
- project-credentials fallback path still exists for non-Express Vertex use
- no regression to existing Gemini Vertex routing/tests
- no Anthropic/OpenAI auth redesign is introduced in this wave

## 10. Verification Plan

- `python -m py_compile modules/core/providers/vertex_provider.py modules/core/llm_router.py tests/test_llm_router.py`
- `pytest tests/test_llm_router.py -q`
- run one targeted live smoke after implementation:
  - shared env containing `VERTEX_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`
  - `vertexai:gemini-3.1-pro-preview`
  - expect no mutual-exclusion error
- `python scripts/check_utf8_hygiene.py config/models.yaml modules/core/llm_router.py modules/core/providers/vertex_provider.py tests/test_llm_router.py docs/2026-03-26/multi-provider-vertex-auth-mode-split-wave1-execution-ssot.md docs/temp/multi-provider-vertex-auth-mode-split-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails

- Do not broaden into Claude request-access or quota workflows.
- Do not modify `AnthropicVertexProvider` unless a tiny constructor-compat note is strictly required.
- Do not redesign all-provider auth handling in this wave.
- Do not touch `response_schemas.py`, `BaseAgent`, or metrics code.
- Do not rely on operator instruction alone; the runtime contract must be explicit in code/config.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: remove temp mirror after implementation + closure audit passes
- roadmap dependency: none; single active execution item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note

Closure Date: 2026-03-26
Closure Status: closed (closure-audited)

Realization Summary:
- `VertexAIProvider` now supports explicit `auth_mode = api_key | project_credentials | auto`.
- API-key mode no longer leaks `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` into the Google client initializer.
- `vertex_ai.auth_mode` is explicit in router defaults and `config/models.yaml`.
- shared-env Gemini Vertex live smoke passed without the prior mutual-exclusion error.

Verification Evidence:
- `python -m py_compile modules/core/providers/vertex_provider.py modules/core/llm_router.py tests/test_llm_router.py` -> PASS
- `pytest tests/test_llm_router.py -q` -> `41 passed`
- shared-env live smoke:
  - `vertexai:gemini-3.1-pro-preview` -> PASS, no `Project/location and API key are mutually exclusive` error
  - `vertexai:gemini-2.5-flash` -> PASS, `backend=google_vertex`, `auth_mode=api_key`
- `python scripts/check_utf8_hygiene.py config/models.yaml modules/core/llm_router.py modules/core/providers/vertex_provider.py tests/test_llm_router.py docs/2026-03-26/multi-provider-vertex-auth-mode-split-wave1-execution-ssot.md docs/temp/multi-provider-vertex-auth-mode-split-wave1-execution-ssot.md` -> PASS

Residual Risk:
- No blocking residual risk remains inside this wave scope.
- `anthropic_vertex` partner-model access / quota / request-access gating remains deferred and was explicitly out of scope for this wave.

Excluded Surface Check:
- `modules/core/providers/anthropic_vertex_provider.py` redesign not opened
- `modules/api/process_runner.py` not touched in this wave
- `modules/core/metrics_collector.py` not touched in this wave
- `modules/domain/agents/base_agent.py` not touched in this wave
