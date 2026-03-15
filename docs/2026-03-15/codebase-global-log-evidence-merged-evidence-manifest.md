# codebase-global-log-evidence-merged Evidence Manifest

Date: 2026-03-15
Status: final
Topic: `codebase-global-log-evidence-merged`
Related Survey Docs: `docs/2026-03-15/codebase-global-log-evidence-merged-3pass-audit.md`; `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
Related Execution Docs: `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md`; `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md`; `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`; `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`

## 1. Summary
- evidence scope:
  - current source tree across `main_a.py`, `modules/`, `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/`, and `config/`
  - latest secured runtime evidence from `projects/00_260315`
- freshness note:
  - source and runtime evidence were re-read against the live workspace on 2026-03-15 at baseline commit `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- known gaps:
  - no fresh Electron/Desktop live run was captured in this bundle
  - run-time authority is strongest for the CLI run and its durable sinks

## 2. Artifact Index

| Artifact | Type | Acquired By | Freshness | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
| `docs/2026-03-15/codebase-global-log-evidence-merged-source-inventory.txt` | inventory | Python path sweep | fresh | survey + execution | current top-level scope counts |
| `docs/2026-03-15/codebase-global-log-evidence-merged-hotspot-ranking.txt` | inventory | line-count sweep | fresh | survey + execution | current text hotspots; non-code reference corpora remain visible but not auto-prioritized |
| `docs/2026-03-15/codebase-global-log-evidence-merged-surface-anchor-inventory.txt` | inventory | anchor sweep | fresh | survey + execution | prompt, persistence, audit, and bridge anchor counts |
| `docs/2026-03-15/codebase-global-log-evidence-merged-side-effects.txt` | side-effect map | manual synthesis | fresh | survey + execution | closes default side-effect categories for the merged bundle |
| `docs/2026-03-15/codebase-global-log-evidence-merged-backend-front-connectivity.txt` | focused evidence | desktop/control-plane source sweep | fresh | survey + execution | renderer/preload/main/bridge/prompt-broker seams |
| `docs/2026-03-15/codebase-global-log-evidence-merged-runtime-log-db-evidence.txt` | runtime evidence | plain log + JSONL + DB + summary synthesis | fresh | survey + execution | current secured run counts, timestamps, and late-write proof |
| `docs/2026-03-15/codebase-global-log-evidence-merged-stage4-rationale-mismatch-table.json` | runtime evidence | DB/JSONL join | fresh | survey + persistence lane | localizes the `2 + 2` Stage 4 rationale mismatches to exact attempt keys |
| `docs/2026-03-15/codebase-global-log-evidence-merged-cross-cut-integrity-matrix.md` | matrix | survey synthesis | fresh | survey + roadmap | merged source/runtime ownership and action mapping |
| `docs/2026-03-15/codebase-global-log-evidence-merged-uncertainty-contradiction-ledger.md` | ledger | survey synthesis | fresh | survey + roadmap | explicit contradiction and uncertainty bounds |
| `docs/2026-03-15/codebase-global-log-evidence-merged-3pass-audit.md` | audit | document review | fresh | survey governance | pass1/pass2/pass3 coverage for the bundle and queue |

## 3. Primary Runtime Artifacts
- `projects/00_260315/logs/session_20260315_144654.log`
- `projects/00_260315/logs/runtime_audit_summary.json`
- `projects/00_260315/logs/pass_rate_monitor.json`
- `projects/00_260315/logs/runtime_audit.jsonl`
- `projects/00_260315/logs/session/ui_events.jsonl`
- `projects/00_260315/logs/session/decisions.jsonl`
- `projects/00_260315/logs/session/state_changes.jsonl`
- `projects/00_260315/logs/session/llm_io.jsonl`
- `projects/00_260315/logs/episode_production.jsonl`
- `projects/00_260315/project_data.db`

## 4. Predecessor Authority
- static-only predecessor:
  - `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
- bounded live-merge predecessor:
  - `docs/2026-03-15/codebase-global-live-merge-00_260315-post-run-merge-audit.md`
- interpretation rule:
  - completed runtime evidence from `projects/00_260315` overrides source-only inference when the two disagree
