# Geuldobi V2 Context Provenance Budget Contract Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/geuldobi-v2-context-provenance-budget-contract-execution-ssot.md`
Temp Mirror Path: `docs/temp/geuldobi-v2-context-provenance-budget-contract-execution-ssot.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: lane1~3 code/tests/docs edits, temp mirror deletions, runtime log, survey bundle docs/evidence, and unrelated local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; Stage 2/3/4 provenance and budget contract landed in code/tests plus dashboard and perf-log surfaces; preserve unrelated dirty files as-is`
Source Survey Docs:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-deep-global-survey.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-evidence-manifest.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-cluster-compression.md`
Evidence Artifacts:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t03-upstream-design-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `95%`

## 1. Intent
- make Stage 2 -> Stage 3 -> Stage 4 context survival and budget use explicit instead of partially inferred
- turn Pack-C style provenance into a durable contract with `present -> survived -> dropped_at -> why`
- remove silent context-budget drift between upstream planners, CW context assembly, and Stage 4 caps

## 2. Baseline Facts
- `T03` and `T04` both found upstream-intent survival and truncation visibility gaps after the lane1 context work
- `T09` found budget authority drift between YAML values and Stage 4 fallbacks
- `stage2_preflight.py`, `stage3_orchestrator.py`, `context_advisor.py`, and `stage4_context_builder.py` jointly shape the final CW context but do not yet emit one stable drop ledger
- lane1 improved Tier 0/1/2 structure inside Stage 4, but did not fully contract Stage 2/3 provenance or total-budget accounting

## 3. Scope
Included:
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/context_advisor.py`
- `modules/core/stage4_context_builder.py`
- related config or constants that define context-budget caps
- durable or operator-visible sinks that must carry provenance/budget facts

Excluded:
- Director semantic split redesign already handled by lane2
- retry or `PASS_WITH_FIX` policy already handled by lane3
- broad UI or desktop rendering changes beyond the minimum needed to surface new context provenance fields
- fresh live-run execution in this document

## 4. Pass 1. Inventory Summary
- main hotspots:
  - Stage 2 pack selection and preflight pruning
  - Stage 3 orchestration and handoff shaping
  - Stage 4 tier assembly and truncation
- main mutable state:
  - retrieval slot budgets
  - mandatory context payloads
  - upstream carry-over summaries and focus fields
- primary risk:
  - losing intent or exceeding local caps without one final ledger that names what survived, what dropped, and where

## 5. Pass 2. Semantic Classification
- Class A: provenance-truth surfaces
  - fields or sinks that must say which upstream packs or items were present, survived, or were dropped
- Class B: budget-authority surfaces
  - config values, fallbacks, and local caps that define slot or mandatory-context limits
- Class C: truncation and degradation behavior
  - the places where overflow or prioritization silently rewrites what the CW or Director sees

## 6. Side-Effect Map
- file writes / artifacts:
  - Stage 4 episode artifacts and any companion summaries that need provenance fields
- DB / schema / transaction boundaries:
  - metadata persistence may need new columns or structured JSON fields for provenance/budget facts
- JSONL / log / audit sinks:
  - Stage 4 audit logs and runtime evidence sinks need bounded provenance/budget events
- console / UI / operator output:
  - operator surfaces may need concise provenance summaries, but not a full debug dump
- rollback / recovery / retry:
  - retry should consume the same budget truth rather than re-deriving caps ad hoc
- cache / global state:
  - cached context plans and singleton histories must not retain stale budget assumptions
- bootstrap fallback / config-env mutation:
  - fallback caps must be explicit and traceable if config is absent

## 7. Realization Architecture
- define one normalized provenance payload for Pack/CW context flow
  - minimum fields: `source_pack`, `source_item`, `stage_present`, `stage_survived`, `dropped_at`, `drop_reason`, `budget_bucket`
- define one final budget ledger produced near Stage 4 assembly
  - minimum fields: `configured_cap`, `effective_cap`, `consumed_chars`, `dropped_chars`, `overflow_reason`
- make Stage 2/3/4 each contribute facts to the same contract instead of emitting unrelated local summaries
- keep Python as collector/router only; any quality judgment about whether a drop was acceptable remains LLM-side or operator-side

## 8. Execution Tranches
1. define the normalized provenance and budget contract
2. instrument Stage 2/3/4 handoff points to emit the contract without changing judgment authority
3. propagate bounded provenance/budget facts to durable sinks and low-cost operator surfaces
4. add targeted regression checks for silent drop or cap-drift regressions

## 9. Acceptance Criteria
- one final context-budget ledger exists for the Stage 2/3/4 chain
- silent context drop without `dropped_at` and `drop_reason` is eliminated for in-scope packs
- config cap, fallback cap, and effective cap are distinguishable in code and sinks
- lane1 Tier 0/1/2 structure remains intact after provenance instrumentation

## 10. Verification Plan
- targeted unit tests around Stage 2/3/4 provenance and budget calculations
- targeted Stage 4 tests that assert `mandatory_context` and retrieval summaries preserve new provenance fields
- low-memory pytest shards for touched context-builder and upstream planner tests
- artifact/log spot check in one bounded project sample after implementation

## 11. Guardrails
- do not turn provenance instrumentation into Python-side quality arbitration
- do not widen CW mandatory context with bulk telemetry noise
- do not change Director prompt semantics in this lane except where new provenance facts must be consumed later
- do not rely on fresh live-run claims before execution-start re-audit

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - completed on 2026-03-17; remove the temp mirror after canonical closure, roadmap update, and queue validation
- roadmap dependency:
  - phase 1 of `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note
- realization outcome:
  - `modules/core/context_advisor.py` now defines one shared provenance and budget observation contract via `build_context_provenance_ledger()`, `build_context_budget_ledger()`, and `build_context_observation()`
  - `modules/core/stage2_preflight.py`, `modules/core/stage3_orchestrator.py`, and `modules/core/stage4_context_builder.py` now emit normalized Stage 2/3/4 provenance and budget ledgers instead of partially unrelated local summaries
  - `modules/core/quality_dashboard.py` and `modules/core/stage4_orchestrator.py` now persist and surface the new ledgers so operator-visible sinks reflect effective cap, drop, and survival facts
- verification evidence:
  - `python -m py_compile modules/core/context_advisor.py modules/core/stage2_preflight.py modules/core/stage3_orchestrator.py modules/core/stage4_context_builder.py modules/core/quality_dashboard.py modules/core/stage4_orchestrator.py tests/test_context_advisor.py tests/test_stage2_preflight.py tests/test_stage3_orchestrator.py tests/test_stage4_context_builder.py tests/test_quality_regression.py`
  - `python -m pytest tests/test_context_advisor.py -q`
  - `python -m pytest tests/test_stage2_preflight.py -k "work_focus_relation_slice_included_in_vector_context or global_budget_truncation" -q`
  - `python -m pytest tests/test_stage3_orchestrator.py -k "TestStageAttemptObservability or stage3_work_focus_relation_slice_included_in_semantic_context" -q`
  - `python -m pytest tests/test_stage4_context_builder.py -k "semantic_relation_slice or retrieval_coverage_warnings or rebalances_sc_and_mc_with_headroom" -q`
  - `python -m pytest tests/test_quality_regression.py -k "RetrievalObservationSummary" -q`
  - `python -m pytest tests/test_bridge_quality_summary.py -k "quality_dashboard_endpoint_combines_result_and_patterns" -q`
- residual risk:
  - Stage 2 and Stage 3 budget ledgers now expose the same contract as Stage 4, but their `dropped_chars` remain coarser than Stage 4's explicit trim accounting; later observability work can refine that precision without reopening this substrate lane
