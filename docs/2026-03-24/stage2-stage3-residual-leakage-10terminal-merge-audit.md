# Stage2 -> Stage3 Residual Leakage 10-Terminal Merge Audit

Date: 2026-03-24
Status: final
Canonical Path: `docs/2026-03-24/stage2-stage3-residual-leakage-10terminal-merge-audit.md`
Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
Baseline Dirty Summary: dirty workspace; active temp queue empty at audit start; many unrelated modified/deleted runtime, doc, test, and project artifact files already present
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
- `docs/2026-03-24/opus-residual/t1-live-run-chronology.md`
- `docs/2026-03-24/opus-residual/t2-stage2-arc-payload.md`
- `docs/2026-03-24/opus-residual/t3-stage2-validation-guardrails.md`
- `docs/2026-03-24/opus-residual/t4-current-episode-extraction.md`
- `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals.md`
- `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection.md`
- `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario.md`
- `docs/2026-03-24/opus-residual/t8-stage4-contradiction-detection.md`
- `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace.md`
- `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger.md`
Evidence Artifacts:
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`
- `projects/00_001/logs/episode_production.jsonl`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/stage4_interview_round.py`
Side-Effect Coverage:
- Stage 3 constraint assembly and prompt injection
- blueprint live prompt formatting
- downstream Stage 4 contradiction detection status
- no DB/schema/persistence contract change in scope

## 1. Scope

Merge-audit the 10 terminal residual-leakage resurvey after the fresh `00_001` rerun, discard stale claims, and isolate the smallest next execution surface that targets the remaining culprit rather than reopening density/refactor waves.

## 2. Merged Conclusion

The 10 lanes converge on one dominant residual culprit:

1. `semantic_carryover` is still entering the Stage 3 blueprint prompt as an unscoped arc-global positive signal.
2. Inside that surface, `continuity_checkpoints` is the loudest field. `growth_justification` is a secondary positive-signal leak. `foreshadow_anchors` is a weaker amplifier.
3. A separate action-bearing residual remains in `_extract_immutable_fact_carryover()`, which still reads `state_changes` without the Wave 1 episode boundary and can contaminate ep2+.
4. A defense-in-depth gap remains in `blueprint_ensemble._format_constraints()`: it renders only `stop_line["content"]` and ignores `future_eps`, so the live prompt under-represents the already-computed all-future prohibition.

Merged confidence: 96%.

## 3. Accepted Findings

### P0. Residual prime culprit

Accepted as primary:

- `modules/domain/agents/blueprint_constraint_compiler.py`
- `semantic_carryover`
- especially `continuity_checkpoints`

Why accepted:

- T2 and T10 independently rank this as the dominant remaining seam.
- Live code still normalizes and renders `semantic_carryover` with no episode awareness.
- Fresh-run ep1 blueprint still ends in ep3/ep4 completion state, matching the same arc-end checkpoint language.

### P1. Action-bearing secondary residual

Accepted as secondary but real:

- `_extract_immutable_fact_carryover()` in `modules/domain/agents/blueprint_constraint_compiler.py`

Why accepted:

- T5 correctly shows this bypasses the Wave 1 `_within_ep()` filter.
- It is inactive for ep1, but active for ep2+ and can reinforce replay/continuity contamination downstream.

### P1. Defense-in-depth contract gap

Accepted as bounded prompt-contract mismatch:

- `modules/domain/agents/blueprint_ensemble.py:_format_constraints()`

Why accepted:

- T9 shows the compiler already computes `future_eps`, but the live prompt formatter only prints the next-episode stop line.
- This is not the primary source of ep1 overconsumption, but it weakens the active defense surface and should travel with the same wave.

## 4. Cleared Or Deferred Claims

Cleared as non-primary for this wave:

- T3 `stage2_validation_pipeline.py` / Stage 2 ep_count split
- T4 current-episode extraction / `must_focus`
- T7 blueprint synthesis as downstream propagation rather than source
- T8 Stage 4 contradiction detection

Deferred as amplifier-only, not culprit-first:

- T6 `genre_ext` treatment injection

Observed but not promoted:

- `modules/core/stage4_interview_round.py:_prepend_arc_first_location_note()` is the only concrete first-episode special handling found in live code. It is a Stage 4 location continuity note, not a credible root cause for Stage 3 ep1 overconsumption.

## 5. Live Cross-Checks

The merged conclusion matches live code and artifacts:

- `modules/domain/agents/blueprint_constraint_compiler.py:93` still loads `semantic_carryover` without episode filtering.
- `modules/domain/agents/blueprint_constraint_compiler.py:126-129` still places semantic carryover ahead of the main constraint block.
- `modules/domain/agents/blueprint_constraint_compiler.py:672-686` still preserves `growth_justification`, `foreshadow_anchors`, and `continuity_checkpoints` with no episode scoping.
- `modules/domain/agents/blueprint_constraint_compiler.py:704-716` still renders those fields as affirmative prompt lines.
- `modules/domain/agents/blueprint_constraint_compiler.py:507-542` still extracts immutable fact carryover from arc-wide `state_changes` for ep2+.
- `modules/domain/agents/blueprint_ensemble.py:944-967` still renders semantic carryover into the live prompt.
- `modules/domain/agents/blueprint_ensemble.py:866-867` still prints only the next-episode stop line, not `future_eps`.
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json:26` still records ep1 ending state as already having capital and corporation completion.
- `projects/00_001/logs/episode_production.jsonl:5-10` still shows ep3/ep4 continuity-firewall replay triggered by ep1 overconsumption.

## 6. Recommended Next Scope

Promote a single bounded execution SSOT with exactly three tranches:

1. `semantic_carryover` boundary hardening in `blueprint_constraint_compiler.py`
2. `_extract_immutable_fact_carryover()` episode filtering in `blueprint_constraint_compiler.py`
3. `future_eps` stop-line render parity in `blueprint_ensemble.py`

Do not widen the next wave into:

- Stage 2 density or allocation redesign
- `final ep_count judgment` ownership changes
- `genre_ext` quarantine
- Stage 4/Director policy changes
- first-episode special-rule redesign

## 7. Operating Consequence

The next action is no longer survey-first. Confidence is high enough to open one compact execution wave aimed at the residual Stage 3 prompt-boundary seams above.
