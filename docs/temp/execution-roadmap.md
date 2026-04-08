# Active Temp Execution Roadmap

Date: 2026-04-01
Status: active (3-pass re-audited 2026-04-07; fresh full run plus r2 Stage4-only sinkproof still anchor the front proof picture, bounded Stage4/Stage2 follow-up slices landed with focused validation, the Stage3 contract-tightening lane has now also landed its first bounded binding/handoff tranche with focused validation, fresh canary/live proof remains intentionally deferred for the realized front lanes, the later partial-fix merge survey clarified Stage4 as schema/eval anchor with Stage3 and then Stage2 as downstream consumers, the first bounded Stage4 partial-fix tranche has now landed its shared-schema plus trace/eval/readback slice, the first bounded Stage3 partial-fix tranche has now also landed its fix-pack-lite plus eval/advisory slice, the first bounded Stage2 partial-fix tranche has landed its child sink contract, the promoted cross-stage substrate has now also landed its first bounded alias-survival tranche, the Stage3 opening-transition lane has now also landed its first bounded contract/intake tranche, the Stage4InterviewRound owner-surface lane has now landed its first bounded post-select boundary extraction tranche, the Stage0 enrich retirement lane has now also landed its first bounded authority-demotion tranche, and the Stage0 BI/TR production-harness lane has now also landed its first bounded source-of-truth declaration tranche so no unopened code implementation lane remains in the active queue; a fresh `000_ㅇㅇㅇ` Stage4 `ep1` post-run merge audit then confirmed persistence success but exposed PASS-side JSONL/session sink-alignment drift, a bounded `stage4_interview_round.py` logging follow-up landed while closure remains rerun-pending, and a dated 2026-04-08 cross-PC handoff note now captures the push-ready rerun state for another machine; no new P0 surfaced)
Canonical Path: `docs/2026-04-01/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `dirty: 0_0 runtime logs/db/artifacts active; legacy temp queue mirrors present; 2026-03-31 0_0 survey docs untracked`
Resume Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
Resume Drift Summary: `2026-04-07 bounded Stage4 consumer implementation landed in post-pass runtime, the operator explicitly deferred fresh canary/live proof, the queued Stage4 repair follow-up then landed its bounded `db_manager.py` + `bridge_server.py` + `stage4_canary_tools.py` readback-surface patch, the same-day non-wuxia state-lock overreach lane landed its bounded Stage4 intake/post-pass normalization, the broader Stage2 residual lane then landed a bounded `stage2_finalizer.py` child slice for non-wuxia persisted-state cleanup, the Stage3 contract-tightening lane has now landed a bounded first tranche that widens binding escalation and preserves/consumes Stage3 binding metadata across the Stage3 -> Stage4 handoff, the later same-day partial-fix merge survey clarified that shared patch-address and `partial_fix_eval` gaps expand the existing Stage4/Stage3/Stage2 partial-fix lanes rather than justify a new queue topic, the promoted cross-stage substrate then landed its first bounded alias-survival tranche across shared helper plus Stage4 consumer adoption, the Stage3 opening-transition lane then landed its first bounded contract helper/schema/validator/Stage4 intake tranche, the Stage4InterviewRound owner-surface lane then landed its first bounded post-select boundary extraction tranche, the Stage0 enrich retirement lane has now also landed its first bounded authority-demotion tranche across legacy prompt, confirm/save logs, and utility wording, and the Stage0 BI/TR lane then landed its first bounded source-of-truth declaration tranche so the queue no longer has an unopened code implementation lane while canary/live proof remains deferred; a later 2026-04-08 fresh `000_ㅇㅇㅇ` Stage4 `ep1` post-run merge audit confirmed persistence success but exposed PASS-side sink drift, the bounded `stage4_interview_round.py` logging follow-up landed, and the dated 2026-04-08 cross-PC handoff note now captures the rerun-pending continuation state`
Supersedes:
- `docs/2026-03-31/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md`
- `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md`
- `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

This roadmap is the active controller for the current `docs/temp/` execution queue.

This refresh folds in the `r2` Stage4-only sinkproof result, the later analyzer/readback backfill, the numeric authority re-audit, the 2026-04-05 `Stage3 ep2 cutoff accepted` note, the 2026-04-06 Stage2 persistence-authority promotion, the later bounded Stage2 implementation/verification pass, the new 2026-04-06 non-wuxia state-lock overreach execution lane, the 2026-04-07 owner-surface and partial-fix survey stack, the same-day queue promotion pass that converts formerly parked/deferred work into formal pending queue lanes, and the later partial-fix merge survey that keeps schema/eval expansion inside the existing Stage4/3/2 child lanes rather than opening a new queue topic. The queue is now intentionally sorted as:

1. verification-pending realized front work (`Stage4 consumer` -> `Stage4 repair` -> `non-wuxia state-lock overreach` -> `broader Stage2 residual`)
2. active partially realized implementation lanes (bounded follow-up slices before broader refactors)
3. blocked holding and reference-validation lanes
4. historical runtime-positive substrate and utility references (demo canary plus landed Stage4 child lanes)

Working order:

1. `0_0-stage4-consumer-contract-normalization-remediation` (aggregate Stage4 wave; PASS proof already exists, the 2026-04-07 post-pass numeric refresh landed, and this item now stays front-ranked for closure bookkeeping while fresh proof is deferred)
2. `0_0-stage4-repair-contract-normalization-remediation` (shared repair-contract grammar/readback lane; bounded readback-surface promotion landed, so this now remains verification-pending rather than the next unopened code slice)
3. `0_0-stage234-nonwuxia-state-lock-overreach-remediation` (bounded P1 dual-owner lane; Stage2 producer plus Stage4 intake/post-pass tranches are landed, and the remaining work is fresh proof rather than a new broad patch)
4. `0_0-stage2-contract-normalization-remediation` (verification-backed Stage2 residual lane; persistence-authority shells, Flow Guard severity split, and bounded non-wuxia finalizer cleanup are landed, while broader Stage2 normalization remains open)
5. `0_0-stage3-contract-tightening-remediation` (bounded Stage3 functional tranche is now landed; binding escalation widened for high-risk Stage3 seams, binding metadata now survives into `_stage3_meta`, and Stage4 now consumes that metadata as Director/retry pressure while fresh canary proof remains deferred)
6. `0_0-stage4-partial-fix-hardening-remediation` (partially realized Stage4 precision lane; the first bounded schema/trace/readback tranche is landed, it remains the Stage4 anchor for the partial-fix family, and fresh proof plus the later verifier tranche are still pending)
7. `0_0-stage3-partial-fix-hardening-remediation` (partially realized Stage3 child lane; the first bounded fix-pack-lite plus `partial_fix_eval` / advisory sink tranche is landed, it remains the Stage3 consumer lane inside the partial-fix family, and fresh proof plus the later verifier/exhaustion tranche are still pending)
8. `0_0-stage2-partial-fix-hardening-remediation` (partially realized Stage2 child lane; the first bounded fix-pack-lite plus `partial_fix_eval` / advisory sink tranche is landed, it now remains the Stage2 consumer lane inside the partial-fix family, and fresh proof plus the later verifier/exhaustion tranche are still pending)
9. `0_0-stage234-cross-stage-contract-normalization-remediation` (partially realized shared-vocabulary substrate; a first bounded alias-survival tranche is now landed around `constraint_summary` family and current-episode mission packet transport into Stage4, while broader owner/strength work and fresh proof remain deferred)
10. `0_0-stage3-opening-transition-contract-normalization-remediation` (partially realized upstream contract lane; a first bounded tranche now normalizes top-level `opening_transition.type` plus Stage4 intake transport, while broader generator retuning and fresh proof remain deferred)
11. `0_0-stage4-interview-round-owner-surface-reduction-remediation` (partially realized structure-first Stage4 module-boundary lane; first bounded post-select boundary extraction landed, while later gate/attempt families and proof remain deferred)
12. `stage0-treatment-enrich-retirement-remediation` (partially realized Stage0 hygiene lane; first bounded authority-demotion tranche landed while default-off hardening and later retirement/quarantine remain deferred)
13. `stage0-bi-tr-production-harness-normalization-remediation` (partially realized long-horizon Stage0 source-of-truth lane; first bounded source-of-truth declaration tranche is landed, while runtime handoff normalization and later production-harness normalization remain deferred)
14. `0_0-stage2-stage3-stage4-readiness-remediation` (blocked parent lane; cannot outrank executable pending work while the proof-deferred front stack and remaining child slices stay open)
15. `frontier-lag-soak-canary-wave1` (older in-progress reference-validation lane; bounded soak harness work remains queue-valid but still sits below executable contract lanes)
16. `npc-martial-state-substrate-wave1` (blocked soak/substrate lane)
17. `0_0-stage34-ep2-single-episode-demo-canary` (completed utility lane; retained only as historical backing)
18. `0_0-stage4-ep2-advisory-escalation-loop-remediation` (runtime-positive substrate; no longer active queue work)
19. `0_0-stage4-canonical-entity-postselect-remediation` (runtime-positive substrate; no longer active queue work)
20. `0_0-stage4-flashback-continuity-localfix-remediation` (completed runtime-positive substrate; historical backing only)
21. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` (runtime-positive substrate lane; historical backing only)

This order now reflects the stronger runtime picture:

- the fresh full run plus `r2` sinkproof canary prove `ep2` can PASS through Stage4
- the earlier sink hard-fail reading no longer governs the queue
- the `__000403` fresh run closes the post-select continuity and fixpack-finalization child lanes with runtime proof rather than static-only confidence
- the surviving active debt is numeric asset authority / carryover owner-boundary plus the still-open repair-contract grammar lane, not NPC false reject, patch-trace non-exercise, or missing final Stage4 rows
- the 2026-04-06 global P0-P1 sweep found no new cross-pipeline P0; the live P1 picture remains the existing Stage4 front seams plus residual Stage2 contract debt, but the bounded Stage2 persistence truth-loss child tranche itself is now landed and verification-backed
- the new non-wuxia state-lock overreach lane remains ahead of the broader residual Stage2 queue item because it is narrower, operator-facing, and already realized enough to sit proof-pending rather than code-unopened
- the Stage4 repair-contract family still sits closest to the front of the open proof stack as substrate for the residual Stage4 numeric seam
- the broader Stage2 residual SSOT still sits behind the new non-wuxia lane because several bounded child slices are already landed, while broader residual normalization remains open
- once the operator chose to defer fresh proof, the next useful reorder was to separate closure-bookkeeping items from unopened implementation lanes instead of hiding the latter behind parking language
- the promoted Stage3 contract lane now leads the pending upstream stack because the Stage3 partial-fix child still depends on that broader parent
- the Stage4 partial-fix lane is now a partially realized anchor lane for shared `PatchTargetRecord`, `partial_fix_eval`, and Stage4-local `repair_trace` expansion inside the partial-fix family
- the Stage3 partial-fix lane is now partially realized as the next consumer after the Stage4 anchor
- the Stage2 partial-fix lane is now partially realized as the third consumer in that family, and the promoted cross-stage substrate has now also landed its first bounded activation tranche rather than remaining unopened
- the promoted cross-stage substrate still matters, but the later merge survey explicitly kept the partial-fix shared-schema delta inside the existing Stage4/Stage3/Stage2 lanes rather than opening or promoting a separate cross-stage queue owner
- the promoted cross-stage substrate shifted the next unopened code implementation down to the Stage3 opening-transition lane, the landed opening-transition tranche shifted it again to Stage4InterviewRound owner-surface reduction, the landed owner-surface tranche shifted it again to `stage0-treatment-enrich-retirement-remediation`, the landed Stage0 enrich authority-demotion tranche shifted it again to `stage0-bi-tr-production-harness-normalization-remediation`, and the newly landed Stage0 BI/TR source-of-truth declaration tranche removes the final unopened code implementation lane from the active queue
- the Stage4InterviewRound owner-surface lane remains below functional pending work because it is structure-first, but its first bounded post-select extraction is now landed so it no longer counts as unopened
- the Stage0 enrich path remains a temporary workaround retirement lane rather than active canonical path work
- the Stage0 BI/TR production harness remains a long-horizon normalization lane rather than an immediate upstream blocker, but it is now partially realized rather than unopened
- the blocked parent readiness lane no longer outranks executable pending items
- the completed demo/substrate lanes remain in the roadmap only as historical runtime backing; they should not outrank pending implementation lanes

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_0-stage4-consumer-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | partial | aggregate Stage4 contract wave active; fresh full run plus r2 sinkproof captured earlier runtime proof, the 2026-04-07 bounded post-pass refresh patch landed for structured numeric carryover promotion, and fresh canary/live proof is explicitly deferred so closure remains pending |
| `0_0-stage4-repair-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | partial | shared grammar, sink, provenance, and repair readback phantom-mismatch normalization lane is now implementation-landed on the readback surface and remains verification-pending while fresh runtime proof is deferred |
| `0_0-stage234-nonwuxia-state-lock-overreach-remediation` | `docs/2026-04-06/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md` | partial | bounded P1 lane; Stage2 producer tranche plus Stage4 intake/post-pass normalization are now landed with focused regression/static validation, but fresh canary/live proof remains deferred so closure stays pending |
| `0_0-stage2-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | partial | active bounded Stage2 tranche; persistence-authority shells, Flow Guard severity split, and bounded non-wuxia finalizer cleanup are now landed, while broader Stage2 normalization plus fresh runtime closure proof remain deferred |
| `0_0-stage3-contract-tightening-remediation` | `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | partial | Stage3 functional contract lane now has a bounded landed tranche: high-risk binding categories widened, binding metadata persists through Stage3 success handoff, and Stage4 consumes that metadata as real intake pressure; fresh tier-2.5 canary proof remains deferred |
| `0_0-stage4-partial-fix-hardening-remediation` | `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md` | partial | Stage4 precision lane now has a bounded landed tranche: shared `PatchTargetRecord` normalization is anchored, Stage4 patch traces persist `repair_trace` / `partial_fix_eval`, analyzer/readback surfaces consume the new payload, and a later fresh `000_ㅇㅇㅇ` Stage4 `ep1` audit landed a bounded pass-side sink-alignment logging follow-up while explicit verifier proof remains deferred |
| `0_0-stage3-partial-fix-hardening-remediation` | `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md` | partial | Stage3 child lane now has a bounded landed tranche: validator/runtime handoff preserves `fix_pack-lite`, the in-place patch loop persists `partial_fix_eval`, and Stage3 advisory / `_stage3_meta` sinks retain the compact patch contract while fresh proof remains deferred |
| `0_0-stage2-partial-fix-hardening-remediation` | `docs/2026-04-07/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md` | partial | Stage2 child lane now has a bounded landed tranche: PASS_WITH_FIX loop and Arc in-place patching preserve `fix_pack-lite`, shared `PatchTargetRecord` targets reach the local patch prompt, and Stage2 attempt/director sinks retain `partial_fix_eval` while fresh proof remains deferred |
| `0_0-stage234-cross-stage-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | partial | first bounded activation tranche landed; shared helper plus Stage4 consumer adoption now preserve `constraint_summary` family and current-episode mission packet aliases, while broader owner/strength normalization remains deferred |
| `0_0-stage3-opening-transition-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | partial | first bounded tranche landed; Stage3 now normalizes top-level `opening_transition.type`, and Stage4 context/IFC/V75-D now consume that structured contract while broader generator retuning plus fresh proof remain deferred |
| `0_0-stage4-interview-round-owner-surface-reduction-remediation` | `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md` | partial | first bounded post-select boundary extraction landed; `Stage4InterviewRound` owner pressure moved from `160 -> 158` direct methods and from `3 -> 2` `180+ LOC` hotspots while later gate/attempt families remain pending |
| `stage0-treatment-enrich-retirement-remediation` | `docs/2026-04-02/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | `docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | partial | first bounded authority-demotion tranche landed; legacy prompt plus confirm/save/runtime logs now mark enrich as non-canonical semantic rewrite utility while default-off hardening and later retirement remain pending |
| `stage0-bi-tr-production-harness-normalization-remediation` | `docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | partial | first bounded source-of-truth declaration tranche landed; treatment vs BI projection vs DB runtime handoff roles are now explicit, while runtime handoff normalization and later production-harness normalization remain deferred |
| `0_0-stage2-stage3-stage4-readiness-remediation` | `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | blocked | Stage3 no longer dominant blocker; parent lane is now blocked by unresolved Stage4 front seams, the new non-wuxia P1 lane, and the newly promoted Stage2 persistence tranche |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | partial | promoted reference-validation lane; bounded soak harness extension remains authorized but still sits below executable contract lanes |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |
| `0_0-stage34-ep2-single-episode-demo-canary` | `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | completed | operator-directed demo utility; bounded ep2 proof captured; historical backing only |
| `0_0-stage4-ep2-advisory-escalation-loop-remediation` | `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | partial | runtime-positive substrate; still useful for history, but no longer active queue work |
| `0_0-stage4-canonical-entity-postselect-remediation` | `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | partial | runtime-positive substrate; moved the blocker forward but is no longer current queue work |
| `0_0-stage4-flashback-continuity-localfix-remediation` | `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | completed | code landed; static validation closed; completed runtime-positive historical substrate |
| `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` | `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | partial | code landed; static validation closed; runtime-positive historical substrate |

## 3. Dependency Notes

- `0_0-stage34-ep2-single-episode-demo-canary` is a temporary operator-directed utility lane. It already produced the bounded ep2 proof needed for this question and now sits below the active closure stack.
- `0_0-stage4-consumer-contract-normalization-remediation` is now the aggregate Stage4 contract wave and the highest-level dependency for any parent-lane advancement.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` and `0_0-stage4-fixpack-finalization-remediation` are now closed runtime-positive child lanes; their runtime proof remains relevant historical backing for the surviving numeric authority / carryover seam.
- `0_0-stage4-repair-contract-normalization-remediation` is now the closest remaining open substrate after those child-lane closures.
- `0_0-stage234-nonwuxia-state-lock-overreach-remediation` is a new bounded P1 lane. It should stay below the current Stage4 consumer/repair pair, but it now outranks the broader residual Stage2 SSOT because it is narrower, directly operator-facing, and already has clear producer/consumer owners plus targeted test coverage.
- `0_0-stage4-flashback-continuity-localfix-remediation` is now a completed runtime-positive substrate lane rather than an active blocker.
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` now sits as a runtime-positive substrate lane because r2 removed it as the immediate live blocker.
- `0_0-stage234-cross-stage-contract-normalization-remediation` is now a partially realized shared-contract substrate wave; its first bounded activation tranche stays below the proof-deferred front stack, and the later partial-fix merge survey still keeps the thin partial-fix schema delta inside the Stage4/Stage3/Stage2 child lanes rather than here.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` is closed and no longer an active queue item; retain it only as historical proof that typed contradiction lineage now survives the post-select downgrade.
- `0_0-stage4-fixpack-finalization-remediation` is closed and no longer an active queue item; retain it only as historical proof that bounded local fix-pack traces survive the finalization sinks.
- `0_0-stage4-canonical-entity-postselect-remediation` produced positive runtime signal but did not close; it now serves as substrate for the new finalization lane.
- `0_0-stage2-stage3-stage4-readiness-remediation` is no longer waiting on upstream Stage3 normalization evidence; it is blocked by the remaining Stage4 consumer-side seams, the new non-wuxia P1 lane, plus the active Stage2 persistence-authority tranche.
- `projects/0000000000_0405_s2fresh_r1` Stage3 ep2 cutoff confirms the temporary S2 detour can stop here; do not reopen Stage2/3 priority from early-gate anxiety alone.
- `0_0-stage4-ep2-advisory-escalation-loop-remediation` remains useful substrate and now has positive ep2 runtime signal, but it still cannot be closed independently of the broader Stage4 finalization outcome.
- `0_0-stage4-repair-contract-normalization-remediation` should normalize shared naming, provenance, and sink visibility when the queue returns from residual quality/finalization work to grammar cleanup.
- the 2026-04-06 revalidation sharpens that repair lane further: readback phantom mismatches and metadata-absence artifacts are now the concrete open substrate under shared repair grammar.
- `0_0-stage2-contract-normalization-remediation` remains an active bounded tranche, but its broader residual work now sits behind the new non-wuxia state-lock overreach lane.
- `0_0-stage3-contract-tightening-remediation` is now a partially realized Stage3 functional lane; its bounded binding/handoff tranche landed, the immediate next artifact is fresh tier-2.5 canary proof rather than another broad patch, and the later Stage3 partial-fix child still stays below this broader parent.
- `0_0-stage3-opening-transition-contract-normalization-remediation` is now a partially realized upstream contract lane; the first bounded contract/intake tranche landed, and the remaining work is proof plus optional later prompt/validator tightening rather than another immediate broad patch.
- `0_0-stage4-partial-fix-hardening-remediation` is now a partially realized precision-first child lane under the broader Stage4 repair substrate; its first shared-schema/trace/readback tranche landed, the later Stage3 and Stage2 consumer tranches are now also landed, and verifier proof remains deferred on the realized front stack.
- the later partial-fix merge survey keeps shared `PatchTargetRecord` authority plus `partial_fix_eval` aggregation anchored in the Stage4 partial-fix lane rather than opening a new cross-stage queue item.
- `0_0-stage3-partial-fix-hardening-remediation` is now a partially realized targeted child lane under `0_0-stage3-contract-tightening-remediation`; its first fix-pack-lite / eval sink tranche has landed and, per the later merge survey, it remains the consumer between the Stage4 anchor and the now-landed Stage2 sink-parity lane.
- `0_0-stage2-partial-fix-hardening-remediation` is now a partially realized targeted child lane under `0_0-stage2-contract-normalization-remediation`; it still should not outrank the broader residual Stage2 lane, it still follows the Stage4/Stage3 anchor-consumer pair for shared partial-fix schema parity, and its first bounded tranche is now landed.
- `stage0-treatment-enrich-retirement-remediation` is now a partially realized Stage0 hygiene lane; Golden Canary pair pass still does not depend on enrich, and the first bounded tranche only demotes authority rather than expanding runtime ownership.
- `stage0-bi-tr-production-harness-normalization-remediation` is now a partially realized long-horizon Stage0 source-of-truth refactor, not an active runtime blocker.
- `0_0-stage4-interview-round-owner-surface-reduction-remediation` is now a partially realized structure-first Stage4 owner-pressure lane; the first post-select extraction is landed, and later gate/attempt families still keep it below the proof-deferred functional stack.
- `0_0-stage3-semantic-fidelity-remediation` is closed via `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`.
- `frontier-lag-soak-canary-wave1` remains a low-priority in-progress reference-validation lane; it is not a prerequisite for the active 0_0 lanes.
- `npc-martial-state-substrate-wave1` stays blocked and does not constrain any active lane.

## 4. Execution Order

1. `0_0-stage4-consumer-contract-normalization-remediation`
2. `0_0-stage4-repair-contract-normalization-remediation`
3. `0_0-stage234-nonwuxia-state-lock-overreach-remediation`
4. `0_0-stage2-contract-normalization-remediation`
5. `0_0-stage3-contract-tightening-remediation`
6. `0_0-stage4-partial-fix-hardening-remediation`
7. `0_0-stage3-partial-fix-hardening-remediation`
8. `0_0-stage2-partial-fix-hardening-remediation`
9. `0_0-stage234-cross-stage-contract-normalization-remediation`
10. `0_0-stage3-opening-transition-contract-normalization-remediation`
11. `0_0-stage4-interview-round-owner-surface-reduction-remediation`
12. `stage0-treatment-enrich-retirement-remediation`
13. `stage0-bi-tr-production-harness-normalization-remediation`
14. `0_0-stage2-stage3-stage4-readiness-remediation`
15. `frontier-lag-soak-canary-wave1`
16. `npc-martial-state-substrate-wave1`
17. `0_0-stage34-ep2-single-episode-demo-canary`
18. `0_0-stage4-ep2-advisory-escalation-loop-remediation`
19. `0_0-stage4-canonical-entity-postselect-remediation`
20. `0_0-stage4-flashback-continuity-localfix-remediation`
21. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`

Order rationale:

- priority 1 remains the aggregate Stage4 consumer-contract wave for closure bookkeeping because fresh runtime proof is still outstanding, but the 2026-04-07 bounded post-pass refresh patch means new code realization can move below it when canary/live proof is intentionally deferred
- priority 2 remains the repair-contract grammar lane for closure bookkeeping because scope/provenance clarity and readback truth still matter for numeric carryover remediation, but the 2026-04-07 bounded readback-surface promotion means this item is now verification-pending rather than the next unopened code substrate
- priority 3 remains the survey-backed non-wuxia state-lock overreach lane for queue bookkeeping because the bounded Stage4 tranche is now landed, but fresh runtime proof is still outstanding so closure cannot be claimed yet
- priority 4 remains the active Stage2 residual lane because a same-day bounded child slice landed for non-wuxia artifact-truth cleanup, but the broader SSOT still holds deferred normalization and Golden follow-up debt with no fresh closure proof yet
- priority 5 is the promoted Stage3 contract-tightening lane because the Stage3 partial-fix child still depends on that broader parent and its canary gate remains the next broader upstream contract decision
- priority 6 is the Stage4 partial-fix hardening lane because it is now the realized anchor for shared `PatchTargetRecord`, `partial_fix_eval`, and Stage4-local `repair_trace` expansion, and the later fresh `000_ㅇㅇㅇ` post-run merge audit kept the next bounded follow-up inside this same lane as pass-side sink alignment rather than opening a new queue topic, while explicit verifier proof and the later tranche remain pending
- priority 7 is the Stage3 partial-fix hardening lane; it is now a partially realized child lane under Stage3 contract tightening, and the first fix-pack-lite / `partial_fix_eval` sink tranche keeps it as the realized consumer after the Stage4 anchor while later verifier hardening remains pending
- priority 8 is the promoted Stage2 partial-fix hardening lane; it remains the most direct bounded Stage2 child slice under the still-open residual owner lane, the later merge survey still places it behind the Stage4/Stage3 anchor-consumer pair for schema and sink parity, and its first bounded tranche is now landed
- priority 9 is the cross-stage contract substrate wave; shared leverage is real, and its first bounded activation tranche is now landed, but the broader owner/strength work still has a wider blast radius than the narrower pending slices above it
- priority 10 is the Stage3 opening-transition refinement lane; its first bounded contract/intake tranche is now landed, so it remains partial rather than unopened while broader retuning and proof stay deferred
- priority 11 is the partially realized Stage4InterviewRound owner-surface reduction lane; its first bounded post-select extraction is landed, so it stays above Stage0 hygiene for continuity of the structure-first wave but no longer counts as the next unopened slice
- priority 12 is the partially realized Stage0 enrich retirement lane; its first bounded authority-demotion tranche is landed, so it stays explicit in the queue but no longer counts as the next unopened slice
- priority 13 is the partially realized Stage0 BI/TR production harness normalization lane; it remains a larger upstream refactor below the nearer enrich hygiene slice in working order, and code-first continuation should stay inside this active lane rather than claim a new unopened slice
- priority 14 is the blocked parent upstream lane and therefore cannot outrank executable pending work
- priority 15 remains a low-priority promoted reference-validation lane
- priority 16 remains blocked and cannot outrank an executable lane
- priorities 17-21 are completed or runtime-positive historical backing lanes; retain them for evidence, but do not treat them as active work ahead of the pending implementation stack

## 5. Per-Item Status Ledger

### 0_0-stage34-ep2-single-episode-demo-canary

- execution SSOT: `completed`
- primary seams:
  - `run_stage34_canary.py` cannot stop at `ep2`
  - `Stage4-only canary` is non-authoritative after blueprint contamination audit
  - demo needs `frozen ep1 authority + fresh ep2 regeneration` as a bounded utility
- next action:
  - do not resume this lane unless a new operator-directed demo question appears
  - do not treat it as Stage4 closure proof
  - the current ep2 proof question is already served; retain as historical utility only
- temp cleanup action:
  - remove mirror after demo runtime proof is captured or the utility is superseded

### 0_0-stage4-consumer-contract-normalization-remediation

- global Stage4 consumer-finalization survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - intake prose flattening of canonical truth
  - fix-pack provenance and routing ambiguity
  - post-select bounded-repair flattening
  - post-pass split truth across `final_state_updates`, `actual_truth`, and `world_state`
- next action:
  - keep Stage4 paused for broad resume claims
  - record the `projects/00_20260403` fresh full run as positive proof that `ep2` can now reach `PASS` through bounded inplace correction
  - record the `r2` Stage4-only sinkproof canary as positive proof that authoritative Stage4 rows now land in `stage_attempts`
  - stop treating Flashback and NpcDrift as the immediate live blocker pair
  - keep opening-authority alignment bounded to declared transition / replay-suppression enforcement without converting the ep2 local-fix into a global same-location hard lock
  - record the 2026-04-07 bounded post-pass structured numeric refresh landing as the current implementation outcome for this lane
  - treat structured numeric carryover baseline refresh as landed for `actual_truth` plus `final_state_updates` surfaces; remaining work here is runtime measurement, not broad new implementation inside the same lane
  - if fresh canary/live proof remains intentionally deferred, open `0_0-stage4-repair-contract-normalization-remediation` as the next code implementation lane while this item stays verification-pending
  - keep the partially realized Stage3 opening-transition lane deferred unless later runtime evidence shifts the owner boundary
- temp cleanup action:
  - keep mirror while this remains the aggregate Stage4 contract lane; remove only on explicit closure or replacement

### 0_0-stage4-flashback-continuity-localfix-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `completed`
- primary seams:
  - real flashback continuity contradictions are detected but flattened into advisory-only text
  - Flashback structured metadata was not retained across Stage4 fix-pack synthesis
  - locally repairable flashback contradictions could not synthesize bounded local fix contracts from zero
- next action:
  - keep Stage4 paused
  - treat this as completed runtime-positive substrate under the aggregate Stage4 wave, not an active blocker
  - do not treat this seam as license for unconditional same-location opening locks; declared transitions and allowed alternate openings remain valid
  - use the merged runtime evidence as closure backing for this lane's bounded contract, while keeping any broader replay wording below the new numeric carryover seam
- temp cleanup action:
  - remove mirror on the next queue cleanup pass once the aggregate consumer lane no longer needs it as an active child reference

### 0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - compressed `relation_to_protag` canonical tags have no semantic-expansion bridge
  - `NpcDrift` relation-tag drift is escalated too coarsely for this subtype
  - advisory-only relation-tag drift cannot synthesize bounded local fix contracts from zero
- next action:
  - keep Stage4 paused
  - treat this as a runtime-positive substrate/reference seam under the aggregate Stage4 wave
  - use the `r2` sinkproof canary as positive proof that this lane no longer blocks ep2 convergence
  - do not widen into broad NpcDrift rewrite before bounded realization is attempted
- temp cleanup action:
  - keep mirror while this remains a referenced runtime-positive substrate lane; remove only on explicit closure or replacement

### 0_0-stage234-cross-stage-contract-normalization-remediation

- matrix survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - shared vocabulary absence across Stage2/3/4
  - owner ambiguity for repair/finalization and post-pass truth
  - strength inversion and structure-to-prose loss at major boundaries
- next action:
  - treat the 2026-04-07 bounded first tranche as landed across `stage_cross_stage_contract.py` and `stage4_context_builder.py`
  - keep the remaining owner/strength and broader transport work deferred inside this lane rather than widening the first tranche into a broad rename wave
  - with this first tranche landed, the next unopened code realization lane moved to `0_0-stage3-opening-transition-contract-normalization-remediation`
- temp cleanup action:
  - keep mirror while this remains the canonical pending shared-contract substrate; remove only on explicit closure or replacement

### 0_0-stage4-post-select-continuity-contract-normalization-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `completed`
- primary seams:
  - post-select conflict contract preserves too little contradiction subtype precision
  - bounded proper-noun/timeline continuity cases are flattened too similarly to broader rewrite-class collapse
- next action:
  - runtime proof is now captured via `projects/__000403`
  - keep this lane closed as historical backing for typed contradiction lineage through the post-select downgrade
  - do not reopen unless a later fresh run shows subtype/detail loss again
- temp cleanup action:
  - mirror removed on the 2026-04-04 closure pass

### 0_0-stage4-fixpack-finalization-remediation

- bounded survey completed (2026-04-02)
- execution SSOT: `completed`
- primary seams:
  - runtime fix-pack backfill when strong advisory escalation creates the first local repair obligation
  - selective fix-pack preservation/classification when post-select conflict downgrades a provisional pass
- next action:
  - runtime proof is now captured via `projects/__000403`
  - keep this lane closed as historical backing for bounded local fix-pack persistence through the finalization sinks
  - do not reopen unless a later fresh run shows bounded fix-pack loss again
- temp cleanup action:
  - mirror removed on the 2026-04-04 closure pass

### 0_0-stage4-canonical-entity-postselect-remediation

- bounded survey completed (2026-04-01)
- execution SSOT: `partially_realized`
- primary seams:
  - Stage4 post-pass active-pressure alignment to final accepted manuscript truth
  - Stage3 fact-lock institution canonical source priority
- next action:
  - bounded code patch landed
  - focused static validation closed
  - runtime partial proof captured via `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
  - keep Stage4 paused
  - keep this lane as substrate while the new Stage4 finalization lane runs
- temp cleanup action:
  - do not remove mirror until the follow-up Stage4 seam is addressed and a later closure audit completes

### 0_0-stage2-stage3-stage4-readiness-remediation

- ctxnorm_r1 canary complete (2026-04-01)
- Stage3 sub-verdict improved materially and remains non-dominant in the latest canary
- `0000000000_0405_s2fresh_r1` Stage3 ep2 cutoff accepted (2026-04-05)
- parent lane verdict: `blocked`
- next action:
  - do not reopen Stage2/3 hierarchy work
  - wait for the remaining Stage4 consumer-side numeric authority / repair-contract seams and the promoted Stage2 persistence tranche to clear
  - reassess the parent lane only after Stage4 can progress beyond the ep3/ep4 blockers
- temp cleanup action:
  - do not remove mirror until the parent lane advances beyond `blocked/partial`

### 0_0-stage4-ep2-advisory-escalation-loop-remediation

- bounded survey completed (2026-04-01)
- execution SSOT: `partially_realized`
- T1-T3 landed:
  - FlashbackVerifier precision
  - strong advisory operator persistence
  - post_select_conflict detail persistence
- next action:
  - keep Stage4 paused
  - retain as substrate lane
  - runtime signal is now positive on Flashback false-positive suppression
  - keep this lane below the newer numeric asset authority / carryover seam
- temp cleanup action:
  - do not remove mirror until combined closure audit completes

### 0_0-stage4-repair-contract-normalization-remediation

- survey/execution seed completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - shared naming and sink visibility for repair-contract metadata
  - provenance persistence for repair/gate surfaces
  - operator-visible scope-authority hygiene
  - phantom mismatch inflation when repair metadata is missing or inconsistently surfaced at readback time
- next action:
  - keep Stage4 paused
  - treat this as a near-front follow-up lane after the consumer umbrella because numeric carryover remediation still depends on clear repair scope/provenance and operator-visible authority
  - record the 2026-04-07 bounded readback-surface promotion in `db_manager.py`, `bridge_server.py`, and `stage4_canary_tools.py` as the current implementation outcome for this lane
  - treat first-class repair subtype/provenance/scope-authority exposure as landed for snapshot/dashboard/canary summaries; remaining work here is fresh runtime proof plus any later shared-grammar cleanup, not another immediate broad patch inside the same substrate
  - that handoff has now been consumed by the same-day non-wuxia Stage4 tranche landing; if fresh canary/live proof remains intentionally deferred for the active Stage4 pair plus this bounded lane, treat `0_0-stage2-contract-normalization-remediation` as the next unopened code realization lane
  - keep this execution SSOT active until fresh proof or a later closure audit says the remaining grammar debt is resolved
- temp cleanup action:
  - keep mirror while this remains a queued metadata/sink follow-up lane; remove only on explicit closure or replacement

### 0_0-stage234-nonwuxia-state-lock-overreach-remediation

- bounded survey and execution SSOT completed (2026-04-06)
- execution SSOT: `partially_realized`
- primary seams:
  - Stage2 producer-side hardening of non-wuxia soft fatigue into `recovery_scene_required` and opening recovery pressure
  - Stage4 opening-authority hardening that treats soft carryover too close to hard canon
  - Stage4 chain-link persistence that can make mild `physical_state` and routine `pending_actions` sticky
  - Stage3 passive carryover seam only if the first-wave Stage2/Stage4 patch leaves residual genre-blind inherited-state pressure
- next action:
  - keep this lane below the current Stage4 consumer/repair pair
  - Stage2 producer tranche is already landed; do not reopen it unless later runtime evidence shows residual producer-side false hardening
  - 2026-04-07 bounded Stage4 intake/post-pass normalization is now landed across `non_wuxia_recovery_policy.py`, `stage4_context_builder.py`, `stage4_immutable_fact_contract.py`, and `stage4_post_processor.py`
  - keep this lane verification-pending until fresh canary/live proof confirms the soft/hard split on a bounded operator path
  - continue to realize this lane as a bounded dual-owner Stage2 + Stage4 patch rather than a broad cross-stage rewrite
  - if proof remains intentionally deferred for the active Stage4 pair plus this lane, treat `0_0-stage2-contract-normalization-remediation` as the next unopened code realization lane
  - preserve `natural healing`
  - preserve true injury continuity while softening false hard-fail pressure for non-wuxia soft-fatigue cases
  - treat Stage3 as optional follow-on only if Stage2/Stage4 normalization is insufficient
- temp cleanup action:
  - keep mirror while this remains a queued bounded P1 lane; remove only on explicit closure, replacement, or strategic deactivation

### 0_0-stage2-contract-normalization-remediation

- global Stage2 production-consumption survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - mission truth trapped in `tactical_doc` prose
  - Stage2-owned packet alias ambiguity at emission time
  - low-signal or dropped fields (`beat_sequence`, `hybrid_composition`, `semantic_carryover`)
  - residual artifact-truth false closure and observability debt recorded in the Golden bounded survey
  - broader Stage2 normalization remains open even though the bounded persistence-authority child tranche has landed
- next action:
  - do not reopen the landed persistence-authority child tranche unless a fresh live run or new evidence reopens the seam
  - treat bounded non-wuxia finalizer cleanup in `stage2_finalizer.py` as landed for persisted `arc_start_state` / `arc_end_state` truth; accepted non-wuxia artifacts should no longer silently rehydrate `internal_energy` / `realm` / `qi_nature` / `martial_arts`
  - keep this Stage2 item below the current Stage4 consumer/repair pair and below the new non-wuxia P1 lane
  - keep broader mission-authority, alias, dead-field, Golden artifact-truth, and observability follow-up work deferred inside this SSOT
  - before widening into any additional Stage2 owner slice, start from a fresh live-run impact check to confirm the remaining residual after the landed child slices
- temp cleanup action:
  - keep mirror while this broader Stage2 SSOT remains partial; remove only on explicit closure or replacement

### 0_0-stage3-contract-tightening-remediation

- static global Stage3 survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - binding scope gap
  - advisory-heavy enforcement
  - semantically lossy Stage3 -> Stage4 handoff
  - targeted timeline and institution contract coverage gaps
- next action:
  - treat the 2026-04-07 bounded first tranche as landed across `unified_blueprint_validator.py`, `three_phase_blueprint_runtime.py`, `stage3_orchestrator.py`, `stage4_director_runtime.py`, and `stage4_outcome_runtime.py`
  - keep this verification-pending until explicit tier-2.5 canary proof confirms the widened binding contract and Stage3 -> Stage4 metadata pressure on a bounded operator path
  - if fresh proof remains intentionally deferred here, treat the now-landed `0_0-stage3-partial-fix-hardening-remediation`, `0_0-stage2-partial-fix-hardening-remediation`, and `0_0-stage234-cross-stage-contract-normalization-remediation` tranches as active child realizations and move the next unopened code realization lane to `0_0-stage3-opening-transition-contract-normalization-remediation`
- temp cleanup action:
  - keep mirror while this remains a queued partial lane; remove only on explicit closure or replacement

### 0_0-stage3-opening-transition-contract-normalization-remediation

- execution SSOT: `partially_realized`
- primary seams:
  - blueprint opening contract does not yet structurally distinguish direct continuation vs explicit transition vs jump opening
  - Stage4 still has to infer too much opening movement/path semantics from prose and prior ending
  - this is an upstream refinement, not the current direct runtime blocker
- next action:
  - treat the 2026-04-07 bounded first tranche as landed across shared opening-transition helper, `BLUEPRINT_SCHEMA`, Stage3 validator normalization, and Stage4 context/IFC/V75-D intake transport
  - keep broader generator retuning, stronger mismatch hardening, and fresh canary/live proof deferred inside this lane rather than widening the first tranche
  - if proof-first is not pulled back to the front, move the next unopened code realization lane to `0_0-stage4-interview-round-owner-surface-reduction-remediation`
- temp cleanup action:
  - keep mirror while this remains a queued partial lane; remove only on explicit closure or replacement

### 0_0-stage4-partial-fix-hardening-remediation

- bounded survey and execution SSOT completed (2026-04-07)
- execution SSOT: `partially_realized`
- primary seams:
  - Stage4 local and structural repair still lack one stable patch-address contract family
  - `must_fix`, `do_not_regress`, and `success_condition` are normalized as contract text but not enforced by a dedicated post-patch guard
  - exact local edit, structural patch, and broader rewrite selection still split across multiple heuristics
- next action:
  - the first bounded tranche is now landed across shared `PatchTargetRecord` normalization, persisted `repair_trace` / `partial_fix_eval`, and analyzer/readback widening
  - the 2026-04-08 fresh `000_ㅇㅇㅇ` Stage4 `ep1` audit confirmed persistence success but found PASS-side sink alignment drift between `stage_attempts`, `episode_production`, and `logs/session/decisions.jsonl`
  - keep the bounded `stage4_interview_round.py` logging follow-up inside this same lane and treat the next required artifact as rerun proof, not a roadmap reorder
  - keep this verification-pending while fresh proof remains intentionally deferred for the realized front stack plus this new landed tranche
  - leave the dedicated verifier hardening and any broader local-vs-structural policy tightening for the next tranche inside this same lane
- temp cleanup action:
  - keep mirror while this remains a queued partial lane; remove only on explicit closure, deactivation, or replacement

### 0_0-stage3-partial-fix-hardening-remediation

- bounded survey and execution SSOT completed (2026-04-07)
- execution SSOT: `partially_realized`
- primary seams:
  - dedicated verifier hardening still depends on broad re-audit-backed sink outcomes rather than a narrower target check
  - blueprint patching still lacks deeper scene/path preservation guarantees beyond the first bounded handoff tranche
  - retry exhaustion still is not keyed tightly enough to repeated `patch_target_id`
- next action:
  - treat the first bounded tranche as landed across `unified_blueprint_validator.py`, `three_phase_blueprint_runtime.py`, and `stage3_orchestrator.py`
  - keep this verification-pending while fresh proof remains intentionally deferred for the realized front stack plus this landed child tranche
  - leave dedicated verifier and retry-exhaustion hardening for the next tranche inside this same lane
- temp cleanup action:
  - keep mirror while this remains a queued partial lane; remove only on explicit closure, deactivation, or replacement

### 0_0-stage2-partial-fix-hardening-remediation

- bounded survey and execution SSOT completed (2026-04-07)
- execution SSOT: `partial`
- primary seams:
  - Stage2 partial-fix still depends on one repair string rather than structured target metadata
  - Arc patching still lacks stable section/field addresses
  - Stage2 still lacks one explicit contract for exact local fix vs bounded section patch vs broader regenerate
- next action:
  - keep this below the proof-deferred front stack and below `0_0-stage2-contract-normalization-remediation`
  - treat the 2026-04-07 bounded first tranche as landed across `stage2_partial_fix_contract.py`, `stage2_finalizer.py`, and `four_phase_arc_generator.py`
  - keep this verification-pending while fresh proof remains intentionally deferred for the realized front stack plus this landed child tranche
  - leave dedicated verifier/retry-exhaustion hardening inside the next tranche of this same lane
- temp cleanup action:
  - keep mirror while this remains a queued partial lane; remove only on explicit closure, deactivation, or replacement

### stage0-treatment-enrich-retirement-remediation

- Stage0 BI generation / DNA sync / Stage2 consume survey completed (2026-04-02)
- execution SSOT: `partial`
- primary seams:
  - `enrich` is an optional semantic rewrite helper, not a canonical Stage0 pair-pass requirement
  - legacy/manual Stage0 flow can still invoke it via opt-in prompt
  - first bounded authority-demotion tranche is landed, but default-off hardening and later retirement are still pending
- next action:
  - keep this as a partially realized Stage0 hygiene and retirement/quarantine lane
  - keep this below the pending Stage4, Stage2, and Stage3 implementation lanes
  - if this lane is continued, open `default-off hardening` next rather than expanding enrich features
- temp cleanup action:
  - keep mirror while this remains a partial lane; remove only on explicit closure or replacement

### stage0-bi-tr-production-harness-normalization-remediation

- Stage0 BI generation / DNA sync / Stage2 consume survey completed (2026-04-02)
- execution SSOT: `partial`
- primary seams:
  - BI file / treatment / DB bible anchor split-truth
  - dual-artifact production with unstable authoritative boundary
  - Stage2 consume contract depends more on runtime handoff than raw artifact truth
- landed bounded tranche:
  - `_stage0_contract` now declares treatment material source vs BI projection vs DB runtime handoff ownership
  - Stage2 bootstrap now surfaces the runtime handoff contract explicitly
- next action:
  - keep this as a partially realized long-horizon Stage0 source-of-truth and production-harness normalization lane
  - keep this below `stage0-treatment-enrich-retirement-remediation` and below the pending Stage4, Stage2, and Stage3 implementation lanes
  - continue `runtime handoff normalization` next rather than widening into a broad builder rewrite
- temp cleanup action:
  - keep mirror while this remains a partially realized lane; remove only on explicit closure or replacement

### 0_0-stage4-interview-round-owner-surface-reduction-remediation

- bounded survey and execution SSOT completed (2026-04-07)
- execution SSOT: `partial`
- primary seams:
  - `Stage4InterviewRound` direct-method pressure is reduced but still above the workspace owner-pressure line
  - the post-select family is now extracted, but `_normalize_director_gate_semantics` and `_append_episode_log` still concentrate distinct runtime families in the owner shell
  - the current extracted runtime siblings plus the new post-select owner prove the boundary pattern is accepted, but the owner still carries too much gate and sink-local responsibility
- next action:
  - keep this below the pending functional Stage4/Stage2/Stage3 stack plus the precision-first partial-fix lanes
  - if structure-first implementation continues, open the gate-semantics family next rather than reopening the landed post-select tranche
  - keep boundary extraction behavior-preserving and avoid same-file helper growth
- temp cleanup action:
  - keep mirror while this remains a partially realized structure lane; remove only on explicit closure, deactivation, or replacement

### frontier-lag-soak-canary-wave1

- next action:
  - keep this as a low-priority promoted reference-validation lane
  - do not let it outrank executable contract or normalization work
- temp cleanup action:
  - remove mirror on explicit closure or replacement

### npc-martial-state-substrate-wave1

- next action:
  - stay blocked pending fresh evidence
- temp cleanup action:
  - remove mirror only after reactivation decision or formal closure

## 6. Cleanup Rule

- canonical execution SSOTs remain in dated `docs/`
- temp mirrors remain the active queue only until each item is realized or formally closed
- when the queue is exhausted, remove:
  - temp execution SSOT mirrors
  - `docs/temp/execution-roadmap.md`
  - `docs/temp/queue-state.json`

## 7. 3-Pass Audit Record (Refresh)

### Pass 1. Structure and Scope

- queue inventory updated to include the new aggregate Stage4 contract lane
- queue inventory updated again to include the new single-episode demo utility ahead of broader closure work
- queue inventory updated again to include the new bounded non-wuxia state-lock overreach execution lane
- queue inventory updated again to include the newly promoted Stage4InterviewRound owner-surface reduction lane
- queue inventory updated again to include the newly promoted Stage4/3/2 partial-fix hardening stack
- queue inventory updated again to record the Stage3 opening-transition lane as partially realized after its first bounded contract/intake tranche landed
- the later partial-fix merge survey clarified that the stack expands existing lanes instead of adding a new queue topic
- new Flashback continuity child lane added directly under the aggregate Stage4 lane
- NpcDrift child lane kept directly below it as the next bounded seam
- existing Stage4 lanes kept as substrate rather than removed
- parent readiness lane remains blocked behind the active Stage4 pair, the new non-wuxia lane, and the broader residual Stage2 lane

### Pass 2. Evidence and Consistency

- canonical and temp paths for the new aggregate lane verified against filesystem
- canonical and temp paths for the new single-episode demo lane verified against filesystem
- canonical and temp paths for the new non-wuxia execution lane verified against filesystem
- canonical and temp paths for the newly promoted owner-surface lane verified against filesystem
- canonical and temp paths for the newly promoted partial-fix hardening stack verified against filesystem
- ordering is consistent with the latest Stage4 consumer-finalization survey, the latest ep2 bounded canary failure, and the new 2026-04-06 bounded survey plus execution SSOT for non-wuxia state-lock overreach
- the 2026-04-07 workspace reinspection was later consumed by a same-day bounded Stage4 tranche landing for the non-wuxia lane, so the item remains partial because runtime proof is still deferred rather than because the Stage4 code is unopened
- the 2026-04-07 partial-fix survey stack is real and precision-first, but the later merge survey makes Stage4 the anchor owner, Stage3 the next consumer, and Stage2 the last consumer without opening a new queue topic
- the 2026-04-07 owner-surface survey confirms the new lane is real but structure-first, so it remains below the functional pending stack
- the 2026-04-07 Stage0 enrich implementation pass is reflected as partial rather than pending, and the later same-day Stage0 BI/TR implementation pass now also makes that lane partial rather than unopened
- blocked and historical legacy items were left in place while the active partial lanes stayed re-ranked around bounded implementation readiness

### Pass 3. Execution and Readability

- per-item status ledger updated with concrete next actions
- dependency chain is explicit: proof-deferred Stage4 consumer -> Stage4 repair -> bounded non-wuxia state-lock overreach -> broader Stage2 residual lane -> active Stage3 contract lane -> Stage4 partial-fix anchor -> Stage3 partial-fix consumer -> Stage2 partial-fix consumer -> broader cross-stage/context/Stage0 lanes -> blocked parent readiness -> reference-validation lane -> historical substrate lanes
- new bounded non-wuxia P1 lane remains inserted without disturbing the current Stage4 front pair
- broader residual Stage2 lane remains below the new non-wuxia lane
- the active partial lanes remain ordered by bounded implementation readiness plus the later Stage4-anchor/Stage3-consumer/Stage2-consumer dependency clarified by the merge survey
- the partial-fix hardening stack now stays explicit as Stage4 anchor -> Stage3 consumer -> Stage2 consumer without claiming closure over the proof-deferred front stack
- the Stage0 enrich lane now sits as a landed bounded authority-demotion slice, and the later Stage0 BI/TR tranche means no unopened code realization remains in the current queue snapshot
- the promoted Stage4 owner-surface reduction lane remains below the functional pending stack and above Stage0/reference-only work even after its first tranche lands
- no overreach: demo utility not promoted to closure proof, Stage4 resume not declared

Confidence: `97%`
