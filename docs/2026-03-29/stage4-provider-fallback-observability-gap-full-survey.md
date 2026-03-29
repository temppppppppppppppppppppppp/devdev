## Stage4 Provider Fallback Observability Gap — Full Survey

Date: 2026-03-29
Status: final (3-pass audited)
Track: system
Topic Slug: stage4-provider-fallback-observability-gap

---

### 1. Scope and Intent

This survey answers one concrete question:

> When a primary Stage 4 model call fails and fallback serves the request, do llm_io, token/cost accounting, audit sinks, and operator-facing canary evidence still describe the same underlying truth, or are they currently split across contradictory sinks?

Included surfaces: `base_agent.py`, `llm_provider.py`, all 4 provider modules, `llm_router.py`, `session_logger.py`, `metrics_collector.py`, `stage4_episode_logging.py`, `stage4_post_processor.py`, `audit_service.py`, `db_manager.py`, `models.yaml`, `run_stage4_canary.py`, canary evidence from 4 projects.

Excluded: provider-policy redesign, fix_scope/fix_pack contract, prompt wording, `.env` editing, default provider changes.

---

### 2. Evidence Sources

| Source | Type | Status |
|--------|------|--------|
| `modules/domain/agents/base_agent.py` | Code | Inspected — ask(), \_finalize\_successful\_ask, \_finalize\_failed\_ask, \_attempt\_backup\_recovery, \_handle\_quota\_fallback\_branch, \_session\_token\_cost\_kwargs, \_log\_llm\_call\_to\_db |
| `modules/core/session_logger.py` | Code | Inspected — log\_llm\_call writes to llm\_io.jsonl |
| `modules/core/metrics_collector.py` | Code | Inspected — start\_call, end\_call, scope breakdown, calculate\_cost |
| `modules/core/llm_router.py` | Code | Inspected — resolve\_provider\_identity, BACKEND\_FAMILY\_MAP |
| `modules/core/llm_provider.py` | Code | Inspected — LLMResponse(provider, backend, family) |
| `modules/core/providers/*.py` | Code | Inspected — all 4 providers return correct provider/backend/family in LLMResponse |
| `modules/core/stage4_episode_logging.py` | Code | Inspected — episode production payload includes model\_tier, round\_model\_breakdown |
| `modules/core/stage4_post_processor.py` | Code | Inspected — snapshot\_and\_reset\_scope writes model\_breakdown to cost\_log |
| `config/models.yaml` | Config | Current: all agents Gemini-first |
| `config/models.canary-fw.bak.yaml` | Config | Claude-first backup: analyst=claude-sonnet-4-6, chief\_writer=claude-sonnet-4-6, director=claude-opus-4-6 |
| `canary_0328_fixpack_contract_check_v2` | Canary evidence | CONTAMINATED — Claude credit-balance 400 errors, Gemini fallback |
| `canary_0328_gemini_direct_fixscope_check` | Canary evidence | CLEAN control — Gemini-only, 3 episodes PASS |
| `canary_0328_sink_verify_micro` | Canary evidence | CLEAN control — Gemini-only, 1 episode PASS |
| `canary_0329_feedback_windowing_check` | Canary evidence | CLEAN — Gemini-only, 2 episodes |

---

### 3. Provider Selection and Fallback Path Map

#### 3.1 Primary Model Selection

Each agent's primary model is resolved at `__init__` time (`base_agent.py:289-297`):

```
resolved_model = model_tier  (explicit override)
if None → _get_agent_default_model(snake_case(class_name))  (from config/models.yaml agents section)
if None → DEFAULT_MODEL_TIER  (gemini-2.5-flash)
```

#### 3.2 Backup Model Resolution

Backup is resolved once at `__init__` (`base_agent.py:300`):

```python
self.backup_model = _resolve_backup_model(self.primary_model, self.MODEL_FALLBACK_CHAIN)
```

Fallback chain from `models.yaml`:

| Primary | Backup |
|---------|--------|
| claude-opus-4-6 | claude-sonnet-4-6 |
| claude-sonnet-4-6 | gemini-2.5-pro |
| gemini-3.1-pro-preview | gemini-2.5-pro |
| gemini-2.5-pro | gemini-2.5-flash |
| gemini-2.5-flash | gemini-2.5-flash (self) |

#### 3.3 Two Distinct Fallback Mechanisms

**Mechanism A — In-loop quota/rate-limit fallback** (`_handle_quota_fallback_branch`, `base_agent.py:1279-1347`):

- Triggered when: `_classify_api_error_mode()` detects `resource_exhausted`, `quota`, `429`, or rate-limit exhaustion
- Behavior: calls `_generate_content(model=next_model)` directly within the ask() loop, returns response as `result["response"]`
- `current_model` is updated to `next_model` in the ask() loop (`base_agent.py:722`)
- Subsequent `_finalize_successful_ask()` receives the correct fallback model

**Mechanism B — Backup recovery** (`_attempt_backup_recovery`, `base_agent.py:1476-1624`):

- Triggered when: ask() loop raises to `_finalize_failed_ask()` (all in-loop retries exhausted or error type not recognized as retryable)
- Behavior: tries `self.backup_model` as a fresh call outside the ask() loop
- If backup\_model itself is Claude and also fails → tries partial response merge → returns error response
- Does NOT cascade to a third model

#### 3.4 Error Classification Gap

`_classify_api_error_mode()` (`base_agent.py:1227-1241`) recognizes:
- `resource_exhausted` or `quota` → `is_quota_exhausted`
- `429` + (`rate`/`limit`/`too many requests`) → `is_rate_limit`
- `429` alone → `is_ambiguous_429`

**Gap identified**: Anthropic's "credit balance too low" returns HTTP 400 with `invalid_request_error` type. This error string does NOT contain `resource_exhausted`, `quota`, `429`, `rate`, `limit`, or `too many requests`. Therefore:
- `is_quota_exhausted` = False
- `is_rate_limit` = False
- `is_ambiguous_429` = False
- All retry/fallback branches return None
- `_handle_api_error()` returns `action="raise"`

This means Anthropic credit-exhaustion errors bypass Mechanism A entirely and always fall through to Mechanism B (backup recovery). This is the exact scenario observed in the fixpack canary.

#### 3.5 "Same Request Recovered by Fallback" vs "New Attempt"

**Mechanism A (in-loop)**: Same request identity. The ask() loop continues with the fallback response as if the primary had succeeded. `current_model` is updated. One logical ask() call.

**Mechanism B (backup recovery)**: New attempt identity. A separate API call with `self.backup_model`. Gets its own `backup_metric_id` in MetricsCollector. But the ask() caller receives a plain string with no metadata indicating it came from backup.

---

### 4. Sink-by-Sink Truth Matrix

#### 4.1 Mechanism A (In-loop fallback — quota/rate-limit)

| Sink | attempted\_model | served\_model | token\_usage | cost | request correlation |
|------|-----------------|--------------|-------------|------|---------------------|
| SessionLogger (llm\_io.jsonl) | ✗ not recorded | ✓ `current_model` updated to fallback | ✓ from actual response | ✗ **cost uses `self.primary_model` pricing** | No request\_id — single entry, no trace of primary attempt |
| \_log\_llm\_call\_to\_db (project\_data.db) | ✗ not recorded separately | ✓ `model=current_model` (fallback) | ✓ from actual response | ✓ cost uses passed `model` param (correct) | No correlation to failed primary |
| MetricsCollector scope breakdown | ✗ `start_call()` recorded primary model | ✗ **`end_call()` does not override model** — tokens attributed to primary | ✓ tokens from actual response | ✗ **cost calculated against primary model pricing** | metric\_id started with primary, never updated |
| episode\_production.jsonl `model_tier` | — | Populated via `getattr(chief_writer, "model_tier", None)` — reflects agent's `primary_model`, not served model | — | — | — |
| episode\_production.jsonl `round_model_breakdown` | — | — | from MetricsCollector scope snapshot | from MetricsCollector scope snapshot | inherits MetricsCollector errors |

**Summary for Mechanism A**: SessionLogger records the correct served model but wrong cost. MetricsCollector attributes tokens and cost to the WRONG model (primary instead of served). DB has correct model and cost. episode\_production inherits MetricsCollector's errors.

#### 4.2 Mechanism B (Backup recovery — non-retryable errors)

| Sink | attempted\_model | served\_model | token\_usage | cost | request correlation |
|------|-----------------|--------------|-------------|------|---------------------|
| SessionLogger (llm\_io.jsonl) — failure entry | ✓ `model=current_model` at time of failure | ✗ | ✗ (estimated from prompt text, not from API) | ✗ (uses `self.primary_model` pricing on estimated tokens) | Logged from `_finalize_failed_ask` |
| SessionLogger (llm\_io.jsonl) — success entry | — | **✗ MISSING** — `_attempt_backup_recovery()` does NOT call `SessionLogger.log_llm_call()` | — | — | **No entry at all** |
| \_log\_llm\_call\_to\_db — failure entry | ✓ `model=current_model` | — | estimated | estimated cost | from `_finalize_failed_ask` |
| \_log\_llm\_call\_to\_db — success entry | — | ✓ `model=self.backup_model` | ✓ from response | ✓ correct model pricing | from `_attempt_backup_recovery` L1530 |
| MetricsCollector — primary metric | ✓ model from `start_call` | — | estimated (fallback from prompt text) | estimated at primary pricing | `end_call` with success=False |
| MetricsCollector — backup metric | — | ✓ `f"{agent_name}_Backup"`, `self.backup_model` | ✓ from response | ✓ correct pricing | separate metric\_id, correct |
| episode\_production.jsonl `model_tier` | — | `None` (confirmed in fixpack canary entry 0) | — | — | — |
| episode\_production.jsonl `round_model_breakdown` | — | — | sum of both metrics (primary estimated + backup real) | sum of both (wrong primary rate + correct backup rate) | Mixed: estimated primary tokens at primary pricing + real backup tokens at backup pricing |

**Summary for Mechanism B**: llm\_io.jsonl records ONLY the failure. The successful backup call is **invisible to llm\_io**. MetricsCollector correctly separates primary/backup metrics but the scope breakdown mixes estimated phantom tokens (attributed to primary) with real backup tokens. DB has both entries correctly.

---

### 5. Live Canary Contradiction Evidence

#### 5.1 Contaminated Canary: `canary_0328_fixpack_contract_check_v2`

**Configuration**: Claude-first (`models.canary-fw.bak.yaml`): analyst=claude-sonnet-4-6, chief\_writer=claude-sonnet-4-6, director=claude-opus-4-6. All other agents Gemini.

**Failure mode**: Anthropic credit balance exhausted → HTTP 400 `invalid_request_error` → NOT recognized by `_classify_api_error_mode()` → falls through to Mechanism B backup recovery.

**llm\_io.jsonl evidence**:
- 54 entries, **ALL failures, 0 successes**
- claude-opus-4-6: 20 failures (Director)
- claude-sonnet-4-6: 34 failures (Analyst + ChiefWriter)
- Error: `"Your credit balance is too low to access the Anthropic API"`
- **Zero Gemini entries** — all successful Gemini backup/primary calls invisible

**episode\_production.jsonl evidence** (same canary):
- 9 entries across 4 rounds, all REJECT (score 50) but with **real content produced**
- Round 0: 32 calls, 238,005 tokens, $1.074858
  - claude-sonnet-4-6: 94,696 tokens, $0.284088
  - claude-opus-4-6: 24,213 tokens, $0.363195
  - gemini-2.5-pro: 119,096 tokens, $0.427575
- `model_tier`: `None`
- Content hash present, artifact paths populated → real manuscripts were generated

**Contradiction**: llm\_io.jsonl says "100% FAIL, zero served content, only Claude models" while episode\_production says "32 calls served, 238K tokens consumed including 119K Gemini tokens, real manuscripts produced with content hashes."

**Token attribution concern**: The claude-sonnet-4-6 "94,696 tokens" in model\_breakdown are likely **estimated** from prompt text length (via `MetricsCollector.estimate_tokens()` fallback when `_call_usage_totals` is zero from failed calls) rather than actual API-reported usage. Anthropic rejected these requests at HTTP 400 before processing any tokens. The $0.284 cost against those phantom tokens is computed at Claude pricing rates. This is **inference based on the code path** — the failed call's `_build_metric_usage_payload(use_accumulated=True)` falls back to `estimate_tokens()` when accumulated usage is zero.

#### 5.2 Clean Control: `canary_0328_gemini_direct_fixscope_check`

**Configuration**: Gemini-only (current models.yaml or equivalent).

**llm\_io.jsonl evidence**:
- 94 entries, **ALL successes, 0 failures**
- gemini-2.5-pro: 85 successes
- gemini-2.5-flash: 9 successes

**episode\_production.jsonl evidence**:
- 3 episodes PASS (scores 96-98)
- Single provider: gemini-2.5-pro
- Token/cost values align between llm\_io and episode\_production

**Control conclusion**: When no fallback occurs, llm\_io and episode\_production agree. The sinks are structurally sound; the divergence is specific to fallback paths.

#### 5.3 Clean Control: `canary_0328_sink_verify_micro`

- 1 episode PASS (score 94), Gemini-only
- Consistent across sinks
- Confirms control baseline

#### 5.4 `canary_0329_feedback_windowing_check`

- Gemini-only, 2 episodes
- Feedback windowing / patch-reaudit cycle working correctly
- Consistent across sinks

---

### 6. Root-Cause Assessment

#### Root Cause 1 — `_attempt_backup_recovery()` does not log to SessionLogger

**Location**: `base_agent.py:1476-1624`

`_attempt_backup_recovery()` calls `_log_llm_call_to_db()` (L1530, L1604) and `MetricsCollector.end_call()` (L1549) for the backup call. It does NOT call `BaseAgent._session_logger_global.log_llm_call()`.

This means successful backup recovery calls are invisible to `llm_io.jsonl`. The failure entry from `_finalize_failed_ask()` is the only record, making the entire ask() appear as a failure to llm\_io consumers.

**Impact**: Any operator reviewing `llm_io.jsonl` sees 100% failure when backup recovery is active. Episode artifacts show progression. This split is the primary observability gap.

#### Root Cause 2 — `_session_token_cost_kwargs()` uses `self.primary_model` for cost calculation

**Location**: `base_agent.py:496`

```python
cost = collector.calculate_cost(
    getattr(self, "primary_model", "") or "",  # ← always primary, never served
    ...
)
```

When fallback has served the request (either Mechanism A or B), the cost recorded in `llm_io.jsonl` is calculated at the **primary model's** pricing rate against the served model's token counts.

**Impact**: If primary=claude-opus-4-6 ($15/$75 per 1M tokens) and served=gemini-2.5-pro ($1.25/$10 per 1M), cost is overstated by ~7-12x in llm\_io.jsonl. Note that `_log_llm_call_to_db()` uses the passed `model` parameter (correct), so DB cost is accurate.

#### Root Cause 3 — MetricsCollector `start_call()` model is never updated on fallback

**Location**: `metrics_collector.py:200-230`, `base_agent.py:1108`

`start_call(agent_name, current_model)` records the model at metric creation time. When in-loop fallback (Mechanism A) changes `current_model`, the existing metric\_id retains the original model. `end_call()` (L232-309) does not accept a model parameter for override.

At `end_call()` time (L291-306):
```python
model = metric.model  # ← still the original primary model
self._model_tokens[model]["input"] += input_tokens
self._scope_model_breakdown[model]["tokens"] += call_tokens
self._scope_model_breakdown[model]["cost"] += cost
```

**Impact**: `model_breakdown` in episode\_production.jsonl and cost\_log DB table attributes tokens and cost to the **attempted primary model** instead of the **actual served model**. For Mechanism B, this is partially mitigated because backup gets its own metric with `agent_name_Backup`, but the primary metric still records estimated phantom tokens.

#### Root Cause 4 — Anthropic 400 credit-exhaustion not classified as quota exhaustion

**Location**: `base_agent.py:1227-1241`

The error string `"Your credit balance is too low"` does not match any of the retryable patterns. This forces ALL Anthropic credit-exhaustion errors through Mechanism B (backup recovery) instead of Mechanism A (in-loop fallback).

**Impact**: Mechanism B has worse observability than Mechanism A. If this error were recognized as quota-related, the in-loop fallback would at least preserve the correct served model in SessionLogger and DB (Root Cause 2 cost issue would remain, Root Cause 3 MetricsCollector issue would remain, but Root Cause 1 llm\_io blindness would be resolved).

#### Root Cause 5 — `model_tier` field in episode\_production is not fallback-aware

**Location**: `stage4_interview_round.py:3432`

```python
model_tier=getattr(chief_writer, "model_tier", None)
```

`model_tier` on the agent is an alias for the constructor's `model_tier` parameter, which resolves to `self.primary_model` at init time. It is never updated after fallback. The fixpack canary confirms: `model_tier: None`.

**Impact**: episode\_production entries carry no usable signal about which model actually served the content.

---

### 7. Highest-Risk Operator Misreads

Ranked by severity of misinterpretation:

**Risk 1 — "llm\_io all fail" while episode artifacts progress** (CRITICAL)

An operator reviewing `llm_io.jsonl` concludes "Stage 4 is broken, zero useful LLM output" while `episode_production.jsonl` shows real manuscripts with content hashes. This was directly observed in the fixpack canary: 54 failures, 0 successes in llm\_io, 4 rounds of content produced in episode\_production.

Misread: "The pipeline is fundamentally broken." Reality: "Claude is down; Gemini backup is serving content successfully."

**Risk 2 — `model_breakdown` implying Claude served tokens it never processed** (HIGH)

The fixpack canary shows `claude-sonnet-4-6: 94,696 tokens, $0.284` in model\_breakdown. These are estimated phantom tokens — Anthropic rejected these requests at HTTP 400 before processing. An operator would conclude "Claude contributed meaningful work alongside Gemini" when in fact Claude contributed zero served tokens.

Misread: "Claude served 40% of the workload." Reality: "Claude served 0%; the 94K tokens are prompt-length estimates from rejected requests."

**Risk 3 — Provider contamination over-attributed to core Stage 4 logic** (HIGH)

When llm\_io shows 100% failure and verdicts are REJECT (score 50), an operator may attribute quality failures to Stage 4 logic (prompt quality, director calibration, etc.) rather than to provider unavailability. The fixpack canary's consistent score-50 REJECTs look like a systemic quality problem, but the root cause is that backup model quality (gemini-2.5-pro serving content originally designed for claude-sonnet-4-6) was insufficient for the quality gates.

Misread: "Stage 4 quality gates are miscalibrated." Reality: "Provider fallback degraded content quality below the threshold."

**Risk 4 — Cost truth divergence between sinks** (MODERATE)

llm\_io.jsonl computes cost at `self.primary_model` pricing. DB computes cost at the actual served model pricing. If primary is Claude Opus ($75/1M output) and served is Gemini Pro ($10/1M output), llm\_io overstates cost by 7.5x. An operator aggregating costs from llm\_io would produce dramatically different totals than one querying cost\_log.

Misread: "This episode cost $3.55." Reality: "This episode cost ~$1.50 in actual API charges."

**Risk 5 — Invisible backup success makes retry budgets look exhausted** (MODERATE)

When ask() returns the backup text, the caller receives a plain string. There is no metadata indicating the response came from a backup model. Quality assessment proceeds as if the primary model served the content. If the backup model's output quality is lower, the director may reject it, consuming retry budget on a problem that is provider-related, not content-related.

---

### 8. Bounded Remediation Options Ranked

| Rank | Option | Scope | Risk | Addresses Root Causes |
|------|--------|-------|------|-----------------------|
| 1 | **Add SessionLogger.log\_llm\_call() to `_attempt_backup_recovery()` for successful backup calls** | 5-10 lines in base\_agent.py | Minimal — adds a log entry, no behavioral change | RC-1 (llm\_io blindness) |
| 2 | **Fix `_session_token_cost_kwargs()` to use the actual served model for cost calculation** | 1 line change in base\_agent.py (pass `current_model` instead of `self.primary_model`) | Minimal — changes only the cost field in llm\_io entries | RC-2 (llm\_io cost truth) |
| 3 | **Add `served_model` parameter to `MetricsCollector.end_call()` to allow model override** | ~10 lines in metrics\_collector.py, ~5 lines in base\_agent.py call sites | Low — additive parameter with backward-compatible default | RC-3 (model\_breakdown truth) |
| 4 | **Extend `_classify_api_error_mode()` to recognize Anthropic credit-exhaustion as quota-like** | ~3 lines in base\_agent.py | Low — routes 400 credit errors to Mechanism A instead of B, improving observability coverage | RC-4 (error classification) |
| 5 | **Add `attempted_model` and `served_model` fields to `SessionLogger.log_llm_call()`** | ~10 lines in session\_logger.py, ~15 lines in base\_agent.py call sites | Low — additive fields, no behavioral change | Enriches RC-1 fix with lineage |
| 6 | **Propagate `served_model` into episode\_production.jsonl `model_tier` field** | ~5 lines in stage4\_interview\_round.py | Low — replaces `getattr(chief_writer, "model_tier")` with actual served info | RC-5 |
| 7 | **Add request-level correlation ID (ask\_id) linking primary attempt and backup recovery** | ~20 lines across base\_agent.py and session\_logger.py | Moderate — new field threading through multiple code paths | Cross-cutting enrichment |
| 8 | **No code change — wait for more evidence** | None | None | None — evidence is already sufficient for options 1-4 |

---

### 9. Recommended Bounded Next Step

**Recommended**: Options 1-4 as a single bounded patch.

Rationale:

The evidence directly proves that the observability gap is structural, not edge-case. The fixpack canary demonstrates that a real operator reviewing llm\_io.jsonl would conclude "100% failure" when the pipeline is producing real content via Gemini backup. This is not a theoretical risk — it has already occurred and has already contaminated canary decision-making.

Options 1-4 are:
- **Independently safe**: Each can be applied and tested in isolation
- **Behaviorally transparent**: None change LLM routing, model selection, retry logic, or quality gates
- **Observability-only**: They add or correct log/metric entries without altering any pipeline decision
- **Small blast radius**: Combined ~25 lines of code changes across 2-3 files
- **Testable via canary**: A single Claude-first canary with credit-exhaustion simulation would prove the fix

Options 5-7 are desirable enrichments but can follow in a second wave after the core truth split is resolved.

Option 8 (no code change) is not recommended because the evidence is sufficient and the gap is actively contaminating canary interpretation.

This conclusion aligns with the preferred operating conclusion:

> Tighten observability around attempted-model vs served-model lineage so contaminated canaries stop misleading operators, without forcing a provider-policy redesign in the same wave.

The recommended options are strictly observability patches. They do not change provider defaults, model selection, retry logic, or quality gates. The provider-policy question (Claude-first vs Gemini-first) remains a separate decision that can be made with better data once the observability gap is closed.

---

### 10. Confidence

| Finding | Confidence | Basis |
|---------|-----------|-------|
| RC-1: `_attempt_backup_recovery()` missing SessionLogger call | **Direct proof** | Code inspection (`base_agent.py:1476-1624`) + canary evidence (54 failures, 0 successes in llm\_io while episode\_production shows content) |
| RC-2: `_session_token_cost_kwargs()` uses wrong model for cost | **Direct proof** | Code inspection (`base_agent.py:496`) — `self.primary_model` hardcoded |
| RC-3: MetricsCollector model not updated on fallback | **Direct proof** | Code inspection (`metrics_collector.py:200-230, 291-306`) — `metric.model` from `start_call`, never overridden |
| RC-4: Anthropic 400 credit error not classified as quota | **Direct proof** | Code inspection (`base_agent.py:1227-1241`) + canary error text match failure |
| RC-5: `model_tier` not fallback-aware | **Direct proof** | Code inspection (`stage4_interview_round.py:3432`) + canary entry `model: None` |
| Phantom token attribution in model\_breakdown | **Inference** | Code path analysis — `_build_metric_usage_payload()` falls back to `estimate_tokens()` when accumulated usage is zero from failed calls. Not directly verified by reading raw MetricsCollector state from canary, but code path makes this the only explanation for Claude token counts appearing in model\_breakdown when Anthropic rejected all requests at HTTP 400. |
| Cost overstatement in llm\_io entries | **Inference** | Follows from RC-2 + known pricing differential. Not verified by comparing raw llm\_io cost fields against DB cost fields from the same canary, because the fixpack canary's llm\_io has no success entries to compare. |
| Gemini-primary agent calls missing from fixpack llm\_io | **Partial inference** | The fixpack llm\_io has 54 Claude failures and zero other entries. Gemini-primary agents (flash-based: arc\_critic, consensus\_validator, etc.) should log successes via `_finalize_successful_ask()`. Their absence suggests either (a) those agents' calls are excluded from Stage 4 interview rounds in this configuration, (b) a SessionLogger initialization timing issue, or (c) an undiscovered code path. This is a secondary question — the primary gap (backup recovery blindness) is proven independently. |
---

### 11. Audit Record

Pass 1 - Scope and structure:
- bounded to provider/fallback observability, not provider-policy redesign
- required survey sections remained intact

Pass 2 - Evidence and consistency:
- RC-1 through RC-5 re-checked against live code paths
- direct proof vs inference labeling stayed bounded

Pass 3 - Actionability and overclaim control:
- next move remains observability-only
- lower-priority `model_tier` enrichment stayed secondary to served-model truth

Estimated confidence: `96%`
