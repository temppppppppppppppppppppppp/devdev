# ROL Live-Merge Global Survey Rolling Watchlist

Date: 2026-03-30
Status: draft-live-run-pending
Canonical Path: `docs/2026-03-30/rol-live-merge-global-survey-rolling-watchlist.md`
Temp Mirror Path: `(none during active live run)`
Baseline Commit: `9ad4efcc`
Baseline Dirty Summary: `dirty: Stage 3 validator/tests touched, live 0_1 Stage 3/4 artifacts and logs advancing, several 2026-03-30 docs untracked`
Live Run Status: `active`
Live Run Evidence:
- `python.exe main_a.py` observed live on host at merge time
Source Inputs:
- operator transcript from Terminal 1 through Terminal 5 read-only survey lanes
- local line-level recheck of top action-bearing findings before merge

## 1. Purpose

This is the merged rolling watchlist for the active `ROL live-merge` global survey.

It is not a final survey and it does not close findings.

Its job is to:
- keep action-bearing findings from disappearing into terminal-only output
- deduplicate terminal 1 to 5 findings into one operator draft
- preserve cross-lane merge notes until the active Stage 4 run reaches a terminal state
- prepare the post-run merge audit

Authority note:
- static code/process findings in this document remain valid independently of the active live run
- the active live run only limits closure claims, temp-queue mutation, and run-artifact truth interpretation
- do not discard a finding merely because the run is still active

## 2. Scope

Covered lanes:
- Terminal 1: runtime/core/orchestration
- Terminal 2: agent/validator/binding
- Terminal 3: persistence/observability/sink
- Terminal 4: harness/test/canary/queue
- Terminal 5: UI/desktop/config/operator ergonomics

Not covered here:
- final runtime artifact truth from the still-running Stage 4 lane
- code changes
- DB changes
- queue cleanup
- execution SSOT closure

## 3. Merge Method

Merge policy used for this draft:
- merge all five lane outputs
- collapse duplicates by seam, not by file count
- re-verify top action-bearing findings locally before promoting them into the merged list
- keep lower-priority lane findings as provisional watchlist items until post-run merge

Locally re-verified before merge:
- duplicate async dispatch pattern in [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- Stage 3 lazy init write-back in [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- Consensus timeout PASS fallback in [consensus_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/consensus_validator.py)
- Stage 4 authoritative fix-scope warning-only seam in [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- shared cursor telemetry writes in [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- stale temp roadmap state in [execution-roadmap.md](C:/Users/User/Desktop/글도비/docs/temp/execution-roadmap.md)
- phantom desktop settings and model/config drift in [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html) and [models_config.py](C:/Users/User/Desktop/글도비/modules/core/models_config.py)

## 4. Merged Action-Bearing Findings

### AB-1. High
Stage 3 lazy init writes app-level state directly, creating hidden authority overlap with other runtime entry paths.

Evidence:
- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L706)
- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L731)
- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L748)
- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L582)

Why it matters:
- Stage 3 orchestrator acts as an implicit producer of `state_tracker`, `world_state`, and `fact_ledger`
- ownership overlaps with other runtime boot/init paths
- order-of-execution can change effective state substrate without a single declared authority

### AB-2. High
Stage 2 / OneStop retains duplicated async dispatch glue and still mixes automation with human-interactive recovery.

Evidence:
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L2917)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L2924)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L4565)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L4572)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L4612)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L4632)

Why it matters:
- duplicated dispatch code can drift silently
- “automatic” pipeline still blocks on operator input during failure paths
- headless or scripted operation remains brittle

### AB-3. High
ConsensusValidator can degrade to synthetic PASS on mass timeout.

Evidence:
- [consensus_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/consensus_validator.py#L165)
- [consensus_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/consensus_validator.py#L234)
- [consensus_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/consensus_validator.py#L242)
- [consensus_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/consensus_validator.py#L267)

Why it matters:
- if all perspectives timeout under load, validation can still collapse into a nominal PASS path
- Stage 2 runtime may proceed with weak or absent real consensus evidence

### AB-4. High
Stage 4 TruthGate-style advisory findings still do not guarantee a binding verdict escalation path.

Evidence:
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1629)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1967)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2004)

Why it matters:
- advisory findings can influence Director context without guaranteeing `PASS_WITH_FIX` or forced retry
- conflicting advisory suppression may also reduce operator-visible evidence in the same subject area

### AB-5. Medium-High
Stage 4 PASS_WITH_FIX can proceed after `authoritative_fix_scope` violation as a warning-only condition.

Evidence:
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2001)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2014)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2022)

Why it matters:
- repair can continue with blank or invalid scope contracts
- downstream patch loops can run on reduced authority

### AB-6. Medium
`save_stage_attempt` and `save_ui_event` still use shared cursor writes despite the local-cursor rule declared in the same file.

Evidence:
- [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py#L52)
- [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py#L3044)
- [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py#L3186)

Why it matters:
- authoritative telemetry write paths violate local cursor hygiene
- current locking reduces race risk, but the declared INF-P1-1 standard is still violated

### AB-7. Medium
`episode_production.jsonl` has multi-writer schema drift and mixed episode key names.

Evidence:
- [stage4_outcome_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_outcome_runtime.py#L415)
- [stage4_outcome_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_outcome_runtime.py#L425)
- [stage4_outcome_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_outcome_runtime.py#L1010)
- [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L2117)
- [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L2123)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L5713)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L5800)

Why it matters:
- some writers use `ep_num`, others use `ep`
- consumers can silently miss records if they normalize only one shape

### AB-8. Medium
Temp execution roadmap is stale relative to the active temp queue.

Evidence:
- [execution-roadmap.md](C:/Users/User/Desktop/글도비/docs/temp/execution-roadmap.md)
- [stage3-blueprint-validator-hardening-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md)
- [stage3-capital-unit-drift-hardening-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md)
- [0_1-stage3-blueprint-fix-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md)
- [live-run-merge-survey-harness.md](C:/Users/User/Desktop/글도비/docs/implementation/live-run-merge-survey-harness.md#L83)

Why it matters:
- queue truth and roadmap truth have diverged
- live-run mode blocks fixing `docs/temp/` mid-run, so this must become a post-run closure item

### AB-9. Medium
Desktop system tab contains phantom settings that do not affect runtime.

Evidence:
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html#L3349)
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html#L7340)
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html#L9549)
- [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py#L820)

Why it matters:
- operator can edit `qualityGate`, `targetLength`, `timeout`, `keyRotate`
- values persist in app settings but are not actually bound to runtime inputs in the surveyed path
- this creates silent misconfiguration risk

### AB-10. Medium
Desktop/app model and API-key hints drift from real runtime behavior.

Evidence:
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html#L3181)
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html#L3217)
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html#L9536)
- [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js#L271)
- [models_config.py](C:/Users/User/Desktop/글도비/modules/core/models_config.py#L45)
- [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml#L38)
- [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml#L49)

Why it matters:
- API key hint says `.env`, but desktop runtime stores in app settings and injects env on spawn
- model tab exposes `2.5` era labels while actual runtime defaults are `gemini-3.1-pro-preview`
- packaged mode has no clean override path for `config/models.yaml`

## 5. Provisional Watchlist

These items are retained as provisional because they were not all re-verified line by line in this merge turn.

### Validator / contract watchlist
- single-empty-scene gap in `scene_completeness` threshold
- dead-NPC advisory string fragility in [arc_draft_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/arc_draft_validator.py)
- `capital_unit` skip when authoritative packet already contains mixed-currency fields
- `arc_timeline_alignment` depending only on `state_changes.timeline`
- silent skip when Stage 3 context lacks callable validation methods

### Persistence / observability watchlist
- `quality_metrics.jsonl` has no explicit authority classification
- `AuditService.flush_audit_buffer()` clears buffer without its own lock
- `runtime_audit` trim windows are asymmetric
- `PassRateMonitor` can double-save on concurrent `% 100 == 0`
- `metrics_collector.save_metrics()` call path is unclear
- `stage4_outcome_runtime.py` relative logs-dir fallback remains edge-case risky

### Harness / regression watchlist
- `run_pytest_lowmem.py` does not set `PYTHONIOENCODING=utf-8` in its subprocess env
- `e2e_menu_smoke.ps1` has no platform note in validation tier metadata
- `test_legacy_reentry_reaudit.py` mixes too many subsystems in one file
- `test_run_stage3_canary.py` mocks `analyze_canary()` too broadly for deep analyzer correctness
- `sync_temp_queue_state.py` has no live-run guard at code level
- parked frontier/npc temp docs still look active to a new operator

### Runtime / operator watchlist
- OneStop frontier helper return annotation allows `None` on early return
- `for...else` control flow in OneStop is harder than necessary to reason about
- Stage 4 `max_loops` cap and `+5` buffer are not operator-visible
- Stage 3 direct `self.app` lookups bypass context purity in multiple spots
- boot silent-return path can make startup failure too quiet
- desktop renderer directly tests Gemini API from renderer memory
- splash fallback timing may expose idle main window before backend readiness
- `현재 사용 중: Key 1` status is fixed text, not backend-truth
- CSP still requires `'unsafe-inline'` because renderer remains inline-script heavy

## 6. Cross-Lane Merge Notes

The merged pattern is more important than any one isolated line item:

1. Authority seams are the dominant repo-wide risk.
- Stage 3 app-state lazy init
- Stage 4 advisory without binding
- multi-writer episode production schema drift
- desktop phantom settings

2. Operator truth vs actual runtime truth still diverges in multiple places.
- UI hints vs real env injection
- roadmap vs actual temp queue
- advisory sinks vs authoritative sinks

3. Several current issues are not code-breakers but LLM-friendliness degraders.
- duplicate async dispatch shells
- branch-heavy OneStop flow
- mixed authority ownership for state/init and repair scope

## 7. Provisional Candidate Execution Lanes

Do not treat this as final execution ordering yet. These are draft candidates only.

Timing note:
- these lanes are survey-derived and can be discussed immediately
- actual realization timing may still wait for the active run to finish when the lane would mutate runtime-adjacent state, queue state, or operator truth artifacts

1. `runtime-authority-and-init-seam-hardening`
- Stage 3 app-level lazy init
- Stage 2/OneStop dispatch duplication and HIL mixing

2. `stage4-binding-and-repair-contract-hardening`
- TruthGate advisory binding
- authoritative fix-scope enforcement

3. `sink-contract-normalization`
- `episode_production.jsonl` schema normalization
- `db_manager` local cursor hygiene

4. `desktop-operator-truth-alignment`
- phantom settings
- API key hint correction
- model/config truth alignment

5. `queue-and-harness-closure-sync`
- stale temp roadmap
- live-run-safe queue sync / operator guidance gaps

## 8. Non-Issue Highlights

These positive notes reduce duplicate future work:

- Stage 2/3/4 context snapshot pattern remains broadly sound at the orchestrator boundary
- Stage 4 top-level exception handling and audit flush path are structurally solid
- `append_jsonl_record` lock design is currently adequate for main-thread Stage 4 writes
- regression tier layering remains conceptually clean
- Stage 3 binding categories for `scene_completeness`, `arc_timeline`, and `capital_unit` are the right hardening seam

## 9. 3-Pass Draft Audit

Pass 1 - Structure and scope:
- merged all five lanes into one draft
- separated action-bearing vs watchlist vs non-issues
- kept live-run constraints explicit

Pass 2 - Evidence and consistency:
- re-verified top cross-lane findings locally before promotion
- kept lower-confidence items provisional instead of overstating closure
- did not create `docs/temp/` artifacts during active run
- clarified that static survey findings remain valid even while final closure stays pending

Pass 3 - Execution and readability:
- grouped findings by seam rather than by terminal
- preserved likely post-run execution lanes
- made the post-run merge path explicit
- separated survey validity from run-dependent closure timing

Confidence:
- 96% for intended use as a rolling live-run watchlist
- not suitable as a closure doc until the active Stage 4 run reaches terminal state
