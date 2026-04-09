# Stage2 Static Parallel 3-Pass Audit

Date: 2026-04-09
Status: final
Document Type: bounded static parallel audit
Canonical Path: `docs/2026-04-09/stage2-static-parallel-3pass-audit.md`
Mode: system-track, survey-only, static-only
Commit State:
- Baseline Commit: `b94390cb508a298a28349152bb15876f36662c65`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Docs:
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-06/rol-global-terminal2-stage2-pipeline-p0p1.md`
- `docs/2026-04-06/01_golden_stage2_p0_p3_bounded_survey.md`
- `docs/temp/execution-roadmap.md`
Evidence Artifacts:
- `docs/2026-04-09/stage2-static-parallel-evidence.json`
Confidence: `96%`
3-Pass Audit: `completed`

## 1. Answer First

Current Stage 2 static code does not reopen a live `P0` or `P1`.

The older high-severity packet-loss seam is now statically closed in the current code path:

- authoritative packet merge is centralized in `modules/core/stage2_contracts.py`
- both validation and finalization call that merge helper before continuity/persistence
- targeted tests explicitly assert that LLM-authored `world_joint` and `status_shadow` survive stale `enriched_block` fallback data

Current Stage 2 also does not show a newly confirmed static `P2`. The active residual lane still reads as `proof-deferred runtime closure work`, not as a fresh static correctness regression.

One issue does remain at `P3-structural` severity:

- `Stage2Orchestrator` and `Stage2Finalizer` both sit at `51` direct methods
- `Stage2Finalizer._record_s2_pass_metrics` is `180 LOC`

That is a real maintenance and regression-risk hotspot under the workspace complexity guardrails, but it is not the same thing as a live truth-corruption defect.

Queue consequence:

- keep `0_0-stage2-contract-normalization-remediation` as the governing Stage 2 lane
- keep its current roadmap position (`priority 4`)
- do not open a new Stage 2 execution lane from this audit alone

## 2. Scope

Included:

- Stage 2 production/runtime owners:
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_contracts.py`
- Stage 2 proof/summary owners:
  - `modules/core/services/audit_service.py`
  - `modules/core/failure_analyzer.py`
- Stage 2 targeted regression surfaces:
  - `tests/test_stage2_validation_pipeline.py`
  - `tests/test_stage2_finalizer.py`
  - `tests/test_audit_service.py`
  - `tests/test_failure_analyzer.py`
- active queue context in `docs/temp/execution-roadmap.md`

Excluded:

- fresh runtime rerun or canary execution
- artifact body reinspection inside `projects/*`
- new code patching
- queue mutation or execution SSOT rewrite

## 3. Pass 1 - Static Inventory

### 3.1 Owner surface

Structured AST inventory for the current Stage 2 owner family:

| Owner | Direct methods | `120+ LOC` methods | `180+ LOC` methods | Max LOC |
| --- | ---: | ---: | ---: | ---: |
| `Stage2Orchestrator` | `51` | `3` | `0` | `153` |
| `Stage2Finalizer` | `51` | `6` | `1` | `180` |
| `Stage2ValidationPipeline` | `32` | `3` | `0` | `144` |
| `FailureAnalyzer` | `75` | `3` | `0` | `176` |
| `AuditService` | `28` | `0` | `0` | `93` |

Stage 2 proof and persistence logic is therefore spread across:

- one high-pressure Stage 2 orchestrator owner
- one high-pressure Stage 2 finalizer owner
- one medium-pressure validation owner
- one cross-stage proof owner (`FailureAnalyzer`)
- one audit summary owner (`AuditService`)

### 3.2 Queue position

The current active roadmap still places Stage 2 here:

- `priority 4`: `0_0-stage2-contract-normalization-remediation`
- `priority 8`: `0_0-stage2-partial-fix-hardening-remediation`
- `priority 14`: `0_0-stage2-stage3-stage4-readiness-remediation` (blocked parent)

So the Stage 2 queue reading remains:

- active residual lane exists
- partial-fix child lane exists
- parent readiness lane stays blocked

### 3.3 Side-effect coverage

Static side-effect coverage inspected:

- file writes / artifact generation:
  - Stage 2 pass metrics and artifact linkage path in `stage2_finalizer.py`
- DB writes:
  - Stage 2 attempt/director selection/session decision proof fields
- JSONL / audit sinks:
  - `AuditService` proof digest and `FailureAnalyzer` sink-alignment summary
- console / UI output:
  - continuity updates and carryover-authority observability
- rollback / retry:
  - reject metrics and PASS_WITH_FIX proof fields
- cache / global state:
  - Stage 2 pass tail cache reset and session-scope handling

Not primary in this static pass:

- config/env mutation
- bootstrap fallback beyond Stage 2 owner entrypoints

## 4. Pass 2 - Semantic Classification

### 4.1 Former P1 packet-loss seam is statically closed

The 2026-04-06 `P1` reading around `joint_docs.world_joint` / `status_shadow` overwrite is no longer live in the current static codebase.

Current code path:

- `modules/core/stage2_contracts.py:19-37` defines `merge_stage2_authoritative_packet(...)`
- `modules/core/stage2_validation_pipeline.py:930-936` uses that helper before continuity inspection
- `modules/core/stage2_validation_pipeline.py:1186-1194` uses the same helper when continuity returns partial corrections
- `modules/core/stage2_finalizer.py:1516-1522` uses the same helper before persistence preparation

Targeted regression evidence:

- `tests/test_stage2_validation_pipeline.py:420-462` asserts that `llm-world` and authoritative `status_shadow` fields survive stale block fallback
- `tests/test_stage2_finalizer.py:905-941` asserts that the saved Stage 2 arc preserves `world_joint`, `expected_injuries`, `item_consumption`, and `key_stat_change`

Closed reading:

- `former P1: closed in static code`

### 4.2 Proof-layer sink parity is present, not absent

The current active Stage 2 SSOT says the next bounded slice is proof-layer hardening. Static code supports that reading.

Current proof surface:

- `modules/core/services/audit_service.py:428-475`
  - Stage 2 live-session summary now computes `attempt_key`, `artifact_path`, `selection_reason`, `verdict_reason`, and `carryover_authority` coverage
- `modules/core/services/audit_service.py:700-767`
  - proof digest now resolves DB + JSONL presence and asks `FailureAnalyzer` for per-stage compact summaries
- `modules/core/failure_analyzer.py:784-844`
  - Stage 2 sink alignment loader reads `attempt_key`, `selection_reason`, `verdict_reason`, `runtime_advisory`, and `retry_directives`
- `modules/core/failure_analyzer.py:1574-1688`
  - Stage 2 rationale comparison explicitly tracks mismatch buckets for `verdict_reason`, `runtime_advisory`, and `retry_directives`
- `modules/core/failure_analyzer.py:1941-2004`
  - sink alignment summary now counts blank-`attempt_key` rows and session-decision parity before compacting proof output

Targeted regression evidence:

- `tests/test_audit_service.py:843-875` guards blank `stage_attempts.attempt_key` warning surfacing
- `tests/test_audit_service.py:876-975` guards missing `session_decisions.verdict_reason` warning surfacing
- `tests/test_audit_service.py:976-1081` guards `runtime_advisory` / `retry_directives` mismatch surfacing
- `tests/test_audit_service.py:1418-1435` guards Stage 2 live-session coverage and carryover-authority surfacing
- `tests/test_stage2_finalizer.py:680-716` guards persistence of `verdict_reason`, `runtime_advisory`, and `retry_directives`

Closed reading:

- `not a reopened static P1/P2`
- still a valid `proof-deferred runtime closure` lane under the existing SSOT

### 4.3 Confirmed P3-structural hotspot remains

The strongest live issue from this static pass is structural, not semantic.

Confirmed facts:

- `Stage2Orchestrator` has `51` direct methods
- `Stage2Finalizer` has `51` direct methods
- `Stage2Finalizer._record_s2_pass_metrics` is `180 LOC`
- `Stage2Orchestrator` still carries three `120+ LOC` methods
- `Stage2ValidationPipeline` still carries three `120+ LOC` methods

Why this closes as `P3-structural`:

- it breaches the workspace comfort line for owner-method pressure
- it keeps Stage 2 proof/persistence changes expensive to audit
- it increases regression risk for the next bounded Stage 2 tranche
- but it does not, by itself, prove wrong accepted artifacts or wrong persisted proof data

Closed reading:

- `confirmed P3-structural`

## 5. Pass 3 - Execution Shape

This audit does not justify:

- a new Stage 2 lane
- queue promotion above the active Stage 4 front
- a rollback of the 2026-04-08 / 2026-04-09 Stage 2 proof work

It does justify the following execution reading:

1. keep the current governing lane as `0_0-stage2-contract-normalization-remediation`
2. if implementation resumes, stay inside the already-declared proof-layer tranche:
   - authoritative `stage_attempts` rationale coverage
   - blank-`attempt_key` hard-warn surfacing
   - `session_decisions.verdict_reason` proof parity
   - `runtime_advisory` / `retry_directives` proof parity
3. use a fresh rerun for closure proof after that tranche rather than reopening older packet-loss claims
4. treat owner-surface reduction as a follow-on structural cleanup, not as the immediate pre-proof blocker

## 6. Severity Verdict

Current static-close verdict:

- `P0`: none confirmed
- `P1`: none confirmed
- `P2`: none newly confirmed from static-only evidence
- `P3`: confirmed

Finding map:

| ID | Closed Severity | Reading |
| --- | --- | --- |
| `F1` | `closed-former-p1` | former authoritative packet overwrite seam is statically closed by shared merge logic plus regression tests |
| `F2` | `not-reopened` | proof-layer sink parity is present in code and guarded by targeted tests; runtime closure still wants a rerun |
| `F3` | `P3-structural` | Stage 2 owner pressure remains above the workspace comfort line (`51` direct methods on both main owners; one `180 LOC` method) |

Historical note:

- the 2026-04-06 Golden survey's `P1/P2/P3` findings remain valid historical runtime evidence for that project/run
- this 2026-04-09 static audit does not re-confirm those runtime findings against current code as still-live defects

## 7. Queue Consequence

Queue-safe consequence:

- no new Stage 2 execution SSOT
- no roadmap reorder
- keep `docs/temp/execution-roadmap.md` authoritative for Stage 2 ordering

Current Stage 2 reading after this audit:

- Stage 2 residual lane stays active at `priority 4`
- Stage 2 partial-fix lane stays below it at `priority 8`
- Stage 2 readiness parent stays blocked at `priority 14`
- the next plausible Stage 2 coding step remains proof-layer hardening, not packet-loss repair revival

## 8. 3-Pass Audit Record

Pass 1, structure and scope:

- bounded the audit to static Stage 2 owner surfaces plus proof owners
- kept runtime reruns, artifact mutation, and queue mutation out of scope
- recorded explicit side-effect categories instead of silently skipping them

Pass 2, evidence and consistency:

- triangulated severity claims with live code, AST inventory, tests, and prior Stage 2 SSOT/roadmap lineage
- rechecked the older 2026-04-06 `P1` seam against current merge-helper call sites and tests
- rechecked the current proof-layer residual against current analyzer/audit-service code and tests

Pass 3, execution and readability:

- kept the output findings-first
- made the queue consequence explicit
- separated `live defect` from `structural hotspot`
- avoided over-promoting runtime-only historical findings into new static severity claims

Confidence rationale:

- evidence classes used: `A + B + C + E`
- no unresolved contradiction on the final severity close
- the main thing preventing a higher score is that this was intentionally `static-only` and therefore cannot close runtime truth on its own
