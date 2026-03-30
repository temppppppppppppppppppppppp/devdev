# ROL Live-Merge Global Survey Bounded Merge Audit

Date: 2026-03-30
Status: draft-live-run-pending
Canonical Path: `docs/2026-03-30/rol-live-merge-global-survey-bounded-merge-audit.md`
Temp Mirror Path: `(none during active live run)`
Baseline Commit: `9ad4efcc`
Baseline Dirty Summary: `dirty: Stage 3 validator/tests touched; live 0_1 Stage 3/4 artifacts and logs advancing; multiple 2026-03-30 docs untracked`
Source Docs:
- `docs/2026-03-30/rol-live-merge-global-survey-rolling-watchlist.md`
- `docs/2026-03-30/0_1-stage4-ep1-6-live-run-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep1-6-fix-execution-ssot.md`

## 1. Scope

This document merges:
- static code/process findings from the global live-merge survey
- bounded live-run evidence from `0_1` Stage 4 `ep_0001` through `ep_0006`

This document does not:
- close the active live run
- mutate `docs/temp/`
- claim repo-wide remediation complete
- authorize mid-run queue cleanup

Authority rule:
- static survey findings remain valid independently of the active run
- live-run evidence outranks static inference on the bounded `ep1-6` manuscript slice
- closure claims still wait for post-run merge completion

## 2. Merge Inputs

### Input A: Static / Global
Primary source: `rol-live-merge-global-survey-rolling-watchlist.md`

Top action-bearing seams carried forward:
- `AB-1` Stage 3 app-state lazy-init authority overlap
- `AB-2` Stage 2 / OneStop automation-human recovery overlap
- `AB-3` Consensus timeout can collapse into synthetic PASS
- `AB-4` Stage 4 advisory findings are not fully binding
- `AB-5` Stage 4 `authoritative_fix_scope` violation remains warning-only
- `AB-6` authoritative telemetry writes still use shared cursor
- `AB-7` `episode_production.jsonl` schema drift (`ep` vs `ep_num`)
- `AB-8` temp roadmap stale against active queue
- `AB-9` desktop phantom system settings
- `AB-10` desktop model/API-key truth drift

### Input B: Live-Run / Bounded
Primary source: `0_1-stage4-ep1-6-live-run-bounded-survey.md`

Live-confirmed bounded findings:
- `P1-01` EP5 -> EP6 order amount contradiction
- `P2-01` EP5 / EP6 metaphor duplication
- `P2-02` `18년 치` vs `20년간` wording drift
- `P2-03` EP6 ending density weakness

Live-confirmed bounded non-findings:
- no P0 blocker in `ep1-6`
- no encoding/placeholder corruption in `drafts/ep_0001.txt` through `ep_0006.txt`
- capital arithmetic in `ep1-6` remains internally coherent
- Stage 4 conflict gate blocked real numeric/config drift in EP3 and EP5

## 3. Merge Decision

Merge result:
- one live-confirmed manuscript issue rises above watchlist level
- three static high-risk seams remain execution candidates even without fresh runtime failure proof
- the rest remain bounded watchlist or post-run closure work

Key interpretation:
1. The active Stage 4 run did not invalidate the static survey.
2. The bounded live-run slice added one concrete, operator-visible manuscript defect family.
3. The most dangerous repo-wide pattern is still weak authority/binding at validation and sink boundaries.

## 4. Severity Ladder After Merge

### Confirmed-by-live-run

#### M-1. P1
EP5 -> EP6 order amount contradiction in the real manuscript slice.

Evidence:
- `ep_0005.txt` explicit `전액` / `전량`
- `ep_0006.txt` actual split `15억 + 4.71억`
- no bridging narration between the two commitments

Reason:
- this is no longer an abstract validator concern
- it already escaped into live-run artifact truth

Disposition:
- bounded manual authoritative repair
- DB-first manuscript repair, then txt export sync

### Static-high-risk

#### S-1. High
Consensus timeout synthetic PASS seam.

Evidence:
- `modules/domain/agents/consensus_validator.py`

Reason:
- validation can degrade into nominal PASS under mass timeout/load
- this is a trust-boundary failure, not mere observability debt

Disposition:
- execution candidate
- no live proof required to justify hardening

#### S-2. High
Stage 4 advisory findings remain non-binding in plain PASS paths.

Evidence:
- `modules/core/stage4_interview_round.py`

Reason:
- TruthGate-style findings can influence the Director context without guaranteeing `PASS_WITH_FIX` or forced retry

Disposition:
- execution candidate

#### S-3. High
Stage 4 `authoritative_fix_scope` violation is warning-only.

Evidence:
- `modules/core/stage4_interview_round.py`

Reason:
- repair can continue after blank/invalid fix scope contracts

Disposition:
- execution candidate

### Static-medium / structural

#### T-1. Medium
Stage 3 lazy-init authority overlap on app-level state.

#### T-2. Medium
Stage 2 / OneStop duplicated dispatch + human-interactive recovery inside "automatic" pipeline.

#### T-3. Medium
Authoritative telemetry sink still uses shared cursor in `save_stage_attempt` / `save_ui_event`.

#### T-4. Medium
`episode_production.jsonl` multi-writer schema drift.

#### T-5. Medium
Desktop system-tab phantom settings and model/API-key truth drift.

Disposition for T-series:
- execution candidates, but lower than S-series unless fresh runtime evidence escalates them

### Post-run-only

#### P-Run-1. Medium
Temp roadmap / queue sync closure.

Reason:
- the stale roadmap is real
- but live-run governance still blocks `docs/temp/` mutation and queue cleanup during the active run

Disposition:
- defer until run completion

## 5. Audit of Existing Stage 4 EP1-6 Repair Lane

The bounded Stage 4 repair lane remains valid after merge, with one important correction already applied:
- manuscript authority is DB `manuscripts` first
- `drafts/ep_*.txt` is export mirror only

Result:
- the bounded repair lane for `P1-01` is still actionable
- but execution must follow `DB authoritative repair -> txt export sync -> read-back verification`

## 6. Bounded Execution Implications

The merged audit supports a bounded execution SSOT now.

What can be planned now:
- manuscript repair lane for the live-confirmed `ep1-6` issue
- static high-risk hardening lanes for validation/binding/seams

What must still wait:
- `docs/temp/` mirror refresh
- queue closure
- aggregate roadmap cleanup
- "resolved" or "regressed" final labels

## 7. Recommended Execution Order

1. `confirmed-by-live-run` manuscript repair lane:
   - EP5 -> EP6 order amount contradiction
2. `static-high-risk` Stage 4 binding + fix-scope contract hardening
3. `static-high-risk` consensus-timeout synthetic PASS hardening
4. `static-medium` sink contract normalization
5. `static-medium` runtime authority/init seam hardening
6. `static-medium` desktop operator-truth alignment
7. `post-run-only` roadmap/queue closure sync

## 8. Non-Promoted Watchlist

The following stay below execution priority for now:
- EP5 / EP6 metaphor duplication
- `18년 치` vs `20년간`
- EP6 ending density
- single-empty-scene threshold gap
- dead-NPC advisory string fragility
- `capital_unit` mixed-packet skip
- `arc_timeline_alignment` single-source dependence
- `quality_metrics.jsonl` authority classification gap
- `AuditService` buffer clear lock asymmetry
- `runtime_audit` trim-window asymmetry
- `PassRateMonitor` double-save possibility
- `metrics_collector.save_metrics()` call-path ambiguity
- `run_pytest_lowmem.py` missing `PYTHONIOENCODING=utf-8`
- harness test/debt watchlist items

## 9. Final Audit Verdict

Verdict: `bounded execution justified`

Reason:
1. The live-run slice produced one real manuscript defect that is small but concrete.
2. The static survey still contains several high-risk seams at validation authority boundaries.
3. The merged picture is now strong enough for a bounded execution SSOT.
4. The active run blocks closure mechanics, not bounded planning.

## 10. 3-Pass Audit Record

Pass 1 — Source fidelity:
- checked merged claims against the rolling watchlist and bounded Stage 4 survey
- re-confirmed the DB-authoritative manuscript contract in the Stage 4 fix SSOT

Pass 2 — Merge logic:
- separated live-confirmed findings from static-only findings
- separated executable items from post-run-only items

Pass 3 — Governance fit:
- preserved `draft-live-run-pending`
- no `docs/temp/` mutation
- no closure claim

Confidence: 96%
