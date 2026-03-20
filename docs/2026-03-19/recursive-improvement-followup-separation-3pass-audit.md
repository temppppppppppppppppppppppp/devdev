# recursive-improvement-followup-separation-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/recursive-improvement-followup-separation-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/stage2-arc-patch-observability-signals-3pass-audit.md`
- `docs/2026-03-19/stage2-local-patch-hard-guards-semantics-3pass-audit.md`
Evidence Basis:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `tests/test_stage2_finalizer.py`
Scope:
- separate the recursive-improvement follow-up from current Stage 2 Arc patch observability work
- define why this item is deferred
- record the likely future handoff path without treating it as an active patch item now
- non-goal: implement recursive improvement wiring in this document

---

## Pass 1. Structure and Scope

This document is a separation note, not an execution order.

Current Stage 2 work already completed:
- narrow Arc patch observability signals
- advisory flag persistence
- `audit_event` emission
- Director re-audit warning context

What is *not* included in that completed work:
- feeding those signals back into the next retry prompt
- using those signals to adapt local patch strategy automatically
- building a stage-level recursive-improvement loop

Key operator question:
- should `Stage2` Arc patch signals now be pushed into retry handoff and next-attempt prompting, or should that be treated as a later system-design item?

---

## Pass 2. Evidence and Consistency

### 1. Current work stops at observability on purpose

Live behavior now records Stage 2 Arc patch signals in:
- `audit["patch_guard_signals"]`
- `advisory_flags`
- `audit_event`
- Director re-audit `story_context`

This is enough for post-hoc review.
It is not yet a recursive-improvement loop.

Conclusion:
- the current patch is deliberately bounded
- recursive improvement was not silently half-implemented

### 2. Recursive improvement would require a different handoff boundary

To become real retry-time improvement, the signal bundle would need to cross at least these boundaries:
- `Stage2Finalizer` result shaping
- `Stage2Orchestrator` `previous_attempt` handoff
- `Stage2Preflight` next local patch / regenerate prompt consumption

That means the feature would stop being “observability only” and become:
- retry policy
- prompt-shaping policy
- possibly dashboard or sink-alignment work

Conclusion:
- this is materially larger than the just-completed Stage 2 observability patch

### 3. Deferring it is the lower-risk choice

Reasons to defer:
- current observability surface should accumulate evidence first
- recursive handoff could amplify noisy signals if introduced too early
- it crosses multiple modules and would no longer be a compact Stage 2 finalizer patch

Conclusion:
- separating this item now improves clarity
- it reduces the chance of mixing “evidence collection” with “automatic policy adaptation”

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. Recursive improvement is a valid future direction.

2. It should not be treated as part of the current Stage 2 Arc patch observability change.

3. As of `2026-03-19`, it is a deferred follow-up item.

### Deferred item definition

Future recursive-improvement follow-up would likely mean:
- carry `patch_guard_signals` through `previous_attempt`
- surface compact signal bundle into next retry / patch prompt
- decide whether any signal changes strategy, scope, or repair lane

None of that is active yet.

### Safe operating rule from this note

Do:
- keep current Stage 2 Arc patch signal work scoped to observability
- revisit recursive improvement only after signal quality is observed in practice
- treat this as a later system-design item, not an immediate bugfix

Do not:
- describe current Stage 2 observability as if recursive improvement is already active
- silently route new signals into retry prompts without a separate policy decision
- merge this item back into the current hard-guard/advisory docs

### Recommended next actions

1. Leave the current implementation as-is.
2. Revisit this item only after live evidence shows which signals are stable and useful.
3. When revisited, write a separate execution note for:
   - `Stage2Finalizer -> Stage2Orchestrator -> Stage2Preflight` handoff
   - retry prompt payload shape
   - signal-to-policy mapping rules

### Audit result

- runtime code change: not part of this note
- regression hardening: not part of this note
- documentation conclusion: recursive improvement is intentionally separated and deferred as of `2026-03-19`
