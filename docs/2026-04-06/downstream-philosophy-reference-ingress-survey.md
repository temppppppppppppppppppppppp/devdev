# Downstream Philosophy Reference Ingress Survey

- Date: 2026-04-06
- Scope: read-only system-track investigation
- Request: determine whether Geuldobi downstream pipeline should consume the new material-side philosophy/constitution docs, where they should be seen, and whether the ROI is high
- Edit policy: no code changes, no runtime mutation, documentation only
- Baseline commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`

## Executive Summary

Yes, it is possible, but the pipeline should not read the full philosophy document raw at late stages.

The highest-ROI approach is:

1. keep the canonical philosophy/constitution in `material_ssot`
2. register that authority in the Stage0 preprocess handoff lane
3. distill it into compact, structured per-work doctrine
4. let downstream consume that doctrine through live slots that already exist

If we try to append the full philosophy text directly into late Stage4 prompts, ROI drops sharply because the repo already trims, compacts, and re-bands context before manuscript generation.

## Bottom-Line Answer

### Is it possible

Yes.

Two no-code lanes already exist:

- the Stage0 preprocess 4-pack / handoff lane can carry the philosophy document as an authority source and distilled doctrine
- the live `work_guard.yaml` lane can carry compact protagonist-first doctrine into Stage2, Stage3, and Stage4 retrieval contracts

### Where should the reference be seen

The recommended order is:

1. `material_ssot` canonical doc remains the law source
2. Stage0 preprocess 4-pack records the doc path and distills non-negotiables
3. `work_guard.yaml` carries the compact runtime-facing doctrine
4. optional TR harness digest reinforces the same doctrine in prompt-time bullets

Not recommended as primary ingress:

- raw `author_directives.txt`
- raw Stage4 `reference_excerpt`
- `narrative_ssot/10_reference_bank` mirror

### Is the ROI high

Yes, if and only if the philosophy is converted into a compact downstream digest before the Stage2 -> Stage3 drift seam.

No, or at least much lower, if the full text is appended late as a generic reference document.

## Key Findings

### F1. The repo already has live downstream doctrine slots

`work_guard.yaml` is loaded at runtime and wrapped around the genre guard in [main_a.py](../../main_a.py), and its config model already has the exact kinds of fields we need:

- `tracking_slots`
- `mandatory_scene_engines`
- `registry_profiles`
- `role_fit_constraints`
- `work_identity.protagonist_evaluation.admiration_axes`
- `work_identity.protagonist_evaluation.forbidden_praise_patterns`
- `work_identity.protagonist_evaluation.observer_tiers`
- `work_identity.protagonist_evaluation.evaluation_thresholds`

Evidence:

- [main_a.py](../../main_a.py#L1344)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L33)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L117)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L548)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L610)

This is the strongest live runtime seam for a protagonist-first doctrine because it already speaks in compact, structured slots rather than raw essay text.

### F2. Stage2 and Stage3 already consume compact work-focus doctrine

Stage2 compresses block intent into short `tracking_slots` and `mandatory_scene_engines`, then passes that into `context_advisor` retrieval planning.

Evidence:

- [stage2_preflight.py](../../modules/core/stage2_preflight.py#L512)
- [stage2_preflight.py](../../modules/core/stage2_preflight.py#L555)
- [stage2_preflight.py](../../modules/core/stage2_preflight.py#L703)
- [context_advisor.py](../../modules/core/context_advisor.py#L478)
- [context_advisor.py](../../modules/core/context_advisor.py#L658)
- [context_advisor.py](../../modules/core/context_advisor.py#L773)

Stage3 also resolves work focus from guard-provided compact doctrine and appends the retrieval contract into Blueprint generation.

Evidence:

- [stage3_orchestrator.py](../../modules/core/stage3_orchestrator.py#L254)
- [stage3_orchestrator.py](../../modules/core/stage3_orchestrator.py#L297)
- [blueprint_ensemble.py](../../modules/domain/agents/blueprint_ensemble.py#L708)

This makes Stage2 -> Stage3 the highest-leverage place to enforce the philosophy.

### F3. The earliest major distortion seam is Stage2 -> Stage3

The compiler turns rich upstream truth into summarized and re-banded constraint text. `state_changes` are summarized, `semantic_carryover` is normalized, and later Stage3 moves some of that truth into the `ADVISORY` band.

Evidence:

- [blueprint_constraint_compiler.py](../../modules/domain/agents/blueprint_constraint_compiler.py#L91)
- [blueprint_constraint_compiler.py](../../modules/domain/agents/blueprint_constraint_compiler.py#L1012)
- [blueprint_ensemble.py](../../modules/domain/agents/blueprint_ensemble.py#L959)
- [blueprint_ensemble.py](../../modules/domain/agents/blueprint_ensemble.py#L1024)
- [0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md](../이전/2026-04-02/0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md#L37)
- [0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md](../이전/2026-04-02/0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md#L141)

Implication:

- if the philosophy has not already been translated into compact structured keys by this seam, later stages will mostly see a diluted paraphrase

### F4. Raw prompt-level document injection is weak and budget-sensitive

`author_directives.txt` is loaded and prepended to prompts, but that entire prompt still goes through the prompt size gate.

Evidence:

- [project_manager.py](../../modules/core/project_manager.py#L114)
- [base_agent.py](../../modules/domain/agents/base_agent.py#L324)
- [base_agent.py](../../modules/domain/agents/base_agent.py#L837)

Stage4 style/reference lanes are also clamped and trimmed.

Evidence:

- [stage4_orchestrator.py](../../modules/core/stage4_orchestrator.py#L32)
- [stage4_orchestrator.py](../../modules/core/stage4_orchestrator.py#L1085)
- [stage4_orchestrator.py](../../modules/core/stage4_orchestrator.py#L1288)
- [stage4_orchestrator.py](../../modules/core/stage4_orchestrator.py#L1309)
- [stage4_orchestrator.py](../../modules/core/stage4_orchestrator.py#L2319)
- [chief_writer_context.py](../../modules/domain/agents/chief_writer_context.py#L617)
- [stage4_context_builder.py](../../modules/core/stage4_context_builder.py#L2809)

Implication:

- a full constitution appended late is likely to be trimmed, rephrased, or simply crowded out

### F5. Stage0 preprocess 4-pack is the correct no-code authority ingress

The router and validators already recognize a fixed 4-pack for preprocess/handoff:

- `source_manifest.json`
- `profile_lock.json`
- `material_bundle_summary.json`
- `phase0_ready_snapshot.json`

Evidence:

- [narrative_router.py](../../scripts/narrative_router.py#L85)
- [router.py](../../modules/narrative_router/router.py#L52)
- [blockguide.py](../../modules/narrative_router/families/blockguide.py#L42)
- [wuxguide.py](../../modules/narrative_router/families/wuxguide.py#L22)
- [stage0_handoff_validator.py](../../scripts/stage0_handoff_validator.py#L37)
- [source_manifest.schema.json](../../contracts/source_manifest.schema.json#L7)
- [profile_lock.schema.json](../../contracts/profile_lock.schema.json#L7)
- [material_bundle_summary.schema.json](../../contracts/material_bundle_summary.schema.json#L7)
- [phase0_ready_snapshot.schema.json](../../contracts/phase0_ready_snapshot.schema.json#L7)

Implication:

- without code changes, the philosophy doc itself should first be carried here as authority provenance and distilled doctrine
- adding a brand-new fifth preprocess artifact would require code changes

### F6. Existing reference-bank mirrors are not live consumers

The narrative reference-bank mirror is traceability infrastructure, not a live runtime reader.

Evidence:

- [sync_narrative_reference_bank.py](../../scripts/sync_narrative_reference_bank.py#L1)
- [mirror_status.json](../../narrative_ssot/10_reference_bank/mirror_status.json#L2)
- [narrative-reference-bank-mirror-necessity-audit.md](../2026-04-03/narrative-reference-bank-mirror-necessity-audit.md#L42)

Implication:

- placing the philosophy doc into a mirror lane alone has low ROI because the active runtime path does not automatically read it

## Recommended Placement Model

### Canonical Law Source

Keep the full philosophy docs authoritative in:

- `material_ssot/20_pitch/protagonist-first-constitution.md`
- `material_ssot/20_pitch/pitch-philosophy.md`
- any successor canonical digest maintained under `material_ssot`

### No-Code Bridge

Use the Stage0 preprocess 4-pack as the handoff registration point:

- `source_manifest.json`
  - record the philosophy document path under authority/provenance
- `profile_lock.json`
  - encode non-negotiable protagonist axes and failure bans
- `material_bundle_summary.json`
  - carry short doctrine summary and opening-reward expectations
- `phase0_ready_snapshot.json`
  - record what must survive into Phase0/TR/BI

This is the right place for provenance and durable handoff, not for a long essay.

### Live Runtime Consumer

Translate the doctrine into `work_guard.yaml`:

- `tracking_slots`
- `mandatory_scene_engines`
- `protagonist_evaluation.*`
- `forbidden_flattenings`
- `role_fit_constraints`

That gives the downstream pipeline an already-supported runtime representation that Stage2/3/4 can actually consume.

### Optional Prompt Reinforcement

If reinforcement is needed, use the TR harness digest lane with short bullets, not raw long-form prose.

Evidence:

- [harness_digest.py](../../modules/narrative_router/harness_digest.py#L17)
- [blockguide-tr-batch-digest.json](../../config/treatments/harness_digests/blockguide-tr-batch-digest.json)
- [wuxguide-tr-batch-digest.json](../../config/treatments/harness_digests/wuxguide-tr-batch-digest.json)

## Recommended Digest Shape

The downstream digest should be short and per-work, not universal and essay-like.

Suggested fields:

- `promise_to_reader`
- `opening_reward_vector`
- `first_block_signature_scene`
- `protagonist_evaluation.admiration_axes`
- `protagonist_evaluation.forbidden_praise_patterns`
- `hard_constraints`
- `do_not_fake`
- `tracking_slots`
- `mandatory_scene_engines`

This shape matches the repo's existing compact doctrine surfaces much better than a full constitution dump.

## ROI Judgment

### High ROI

- Stage2 -> Stage3 compact doctrine injection
- `work_guard.yaml` protagonist-evaluation translation
- preprocess 4-pack provenance plus distilled lock data

### Medium ROI

- TR harness digest reinforcement
- Director appendix reminder for review/reject-retry situations

### Low ROI

- full philosophy doc appended to `author_directives.txt`
- full philosophy doc appended as Stage4 `reference_excerpt`
- storing the doc only in reference-bank mirror lanes

## Risks

- full-text injection will hit existing prompt-size and mandatory-context clamps
- philosophy as prose-only guidance is weaker than philosophy encoded as structured slots
- mirror/reference storage can create false confidence if there is no live consumer
- style-reference lanes can distort doctrine into prose imitation rather than narrative law

## Decision

The best no-code plan is:

1. treat the philosophy doc as upstream canonical law in `material_ssot`
2. register it in the Stage0 preprocess 4-pack
3. distill it into runtime-facing compact doctrine
4. let `work_guard.yaml` and Stage2/3 work-focus machinery carry it downstream
5. only use late prompt appendices as reinforcement, never as the main contract

## 3-Pass Audit

- Pass 1: verified live consumer paths versus storage-only paths
- Pass 2: verified distortion seams and prompt-budget clamps
- Pass 3: reconciled upstream handoff lane versus runtime lane so recommendation is not path-confused
- Confidence: 0.97
