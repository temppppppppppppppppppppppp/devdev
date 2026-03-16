<!-- [참고자료] -->
﻿# codebase-global-log-evidence-merged Deep Global Integrity Survey

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
Related Evidence Manifest: `docs/2026-03-15/codebase-global-log-evidence-merged-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/pdf/log artifacts already present; merged survey authority is bounded to included source paths plus selected 00_260315 runtime artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `artifact-truth addendum and 15일 transcript supplement folded into the same bounded survey scope`

## 1. Intent
- Merge a full codebase-global static survey with the latest secured runtime evidence from `projects/00_260315`.
- Produce one log-inclusive deep survey bundle, one single-SSOT roadmap, and refreshed execution SSOTs without entering realization.
- Re-evaluate earlier source-only and bounded live-merge findings against durable log, JSONL, summary, and DB artifacts.

## 2. Scope Lock
- included source paths:
  - `main_a.py`
  - `modules/`
  - `scripts/`
  - `tests/`
  - `UI/`
  - `geuldobi-desktop/`
  - `config/`
- included runtime artifacts:
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
  - referenced Stage 2/3/4 artifacts under `projects/00_260315/logs/artifacts/`
  - supplemental operator transcript `15일.txt`
- predecessor authority considered:
  - `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
  - `docs/2026-03-15/codebase-global-live-merge-00_260315-post-run-merge-audit.md`
- excluded:
  - code edits, DB mutation, runtime mutation, `node_modules/`, `dist/`, `build/`, stale low-memory pytest artifacts, unrelated project logs outside the selected secured run

## 3. Coverage Matrix
- macro views covered:
  - repo topology
  - runtime spine and authority map
  - desktop/backend control plane
  - runtime artifact lineup
- micro views covered:
  - current source inventory
  - hotspot ranking
  - prompt/persistence/control-plane anchor counts
  - direct hotspot reads for shutdown, audit summary, prompt surfaces, session logging, and bridge files
- cross-cut views covered:
  - source text and output encoding
  - persistence and observability
  - session identity and sink alignment
  - operator surface
  - backend-front connectivity
  - recovery/retry
  - regression/tooling
- operational views covered:
  - secured CLI run evidence
  - validators and queue governance
  - bounded use of predecessor docs with explicit authority rules
- deferred surfaces:
  - fresh Electron/Desktop runtime reproduction
  - unrelated project folders and archival logs

## 4. Macro View
- topology:
  - `main_a.py` remains the runtime spine and shutdown owner.
  - `DBManager`, `AuditService`, and `SessionLogger` remain the dominant persistence and observability authorities.
  - `UIService` and `StudioVisualizer` remain the main wrapper prompt surfaces on the CLI side.
  - `geuldobi-desktop/src/index.html`, `preload.js`, `main.js`, `bridge_server.py`, `process_runner.py`, and `prompt_broker.py` remain the desktop/backend control-plane chain.
- runtime authority map:
  - stage completion callbacks trigger `write_audit_summary(...)` from stage2, stage3, and stage4 orchestrators
  - shutdown path in `main_a.py` still commits then closes DB resources before all in-flight callbacks are guaranteed quiescent
  - plain session log, session JSONL, runtime audit JSONL, pass-rate summary, and DB are parallel truth surfaces rather than one unified sink
- secured runtime classification:
  - the selected run is a completed CLI session for `projects/00_260315`
  - latest plain-log token is `20260315_144654`
  - structured UI sinks use `session_id=20260315_144741`
- direct runtime outcomes:
  - menu `7` no longer asks the older one-time tranche prompt on this secured run; the plain log records `auto-selected default batch_size: 3`
  - `15일.txt` corroborates the same no-input FrontierLag path and shows auto-continue continuing past the first tranche
  - summary finalization still lands before the system fully quiesces
  - two UI-event writes and at least one `llm_calls` write hit a closed DB after shutdown
  - all referenced Stage 2/3/4 artifact files currently exist and decode cleanly, but their persisted hash metadata does not match current bytes on disk
  - the app-level shutdown path can log completion before Python teardown fully quiesces, as shown by post-completion `threading/_python_exit` and `BaseEventLoop.__del__` exceptions in `15일.txt`

## 5. Micro View
- hotspot ranking:
  - highest-value active code hotspots remain `modules/core/stage4_interview_round.py`, `main_a.py`, `modules/core/db_manager.py`, `modules/core/stage4_context_builder.py`, `modules/domain/agents/base_agent.py`, and `modules/core/stage3_orchestrator.py`
  - active source-text corruption is still directly visible in `main_a.py` and `modules/core/session_logger.py`
- anchor counts from current source:
  - `raw input(...)`: `92`
  - `_get_int_input(...)`: `5`
  - `prompt(...)`: `262`
  - `save_director_selection(...)`: `68`
  - `save_stage_attempt(...)`: `53`
  - `write_audit_summary(...)`: `19`
  - `flush_audit_buffer(...)`: `19`
  - `.commit(...)`: `100`
  - `.rollback(...)`: `32`
  - `prompt_request`: `14`
  - `bridgeFetch(...)`: `9`
- runtime micro facts:
  - `runtime_audit_summary.json` timestamp: `2026-03-15 17:24:09`
  - `pass_rate_monitor.json` last_updated: `2026-03-15T17:24:25.933860`
  - `llm_io.jsonl` last timestamp: `2026-03-15T17:24:58`
  - summary `proof_digest.artifacts.ui_events_count`: `1419`
  - final `ui_events` DB count: `1446`
  - final `ui_events.jsonl` count: `1448`
  - summary Stage 4 issue counts: `selection_reason_mismatches=2`, `verdict_reason_mismatches=2`
  - artifact inventory counts: `stage2=3`, `stage3=12`, `stage4=28`
  - `stage_attempts` rows with `artifact_path`: `29`; `content_hash` mismatches against current bytes: `29/29`
  - linked `episode_production` attempt rows: `14`; `content_hash` or `selection_content_hash` mismatches against current bytes: `28`
  - artifact structural non-findings: `missing=0`, `zero-byte=0`, `utf-8 decode failures=0`, `stage2/stage3 json parse failures=0`
  - `episode_production.jsonl` also carries `5` event-only rows without `attempt_key`, so it is not a pure attempt-truth sink
- localized mismatch proof:
  - the Stage 4 mismatch table resolves the `2 + 2` counts to attempt keys `s4:ep4:arc1:a1:20260315_144741` and `s4:ep5:arc2:a1:20260315_144741`
  - latest ep10 and ep11 Stage 4 rows are not the mismatch surface
  - artifact-truth mismatch proof spans Stage 2, Stage 3, and Stage 4 rather than only the two bounded rationale-mismatch attempts

## 6. Cross-Cut Integrity Matrix
- Companion matrix: `docs/2026-03-15/codebase-global-log-evidence-merged-cross-cut-integrity-matrix.md`
- Key summary:
  - source corruption and shell-safe output are now one combined lane because both source text and host emission materially affect operator-visible evidence
  - persistence and observability are now the highest-value runtime lane because the secured run plus artifact-truth sweep prove stale summary timing, late writes after close, session-id split, systematic artifact-hash drift, and bounded Stage 4 rationale drift
  - backend-front connectivity remains action-bearing from source evidence even though the secured run is CLI-only
  - runtime/operator prompt fragmentation still exists, but the latest secured evidence retained the repaired FrontierLag and prompt-dedup behavior

## 7. Operational and Regression View
- tests and smoke surface:
  - the workspace still has broad targeted coverage for DB, audit, FrontierLag, UI wrappers, process runner, and desktop transport
  - missing regression focus is now sharper:
    - no lock for `no writes after DB close during shutdown`
    - no lock for `summary finalizes after quiescent point`
    - no lock for `plain log token / structured session id lineage`
    - no fresh desktop live-run regression for reconnect or prompt concurrency
- validator surface:
  - `scripts/check_utf8_hygiene.py`
  - `scripts/ops_validator.py`
  - `scripts/validate_deep_global_survey_bundle.py`
- retained non-findings from the secured run:
  - no duplicate-column migration burst
  - no fresh prompt duplication regression in durable UI sinks
  - no fresh menu `7` interactive block on the secured CLI run
- bounded interpretation:
  - desktop/backend transport claims remain source-led
  - runtime persistence/summary/logging claims are strongly supported by current durable evidence

## 8. Contradiction and Uncertainty Ledger
- Companion ledger: `docs/2026-03-15/codebase-global-log-evidence-merged-uncertainty-contradiction-ledger.md`
- contradictions closed:
  - latest CLI runtime evidence supersedes older March 15 prompt-contract drift claims for menu `7`
  - Stage 4 rationale mismatch counts are now localized to exact attempts
- contradictions still open:
  - summary contract vs actual finalization point
  - session token split across plain log and structured sinks
  - stored artifact hash lineage vs actual bytes on disk
  - shutdown completion message vs process-level teardown exceptions
  - source/output encoding boundary responsibilities
  - desktop/control-plane severity without fresh runtime proof
- uncertainty bounds:
  - no fresh desktop runtime capture in this bundle
  - exact late-write callback chain is inferred from logs plus code ownership, not fully instrumented end-to-end
  - exact stale-hash capture point is still inferred from artifact comparisons rather than direct write-order instrumentation
  - unrelated dirty files remain outside authority unless explicitly read

## 9. Severity and Action Map
- `P0` items:
  - none from current merged evidence
- `P1` items:
  - scoped source-text corruption and operator/output encoding hygiene remain active in current source and tooling paths
  - persistence/observability finalization and sink alignment defects are runtime-proven:
    - stale summary timestamp
    - late `ui_events` / `llm_calls` writes after DB close
    - plain-log vs structured session-id split
    - systematic `content_hash` / `selection_content_hash` drift against durable artifacts
    - exact Stage 4 rationale mismatch table
    - post-completion teardown exceptions after claimed shutdown success
  - backend-front/control-plane connectivity gaps remain action-bearing from current source evidence
- `P2` items:
  - runtime/operator prompt authority remains fragmented, but the latest secured run retained the key user-facing fixes
- action-bearing areas:
  - source text and runtime/output encoding hygiene
  - persistence/observability finalization and sink alignment
  - backend-front/control-plane connectivity hardening
  - runtime/operator surface unification refresh
- areas with `no-execution-doc-required`:
  - `UI/` asset archives
  - broader `config/style_references` corpora as a standalone lane
  - regression/test tree as a standalone lane

## 10. Execution SSOT Mapping

| Area | Classification | Canonical Execution Doc | Notes |
| --- | --- | --- | --- |
| source text and runtime/output encoding hygiene | action-bearing | `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md` | merges source corruption repair, shell-safe tooling, and operator-visible encoding trust |
| persistence/observability finalization and sink alignment | action-bearing | `docs/2026-03-15/persistence-observability-finalization-and-sink-alignment-remediation-execution-ssot.md` | closes stale summary timing, late writes after close, session-id lineage, artifact hash truth drift, teardown exceptions, and Stage 4 rationale mismatch drift |
| backend-front/control-plane connectivity | action-bearing | `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md` | remains source-led until a fresh desktop run is captured |
| runtime/operator surface unification | action-bearing | `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md` | narrowed to prompt-authority reduction after latest CLI fixes held |
| UI asset packs | no-execution-doc-required | none | not the main runtime-control surface in this bundle |
| corpora and narrative references | no-execution-doc-required | none | outside the system remediation queue here |
| tests/regression | no-execution-doc-required | none | verification is attached to each execution lane |

## 11. Single SSOT Roadmap Lineage
- canonical roadmap:
  - `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md`
- temp roadmap mirror:
  - `docs/temp/execution-roadmap.md`
- execution order basis:
  - runtime-proven persistence finalization first, then source/output encoding, then desktop/backend connectivity hardening, then prompt-authority unification
- lane structure:
  - Phase 1: persistence/observability finalization and sink alignment
  - Phase 2: source text and runtime/output encoding hygiene
  - Phase 3: backend-front/control-plane connectivity hardening
  - Phase 4: runtime/operator surface unification refresh

## 12. Confidence Summary
- estimated score:
  - `98/100`
- score rationale:
  - global source coverage remained intact from the earlier clean-room sweep and was re-anchored with fresh raw inventory artifacts
  - runtime evidence is durable and triangulated across plain log, supplemental transcript, summary JSON, pass-rate JSON, JSONL sinks, artifact files, and the project DB
  - the main contradiction clusters are now either closed or explicitly bounded in the ledger
  - the action map converges to four coherent execution lanes under one roadmap
- reasons the score is not higher:
  - no fresh desktop/Electron runtime capture
  - exact late-write call-chain instrumentation is still inferred rather than directly traced end-to-end
  - exact stale-hash capture point is still inferred rather than directly instrumented
  - unrelated dirty workspace changes remain present and must stay out of future realization scope unless explicitly included
- final save decision:
  - allowed because the merged bundle exceeds the 95% gate and its remaining uncertainty is explicit rather than hidden
