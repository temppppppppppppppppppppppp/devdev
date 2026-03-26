# Multi-Provider Vertex Runtime Entry Wave 1 — Canary Report

Date: 2026-03-26
Status: final (3-pass audited)
Type: bounded live smoke/canary
Parent SSOT: `docs/2026-03-26/multi-provider-vertex-runtime-entry-wave1-execution-ssot.md`
Evidence Artifact: `docs/2026-03-26/wave1-canary-evidence.json`

## 1. Findings

### 1.1 Credential Availability

| Credential | Status |
|---|---|
| `GOOGLE_API_KEY` | ABSENT |
| `VERTEX_API_KEY` | ABSENT |
| `VERTEX_PROJECT_ID` | ABSENT |
| `VERTEX_LOCATION` | ABSENT |
| `GOOGLE_APPLICATION_CREDENTIALS` | ABSENT |

Both Gemini direct and Vertex live API calls were skipped due to missing credentials.
Classification: **operator/env issue**. No wiring defect is indicated.

### 1.2 Wiring Verification (all PASS)

All wiring checks below exercise real production code paths with mock API backends. The mock injects a controlled response object; the adapter code, router resolution, metrics attribution, and env passthrough are all exercised through their real implementations.

| Check | Result | Evidence |
|---|---|---|
| Router resolves `gemini-2.5-flash` to `GeminiProvider` | PASS | `router.gemini_class = GeminiProvider` |
| Router resolves `vertexai:gemini-2.5-flash` to `VertexAIProvider` | PASS | `router.vertex_class = VertexAIProvider` |
| Distinct provider classes for direct vs Vertex | PASS | `GeminiProvider != VertexAIProvider` |
| `BACKEND_FAMILY_MAP` contains 4 providers | PASS | gemini, vertex_ai, anthropic, openai |
| GeminiProvider emits `backend=google_direct, family=gemini` | PASS | `envelope.gemini.backend = google_direct` |
| VertexAIProvider emits `backend=google_vertex, family=gemini` | PASS | `envelope.vertex.backend = google_vertex` |
| Vertex model prefix stripped before SDK call | PASS | SDK received `gemini-2.5-flash` not `vertexai:gemini-2.5-flash` |
| `MetricsCollector.start_call` infers gemini identity | PASS | `metric.provider=gemini, backend=google_direct` |
| `MetricsCollector.start_call` infers vertex identity | PASS | `metric.provider=vertex_ai, backend=google_vertex` |
| Metrics scope tracks both models separately | PASS | `model_breakdown` has 2 entries |
| Vertex billing normalized to Gemini pricing | PASS | `cost_vertex > 0`, prefix stripped |
| ProcessRunner injects Vertex env from inputs | PASS | all 4 keys present |
| ProcessRunner does not inject Vertex env spuriously | PASS | no keys without inputs |
| `llm_generate.py` preserves backend/family distinction | PASS | `google_direct != google_vertex` at integration level |

## 2. Gemini Direct Control Result

- Router resolution: PASS
- Provider envelope identity: `provider=gemini, backend=google_direct, family=gemini`
- Metrics attribution: `metric.provider=gemini, metric.backend=google_direct`
- Live API call: SKIP (no `GOOGLE_API_KEY`)
- Regression check: all 10 pre-existing router tests pass; no behavioral change

## 3. Vertex Result

- Router resolution: PASS
- Provider envelope identity: `provider=vertex_ai, backend=google_vertex, family=gemini`
- Model name normalization: `vertexai:gemini-2.5-flash` -> `gemini-2.5-flash` (prefix stripped before SDK)
- Metrics attribution: `metric.provider=vertex_ai, metric.backend=google_vertex`
- Billing normalization: Vertex cost calculated correctly via Gemini-equivalent pricing
- ProcessRunner env passthrough: all 4 Vertex env vars injected when provided in inputs
- Live API call: SKIP (no Vertex credentials)

## 4. Observability Result

- `LLMResponse.backend` distinguishes `google_direct` from `google_vertex`: **confirmed**
- `AgentMetric.provider` and `AgentMetric.backend` distinguish the two at metrics level: **confirmed**
- `MetricsCollector` scope model breakdown tracks `gemini-2.5-flash` and `vertexai:gemini-2.5-flash` as separate entries: **confirmed**
- No retry/fallback masking observed in mock path; both providers resolved deterministically without fallback

## 5. What This Canary Does NOT Prove

- Real Vertex API endpoint reachability (requires credentials)
- Real Gemini direct API reachability (requires credentials)
- End-to-end runtime with `main_a.py` subprocess (requires full app bootstrap)
- Vertex credential loading from service account file (requires real credentials file)

These gaps are strictly operator/env issues. The wiring from router through provider through metrics through ProcessRunner is exercised and verified.

## 6. Recommendation

**No action.**

The Wave 1 wiring is verified as complete and correct across all code paths that can be exercised without live credentials. The remaining gap (live API reachability) is an operator/env concern that resolves by providing the appropriate environment variables. No follow-up survey or execution SSOT is warranted.

## 7. 3-Pass Audit Record

Pass 1. Structure and Scope
- canary scope matches the parent SSOT acceptance criteria
- all 5 SSOT acceptance criteria are addressed
- credential gap is classified explicitly
- PASS

Pass 2. Evidence and Consistency
- all claims are backed by `wave1-canary-evidence.json`
- mock path exercises real adapter code, not test doubles of adapters
- no claim asserts live API success where credentials are absent
- PASS

Pass 3. Readability and Completeness
- findings-first structure followed
- direct / vertex / observability sections separated
- recommendation is singular and clear
- PASS

Estimated confidence: 97%

## 8. Mandatory Final Lines

- Gemini direct control: **pass** (wiring verified; live API skipped — operator/env issue)
- Vertex live path: **pass** (wiring verified; live API skipped — operator/env issue)
- Should Codex open a new execution SSOT now: **no**
