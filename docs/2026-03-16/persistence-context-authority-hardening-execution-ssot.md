<!-- [완료] -->
<\!-- [완료] -->
# persistence-context-authority-hardening Execution SSOT

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/persistence-context-authority-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/persistence-context-authority-hardening-execution-ssot.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: wide workspace code/docs changes already present; OPUS memo re-audit and survivor queue promotion in progress`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `dirty: lane realized in stage01_helpers/fact_ledger/world_state/db_manager/stage4_context_builder/base_agent plus targeted tests`
Source Survey Docs:
- `docs/2026-03-16/opus-survivor-intake-authority-reclassification.md`
- `docs/2026-03-15/opus/all-stage-deepdive-fix-candidates-ssot.md`
- `docs/2026-03-15/opus/all-subsystem-tf-consolidated-ssot.md`
- `docs/2026-03-15/opus/detail-subsystem-tf-consolidated-ssot.md`
Evidence Artifacts:
- `docs/2026-03-16/opus-survivor-intake-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- Harden low-level authority boundaries where the current workspace still fails open or bypasses its own infrastructure.
- Promote only the survivor items that remain directly supported by live code: `S0-1`, `X-2`, `TF-BA-02`, `TF-S4CB-02`.

## 2. Baseline Facts
- `stage01_helpers.py` still continues after a failed DNA sync because only the success branch exists.
- `FactLedger.save()` and `WorldState.save()` still log and continue on save failure instead of surfacing a structured degraded state.
- `Stage4ContextBuilder` still uses `_db._lock` plus `_db.conn.cursor()` directly for tier-2 summary retrieval.
- cached-context LLM calls still bypass `MetricsCollector.start_call()` / `end_call()` in `BaseAgent`.

## 3. Scope
Included:
- `modules/core/stage01_helpers.py`
- `modules/core/fact_ledger.py`
- `modules/core/world_state.py`
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/base_agent.py`
- targeted tests for init failure, save failure, metrics, and DBManager authority

Excluded:
- Stage 3 history truncation
- director grading / feedback quantification logic
- broader persistence lane artifacts already closed in the 2026-03-15 roadmap

## 4. Pass 1. Inventory Summary
- Survivor count in this lane: `4`
- Main hotspots:
  - initialization fail-open
  - silent persistence degradation
  - raw DB authority bypass
  - metrics blind spot on cached path

## 5. Pass 2. Semantic Classification
- Class A: fail-open bootstrap/init behavior (`S0-1`)
- Class B: non-blocking save failure without explicit degraded contract (`X-2`)
- Class C: infrastructure bypass / observability gap (`TF-S4CB-02`, `TF-BA-02`)

## 6. Side-Effect Map
- file writes / artifacts:
  - project anchors and JSONL/metrics artifacts may change
- DB / schema / transaction boundaries:
  - DBManager access path and anchor save behavior are direct scope
- JSONL / log / audit sinks:
  - metrics emission and degraded-state logging may change
- console / UI / operator output:
  - Stage 0 failure messaging may become explicit
- rollback / recovery / retry:
  - save/init failure contracts are direct scope
- cache / global state:
  - cached-context metrics path is direct scope
- bootstrap fallback / config-env mutation:
  - Stage 0 bootstrap path is direct scope

## 7. Realization Architecture
- Replace silent or warning-only failure seams with explicit structured outcomes.
- Route tier-2 Stage 4 summary reads through DBManager-owned seams or a clearly-owned adapter.
- Ensure cached-context requests participate in the same metrics contract as direct asks.

## 8. Execution Tranches
1. Make Stage 0 DNA sync failure explicit and non-silent.
2. Add structured degraded-state reporting for FactLedger / WorldState save failure paths.
3. Remove or bound raw Stage 4 DB cursor bypass and restore metrics coverage for cached-context calls.

## 9. Acceptance Criteria
- DNA sync failure no longer falls through as silent success.
- FactLedger / WorldState save failures become contract-explicit enough for later callers or operators to detect.
- Stage 4 context tier-2 retrieval no longer bypasses DBManager authority blindly.
- cached-context calls produce metrics start/end coverage comparable to direct ask paths.

## 10. Verification Plan
- targeted pytest for Stage 0 init failure behavior
- targeted pytest for FactLedger / WorldState save-path signaling
- targeted pytest for Stage 4 context retrieval contract
- targeted pytest for BaseAgent cached metrics path
- `python -m py_compile` for touched Python files

## 11. Guardrails
- Do not reopen already-closed 2026-03-15 persistence finalization scope beyond these survivor items.
- Do not widen this lane into general DB refactoring.
- Do not silently swallow save failures again under a different log message.

## 12. Temp Queue Notes
- temp status: cleaned after closure
- cleanup condition: remove the mirror after realization and closure
- roadmap dependency: `docs/2026-03-16/opus-survivor-followup-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Summary
- realization status:
  - `S0-1` landed: Stage 0 DNA sync failure now emits explicit warning plus audit event instead of failing silently
  - `X-2` landed: `FactLedger.save()` and `WorldState.save()` now return `bool` and expose `last_save_ok` / `last_save_error`
  - `TF-S4CB-02` landed: tier-2 Stage 4 summary reads now go through `DBManager.get_episode_meta_summaries()`
  - `TF-BA-02` landed: cached-context LLM calls now participate in metrics start/end coverage
- verification:
  - `python -m py_compile modules/core/stage01_helpers.py modules/core/fact_ledger.py modules/core/world_state.py modules/core/db_manager.py modules/core/stage4_context_builder.py modules/domain/agents/base_agent.py tests/test_stage01_helpers.py tests/test_fact_ledger.py tests/test_stage4_context_builder.py tests/test_base_agent.py tests/test_world_state_manager.py`
  - `python -m pytest tests/test_stage01_helpers.py -k dna_failure_skips_post_processing`
  - `python -m pytest tests/test_fact_ledger.py -k "save_sets_degraded_contract_on_failure or save_clears_degraded_contract_on_success"`
  - `python -m pytest tests/test_world_state_manager.py`
  - `python -m pytest tests/test_stage4_context_builder.py -k "tier2_summary"`
  - `python -m pytest tests/test_base_agent.py -k "cached_context_metrics or ask_accumulates_usage_across_continuations"`
  - `python -m pytest tests/test_stage4_post_processor.py -k "transaction_wraps_both_saves or transaction_rollback_on_failure"`
- residual risk:
  - no open blocker inside this lane
  - broader persistence or continuity follow-up remains in later survivor lanes, not here
- next queue item:
  - `docs/2026-03-16/director-feedback-decision-integrity-hardening-execution-ssot.md`
