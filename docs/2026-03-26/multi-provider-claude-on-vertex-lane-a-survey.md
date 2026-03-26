# Lane A Survey: Identity / Config / Routing — Claude on Vertex

Date: 2026-03-26
Status: final
Type: system-track parallel survey lane
Lane Owner: Terminal 1
Canonical Path: `docs/2026-03-26/multi-provider-claude-on-vertex-lane-a-survey.md`
Source Master Order: `docs/2026-03-26/multi-provider-claude-on-vertex-entry-parallel-survey-master-order.md`

Evidence Basis:
- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- `modules/core/llm_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/vertex_provider.py`
- `tests/test_llm_router.py`

Commit State:
- Baseline Commit: `07e9aaf8`
- Resume Drift Summary: dirty workspace (config/models.yaml, llm_router.py, llm_provider.py, providers/, survey docs)

## 1. Lane A Core Question

Can the current router/config identity admit `backend=anthropic_vertex, family=claude` cleanly, or does the existing shape treat Vertex as exclusively Gemini and Claude as exclusively direct?

## 2. Findings

### 2.1 BACKEND_FAMILY_MAP Has No anthropic_vertex Slot

`llm_router.py:25-29` defines:

```python
BACKEND_FAMILY_MAP = {
    "gemini":    ("google_direct",    "gemini"),
    "vertex_ai": ("google_vertex",    "gemini"),
    "anthropic": ("anthropic_direct", "claude"),
    "openai":    ("openai_direct",    "gpt"),
}
```

**Gap**: There is no 5th entry for `anthropic_vertex -> (anthropic_vertex, claude)`. The map currently assumes:
- Vertex = always Gemini family
- Claude = always Anthropic direct

Claude on Vertex breaks both assumptions simultaneously.

### 2.2 Prefix Routing Has a Hard Conflict

`llm_router.py:104-114` — `infer_provider_name()`:

```python
if normalized.startswith(("vertexai:", "vertex:", "vertex/")):
    return "vertex_ai"           # → always Gemini family
if normalized.startswith("claude"):
    return "anthropic"           # → always direct backend
```

**Critical conflict**: A model string like `vertexai:claude-sonnet-4-6` would match the `vertexai:` prefix first and route to `vertex_ai` provider (Gemini family). The `claude` prefix never fires.

A model string like `claude-sonnet-4-6` always routes to `anthropic` (direct). There is currently **no prefix convention** that can express "Claude, but on Vertex backend."

This is the **#1 routing blocker** for Claude on Vertex entry.

### 2.3 Provider Builder Only Knows 4 Slots

`llm_router.py:53-67` — `_build_provider()`:

```python
if provider_name == "gemini":      ...
if provider_name == "anthropic":   ...
if provider_name == "openai":      ...
if provider_name == "vertex_ai":   ...
raise ValueError(...)
```

There is no `anthropic_vertex` case. Adding Claude on Vertex requires a 5th registration slot.

### 2.4 Config Has No anthropic_vertex Section

`config/models.yaml:1-26`:
- `vertex_ai`: Google SDK auth (project_id, location, credentials) — for Gemini-on-Vertex
- `anthropic`: Anthropic API key auth — for Claude direct

Claude on Vertex requires **Vertex-style auth** (project_id, location, credentials) but uses the **Anthropic SDK** (`anthropic.AnthropicVertex` client class), not the Google `genai` SDK. This is a fundamentally different auth+SDK combination from both existing entries.

Neither existing config section can serve Claude on Vertex:
- `vertex_ai` has the right auth shape but the wrong SDK (`google-genai`)
- `anthropic` has the right SDK (`anthropic`) but the wrong auth (API key only)

### 2.5 VertexAIProvider Cannot Serve Claude Models

`vertex_provider.py:131-139`:

```python
return LLMResponse(
    ...
    provider=self.provider_name,   # "vertex_ai"
    backend="google_vertex",
    family="gemini",               # ← hardcoded Gemini
)
```

The `VertexAIProvider` uses `genai.Client(vertexai=True)` — a Google SDK call. Claude on Vertex uses `anthropic.AnthropicVertex(project_id=..., region=...)` — a completely different SDK client. These are not the same transport at all.

**Conclusion**: VertexAIProvider cannot be extended for Claude. It is a Gemini-on-Vertex adapter, not a generic Vertex adapter.

### 2.6 AnthropicProvider Cannot Serve Vertex Backend

`anthropic_provider.py:30-44`:

```python
def _get_client(self):
    api_key = os.getenv(self.api_key_env)
    ...
    self._client = Anthropic(api_key=api_key)
```

Hardcoded to `Anthropic(api_key=...)` — the direct-API client. Claude on Vertex requires `AnthropicVertex(project_id=..., region=...)` — a separate client class in the same `anthropic` package.

`anthropic_provider.py:82-90`:

```python
return LLMResponse(
    ...
    backend="anthropic_direct",    # ← hardcoded direct
    family="claude",
)
```

**Conclusion**: AnthropicProvider has the right response shape (`family="claude"`) and the right SDK (`anthropic`), but the wrong client constructor and the wrong auth path.

### 2.7 LLMResponse Is Ready

`llm_provider.py:16-33` already carries `provider`, `backend`, `family` fields. No schema change needed. The response envelope can already express `backend="anthropic_vertex", family="claude"`.

### 2.8 models_config.py Inline Defaults Are Gemini-Only (Existing Debt)

`models_config.py:11-41`: All `DEFAULT_*` constants are Gemini strings. This is known debt from the spine survey (§1.2) and is not a new Claude-on-Vertex-specific finding, but it means Claude on Vertex cannot benefit from any fallback chain mechanism today.

### 2.9 Test Coverage Is Direct-Only for Claude

`tests/test_llm_router.py:280-304` tests `AnthropicProvider` but only asserts:
```python
assert response.backend == "anthropic_direct"
assert response.family == "claude"
```

No test exists for a Claude-on-Vertex path because the path does not exist yet.

## 3. Must-Answer Questions

### Q1. Does the current identity model have room for anthropic_vertex?

**No.** The identity model has the *shape* for it (`BACKEND_FAMILY_MAP`, `LLMResponse` fields) but no actual slot. The 4-entry map, 4-case builder, and 2-rule prefix router all need expansion.

### Q2. Is a new provider registration sufficient, or does current routing shape block it?

**Routing shape blocks it.** The `vertexai:` prefix is hardwired to `vertex_ai` (Gemini). Adding a 5th provider registration alone is not enough — `infer_provider_name()` must also learn to distinguish `vertexai:claude-*` from `vertexai:gemini-*`, or a new prefix convention must be adopted (e.g., `anthropic-vertex:claude-sonnet-4-6`).

### Q3. What minimum config/routing delta does Claude on Vertex actually need?

Minimum delta (5 items):

1. **New config section** in `models.yaml`:
   ```yaml
   anthropic_vertex:
     enabled: false
     sdk: "anthropic"
     project_id_env: "ANTHROPIC_VERTEX_PROJECT_ID"
     location_env: "ANTHROPIC_VERTEX_LOCATION"
     credentials_env: "GOOGLE_APPLICATION_CREDENTIALS"
   ```

2. **New BACKEND_FAMILY_MAP entry**:
   ```python
   "anthropic_vertex": ("anthropic_vertex", "claude"),
   ```

3. **New prefix convention** in `infer_provider_name()`:
   Option A: `anthropic-vertex:claude-sonnet-4-6` → new prefix
   Option B: extend `vertexai:` to inspect model name substring — `vertexai:claude-*` → `anthropic_vertex`, `vertexai:gemini-*` → `vertex_ai`
   Option C: secondary prefix like `vertex-claude:` or `vclaude:`

4. **New _build_provider case**:
   ```python
   if provider_name == "anthropic_vertex":
       return AnthropicVertexProvider(...)
   ```

5. **New DEFAULT_PROVIDER_CONFIGS entry** in `llm_router.py:10-22`.

## 4. Prefix Convention Analysis

| Option | Prefix Example | Pros | Cons |
|--------|---------------|------|------|
| A: `anthropic-vertex:` | `anthropic-vertex:claude-sonnet-4-6` | Explicit, no ambiguity | Verbose, new convention |
| B: `vertexai:` with model-name inspection | `vertexai:claude-sonnet-4-6` | Reuses existing prefix | Couples routing to model-name substring parsing; fragile |
| C: `vclaude:` | `vclaude:claude-sonnet-4-6` | Short | Invents ad-hoc prefix; doesn't generalize |

**Recommended: Option A** (`anthropic-vertex:` prefix). Reason: It follows the existing pattern where the prefix declares the *backend*, not the *family*. `vertexai:` means Google-Vertex-backend; `anthropic-vertex:` means Anthropic-Vertex-backend. This scales cleanly if OpenAI-on-Azure appears later (`azure:gpt-*`).

Option B is tempting but creates a hidden coupling: the prefix declares backend, then the model name re-declares family. If a future Vertex model has an ambiguous name, the routing breaks silently.

## 5. Cross-Lane Dependencies Detected

| Dependency | Target Lane | Evidence |
|------------|-------------|----------|
| SDK client class (`AnthropicVertex` vs `Anthropic`) | Lane B | anthropic_provider.py:43 vs anthropic SDK docs |
| Auth shape (project_id + region vs API key) | Lane B, Lane D | Different constructor, different env vars |
| Capability asymmetry (Claude direct vs Vertex) may affect routing decisions | Lane C | Some features may not be available on Vertex |
| Pricing/billing identity must distinguish anthropic_direct from anthropic_vertex | Lane D | metrics_collector.py pricing table |

## 6. Lane A Verdict

### Already Claude-on-Vertex-Friendly

1. `LLMResponse` already has `backend`, `family` fields — no schema change needed
2. `BACKEND_FAMILY_MAP` pattern already separates backend from family — just needs a 5th entry
3. Provider registration is extensible — `_build_provider` is a simple if-chain, not a closed enum
4. `config/models.yaml` structure already supports per-provider auth config

### Blocks Claude on Vertex Entry

1. **`infer_provider_name()` prefix routing** — `vertexai:` hardcodes to Gemini; `claude` hardcodes to direct. No path exists for Claude-on-Vertex.
2. **`BACKEND_FAMILY_MAP`** — missing `anthropic_vertex` entry
3. **`_build_provider()`** — missing `anthropic_vertex` case
4. **`DEFAULT_PROVIDER_CONFIGS`** — missing `anthropic_vertex` defaults
5. **`config/models.yaml`** — missing `anthropic_vertex` section

### What Claude-on-Vertex Wave 1 Must Do (Identity/Config/Routing Only)

1. Add `anthropic_vertex` to `BACKEND_FAMILY_MAP`
2. Add `anthropic-vertex:` prefix to `infer_provider_name()`
3. Add `anthropic_vertex` to `DEFAULT_PROVIDER_CONFIGS` and `_build_provider()`
4. Add `anthropic_vertex` section to `config/models.yaml`

### What Should Wait

1. Agent model assignment refactor (still string-only, Gemini-only — pre-existing debt)
2. Capability metadata in YAML (not needed for initial routing)
3. Fallback chain for Claude models (requires broader design)
4. `models_config.py` inline defaults diversification (pre-existing debt)

## 7. Estimated Scope

Identity/config/routing delta for Claude on Vertex: **~30-40 lines across 3 files** (llm_router.py, models.yaml, one new import). This is smaller than the Gemini-on-Vertex entry was.

The routing/identity layer is **not the bottleneck**. The harder questions are in Lane B (adapter/SDK boundary) and Lane C (capability asymmetry).

## 8. 3-Pass Audit Record

Pass 1. Structure and Scope
- Lane-local survey only
- Bounded to identity/config/routing
- Does not invade Lane B adapter or Lane C capability territory
- PASS

Pass 2. Evidence and Consistency
- `models.yaml` verified: vertex_ai.enabled=true, anthropic.enabled=false, no anthropic_vertex section
- `llm_router.py` verified: 4-entry map, 4-case builder, prefix conflict confirmed
- `anthropic_provider.py` verified: hardcoded `anthropic_direct` backend, API-key-only auth
- `vertex_provider.py` verified: hardcoded `google_vertex` backend, `genai.Client` SDK
- `llm_provider.py` verified: `LLMResponse` already has backend/family fields
- No stale claims carried from spine survey
- PASS

Pass 3. Execution and Readability
- Clear separation between "what exists" and "what blocks"
- Prefix convention recommendation is justified with comparison table
- Scope estimate is concrete
- PASS

Estimated confidence: 97%
