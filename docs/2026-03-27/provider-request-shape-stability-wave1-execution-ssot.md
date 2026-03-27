# Provider Request-Shape Stability Wave1 Execution SSOT

Date: 2026-03-27
Status: closed
Canonical Path: `docs/2026-03-27/provider-request-shape-stability-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/provider-request-shape-stability-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/router/stage3/stage4/fact/main_a/config surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked dated docs, provider adapter/tests, BI/TR artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `new queue item raised after contaminated system-maturity canary attempt was paused; current priority is code-stability-first before the next clean canary`
Source Survey Docs:
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-opus-deep-dive-audit.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md`
Evidence Artifacts:
- live recheck of `modules/core/llm_generate.py`
- live recheck of `modules/core/llm_router.py`
- live recheck of `modules/core/metrics_collector.py`
- live recheck of `modules/core/providers/__init__.py`
- live recheck of `modules/api/process_runner.py`
- live recheck of `modules/domain/agents/base_agent.py`
- live recheck of `modules/domain/agents/chief_writer.py`
- live recheck of `modules/domain/agents/chief_writer_prompts.py`
- live recheck of `modules/core/stage4_interview_round.py`
- live recheck of `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-canary-contamination-note.md`
- `docs/2026-03-27/provider-request-shape-stability-wave1-execution-closure.md`
- live recheck of `docs/temp/queue-state.json`
Side-Effect Coverage: covered

## 1. Intent

- Realize the next code-stability-priority bundle before the next clean canary cycle.
- Keep the bundle narrowly focused on the two deferred items that most directly improve runtime contract clarity without opening the heavier `_god1_*` or realm/NPC-model work.
- Finish the bundle with one clean, single-process canary cycle rather than trying to salvage the currently contaminated maturity canary attempt.

Why now:
- the current `system-maturity-next-band-wave1` Tranche 2 canary attempt is not closure-ready because two target-mutating canary processes wrote into the same project
- even if that run finished, provider/request-shape work would immediately stale the result
- the user explicitly reprioritized toward code stability first, then canary

## 2. Baseline Facts

- frozen defer order already places these two items ahead of `_god1_*` replacement and `realm authority / NPC technique-model gap` for code-stability-first work
- provider identity/usage normalization still spans multiple owners:
  - router inference in `modules/core/llm_router.py`
  - generate-path backend/family overwrite in `modules/core/llm_generate.py`
  - metrics inference/override behavior in `modules/core/metrics_collector.py`
  - provider export surface in `modules/core/providers/__init__.py`
  - runtime env pass-through in `modules/api/process_runner.py`
  - usage normalization in `modules/domain/agents/base_agent.py`
- writer/context request-shape remains oversized even after partial local bundling:
  - `ChiefWriter.generate_ensemble` currently exposes 37 parameters
  - `ChiefWriter.regenerate_with_feedback` currently exposes 35 parameters
  - `ChiefWriter.patch_with_feedback` currently exposes 34 parameters
  - `build_chief_writer_main_prompt` currently exposes 34 parameters
  - `stage4_interview_round.py` already has `_build_common_writer_kwargs`, but the chain is still large and partly split between dict-bundled and explicit forwarding surfaces
- current canary pause facts:
  - two concurrent `run_stage3_canary.py` processes targeted `projects/canary_0327_stage3_cadence`
  - `stage3_canary_summary.json` remains stale from `2026-03-26`
  - partial fresh artifacts exist for episodes 1 to 3, but the attempt is non-authoritative for closure

## 3. Scope

Included:
- `modules/core/llm_generate.py`
- `modules/core/llm_router.py`
- `modules/core/metrics_collector.py`
- `modules/core/providers/__init__.py`
- `modules/api/process_runner.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_interview_round.py`
- one clean post-bundle canary rerun and its operator note / evidence doc

Excluded:
- `_god1_*` channel replacement
- `realm authority / NPC technique-model gap`
- broad provider migration or new provider introduction
- schema redesign beyond the minimal provider/request-shape contract normalization needed by this bundle
- broad Stage 4 owner-surface cleanup beyond the request-shape chain needed here
- maturity wave closure itself

## 4. Pass 1. Inventory Summary

- active bundle families: 2
  - provider identity / usage normalization
  - writer/context request-shape cleanup
- queue shape after reprioritization:
  - this new execution SSOT enters the temp queue
  - `system-maturity-next-band-wave1` remains queued but no longer first in order
- current runtime pressure:
  - provider identity fields can still drift between router, response object, metrics, and runtime env seams
  - Stage 4 writer request construction already has one bundling shell, which makes this a bounded cleanup rather than a full redesign

## 5. Pass 2. Semantic Classification

- Class A. Provider Contract Normalization
  - align provider identity, backend/family meaning, export surface, and usage capture so operator-visible records stop depending on implicit cross-file inference
- Class B. Request-Shape Stabilization
  - reduce the oversized Stage 4 writer request surface by consolidating what is already partially bundled and making the remaining explicit contracts easier to follow
- Class C. Post-Bundle Runtime Proof
  - rerun one clean canary only after A and B land, using a fresh single-process run as the checkpoint

## 6. Side-Effect Map

- file writes / artifacts:
  - production-source changes in the included provider/runtime and writer/context files
  - canonical execution doc and temp mirror refresh
  - one post-bundle canary evidence note and/or closure note
- DB / schema / transaction boundaries:
  - no schema migration should be opened by this bundle
  - the post-bundle canary may write normal project DB rows through existing pipeline paths
- JSONL / log / audit sinks:
  - provider identity and usage fields may change in runtime logs, metrics, and canary artifacts
  - the clean canary rerun will create new logs and summary artifacts
- console / UI / operator output:
  - provider naming and canary operator output may change slightly
- rollback / recovery / retry:
  - the post-bundle canary is expected to validate retry/usage surfaces, but this bundle should not redesign retry policy
- cache / global state:
  - existing runtime caches may be exercised but should not be redesigned here
- bootstrap fallback / config-env mutation:
  - keep env changes bounded to clarifying existing provider pass-through behavior only

## 7. Realization Architecture

- order inside the bundle:
  1. provider identity / usage normalization
  2. writer/context request-shape cleanup
  3. clean canary rerun
- dependency rule:
  - the clean canary must run after the code changes, not before, because the current target evidence is already contaminated and would be stale after this bundle lands
- shrink-scope rule:
  - prefer contract normalization and boundary clarification over opening new owner splits
  - if a proposed cleanup expands into `_god1_*` replacement or realm/NPC authority work, stop and split it into a later wave
- dirty-worktree rule:
  - before touching any already-dirty included file, re-audit the local diff and confirm the bundle still fits the live workspace

## 8. Execution Tranches

1. Provider Identity / Usage Normalization
   - normalize where provider/backend/family truth comes from
   - keep provider export and runtime env pass-through aligned with the intended live provider surface
   - preserve behavior unless a bounded contract cleanup is already accepted as part of current live code

2. Writer / Context Request-Shape Cleanup
   - consolidate the oversized Stage 4 writer request chain around the existing common-kwargs seam
   - reduce duplicated explicit argument forwarding where it no longer adds clarity
   - do not inflate this into a broad Stage 4 refactor wave

3. Clean Checkpoint Canary
   - run one clean single-process canary on a fresh target after Tranche 1 and 2 land
   - record exact command, target project, summary provenance, and DB truth
   - do not reuse contaminated artifacts from the paused maturity canary attempt

## 9. Acceptance Criteria

- provider tranche
  - provider identity, backend/family meaning, and usage payloads are no longer split across contradictory interpretations in the touched surfaces
  - touched provider/runtime tests or targeted validation pass
- request-shape tranche
  - the main Stage 4 writer request chain is measurably easier to follow and no longer depends on the same degree of large explicit forwarding
  - no touched behavior regresses in targeted tests
- post-bundle canary
  - a single-process fresh canary completes on a clean target
  - canary evidence is generated by the fresh run itself, not copied from stale artifacts
  - provider/runtime/operator evidence is coherent enough to use as the next checkpoint

## 10. Verification Plan

- targeted validation hooks
  - low-memory pytest shards for touched provider/runtime and Stage 4 surfaces only
  - targeted compile checks on touched production files
  - `python scripts/check_utf8_hygiene.py <touched files> docs/2026-03-27/provider-request-shape-stability-wave1-execution-ssot.md docs/temp/provider-request-shape-stability-wave1-execution-ssot.md`
  - `python scripts/sync_temp_queue_state.py`
  - `python scripts/ops_validator.py --strict`
- post-bundle runtime proof
  - run exactly one clean canary command against a fresh target
  - verify summary provenance, DB truth, and operator evidence before any closure claim

## 11. Guardrails

- Do not open `_god1_*` replacement work in this bundle.
- Do not open realm/NPC technique authority work in this bundle.
- Do not redesign the provider stack beyond the minimal contract normalization needed here.
- Do not salvage or cite the contaminated `canary_0327_stage3_cadence` run as the checkpoint canary for this bundle.
- Do not start implementation from this SSOT without a fresh 3-pass re-audit against the live workspace.

## 12. Temp Queue Notes

- temp status: closed
- cleanup condition: satisfied after closure audit, temp mirror removal, and queue-state refresh
- roadmap dependency: this item requires the aggregate roadmap because `system-maturity-next-band-wave1` remains queued at the same time

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1. Structure and Scope
- kept the new execution SSOT bounded to exactly two deferred items plus the post-bundle canary
- kept `system-maturity` as a separate queued item rather than silently merging the waves
- PASS

Pass 2. Evidence and Consistency
- rechecked the live provider/runtime seams
- rechecked the live Stage 4 request-shape chain
- rechecked the contaminated canary state and confirmed that a clean rerun belongs after this bundle
- PASS

Pass 3. Execution Readiness
- queue order is explicit
- guardrails prevent wave creep into `_god1_*` and realm/NPC work
- the clean canary now has an explicit place in the bundle instead of floating as an unsourced next step
- PASS

## 15. Realization Record

### Tranche 1: Provider Identity / Usage Normalization
- `modules/core/llm_router.py`: added `_infer_provider_name_safe()` (standalone module-level prefix matcher) and `resolve_provider_identity()` (single source of truth for `(provider, backend, family)` tuple)
- `modules/core/llm_router.py`: refactored `LLMProviderRouter.infer_provider_name()` to delegate to `_infer_provider_name_safe()`
- `modules/core/metrics_collector.py`: removed duplicated `_infer_provider_identity()` (19 lines), replaced with `from modules.core.llm_router import resolve_provider_identity as _infer_provider_identity`
- No changes needed in `llm_generate.py`, `providers/__init__.py`, `process_runner.py`, `base_agent.py`

### Tranche 2: Writer / Context Request-Shape Cleanup
- `modules/domain/agents/chief_writer.py`: simplified `regenerate_with_feedback` from 35 explicit params to 3 (`previous_attempt`, `attempt_number`, `**writer_kwargs`), removing ~45 lines of boilerplate forwarding
- `modules/domain/agents/chief_writer.py`: simplified `patch_with_feedback` from 34 explicit params to 4 (`original_manuscript`, `previous_attempt`, `attempt_number`, `**writer_kwargs`), removing ~30 lines of boilerplate forwarding
- `generate_ensemble` signature unchanged (leaf method, keeps full explicit contract)
- No changes needed in `chief_writer_prompts.py`, `stage4_interview_round.py`

### Tranche 3: Clean Canary
- Command: `python scripts/run_stage3_canary.py full --source-project 코덱스_테스트 --target-project canary_0327_prs_wave1 --from-ep 1 --target-ep 3 --force`
- Target: `projects/canary_0327_prs_wave1` (fresh, single-process)
- Results: 3 blueprints, all first-attempt PASS (scores: 92, 96, 88)
- Hard gates: PASS (0 errors, 0 warnings)
- Summary provenance: `projects/canary_0327_prs_wave1/logs/stage3_canary_summary.json`
- DB truth: session-scoped evidence for `session_id=20260327_124530` shows 3 Stage 3 attempts and 3 blueprint rows for episodes 1 to 3; the project DB retains older historical `stage_attempts` rows outside this canary session
- Contaminated older canary artifacts (`canary_0327_stage3_cadence`) were NOT used

### Validation
- 8 production files: compile clean
- 563 tests passed across 7 pytest shards (llm_router 41, CW patch/regen 10, stage4_interview 219, carryover 4, models+bridge 79, stage3/4 181, blocking_validator 29)
- `sync_temp_queue_state`: PASS (2 items, aggregate mode)
- `ops_validator --strict`: PASS (0 errors, 0 warnings)

## 16. Closure Record

- closure note: `docs/2026-03-27/provider-request-shape-stability-wave1-execution-closure.md`
- acceptance criteria satisfied across the provider tranche, request-shape tranche, and clean canary tranche
- residual scope intentionally left out of this wave:
  - `_god1_*` replacement
  - `realm authority / NPC technique-model gap`
  - broader provider redesign beyond the landed normalization seam
- next queue item remains `system-maturity-next-band-wave1`

## 17. Confidence

Estimated confidence: 97%
