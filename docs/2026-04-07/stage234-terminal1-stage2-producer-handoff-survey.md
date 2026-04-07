# Stage234 Terminal 1: Stage2 Producer / Handoff Survey

Date: 2026-04-07
Status: final
Document Type: read-only terminal survey
Track: system
Mode: read-only parallel survey; no code patching; docs-only output
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread narrative/output/docs deltas`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Coverage

### Read

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/commit-state-minimal-contract.md`
- `docs/stage_map/interfaces.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `modules/domain/agents/arc_ensemble.py`
- `modules/core/response_schemas.py`
- `config/prompts/ensemble.yaml`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_entity_contract.py`
- `modules/core/tactical_utils.py`
- `modules/core/stage2_contracts.py`
- `modules/core/stage2_preflight.py`

### Intentionally excluded

- Stage3/4 code — owned by Terminal 2 and Terminal 3
- Cross-stage matrix — owned by Terminal 4
- `docs/temp/` mutation — prohibited by order
- Runtime artifacts in `projects/` — read-only survey only

## 2. Findings

### F-1. `tactical_doc` prose dominance as mission authority (severity: high, class: stage-local)

`tactical_doc` is the single largest Stage2 truth owner. It carries per-episode mission detail, start/end states, character arcs, pacing, and constraint compliance as a monolithic freeform string. The canonical schema (`ARC_DESIGN_SCHEMA` at `modules/core/response_schemas.py:386`) types it as `types.Type.STRING` with no substructure.

Downstream extraction relies on regex header patterns:
- `modules/core/tactical_utils.py:6-18` — six regex templates for episode header matching
- `modules/domain/agents/arc_ensemble.py:220-245` — `_extract_episode_detail_map_from_tactical_doc()` as a last-resort fallback for when `episode_details` is absent

This means the richest Stage2 mission truth is trapped in prose that downstream consumers cannot structurally traverse. Stage3 compiler receives `tactical_doc` as a raw string; any machine-meaningful extraction from it is either regex-fragile or absent.

Owner files:
- `modules/domain/agents/arc_ensemble.py`
- `config/prompts/ensemble.yaml`
- `modules/core/response_schemas.py`

### F-2. `episode_details` strong canonical packet with bounded coverage (severity: medium, class: stage-local)

`episode_details` is the strongest structured mission surface Stage2 produces. It is explicitly declared as the "canonical per-episode mission authority" in `config/prompts/ensemble.yaml:74-77`. The prompt instructs the LLM to emit it first, then expand into `tactical_doc`, and resolves conflicts in favor of `episode_details`.

Strong normalization exists:
- `arc_ensemble.py:154-185` — `_normalize_episode_details()` with ep_start/ep_end bounds
- `arc_ensemble.py:248-270` — `_build_canonical_episode_details()` with three-tier fallback: `episode_details` > `beat_sequence` > `tactical_doc` regex

Contract health scoring at `arc_ensemble.py:453-519` penalizes missing or partial `episode_details` coverage with up to 12 penalty points.

Remaining weakness: coverage can be partial. When the LLM omits per-episode entries, the beat_sequence or tactical_doc regex fallback may provide only titles rather than actionable beats. The downstream consumer (Stage3) does not distinguish between primary and fallback-sourced episode detail.

Owner files:
- `modules/domain/agents/arc_ensemble.py`

### F-3. `state_constraints` — strongest structured handoff surface (severity: low, class: stage-local)

`state_constraints` is schema-enforced via `ARC_STATE_CONSTRAINTS_SCHEMA` in `response_schemas.py`. It carries `arc_start_state`, `arc_end_state`, `items_acquired`, `items_consumed`, and `investment_calc` as typed structured fields.

Stage2 has strong producer-side validation:
- Location label collapse at finalization (`stage2_finalizer.py:325-358` — `_sync_stage2_end_location_contract`)
- Inventory carryover computation (`stage2_finalizer.py:246-322` — `_sync_stage2_end_state_inventory_contract`)
- Vocabulary issue detection (`arc_ensemble.py:320-367` — `_collect_state_contract_vocabulary_issues`)
- Non-wuxia state noise detection (`arc_ensemble.py:370-388`)
- Investment arithmetic checking (`arc_ensemble.py:422-450`)

This is the strongest Stage2 canonical surface. The structured fields survive into Stage3 arc context via `anchors["arcs"]`.

### F-4. `merge_stage2_authoritative_packet` merge semantics at validation/finalization (severity: medium, class: stage-local)

`modules/core/stage2_contracts.py:19-37` defines `merge_stage2_authoritative_packet` with these semantics:
1. Start from fallback (`enriched_block`) as deep-copy base
2. Overlay non-empty authoritative (`refined_arc`) values
3. Keep fallback for empty authoritative fields
4. Recurse for nested dicts

This is called at two critical points:
- **Validation pipeline** (`stage2_validation_pipeline.py:930-937`): merges `refined_arc.joint_docs` and `status_shadow` with `enriched_block` versions before ContinuityInspector
- **Finalizer** (`stage2_finalizer.py:1210-1217`): merges again during PASS preparation

The 2026-04-06 SSOT identified this as a live P1: when the LLM-authored `world_joint` or `status_shadow` fields are empty or thin, the merge backfills from `enriched_block` values, which may carry stale block-level data from a prior pipeline stage. The bounded persistence-authority tranche has reportedly landed across `stage2_preflight_runtime.py`, `stage2_validation_pipeline.py`, and `stage2_finalizer.py`, but the merge contract itself still allows fallback injection.

Owner files:
- `modules/core/stage2_contracts.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`

### F-5. `beat_sequence` and `hybrid_composition` — effectively dead fields at boundary (severity: low, class: boundary-local)

Per the existing cross-stage survey evidence:
- `beat_sequence` is used only as a fallback source for `episode_details` in `_build_canonical_episode_details` (`arc_ensemble.py:254`)
- `hybrid_composition` is carried through as a metadata field with no downstream structured consumer

Neither field has an explicit keep-or-drop policy. They inflate the arc payload without providing machine-meaningful value to Stage3.

Owner files:
- `modules/domain/agents/arc_ensemble.py`
- `modules/core/response_schemas.py`

### F-6. Carryover Authority Packet — strong but prompt-only contract (severity: medium, class: stage-local)

The 2026-04-05 bounded realization added a `[Carryover Authority Packet]` system:
- `arc_ensemble.py:57-83` — `_extract_carryover_authority_packet` parses a text-block from `prev_arc_context`
- `arc_ensemble.py:108-134` — `_render_carryover_authority_packet` serializes for prompt injection
- `config/prompts/ensemble.yaml:66-72` — ranked above generic `Previous Arc Context`

This is a strong Stage2 producer-side contract for opening-state continuity. However, the packet is a prompt-injected text block, not a structured field in the response schema or the persisted arc payload. It exists only during generation time and is not preserved in `anchors["arcs"]` for downstream access.

Owner files:
- `modules/domain/agents/arc_ensemble.py`
- `config/prompts/ensemble.yaml`

### F-7. Entity name canonicalization — bounded but fixed-path (severity: low, class: stage-local)

`modules/core/stage2_entity_contract.py:130-171` applies entity name normalization across a fixed set of arc paths:
- `tactical_doc`, `joint_docs.final_location`, `joint_docs.physical_inventory`, `state_constraints.arc_start_state.*`, `state_constraints.arc_end_state.*`, `episode_details`

The path list is hardcoded. Any new field added to the arc schema would need manual inclusion. This is acceptable for current scope but represents a minor producer-local maintenance debt.

## 3. Authority / Loss Map

| Surface | Authoritative Owner | Actual Downstream Consumer | Loss/Compression Point |
|---|---|---|---|
| `tactical_doc` | `arc_ensemble.py` + `ensemble.yaml` (prompt-generated freeform string) | Stage3 reads as raw prose via `anchors["arcs"]` | **prose flattening**: machine-meaningful mission detail locked in unstructured text |
| `episode_details` | `arc_ensemble.py` `_build_canonical_episode_details` (structured list) | Stage3 reads from arc dict; Stage4 via blueprint | minor: fallback-sourced entries may be title-only |
| `state_constraints` | `arc_ensemble.py` + `stage2_finalizer.py` (schema-enforced structured dict) | Stage3 reads directly; strong survival | minimal loss at Stage2→Stage3 boundary |
| `joint_docs` | `arc_ensemble.py` generation + `stage2_contracts.py` merge + `stage2_finalizer.py` sync | Stage3 reads; Stage4 via blueprint | **merge contamination risk**: enriched_block fallback can inject stale values |
| `status_shadow` | `arc_ensemble.py` generation + `stage2_contracts.py` merge | Stage3/4 as advisory only | **advisory downgrade**: always advisory, never binding |
| `state_changes` | `arc_ensemble.py` generation + StateExtractor Python fallback | Stage3/4 via anchors | moderate: LLM may omit; Python fallback has ~98% accuracy per existing surveys |
| `beat_sequence` | `arc_ensemble.py` (schema field, LLM-generated) | Stage3 does not meaningfully consume | **field death**: present in payload but not used |
| `hybrid_composition` | `arc_ensemble.py` (schema field, LLM-generated) | Stage3 does not meaningfully consume | **field death**: present in payload but not used |
| `Carryover Authority Packet` | `arc_ensemble.py` prompt-time text block | Not persisted; generation-time only | **prompt-only scope**: strong at generation but invisible to downstream |

## 4. Non-Issues

- **Stage2 content quality**: Stage2 is described as `content-sufficient`. The problem is not that Stage2 generates bad content, but that the strongest content lives in prose form.
- **Stage2 schema enforcement**: `ARC_DESIGN_SCHEMA` and `ARC_STATE_CONSTRAINTS_SCHEMA` provide strong Gemini response_schema enforcement. Structured fields that the LLM fills are well-typed.
- **Location and inventory sync**: `_sync_stage2_end_location_contract` and `_sync_stage2_end_state_inventory_contract` in `stage2_finalizer.py` are working contract enforcement at finalization time. These are not front debt.
- **Investment arithmetic checking**: `InvestmentArithmeticChecker` provides pre-selection validation for financial consistency. This is functional producer-side validation.
- **Strategy diversity and selection bias**: `_build_strategy_execution_plan` and `_summarize_candidate_diversity` in `arc_ensemble.py` work as designed for ensemble selection. Not front debt.

## 5. Owner Verdict

If a future producer-side harness wave is promoted, the narrowest owner set is:

1. **`modules/domain/agents/arc_ensemble.py`** — primary generation, prompt assembly, candidate scoring, carryover packet extraction, episode_details normalization, and contract health scoring
2. **`modules/core/stage2_contracts.py`** — `merge_stage2_authoritative_packet` defines the merge semantics that govern persistence-time authority
3. **`modules/core/stage2_finalizer.py`** — location/inventory sync, PASS preparation merge, and final arc structure repair before persistence

Secondary owner family (already cited in existing SSOT):
- `config/prompts/ensemble.yaml` — prompt contract for canonical field priority
- `modules/core/stage2_validation_pipeline.py` — pre-Director validation merge point
- `modules/core/response_schemas.py` — `ARC_DESIGN_SCHEMA` defines the schema boundary

## 6. Promotion Signal

`covered-by-existing-queue`

Rationale:
- F-1 (tactical_doc prose dominance) and F-2 (episode_details coverage) are covered by `0_0-stage2-contract-normalization-remediation-execution-ssot.md` Tranche 1 (Mission Authority Extraction) and Tranche 2 (Contract Vocabulary Normalization)
- F-4 (merge_stage2_authoritative_packet) is covered by the same SSOT's active Tranche 1 (Persistence-Authority Merge), which has already partially landed
- F-5 (dead fields) is covered by the same SSOT's Tranche 3 (Dead-Field Keep-or-Drop Cleanup)
- F-6 (Carryover Authority Packet prompt-only scope) is a residual from the 2026-04-05 bounded realization; it enriches the same SSOT but does not justify a separate execution lane
- F-7 (entity contract fixed paths) is minor maintenance debt, not execution-lane material

No new execution SSOT is needed from this terminal. The existing `0_0-stage2-contract-normalization-remediation-execution-ssot.md` already covers all identified producer-local debt. The merged 4-terminal audit should confirm whether any cross-stage seams require additions to the existing cross-stage future-wave SSOT.

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
