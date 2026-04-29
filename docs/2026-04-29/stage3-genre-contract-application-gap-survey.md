# Stage3 Genre Contract Application Gap Survey

Date: 2026-04-29
Status: final - GitHub issue backing survey
Track: system
Scope: Stage3 blueprint ensemble genre-strategy contract application gap observed in `projects/0_카나리아`
Canonical Path: `docs/2026-04-29/stage3-genre-contract-application-gap-survey.md`
Baseline Commit: `8a1463b237499b2aa0d56ea95a67eac54d2cefb9`
Dirty State: active workspace already had unrelated project/material/doc changes; this survey only records read-only evidence.

## 1. Question

Did PR #84 make the Stage3/Stage4 ensemble genre strategy contract available, and did the current `0_카나리아` Stage3 run actually apply it?

## 2. Short Answer

PR #84 did add the investment/business-power `action_focused` genre strategy contract and Director-visible transport path.

The current `0_카나리아` Stage3 run did not appear to apply that contract. The likely cause is that `BlueprintEnsembleGenerator._resolve_blueprint_ensemble_genre()` only reads `bible._genre`, while this project stores the effective genre in `style_guide.genre` and nested bible metadata.

This is a real application-path bug. The current run did not show physical-action corruption in selected `action_focused` blueprints, probably because the investment-material gravity was strong, but the explicit contract proof is absent.

## 3. Evidence

### 3.1 Implemented Contract Exists

`modules/domain/agents/blueprint_ensemble.py:80-95` defines `build_genre_strategy_contract()`.

Observed contract fields:
- `contract_id`: `investment_business_power.action_focused.v1`
- `authority_level`: `route`
- `authority_source`: `stage3_genre_strategy_contract`
- `genre_family`: `investment_business_power`
- `factsheet_mutation`: `False`
- `material_mutation`: `False`

The implementation applies only when:

```python
_is_investment_business_power_genre(normalized_genre)
and normalized_strategy == "action_focused"
```

### 3.2 Resolver Reads Only `bible._genre`

`modules/domain/agents/blueprint_ensemble.py:686-695` currently resolves genre as:

```python
genre = GenreTypes.WUXIA
bible = self.context.db.load_anchor("bible")
if bible:
    genre = bible.get("_genre", GenreTypes.WUXIA)
```

No fallback to `style_guide.genre`, nested bible `genre_archetype`, or `stage0_output/style_guide.json` is visible in this resolver.

### 3.3 Current Project Stores Genre Elsewhere

Byte-level/SQLite readback from `projects/0_카나리아/project_data.db`:

- `anchors.bible` exists.
- `bible.top_level._genre`: `None`
- `bible.MasterBible.ProjectData.MetaInfo.genre_archetype`: `investment + 회귀물 + 패밀리오피스 통제권 장악`
- `anchors.style_guide` exists.
- `style_guide.genre`: `investment`

This matches an investment project, but not in the top-level field the Stage3 resolver currently expects.

### 3.4 Current Stage3 Action Artifacts Lack Contract Metadata

Readback of selected final Stage3 action-focused artifacts:

| Episode | Artifact | Strategy | Contract Metadata |
| --- | --- | --- | --- |
| 8 | `projects/0_카나리아/logs/artifacts/stage3/ep_0008/attempt_02/final_blueprint__action_focused.json` | `action_focused` | absent |
| 10 | `projects/0_카나리아/logs/artifacts/stage3/ep_0010/attempt_01/final_blueprint__action_focused.json` | `action_focused` | absent |
| 11 | `projects/0_카나리아/logs/artifacts/stage3/ep_0011/attempt_01/final_blueprint__action_focused.json` | `action_focused` | absent |
| 14 | `projects/0_카나리아/logs/artifacts/stage3/ep_0014/attempt_05/final_blueprint__action_focused.json` | `action_focused` | absent |

For all four artifacts:
- `_ensemble_meta.genre_strategy_contract`: absent
- `_ensemble_meta.prompt_envelope.genre_strategy_contracts`: absent

### 3.5 Negative Evidence: Current Output Did Not Obviously Become Physical Action

Forbidden physical-action terms checked in the final action-focused artifacts:

- Korean: `전투`, `추격`, `침입자`, `차량 공격`, `물리적 위기`, `액션 클리프`, `총격`, `폭행`, `암살`, `납치`
- English: `combat`, `chase`, `intruder`, `vehicle attack`, `physical crisis`, `thriller infiltration`

Observed forbidden hits: none in the four selected final action-focused artifacts.

Observed business/investment tension examples:

- ep8: market volatility and sell wall
- ep10: sideways market, PB pressure, Ecuador crisis signal
- ep11: geopolitical crisis and market breakout
- ep14: gold futures entry before subprime risk

## 4. Findings

F1. The codebase contains the intended PR #84 contract, but `0_카나리아` did not receive it at runtime. Severity: P2, with P1 risk in weaker material contexts.

F2. The resolver has an application gap. It treats missing `bible._genre` as `wuxia` even when other authoritative project surfaces clearly identify `investment`.

F3. The prior proof covered the contract path but did not cover this project-storage shape. A regression should cover projects where `style_guide.genre` is present and `bible._genre` is absent.

F4. The current contract is narrow: it primarily remaps `investment + action_focused`. Full genre-register semantics for `emotion_focused` and `dialogue_focused` remain a separate enhancement unless intentionally included in the follow-up.

## 5. Side-Effect Coverage

- File writes: not performed by this survey except this document.
- DB writes: none.
- Runtime/process interaction: none; active S4 run was not touched.
- JSONL/log sinks: read-only inspection only.
- Artifact truth: final Stage3 blueprint JSON artifacts were read directly.
- Metadata truth: SQLite anchors and final blueprint `_ensemble_meta` were inspected.
- Narrative truth: selected `action_focused` artifact content was checked for obvious physical-action drift.

## 6. Recommendation

Open a follow-up GitHub issue distinct from #56/#84:

`[Stage3] Genre strategy contract not applied when project genre lives outside bible._genre`

Recommended execution scope:

- Add resolver fallback order:
  1. `bible._genre`
  2. `style_guide.genre`
  3. nested `bible.MasterBible.ProjectData.MetaInfo.genre_archetype`
  4. `stage0_output/style_guide.json`
  5. default `GenreTypes.WUXIA`
- Add tests for `style_guide.genre=investment` with missing `bible._genre`.
- Add tests proving final `action_focused` candidate metadata includes `investment_business_power.action_focused.v1`.
- Add an operator warning when defaulting to `wuxia` despite available investment-like genre signals.
- Keep current S4 run untouched; apply after current live run completes or in a separate bugfix wave.

## 7. Document 3-Pass Audit

Pass 1 - Structure and scope:
- PASS. The document is a survey, not an execution plan.
- Scope is limited to the application gap in Stage3 genre contract routing.
- Included surfaces: code resolver, DB anchors, Stage3 artifacts, prior GitHub issue/PR context.
- Excluded surfaces: code modification, active run control, full Stage4 manuscript audit.

Pass 2 - Evidence and consistency:
- PASS. Claims are anchored to code lines, SQLite readback, and artifact metadata readback.
- Negative output-quality evidence is bounded to selected final action-focused artifacts.
- The document does not claim all genre-lane semantics are implemented.

Pass 3 - Execution and readability:
- PASS. Findings separate implementation existence, runtime application failure, and quality impact.
- Recommendation is actionable and suitable for GitHub issue creation.
- Estimated confidence: 96%.

