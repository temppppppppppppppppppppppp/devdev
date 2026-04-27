# T10 #58 Synthesis Map

Date: 2026-04-27
Workspace: `C:\Users\wjjo\Desktop\글도비`
Repository: `temppppppppppppppppppppppp/devdev`
GitHub Issue: #58 `[Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs`
Baseline commit at dispatch: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Document type: read-only synthesis map. Not an execution SSOT, not a patch order, not a final survey conclusion. No `docs/temp/` mirror.
Encoding: UTF-8.

## Scope

This terminal merges the #58 dispatch, the live-run handoff evidence behind it, and any present T01-T09 terminal reports into a single picture for Director review.

In scope:

- Confirm what is already known from the issue body and the source docs the dispatch cites.
- Assemble a pending-evidence matrix for T01-T09 because none of those terminal reports were saved to this folder at synthesis time.
- Classify the most likely root-cause families against the seven candidate families requested by the dispatch.
- Map regression-test candidates that can be justified from current evidence alone, without claiming the issue is reproduced or fixed.
- Recommend the next safe step (additional survey, targeted tests first, fresh live-run proof gate, or execution SSOT) consistent with AGENTS.md governance, Director authority, and the live-merge harness.

Out of scope:

- Source-code edits, test edits, GitHub edits, DB writes, branch/commit/PR creation.
- Restarting or re-running the stopped 5-arc run.
- Editing other terminal reports.
- Creating an execution SSOT or any `docs/temp/` execution mirror.
- Claiming clean 5-arc readiness, claiming the issue is fixed, or promoting Python/canary signals into final narrative judgment.

## Commands / Evidence

Directory inventory at synthesis time:

- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`
  - `stage4-post-select-conflict-parallel-investigation-dispatch.md` (present)
  - `terminal-01-current-run-forensics.md` (absent)
  - `terminal-02-postselect-conflict-route.md` (absent)
  - `terminal-03-stage3-stage4-handoff.md` (absent)
  - `terminal-04-continuity-authority-carriers.md` (absent)
  - `terminal-05-memory-cache-side-effects.md` (absent)
  - `terminal-06-retry-hydration-replay.md` (absent)
  - `terminal-07-context-cache-lineage.md` (absent)
  - `terminal-08-regression-gap-design.md` (absent)
  - `terminal-09-artifact-truth-samples.md` (absent)
  - `terminal-10-synthesis-map.md` (this file, being written)

The sibling investigation `docs/2026-04-27/security-parallel-investigation/` has T01, T02, T03, T04, T05, T08, T10 terminal reports already saved. That confirms the dispatch->terminal-report->synthesis pipeline works in this workspace today, and the absence of #58 terminal reports is a sequencing fact, not a process failure.

Documents read for synthesis (UTF-8 read-back):

- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md`
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`
- `docs/2026-04-27/gcp-iam-5arc-sleep-ops-context.md`
- `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md` (selected lines around the Jan1/Jan3 contradiction)
- `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md` (P0/P1 closeout section, especially the T6/T7 continuity authority item)
- `AGENTS.md` (system-track, Director authority, UTF-8, document save, live-merge governance)

Code lookups used to anchor the post-select surface:

- `Grep POST_SELECT_CONFLICT modules/` returned `modules/core/stage4_reject_runtime.py:997` mapping `"post_select_conflict" -> "POST_SELECT_CONFLICT"` inside the reject-bucket-to-category translation.
- `Read modules/core/stage4_postselect_runtime.py` (lines 1-100) showed structured `truth_pins` extraction (`_extract_post_select_truth_pins`) over `conflicts` and `contradiction_details`, including a `family_group_name` pin (proper-noun group conflict) and a `protagonist_personal_assets` pin (asset-state conflict). This proves the post-select surface is already structured and not just a free-text bucket, but it does not by itself prove that all carryover-class drifts route through it without false positives or false negatives.
- The keyword `POST_SELECT_CONFLICT` is referenced across `modules/core/stage4_outcome_runtime.py`, `modules/core/stage4_postselect_runtime.py`, `modules/core/stage4_reject_runtime.py`, `modules/core/stage4_retry_runtime.py`, `modules/core/stage4_interview_round.py`, `modules/core/stage4_policy_digest.py`, `modules/core/feedback_system.py`, plus tests `tests/test_stage4_orchestrator.py`, `tests/test_stage4_interview_round.py`, `tests/test_stage4_advisory_escalation_seam.py`, `tests/test_failure_analyzer.py`, `tests/test_chief_writer_candidate_lane_f.py`, `tests/test_quality_regression.py`, `tests/test_stage4_handoff_carryover_guardrail.py`, `tests/test_stage4_lane4_sink_contract.py`, `tests/test_arc_difficulty.py`, `tests/test_stage2_preflight_helpers.py`, `tests/test_feedback_system.py`. T02 and T08 should attest that this is the full surface; this synthesis only notes the spread.

Live-run anchors restated for the record:

- Run id `20260427_070602_68e560f5d2`, Stage attempt session id `20260427_070604`, target `projects/01_골든카나리아`.
- Stage4 in-session attempt verdicts at the stop snapshot:
  - `ep4`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep5`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep6`: `REJECT:LOGIC_ERROR | REJECT:CONSTRAINT_VIOLATION | REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep7`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep8`: `REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep9`: `REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT` (no PASS persisted; run was stopped)
- The handoff calls the active bottleneck "downstream continuity/history drift" with named symptom shapes "institution naming" and "duplicated continuation beats" (handoff doc lines 89-93 and 117-122).
- Memory/cache transport was demonstrably active in this session (cached tokens 8,020,575; 207 `context_cache_attempts` rows; `VecMem ... fallback=false` log lines), but the handoff is explicit that this proves transport only, not final quality success.
- The 2026-04-26 stabilization SSOT (lines 690-707) records the standing P1: T6/T7 continuity authority needs fresh multi-arc proof; session memory and context caching are helper telemetry, not the authority carrier for Jan1/Jan3-class drift.
- The 2026-04-26 post-run merge audit (lines 78-107) is the recorded prior incident shape: Blueprint time flow used `2006년 1월 1일` while Arc state required `2006년 1월 3일`, and the run hit Stage3 user-abort.

This synthesis intentionally did not open the live `project_data.db`, the active session log, or generated manuscript bodies. Those are T01 (DB/log) and T09 (artifact truth) deliverables.

## Findings

1. **Investigation is not yet complete.** Only the dispatch exists in this folder. T01-T09 terminal reports have not been saved as of synthesis time. Any conclusion below must be read as "candidate and pending evidence", not "established root cause".

2. **The current symptom is recovering, not unrecovering.** Compared to early-April canary runs (ep2 needing 9 attempts, ep4 with 4 REJECTs and no PASS in one DB snapshot), the current 5-arc run shows bounded 2-to-4 attempt recovery for ep4 through ep8, with ep9 still open at stop. This is an incremental improvement of recovery behavior, not a clean run.

3. **The classifier name "POST_SELECT_CONFLICT" is already structured at the source.** `modules/core/stage4_postselect_runtime.py` extracts `truth_pins` with families like `proper_noun_group` (matches the "institution naming" symptom) and `asset_state` (a numeric/asset family, distinct from institution naming). `modules/core/stage4_reject_runtime.py` then maps the `post_select_conflict` bucket to the `POST_SELECT_CONFLICT` category. So the runtime is not collapsing all drift into one opaque bucket; it carries family-level structure forward. This makes "post-select classifier over-broadness" a real candidate, but not the most likely sole root cause.

4. **The Jan1/Jan3-class incident shape is still on the open risks list.** The 2026-04-26 stabilization SSOT (lines 690-707) explicitly leaves "T6/T7 continuity authority needs fresh multi-arc proof" as an unclosed P1. The current 5-arc run was stopped before producing such proof. So even though Stage4 is recovering, the underlying authority-projection contract is not yet validated under live multi-arc conditions.

5. **Memory/cache evidence is high but interpretively limited.** Vertex `cachedContents` and VecMem/`fallback=false` calls are confirmed active. Per the handoff and the stabilization SSOT, this only proves transport; it does not prove that helper layers are filtering rejected/stale content out of future Stage4 context. T05 and T07 must distinguish memory write timing from memory read/use timing before a cache pollution claim is justified.

6. **The handoff names two narrative-truth symptoms that are not currently visible in structured state.** "Institution naming" drift and "duplicated continuation beats" are described in operator language. T02 (post-select route) and T09 (artifact truth) must show whether the runtime sees those exact families as structured `truth_pins` / continuity-pin reasons, or only as free-text reject conflict lines.

7. **Recovery is not the same as durability.** ep6 needed three rejects (`LOGIC_ERROR | CONSTRAINT_VIOLATION | POST_SELECT_CONFLICT`) before PASS, and ep8 needed two `POST_SELECT_CONFLICT` rejects. ep9 stopped at two `POST_SELECT_CONFLICT` rejects with no PASS. A retry-band that always trends toward more rejects in deeper episodes is consistent with carryover/continuity drift accumulating across the arc, not with a single-episode prompt issue.

## Root-Cause Candidates

The dispatch listed seven candidate root-cause families. Below is an evidence-bounded assessment with each family ranked by current likelihood. Likelihood here means "probability that this family contributes to #58", not "probability that it is the sole cause".

| Family | Likelihood | Why current evidence supports it | What current evidence does not yet prove |
| --- | --- | --- | --- |
| Stage3->Stage4 handoff lineage failure | High | The Jan1/Jan3 incident was a Stage3 contradiction; the current Stage4 rejects are framed as carryover drift coming into Stage4. Lineage and ordinal/episode-boundary failures are exactly the path that would surface as POST_SELECT_CONFLICT downstream. | That stage3->stage4 packets specifically deliver stale arcs/blueprints in the current run. T03 needs to confirm or rule this out. |
| Continuity authority not consumed or not specific enough | High | The stabilization SSOT already flagged T6/T7 as unproven under multi-arc. Director continuity, authoritative continuity projection, episode_state_arbiter, immutable_fact_contract, and continuity_pin_guard exist; the open question is whether Stage4 actually consumes them with the right specificity (date, institution, asset state, continuation beats). | Whether those modules are wired into the current post-select route as authority, or only as parallel advisory. T04 must answer this. |
| Previous-attempt hydration or retry feedback replay | Medium-High | ep8 and ep9 both show repeated POST_SELECT_CONFLICT inside the same episode. If retry hydration replays prior rejected attempts as reference content (instead of as failure feedback only), the next attempt can re-emit the same drift and re-hit the same family of conflict. | Whether `stage4_retry_runtime` / `stage4_interview_round` actually replays prior content into the new prompt vs. only forwarding failure_category + reason. T06 must answer this. |
| Post-select classifier over-broadness | Medium | `_extract_post_select_truth_pins` is structured, but `stage4_reject_runtime` falls back to `_reject_bucket.upper()` when no specific category fits. That generic upper-case path could be silently absorbing distinct drift shapes under the same `POST_SELECT_CONFLICT` label. | Whether the classifier ever rejects a manuscript that is actually narratively coherent (false positive) or whether it ever passes one with concealed drift (false negative). T02 must answer with concrete examples. |
| Stale context-cache injection | Medium | Vertex `cachedContents` is materially active. AGENTS.md explicitly warns that helper memory/cache layers must not become final authority. Cached Stage2/Stage3 context that no longer reflects the latest authority projection could push older institution names or older state back into Stage4 prompts. | Whether the cache currently invalidates on Stage2/Stage3 state changes, and whether bypass/lineage fingerprints exist. T07 must answer this. |
| Session/vector memory side-effect pollution | Medium-Low | Session/vector memory is active and writes after PASS-class events. If a partially settled or rejected attempt enters memory and is later retrieved in a future Stage4 context, it could silently reintroduce the drift it was rejected for. | Whether memory currently filters rejected/partially settled rows out of retrieval, and whether memory write timing is gated on Director PASS. T05 must answer this. |
| Actual artifact-level narrative contradiction not represented in structured state | Medium | The Jan1/Jan3 case is exactly this: a real narrative contradiction that needed structured authority (date authority) to be enforced. The handoff also names "duplicated continuation beats" as an operator-level symptom that may not have a dedicated `truth_pin` family yet. | Whether the current ep4-ep9 rejects map cleanly onto existing structured pin families or rely on free-text conflict lines. T09 must show artifact-level evidence; T08 must propose regression coverage where the current pin set is insufficient. |

Composite reading: the most likely failure shape is a combination of (a) Stage3->Stage4 handoff or continuity-authority specificity gaps producing the drift, (b) retry/previous-attempt hydration or stale cache reintroducing it across attempts, and (c) parts of the drift surface presenting as narrative-truth symptoms (continuation beats, institution naming) that are not yet first-class structured pins. No single family above is currently disprovable from the evidence reviewed at synthesis time.

## Regression / Test Candidates

These are candidate test shapes only. T08 will write the binding regression-design report. None of these are committed orders, and Python tests are tripwires for Director, never the final narrative judge.

1. Stage3->Stage4 handoff packet lineage test: assert that a Stage3 envelope rebuilt after a state change cannot deliver a stale-arc or stale-blueprint reference into Stage4 context. Targets `modules/core/stage3_envelope_builder.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage4_context_packets.py`. Uses fixtures from `tests/test_stage4_context_builder.py`, `tests/test_stage2_stage3_episode_boundary_guardrail.py`.
2. Previous-attempt hydration filter test: assert that `stage4_retry_runtime` and `stage4_interview_round` forward only failure category + reason for a previous REJECT, not the rejected content body. Targets `modules/core/stage4_interview_round.py`, `modules/core/stage4_retry_runtime.py`. Builds on `tests/test_stage4_handoff_carryover_guardrail.py`, `tests/test_stage4_carryover_ceiling_handoff.py`, `tests/test_stage4_ep9_remediation.py`.
3. POST_SELECT_CONFLICT specificity test: assert that the bucket-to-category fallback in `stage4_reject_runtime.py:997` does not erase a more specific known drift family (institution naming, duplicated continuation beat, asset state, date drift). Targets `modules/core/stage4_postselect_runtime.py`, `modules/core/stage4_reject_runtime.py`. Pairs with new `truth_pins` families if T08 finds the existing set is incomplete.
4. Continuity authority consumption test: assert that an explicit conflict registered in `authoritative_continuity_projection` / `continuity_pin_guard` / `episode_state_arbiter` causes Stage4 to either reject or repair, not silently produce a new attempt that can re-hit the same conflict. Targets `modules/core/authoritative_continuity_projection.py`, `modules/core/continuity_pin_guard.py`, `modules/core/episode_state_arbiter.py`, `modules/core/stage4_immutable_fact_contract.py`.
5. Memory/cache rejected-content suppression test: assert that a REJECTed Stage4 candidate is not written into session/vector memory in a way that allows future Stage4 retrieval to re-emit the same drift. Targets `modules/core/session_memory_envelope.py`, `modules/core/vec_memory.py`, `modules/core/stage4_post_pass_runtime.py`.
6. Context-cache lineage invalidation test: assert that an authoritative state change (e.g., Jan1 -> Jan3 fix) invalidates downstream cached prompt context before the next Stage4 attempt. Targets `modules/domain/agents/director_caching.py`, `modules/core/stage0_handoff.py`, `modules/core/stage4_context_packets.py`. Builds on `tests/test_audit_stage34_cache_gate_corpus.py`, `tests/test_audit_stage34_cache_proof.py`.
7. Narrative-truth pin coverage test: for the operator-named symptom "duplicated continuation beats", confirm there is at least one `truth_pin` family that can fire structurally; if not, propose a new family in T08 rather than relying on free-text conflict lines.
8. Per-episode reject-trend regression test: assert that POST_SELECT_CONFLICT count per episode within a single session is bounded and that ep9-class deep episodes do not exhibit a monotonic increase in reject count under the same arc.

## Dependencies On Other Terminals

This synthesis depends on the following terminals once they save. Each row records the decision the terminal should unlock and the part of this synthesis that is currently soft because the terminal has not run.

| Terminal | Save path | Decision it should unlock | Currently-soft part of this synthesis |
| --- | --- | --- | --- |
| T01 | `terminal-01-current-run-forensics.md` | Confirms the live DB/log shape behind ep4-ep9 rejects, including session id, attempt rows, verdicts, and artifact pointers. | Section "Live-run anchors" relies on the handoff doc only; T01 must confirm by direct read-only DB query. |
| T02 | `terminal-02-postselect-conflict-route.md` | Confirms whether POST_SELECT_CONFLICT is structurally specific or partly opaque, and where Director, post-select, runtime reject, and persistence boundaries actually sit. | The "post-select classifier over-broadness" likelihood and the bucket-fallback finding above. |
| T03 | `terminal-03-stage3-stage4-handoff.md` | Confirms whether Stage3->Stage4 packets can deliver stale arc/blueprint/episode-boundary state into Stage4. | The "Stage3->Stage4 handoff lineage failure" likelihood. |
| T04 | `terminal-04-continuity-authority-carriers.md` | Confirms which continuity authority is supposed to govern date, institution, asset, and continuation-beat truth at Stage4, and whether Stage4 actually consumes it as authority vs. advisory. | The "Continuity authority not consumed or not specific enough" likelihood and the standing T6/T7 P1. |
| T05 | `terminal-05-memory-cache-side-effects.md` | Confirms whether session/vector memory can carry rejected or partially settled content into future Stage4 reads. | The "Session/vector memory side-effect pollution" likelihood. |
| T06 | `terminal-06-retry-hydration-replay.md` | Confirms whether retry hydration replays prior content vs. only failure feedback. | The "Previous-attempt hydration or retry feedback replay" likelihood and the ep8/ep9 repeated-reject pattern reading. |
| T07 | `terminal-07-context-cache-lineage.md` | Confirms whether Vertex `cachedContents` / BaseAgent / director caching invalidates on authoritative state changes and whether stale lineage can be reinjected. | The "Stale context-cache injection" likelihood and the cache-active-but-not-authority interpretation. |
| T08 | `terminal-08-regression-gap-design.md` | Confirms which of the regression-test candidates above are gaps vs. already covered by existing tests, and proposes exact new test names/fixtures. | The "Regression / Test Candidates" section as a whole. |
| T09 | `terminal-09-artifact-truth-samples.md` | Confirms whether the operator-described symptoms (institution naming drift, duplicated continuation beats, prior-failure replay, date drift) appear in actual ep4-ep9 artifacts and whether they map to structured pins or only to free-text conflict lines. | The "Actual artifact-level narrative contradiction not represented in structured state" likelihood and the narrative-truth pin coverage suggestion. |

If T01-T09 are run later, this synthesis should be revisited and either updated in place or superseded by a follow-on synthesis pass.

## Open Questions

1. Does Stage4 in the current 5-arc run consume `authoritative_continuity_projection` as authority for date / institution / asset / continuation-beat truth, or as advisory only? T04 must answer.
2. Are the operator-named symptoms ("institution naming drift", "duplicated continuation beats") representable as structured `truth_pins` families today, or are they only free-text conflict lines? T02 + T09 must answer.
3. Is the bucket-to-category fallback in `stage4_reject_runtime.py:997` ever actually exercised in the current live run, and if so, for which drift family? T02 must answer with DB/log evidence.
4. When Stage4 retries after a POST_SELECT_CONFLICT, does the next attempt receive the rejected candidate body, or only its failure category and reason? T06 must answer.
5. Do session and vector memory writes wait for Director PASS, or can a partially settled / REJECT candidate enter memory and later be retrieved into a future Stage4 attempt? T05 must answer.
6. When a Stage2/Stage3 authoritative state change fixes a contradiction (e.g., Jan1 -> Jan3), does the Vertex context cache and BaseAgent/director cache invalidate downstream cached prompt content before the next Stage4 attempt? T07 must answer.
7. For ep9 specifically (which stopped without PASS), is the reject-cause family identical across both attempts, or did it shift between attempts? T01 + T09 must answer with attempt-level data and artifact diff.
8. Does the workspace already have a structured rule that "duplicated continuation beat" is a Stage4 reject family, or is that symptom currently being detected by a generic similarity / repetition check? T02 + T08 must answer.

## Closure Recommendation

This synthesis is intentionally not promoting itself into an execution SSOT, and not asking for an immediate code patch.

Recommended sequencing for the Director, in order:

1. **Run T01-T09 first.** Synthesis without their reports cannot triangulate the seven root-cause families per the dispatch. Each missing terminal collapses one family above into "candidate, unproven". This is consistent with `docs/implementation/evidence-triangulation-contract.md` and the live-merge harness rule that final survey conclusions wait until raw evidence is in.
2. **Re-run T10 synthesis after T01-T09 save.** The intent is to convert the likelihood column above into evidence-anchored findings, retire ruled-out families, and lock the surviving root-cause set.
3. **Then decide between targeted regression first vs. fresh live-run proof gate.** Both are AGENTS.md-aligned. The trade-off:
   - Targeted regression tests first close the surface on family-specific reproducibility and protect against re-regression after any future patch. They cost less than a full multi-arc run and they do not need an active live run. They are the right next step if T02 / T03 / T06 surface a structurally reproducible bug shape that does not require a real arc context to reproduce.
   - A fresh live-run proof gate (a clean reuse-or-fresh 5-arc run with strict failure policy) is the right next step if the surviving root-cause set is dominated by emergent multi-arc behavior (continuity authority specificity, cache lineage under multi-episode load, retry hydration across long attempt chains). The 2026-04-26 stabilization SSOT already records this as the unmet T6/T7 P1.
   - The most defensible path is "targeted regression first, then fresh live-run proof gate", because regression closes the cheap, structurally-verifiable surface before the expensive live run is committed, and the live run then becomes a proof gate, not an investigation tool.
4. **Only after the surviving root-cause set is locked should an execution SSOT be created.** That SSOT must be saved under `docs/2026-04-27/` as the canonical, then mirrored to `docs/temp/` per AGENTS.md. It must pass the document 3-pass audit at 95%+ confidence before any code change starts. If multiple execution SSOTs end up active at the same time, the aggregate roadmap rule applies.
5. **Until that SSOT exists, do not claim that #58 is fixed, do not claim clean 5-arc readiness, and do not promote helper memory/cache evidence into final narrative authority.**

This synthesis explicitly does not authorize any source-code change, any test implementation, any GitHub issue closure, any DB mutation, any 5-arc live-run restart, or any `docs/temp/` execution mirror.

## 3-Pass Save Audit

Pass 1 - structure and scope:

- PASS. The document is a synthesis map, not an execution SSOT, and not a patch order.
- PASS. T01-T09 absence is recorded explicitly and a pending-evidence matrix is provided per dispatch instruction.
- PASS. All seven candidate root-cause families from the dispatch are addressed.
- PASS. No claim of clean 5-arc readiness.

Pass 2 - evidence and authority:

- PASS. Source docs were read with explicit UTF-8 reads.
- PASS. Code anchors were derived from the existing tracked files; no module was patched.
- PASS. Helper memory/cache evidence is described as helper, not authority, consistent with AGENTS.md and the 2026-04-26 stabilization SSOT P1 line.
- PASS. Director authority is preserved; Python tools are described as tripwires only.

Pass 3 - readability and operational use:

- PASS. The document follows the dispatch report schema exactly.
- PASS. Each open question maps to at least one terminal owner.
- PASS. Closure recommendation gives a sequencing plan with explicit gates rather than a single-step instruction.

Estimated operational confidence at synthesis time, given that T01-T09 are absent: 90%. Confidence is intentionally below 95% because the root-cause likelihood ranking depends on terminal evidence that has not yet been produced. The synthesis structure, scope, and procedural conclusions are at higher confidence than the family-likelihood ranking itself.
