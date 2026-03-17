# Geuldobi V2 Gate Repair Observability Chain Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/geuldobi-v2-gate-repair-observability-chain-execution-ssot.md`
Temp Mirror Path: `docs/temp/geuldobi-v2-gate-repair-observability-chain-execution-ssot.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: lane1~3 code/tests/docs edits, temp mirror deletions, runtime log, survey bundle docs/evidence, and unrelated local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; gate/repair semantics now survive through durable sinks, dashboard/bridge summaries, and proof tooling without reopening lane2/3 judgment authority`
Source Survey Docs:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-deep-global-survey.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-cross-cut-integrity-matrix.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-cluster-compression.md`
Evidence Artifacts:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t06-persistence-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `95%`

## 1. Intent
- carry lane2/3 semantics all the way from raw Stage 4 sinks to durable metadata and operator-visible surfaces
- stop downstream consumers from collapsing rich repair/gate truth back to only `final_verdict` or `final_score`
- normalize the cheapest repeatable proof path for gate/repair durability without opening a separate proof-only SSOT

## 2. Baseline Facts
- `T05` found `director_verdict`, `gate_basis`, `repair_scope`, `retry_budget_axes`, and `fix_pack` semantics in the live lane2/3 code path
- `T06` found that final Stage 4 truth can diverge from snapshot or selection surfaces
- `T07` found operator-facing surfaces thinner than the backend payloads and raw sinks
- `T08` found proof tooling exists, but the cheapest repeatable validation path for several keep-themes is still unclear

## 3. Scope
Included:
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/db_manager.py`
- `modules/core/quality_dashboard.py`
- `modules/core/pass_rate_monitor.py`
- `modules/api/bridge_server.py`
- operator-facing or summary surfaces that consume Stage 4 verdict/repair metadata

Excluded:
- core lane2 verdict semantics redesign
- core lane3 `PASS_WITH_FIX` eligibility redesign
- broad desktop visual redesign unrelated to richer semantic projection
- global prompt/config authority cleanup outside fields needed for this chain

## 4. Pass 1. Inventory Summary
- main hotspots:
  - gate and retry truth production in Stage 4
  - persistence of final-authority metadata
  - dashboard and bridge projection of that metadata
- main mutable state:
  - `retry_budget_axes`
  - `fix_pack`
  - `gate_basis`
  - `repair_scope`
  - final versus snapshot summary payloads
- primary risk:
  - correct lane2/3 semantics exist but are not the semantics most downstream readers actually consume

## 5. Pass 2. Semantic Classification
- Class A: raw truth emitters
  - Stage 4 code paths that already know the full gate/repair decision
- Class B: durable truth surfaces
  - DB rows, JSONL logs, and artifact summaries that should persist the same meaning
- Class C: operator projection surfaces
  - dashboard, bridge, desktop, and summary payloads that should expose enough of the durable truth to avoid verdict collapse
- Class D: proof surfaces
  - tests and low-cost validation paths that can confirm the chain stays coherent

## 6. Side-Effect Map
- file writes / artifacts:
  - episode artifacts and sidecar summaries that capture verdict/repair metadata
- DB / schema / transaction boundaries:
  - Stage 4 post-processing and metadata persistence may need richer schema or JSON fields
- JSONL / log / audit sinks:
  - JSONL and audit logs must retain structured semantics instead of flattened verdict summaries
- console / UI / operator output:
  - bridge or dashboard surfaces may need richer bounded fields for repair and retry semantics
- rollback / recovery / retry:
  - retries must reuse the same truth source rather than reconstructing semantics later
- cache / global state:
  - pass-rate or dashboard caches must not discard `gate_basis`, `repair_scope`, or `fix_pack` too early
- bootstrap fallback / config-env mutation:
  - not a primary surface, except where summary fields are conditionally enabled or hidden

## 7. Realization Architecture
- define one durable Stage 4 truth contract that names final-authority fields and snapshot-only fields separately
- update sink and surface adapters so they consume the durable contract instead of rolling their own verdict collapse
- include a bounded proof pack in this lane
  - minimum proof targets:
    - durable `fix_pack` survival
    - operator-visible `repair_scope` survival
    - final-authority versus snapshot separation
    - retry-budget visibility where already emitted

## 8. Execution Tranches
1. define the durable truth contract and final-authority versus snapshot boundary
2. wire raw Stage 4 semantics through persistence and summary sinks
3. expose bounded repair/gate truth on operator surfaces without flooding them
4. add a low-cost proof matrix for this chain and fold it into normal validation paths

## 9. Acceptance Criteria
- downstream durable sinks preserve `gate_basis`, `repair_scope`, and `fix_pack` where they are already known upstream
- operator surfaces stop implying that terminal verdict alone is the whole Stage 4 truth
- snapshot surfaces are explicitly non-final where applicable
- a repeatable low-memory verification path exists for the gate/repair observability chain

## 10. Verification Plan
- targeted tests for persistence and summary projection of lane2/3 fields
- targeted tests for bridge/dashboard payloads where applicable
- low-memory pytest shards for `stage4_interview_round`, persistence modules, and operator-surface consumers
- post-implementation evidence check that compares one raw sink, one durable sink, and one operator-visible surface

## 11. Guardrails
- do not redesign Director sovereignty in this lane
- do not broaden `PASS_WITH_FIX` while improving observability
- do not mistake snapshot summaries for final-authority truth
- do not solve proof-path gaps by requiring expensive full canary runs for every iteration

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - completed on 2026-03-17; remove the temp mirror after canonical closure, roadmap update, and queue validation
- roadmap dependency:
  - phase 2 of `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note
- realization outcome:
  - `modules/core/stage4_interview_round.py` now persists `director_verdict`, `gate_basis`, `repair_scope`, `fix_pack`, and `retry_budget_axes` into both session decision logs and `pass_rate_monitor`
  - `modules/core/db_manager.py` and `modules/core/failure_analyzer.py` now expose one bounded Stage 4 gate/repair snapshot plus sink-alignment checks for durable truth survival and metadata gaps
  - `modules/api/bridge_server.py` now projects a bounded `gate_repair_summary` and nests the same payload under `result_summary` so operator surfaces no longer collapse Stage 4 truth to `final_verdict` alone
- verification evidence:
  - `python -m py_compile modules/core/pass_rate_monitor.py modules/core/stage4_interview_round.py modules/core/db_manager.py modules/core/failure_analyzer.py modules/api/bridge_server.py tests/test_stage4_interview_round.py tests/test_failure_analyzer.py tests/test_bridge_quality_summary.py`
  - `python -m pytest tests/test_stage4_interview_round.py -k "record_s4_attempt or pass_with_fix" -q`
  - `python -m pytest tests/test_failure_analyzer.py -k "sink_alignment_summary" -q`
  - `python -m pytest tests/test_bridge_quality_summary.py -k "quality_dashboard_endpoint" -q`
- residual risk:
  - old `pass_rate_monitor.json` fixtures that omit `timestamp` still load through a warning path in `PassRateMonitor`; the authoritative sink-alignment and dashboard proofs now stay correct, but a later hygiene pass can make that compatibility path quieter
