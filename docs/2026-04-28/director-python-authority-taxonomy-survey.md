# Director-Python Authority Taxonomy Survey

Date: 2026-04-28
Track: system
Status: survey-complete, pre-implementation
Canonical Path: `docs/2026-04-28/director-python-authority-taxonomy-survey.md`
Related Context:
- `docs/2026-04-28/director-python-authority-followup-context.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md`
- `docs/2026-04-27/security-and-frontier-active-execution-roadmap.md`
Commit State:
- Baseline Commit: `3632369f556d60867da90705ef5e653c258f9d20`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Evidence Inputs:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- local code inspection on the Stage3/Stage4 files named below
- GitHub PR `#115`
- GitHub issue `#57`

## 1. Purpose

This document freezes the current authority-contract survey before the next implementation wave.

PR `#115` fixed the narrow `fact_lock_person` hard-binding loop. It did not finish the broader redesign. The remaining work is to stop Python runtime heuristics, regex, and repair-contract routing from presenting themselves as if they were Director judgment.

This is a read-only survey. No CI, no live proof run, no GCP/Vertex/LLM run, and no code patch were performed in this wave.

## 2. Current-State Drift Note

Two operator-visible state drifts now exist and should be treated explicitly:

1. `main` is no longer at the PR `#115` merge commit.
   - PR `#115` merged at `767cd1b7`.
   - Current `main` during this survey is `3632369f`.
   - If a future implementation wave wants the exact PR `#115` base, it must branch from `767cd1b7` explicitly instead of using current `main` HEAD.
2. GitHub issue `#57` no longer matches the pre-merge doc intent.
   - The pre-merge and merge-time intent was to keep `#57` open.
   - GitHub now shows `#57` as auto-closed by PR `#115` at `2026-04-28T09:44:27Z`.
   - That closure must not be read as full Frontier Lag proof completion or as completion of the authority-contract redesign.

## 3. Executive Verdict

The repo already has partial layer separation fields such as `director_verdict`, `runtime_route_verdict`, `final_judgment_authority`, and `runtime_gate_authority`.

The remaining problem is not lack of vocabulary. The remaining problem is that several Stage3 and Stage4 flows still mutate compatibility verdict fields directly:

- semantic-looking Python prevalidation findings still widen or rewrite PASS-like results
- quality floor and repair-contract gates still convert Director PASS-like results into runtime REJECT surfaces
- some post-select and strong-advisory routes still collapse semantic and runtime authority into the same visible verdict field

The first implementation wave should therefore be Stage3-first and narrow:

- keep `director_verdict` immutable
- convert semantic Python findings into evidence-only or Director-required packets
- keep true process guards as runtime-route-only guards
- stop using compatibility `final_verdict` as the internal source of truth for route decisions

## 4. Taxonomy

### `evidence_only`

Python may collect, normalize, count, diff, hash, package, and persist evidence.

It may not force regenerate or reject from semantic suspicion alone.

### `director_required`

If the question is semantic, canon, narrative, or interpretation-heavy, Director must adjudicate it.

### `runtime_route_guard`

Python may block automatic progress when the problem is contract, process, persistence, or route safety.

The block must preserve the Director layer and speak as route metadata, not as a replacement verdict.

### `absolute_invariant`

Only true fail-closed safety boundaries belong here.

Examples:

- accepted authority artifact cannot be durably persisted
- schema or transport state is broken enough that authority cannot be verified
- a real present-time dead-character active-role invariant if the detector is already treated as canonical rule enforcement rather than semantic style advice

## 5. Survey Matrix

| Surface | Current Behavior | Taxonomy | First Patch Direction |
| --- | --- | --- | --- |
| `modules/domain/agents/unified_blueprint_validator.py:880-944` | `_apply_binding_prevalidation_contract` rewrites `PASS` / `PASS_WITH_WARNING` into `PASS_WITH_FIX` | `runtime_route_guard` for true structural guards only | keep Director verdict unchanged; emit route payload only |
| `modules/domain/agents/unified_blueprint_validator.py:63-88` | `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` still hard-binds many semantic categories | mixed; currently over-broad | split categories into semantic vs route-only |
| `modules/domain/agents/unified_blueprint_validator.py:2485-2517` | `fact_lock_person` is still emitted as CRITICAL evidence | `director_required` | keep as evidence packet; do not re-promote into hard route |
| `modules/domain/agents/unified_blueprint_validator.py:3817-3858` | tactical intrusion is treated as CRITICAL structural violation | likely `director_required` unless separately narrowed to objective rule breach | stop direct route implication until adjudicated |
| `modules/domain/agents/unified_blueprint_validator.py:633-661` | dead NPC check is marked advisory-only in helper comment, but the category still belongs to hard binding set | currently self-contradictory | decide whether this is true `absolute_invariant` or Director-required evidence |
| `modules/domain/agents/stage3_validation_boundary.py:261-275` | quality gate turns `PASS` into `REJECT` | `runtime_route_guard` | preserve Director PASS and emit route-layer reject/block |
| `modules/domain/agents/stage3_validation_boundary.py:295-371` | terminal low-score PASS is promoted to `PASS_WITH_WARNING` with explicit route metadata | `runtime_route_guard` | mostly correct direction; reduce reliance on compatibility verdict mutation |
| `modules/domain/agents/three_phase_blueprint_runtime.py:319-342` | unresolved binding issues force full regenerate before local patch loop | `runtime_route_guard` | consume typed route categories instead of broad binding count |
| `modules/domain/agents/three_phase_blueprint_runtime.py:3186-3245` | emergency fallback is blocked and `final_verdict` becomes `FAILED` | `runtime_route_guard` | keep objective blocked, not compatibility verdict rewrite |
| `modules/domain/agents/three_phase_blueprint_runtime.py:3297-3387` | `PASS_WITH_FIX` can be rerouted to full regenerate when binding categories persist | `runtime_route_guard` | trigger from typed route payload, not from semantic category bundle |
| `modules/domain/agents/three_phase_blueprint_runtime.py:3403-3463` | actionless or low-yield advisory residuals become `PASS_WITH_WARNING` | borderline compatibility shim | acceptable as route annotation, but should not be the authority source |
| `modules/core/stage4_postselect_runtime.py:487-533` | post-select continuity/history conflicts directly convert result to `REJECT` | mostly `director_required`, currently expressed as route+verdict collapse | keep conflict artifact and route block separate from Director layer |
| `modules/core/stage4_interview_round.py:6300-6315` | Stage4 quality floor turns `PASS` into `REJECT` | `runtime_route_guard` | preserve Director PASS, annotate route rejection |
| `modules/core/stage4_interview_round.py:3752-3804` | invalid PASS_WITH_FIX local repair contract is downgraded to `REJECT` | `runtime_route_guard` | preserve Director verdict and expose runtime contract failure separately |
| `modules/core/stage4_interview_round.py:3927-4063` | invalid fix scope or strong advisory escalation can convert `PASS_WITH_FIX` to `REJECT` | mixed; advisory-triggered lane is over-broad | do not let advisory-origin signals present as Director rejection |
| `modules/core/stage4_retry_runtime.py:621-671` | empty feedback or invalid PASS_WITH_FIX contract aborts repair loop into reject route | `runtime_route_guard` | keep as route failure, not Director rewrite |
| `modules/core/stage4_retry_runtime.py:1058-1073` | patch re-audit PASS below quality floor is routed to `REJECT` | `runtime_route_guard` | preserve Director PASS and set runtime route block |
| `modules/core/stage4_retry_runtime.py:1193-1204` | exhausted PASS_WITH_FIX loop finalizes as `REJECT` | `runtime_route_guard` | preserve Director origin; mark repair loop exhaustion separately |
| `modules/core/stage4_interview_round.py:76-80,8949-8997` | accepted Stage4 authority must persist to DB or fail closed | `absolute_invariant` | keep fail-closed |

## 6. Stage3-First Patch Plan

### Step 1. Split prevalidation categories by authority

The current Stage3 hard-binding basket is too broad.

The first split should be:

- keep route-only categories in the structural route lane
- move semantic or interpretation-heavy categories to Director adjudication
- keep advisory-only categories fully out of hard route evaluation

Proposed Stage3-first classification:

- `evidence_only`
  - relationship visibility
  - anchor density
  - scene density and similar explicitly advisory findings
- `director_required`
  - `fact_lock_item`
  - `fact_lock_location`
  - `fact_lock_provenance`
  - `fact_lock_institution`
  - `fact_lock_person`
  - `arc_compliance`
  - `arc_timeline`
  - `opening_anchor`
  - `mission_clarity`
  - `timeline_specificity`
  - `protagonist_state`
  - `work_identity_opening`
  - `tactical_semantic_fidelity`
- `runtime_route_guard`
  - explicit repair-contract missing
  - local patch contract invalid
  - quality floor block
  - artifact adoption block after Director-like result
  - schema incompatibility
- `absolute_invariant`
  - durable authority persistence missing
  - transport/schema state that makes authority unverifiable
  - dead-NPC present-time active-role only if the detector is intentionally promoted as canonical invariant rather than semantic suspicion

### Step 2. Stop verdict rewrite in Stage3 validator

Primary seam:

- `modules/domain/agents/unified_blueprint_validator.py`

Target:

- `_apply_binding_prevalidation_contract` should no longer return a rewritten verdict for semantic categories
- instead it should emit route payloads only for the categories that truly belong in `runtime_route_guard` or `absolute_invariant`

### Step 3. Make runtime consume route payloads, not compatibility verdicts

Primary seams:

- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/stage3_validation_boundary.py`

Target:

- consume typed route metadata for regenerate/block/retry
- treat compatibility `final_verdict` as boundary surface only
- preserve `director_verdict` as the semantic authority source

## 7. Stage4 Follow-Up Seams

Stage4 should not be patched first, but the main follow-up seams are already clear:

- `_apply_director_gate_update` in `stage4_interview_round.py` still rewrites visible verdict layers too aggressively
- `post_select_conflict` should be modeled as route-safe conflict handling rather than as a synthetic Director reject
- PASS_WITH_FIX repair-contract enforcement should preserve Director authority and report route failure separately
- strong advisory escalation should remain advisory unless explicitly promoted by typed contract, not by unlabeled heuristic convenience

The existing `advisory_authority.py` helper is useful substrate. The remaining work is to apply the same explicit authority typing to verdict-mutating branches, not only to stored advisory payloads.

## 8. Recommended Next Move

1. Branch for implementation from the intended base explicitly.
2. Patch Stage3 only.
3. Keep validation local and deterministic.
4. Merge the Stage3 authority-contract patch to `main`.
5. Re-open a Stage4 follow-up branch after Stage3 lands cleanly.

If the operator wants the exact PR `#115` base, use:

```powershell
git checkout -b codex/director-python-authority-contract 767cd1b7
```

If the operator wants current `main`, branch from current HEAD instead.

## 9. 3-Pass Document Audit

Pass 1 - scope:

- PASS. This document is a pre-implementation survey and does not claim runtime closure.
- PASS. It explicitly covers the six requested Stage3/Stage4 files and the authority taxonomy asked for in the handoff.

Pass 2 - evidence and consistency:

- PASS. All listed verdict-mutation sites were verified against current local code.
- PASS. The document records the current drift between repo docs, current `main` HEAD, and GitHub issue state.
- PASS. The proposed classification keeps semantic judgment with Director and limits Python to evidence or route layers.

Pass 3 - implementation readiness:

- PASS. The first patch seam is narrow and Stage3-first.
- PASS. No live proof, CI, or cost-bearing runtime is required before that patch wave starts.

Estimated confidence: 97%.
