# Stage234 Terminal 3: Stage4 Consumer / Manuscript Handoff Survey

Date: 2026-04-07
Status: final
Document Type: read-only parallel survey output
Track: system
Terminal: 3
Lane Owner: Stage4 consumer / manuscript handoff harness
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread narrative/output/docs deltas`
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

Terminal 3 lane-specific reads:

- `modules/core/stage4_orchestrator.py` (top-level entry, `_prepare_current_episode_inputs`, `_build_episode_prompt_bundle`, `stage_4_v2_chief_writer`)
- `modules/core/stage4_context_builder.py` (TypedDict payloads, `_build_episode_base_payload`, `_build_episode_state_payload`, `_build_mandatory_context_payload`, `_build_mandatory_context_seed`, `_build_numeric_carryover_authority_block`, work identity authority injection)
- `modules/core/stage4_context_packets.py` (continuity NPC/relationship/fact sections, continuity packet rendering)
- `modules/core/stage4_context.py` (DI container, `from_app` factory, callback property delegation)
- `modules/core/stage4_interview_round.py` (`_build_post_select_conflict_contract`, retry advisory tagging, blueprint UI contamination sanitization, `_handle_reject`)
- `modules/core/pre_director_manuscript_checker.py` (dialogue ratio, scene reflection, cliche density, scene header contract — all advisory-only)
- `modules/core/stage4_post_pass_runtime.py` (`_build_state_truth_owner_contract`, `_build_numeric_carryover_authority_visibility`, `_merge_storage_only_state_change_families`, `_submit_manager_async`, `_memorize_and_validate`, `_collect_manager_and_build_delta`)
- `modules/domain/agents/chief_writer_context.py` (`build_common_context`, `_build_writer_core_sections`, `_extract_blueprint_sections`, `_build_world_state_section`)
- `modules/domain/agents/chief_writer_prompts.py` (`build_chief_writer_main_prompt` — full template with authority hierarchy)
- `modules/domain/agents/chief_writer_quality.py` (`sanitize_leakage`, `_extract_content_text`)
- `modules/domain/agents/manuscript_validator.py` (`validate_candidate`, length/scene/continuity/keyword checks — advisory-only)
- `modules/core/stage4_post_processor.py` (`process_pass_result` — primary DB save → quality sidecars → post-pass pipeline → session finalization)

### Intentionally excluded

- Stage2 production internals (Terminal 1 scope)
- Stage3 compiler/validator/blueprint generation internals (Terminal 2 scope)
- Cross-stage vocabulary matrix construction (Terminal 4 scope)
- DB schema or JSONL sink structure deep dives
- Narrative artifact content inspection

## 2. Findings

Ordered by severity, highest first.

### F-1. Blueprint truth arrives at Stage4 as structured dict but is flattened into prose for the writer (severity: high, classification: stage-local)

**Evidence:**
- `stage4_orchestrator.py:1137` — blueprint arrives as `self.ctx.current_project.get_blueprint(next_ep)`, which is a structured dict from `db.get_blueprint()`.
- `stage4_context_builder.py:2424-2427` — `arc_tactical` is read as `arc_data.get("tactical_doc")` and immediately cast to string. If it is a dict, it is `json.dumps`-ed.
- `chief_writer_context.py:286-308` — `_extract_blueprint_sections()` converts `scene_breakdown` dict to `json.dumps(scenes, ensure_ascii=False, indent=2)` for prompt injection. `integrated_scenario_advisory` is wrapped in a markdown header block with explicit de-prioritization language ("낮은 우선순위").
- `chief_writer_prompts.py:96-149` — `build_chief_writer_main_prompt()` assembles the Writer prompt with an explicit `[STEP 0.5: 권위 우선순위]` hierarchy. Structured scene breakdown is at tier 3, below Opening Anchor and Immutable Facts.

**Impact:** The blueprint's machine-readable constraints (NPC roster, scene structure, constraint_summary, ending_hook) are serialized into prompt text where the LLM Writer must re-parse them from prose. Scene-level enforcement depends on the Writer's compliance, not a structured contract. The hierarchy is well-intentioned but enforcement is advisory — no machine-readable gate blocks the Writer from contradicting scene_breakdown fields.

### F-2. Post-pass state truth persists across three partially independent surfaces without autonomous baseline promotion (severity: high, classification: stage-local)

**Evidence:**
- `stage4_post_pass_runtime.py:128-216` — `_build_state_truth_owner_contract()` explicitly maps five field families: `actual_truth_surface` (Manager), `final_state_updates` (Director), `inventory_counts` (runtime overlay), `relationship_changes` (runtime overlay), `npc_martial_state_changes` (arc-state world-only), `active_pressure_vectors` (runtime blueprint overlay), and `numeric_carryover_authority` (fact ledger baseline).
- `stage4_post_pass_runtime.py:208-216` — the contract is versioned (`stage4_state_truth_owner_contract_v1`) but carries no autonomous promotion logic. It only records which source currently owns which field family.
- Active temp execution roadmap lines 45-46 — confirm the surviving seam is "numeric carryover baseline-promotion / owner-boundary", meaning manuscript-proven numeric changes still do not autonomously promote into the next carryover baseline.

**Impact:** After PASS settlement, the next episode's context builder reads the `fact_ledger` carryover baseline, but a legitimately changed numeric value from the just-PASS'd manuscript can trigger false-positive contradiction-firewall retry pressure because the baseline was not promoted. This is the sharpest still-live consumer-local seam and matches the active queue front.

### F-3. Pre-Director checks are purely advisory with no Stage4-owned structural gate on scene fidelity (severity: medium, classification: stage-local)

**Evidence:**
- `pre_director_manuscript_checker.py:1-9` — docstring explicitly states "PreDirectorChecklist에서 분리된 5개 원고 관련 체크".
- `pre_director_manuscript_checker.py:259` — `[TF-51] FAIL→WARNING`: even high-impact zone scene non-reflection was downgraded from FAIL to WARNING because of Python keyword-matching false positives. Director LLM judgment is now the sole enforcement.
- `manuscript_validator.py:1-7` — docstring explicitly states "중요: REJECT 권한 없음! 경고만 생성하여 Director에게 '집중 검토 포인트'로 전달."

**Impact:** Scene fidelity is checked by Python keyword matching (coarse) and then delegated to the Director LLM. If the Director LLM does not catch a scene omission, there is no fallback structural gate. This is by design ("Director 주권주의") but means Stage4 has no machine-readable scene-contract enforcement between blueprint intake and manuscript output.

### F-4. Repair loop compensates for intake weakness: post-select conflict contract is synthesized at reject time, not at intake time (severity: medium, classification: boundary-local Stage3→Stage4)

**Evidence:**
- `stage4_interview_round.py:127-187` — `_build_post_select_conflict_contract()` is constructed from `conflicts` list at reject/retry time. It parses conflict lines by `"]"` splitting to extract type and detail.
- `stage4_interview_round.py:130-134` — `target_kind` and `bounded_local_fix_hint` are only attached when the caller has already identified a local-fixable conflict. The contract structure is adequate but constructed reactively.
- `stage4_interview_round.py:190-217` — `_extract_opening_continuity_pin_metadata()` reads `_continuity_pins` from blueprint — a Stage3-emitted structured field that does survive as machine-readable metadata.

**Impact:** The repair contract is synthesized from reject-time conflict text rather than from a pre-computed intake contract. This means the Stage4 repair loop must re-derive contradiction types and fix scopes from free-text analysis, which introduces classification instability across retry rounds. The `_continuity_pins` field is a positive exception where Stage3 does emit structured metadata that survives intake.

### F-5. Writer prompt budget trimming can silently drop mandatory context sections (severity: medium, classification: stage-local)

**Evidence:**
- `stage4_orchestrator.py:61-99` — `_fit_mandatory_context_budget()` splits mandatory context by `\n[` section markers and drops sections from the tail when over budget. `removed_count` and `removed_chars` are tracked but the caller determines whether to log/report the loss.
- `stage4_orchestrator.py:49-57` — `_trim_mandatory_context_for_budget()` uses `smart_truncate` with 55% head preservation, losing the tail when fallback is used.

**Impact:** Tier-0 authority sections (Opening Anchor, Immutable Facts, Work Identity Authority) are placed at the head of mandatory context, so they are most likely preserved. But later sections (tier-1/tier-2 continuity packets, relationship trajectories, numeric fact history) can be silently dropped under budget pressure without a structured record of what was lost. This is a bounded risk because the system does track section removal counts.

### F-6. Stage4ContextBuilder injects work identity authority and numeric carryover authority as structured packets, but downstream consumption is still prompt-only (severity: low, classification: stage-local)

**Evidence:**
- `stage4_context_builder.py:950-985` — Work Identity Authority block builds `tracking_slots`, `mandatory_scene_engines`, `registry_profiles`, linked authority entities, and `active constraint spine` into a text block under `[Stage4 Work Identity Authority]`.
- `stage4_context_builder.py:1006-1059` — Numeric Carryover Authority block reads from `fact_ledger.get_numbers()` where `authority_scope == carryover_baseline`, constructs a text block under `[Stage4 Numeric Carryover Authority]`, and includes an explicit instruction: "do not overwrite these baselines with arc or blueprint target numbers unless the manuscript explicitly shows the bridge transaction".
- `chief_writer_context.py:546-556` — `_extract_named_context_block()` re-surfaces the work identity authority block at the head of `writer_hard_canon_section`.

**Impact:** These are the strongest remaining structured-to-prompt bridges in Stage4 intake. They successfully elevate Stage2/3 authority into tier-0 writer canon. However, the consumption remains LLM-prompt-only — there is no machine-readable gate that blocks the Writer from ignoring these authority packets. This is the expected design under "Director 주권주의" but represents the ceiling of current structured enforcement.

## 3. Authority / Loss Map

| Authority Surface | Actual Consumer Surface | Loss/Compression Point |
|---|---|---|
| `db.get_blueprint(ep_num)` — structured dict with `scene_breakdown`, `integrated_scenario`, `ending_hook`, `_continuity_pins` | `chief_writer_prompts.build_chief_writer_main_prompt()` — flattened into f-string prompt text with explicit authority hierarchy | `chief_writer_context._extract_blueprint_sections()` — `scene_breakdown` serialized via `json.dumps`, `integrated_scenario` wrapped with de-prioritization header |
| `arc_data.tactical_doc` — Stage2 mission prose | `stage4_context_builder._build_episode_base_payload()` — `arc_tactical` as string | Identity transport (dict → `json.dumps`, else passthrough). No semantic loss but no structured enforcement. |
| `fact_ledger.get_numbers()` carryover baselines | `stage4_context_builder._build_numeric_carryover_authority_block()` → tier-0 prompt text | Survives as structured prompt packet. Loss point: no autonomous post-pass promotion after manuscript-proven change. |
| `state_truth_owner_contract` — explicit field/owner/surface mapping | `stage4_post_pass_runtime._build_state_truth_owner_contract()` → persisted in `episode_bible` and `state_log` | Survives as structured metadata. No consumption-time enforcement — serves as provenance record, not as a runtime constraint. |
| Director `final_state_updates` + Manager `actual_truth` + runtime overlays | `stage4_post_processor.process_pass_result()` → DB persistence across `manuscripts`, `state_logs`, `episode_bibles`, `world_state`, `fact_ledger` | Three semi-independent truth surfaces persist without a unified owner boundary. `_merge_storage_only_state_change_families()` does patch merge but does not reconcile authority conflicts. |
| `_continuity_pins` (Stage3 structured emission) | `stage4_interview_round._extract_opening_continuity_pin_metadata()` → contradiction type/detail for reject-time repair | Survives as structured metadata through the full reject→retry path. This is the strongest Stage3→Stage4 structured handoff example. |
| Pre-Director manuscript checks (scene reflection, cliche, dialogue ratio, scene header) | Director LLM receives these as advisory focus points | All checks are advisory-only with no REJECT authority. High-impact zone check was further downgraded from FAIL to WARNING per `[TF-51]`. |

## 4. Non-Issues

- **Blueprint JSON transport is intact.** `db.get_blueprint()` returns a well-formed dict. There is no JSON corruption, schema invention, or silent fallback at the Stage3→Stage4 boundary. The concern is semantic flattening at prompt assembly, not transport integrity.

- **Stage4Context DI container is well-structured.** `stage4_context.py` implements a clean DI container with explicit slot declarations, callback property delegation via `_stage4_context_budget_meta`, and `from_app()` factory. The owner surface is clear and modular. The existing 2026-04-07 parked Stage4InterviewRound owner-surface-reduction SSOT is a structure-first future lane, not a live runtime blocker.

- **Writer prompt authority hierarchy is explicit and well-ordered.** The `[STEP 0.5: 권위 우선순위]` block in `chief_writer_prompts.py` correctly ranks Opening Anchor > Immutable Facts > structured scene breakdown > advisory prose > feedback/constraints. This is not a debt — it is a functional design with known enforcement limits.

- **Budget trimming tracks section removal counts.** `_fit_mandatory_context_budget()` returns `removed_count` and `removed_chars`, so the caller can detect and log budget-driven context loss. This is adequate observability for a prompt budget system.

- **`_stage3_meta` handoff exists but is thin.** Per `docs/stage_map/interfaces.md` Invariant 3, Stage3 emits `_stage3_meta.quality_risk`, `_stage3_meta.quality_gate_failed`, `_stage3_meta.last_score`. Stage4 can tighten escalation when this metadata is present. This is not a consumer-local gap — it is a Stage3-owned emission breadth decision.

## 5. Owner Verdict

If a future Stage4 consumer-harness wave is promoted:

**Narrowest owner set:**

1. `modules/core/stage4_post_pass_runtime.py` — owns the post-pass state truth owner contract, numeric carryover authority visibility, and the three-surface state persistence merge. The carryover baseline-promotion gap lives here.

2. `modules/core/stage4_context_builder.py` — owns intake authority injection (work identity, numeric carryover, tier-0 mandatory context seed), blueprint-to-prompt assembly, and budget-driven context trimming. The prose-flattening of structured blueprint truth lives here.

3. `modules/core/stage4_interview_round.py` — owns the repair loop (post-select conflict contract synthesis, retry advisory management, reject runtime delegation). The reactive repair-contract construction lives here.

Secondary owner if scope widens to enforcement:

4. `modules/domain/agents/chief_writer_context.py` — owns the Writer prompt assembly, writer hard/soft canon section construction, and blueprint section extraction. The prompt-level enforcement boundary lives here.

## 6. Promotion Signal

`covered-by-existing-queue`

Rationale:

- F-1 (blueprint prose flattening) is explicitly covered by the parked `0_0-stage234-cross-stage-contract-normalization-remediation` lane (Tranche 3: Boundary Transport Tightening) and partially by the active `0_0-stage4-consumer-contract-normalization-remediation` lane (Tranche 4: Intake Authority Protection, which has already landed work identity authority injection).

- F-2 (numeric carryover baseline-promotion gap) is the explicit active front of `0_0-stage4-consumer-contract-normalization-remediation` and matches the roadmap's documented next seam.

- F-3 (advisory-only pre-Director checks) is a design decision under "Director 주권주의", not an unintended gap. If enforcement is desired, it would be a future policy change, not a queue item.

- F-4 (reactive repair contract) is covered by `0_0-stage4-repair-contract-normalization-remediation` (queue position 2), which specifically targets shared repair-contract grammar normalization.

- F-5 (budget-driven context section loss) is bounded and observability-adequate. Not queue-promotion-worthy.

- F-6 (structured-to-prompt-only authority packets) is a natural ceiling of the current "Director 주권주의" design. Further tightening would require architecture decisions beyond the current queue scope.

No new execution SSOT is needed from this lane. All identified debt maps cleanly to existing queue items.

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
