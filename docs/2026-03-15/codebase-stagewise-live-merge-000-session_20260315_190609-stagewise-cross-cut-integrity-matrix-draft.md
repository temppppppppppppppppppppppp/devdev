# Codebase Stagewise Cross-Cut Integrity Matrix Draft

Date: 2026-03-15
Status: draft-live-run-pending
Project: `projects/000`
Structured Session Id: `20260315_190609`

| Stage | Primary Source Authority | Live Evidence Strength | Current Good Signal | Current Risk Signal | Draft Severity |
| --- | --- | --- | --- | --- | --- |
| Stage 0 | `stage01_helpers.py`, `stage0/` | medium | `style_guide.json` written | branch matrix still under-exercised | P2 |
| Stage 1 | `stage01_helpers.py` | low | helper surface is small and understandable | no fresh runtime evidence, weak dedicated observability | P3 |
| Stage 2 | `stage2_orchestrator.py`, `stage2_validation_pipeline.py`, `stage2_finalizer.py` | high | 2/2 arc artifacts persisted | `constraint_summary` omission warning affects downstream trust | P1 |
| Stage 3 | `stage3_orchestrator.py` and blueprint agent layer | high | 7 blueprints persisted with matching attempt counts | completion visibility lags while app remains alive | P2 |
| Stage 4 | `stage4_orchestrator.py`, `stage4_context_builder.py`, `stage4_interview_round.py`, CW/Director agents | very high | retry/rationale/artifact lineage is rich and visible | retry-loop pressure, context compression, mojibake in structured payloads | P1 |

## Cross-Cut Notes
- `prompt / operator authority`
  - concentrated in Stage 0 and shared runtime shell, but still matters across all stages
- `context carryover`
  - strongest Stage 4 issue, partly fed by Stage 2 and Stage 3 outputs
- `persistence / finalization`
  - not stage-local; summary and pass-rate lag behind later Stage 4 writes
- `artifact truth`
  - current artifact counts look healthy, especially for Stage 2-4
- `human-readable observability`
  - structured sinks still carry mojibake-like payload text late in the run
