# OPUS BE P0-P3 Remaining Screening (3-Pass Audit)

Date: 2026-03-20
Mode: system-track screening
Confidence: 0.96

## Scope

- Source OPUS doc:
  - `docs/2026-03-18/OPUS/ssot_execution/s8-0_260318-project-deepdive-execution.md`
- Live re-check targets:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/npc_drift_advisor.py`
  - `modules/core/db_manager.py`
  - `modules/core/fact_ledger.py`
  - `modules/core/world_state.py`
  - `modules/core/project_manager.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/failure_analyzer.py`

This document is a bounded screening note. It is not an execution SSOT.

## Summary

Live re-check result:

- already handled: `C1`, `C2`, `C5`, `C6`, `C7-1`, `C7-2`, `C8`, `C10`
- still-live bounded backend candidates: none
- still-live but policy-shaped: `C3`, `C4`, `C9`
- stale or reclassified, needs fresh live survey or schema work instead of direct patch: `C7-3`

Narrative TF items (`TF-S1` ... `TF-C`) are excluded from this backend screening because they are narrative-pipeline / artifact-truth items, not direct BE code candidates.

## Decision Table

| ID | OPUS label | Live status | Current judgment | Notes |
| --- | --- | --- | --- | --- |
| C1 | Arc vs Manuscript title mismatch | fixed | closed | arc title now propagates into Stage 3 constraints and prompt text |
| C2 | stop-line validation missing | fixed | closed | stop-line extraction existed already; validator is now hardened beyond weak prefix substring matching |
| C3 | Director 99 override / CRITICAL warnings weak | likely live | policy-shaped high | contradiction firewall exists, but generic python warning hard-gate is still unclear/incomplete |
| C4 | `quality_risk` discriminability = 0 | live | policy-shaped | verdict-folding exists across Director compare, validator, and Stage 3 pipeline |
| C5 | failure_analyzer AttributeError | fixed | closed | proof-digest DB facade already added |
| C6 | Stage 2/3 token_cost = 0.0 | fixed | closed | live callers now pass token cost |
| C7 | empty tracking tables | split | partially fixed / partially reclassified | `karma_status` sink gap fixed; `canonical_facts` direct-finance coverage fixed; `timeline_entries` remains input/schema-shaped |
| C8 | Stage 3 intermediate failure not recorded | fixed | closed | retry-loop intermediate rejects now persist as distinct observability rows |
| C9 | NPC drift advisory-only | live | policy boundary | current design is explicitly advisory-only |
| C10 | target_ep selection not logged | fixed | closed | target episode stop now emits a dedicated stage4_control decision row |

## Evidence Notes

### C1 - fixed

- `modules/domain/agents/blueprint_constraint_compiler.py`
  - Stage 3 constraints now propagate `arc_title`
- `modules/domain/agents/blueprint_ensemble.py`
  - title is now emitted into the generation constraint text

Judgment:

- previously live
- now closed as a bounded backend patch

### C2 - hardened and closed

- `modules/domain/agents/blueprint_constraint_compiler.py:238`
  - `_extract_stop_line()` exists
- `modules/domain/agents/unified_blueprint_validator.py:613`
  - stop-line Python check existed
- current pass hardened it from prefix-substring matching to clause/token leakage detection

Judgment:

- OPUS wording "Python validation missing" was stale
- remaining weakness was real and bounded
- that bounded weakness is now closed

### C3 - still plausible, but policy-shaped

- `modules/domain/agents/director_ensemble.py:1565-1603`
  - contradiction firewall hard-gates `CRITICAL`/`MAJOR` contradiction cases
- `modules/domain/agents/director_prompts.py:146`
  - `python_warnings` remains a scoring slot
- `modules/domain/agents/director_ensemble.py:1681-1691`
  - issue count can clamp `python_warnings`, but this is still score-shaping, not a general hard gate

Judgment:

- OPUS wording is partially overstated because some hard-gate logic already exists
- however, the broader complaint remains live:
  generic Python critical/warning signals are not uniformly promoted to a hard reject rule
- this is now a policy/runtime-governance question, not a tiny bounded bugfix
- dedicated focused audit:
  - `docs/2026-03-20/c3-director-python-critical-hardgate-policy-audit.md`

### C4 - semantic split implemented and closed

- `modules/domain/agents/director_ensemble.py`
  - `PASS_WITH_FIX/PASS_WITH_WARNING` no longer force `quality_risk=True`
  - `revision_required` is emitted separately
- `modules/domain/agents/unified_blueprint_validator.py`
  - compare flow and single-candidate flow now emit `revision_required`
  - verdict-driven `quality_risk` folding is removed
- `modules/domain/agents/three_phase_blueprint_generator.py`
  - Stage 3 pipeline now persists `revision_required` separately from `quality_risk`
- `modules/core/stage3_orchestrator.py`
  - Stage 3 meta / director selection advisory / QualityDashboard now carry `revision_required`
- `modules/core/stage4_interview_round.py`
  - Stage 4 receives a softer advisory for `revision_required`
  - V75-D early trigger still keys off `quality_risk` only
- dedicated focused audit:
  - `docs/2026-03-20/c4-quality-risk-semantic-split-3pass-audit.md`

Judgment:

- OPUS complaint was materially valid
- the issue was cross-layer, but still patchable in a bounded way
- the semantic split is now closed

### C7 - split after fresh live DB survey

- fresh DB query against `projects/0_260318/project_data.db`
  - `karma_status = 0`
  - `canonical_facts = 0`
  - `timeline_entries = 0`
  - `state_logs = 2`
  - `fact_ledger.last_updated_ep = 2`
  - `world_state.last_updated_ep = 2`
- `state_logs.karma_matrix` was non-empty in the real run
- `modules/core/stage4_post_processor.py`
  - live PASS path previously persisted `karma_matrix` into state logs / episode bible only
  - now also dual-writes into `karma_status`
- `modules/core/fact_ledger.py`
  - `canonical_facts` sync already existed, but extractor coverage was too narrow for live direct finance scalars
- `modules/core/world_state.py`
  - `timeline_entries` sync already exists, but only through `time_markers`
- `docs/2026-03-20/c7-2-direct-financial-canonical-facts-coverage-fix-3pass-audit.md`
  - fresh live evidence reopened `C7-2`
  - direct `capital/total_assets/wealth` coverage is now fixed in a bounded way

Judgment:

- `C7-1 karma_status`
  - bounded live sink gap
  - now fixed
- `C7-2 canonical_facts`
  - bounded live extractor coverage gap
  - now fixed for direct finance scalars observed in the live run
- `C7-3 timeline_entries`
  - not a direct missing-table bug from current evidence
  - reclassified as upstream input/extraction issue

### C8 - fixed

- `modules/core/stage3_orchestrator.py`
  - final pass and final reject paths were already recorded
- `modules/domain/agents/three_phase_blueprint_generator.py`
  - retry-loop `generate_failed`, `continuity_reject`, `patch_retry_reject`, `validation_reject` branches now emit intermediate observability rows
- distinct `:intermediate:<event_tag>` attempt-key suffixes avoid collisions with final Stage 3 rows

Judgment:

- OPUS claim was materially valid
- bounded backend observability patch is now closed

### C9 - still live, but explicit policy

- `modules/core/npc_drift_advisor.py`
  - module doc explicitly says advisory-only and Director-owned

Judgment:

- OPUS claim is directionally valid
- but this is not a straight bugfix
- changing it means changing governance philosophy
- dedicated focused audit:
  - `docs/2026-03-20/c9-npc-drift-advisory-governance-audit.md`

### C10 - fixed

- `modules/core/stage4_orchestrator.py`
  - target episode stop now writes a dedicated `stage4_control` decision row
- audit hook now also emits `target_ep_reached`

Judgment:

- OPUS claim was materially valid
- very small bounded backend patch is now closed

## Recommended Order

No clearly bounded backend patch candidate remains from this screening set.

Treat the remaining items separately:

- `C3` - policy/runtime governance decision
- `C7-3` - schema/input coverage follow-up, not bounded sink patch
  - `docs/2026-03-20/c7-3-timeline-entries-input-coverage-audit.md`
- `C9` - policy boundary, not direct bugfix

## Screening Conclusion

There were still useful OPUS-derived backend candidates, and the bounded set is now effectively cleared.

Everything left in this note is either policy-shaped or requires a fresh live survey instead of another immediate bounded patch.
