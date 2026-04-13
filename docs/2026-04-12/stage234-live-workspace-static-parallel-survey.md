# Stage234 Live Workspace Static Parallel Survey

Date: 2026-04-12
Status: final
Canonical Path: `docs/2026-04-12/stage234-live-workspace-static-parallel-survey.md`
Scope: `Stage2 + Stage3 + Stage4 static survey on the current live workspace, including execution-doc validity drift`
Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
Baseline Dirty Summary: `tracked_modified=74, untracked=17, total=91`
Source Docs:
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
Side-Effect Coverage: static only; no new runtime artifacts or DB mutations were produced for this survey

## 1. Answer First

- New `P0`: none
- New `P1`: none reopened on the current live workspace
- Current front residuals are now mostly `P2 doc/queue drift` plus `P3 structural pressure`
- The sharpest current mismatch is no longer code truth vs code truth; it is `live code truth vs execution-doc wording`

This means the next high-ROI move is:

1. refresh the stale Stage2 / Stage3 / Stage4 execution docs and roadmap wording
2. then run the bounded fresh proof wave
3. only reopen broader structure work after post-run merge evidence

## 2. Severity Summary

### P0

- none found in this static pass

### P1

- none found in this static pass

### P2

1. Stage2 parent lane wording is stale against current live code.
   - The Stage2 SSOT and roadmap still say bounded residuals remain around `runtime_advisory` fallback, `ep_num` semantics, and carryover start-state truth.
   - Live code now shows those slices landed:
     - `stage2_finalizer.py` synchronizes `location`, `total_assets`, `capital`, `portfolio_position`, and tactical start-state rendering from previous arc authority.
     - `stage2_finalizer.py` resolves Stage2 `runtime_advisory` / `retry_directives` before sink persistence.
     - `stage2_orchestrator.py` logs `single_arc_attempt` with `ep_num=arc ordinal` and preserves absolute episode start in `meta.current_ep_start`.
   - Evidence:
     - `modules/core/stage2_finalizer.py:1764`
     - `modules/core/stage2_finalizer.py:1818`
     - `modules/core/stage2_finalizer.py:3501`
     - `modules/core/stage2_finalizer.py:4162`
     - `modules/core/stage2_orchestrator.py:1206`
     - `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md:4`
     - `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md:45`
     - `docs/2026-04-01/active-temp-execution-roadmap.md:148`
     - `docs/2026-04-01/active-temp-execution-roadmap.md:193`
     - `docs/2026-04-01/active-temp-execution-roadmap.md:424`

2. Stage3 contract-tightening SSOT is stale-likely after the new fail-only structural hardening tranche.
   - The doc still frames Stage3 validator/binding as advisory-heavy and unable to hard-block the most dangerous seams.
   - Live code now escalates `opening_anchor` and `scene_completeness` to `full` regenerate-only repair, carries `binding_regenerate_only_categories`, and surfaces that reason through runtime/meta.
   - `scene.key_events` bulk omission also now joins `scene_completeness`, so the fail-only lane is materially stronger than the doc text implies.
   - Evidence:
     - `modules/domain/agents/unified_blueprint_validator.py:76`
     - `modules/domain/agents/unified_blueprint_validator.py:424`
     - `modules/domain/agents/unified_blueprint_validator.py:1873`
     - `modules/domain/agents/unified_blueprint_validator.py:1911`
     - `modules/domain/agents/three_phase_blueprint_runtime.py:1292`
     - `modules/domain/agents/three_phase_blueprint_runtime.py:1552`
     - `modules/core/stage3_orchestrator.py:2332`
     - `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md:4`
     - `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md:50`
     - `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md:81`

3. Stage4 repair / owner-surface docs are behind the live raw-evidence and operator-summary substrate.
   - The repair SSOT scope still centers older grammar/readback framing and does not yet describe the landed raw-evidence family:
     - `stage4_raw_evidence.py`
     - Stage4 raw evidence persistence
     - FailureAnalyzer raw rationale health/watchlist/operator summary
   - The owner-surface SSOT recount is also stale: it still says `159 direct methods / 2 / 5`, while the current live recount is `166 direct methods / 2 / 5`.
   - Evidence:
     - `modules/core/stage4_raw_evidence.py:74`
     - `modules/core/failure_analyzer.py:126`
     - `modules/core/failure_analyzer.py:319`
     - `modules/core/failure_analyzer.py:426`
     - `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md:67`
     - `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md:11`
     - `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md:27`

### P3

1. Stage2 structure pressure remains real.
   - `Stage2Finalizer`: `51` direct methods, `7` methods at `120+ LOC`, `1` method at `180 LOC`
   - `Stage2Orchestrator`: `51` direct methods, `3` methods at `120+ LOC`
   - Current hotspots:
     - `modules/core/stage2_finalizer.py:3463` `_record_s2_pass_metrics` `180 LOC`
     - `modules/core/stage2_finalizer.py:1580` `_repair_stage2_pass_arc_structure` `132 LOC`
     - `modules/core/stage2_orchestrator.py:279` `_bootstrap_stage2_arc_pipeline` `153 LOC`
     - `modules/core/stage2_orchestrator.py:1182` `_run_stage2_single_arc_attempt` `133 LOC`

2. Stage3 structure pressure remains non-trivial.
   - `Stage3Orchestrator`: `50` direct methods, `4` methods at `120+ LOC`
   - Current hotspots:
     - `modules/core/stage3_orchestrator.py:828` `stage_3_batch_blueprinting` `148 LOC`
     - `modules/core/stage3_orchestrator.py:1699` `_run_stage3_blueprint_generation_handoff` `144 LOC`
     - `modules/core/stage3_orchestrator.py:2319` `_annotate_stage3_success_blueprint` `139 LOC`
     - `modules/core/stage3_orchestrator.py:3246` `_record_stage3_failure_attempt` `133 LOC`

3. Stage4 / analyzer structure pressure remains the dominant owner-surface debt.
   - `Stage4InterviewRound`: `166` direct methods, `5` methods at `120+ LOC`, `2` methods at `180+ LOC`
   - `FailureAnalyzer`: `77` direct methods, `4` methods at `120+ LOC`, `2` methods at `180+ LOC`
   - Current hotspots:
     - `modules/core/stage4_interview_round.py:7226` `_append_episode_log` `275 LOC`
     - `modules/core/stage4_interview_round.py:3129` `_normalize_director_gate_semantics` `225 LOC`
     - `modules/core/failure_analyzer.py:2571` `_build_sink_alignment_summary_payload` `286 LOC`
     - `modules/core/failure_analyzer.py:1725` `_collect_sink_alignment_raw_rationale_results` `281 LOC`

## 3. Stage-by-Stage Verdict

### Stage2

- Functional static verdict: mostly clean on the previously reopened observability / carryover trio
- Remaining risk center: structure pressure, not the older advisory / `ep_num` / carryover truth seam
- Doc verdict: stale-likely and should be refreshed before the next proof-wave bookkeeping

### Stage3

- Functional static verdict: the fail-only hardening tranche materially improved runtime routing safety
- Remaining risk center: proof still pending, plus residual heuristic pressure outside the new regenerate-only lane
- Doc verdict: partially stale because the latest regenerate-only hardening and visibility propagation are not reflected

### Stage4

- Functional static verdict: no new P0/P1 reopened; raw evidence and auditability substrate are materially stronger
- Remaining risk center: owner pressure and proof-pending closure
- Doc verdict: repair and owner-surface docs understate the amount of landed raw-evidence / operator-summary work and the current recount

## 4. Doc Validity Verdict

### Still broadly valid

- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
  - opening-state intake plus capital-boundary filtering wording still matches live code closely enough

### Needs refresh

- `docs/2026-04-01/active-temp-execution-roadmap.md`
  - Stage2 residual wording is stale
  - Stage4 owner-surface recount is stale
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
  - parent-lane residual description is stale against current code
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
  - advisory-heavy / weak-binding framing is stale after the regenerate-only tranche
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
  - raw-evidence / operator-summary substrate is not reflected
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
  - owner recount is stale
- `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
  - Stage4-first feedback-routing tranche is now landed and should no longer read as the next unopened slice

## 5. Recommended Next Order

1. refresh the stale Stage2 / Stage3 / Stage4 execution docs and the active roadmap first
2. keep `docs/temp/` mirrors and `queue-state.json` aligned with those canonical edits
3. only after that, run the bounded fresh proof wave
4. defer new structure-first coding until the post-run merge audit says which `P3` item actually survived

## 6. Pass 1 Audit

- document type matches the request: yes, this is a survey-only system-track document
- scope is explicit: yes, Stage2 + Stage3 + Stage4 static code plus execution-doc validity
- included vs excluded surfaces are explicit enough: yes

## 7. Pass 2 Audit

- findings are bounded to inspected live code, AST recounts, and current canonical docs
- no runtime-positive claims were upgraded without a fresh rerun
- severity claims were trimmed to `P2 doc drift` and `P3 structure pressure`; no unsupported new `P1` was asserted

## 8. Pass 3 Audit

- the document is actionable:
  - refresh stale docs
  - then run proof
  - then decide whether any structure lane should reopen
- queue and roadmap consequence is explicit
- overreach is trimmed: no closure claims without fresh proof

## 9. Confidence

- Estimated confidence: `96%`
- Rationale:
  - live code and live docs were read directly
  - structural counts were recomputed from the current workspace
  - no runtime claims were promoted beyond static authority
