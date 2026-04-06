# Opus 5-Terminal Downstream Philosophy Survey Order

## Mission

Determine, in read-only mode, whether Geuldobi downstream pipeline should consume the new material-side philosophy/constitution docs, where that reference should enter, and whether the ROI is high.

This is a survey-only order.

- No code changes
- No prompt or config mutation
- No DB writes
- No moving files
- No speculative implementation

Each terminal should answer:

1. Is there a live consumer path here
2. Is the path authority-bearing or just traceability/storage
3. Would a raw philosophy doc survive here, or must it be distilled
4. What is the ROI if we use this path

## Common Guardrails

- Work in UTF-8-safe read-only mode
- Prefer exact file and line references
- Distinguish `live consumer`, `manual handoff`, `mirror/residue`, and `legacy-only`
- Separate `possible in theory` from `possible without code changes`
- If the path only accepts compact bullets, say so explicitly

## Shared Inputs

All terminals should read these first:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `material_ssot/20_pitch/protagonist-first-constitution.md`
- `material_ssot/20_pitch/pitch-philosophy.md`

## Terminal 1

### Goal

Map live ingress surfaces that can already carry a philosophy reference or compact doctrine into downstream runtime.

### Focus files

- `main_a.py`
- `modules/core/project_manager.py`
- `modules/core/project_support.py`
- `modules/core/genre_guards/work_guard.py`
- `modules/core/stage4_orchestrator.py`
- `geuldobi-desktop/src/main.js`
- `modules/api/bridge_server.py`

### Questions

- Is `work_guard.yaml` a live doctrine seam
- Is `author_directives.txt` live, and how strong is it
- Is `style_guide.json` a better place for philosophy or only for prose/style
- What exact config surfaces are already exposed in desktop/bridge

### Deliverable

One memo titled `Ingress Surfaces` with:

- live paths
- strength ranking
- no-code viability

## Terminal 2

### Goal

Find the main distortion seams where upstream truth gets summarized, re-banded, or dropped before manuscript generation.

### Focus files

- `modules/core/stage2_preflight.py`
- `modules/core/context_advisor.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `docs/이전/2026-04-02/0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md`

### Questions

- Where does Stage2 doctrine become Stage3 free reinterpretation
- Which fields survive as structured authority and which are demoted to advisory
- At what point would a raw philosophy doc become noise

### Deliverable

One memo titled `Distortion Seams` with:

- first hard loss point
- later compaction points
- survival odds for raw document versus compact digest

## Terminal 3

### Goal

Map existing reference-doc and auxiliary-policy patterns already used by the repo.

### Focus files

- `modules/core/stage0/style_extractor.py`
- `modules/core/stage01_helpers.py`
- `modules/core/reference_anchor.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_director_runtime.py`
- `modules/domain/agents/director_ensemble.py`
- `scripts/sync_narrative_reference_bank.py`
- `docs/2026-04-03/narrative-reference-bank-mirror-necessity-audit.md`

### Questions

- Which reference patterns are truly live
- Which are style-only
- Which are mirror-only
- Which appendix/reference patterns are reusable for philosophy reminders

### Deliverable

One memo titled `Reference Patterns` with:

- best reusable pattern
- bad pattern to avoid
- budget and enforcement caveats

## Terminal 4

### Goal

Map the upstream handoff lane and determine whether philosophy docs can already be registered there without code changes.

### Focus files

- `scripts/narrative_router.py`
- `modules/narrative_router/router.py`
- `modules/narrative_router/families/blockguide.py`
- `modules/narrative_router/families/wuxguide.py`
- `scripts/stage0_handoff_validator.py`
- `contracts/source_manifest.schema.json`
- `contracts/profile_lock.schema.json`
- `contracts/material_bundle_summary.schema.json`
- `contracts/phase0_ready_snapshot.schema.json`
- `material_ssot/10_research/30_work_materials/README.md`

### Questions

- Can the philosophy document path be carried as authority today
- Can its doctrine be distilled into existing 4-pack fields
- Would a new standalone artifact require code changes

### Deliverable

One memo titled `Handoff Lane` with:

- current no-code path
- what can be represented now
- what still lacks a live consumer

## Terminal 5

### Goal

Judge ROI by stage and recommend a placement strategy that balances authority, survival, and token budget.

### Focus files

- `modules/domain/agents/base_agent.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_types.py`
- `modules/core/stage4_director_runtime.py`
- `docs/stage_map/stage0.md`
- `docs/stage_map/stage4.md`
- any prior audit on downstream weak links or context pressure

### Questions

- Which stage has the best ROI for philosophy enforcement
- Is Stage4 too late
- Should the philosophy be always-on or stage-gated
- Should the downstream consumer read the full document or a digest

### Deliverable

One memo titled `ROI Judgment` with:

- per-stage ROI
- always-on versus gated recommendation
- full text versus digest recommendation

## Synthesis Rules

The final synthesizer should merge the five memos into one decision using these tests:

1. Prefer live consumer over mirror/storage lane
2. Prefer compact structured doctrine over raw essay text
3. Prefer earlier stages if they survive the Stage2 -> Stage3 seam better
4. Treat late Stage4 appendices as reinforcement only
5. Reject any recommendation that needs code changes unless it is explicitly labeled `future implementation`

## Expected Final Decision Shape

The synthesis should answer in this order:

1. `possible?`
2. `best no-code ingress`
3. `best live runtime consumer`
4. `highest-risk distortion seam`
5. `ROI verdict`
6. `do this / do not do this`

## 3-Pass Audit

- Pass 1: checked that the five terminals are disjoint enough to avoid duplicate work
- Pass 2: checked that every terminal has a clear yes/no question and concrete files
- Pass 3: checked that the synthesis rules force a usable operator decision rather than five unrelated memos
- Confidence: 0.98
