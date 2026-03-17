# Stage Pipeline Lane 2 Director Gate Semantics and Prompt Austerity Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md`
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Resume Drift Summary: `1 commit since baseline; dirty lane-1 closure surfaces plus runtime log; hotspots: docs/2026-03-17/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md, docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md, modules/core/context_advisor.py, modules/core/stage4_context_builder.py, tests/test_context_advisor.py, tests/test_stage4_context_builder.py, projects/test_project/logs/episode_production.jsonl`
Source Survey Docs:
- `docs/2026-03-17/stage-pipeline-process-integrity-global-survey.md`
- `docs/2026-03-17/quality-gate-semantics-outline.md`
- `docs/2026-03-17/director-prompt-austerity-outline.md`
Evidence Artifacts:
- `docs/2026-03-17/stage-pipeline-process-integrity-evidence-manifest.md`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- realize the bounded survey finding that Director judgment quality is currently limited more by hierarchy blur than by missing evidence
- separate decision-critical meaning from advisory, score, and reference bulk before further retry-policy work
- establish a slimmer and semantically cleaner Director input contract for Stage 4

## 2. Baseline Facts
- Director already receives stable story context, candidate manuscripts, validation results, and a thick caller-built `mandatory_context`
- live code overload is semantic, not evidentiary:
  - verdict, score, fix scope, advisory, and downstream gates partially overlap in meaning
- caller-side `mandatory_context` mixes truth, operational memos, Python warnings, stats, and reference-only notes inside one authority band
- bounded survey classified this lane as `P1-B` and placed it after CW context architecture because Director-side slimming benefits from cleaner upstream ranking

## 3. Scope
Included:
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/director_prompts.py`
- Director-side semantic fields and prompt assembly boundaries
- targeted tests for verdict transitions, advisory behavior, and Director prompt inputs

Excluded:
- CW mandatory-context ranking except where lane 1 output becomes a dependency
- PASS_WITH_FIX narrowing and retry round policy except where semantics must align
- persistence-layer changes and bridge/dashboard execution unless semantics logging later requires them

## 4. Pass 1. Inventory Summary
- stable context already exists as a usable primary decision substrate
- candidate evidence already exists in `validation_results` and candidate-specific warnings
- heavy duplication currently happens in caller-built `mandatory_context`
- verdict transitions already pass through:
  - Director primary judgment
  - quality floor
  - post-select conflict checks
  - PASS_WITH_FIX re-audit

## 5. Pass 2. Semantic Classification
- Class A: decision core
  - blueprint, story context, previous ending, previous manuscript text, must-hold truth and continuity
- Class B: candidate evidence
  - candidate manuscripts, candidate warnings, structured validation evidence
- Class C: reference appendix and soft authority
  - trend stats, diversity notes, scene similarity, preflight bulk, work review memos, broad advisory history

## 6. Side-Effect Map
- file writes / artifacts:
  - Stage 4 verdict records, runtime summaries, and any saved process traces that expose judgment semantics
- DB / schema / transaction boundaries:
  - not-applicable for primary lane intent; schema change is out of scope
- JSONL / log / audit sinks:
  - verdict and gate-transition traces may gain clearer semantic fields
- console / UI / operator output:
  - future dashboard or bridge consumers may reflect clearer gate naming, but that is secondary in this lane
- rollback / recovery / retry:
  - retry entry conditions and patch/re-audit interpretation depend on cleaned semantics
- cache / global state:
  - Director prompt assembly buffers and Stage 4 in-memory verdict state
- bootstrap fallback / config-env mutation:
  - none expected

## 7. Realization Architecture
- split Director input into three packs:
  - Decision Core
  - Candidate Evidence
  - Reference Appendix
- split semantic fields so result, reason, repair width, and advisory authority do not share one overloaded channel
- treat score as a quality index first and explicit floor failure as a separate gate event
- keep Director sovereignty intact; Python organizes, annotates, and routes but does not become the quality judge

## 8. Execution Tranches
1. semantic split foundation
   - establish `director_verdict`, `final_verdict`, `gate_basis`, and `repair_scope`
   - freeze minimal meaning before behavioral tuning
2. Director prompt austerity
   - deduplicate caller-built `mandatory_context`
   - define Decision Core, Candidate Evidence, and Reference Appendix
3. advisory-state isolation
   - classify advisory as `reference_only`, `decision_support`, or `escalated`
   - make round-0 slim-first and retry-only expansion explicit where needed

## 9. Acceptance Criteria
- Director primary judgment and final terminal outcome are distinguishable in runtime semantics
- final gate reason is represented through an explicit `gate_basis`-style contract
- `repair_scope` is no longer overloaded as both verdict meaning and routing explanation
- Director round-0 prompt is slimmer and more hierarchical than the current mixed `mandatory_context`
- reference appendix content is clearly separated from decision-core content

## 10. Verification Plan
- `python -m pytest tests/test_stage4_interview_round.py -k "advisory or conflict or reduced_strategy_budget or full_strategy_budget or post_select_conflict"`
- `python -m pytest tests/test_stage4_orchestrator.py -k "stage4_to_3_feedback or director"`
- `python -m pytest tests/test_pre_director_submodules.py -q`
- `python scripts/ops_validator.py`
- bounded prompt inspection on round 0 and retry fixtures to confirm Decision Core remains ahead of Reference Appendix

## 11. Guardrails
- do not fold lane 3 retry-budget execution into this lane except for semantics alignment points
- do not promote advisory into hidden hard-gate authority without explicit semantic state
- keep Director sovereignty visible; this lane is about hierarchy and meaning, not replacing Director judgment
- avoid premature dashboard/schema expansion before semantic contracts stabilize

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - remove `docs/temp/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md` only after implementation closes and the roadmap marks this item completed
- roadmap dependency:
  - `docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note
- realization outcome:
  - `modules/domain/agents/director_ensemble.py` now returns and logs explicit `director_verdict`, `final_verdict`, `gate_basis`, and `repair_scope` fields and accepts split Director prompt packs instead of relying on one overloaded context channel
  - `modules/core/stage4_interview_round.py` now assembles Director input as `Decision Core -> Candidate Evidence -> Reference Appendix`, normalizes post-select and re-audit gate transitions through the split semantics contract, and persists gate semantics into selection metadata and episode logs
  - `config/prompts/director.yaml` and `modules/domain/agents/director_prompts.py` now keep stable and fallback Director prompt paths aligned on the three-pack input contract
- verification evidence:
  - `python -m pytest tests/test_stage4_interview_round.py -k "Lane2DirectorSemantics or director_mandatory_context or save_director_selection_persists_verdict_metadata or append_episode_log" -q`
  - `python -m pytest tests/test_director_modules.py -k "Lane2DirectorEnsembleSemantics or DirectorEnsembleCaching or ensemble_all_short_manuscripts_reject" -q`
  - `python -m pytest tests/test_stage4_orchestrator.py -k "stage4_to_3_feedback or director" -q`
  - `python -m pytest tests/test_pre_director_submodules.py -q`
  - `python scripts/ops_validator.py`
- residual risk:
  - lane 3 retry-contract tightening is still pending; `PASS_WITH_FIX` budget policy and Fix Pack behavior may still refine downstream `gate_basis` consumers, but lane 2 semantic separation and prompt-pack hierarchy are now live and independently validated
