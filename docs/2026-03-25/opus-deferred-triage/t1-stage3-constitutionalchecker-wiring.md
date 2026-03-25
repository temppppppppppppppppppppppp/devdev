# T1. Stage 3 ConstitutionalChecker Dynamic Wiring — Triage Report

Date: 2026-03-25
Status: final
Document Type: lane triage report
Canonical Path: `docs/2026-03-25/opus-deferred-triage/t1-stage3-constitutionalchecker-wiring.md`
Lane: T1 of `deferred-followups-yesno-triage-7terminal-master-order.md`
Mode: survey only — no code changes

## 1. Question

Does wiring `get_architect_constitution()` into live Stage 3 prompt assembly have strong enough ROI now, or should it wait for fresh canary evidence after the static self-audit wave?

## 2. Findings

### Finding A. The static self-audit checklist was just landed and is untested

The self-audit wave (execution SSOT: `stage3-blueprint-self-audit-wave-execution-ssot.md`, status: closed) inserted a static 7-item `자가 검증 체크리스트` into `config/prompts/ensemble.yaml` at L378.

- File anchor: `config/prompts/ensemble.yaml:378`
- Items cover B1 (unacquired items), B2 (cliffhanger continuity), B3 (scene count), B4 (ending_hook), B5 (tactical_doc scope), plus density/location items
- This is a zero-to-one structural gap closure
- **No fresh canary has run since this change landed.** The closure note explicitly states: "self-audit remains prompt-instruction only; real compliance still needs a fresh canary/live run"

### Finding B. Dynamic wiring adds marginal value over the static checklist

`ConstitutionalChecker.get_architect_constitution()` (`modules/core/constitutional_checker.py:277-315`) generates:

1. **B1-B5 constitutional articles** — already covered by the static checklist in `ensemble.yaml`
2. **Dynamic `ending_hook` injection** from `prev_blueprint` (up to 150 chars, L291-295)
3. **Dynamic `tactical_doc` injection** from `arc_data` (up to 200 chars, L298-302)

The dynamic data (items 2 and 3) is **already present** in the blueprint prompt through existing channels:
- `prev_info` parameter in `_generate_single()` carries previous blueprint information including ending_hook
- `arc_focus` carries tactical_doc content extracted via `_resolve_blueprint_arc_focus()` (L215-252)
- `constraints_str` from `_format_constraints()` includes the full authority-banded constraint block with continuity, inherited state, and stop-line content

The net unique content from dynamic wiring would therefore be a reformatted duplication of data already in the prompt — not new information.

### Finding C. Wiring cost is moderate and crosses multiple DI surfaces

The Stage 2 wiring pattern (`stage2_preflight_runtime.py:272-277`) shows how constitutional_checker is threaded:

1. `SovereignApp.constitutional_checker` is bootstrapped at `sovereign_bootstrap_runtime.py:432`
2. `Stage2Context.__slots__` includes `constitutional_checker` (`stage2_context.py:159`)
3. `Stage2Context.from_app()` extracts it (`stage2_context.py:341`)
4. `stage2_preflight_runtime.py:272` calls `self.ctx.constitutional_checker.get_full_injection(stage=2, ...)`

Replicating this for Stage 3 requires:
- Add `constitutional_checker` slot to `Stage3Context` (`stage3_context.py`) — 1 slot, `__init__` param, `from_app` line
- Pass to `ThreePhaseBlueprintGenerator` → `BlueprintEnsembleGenerator` (`three_phase_blueprint_generator.py:48`)
- Call in `_build_blueprint_prompt_bundle()` or `_generate_single()` (`blueprint_ensemble.py:641+`)
- **3-4 production file changes, new DI wiring path**

### Finding D. Token cost adds up without clear return

- Current `BLUEPRINT_GENERATION_PROMPT` is ~2,000-3,000 tokens (survey estimate)
- Static self-audit checklist added ~150-250 tokens
- `get_architect_constitution()` output adds ~300-500 tokens per candidate
- With 3 parallel candidates, total additional cost: ~900-1,500 tokens per episode
- The self-audit survey (`pre-director-self-audit-stagewise-survey-report.md`) estimated 200-300 tokens for constitutional injection — but that was before the static checklist existed. Now both would run, compounding the cost with overlapping content.

### Finding E. Attribution would be muddied

The static checklist was just landed. If dynamic wiring is added before a canary run:
- There is no way to attribute quality changes to static vs dynamic self-audit
- The operating preference (per `bp-clarity-density-4terminal-merge-audit.md`, Finding D) has been to maintain single-variable canary attribution
- The self-audit wave closure explicitly chose approach B (inline) over approach A (wire ConstitutionalChecker) to preserve clean attribution

## 3. Blast-Radius Note

If wiring were attempted now:
- **Files touched**: `stage3_context.py`, `three_phase_blueprint_generator.py`, `blueprint_ensemble.py`, possibly `stage3_orchestrator.py`
- **Runtime impact**: additional ~900-1,500 tokens per episode in prompt budget, duplicated checklist content
- **Attribution risk**: blocks clean canary evaluation of the static self-audit wave
- **Revert cost**: moderate (DI slot addition is low-risk but multi-file)

## 4. Confidence

Estimated confidence: 96%

Why this clears the 95% gate:
- All claims backed by live code evidence with file:line anchors
- The overlap between static checklist and dynamic injection is structurally verifiable (same B1-B5 articles)
- The context duplication claim (ending_hook, tactical_doc already in prompt) is confirmed by reading `_generate_single()` parameter assembly at `blueprint_ensemble.py:562-639`
- The attribution concern is directly supported by the operating principles documented in the merge audit

Limits:
- This assessment does not predict whether the static checklist will show positive signal in the next canary
- If the static checklist proves insufficient, the incremental value of dynamic wiring may rise

## 5. Verdict

Lane verdict: later after canary
Best bounded next wave from this lane: ConstitutionalChecker Stage 3 dynamic wiring (only if static self-audit canary shows positive but incomplete signal)
Should Codex open an execution SSOT from this lane now: no
