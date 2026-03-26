# Wuxia Combat-Scene Readiness Compact Survey

Date: 2026-03-26
Type: compact static survey (survey-only, no code changes)
Scope: wuxia combat-heavy episode readiness — spatial progression, tactical variation, injury/state carry-forward, tempo, multi-episode fights
Excluded: investment-specific seams, Stage 3 latency optimization, model-switch compatibility

## Findings

### Investigation Question 1: Can Stage 3 produce a valid blueprint for combat-heavy episodes?

**Yes.** Blueprint structure is genre-agnostic.

- `modules/models/blueprint.py` L18-62: Blueprint contains `scene_breakdown`, `integrated_scenario`, `pacing_notes`, `protagonist_state`, `target_beat`, `expected_ending`. No field requires dialogue ratio or scene-type diversity.
- `modules/domain/agents/three_phase_blueprint_runtime.py` L908+: `_run_pass_with_fix_loop()` evaluates by score, not by scene-type composition.
- Director scoring rubric (`modules/domain/agents/director_prompts.py` L118-125): "Blueprint scene coverage (20%)" checks whether designed scenes are uniformly reflected, not whether scenes are dialogue-heavy vs action-heavy.
- No "scene mix enforcement" or "minimum dialogue percentage" exists in blueprint generation, validation, or director audit.

### Investigation Question 2: Does the contract support combat-specific state tracking?

**Mostly yes, with gaps.**

Already supported:
- **Injury carry-forward**: `modules/domain/agents/state_tracker.py` L40-82 tracks `injuries` field with severity levels (정상/경상/중상/위독). `state_tracker_npc.py` L32-70 extracts permanent injuries (amputation, blindness, scarring).
- **Injury-action restrictions**: `config/genres/wuxia.yaml` L179-201 defines `injury_action_limits` — 중상 blocks 전력질주, 경공전개, 내공폭발; 기력저하 blocks 내공운용, 진기순환, 장력, 검기. Guard enforces these.
- **Weapon/item state**: `state_tracker.py` L610-611 tracks weapon lists per episode with auto-detection for wuxia weapon suffixes (검/도/창/궁/장/봉).
- **Power hierarchy**: `wuxia.yaml` L155-177 defines 9-tier `realm_hierarchy` (입문→삼류→이류→일류→절정→초절정→화경→현경→귀신) with `realm_technique_limits` gating technique access by realm.
- **Multi-episode continuation**: `expected_ending` field allows open-ended scenes. No "fight must conclude per episode" requirement anywhere.
- **Reference anchors**: `modules/core/reference_anchor.py` L22-31 defines `combat` and `injury` anchor types. L61-99 extracts combat outcomes and injury state for cross-episode continuity. L162, L278: `injury` is a `critical_type` preserved across all anchor windows.

Gaps:
- **No fight geography tracking**: No field tracks spatial progression within a fight (e.g., "pushed from hall to courtyard to cliff edge"). Spatial keywords exist in `ActionSceneEvaluator` (L67-89) but are advisory, not persisted.
- **No stance/technique progression within a fight**: Realm hierarchy gates what techniques are accessible, but there's no tracking of which techniques have been used/revealed during a multi-episode fight.
- **No tactical escalation validation across episodes**: Stakes escalation is checked within a single manuscript (`ActionSceneEvaluator.evaluate_stakes_escalation`) but not across episodes.

### Investigation Question 3: Hidden bias toward "varied scene mix"?

**Mild bias exists but is not blocking.**

- **ChiefWriter prompt Rule 13** (`config/prompts/chief_writer.yaml` L44-45): "각 씬에 최소 1개의 실제 대화(따옴표 포함)" — each scene requires at least 1 actual dialogue. A combat scene with zero speech fails this rule.
- **ChiefWriter prompt Rule 16** (`chief_writer.yaml` L54): "최소 1개의 상황 변화" — at least 1 situation change per episode. Combat satisfies this easily (injury, power shift, tactical position change).
- **Pre-LLM dialogue check** (`modules/validation/pre_llm_validator.py` L220-240): `expected_min = max(3, int(len(manuscript) / 700))`. For a 5,000-char manuscript: 7 dialogue pairs minimum. **However** — `pre_llm_validator.py` L128-133 explicitly states: "Python은 REJECT 권한 없음, 항상 `passed=True`". Dialogue deficit is advisory only.
- **ScoringValidator** (`modules/validation/scoring_validator.py` L56-58, L340-341): `dialogue_quality` has 15-point allocation. `dialogue_score = min(15, 5 + int(dialogue_count / 10))`. Low dialogue → lower score, but minimum 5 points awarded even with 0 dialogue. Not a hard gate.
- **`pattern_diversity`** (`scoring_validator.py` L58, L347): 10 points max, baseline 6. Low diversity reduces score by at most 4 points. Not a hard gate.

**Net effect**: A combat-heavy episode with minimal but nonzero dialogue (e.g., battle cries, taunts, shouted commands) would lose 0-10 points on dialogue_quality + pattern_diversity from fallback scoring, but would not be auto-rejected. The LLM-based scoring may or may not penalize further depending on prompt interpretation.

### Investigation Question 4: Would validators over-reject or under-specify?

**Low over-rejection risk. Under-specification risk is moderate.**

- **Continuity validator** (`modules/validation/continuity_validator.py` L104-114): Checks injury-action consistency (strenuous actions while injured). Non-blocking — issues warnings. Combat-heavy episodes with proper injury tracking will pass.
- **Blocking validator** (`modules/validation/blocking_validator.py` L56-135): Checks dead NPC resurrection, unowned items, damaged items, physical capability. All relevant to combat and all correctly enforced.
- **ActionSceneEvaluator** (`modules/validation/action_scene_evaluator.py` L1-197): Evaluates choreography (spatial clarity 40%), power consistency (30%), stakes escalation (30%). Score 0-10. **Advisory only** — integrated into validation orchestrator (`validation_orchestrator.py` L257) but does not trigger REJECT.
- **Wuxia guard** (`config/genres/wuxia.yaml`): Comprehensive injury-action limits and realm-technique gates. These are well-suited for combat validation.

Under-specification:
- No cross-episode fight choreography validation. A fight that starts in a courtyard in EP5 could be described as happening on a mountain in EP6 without any validator catching the spatial inconsistency.
- No technique repetition detection. A protagonist could use the same sword move 50 times across 3 episodes without any advisory.

### Investigation Question 5: Ready now or wave needed?

**Mixed.** The core infrastructure (state tracking, injury carry-forward, power hierarchy, reference anchors, genre guard) is solid and production-tested. The system can generate combat-heavy wuxia episodes today and will correctly enforce injury restrictions, weapon state, and realm limits.

The gaps are in *cross-episode combat coherence*:
- Fight geography not persisted
- Tactical escalation not validated across episodes
- No technique progression tracking within a sustained fight

These gaps mean the system relies entirely on the LLM's own coherence for fight spatial/tactical consistency across episodes. For a 1-episode fight, this is adequate. For a 3-episode continuous battle, drift is likely without explicit contract support.

## Evidence Surfaces Inspected

| Surface | File | Key Lines | Status |
|---------|------|-----------|--------|
| Blueprint structure | `modules/models/blueprint.py` | L18-62 | genre-agnostic, no combat-specific fields |
| Stage 3 generation | `modules/domain/agents/three_phase_blueprint_runtime.py` | L908+ | no scene-mix enforcement |
| ChiefWriter prompts | `config/prompts/chief_writer.yaml` | L44-45, L54 | per-scene dialogue minimum (Rule 13) |
| Director scoring rubric | `modules/domain/agents/director_prompts.py` | L118-146 | scene coverage 20%, no scene-type bias |
| Director compare rubric | `modules/domain/agents/director_prompts.py` | L409-446 | scene density uniformity, not type |
| Pre-LLM validator | `modules/validation/pre_llm_validator.py` | L79-83, L128-133, L220-240 | dialogue check advisory, never REJECT |
| Scoring validator | `modules/validation/scoring_validator.py` | L53-60, L340-347 | dialogue_quality 15pt + pattern_diversity 10pt; low = less score, not reject |
| Action scene evaluator | `modules/validation/action_scene_evaluator.py` | L1-197, L67-89, L119-124 | choreography + power + escalation; advisory |
| Validation orchestrator | `modules/validation/validation_orchestrator.py` | L254-257 | ActionSceneEvaluator integrated |
| Wuxia guard YAML | `config/genres/wuxia.yaml` | L155-201 | realm hierarchy + injury-action limits |
| State tracker | `modules/domain/agents/state_tracker.py` | L40-82 | injury/weapon/item state per episode |
| NPC injury extraction | `modules/domain/agents/state_tracker_npc.py` | L32-70 | permanent injury detection |
| Reference anchors | `modules/core/reference_anchor.py` | L22-31, L61-99, L162 | combat + injury anchor types |
| Continuity validator | `modules/validation/continuity_validator.py` | L104-114 | injury-action consistency |
| Blocking validator | `modules/validation/blocking_validator.py` | L56-135 | physical capability check |
| Adversarial self-play | `modules/core/adversarial_self_play.py` | L351-353 | dialogue_count < 3 → issue (advisory) |

## Existing Test Coverage

| Test File | Combat-Related Content |
|-----------|----------------------|
| `tests/test_action_scene_evaluator.py` | Basic wuxia action evaluation (2 combat terms) |
| `tests/test_continuity_modules.py` | Injury/state continuity (23 combat terms) |
| `tests/test_martial_manager.py` | Martial arts system management (14 combat terms) |
| `tests/test_wuxia_guard_init_lane_c.py` | Guard initialization (4 combat terms) |
| `tests/test_genre_guards_extended.py` | Extended guard coverage |

**Gap**: No dedicated test for multi-episode continuous fight with injury progression + weapon state + spatial tracking.

## Classification

### Already Ready
- Injury state tracking and carry-forward (정상→경상→중상→위독 + permanent injuries)
- Injury-action restriction enforcement (wuxia guard `injury_action_limits`)
- Weapon/item state persistence across episodes
- Power realm hierarchy with technique gating (9 tiers, 6+ technique categories)
- Combat and injury reference anchors for cross-episode continuity
- Blueprint generation without scene-type bias
- Director scoring without forced scene-type diversity
- Multi-episode fight continuation (no forced per-episode resolution)
- ActionSceneEvaluator for choreography/power/escalation advisory

### Likely Weak
- **Per-scene dialogue requirement** (Rule 13): Each blueprint scene needs at least 1 dialogue. A pure swordplay scene with no speech would trigger a ChiefWriter rule violation. Workaround: battle cries, taunts, shouted commands count as dialogue.
- **Dialogue scoring penalty**: ScoringValidator allocates 15 points to dialogue_quality. Combat-heavy manuscripts with sparse dialogue lose points but are not rejected.
- **LLM prompt interpretation**: Director and ChiefWriter prompts are genre-agnostic. A wuxia combat prompt injection point exists (genre guard + style guide), but the main prompts may implicitly favor varied scenes if the LLM infers "good novel = dialogue + action + reflection mix."

### Clearly Missing
- **Cross-episode fight geography persistence**: No contract field or state tracker for spatial progression within a sustained fight. A fight location can drift between episodes undetected.
- **Cross-episode tactical escalation validation**: ActionSceneEvaluator checks within-manuscript escalation but not whether EP6's fight escalates beyond EP5's climax.
- **Technique/move progression tracking**: No tracking of which specific techniques have been used/revealed during a multi-episode fight, risking repetitive choreography.
- **Multi-episode fight test suite**: No dedicated test validating a 2-3 episode continuous fight scenario end-to-end.

## Recommendation

**One compact follow-up execution SSOT**, scoped to:
1. Add an optional `fight_geography` field to blueprint/state contract for multi-episode fights
2. Add a `combat_context` section to ChiefWriter prompt injection for active fights (current spatial position, techniques already used, escalation state)
3. Relax or annotate Rule 13 for combat-designated scenes (battle cries/taunts satisfy dialogue minimum)
4. Add 2-3 targeted tests for multi-episode fight continuity

This is a bounded wave. The core infrastructure is solid. The missing pieces are contract extensions, not architectural changes.

Do not open the execution SSOT yet — this survey needs user review first, and confidence on the "fight_geography" contract shape is below 95% without a design pass.

---

## 3-Pass Audit Notes

- Pass 1: scope bounded to wuxia combat-scene readiness; investment/latency/model-switch excluded; 16 evidence surfaces inspected with file:line anchors; classification into ready/weak/missing is explicit
- Pass 2: all claims anchored to live code — injury_action_limits verified at wuxia.yaml L179-201, pre_llm_validator L128-133 confirms advisory-only, scoring_validator L340-341 confirms dialogue penalty formula, ActionSceneEvaluator L1-197 confirmed advisory; no overclaim beyond inspected evidence
- Pass 3: recommendation is bounded (one compact execution SSOT for contract extensions); explicitly defers opening the SSOT pending user review; no scope creep into Director prompt redesign or ensemble strategy changes
- Confidence: 96%

---

- Wuxia combat-scene readiness: **mixed** (core infra ready, cross-episode fight coherence gaps)
- Dominant risk seam: **cross-episode fight geography/escalation not persisted**
- Should Codex open an execution SSOT now: **no** (survey needs user review; fight_geography contract shape needs design pass first)
