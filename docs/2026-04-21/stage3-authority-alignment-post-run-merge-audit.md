# Stage3 Authority Alignment Post-Run Merge Audit

Date: 2026-04-21
Status: final (3-pass audited; bounded Stage3 authority-alignment sibling residual landed in code, targeted proof reruns executed, and the original project was restored to the stronger successful proof snapshot after a later nondeterministic regression run)
Canonical Path: `docs/2026-04-21/stage3-authority-alignment-post-run-merge-audit.md`
Commit State:
- Baseline Commit: `b0e94a81bc6acb5079e31b1810bda554dd02a63e`
- Baseline Dirty Summary: `dirty: 6 modified, 97 deleted, 5 untracked; hotspots: docs/temp mirrors, canary/manual-backup trees, blueprint_ensemble.py, test fixtures`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD with bounded working-tree edits in Stage3 validator/orchestrator/tests plus this canonical audit; no queue-roadmap rewrite performed because this was a user-directed sibling lane executed immediately`
Source Survey Docs:
- `docs/2026-04-17/stage234-s2-s3-s4-authority-alignment-current-head-adversarial-3pass-audit.md`
- `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
- `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
Evidence Artifacts:
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage3_orchestrator.py`
- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_stage3_orchestrator.py`
- `projects/00_0420/config/work_guard.yaml`
- `projects/00_0420/plans/blueprints/blueprint_0001.txt`
- `projects/00_0420/logs/stage3_canary_summary.json`
- `projects/00_0420/logs/session/ui_events.jsonl`
- `projects/_manual_backup/00_0420_authority_alignment_20260420_235841`
- `projects/_manual_backup/00_0420_authority_alignment_rerun2_20260421_002434`
- `projects/_manual_backup/00_0420_authority_alignment_rerun3_20260421_003607`
Side-Effect Coverage: covered (Stage3 binding prevalidation, replay screening, selection companion sinks, pass-rate/session/director selection sinks, original `00_0420` project DB/log/blueprint restoration path)
Confidence: `96%`

## 1. Intent

Close the newly observed Stage3 authority-alignment sibling residual that surfaced after the earlier replay/reroute fixes:

- prove whether the donorized opening doctrine in `work_guard` is actually binding at live Stage3 time
- prove whether replay screening can distinguish a lawful moved-anchor opening from a stale replay
- prevent misleading Stage3 selection companion sinks when selected-candidate identity and rationale drift apart
- gather fresh live evidence on `projects/00_0420` instead of stopping at static inference

This audit intentionally does not reopen the parked Stage234 parent lane or mutate the parked temp roadmap.

## 2. Adversarial Findings

### Finding 1. The opening-doctrine hardening existed in code only as a dormant branch until `working_ep` was threaded into live prevalidation

Severity: high

The bounded opening-doctrine helper landed in `UnifiedBlueprintValidator`, but the first live rerun showed `binding=0` on Episode 1 even though the saved winning blueprint still closed in the private bedroom and left `end_location` / `ending_state.location` on the same private anchor.

Root cause:

- `_collect_work_identity_opening_issues()` depended on `working_ep <= 4`
- live candidate payloads frequently reached `_python_pre_validate()` without `ep_num`
- the validator only derived the episode marker from `blueprint.ep_num`, `blueprint.episode_number`, or `constraint_block.ep_num`
- the live compare path already knew `working_ep`, but it never forwarded that value into `_python_pre_validate()`

Bounded landing:

- `_python_pre_validate(..., working_ep_override=...)` now accepts the orchestrator-known episode marker
- `_prepare_compare_candidate()` and `_run_python_prevalidation_phase()` now pass the live `working_ep`

Operational consequence:

- early-opening doctrine is no longer a dead branch for candidate payloads that omit episode numbering

### Finding 2. Replay screening needed a narrower Scene 1 moved-anchor exemption tied to explicit opening-truth, not just normalized transition type

Severity: medium

The earlier replay-screen follow-up needed one more precision pass. A broad Scene 1 exemption based only on normalized transition type would have masked legitimate replay findings. The corrected rule now fires only when:

- the repeated surface is `scene_1`
- `episode_state_packet.opening_truth.opening_transition_expectation` explicitly says the opening should not be `direct_continuation`
- the normalized transition is an actual moved-anchor type such as `explicit_transition` or `jump_opening`

Bounded landing:

- `UnifiedBlueprintValidator._collect_episode_progression_issues()` now consumes `normalized_opening_transition`
- Scene 1 replay exemption is gated by explicit opening-truth expectation rather than by raw normalization alone

Operational consequence:

- lawful arc-opening or moved-anchor handoffs get a narrow escape hatch
- older replay tests still fire on true stale continuation attempts

### Finding 3. Stage3 selection-contract guard must inspect winner-facing rationale, not generic compare notes

Severity: medium

The first selection-contract guard correctly caught mismatched winner narration, but it was initially too aggressive because `comparison_notes` legitimately mention losing candidates. That version suppressed `director_selections` and `session_decisions` even on otherwise healthy successful attempts.

Bounded landing:

- Stage3 now snapshots a selection contract from:
  - `validate.selected_index`
  - `selected_candidate_advisory.candidate_index`
  - selected strategy / artifact candidate key
  - winner-facing `selection_reason` and `verdict_reason`
- `comparison_notes` are no longer treated as winner identity proof
- on mismatch, Stage3:
  - emits `stage3_selection_contract_mismatch`
  - strips winner rationale from `stage_attempts`
  - suppresses misleading `director_selections` and `session_decisions`

Operational consequence:

- genuine winner/rationale drift is blocked
- normal compare prose no longer looks like a sink-contract violation

## 3. Pass 1. Inventory

Static/code inventory touched in this bounded sibling lane:

- `modules/domain/agents/unified_blueprint_validator.py`
  - new `work_identity_opening` binding category
  - active work-guard load/cache
  - live `working_ep_override`
  - narrower Scene 1 opening-shift replay exemption
- `modules/core/stage3_orchestrator.py`
  - Stage3 selection-contract snapshot helper
  - companion-sink suppression on true mismatch
  - stage-attempt rationale scrubbing when mismatch is detected
- `tests/test_unified_blueprint_validator_lane_c.py`
  - opening-doctrine miss
  - opening-doctrine satisfied case
  - authorized moved-anchor opening replay false-positive guard
- `tests/test_stage3_orchestrator.py`
  - success-path selection-contract suppression
  - failure-path selection-contract suppression

Live-proof inventory:

- successful fresh rerun session: `20260421_002444`
  - Episode 1 `PASS 95`
  - Episode 2 `PASS_WITH_WARNING 95`
- later fresh rerun session: `20260421_003616`
  - Episode 1 `PASS 95`
  - Episode 2 `FAILED`
  - this later run restored normal selection companion sinks after the compare-note overblocking fix
- restored stable project state:
  - `projects/00_0420` was restored from `projects/_manual_backup/00_0420_authority_alignment_rerun3_20260421_003607`
  - that backup contains the stronger successful proof snapshot from immediately before the later nondeterministic regression rerun

## 4. Pass 2. Merged Evidence

### 4.1 Work-guard donor doctrine is live and binding now

`projects/00_0420/config/work_guard.yaml` already carried the generalized donor doctrine:

- `visible pressure -> execution -> public proof -> private receipt -> observer shift -> next gate`
- `first proof must not end at public proof only`
- early tranche requirements for private receipt / access-shift and next-gate visibility

The live code now binds that doctrine inside Stage3 candidate prevalidation instead of leaving it purely advisory.

### 4.2 The first fresh rerun proved the `working_ep` bug and the replay frontier shape

Session `20260420_235854` showed:

- Episode 1 passed with `binding=0`
- the winning Episode 1 blueprint still ended at `2006년 서울 성북동 본가 저택 침실`
- Episode 2 died in the same replay plateau lane:
  - `source_anchor=prev_ep=1:2006년 서울 성북동 본가 저택 침실 | prev_opening=jump_opening`

That was the decisive evidence that the new opening-doctrine check existed in code but was not firing on live candidates.

### 4.3 The second fresh rerun proved the live opening-doctrine fix

Session `20260421_002444` showed:

- Episode 1 `PASS 95`
- Episode 2 `PASS_WITH_WARNING 95`
- `blueprint_db_count=2`
- `blueprint_file_count=2`

This was the strongest narrative proof that the Stage3 authority-alignment closure materially improved the reroute frontier.

Residual on that run:

- `director_selections=0`
- `session_decisions=0`

That residual came from the first, too-broad selection-contract guard and was fixed afterward.

### 4.4 The third fresh rerun proved the narrowed selection-contract sink behavior, but the content path remained nondeterministic

Session `20260421_003616` showed:

- `director_selections=2`
- `session_decisions=2`
- coverage gaps returned to `0`

So the narrowed winner-only selection-contract logic worked as intended.

However the content generation path regressed to:

- Episode 1 `PASS 95`
- Episode 2 `FAILED`
- same replay/authority plateau family

This means:

- the sink-side authority fix is live
- the narrative frontier remains nondeterministic even after the opening-doctrine hardening

### 4.5 Stable project state was restored to the stronger successful proof snapshot

Because the later rerun regressed after the sink fix, the original `projects/00_0420` workspace was restored to the stronger successful proof snapshot from the prior backup.

Current restored project truth:

- `latest_session_id = 20260421_002444`
- Episode 1 `PASS 95`
- Episode 2 `PASS_WITH_WARNING 95`
- `blueprint_count = 2`

This restoration was deliberate and should be treated as the authoritative local project state after this lane.

## 5. Pass 3. Operating Consequence

What is now closed in code:

- donorized opening doctrine is genuinely binding in live early-episode Stage3 validation
- replay screening has a bounded, explicit opening-truth escape hatch
- winner/rationale mismatch can no longer silently poison Stage3 companion sinks

What is now closed in project state:

- `projects/00_0420` is not left in the later failed rerun state
- the original project has been restored to the stronger successful rerun snapshot

What remains open:

- the Episode 2 frontier is still nondeterministic under fresh reruns
- one fresh rerun cleared the narrative path and one later rerun regressed
- therefore this lane should be read as `bounded authority-alignment improvement landed with mixed fresh-proof stability`, not as a permanent deterministic closure claim

## 6. Validation

Static verification:

- `pytest tests/test_unified_blueprint_validator_lane_c.py -q` -> `42 passed`
- `pytest tests/test_stage3_orchestrator.py -q` -> `103 passed`

Live verification:

- fresh rerun `20260421_002444` -> `ep1 PASS 95`, `ep2 PASS_WITH_WARNING 95`
- fresh rerun `20260421_003616` -> `ep1 PASS 95`, `ep2 FAILED`
- project restored to the stronger successful rerun snapshot afterward

## 7. Queue / Temp Note

No new temp execution SSOT mirror was created in `docs/temp/` for this lane.

Reason:

- the active temp roadmap remained in parked mode
- this task was a user-directed bounded sibling residual executed immediately rather than queued as a parked roadmap reactivation
- the canonical dated audit above is the authority record for this wave

