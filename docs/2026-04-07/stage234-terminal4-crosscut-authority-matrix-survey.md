# Stage234 Terminal 4: Cross-Cut Authority / Compression / Promotion Matrix Survey

Date: 2026-04-07
Status: final
Document Type: read-only terminal survey
Canonical Path: `docs/2026-04-07/stage234-terminal4-crosscut-authority-matrix-survey.md`
Temp Mirror Path: `(none — survey output only)`
Track: system
Mode: read-only parallel survey; no code patching; docs-only output
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread narrative/output/docs deltas; hotspots include docs/temp/execution-roadmap.md, docs/temp/queue-state.json, docs/2026-04-01/active-temp-execution-roadmap.md, narrative-router files, multiple BI/TR artifacts, and untracked docs/2026-04-07 notes`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Coverage

### Read

Common prereads:

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

Terminal 4 additional reads:

- `modules/core/response_schemas.py` (Stage2 schema definitions — ARC_DESIGN_SCHEMA, joint_docs, status_shadow, state_constraints shapes)
- `modules/domain/agents/arc_ensemble.py` (Stage2 packet producer — tactical_doc, episode_details, beat_sequence, constraint_summary, joint_docs, status_shadow, state_changes emission)
- `modules/domain/agents/blueprint_constraint_compiler.py` (Stage3 compiler — constraint_block assembly from arc_data, arc_constraint_summary transport, must_focus/stop_line/inherited_state/state_changes_summary extraction)
- `modules/core/stage4_context_builder.py` (Stage4 context consumer — arc_data.constraint_summary as tier-0 prose, world_state summary injection, numeric carryover authority block, state_changes NPC/entity collection, Work Identity Authority packet)
- `modules/core/stage4_orchestrator.py` (Stage4 entry shell — blueprint dict intake via get_blueprint, mandatory_context budget trimming, reference_excerpt clamping)

Code-level grep traces across:

- `modules/core/stage4_post_pass_runtime.py` (state_truth_owner_contract, numeric_carryover_authority persistence, provenance tagging)
- `modules/core/stage4_interview_round.py` (fix_pack provenance stamping — director_authored / runtime_backfilled / runtime_synthesized)
- `modules/core/stage4_director_runtime.py` (_stage3_meta / quality_risk advisory injection)
- `modules/core/stage3_orchestrator.py` (_stage3_meta emission at blueprint save)
- `modules/core/stage2_finalizer.py` (arc persistence via save_v20_anchor, enriched_block overwrite seam)
- `modules/core/stage2_validation_pipeline.py`, `modules/core/stage2_preflight_runtime.py` (persistence-authority merge surfaces)
- `modules/core/fact_ledger.py` (carryover_baseline numeric authority, status_shadow auto-extraction)
- `modules/core/numeric_consistency_checker.py` (numeric_carryover_authority mismatch detection)
- `modules/core/db_manager.py` (save_blueprint, blueprint persistence surface)
- `modules/core/project_manager.py` (save_v20_anchor for arcs, _save_arcs_to_txt, _save_blueprint_to_txt export)

### Intentionally excluded

- Deep single-stage agent prompt content (covered by Terminals 1/2/3)
- Narrative pipeline artifacts (`bible/`, `treatments/`, `projects/` content)
- Stage0 preprocess and Stage1 volume planning (not in scope for Stage2→3→4 chain)
- Stage4 deep interview/retry/reject internal logic (Terminal 3 scope)

## 2. Findings

### F1. (cross-stage, severity: high) Numeric carryover baseline is never autonomously promoted across episode boundaries

**Evidence:**

- `modules/core/stage4_context_builder.py:978,1006` — `_build_numeric_carryover_authority_block` injects FactLedger carryover baseline into writer prompt
- `modules/core/stage4_post_pass_runtime.py:196-204` — `state_truth_owner_contract` persists `numeric_carryover_authority` with `authority_scope = carryover_baseline` and `owner = fact_ledger_carryover_baseline`
- But **no code path** autonomously promotes manuscript-proven numeric change into the next carryover baseline boundary
- This means legitimately changed numeric truth (e.g., protagonist's capital rising from 1천만원 to 200억) can still be re-flagged as a contradiction at the next-episode boundary, creating bounded false-positive retry pressure
- The seam spans Stage2 (fact_ledger population from arc state_changes), Stage3 (no numeric authority transport), and Stage4 (carryover readback without promotion)

**Classification:** cross-stage (packet owner: Stage2 fact_ledger seeder; compiler owner: Stage3 no-op; consumer owner: Stage4 post-pass runtime; persistence owner: Stage4 state_truth_owner_contract)

### F2. (cross-stage, severity: high) constraint_summary undergoes strength inversion from Stage2 to Stage4

**Evidence:**

- `modules/domain/agents/arc_ensemble.py` — Stage2 emits `constraint_summary` as a structured field in the arc candidate
- `modules/domain/agents/blueprint_constraint_compiler.py:91-94` — Stage3 reads `arc_data.get("constraint_summary")` and passes it through as `arc_constraint_summary` inside `constraint_block`
- `modules/core/stage4_context_builder.py:812-814,974-976` — Stage4 injects `constraint_summary` as a short prose line (`현재 갈등축: ...`) or as `active constraint spine:`, trimmed to 140-160 chars
- `modules/core/stage4_context_builder.py:1931-1933` — separately injected as `[Arc 제약 - MUST NOT DO]` tier-0 part
- **Net effect:** Stage2 machine-meaningful structured constraint becomes Stage4 prose advisory. The original structured strength is lost; Stage4 has no way to distinguish a MUST-level constraint from a SHOULD-level advisory

**Classification:** cross-stage (produced at Stage2, transported without strength metadata through Stage3, consumed as undifferentiated prose at Stage4)

### F3. (cross-stage, severity: high) Stage4 split-truth across final_state_updates / actual_truth / world_state persists without autonomous reconciliation

**Evidence:**

- `modules/core/stage4_post_pass_runtime.py:129-209` — `_build_state_truth_owner_contract` explicitly marks `actual_truth_surface` as `manager_actual_truth` or `director_state_updates_fallback`, marks `final_state_updates` as Director-owned, marks `inventory_counts` / `relationship_changes` as runtime storage overlays, marks `active_pressure_vectors` as `runtime_blueprint_overlay`
- The contract is emitted and persisted, but **no downstream consumer reconciles** these three truth surfaces into a single authoritative state for the next episode
- Next-episode Stage4 context builder reads `world_state` as a single summary, and separately reads arc-derived state_changes — the split truth provenance is invisible at intake time

**Classification:** cross-stage (produced at Stage4 post-pass, consumed at Stage4 context builder for next episode, but the split originates from Stage2 arc state vs Stage3 blueprint state vs Stage4 Director state)

### F4. (boundary-local, severity: medium) _stage3_meta is advisory-only at the Stage3→Stage4 boundary

**Evidence:**

- `modules/core/stage3_orchestrator.py:2005-2008` — Stage3 emits `blueprint["_stage3_meta"]` with `quality_gate_failed`, `last_score`, `quality_risk`, `final_verdict`
- `modules/core/stage4_director_runtime.py:1183-1190` — Stage4 Director reads `_stage3_meta.quality_risk` and adds a prose advisory warning if True
- **No other Stage4 consumer reads `_stage3_meta`** — it does not affect escalation thresholds, retry policy, or repair contract routing
- The metadata survives transport but has no machine-meaningful binding at the consumer side

**Classification:** boundary-local (Stage3 emits, Stage4 reads but only as prose advisory — the binding gap is at the Stage3→Stage4 boundary)

### F5. (cross-stage, severity: medium) beat_sequence, hybrid_composition, semantic_carryover are effectively dead at the Stage2→Stage3 boundary

**Evidence:**

- `modules/domain/agents/arc_ensemble.py:189-196` — `beat_sequence` is generated and used as fallback episode detail extraction
- `modules/domain/agents/blueprint_constraint_compiler.py` — does **not** read `beat_sequence`, `hybrid_composition`, or `semantic_carryover` from arc_data
- `modules/core/stage4_context_builder.py` — does **not** read these fields from arc_data
- These fields are produced by Stage2 and persisted in the arcs anchor, but no downstream stage consumes them as authority

**Classification:** cross-stage field death (producer: Stage2; no compiler or consumer reads them)

### F6. (cross-stage, severity: medium) Stage2 persistence-authority overwrite seam for joint_docs.world_joint / status_shadow

**Evidence:**

- `modules/core/stage2_finalizer.py:1458-1471` — `_persist_stage2_pass_arc_commit` persists refined_arc via `save_v20_anchor("arcs", ...)` — the arc payload at this point may have been mutated by validation/enrichment
- `modules/core/stage2_validation_pipeline.py` and `modules/core/stage2_preflight_runtime.py` — recently patched truth-preserving merge surfaces, but the broader enriched_block overwrite pattern means LLM-authored `joint_docs.world_joint` and `status_shadow` can still be overwritten by block-level fallback structures if the merge path is not exercised
- This matters cross-stage because Stage3 compiler reads `arc_data.get("joint_docs")` and `arc_data.get("status_shadow")` downstream — if the persisted values are stale/overwritten, Stage3 inherits corrupted truth

**Classification:** cross-stage (Stage2 producer persistence seam; downstream impact on Stage3 compiler and Stage4 context builder via arc_data chain)

### F7. (boundary-local, severity: medium) Stage3→Stage4 blueprint handoff is transport-clean but semantic-lossy

**Evidence:**

- `modules/core/stage3_orchestrator.py` saves blueprint via `project.save_blueprint(ep_num, data)` as a JSON dict to DB
- `modules/core/stage4_orchestrator.py` reads blueprint via `project.get_blueprint(ep_num)` — this returns the same dict, so transport is lossless
- But Stage3 blueprint prose (scene descriptions, plot directions, dialogue hints) does not carry machine-readable authority strength for the constraints it encodes
- Stage4 context builder treats blueprint content as context material, not as binding constraint — the semantic authority that Stage3 validator/compiler intended is flattened into writer-facing prose

**Classification:** boundary-local (the loss is at the Stage3→Stage4 semantic interpretation boundary, not transport)

### F8. (stage-local, severity: low) fix_pack provenance is now explicit but not yet reconciled with baseline promotion

**Evidence:**

- `modules/core/stage4_interview_round.py:1933-2007` — fix_pack provenance is stamped as `director_authored`, `runtime_backfilled`, or `runtime_synthesized`
- `modules/core/stage4_post_pass_runtime.py` — state_truth_owner_contract persists provenance
- But the provenance does not feed back into the carryover baseline promotion decision at F1 — a `runtime_synthesized` fix that changes numeric truth still does not autonomously promote the new baseline

**Classification:** stage-local (Stage4 internal; the provenance infrastructure exists but the promotion loop is open)

## 3. Authority / Loss Map

| Concept | Stage2 Authoritative Surface | Stage3 Actual Consumer Surface | Stage4 Actual Consumer Surface | Loss Type | Loss Point |
|---|---|---|---|---|---|
| constraint_summary | structured field in arc candidate (`arc_ensemble.py`) | `arc_constraint_summary` passthrough in constraint_block (`blueprint_constraint_compiler.py:92`) | prose advisory `현재 갈등축:` / `active constraint spine:` trimmed to 140-160 chars (`stage4_context_builder.py:812,974`) | **strength inversion** + **prose flattening** | Stage3→Stage4 intake |
| tactical_doc | prose field in arc candidate, main mission authority | Stage3 reads for `must_focus` / `stop_line` extraction (`blueprint_constraint_compiler.py:281,336`) | Stage4 reads as `arc_tactical` prose injection (`stage4_context_builder.py:2424`) | **prose passthrough** (no structured extraction) | Stage2 emission (never structured) |
| episode_details | list[dict] in arc candidate | Stage3 reads for episode focus (`blueprint_constraint_compiler.py:326-328`) | Stage4 reads indirectly via blueprint context | **partial survival** | some Stage2 detail lost in blueprint compilation |
| beat_sequence | list in arc candidate | **not read** | **not read** | **field death** | Stage2→Stage3 boundary |
| hybrid_composition | field in arc candidate | **not read** | **not read** | **field death** | Stage2→Stage3 boundary |
| semantic_carryover | field in arc candidate | read only by compiler as normalized text (`blueprint_constraint_compiler.py:98`) | **not directly read** | **near-death** (low signal) | Stage2→Stage3 boundary |
| joint_docs.world_joint | structured field in arc, persistence-authority seam | compiler reads `arc_data.get("joint_docs")` for inventory (`blueprint_constraint_compiler.py:498-500`) | Stage4 context builder accesses `world_state` object, not raw joint_docs | **advisory downgrade** | Stage2 persistence (overwrite risk) → Stage3 partial read → Stage4 alternative source |
| status_shadow | structured field in arc (genre-dependent) | compiler reads `arc_data.get("status_shadow")` for state extraction (`blueprint_constraint_compiler.py:507-508`) | Stage4 accesses `world_state` / `fact_ledger` instead | **advisory downgrade** + **source substitution** | Stage2 persistence → Stage3 partial read → Stage4 alternative source |
| state_changes | structured dict in arc | compiler reads for `state_changes_summary` (`blueprint_constraint_compiler.py:97`) | Stage4 context builder reads `arc_data.state_changes` for NPC/entity/item collection (`stage4_context_builder.py:289-400`) | **partial survival** | summary compression at Stage3; direct but selective read at Stage4 |
| _stage3_meta (quality_risk) | N/A | emitted at blueprint save (`stage3_orchestrator.py:2005`) | Director reads as prose advisory only (`stage4_director_runtime.py:1183-1190`) | **advisory downgrade** | Stage3→Stage4 boundary |
| numeric carryover baseline | fact_ledger seeded from Stage2 state_changes | **no transport** | context builder injects, post-pass persists, but **no autonomous promotion** | **repair-loop compensation** (contradiction firewall catches mismatch) | cross-stage: Stage2 seeds → Stage3 ignores → Stage4 reads but cannot promote |
| fix_pack provenance | N/A | N/A | stamped at Stage4 (`stage4_interview_round.py:1933-2007`), persisted in state_truth_owner_contract | **no cross-stage loss** (Stage4-only concept) | N/A |
| final_state_updates / actual_truth / world_state | Stage2 seeds state_changes | Stage3 does not reconcile | Stage4 post-pass persists split truth with explicit owner contract but **no downstream reconciliation** | **multi-owner split truth** | Stage4 post-pass → Stage4 next-episode intake |

## 4. Non-Issues

### N1. Blueprint transport fidelity

The Stage3→Stage4 blueprint JSON dict handoff via DB (`save_blueprint` / `get_blueprint`) is transport-clean. There is no JSON corruption, field dropping, or encoding loss at this boundary. The loss is semantic, not transport.

### N2. Stage2 content quality

Stage2 is not content-starved. The surveys confirm `content-sufficient but schema-fragile`. The cross-stage problem is not missing narrative content from Stage2 — it is authority packaging, strength metadata, and persistence integrity.

### N3. Stage4 fix_pack provenance infrastructure

The recently landed provenance stamping (`director_authored`, `runtime_backfilled`, `runtime_synthesized`) and state_truth_owner_contract infrastructure are functioning as designed. These are not debt — they are substrate that the open baseline-promotion seam needs to leverage.

### N4. Stage4 Work Identity Authority packet

The recently landed `[Stage4 Work Identity Authority]` tier-0 injection in `stage4_context_builder.py` correctly surfaces tracking_slots, mandatory_scene_engines, and registry_profiles as structured authority. This is not a compression or loss point.

### N5. Stage3 generation hierarchy

Stage3 is not hierarchy-free chaos. The generation, compilation, and validation pipeline is explicit and reasonably well-structured. The debt is in enforcement binding and semantic handoff, not in missing architecture.

## 5. Owner Verdict

### Packet owner (Stage2 emission)

- `modules/domain/agents/arc_ensemble.py`
- `modules/core/response_schemas.py`
- `modules/core/stage2_finalizer.py`

Owns: arc candidate schema, field emission, persistence-authority merge

### Compiler owner (Stage3 compilation)

- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/unified_blueprint_validator.py`

Owns: constraint_block assembly, arc-to-blueprint semantic transport, enforcement binding scope

### Consumer owner (Stage4 intake + post-pass)

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_interview_round.py`

Owns: intake authority hierarchy, state-truth owner contract, fix_pack provenance, carryover baseline readback

### Persistence owner (cross-stage)

- `modules/core/db_manager.py` (blueprint and arc persistence)
- `modules/core/project_manager.py` (save_v20_anchor for arcs, txt export)
- `modules/core/fact_ledger.py` (numeric authority seeding from state_changes)

Owns: durable handoff surface, anchor integrity, carryover baseline population

### Observability owner (cross-stage)

- `modules/core/stage4_post_pass_runtime.py` (state_truth_owner_contract visibility)
- `modules/core/numeric_consistency_checker.py` (carryover mismatch detection)
- `modules/core/stage2_validation_pipeline.py` (Stage2 correction/retrieval surfacing)

Owns: operator-facing truth provenance, contradiction detection, correction visibility

## 6. Promotion Signal

### Signal: `covered-by-existing-queue` for the majority; `merge-first-no-promotion` for the merged cross-cut picture

**Rationale:**

The five highest-severity findings map to existing queue items as follows:

| Finding | Existing Queue Item | Coverage Status |
|---|---|---|
| F1. numeric carryover baseline promotion gap | `0_0-stage4-consumer-contract-normalization-remediation` (§15, numeric carryover baseline promotion) | **covered** — explicitly the surviving active P1 in this lane |
| F2. constraint_summary strength inversion | `0_0-stage234-cross-stage-contract-normalization-remediation` (§4, Tranche 2 owner/strength normalization) | **covered** — explicitly named as one of the three highest-cost mismatch families |
| F3. split-truth final_state_updates/actual_truth/world_state | `0_0-stage234-cross-stage-contract-normalization-remediation` (§4, Tranche 2) + `0_0-stage4-consumer-contract-normalization-remediation` (Tranche 3) | **covered** — split between the cross-stage substrate and the Stage4 consumer lane |
| F4. _stage3_meta advisory-only | `0_0-stage3-contract-tightening-remediation` (§7, Tranche 1 binding scope) | **covered** — the binding scope tightening tranche explicitly targets advisory-only enforcement weakness |
| F5. dead fields at Stage2→Stage3 boundary | `0_0-stage2-contract-normalization-remediation` (§7, Tranche 3 dead-field cleanup) | **covered** — explicit keep-or-drop tranche |
| F6. Stage2 persistence overwrite seam | `0_0-stage2-contract-normalization-remediation` (§7, Tranche 1 persistence-authority merge) | **covered** — the bounded tranche has already landed partial realization |
| F7. Stage3→Stage4 semantic-lossy handoff | `0_0-stage3-contract-tightening-remediation` (Tranche 3 semantic handoff preservation) | **covered** |
| F8. fix_pack provenance not feeding baseline promotion | `0_0-stage4-consumer-contract-normalization-remediation` (surviving active P1) | **covered** — the promotion loop closure is the same seam as F1 |

**Conclusion:**

All eight findings trace to existing queue items. No uncovered debt was identified that would justify a new execution SSOT.

The merged cross-cut matrix picture is useful as a single-document authority map for the existing queue items to reference, but it does not itself constitute a new execution topic. Therefore:

- **Do not promote** a new execution SSOT from this survey
- **Do** attach the merged authority/loss map (§3) to the existing cross-stage SSOT (`0_0-stage234-cross-stage-contract-normalization-remediation`) as an evidence update when that lane is next re-audited
- **Do** treat this survey as merged evidence for the central 4-terminal merge audit

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
