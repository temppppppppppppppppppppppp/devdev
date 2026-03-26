# Genre Expansion Family-Native Ingress Wave 1 Canary Report

Date: 2026-03-26
Type: bounded post-closure proof
Governing SSOT: `docs/2026-03-26/genre-expansion-family-native-ingress-normalizer-wave1-execution-ssot.md`
SSOT Status: closed (closure-audited)

## Findings

Both canary probes pass. The ingress normalizer wave 1 achieves its stated acceptance criteria without regression.

## Control Probe: golden canaria

Artifact pair:
- `bible/01_bi_투자물_골든_카나리아 테스트.json`
- `treatments/01_tr_투자물_골든_카나리아 테스트.json`

Raw shape: TR is `list` (60 entries). This is the canonical list path.

| Check | Result | Detail |
| --- | --- | --- |
| `validate_treatment_structure()` | PASS | valid=True, 0 errors, 0 warnings |
| `validate_phase0_files()` | PASS | valid=True, block_count=60 |
| `build_plot_roadmap_from_treatment()` | PASS | 60 entries, all have `block_no` (1-60) |
| `validate_plot_roadmap_entries()` | PASS | 0 warnings, Stage 2 ready |
| `protagonist_config` preservation | PASS | 6 fields intact (world_origin, incarnation_type, regression_point, execution_doctrine, governance_doctrine, secrecy_rule) |
| Unit tests (`test_stage01_helpers.py`) | PASS | 50 passed |
| Unit tests (`test_stage2_preflight_helpers.py`) | PASS | 46 passed |
| Unit tests (`test_stage0_handoff_ingress.py`) | PASS | 5 passed |

List-path non-regression: confirmed. The normalizer admits `list` input unchanged, adds `block_no` via enumeration fallback (golden canaria blocks use `block_id` strings without embedded integers for direct extraction, so enumeration index is the correct fallback), and produces a Stage 2-ready roadmap with 0 warnings.

## Adapter Probe: wuxia_heavenly_physician

Artifact pair:
- `bible/0_bi_wuxia_heavenly_physician.json`
- `treatments/wuxia_heavenly_physician_tr_block_070_draft.json`

Raw shape: TR is `dict` with `blocks` key (70 entries). This is the family-native dict.blocks path.

| Check | Result | Detail |
| --- | --- | --- |
| `resolve_treatment_block_sequence()` | PASS | dict.blocks resolved to list of 70 |
| `validate_treatment_structure()` | PASS | valid=True, 0 errors, 0 warnings |
| `validate_phase0_files()` | PASS | valid=True, block_count=70 |
| `build_plot_roadmap_from_treatment()` | PASS | 70 entries, all have `block_no` (1-70), all unique |
| `validate_plot_roadmap_entries()` | PASS | 0 warnings, Stage 2 ready |
| `protagonist_config` preservation | PASS | 9 family-native fields intact (name, age_at_start, opening_status, initial_goal, mid_goal, final_goal, true_strength, true_weakness, combat_role) |
| `protagonist_config` merge-safe | PASS | additive merge preserves all native fields while accepting runtime subset additions |
| DNA sync path (`force_sync_v25_dna`) | PASS | calls `build_plot_roadmap_from_treatment()`, uses normalized block list |
| Content preservation | PASS | 70/70 entries retain `content` dict |
| Family-native field passthrough | PASS | `martial_ext`, `realm_before`, `realm_after`, `martial_event` present in normalized roadmap entries as raw_data passthrough |

Raw family-native admission: confirmed. The ingress normalizer resolves `dict.blocks`, extracts `block_no` from `block_id` strings (e.g., "Block 1" -> 1), and produces a canonical block list with all original fields preserved.

`block_no` extraction detail: wuxia TR blocks carry `block_id` as "Block N" strings. The normalizer's `_extract_block_no()` falls through to regex extraction (`r"(\d+)"`), correctly producing integer block numbers 1-70.

Stage 2-ready payload: confirmed. All 70 roadmap entries carry `content` dicts with `context/event_villain/solution/reward` fields, producing non-empty payload fragments that satisfy `_collect_stage2_payload_fragments()`. This is a significant improvement from the pre-wave state where the wuxia roadmap produced 140 warnings (70 block_no missing + 70 title/summary only).

## Assessment Summary

| Criterion | Verdict |
| --- | --- |
| List-path non-regression | PASS |
| Raw family-native admission (dict.blocks) | PASS |
| `plot_roadmap` with `block_no` | PASS (both probes, all entries) |
| Stage 2-ready payload survival | PASS (both probes, 0 warnings) |
| `protagonist_config` merge preservation | PASS (merge-safe, no destructive overwrite) |

## Failure Classification

No failure occurred in either probe. No classification needed.

## Residual Observations (non-blocking)

1. Golden canaria's raw BI `plot_roadmap` entries do not carry `block_no` natively. The normalizer assigns them via enumeration index. This is correct behavior (enumeration fallback is the designed last resort), but it means the golden canaria `block_no` sequence is positional rather than semantically extracted.
2. The wuxia BI's raw `plot_roadmap` (as stored in the BI file) still does not carry `block_no`. The ingress normalizer operates on the TR, not the BI's pre-existing roadmap. At runtime, `force_sync_v25_dna()` rebuilds the roadmap from TR, so the BI's raw roadmap is overwritten by the normalized version. This is the intended behavior.
3. `protagonist_config` merge is shallow (`dict.update`). Nested field collision (e.g., both native and runtime having the same key with dict values) would overwrite rather than deep-merge. This is a known residual risk documented in the closure note.

## Evidence Artifacts

- Unit tests: 101 passed (50 + 46 + 5), 0 failed
- Runtime validation scripts: inline Python probe against live artifact files
- No live app run was required; all checks operate at the ingress/handoff contract layer which is fully testable without UI or DB

## Recommendation

No action. Both probes pass cleanly. The ingress normalizer wave 1 closure is validated. No new execution SSOT is warranted by this proof.

---

Control path status: pass
Adapter path status: pass
Should Codex open a new execution SSOT now: no
