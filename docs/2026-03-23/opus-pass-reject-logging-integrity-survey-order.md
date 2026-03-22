Date: 2026-03-23
Status: active
Document Type: system-track survey order
Canonical Path: `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-order.md`
Temp Mirror Path: none

Commit State:
- Baseline Commit: `203b328fb35633f9a23fe986862994c8b6dddab7`
- Baseline Dirty Summary: `dirty: 6 tracked, 1 untracked; hotspots: modules/core/stage0/__init__.py, modules/core/stage2_finalizer.py, tests/test_stage0_work_guard_style_cache.py, tests/test_stage2_finalizer.py, .tmp_stage0_msg/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose
- Define a bounded Opus investigation order for `why a path passes or rejects`, `which DB/log/console sinks record that decision`, and `whether long-function decomposition caused behavioral or operator-surface loss`.
- Require a `static source map + fresh live run + merge audit` flow instead of ad hoc patching.
- Focus on operator-trust surfaces: pass/reject reason visibility, DB persistence, audit trail continuity, and console/UI logs.

## 2. Primary Questions
1. For each stage, where is the authoritative PASS/REJECT decision made?
2. What exact payload fields carry the reason, score, verdict, gate basis, or retry instruction?
3. Which DB writes, JSON/metrics writes, audit sinks, and console logs should reflect that decision?
4. After the long-function decomposition campaign, did any of those sinks stop firing, downgrade, duplicate, or become mojibake?
5. If console output volume changed, is that due to intended duplicate-log collapse or unintended operator-surface loss?

## 3. Scope
Included runtime surfaces:
- `main_a.py`
  - audit facade
  - session metrics / shutdown saves
  - boot / operator console entrypoints
- `modules/core/stage2_validation_pipeline.py`
  - pre-director PASS/REJECT logic
  - `pass_rate_monitor.record_attempt(...)`
  - continuity / flow / duplicate guard advisory promotion
- `modules/core/stage2_finalizer.py`
  - pass-finalization logging
  - constraint DB update path
  - Stage 2 post-pass side effects
- `modules/core/stage3_orchestrator.py`
  - blueprint generation handoff and failure surfacing
- `modules/core/stage4_director_runtime.py`
  - director verdict, score, gate basis, candidate selection, decision summary logging
- `modules/core/stage4_post_processor.py`
  - pass settlement owner shell
  - DB / file / HUD / session finalize side effects
- `modules/core/stage4_post_pass_runtime.py`
  - world-state persistence
  - manager delta and advisory sidecars
- persistence / sink substrate
  - `modules/core/db_manager.py`
  - `modules/core/pass_rate_monitor.py`
  - audit service behind `main_a.py::_audit_event`

Included side-effect categories:
- console / UI logs
- DB writes and transaction boundaries
- audit-event writes
- pass-rate / metrics writes
- file artifacts and summary files
- rollback / compensation paths

Excluded for this order unless evidence points there:
- narrative quality of generated manuscripts
- style / BI / treatment semantic correctness
- non-runtime historical docs cleanup
- broad refactor planning beyond regressions found by this survey

## 4. Anchor Evidence Surfaces
Authoritative code anchors to inspect first:
- `main_a.py:3063` `_audit_event(...)`
- `modules/core/stage2_validation_pipeline.py:1023` Stage 2 reject metrics recording
- `modules/core/stage2_finalizer.py:1243` constraint DB update log path
- `modules/core/stage4_director_runtime.py:642` director decision summary logging
- `modules/core/stage4_post_processor.py:553` pass-result owner sink boundary
- `modules/core/stage4_post_pass_runtime.py:855` world-state atomic persistence

Fresh-run evidence targets:
- terminal transcript
- `crash_dump.log` if created
- session metrics JSON under `projects/<project>/logs/metrics/`
- pass-rate persistence outputs
- audit summary outputs
- DB rows written during the run

## 5. Required Investigation Method
This order is survey-first. Do not patch during Pass 1 or Pass 2 unless:
- the live run cannot proceed at all without a compile/runtime blocker fix, and
- that fix is logged as a survey unblocker rather than a general cleanup.

### Pass 1. Static Source Map
- Build a stage-by-stage authority map:
  - who decides PASS/REJECT
  - which object owns the verdict
  - where the reason/score/verdict is shaped
- Build a sink map:
  - `ui.log`
  - `audit_event`
  - pass-rate / metrics writes
  - DB save methods
  - file / artifact output
- Record expected operator-visible lines for each stage family.

### Pass 2. Fresh Live Run
- Run one bounded fresh path that exercises Stage 0 and, if stable, the smallest available Stage 2/3/4 path.
- Capture:
  - actual console transcript
  - metrics file
  - audit and DB side effects
- Mark each expected log/sink as:
  - observed
  - missing
  - duplicated
  - mojibake
  - delayed / reordered

### Pass 3. Merge Audit
- Compare static expectation vs live evidence.
- Classify each mismatch as one of:
  - intended thin-shell reduction
  - duplicate/dead-log cleanup
  - source-string corruption
  - sink omission regression
  - verdict/contract drift
  - persistence-only drift
- If a mismatch is not proven by both source and run evidence, leave it as unresolved rather than overclaim.

## 6. Regression Questions To Answer Explicitly
- Did any stage stop explaining `why it rejected` even though the verdict still persisted?
- Did any stage continue logging PASS/REJECT to console but stop writing the corresponding DB or audit sink?
- Did any DB write survive while the operator-facing console line disappeared?
- Did any post-refactor helper extraction move a side effect behind a path that is no longer invoked?
- Did any mojibake come from source-string corruption rather than terminal rendering?

## 7. Output Requirements
Minimum deliverables:
- one survey report with stage-by-stage decision and sink map
- one mismatch ledger with severity and proof source
- one explicit statement on whether long-function decomposition caused confirmed functionality loss

Only create an execution SSOT if the survey proves concrete regressions that need implementation.

## 8. Acceptance Criteria
This survey order is complete only if it can answer all of the following:
- authoritative PASS/REJECT owner is named for each inspected stage
- console / DB / audit / metrics sinks are mapped for each inspected stage
- each observed live mismatch has a code anchor
- each code suspicion has live-run confirmation or is explicitly marked unconfirmed
- long-function decomposition is classified as:
  - no confirmed loss
  - operator-surface-only loss
  - persistence loss
  - contract / verdict loss

## 9. Stop Rules
- Stop broadening scope once the decision/sink path is proven for Stage 0/2/3/4 core lanes.
- Do not escalate into refactor planning during this survey unless a regression is proven.
- Do not clean unrelated legacy mojibake or historical docs under this order.
- Prefer `fresh run -> fail-only fix -> rerun` over opening a new refactor wave.

## 10. Suggested First Run Sequence
1. Reproduce Stage 0 reference-analysis entry and capture console text exactly.
2. Exercise the smallest Stage 2 rejection path and confirm:
   - console reason
   - `pass_rate_monitor.record_attempt(...)`
   - audit-event path
   - DB / finalizer side effects
3. Exercise one Stage 4 pass or reject path and confirm:
   - director verdict summary
   - post-pass sink writes
   - metrics / audit persistence
