Date: 2026-03-23
Document Type: R2 Q7 context reception evidence manifest
Terminal: T7

---

## Evidence Sources

### Primary Scope Files Verified (R2)

| File | Lines Read | Key Verification |
|------|-----------|-----------------|
| `chief_writer_context_packets.py` | 140-173 | L158: `smart_truncate(prev_manuscripts_text)` — default 1M/80K 확인, R1 P1-1 persists |
| `stage4_context_builder.py` | 100-139, 1130-1216, 1240-1340 | L125: head_ratio=0.55 확인 (P1-2), L1144-1170: 보호 2건만 (P1-3), L1214: emergency ratio=0.68 |
| `stage4_context_packets.py` | grep | L39,91: `npc_names[:10]` 확인 (T9 P2-1/RX-7) |
| `director_ensemble.py` | 720-767, 840-860, grep | L748: `smart_truncate(prev_manuscripts_text)` — **NO** explicit max_chars/head_chars (P1-4 stale) |
| `base_agent.py` | 300-349 | L310-334: `_apply_prompt_size_gate` 확인, MAX_CONTEXT_CHARS=1M |
| `constants.py` | 135-154 | L145: `smart_truncate` default max_chars=1M, head_chars=80K |

### Git Archaeology (P1-4 Stale Verification)

| Commit | Check | Result |
|--------|-------|--------|
| `a3b9a286` (79f570f2의 직전) | `git show a3b9a286:modules/domain/agents/director_ensemble.py \| grep "200000\|150000"` | **0 matches** |
| `ea8a597b` (2커밋 전) | `git show ea8a597b:modules/domain/agents/director_ensemble.py \| grep "200000\|150000\|smart_truncate"` | L729: `smart_truncate(` — **no explicit params** |
| live code | `grep "200000\|150000" director_ensemble.py` | **0 matches** |

**결론**: Director ensemble의 `smart_truncate` 호출에 `max_chars=200000, head_chars=110000` 파라미터가 존재한 적 없음. R1 P1-4는 오보.

### Commit 79f570f2 Diff Analysis (Q7 Impact)

| 변경 | 파일 | Q7 영향 |
|------|------|---------|
| `[:160]` 절삭 제거 (quality_gate_reasons) | `director_ensemble.py:67` | 없음 — logging 범위 (Q8) |
| `[:160]`, `[:120]` 절삭 제거 (contradiction_summary) | `director_ensemble.py:419-422` | 없음 — logging 범위 (Q8) |
| `_short_text()` 한도 제거 (_log_director_frame) | `director_ensemble.py:473-479` | 없음 — logging 범위 (Q8) |
| `_operator_log` score provenance 추가 | `director_ensemble.py:903+` | 없음 — observability (Q8) |
| `ep_type` forwarding | `director_ensemble.py:964` | 없음 — verdict accuracy (Q3) |
| fail-closed guard | `director_ensemble.py:1091+` | 없음 — verdict accuracy (Q3) |
| `[:100]` 절삭 제거 (review_reason) | `director_ensemble.py:1041` | 없음 — logging 범위 (Q8) |
| contradiction_details limit 확장 | `director_ensemble.py:1019+` | 없음 — feedback (Q4) |

**Q7 primary scope에서 dirty 파일**: 0개

### Fresh Run Evidence (projects/0_0323/)

#### Context Budget Usage

| Log Line | Timestamp | Event | Values |
|----------|-----------|-------|--------|
| L2156 | 14:03:38 | `[SC] Context budget` | 2159/300000 (0.72%) — ep1 |
| L2810 | 14:10:20 | `[SC] Context budget` | 2027/300000 (0.68%) — ep2 |
| L3592 | 14:18:47 | `[SC] Context budget` | 1807/300000 (0.60%) — ep3 |

#### Tier Composition

| Log Line | Timestamp | tier0 | tier1 | tier2 | total | limit |
|----------|-----------|-------|-------|-------|-------|-------|
| L2157 | 14:03:38 | 220 | 579 | 2167 | 2970 | 400000 |
| L2811 | 14:10:20 | 1258 | 2291 | 2037 | 5590 | 400000 |
| L2812 | 14:10:20 | 1258 | 2291 | 2158 | 5711 | 400000 |
| L3593 | 14:18:47 | 1413 | 2512 | 1817 | 5746 | 400000 |
| L3594 | 14:18:47 | 1413 | 2512 | 1938 | 5867 | 400000 |

#### Slot Allocation

| Log Line | Timestamp | Stage | Slots | Budget |
|----------|-----------|-------|-------|--------|
| L745 | 13:47:49 | stage3 | 3 | 80000 |
| L1258 | 13:54:22 | stage3 | 4 | 80000 |
| L2777 | 14:10:19 | stage4 | 8 | 300000 |
| L3077 | 14:15:28 | director | 1 | 300000 |
| L3570 | 14:18:46 | stage4 | 7 | 300000 |
| L3828 | 14:22:50 | director | 1 | 300000 |

#### Truncation/Emergency Events

| Event Type | Count | Evidence |
|-----------|-------|---------|
| `[SC:TRIM]` | 0 | grep 결과 없음 |
| `[SC:TRIM:EMERGENCY]` | 0 | grep 결과 없음 |
| `[TF3-H7] Prompt length gate` | 0 | grep 결과 없음 |
| `smart_truncate` 활성 절삭 로그 | 0 | grep 결과 없음 |

### Cross-Reference Verification

| Source | Finding | Q7 R2 상태 |
|--------|---------|-----------|
| T9 P2-1: NPC 10-name cap | `stage4_context_packets.py:39,91` 확인 | persists (supplementary) |
| T9 verdict: fresh-run-before-fix: yes | Q7 판정과 합치 | 흡수 |
| Gen-Coherence RX-1: Tier2 silent drop | `stage4_context_builder.py:1251-1253` 확인 | persists |
| Gen-Coherence RX-2: Emergency ratio=0.68 | `stage4_context_builder.py:1214` 확인 | persists |
| Gen-Coherence RX-7: NPC 10명 캡 | `stage4_context_packets.py:39,91` 확인 | persists |
| Merge Audit: Q7 = long-run structural | 실증 합치 | 흡수 |

### Configuration Values Re-Verified

| Key | Value | Source | R1과 동일 |
|-----|-------|--------|----------|
| `context.max_context_chars` | 1,000,000 | validation.yaml | yes |
| `smart_retrieval.stage4_total_budget` | 300,000 | validation.yaml | yes |
| `smart_retrieval.director_total_budget` | 300,000 | validation.yaml | yes |
| `context.mandatory_context_max` | 400,000 | validation.yaml | yes |
| `smart_truncate` defaults | max_chars=1M, head_chars=80K | constants.py:145 | yes |
| `_fit_context_text` head_ratio | 0.55 | stage4_context_builder.py:125 | yes |
| `_apply_context_budget` protected prefixes | 2개 (`[작품 추적 슬롯 요약]`, `[SC:arc_semantic_carryover]`) | stage4_context_builder.py:1144,1168 | yes |
| Emergency trim protected ratio | 0.68 | stage4_context_builder.py:1214 | yes |
| NPC name cap | 10 | stage4_context_packets.py:39,91 | yes |
