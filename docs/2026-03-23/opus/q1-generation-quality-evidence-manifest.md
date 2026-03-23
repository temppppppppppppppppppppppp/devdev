Date: 2026-03-23
Document Type: Q1 evidence manifest (raw anchors)
Canonical Path: `docs/2026-03-23/opus/q1-generation-quality-evidence-manifest.md`

---

## Primary Scope Files

| File | LOC | Role |
|---|---|---|
| `modules/domain/agents/chief_writer.py` | 2,265 | Stage 4 manuscript ensemble engine |
| `modules/domain/agents/arc_ensemble.py` | 1,527 | Stage 2 arc ensemble generator |
| `modules/domain/agents/blueprint_ensemble.py` | 1,151 | Stage 3 blueprint ensemble generator |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 278 | Stage 3 thin owner shell + stats |

## Supporting Files Inspected

| File | LOC | Scope |
|---|---|---|
| `modules/domain/agents/three_phase_blueprint_runtime.py` | 1,382 | Stage 3 runtime orchestration |
| `modules/domain/agents/chief_writer_context.py` | 511 | CW context assembly |
| `modules/domain/agents/chief_writer_quality.py` | 1,297 | CW quality gate (partial read) |
| `modules/domain/agents/director_ensemble.py` | — | V60.97 swap logic (targeted read) |

## Finding Anchors

### H-1. V60.97 swap cascade
- `director_ensemble.py:889-896` — swap from Director pick to longest qualified
- `director_ensemble.py:921-926` — score reset to 50, verdict to CONDITIONAL_PASS
- `director_ensemble.py:1119-1124` — CONDITIONAL_PASS + V60.97 swap → final REJECT

### H-2. Pass rate counter bug
- `three_phase_blueprint_generator.py:57-63` — stats dict: total_attempts, phase3_pass, phase3_reject
- `three_phase_blueprint_generator.py:257-262` — get_stats(): terminal = pass + reject, rate = pass/terminal
- `three_phase_blueprint_runtime.py:162` — total_attempts += 1 (per generate() call)
- Counter increments for phase3_pass/phase3_reject happen in runtime at retry granularity (not at generate() granularity)

### H-3. Error fallback candidate
- `chief_writer.py:501-544` — _recover_generate_ensemble_candidates(): all fail → single retry
- `chief_writer.py:546-564` — _finalize_generate_ensemble_candidates(): no candidates → error_fallback dict

### H-4. Context cache bypass
- `chief_writer.py:359-370` — cache_info, cache_name, logging.info on success, logging.debug on failure
- `blueprint_ensemble.py:276-281` — _get_or_create_context_cache for blueprint_ensemble
- `arc_ensemble.py:460-468` — _resolve_ensemble_cache_name for arc_ensemble
- All three: cache failure logged at DEBUG, not WARNING

### H-5. Diversity annotation-only
- `chief_writer.py:210-265` — _annotate_candidate_diversity(): 3-gram Jaccard, threshold=0.7, metadata annotation
- `chief_writer.py:247-249` — warning string built but only stored in metadata["diversity"]["warning"]
- `chief_writer.py:563` — annotation called after validation, before return
- `arc_ensemble.py:293-340` — _summarize_candidate_diversity(): same pattern, metadata-only

### H-6. Self-critique opacity
- `chief_writer.py:759-768` — apply_self_critique() called on every candidate
- `chief_writer.py:874-897` — _finalize_single_candidate_critique(): JSON parse, fallback to original
- `chief_writer_quality.py:40-80` — sanitize_leakage(): removes banned keys, no delta logging

### H-7. Blueprint min scene count
- `blueprint_ensemble.py:438` — `if scene_count >= 4 and integrated_len >= 500:`
- Hard-coded, not pacing-aware

### H-8. Arc tactical length warning
- `arc_ensemble.py:609-626` — logging.info for individual filter, _operator_log for individual
- `arc_ensemble.py:639-648` — logging.warning for "severely short", no _operator_log

### H-9. QR-3 silent operation
- `chief_writer.py:120-172` — _load_strategy_bias(lookback=20), _build_strategy_execution_plan()
- `chief_writer.py:168-172` — logging.info with strategy shares
- `arc_ensemble.py:213-271` — same pattern, logging.info only

## Cross-Reference: Fresh Run Findings

| Fresh Run Finding | Q1 Anchor | Status |
|---|---|---|
| P1-1 Ep5 V60.97 auto-swap REJECT | H-1 | **live confirmed** |
| P1-2 Ep6 Blueprint retry storm (7 tries) | H-2 (counter), Stage 3 runtime | **live confirmed** |
| P1-3 Ep1-2 length undershoot → TF-H patch | H-3 (tangential) | **live confirmed** |
| P2-4 Blueprint coverage 60% | H-7 (tangential) | **env-dependent** |
| P3-2 Pass rate > 100% | H-2 | **live confirmed** |

## Strategy Definitions

### ChiefWriter (Stage 4)
- balanced: temp 0.7, Blueprint 충실 재현
- narrative: temp 0.8, 심리 묘사 + 관계 발전
- tension: temp 0.9, 반전 + 클리프행어

### ArcEnsemble (Stage 2)
- conservative: temp 0.3, 안정성과 연속성 우선
- balanced: temp 0.5, 연속성과 새로움의 균형
- creative: temp 0.7, 서사적 흥미 우선

### BlueprintEnsemble (Stage 3)
- action_focused: tension 7-9, 전투/추격/대결
- emotion_focused: tension 4-6, 캐릭터 심리/갈등
- dialogue_focused: tension 3-7, 정보 교환/음모

## Ensemble Timeout Configuration

| Generator | Ensemble Timeout | Single Candidate Timeout | Source |
|---|---|---|---|
| ChiefWriter | 600s | 540s | system.yaml ensemble_timeouts.chief_writer |
| ArcEnsemble | 300s | 240s | system.yaml ensemble_timeouts.arc |
| BlueprintEnsemble | 300s | 240s | system.yaml ensemble_timeouts.blueprint |
