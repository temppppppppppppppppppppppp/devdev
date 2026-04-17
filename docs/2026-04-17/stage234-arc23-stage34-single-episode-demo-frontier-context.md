# Stage234 Arc2/3 Stage34 Single-Episode Demo Frontier Context

Date: 2026-04-17
Status: final (current session context note; 3-pass sanity-read completed before save)
Canonical Path: `docs/2026-04-17/stage234-arc23-stage34-single-episode-demo-frontier-context.md`

## 1. Current branch and head

- branch: `codex/post-merge-authority-drift-refresh`
- synced branch head at session start: `6325ad427afd75c73abc37b32b29ec217ffe2f9a`
- no live `python` runtime remained after the partial `stage34_ep7_r3` run was explicitly stopped

## 2. What is already proven

- the Arc2/3 Stage2 post-patch proof remains green in bounded scope from the earlier `r1` canary chain
- the exact failed-lineage Stage3 follow-up is now green: `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2` records `ep7 PASS`, `score 95`, `attempt 2`, `prevalidation 0`, `binding 0`
- the Stage34 demo utility now has two bounded contract upgrades:
  - sparse-target Stage4 summary analysis can validate only the intended regenerated draft episode instead of assuming `draft_count == target_ep`
  - missing exact frozen-authority `draft/manuscript` now downgrades to a warning when earlier authority history exists, rather than always hard-failing the demo boundary

## 3. What the fresh `r3` attempt proved

- fresh target prepared: `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r3`
- source used for that run: `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2`
- the source lineage still had `blueprints 1..7` but only `manuscripts 1..2`
- because Stage4 runtime starts from `current_project.get_latest_episode_number()`, the effective Stage4 frontier for this lineage was still `ep3`, not `ep7`
- the live run therefore entered sequential Stage4 catch-up (`ep3`, then `ep4`, and onward) instead of an `ep7`-only proof surface
- user interruption happened after a long live run; the process had to be explicitly stopped afterward

Partial `r3` evidence left behind:

- manuscripts persisted through `ep3`
- Stage4 attempts were recorded through `ep4`
- no final `stage34_ep_demo_canary_summary.json` was produced
- `r3` is therefore a partial evidence target, not a clean closure-grade canary

## 4. Current authoritative reading

- the active blocker is no longer well-described as only `frozen_authority_draft_missing:ep6`
- the stronger and more accurate reading is: this lineage currently has a `single-episode Stage34 demo frontier/source-contract mismatch`
- said differently, `target_ep=7` was not ignored; the runner contract still means `start from the current manuscript frontier and continue until target`, and this source's frontier was `ep3`

## 5. Follow-up that should happen next

1. do not reuse `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r3` as the clean next proof target
2. keep the Arc2/3 proof lane bounded and `partially_realized`
3. before any new downstream Stage34 replay, choose one of the two valid next moves:
   - prepare a source whose Stage4 frontier is already aligned to `ep7` so the single-episode demo contract is actually true at runtime
   - revise the Stage34 demo runner more deeply so Stage4 can operate as a genuine sparse single-target proof flow rather than sequential catch-up
4. only after one of those two paths lands should a fresh `r4+` Stage34 demo replay be attempted

## 6. Guardrail now in code

- `scripts/run_stage34_ep_demo_canary.py` now fails fast before the live run if the resolved Stage4 `start_ep` does not equal the requested `target_ep`
- this prevents another long-running partial demo from silently turning into sequential catch-up on a non-aligned source lineage

## 7. Validation completed in this session

- `python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -q`
- `python -m pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`
- `python -m pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q`
- `python -m pytest tests/test_run_stage34_ep_demo_canary.py -q`
- `python -m pytest tests/test_stage4_canary_tools.py -k "sparse_required_draft_eps or metadata_only_sink_warn or companion_only_sink_warn" -q`
- `python scripts/check_utf8_hygiene.py modules/core/stage4_canary_tools.py scripts/run_stage34_ep_demo_canary.py tests/test_run_stage34_ep_demo_canary.py tests/test_stage4_canary_tools.py`
