<!-- [참고자료] -->
# Codebase Global ROL DB Log Frontier Lag Re-Audit Evidence Manifest

Date: 2026-03-14
Status: final
Topic: `codebase-global-rol-db-log-frontier-lag-reaudit`
Related Survey Docs:
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-3pass-audit.md`
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`
Related Execution Docs:
- `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
- `docs/2026-03-14/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md`
- `docs/2026-03-14/db-bootstrap-migration-noise-remediation-execution-ssot.md`
- `docs/2026-03-14/encoding-boundary-mojibake-refresh-remediation-execution-ssot.md`
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-execution-roadmap.md`

## 1. Summary
- evidence scope: menu `7` prompt sites, live DB/JSONL sink joins, duplicate-column migration clusters, and encoding-boundary samples
- freshness note: all raw evidence artifacts in this manifest were generated from the live workspace on 2026-03-14 during this re-audit
- known gaps: no fresh runtime replay was performed; all runtime findings come from the captured session artifacts plus read-only analyzer queries

## 2. Artifact Index

| Artifact | Type | Acquired By | Freshness | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
| `docs/2026-03-14/db-log-frontier-lag-reaudit-prompt-sites.txt` | code + runtime excerpt index | inline Python extraction | fresh | re-audit + frontier-lag execution | maps menu `7` interactive sites to print/log evidence |
| `docs/2026-03-14/db-log-frontier-lag-reaudit-sink-alignment.json` | structured integrity report | inline Python + `FailureAnalyzer` | fresh | re-audit + runtime-audit execution | joins saved summary, live analyzer output, rationale samples, and `ui_events` failure counts |
| `docs/2026-03-14/db-log-frontier-lag-reaudit-migration-noise.txt` | log cluster inventory | inline Python extraction | fresh | re-audit + DB bootstrap execution | quantifies repeated duplicate-column noise and owning call paths |
| `docs/2026-03-14/db-log-frontier-lag-reaudit-encoding-samples.txt` | encoding boundary samples | inline Python decode checks | fresh | re-audit + encoding execution | distinguishes authoritative UTF-8 artifacts from UTF-16 stderr wrapper output |
| `260314-print.txt` | live operator artifact | direct read | fresh | re-audit + frontier-lag execution | confirms current normal-path prompt behavior with the user-provided print capture |
| `projects/00_20260314/logs/session_20260314_213845.log` | live session log | direct read | fresh | all execution docs | authoritative timestamp ordering for prompt, migration, and `ui_events` failures |
| `projects/00_20260314/logs/runtime_audit_summary.json` | saved proof digest | direct read | fresh | runtime-audit execution | stale summary baseline that triggered the re-audit |
| `projects/00_20260314/logs/pass_rate_monitor.json` | saved monitor sink | direct read | fresh | runtime-audit execution | shows post-summary update timing and current final records |
| `projects/00_20260314/logs/session/decisions.jsonl` | session rationale sink | direct read | fresh | runtime-audit execution | used for attempt-key and rationale join checks |
| `projects/00_20260314/logs/episode_production.jsonl` | lifecycle rationale sink | direct read | fresh | runtime-audit execution | used for Stage 4 lifecycle joins |
| `projects/00_20260314/project_data.db` | live SQLite authority | direct read + sqlite queries | fresh | runtime-audit + DB bootstrap execution | authoritative source for `stage_attempts`, `director_selections`, and `ui_events` |
| `error.log` | redirected stderr artifact | direct read + decode checks | fresh | encoding execution | proves UTF-16 wrapper plus mojibake prompt leakage |
| `docs/2026-03-14/codebase-global-rol-post-closure-reaudit.md` | predecessor authority | direct read | fresh | re-audit | closure baseline that is now reopened only in this bounded lane |
| `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md` | predecessor contract doc | direct read | fresh | frontier-lag execution | harness semantics remain valid but do not settle interactive operator policy |

## 3. Limitations
- terminal rendering inside some local tooling can show mojibake for otherwise valid UTF-8 files, so the encoding samples should be interpreted from declared file encodings rather than from a single terminal renderer
- `runtime_audit_summary.json` is a saved snapshot artifact and not live truth by itself; it must always be compared with the current DB and JSONL sinks
- this manifest indexes evidence for the reopened bundle only; it does not supersede older manifests outside the DB/log/menu `7` scope
