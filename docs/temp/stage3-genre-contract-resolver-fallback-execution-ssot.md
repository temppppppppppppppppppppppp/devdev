# Stage3 Genre Contract Resolver Fallback Execution SSOT

Date: 2026-04-29
Status: proposed - GitHub issue backing execution doc
Track: system
Canonical Path: `docs/2026-04-29/stage3-genre-contract-resolver-fallback-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-genre-contract-resolver-fallback-execution-ssot.md`
Source Survey: `docs/2026-04-29/stage3-genre-contract-application-gap-survey.md`
Source Survey Docs:
- `docs/2026-04-29/stage3-genre-contract-application-gap-survey.md`
- `docs/2026-04-29/stage3-genre-contract-resolver-fallback-execution-ssot.md`
Baseline Commit: `8a1463b237499b2aa0d56ea95a67eac54d2cefb9`
Runtime Guard: do not touch the active S4 run for `projects/0_카나리아`.

## 1. Intent

Fix the application gap where the Stage3 genre strategy contract exists in code but is skipped when the project genre is not stored at top-level `bible._genre`.

The immediate bug is not that PR #84 is absent. The bug is that the resolver defaults to `wuxia` even when the project has authoritative investment signals elsewhere.

## 2. Problem Statement

`BlueprintEnsembleGenerator._resolve_blueprint_ensemble_genre()` currently reads only:

```python
bible = self.context.db.load_anchor("bible")
genre = bible.get("_genre", GenreTypes.WUXIA)
```

In `projects/0_카나리아`:

- `bible._genre` is absent.
- `style_guide.genre` is `investment`.
- nested bible metadata includes `genre_archetype = investment + 회귀물 + 패밀리오피스 통제권 장악`.
- selected Stage3 `action_focused` artifacts have no `genre_strategy_contract` metadata.

Therefore `investment_business_power.action_focused.v1` is available but not applied.

## 3. Non-Goals

- Do not patch or restart the currently active S4 run.
- Do not mutate factsheets, bible content, style guides, or project material as part of the resolver fix.
- Do not let Python judge narrative quality. Python may resolve genre routing signals and transport advisory contracts only.
- Do not remove tactical intrusion guards.

## 4. Execution Tranches

### Tranche A - Resolver Fallback

Owner surface:
- `modules/domain/agents/blueprint_ensemble.py`

Implement a bounded resolver order:

1. `bible._genre`
2. `style_guide.genre` from DB anchor
3. `bible.MasterBible.ProjectData.MetaInfo.genre_archetype`
4. project file fallback `stage0_output/style_guide.json`
5. `GenreTypes.WUXIA`

Normalize investment-like values through the existing `_is_investment_business_power_genre()` family.

Expected behavior:
- If `style_guide.genre=investment` and `bible._genre` is absent, return `GenreTypes.INVESTMENT` or an accepted investment value.
- If only nested `genre_archetype` contains `investment`, return an accepted investment value.
- If no genre signal exists, default to `GenreTypes.WUXIA`.

### Tranche B - Deterministic Tests

Owner surface:
- `tests/test_blueprint_ensemble_generate_ensemble.py`

Add tests for:

- missing `bible._genre` + `style_guide.genre=investment` resolves to investment.
- missing `bible._genre` + nested bible `genre_archetype` containing `investment` resolves to investment.
- an investment-resolved `action_focused` prompt contains `investment_business_power.action_focused.v1`.
- an investment-resolved `action_focused` candidate stores `_ensemble_meta.genre_strategy_contract` after finalization.

### Tranche C - Operator Observability

Owner surface:
- `modules/domain/agents/blueprint_ensemble.py`

Add a compact warning when the resolver defaults to `wuxia` while weaker investment-like signals are present but malformed or unreadable.

The warning must be operational, not narrative judgment:

`[BPEnsemble] genre defaulted to wuxia; detected unresolved investment-like genre signal at <source>`

### Tranche D - Optional Lane Expansion Decision

Do not silently widen this bugfix into a full lane-semantics rewrite.

Open a separate enhancement or explicit subtask if the team wants genre-register contracts for:

- `emotion_focused`
- `dialogue_focused`
- Stage4 `balanced/narrative/tension`

The immediate acceptance target is `investment + action_focused` application parity with PR #84.

## 5. Acceptance Criteria

- `0_카나리아`-shaped fake DB fixture resolves investment without top-level `bible._genre`.
- Investment `action_focused` prompt does not include the raw physical-action directive text.
- Finalized investment `action_focused` candidate metadata includes:
  - `contract_id = investment_business_power.action_focused.v1`
  - `authority_level = route`
  - `factsheet_mutation = False`
  - `material_mutation = False`
- Existing tactical intrusion tests remain green.
- No active S4 process is touched during the fix.

## 6. Validation Plan

Run targeted low-memory verification:

```powershell
python -m py_compile modules/domain/agents/blueprint_ensemble.py tests/test_blueprint_ensemble_generate_ensemble.py
python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -q
python scripts/check_utf8_hygiene.py modules/domain/agents/blueprint_ensemble.py tests/test_blueprint_ensemble_generate_ensemble.py
```

If Director-visible Stage4 transport is touched, also run:

```powershell
python -m pytest tests/test_stage3_director_compare_advisory_lane.py tests/test_tf29_open_review.py tests/test_director_modules.py -q
```

## 7. Risk Rating

Current severity: P2.

Escalation condition: P1 if a weaker or mixed-genre project produces physical chase/combat/thriller intrusion because the explicit genre contract was skipped.

Current `0_카나리아` evidence does not show physical-action drift in selected action-focused blueprints, so the active run should continue and this fix should be handled as a follow-up.

## 8. GitHub Issue Payload

Recommended title:

`[Stage3] Genre strategy contract not applied when project genre lives outside bible._genre`

Recommended labels:

- `bug`
- `stage3`
- `quality`

Recommended body summary:

- #56/#84 implemented `investment_business_power.action_focused.v1`.
- `0_카나리아` shows `style_guide.genre=investment` but `bible._genre=None`.
- Stage3 action-focused artifacts lack contract metadata.
- Fix resolver fallback and add `0_카나리아`-shaped regression tests.

## 9. Document 3-Pass Audit

Pass 1 - Structure and scope:
- PASS. This is an execution SSOT, not a survey.
- Scope, non-goals, tranches, acceptance criteria, and validation are explicit.
- Canonical and temp paths are declared.

Pass 2 - Evidence and consistency:
- PASS. The execution plan is grounded in the companion survey and does not overclaim output corruption.
- It distinguishes the existing PR #84 contract from the resolver application failure.
- It preserves Director authority and factsheet ownership.

Pass 3 - Execution and readability:
- PASS. The plan is small enough for a focused bugfix wave and avoids active-run interference.
- Optional lane expansion is separated from the immediate fix.
- Estimated confidence: 96%.
