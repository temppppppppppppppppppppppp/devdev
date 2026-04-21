# 00_0420 S2-S3-S4 Authority Alignment 3-Pass Audit

Date: 2026-04-21
Status: final (3-pass audited; live Stage4 rerun frozen for stable evidence merge; parallel S2/S3/S4 survey completed before remediation)
Canonical Path: `docs/2026-04-21/00_0420-s2-s3-s4-authority-alignment-3pass-audit.md`
Commit State:
- Baseline Commit: `e9b45933c1e0ba1b61528f466e6b7415494a698b`
- Baseline Dirty Summary: `dirty: large existing workspace drift across canary/manual-backup trees, docs/temp mirrors, runtime logs/db/artifacts, several Stage4 modules/tests already modified by prior bounded fixes; no unrelated rollback performed`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD with this audit lane only; active Stage4 rerun for projects/00_0420 was intentionally stopped before survey merge`
Source Survey Docs:
- `docs/2026-04-21/stage3-authority-alignment-post-run-merge-audit.md`
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
Evidence Artifacts:
- `projects/00_0420/plans/arcs/arc_001.txt`
- `projects/00_0420/plans/blueprints/blueprint_0003.txt`
- `projects/00_0420/plans/blueprints/blueprint_0004.txt`
- `projects/00_0420/drafts/ep_0003.txt`
- `projects/00_0420/drafts/ep_0003.settlement.json`
- `projects/00_0420/logs/session/ui_events.jsonl`
- `projects/00_0420/logs/session/decisions.jsonl`
- `projects/00_0420/logs/session/llm_io.jsonl`
- `projects/00_0420/logs/session_20260421_070730.log`
- `projects/00_0420/logs/episode_production.jsonl`
- `projects/00_0420/project_data.db`
- `projects/_manual_backup/00_0420_stage3_resume_20260421_031725/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`
- `projects/_manual_backup/00_0420_stage3_resume_20260421_031725/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json`
- `projects/_manual_backup/00_0420_stage3_resume_20260421_031725/logs/quality_metrics.jsonl`
- `projects/_manual_backup/00_0420_stage3_resume_20260421_031725/logs/session/decisions.jsonl`
- `projects/_manual_backup/00_0420_stage3_resume_20260421_031725/logs/session/llm_io.jsonl`
- `projects/00_0420/config/work_guard.yaml`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/core/stage4_retry_runtime.py`
Side-Effect Coverage: covered (active Stage4 process freeze, DB/log/blueprint/manuscript truth, Stage2 carryover packet, Stage3 validator/pass sinks, Stage4 prompt/retry/post-select seams)
Confidence: `97%`

## 1. Intent

Run the formal-route authority survey the user explicitly asked for:

- freeze the active `projects/00_0420` Stage4 rerun instead of mixing evidence with a still-mutating run
- inspect `Stage2 -> Stage3 -> Stage4` as one authority chain rather than doing another local fail-only patch
- decide whether the frontier is mainly S2 carryover truth, S3 PASS gating, or S4 retry/prompt amplification
- produce a canonical audit and execution SSOT before more reruns

## 2. Executive Conclusion

The current `ep4` failure is not one bug and not mainly a numeric carryover problem.

It is a three-layer authority misalignment:

1. `Stage2` handed `ep4` a tactical/carryover contract that is internally coherent but already under-shoots the work-guard doctrine.
2. `Stage3` allowed that under-powered contract to pass as a strong blueprint even though it re-opened a procedural PB conflict and failed to surface the required `signboard / next-ticket` progression.
3. `Stage4` actually knows stronger carryover truth, but its generation prompt and retry path still preserve stale authority surfaces, so the wrong blueprint is amplified first and only rejected after selection.

Current owner of the final reject is:

- `Director/post-select continuity truth`, not `numeric_carryover_authority`

Current highest-ROI remediation direction is:

- tighten early-episode Stage3 work-identity opening enforcement
- stop Stage4 retry from treating every post-select conflict as a duplicate-suppression bypass just because a reuse contract exists

## 3. Adversarial Findings

### Finding 1. Stage2 handed off an ep4 state that already undershoots the work-guard ladder

Severity: high

`arc_001.txt` defines ep4 as:

- immediate trust liquidation
- 20억 확보
- SW인베스트먼트 설립
- HTS 세팅
- end at the private bedroom with the bankbook copy, laptop, and seal

This same contract appears in:

- `projects/00_0420/plans/arcs/arc_001.txt`
- `projects/_manual_backup/.../final_arc__conservative.json`
- `project_data.db` cross-stage authority packet / canonical facts

But the work-guard and benchmark expect a stronger early ladder:

- ep3 should already show PB tone shift plus private receipt / access shift
- ep4 should show the first signboard / next-cycle ticket, not only more procedural setup

So the Stage2 ep4 order is not random noise; it is a coherent but under-powered authority packet.

### Finding 2. Stage3 passed a blueprint that re-opened PB procedural conflict instead of promoting the lane

Severity: critical

`blueprint_0004.txt` replays:

- PB phone conflict
- approval / procedure / risk pushback
- VIP-room document signing
- temporary office HTS setup

That blueprint does not lock a meaningful `signboard / next-ticket` closing beat.

This matters because ep3 blueprint truth closes on “next prey / next call” while the actual ep3 manuscript truth already says:

- FX route secured
- direct order line set
- 20억 margin transfer waiting

So Stage3 passed a blueprint that is too weak for the doctrine and too stale for the manuscript truth.

The pass sink also flattened rationale:

- compare-time reasoning was more specific
- final sink reduced it to strong score / pass framing

This made the structural weakness harder to see until Stage4.

### Finding 3. Stage4 knows the stronger truth, but the prompt/retry path still re-amplifies stale upstream input

Severity: critical

Stage4 evidence shows:

- round 1 and round 2 both reached provisional `PASS` / `PASS_WITH_FIX`
- both were later downgraded to `REJECT` with `post_select_conflict`
- round 3 was rejected directly because the blueprint itself conflicted with prior manuscript truth

Stage4 context builder already injects:

- opening-scene authority
- carryover precedence
- FactLedger numeric carryover authority

So Stage4 is not blind.

The problem is that the prompt still includes stale carryover/task surfaces alongside the stronger prior-manuscript bridge, and the retry path keeps a reuse contract that can bypass duplicate suppression even for continuity/history-heavy post-select conflicts.

Operationally, this means:

- the bad path is not blocked at generation time
- it is blocked only after candidate selection
- the retry loop is then biased toward reusing the contaminated near-pass baseline

### Finding 4. PB role truth is duplicated and contradictory across downstream surfaces

Severity: medium

`ep_0003.settlement.json` says PB is effectively an execution partner / tactical enabler, but relation labeling still leaves PB as `목격자`.

That mismatch leaks into advisory and downstream interpretation:

- work guard frames PB as a gatekeeper whose tone shift matters
- settlement/world-state surfaces still allow PB to look like a re-negotiable external witness

This does not appear to be the top reject owner, but it is a real amplifier of the ep4 drift.

### Finding 5. Numeric carryover warnings were noisy but secondary in this session

Severity: medium

There are real numeric warnings:

- `20억` asset/capital/wealth checks
- `66억` cash-style claims

But in the active ep4 session the Director repeatedly dismissed the numeric mismatch family as non-primary.

The stronger reject owner remained:

- continuity / history / flashback / PB-role drift

So numeric carryover is not the main reason ep4 is stuck right now.

## 4. Pass 1. Inventory

### 4.1 Stage2 inventory

- `arc_001.txt` tactical doc and carryover packet
- `project_data.db` cross-stage authority packet / canonical facts
- archived Stage2 final arc artifact

Key Stage2 facts:

- `end_total_assets = 20억원`
- `end_capital = 20억원`
- `end_portfolio_position = 해외 선물 레버리지 대기 상태`
- `end_location = 서울 성북동 본가, 한시우의 개인 침실`
- `end_equipment` includes the bankbook copy, HTS laptop, and seal

### 4.2 Stage3 inventory

- `blueprint_0003.txt`
- `blueprint_0004.txt`
- archived Stage3 ep3 blueprint artifact
- live validator / quality sink code

Key Stage3 facts:

- ep3 blueprint seam closes on the next-target frontier rather than on a named signboard
- ep4 blueprint re-opens PB procedural conflict instead of escalating the authority lane
- current validator already has `work_identity_opening`, but the heuristic remains too forgiving for multi-location early-episode setups

### 4.3 Stage4 inventory

- `ep_0003.txt`
- `decisions.jsonl`
- `llm_io.jsonl`
- `episode_production.jsonl`
- `session_20260421_070730.log`
- Stage4 prompt / retry / post-select runtime code

Key Stage4 facts:

- ep3 manuscript already says PB route and direct order line are prepared
- ep4 candidates repeated PB friction anyway
- the loop reached multiple provisional passes before post-select truth shut them down

## 5. Pass 2. Merged Evidence

### 5.1 The active Stage4 rerun was producing fresh evidence, not random noise

Before the survey freeze, the live session `20260421_070731` had already reached:

- `Round 4/10`

DB/manuscript truth at freeze time:

- manuscript count = `3`
- latest manuscript ep = `3`

So the frontier was genuinely `ep4`, not a stale crash.

### 5.2 Ep3 manuscript truth and ep4 blueprint truth disagree on the PB state

Ep3 manuscript truth:

- PB route secured
- direct order line set
- 20억 transfer waiting

Ep4 blueprint truth:

- PB resists again
- approval/procedure/risk conflict restarts
- VIP room signing happens as if setup were still incomplete

This is the clearest single conflict seam in the current lane.

### 5.3 Stage4 rejection behavior proves downstream continuity truth is stronger than the blueprint

The Stage4 logs show a repeated pattern:

- candidate selected as a provisional pass
- post-select conflict detection downgrades it
- later rounds escalate to direct blueprint-level rejection

That means:

- Stage4 is not simply hallucinating a reject
- the stronger truth owner is already present
- the system is spending too much cost before the stronger truth wins

### 5.4 Stage4 retry is over-trusting reuse on the wrong class of post-select conflicts

`stage4_postselect_runtime.py` unconditionally stores a reuse contract for post-select conflicts.

`stage4_retry_runtime.py` then lets any reuse contract skip duplicate suppression.

That is a reasonable rule for truly bounded local-fix cases.

It is too permissive for:

- continuity-heavy
- history-heavy
- rewrite-required

post-select conflicts.

In those cases the loop is encouraged to preserve the wrong trajectory.

### 5.5 Stage3 opening-doctrine enforcement exists but is still semantically loose

Current validator logic already checks for:

- `private receipt`
- `observer shift`
- `next gate`

But it also contains a multi-location escape hatch that can let an early-episode blueprint through if it simply moves across several locations while surfacing one partial progression token.

That matches the shape of the current ep4 seam too closely to ignore.

## 6. Pass 3. Operating Consequence

What should not happen next:

- do not rerun Stage4 first and hope the prompt heals itself
- do not treat numeric carryover as the primary owner
- do not patch only one project artifact by hand and call the lane closed

What the merged evidence says to do next:

1. tighten Stage3 early-episode work-identity opening enforcement so multi-location setup alone does not excuse missing `private receipt / observer shift / next gate`
2. tighten Stage4 retry duplicate suppression so `reuse_contract` no longer auto-bypasses suppression for rewrite-required continuity/history conflicts
3. only after those structural fixes, rerun the affected lane (`S3 ep4` first, then `S4 ep4`)

## 7. Residual Risk

- `arc_001` itself is still an under-powered handoff relative to the work-guard ladder
- PB role labeling drift remains in settlement/world-state surfaces
- Stage4 carryover prompt duplication around `pending_actions` remains a likely secondary amplifier even after the first remediation wave

These residuals should be tracked, but they are not a reason to skip the two highest-ROI structural fixes above.

## 8. Final Verdict

This lane is now formally diagnosed.

Canonical finding:

- `ep4` is blocked by cross-stage authority misalignment, not by a single Stage4 bug

Primary remediation owner order:

1. `Stage3 validator / doctrine enforcement`
2. `Stage4 retry duplicate-suppression contract`
3. `Stage4 carryover prompt dedupe`
4. `Stage2 handoff doctrine refresh` if the lane still stalls after the first two fixes
