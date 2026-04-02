Date: 2026-04-02
Status: final-bounded-survey
Canonical Path: `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-bounded-survey.md`
Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
Baseline Dirty Summary: `dirty: config/models.yaml, active/temp roadmap mirrors, queue-state, canary fixpack runtime artifacts; untracked stage2/stage3/stage4 survey bundles and matrix lane drafts`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane1-term-inventory-draft.md`
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane2-owner-strength-draft.md`
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane3-transport-drift-draft.md`
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane4-vertical-slice-draft.md`
Related Baselines:
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-evidence.json`
Mode: survey only, read-only only

---

## Answer First

The evidence supports a strong `yes` on the need for a shared cross-stage vocabulary and source-of-truth matrix.

The largest current debt is not that Stage2, Stage3, or Stage4 individually lack concepts. The debt is that the same concept changes name, strength, structure, or owner at each boundary, and Stage4 introduces additional local terminology for truths that originated upstream. The highest-cost seams are:

1. `Stage3 -> Stage4` constraint hierarchy loss
2. `Stage4` split truth across `final_state_updates`, `actual_truth`, and `world_state`
3. `fix_scope / authoritative_fix_scope / repair_scope` owner split inside Stage4

The bounded survey supports these next long-term directions, in order:

1. `contract normalization`
2. `owner consolidation`
3. `Stage3 compiler/substep compression`

It also supports immediate inclusion of the following Stage4 concepts into the shared cross-stage matrix instead of keeping them stage-local:

- `fix_pack`
- `fix_scope`
- `authoritative_fix_scope`
- `post_select_conflict`
- `final_state_updates`
- `actual_truth`
- `world_state`
- `active_pressure_vectors`

---

## Hard Conclusions

### 1. The current system is cross-stage-vocabulary-drift heavy

The term inventory lane traced 33 major concepts across Stage2, Stage3, and Stage4. Only a small subset remain true equivalents across boundaries. The rest either rename, flatten, split, or die.

The most damaging drift is not cosmetic naming noise. It is:

- strength inversion
- structure-to-prose flattening
- owner collision
- stage-local terminology for upstream truth

### 2. The most expensive boundary is `Stage3 -> Stage4`

Stage3 compiles structured constraint hierarchy:

- `IMMUTABLE`
- `HARD CONSTRAINT`
- `EXPECTED CONTINUITY`
- `ADVISORY`

But Stage4 does not consume that structure as machine-readable authority. It rebuilds authority from persistent stores and receives most of the rest as prose. This makes Stage3's compilation partially redundant and turns Stage4 into a second authority compiler. That is the single biggest translation-pressure seam found in this survey.

### 3. Stage4 contains the worst owner split

The owner-strength lane and vertical slices agree that Stage4 has three parallel truth surfaces after PASS:

- `final_state_updates` from Director
- `actual_truth` from Manager
- `world_state` from Python/PostProcessor

These are not consistently reconciled under one explicit owner protocol. Some families defer to Director, some get corrected by Python, and some are injected into Manager truth after the fact.

This is not a local bug. It is a contract-level source-of-truth ambiguity.

### 4. `fix_scope` is a multi-owner concept and should be normalized

The survey confirms a three-way split:

- Director produces an intended repair scope
- Validator can override scope conditions
- InterviewRound/runtime can widen scope again

The strongest evidence is the real runtime split:

- `fix_scope`
- `authoritative_fix_scope`
- `repair_scope`

These are three labels for one repair-routing concept with different owners. The system already knows it has split the concept; the matrix should formalize it.

### 5. Several Stage2 concepts die too early

The transport lane and term inventory lane both found dead or low-signal Stage2 fields:

- `beat_sequence`
- `hybrid_composition`
- `semantic_carryover`
- `status_shadow`
- `vol_strategy`

This does not mean Stage2 is the primary blocker today. It does mean Stage2 emits more conceptual structure than Stage3/4 preserve.

### 6. The next long-term simplification direction is supported

The evidence supports:

- first: `contract normalization`
- second: `owner consolidation`
- third: `Stage3 compiler/substep compression`

It does not support keeping the current vocabulary and owner model as-is.

---

## Production Truth

Stage2 is still `content-sufficient but schema-fragile`.

Its strongest stable productions are:

- `tactical_doc`
- `constraint_summary`
- `state_constraints`
- `state_changes`

Its weakest productions are fields whose boundary survival is poor:

- `beat_sequence`
- `hybrid_composition`
- `semantic_carryover`
- `episode_details`

The production problem is not absence of information. It is uneven survivability of emitted structure.

---

## Consumption Truth

The downstream consumer pattern is `consumer-diluted`.

### Stage3 consumption

Stage3 is the first place where:

- `tactical_doc` becomes `arc_focus`
- `constraint_summary` becomes `arc_constraint_summary`
- `state_changes` becomes `state_changes_summary`

This is partly useful compilation and partly lossy renaming/compression.

### Stage4 consumption

Stage4 does not trust Stage3's structured authority enough to consume it directly. Instead it:

- rebuilds authority from `world_state`, `fact_ledger`, and other persistent stores
- receives most authority as prose for CW/Director prompt consumption
- adds its own local finalization vocabulary

That is why Stage4 was previously described as `consumer/finalization split-truth-heavy`.

---

## Artifact Truth

The representative slices confirm that drift changes behavior, not just labels.

### Slice A: `0_0` ep2

This slice proves the repair-scope split. Runtime produced:

- `fix_scope = full`
- `authoritative_fix_scope = inplace`
- `repair_scope = full`

This is a live example where the same repair concept is split by owner and lane.

### Slice B: `0_0` ep5 and ep6

Under retry pressure, structured repair vocabulary degraded:

- `gate_semantics` empty
- `fix_pack` empty
- `authoritative_fix_scope` absent

The most structured contracts degraded exactly where retry cost was highest.

### Slice C: `canary_0_0_stage34_arc2_fixpack_r1`

This slice exposed the richest vocabulary compound:

- `conflict_contract`
- `reuse_contract`
- `scope_origin`
- `rationale_blanked_by`
- compound pathology fingerprints

This proves the system is already encoding the vocabulary split internally, but only ad hoc.

### Slice D: `0_1` canary ep9/ep13

The vocabulary shape remains broadly consistent across projects. That means this is not a single-project naming accident. It is a cross-project substrate issue.

---

## Contract Drift

### Shared canonical vocabulary that should be standardized first

#### Authority strength family

- `IMMUTABLE`
- `HARD CONSTRAINT`
- `MISSION`
- `CARRYOVER`
- `ADVISORY`

This is the highest-value vocabulary family because the current system inverts strength across boundaries.

#### Episode mission family

- Stage2 `tactical_doc`
- Stage3 `arc_focus`
- Stage4 `arc_tactical`

These should become one canonical mission family instead of three stage-local labels.

#### Post-finalization truth family

- `final_state_updates`
- `actual_truth`
- `world_state`

These should not remain three parallel unlabeled truth surfaces.

#### Repair contract family

- `fix_pack`
- `fix_scope`
- `authoritative_fix_scope`
- `repair_scope`
- `post_select_conflict`

These should become one explicit contract family with declared owner precedence.

### Highest-cost mismatches

1. `constraint_summary -> arc_constraint_summary -> Stage4 hard prohibition prose`
2. `tactical_doc -> arc_focus -> arc_tactical`
3. `state_changes -> state_changes_summary -> actual_truth/world_state/final_state_updates`

### Concepts that survive only as prose

- `world_state_summary`
- `fact_ledger_summary`
- `canonical_constraints`
- `continuity_packet`
- much of the Stage3 constraint hierarchy once it enters Stage4/CW prompt assembly

These are the main machine-readable authority losses.

---

## Long-Term Direction

### 1. Contract normalization

This survey strongly supports a dedicated cross-stage contract-normalization wave.

Priority targets:

- authority-strength vocabulary
- episode mission vocabulary
- repair contract vocabulary
- post-finalization truth vocabulary

### 2. Owner consolidation

The survey supports explicit owner boundary work in Stage4:

- Director-owned state
- Manager-owned state
- Python-owned persistence truth

These need declared merge rules instead of implicit case-by-case dominance.

### 3. Stage3 compiler/substep compression

The evidence supports this as a long-term direction, not an immediate patch wave.

Rationale:

- Stage3's most defensible role is compiler-like normalization and packaging
- its least defensible role is redundant re-translation whose structure is then lost before Stage4

This does not mean `delete Stage3 now`. It means the survey found real evidence that Stage3 is the leading candidate for eventual external-stage compression.

---

## Non-Issues

- `protagonist_name` and protagonist identity remain stable across stages
- arc/episode numbering is stable hard truth
- Stage3 blueprint top-level key shape is internally stable
- DB serialization boundary itself is not the core problem
- cross-project vocabulary shape is more consistent than the runtime behavior layered on top of it

---

## Verdict

`matrix-needed-now`

More precisely:

- Stage2: `content-sufficient but schema-fragile`
- Stage3: `compiler-like but enforcement-lossy`
- Stage4: `consumer/finalization split-truth-heavy`

The system is now at the point where a shared cross-stage vocabulary and source-of-truth matrix is no longer optional cleanup. It is the clearest next long-term simplification substrate.

---

## Operating Consequence

The survey does **not** by itself justify immediate broad architecture rewrite.

It **does** justify:

1. keeping Stage2 and Stage3 parked SSOTs narrow
2. keeping Stage4 consumer-contract normalization as the active aggregate wave
3. treating a future cross-stage matrix wave as the right substrate before any serious Stage-count simplification

---

## Stop

survey-only bundle complete; no code, queue, or runtime artifacts mutated in this synthesis step

---

## 3-Pass Audit Record

Pass 1. Structure and scope
- document type matches bounded survey request
- scope kept to cross-stage vocabulary and source-of-truth matrix
- did not inflate into execution SSOT or patch plan

Pass 2. Evidence and consistency
- claims were bounded to the four lane drafts and their cited runtime/code anchors
- baseline commit and dirty summary were refreshed from live workspace
- all major conclusions align with stage2, stage3, and stage4 prior surveys

Pass 3. Execution and readability
- answer-first, operating consequence, and long-term direction are explicit
- highest-cost mismatches and matrix-first canonical families are actionable
- overreach trimmed: no stage-deletion recommendation elevated beyond long-term direction

Confidence: 96%
