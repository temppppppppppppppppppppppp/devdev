Date: 2026-03-27
Status: final (3-pass audited)
Document Type: system-track compact survey order
Canonical Path: `docs/2026-03-27/canary-observability-optimization-prep-compact-survey-order.md`
Temp Mirror Path: none
Parent Authority:
- `docs/2026-03-27/state-changes-schema-formalization-wave1-execution-ssot.md`
- `docs/2026-03-27/state-and-maturity-execution-roadmap.md`
Priority Slot:
- post-wave1 sidecar planning

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/context/validator/stage4/orientation/runtime surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Order Summary

Open one bounded compact survey for `canary / observability / optimization-prep readiness`.

This order is survey-only.

The goal is to classify four lanes against the live codebase:
- `ready now`
- `short additional work`
- `new design needed`
- `recommended next-doc split after wave1 closure`

Target topics:
- baseline canary
- cost/time/retry measurement
- quality dashboard interpretation
- budget gate
- canary summary diff
- shadow replay
- golden contract fixture pack

This order does **not** authorize implementation.

## 2. Hard Guardrails

### Absolute No-Change Rule

Do **not** modify production code.

Do **not**:
- patch `modules/`
- patch `main_a.py`
- patch tests
- patch config
- patch DB, project logs, or runtime artifacts
- patch `docs/temp/queue-state.json`
- patch any active execution SSOT
- patch `docs/temp/execution-roadmap.md`
- create an execution SSOT
- create a roadmap
- create a closure doc
- silently escalate into implementation

Allowed outputs:
- one compact survey document
- one optional raw evidence note

### No-Mutation Run Rule

Do **not** run mutation-capable smoke/canary/probe helpers that write project state.

Examples forbidden in this survey:
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`
- `scripts/run_stage3_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/run_stage4_canary.py`

Read-only inspection of code, tests, existing logs, existing JSON, and existing docs is allowed.

### Queue Isolation Rule

This survey is a sidecar planning artifact only.

Do **not**:
- alter queue order
- mark wave1 closed
- remove temp mirrors
- update queue status fields
- claim that any queued item is realized

## 3. Survey Question

Answer exactly this:

`What can the current workspace already do for canary-based stabilization and optimization prep, what needs only a small bounded extension, what still needs fresh design, and what is the cleanest document split to pursue after wave1 closure?`

## 4. Required Coverage

### A. Canary Execution Surfaces

- `scripts/run_stage3_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/run_stage4_canary.py`
- `modules/core/stage4_canary_tools.py`
- `scripts/regression_validation_tiers.py`
- `scripts/probe_claude_vertex_matrix.py`

### B. Measurement / Dashboard Surfaces

- `modules/core/pass_rate_monitor.py`
- `modules/api/bridge_server.py`
- `modules/core/db_manager.py`
- `modules/core/failure_analyzer.py`
- any canary summary builder or dashboard payload helper that already exposes:
  - runtime
  - cost
  - duration
  - retry
  - sink alignment
  - patch trace

### C. Fixture / Replay Adjacent Surfaces

- `scripts/prepare_smoke_fixture.py`
- `scripts/smoke_fixture_contract.py`
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`
- any rollback or DB-backed replay path that would matter for `shadow replay`

### D. Regression / Proof Tests

At minimum inspect:
- `tests/test_run_stage4_canary.py`
- `tests/test_stage4_canary_tools.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_pass_rate_monitor_rol.py`
- `tests/test_arc_difficulty.py`
- `tests/test_probe_claude_vertex_matrix.py`

If any listed surface is non-applicable, mark it explicitly as non-applicable instead of skipping it.

## 5. Required Outputs

### Canonical Survey Doc

Write:
- `docs/2026-03-27/canary-observability-optimization-prep-compact-survey.md`

### Optional Raw Evidence

Only if needed:
- `docs/2026-03-27/canary-observability-optimization-prep-evidence.md`

Do not create temp mirrors.

## 6. Minimum Findings Required

The survey is incomplete unless it explicitly contains all of the following.

### A. Ready-Now Asset Ledger

For each of these, record what already exists and how usable it is today:
- baseline canary lanes
- cost/time/retry measurement
- quality dashboard interpretation surfaces
- provider boundary probe matrix if relevant to future canary expansion

For each item, record:
- owner files
- current entry command or entry function
- whether it is static-only, read-only, or mutation-capable
- what evidence artifact it produces
- whether it is trustworthy enough to use immediately after wave1 closure

### B. Short-Additional Work Map

Cover exactly these two:
- `budget gate`
- `canary summary diff`

For each one, record:
- smallest plausible insertion point
- whether existing metrics are already sufficient
- whether a new script/helper is needed
- bounded blast radius
- why it qualifies as `short additional work` instead of fresh design

### C. Design-Needed Concept Ledger

Cover exactly these two:
- `shadow replay`
- `golden contract fixture pack`

For each one, record:
- why current assets are insufficient
- what authoritative inputs would be needed
- what mutation/risk boundary makes it non-trivial
- whether it should be surveyed separately before implementation

### D. Classification Table

Produce one explicit table or equivalent ledger that classifies each target topic as one of:
- `ready now`
- `short additional work`
- `design needed`

### E. Next-Doc Recommendation

Recommend the cleanest next document split after wave1 closure.

At minimum decide whether the next step should be:
- one combined execution SSOT for `baseline canary + budget gate + canary summary diff`
- or two documents:
  - one bounded execution SSOT for near-term canary/observability work
  - one separate survey order for `shadow replay + golden contract fixture pack`

## 7. Required Side-Effect Sweep

Even though this is a survey-only order, the following side-effect categories must still be checked.

- whether current canary helpers mutate fixture projects or live project state
- whether current summaries already persist proof artifacts
- whether dashboard payloads depend on non-authoritative caches
- whether replay-oriented ideas would touch rollback, DB rebuild, or artifact regeneration paths

If a side-effect category is non-applicable, say so explicitly.

## 8. Success Criteria

This order is complete only if the resulting survey can answer:

1. Which canary/measurement capabilities can be used immediately after wave1 closure
2. Which two bounded additions are genuinely small enough to justify a compact implementation wave
3. Why `shadow replay` is not yet a ready-now or short-additional item
4. Why `golden contract fixture pack` is not yet a ready-now or short-additional item
5. What the cleanest next document split is

If the survey cannot answer all five, it is not complete and should not be used for promotion.

## 9. Recommended Survey Shape

Keep the survey compact and execution-facing.

Recommended section order:
1. executive summary
2. scope and exclusions
3. ready-now asset ledger
4. short-additional work map
5. design-needed concept ledger
6. side-effect coverage
7. next-doc recommendation
8. confidence and limits

## 10. Promotion Rule

This order itself does **not** create an execution SSOT.

Only after the compact survey is complete and 3-pass audited may a later turn decide whether to promote it into:
- one bounded execution SSOT for near-term canary/observability work
- and/or one new survey order for replay/fixture design work

## 11. Confidence Target

Required confidence for the resulting survey:
- `95%+`

If confidence stays below `95%`, do not final-save the survey as authoritative.

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- document type matches a sidecar survey-order request
- scope is bounded to canary/observability optimization prep
- no implementation authority is granted
- PASS

### Pass 2. Evidence and Consistency
- output paths are canonical dated docs only
- no temp execution semantics were introduced
- queue isolation and no-mutation rules are explicit
- PASS

### Pass 3. Execution and Readability
- classification targets are operationally explicit
- ready-now vs short-additional vs design-needed is forced into one deliverable
- next-doc recommendation is bounded and actionable
- PASS

Estimated confidence: `96%`
