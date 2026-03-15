# Codebase Global Live-Merge 00_260315 Post-Run Merge Audit

Date: 2026-03-15
Status: final
Mode: `ROL 전역 전체 전수조사` + `ROL live-merge`
Canonical Path: `docs/2026-03-15/codebase-global-live-merge-00_260315-post-run-merge-audit.md`
Baseline Commit: `083c86d9`
Baseline Dirty Summary: `modified=30, deleted=54, untracked=7`
Latest Project Folder: `projects/00_260315`
Terminal Run State: `stopped / bounded-partial`
Confidence: `95%`
Predecessor Working Docs:
- `docs/2026-03-15/codebase-global-live-merge-00_260315-preflight-watchlist.md`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-live-run-evidence-manifest.md`
- `docs/2026-03-15/codebase-global-live-merge-00_260315-live-run-evidence.txt`
Predecessor Authority Docs:
- `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
- `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`

## 1. Intent
- Merge the bounded fresh live run from `projects/00_260315` with a codebase-global static survey.
- Revalidate earlier FrontierLag, logging, audit, and UTF-8 assumptions against current terminal evidence.
- Stop at investigation outputs only. No implementation, execution SSOT refresh, or roadmap mutation is included in this turn.

## 2. Scope Lock
- Included primary runtime surfaces:
  - `projects/00_260315/logs/session_20260315_132843.log`
  - `projects/00_260315/logs/session/ui_events.jsonl`
  - `projects/00_260315/logs/session/decisions.jsonl`
  - `projects/00_260315/logs/session/llm_io.jsonl`
  - `projects/00_260315/logs/runtime_audit_summary.json`
  - `projects/00_260315/logs/pass_rate_monitor.json`
  - `projects/00_260315/logs/runtime_audit.jsonl`
  - `projects/00_260315/project_data.db`
  - `projects/00_260315/project_data.db-wal`
- Included static global sweep:
  - `main_a.py`
  - `modules/core/logger.py`
  - `modules/core/session_logger.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/db_manager.py`
  - `modules/core/studio_visualizer.py`
  - `modules/core/services/ui_service.py`
  - `modules/api/process_runner.py`
  - `scripts/check_utf8_hygiene.py`
  - relevant test coverage under `tests/`
- Included by reference, not primary sweep target:
  - `docs/implementation/*`
  - predecessor dated docs listed above
- Excluded:
  - `dist/`, `python-embed/`, archival logs, stale `logs/pytest_lowmem/`
  - code edits, DB mutation, config mutation, execution queue operations

## 3. Terminal Run Classification
- The latest project folder by `mtime` is `projects/00_260315`.
- No live `python main_a.py` process remained when the post-run audit started.
- The plain session log ends at line `2453` with an in-flight HTTP response wait during Arc 2 Stage 2, not with a graceful shutdown sequence.
- There is no current-run traceback, `closed database`, duplicate-column burst, or crash dump for this session.
- `runtime_audit_summary.json` is tagged `stage4_complete` at `2026-03-15 13:51:59`, which matches the completed Arc 1 Stage 4 slice, not whole FrontierLag completion.
- Judgment:
  - this was a bounded partial run
  - the evidence is valid for Arc 1 complete slices and early Arc 2 entry
  - it is not valid to call the full 3-arc FrontierLag run `completed`

## 4. Coverage Accounting

### Tranche A. Macro Topology
- Covered.
- Active system entrypoint remains `main_a.py` (`4670` lines).
- Runtime-adjacent surfaces remain concentrated in `modules/core` (`180` files), `scripts` (`36` files), `tests` (`354` files), `UI` (`637` files), and `geuldobi-desktop` (`20037` files).

### Tranche B. Runtime Core
- Covered.
- FrontierLag entry flow lives in `main_a.py`.
- Audit-summary callbacks are wired through `main_a.py:3252-3254`, `modules/core/stage2_orchestrator.py:995`, `modules/core/stage3_orchestrator.py:603`, and `modules/core/stage4_orchestrator.py:1644-1651`.

### Tranche C. Domain and Agent Layer
- Covered at bounded depth.
- Completed slice evidence shows:
  - `stage_attempts`: Stage 2 x1, Stage 3 x3, Stage 4 x2
  - `director_selections`: Stage 2 x1, Stage 3 x3, Stage 4 x2
- No fresh selection-reason divergence surfaced in the completed slice.

### Tranche D. Persistence and Observability
- Covered.
- `ui_events.jsonl` and `ui_events` DB mirror both reached `442`.
- `llm_io.jsonl` and `llm_calls` DB mirror stayed aligned during observation.
- `runtime_audit_summary.json` and `pass_rate_monitor.json` are aligned for the completed Arc 1 Stage 4 slice.

### Tranche E. Operator Surface and App Shell
- Covered.
- Menu `7` prompt/selection behavior, prompt dedup, and session-log rendering were observed directly.

### Tranche F. Quality and Regression Surface
- Covered at hotspot level.
- Relevant test surface exists in at least `33` targeted test files touching FrontierLag, logging, audit, session logger, prompt UI, process runner, and encoding boundaries.

### Tranche G. Scripts and Utility Surface
- Covered.
- `scripts/check_utf8_hygiene.py` is a fresh action-bearing hotspot.

### Tranche H. Cross-Cutting Contracts and Config
- Covered.
- Current contract pressure points are:
  - FrontierLag operator contract
  - UTF-8 guardrail implementation
  - runtime summary semantics during partial runs

## 5. Pass 1. Evidence Inventory
- `session_20260315_132843.log:221`
  - menu `7` still asks: `몇 개 초기 tranche로 Arc를 진행할까요? (1~60, 기본: 3):`
- `session_20260315_132843.log:224`
  - the chosen batch is then logged as `initial batch_size selected: 3`
- `session_20260315_132843.log:227`
  - FrontierLag enters `Arc 1/60 frontier 전진 (1/3)`
- `session_20260315_132843.log:1424`
  - Arc 1 Episode 1 Stage 4 reaches `director_verdict=PASS`
- `session_20260315_132843.log:2442-2453`
  - the final visible evidence is an in-flight Stage 2 network call for Arc 2
- `ui_events.jsonl`
  - includes one visible `prompt`, one hidden `prompt_response`, and one hidden `selection` for the FrontierLag initial-tranche interaction
- `runtime_audit_summary.json`
  - final artifact in this run is `tag=stage4_complete`
  - proof digest reports Stage 3 `3` and Stage 4 `2` attempts with `status=ok`
- `pass_rate_monitor.json`
  - records `6` completed items: Stage 2 x1, Stage 3 x3, Stage 4 x2
- `project_data.db` and `project_data.db-wal`
  - show aligned counts for completed durable sinks

## 6. Pass 2. Semantic Classification

### Confirmed Action-Bearing Findings
1. Menu `7` operator contract drift
2. UTF-8 hygiene gate false positives and cp949 shell crash

### Confirmed Non-Findings / Retained Fixes
1. Prompt dedup fix remains effective in durable UI sinks
2. Prior runtime-audit stale-summary issue did not reappear on the completed Arc 1 Stage 4 slice
3. Plain session-log mojibake is not reproduced when the file is read as UTF-8 directly

### Bounded Observability Note
1. The run stopped mid-Arc-2 without a graceful shutdown marker, so post-Arc-1 claims must remain bounded

## 7. Findings

### [F1] P1 | Menu `7` still blocks the user-desired nonstop contract with an initial Enter/input prompt
- Static evidence:
  - `main_a.py:4197` contains the initial tranche prompt string
  - `main_a.py:4206` logs `initial batch_size selected`
  - `main_a.py:4070` still preserves `batch_size_override` for harnessed paths
- Live evidence:
  - `projects/00_260315/logs/session_20260315_132843.log:221`
  - `projects/00_260315/logs/session/ui_events.jsonl` rows `178-180`
- Judgment:
  - current implementation matches the later `interactive-prompt-contract-refresh` authority
  - current implementation contradicts the user’s stated desired contract of true no-input nonstop behavior
  - this is a real operator-contract mismatch, not a logging illusion
- Predecessor contradiction:
  - `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md` removed the initial prompt
  - `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md` reintroduced a one-time prompt for interactive runs
  - the fresh run confirms the latter is what is live today

### [F2] P1 | `check_utf8_hygiene.py` over-flags legitimate Korean prompt lines and crashes on cp949 PowerShell output
- Static evidence:
  - `scripts/check_utf8_hygiene.py:50`
    - `NONASCII_QUESTION_RE = re.compile(r"(?:\\?[^\\x00-\\x7f]|[^\\x00-\\x7f]\\?)")`
  - `scripts/check_utf8_hygiene.py:177`
    - findings are printed directly with `print(_format_finding(finding))`
- Live evidence:
  - `collect_findings(...)` against `session_20260315_132843.log` and `ui_events.jsonl` reported `nonascii_adjacent_question_mark` on legitimate Korean question prompts
  - direct CLI execution against live log targets raised `UnicodeEncodeError` in cp949 PowerShell when emitting snippets with emoji
- Judgment:
  - the gate is too aggressive for real Korean operator prompts
  - the CLI emission path is not shell-safe on the current Windows host
  - this is an action-bearing regression in tooling, not in runtime generation

### [F3] P2 | The live run ended as a bounded partial slice, so whole-run completion claims would be false
- Evidence:
  - no live `main_a.py` process remained
  - `session_20260315_132843.log` ends at line `2453` during Stage 2 network IO for Arc 2
  - no shutdown sequence, traceback, or current-run crash dump exists
  - `runtime_audit_summary.json` only captures `stage4_complete` from the completed Arc 1 Stage 4 slice
- Judgment:
  - this is not enough evidence to file a runtime crash defect
  - it is enough evidence to classify the run as `stopped / bounded-partial`
  - all conclusions in this audit are therefore intentionally bounded to the completed slice plus early Arc 2 ingress

## 8. Rejected or Narrowed Hypotheses

### Rejected H1. Plain session log sink is globally mojibake-corrupted
- The direct UTF-8 read of `session_20260315_132843.log` is clean.
- The earlier mojibake-looking console excerpts came from shell-host rendering, not from source-file corruption.
- `modules/core/logger.py:81` and `modules/core/logger.py:99` already write the session log via UTF-8 `FileHandler`s.

### Narrowed H2. Runtime audit summary is still stale for completed slices
- For the completed Arc 1 slice, `runtime_audit_summary.json` and `pass_rate_monitor.json` are aligned.
- The file is not a whole-FrontierLag completion marker, but the earlier stale-summary defect did not reproduce for the completed Stage 3/Stage 4 artifacts in this run.

### Confirmed H3. Prompt dedup fix is retained
- `ui_events.jsonl` shows one visible prompt plus hidden response/selection rows.
- There is no evidence of the earlier visible prompt triplication reappearing in the durable UI sink.

## 9. Cross-Cut Integrity Matrix

| Surface | Prior or Suspected State | Fresh Run Result | Judgment |
| --- | --- | --- | --- |
| Menu `7` normal path | disputed between “zero prompt” and “ask once” docs | asks once, then continues with batch `3` | operator mismatch against current user requirement |
| Prompt dedup | previously fixed in code/tests | retained in `ui_events.jsonl` | no fresh regression |
| Session log mojibake | suspected from console excerpts | UTF-8 file read is clean | shell-render artifact, not file corruption |
| Audit summary alignment | previously stale on completed slices | aligned for completed Arc 1 Stage 4 slice | prior stale defect not reproduced here |
| DB / JSONL sink alignment | previously under watch | aligned counts on completed slice | retained improvement |
| UTF-8 hygiene gate | newly added hardening expected to be protective | false positives + cp949 print crash | fresh action item |

## 10. Tranche-by-Tranche Outcome

### Tranche A. Macro Topology
- No fresh topology defect.
- Current investigation is still centered on runtime core plus utility/tooling surfaces.

### Tranche B. Runtime Core
- One fresh action-bearing finding:
  - menu `7` contract drift

### Tranche C. Domain and Agent Layer
- No fresh defect proven in the completed slice.
- Stage 3/4 durable attempt records are internally consistent for Arc 1.

### Tranche D. Persistence and Observability
- No fresh sink-misalignment defect proven in the completed slice.
- Partial-run classification remains necessary because the run stopped during Arc 2 Stage 2.

### Tranche E. Operator Surface and App Shell
- One fresh operator-facing mismatch:
  - menu `7` still waits for input once
- One rejected suspicion:
  - session-log mojibake as file corruption

### Tranche F. Quality and Regression Surface
- Existing targeted tests cover much of the touched runtime surface.
- Missing gap:
  - no regression test currently locks “legitimate Korean question prompts must not fail UTF-8 hygiene”
  - no regression test locks cp949-safe emission for the hygiene tool

### Tranche G. Scripts and Utility Surface
- One fresh action-bearing tooling defect:
  - `scripts/check_utf8_hygiene.py`

### Tranche H. Cross-Cutting Contracts and Config
- Current closed docs contain a live authority conflict on the FrontierLag operator contract.
- Current UTF-8 guardrail implementation is stricter than the runtime/operator reality can safely support.

## 11. Action-Bearing Areas
- Area 1:
  - FrontierLag operator contract needs to be re-decided and then reimplemented consistently
- Area 2:
  - UTF-8 hygiene gate needs to be narrowed and made Windows-shell safe

Investigation-only note:
- No new execution SSOTs were created in this turn because the user asked for investigation and the run ended as a bounded partial slice.
- If realization is requested next, these two areas should become the next compact execution items.

## 12. Confidence Summary
- `95%` is justified because:
  - the latest project folder and terminal run state were verified directly
  - primary findings are tied to exact code lines plus live artifacts
  - suspected session-log corruption was explicitly falsified with UTF-8 direct reads
  - completed-slice sink alignment was checked across JSONL, DB, pass-rate, and runtime summary artifacts
- Confidence is not higher than `95%` because:
  - the run did not complete the full intended 3-arc scenario
  - terminal stop cause could not be distinguished between operator kill and external interruption from artifact evidence alone
