# ROL Live-Merge Global Survey Bounded Execution SSOT

Date: 2026-03-30
Status: draft-live-run-pending
Canonical Path: `docs/2026-03-30/rol-live-merge-global-survey-bounded-execution-ssot.md`
Temp Mirror Path: `(none during active live run)`
Baseline Commit: `9ad4efcc`
Baseline Dirty Summary: `dirty: Stage 3 validator/tests touched; live 0_1 Stage 3/4 artifacts and logs advancing; multiple 2026-03-30 docs untracked`
Source Docs:
- `docs/2026-03-30/rol-live-merge-global-survey-bounded-merge-audit.md`
- `docs/2026-03-30/rol-live-merge-global-survey-rolling-watchlist.md`
- `docs/2026-03-30/0_1-stage4-ep1-6-live-run-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep1-6-fix-execution-ssot.md`

## 1. Scope

This is the bounded execution order derived from:
- the static/global live-merge survey
- the bounded Stage 4 `ep1-6` live-run audit

This document does not:
- authorize immediate code changes during the current run
- mutate `docs/temp/`
- close queue items
- claim repo-wide remediation complete

Execution rule for this document:
- `confirmed-by-live-run` beats `static-high-risk`
- `static-high-risk` beats `static-medium`
- `post-run-only` stays deferred even if important

## 2. Authoritative Contracts

### Manuscript repair
- authoritative source: DB `manuscripts` table
- export mirror: `drafts/ep_*.txt`
- repair order: DB repair -> txt export sync -> DB/txt read-back verification

### Validation / gating repair
- Python may collect/format evidence
- binding and verdict authority must remain explicit at the gate seam
- no hidden downgrade from strong finding to advisory-only PASS path

### Queue / roadmap repair
- active run blocks `docs/temp/` mutation and closure cleanup
- queue closure belongs to post-run only

## 3. Execution Order

### Lane 1 — Confirmed-by-live-run
Name: `stage4-ep1-6-manuscript-amount-bridge-repair`

Priority: P1
Status: ready-but-defer-until-safe-edit-window
Source:
- `0_1-stage4-ep1-6-live-run-bounded-survey.md`
- `0_1-stage4-ep1-6-fix-execution-ssot.md`

Problem:
- EP5 commits to `전액` / `전량`
- EP6 executes `15억 + 4.71억`
- bridging narration is absent

Action:
- manual authoritative repair
- preferred narrative option: add EP6 bridging rather than weaken EP5 if operator wants to preserve EP5 tension

Guardrails:
- DB-first only
- txt-only surgery forbidden
- no Stage 4 rerun in this lane

Validation:
- DB read-back and txt read-back match
- no arithmetic drift from `19.71억 = 15억 + 4.71억`
- no new continuity drift at EP6 opening

### Lane 2 — Static-high-risk
Name: `stage4-binding-and-fix-scope-contract-hardening`

Priority: P1 candidate
Status: execution-candidate
Sources:
- `rol-live-merge-global-survey-rolling-watchlist.md`

Problem cluster:
- TruthGate-style advisories are not fully binding
- `authoritative_fix_scope` violations remain warning-only

Touched area:
- `modules/core/stage4_interview_round.py`

Target:
- strong advisory classes must not silently end as plain `PASS`
- invalid/blank fix scope must force a stronger gate action than warning-only

Validation:
- targeted regression on plain-PASS coercion / retry / reject path
- no regression in existing `PASS_WITH_FIX` happy path

### Lane 3 — Static-high-risk
Name: `consensus-timeout-pass-seam-hardening`

Priority: P1 candidate
Status: execution-candidate
Sources:
- `rol-live-merge-global-survey-rolling-watchlist.md`

Problem:
- under mass timeout, consensus can collapse into synthetic PASS with `confidence=0.5`

Touched area:
- `modules/domain/agents/consensus_validator.py`
- possible downstream guard seam if needed

Target:
- timeout/error fallback must not impersonate real consensus PASS
- downstream contract must distinguish degraded validation from true acceptance

Validation:
- synthetic timeout regression tests
- confidence and verdict contract tests

### Lane 4 — Static-medium
Name: `sink-contract-normalization`

Priority: P2
Status: execution-candidate
Sources:
- `rol-live-merge-global-survey-rolling-watchlist.md`

Problem cluster:
- shared-cursor authoritative telemetry writes
- `episode_production.jsonl` writer/schema drift

Touched area:
- `modules/core/db_manager.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`

Target:
- local-cursor compliance on authoritative sink writes
- single normalized episode key contract for `episode_production.jsonl`

Validation:
- sink read/write regression
- consumer compatibility checks

### Lane 5 — Static-medium
Name: `runtime-authority-and-init-seam-hardening`

Priority: P2
Status: execution-candidate
Sources:
- `rol-live-merge-global-survey-rolling-watchlist.md`

Problem cluster:
- Stage 3 app-level lazy-init authority overlap
- duplicated async dispatch glue
- OneStop human-interactive failure recovery inside automation

Touched area:
- `modules/core/stage3_orchestrator.py`
- `main_a.py`

Target:
- make domain-state producer ownership explicit
- reduce duplicated dispatch seam
- isolate or document human-interactive recovery boundary

Validation:
- boot/init contract tests
- OneStop/Stage 2 flow sanity checks

### Lane 6 — Static-medium
Name: `desktop-operator-truth-alignment`

Priority: P2
Status: execution-candidate
Sources:
- `rol-live-merge-global-survey-rolling-watchlist.md`

Problem cluster:
- phantom system-tab settings
- model/API-key hint drift

Touched area:
- `geuldobi-desktop/src/index.html`
- `modules/api/process_runner.py`
- `modules/core/models_config.py`
- related desktop/runtime config seam

Target:
- remove or clearly mark non-effective settings
- align visible UI truth with actual runtime truth

Validation:
- settings round-trip audit
- packaged/dev truth checks

### Lane 7 — Post-run-only
Name: `queue-roadmap-closure-sync`

Priority: P2
Status: deferred-post-run-only
Sources:
- `rol-live-merge-global-survey-rolling-watchlist.md`

Problem:
- temp roadmap is stale versus actual queue state

Why deferred:
- active live-run governance blocks `docs/temp/` mutation and queue cleanup

Target after run:
- sync queue state
- refresh roadmap
- close or reclassify stale temp items

## 4. Immediate Recommendation

Recommendation now:
1. keep the current run intact
2. preserve this document as bounded execution order
3. if a safe edit window opens before post-run implementation, Lane 1 is the first manual repair candidate
4. otherwise, wait for run completion and then realize Lanes 1 -> 7 in order

## 5. Deferred / Not in This SSOT

The following are intentionally not promoted here:
- EP5 / EP6 metaphor duplication
- `18년 치` vs `20년간`
- EP6 ending-density tweak
- lower-confidence watchlist items from validator/persistence/harness/UI lanes

Reason:
- they are real but not ahead of the current P1/P1-candidate stack

## 6. Closure Criteria

This bounded execution SSOT is ready for realization when all are true:
1. the current live run reaches a safe realization window
2. source docs still match workspace truth after a fresh 3-pass re-audit
3. no contradictory live-run evidence demotes or reorders the lanes

Per-lane closure:
- Lane 1 closes only after DB/txt read-back alignment
- Lanes 2-6 close only after targeted regression and contract verification
- Lane 7 closes only after temp queue / roadmap sync is actually performed post-run

## 7. Guardrails

- no `docs/temp/` mirror while the active run remains live
- no queue cleanup during active run
- no "resolved" label until a post-run re-audit
- if fresh live-run evidence contradicts this ordering, re-audit before realization

## 8. 3-Pass Audit Record

Pass 1 — Source alignment:
- checked the execution order against the bounded merge audit and the two source survey docs
- re-confirmed the manuscript authority correction in the Stage 4 EP1-6 fix SSOT

Pass 2 — Ordering logic:
- ensured live-confirmed repair precedes static hardening
- kept post-run-only queue closure separate from executable lanes

Pass 3 — Governance fit:
- preserved `draft-live-run-pending`
- no temp mirror
- no closure claim

Confidence: 96%
