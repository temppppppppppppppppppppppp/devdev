# fresh-run-followup-fixes Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/fresh-run-followup-fixes-execution-ssot.md`
Temp Mirror Path: `docs/temp/fresh-run-followup-fixes-execution-ssot.md`
Commit State:
- Baseline Commit: `203b328fb35633f9a23fe986862994c8b6dddab7`
- Baseline Dirty Summary: `dirty: post-fresh-run audit docs, stage0/stage2/stage3/stage4 follow-up edits, runtime JSONL drift, tests, docs/2026-03-23/, .tmp_stage0_msg/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-23/fresh-run-3pass-audit-report.md`
- `docs/2026-03-23/weekend-long-function-global-3pass-audit.md`
- `docs/2026-03-20/TF-static-complexity-audit-v2.md`
Evidence Artifacts:
- none
Side-Effect Coverage: covered

## 1. Intent
- Convert the morning fresh-run findings into a bounded post-run fix queue.
- Realize only the findings that are now:
  - clearly live-fixable
  - low-to-medium risk
  - supported by code anchors
- Leave design-tension items and environment-dependent items out of this execution unless a later survey or live repro promotes them.

This item is a fix bundle, not another long-function campaign.

## 2. Baseline Facts
- The fresh run reported:
  - P0 crash / data-loss findings: none
  - refactor-caused regression: none confirmed
  - 213 LLM calls, 100% success
  - ep1-4 completed, ep5 rejected, DI pipeline and caching operational
- The fresh-run report is operationally useful, but contains localized mojibake residue and should not be treated as the sole truth source.
- Live-fixable items with concrete anchors:
  - `three_phase_blueprint_generator.py` Stage 3 pass-rate math can exceed 100%
  - `stage3_orchestrator.py` omits `score_breakdown` when recording Stage 3 attempts into `pass_rate_monitor`
  - `config/prompts/director.yaml` `ENSEMBLE_VARIABLE_PROMPT` still emits template substitution failures
  - session-scope cost wording is easy to misread as total-run cost even though `snapshot_and_reset_scope()` stores residual scope only
- High-risk or environment-dependent findings remain out of scope for this item:
  - V60.97 swap vs Director judgment conflict
  - ep6 retry storm / TF-35 threshold tuning
  - TF-H length-patch semantics
  - NPC encyclopedia DEGRADED
  - XC-002 JSON exception
  - `constraint_summary` missing
  - terminal encoding-only issues

## 3. Scope
Included:
- [three_phase_blueprint_generator.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py#L256)
- [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L1812)
- [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L2499)
- [config/prompts/director.yaml](/c:/Users/User/Desktop/글도비/config/prompts/director.yaml#L37)
- [metrics_collector.py](/c:/Users/User/Desktop/글도비/modules/core/metrics_collector.py#L492)
- [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py#L2339)

Excluded:
- any change to Director verdict policy or candidate-selection semantics
- any threshold tuning for TF-35 / TF-H
- any Stage 4 continuity or length-gate policy changes
- any dist-packaged prompt copy refresh under `dist/` or `geuldobi-desktop/`
- any environment-only issue without a stable code repro
- refresh of the fresh-run report itself; Codex can merge-refresh after implementation audit

## 4. Pass 1. Inventory Summary
- `three_phase_blueprint_generator.py`
  - `get_stats()` computes Stage 3 pass rate from `phase3_pass / total_attempts`, while runtime counters increment `phase3_reject` on retry / reject paths independently; this can push pass rate above 100%
- `stage3_orchestrator.py`
  - Stage 3 PASS and REJECT `pass_rate_monitor.record_attempt(...)` calls omit `score_breakdown`, creating an observability gap relative to Stage 4
- `config/prompts/director.yaml`
  - `ENSEMBLE_VARIABLE_PROMPT` is the anchor reported by fresh run for substitution warnings
- `metrics_collector.py` + `main_a.py`
  - current wording around `snapshot_and_reset_scope()` and shutdown save makes residual session-cost records easy to misread as cumulative total cost

## 5. Pass 2. Semantic Classification
- Class A. Real bugfix
  - Stage 3 pass-rate percentage must not exceed 100%
- Class B. Observability contract fill
  - Stage 3 `score_breakdown` should reach `pass_rate_monitor` for PASS and REJECT
- Class C. Prompt source hygiene
  - `director.yaml` variable prompt should render without substitution warnings
- Class D. Operator wording / UX clarification
  - session residual-cost wording should explain that it is scope residual, not cumulative run total
- Class E. Deferred design or environment issues
  - V60.97 swap conflict
  - retry storm / threshold tuning
  - length-patch semantics
  - NPC encyclopedia / XC-002 / constraint_summary environmental findings

## 6. Side-Effect Map
- file writes / artifacts:
  - source file edits only
  - no intended artifact schema changes
- DB / schema / transaction boundaries:
  - no schema changes
  - Stage 3 monitor payload enrichment changes runtime write contents only
- JSONL / log / audit sinks:
  - Stage 3 `pass_rate_monitor` payload gains `score_breakdown`
  - PromptLoader warning volume should decrease if the template fix works
  - shutdown cost wording may change console/operator logs
- console / UI / operator output:
  - pass-rate summary should no longer show impossible percentages
  - session cost wording becomes clearer
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - PromptLoader cache behavior may require explicit cache invalidation in tests
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Keep the bundle split by certainty:
  - definite bug / contract fixes first
  - wording-only clarification last
- Do not change verdict decisions, retry counts, or gate thresholds in this item.
- Prefer repairing derived metrics and observability payloads over changing core generation semantics.
- Treat `config/prompts/director.yaml` as the only source-of-truth prompt target; do not patch packaged copies.

## 8. Execution Tranches
1. Stage 3 metrics fix
   - repair `ThreePhaseBlueprintGenerator.get_stats()` so displayed Stage 3 pass rate cannot exceed 100%
   - use a denominator aligned with terminal Stage 3 outcomes rather than raw `total_attempts`
   - do not rewrite the broader runtime counter model in this item
2. Stage 3 observability fill
   - pass `score_breakdown` into Stage 3 `pass_rate_monitor.record_attempt(...)` for both PASS and REJECT paths
   - preserve existing best-effort sink semantics
3. Director prompt template fix
   - repair `config/prompts/director.yaml` `ENSEMBLE_VARIABLE_PROMPT` formatting so PromptLoader stops logging substitution failures during normal render
   - keep semantic prompt intent unchanged
4. Cost wording clarification
   - clarify residual-vs-total cost wording around `snapshot_and_reset_scope()` and session save / shutdown logs
   - wording-only; do not change persistence math

## 9. Acceptance Criteria
- Stage 3 displayed pass rate cannot exceed 100% after the fix
- Stage 3 `pass_rate_monitor` records include `score_breakdown` when available for PASS and REJECT
- `PromptLoader` no longer logs template substitution warnings for `director/ENSEMBLE_VARIABLE_PROMPT` in the covered path
- session residual-cost wording clearly distinguishes residual scope from cumulative total
- no verdict-policy, retry-policy, or threshold behavior changes land as part of this item

## 10. Verification Plan
- `python -m py_compile modules/domain/agents/three_phase_blueprint_generator.py modules/core/stage3_orchestrator.py modules/core/metrics_collector.py main_a.py modules/core/prompt_loader.py`
- `python -m pytest tests/test_stage3_orchestrator.py -q`
- `python -m pytest tests/test_blueprint_patch_mode.py -q`
- `python -m pytest tests/test_director_modules.py -q -k "ENSEMBLE_VARIABLE_PROMPT or director_ensemble"`
- `python -m pytest tests/test_prompt_loader.py -q`
- `python scripts/check_utf8_hygiene.py modules/domain/agents/three_phase_blueprint_generator.py modules/core/stage3_orchestrator.py modules/core/metrics_collector.py main_a.py config/prompts/director.yaml docs/2026-03-23/fresh-run-followup-fixes-execution-ssot.md docs/temp/fresh-run-followup-fixes-execution-ssot.md`
- `python scripts/ops_validator.py`

## 11. Guardrails
- Do not change V60.97 candidate swap semantics in this item.
- Do not tune TF-35 or TF-H thresholds here.
- Do not patch packaged prompt copies under `dist/` or `geuldobi-desktop/`.
- Do not reopen environment-dependent P2 items without a fresh repro.
- Keep wording fixes semantics-preserving.

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - implementation merged
  - Codex post-execution audit completed
  - canonical status updated to `closed` or `partially_realized`
- roadmap dependency:
  - none

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - if any included item is already fixed in live code at execution time, shrink scope instead of redoing it

## 14. Closure Note
- Realization state:
  - closed
- Implemented scope:
  - `ThreePhaseBlueprintGenerator.get_stats()` pass-rate denominator aligned to terminal Stage 3 outcomes
  - Stage 3 PASS / REJECT `pass_rate_monitor.record_attempt(...)` now forwards `score_breakdown` when available
  - `config/prompts/director.yaml` `ENSEMBLE_VARIABLE_PROMPT` and `ENSEMBLE_SELECTION_PROMPT` escaped bare JSON braces in `fix_pack`
  - shutdown residual-cost wording clarified in `main_a.py` and `metrics_collector.py`
- Verification evidence:
  - `python -m py_compile modules/domain/agents/three_phase_blueprint_generator.py modules/core/stage3_orchestrator.py modules/core/metrics_collector.py main_a.py modules/core/prompt_loader.py`
  - `python -m pytest tests/test_stage3_orchestrator.py -q` -> `77 passed`
  - `python -m pytest tests/test_blueprint_patch_mode.py -q` -> `31 passed`
  - `python -m pytest tests/test_director_modules.py -q` -> `110 passed`
  - `python -m pytest tests/test_nc3_checklist.py -q` -> `18 passed`
  - `python -m pytest tests/test_prompt_loader.py -q` -> `29 passed`
  - `python scripts/check_utf8_hygiene.py modules/domain/agents/three_phase_blueprint_generator.py modules/core/stage3_orchestrator.py modules/core/metrics_collector.py main_a.py config/prompts/director.yaml docs/2026-03-23/fresh-run-followup-fixes-execution-ssot.md docs/temp/fresh-run-followup-fixes-execution-ssot.md`
  - `python scripts/ops_validator.py`
- Residual risk:
  - V60.97 swap conflict, retry-storm tuning, TF-H semantics, and environment-dependent Stage 4 findings remain intentionally deferred
  - `fresh-run-3pass-audit-report.md` still contains localized mojibake and should be merge-refreshed separately if it will be reused as an operator-facing canonical report
- Temp cleanup:
  - remove `docs/temp/fresh-run-followup-fixes-execution-ssot.md`
  - resync `docs/temp/queue-state.json`
