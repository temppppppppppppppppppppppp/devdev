# Stage 4 Director facade signature mismatch 3-pass audit

Date: 2026-03-18
Status: final; investigation-only
Canonical Path: `docs/2026-03-18/stage4-director-facade-signature-mismatch-3pass-audit.md`
Temp Mirror Path: `none`
Commit State:
- Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`
- Baseline Dirty Summary: `dirty: 12 tracked, 8 untracked; hotspots: docs/2026-03-18/, modules/core/response_schemas.py, modules/domain/agents/base_agent.py, projects/0_260318/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `none`
Evidence Artifacts:
- `projects/0_260318/logs/session/ui_events.jsonl`
- `projects/0_260318/logs/session_20260318_125200.log`
- `projects/0_260318/logs/runtime_audit_summary.json`
- `projects/0_260318/project_data.db`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_orchestrator.py`
- `main_a.py`
- `tests/test_director_modules.py`
- `tests/test_stage4_interview_round.py`
Side-Effect Coverage: covered
Temp Queue State: `docs/temp/` contains `README.md` only; no active execution mirrors
Confidence After 3-Pass Audit: `97%`

---

## 1. Intent

- Investigate the Stage 4 production failure reported on project `0_260318`.
- Bound the root cause to live code and persisted runtime evidence.
- Document operator-visible impact and persistence side effects without starting implementation.

Non-goals:
- no code patch
- no execution SSOT or temp mirror creation
- no narrative-pipeline audit

---

## 2. Baseline Facts

### 2.1 Session-level reproduction evidence

The failure reproduced repeatedly in the same session:

- `projects/0_260318/logs/session/ui_events.jsonl`
  - seq `348`: `Stage 4 V2 오류: Director.select_and_judge_ensemble() got an unexpected keyword argument 'decision_core'`
  - seq `349`: immediately followed by `✅ [Stage 4] 원고 완료 (0화 생산)`
  - seq `351`: pipeline continues to `Arc 2/60 frontier 전진`
  - seq `490`, `491`, `493`: same error/success/continue pattern repeats
  - seq `632`, `633`, `637`: same error/success/continue pattern repeats again

- `projects/0_260318/logs/session_20260318_125200.log`
  - line `2432`
  - line `4832`
  - line `6249`
  - all three lines record the same `unexpected keyword argument 'decision_core'` failure

### 2.2 On-disk and DB truth after the failed run

Collected from `projects/0_260318/` and `project_data.db`:

- `drafts/` contains no manuscript files
- `manuscripts` table: `0` rows, `max(ep_num)=0`
- `episode_meta` table: `0` rows, `max(ep_num)=0`
- `blueprints` table: `11` rows, `max(ep_num)=11`
- `stage_attempts` table by stage:
  - stage `2`: `3`
  - stage `3`: `11`
  - stage `4`: `0`
- latest `director_selections` rows are all stage `3`; no stage `4` row was recorded
- `logs/artifacts/` has stage `2` and stage `3` artifacts, but no stage `4` artifact subtree

### 2.3 Runtime summary mismatch

`projects/0_260318/logs/runtime_audit_summary.json` reports:

- `episode_production_exists: false`
- authoritative stage coverage is present for stage `3`
- no authoritative stage `4` production sink exists for this run

This matches the DB and filesystem evidence: Stage 4 reached pre-director preparation, but no final manuscript production completed.

---

## 3. Pass 1. Inventory

### 3.1 Runtime call chain hotspots

1. `modules/core/stage4_interview_round.py`
   - Stage 4 runtime call site invokes `self.ctx.agents["director"].select_and_judge_ensemble(...)`
   - the call now passes:
     - `decision_core`
     - `candidate_evidence`
     - `reference_appendix`

2. `modules/domain/agents/director.py`
   - `Director.select_and_judge_ensemble(...)` is the facade used by Stage 4
   - its signature still accepts only:
     - `mandatory_context`
     - `prev_manuscripts_text`
     - `story_context`
   - it does not accept `decision_core`, `candidate_evidence`, or `reference_appendix`

3. `modules/domain/agents/director_ensemble.py`
   - `DirectorEnsembleSelector.select_and_judge_ensemble(...)` does accept the new arguments
   - it actively consumes them through prompt-pack normalization and prompt loading

4. `modules/core/stage4_orchestrator.py`
   - `stage_4_v2_chief_writer(...)` catches broad exceptions
   - it logs the error but does not re-raise it

5. `main_a.py`
   - FrontierLag measures manuscript progress only by `ms_max_after - ms_max_before`
   - because Stage 4 returns after swallowing the exception, FrontierLag logs `원고 완료 (0화 생산)`
   - `arcs_advanced += 1` still executes after the Stage 4 `try/except`, so the controller advances the arc tranche even when manuscript truth did not move

### 3.2 Test coverage hotspots

1. `tests/test_director_modules.py`
   - direct ensemble tests cover `decision_core`, `candidate_evidence`, `reference_appendix`
   - the facade delegation test still exercises only the old argument set

2. `tests/test_stage4_interview_round.py`
   - Stage 4 round tests assert that the new kwargs are assembled and sent
   - the test uses a mocked `director` agent, so it never crosses the real `Director` facade boundary

---

## 4. Pass 2. Semantic Classification

### A. Primary root cause: facade signature drift

The fatal error occurs before Director ensemble delegation.

- Stage 4 caller: updated
- Director facade: stale
- Director ensemble implementation: updated

Because Python validates keyword arguments against the immediate callee first, the runtime fails inside `Director.select_and_judge_ensemble(...)` before `_ensemble.select_and_judge_ensemble(...)` can run.

### B. Secondary defect: fatal Stage 4 exception is downgraded to a soft operator event

`modules/core/stage4_orchestrator.py` logs the exception and returns control without re-raising. Even non-exceptional Stage 4 early-return paths still run `run_post_episode_tasks(...)` before control returns. This makes the caller treat a fatal manuscript-stage failure as a completed Stage 4 cycle.

### C. Operator-surface defect: FrontierLag reports success semantics for a failed stage

`main_a.py` computes `arc_manuscripts` from the manuscript frontier delta only. When the delta is zero after a swallowed exception, the UI still prints:

- `✅ [Stage 4] 원고 완료 (0화 생산)`

and then auto-continues to later arcs.

### D. Observability defect: authoritative Stage 4 attempt sinks are not populated

The failure occurs before Stage 4 writes:

- `stage_attempts` stage `4`
- `director_selections` stage `4`
- `manuscripts`
- `episode_meta`
- stage `4` artifact snapshots

The session still emits Stage 4 pre-validation and advisory logs, so a partial Stage 4 trail exists, but the authoritative production sinks remain empty.

### E. Regression provenance

`git show f39e3fe8` demonstrates that the March 17, 2026 change set updated:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`
- `tests/test_director_modules.py`

but did not update:

- `modules/domain/agents/director.py`

This is the most likely introduction point for the signature mismatch.

---

## 5. Side-Effect Map

### File writes and artifact generation

- Stage `2` and Stage `3` artifacts are written normally under `logs/artifacts/`
- no manuscript file is written to `projects/0_260318/drafts/`
- no stage `4` artifact snapshot is present under `logs/artifacts/`

### DB writes, schema touchpoints, transaction boundaries

- `blueprints` persisted through episode `11`
- `manuscripts` remains empty
- `episode_meta` remains empty
- `stage_attempts` has no stage `4` entry
- `director_selections` has no stage `4` entry

The defect therefore blocks Stage 4 before authoritative production persistence begins.

### JSONL, log, and audit sinks

- `ui_events.jsonl`: failure is operator-visible
- plain session log: failure is repeated and timestamped
- `quality_metrics.jsonl`: stage `4` retrieval observations are still written before the crash
- `runtime_audit_summary.json`: stage `4` production absence is indirectly visible through missing authoritative sinks

### Console and UI output

The operator sees three misleading transitions:

1. fatal Stage 4 error
2. immediate `원고 완료 (0화 생산)` success-style line
3. automatic continuation into the next arc

This makes the failure easy to miss in long runs.

### Rollback, recovery, retry, compensation

- no local Stage 4 retry occurs after the facade error
- current episode production aborts immediately
- outer FrontierLag loop continues with later arcs
- compensation is effectively `none`

### Cache, singleton, global-state, in-memory mutation

- Stage 4 still initializes `StateTracker`, `WorldStateManager`, and `FactLedger`
- blueprint frontier and arc frontier keep advancing
- manuscript frontier stays at `0`

This creates a backlog-skewed project state: design progresses while manuscript production remains blocked.

### Config mutation, env loading, bootstrap fallback behavior

- no config or env mutation was observed as part of this failure path
- not applicable beyond normal runtime bootstrap

---

## 6. Pass 3. Operational Consequence

### Severity

- `P0` for Stage 4 manuscript production on any runtime path that reaches the updated Stage 4 director review call through the `Director` facade

### Blocking condition

- every Stage 4 run that passes `decision_core`-family kwargs into `self.ctx.agents["director"]` will fail before Director review

### Practical impact on `0_260318`

- Arc design advanced to `3`
- Blueprint production advanced to episode `11`
- Manuscript production remained at `0`
- FrontierLag kept expanding backlog despite repeated Stage 4 failure

### Safe next action if implementation is later requested

1. Update `modules/domain/agents/director.py` facade signature and forwarding to match the ensemble contract.
2. Add a facade-bound regression test that calls `Director.select_and_judge_ensemble(...)` with the new kwargs.
3. Stop swallowing fatal Stage 4 exceptions as success-equivalent completions.
4. Ensure FrontierLag treats a swallowed Stage 4 failure as a blocked stage, not as `0화 생산` success.
5. Add earlier failure logging to an authoritative stage `4` sink when manuscript production aborts before persistence.

Because the current user request is investigation and documentation only, those items are recorded here but not turned into an execution SSOT in this turn.

---

## 7. 3-Pass Audit Record

### Pass 1. Structure and scope

- document type matches request: yes
- scope is explicit: yes
- canonical/temp policy is correct: yes
- investigation-only boundary is explicit: yes

### Pass 2. Evidence and consistency

- live code, DB, filesystem, and session logs were checked directly
- commit-state metadata is present
- root-cause claim is bounded to inspected code and runtime artifacts
- side-effect categories were addressed explicitly

### Pass 3. Execution and readability

- operating consequence is explicit
- no implementation authority is implied
- next-action surface is clear without overspecifying a patch plan

Final confidence judgement:

- `97%`
- remaining uncertainty is limited to exact first-bad release lineage before commit `f39e3fe8`; it does not affect the confirmed runtime root cause or the documented blast radius
