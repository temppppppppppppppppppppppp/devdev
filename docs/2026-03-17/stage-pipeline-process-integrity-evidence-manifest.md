# Stage Pipeline Process Integrity Evidence Manifest

Date: 2026-03-17
Status: final
Topic: `stage-pipeline-process-integrity`
Related Survey Docs:
- `docs/2026-03-17/stage-pipeline-process-integrity-global-survey.md`
Related Execution Docs:
- none in this survey-only bundle

## 1. Summary
- evidence scope: bounded global survey evidence for Stage 2/3/4 process integrity, Director/CW authority flow, gate semantics, repair/retry semantics, persistence, and process observability
- freshness note: all live-code readings and pytest shards in this manifest were collected from the current workspace on 2026-03-17 against `Baseline Commit: 100ecd03557e1b8c7a3544b5285fc80e7105050c`
- known gaps:
  - no fresh live run or canary execution in this order
  - no broad UI/desktop full sweep in this bounded survey
  - no execution SSOT docs opened in this survey-only turn

## 2. Artifact Index

| Artifact | Type | Acquired By | Freshness | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
| `docs/2026-03-17/stage-pipeline-process-integrity-global-survey-order-outline.md` | planning note | manual doc read | fresh | survey framing | reusable order wording and bounded scope lock |
| `docs/2026-03-17/cw-context-delivery-optimization-outline.md` | planning note | manual doc read | fresh | survey hypothesis seed | context timing/form/authority seed only; not authority |
| `docs/2026-03-17/stage4-context-composition-ranking-outline.md` | planning note | manual doc read | fresh | survey hypothesis seed | tiering and work-focus asymmetry seed only |
| `docs/2026-03-17/quality-gate-semantics-outline.md` | planning note | manual doc read | fresh | survey hypothesis seed | verdict/score/advisory semantics seed only |
| `docs/2026-03-17/pass-with-fix-local-repair-contract-outline.md` | planning note | manual doc read | fresh | survey hypothesis seed | local repair contract seed only |
| `docs/2026-03-17/director-prompt-austerity-outline.md` | planning note | manual doc read | fresh | survey hypothesis seed | Director input-channel austerity seed only |
| `docs/2026-03-17/retry-budget-policy-outline.md` | planning note | manual doc read | fresh | survey hypothesis seed | retry budget separation seed only |
| `modules/core/stage2_preflight.py` | live code | UTF-8 code read | fresh | macro + micro + cross-cut | Stage 2 retrieval planning, work focus, Stage3->2 reverse feedback fallback |
| `modules/core/stage3_orchestrator.py` | live code | UTF-8 code read | fresh | macro + persistence | Stage 3 reject history persistence into `stage_rejection_history` and observability surfaces |
| `modules/core/stage4_context_builder.py` | live code | UTF-8 code read | fresh | macro + micro + context architecture | Stage 4 mandatory-context accumulation, retrieval planning, coverage warnings, retrieval observations |
| `modules/core/context_advisor.py` | live code | UTF-8 code read | fresh | retrieval/ranking | Stage4/Director retrieval slot planning and work-focus slot generation |
| `modules/core/stage4_interview_round.py` | live code | UTF-8 code read + `rg` | fresh | macro + micro + gate/retry | Director MC assembly, advisory suppression, verdict transitions, PASS_WITH_FIX, retry routing, adaptive guidance |
| `modules/domain/agents/director_ensemble.py` | live code | UTF-8 code read | fresh | authority + prompt path | stable/variable prompt split, mandatory-context append, cached Director path |
| `modules/domain/agents/chief_writer.py` | live code | UTF-8 code read | fresh | retry/routing | strategy budget handling and reduced/full ensemble selection |
| `modules/core/adaptive_retry.py` | live code | UTF-8 code read + `rg` | fresh | retry guidance | guidance-only retry side layer, ultimate recommendations, injection prompt surfaces |
| `modules/core/stage4_post_processor.py` | live code | UTF-8 code read | fresh | persistence + carry-over | state log, bible, world state, fact ledger durability for relationship and pressure surfaces |
| `modules/core/world_state.py` | live code | UTF-8 code read | fresh | persistence consumer | active pressure vector consumer and known state holder |
| `modules/validation/continuity_validator.py` | live code | UTF-8 code read | fresh | continuity consumer | threat/pressure carry-over warning surface in opening continuity checks |
| `modules/core/quality_dashboard.py` | live code | UTF-8 code read | fresh | observability | validation, retrieval, HUD, coverage, and quality-signal recording surfaces |
| `modules/core/pass_rate_monitor.py` | live code | UTF-8 code read | fresh | observability | patch effectiveness and stage retry metrics surface |
| `modules/api/bridge_server.py` | live code | UTF-8 code read | fresh | operator surface | quality dashboard payload, patch effectiveness, quality signal snapshot, cost summary |
| `tests/test_stage4_context_builder.py` | regression shard | `pytest -q -k "plan_stage4_retrieval or work_slot_summary or active_pressure_vectors"` | fresh | operational confirmation | `2 passed, 52 deselected` |
| `tests/test_stage4_interview_round.py` | regression shard | `pytest -q -k "reduced_strategy_budget or full_strategy_budget or post_select_conflict or advisory"` | fresh | operational confirmation | `11 passed, 74 deselected` |
| `tests/test_stage4_post_processor.py` | regression shard | `pytest -q -k "relationship_changes or active_pressure_vectors"` | fresh | operational confirmation | `2 passed, 44 deselected` |
| `tests/test_stage3_orchestrator.py` | regression shard | `pytest -q -k "rejection_history"` | fresh | operational confirmation | `1 passed, 71 deselected` |
| `tests/test_stage2_preflight.py` | regression shard | `pytest -q -k "stage3_reverse_feedback"` | fresh | operational confirmation | `2 passed, 25 deselected` |
| `tests/test_bridge_quality_summary.py` | regression shard | `pytest -q -k "patch_effectiveness or quality_signal_snapshot"` | fresh | operational confirmation | `2 passed, 9 deselected` |

## 3. Limitations
- this manifest indexes live code and targeted regression evidence only; it does not include a fresh runtime trace bundle
- historical docs were used only as brainstorming seeds or governance references, not as primary authority
- broad desktop/UI surfaces were intentionally excluded by the bounded survey scope and therefore do not appear here
