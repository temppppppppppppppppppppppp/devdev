# BP Clarity / Density 4-Terminal Merge Audit

Date: 2026-03-25
Status: final
Document Type: merge audit
Canonical Path: `docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: canary_0325 live artifacts/logs, prior closed Stage3 docs, 2026-03-25 survey docs, temp queue empty at merge start`
Source Survey Docs:
- `docs/2026-03-25/opus-bp-clarity-density/t1-stage2-upstream-specificity.md`
- `docs/2026-03-25/opus-bp-clarity-density/t2-stage3-authority-schema.md`
- `docs/2026-03-25/opus-bp-clarity-density/t3-stage3-prevalidation-coverage.md`
- `docs/2026-03-25/opus-bp-clarity-density/t4-bounded-improvement-option-ledger.md`
Evidence Artifacts:
- `projects/canary_0325/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/canary_0325/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__action_focused.json`
- `projects/canary_0325/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json`
- `config/prompts/ensemble.yaml`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
Side-Effect Coverage:
- Stage 3 prompt authority presentation
- Stage 3 Python prevalidation and quality-risk surfacing
- Stage 3 candidate qualification and Director-facing advisory payload
- no Stage 2 schema change, no Stage 4 redesign, no DB/JSONL schema change in the recommended wave

## 1. Scope

This merge audit synthesizes the blueprint clarity/density structural survey only.

It answers one question:

What is the highest-ROI bounded next wave for blueprint clarity and density, given that the old Stage 3 culprit family now appears suppressed in the partial canary?

## 2. Converged Findings

### Finding A. The biggest remaining limiter is in Stage 3, not Stage 2

The lanes do not support "upstream sparsity is the only real problem."

What they do support:

- Stage 2 `tactical_doc` is already rich enough to generate stronger blueprints
- Stage 2 `episode_details` being optional is a real weakness, but it is not the highest-ROI next wave
- clarity loss currently happens mainly when Stage 3 flattens authority and cannot diagnose thin/vague content

Merge judgment:

- Stage 2 upstream specificity is a deferred structural lane
- Stage 3 remains the immediate quality-up surface

### Finding B. Authority presentation is a real Stage 3 limiter

The authority/schema lane establishes that the system already has multiple authority bands, but the prompt presents too many surfaces as visually coequal.

This matters because:

- hard constraints and advisory guidance share the same visual band
- the LLM must infer override rules that the system already "knows" implicitly
- degraded paths can duplicate `must_focus.content` across tactical and constraint surfaces

Merge judgment:

- explicit authority re-banding is action-bearing and bounded
- this is not cosmetic wording cleanup; it is a real Stage 3 quality limiter

### Finding C. Python prevalidation has a high-impact density blind spot

The prevalidation lane shows a clear gap:

- current checks catch structural absence and factual contradictions
- current checks do not measure scene specificity or scenario density in a meaningful way
- quality-risk remains too generic to distinguish "thin blueprint" from "wrong blueprint"

Merge judgment:

- a bounded density/specificity prevalidation expansion is action-bearing
- this belongs in the next wave

### Finding D. Prompt-level self-audit is useful, but secondary

The option-ledger lane is directionally right that self-audit can help.

However, across all four lanes:

- self-audit is an amplifier, not the dominant limiter
- it is harder to attribute cleanly in the next canary if bundled immediately with the primary fixes
- the current operating preference has been to keep single-culprit interpretation as sharp as possible

Merge judgment:

- self-audit should be deferred behind the more primary Stage 3 fixes
- it remains a good follow-up prompt wave if clarity/density still lags after the bounded Stage 3 wave

## 3. Cleared Or Deferred Items

Cleared from immediate Wave 1:

- Stage 2 upstream specificity floor as the next active wave
- schema-tightening-first strategy
- scene-level Director retry feedback as the first move
- a large mixed Stage 2 + Stage 3 bundle

Deferred but still credible:

- Stage 2 `episode_details` specificity floor
- prompt-level self-audit instruction
- scene-level Director retry feedback

## 4. Recommended Execution Shape

The best bounded next wave is:

1. explicit Stage 3 authority re-banding in the blueprint prompt / constraint formatting
2. bounded Stage 3 density/specificity prevalidation checks

Explicitly not in Wave 1:

- Stage 2 schema/prompt redesign
- self-audit prompt rollout
- Director retry-feedback redesign

Reason for trimming the option-ledger's `B + C + A` bundle to `B + C`:

- `B` and `C` are the primary limiters supported across all lanes
- `A` is an acknowledged secondary amplifier
- keeping `A` out preserves cleaner canary attribution and fits the current single-culprit-first operating rule

## 5. Recommended Action

Open one bounded execution SSOT for:

- Stage 3 authority re-banding
- Stage 3 scene-specificity and scenario-density prevalidation

Treat self-audit as a later prompt wave, not part of this one.

## 6. Confidence

Estimated confidence: 95%

Why this clears the gate:

- all four lanes converge on the same primary Stage 3 quality-up surface
- the partial canary removes pressure to keep chasing the old residual bug family
- the recommended wave is narrower than the broadest lane proposal, not broader

## 7. Final Decision

- Dominant current limiter: `Stage 3 authority mixing + Stage 3 density validation blind spot`
- Best bounded next wave: `authority re-banding + density prevalidation`
- Should this merge open an execution SSOT now: `yes`
