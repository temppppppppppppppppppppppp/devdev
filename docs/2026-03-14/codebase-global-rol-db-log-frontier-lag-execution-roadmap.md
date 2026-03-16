<!-- [참고자료] -->
# Codebase Global ROL DB Log Frontier Lag Aggregate Execution Roadmap

Date: 2026-03-14
Status: closed
Canonical Path: `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
- Baseline Dirty Summary: `dirty: 7 tracked, 3 untracked; hotspots: docs/implementation/*, 260314-print.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `all four execution items realized by 2026-03-15; temp queue exhausted after encoding-boundary closure and queue cleanup`
Queue Snapshot:
- queue exhausted on `2026-03-15`; no active temp execution mirrors remain

## 1. Purpose
- Control the reopened multi-item queue created by `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`.
- Keep DB/log/menu `7` and encoding work ordered under one SSOT roadmap instead of reopening the old closed roadmap.
- Preserve one canonical execution order for the active bundle.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `runtime-audit-rationale-sink-alignment` | `docs/2026-03-14/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md` | `docs/temp/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md` | completed | closed on `2026-03-15`; temp mirror removed after verification and roadmap sync |
| `db-bootstrap-migration-noise` | `docs/2026-03-14/db-bootstrap-migration-noise-remediation-execution-ssot.md` | `docs/temp/db-bootstrap-migration-noise-remediation-execution-ssot.md` | completed | closed on `2026-03-15`; temp mirror removed after verification and roadmap sync |
| `frontier-lag-nonstop-contract` | `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md` | `docs/temp/frontier-lag-nonstop-contract-remediation-execution-ssot.md` | completed | closed on `2026-03-15`; temp mirror removed after targeted pytest verification and roadmap sync |
| `encoding-boundary-mojibake-refresh` | `docs/2026-03-14/encoding-boundary-mojibake-refresh-remediation-execution-ssot.md` | `docs/temp/encoding-boundary-mojibake-refresh-remediation-execution-ssot.md` | completed | closed on `2026-03-15`; temp mirror removed after targeted encoding/process-runner/transport verification and roadmap closure |

## 3. Dependency Graph
- `runtime-audit-rationale-sink-alignment -> db-bootstrap-migration-noise`
- `runtime-audit-rationale-sink-alignment -> encoding-boundary-mojibake-refresh`
- shared substrate:
  - operator-visible event truth
  - audit summary trust
  - durable DB/JSONL sink contracts
- merge opportunities:
  - `ui_events` stage normalization stays inside the runtime-audit item and should not reopen a separate queue entry
## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`
- truth-first ordering over convenience-first ordering

1. `runtime-audit-rationale-sink-alignment`
2. `db-bootstrap-migration-noise`
3. `frontier-lag-nonstop-contract`
4. `encoding-boundary-mojibake-refresh`

## 5. Per-Item Plan

### runtime-audit-rationale-sink-alignment
- goal: restore trustworthy saved proof digests and one canonical rationale field across sinks
- prerequisites: none
- execution notes: includes the `ui_events` stage-label DB failure because it is the same persistence contract
- completion signal: saved audit summaries match live analyzer truth and `ui_events` DB mirror failures disappear
- closure evidence: `181` targeted unit tests passed, `24` summary/sink integration tests passed, `python scripts/ops_validator.py --strict` passed on `2026-03-15`
- temp cleanup action: completed on `2026-03-15`

### db-bootstrap-migration-noise
- goal: remove repeated duplicate-column noise from summary-time DB re-entry
- prerequisites: runtime-audit sink truth is fixed so proof-digest behavior is stable
- execution notes: keep old-DB compatibility while replacing exception-driven migration checks
- completion signal: no repeated duplicate-column bursts at Stage 2/3/4 audit-summary checkpoints
- closure evidence: `26` audit/bootstrap tests passed, `24` summary/sink integration tests passed, `26` DBManager regression tests passed, `python scripts/ops_validator.py --strict` passed on `2026-03-15`
- temp cleanup action: completed on `2026-03-15`

### frontier-lag-nonstop-contract
- goal: enforce normal-path non-stop behavior for interactive menu `7`
- prerequisites: none
- execution notes: preserve `batch_size_override`, failure prompts, and `wait_for_menu_return`
- completion signal: interactive menu `7` no longer asks the initial Arc-count question on the normal path
- closure evidence: `4` Frontier Lag regression tests passed, `9` harness tests passed, prompt-site reinspection confirmed the normal-path prompt removal while preserving failure prompts on `2026-03-15`
- temp cleanup action: completed on `2026-03-15`

### encoding-boundary-mojibake-refresh
- goal: re-establish authoritative UTF-8 operator artifact rules and quarantine stderr-only capture ambiguity
- prerequisites: runtime-audit sink truth is stable enough to define which artifacts are authoritative
- execution notes: do not rewrite source text unless new evidence proves source corruption
- completion signal: authoritative operator artifacts are UTF-8 clean and boundary-only stderr captures are documented or fenced
- closure evidence: `4` encoding-boundary contract tests passed, `31` ProcessRunner regression tests passed, `3` desktop transport contract tests passed, `python scripts/ops_validator.py --strict` passed on `2026-03-15`
- temp cleanup action: completed on `2026-03-15`

## 6. Shared Risks and Side-Effects
- shared write paths:
  - project-local logs
  - project-local SQLite assets
  - runtime audit summaries
  - session JSONL sinks
- shared DB/schema touchpoints:
  - `DBManager`
  - `AuditService`
  - `ui_events`
  - `director_selections`
  - `stage_attempts`
- shared logs/UI surfaces:
  - `ui.log`
  - runtime audit summaries
  - session log output
  - stderr/error capture artifacts
- rollback/recovery concerns:
  - summary-timing, DB bootstrap, and encoding work all touch the operator-truth boundary and should not run in parallel
- queue collision or ordering risks:
  - opening a second roadmap for this bundle would violate single-SSOT authority

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `runtime-audit-rationale-sink-alignment` | completed | 2026-03-15 | none |
| `db-bootstrap-migration-noise` | completed | 2026-03-15 | none |
| `frontier-lag-nonstop-contract` | completed | 2026-03-15 | none |
| `encoding-boundary-mojibake-refresh` | completed | 2026-03-15 | none |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
