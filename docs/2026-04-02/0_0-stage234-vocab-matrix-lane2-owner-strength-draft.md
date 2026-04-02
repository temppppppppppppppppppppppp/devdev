# 0_0 Stage234 Vocab Matrix Lane 2: Owner and Strength Matrix Draft

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: cross-stage survey lane draft
Lane: 2 (owner and strength matrix)
Terminal: Opus Terminal 2
Parent Order: `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`

Required Surfaces Inspected:
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`

Existing Survey Baseline Used:
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`

---

## 1. Coverage

### Surfaces Inspected

| Surface | Lines | Focus |
|---------|-------|-------|
| `unified_blueprint_validator.py` | ~1,700 | Stage3 prevalidation owner/strength patterns, Director delegation, binding contract authority |
| `blueprint_constraint_compiler.py` | ~1,200 | Stage2->3 constraint compilation, 4-tier strength hierarchy, fact_lock/capital immutability |
| `stage4_interview_round.py` | ~5,200 | Stage4 policy gating, fix_scope/fix_pack transform, post_select_conflict detection, advisory escalation |
| `stage4_post_processor.py` | ~1,100 | Stage4 PASS persistence, world_state/actual_truth/pressure_vectors sink, karma/state delta |
| `stage4_post_pass_runtime.py` | ~400 (via delegate) | Manager audit harvest, atomic dual-write, bible delta |

### Concepts Traced

All 14 major cross-stage concepts from the master order's scope, plus 4 additional concepts discovered during the survey:

- fix_pack, fix_scope, authoritative_fix_scope
- post_select_conflict
- final_state_updates, state_changes, actual_truth
- world_state, active_pressure_vectors
- blueprint, arc_data, constraint_block
- validation_warnings, director_result
- fact_lock_packet, capital_continuity_packet (discovered)
- karma_matrix, immutable_fact_carryover (discovered)

---

## 2. Findings

### 2A. Owner-by-Stage Matrix

| Concept | Stage 2 Owner | Stage 3 Owner | Stage 4 Owner | Collision? |
|---------|--------------|---------------|---------------|-----------|
| **fix_pack** | (n/a) | (n/a) | Director produces; InterviewRound normalizes + backfills | YES: dual provenance (Director + advisory backfill) |
| **fix_scope** | (n/a) | Validator can override Director's | InterviewRound can widen; PostProcessor executes | YES: 3 modifiers (Director, Validator, InterviewRound) |
| **authoritative_fix_scope** | (n/a) | (n/a) | Director produces; InterviewRound tracks but routing ignores actual value | YES: tracked but unused |
| **post_select_conflict** | (n/a) | (n/a) | InterviewRound ORIGINATES detection + verdict downgrade | NO: Stage4-local origin |
| **final_state_updates** | (n/a) | (n/a) | Director produces; InterviewRound annotates; PostProcessor persists selectively | YES: quality labels stripped, rest merged |
| **actual_truth** | (n/a) | (n/a) | Manager LLM produces; PostProcessor finalizes + applies corrections | YES: PostProcessor can override Manager martial arts via StateTextVerifier |
| **world_state** | (n/a) | (n/a) | PostProcessor is SOLE writer | NO: single authoritative sink |
| **active_pressure_vectors** | (n/a) | (n/a) | PostProcessor builds from blueprint, filters by manuscript, injects into actual_truth | YES: injected into Manager's document without Manager authorization |
| **state_changes** | Arc Ensemble produces | Compiler transforms to summary | PostProcessor persists via state_log | NO: clean pipeline |
| **fact_lock_packet** | prev_blueprint provides anchors | Compiler compiles to immutable packet | Validator checks drift against packet | NO: clean escalation |
| **capital_continuity_packet** | Arc data provides capital fields | Compiler compiles to immutable packet | Director enforces via prompt | NO: clean escalation |
| **constraint_block** | Arc data + prev_blueprint | Compiler OWNS compilation; Ensemble formats tiers | Director evaluates via prompt (prose only) | YES: structure lost at Stage3->4 boundary |
| **blueprint** | (n/a) | Ensemble generates; Validator validates | InterviewRound sanitizes for writer | NO: clean pipeline |
| **validation_warnings** | (n/a) | Validator produces (advisory) | InterviewRound collects + logs | NO: advisory stays advisory |
| **director_result** | (n/a) | Validator delegates to Director | InterviewRound gates with policy | YES: director_verdict != final_verdict |
| **karma_matrix** | (n/a) | (n/a) | Manager produces; PostProcessor persists to DB | NO: single pipeline |
| **immutable_fact_carryover** | state_changes provides source facts | Compiler extracts + escalates to immutable | InterviewRound enforces via ImmutableFactPacket | NO: clean escalation pipeline |

### 2B. Strength-by-Stage Matrix

| Concept | Stage 2 Strength | Stage 3 Strength | Stage 4 Strength | Inversion? |
|---------|-----------------|------------------|-------------------|-----------|
| **fix_pack** | (n/a) | (n/a) | Advisory (Director) -> Blocking (gate) | UP: advisory->blocking via contract check |
| **fix_scope** | (n/a) | Conditional Hard (Validator override) | Conditional Hard (InterviewRound widens) | FLAT: stays conditional |
| **authoritative_fix_scope** | (n/a) | (n/a) | Hard for contract; ignored for routing | DOWN: hard->ignored |
| **post_select_conflict** | (n/a) | (n/a) | Advisory detection -> Blocking verdict | UP: non-negotiable PASS->REJECT |
| **final_state_updates** | (n/a) | (n/a) | Authoritative (Director) -> Carryover (PostProcessor defers) | FLAT: respected |
| **actual_truth** | (n/a) | (n/a) | Authoritative (Manager) -> Correctable (PostProcessor) | DOWN: Manager overridden on martial arts |
| **world_state** | (n/a) | (n/a) | Authoritative (PostProcessor sole writer) | FLAT: stable |
| **active_pressure_vectors** | (n/a) | (n/a) | Advisory (blueprint source) -> Authoritative (injected into actual_truth) | UP: advisory->authoritative |
| **state_changes** | Advisory (reference) | Advisory (summary) -> Immutable (fact carryover for deaths/items) | Advisory (logged) | UP at Stage3: deaths become immutable |
| **constraint_summary** | Hard (arc-level rules) | Hard (passed through) | Prose only (structure lost) | DOWN: hard->prose |
| **fact_lock_packet** | Hard (prev_blueprint) | Immutable (Tier 0) | Hard (drift-checked) | UP at Stage3: hard->immutable |
| **capital_continuity_packet** | Hard (arc data) | Immutable (Tier 0) | Hard (Director prompt) | UP at Stage3: hard->immutable |
| **constraint_block** | (compound) | 4-tier structured hierarchy | Prose-only (entered via prompt) | DOWN: structure->prose at Stage3->4 |
| **blueprint** | (n/a) | Hard (generated output) | Advisory (sanitized template) | DOWN: hard->advisory for writer |
| **validation_warnings** | (n/a) | Advisory | Advisory | FLAT: stays advisory |
| **director_result** | (n/a) | Hard (Director verdict) | Conditional Hard (gated by policy) | DOWN: can be overridden by policy |
| **karma_matrix** | (n/a) | (n/a) | Advisory (Manager audit) -> Authoritative (persisted) | UP: advisory->authoritative |

### 2C. Top 3 Owner Collisions

**Collision 1: fix_scope triple-modifier chain**

Director produces `authoritative_fix_scope` -> Validator can override to `fix_scope_reasoning` with binding prevalidation -> InterviewRound can widen from `inplace` to `partial` or `full` via strong advisory escalation or post_select_conflict.

Three separate actors modify the same concept without a single canonical authority. Result: the `authoritative_fix_scope` that Director intended is tracked in logging but never consumed for actual routing. The routing uses whichever modifier acted last.

Evidence:
- `unified_blueprint_validator.py` L234-238: binding prevalidation forces PASS_WITH_FIX + overrides scope
- `stage4_interview_round.py` L2277: InterviewRound widens to `partial` for advisory escalation
- `stage4_interview_round.py` L4376: post_select_conflict overrides to `full`
- `stage4_interview_round.py` L2170-2171: `authoritative_fix_scope` extracted but used only for contract validation, not routing

**Collision 2: actual_truth vs final_state_updates parallel state surfaces**

Director produces `final_state_updates` (verdict + score + state delta). Manager produces `actual_truth` (comprehensive state audit). PostProcessor must merge both.

Three truth surfaces exist after PASS:
- Director state: what Director declared should change
- Manager state: what Manager audited as current truth
- Python state: what PostProcessor corrected via StateTextVerifier

PostProcessor defers to Director for capital (explicit Director sovereignty check at L594-600) but overrides Manager for martial arts (StateTextVerifier corrections at L442-446). No general reconciliation protocol exists.

Evidence:
- `stage4_post_processor.py` L594-600: "Director 주권 존중" capital check
- `stage4_post_processor.py` L442-446: StateTextVerifier overrides Manager martial arts
- Stage4 consumer survey: confirmed `state_truth_triple_split` as proven seam

**Collision 3: active_pressure_vectors unauthorized injection**

PostProcessor builds pressure vectors from blueprint fields (ending_hook, cliffhanger, expected_ending), filters them by manuscript tail match, then injects them into `actual_truth` — which is Manager's document.

Manager never authorized these vectors. PostProcessor silently extends Manager's truth output with Python-constructed data. Downstream consumers of actual_truth see pressure vectors as if Manager produced them.

Evidence:
- `stage4_post_processor.py` L437-446: `_build_active_pressure_vectors()` from blueprint
- `stage4_post_processor.py` L449-494: `_filter_active_pressure_vectors_by_manuscript()`
- `stage4_post_processor.py` L467: injection into actual_truth dict

### 2D. Strength Inversions (Confirmed)

**Inversion 1: state_changes advisory -> immutable (Stage2 -> Stage3)**

Stage2 `state_changes` is advisory reference. BlueprintConstraintCompiler `_extract_immutable_fact_carryover()` escalates NPC deaths, items, and relationship changes to IMMUTABLE tier — the highest authority level. This escalation is intentional and well-designed.

**Inversion 2: constraint_block structured -> prose (Stage3 -> Stage4)**

Compiler produces a 4-tier structured hierarchy (IMMUTABLE > HARD > EXPECTED > ADVISORY). This structure enters Stage4 only as prose in the blueprint text and Director prompt. Stage4 InterviewRound cannot machine-read the original tiers. The highest-cost drift source.

**Inversion 3: authoritative_fix_scope hard -> ignored (Stage4 internal)**

Director's `authoritative_fix_scope` is extracted, validated for contract compliance (blank/invalid triggers REJECT), then stored in logging — but never used for actual fix routing. The routing uses `fix_scope` from whichever modifier (Validator/InterviewRound) acted last.

**Inversion 4: advisory -> blocking via escalation (Stage4 internal)**

Python advisory signals from TruthGate, NpcDrift, RelDrift etc. can trigger `strong_advisory_escalation` converting PASS -> PASS_WITH_FIX. Post-select conflict detection converts PASS -> REJECT. Both are advisory-origin but blocking-effect.

**Inversion 5: actual_truth authoritative -> correctable (Stage4 PostProcessor)**

Manager's actual_truth is nominally the authoritative state audit. But PostProcessor applies StateTextVerifier corrections to martial arts, and injects pressure vectors. Manager's document arrives authoritative but leaves corrected.

### 2E. Director State vs Manager State vs Python State

| State Layer | Authoritative Scope | Key Concepts | Persistence Sink |
|------------|---------------------|--------------|-----------------|
| **Director (LLM)** | Verdict, selection, fix strategy, score | director_verdict, fix_scope, fix_pack, final_state_updates, score | director_selections DB, session log |
| **Manager (LLM)** | Post-PASS state audit, NPC inventory, actual world state | actual_truth, karma_matrix, key_npcs, martial_arts_snapshot | state_log, bible, memory |
| **Python (Code)** | Structural validation, advisory detection, policy gating | validation_warnings, post_select_conflict, strong_advisory_escalation, quality_floor | attempt_artifact_meta, quality signals |

**Where they diverge:**

1. **Capital**: Director owns (PostProcessor explicit sovereignty deference). Manager excluded.
2. **Martial arts**: Manager produces snapshot. PostProcessor overrides with StateTextVerifier. Director excluded from correction.
3. **Active pressure vectors**: Python constructs from blueprint. Injected into Manager's actual_truth. Director and Manager excluded from construction.
4. **NPC positions**: Manager provides key_npcs audit. PostProcessor syncs into world_state. Director excluded.
5. **Verdict**: Director produces. Python policy gates can override (InterviewRound final_verdict != director_verdict). Manager excluded.

**Net effect**: No single authority spans all state concepts. Each concept has an implicit primary owner, but the PostProcessor merger creates undocumented authority transfers between layers.

---

## 3. Non-Issues

### 3A. Clean Pipelines (No Collision)

| Concept | Reason |
|---------|--------|
| **world_state** | PostProcessor is sole writer; no competitor |
| **fact_lock_packet** | Clean Stage2 -> Stage3 escalation; no override |
| **capital_continuity_packet** | Clean Stage2 -> Stage3 escalation; no override |
| **state_changes -> immutable_fact_carryover** | Intentional, well-designed escalation |
| **validation_warnings** | Advisory throughout; never pretends to be blocking |
| **karma_matrix** | Single Manager -> PostProcessor pipeline |
| **blueprint generation -> sanitized writer blueprint** | Clean transform; original preserved |

### 3B. Already Proven by Stage4 Consumer Survey

The following seams are confirmed by the existing consumer-finalization survey and not re-proven here:
- `post_select_fix_scope_flattening`: bounded repairs forced to full rewrite
- `strong_advisory_escalation_non_local_fix`: missing patch_targets
- `intake_prose_flattening`: tier0 canonical truth enters as prose only
- `state_truth_triple_split`: three parallel state surfaces
- HUD-before-manager drift

### 3C. Design-Intentional Authority Patterns

| Pattern | Justification |
|---------|--------------|
| Director sovereignty over capital | Explicit code comment "Director 주권 존중" |
| Binding prevalidation can override Director PASS | Dead NPC / structural integrity requires Python safety net |
| Post-select conflict is non-negotiable | Continuity / history violations discovered after selection must REJECT |
| Advisory chain parallel execution | Performance optimization; 8 advisories in ThreadPoolExecutor(max_workers=8) |

---

## 4. Verdict

**owner-collision-heavy**

Rationale:
- 3 major owner collisions identified (fix_scope triple-modifier, actual_truth/final_state_updates parallel surfaces, pressure_vectors unauthorized injection)
- 5 strength inversions confirmed (2 intentional escalations, 1 structure->prose demotion, 1 hard->ignored, 1 authoritative->correctable)
- Director State / Manager State / Python State triple-truth split is systemic, not local
- No reconciliation protocol exists for the PostProcessor merge step
- `authoritative_fix_scope` is tracked but functionally dead for routing
- Constraint hierarchy structure is lost at Stage3->4 boundary (the highest-cost single inversion)

The evidence supports:
1. **Contract normalization** as next direction: especially fix_scope/fix_pack provenance and actual_truth/final_state_updates reconciliation
2. **Owner consolidation** for the PostProcessor merge: explicit authority protocol instead of implicit case-by-case deference
3. **Stage3 compiler/substep compression**: constraint_block should survive as machine-readable data into Stage4, not be flattened to prose

---

## 5. Stop

read-only lane complete; no files mutated
