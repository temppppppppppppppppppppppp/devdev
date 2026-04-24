# Execution Meta Block Phase2 Dependency Rank Guard 3-Pass Audit

Date: 2026-04-23
Status: final
Scope: narrow prep audit for the second execution-meta-block tranche after phase 1 landed on the feature branch
Mode: implementation-prep audit only; no code mutation in this document
Canonical Path: `docs/2026-04-23/execution-meta-block-phase2-dependency-rank-guard-3pass-audit.md`
Commit State:
- Baseline Commit: `6c794454c077ecc5a73f29f567394ec7a29d8d43`
- Baseline Dirty Summary: `dirty: unrelated projects/test_project/logs/episode_production.jsonl only`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `phase2 narrowed to rank-vs-dependency guardrail only`
Confidence: `97%`

## 1. Intent

Freeze the next safe tranche after execution-meta phase 1.

The goal is not to make dependency order fully operative everywhere yet. The goal is only to prevent an invalid queue state where `roadmap_rank` contradicts explicit `depends_on`.

## 2. Current State After Phase 1

Phase 1 already landed these capabilities:

- canonical execution-meta block parsing
- block-backed `depends_on` extraction into `docs/temp/queue-state.json`
- dependency graph validation for:
  - malformed `depends_on`
  - self-dependency
  - duplicate dependency topics
  - unknown dependency topics
  - dependency cycles

What phase 1 does **not** enforce:

- `roadmap_rank` compatibility with `depends_on`
- automatic topological reordering
- block authority for `status`, `queue_role`, or `roadmap_rank`

## 3. Why Phase 2 Is Needed

The queue now carries dependency truth, but ordering truth is still rank-first.

Today that means a future queue could still be structurally valid while being operationally misleading:

- `A depends_on B`
- but `A.roadmap_rank < B.roadmap_rank`

In that state:

- `queue-state.json` would expose the contradiction
- `build_execution_roadmap.py` would still render the rank-first order
- ClickUp copy would mention dependencies, but the visual ordering could still imply the wrong front item

This is the smallest remaining integrity gap after phase 1.

## 4. Narrow Phase 2 Decision

Phase 2 should implement only this invariant:

- if `item.depends_on` contains `dep`
- and both `item.roadmap_rank` and `dep.roadmap_rank` are integers
- then `dep.roadmap_rank` must be strictly less than `item.roadmap_rank`

Failure policy:

- mismatch is invalid queue state
- validator should fail
- queue refresh should fail fast rather than silently reorder

Phase 2 should **not** implement:

- full topological sorting
- automatic roadmap-rank rewrites
- ClickUp-specific reordering logic
- authority migration of `roadmap_rank` into the execution-meta block

## 5. Proposed Code Surface

Primary implementation surface:

- `scripts/sync_temp_queue_state.py`
  - after dependency graph validation, reject rank-vs-dependency contradictions

Secondary implementation surface:

- `scripts/ops_validator.py`
  - mirror the same invariant against `docs/temp/queue-state.json`

Deferred for now:

- `scripts/build_execution_roadmap.py`
  - keep rank-first rendering
  - rely on the stronger upstream invariant so contradictory input never survives

- `scripts/sync_clickup_queue.py`
  - keep reflecting `depends_on`
  - do not add ordering semantics in phase 2

## 6. Contract and Harness Implications

Phase 2 should carry small documentation follow-ups:

- `docs/implementation/execution-meta-block-contract.md`
  - clarify that `roadmap_rank` remains legacy authority
  - but when `depends_on` exists, `roadmap_rank` is constrained by dependency order and is not an independent ordering source

- `docs/implementation/temp-execution-queue-roadmap-harness.md`
  - add one explicit rule that a `roadmap_rank`/`depends_on` contradiction is invalid and blocks realization until queue artifacts are refreshed

- `docs/implementation/temp-queue-state-contract-v1.json`
  - do not attempt a heavy cross-item JSON-schema rewrite in phase 2
  - instead document the invariant in the adjacent contract/harness and enforce it in queue tooling plus validator

## 7. Test Envelope

Phase 2 should add targeted tests only:

- `sync_temp_queue_state.py`
  - valid dependency-aligned ranks pass
  - dependency rank inversion fails
  - missing `roadmap_rank` on either side stays allowed

- `ops_validator.py`
  - queue-state rank inversion fails with a targeted message
  - clean rank/dependency alignment passes

No broad new queue automation tests are needed unless phase 2 expands beyond the guard.

## 8. Ready-To-Implement Result

The branch is ready for phase 2 implementation because:

- the remaining gap is narrow and well-bounded
- there is no need to reopen phase 1 authority decisions
- the implementation can stay inside queue tooling and validator surfaces
- no runtime or production subsystem behavior changes are required

Recommended next execution order:

1. add the rank-vs-dependency invariant to `sync_temp_queue_state.py`
2. mirror it in `ops_validator.py`
3. add the small targeted tests
4. update the contract and harness wording
5. rerun queue sync and strict validation
