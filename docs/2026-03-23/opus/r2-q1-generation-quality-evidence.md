Date: 2026-03-23
Document Type: Q1 R2 evidence manifest
Canonical Path: `docs/2026-03-23/opus/r2-q1-generation-quality-evidence.md`

---

## R1 Finding Live Code Anchors (re-verified)

### H-1. V60.97 swap + adaptive gate
- `director_ensemble.py:907-913` — V60.97 swap: `selected_idx = max(qualified_indices, key=...)`
- `director_ensemble.py:939-947` — score reset: `score = 50`, `original_verdict = "CONDITIONAL_PASS"`
- `director_ensemble.py:1187-1198` — adaptive gate: V60.97 branch with threshold check
- R1 anchors at L889-896/921-926/1119-1124 shifted to L907-913/939-947/1187-1198

### H-2. Stage 3 counter (RESOLVED)
- `three_phase_blueprint_generator.py:254-262` — `terminal = phase3_pass + phase3_reject`; rate = pass/terminal
- `three_phase_blueprint_runtime.py:162` — `total_attempts += 1` (per generate() call, not used in rate)

### H-3. Error fallback
- `chief_writer.py:501-544` — `_recover_generate_ensemble_candidates()`: all fail → single retry
- `chief_writer.py:546-564` — `_finalize_generate_ensemble_candidates()`: no candidates → error_fallback dict

### H-4. Cache bypass
- `chief_writer.py:370` — `logging.debug(f"[SILENT] context caching: {e}")`
- `blueprint_ensemble.py:276-281` — cache creation (targeted read, same pattern)
- `arc_ensemble.py:460-468` — cache resolution (targeted read, same pattern)

### H-5. Diversity annotation
- `chief_writer.py:210-265` — `_annotate_candidate_diversity()`: pairwise Jaccard → metadata["diversity"]
- `chief_writer.py:246-249` — warning string stored in metadata only
- `arc_ensemble.py:293-340` — `_summarize_candidate_diversity()`: same pattern

### H-6. Self-critique opacity
- `chief_writer.py:759-768` — `quality_gate.apply_self_critique()` called, no delta logging
- `chief_writer.py:750-751` — `quality_gate.sanitize_leakage()` called, no delta logging

### H-7. Blueprint min scene hardcoded
- `blueprint_ensemble.py:438` — `if scene_count >= 4 and integrated_len >= 500:`

### H-8. Arc tactical warning
- `arc_ensemble.py:609-648` — `logging.warning` for severely short, no `_operator_log`

### H-9. QR-3 silent
- `chief_writer.py:168-172` — `logging.info("[QR-3] ChiefWriter ...")`, no operator log

## Dirty Workspace Changes

### Scene detection 2-pass fix
- File: `modules/validation/blocking_validator_scene_checks.py`
- Status: modified, not staged
- Key diff: `_SCENE_HEADER_RE` regex added (L129-133), 2-pass logic (L157-172), `_analyze_scenes_by_headers()` new method, `_analyze_scenes_by_keywords()` extracted

### Blueprint time_flow truth source
- File: `modules/domain/agents/blueprint_ensemble.py`
- Status: modified, not staged
- Key diff: L1128-1136 — prev manuscript ending 800 chars injected with "시간 진실 소스" header

## T-Report Absorbed Finding Anchors

### T6 P1-2 / T10 F2: Scene detection false-positive
- `blocking_validator_scene_checks.py:44-51` — `_check_required_scenes` returns `passed: True` always
- `blocking_validator_scene_checks.py:129-133` — NEW: `_SCENE_HEADER_RE` pattern
- `blocking_validator_scene_checks.py:157-172` — NEW: 2-pass logic
- Evidence: `projects/0_0323/drafts/ep_0003.txt` L3: `### 씬 1: 보이지 않는 감시망`

### T10 F1 / T6 P1-1: Blueprint time_flow date contamination
- `blueprint_ensemble.py:1128-1136` (dirty) — prev manuscript ending injection
- Evidence: `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` — time_flow mismatch confirmed by T10

### T10 F3: Empty scene_breakdown fields
- Evidence: `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` — scene_1 through scene_5: goal="", summary="", characters=[], key_events=[], content=""

### GQ-1: qualified[0] hardcoded
- `blueprint_ensemble.py:475` — `return qualified_candidates[0], qualified_candidates`

## Fresh-Run Artifact Inventory (0_0323)

### Drafts
| File | Bytes | Estimated Chars |
|------|-------|-----------------|
| `projects/0_0323/drafts/ep_0001.txt` | 12,520 | ~5,200 |
| `projects/0_0323/drafts/ep_0002.txt` | 13,128 | ~5,400 |
| `projects/0_0323/drafts/ep_0003.txt` | 12,831 | ~5,300 |

### Stage 4 Artifacts (12 files)
| Episode | Attempt | Verdict | Files |
|---------|---------|---------|-------|
| ep0001 | att01 | PASS (100) | `selected_candidate__C.txt`, `final_manuscript__C.txt` |
| ep0002 | att01 | PASS (98) | `selected_candidate__C.txt`, `final_manuscript__C.txt` |
| ep0003 | att01 | REJECT (80) | `rejected_best__C.txt`, `rejected_best__C_balanced.txt` |
| ep0003 | att02 | EMPTY (0) | (none) |
| ep0003 | att03 | REJECT (76) | `rejected_best__A.txt`, `rejected_best__A_balanced.txt` |
| ep0003 | att04 | REJECT (98→downgrade) | `selected_candidate__A_asp_correction.txt`, `rejected_best__A_asp_correction.txt` |
| ep0003 | att05 | PASS (98) | `selected_candidate__A.txt`, `patched_after_fix__A.txt` |

### Stage 3 Blueprint Artifacts
| Episode | Attempts | Strategy | File |
|---------|----------|----------|------|
| ep0001 | 2 | emotion_focused | `final_blueprint__emotion_focused.json` |
| ep0002 | 1 | emotion_focused | `final_blueprint__emotion_focused.json` |
| ep0003 | 1 | action_focused | `final_blueprint__action_focused.json` |
| ep0004 | 1 | dialogue_focused | `final_blueprint__dialogue_focused.json` |

## Cross-Reference Summary

| R1 Finding | T5 | T6 | T10 | GC | Fresh Run |
|------------|----|----|-----|----|-----------|
| H-1 V60.97 | — | — | FL (not triggered in 0_0323) | — | not triggered |
| H-2 Counter | — | — | — | — | resolved in live code |
| H-3 Error fallback | F-1 (patch failure) | P2-1 (att02 empty) | — | GQ-3 | ep3 att02 EMPTY |
| H-4 Cache bypass | — | — | — | — | P3-1 PromptLoader failure |
| H-5 Diversity | — | — | — | GQ-5/6 (bias) | balanced 3/3 selected |
| Scene detection | — | P1-2 | F2 | — | 0/5 false positive (pre-fix) |
| Blueprint time_flow | — | P1-1 | F1 (P0) | — | ep3 date contamination |
| Blueprint scene fields | — | — | F3 | — | all empty |
| qualified[0] | — | — | — | GQ-1 (P0) | — |
