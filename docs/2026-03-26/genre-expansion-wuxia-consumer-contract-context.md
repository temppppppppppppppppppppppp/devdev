# Genre Expansion Wuxia Consumer-Contract Context

Date: 2026-03-26
Status: final
Type: bounded system-track context memo

## Purpose
- Preserve the current understanding of how Geuldobi actually consumes `BI/TR` during runtime.
- Record why `golden canaria` currently works and why `wuxia_heavenly_physician` does not enter the same path cleanly.
- Leave implementation to another machine; this document is context only.

## Scope
- Runtime ingress from selected `BI/TR` into `main_a.py` and Stage 2.
- Downstream Stage 3/4 context consumption only insofar as it affects genre expansion risk.
- Persistence, rollback, and operator surface behavior only at a contract level.

## Out of Scope
- Code patching.
- Narrative quality judgment.
- Re-auditing TR/BI production harness quality in full.

## Commit State
- Baseline Commit: `faf5f126af61d56f5bd6ee837df4066cd6c16174`
- Baseline Dirty Summary: `dirty: 4 untracked; surfaces: docs/2026-03-26/genre-expansion-consumer-contract-survey-master-order.md, docs/temp/wuxia_block1_check.md, docs/temp/wuxia_heavenly_physician_rebuild.json, docs/temp/wuxia_heavenly_physician_rebuild_audit.md`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Target Artifacts
- Stable baseline BI: `bible/01_bi_투자물_골든_카나리아 테스트.json`
- Stable baseline TR: `treatments/01_tr_투자물_골든_카나리아 테스트.json`
- Candidate BI: `bible/0_bi_wuxia_heavenly_physician.json`
- Candidate TR: `treatments/wuxia_heavenly_physician_tr_block_070_draft.json`

## Evidence Basis
- Operator-run parallel survey outputs from Terminal 1 through Terminal 5 on 2026-03-26.
- Local spot-checks against the live workspace:
  - `modules/core/project_manager.py`
  - `modules/core/response_schemas.py`
  - `modules/core/stage0_handoff.py`
  - `main_a.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage2_preflight.py`
  - `modules/domain/agents/analyst.py`
  - `modules/domain/agents/chief_writer_context.py`
  - `modules/core/constants.py`
  - `modules/core/martial_manager.py`
  - `modules/api/process_runner.py`
  - `scripts/process_and_audit_tr_bi_loop.py`

## Executive Verdict
- The current system does not consume raw family-native `BI/TR` directly.
- The real runtime contract is `ingress-normalized treatment list + Stage2-ready plot_roadmap + minimally compatible protagonist_config`.
- `golden canaria` works because its artifacts already fit, or can be promoted into, that runtime contract.
- `wuxia_heavenly_physician` currently fails primarily at ingress and Stage 2 readiness, not because Stage 3/4 or persistence inherently reject wuxia.

## Canonical Consumer Model
1. Runtime ingress loads `BI/TR`, validates shape, and injects `plot_roadmap` into the working bible.
2. Stage 2 accepts only a `plot_roadmap` that passes `check_plot_roadmap_ready()`.
3. Stage 3/4 mostly tolerate missing fields, but default aggressively and can silently contaminate genre assumptions.
4. Persistence and rollback survive the current wuxia sample because it already carries `MartialHUD`, but the layer remains structurally martial-centric.

## Confirmed Hard Blockers

### 1. TR shape mismatch at ingress
- `validate_treatment_structure()` requires the loaded treatment to be a list and rejects dict-wrapped TR data.
- Local spot-check:
  - `modules/core/response_schemas.py:827-828`
  - `if not isinstance(treatment_data, list): return False, ["Treatment 데이터가 list 형식이 아닙니다"], []`
- Runtime helper spot-check:
  - `validate_phase0_files(golden_bi, golden_tr) -> True`
  - `validate_phase0_files(wuxia_bi, wuxia_tr) -> False`
  - failure reason: `Treatment 데이터가 list 형식이 아닙니다`

### 2. DNA sync path assumes list iteration
- `force_sync_v25_dna()` iterates `treatment_data` directly and builds `plot_roadmap` entry-by-entry under a list assumption.
- Local spot-check:
  - `modules/core/project_manager.py:842`
- If the dict-wrapped wuxia TR reaches this path without prior normalization, the loop reads wrapper keys instead of block dicts.

### 3. Stage 0 handoff only unwraps `treatments`, not `blocks`
- `build_plot_roadmap_from_treatment()` checks `dict["treatments"]` but not `dict["blocks"]`.
- Local spot-check:
  - `modules/core/stage0_handoff.py:20-24`
- Result: current wuxia TR does not normalize into a runtime roadmap through this helper.

### 4. Raw wuxia BI roadmap fails Stage 2 readiness
- `check_plot_roadmap_ready()` returns not ready if any entry is warning-bearing.
- Local spot-check:
  - `modules/core/stage0_handoff.py:130-163`
  - `modules/core/stage2_orchestrator.py:305-310`
  - `main_a.py:4404-4409`
  - `main_a.py:4723-4729`
- Runtime helper spot-check against `bible/0_bi_wuxia_heavenly_physician.json`:
  - `roadmap_len = 70`
  - `ready = False`
  - `warning_count = 140`
  - first warnings:
    - `roadmap[0]: block_no missing`
    - `roadmap[0] (block_no=?): title/summary only; no Stage 2 consumer-backed payload`

## Soft Degradation and Structural Debt

### 1. `protagonist_config` is not runtime-compatible as-is
- Phase 0 helper builds a narrow runtime-oriented config:
  - `modules/core/stage01_helpers.py:224-229`
- Save helper fully overwrites the existing BI config instead of merging:
  - `modules/core/stage01_helpers.py:307-313`
- The wuxia BI uses a different schema centered on name/goal/combat-role data, so overwrite behavior risks losing family-native protagonist identity.

### 2. Stage 3/4 defaults can silently contaminate genre assumptions
- `Analyst` defaults:
  - `modules/domain/agents/analyst.py:221-234`
  - `world_origin -> "원시인"`, `incarnation_type -> "회귀자"`
- `Chief Writer` defaults:
  - `modules/domain/agents/chief_writer_context.py:329-331`
  - `world_origin -> "원시인"`, `incarnation_type -> ""`
- `Stage 4` also reads `protagonist_config` and falls back to `"미상"` when fields are missing:
  - `modules/core/stage4_orchestrator.py:2161-2182`
- This is mostly not a crash path; it is a silent prompt/context distortion path.

### 3. Stage 2 only recognizes a narrow payload family
- `_collect_stage2_payload_fragments()` reads:
  - top-level `context/event_villain/solution/reward`
  - nested `content.*`
  - `genre_ext`
  - `tactical_doc`
  - `key_events`
- Local spot-check:
  - `modules/core/stage0_handoff.py:85-127`
- Wuxia-specific fields such as `martial_ext`, `realm_before`, `realm_after`, `martial_event` do not currently contribute to readiness.

### 4. Persistence survives wuxia but remains martial-biased
- HUD root selection falls back to `MartialHUD` for unknown genres:
  - `modules/core/constants.py:432-434`
- `MartialManager` reads and writes `MartialHUD` directly:
  - `modules/core/martial_manager.py:133-155`
  - `modules/core/martial_manager.py:308-309`
- This does not block the current wuxia sample, but it is not a genre-neutral design.

### 5. Operator and audit surfaces still show investment/martial bias
- API runner defaults missing `genre_index` to investment:
  - `modules/api/process_runner.py:721`
  - `modules/api/process_runner.py:744`
- Offline TR/BI audit loop assumes `FinanceHUD` and investment capital fields:
  - `scripts/process_and_audit_tr_bi_loop.py:141-156`
  - `scripts/process_and_audit_tr_bi_loop.py:175-185`
- These are not the primary runtime blockers, but they will produce false negatives for broader genre expansion.

## Practical Interpretation
- `천의무쌍` is not yet a drop-in artifact pair for the current `main_a` runtime path.
- The main failure is not “wuxia is unsupported”; it is “the current runtime ingress expects a canonical internal contract that the current wuxia pair does not yet normalize into.”
- Once ingress normalization exists, most of the remaining risk moves from `P0 runtime block` to `P1/P2 quality drift`.

## Recommended Implementation Direction For The Other PC
- Keep raw family-native `BI/TR` as source truth.
- Add a single ingress normalizer before runtime consumers:
  - accept `list`, `dict.blocks`, and `dict.treatments`
  - normalize into one treatment block list
  - rebuild runtime `plot_roadmap` from TR when TR is available
  - map `block` to `block_no`
  - merge `protagonist_config` instead of overwriting it
  - guarantee a small universal runtime subset with blank-safe defaults
- Avoid widening Stage 2/3/4 to directly consume multiple raw family schemas.

## Canary-Protecting Rule
- Do not change the internal runtime contract just to admit raw wuxia artifacts.
- Preserve `golden canaria` as the canonical runtime canary.
- If a future patch is made, the safer test split is:
  - `golden canaria`: canonical runtime-contract canary
  - `wuxia_heavenly_physician`: ingress-adapter canary

## Deferred Work
- Any code patch.
- Any DB schema redesign for non-martial trackers.
- Any operator dashboard redesign.
- Any family-wide narrative harness redesign.

## Audit Status
- Pass 1: structure and scope checked against the current request.
- Pass 2: claims bounded to operator survey outputs plus local code/helper spot-checks.
- Pass 3: operating consequence and future implementation seam made explicit.
- Estimated confidence: 0.97

## Save Consequence
- This memo is intended to unblock later implementation on another PC.
- Treat it as context and boundary guidance, not as a patch instruction set.
