# 0_1 EP8 Artifact-vs-Code Execution SSOT

Date: 2026-03-30
Status: final (3-pass audited; canonical only)
Document Type: execution SSOT
Canonical Path: `docs/2026-03-30/0_1-ep8-artifact-vs-code-execution-ssot.md`
Temp Mirror Path: `(deferred in this turn - docs/temp queue admission and roadmap refresh were not performed)`
Baseline Commit: `92ba1cf7`
Baseline Dirty Summary: `dirty: 0_temp.txt modified; 0_1 episode/log DB sinks advanced; ep_0008 Stage 4 artifact dir untracked`
Resume Commit: `92ba1cf7`
Resume Drift Summary: `same commit during doc synthesis; no implementation landed in this turn`
Source Survey Docs:
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane1-artifact-truth-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane2-code-contract-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane3-persistence-timeline-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane4-master-synthesis-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-merge-audit.md`
Evidence Artifacts:
- `projects/0_1/plans/blueprints/blueprint_0008.txt`
- `projects/0_1/drafts/ep_0007.txt`
- `projects/0_1/logs/artifacts/stage4/ep_0008/attempt_05/selected_before_fix__C_asp_correction.txt`
- `projects/0_1/logs/session_20260330_161043.log`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/project_data.db`
Side-Effect Coverage:
- blueprint DB write and txt export sync
- Stage 4 gate/retry verdict flow
- DB and JSONL persistence
- operator-visible retry diagnostics

## 1. Scope

This SSOT defines the next bounded execution wave for EP8 only.

It covers:

- one artifact-authority repair lane
- one code-contract hardening lane
- one post-fix validation lane

It does not cover:

- broad queue cleanup
- `docs/temp/` roadmap sync
- unrelated Stage 3 or desktop lanes

## 2. Master Decision

EP8 is `mixed`.

Execution must therefore include both:

1. artifact repair for the current episode
2. code hardening for the reusable Stage 4 seam

## 3. Authoritative Contracts

### 3.1 Blueprint repair authority

Primary source:

- DB `blueprints` table

Export mirror:

- `projects/0_1/plans/blueprints/blueprint_0008.txt`

Authority anchor:

- `modules/core/db_manager.py` `save_blueprint()`
- `modules/core/project_manager.py` `_save_blueprint_to_txt()`

Required order:

1. DB `blueprints` authoritative repair
2. txt export sync
3. DB/txt read-back verification

txt-only repair is forbidden.

### 3.2 Stage 4 contract repair authority

Primary code owners:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`

Contract goal:

- no impossible `PASS_WITH_FIX` state
- no stale retry scope after post-select conflict downgrade

## 4. Execution Order

### Lane 1. EP8 blueprint truth repair

Priority: `P1`
Status: `execution-candidate`

Problem:

- EP8 blueprint says `18년 전 과거의 기억`
- EP8 blueprint says `남은 5억 원`
- both contradict authoritative episode truth

Repair target:

- DB `blueprints.ep_num=8`
- synced txt export `plans/blueprints/blueprint_0008.txt`

Required corrections:

1. replace the timeline phrase with a perspective-correct wording
   - acceptable direction:
     - `18년 치 미래의 데이터`
     - `회귀 전 삶의 기억`
     - equivalent wording that preserves the intended effect without temporal inversion
2. replace `남은 5억 원` with `남은 4억 7,100만 원`
3. optional hardening:
   - explicitly preserve `SW인베스트먼트 전담 PB 박성호` wording in the blueprint where it helps suppress recurrence

Guardrails:

- minimum-invasive patch only
- preserve scene order and intended hook
- no broad prose rewrite
- no Stage 4 rerun inside this lane

Validation:

- DB read-back matches edited blueprint payload
- txt export matches DB
- no UTF-8 hygiene violations
- exact contradictory phrases removed

### Lane 2. Stage 4 advisory-escalation and post-select scope hardening

Priority: `P1`
Status: `execution-candidate`

Problem cluster:

1. strong advisory escalation can create `PASS_WITH_FIX` without a viable local fix pack
2. post-select conflict downgrade can lose the runtime `full` rewrite intent downstream

Touched files:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- targeted tests only

Required behavioral outcomes:

1. if strong advisory escalates a plain `PASS`, the next state must be internally coherent
   - either produce a valid local-fix contract
   - or route directly to a non-local retry path without pretending patch-local repair is ready
2. a post-select conflict downgrade must preserve `full`-repair semantics end-to-end
3. operator-visible diagnostics must make the routing reason explicit

Guardrails:

- do not weaken Lane 2 binding semantics already landed
- do not re-open unrelated Stage 4 contract families
- no broad refactor outside the touched files

Validation:

- regression for attempts 1-4 style advisory-escalation loop
- regression for attempt 5 style post-select conflict scope propagation
- no regression in valid local `PASS_WITH_FIX` happy path
- UTF-8 hygiene

### Lane 3. Bounded EP8 rerun and acceptance audit

Priority: `P1`
Status: `defer-until-lanes-1-and-2-land`

Goal:

- rerun EP8 only after the artifact and code lanes above are complete
- verify whether acceptance is now blocked or cleared on clean evidence

Validation targets:

- no reappearance of `18년 전 과거의 기억`
- no `5억 원` residual-cash drift where `4억 7,100만 원` is authoritative
- no repeated `pass_with_fix_contract_missing_patch_targets` loop
- no wrong `inplace` retry after post-select conflict

## 5. Why This Order

This order is chosen because:

- Lane 1 removes deterministic blueprint contradictions
- Lane 2 removes a proven retry-budget and routing defect
- Lane 3 should not be trusted until both of the above are fixed

## 6. Shared Risks and Side-Effects

- shared write path for Lane 1:
  - `project_data.db` blueprints row
  - `plans/blueprints/blueprint_0008.txt`
- shared write path for Lane 2:
  - Stage 4 runtime contract files
  - targeted tests
- shared observability surfaces:
  - `stage_attempts`
  - `director_selections`
  - `episode_production.jsonl`
  - session logs and operator console reasons

## 7. Queue Note

This SSOT is canonical and ready, but its `docs/temp/` mirror is intentionally deferred in this turn.

Reason:

- `docs/temp/` is already governed by an older aggregate roadmap with unrelated active items
- admitting this SSOT into the temp queue without a roadmap refresh would create stale queue authority

If the user wants queue admission next, do this in order:

1. refresh or supersede the active aggregate roadmap
2. mirror this SSOT into `docs/temp/`
3. validate queue integrity

## 8. 3-Pass Audit Record

Pass 1, structure and scope:

- execution SSOT type is correct
- lane boundaries and authorities are explicit
- queue defer reason is explicit rather than implicit

Pass 2, evidence and consistency:

- execution lanes map directly to merge-audit findings
- artifact authority is anchored to DB-first blueprint storage
- code lane targets match the observed contract seam

Pass 3, execution and readability:

- order is actionable
- validation criteria are concrete
- no unrelated queue cleanup was smuggled into the plan

Confidence: 96%
