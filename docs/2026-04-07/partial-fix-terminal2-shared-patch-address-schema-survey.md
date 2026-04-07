# Partial-Fix Terminal 2 — Shared Patch Address Schema Survey

Date: 2026-04-07
Status: final
Document Type: read-only terminal survey
Canonical Path: `docs/2026-04-07/partial-fix-terminal2-shared-patch-address-schema-survey.md`
Temp Mirror Path: `(none - terminal survey output only; no docs/temp mirror)`
Track: system
Lane: terminal 2 of `partial-fix-hardening-3terminal-parallel-survey-order`
Mode: read-only; no code patched; queue not mutated
Operator Order: `docs/2026-04-07/partial-fix-hardening-3terminal-parallel-survey-order.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: widespread tracked/untracked across docs/, treatments/, material_ssot/, modules/, tests/; survey-only and does not mutate queue or code`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Coverage

### 1.1 Read

Live code:

- `modules/core/stage2_finalizer.py` (PASS_WITH_FIX loop, `re_slice_instruction`, `_inplace_patch_arc` call sites at 2225-2308 and 2520-2611)
- `modules/domain/agents/four_phase_arc_generator.py` (`_inplace_patch_arc` at 619-684)
- `modules/domain/agents/three_phase_blueprint_runtime.py` (validator handoff and PWF loop at 1018-1158)
- `modules/domain/agents/three_phase_blueprint_generator.py` (`_inplace_patch_blueprint` at 158-252)
- `modules/core/stage4_interview_round.py` (`_normalize_fix_pack`, `_evaluate_fix_pack_contract`, `_evaluate_pass_with_fix_contract`, `_build_fix_pack_payload` at 1870-2140; gate at 2680-2780)
- `modules/domain/agents/chief_writer.py` (`_build_structural_patch_plan`, `_attempt_structural_inplace_patch` at 1302-1518)
- `modules/domain/agents/chief_writer_inplace_local_ops.py` (whole module: `SUPPORTED_LOCAL_TARGET_KINDS`, `supports_local_edit_fix_pack`, `_apply_replace_operation`, span guard)

Canonical docs:

- `docs/2026-04-07/partial-fix-hardening-3terminal-parallel-survey-order.md`
- `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
- `docs/2026-04-07/stage2-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage3-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage4-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`
- `docs/2026-04-07/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`

Harnesses:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/commit-state-minimal-contract.md`

### 1.2 Intentionally Excluded

- Terminal 1 telemetry / eval-harness surfaces (owned by lane 1).
- Terminal 3 operator-facing trace surfaces (owned by lane 3).
- DB schema and persistence-row layout for repair traces.
- Stage0 / Phase 0 preprocess surfaces (no PWF loop in scope).
- Director-side prompt grammar redesign and fix_pack provenance redesign.
- Live runtime / canary execution; no fresh runs were performed.
- Active queue mutation. The temp roadmap was read as context only.

## 2. Findings

Ordered by severity (highest first).

### F1. Only Stage4 has any structured patch-target metadata; Stage2/3 carry zero target fields

- Stage4 normalizes a `fix_pack` dict at `modules/core/stage4_interview_round.py:1998-2060` with the keys `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`, `target_kinds`, plus `evidence_summary`, `subtype`, `subtypes`, `provenance`, `provenance_sources`.
- Stage4 enforces those keys as a contract gate at `_evaluate_fix_pack_contract` (`modules/core/stage4_interview_round.py:2063-2080`) and refuses PWF without them at `_evaluate_pass_with_fix_contract` (`modules/core/stage4_interview_round.py:2082-2105`) and the Stage4 gate (`modules/core/stage4_interview_round.py:2696-2780`).
- Stage2 PWF entry passes only `re_slice_instruction` (a free-form Korean directive string) plus `fix_scope` into `_inplace_patch_arc(...)` (`modules/core/stage2_finalizer.py:2282-2308` and `2577-2611`). There is no `patch_targets`, no `target_kind`, no `must_fix`, no `do_not_regress`, no `success_condition`.
- Stage3 PWF entry is identical in shape: `fix_scope` plus `re_slice_instruction` or `feedback`, then `owner._inplace_patch_blueprint(...)` (`modules/domain/agents/three_phase_blueprint_runtime.py:1018-1045`). Same gap.
- Both `_inplace_patch_arc` (`modules/domain/agents/four_phase_arc_generator.py:619-684`) and `_inplace_patch_blueprint` (`modules/domain/agents/three_phase_blueprint_generator.py:158-252`) take only `original_<container>: dict` plus `director_feedback: str` and prompt the LLM to "fix only the pointed parts" without ever passing structured target coordinates. The whole-container JSON is rewritten in place, not addressed.

Severity rationale: this is the largest cross-stage gap. It is what makes Stage2/3 partial-fix coarse versus Stage4.

### F2. Even Stage4 carries two distinct address dialects, and they share keys at the contract level only

- Local-edit dialect (`modules/domain/agents/chief_writer_inplace_local_ops.py:8-79`): the address is enforced at the **op** layer, not at the patch_target layer. Each replace operation carries `old_text`, `new_text`, `anchor_before`, `anchor_after`, with span limits derived from `target_kind in {entity_ref, local_phrase, local_sentence}` (`_passes_local_span_guard` at lines 223-230).
- Structural dialect (`modules/domain/agents/chief_writer.py:1344-1396`): the address is `target_scene_ids: list[str]` plus a derived `target_index_map: dict[scene_id, int]`, with `boundary_context` carrying ±220-char prev/next excerpts. The contract is scene-keyed, not text-anchored.
- Both dialects coexist under the same `fix_pack` envelope but the local-op address fields (`old_text`, `anchor_before`, `anchor_after`) live inside the LLM-returned `operations[]` payload (`chief_writer_inplace_local_ops.py:140-160`), not inside `fix_pack` itself. `fix_pack.patch_targets` is currently a free-form `list[str]` of human descriptions, not a list of structured address records.

Severity rationale: the existing fix_pack contract is text-only at the target layer; the structured address only appears at op-time inside Stage4 and only in the local dialect. Anything that wants to reuse Stage4 address strength cross-stage has to first lift it from op-layer to target-layer.

### F3. `target_kind` enumeration is Stage4-specific and silently strict

- `_evaluate_fix_pack_contract` accepts only `{entity_ref, local_phrase, local_sentence}`, treats `scene_model` as `not local-fixable` (`modules/core/stage4_interview_round.py:2075-2079`), and rejects every other value as `invalid_target_kind`.
- `chief_writer_inplace_local_ops.py:8` independently re-declares `SUPPORTED_LOCAL_TARGET_KINDS = {"entity_ref", "local_phrase", "local_sentence"}` and recomputes the same gate via `supports_local_edit_fix_pack`. Two definitions, same set, two locations.
- Stage2 has no natural `entity_ref` or `local_phrase` notion at all — its container is the Arc dict (state_constraints, tactical sections), not free text. Stage3's container is the Blueprint dict (`scene_breakdown`, `dialogue_outline`, etc.). Stage4's container is the Manuscript text. The current `target_kind` family is implicitly **manuscript-text-shaped** and will not survive an unaltered copy into Stage2/3.

Severity rationale: this is the highest-risk dialect-drift seam. If the parked Stage2/3 SSOTs lift `target_kind` literally, they will invent their own values per stage, and the cross-stage `fix_pack-lite` dialect fragments on day one.

### F4. Stage3 already has natural address coordinates inside its container, but PWF ignores them

- `three_phase_blueprint_generator.py:232-247` proves the blueprint has a `scene_breakdown: dict[scene_key, dict]` shape, and `_inplace_patch_blueprint` already has to **restore lost scene keys** from the original after the LLM's whole-blueprint rewrite.
- That means Stage3 is already keyed-by-scene at the data shape, but the PWF contract still sends nothing addressable. The runtime side only knows the whole `original_blueprint` dict.
- Stage4 structural patch already uses `scene_id` strings as the addressing primitive (`chief_writer.py:1344-1396`). Stage3 could trivially share that primitive without inventing a new one.

Severity rationale: this is the cheapest cross-stage normalization win. `scene_id` already exists in two stages; harmonizing it as the cross-stage block primitive is mostly a doc decision, not a code redesign.

### F5. Stage2 has no free-text container, so any "text anchor" address from Stage4 will not transfer

- Stage2 Arc partial-fix already carries dict children like `state_constraints`, `tactical_section`, and bounded scene fields. The natural Stage2 addressing primitive is a dotted `field_path` inside the Arc dict, not `old_text`/`anchor_before`/`anchor_after`.
- Lifting the Stage4 local-op address dialect into Stage2 unchanged would either force Arc tactical text to be treated as free-form prose (loss of structure) or generate dead address fields that never resolve.
- The parked Stage2 partial-fix SSOT (Tranche 2) already names the realization direction as `tactical section` / `state-constraint section` / `bounded field path`, but does not yet pin the cross-stage schema for that field path.

Severity rationale: this defines the lower bound of how universal a cross-stage schema can become before it starts to lie.

### F6. `patch_targets` is a list of strings today, never a list of structured records

- In `_normalize_fix_pack` (`modules/core/stage4_interview_round.py:2001`) `patch_targets` is normalized via `_normalize_fix_pack_list(...)`, which produces a `list[str]`. The strings are short human descriptions like `NPC relation_to_protag 관계 프레이밍 문장` (`stage4_interview_round.py:2232`).
- Nothing in the current contract makes a single `patch_target` an object with its own address fields. The address only materializes one layer down inside the LLM-returned `operations[]` (local mode) or inside the `target_scene_ids` plan (structural mode).
- Any cross-stage `fix_pack-lite` document that promises `patch_targets` without specifying whether each entry is a free string or a structured `{target_kind, scene_id, field_path, text_anchor?}` record will silently inherit Stage4's string-only convention.

Severity rationale: this is the smallest-footprint, highest-leverage decision in the whole survey. It is the one missing-key decision that decides whether stage-local lanes converge or fork.

## 3. Existing Coverage Check

### 3.1 Already covered by ranks 9-11

- Each parked SSOT (`docs/2026-04-07/0_0-stage{2,3,4}-partial-fix-hardening-remediation-execution-ssot.md`) explicitly names Tranche 1 as a `fix_pack-lite contract` introducing the keys `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`. The **field-name vocabulary** is therefore already on the queue, three times.
- Each parked SSOT names Tranche 2 as `section/field-aware` or `scene/path-aware` patch targeting. So the **idea** of moving from whole-container rewrite to addressed repair is also queued, three times.
- Stage4's parked SSOT explicitly names Tranche 1 as `Patch-Address Normalization` and accepts that local-edit and structural-patch modes need to share an address family.

### 3.2 Implied but not explicit

- None of the three parked SSOTs declares any of the others as a dependency, prerequisite, or shared-substrate authority. Each is written as if it can land alone.
- None of them defines `target_kind` cross-stage. Each will re-derive its own values when activated.
- None of them defines whether `patch_targets` becomes `list[str]` (current Stage4) or `list[{...address...}]`.
- None of them names the `scene_id` primitive as cross-stage even though Stage3 and Stage4 both naturally key by it.

### 3.3 Still missing

- One **shared schema authority** doc that fixes:
  - the shape of a single patch-target record
  - the cross-stage `target_kind` enumeration
  - which fields are universal versus stage-only
  - the canonical `scene_id` / `field_path` / `text_anchor` semantics
- The minimal coordination contract that lets the three stage-local fix-pack-lite tranches land in sequence without re-renaming each other's keys.

## 4. Minimal Contract Proposal

Goal: pin **the smallest schema delta** that lets the three queued stage-local lanes ship without dialect drift. This is a contract proposal, not an implementation order.

### 4.1 Single Patch Target Record

Each entry in `patch_targets` becomes an object instead of a free string. Keys:

```
{
  "stage":          "stage2" | "stage3" | "stage4",
  "container_kind": "arc" | "blueprint" | "manuscript",
  "container_id":   "<arc_no | episode_number | manuscript_episode_id>",
  "target_kind":    "<see 4.2>",
  "scene_id":       "<optional; required when container has scene_breakdown / scene_ids>",
  "field_path":     "<optional dotted path inside the dict container>",
  "text_anchor":    {                       // optional; only when container is free text
    "old_text":      "...",
    "anchor_before": "...",
    "anchor_after":  "..."
  },
  "summary":        "<short human description; replaces today's free string>"
}
```

Compatibility with current code:

- Stage4's current `fix_pack.patch_targets: list[str]` becomes `list[PatchTargetRecord]`. The `summary` field carries today's free string so no human-facing prompt loses content.
- Stage4 local-op `operations[].old_text|anchor_before|anchor_after` keep their existing op-layer location. The new `text_anchor` block at target layer only **predeclares** the anchor at planning time so the post-patch verifier (Terminal 3 / future verifier work) can compare.

### 4.2 Cross-Stage `target_kind` Enumeration

Pinned, additive, and stage-aware:

- `entity_ref`        — Stage4 only (manuscript)
- `local_phrase`      — Stage4 only (manuscript)
- `local_sentence`    — Stage4 only (manuscript)
- `scene_block`       — Stage3 + Stage4 (scene_breakdown / scene_ids)
- `field_value`       — Stage2 + Stage3 (dict field replace, no free text)
- `state_constraint`  — Stage2 + Stage3 (state_constraints subtree)
- `tactical_section`  — Stage2 (Arc tactical section)
- `scene_model`       — escalation marker; not local-fixable; preserves today's Stage4 semantics

Notes:

- The Stage4 set `{entity_ref, local_phrase, local_sentence, scene_model}` survives unchanged. No Stage4 regression.
- The Stage2/3 additions are exactly the realization directions already named in their parked SSOTs, given a stable name.
- `_evaluate_fix_pack_contract` becomes `_evaluate_fix_pack_contract(stage)` and gates only `target_kind` values that are valid for that stage.

### 4.3 Universal Versus Stage-Only Fields

Universal across Stage2/3/4:

- `stage`, `container_kind`, `container_id`, `target_kind`, `summary`
- `must_fix`, `do_not_regress`, `success_condition` (already Stage4)

Stage-conditional:

- `scene_id` — required for `scene_block`, optional otherwise
- `field_path` — required for `field_value` / `state_constraint` / `tactical_section`
- `text_anchor` — required only when the eventual op layer is text-anchored (Stage4 local-edit). Forbidden for Stage2 / Stage3 because their containers are dict, not text.

### 4.4 What This Does Not Do

- It does not redesign `_inplace_patch_arc` or `_inplace_patch_blueprint`. Those refactors remain inside the parked Stage2/3 SSOT lanes.
- It does not introduce a new persistence row, DB column, or sink. Address records ride inside the existing `fix_pack` payload.
- It does not redefine `fix_scope`. The `inplace / partial / full` gate is unchanged.
- It does not require Director-prompt rewrites. The new fields can be filled in by the existing director output normalization step.

## 5. Owner Verdict

Narrowest plausible owner set, in execution-readiness order:

1. **Schema authority** — `modules/core/stage4_interview_round.py` `_normalize_fix_pack` / `_evaluate_fix_pack_contract` / `_build_fix_pack_payload`. Stage4 is the only place that already has a normalization seam, so the cross-stage record shape should be defined here and re-exported.
2. **Stage4 local-op consumer** — `modules/domain/agents/chief_writer_inplace_local_ops.py` `SUPPORTED_LOCAL_TARGET_KINDS`, `supports_local_edit_fix_pack`. Must consume the new `target_kind` enumeration from the schema authority instead of re-declaring it.
3. **Stage4 structural consumer** — `modules/domain/agents/chief_writer.py` `_build_structural_patch_plan`. Must accept `scene_block` patch targets natively rather than inferring them from `_classify_structural_patch_focus`.
4. **Stage3 PWF caller** — `modules/domain/agents/three_phase_blueprint_runtime.py` PWF loop at 1018-1045. Becomes the second consumer once the Stage3 parked SSOT activates Tranche 1.
5. **Stage3 patch executor** — `modules/domain/agents/three_phase_blueprint_generator.py` `_inplace_patch_blueprint`. Receives target records as input instead of just `director_feedback`.
6. **Stage2 PWF caller** — `modules/core/stage2_finalizer.py` PWF loops at 2282-2308 and 2577-2611. Third consumer once the Stage2 parked SSOT activates.
7. **Stage2 patch executor** — `modules/domain/agents/four_phase_arc_generator.py` `_inplace_patch_arc`. Receives target records as input instead of just `director_feedback`.

The schema authority and its enumeration live in one place. Each downstream consumer is touched by its own queued lane. No new owner module is required.

## 6. Promotion Signal

`extend-rank9-11-stage-local-wave`

Reasoning:

- The vocabulary additions (`patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`) are already promised three times by the existing queued ranks 9-11.
- The cross-stage missing piece is small: one shared schema reference plus the cross-stage `target_kind` enumeration. It does not justify a wholly new execution lane.
- The right home is a **Tranche 0** appended to each of the three parked SSOTs that points to the same shared schema doc, so all three lanes consume one source of truth when activated.
- If a later operator wave decides the schema authority should live as a standalone canonical reference doc rather than inside Stage4 code comments, that doc can be created without a queue mutation in this wave; the parked SSOTs already commit to consuming it.

This is intentionally **not** `candidate-new-cross-stage-lane`. The risk of adding a dedicated lane is that it competes with the parked stage-local lanes for the same files, which doubles regression surface for almost no gain. Keep the cross-stage piece as a thin shared schema dependency consumed by the existing queued items.

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
