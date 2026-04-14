# Active Temp Execution Roadmap

Date: 2026-04-01
Status: active (3-pass re-audited 2026-04-14 against the live workspace; the current-head bounded Stage3 debt survey records a conservative predictive contract-debt resolution estimate of `93%`, so fresh Stage3 runtime is now operator-gated rather than auto-presented. Older `ep9 continuation` and proof-rerun wording below remains historical queue state unless explicitly re-authorized.)
Canonical Path: `docs/2026-04-01/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `dfb44351bc41de1243e0def0bfbcb7336bc93388`
Baseline Dirty Summary: `dirty: scene-flex closure edits plus unrelated stage0/material work already present in worktree`
Resume Commit: `8a9490531f7fa2f0527cb70407cdb804d87d7ddd`
Resume Drift Summary: `current-head revalidation after snapshot commit 'stage2: emit cross-stage authority packet' first established the bounded Stage234 Tranche A landing, and the live working tree now also realizes bounded Tranche B Stage3 preferential consume in EpisodeStateArbiter plus BlueprintConstraintCompiler with fallback-safe behavior; the closure audit is now recorded and Tranche C is the next unopened local move inside the Stage234 lane`
2026-04-14 bounded survey + rerun gate override:

- Local audit HEAD: `81b426a688c2a5b6279d254c7746baac1261235b`
- authoritative gate doc: `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- authoritative conservative predictive estimate: `93% resolved`
- do not auto-authorize or auto-present fresh Stage3 runtime unless a canonical current-head bounded survey records `>=90%` predictive contract-debt resolution
- if the estimate falls below `90%`, the only authorized next step is bounded debt-remediation survey / execution-SSOT refresh
- current policy state is `threshold met, authorization not yet consumed`
- current project state has Stage3 blueprints through `ep8` and manuscripts through `ep0`, so local `Stage3 continue` semantics start at `ep9` unless the operator first rewinds the project
- for this local session, do not present `ep9` continuation, the bounded `ep7/ep8` proof rerun, or the broader `ep1-ep8` proof rerun as the automatic immediate local action
- any fresh Stage3 runtime on `projects/000_260412_a`, whether `ep9` continuation or rollback-based proof rerun, now requires explicit operator re-authorization
- rollback target `7` means bounded `ep7/ep8` proof rerun
- rollback target `1` means full `ep1-ep8` proof rerun
- keep the older same-doc `immediate-next` wording below as historical queue state, not as the active local controller

2026-04-14 post-T3/T4.1 local override:

- Local landing HEAD: `81b426a688c2a5b6279d254c7746baac1261235b`
- the formerly front parent `tactical-authority synonym parity` tranche is now landed on the local workspace
- child-lane T2 residual cleanup, full Tranche 3 retry-feedback surgery, and bounded T4.1 Director candidate-summary expansion are now also landed locally
- no additional pre-rerun code tranche is required for the current local path
- remaining T4.2-T4.5 and gated T5 work stay deferred behind fresh rerun evidence
- immediate local next action is no longer auto-presented; fresh Stage3 continuation or proof rerun is operator-gated under the bounded survey rule above

2026-04-14 long-horizon root-cause remediation override:

- Local survey HEAD: `f58059fefd10ed3f41d7bacca3b908dd47ada418`
- the current local operator preference explicitly opens a long-horizon debt-first Stage3 lane instead of treating fresh rerun as the practical next move
- authoritative survey:
  - `docs/2026-04-14/stage3-fundamental-root-cause-bounded-survey.md`
- authoritative execution SSOT:
  - `docs/2026-04-14/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
  - temp mirror: `docs/temp/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
- this lane is bounded and architecture-first, not a `Polaris` / `DecisionKernel` migration
- active target stack:
  1. `EpisodeStateArbiter` / single pre-generation `EpisodeStatePacket`
  2. unified Stage3 prompt-envelope budget
  3. bounded Stage3 boundary split (`EnvelopeBuilder` / `ValidationBoundary` / `RetryCoordinator`)
- for this local session, do not auto-present fresh Stage3 continuation or proof rerun as the practical next action while this debt-first lane remains the chosen mode
- keep the older rerun-gate language and older item ordering below as historical backing unless this new lane is later demoted or partially realized

2026-04-14 post-Tranche-C global authority-alignment follow-up override:

- Local survey HEAD: `f005794b578d68bb855a960778c75ca3f77787a6`
- the post-`Tranche C` branch decision is now exercised in favor of the next bounded cross-stage authority-alignment follow-up rather than fresh rerun or retry-owner-debt reopening
- authoritative survey:
  - `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
- authoritative execution SSOT:
  - `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
  - temp mirror: `docs/temp/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
- this follow-up remains bounded to `Stage2 emit -> Stage3 consume -> Stage4 consume/persist`
- active target stack:
  1. `CrossStageAuthorityPacket` contract plus Stage2 emission
  2. Stage3 preferential consume
  3. Stage4 intake/post-pass reuse
- do not reopen fresh rerun automatically while this follow-up remains the chosen debt-first next move
- do not widen this follow-up into the older broad Stage234 vocabulary lane, `Polaris`, or retry-owner-debt structure work

2026-04-14 Stage234 tranche-closure override:

- Local audit HEAD: `8a9490531f7fa2f0527cb70407cdb804d87d7ddd`
- authoritative audits:
  - `docs/2026-04-14/stage234-global-authority-alignment-tranche-a-current-head-3pass-audit.md`
  - `docs/2026-04-14/stage234-global-authority-alignment-tranche-b-working-tree-3pass-audit.md`
- `Tranche A` is now landed on current `main`
- working-tree `Tranche B` closure audit is now green within bounded scope
- landed effects:
  - new shared `CrossStageAuthorityPacket` contract under `modules/core/`
  - Stage2 finalized arc payload now emits `cross_stage_authority_packet`
  - Stage2 advisory sinks mirror the packet while preserving legacy carryover summary and text surfaces
  - Stage3 now prefers the explicit packet in `EpisodeStateArbiter` and `BlueprintConstraintCompiler` while preserving scattered fallback compatibility
  - focused compatibility canaries remain green on the unchanged `four_phase` / `arc_ensemble` carryover text path
- current next action is no longer `Tranche A`
- current next bounded action is:
  1. decide whether `Tranche C` opens immediately or after another bounded audit
  2. keep any Stage4 follow-up bounded to intake/post-pass reuse only
  3. avoid broader Stage4 redesign, retry-owner debt, or a vocabulary sweep in the same wave
- do not widen this lane into broader Stage4 redesign, retry-owner debt, or a vocabulary sweep during the Tranche C decision

2026-04-10 refresh override:

- the older direct Stage4 consumer/repair P1 wording is now `stale-likely` under current code/test evidence
- roadmap reading should prefer the stale-likely notes plus the current queue text below over any older direct-P1 phrasing that remains in historical summary lines
- the next operator-directed action is one minimal merged proof wave, not more broad Stage4 patching or repeated canaries
- the scene-flex lane is now fully closure-clean on the current workspace state, so its temp mirror is removed and the lane remains only as completed historical backing in this roadmap

2026-04-13 post-run override:

- the fresh Stage3 rerun is now completed on current `main` with `ep4` through `ep6` closed and `success 3 | failure 0`
- the Stage3 child `scenario_density` acceptance slice is now both landed and live-proven on `ep4/ep5`
- the bounded Stage3 parent coherence tranche for `ep6` is now landed on the current workspace: final-retry `PASS < quality_gate` promotes directly to authoritative `PASS_WITH_WARNING`
- the later same-day rerun surfaced a stronger parent-owned residual on `ep7/ep8`: unresolved binding-prevalidation was still churning through local patch and warning acceptance surfaces
- the newest landed Stage3 parent slice now statically kills that family: MAJOR/CRITICAL binding-prevalidation categories force regenerate-only repair, Phase2 blocks inplace reopen after binding rejects, and terminal fallback remains blocked on unresolved binding issues
- the next cheaper parent-owned Stage3 tranche is now also landed:
  - Phase2 retry reopen now prefers explicit `repair_contract` / `scope_authority` over raw `fix_scope` whenever a contract exists
  - unsupported or non-local contract targets fail closed back to regenerate instead of silently re-entering faux-inplace
  - success sinks now preserve `PASS_WITH_FIX` instead of flattening it to plain `PASS`
- the newest operator-safe sequencing override now supersedes that `proof-next` reading:
  - tranche 1 `Stage3RepairRouter` extraction is now committed as an authority-only refactor
  - tranche 2 strict local-fix contract gating is now landed on the live workspace:
    - local patch entry now fails closed without a ready local-fix contract
    - missing authoritative scope, patch target records, `must_fix`, or `success_condition` now route back to regenerate
  - tranche 3 is now landed on the live workspace:
    - the first bounded Stage3 patch-IR lane now exists for `dialogue`, `entity_ref`, `field_value`, `local_phrase`, and `local_sentence`
    - unresolvable target snapshots fail closed before the local patch call
    - broader `scene_block` repair stays on the legacy whole-blueprint lane for now
- at the time of this tranche-3 landing, the immediate-next operator-directed action was the tranche-3 snapshot commit plus one bounded fresh proof rerun for `ep7/ep8`, not a broader live wave
- roadmap reading should prefer this post-run override over older same-day wording that still says the next Stage3 move is only a proof wave
- this override does not by itself close the broader Stage4 verifier/bookkeeping stack

2026-04-13 late formalization override:

- the newer formal `ep8` root-cause survey now supersedes the older `proof rerun next` reading for the current live workspace
- the current `ep8` blocker is best read as primary producer-side contract drift:
  - Stage3 prompt/schema/qualify expectations still admit candidates that later fail on `opening_transition`, `protagonist_state`, structure completeness, and tactical authority
  - this is not a clean Director-primary false-reject family
- the fixed `after 3 patch attempts` terminal wording is also now tracked as a same-family honesty bug because regenerate-before-patch routes can still print it
- at the time of this formalization override, the immediate-next operator-directed action was:
  - one bounded Stage3 producer-side contract-alignment / route-honest failure-surface tranche
  - then one bounded paid `ep7/ep8` rerun
- keep the opening sibling lane as support for bounded `opening_transition` producer-contract parity
- keep the partial-fix child lane out of primary ownership except for route-honesty / locality debt

2026-04-13 late landing override:

- the bounded producer-side contract-alignment / route-honest failure-surface tranche is now landed on current `main`
- landed effects:
  - Stage3 ensemble prompt now carries schema-consistent `episode_number` plus explicit `opening_transition`
  - candidate sanitization / qualification now rejects missing `opening_transition`, empty `protagonist_state`, and under-structured scene shells before validator spend
  - the qualified integrated-scenario floor is now `800`
  - PASS_WITH_FIX failure wording now distinguishes rerouted-before-patch from actually executed local patch attempts
- at the time of this producer-side contract-alignment landing, the immediate-next operator-directed action had returned to one bounded paid `ep7/ep8` rerun
- keep broader generator retuning, Director retuning, and tactical-semantic heuristic surgery deferred until that rerun reopens them

2026-04-13 latest P2/P3 follow-up landing override:

- the newer `s2-s3-s4` residual follow-up survey is now authoritative for the remaining cheap producer-side `P2/P3` debt:
  - `docs/2026-04-13/s2-s3-s4-producer-smarts-p2-p3-followup-survey.md`
- the bounded follow-up tranche it justified is now landed on current `main`:
  - Stage2 shortlist now drops generic mission-packet siblings when an actionable shortlist-worthy candidate already exists
  - Stage3 cheap admission now rejects placeholder `protagonist_state` shells instead of counting any non-empty state label as meaningful
  - Stage4 candidate ordering now prefers stronger manuscript contract traces even when the gate falls back to least-bad degraded-mode ordering
- this latest landing does not widen queue ownership or open a new lane
- at the time of this `P2/P3` landing, the immediate-next operator-directed action still remained one bounded paid `ep7/ep8` rerun

2026-04-13 latest opening-transition parity support landing override:

- the bounded opening sibling support slice is now also landed on current `main`
- landed effects:
  - Stage3 request/sanitize flow now threads `prev_blueprint` into cheap admission
  - declared alias forms now normalize into canonical `opening_transition.type`
  - missing `opening_transition` payloads can now be inferred before cheap admission when local opening-scene continuity is already sufficient
- this support landing stays inside the existing Stage3 parent plus opening sibling ownership
- at the time of this opening-transition parity support landing, the immediate-next operator-directed action still remained one bounded paid `ep7/ep8` rerun

2026-04-13 latest tactical-authority / scene-completeness producer support landing override:

- the bounded producer-support slice is now also landed on current `main`
- landed effects:
  - Stage3 cheap admission now rejects scene shells that still lack actionable `key_events`
  - Stage3 sanitize now rejects obvious unauthorized tactical intrusion events before validator spend when the current episode authority does not already include them
  - the Stage3 producer prompt/checklist now makes both contracts explicit
- this support landing stays inside the existing Stage3 parent ownership and does not open a new lane
- at the time of this tactical-authority / scene-completeness support landing, the immediate-next operator-directed action still remained one bounded paid `ep7/ep8` rerun

2026-04-13 adversarial execution-promotion override:

- the newer adversarial audit plus `x3` follow-up are now authoritative for the front Stage3 residual:
  - `docs/2026-04-13/stage3-producer-contract-tightening-3pass-audit-and-adversarial-review.md`
  - `docs/2026-04-13/stage3-producer-adversarial-followup-x3-addendum.md`
- the bounded producer-side support slice is not yet rerun-ready under hostile reading
- the current stronger blocker is one bounded same-parent `P1`:
  - Korean synonym tactical-intrusion phrasing can survive producer sanitize and validator Python prevalidation when it falls outside the current marker lexicon
- this override does not open a new queue family
- at the time of this adversarial override, the immediate-next operator-directed action was:
  1. one bounded Stage3 parent tranche for tactical-authority synonym parity across producer and validator
  2. then one bounded paid `ep7/ep8` rerun
- keep declared `opening_transition` mismatch and generic verby scene shells as subordinate `P2/P3` watch items behind that tranche

2026-04-13 ten-terminal parallel investigation + synthesis + five-tranche execution SSOT override:

- the 10-terminal parallel investigation order, all 10 deliverables, and the synthesis are now landed as canonical:
  - `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
  - `docs/2026-04-13/t1-producer-initial-prompt-forensics.md` through `t10-stage3-to-stage4-handoff-and-s4-writer-smarts-audit.md`
  - `docs/2026-04-13/s2-s3-s4-runtime-improvement-synthesis.md`
- the synthesis ranks 5 bounded tranches by cross-terminal evidence weight, with `Θ1 opening-transition vocabulary collision` cited by 10 of 10 terminals
- one bounded execution SSOT now formalizes the five-tranche realization plan inside the existing `0_0-stage3-contract-tightening-remediation` parent lane:
  - `docs/2026-04-13/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md`
  - temp mirror: `docs/temp/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md`
- this override does not open a new queue family; the new SSOT sits under the existing parent lane and uses the existing sibling lanes for support
- at the time of this five-tranche planning override, the immediate-next operator-directed action was:
  1. keep the parent `0_0-stage3-contract-tightening-remediation` lane's bounded tactical-authority synonym parity tranche as the front controller
  2. treat `0_0-stage3-quality-closure-five-tranche-remediation` as a child lane with Tranche 1 landed and Proof Gate 1 deferred behind that parent tranche
  3. once the parent tranche lands or is explicitly demoted, take Proof Gate 1 fresh `000_260412_a` ep1–ep8 rerun confirming avg attempt count < 6
  4. only after Proof Gate 1 passes, realize Tranches 2/3/4 in parallel, one snapshot commit each
  5. Proof Gate 2 second rerun
  6. realize Tranche 5 (cost cap and round truncation) only after Proof Gate 2 passes
  7. Proof Gate 3 third rerun confirming cost reduction without verdict regression
- the older same-day adversarial execution-promotion override remains the front-sequencing controller for the parent lane; Tranche 2 may later absorb adjacent vocabulary cleanup, but it does not erase the current parent-front tactical tranche

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
- `docs/temp/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
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

1. `0_0-stage3-state-arbiter-envelope-bounded-remediation` (new bounded long-horizon Stage3 root-cause lane; the current local operator preference now explicitly promotes pre-generation `EpisodeStateArbiter`, unified Stage3 prompt-envelope budget, and bounded Stage3 boundary split ahead of another rerun-first move, and this lane is architecture-first without widening into `Polaris` / `DecisionKernel`)
2. `0_0-stage234-global-authority-alignment-bounded-remediation` (new bounded cross-stage follow-up lane; `Tranche A` Stage2 emission is landed on current `main`, the live working tree now also realizes bounded `Tranche B` Stage3 preferential consume, the closure audit is recorded, and the current next bounded move inside this lane is the Tranche C decision before any broader follow-up)
3. `0_0-stage3-contract-tightening-remediation` (bounded Stage3 functional lane owns the 2026-04-12/13 live rerun blocker family, and the bounded parent-owned fail-only slices are now landed: `blueprint_0002` over-consumption plus `blueprint_0003` replay / canonical institution drift now route through Stage3 replay suppression, expanded institution fact-lock coverage, and regenerate-only `episode_progression` gating, the child retry-plateau breaker now stops low-yield inplace reopening after `PASS_WITH_FIX unresolved` or repeated inplace score/signature plateau, the same-day quality-gate/truth follow-up now blocks `Director PASS < quality_gate` patch reopening while suppressing blind live-HUD `V46` current-state injection during blueprint scoring unless an explicit `blueprint_scoring_hud` is supplied, the narrower same-day completion-summary observability slice is now also landed so Stage3 separates current-run pass-rate authority from cumulative generator pass-rate authority, the earlier bounded parent-owned post-proof `ep6` terminal-quality-gate coherence tranche is now landed, the later same-day parent binding-family static-kill tranche now forces all MAJOR/CRITICAL binding-prevalidation residuals through regenerate-only repair while blocking inplace reopen after binding rejects, the newer same-day contract-driven repair-eligibility / success-projection tranche is now also landed so explicit Stage3 repair contracts outrank raw `fix_scope` during Phase2 reopen and success sinks preserve `PASS_WITH_FIX` semantics, the later same-day formal `ep8` root-cause survey now reclassifies the front residual as primary producer-side contract drift plus misleading failure wording, the bounded producer-side contract-alignment / route-honest failure-surface tranche is now likewise landed, the latest same-day `P2/P3` producer-follow-up tranche is now also landed so Stage2 shortlist honesty, Stage3 placeholder-state hardening, and Stage4 degraded fallback ordering are tighter on live code, tranche 1 `Stage3RepairRouter Extraction`, tranche 2 strict local-fix contract gating, tranche 3 bounded patch-IR, and the formerly front tactical-authority synonym parity tranche are all now landed locally; the authoritative 2026-04-14 bounded survey records `93%` predictive contract-debt closure, so fresh Stage3 continuation or proof rerun is threshold-cleared but still operator-gated rather than the automatic next queue step)
4. `0_0-stage3-opening-transition-contract-normalization-remediation` (partially realized upstream contract lane; the landed opening-authority and capital-boundary follow-up remains valid, and the 2026-04-12 live rerun support slice is now also landed so this sibling now carries immediate-next-day / winter-season / blocked-scene-family carryover truth on the ep2 -> ep3 seam ahead of the next proof wave)
5. `0_0-stage4-consumer-contract-normalization-remediation` (aggregate Stage4 wave; the current rerun shows Stage4 now behaving mainly as downstream verifier: the old ep2 truth-pin family no longer fronts the queue, while ep3 replay / season truth still gets caught post-select, so this item stays near the front for verification bookkeeping but no longer leads the next patch slice)
6. `0_0-stage4-repair-contract-normalization-remediation` (shared repair-contract readback lane; bounded readback-surface promotion landed, the 2026-04-09 static recheck makes the older residual-P1 wording stale-likely, and this item now remains verification-pending behind the now-landed Stage3 ep3 fail-only slice rather than as the next unopened code slice)
7. `0_0-stage234-nonwuxia-state-lock-overreach-remediation` (bounded P1 dual-owner lane; Stage2 producer plus Stage4 intake/post-pass tranches are landed, and the remaining work is fresh proof rather than a new broad patch)
8. `0_0-stage2-contract-normalization-remediation` (verification-backed broader Stage2 lane; persistence-authority shells, Flow Guard severity split, bounded non-wuxia finalizer cleanup, and the later advisory fallback / `ep_num` / carryover-authority truth tranche are now landed on the live workspace, so this lane stays open mainly as proof-pending broader normalization rather than because those older bounded observability seams remain live)
9. `0_0-stage4-partial-fix-hardening-remediation` (partially realized Stage4 precision lane; the first bounded schema/trace/readback tranche and later proof-operational metadata follow-up are landed, the interrupted `ep2` numauth evidence harvest has now been absorbed by a same-day code tranche that lands companion sink truth plus monitor/proof surfacing, it remains the Stage4 anchor for the partial-fix family, and fresh proof plus the later verifier tranche are still pending)
10. `0_0-stage3-partial-fix-hardening-remediation` (partially realized Stage3 child lane; the first bounded fix-pack-lite plus `partial_fix_eval` / advisory sink tranche is landed, the later runtime hardening preserves low-score `PASS` patch state, the latest 2026-04-13 follow-up now blocks low-yield inplace reopening after `PASS_WITH_FIX unresolved` or repeated inplace plateau, a later same-day closure-residual follow-up now accepts advisory-only `scenario_density` residuals as `PASS_WITH_WARNING` without reopening the local patch lane, and the completed rerun now live-proves that exact acceptance path on `ep4/ep5`, so this lane returns to deferred verifier / exhaustion / locality debt rather than front-blocker ownership)
11. `0_0-stage2-partial-fix-hardening-remediation` (partially realized Stage2 child lane; the first bounded fix-pack-lite plus `partial_fix_eval` / advisory sink tranche is landed, it remains the Stage2 consumer lane inside the partial-fix family, and any next child work still waits behind the parent Stage2 proof / observability tranche)
12. `0_0-stage234-cross-stage-contract-normalization-remediation` (partially realized shared-vocabulary substrate; a first bounded alias-survival tranche is landed around `constraint_summary` family and current-episode mission packet transport into Stage4, the compact 2026-04-12 Stage4-first follow-ups are now three landed slices as `Stage4 strategy_feedback_map`, `style_guide anchor fallback reuse`, and `post-select truth-pin / retry-lane hardening`, while the current rerun follow-up now keeps later shared Stage3/S2 extension pending behind the next proof wave after the landed Stage3 ep3 slices)
13. `0_0-stage4-interview-round-owner-surface-reduction-remediation` (partially realized structure-first Stage4 module-boundary lane; first bounded post-select boundary extraction landed, later contract/session/episode/retry/raw-evidence helper work is also landed, and the current live recount still leaves dominant owner pressure at `166 direct methods / 2 180+ / 5 120+`, so proof-first sequencing still outranks renewed structure work)
14. `stage0-treatment-enrich-retirement-remediation` (partially realized Stage0 hygiene lane; first bounded authority-demotion tranche landed while default-off hardening and later retirement/quarantine remain deferred)
15. `stage0-bi-tr-production-harness-normalization-remediation` (partially realized long-horizon Stage0 source-of-truth lane; first bounded source-of-truth declaration tranche is landed, while runtime handoff normalization and later production-harness normalization remain deferred)
16. `0_0-stage2-stage3-stage4-readiness-remediation` (blocked parent lane; cannot outrank executable pending work while the Stage4 front stack, the non-wuxia P1 lane, and the still-open Stage2 child slices remain unresolved)
17. `frontier-lag-soak-canary-wave1` (older in-progress reference-validation lane; bounded soak harness work remains queue-valid but still sits below executable contract lanes)
18. `npc-martial-state-substrate-wave1` (blocked soak/substrate lane)
19. `0_0-stage34-ep2-single-episode-demo-canary` (completed utility lane; retained only as historical backing)
20. `0_0-stage4-ep2-advisory-escalation-loop-remediation` (runtime-positive substrate; no longer active queue work)
21. `0_0-stage4-canonical-entity-postselect-remediation` (runtime-positive substrate; no longer active queue work)
22. `0_0-stage4-flashback-continuity-localfix-remediation` (completed runtime-positive substrate; historical backing only)
23. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` (runtime-positive substrate lane; historical backing only)
24. `0_0-stage3-quality-closure-five-tranche-remediation` (newly opened Stage3 quality-closure child lane backed by the 10-terminal parallel investigation + synthesis at 97% confidence; Tranche 1 opening-transition vocabulary coherence is landed on `main`, and the current local workspace now also carries child-lane T2 residual cleanup, full Tranche 3 retry-feedback surgery, and bounded T4.1 Director candidate-summary expansion, so this lane's remaining T4.2-T4.5/T5 work is deferred behind fresh rerun evidence rather than fronting another pre-rerun code slice; no new queue family)

This order now reflects the stronger runtime picture:

- the fresh full run plus `r2` sinkproof canary prove `ep2` can PASS through Stage4
- the earlier sink hard-fail reading no longer governs the queue
- the `__000403` fresh run closes the post-select continuity and fixpack-finalization child lanes with runtime proof rather than static-only confidence
- the strongest remaining direct Stage4 question is whether the older numeric-authority and repair-readback P1 framing survives a current-HEAD proof wave, not whether Stage4 still lacks final sinks or first-class readback fields
- the interrupted `ep2` numauth evidence harvest still does not reorder the queue: it reaffirmed Stage4 consumer as the semantic owner of numeric authority, the bounded same-day Stage4 partial-fix patch has now landed the proof-channel follow-up for companion sinks / monitor compatibility / numeric surfacing, the next same-day follow-up has now also landed Stage3/Stage2 upstream observability surfacing, and the next need is one merged proof wave that remeasures consumer carryover, repair readback, and Stage3 reach without fanning out into repeated canaries
- the 2026-04-06 global P0-P1 sweep no longer stands alone for direct Stage4 severity: the 2026-04-09 static validity recheck now marks the older consumer/repair P1 wording stale-likely, while the mixed non-wuxia P1 lane plus residual Stage2 contract debt remain live
- the new non-wuxia state-lock overreach lane remains ahead of the broader residual Stage2 queue item because it is narrower, operator-facing, and already realized enough to sit proof-pending rather than code-unopened
- the Stage4 repair-contract family still sits near the front of the open proof stack as a runtime-decision substrate for the residual Stage4 numeric story, not as a reopened broad code patch lane
- the broader Stage2 residual SSOT still sits behind the new non-wuxia lane because several bounded child slices are already landed, while broader residual normalization remains open
- once the operator chose to defer fresh proof, the next useful reorder was to separate closure-bookkeeping items from unopened implementation lanes instead of hiding the latter behind parking language
- the promoted Stage3 contract lane now leads the pending upstream stack because the Stage3 partial-fix child still depends on that broader parent
- the Stage4 partial-fix lane is now a partially realized anchor lane for shared `PatchTargetRecord`, `partial_fix_eval`, Stage4-local `repair_trace` expansion, the later proof-operational metadata follow-up, and the now-landed same-session proof-channel hardening tranche inside the partial-fix family, with fresh rerun proof still pending
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
| `0_0-stage4-consumer-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | partial | aggregate Stage4 contract wave active; the 2026-04-12 live rerun follow-up shows Stage4 now acting mainly as downstream verifier, with the older ep2 truth-pin family improved and the current ep3 replay / season-truth blocker pointing upstream to Stage3, so the next measurement is the rerun after the promoted Stage3 fail-only slice rather than another Stage4-first retry patch |
| `0_0-stage4-repair-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | partial | shared grammar, sink, provenance, and repair readback phantom-mismatch normalization lane is now implementation-landed on the readback surface, and the later raw-evidence plus operator-summary substrate is also landed; the 2026-04-09 static validity recheck says the older residual-P1 wording is now stale-likely under code/test evidence, and the intended next measurement is the same merged proof wave rather than a separate repair-only canary |
| `0_0-stage234-nonwuxia-state-lock-overreach-remediation` | `docs/2026-04-06/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md` | partial | bounded P1 lane; Stage2 producer tranche plus Stage4 intake/post-pass normalization are now landed with focused regression/static validation, but fresh canary/live proof remains deferred so closure stays pending |
| `0_0-stage2-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md` | partial | broader Stage2 normalization lane; earlier persistence-authority shells, Flow Guard severity split, bounded non-wuxia finalizer cleanup, carryover-authority observability surfacing, compare-meta normalization, `arc_design` parity hardening, and the later advisory fallback / `ep_num` / carryover-truth tranche are now landed on the live workspace, while fresh proof plus broader deferred normalization still remain |
| `0_0-stage3-contract-tightening-remediation` | `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md` | partial | Stage3 functional contract lane now has bounded landed tranches plus landed live-workspace truth-first, structural-hardening, and observability slices: success proof sink ordering after committed persistence, Stage3 advisory / retry normalization, `PASS_WITH_FIX` success parity, bounded analyzer sink-alignment coverage parity, replay suppression / canonical institution truth / regenerate-only `episode_progression` gating, current-run vs cumulative pass-rate authority, the later same-day parent binding-family static-kill tranche that routes all MAJOR/CRITICAL binding-prevalidation residuals through regenerate-only repair while blocking inplace reopen after binding rejects, the later same-day contract-driven repair-eligibility / success-projection tranche, the landed three-tranche safe route through bounded patch-IR, the landed producer-side contract-alignment / route-honest failure-surface tranche, and the now-landed Korean tactical-authority synonym parity tranche; the authoritative 2026-04-14 bounded survey records `93%` predictive contract-debt closure, so fresh Stage3 continuation or proof rerun is no longer queue-forced and instead requires explicit operator re-authorization |
| `0_0-stage4-partial-fix-hardening-remediation` | `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md` | partial | Stage4 precision lane now has bounded landed tranches: shared `PatchTargetRecord` normalization is anchored, Stage4 patch traces persist `repair_trace` / `partial_fix_eval`, analyzer/readback surfaces consume the new payload, the later `canary_000_ㅇㅇㅇ_stage4_ep1_sinkproof_r1` rerun proved current-session Stage4 sink alignment clean, a same-day proof-operational metadata follow-up now exposes latest-session Stage4 run metadata in `runtime_audit_summary.json`, the later same-day proof-channel tranche now also lands companion sink truth plus monitor/proof surfacing, and the remaining deferred work is the dedicated verifier/policy tranche plus fresh rerun validation inside the same lane rather than rerun-pending sink drift |
| `0_0-stage3-partial-fix-hardening-remediation` | `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md` | partial | Stage3 child lane now has bounded landed tranches: validator/runtime handoff preserves `fix_pack-lite`, the in-place patch loop persists `partial_fix_eval`, low-score `PASS` patch state now survives retry carry-forward, advisory-only `scenario_density` residuals now settle as `PASS_WITH_WARNING` without reopening the low-yield local patch lane, and the completed rerun now live-proves that acceptance path on `ep4/ep5`, returning this lane to deferred verifier / retry-exhaustion / locality hardening rather than front-blocker ownership |
| `0_0-stage2-partial-fix-hardening-remediation` | `docs/2026-04-07/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md` | partial | Stage2 child lane now has a bounded landed tranche: PASS_WITH_FIX loop and Arc in-place patching preserve `fix_pack-lite`, shared `PatchTargetRecord` targets reach the local patch prompt, and Stage2 attempt/director sinks retain `partial_fix_eval`; this child lane inherits the parent's operator-parked-by-default posture unless explicit reactivation is ordered |
| `0_0-stage234-cross-stage-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md` | partial | first bounded activation tranche landed; shared helper plus Stage4 consumer adoption now preserve `constraint_summary` family and current-episode mission packet aliases, and the compact 2026-04-12 Stage4-first follow-ups are now three landed slices as `Stage4 strategy_feedback_map`, `style_guide anchor fallback reuse`, and `post-select truth-pin / retry-lane hardening`, while the current rerun follow-up now keeps later shared Stage3/S2 extension pending behind the next proof wave after the landed Stage3 ep3 slices |
| `0_0-stage3-opening-transition-contract-normalization-remediation` | `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md` | partial | first bounded tranche landed; Stage3 now normalizes top-level `opening_transition.type`, Stage4 context/IFC/V75-D consume that structured contract, the live-workspace sibling follow-up is also landed for authoritative opening-state intake plus capital-boundary filtering, and the later 2026-04-12 support slice now surfaces immediate-next-day / winter-season / blocked-scene-family carryover truth for the ep2 -> ep3 seam ahead of proof |
| `0_0-stage4-interview-round-owner-surface-reduction-remediation` | `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md` | partial | first bounded post-select boundary extraction landed; later contract/session/episode/retry/raw-evidence helper work is also landed, but current live owner pressure still sits at `166` direct methods with `2` `180+ LOC` and `5` `120+ LOC` hotspots |
| `stage0-treatment-enrich-retirement-remediation` | `docs/2026-04-02/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | `docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md` | partial | first bounded authority-demotion tranche landed; legacy prompt plus confirm/save/runtime logs now mark enrich as non-canonical semantic rewrite utility while default-off hardening and later retirement remain pending |
| `stage0-bi-tr-production-harness-normalization-remediation` | `docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md` | partial | first bounded source-of-truth declaration tranche landed; treatment vs BI projection vs DB runtime handoff roles are now explicit, while runtime handoff normalization and later production-harness normalization remain deferred |
| `0_0-stage2-stage3-stage4-readiness-remediation` | `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | blocked | Stage3 no longer dominant blocker; parent lane is now blocked by unresolved Stage4 front seams, the new non-wuxia P1 lane, and the still-open Stage2 residual/child slices even though the Stage2 lane is now operator-parked by default |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | partial | promoted reference-validation lane; bounded soak harness extension remains authorized but still sits below executable contract lanes |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |
| `0_0-stage34-ep2-single-episode-demo-canary` | `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md` | completed | operator-directed demo utility; bounded ep2 proof captured; historical backing only |
| `0_0-stage4-ep2-advisory-escalation-loop-remediation` | `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | partial | runtime-positive substrate; still useful for history, but no longer active queue work |
| `0_0-stage4-canonical-entity-postselect-remediation` | `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md` | partial | runtime-positive substrate; moved the blocker forward but is no longer current queue work |
| `0_0-stage4-flashback-continuity-localfix-remediation` | `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md` | completed | code landed; static validation closed; completed runtime-positive historical substrate |
| `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` | `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` | partial | code landed; static validation closed; runtime-positive historical substrate |
| `0_0-stage34-scene-flex-contract-normalization-remediation` | `docs/2026-04-09/0_0-stage34-scene-flex-contract-normalization-remediation-execution-ssot.md` | `-` | completed | explicit operator override opened this lane, and the current workspace state now closes tranche-1 residual closure, tranche-2 anti-compression promotion, tranche-3 Wave A/B runtime normalization, and the former parked secondaries; the temp mirror was removed in the 2026-04-10 closure sync and the lane remains only as historical backing |

## 3. Dependency Notes

- `0_0-stage34-ep2-single-episode-demo-canary` is a temporary operator-directed utility lane. It already produced the bounded ep2 proof needed for this question and now sits below the active closure stack.
- `0_0-stage4-consumer-contract-normalization-remediation` is now the aggregate Stage4 contract wave, the highest-level Stage4 dependency for parent-lane advancement, and the first proof-wave demotion decision point.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` and `0_0-stage4-fixpack-finalization-remediation` are now closed runtime-positive child lanes; their runtime proof remains relevant historical backing for the earlier numeric authority / carryover question now under stale-likely review.
- `0_0-stage4-repair-contract-normalization-remediation` is now the closest remaining Stage4 proof-decision substrate after those child-lane closures; do not treat it as a reopened broad grammar patch by default.
- `0_0-stage234-nonwuxia-state-lock-overreach-remediation` is a new bounded P1 lane. It should stay below the current Stage4 consumer/repair pair, but it now outranks the broader residual Stage2 SSOT because it is narrower, directly operator-facing, and already has clear producer/consumer owners plus targeted test coverage.
- `0_0-stage4-flashback-continuity-localfix-remediation` is now a completed runtime-positive substrate lane rather than an active blocker.
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` now sits as a runtime-positive substrate lane because r2 removed it as the immediate live blocker.
- `0_0-stage234-cross-stage-contract-normalization-remediation` is now a partially realized shared-contract substrate wave; its first bounded activation tranche stays below the proof-deferred front stack, the later partial-fix merge survey still keeps the thin partial-fix schema delta inside the Stage4/Stage3/Stage2 child lanes rather than here, and the now-landed `style_guide anchor fallback reuse` plus `post-select truth-pin / retry-lane hardening` slices both belong here because they are producer/consumer and retry-contract seam fixes rather than new standalone Stage4 families.
- `0_0-stage4-post-select-continuity-contract-normalization-remediation` is closed and no longer an active queue item; retain it only as historical proof that typed contradiction lineage now survives the post-select downgrade.
- `0_0-stage4-fixpack-finalization-remediation` is closed and no longer an active queue item; retain it only as historical proof that bounded local fix-pack traces survive the finalization sinks.
- `0_0-stage4-canonical-entity-postselect-remediation` produced positive runtime signal but did not close; it now serves as substrate for the new finalization lane.
- `0_0-stage2-stage3-stage4-readiness-remediation` is no longer waiting on upstream Stage3 normalization evidence; it is blocked by unresolved Stage4 closure bookkeeping, the new non-wuxia P1 lane, plus the active Stage2 residual/child slices while direct Stage4 severity awaits proof-wave confirmation.
- `projects/0000000000_0405_s2fresh_r1` Stage3 ep2 cutoff confirms the temporary S2 detour can stop here; do not reopen Stage2/3 priority from early-gate anxiety alone.
- `0_0-stage4-ep2-advisory-escalation-loop-remediation` remains useful substrate and now has positive ep2 runtime signal, but it still cannot be closed independently of the broader Stage4 finalization outcome.
- `0_0-stage4-repair-contract-normalization-remediation` already landed the shared naming/provenance/readback-surface slice; the remaining question is fresh proof on current HEAD rather than another broad grammar patch.
- the 2026-04-09 static validity recheck now marks the older repair P1 wording stale-likely, so demotion should be decided by proof-wave evidence rather than more static-only edits.
- `0_0-stage2-contract-normalization-remediation` remains open as a broader proof-pending normalization lane, but the older bounded advisory fallback / `ep_num` / carryover-truth residue is now landed on live code; keep it below the Stage4 front stack and below the now-landed Stage3 contract/opening slices until the proof wave finishes.
- `0_0-stage3-contract-tightening-remediation` is now a partially realized Stage3 functional lane; its bounded binding/handoff/source-anchor slices remain landed, the live-workspace truth-first sink-contract slice is now also landed, the 2026-04-12 live rerun follow-up now promotes one bounded fail-only slice on replay suppression / canonical institution truth / ep2->ep3 progression truth before any packet-layering / threshold alignment / canonical-anchor follow-up is reconsidered, and the same-day first-ensemble visibility survey keeps a smaller main-console heartbeat slice inside this same owner rather than opening a new queue family.
- `0_0-stage3-opening-transition-contract-normalization-remediation` is now a partially realized upstream contract lane; the first bounded contract/intake tranche landed, the live-workspace opening-authority / capital-boundary follow-up is now also landed, and the 2026-04-12 live rerun follow-up now uses this lane as the sibling support owner for immediate-next-day / winter-season carryover truth rather than treating it as pure proof deferral.
- `0_0-stage4-partial-fix-hardening-remediation` is now a partially realized precision-first child lane under the broader Stage4 repair substrate; its first shared-schema/trace/readback tranche landed, the later Stage3 and Stage2 consumer tranches are now also landed, the same-day proof-operational metadata follow-up is now also landed for real fresh-run reuse, and verifier proof remains deferred on the realized front stack.
- the later partial-fix merge survey keeps shared `PatchTargetRecord` authority plus `partial_fix_eval` aggregation anchored in the Stage4 partial-fix lane rather than opening a new cross-stage queue item.
- `0_0-stage3-partial-fix-hardening-remediation` is now a partially realized targeted child lane under `0_0-stage3-contract-tightening-remediation`; its first fix-pack-lite / eval sink tranche has landed and, per the later merge survey, it remains the consumer between the Stage4 anchor and the now-landed Stage2 sink-parity lane, the 2026-04-10 aborted `00_000` fresh run promoted it from proof-deferred child to the immediate Stage3 runtime bug owner, the same-day bounded runtime hardening follow-up is now also landed, and the latest structural split keeps the remaining debt here to verifier / exhaustion / locality hardening while parent-owned packet layering moves back up a level.
- `0_0-stage2-partial-fix-hardening-remediation` is now a partially realized targeted child lane under `0_0-stage2-contract-normalization-remediation`; it still should not outrank the broader residual Stage2 lane, it still follows the Stage4/Stage3 anchor-consumer pair for shared partial-fix schema parity, its first bounded tranche is now landed, and it inherits the parent's operator-parked-by-default posture unless explicit reactivation is ordered.
- `stage0-treatment-enrich-retirement-remediation` is now a partially realized Stage0 hygiene lane; Golden Canary pair pass still does not depend on enrich, and the first bounded tranche only demotes authority rather than expanding runtime ownership.
- `stage0-bi-tr-production-harness-normalization-remediation` is now a partially realized long-horizon Stage0 source-of-truth refactor, not an active runtime blocker.
- `0_0-stage4-interview-round-owner-surface-reduction-remediation` is now a partially realized structure-first Stage4 owner-pressure lane; the first post-select extraction is landed, and later gate/attempt families still keep it below the proof-deferred functional stack.
- `0_0-stage34-scene-flex-contract-normalization-remediation` is now a completed operator-override lane for `scene-flex / anti-compression` work; the 2026-04-09 survey still says the true owners were `Stage3 hard floor + Stage4 amplification`, and the current workspace state now closes tranche-1 residual closure, tranche-2 anti-compression promotion, tranche-3 Wave A/B runtime normalization, and the former parked secondaries without closing or reordering the broader proof-wave/front closure stack.
- `0_0-stage3-semantic-fidelity-remediation` is closed via `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`.
- `frontier-lag-soak-canary-wave1` remains a low-priority in-progress reference-validation lane; it is not a prerequisite for the active 0_0 lanes.
- `npc-martial-state-substrate-wave1` stays blocked and does not constrain any active lane.

## 4. Execution Order

1. `0_0-stage3-state-arbiter-envelope-bounded-remediation`
2. `0_0-stage234-global-authority-alignment-bounded-remediation`
3. `0_0-stage3-contract-tightening-remediation`
4. `0_0-stage3-opening-transition-contract-normalization-remediation`
5. `0_0-stage4-consumer-contract-normalization-remediation`
6. `0_0-stage4-repair-contract-normalization-remediation`
7. `0_0-stage234-nonwuxia-state-lock-overreach-remediation`
8. `0_0-stage2-contract-normalization-remediation`
9. `0_0-stage4-partial-fix-hardening-remediation`
10. `0_0-stage3-partial-fix-hardening-remediation`
11. `0_0-stage2-partial-fix-hardening-remediation`
12. `0_0-stage234-cross-stage-contract-normalization-remediation`
13. `0_0-stage4-interview-round-owner-surface-reduction-remediation`
14. `stage0-treatment-enrich-retirement-remediation`
15. `stage0-bi-tr-production-harness-normalization-remediation`
16. `0_0-stage2-stage3-stage4-readiness-remediation`
17. `frontier-lag-soak-canary-wave1`
18. `npc-martial-state-substrate-wave1`
19. `0_0-stage34-ep2-single-episode-demo-canary`
20. `0_0-stage4-ep2-advisory-escalation-loop-remediation`
21. `0_0-stage4-canonical-entity-postselect-remediation`
22. `0_0-stage4-flashback-continuity-localfix-remediation`
23. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`
24. `0_0-stage3-quality-closure-five-tranche-remediation`

Order rationale:

- priority 1 is now the bounded Stage3 root-cause lane because the current local operator preference explicitly shifts from rerun-first to debt-first architecture work, and the most durable live-code fix point is now documented as `EpisodeStateArbiter + unified prompt-envelope budget + bounded Stage3 boundary split`
- priority 2 is now the bounded global authority-alignment follow-up because the post-`Tranche C` branch decision now prefers one shared `CrossStageAuthorityPacket` transport lane across `Stage2 emit -> Stage3 consume -> Stage4 consume/persist` before rerun reopening or retry-owner-debt structure work
- priority 3 remains the promoted Stage3 contract-tightening lane because the completed rerun proves the landed `ep2 -> ep5` follow-ups are holding, the later same-day parent binding-family static-kill tranche is now landed on the current workspace, and the newer same-day cost-first survey still finds one cheaper parent-owned static tranche before rerun: contract-driven repair eligibility plus success-state projection normalization; the newly documented first-ensemble visibility slice stays as same-lane observability work rather than justification for a new family or queue reorder
- priority 4 remains the Stage3 opening-transition sibling lane because the rerun keeps its immediate-next-day / winter-season carryover truth slice as valid landed support, even though the next direct Stage3 move now sits in the new bounded root-cause lane rather than another proof-only pass
- priority 5 remains the aggregate Stage4 consumer-contract wave, but now as a downstream verifier-first lane rather than the first patch owner for this rerun family
- priority 6 remains the repair-contract lane for closure bookkeeping because the same proof wave still has to decide whether residual mismatch volume survives, but it now sits behind the promoted Stage3 live blocker rather than in front of it
- priority 7 remains the survey-backed non-wuxia state-lock overreach lane for queue bookkeeping because the bounded Stage4 tranche is now landed, but fresh runtime proof is still outstanding so closure cannot be claimed yet
- priority 8 remains the broader Stage2 normalization lane because the older bounded advisory fallback / `ep_num` / carryover-truth residue is now landed on current-main, while fresh proof and larger deferred normalization still remain
- priority 9 is the Stage4 partial-fix hardening lane because it is now the realized anchor for shared `PatchTargetRecord`, `partial_fix_eval`, Stage4-local `repair_trace` expansion, the new proof-operational metadata follow-up, and the newly landed companion-sink / monitor / numeric-surfacing proof-channel tranche, the later `canary_000_ㅇㅇㅇ_stage4_ep1_sinkproof_r1` rerun has already closed the earlier sink-alignment uncertainty inside this same lane, and the next runtime need is a fresh rerun before the later dedicated verifier tranche rather than a new queue topic, and it now stays proof-pending under the front Stage4 proof-wave stack
- priority 10 is the Stage3 partial-fix hardening lane; it is now a partially realized child lane under Stage3 contract tightening, the first fix-pack-lite / `partial_fix_eval` sink tranche keeps it as the realized consumer after the Stage4 anchor, the 2026-04-10 aborted `00_000` fresh run made it the immediate Stage3 bug owner, the same-day bounded runtime hardening follow-up is now landed, and the latest structural split keeps the remaining work here to verifier hardening / retry exhaustion / locality preservation while the parent absorbs packet layering
- priority 11 is the promoted Stage2 partial-fix hardening lane; it remains the most direct bounded Stage2 child slice under the still-open residual owner lane, the later merge survey still places it behind the Stage4/Stage3 anchor-consumer pair for schema and sink parity, and its first bounded tranche is now landed
- priority 12 is the cross-stage contract substrate wave; shared leverage is real, and its first bounded activation tranche is now landed, but the broader owner/strength work still has a wider blast radius than the narrower pending slices above it
- priority 13 is the partially realized Stage4InterviewRound owner-surface reduction lane; its first bounded post-select extraction is landed, so it stays above Stage0 hygiene for continuity of the structure-first wave but no longer counts as the next unopened slice
- priority 14 is the partially realized Stage0 enrich retirement lane; its first bounded authority-demotion tranche is landed, so it stays explicit in the queue but no longer counts as the next unopened slice
- priority 15 is the partially realized Stage0 BI/TR production harness normalization lane; it remains a larger upstream refactor below the nearer enrich hygiene slice in working order, and code-first continuation should stay inside this active lane rather than claim a new unopened slice
- priority 16 is the blocked parent upstream lane and therefore cannot outrank executable pending work
- priority 17 remains a low-priority promoted reference-validation lane
- priority 18 remains blocked and cannot outrank an executable lane
- priorities 18-22 are completed or runtime-positive historical backing lanes; retain them for evidence, but do not treat them as active work ahead of the pending implementation stack
- priority 23 is the child Stage3 quality-closure five-tranche lane; it remains historically authoritative for tranche decomposition, but the current local operator mode now keeps it behind the new root-cause lane rather than treating it as the practical front executor
- completed scene-flex lane is now historical backing only and is intentionally omitted from the active execution-order set unless regression evidence reopens it

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
  - record the 2026-04-12 live rerun follow-up as the new owner-boundary update:
    - the old ep2 truth-pin family looks improved
    - the new active blocker is upstream Stage3 replay / season-truth drift
    - this lane now waits as downstream verifier-first rather than the first new patch owner
  - treat structured numeric carryover baseline refresh as landed for `actual_truth` plus `final_state_updates` surfaces; remaining work here is runtime measurement, not broad new implementation inside the same lane
  - the 2026-04-09 static validity recheck now says the older front-P1 wording is stale-likely under current code/test evidence; keep queue order unchanged, but do not reopen broad consumer patching or advance repair as a new code lane on static grounds alone
  - use one merged proof wave to decide whether the older consumer P1 wording can be demoted; prefer a single current-HEAD rerun that also keeps Stage3 reach open if Stage4 stays clean, and do not split this into repeated canaries unless the first run is infra-invalid or semantically ambiguous
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
  - keep the 2026-04-12 Stage4 feedback-routing tranche as landed
  - keep the 2026-04-12 Stage4 style-guide fallback tranche as landed
  - keep the 2026-04-12 Stage4 post-select truth-pin / retry-lane hardening tranche as landed
  - next extend the same routing contract to `Stage3` and then `Stage2`
  - keep the remaining owner/strength and broader transport work deferred inside this lane rather than widening the current bounded slices into a broad rename wave
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
  - treat this as a near-front proof-wave follow-up lane after the consumer umbrella because numeric carryover closure still depends on clear repair scope/provenance and operator-visible authority
  - record the 2026-04-07 bounded readback-surface promotion in `db_manager.py`, `bridge_server.py`, and `stage4_canary_tools.py` as the current implementation outcome for this lane
  - treat first-class repair subtype/provenance/scope-authority exposure as landed for snapshot/dashboard/canary summaries; remaining work here is fresh runtime proof plus any later shared-grammar cleanup, not another immediate broad patch inside the same substrate
  - the 2026-04-09 static validity recheck now says the older residual-P1 wording is stale-likely under current code/test evidence; keep queue order unchanged, but do not reopen this substrate as a new code lane or demote it on static grounds alone
  - reuse the same merged proof-wave artifacts to measure repair mismatch volume; do not schedule a separate repair-only canary unless the merged run is infra-invalid or semantically ambiguous
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
  - keep this lane verification-pending until the merged proof wave or a later focused proof confirms the soft/hard split on a bounded operator path
  - continue to realize this lane as a bounded dual-owner Stage2 + Stage4 patch rather than a broad cross-stage rewrite
  - only if the merged proof wave is explicitly deferred again should `0_0-stage3-contract-tightening-remediation` become the next unopened code realization lane
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
  - do not reopen the landed persistence-authority, compare-meta, or `arc_design` parity child tranches unless fresh evidence reopens them
  - treat bounded non-wuxia finalizer cleanup in `stage2_finalizer.py` as landed for persisted `arc_start_state` / `arc_end_state` truth; accepted non-wuxia artifacts should no longer silently rehydrate `internal_energy` / `realm` / `qi_nature` / `martial_arts`
  - keep this Stage2 item below the current Stage4 consumer/repair pair, below the new non-wuxia P1 lane, and below the reopened `0_0-stage3-contract-tightening-remediation` tranche
  - record the 2026-04-09 `projects/000_260408_ㅇ` rerun as the latest runtime anchor for this lane: the earlier proof-blocking Stage2 sink warn pair is now closed (`proof_digest.status = ok`, `proof_digest.stages.stage2.status = ok`, `issue_counts = {}`)
  - treat the later bounded parent-lane observability tranche as landed on current HEAD:
    - `runtime_advisory` fallback tightening on PASS_WITH_FIX paths
    - `ep_num` / `current_ep_start` semantics normalization across UI and authoritative sinks
    - broader carryover-authority start-state truth beyond equipment-only sync
  - use the next fresh proof wave to decide whether any broader Stage2 normalization residue still needs reactivation; until then, keep mission-authority, alias, dead-field, Golden artifact-truth, and Stage3 `semantic_carryover` semantics deferred inside this SSOT
- temp cleanup action:
  - keep mirror while this broader Stage2 SSOT remains partial; remove only on explicit closure or replacement

### 0_0-stage3-state-arbiter-envelope-bounded-remediation

- bounded root-cause survey and execution SSOT completed (2026-04-14)
- execution SSOT: `active (Tranche A/B/C landed locally; post-tranche proof deferred)`
- realized local closures:
  - `EpisodeStatePacket` now exists as the explicit Stage3 pre-generation authority surface
  - whole-envelope Stage3 prompt budget and archive appendix demotion are live locally
  - bounded Stage3 boundary split (`EnvelopeBuilder` / `ValidationBoundary` / `RetryCoordinator`) is live locally
- next action:
  - record current local workspace truth:
    - `Tranche A` (`EpisodeStateArbiter`) is landed locally
    - `Tranche B` (unified Stage3 prompt-envelope budget + archive appendix demotion) is landed locally
    - `Tranche C` (`Stage3EnvelopeBuilder` / `Stage3ValidationBoundary` / `Stage3RetryCoordinator`) is landed locally
  - before any rerun or lane expansion:
    - re-audit governing docs against the current workspace
    - keep fresh rerun proof deferred until the post-Tranche-C document audit closes
  - after the post-Tranche-C audit:
    - decide between fresh operator-gated rerun and the next global authority-alignment follow-up
  - if the lane extends, keep it bounded:
    - `Stage3EnvelopeBuilder`
    - `Stage3ValidationBoundary`
    - `Stage3RetryCoordinator`
  - do not widen this lane into `Polaris` or `DecisionKernel`
  - do not auto-demote it behind rerun-first wording while the current local operator preference stays debt-first
  - current local complexity delta:
    - `_run_phase2_generation`: `194 -> 39`
    - `_run_stage3_blueprint_generation_handoff`: `147 -> 22`
    - `_build_stage3_blueprint_semantic_bundle`: `44 -> 18`
  - remaining `120+ LOC` helper shells are classified as bounded seam owners rather than new semantic-owner growth:
    - `Stage3RetryCoordinator.run_phase2_generation` (`retry-shell`)
    - `Stage3ValidationBoundary.record_phase3_validation_payload` (`sink-boundary`)
    - `Stage3EnvelopeBuilder.run_blueprint_generation_handoff` (`envelope-shell`)
- temp cleanup action:
  - keep mirror while this remains the active long-horizon Stage3 bounded remediation lane; remove only on explicit closure, demotion, or replacement

### 0_0-stage234-global-authority-alignment-bounded-remediation

- bounded cross-stage authority survey and execution SSOT completed (2026-04-14)
- execution SSOT: `active (next bounded long-horizon follow-up after Stage3 Tranche C)`
- intent:
  - normalize one shared cross-stage authority transport across `Stage2 emit -> Stage3 consume -> Stage4 consume/persist`
- next action:
  - realize `Tranche A` first:
    - define `CrossStageAuthorityPacket`
    - emit it from Stage2 alongside current compatible surfaces
  - defer rerun and retry-owner-debt reopening while this lane remains the chosen debt-first next move
  - keep later tranches bounded:
    - `Tranche B`: Stage3 preferential consume
    - `Tranche C`: Stage4 intake/post-pass reuse
- non-goals:
  - do not widen into the older broad Stage234 vocabulary lane
  - do not widen into `Polaris` / `DecisionKernel`
  - do not consume rerun authorization in this lane
- temp cleanup action:
  - keep mirror while this lane remains the active cross-stage follow-up; remove only on explicit closure, demotion, or replacement

### 0_0-stage3-contract-tightening-remediation

- static global Stage3 survey completed (2026-04-02)
- execution SSOT: `partially_realized`
- primary seams:
  - binding scope gap
  - selective regenerate-only enforcement is now landed for the highest-risk structural seams, but broader Stage3 semantic-lossy handoff and proof confirmation still remain
  - semantically lossy Stage3 -> Stage4 handoff
  - targeted timeline and institution contract coverage gaps
- next action:
  - treat the 2026-04-07 bounded first tranche as landed across `unified_blueprint_validator.py`, `three_phase_blueprint_runtime.py`, `stage3_orchestrator.py`, `stage4_director_runtime.py`, and `stage4_outcome_runtime.py`
  - record the 2026-04-10 `00_000-stage3-fresh-run-abort-post-run-merge-audit` as the current runtime anchor: Stage3 now was exercised on current HEAD, but the run was operator-aborted before committed Stage3 sinks finalized
  - treat the same-day bounded Stage3 partial-fix/runtime repair follow-up as landed
  - treat the live-workspace truth-first follow-up as landed across `stage3_orchestrator.py` and `failure_analyzer.py`
  - treat the later fail-only structural hardening tranche as landed across `unified_blueprint_validator.py`, `three_phase_blueprint_runtime.py`, and `stage3_orchestrator.py`:
    - `opening_anchor` and `scene_completeness` now force regenerate-only full repair
    - bulk `key_events` omission now joins the same structural category
    - `binding_regenerate_only_categories` / `binding_regenerate_only_reason` now survive into retry/meta surfaces
  - record the 2026-04-12 live rerun follow-up as the current front blocker:
    - `blueprint_0002` over-consumes later beats
    - `blueprint_0003` repeats ep2 scene families and drifts on canonical institution truth
  - treat the bounded fail-only parent slice as landed across compiler / validator / runtime:
    - replay suppression now flows through `episode_progression_packet`
    - canonical institution truth now uses widened fact-lock sourcing
    - replay-family and institution-truth violations now reroute to regenerate-only `episode_progression` repair
  - record the 2026-04-13 post-run global survey as the current runtime anchor:
    - the completed rerun closes `ep4` through `ep6` with `success 3 | failure 0`
    - the child-lane `scenario_density` acceptance path is now live-proven on `ep4/ep5`
    - `ep6` exposed the bounded parent-owned terminal-quality-gate coherence family: `Director PASS < quality_gate -> emergency fallback PASS_WITH_WARNING`
  - record the later same-day frozen rerun termination as the newer parent-owned blocker family:
    - `ep7` spent repeated local patch attempts on `arc_timeline` and still saved through warning acceptance
    - `ep8` immediately reopened on the same binding family before operator shutdown
  - treat the newer same-day bounded parent tranche as now landed on the current workspace:
    - all MAJOR/CRITICAL binding-prevalidation categories now force regenerate-only repair
    - Phase2 blocks inplace reopen after binding rejects
    - terminal fallback remains blocked on unresolved binding issues
  - record the later same-day cost-first static survey as the new parent-owned direction:
    - the next cheap tranche is `contract-driven repair eligibility`
    - plus `success-state projection normalization`
  - at that point in the queue history, the next action here was that bounded static tranche, not the paid rerun yet
  - only after that tranche landed would this lane take the next rerun to confirm the corrected binding-family no-churn path on a bounded operator route
  - keep this verification-pending until runtime evidence confirms both committed sink truth and the later contract-driven eligibility / projection normalization on a bounded operator route
  - record the newer same-day formal `ep8` root-cause survey as the latest queue anchor:
    - the current blocker is primary producer-side contract drift, not a clean Director-primary false reject
    - prompt/schema/qualify expectations still admit candidates that later fail on `opening_transition`, `protagonist_state`, structure completeness, and tactical authority
    - the fixed `after 3 patch attempts` line is misleading for regenerate-before-patch routes and now counts as same-family honesty debt
  - record the bounded producer-side contract-alignment / route-honest failure-surface tranche as now landed on current `main`:
    - Stage3 ensemble prompt now carries schema-consistent `episode_number` plus explicit `opening_transition`
    - candidate sanitization / qualification now rejects missing `opening_transition`, empty `protagonist_state`, and under-structured scene shells before validator spend
    - the qualified integrated-scenario floor is now `800`
    - PASS_WITH_FIX failure wording now distinguishes rerouted-before-patch from actually executed local patch attempts
  - record that, at this point in the queue history, the next action here had been restored to the bounded paid `ep7/ep8` rerun
  - record the later adversarial execution-promotion follow-up as the newer front blocker:
    - current Korean synonym phrasing can still express unauthorized physical-threat intrusion outside the present marker lexicon
    - that family now survives producer cheap admission, producer sanitize, and validator Python prevalidation when the rest of the candidate is structurally dense enough
  - record that this rerun-first reading was later superseded again:
    - the then-immediate-next action became one bounded tactical-authority synonym parity tranche across producer and validator
    - only after that tranche landed would this lane take the paid `ep7/ep8` rerun
  - keep the arc 3 asset-math contradiction as a watch item for any subsequent rerun; it is a semantic/runtime issue, not the current proof blocker
  - treat `0_0-stage3-opening-transition-contract-normalization-remediation` as the landed bounded sibling support lane for immediate-next-day / winter-season / blocked-scene-family carryover truth
  - record the same-day first-ensemble visibility survey as a bounded same-lane observability slice:
    - session-log and UI-event evidence prove progress
    - `0_temp.txt` main-console capture still feels frozen during the first expensive ensemble wait
    - any follow-up should stay limited to heartbeat / candidate-progress surfacing, not generation retuning
  - treat the narrower same-day closure-residual observability follow-up as landed in `stage3_orchestrator.py`:
    - Stage3 completion stats now separate current-run pass-rate authority from cumulative generator pass-rate authority
    - this closes the mixed `성공/실패` vs `통과율` operator-surface drift without reopening the older first-ensemble heartbeat slice
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
  - treat the live-workspace bounded follow-up as landed inside this lane:
    - authoritative `arc_start_state` intake for opening-state inheritance
    - investment capital-continuity episode-boundary filtering
  - record the 2026-04-12 live rerun follow-up as a landed bounded sibling support slice in this lane:
    - support immediate-next-day opening truth
    - support winter/January season carryover
    - support anti-replay opening disambiguation after ep2 already consumed the analogous morning-start family
  - keep this sibling support bounded to `opening_transition` producer-contract parity rather than broad prompt retuning
  - keep broader generator retuning and stronger mismatch hardening deferred behind proof
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
  - the 2026-04-08 fresh `000_ㅇㅇㅇ` Stage4 `ep1` audit found PASS-side sink alignment drift, and the later `canary_000_ㅇㅇㅇ_stage4_ep1_sinkproof_r1` rerun now proves that the bounded `stage4_interview_round.py` logging follow-up fixed that Stage4 current-session sink seam
  - the same-day proof-operational metadata follow-up is now also landed: Stage4 start/stop/post-pass surfaces carry `session_id`, and `runtime_audit_summary.json` now summarizes latest-session exercised/non-exercised metadata for real fresh-run reuse
  - keep this lane verification-pending because the dedicated verifier hardening and broader local-vs-structural policy tightening still remain deferred inside the same lane
  - do not open a new queue topic for the resolved sink-alignment question
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
  - treat the 2026-04-10 `00_000-stage3-fresh-run-abort-post-run-merge-audit` as the current runtime anchor for this lane:
    - live Stage3 ep1 reaches `PASS_WITH_FIX`
    - local patching can produce re-audit `PASS`
    - `PASS < quality_gate` then falls into `[TF-35]` churn instead of preserving the improved patched state cleanly for the next retry
    - secondary patch-preservation drift remains visible in the same run
  - treat the same-day bounded runtime repair as landed:
    - low-score `PASS` patch state is now preserved for retry carry-forward
    - reject bookkeeping now follows the re-audit score rather than the stale pre-patch score
  - treat the later same-day closure-residual follow-up as landed:
    - advisory-only `scenario_density` residuals now accept bounded `PASS_WITH_WARNING` without reopening the low-yield local patch lane
    - validate metadata now records that advisory-only residual acceptance instead of sending the run back through the same local repair loop
  - record the 2026-04-13 post-run global survey as the current runtime anchor for this lane:
    - the completed rerun proves that advisory-only `scenario_density` acceptance path on `ep4/ep5`
    - the same rerun still reaches `ep6` closure and exits cleanly
  - treat the later structural/adversarial audit as the current owner split:
    - parent lane owns packet layering / threshold alignment / canonical anchors
    - this child lane keeps verifier / retry-exhaustion / locality hardening
  - keep this verification-pending only for deferred verifier / retry-exhaustion / locality debt; do not front-reactivate it for the same advisory family
  - let the parent lane own the new `ep6` post-proof terminal-quality-gate coherence slice
  - leave dedicated verifier and retry-exhaustion hardening for the next tranche inside this same lane, not as a substitute for the parent structural tranche
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
  - inherit the parent Stage2 lane's operator-parked-by-default posture unless explicit reactivation is ordered
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
  - treat the earlier `159 direct methods / 2 / 5` recount as historical only; current live recount is `166 direct methods / 2 / 5`
  - if structure-first implementation continues after proof, reopen the gate-semantics family next rather than pretending the helper-heavy auditability follow-up closed owner pressure
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

### 0_0-stage34-scene-flex-contract-normalization-remediation

- bounded survey and execution SSOT completed (2026-04-09)
- execution SSOT: `completed (tranche-1/2/3 plus former secondary surfaces closure-clean on the current workspace state)`
- primary seams:
  - Stage3 historically hard-failed `<4` scenes in the earliest qualification/judgment path, and the current tranche has now demoted that floor to `<=1` across the direct residual blockers
  - Stage4 now also lands the bounded anti-compression retune across the remaining active writer/director/template/feedback surfaces, while preserving header/template compatibility
  - the later tranche-3 Wave A/B patch now normalizes the active validator / precheck / confidence / continuity owner set so dense `2-scene` and `3-scene` manuscripts no longer draw low-scene false pressure on the bounded runtime seam
- next action:
  - keep tranche 1 closed unless regression evidence reopens it
  - keep tranche 2 closed unless regression evidence reopens it
  - keep tranche 3 and the former secondary surfaces closed unless regression evidence reopens them
  - return to the broader proof-wave/front queue instead of reopening this closed lane by default
- temp cleanup action:
  - temp mirror removed in the 2026-04-10 closure sync

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
- queue inventory updated again to include the new scene-flex execution lane, later refreshed to record explicit tranche-1 activation by operator override, and now refreshed again to mark the lane closed with temp-mirror cleanup
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
- canonical scene-flex path and temp-mirror cleanup state verified against filesystem
- ordering is consistent with the latest Stage4 consumer-finalization survey, the latest ep2 bounded canary failure, and the new 2026-04-06 bounded survey plus execution SSOT for non-wuxia state-lock overreach
- the 2026-04-07 workspace reinspection was later consumed by a same-day bounded Stage4 tranche landing for the non-wuxia lane, so the item remains partial because runtime proof is still deferred rather than because the Stage4 code is unopened
- the 2026-04-07 partial-fix survey stack is real and precision-first, but the later merge survey makes Stage4 the anchor owner, Stage3 the next consumer, and Stage2 the last consumer without opening a new queue topic
- the 2026-04-07 owner-surface survey confirms the new lane is real but structure-first, so it remains below the functional pending stack
- the 2026-04-07 Stage0 enrich implementation pass is reflected as partial rather than pending, and the later same-day Stage0 BI/TR implementation pass now also makes that lane partial rather than unopened
- the 2026-04-09 scene-split/density survey supports the lane's owner split as `Stage3 hard floor + Stage4 amplification`, and the later execution-start re-audit keeps that owner split while limiting activation to bounded tranche 1 only
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
- the scene-flex lane now remains only as completed historical backing rather than live queue work; the closure refresh clears tranche 1, tranche 2, tranche-3 Wave A/B, and the former secondaries on the current workspace state without escalating the lane above proof/front work
- no overreach: demo utility not promoted to closure proof, Stage4 resume not declared

Confidence: `97%`
