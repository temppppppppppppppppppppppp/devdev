<!-- [참고자료] -->
# Codebase Stagewise Live-Merge Evidence Manifest

Date: 2026-03-15
Status: draft-live-run-pending
Project: `projects/000`
Structured Session Id: `20260315_190609`
Observed Plain Log Token: `20260315_190600`

## 1. Runtime Evidence
- plain session log:
  - `projects/000/logs/session_20260315_190600.log`
- runtime summary:
  - `projects/000/logs/runtime_audit_summary.json`
- pass rate:
  - `projects/000/logs/pass_rate_monitor.json`
- runtime audit jsonl:
  - `projects/000/logs/runtime_audit.jsonl`
- session sinks:
  - `projects/000/logs/session/ui_events.jsonl`
  - `projects/000/logs/session/decisions.jsonl`
  - `projects/000/logs/session/llm_io.jsonl`
  - `projects/000/logs/session/state_changes.jsonl`
- production sink:
  - `projects/000/logs/episode_production.jsonl`
- quality sink:
  - `projects/000/logs/quality_metrics.jsonl`

## 2. Artifact Evidence
- Stage 0:
  - `projects/000/stage0_output/style_guide.json`
- Stage 2:
  - `projects/000/logs/artifacts/stage2/`
  - `projects/000/plans/arcs/`
- Stage 3:
  - `projects/000/logs/artifacts/stage3/`
  - `projects/000/plans/blueprints/`
- Stage 4:
  - `projects/000/logs/artifacts/stage4/`
  - `projects/000/drafts/`

## 3. Persistence Evidence
- DB:
  - `projects/000/project_data.db`
  - `projects/000/project_data.db-wal`
  - `projects/000/project_data.db-shm`

## 4. Source Evidence
- runtime spine:
  - `main_a.py`
- Stage 0 / 1:
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage0/`
- Stage 2:
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_optimizer.py`
- Stage 3:
  - `modules/core/stage3_orchestrator.py`
  - blueprint agent surfaces under `modules/domain/agents/`
- Stage 4:
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/domain/agents/chief_writer.py`
  - `modules/domain/agents/chief_writer_context.py`
  - `modules/domain/agents/director_ensemble.py`

## 5. Companion Docs
- prior global survey:
  - `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
- prior stage4 focused investigation:
  - `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-investigation.md`
