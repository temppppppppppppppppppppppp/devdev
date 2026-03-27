Date: 2026-03-27
Type: evidence manifest
Lane: T3 — Stage 4 Authority / Verdict / Retry Gimmicks
Parent Report: `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict.md`

## File Inventory

| File | Lines | Inspected Sections |
|---|---|---|
| `modules/core/stage4_interview_round.py` | 6,019 | L1-500 (init/helpers), L1150-1400 (attempt/failure), L1940-2086 (writer kwargs), L2240-2740 (run/validation/review/finalize), L3580-3730 (post-select), L4350-4850 (advisory chain) |
| `modules/core/stage4_director_runtime.py` | 1,518 | L1-500 (dataclasses/prevalidation/core), L500-1000 (decision/logging/retrieval) |
| `modules/core/stage4_post_processor.py` | 1,010 | L1-500 (init/helpers/karma/capital) |
| `modules/core/stage4_post_pass_runtime.py` | 1,350 | L1-500 (delegates/submit/memorize/manager) |
| `modules/core/stage4_reject_runtime.py` | 916 | L1-500 (dataclasses/handle_reject/finalize) |
| `modules/core/stage4_retry_runtime.py` | 1,096 | L1-500 (dataclasses/pass_with_fix_loop/generate), L800-900 (retry lane routing) |
| `modules/domain/agents/director_ensemble.py` | 2,298 | L1-500 (helpers/gates/frame), L500-1000 (ensemble candidate/prompt/response/selection), L1340-1440 (decision payload/blueprint) |

## Gimmick Anchors

| Gimmick | Primary Anchor | Consumer Anchor |
|---|---|---|
| G1 `_god1_*` channel | `stage4_interview_round.py:2270-2280` | `stage4_director_runtime.py:102-110` |
| G2 Verdict field precedence | `director_ensemble.py:1346-1397` | `stage4_interview_round.py:2630` (`director_result` consumed) |
| G3 Quality gate mutation | `director_ensemble.py:976-1157` | `director_ensemble.py:1346` (state consumed in decision payload) |
| G4 Advisory chain | `stage4_interview_round.py:4594-4711` | `stage4_director_runtime.py:569` (advisory_summary in input pack) |
| G5 Post-select conflict | `stage4_interview_round.py:3635-3729` | `stage4_interview_round.py:3806` (_process_verdict) |
| G6 PASS_WITH_FIX loop | `stage4_retry_runtime.py:90-236` | `stage4_interview_round.py:3806` (_process_verdict calls loop) |
| G7 Retry lane routing | `stage4_retry_runtime.py:825-896` | `stage4_retry_runtime.py:267` (generate_candidates reads lanes) |
| G8 Contradiction firewall | `director_ensemble.py:449-475` | `director_ensemble.py:990` (_apply_contradiction_firewall_gate) |
| G9 IFC violation escalation | `stage4_reject_runtime.py:477-510` | `stage4_immutable_fact_contract.py` (imported module) |

## Prior Wave Delta

| Prior Finding | Prior ID | Current Status |
|---|---|---|
| Verdict field precedence contract comment | H1/Q1 (2026-03-24 T2) | **REALIZED** — contract comment at `director_ensemble.py:1346-1354` |
| Thin delegate markers | H4/Q2 (2026-03-24 T2) | **NOT REALIZED** — `stage4_post_pass_runtime.py:26-47` has no markers |
| Quality gate mutation docs | H2/Q3 (2026-03-24 T2) | **NOT REALIZED** — no `# Mutates:` annotations |
| Parameter grouping in finalize | H3/Q4 (2026-03-24 T2) | **NOT REALIZED** — 26-param signature unchanged |
| Verdict branching note | H5/Q5 (2026-03-24 T2) | **NOT REALIZED** |
| Retry lane routing header | H6/Q6 (2026-03-24 T2) | **NOT REALIZED** |
| EnsembleSelectionState docstring | H7/Q7 (2026-03-24 T2) | **NOT REALIZED** |

## Elegance Criteria Evidence

For each gimmick, the 5-criterion test from the master order:

| Gimmick | One Owner | Explicit Input | Explicit Precedence | Minimal Hidden State | 2-4 Hops | Verdict |
|---|---|---|---|---|---|---|
| G1 `_god1_*` | YES (annotated) | NO (setattr) | N/A | **NO** (hidden mutation) | 2 files | **Inelegant** |
| G2 Verdict fields | YES | YES (state) | **YES** (comment) | YES | 1 file | **Elegant** |
| G3 Quality gates | YES | YES (state) | NO (call order) | PARTIAL (mutation) | 1 file | **Mixed** |
| G4 Advisory chain | YES | YES (params) | YES (peers) | YES (cloned) | 1 file | **Elegant** |
| G5 Post-select | YES | YES (params) | YES (after director) | YES (tuple return) | 1 file | **Elegant** |
| G6 PWF loop | YES | YES (params) | YES (verdict gate) | YES (dataclass) | 1 file | **Elegant** |
| G7 Retry lanes | YES | YES (dataclass) | NO (boolean) | YES (dataclass) | 1 file | **Mixed** |
| G8 Firewall | YES | YES (params) | YES (explicit) | YES (pure fn) | 1 file | **Elegant** |
| G9 IFC escalation | YES | PARTIAL | NO (implicit) | YES | 2 files | **Mixed** |
