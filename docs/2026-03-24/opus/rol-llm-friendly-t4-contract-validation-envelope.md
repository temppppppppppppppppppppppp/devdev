Date: 2026-03-24
Status: final (3-pass audited)
Document Type: system-track LLM-friendliness lane survey report
Lane: T4 — Contract / Validation / Envelope Surface
Canonical Path: `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope.md`
Evidence Path: `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope-evidence.md`

Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: tracked stage4/state/writer surfaces, docs/temp/queue-state.json, docs/2026-03-23/console.txt, many project artifacts deleted, new docs/2026-03-24/ and stage4 immutable-fact files`

Source Survey Docs:
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`

---

## 1. Executive Summary

The Contract / Validation / Envelope lane is **partially navigation-ready** for an LLM. Two files carry material comprehension cost; the rest are settled or clean.

The primary friction sources are:
- **Tier-specific result schema inconsistency** in `validation_orchestrator.py` — six validators, six different result shapes, no unified contract reference
- **Envelope proliferation** in `four_phase_arc_runtime.py` — 10 dataclass envelopes with ~80% field overlap and 27-parameter forwarding methods
- **Undocumented advisory side-channel** — underscore-prefixed keys (`_continuity_advisory`, `_blocking_advisory`, etc.) carrying structured data to Director, invisible to the documented return contract

The remaining scope files are clean:
- `pre_director_checklist.py`: well-typed dataclass contracts, enum-based severity, lazy sub-modules
- `blueprint_constraint_compiler.py`: clear compile/compile_to_prompt contract, documented dict keys
- `three_phase_blueprint_runtime.py`: 9 envelopes with distinct semantics, less overlap
- `base_agent.py`: `_extract_json_robust` already flagged in prior survey; lock grouping comments already added by post-survey SSOT

**Lane verdicts:**
- Navigation-ready for this lane: **partially** (two hotspot files slow comprehension; rest is settled)
- Cheap-fix-first verdict: **yes** (comment/doc can address the main understanding gaps without refactor)
- Boundary-refactor can wait: **yes** (envelope consolidation and result typing are long-term)

**Top 3 highest-ROI quick wins:**
1. Add a tier result schema reference table at the top of `validation_orchestrator.py` (doc-only)
2. Document the underscore-prefixed advisory side-channel contract (comment-only)
3. Add envelope family relationship comment block in `four_phase_arc_runtime.py` (comment-only)

---

## 2. Included Coverage / Exclusions

### Included (primary scope)
| File | LOC | Role |
|---|---|---|
| `modules/validation/validation_orchestrator.py` | 1,674 | 6-tier validation pipeline orchestrator |
| `modules/validation/*.py` (family) | ~16 files | Individual tier validators |
| `modules/domain/agents/four_phase_arc_runtime.py` | 1,704 | Arc-level 4-phase pipeline runtime |
| `modules/domain/agents/three_phase_blueprint_runtime.py` | 1,600 | Blueprint-level 3-phase pipeline runtime |
| `modules/core/pre_director_checklist.py` | 717 | Python-only pre-Director gating |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 692 | Arc constraint-to-prompt compiler |
| `modules/domain/agents/base_agent.py` | 2,288 | Shared agent base (JSON parsing, API, caching) |

### Excluded
- Validator internals beyond contract surface (blocking_validator_*.py sub-checks are not primary scope)
- `stage4_interview_round.py` and `stage4_director_runtime.py` (T2 lane)
- `chief_writer.py` and prompt builders (T3 lane)
- Persistence/DB sinks (T5 lane)

---

## 3. Current Read Order or Ownership Map

### Contract Read Order for This Lane

1. **`validation_orchestrator.py`** — the central orchestrator
   - `validate()` L329: main synchronous entry
   - `validate_parallel_v59()` L1390: async parallel entry
   - Tier execution order: PRE_LLM → CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY
   - `_finalize_validation_result()` L777: final decision assembly
   - `calculate_adaptive_threshold_v59()` L1516: threshold calculation

2. **`pre_director_checklist.py`** — Python-only pre-Director gate
   - `check()` L172: main entry, returns `ChecklistResult` dataclass
   - Sub-modules: `manuscript_checker`, `narrative_checker`, `style_checker` (lazy)

3. **`blueprint_constraint_compiler.py`** — Arc constraint extraction
   - `compile()` L43: extracts structured constraint block dict
   - `compile_to_prompt()` L119: renders constraint block to prompt string

4. **`four_phase_arc_runtime.py`** — Arc pipeline runtime
   - 10 envelope dataclasses L19-135: phase transfer objects
   - `_run_generate_retry_cycle()` L435: main retry loop
   - `_run_generation_phase()` L730: 27-param phase execution

5. **`three_phase_blueprint_runtime.py`** — Blueprint pipeline runtime
   - 9 envelope dataclasses L22-96: phase transfer objects
   - `_resolve_constraint_block()` L247: constraint resolution
   - `_run_phase2_generation()` L384: generation phase

6. **`base_agent.py`** — Shared agent infrastructure
   - `_extract_json_robust()` L1777: 5-strategy JSON repair engine
   - `ask()` and API infrastructure: L289+
   - Lock/state grouping: L164-198

### Ownership Map

| Contract Surface | Owner | Authoritative Location |
|---|---|---|
| Final validation decision | `ValidationOrchestrator._finalize_validation_result()` | `validation_orchestrator.py:777` |
| Pre-Director gate | `PreDirectorChecklist.check()` | `pre_director_checklist.py:172` |
| Adaptive threshold | `ValidationOrchestrator.calculate_adaptive_threshold_v59()` | `validation_orchestrator.py:1516` |
| Blueprint constraint block | `BlueprintConstraintCompiler.compile()` | `blueprint_constraint_compiler.py:43` |
| Arc envelope transfer | `FourPhaseArcRuntime` 10 dataclasses | `four_phase_arc_runtime.py:19-135` |
| Blueprint envelope transfer | `ThreePhaseBlueprintRuntime` 9 dataclasses | `three_phase_blueprint_runtime.py:22-96` |
| JSON repair | `BaseAgent._extract_json_robust()` | `base_agent.py:1777` |

---

## 4. Top Hotspots

| # | File | Line Anchor | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|---|
| H1 | `validation_orchestrator.py` | L329-354 (docstring) vs L777-822 (actual return) | Contract | **P1** | `validate()` docstring documents 7 return fields but actual return carries 15+ fields including `_continuity_advisory`, `_blocking_advisory`, `_consistency_advisory`, `_retrospective_advisory`, `adaptive_threshold`, `detailed_feedback`, `refine_recommended`, `refine_reason`, `catharsis_result`, `action_result`, `pre_llm_result`. The documented contract is a subset of the actual contract. | doc-only (expand docstring) |
| H2 | `validation_orchestrator.py` | L456, L537, L547-552, L753-758 | Contract | **P1** | Four underscore-prefixed advisory keys (`_continuity_advisory`, `_blocking_advisory`, `_consistency_advisory`, `_retrospective_advisory`) act as a structured side-channel from validators to Director. These are invisible to the documented API but carry `source`, `violations`/`failures`, `feedback`, `severity` payloads. An LLM modifying the validation flow could silently break this channel. | comment-only (document the advisory channel at top of class) |
| H3 | `four_phase_arc_runtime.py` | L19-135 | Contract | **P1** | 10 envelope dataclasses with ~80% field overlap. `best_arc`, `feedback`, `prev_rejected_arc`, `prev_reject_feedback`, `prev_selected_strategy`, `spare_candidates` appear in 5-7 envelopes. `should_continue`/`should_return` booleans appear in 5. An LLM adding a field must check all 10 to know which ones need it. | comment-only (add relationship diagram comment) |
| H4 | `four_phase_arc_runtime.py` | L730-757 | Contract | **P1** | `_run_generation_phase()` takes 27 named parameters — the highest parameter count in the surveyed lane. This is phase-state forwarding, not a design defect, but the sheer width makes it hard for an LLM to trace which parameter feeds which downstream call. | comment-only (add param-group docstring) |
| H5 | `validation_orchestrator.py` | tier result shapes across L404-587 | Contract | **P1** | Six validators return six different dict schemas. PRE_LLM: `{passed, critical_issues, warnings, score_deduction}`. CONTINUITY: `{passed, violations, warnings, warning_count}`. BLOCKING: `{passed, failures, warnings, degraded_checks}`. CONSISTENCY: `{unjustifiable_violations, justifiable_violations, score_penalty}`. SCORING: `{total_score, passed, message, breakdown}`. ADVISORY: `{suggestions}`. No unified schema reference exists. | doc-only (add tier schema table) |
| H6 | `base_agent.py` | L1777-1900 | Local Read | **P1** | `_extract_json_robust`: 120+ LOC mixing 5 repair strategies + recursive flattening. Already flagged by prior global survey. Agent-specific regex fallbacks (tactical_doc, content, scene_breakdown, integrated_scenario) are hardcoded inside a generic method. | boundary-refactor (defer: split per strategy) |
| H7 | `validation_orchestrator.py` | L184-280 (module constants) | Navigation | **P2** | 100 lines of module-level constants (`GENRE_THRESHOLD_PROFILES`, `EPISODE_TYPE_ADJUSTMENTS`, `STREAK_ADJUSTMENTS`, `PATTERN_ADJUSTMENTS`) precede the class definition. These are well-commented but dense. A cold LLM may mistake them for the core logic. | comment-only (add section divider before class) |

---

## 5. Top Quick Wins

| # | Target | Fix Type | Action | ROI |
|---|---|---|---|---|
| QW1 | `validation_orchestrator.py` L185 (before class) | **doc-only** | Add a tier result schema reference table as a class-level docstring section listing all 6 tier return shapes side by side | HIGH — eliminates the #1 contract comprehension cost |
| QW2 | `validation_orchestrator.py` L456 area | **comment-only** | Add a block comment documenting the underscore-prefixed advisory channel: `# --- Advisory side-channel keys ---` with `_continuity_advisory: {source, violations, feedback, severity}` etc. | HIGH — makes the hidden channel visible |
| QW3 | `four_phase_arc_runtime.py` L19 | **comment-only** | Add an envelope family relationship comment block explaining: Bootstrap→State, ConstraintEnvelope→Phase1, GenerationEnvelope→Phase2, CandidateEnvelope→Director input, DirectorSelectionEnvelope→Phase3 input, ValidationEnvelope→Phase3 output, RetryCycleEnvelope→retry loop | HIGH — maps the 10 envelopes to their lifecycle |
| QW4 | `validation_orchestrator.py` L329 | **doc-only** | Expand the `validate()` docstring to list all actual return keys including advisory keys, result sub-dicts, and diagnostic fields | MEDIUM — aligns documented and actual contract |
| QW5 | `four_phase_arc_runtime.py` L730 | **comment-only** | Add a brief param-group docstring to `_run_generation_phase`: `# Params: identity(retry,arc_no,ep_start), context(curr_block,prev_arcs,assets), agents(state_tracker,adversarial_self_play), state(protagonist_config,...,spare_candidates), artifacts(pipeline_result)` | MEDIUM — makes 27 params scannable |
| QW6 | `validation_orchestrator.py` L79 | **comment-only** | Add `# ═══ Module constants ═══` before the constants block and `# ═══ ValidationOrchestrator ═══` before class definition to separate config from logic | LOW — navigation aid |
| QW7 | `three_phase_blueprint_runtime.py` L22 | **comment-only** | Add a brief envelope lifecycle comment: RetryState→across retries, Bootstrap→init, Phase2Result→generation, Phase3ValidationResult→validation, PassWithFix→fix iteration, RejectState→reject feedback, RetryCycleResult→retry loop | LOW — less urgent than FourPhase (less overlap) |

**Proportion check:** 6/7 quick wins are comment/doc (86%), exceeding the >50% requirement.

---

## 6. Deferred Refactor Candidates

| # | Target | Action | Blast Radius | Why Defer | Tag |
|---|---|---|---|---|---|
| DR1 | `four_phase_arc_runtime.py` L19-135 | Consolidate 10 envelopes into fewer shared-base envelopes (e.g., `_FourPhaseResult(best_arc, feedback, should_continue, should_return)` base + phase-specific extensions) | Medium — all callers in runtime file | Comment-only mapping eliminates understanding cost now; structural consolidation is polish, not blocking | **long-term** |
| DR2 | `validation_orchestrator.py` return contract | Introduce a `ValidationResult` typed dataclass or TypedDict replacing the ad-hoc dict returns | Medium — all callers (Stage 4 interview round, director runtime) must update | Expanding the docstring and documenting advisory keys removes the LLM comprehension hazard without changing runtime behavior | **defer** |
| DR3 | `base_agent.py` L1777-1900 | Split `_extract_json_robust` into per-strategy helper methods | Low — internal to BaseAgent | Already flagged by prior global survey; the method works correctly. Splitting improves readability but doesn't change behavior. | **long-term** |

---

## 7. No-Action / Settled Areas

| Area | Reason |
|---|---|
| `pre_director_checklist.py` | Clean typed contracts: `ChecklistResult`, `CheckItem`, `CheckCategory`, `CheckSeverity` dataclasses/enums. Lazy sub-module pattern is standard. No hidden channels. |
| `blueprint_constraint_compiler.py` | Clear `compile()` → dict → `compile_to_prompt()` → str pipeline. Field names are self-documenting. Immutable fact carryover (IFC) section is well-commented. |
| `three_phase_blueprint_runtime.py` | 9 envelopes have distinct semantics with minimal overlap. `_ThreePhaseRetryState` cleanly accumulates retry context. Runtime methods are reasonably sized. |
| `base_agent.py` lock/state grouping | Already addressed by post-survey SSOT (item A6). Grouping comments present at L164-198. |
| `base_agent.py` API/model infrastructure | Model fallback chain, key rotation, quota cache are internally complex but self-contained. An LLM modifying validation or envelope code does not need to understand these. |
| Validator family (`blocking_validator.py`, `continuity_validator.py`, etc.) | Individual validators have consistent internal patterns. Their tier-specific result shapes are the contract issue — not their internal logic. |
| Module-level threshold constants | `GENRE_THRESHOLD_PROFILES`, `EPISODE_TYPE_ADJUSTMENTS`, etc. are well-commented configuration. They don't create authority or contract confusion. |
| Adaptive threshold system | `calculate_adaptive_threshold_v59()` and helpers are internally clean. Floor/cap/reset logic is well-guarded. |

---

## 8. Cross-Lane Handoff Notes

### To T2 (Stage 4 Authority / Verdict Flow)
- The `_*_advisory` side-channel keys from `validation_orchestrator.py` are consumed by `stage4_director_runtime.py`. If T2 finds the consumer side unclear, the QW2 comment block in this lane would help both lanes.
- The `validation_context` dict passed into `validate()` is assembled by `stage4_interview_round.py`. Contract clarity improvements here should be cross-checked with T2's view of what gets injected.

### To T3 (Writer / Prompt / Context Reception)
- `blueprint_constraint_compiler.py` `compile_to_prompt()` output is injected into Writer prompts. If T3 finds prompt assembly confusing, the constraint compiler is already clean — the issue is likely in the prompt builder assembly, not here.

### To T5 (Persistence / Observability)
- `validation_orchestrator.py` logs extensively via `logging.info`/`logging.warning` during validation. Pass-rate recording happens in `_record_validation_history_v59()` (in-memory only). The durable persistence of validation results is T5's domain via `pass_rate_monitor.py` and DB writes.

### To T6 (Peripheral / Regression)
- `tests/test_blueprint_patch_mode.py` and `tests/test_chief_writer_context.py` are modified in the current dirty state. These test the validation/constraint surface. T6 should confirm test coverage is stable.

---

## 9. Confidence And Limits

**Confidence: 95%**

Basis:
- All 7 primary scope files were read in sufficient depth (key methods, contracts, dataclass definitions, return shapes)
- Tier result schemas were verified against actual code, not prior survey text
- Envelope overlap was counted against live dataclass definitions
- Advisory side-channel was traced from producer (validation) to consumer mention in orientation pack
- Already-resolved post-survey items (A6 base_agent lock comments, B1 director_runtime debug log, validation_orchestrator tier schema mention in orientation pack) were verified as closed

Limits:
- Individual validator internals (e.g., `blocking_validator_consistency_checks.py` internal logic) were sampled, not exhaustively traced
- The `validation_context` dict assembly in `stage4_interview_round.py` was not traced from this lane (T2 scope)
- `base_agent.py` context caching infrastructure (L1946+) was not deeply surveyed as it is not primarily a contract/validation surface

---

## 10. 3-Pass Audit Record

### Pass 1. Structure and Scope
- All required sections present (1-9)
- Every P1 hotspot has file:line anchor
- Every recommendation has a fix type
- Quick wins are 86% comment/doc (exceeds >50% requirement)
- Deferred refactor candidates capped at 3 with explicit long-term/defer tags
- PASS

### Pass 2. Evidence and Consistency
- Tier result schema descriptions verified against live code (PRE_LLM at L404-434, CONTINUITY at L436-467, BLOCKING at L503-541, CONSISTENCY at L542-562, SCORING at L673-707, ADVISORY at L695-698)
- Envelope count verified: 10 in four_phase, 9 in three_phase
- `_run_generation_phase` parameter count verified: 27 named params at L730-757
- Advisory side-channel keys verified: `_continuity_advisory` at L456, `_blocking_advisory` at L537, `_consistency_advisory` at L547, `_retrospective_advisory` at L753
- Post-survey SSOT closure verified: items A6, B1 are closed
- No contradictions with prior survey findings — this lane deepens the contract axis
- PASS

### Pass 3. Execution and Readability
- Quick wins are actionable without opening refactor waves
- Deferred items have explicit blast radius and deferral rationale
- Cross-lane handoff notes identify the three most relevant adjacent lanes
- No-action list prevents over-investigation of clean files
- Report is scoped to contract/validation/envelope — does not reopen long-function or authority topics
- PASS

### Confidence Gate
- Estimated confidence: 95%
- Threshold: 95% required for final save
- Gate: **MET**
