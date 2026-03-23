Date: 2026-03-23
Status: final (3-pass audited)
Document Type: evidence-based bottleneck remediation plan
Canonical Path: `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain.md`
- `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator.md`
- `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression.md`
- `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
- `docs/2026-03-23/q1-q8-r2-merge-audit.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/00_00/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_00/plans/blueprints/blueprint_0003.txt`
- `projects/00_00/logs/artifacts/stage4/ep_0003/attempt_02/selected_before_fix__A.txt`
- `projects/00_00/logs/artifacts/stage4/ep_0003/attempt_04/selected_candidate__A.txt`
- `projects/00_00/logs/pass_rate_monitor.json`
- `projects/00_00/logs/episode_production.jsonl`
- `projects/00_00/project_data.db`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace with runtime/test/doc/model-default edits and current fresh-run artifacts for projects/00_00`
- Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Resume Drift Summary: `same HEAD; plan synthesized from live console/artifact/DB evidence after ROL 3-terminal survey completion`
Side-Effect Coverage:
- artifact truth: yes
- DB truth: yes
- console/operator truth: yes
- JSONL/metrics truth: yes
- config/bootstrap: considered, not primary

---

## 1. Executive Summary

The current bottleneck is **not** a repo-wide logging, DB, or Stage 2 architecture failure.

The fresh run and the completed ROL survey together point to a narrower diagnosis:

1. **Stage 4 is not faithfully materializing the Stage 3 scene contract into manuscript structure.**
2. **Stage 4 opening continuity is being contaminated after a good Stage 3 handoff.**
3. **Director PASS and post-select REJECT are still split across two misaligned decision layers.**
4. **The retry loop is accumulating feedback, but not converging on actionable patch targets.**

Evidence does **not** support `Stage 2 pacing is too thin` as the first-order cause.

- Stage 2 Arc 1 tactical design is reasonably dense and coherent.
- Stage 3 Episode 3 blueprint is explicit: 5 scenes, correct opening location, correct time flow, and correct family-confrontation beats.
- The major drift appears when Stage 4 candidate manuscripts are written and then repeatedly patched.

Operational verdict:

- `fix first, rerun second` remains the best ROI.
- The next wave should target **Stage 4 write/fix/gate seams**, not broad Stage 2/3 or repo-wide infrastructure.

## 2. Evidence Basis

### 2.1 Fresh-Run Console

Key live run signals from `docs/2026-03-23/console.txt`:

- Stage 2 Arc 1 passed strongly:
  - `Arc 1 PASS score=100` around `console.txt:339`
- Stage 3 Episodes 1-4 all passed:
  - Episode 1 PASS around `console.txt:399`
  - Episode 2 PASS around `console.txt:414`
  - Episode 3 PASS around `console.txt:430`
  - Episode 4 PASS around `console.txt:446`
- Stage 4 Episode 3 repeatedly raised:
  - `씬 완성도 부족: 0/5 씬만 완성` around `console.txt:496-507`, `566-580`, `651-671`, `994-1006`
- Stage 4 Episode 3 also repeatedly showed:
  - Director PASS/PASS_WITH_FIX first
  - post-select continuity/history conflict downgrade after that
  - examples around `console.txt:753-772`, `888-901`, `1025-1038`
- Retry pathology appeared explicitly:
  - `Fix Pack patch_targets is empty` around `console.txt:901`, `1061`

### 2.2 Artifact Truth

Stage 3 Episode 3 blueprint artifact:

- `projects/00_00/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`
- `scene_count = 5`
- `start_location = 강남 5성급 호텔 라운지 카페 프라이빗 룸`
- `time_flow = 오전 11시 -> 오후 1시`
- scene breakdown explicitly models:
  - hotel intrusion
  - sedan transfer
  - family confrontation in the study
  - investment-firm declaration
  - corridor exit

Stage 4 Episode 3 manuscript artifacts:

- `projects/00_00/logs/artifacts/stage4/ep_0003/attempt_02/selected_before_fix__A.txt`
- `projects/00_00/logs/artifacts/stage4/ep_0003/attempt_04/selected_candidate__A.txt`

Observed facts:

- neither artifact contains markdown scene headers
- neither artifact contains `###` scene blocks
- both are long prose blocks with only a few bracket headers
- attempt 2 opens with:
  - `[오후 2시 15분, 여의도 콘래드 호텔 스위트룸]`

This is direct evidence that the Stage 4 writer is **not preserving the Stage 3 opening contract** for Episode 3.

### 2.3 DB Truth

From `projects/00_00/project_data.db`:

- Stage 4 Episode 3 `director_selections` rows:
  - round 1: `REJECT`, score `44`, firewall triggered
  - round 2: `PASS_WITH_FIX`, score `90`
  - round 3: `PASS`, score `95`
  - round 4: `PASS`, score `95`
- Stage 4 Episode 3 `stage_attempts` rows:
  - attempts 1-4 all end as `REJECT`
  - attempt 1 has `failure_category = LOGIC_ERROR`
  - attempts 2-4 have `failure_category = NULL`
  - attempts 2-4 are all patch attempts (`is_patch = 1`)
- `attempt_raw_rationale` rows exist for Episode 3:
  - `director_thinking` length about `2.9K -> 4.2K`
  - `advisory_warnings_raw` length about `1.3K -> 2.1K`

### 2.4 Pass-Rate / JSONL Truth

From `projects/00_00/logs/pass_rate_monitor.json` and `projects/00_00/logs/episode_production.jsonl`:

- attempt 2 still had concrete `patch_targets` (4 items)
- attempts 3 and 4 had `patch_targets = []`
- rounds 3 and 4 record:
  - `fix_pack_ready = False`
  - `fix_pack_reason = missing_patch_targets`
- round 4 also records:
  - `plateau_detected = True`

This is strong evidence that the loop is not merely failing; it is **degrading**.

## 3. Non-Primary Suspects

### 3.1 Stage 2 pacing is not the first-order bottleneck

Why this is not the primary explanation:

- Stage 2 passed cleanly in the run.
- The Stage 3 blueprint for Episode 3 is not vague. It already contains the correct high-level sequence, location, and time-flow contract.
- The Stage 4 candidate drift is not a subtle quality issue. It is a direct opening-scene contradiction against the Stage 3 artifact.

Conclusion:

- `Stage 2 tactical density` may still be tunable later.
- It is not the highest-ROI bottleneck for this run family.

### 3.2 ROL T2/T3 findings are not primary blockers here

The ROL global survey found valuable residuals in persistence/operator/config/test coverage, but:

- T2 was mostly observability and parity debt
- T3 was mostly config/test hygiene debt
- neither explains why Episode 3 Stage 4 rewrote the correct Gangnam/morning opening into Yeouido/afternoon

## 4. Bottleneck A: Stage 4 Manuscript Structure Is Not Reflecting the Blueprint Scene Model

### Evidence

- Stage 3 blueprint declares 5 scenes with explicit scene-by-scene goals and locations.
- Stage 4 candidates still trigger `씬 완성도 부족: 0/5 씬만 완성` repeatedly in the live run.
- Stage 4 manuscript artifacts do not emit scene headers or clear scene block boundaries.

### Diagnosis

The validator is no longer the main problem.

The more likely issue is:

- the **Chief Writer prompt contract** carries `scene_breakdown` as JSON-like context,
- but the actual manuscript-generation contract does not force scene-by-scene realization strongly enough,
- so the writer can output fluent prose that ignores the scene model entirely.

### Code Targets

- `modules/domain/agents/chief_writer_context.py:177`
- `modules/domain/agents/chief_writer_context.py:253`
- `modules/core/writer_template.py:115`
- `modules/core/writer_template.py:280`
- `modules/core/pre_director_manuscript_checker.py:153`
- `modules/domain/agents/chief_writer.py:1329`

### Solution

Implement a **scene-locked writing contract**:

1. convert blueprint scene breakdown into an explicit scene-by-scene writing skeleton
2. require Stage 4 candidates to emit recognizable scene boundaries
3. make pre-director manuscript checks fail fast when scene reflection is effectively zero

### Acceptance Criteria

- Episode 3-like manuscripts emit explicit 5-scene structure
- scene reflection no longer reads as `0/5`
- writer output cannot pass pre-director checks when it collapses the blueprint into unstructured prose

## 5. Bottleneck B: Stage 4 Opening Continuity Is Being Contaminated After a Good Handoff

### Evidence

Stage 3 Episode 3 blueprint:

- start location: `강남 5성급 호텔 라운지 카페 프라이빗 룸`
- time flow: `오전 11시 -> 오후 1시`

Stage 4 attempt 2 selected manuscript:

- opens with `오후 2시 15분, 여의도 콘래드 호텔 스위트룸`

The console and pass-rate artifacts then report:

- hotel location conflict
- repeated father confrontation / history conflict
- notebook storage inconsistency

### Diagnosis

The Stage 3 handoff itself is good enough.

The likely failure is inside Stage 4 context assembly and opening-scene generation:

- the writer receives too many competing context sources
- the opening anchor is not treated as immutable
- the patch loop keeps rewriting around the contradiction instead of reasserting the correct opening truth

### Code Targets

- `modules/core/stage4_context_builder.py:1914`
- `modules/domain/agents/chief_writer_context.py:177`
- `modules/core/stage4_interview_round.py:760`
- `modules/core/stage4_orchestrator.py:1698`
- `modules/core/stage4_orchestrator.py:2007`

### Solution

Create an **opening-anchor packet** that cannot be casually overridden:

1. derive a compact immutable opening contract from:
   - previous manuscript ending
   - current blueprint `start_location`
   - current blueprint `time_flow`
   - blueprint scene 1 summary / goal
2. inject that packet into writer and director paths explicitly
3. compare manuscript opening lines against that packet before accepting PASS or PASS_WITH_FIX
4. when the opening anchor is broken, escalate to blueprint regeneration or opening rewrite, not general prose patching

### Acceptance Criteria

- a Gangnam/morning blueprint cannot yield a Yeouido/afternoon opening without triggering an immediate hard continuity failure
- hotel/time drift is caught before late post-select downgrade
- patch attempts keep the first scene aligned with Stage 3 truth

## 6. Bottleneck C: Director PASS And Post-Select REJECT Still Form A Split-Brain Verdict Chain

### Evidence

Episode 3 Stage 4 sequence in DB and console:

- round 2: Director `PASS_WITH_FIX`, score `90` -> final row still `REJECT`
- round 3: Director `PASS`, score `95` -> final row still `REJECT`
- round 4: Director `PASS`, score `95` -> final row still `REJECT`

Console shows:

- PASS or PASS_WITH_FIX is declared first
- then post-select continuity/history checks downgrade it

### Diagnosis

The system still has two decision layers that are not aligned enough:

- Director is making a positive verdict without the full weight of the eventual post-select conflict surface
- post-select then vetoes that verdict afterward

This creates two costs:

- wasted retry rounds
- noisy learning, because the operator sees a positive Director score that was never truly safe

### Code Targets

- `modules/core/stage4_interview_round.py:3574`
- `modules/core/stage4_director_runtime.py:364`
- `modules/core/stage4_reject_runtime.py:309`
- `modules/core/stage4_outcome_runtime.py`

### Solution

Unify the verdict chain:

1. treat Director PASS as **provisional** until post-select checks clear
2. feed post-select continuity/history conflict summaries into the same decision contract earlier
3. record explicit downgrade cause and category when provisional PASS is vetoed
4. stop presenting a clean PASS operator event before post-select resolution is known

### Acceptance Criteria

- no Episode 3-style `PASS -> immediate REJECT downgrade` sequence without explicit provisional status
- downgraded rows always persist a concrete `failure_category`
- post-select conflict reasons are visible inside the same verdict chain, not only after the fact

## 7. Bottleneck D: Retry / Fix-Pack Synthesis Is Degrading Instead Of Converging

### Evidence

From pass-rate and episode-production evidence:

- attempt 2 had 4 concrete patch targets
- attempt 3 had `patch_targets = []`
- attempt 4 had `patch_targets = []`
- rounds 3 and 4 both marked:
  - `fix_pack_ready = False`
  - `fix_pack_reason = missing_patch_targets`
- round 4 marked:
  - `plateau_detected = True`

From DB:

- `retry_directives` lengths keep growing across attempts:
  - about `1346 -> 3062 -> 3842`

### Diagnosis

The retry loop is accumulating too much natural-language feedback and not preserving enough actionable structure.

By rounds 3-4:

- the patch path still runs
- but the fix pack no longer knows what to patch
- so the system burns more rounds without a sharper edit target

### Code Targets

- `modules/core/stage4_interview_round.py:572`
- `modules/core/stage4_interview_round.py:1675`
- `modules/core/stage4_reject_runtime.py:309`
- `modules/core/stage4_retry_runtime.py:888`
- `modules/core/stage4_retry_runtime.py:951`

### Solution

Replace the current freeform retry drift with a **diff-driven retry contract**:

1. synthesize patch targets from:
   - blueprint scene 1-2 truth
   - previous accepted manuscript ending
   - current selected manuscript opening/body
2. dedupe repeated contradiction families
3. keep only the top 3 blocking directives
4. if `patch_targets` is empty once after a provisional PASS downgrade, switch to:
   - blueprint regeneration, or
   - targeted opening rewrite lane
   not another generic patch round

### Acceptance Criteria

- `missing_patch_targets` cannot repeat across two consecutive patch attempts
- retry directives shrink and sharpen instead of growing without bound
- plateau detection causes route escalation, not one more identical patch loop

## 8. Bottleneck E: Failure Classification Still Falls Off On Post-Select Rejects

### Evidence

Stage 4 Episode 3 `stage_attempts` rows:

- attempt 1: `failure_category = LOGIC_ERROR`
- attempts 2-4: `failure_category = NULL`

But the same attempts clearly contain:

- post-select continuity conflict
- post-select history conflict
- empty patch-target pathology

### Diagnosis

The learning substrate is much better than before, but final reject classification is still incomplete exactly where the loop becomes most pathological.

### Code Targets

- `modules/core/stage4_interview_round.py:5609`
- `modules/core/stage4_interview_round.py:5772`
- `modules/core/stage4_reject_runtime.py:309`

### Solution

Add explicit reject-category mapping for:

- `post_select_continuity_conflict`
- `post_select_history_conflict`
- `missing_patch_targets`
- `retry_plateau`

### Acceptance Criteria

- post-select downgrades never persist `NULL` failure categories
- failure analyzer and later surveys can group these cases without freeform text parsing

## 9. Recommended Fix Order

### Priority 1. Scene-Locked Writer Contract

Why first:

- the `0/5 scene completeness` warning is present from the first manuscript attempt
- if Stage 4 does not materialize the blueprint scene model, later fixes only patch around a broken base text

### Priority 2. Opening-Anchor Packet

Why second:

- Episode 3 failure is not a minor style miss
- it is an immediate first-scene continuity drift against Stage 3 truth

### Priority 3. Verdict-Chain Unification

Why third:

- PASS and post-select veto cannot keep fighting each other if we want reliable rerun evidence

### Priority 4. Retry / Fix-Pack Sharpening

Why fourth:

- once the first two are stronger, retry quality will improve
- but the empty patch-target loop still needs a structural stop rule

### Priority 5. Failure Category Completion

Why fifth:

- this is not the main content bug
- but it is necessary for higher-quality learning from the next rerun

## 10. Suggested Next Run Strategy

Do **not** jump straight to another long soak run from the current state.

Recommended order:

1. implement the Stage 4 fix cluster above
2. rerun a short targeted sanity lane around Arc 1 Episode 3-style continuity pressure
3. only then start the 10-arc run

Reason:

- the next long run should test long-run consistency and context pressure
- it should not be consumed by a still-open Stage 4 local loop pathology

## 11. Deferred / Not First Order

These should stay behind the Stage 4 fix cluster:

- Stage 2 pacing retuning
- Q7-style long-run context budget redesign
- T2/T3 global config/test hygiene fixes
- broad observability waves already closed

## 12. 3-Pass Audit Record

### Pass 1. Structure and Scope

- kept scope to current fresh-run bottlenecks plus current ROL survey conclusions
- excluded older already-closed broad DB/console waves
- used artifact truth, DB truth, console truth, and JSONL truth together

### Pass 2. Evidence and Consistency

- confirmed Stage 3 Episode 3 blueprint still carries the correct Gangnam / morning contract
- confirmed Stage 4 Episode 3 candidate artifact opens with Yeouido / afternoon drift
- confirmed Director selection rows and final stage attempt rows disagree on PASS vs REJECT for the same attempts
- confirmed retry patch targets collapse to empty on later rounds

### Pass 3. Execution and Readability

- converted diagnosis into a priority-ordered remediation plan
- kept each bottleneck tied to code targets and acceptance criteria
- separated primary bottlenecks from deferred structural debt

## 13. Confidence

Confidence: `96%`

Why not lower:

- the key claims are triangulated across console, artifacts, DB, and JSONL/metrics
- the primary contradiction is concrete and repeated, not inferential
- the recommended fix seams are bounded to current Stage 4 write/fix/gate ownership

Residual uncertainty:

- exact prompt-level wording changes for the Chief Writer may need one local iteration after implementation
- there may be a secondary Stage 4 context-packet contributor beyond the first opening-anchor drift
