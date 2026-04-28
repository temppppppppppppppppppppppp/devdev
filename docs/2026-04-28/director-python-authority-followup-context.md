# Director-Python Authority Follow-Up Context

Date: 2026-04-28
Status: follow-up context for post-PR #115 work
Track: system
Baseline Branch: `codex/person-fact-lock-director-advisory`
Target Base After Merge: `main`
Related PR: `#115`
Related Issue: `#57`

## 1. Purpose

This document preserves the handoff context for the next wave after PR #115.

PR #115 is a narrow authority-correction patch. It fixes the observed Stage 3 `fact_lock_person` hard-binding loop, but it does not finish the broader Director/Python authority redesign.

The next wave should start from updated `main` on a new branch, likely:

```powershell
git checkout main
git fetch origin
git pull --ff-only origin main
git checkout -b codex/director-python-authority-contract
```

## 2. What PR #115 Does

PR #115 changes the person fact-lock lane only.

- `fact_lock_person` remains collectible diagnostic evidence.
- `fact_lock_person` no longer belongs to hard binding prevalidation categories.
- `fact_lock_person` no longer belongs to Stage 3 regenerate-only binding categories.
- Generic Korean role phrases such as `국가 대표`, `법인 대표`, and related representative phrases are filtered before becoming person anchors.
- The Frontier Lag SSOT and active roadmap now record that this is a narrow merge candidate, not #57 closure.

This aligns the observed failure with the workspace invariant:

- Python collects evidence.
- Director adjudicates semantic/canon meaning.
- Python regex/heuristics must not silently become the semantic judge.

## 3. What PR #115 Does Not Finish

The broader authority problem remains open.

Known remaining runtime authority surfaces:

- `modules/domain/agents/unified_blueprint_validator.py`
  - `_apply_binding_prevalidation_contract` can still route Director `PASS` / `PASS_WITH_WARNING` into `PASS_WITH_FIX` for other binding categories.
  - This currently carries explicit layer metadata such as `final_judgment_authority=director_llm` and `runtime_gate_authority=python_runtime_routing_gate`, but the visible verdict/routing surface can still be confusing.
- `modules/domain/agents/three_phase_blueprint_runtime.py`
  - unresolved binding issues can block emergency fallback artifact adoption.
  - this is represented as runtime/objective blocking, but the compatibility `final_verdict` surface still exists.
- `modules/domain/agents/stage3_validation_boundary.py`
  - quality/runtime gates can still affect Stage 3 routing after a Director-like result.
- Stage 4 runtime surfaces
  - PASS_WITH_FIX contract checks, post-select conflict handling, quality floor checks, and retry loop guards still act as runtime gates.

These surfaces may be legitimate process guards, but the next wave must classify them explicitly. The key is not to delete all runtime gates. The key is to stop Python semantic heuristics or regex from presenting themselves as Director judgment.

## 4. Proposed Authority Taxonomy

Use this taxonomy as the first design target.

### Evidence Only

Python may collect, normalize, hash, count, diff, and package evidence.

Examples:

- regex-detected possible person drift
- possible role/name mismatch
- scene density warning
- suspicious opening anchor
- continuity canary finding awaiting Director review

Expected route:

- store as `evidence_packet_v1`
- surface to Director as a question
- do not force regenerate by itself

### Director Required

Semantic/canon questions must be adjudicated by Director.

Examples:

- whether `박성호 PB` is a wrong person or a valid concrete name for `경고하는 PB`
- whether a representative phrase is a person, role label, institution, or generic descriptor
- whether a timeline transition is acceptable narrative compression
- whether a location phrase is a hard continuity violation or acceptable scene movement

Expected route:

- Director returns confirmed violation, false positive, repair needed, or insufficient evidence.
- runtime follows Director-labeled outcome.

### Runtime Route Guard

Python may block automatic progress when the issue is process/transport/contract level, not semantic authorship.

Examples:

- malformed required schema
- missing Director verdict
- failed persistence of an accepted authority artifact
- invalid UTF-8 in touched source/output boundary
- missing required artifact file after a claimed success
- explicit unresolved structural contract that has already been Director-confirmed or contract-confirmed

Expected route:

- preserve `director_verdict`
- set separate `runtime_route_verdict`, `runtime_route_action`, `runtime_route_reason`, `runtime_gate_authority`
- avoid presenting runtime block as Director rejection

### Absolute Invariant

Only a small set should remain hard fail-closed without semantic scoring.

Examples:

- deceased NPC active action/dialogue in present-time scene, unless explicitly framed as memory/mention/past scene
- artifact adoption without durable persistence evidence
- broken schema/transport state that makes Director result unavailable or unverifiable

Even here, Python should say `runtime cannot safely progress`, not `story is bad`.

## 5. Suggested Contract Shape

Introduce or consolidate an evidence packet shape similar to:

```json
{
  "schema_version": "evidence-packet-v1",
  "source_stage": "stage3",
  "source_component": "python_prevalidation",
  "authority_level": "evidence_only",
  "decision_boundary": "director_verdict_required",
  "category": "fact_lock_person",
  "severity": "MAJOR",
  "subject": {
    "type": "person_or_role",
    "name": "경고하는 PB"
  },
  "expected": "경고하는 PB",
  "observed": "박성호 PB",
  "evidence": [],
  "director_question": "Is this a true person/canon violation or an acceptable concrete role realization?",
  "must_not_auto_apply": true
}
```

Director response should be a separate verdict packet:

```json
{
  "schema_version": "director-evidence-adjudication-v1",
  "director_verdict": "PASS_WITH_FIX",
  "evidence_verdict": "CONFIRMED_VIOLATION",
  "dismissed_evidence": [],
  "confirmed_evidence": [],
  "repair_scope": "inplace",
  "runtime_route": "allow_repair",
  "final_judgment_authority": "director_llm"
}
```

## 6. Recommended Next Work Order

1. Survey all current Python runtime gates that can affect Director PASS-like output.
2. Classify each gate as `evidence_only`, `director_required`, `runtime_route_guard`, or `absolute_invariant`.
3. Patch Stage 3 first:
   - keep Director verdict immutable
   - route semantic regex/heuristic categories through evidence packets
   - preserve process guards as route-layer metadata
4. Add tests proving semantic evidence cannot force regenerate until Director adjudicates it.
5. Patch Stage 4 with the same taxonomy after Stage 3 is stable.
6. Only then run another bounded frontier proof with explicit runtime/token/cost caps.

Do not start with a new expensive proof run. Merge PR #115 first, then continue the authority contract work from `main`.

## 7. Validation Status At Handoff

PR #115 local validation:

- `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/unified_blueprint_validator.py modules/domain/agents/three_phase_blueprint_runtime.py` -> passed
- `python -m pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q` -> 58 passed
- `python -m pytest tests/test_stage23_stage4_readiness_wave1.py -k "binding or fact_lock" -q` -> 3 passed, 8 deselected
- `python -m pytest tests/test_blueprint_patch_mode.py -k "binding_prevalidation or candidate_disqualified" -q` -> 8 passed, 90 deselected
- `python -m pytest tests/test_unified_blueprint_validator_lane_c.py -k "binding_prevalidation or fact_lock" -q` -> 1 passed, 59 deselected
- `python -m pytest tests/test_stage3_orchestrator_handle_success_lane_c.py -q` -> 4 passed
- `python scripts/check_utf8_hygiene.py <touched code/test/docs>` -> passed
- `git diff --check main...HEAD` -> passed
- `python scripts/ops_validator.py --strict` -> passed

GitHub Actions status:

- GitHub Actions did not run real steps because account billing/spending limit prevented job startup.
- Treat local/internal validation as the merge evidence for PR #115.

## 8. 3-Pass Document Audit

Pass 1 - scope:

- PASS. This document is a follow-up handoff, not an execution completion claim.
- PASS. It clearly separates PR #115 narrow closure from the broader authority redesign.

Pass 2 - evidence and consistency:

- PASS. The remaining risk surfaces match current code inspection: binding prevalidation, emergency fallback blocking, Stage 3 quality/runtime gates, and Stage 4 contract/post-select gates.
- PASS. The document preserves the rule that Python may collect evidence but Director owns semantic/canon judgment.

Pass 3 - next-step readiness:

- PASS. The recommended next step is a new branch from updated `main`, not another live proof run.
- PASS. The next work order is bounded: survey/classify, then patch Stage 3, then Stage 4.

Estimated confidence: 96%.
