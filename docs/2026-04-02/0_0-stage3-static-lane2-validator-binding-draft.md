# 0_0 Stage3 Static Lane 2 — Validator / Binding / Semantic Fidelity

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: survey lane draft
Track: system
Mode: bounded static parallel survey, read-only
Master Order: `docs/2026-04-02/0_0-stage3-static-global-parallel-master-order.md`
Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
Terminal: 2 (Opus)
Role: Stage3 validator / binding / semantic fidelity lane

---

## 1. Coverage

### Primary Surfaces Inspected

| Surface | File | LOC (approx.) |
|---|---|---|
| UnifiedBlueprintValidator | `modules/domain/agents/unified_blueprint_validator.py` | ~1,839 |
| BlueprintConstraintCompiler | `modules/domain/agents/blueprint_constraint_compiler.py` | ~1,083 |
| ThreePhaseBlueprintGenerator | `modules/domain/agents/three_phase_blueprint_generator.py` | top 80 lines |
| ThreePhaseBlueprintRuntime | `modules/domain/agents/three_phase_blueprint_runtime.py` | validate flow L790-1400 |
| Director facade | `modules/domain/agents/director.py` | `compare_and_select_blueprint`, `audit_manuscript` signatures |
| DirectorEnsemble | `modules/domain/agents/director_ensemble.py` | `compare_and_select_blueprint` signature |
| ensemble.yaml | `config/prompts/ensemble.yaml` | binding/prevalidation references |

### Secondary Traces

- `PASS_WITH_FIX` flow across `director_auditor.py`, `director_grading.py`, `director_ensemble.py`, `bridge_server.py`, `failure_analyzer.py`
- `_BINDING_PREVALIDATION_CATEGORIES` usage in `unified_blueprint_validator.py`
- `constraint_compiler` wiring in `stage2_context.py`, `stage2_preflight.py` (Stage 2 constraint compiler is a different class: `ConstraintCompiler`, not `BlueprintConstraintCompiler`)

---

## 2. Findings

### F-1. Binding Prevalidation: Structurally Present But Verdict-Weak

**The binding prevalidation contract (`_apply_binding_prevalidation_contract`) never issues REJECT.**

Mechanics:
- `_collect_binding_prevalidation_issues()` filters pre-validation issues by category membership in `_BINDING_PREVALIDATION_CATEGORIES` (9 categories) and severity ≥ MAJOR.
- `_apply_binding_prevalidation_contract()` is called **after** Director verdict arrives.
- If Director already said REJECT → binding issues are appended but verdict stays REJECT (no-op).
- If Director said PASS or PASS_WITH_WARNING and binding issues exist → verdict is **promoted to PASS_WITH_FIX**, feedback is enriched with a `[Binding prevalidation]` note.
- **Binding never escalates a PASS to REJECT.** It can only promote PASS → PASS_WITH_FIX.

Consequence:
- Binding prevalidation is **advisory-to-Director, repair-advisory-post-Director**. It does not block. It nudges the pipeline into a `PASS_WITH_FIX` loop (max ~3 iterations), but if those iterations fail the blueprint is still adopted at the patched score (see `_run_pass_with_fix_loop` L1184-1196).
- **Structural invariants like `scene_completeness`, `opening_anchor`, `mission_clarity`, `timeline_specificity`, `protagonist_state`, `fact_lock_institution`, `tactical_semantic_fidelity` cannot independently reject a blueprint.**
- The only real blocking power comes from Director itself (verdict=REJECT) or from the quality gate (PASS + score < threshold → forced REJECT).

Classification: **advisory-heavy binding**

### F-2. Python Prevalidation: Broad Surface, Director-Deferred Authority

`_python_pre_validate()` runs 12 distinct issue collectors:

| # | Collector | Severity Cap | Category |
|---|---|---|---|
| 1 | `_collect_structure_prevalidation_issues` | MAJOR | structure |
| 2 | `_collect_fidelity_prevalidation_issues` | MINOR | fidelity |
| 3 | `_collect_arc_compliance_prevalidation_issues` | CRITICAL | arc_compliance |
| 4 | `_collect_continuity_prevalidation_issues` | MAJOR | continuity |
| 5 | `_collect_fact_lock_drift_issues` | CRITICAL | fact_lock_* |
| 6 | `_collect_capital_state_drift_issues` | CRITICAL | capital_state |
| 7 | `_collect_capital_unit_alignment_issues` | MAJOR | capital_unit |
| 8 | `_collect_temporal_deictic_drift_issues` | MAJOR | temporal_deictic |
| 9 | `_collect_scene_specificity_issues` | MAJOR | scene_specificity |
| 10 | `_collect_scene_characters_issues` | MAJOR | scene_completeness |
| 11 | `_collect_arc_timeline_alignment_issues` | MAJOR | arc_timeline |
| 12 | `_collect_tactical_semantic_fidelity_issues` | CRITICAL | tactical_semantic_fidelity |
| 13 | `_collect_stage4_readiness_contract_issues` | MAJOR | opening_anchor, mission_clarity, timeline_specificity, protagonist_state |
| 14 | `_collect_scenario_density_issues` | MINOR | scenario_density |

**All 14 collectors produce warnings only.** The result (`_build_python_prevalidation_result`) sets `has_critical` and `has_major_excess` flags, but these flags are **never used to block**. They are forwarded to Director as context:
- `python_warnings` (up to 4) are injected as a `[Director Focus Header]` prepended to the manuscript text for Director's LLM call.
- The warnings are bounded to 4 entries, 160 chars each.

**Director sees a compressed, truncated advisory summary — not the full diagnostic.** If Director ignores the header (which LLMs routinely do for prepended metadata), the Python findings vanish.

Classification: **advisory-only prevalidation**

### F-3. Dead NPC Advisory: CRITICAL Flag, Director-Deferred Resolution

`_apply_dead_npc_advisory()` marks `has_critical = True` and appends a CRITICAL-severity issue. But the only consumer pathway is:
1. Log a warning: `"[V60.96] Dead NPC advisory forwarded to Director"`
2. Forward to Director via the `python_warnings` mechanism.

**No hard block.** If Director PASS-es despite the advisory, the dead NPC issue survives only as metadata on the blueprint's `_ensemble_meta.python_warnings`.

Classification: **CRITICAL label, advisory authority**

### F-4. Binding Categories Are Well-Defined But Narrow

The 9 categories in `_BINDING_PREVALIDATION_CATEGORIES`:
```
scene_completeness, arc_timeline, capital_unit, opening_anchor,
mission_clarity, timeline_specificity, protagonist_state,
fact_lock_institution, tactical_semantic_fidelity
```

These target Stage4-readiness contracts, capital integrity, and semantic fidelity — the right surfaces. However:
- Only **4 of 14** collectors produce issues in these categories (collectors 7, 10, 12, 13).
- The remaining 10 collectors' issues (structure, fidelity, arc_compliance, continuity, fact_lock_location/item/provenance, capital_state, phantom_capital, temporal_deictic, scenario_density) are **outside binding scope** and go only through the general `python_warnings` path.
- This means the most dangerous drift types — **arc_compliance (stop-line violation), fact_lock_location, fact_lock_provenance, capital_state** — are labeled CRITICAL but **not in binding scope**, so they cannot even trigger PASS_WITH_FIX promotion.

Classification: **binding scope gap — highest-severity drift types excluded**

### F-5. Fact-Lock Packet: Rich Compilation, Weak Enforcement

`BlueprintConstraintCompiler._build_fact_lock_packet()` builds a thorough 6-category packet:
1. Location anchor (위치)
2. Time/day anchor (시간)
3. Ending hook anchor (엔딩훅)
4. Protagonist state anchor (소지품, 부상)
5. Manuscript-derived provenance (아이템위치)
6. NPC/Institution authority anchor (기관)

And `_collect_fact_lock_drift_issues()` checks 4 drift modes:
- Location drift (fact_lock_location → MAJOR)
- Item storage drift (fact_lock_item → MAJOR)
- Ending hook provenance drift (fact_lock_provenance → CRITICAL)
- Institution authority drift (fact_lock_institution → CRITICAL)

**But** only `fact_lock_institution` is in binding scope. The other three CRITICAL/MAJOR fact-lock categories go through the advisory-only path. This is the sharpest gap: the most specific, Python-detectable contract violations (item moved, location contradicted, trust sentiment flipped) **cannot trigger repair**.

### F-6. Constraint Compiler Output: Structurally Complete, Prompt-Injected

`BlueprintConstraintCompiler.compile()` produces a 12-field constraint block:
```
ep_num, arc_no, arc_position, must_focus, stop_line, continuity,
inherited_state, arc_constraint_summary, state_changes_summary,
semantic_carryover, immutable_fact_carryover, fact_lock_packet,
capital_continuity_packet
```

`compile_to_prompt()` renders this into a structured prompt injection with clear section headers and emoji markers. The prompt ordering is:
1. Semantic carryover (pre-header)
2. **FACT-LOCK** (highest priority, explicit "변경 금지")
3. **CAPITAL-LOCK** (investment-genre, explicit "REJECT" language)
4. MUST_FOCUS (core arc events)
5. STOP_LINE (future episode boundary)
6. CONTINUITY (prev ep state)
7. INHERITED_STATE (physical state)
8. ARC constraints (MUST NOT DO)
9. State changes summary
10. IFC (immutable fact carryover)

The prompt compilation is well-structured and priority-ordered. **But its enforcement relies entirely on the LLM (blueprint ensemble) respecting these text blocks during generation.** There is no post-generation structural verification that the fact-lock or capital-lock constraints were actually honored, except for the soft Python prevalidation checks described above.

### F-7. Semantic Carryover: W2 Suppressions Reduce Drift Signal

`_normalize_semantic_carryover()` explicitly suppresses two fields:
- `growth_justification`: "encodes future achievement"
- `continuity_checkpoints`: "describes arc-end completion state"

These suppressions are well-justified (they prevented current-episode drift toward arc-end targets). But they also mean that arc-level growth trajectory and completion benchmarks are **invisible to Stage3** — the blueprint cannot cross-reference whether it's pacing toward arc closure correctly.

### F-8. Compare Mode: Binding Applied Post-Selection

In compare mode (`_run_compare_validation`):
1. Each candidate gets independent `_prepare_compare_candidate()` (Python pre-validate + dead NPC advisory).
2. Director `compare_and_select_blueprint()` selects one candidate.
3. **After** Director selection, `_apply_binding_prevalidation_contract()` runs on the selected candidate's pre-result.

This means:
- Binding cannot influence Director's candidate selection.
- If Director picks a candidate with binding issues over one without, the binding system can only retrofit a PASS_WITH_FIX verdict on the already-selected candidate.
- The `candidate_advisories` array is logged but not consumed by Director's selection prompt.

---

## 3. Non-Issues

### N-1. Director Sovereignty Is Preserved

Python prevalidation never overrides Director. The architecture faithfully implements 디렉터주권주의 (Director Sovereignty). This is not a bug — it's the documented design principle. The question is whether the advisory-only binding is *sufficient*, not whether it violates governance.

### N-2. Constraint Compiler Output Quality Is High

The `BlueprintConstraintCompiler` produces structurally sound, well-ordered constraint blocks. The prompt rendering is clear, uses emoji section markers, and places fact-lock before must-focus. The compilation itself is not a drift source.

### N-3. Capital Continuity Packet Is Genre-Bounded

`_build_capital_continuity_packet()` correctly activates only for `genre == "investment"`. No false positive risk for wuxia/hunter/fantasy runs. The multi-layer extraction (ending_state → protagonist_state → equipment → status text → manuscript tail → state_changes) is thorough.

### N-4. Stop-Line Enforcement Has Two Detection Modes

`_detect_stop_line_violation()` uses both clause substring matching (≥12 chars) and token overlap (≥3 tokens, ≥75% overlap ratio). This is reasonable for catching obvious next-episode content leakage without excessive false positives.

### N-5. Quality Gate Provides a Backstop

The quality gate (`_apply_phase3_quality_gate`) forces REJECT when Director PASS-es but score < threshold (default 90). This catches some of the low-quality PASS-es that binding alone cannot block.

---

## 4. Verdict

**advisory-heavy**

Rationale:

1. **No binding check can independently REJECT a blueprint.** All Python prevalidation is advisory to Director. The binding prevalidation contract can only promote PASS → PASS_WITH_FIX (a soft repair loop, not a hard block).

2. **The highest-severity drift detectors are outside binding scope.** `arc_compliance` (stop-line violations), `fact_lock_location`, `fact_lock_provenance`, `fact_lock_item`, and `capital_state` are all CRITICAL-rated but cannot trigger even PASS_WITH_FIX because their categories are not in `_BINDING_PREVALIDATION_CATEGORIES`.

3. **Director sees a compressed 4-entry summary, not the full diagnostic.** The `python_warnings` pathway truncates findings to 4 × 160 chars and prepends them to the manuscript. If Director's LLM attention doesn't prioritize the focus header, the signal is lost.

4. **Binding applies post-Director-selection in compare mode.** It cannot influence which candidate Director picks, only retrofit a repair verdict on the already-chosen one.

5. **The constraint compiler produces strong input contracts, but enforcement is LLM-honor-system on generation and advisory-only on validation.** The fact-lock, capital-lock, and stop-line constraints are well-compiled into the prompt but not structurally verified after the LLM generates.

### Dominant Residual Seam

The dominant seam is the **binding scope gap**: the most specific, Python-detectable contract violations (fact-lock location/item/provenance, capital state contradictions, stop-line violations) carry CRITICAL severity labels but are excluded from the binding categories that could trigger PASS_WITH_FIX. They depend entirely on Director's LLM attention to a compressed focus header.

### Implication for Required Questions

| Question | Answer |
|---|---|
| Which Stage3 problems are genuinely blocked by binding prevalidation? | **None are genuinely blocked.** 9 binding categories can promote PASS → PASS_WITH_FIX (a repair loop), but cannot REJECT. The PASS_WITH_FIX loop itself has a max-iteration fallback that accepts the patched blueprint anyway. |
| Which major seams are still advisory or Director-deferred? | **All seams are advisory or Director-deferred.** The 14 Python collectors, dead NPC advisory, and 9 binding categories all ultimately depend on Director's LLM judgment. No structural hard block exists except the quality gate (score < 90 → REJECT). |
| Where do semantic fidelity and identity/institution drift still slip through? | (a) `fact_lock_institution` is in binding scope but can only trigger PASS_WITH_FIX, not REJECT. (b) `fact_lock_location`, `fact_lock_item`, `fact_lock_provenance` are CRITICAL but outside binding scope — they go through advisory-only path. (c) `tactical_semantic_fidelity` is in binding scope but checks only one narrow pattern (unauthorized intrusion events). Broader semantic drift (mission dilution, identity softening, arc-focus erosion) has no Python detector at all and depends entirely on Director's LLM judgment. |

---

## 5. Stop

read-only lane complete; no files mutated
