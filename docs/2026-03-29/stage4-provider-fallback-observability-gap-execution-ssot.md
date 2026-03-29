# Stage4 Provider Fallback Observability Gap Execution SSOT

Date: 2026-03-29
Status: execution-ready
Canonical Path: `docs/2026-03-29/stage4-provider-fallback-observability-gap-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: 14 tracked, 368 untracked; hotspots: feedback-windowing code/tests, narrative docs, canary projects, temp queue`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; execution-start re-audit completed on 2026-03-29 with provider/fallback survey draft promoted to final and only unrelated narrative/temp/canary drift present`
Source Survey Docs:
- `docs/2026-03-29/stage4-provider-fallback-observability-gap-full-survey-audit-order.md`
- `docs/2026-03-29/stage4-provider-fallback-observability-gap-full-survey.md`
Evidence Artifacts:
- `projects/canary_0328_fixpack_contract_check_v2/logs/session/llm_io.jsonl`
- `projects/canary_0328_fixpack_contract_check_v2/logs/episode_production.jsonl`
- `projects/canary_0328_gemini_direct_fixscope_check/logs/session/llm_io.jsonl`
- `projects/canary_0328_gemini_direct_fixscope_check/logs/episode_production.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe observability correction after the provider/fallback survey.

The next confirmed structural issue is:

> fallback can serve a Stage 4 request successfully while `llm_io`, token/cost accounting, and model-level episode breakdown still describe the request as a primary-model failure or primary-model cost.

This wave is not a provider-policy redesign.
This wave is a bounded observability correction so contaminated canaries stop misleading operators.

## 2. Baseline Facts

- `RC-1`: `_attempt_backup_recovery()` writes DB and metrics but does not write a successful SessionLogger entry, so `llm_io.jsonl` can look like `100% FAIL`
- `RC-2`: `_session_token_cost_kwargs()` calculates `llm_io` cost using `self.primary_model`, not the served model
- `RC-3`: `MetricsCollector.end_call()` attributes tokens/cost to `metric.model` from `start_call()`, with no served-model override
- `RC-4`: Anthropic `"credit balance is too low"` 400 errors are not classified as quota-like, so they bypass the more observable in-loop fallback branch
- `RC-5` (`model_tier` fallback awareness) is real but lower priority and excluded from this wave

## 3. Scope

Included:

- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- `tests/test_base_agent.py`
- `tests/test_cost_tracking.py`
- canonical execution SSOT and temp mirror maintenance

Excluded:

- `modules/core/session_logger.py` schema redesign
- `modules/core/stage4_interview_round.py` `model_tier` or `round_model_breakdown` contract redesign
- `modules/core/llm_router.py`
- provider modules and fallback-chain policy changes
- `.env`, `config/models.yaml`, canary runner changes
- request correlation id propagation
- `attempted_model` / `served_model` multi-sink schema expansion
- DB schema changes

## 4. Pass 1. Inventory Summary

- one missing-success sink:
  - backup recovery success never reaches `SessionLogger.log_llm_call()`
- one wrong-cost sink:
  - `llm_io` cost uses primary-model pricing even when fallback serves
- one wrong-model sink:
  - `MetricsCollector` keeps the `start_call()` model through `end_call()`
- one misrouted provider error:
  - Anthropic credit-exhaustion 400 is treated as non-quota and falls into backup recovery

## 5. Pass 2. Semantic Classification

- Class A: patch now
  - backup recovery success/failure visibility in `llm_io`
  - served-model cost truth for SessionLogger entries
  - served-model truth for MetricsCollector scope/model breakdown
  - Anthropic credit-exhaustion classification into the existing quota-like path

- Class B: explicitly deferred
  - `model_tier` fallback awareness in episode artifacts
  - `attempted_model` vs `served_model` explicit schema fields
  - cross-sink request lineage ids
  - provider-default changes

## 6. Side-Effect Map

- file writes / artifacts:
  - `modules/domain/agents/base_agent.py`
  - `modules/core/metrics_collector.py`
  - targeted tests
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - no DB schema change intended
  - DB write count may increase only if backup-recovery paths already write there and SessionLogger now mirrors them

- JSONL / log / audit sinks:
  - `llm_io.jsonl` will gain explicit backup-recovery entries
  - `total_cost_usd` in SessionLogger entries will reflect served-model pricing
  - canary operator interpretation should stop treating backup-served episodes as pure failure

- console / UI / operator output:
  - no intended console wording change
  - episode-level `model_breakdown` should stop attributing fallback-served tokens to the wrong model in scope summaries

- rollback / recovery / retry:
  - no retry-budget or Stage 4 quality-gate change intended
  - existing fallback order remains intact except for quota-like classification of Anthropic credit exhaustion

- cache / global state:
  - no new global state intended

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### 7.1 Backup-Recovery Session Logging Contract

The intended behavior is:

- when `_attempt_backup_recovery()` succeeds, `SessionLogger.log_llm_call()` must record a successful entry using `self.backup_model`
- when `_attempt_backup_recovery()` fails, `SessionLogger.log_llm_call()` should record the failed backup attempt as a separate entry using `self.backup_model`
- backup-recovery entries may use additive meta such as `context_tag="backup_recovery"` if the current logging surface already supports it

This wave must not redesign `llm_io` schema.
It only needs to stop hiding backup recovery from the existing sink.

### 7.2 Session-Cost Truth Contract

The intended behavior is:

- `_session_token_cost_kwargs()` must be able to calculate cost against the served model, not only `self.primary_model`
- success/failure finalizers that already know `current_model` must pass that model through
- backup-recovery session logging must use `self.backup_model` pricing

This wave must not change token-count collection semantics.
It only corrects which price table is applied.

### 7.3 MetricsCollector Served-Model Override Contract

The intended behavior is:

- `MetricsCollector.end_call()` may accept an additive served-model override
- when present, the metric should attribute tokens/cost/scope breakdown to the served model rather than the original `start_call()` model
- if provider/backend/family overrides are not passed explicitly, they should be inferred from the served-model override before the metric is finalized

This wave must not redesign `start_call()`.
It only corrects final attribution when fallback changes the served model.

### 7.4 Credit-Exhaustion Classification Contract

The intended behavior is:

- Anthropic `"credit balance is too low"` style 400 errors should classify as quota-like for fallback handling purposes
- the existing in-loop fallback mechanism should then remain the primary recovery path

This wave must not broaden into generic provider heuristics.
It should only recognize the known credit-exhaustion family that is already contaminating Stage 4 canaries.

## 8. Execution Tranches

1. Tranche 1: BaseAgent observability correction
   - add SessionLogger backup-recovery entries
   - teach `_session_token_cost_kwargs()` to use served-model pricing

2. Tranche 2: MetricsCollector attribution correction
   - add served-model override to `end_call()`
   - update relevant BaseAgent call sites that already know the effective model

3. Tranche 3: Anthropic credit-exhaustion classification
   - recognize the known 400 error family as quota-like
   - keep the rest of fallback logic unchanged

4. Tranche 4: regression coverage
   - prove backup-recovery success reaches `llm_io`
   - prove SessionLogger cost uses served-model pricing
   - prove `MetricsCollector` scope/model breakdown respects served-model override
   - prove credit-exhaustion classification routes as quota-like

## 9. Acceptance Criteria

- a successful backup recovery produces a successful `llm_io` entry for `self.backup_model`
- a failed backup recovery produces a distinct backup-failure `llm_io` entry or an equivalent explicit observability record within the same sink family
- SessionLogger `total_cost_usd` uses served-model pricing rather than unconditional `self.primary_model` pricing
- `MetricsCollector` model breakdown attributes tokens/cost to the served model when fallback changes the served model
- Anthropic `"credit balance is too low"` errors classify as quota-like
- no provider default, fallback chain order, Stage 4 quality gate, or retry threshold changes occur in this wave
- `model_tier` fallback awareness remains unchanged and documented as deferred

## 10. Verification Plan

- targeted pytest for:
  - backup-recovery logging and cost truth in `tests/test_base_agent.py`
  - served-model override accounting in `tests/test_cost_tracking.py`
- `python -m py_compile` on touched code/tests
- `ruff check` on touched code/tests
- `python scripts/check_utf8_hygiene.py` on touched code/tests/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Fresh canary validation should happen only after this wave lands.

## 11. Guardrails

- do not redesign `SessionLogger` schema beyond additive metadata already supported by `**meta`
- do not add DB columns
- do not touch `.env`, `config/models.yaml`, or canary runner logic
- do not fix `model_tier` in this wave
- do not add broad provider heuristics beyond the known Anthropic credit-exhaustion family
- do not let the patch change provider ordering or fallback policy except by routing the existing credit-exhaustion case into the existing quota-like branch

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - remove `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md` after realization and closure
- roadmap dependency:
  - refresh `docs/temp/execution-roadmap.md` before realization because the active temp queue predates this item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- queue sync command: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least `95%` confidence against the current workspace state before patching from it

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- implementation stays bounded to RC-1 through RC-4
- provider-policy redesign and episode artifact redesign stay excluded
- PASS

### Pass 2. Evidence and Consistency

- each tranche maps directly to a survey-confirmed root cause
- lower-confidence claims remain deferred instead of being bundled
- PASS

### Pass 3. Actionability and Overclaim Control

- execution can land in two production files and two targeted test files
- guardrails keep the wave observability-only
- PASS

Estimated confidence: `96%`
