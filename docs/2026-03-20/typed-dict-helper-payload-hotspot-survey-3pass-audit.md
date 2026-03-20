# TypedDict Helper Payload Hotspot Survey

Date: 2026-03-20
Status: completed
Canonical Path: `docs/2026-03-20/typed-dict-helper-payload-hotspot-survey-3pass-audit.md`
Related Re-Audit: `docs/2026-03-20/typed-dict-helper-payload-live-reaudit-3pass-audit.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: ongoing stage/smoke/doc/project churn, low-trust intake bundle, prior closed decomposition tranche`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose
- Identify the smallest high-ROI helper payload surfaces for first-wave `TypedDict` introduction.

## 2. Hotspot Summary

### 2.1 Stage2Finalizer
Primary candidates:
- `modules/core/stage2_finalizer.py:_prepare_stage2_pass_arc_for_persistence`
- `modules/core/stage2_finalizer.py:_finalize_stage2_pass_persistence_and_tail`
- `modules/core/stage2_finalizer.py:_run_stage2_pass_with_fix_loop`

### 2.2 Stage2Orchestrator
Primary candidates:
- `modules/core/stage2_orchestrator.py:_bootstrap_stage2_arc_pipeline`
- `modules/core/stage2_orchestrator.py:_run_stage2_batch_enrichment`
- `modules/core/stage2_orchestrator.py:_handle_stage2_finalize_transition`
- `modules/core/stage2_orchestrator.py:_handle_stage2_arc_failure`

### 2.3 Stage4ContextBuilder
Primary candidates:
- `modules/core/stage4_context_builder.py:_resolve_work_retrieval_focus`
- `modules/core/stage4_context_builder.py:_build_tier0_mandatory_sections`
- `modules/core/stage4_context_builder.py:_collect_stage4_retrieval_context`
- `modules/core/stage4_context_builder.py:_compose_context_with_retrieval_coverage`
- `modules/core/stage4_context_builder.py:_build_tier12_auxiliary_sections`

## 3. Exclusions
- `stage4_interview_round.py`
  - too policy-coupled for the first `TypedDict` tranche
- raw DB rows and audit payloads
  - too broad; likely to mix with persistence policy
- raw blueprint/manuscript payloads
  - still too shape-fluid and closer to LLM contract than coordinator contract

## 4. Queue Decision
- open `3` execution SSOTs
- create one aggregate roadmap
- mirror only those `3` items plus the roadmap into `docs/temp/`

## 5. Confidence
- pass 1:
  - helper inventory rechecked
- pass 2:
  - exclusions trimmed to keep blast radius bounded
- pass 3:
  - queue size and roadmap need revalidated
- estimated confidence:
  - `0.96`
