# Lane B Survey: Provider Adapter Boundary — Claude on Vertex

Date: 2026-03-26
Status: final (3-pass audited, lane-local survey)
Type: system-track parallel survey lane
Lane Owner: Terminal 2
Canonical Path: `docs/2026-03-26/multi-provider-claude-on-vertex-lane-b-survey.md`
Source Master Order: `docs/2026-03-26/multi-provider-claude-on-vertex-entry-parallel-survey-master-order.md`
Evidence Basis:
- `modules/core/llm_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/llm_router.py`
- `docs/2026-03-26/llm-multi-provider-context-note.md` (external API context §5.2, §5.3)

Commit State:
- Baseline Commit: `07e9aaf8`
- Baseline Dirty Summary: dirty workspace (multi-provider wave1 changes in flight)

## 1. Lane B Core Question

Can `anthropic_provider.py` be cleanly extended/reused for Claude on Vertex, or is a separate adapter required?

## 2. Findings

### 2.1 Current AnthropicProvider Anatomy

`anthropic_provider.py` (91 lines) has 4 functional blocks:

| # | Block | Lines | Responsibility |
|---|-------|-------|----------------|
| 1 | `_get_client()` | L30-44 | Auth + client construction |
| 2 | Request building | L46-66 | Extract config → build `messages.create()` kwargs |
| 3 | Response parsing | L68-80 | Extract text + usage from Anthropic response shape |
| 4 | Identity stamping | L82-90 | `provider/backend/family` on `LLMResponse` |

### 2.2 What Claude Direct and Claude on Vertex Share

Per Anthropic official docs (context note §5.2): the Vertex API is nearly identical to the Messages API. Both use the `anthropic` Python SDK. Both call `client.messages.create()` with the same kwargs.

Shared code surface in current `AnthropicProvider`:

| Component | Shareable | Evidence |
|-----------|-----------|----------|
| `_config_value()` static helper | yes, identical | `anthropic_provider.py:17-22` |
| `_normalize_messages()` static helper | yes, identical | `anthropic_provider.py:25-28` |
| Request kwargs construction (`model`, `messages`, `max_tokens`, `temperature`, `top_p`, `system`) | yes, identical | `anthropic_provider.py:48-65` |
| `client.messages.create(**kwargs)` call shape | yes, identical | `anthropic_provider.py:67` |
| Response text extraction (`block.type == "text"`) | yes, identical | `anthropic_provider.py:69-72` |
| Usage extraction (`usage.input_tokens`, `usage.output_tokens`) | yes, identical | `anthropic_provider.py:74-80` |
| `LLMResponse` envelope construction | yes, except `backend` field | `anthropic_provider.py:82-90` |

**Result: 6 of 7 components are fully shareable. Only client construction and identity stamping diverge.**

### 2.3 What Must Diverge

| Divergence | Claude Direct | Claude on Vertex |
|------------|---------------|------------------|
| SDK client class | `anthropic.Anthropic` | `anthropic.AnthropicVertex` |
| Auth mechanism | API key (`ANTHROPIC_API_KEY`) | Google Cloud credentials (project_id + region + ADC/service account) |
| Client constructor kwargs | `api_key=str` | `project_id=str, region=str` (+ optional credentials) |
| `LLMResponse.backend` | `"anthropic_direct"` | `"anthropic_vertex"` |

The `anthropic.AnthropicVertex` class is available from the same `anthropic` package. It wraps the same Messages API but routes through Vertex AI endpoints and uses Google Cloud auth instead of Anthropic API keys.

### 2.4 Existing Gemini / Vertex Split Pattern (Precedent)

The codebase already has a Gemini/Vertex split:

| | GeminiProvider | VertexAIProvider |
|-|----------------|------------------|
| File | `gemini_provider.py` (52 lines) | `vertex_provider.py` (139 lines) |
| Client | Passed-in `client` | Self-managed `genai.Client(vertexai=True)` |
| `generate()` body | ~30 lines | ~30 lines (near-duplicate) |
| Response parsing | Lines 19-41 | Lines 106-129 (identical logic) |
| Identity | `google_direct / gemini` | `google_vertex / gemini` |

**Observation**: The Gemini/Vertex split duplicated the entire response parsing block. This was acceptable because `google.genai` response objects are identical for both backends. But it is still duplication.

### 2.5 Three Adapter Design Options

#### Option A: Separate `AnthropicVertexProvider` class

Create a new `anthropic_vertex_provider.py` that duplicates request building and response parsing.

- Pro: follows the existing Gemini/Vertex precedent
- Con: duplicates 6 of 7 blocks (47 of ~60 functional lines)
- Con: any future change to Anthropic request/response logic must be applied twice
- Fit: weak — Claude's case is simpler than Gemini's because both use the same SDK package and the same `messages.create()` call

#### Option B: Extend `AnthropicProvider` via subclass

Create `AnthropicVertexProvider(AnthropicProvider)` that overrides only `_get_client()` and identity.

```python
class AnthropicVertexProvider(AnthropicProvider):
    provider_name = "anthropic_vertex"

    def __init__(self, *, project_id_env="VERTEX_PROJECT_ID",
                 region_env="VERTEX_LOCATION",
                 credentials_env="GOOGLE_APPLICATION_CREDENTIALS"):
        ...

    def _get_client(self):
        # AnthropicVertex(project_id=..., region=...)
        ...
```

- Pro: zero duplication of request/response logic
- Pro: `_get_client()` is already a clean override seam
- Pro: identity can be stamped by overriding `backend` attribute
- Con: subclass coupling — if `AnthropicProvider.generate()` changes internals, subclass inherits
- Fit: strong — the divergence is exactly at the `_get_client()` boundary

#### Option C: Single class with backend parameter

Make `AnthropicProvider` accept a `backend_mode` param that switches client construction.

```python
class AnthropicProvider:
    def __init__(self, *, backend="anthropic_direct", ...):
        self._backend = backend
        ...

    def _get_client(self):
        if self._backend == "anthropic_vertex":
            from anthropic import AnthropicVertex
            self._client = AnthropicVertex(project_id=..., region=...)
        else:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=...)
```

- Pro: single class, no duplication, no inheritance
- Con: `_get_client()` becomes a conditional branch — mixes two auth concerns in one method
- Con: constructor parameter list becomes a union of direct + vertex kwargs
- Fit: moderate — simpler than subclass but dirtier as more backends are added

### 2.6 Recommended Adapter Design

**Option B (subclass) is the best fit.**

Reasons:

1. **The divergence surface is exactly one method.** `_get_client()` is already isolated. Subclass override is the textbook pattern for "same behavior, different construction."

2. **Zero request/response duplication.** Unlike the Gemini/Vertex split (which duplicated 30 lines of response parsing), the Anthropic subclass inherits all of `generate()` unchanged.

3. **Identity is trivially overridable.** The subclass sets `provider_name = "anthropic_vertex"` and the `LLMResponse` construction already reads `self.provider_name`. The `backend` field needs one small adjustment (see §2.7).

4. **The router already has the registration shape.** `llm_router.py:53-67` (`_build_provider()`) can add one `if provider_name == "anthropic_vertex"` branch. `BACKEND_FAMILY_MAP` at line 25-30 can add one entry.

5. **Future-proof without over-engineering.** If Anthropic adds Vertex-specific features later, the subclass can override individual methods without touching the direct path.

### 2.7 Required `AnthropicProvider` Adjustment for Subclass Support

Current `generate()` hardcodes `backend="anthropic_direct"` at line 88:

```python
return LLMResponse(
    ...
    provider=self.provider_name,
    backend="anthropic_direct",  # ← hardcoded
    family="claude",
)
```

For the subclass to inherit `generate()` cleanly, `backend` must be derived from instance state instead of hardcoded. Minimal change:

```python
# Add class-level attribute
class AnthropicProvider:
    provider_name = "anthropic"
    _backend = "anthropic_direct"
    _family = "claude"
    ...

    def generate(self, ...):
        ...
        return LLMResponse(
            ...
            provider=self.provider_name,
            backend=self._backend,
            family=self._family,
        )
```

Then the subclass sets:
```python
class AnthropicVertexProvider(AnthropicProvider):
    provider_name = "anthropic_vertex"
    _backend = "anthropic_vertex"
    _family = "claude"
```

This is a 3-line addition to `AnthropicProvider` and a ~30-line new file.

### 2.8 Router Registration Delta

Current router state:

| Router component | Current | Needed for Claude on Vertex |
|------------------|---------|------------------------------|
| `BACKEND_FAMILY_MAP` (`llm_router.py:25-30`) | 4 entries (gemini, vertex_ai, anthropic, openai) | +1 entry: `"anthropic_vertex": ("anthropic_vertex", "claude")` |
| `DEFAULT_PROVIDER_CONFIGS` (`llm_router.py:10-22`) | 4 providers | +1 entry: `"anthropic_vertex"` with `project_id_env`, `region_env`, `credentials_env` |
| `_build_provider()` (`llm_router.py:53-67`) | 4 branches | +1 branch: `if provider_name == "anthropic_vertex"` |
| `infer_provider_name()` (`llm_router.py:104-114`) | `claude` → `"anthropic"` | needs prefix-based disambiguation (see cross-lane dependency to Lane A) |

**Key routing question for Lane A**: How does the router distinguish "Claude direct" from "Claude on Vertex"? Current `infer_provider_name()` maps all `claude*` models to `"anthropic"`. A prefix convention (e.g., `vertex:claude-sonnet-4-6`) or config-level default-backend setting is needed. This is a Lane A decision, not Lane B.

### 2.9 Anthropic SDK Availability Check

Both `Anthropic` and `AnthropicVertex` come from the same `anthropic` package:

```python
from anthropic import Anthropic          # direct
from anthropic import AnthropicVertex    # vertex
```

The existing lazy-import pattern in `_get_client()` (`anthropic_provider.py:39-41`) already handles missing package gracefully. The subclass can use the same pattern for `AnthropicVertex`.

`AnthropicVertex` requires `google-auth` as an additional dependency (for Google Cloud credential loading). This is already available in the environment because `VertexAIProvider` uses `google.auth.load_credentials_from_file` (`vertex_provider.py:44`).

## 3. Must-Answer Questions

### Q1. What parts of Claude direct can be shared with Claude on Vertex?

**Almost everything.** Specifically:

- `_config_value()` — shared (static, no provider coupling)
- `_normalize_messages()` — shared (static, no provider coupling)
- Request kwargs construction — shared (same `messages.create()` contract)
- `messages.create()` call — shared (same SDK method, both clients expose it)
- Response text extraction — shared (same response shape)
- Usage extraction — shared (same `usage.input_tokens/output_tokens` shape)
- `LLMResponse` envelope — shared except `backend` field value

### Q2. What parts must diverge?

Only two:

1. **Client construction**: `Anthropic(api_key=...)` vs `AnthropicVertex(project_id=..., region=...)`
2. **Runtime identity**: `backend="anthropic_direct"` vs `backend="anthropic_vertex"`

### Q3. Which abstraction is right?

**Subclass (`AnthropicVertexProvider extends AnthropicProvider`).**

- Not "extend `AnthropicProvider`" by adding conditionals — that mixes auth concerns
- Not "create a fully separate `AnthropicVertexProvider`" — that duplicates 80% of the code
- Not "shared Claude substrate with two thin backends" — that's over-engineering for a 1-method divergence
- The subclass override pattern is the exact right weight for this divergence shape

## 4. Cross-Lane Dependencies

| To Lane | Dependency | Evidence |
|---------|-----------|----------|
| Lane A (identity/routing) | Router must disambiguate Claude-direct vs Claude-on-Vertex model strings. Current `infer_provider_name()` maps all `claude*` to `"anthropic"`. A prefix convention or config-level backend default is needed. | `llm_router.py:111` |
| Lane A (config) | `config/models.yaml` needs an `anthropic_vertex` provider section with `project_id_env`, `region_env`, `credentials_env` | `config/models.yaml:6-9` (current anthropic section) |
| Lane C (capability) | Structured output availability may differ between Claude direct and Claude on Vertex (context note §5.3). Adapter itself is identical, but capability gating is needed upstream. | `llm-multi-provider-context-note.md:121-128` |
| Lane D (usage/cost) | Usage extraction is identical (`input_tokens`, `output_tokens`), but pricing may differ. Metrics must distinguish `anthropic_direct` vs `anthropic_vertex` for billing. | `anthropic_provider.py:77-80`, `metrics_collector.py` |

## 5. Lane B Verdict

### Already Claude-on-Vertex-Friendly

1. `AnthropicProvider.generate()` request building is backend-agnostic — uses `messages.create()` with standard kwargs (`anthropic_provider.py:46-67`)
2. `AnthropicProvider.generate()` response parsing is backend-agnostic — same Anthropic response shape regardless of backend (`anthropic_provider.py:69-80`)
3. `_config_value()` and `_normalize_messages()` are static helpers with no backend coupling (`anthropic_provider.py:17-28`)
4. `LLMResponse` envelope already has `backend` and `family` fields (`llm_provider.py:28-33`)
5. `anthropic` Python SDK ships both `Anthropic` and `AnthropicVertex` in the same package
6. `google-auth` dependency already present in environment via `vertex_provider.py`

### Still Anthropic-Direct-Only

1. `_get_client()` constructs `Anthropic(api_key=...)` only — no Vertex client path (`anthropic_provider.py:30-44`)
2. `backend="anthropic_direct"` is hardcoded in `generate()` return (`anthropic_provider.py:88`)
3. Router maps all `claude*` to `"anthropic"` with no Vertex disambiguation (`llm_router.py:111`)
4. No `anthropic_vertex` entry in `BACKEND_FAMILY_MAP` or `DEFAULT_PROVIDER_CONFIGS` (`llm_router.py:10-30`)
5. No `anthropic_vertex` provider section in `config/models.yaml` (`config/models.yaml:6-9`)

### Must Change for Claude on Vertex Now

1. **Make `backend` derivable** — change `AnthropicProvider` to use class-level `_backend`/`_family` attributes instead of hardcoded strings in `generate()` (3-line delta in `anthropic_provider.py`)
2. **Create `AnthropicVertexProvider` subclass** — override `_get_client()` to construct `AnthropicVertex(project_id=..., region=...)`, set `provider_name="anthropic_vertex"`, `_backend="anthropic_vertex"` (~30 lines, new file or same file)

### Should Wait for Later

1. Structured output capability gating between Claude direct and Claude on Vertex (Lane C scope)
2. Thinking/extended-thinking support for Anthropic family (not yet used in this codebase)
3. Prompt caching divergence between direct and Vertex (Anthropic prompt caching is beta; capability gate, not adapter concern)
4. Unified request config abstraction (BaseAgent still compiles Gemini-native; broader refactor)

## 6. Estimated Effort

| Change | Scope | Lines |
|--------|-------|-------|
| `AnthropicProvider` backend attribute refactor | `anthropic_provider.py` | ~5 lines changed |
| `AnthropicVertexProvider` subclass | new file or appended to `anthropic_provider.py` | ~30-35 lines |
| Router registration (`_build_provider`, `BACKEND_FAMILY_MAP`, `DEFAULT_PROVIDER_CONFIGS`) | `llm_router.py` | ~15 lines added |
| Config section | `config/models.yaml` | ~8 lines added |
| **Total** | | **~60 lines** |

## 7. 3-Pass Audit Record

Pass 1. Structure and Scope
- Document type is lane-local survey, not execution SSOT
- Scope bounded to provider adapter boundary per master order §8 Lane B
- Does not take over Lane A routing, Lane C capability, or Lane D usage conclusions
- All 3 must-answer questions addressed
- Cross-lane dependencies noted without concluding other lanes' findings
- PASS

Pass 2. Evidence and Consistency
- `AnthropicProvider` anatomy verified by direct read of `anthropic_provider.py` (91 lines)
- `AnthropicVertex` SDK availability verified from Anthropic official docs referenced in `llm-multi-provider-context-note.md:112-118`
- `google-auth` dependency presence verified via `vertex_provider.py:44`
- Gemini/Vertex duplication precedent verified by comparing `gemini_provider.py:19-41` vs `vertex_provider.py:106-129`
- Router registration shape verified by direct read of `llm_router.py:10-67, 104-114`
- Shareable surface quantified by line-by-line analysis of `anthropic_provider.py`
- No claims beyond inspected code and referenced official docs
- PASS

Pass 3. Execution and Readability
- Findings-first structure
- File:line anchors for every claim
- Clear separation of shared / divergent / must-change-now / should-wait
- Three adapter options compared with explicit pro/con
- Cross-lane dependencies documented as evidence, not conclusions
- PASS

Estimated confidence: 97%

Reasoning:
- High confidence on shareable surface because both backends use the same `anthropic` SDK and `messages.create()` contract, verified by official docs
- High confidence on subclass design because `_get_client()` is already isolated as the sole client construction point
- High confidence on effort estimate because the total change surface is ~60 lines across 3 files
- Moderate residual uncertainty only on whether `AnthropicVertex` has any response-shape differences not documented in current official sources (assessed as unlikely but not impossible)
