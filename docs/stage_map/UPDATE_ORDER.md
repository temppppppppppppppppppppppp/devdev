# stage_map 최신화 마스터 오더

> 상태: `Active / canonical`
> 목적: `docs/stage_map` 전체를 current workspace truth 기준으로 최신화하는 단일 실행 오더

## Summary
- 이 문서는 `docs/stage_map`의 canonical refresh order다.
- 우선순위는 `current workspace code > 2026-03-13 consolidated audits > existing stage_map docs`다.
- 기준 truth는 마지막 clean commit이 아니라 현재 dirty workspace다.

## Source Priority
1. Current workspace code, config, and runtime-facing entrypoints in this working tree.
2. Consolidated audit evidence from `docs/2026-03-13/*`.
3. Existing `docs/stage_map/*` text.
4. Historical helper orders (`FILL_ORDER.md`, `ENHANCE_ORDER.md`) for context only.

## Metadata Rule
- Active stage_map docs use the footer schema below:
  - `Date`
  - `Commit`
  - `Workspace State`
  - `Code Sync (Yes/No)`
  - `Verified By`
- Use HEAD commit as the `Commit` basis and explicitly mark `Workspace State: dirty` when verifying an uncommitted tree.
- If a document intentionally preserves history instead of current behavior, mark it `Deprecated` in `doc_status.md` instead of pretending it is synced.

## Work Packages

### WP0. Baseline Freeze
- Record current HEAD commit, current workspace state, and `git status --short` surface.
- Map dirty code paths to stage_map targets before editing:
  - `modules/core/stage0/*`, `main_a.py`, `stage01_helpers.py` -> `stage0.md`, `stage1.md`
  - `modules/core/stage2_*`, `stage2_context.py`, `stage2_finalizer.py` -> `stage2.md`
  - `modules/core/stage3_*`, `three_phase_blueprint_generator.py` -> `stage3.md`
  - `modules/core/stage4_*`, `chief_writer*`, `consistency_validator.py` -> `stage4.md`
  - `db_manager.py`, `project_manager.py` -> `interfaces.md`, `runbook.md`
  - `config/settings/validation.yaml`, `constants.py`, `CLAUDE.md` -> `metrics_baseline.md`
- Inventory stale metadata first:
  - mismatched footers
  - stale `doc_status` rows
  - old threshold language
  - old operator/UI caveats

### WP1. Stage Docs Refresh
- Refresh in this order: `stage0.md -> stage1.md -> stage2.md -> stage3.md -> stage4.md`
- Keep the existing section structure where it still fits.
- Do not rewrite code or dated audit docs.
- If code and dated audit docs conflict, document the code path as truth and move the disagreement into `Open Risks` or `Known drift`.

Required reflection points:
- `stage0.md`
  - style/reference provenance contract
  - `reference_excerpt` 50,000-char cap
  - missing downstream truncation guard risk
  - preset / POV UI drift surface
- `stage1.md`
  - `_show_volume_table()` is live but duck-typed through `hasattr`
  - operator-facing table is post-save UI, not storage truth
  - `_validate_volume_boundaries()` still lives in `main_a.py`
- `stage2.md`
  - Stage2Context callback surface includes `validate_arc_data_fields`
  - Stage2Context has no dedicated `world_state` slot
  - auto-correct / structural normalization boundary must be described carefully
  - response schema mismatch and repair-hook regression gap must be recorded as risks
- `stage3.md`
  - unified `quality_gate_score=90`
  - PASS_WITH_FIX patch accumulation risk
  - entity registry Stage3/Stage4 double extraction risk
  - treatment-block and generate-exception coverage gaps
- `stage4.md`
  - 1M-context thresholds and stale Python fallback defaults
  - `_build_cv_context()` NPC profile resolution through facade-or-fallback path
  - EMPTY caller verdict vs attempt-row `ERROR` nuance
  - current advisory / CoVe / patch-loop semantics

### WP2. Cross-cut Refresh
- Update `interfaces.md` after the stage docs so stage handoff language matches the stage-specific truth.
- Update `agent_graph.md` to reflect live call paths, current DI seams, and round / gate behavior.
- Update `gotchas.md` to remove obsolete dedicated-blueprint-gate assumptions and old 80-point patch-routing language.
- Update `metrics_baseline.md` to separate:
  - last verified full-suite baseline
  - current YAML / constant thresholds
  - partial verification note for this session
- Update `runbook.md` using only `main_a.py`, `project_service.py`, and DB reset semantics as truth.

### WP3. Navigation and Ledger Refresh
- Update `README.md` usage order to:
  - `README.md`
  - `UPDATE_ORDER.md`
  - relevant stage docs
  - `interfaces.md` / `runbook.md`
  - `doc_status.md`
- Update `doc_status.md` so active rows match actual active doc footers 1:1.
- Expand `doc_status.md` coverage to include:
  - `README.md`
  - `UPDATE_ORDER.md`
  - `SYNC_CHECK.md`
  - `FILL_ORDER.md`
  - `ENHANCE_ORDER.md`

### WP4. Legacy Cleanup
- Keep `FILL_ORDER.md` and `ENHANCE_ORDER.md` as historical docs only.
- Add a clear `superseded by UPDATE_ORDER.md` banner to both.
- Strip obsolete operational detail from the legacy docs so stale thresholds do not remain discoverable as current guidance.
- Keep `SYNC_CHECK.md` active, but make it read `UPDATE_ORDER.md` first and evaluate dirty workspace changes, not only clean-commit deltas.

## Acceptance Checks
- Active doc footers and `doc_status.md` rows match 1:1.
- `docs/stage_map` no longer presents these as current truth:
  - a separate low blueprint-only quality gate
  - Stage 4 routing driven by an old 80-point patch threshold
  - a hard-coded fixed volume-count title
  - stale small round-count / context-budget limits as live semantics
- `README.md + UPDATE_ORDER.md + stage_map` are enough to explain:
  - current Stage 0-4 responsibilities
  - Stage 2/3/4 quality gate = 90
  - Stage 4 reads blueprint SSOT from DB, not txt
  - safe-op rollback / wipe / reset / rewind meaning
- UTF-8 check across `docs/stage_map/*` finds no replacement characters or mojibake.

## Notes
- Historical audit docs remain evidence, not execution truth.
- Historical stage_map helper orders remain archived guidance, not active instructions.

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
