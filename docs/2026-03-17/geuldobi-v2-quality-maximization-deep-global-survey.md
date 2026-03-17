# Geuldobi V2 Quality Maximization Deep Global Survey

Date: 2026-03-17
Status: final
Canonical Path: `docs/2026-03-17/geuldobi-v2-quality-maximization-deep-global-survey.md`
Related Evidence Manifest: `docs/2026-03-17/geuldobi-v2-quality-maximization-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: lane1~3 code/tests/docs edits, temp execution-mirror deletions, runtime log, and geuldobi-v2 survey bundle docs/evidence; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent
- produce the merged repo-wide deep survey bundle for the `geuldobi-v2-quality-maximization` cycle
- turn the triaged `roadmap-v2` themes into one live-code-governed process picture
- stay in survey-only mode and stop before execution realization
- distinguish already-landed lane1~3 work from still-open cross-cut quality risks

## 2. Scope Lock
- included paths:
  - `main_a.py`, `main.js`
  - `modules/`
  - `config/`
  - `scripts/`
  - `tests/`
  - `UI/`
  - `geuldobi-desktop/`
  - runtime artifact/log surfaces under `projects/` where artifact truth or metadata truth mattered
- excluded paths:
  - narrative-production content review by `work_id`
  - direct code patching
  - DB/config mutation
  - new execution-queue activation in this turn
  - broad archival or cache directories
- change-lock or canary constraints:
  - survey-only
  - no code edits
  - no temp execution queue activation
  - no fresh live run in this merged survey turn
- baseline docs read:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-prompt-pack.md`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t02-runtime-spine-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t03-upstream-design-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t06-persistence-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t10-merge-watchlist.txt`

## 3. Coverage Matrix
- macro views covered:
  - repo topology and entrypoint authority (`T01`)
  - runtime/control-flow spine and control-plane seams (`T02`)
  - stage-pipeline macro lineage from Stage 2 through Stage 4 (`T03`, `T04`, `T05`)
- micro views covered:
  - upstream intent-loss hotspots (`T03`)
  - CW input/truncation hotspots (`T04`)
  - Director/gate/retry hotspots (`T05`)
  - persistence and final-authority hotspots (`T06`)
  - operator-surface hotspots (`T07`)
  - validation/tooling hotspots (`T08`)
  - config/prompt/threshold drift hotspots (`T09`)
- cross-cut views covered:
  - context provenance and budget accounting
  - repair/gate semantics durability
  - prompt/config authority drift
  - runtime/control-plane authority hygiene
  - proof-matrix and telemetry adequacy
- operational views covered:
  - regression/tooling contract review (`T08`)
  - persistence/operator-surface linkage (`T06`, `T07`)
  - config/routing/cost telemetry review (`T09`)
- deferred surfaces:
  - fresh live-run bundle
  - new execution SSOT creation for cross-cut clusters
  - new temp roadmap activation

## 4. Macro View
- topology:
  - the active runtime stack is `desktop/app shell -> bridge/control plane -> process runner -> main_a.py -> stage pipeline`
  - the repo still contains compatibility or maintenance-adjacent lanes such as root `main.js`, `lite_mode/`, `test_mode/`, and direct root utilities
- authority map:
  - live code is authoritative
  - `docs/roadmap-v2.md` is seed-only
  - lane1~3 execution docs are prior realized subset references, not current repo-wide bundle controllers
  - prompt/config authority is currently split across YAML, fallback literals, and some legacy inline constants
- runtime/control-flow spine:
  - public control-plane behavior is effectively Mode-B-centered through bridge/process-runner paths
  - early boot failures write to workspace-level roots, while later runtime events write to project-local sinks
  - Stage 2 and Stage 3 still perform critical context compression and handoff before Stage 4 semantics begin
- subsystem boundaries:
  - strong:
    - persistence sinks vs generation agents
    - desktop renderer vs backend control plane
  - blurred:
    - prompt/config authority
    - final-authority versus snapshot/surface authority
    - validation/gate semantics versus retry routing

## 5. Micro View
- hotspot ranking:
  1. `modules/core/stage4_interview_round.py`
  2. `modules/core/stage4_context_builder.py`
  3. `modules/core/stage2_preflight.py` + `modules/core/stage3_orchestrator.py`
  4. `modules/core/stage4_post_processor.py` + `modules/core/db_manager.py`
  5. `modules/domain/agents/director_ensemble.py` + `modules/domain/agents/director_prompts.py`
  6. `modules/api/process_runner.py` + `main_a.py`
  7. `modules/core/quality_dashboard.py` + `modules/core/pass_rate_monitor.py` + `modules/api/bridge_server.py`
  8. `config/settings/validation.yaml`, `config/settings.json`, `config/prompts/director.yaml`, `config/models.yaml`
- high-risk files/modules:
  - `stage4_interview_round.py`: gate/retry/persistence fan-in and fan-out
  - `stage4_context_builder.py`: context tiering plus literal trim policy
  - `stage2_preflight.py` and `stage3_orchestrator.py`: upstream intent-loss and budget drift
  - `stage4_post_processor.py` / `db_manager.py`: durable truth versus snapshot truth
  - `process_runner.py` / `main_a.py`: control-plane prompt contract and bootstrap split
  - `director_prompts.py` / YAML prompt maps: stale authority risk
- dominant mutable state surfaces:
  - `stage_rejection_history`
  - `_last_retry_budget_axes`, `_last_strategy_budget`, `_last_strategy_count`
  - `world_state`, `fact_ledger`, `state_tracker` singletons
  - dashboard/pass-rate in-memory histories
  - process-runner prompt state and failure-phase memory
- dense side-effect clusters:
  - Stage 4 final-authority and metadata sinks
  - desktop/backend control-plane logs and provenance outputs
  - project-local versus workspace-level boot/runtime log roots
  - config fallback and prompt-loader cache usage

## 6. Cross-Cut Integrity Matrix
- companion doc:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-cross-cut-integrity-matrix.md`
- merged summary:
  - observability and persistence are no longer absent, but they are unevenly authoritative
  - operator surfaces remain thinner than raw sink richness
  - contracts/config are the strongest repo-wide drift source in the current bundle
  - proof and telemetry paths exist, but the cheapest repeatable proof matrix is still under-specified

## 7. Operational and Regression View
- tests:
  - worker evidence used static code + targeted test inventory review, not a fresh full test run
  - existing targeted lane1~3 tests make already-landed semantics credible at code level
  - repo-wide proof for `keep` themes is still more uneven than proof for lane1~3 regressions
- smoke/canary:
  - highest proof lanes remain expensive and mutation-heavy
  - `full_canary_proof` is not yet a cheap repeatable default
  - `run_pytest_lowmem.py` is operationally important but not yet embedded in the shared validation-tier contract
- repair tooling:
  - retry, patch, regenerate, and proof tooling exist
  - governance-prescribed doc/queue validators remain more governance-backed than strongly regression-backed
- read-only vs mutation-heavy boundaries:
  - this merged turn stayed read-only for code/runtime
  - evidence came from worker docs, live code reads, and artifact/log inspection
  - action-bearing clusters are identifiable without yet opening realization

## 8. Contradiction and Uncertainty Ledger
- companion doc:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-uncertainty-contradiction-ledger.md`
- contradictions closed:
  - prompt/config authority drift is real and bounded, not speculative
  - raw sink richness versus thin operator surfaces is a current-state gap, not a hypothetical
  - final Stage 4 truth and `director_selections` snapshot truth are not the same authority surface
  - worker coverage is complete for `T01` to `T09`, so the bundle is synthesis-ready
- contradictions still open:
  - none are left unresolved at the level needed to block merged survey save
- uncertainty items:
  - whether non-test live runs already emit strong Pack-B/Pack-E durability across all target cases
  - whether Lite/Test runtime lanes are supported lanes or compatibility residue
  - whether the current thin renderer is intentional or simply lagging backend observability
- confidence caps still in effect:
  - no active hard cap below 95 remains
  - the main remaining limits affect future execution planning, not survey save itself

## 9. Severity and Action Map
- `P0` items:
  - none proven in this survey bundle
- `P1` items:
  - `context-provenance-and-budget-contract`
    - upstream intent survival and final context-budget accounting remain under-instrumented and partially contract-less
  - `gate-repair-observability-chain`
    - lane2/3 semantics exist, but durable/operator-visible consumption still appears verdict-centric
  - `prompt-config-authority-hygiene`
    - YAML, JSON, fallback literals, and legacy inline prompt constants disagree in live authority terms
  - `runtime-control-plane-authority-hygiene`
    - Mode-B public path, compatibility lanes, and maintenance-path exceptions are not yet one clean authority story
- action-bearing areas:
  - not opened as execution docs in this turn
  - current bundle instead identifies candidate clusters for a follow-on execution-doc cycle
- areas with `no-execution-doc-required`:
  - none of the `P1` clusters qualify for `no-execution-doc-required`
  - already-landed lane1~3 items do not need new execution docs in this bundle because their canonical execution docs already exist

## 10. Execution SSOT Mapping

| Area | Classification | Canonical Execution Doc | Notes |
| --- | --- | --- | --- |
| `stage-pipeline-cw-context-architecture` | existing-realized | `docs/2026-03-17/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md` | existing realized subset for CW context tiering and work-focus delivery |
| `stage-pipeline-director-gate-semantics` | existing-realized | `docs/2026-03-17/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md` | existing realized subset for Director semantic split |
| `stage-pipeline-repair-retry-architecture` | existing-realized | `docs/2026-03-17/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md` | existing realized subset for PASS_WITH_FIX narrowing and retry-budget surfacing |
| `context-provenance-and-budget-contract` | candidate-action-bearing | none opened in this turn | extends beyond lane1 because it now spans Stage 2/3/4 provenance and contract drift |
| `gate-repair-observability-chain` | candidate-action-bearing | none opened in this turn | extends beyond lane2/3 because it now spans persistence and operator-surface truth |
| `runtime-control-plane-authority-hygiene` | candidate-action-bearing | none opened in this turn | repo-wide authority hygiene, not yet reduced to one execution-ready slice |
| `verification-proof-matrix` | candidate-action-bearing | none opened in this turn | proof-path and tooling-contract cluster remains survey-derived only |
| `cost-and-long-run-telemetry-contract` | candidate-action-bearing | none opened in this turn | Pack D/E telemetry cluster needs a dedicated execution-doc pass later |

## 11. Single SSOT Roadmap Lineage
- canonical roadmap:
  - prior realized subset reference: `docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md`
- temp roadmap mirror:
  - none active in the current survey-only bundle
- execution order basis:
  - if a follow-on execution-doc cycle opens two or more new candidate-action-bearing areas, exactly one new canonical roadmap must govern them
- lane or phase structure:
  - existing realized lineage remains lane1 -> lane2 -> lane3
  - current repo-wide bundle stops at synthesis and does not activate a new queue

## 12. Confidence Summary
- estimated score: `95/100`
- score rationale:
  - scope and path coverage completeness: `19/20`
  - macro + micro + cross-cut + operational completeness: `15/15`
  - side-effect and durability coverage: `15/15`
  - evidence triangulation quality: `14/15`
  - contradiction closure quality: `8/10`
  - uncertainty ledger quality: `10/10`
  - execution-SSOT mapping and single-roadmap coherence: `9/10`
  - validation and proof artifacts: `5/5`
- closed gaps:
  - worker coverage is complete across `T01` to `T09`
  - major contradictions are bounded and converted into explicit findings rather than hidden prose drift
  - no temp-queue ambiguity remains for this survey-only bundle
- remaining gaps:
  - no fresh live-run evidence in this merged turn
  - no new execution-doc cycle has been opened yet for the new cross-cut clusters
- final statement:
  - this merged survey is trustworthy enough at the 95% threshold to govern a follow-on execution-doc cycle
  - it is not itself an execution authorization for code changes
