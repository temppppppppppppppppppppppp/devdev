# Stage3 Generator Genre-Aware Surface Diversification Context

Date: 2026-04-17
Status: final
Canonical Path: `docs/2026-04-17/stage3-generator-genre-aware-surface-diversification-context.md`
Temp Mirror Path: `not-applicable`

Commit State:
- Baseline Commit: `ce0f3b47b465fcd67796f75e0497a5f7c7b2424f`
- Baseline Dirty Summary: `dirty: 8 tracked, 6 untracked; hotspots: blueprint_constraint_compiler.py, blueprint_ensemble.py, three_phase_blueprint_runtime.py, stage3_retry_coordinator.py, audit/context docs, canary artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Scope
- Question: should the planned long-term fix for Stage3 replay/surface-collapse be genre-aware rather than one-size-fits-all?
- Included surfaces:
  - Stage3 genre bootstrap
  - Stage3 blueprint ensemble prompt/screening behavior
  - Stage3 replay detection and retry routing
  - existing Writer/Director/genre-guard evidence showing the workspace already treats genre as a first-class concern elsewhere
- Excluded:
  - implementation patching
  - new rerun authorization
  - narrative-family router policy for material-side orders

## Evidence Basis
- Genre inventory:
  - `modules/core/constants.py`
- Stage3 runtime/bootstrap:
  - `modules/domain/agents/three_phase_blueprint_runtime.py`
- Stage3 generator:
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
- Existing genre-aware precedent:
  - `modules/domain/agents/writer.py`
  - `modules/domain/agents/director.py`
  - `modules/core/genre_guards/investment_guard.py`
- Current failure context:
  - `docs/2026-04-17/stage3-ep9-generator-longterm-direction-adversarial-3pass-audit.md`
  - `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1/logs/session_20260417_144754.log`

## Executive Verdict
Yes. The long-term Stage3 generator fix should be genre-aware.

But the correct shape is:
- `common core` for replay-collapse handling
- plus `genre adapters` for surface-family semantics

It should **not** be:
- one investment-shaped rule set applied to every genre
- or episode-specific hardcoding in Python

Recommended label: `genre-aware by design, generic at the contract layer`.

## Findings
- High: the workspace already treats genre as a first-class system concern in multiple places. Supported genres are explicit in `GenreTypes`. [constants.py](C:\Users\wjjo\Desktop\글도비\modules\core\constants.py:47)
- High: Stage3 generator currently resolves genre, but most of the replay/surface-collapse path is still effectively genre-neutral. Runtime bootstraps `genre` from bible, yet replay guidance and replay detection do not branch on genre semantics. [three_phase_blueprint_runtime.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\three_phase_blueprint_runtime.py:1278), [blueprint_constraint_compiler.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py:1054), [unified_blueprint_validator.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py:2196)
- High: `BlueprintEnsemble` currently uses genre only in narrow ways such as system-UI contamination allowance and one wuxia inherited-state field. It does not use genre to diversify candidate surface families. [blueprint_ensemble.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py:1722), [blueprint_ensemble.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py:1562)
- Medium: Writer and genre guards already demonstrate the intended architectural pattern: a common pipeline with genre-specific rule injection. Investment Writer prompt injection and InvestmentGuard finance rules are direct precedent. [writer.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\writer.py:338), [investment_guard.py](C:\Users\wjjo\Desktop\글도비\modules\core\genre_guards\investment_guard.py:613)
- Medium: Director also carries explicit genre validation enablement, so a genre-aware Stage3 fix would align with existing governance rather than invent a new principle. [director.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\director.py:80)

## Pass 1. Structure And Scope
Question attacked: is “genre-aware” even the right question, or is this just an ep9 investment-only detail?

Adversarial challenge:
- Maybe the current concern is only a local investment-episode pathology, so introducing genre-aware design would overgeneralize from one case.

Counter-evidence:
- The already-saved ep9 long-term audit concluded the structural problem is not `investment-specific authority missing`, but `replay basin / thin-structure basin` collapse in Stage3 generation.
- That collapse mechanism is general, but the meaning of “different enough surface” is not general.
- In investment fiction, `VIP룸 대치 -> 승인 라인 -> 체결/집행 -> 후속 모니터링` is a meaningful surface progression.
- In wuxia, hunter, medical, sports, or actor genres, the equivalent off-axis progression families would be different.

Pass 1 verdict:
- Genre-awareness is the right scope question.
- The failure mechanism is cross-genre, but the correct diversification targets are genre-specific.

## Pass 2. Evidence And Consistency
Question attacked: does current code already have enough genre-aware behavior here, making new genre adapters unnecessary?

Adversarial challenge:
- Maybe genre is already threaded deeply enough through Stage3 that extra genre-aware design would duplicate existing behavior.

What the code actually shows:
- Stage3 runtime loads genre from the bible and carries it forward. [three_phase_blueprint_runtime.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\three_phase_blueprint_runtime.py:1282)
- `BlueprintEnsemble` resolves genre and passes it around. [blueprint_ensemble.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py:443), [blueprint_ensemble.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py:466)
- But the actual replay-collapse logic is still generic text:
  - “start anchor short”
  - “open institution line”
  - “move to approval / execution / aftermath”
  These are useful for the current investment lane, but they are not a general genre model. [blueprint_constraint_compiler.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py:1262)
- The replay detector itself looks only at location and character overlap, without genre-specific family semantics. [unified_blueprint_validator.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py:2273)
- The strongest currently visible genre-specific behavior in `BlueprintEnsemble` is:
  - allow explicit system UI only for hunter/fantasy
  - include inherited internal-energy continuity only for wuxia
  This is much narrower than genre-aware surface diversification. [blueprint_ensemble.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py:1722), [blueprint_ensemble.py](C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py:1562)

Pass 2 verdict:
- Current Stage3 generator is genre-threaded but not genre-shaped.
- Therefore a genre-aware long-term fix is not duplication; it fills a real gap.

## Pass 3. Execution And Readability
Question attacked: if we make this genre-aware, what shape avoids overfitting and hotfile bloat?

Adversarial challenge:
- “Genre-aware” can easily become a mess of `if genre == ...` branches, episode heuristics, and hidden authorial hardcoding.

Healthy shape:
- Keep a common Stage3 replay-collapse substrate:
  - candidate diversification contract
  - retry basin classification
  - replay-family contract structure
- Add genre adapters only for:
  - what counts as a meaningful `surface family`
  - what counts as an `off-axis progression lane`
  - which kinds of procedural/institutional/physical/emotional progression families should be explored before repeating the same surface

Unhealthy shape:
- hardcode per-episode routes like `ep9 must use branch manager room`
- scatter large `if genre == ...` blocks into already-large owners
- weaken replay validation globally just because one genre has narrow-handoff episodes

Implementation implication:
- prefer a small genre-profile provider or adapter layer over piling more rules into:
  - `blueprint_constraint_compiler.py`
  - `blueprint_ensemble.py`
  - `unified_blueprint_validator.py`
- use the existing workspace precedent:
  - common pipeline
  - genre-specific rule payload injection

Pass 3 verdict:
- The idea should move forward only as `common substrate + genre adapters`.
- A flat one-rule-fits-all policy would be incorrect.

## Recommended Framing For The Next Wave
Do this:
1. define a generic Stage3 diversification contract
2. define genre-specific surface-family adapters
3. let workers diversify against those genre-family lanes
4. let retry feedback mention the failed basin in genre-appropriate terms
5. refine replay validation with genre-family semantics only after generation improves

Do not do this:
- port the current investment-shaped `approval/execution/aftermath` wording directly into every genre
- patch `BlueprintEnsemble` with large inline per-genre trees
- treat current ep9 investment evidence as permission to author genre story logic inside Python

## Working Interpretation
The right mental model is:

- `common problem`: candidates collapse into the same basin
- `genre-specific answer`: what counts as a meaningfully different basin depends on genre

Illustrative examples below are inference, not current code truth:
- investment:
  - negotiation / approval / execution / monitoring
- wuxia:
  - confrontation / sect response / closed-door preparation / movement or aftermath
- hunter:
  - briefing / gate entry / encounter shift / system or guild consequence
- medical:
  - intake / diagnosis / procedure / ethical or institutional fallout

The point is not the exact labels above.
The point is that Stage3 needs a genre-aware vocabulary for “different enough next surface.”

## Final Judgment
The user’s instinct is correct:
- yes, this should go differently by genre

More precise version:
- the long-term fix should be generic in architecture
- and genre-specific in surface semantics

That is already consistent with how this workspace handles genre elsewhere.

## Side-Effect Coverage
- Human-facing doc only
- No code or DB mutation performed for this note
- No temp execution mirror created
- Active temp queue acknowledged but not modified

## Confidence
- Estimated confidence: 96%
- Reason:
  - current code clearly shows genre is important across the workspace
  - current Stage3 replay/diversification path is clearly under-genre-modeled
  - the remaining uncertainty is implementation design shape, not whether genre-awareness is needed
