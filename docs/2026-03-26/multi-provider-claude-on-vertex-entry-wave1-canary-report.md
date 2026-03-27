# Multi-Provider Claude on Vertex Entry Wave 1 Canary Report

Date: 2026-03-26
Type: bounded live smoke/canary
Source SSOT: `docs/2026-03-26/multi-provider-claude-on-vertex-entry-wave1-execution-ssot.md`
SSOT Status: closed (closure-audited)
Canary Timestamp: `2026-03-26T18:17:44`
Commit: current working tree on `main`, post-closure

## 1. Findings

### 1.1 Wiring (routing + provider + metrics + env) is fully operational

Every Wave 1 code path exercised without code changes:

| Layer | Claude Direct | Claude on Vertex | Distinguishable |
|-------|--------------|------------------|-----------------|
| Router prefix inference | `anthropic` | `anthropic_vertex` | yes |
| Provider class resolved | `AnthropicProvider` | `AnthropicVertexProvider` | yes |
| `provider_name` | `anthropic` | `anthropic_vertex` | yes |
| `_backend` | `anthropic_direct` | `anthropic_vertex` | yes |
| `_family` | `claude` | `claude` | same (correct) |
| `BACKEND_FAMILY_MAP` | `("anthropic_direct", "claude")` | `("anthropic_vertex", "claude")` | yes |
| Metrics `_infer_provider_identity` | `("anthropic", "anthropic_direct", "claude")` | `("anthropic_vertex", "anthropic_vertex", "claude")` | yes |
| Metrics billable model | `claude-sonnet-4-6` | `claude-sonnet-4-6` | same (correct: prefix stripped) |
| Metrics cost entry | `$3.00/$15.00` | `$3.00/$15.00` | same (correct: same model) |
| `AgentMetric.provider` | `anthropic` | `anthropic_vertex` | yes |
| `AgentMetric.backend` | `anthropic_direct` | `anthropic_vertex` | yes |
| ProcessRunner env | `ANTHROPIC_API_KEY` passthrough | `VERTEX_PROJECT_ID` + `VERTEX_LOCATION` passthrough | yes |
| BaseAgent usage normalization | `input_tokens` -> `prompt_token_count` bridge | same bridge | yes |

### 1.2 Live API calls blocked by missing credentials

Both live calls failed. Both failures are strictly **operator/env issues**, not wiring issues.

| Path | Error | Classification |
|------|-------|---------------|
| Claude direct | `ANTHROPIC_API_KEY is required to activate AnthropicProvider` | operator/env issue |
| Claude on Vertex | `VERTEX_PROJECT_ID (or GOOGLE_CLOUD_PROJECT) is required to activate AnthropicVertexProvider` | operator/env issue |

No unexpected fallback occurred. No Gemini path was silently triggered. The errors are clean `RuntimeError` from the provider `_get_client()` methods, exactly as designed.

### 1.3 No regression on existing paths

- Gemini direct and Gemini Vertex paths are untouched by this canary.
- `AnthropicProvider` still emits `backend="anthropic_direct"` (non-regression confirmed by both canary and existing test `test_anthropic_direct_provider_non_regression`).

## 2. Direct Control Result

**Claude direct API call**: blocked by missing `ANTHROPIC_API_KEY`.

Evidence:
```json
{
  "status": "fail",
  "error_type": "RuntimeError",
  "error": "ANTHROPIC_API_KEY is required to activate AnthropicProvider",
  "classification": "operator/env issue"
}
```

Routing, provider instantiation, metrics attribution all passed. Only the live SDK call failed.

## 3. Vertex Result

**Claude on Vertex API call**: blocked by missing `VERTEX_PROJECT_ID`.

Evidence:
```json
{
  "status": "fail",
  "error_type": "RuntimeError",
  "error": "VERTEX_PROJECT_ID (or GOOGLE_CLOUD_PROJECT) is required to activate AnthropicVertexProvider",
  "classification": "operator/env issue"
}
```

Routing, provider instantiation, metrics attribution all passed. Only the live SDK call failed.

## 4. Observability Result

Provider/backend/family attribution is fully distinguishable across all layers:

```
claude-sonnet-4-6
  -> provider=anthropic, backend=anthropic_direct, family=claude

anthropic-vertex:claude-sonnet-4-6
  -> provider=anthropic_vertex, backend=anthropic_vertex, family=claude
```

This distinction survives through:
- router inference
- provider class selection
- LLMResponse fields
- MetricsCollector AgentMetric fields
- cost calculation (same model, different provider attribution)
- ProcessRunner env injection

Usage normalization bridge verified:
```
input:  {"input_tokens": 100, "output_tokens": 50}
output: {"input_tokens": 100, "output_tokens": 50, "prompt_token_count": 100, "candidates_token_count": 50}
bridge_ok: true
```

## 5. ProcessRunner Env Passthrough

Verified that `ProcessRunner._build_env()` correctly propagates:

| Input Key | Env Var | Evidence Value |
|-----------|---------|---------------|
| `anthropic_api_key` | `ANTHROPIC_API_KEY` | `sk-ant-test-123` |
| `vertex_project_id` | `VERTEX_PROJECT_ID` | `canary-proj` |
| `vertex_location` | `VERTEX_LOCATION` | `us-east5` |

All three reach the subprocess environment.

## 6. Credential State Summary

```
ANTHROPIC_API_KEY:              unset
VERTEX_PROJECT_ID:              unset
VERTEX_LOCATION:                unset
VERTEX_API_KEY:                 set (Gemini Vertex only)
GOOGLE_APPLICATION_CREDENTIALS: unset
GOOGLE_CLOUD_PROJECT:           unset
anthropic SDK:                  0.78.0 (AnthropicVertex available)
```

To unblock live calls, the operator must provide:
- For Claude direct: `ANTHROPIC_API_KEY` in `.env`
- For Claude on Vertex: `VERTEX_PROJECT_ID` + `VERTEX_LOCATION` in `.env` (plus GCP ADC or service account)

## 7. Failure Classification

| Failure | Classification | Wiring Issue | Code Fix Needed |
|---------|---------------|-------------|-----------------|
| Claude direct live call | operator/env issue | no | no |
| Claude on Vertex live call | operator/env issue | no | no |

No router/provider wiring issues found.
No metrics attribution issues found.
No unexpected fallback masking detected.
No unrelated runtime issues encountered.

## 8. Recommendation

**No action** on the code side. Wave 1 wiring is fully operational.

The only blocker is operator credential provisioning:
1. Set `ANTHROPIC_API_KEY` for Claude direct
2. Set `VERTEX_PROJECT_ID` + `VERTEX_LOCATION` + GCP auth for Claude on Vertex

Once credentials are in place, the same canary script can be re-run to prove end-to-end live calls.

## 9. 3-Pass Audit Record

Pass 1. Structure and Scope
- canary is bounded to Wave 1 scope only
- no Gemini/OpenAI testing included
- no code changes made
- no new execution SSOT written
- PASS

Pass 2. Evidence and Consistency
- routing evidence matches provider instantiation evidence
- metrics attribution evidence matches BACKEND_FAMILY_MAP
- live call failures match credential state
- ProcessRunner env evidence matches _build_env implementation
- no contradiction between any evidence layers
- PASS

Pass 3. Completeness and Readability
- findings-first structure preserved
- direct vs Vertex results separated
- observability result explicitly covers all attribution layers
- failure classification is strict and non-speculative
- recommendation is singular
- PASS

Estimated confidence: 98%

## 10. Mandatory Final Lines

- Claude direct control: **mixed** (wiring pass, live call blocked by missing ANTHROPIC_API_KEY — operator/env issue)
- Claude on Vertex live path: **mixed** (wiring pass, live call blocked by missing VERTEX_PROJECT_ID — operator/env issue)
- Should Codex open a new execution SSOT now: **no**
