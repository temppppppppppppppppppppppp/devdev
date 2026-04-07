# Lane 2: Stage3 Blueprint Carryover / Opening Pin Intake

Date: 2026-04-06
Lane Owner: Terminal 2
Status: complete
Authority: `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md`

## 1. Scope

Primary question: does Stage3 merely pass through Stage2 pressure, or does it add new opening-hardening behavior of its own?

## 2. Files Inspected

| File | Purpose |
|------|---------|
| `modules/core/stage3_orchestrator.py` | Stage3 batch blueprint orchestration |
| `modules/core/continuity_pin_guard.py` | Deterministic continuity pin logic |
| `modules/domain/agents/blueprint_ensemble.py` | Blueprint LLM prompt construction including constraint formatting |
| `modules/domain/agents/blueprint_constraint_compiler.py` | Constraint block compilation (Stage2 arc_data → structured constraint_block) |
| `modules/domain/agents/three_phase_blueprint_runtime.py` | ThreePhase generate pipeline, constraint_block resolution |
| `modules/core/stage4_orchestrator.py` L860-920 | Stage4 preflight pin application (downstream consumer for Stage3-produced pins) |
| `modules/core/stage4_interview_round.py` L190-217, L5005-5067 | Stage4 pin metadata consumption |
| `tests/test_continuity_pin_guard.py` | Pin guard unit tests |
| `tests/test_stage3_orchestrator.py` L1363-1376 | Unresolved pin test |
| `tests/test_stage2_stage3_semantic_carryover_guardrail.py` | Semantic carryover quarantine tests |
| `tests/test_stage2_stage3_episode_boundary_guardrail.py` | Episode boundary state_changes filtering |

## 3. Evidence

### E-1: Stage3 Orchestrator Has No Native Fatigue/Recovery/State-Lock Logic

Grep for `opening`, `recovery`, `fatigue`, `physical_state`, `carryover`, `must_start`, `state_lock`, `피로`, `회복`, `부상`, `자연치유`, `natural heal` in `stage3_orchestrator.py` returns **zero matches** (except one `constraint_summary` containing `회복` in test data at L903, which is a plot keyword, not a system keyword).

Stage3 Orchestrator code contains:
- No reference to `recovery_scene_required`
- No reference to `must_start_with`
- No reference to `physical_state`
- No reference to `chain_link`
- No genre-specific fatigue/injury logic
- No opening-hardening beyond the continuity pin guard

**Conclusion**: Stage3 Orchestrator itself adds **zero** new fatigue/recovery/state-lock hardening.

### E-2: `apply_continuity_pins()` — The Only Stage3-Native Deterministic Patch

The continuity pin guard (`continuity_pin_guard.py`) operates on **three pin types only**:

1. **`proper_noun_pin`** (L154-172): fixes quoted-token mismatches between previous published text and blueprint. Genre-agnostic. No fatigue/recovery relevance.

2. **`elapsed_time_pin`** (L175-185): fixes time-surface mismatches between arc tactical text and blueprint. Genre-agnostic. No fatigue/recovery relevance.

3. **`opening_action_continuity_pin`** (L188-203): detects when previous episode ended with explicit non-stop exit motion (patterns: `멈추지 않`, `걸음을 멈추지 않`, `현관문을 향해 나아`, `등 뒤로 흘려보냈`, `손잡이를 단단히 움켜쥐`, `외면했`, `무시했`) **AND** the new blueprint opens with reversal (patterns: `걸음을 멈췄`, `몸을 돌`, `마주 보`, `서재로 와라`, `서재를 향해`, `뒤를 따라`) **AND** father-call patterns appear in both.

This third pin is narrowly scoped to a specific **father-call + exit-reversal** scenario (investment/family drama). It produces a **change annotation** on the blueprint, not a rejection. The pin's behavior:
- Does NOT reject the blueprint
- Does NOT force an opening rewrite
- Annotates `_continuity_pins` list on the blueprint for downstream consumption
- Stage4 reads this annotation as `contradiction_types: ["opening_action_continuity"]` in the post-select fix flow (not preflight reject)

**Confidence: 99%** — this is a textual annotation, not a hard gate.

### E-3: `_continuity_pins` Flow Through Stage4

Stage3 writes `_continuity_pins` and `_continuity_pin_unresolved` onto the blueprint dict. Stage4 consumes these in two places:

1. **Stage4 Preflight** (`stage4_orchestrator.py` L910-920): Stage4 independently re-runs `apply_continuity_pins()` on the same blueprint with its own previous manuscript lookup. If pins change, it patches the blueprint and writes new `_continuity_pins`. This is a **redundant re-application**, not an amplification of Stage3 pins.

2. **Stage4 Interview Round** (`stage4_interview_round.py` L190-217, L5037-5055): `_extract_opening_continuity_pin_metadata()` reads `_continuity_pins` from the blueprint and extracts `opening_action_continuity_pin` entries into `contradiction_types` and `contradiction_details`. These are merged into the `_post_select_conflict_contract` which feeds the Chief Writer's fix-pack, not a hard-reject gate.

**Conclusion**: Stage3's pin annotations are informational metadata, not hard-fail signals. Stage4 consumes them as fix guidance, not rejection criteria.

### E-4: `BlueprintConstraintCompiler._extract_inherited_state()` — The Actual Injury Carryover Path

The `_extract_inherited_state()` method (`blueprint_constraint_compiler.py` L491-549) is called during Stage3's constraint block compilation (`three_phase_blueprint_runtime.py` L269). This is where physical state enters the blueprint generation prompt:

- Default: `injuries: "없음"` (none)
- Sources: `arc_data.status_shadow.expected_injuries`, `arc_data.state_constraints.arc_start_state.injuries`, `prev_blueprint.protagonist_state.injuries`
- Non-wuxia already receives a partial carveout: `internal_energy` is excluded for non-wuxia genres (L493-496, L514-516, L530-532) — tagged `[TF-41] P1-1`

However, **injuries are genre-agnostic** — a non-wuxia work with `status_shadow.expected_injuries = "가벼운 피로"` will have that carried forward with the same weight as a wuxia work with `"심각한 내상"`.

### E-5: 4-Tier Authority Banding in `_format_constraints()`

The constraint formatting in `blueprint_ensemble.py` (`_format_constraints()` L898-1078) places injury/state data at:

| Band | Label | Injury-Related Content | Prompt Framing |
|------|-------|----------------------|----------------|
| 1 IMMUTABLE | 확정 사실, 변경 불가 | None | — |
| 2 HARD CONSTRAINT | 필수 준수, 위반 시 REJECT | `arc_constraint_summary` (from Stage2 `constraint_summary`) | "MUST NOT DRIFT" |
| 3 EXPECTED CONTINUITY | 계승 필수, 불일치 시 경고 | `inherited_state.injuries`, `inherited_state.mood` | `[계승 상태] 부상: ...` |
| 4 ADVISORY | 참고용, 필수 아님 | `permanent_injuries`, `semantic_carryover` | `[상태 변경 요약]` |

The Band 3 placement means that **injuries are presented as expected continuity, not hard-fail canon**. However, if Stage2's `constraint_summary` encodes recovery pressure (e.g., "회복 장면 필수"), that would land at **Band 2 HARD CONSTRAINT** with "MUST NOT DRIFT" framing — a significantly higher authority level.

### E-6: `_format_prev_blueprint_carryover()` — Blueprint-to-Blueprint Injury Persistence

When previous blueprints are carried over to the LLM context (`blueprint_ensemble.py` L1280-1360), `protagonist_state.injuries` is rendered under `[주인공상태]` with format `부상:{text}`. This is display-context only — not a constraint band. However, the surrounding text at L1377 says:

> "이전 에피소드의 구조화된 계승 정보입니다. 모순되는 내용을 절대 생성하지 마세요."

This Korean instruction translates to: **"This is structured carryover information from previous episodes. You must NEVER generate content that contradicts this."** This is a strong LLM-direction that could turn a descriptive injury field into an implicit hard constraint.

### E-7: Test Codification

- `test_continuity_pin_guard.py`: 3 tests covering proper_noun_pin, elapsed_time_pin, opening_action_continuity_pin. All tests verify **annotation** behavior, not rejection. No test enforces injury/recovery/fatigue hardening.
- `test_stage3_orchestrator.py` L1363-1376: `test_unresolved_continuity_pins_do_not_discard_blueprint` — explicitly tests that unresolved pins do NOT cause blueprint rejection. This is a healthy test.
- `test_stage2_stage3_semantic_carryover_guardrail.py`: Tests that `continuity_checkpoints` and `growth_justification` are suppressed from semantic_carryover (arc-end state quarantine). No recovery/fatigue test coverage.
- `test_stage2_stage3_episode_boundary_guardrail.py`: Has one injury reference (`팔 부상` at L60) as test data, not as an assertion about hardening behavior.

## 4. Findings

### Finding 1: Stage3 Is a Passive Carrier, Not an Active Overreach Amplifier

Stage3 Orchestrator code adds **zero** fatigue/recovery/state-lock hardening logic. It does not reference physical state, recovery scenes, or opening recovery obligations. The constraint_summary from Stage2 flows through Stage3 as a transparent passthrough to the constraint compiler, which places it at Band 2 (HARD CONSTRAINT).

**Severity: N/A for Stage3 code itself.**

### Finding 2: The Continuity Pin Guard Is Narrowly Scoped and Non-Blocking

The only Stage3-native continuity mechanism (`apply_continuity_pins`) is:
- Limited to 3 pin types (proper noun, elapsed time, opening action reversal)
- Operates on text-matching, not semantic state
- Produces annotations, not rejections
- Has no genre awareness
- Has no fatigue/recovery/injury awareness

The `opening_action_continuity_pin` is the closest to "opening hardening" but is narrowly specific to father-call + exit-reversal scenarios and produces metadata, not hard-fail.

**Severity: P3** — the pin guard is correctly designed as non-blocking.

### Finding 3: The Real Overreach Surface Is the Constraint Compiler + Prompt Framing

The actual overreach risk in the Stage3 supply chain lives in two places:

1. **`BlueprintConstraintCompiler._extract_inherited_state()`**: Injuries are carried over genre-agnostically. A non-wuxia "가벼운 피로" is treated with the same structural weight as a wuxia "내상". The `[TF-41]` carveout only addresses `internal_energy`, not injury/fatigue severity classification.

2. **`_format_constraints()` Band assignment**: Injuries land at Band 3 (EXPECTED CONTINUITY), which is appropriate. But `constraint_summary` from Stage2 (which may encode recovery pressure) lands at Band 2 (HARD CONSTRAINT, "MUST NOT DRIFT"). If Stage2 writes `constraint_summary: "회복 장면 필수"` for a non-wuxia work, Stage3 carries this as a hard constraint without genre normalization.

3. **Prev blueprint carryover prompt**: The instruction "모순되는 내용을 절대 생성하지 마세요" (never generate contradictory content) applied to `protagonist_state.injuries` could cause the LLM to treat mild fatigue persistence as an immutable fact.

**Severity: P2** — meaningful overreach potential via prompt framing, but this is a constraint-compiler / prompt-builder surface, not a Stage3 Orchestrator surface.

### Finding 4: Stage3 Has a Clean Seam for Future Normalization

Because Stage3 Orchestrator is genuinely passive on this axis:
- No code changes needed in `stage3_orchestrator.py` itself
- The constraint compiler (`blueprint_constraint_compiler.py`) has a clear `_extract_inherited_state()` method that could add injury-severity classification
- The prompt formatter (`blueprint_ensemble.py`) has explicit band labels where injury severity could be downgraded from Band 3 to Band 4 for non-critical, non-wuxia conditions
- The `[TF-41]` pattern (internal_energy genre carveout) is an existing precedent for genre-aware state filtering

## 5. Open Questions

1. **Does Stage2 actually produce `constraint_summary` values that encode recovery obligations for non-wuxia works?** (Lane 1 should answer this — if Stage2 never encodes recovery pressure in `constraint_summary`, the Band 2 hard-constraint path is theoretical.)

2. **Does `status_shadow.expected_injuries` or `state_constraints.arc_start_state.injuries` ever contain soft-fatigue descriptions for non-wuxia works?** (Lane 1 should answer this — the constraint compiler passthrough is genre-blind.)

3. **Is the "모순되는 내용을 절대 생성하지 마세요" instruction in prev-blueprint carryover actually causing LLM over-compliance with mild fatigue persistence?** (Lane 5 runtime evidence should answer this.)

## 6. Provisional Severity

| Surface | Severity | Confidence |
|---------|----------|------------|
| Stage3 Orchestrator code | N/A (no native hardening) | 99% |
| `apply_continuity_pins()` | P3 (annotation-only, correctly non-blocking) | 99% |
| `BlueprintConstraintCompiler._extract_inherited_state()` — genre-blind injury passthrough | P2 | 95% |
| `_format_constraints()` Band 2 placement of `constraint_summary` | P2 (if Stage2 writes recovery pressure) | 90% — depends on Lane 1 findings |
| Prev-blueprint carryover prompt wording | P2-P3 (implicit hardening via LLM instruction) | 85% — depends on Lane 5 runtime evidence |

**Overall Stage3 supply chain severity: P2** — Stage3 is a passive carrier with no native overreach, but the constraint compiler and prompt formatting within its supply chain can amplify Stage2 producer-side overreach without genre normalization.

## 7. Recommended Merge Notes

- Stage3 Orchestrator itself is **clean** — no implementation changes needed there.
- The constraint compiler's `_extract_inherited_state()` is the most actionable normalization seam: add an injury/fatigue severity classifier that downgrades non-critical, non-wuxia conditions from the `injuries` field to an advisory annotation.
- The `[TF-41]` internal_energy genre carveout pattern is a direct precedent for this normalization.
- The prev-blueprint carryover instruction ("절대 생성하지 마세요") should be reviewed — it may need qualification for soft-state fields like mood/fatigue.
- Stage3's `_continuity_pins` annotation pattern is well-designed and should not be changed.
- The Band 2 placement of `constraint_summary` is correct in general, but if Stage2 encodes soft-fatigue recovery pressure in this field, the fix belongs at the **producer side** (Stage2), not in Stage3's passthrough.

---

3-Pass Audit Record:

Pass 1: Structure and scope verified against Lane 2 order requirements. All 7 required sections present.

Pass 2: File paths verified against live workspace. Evidence items cross-referenced with line numbers. No overclaim beyond inspected code.

Pass 3: Findings are operationally actionable. Open questions are bounded and directed to correct lanes. Severity assessments include confidence levels.

Estimated confidence: 96%
