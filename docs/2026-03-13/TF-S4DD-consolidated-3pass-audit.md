# TF-S4DD: Stage 4 Detail Deep-Dive 전량 전수조사 — 3pass 감리 최종 보고서

**Date**: 2026-03-13
**Scope**: Stage 4 원고 생산 파이프라인 (~28,000줄, 25+ 파일)
**Method**: 5트랙 병렬 초벌(Pass 1) → 교차검증(Pass 2) → 오탐제거(Pass 3)
**Status**: Read-only audit (코드 수정 없음)

---

## Executive Summary

| 트랙 | CRITICAL | MAJOR | MINOR | INFO | 판정 |
|------|:---:|:---:|:---:|:---:|------|
| T1 Contract & Interface | 0 | 0 | 0 | 8 | CLEAN |
| T2 Logic & Flow | 0 | 0 | 3 | 14 | CLEAN (유지보수 리스크만) |
| T3 Advisory Chain | 0 | 0 | 0 | 6 | CLEAN |
| T4 Data Integrity | 0 | 0 | 1 | 5 | CLEAN |
| T5 Test & Config | 0 | 0 | 3 | 6 | 주의 (기본값 불일치) |
| **합계** | **0** | **0** | **7** | **39** | |

**CRITICAL 0건, MAJOR 0건** — Stage 4 파이프라인은 구조적으로 건전함.

---

## Pass 2: 교차검증 결과

### Cross-1: T2 Threshold ↔ T5 Config (병합)

T2-2.5-1 (7곳 stale defaults)과 T5-5.3 (11곳 stale defaults)은 **동일 루트 원인**:
> `[1M-CTX-P0]` 컨텍스트 확장 후 Python 기본값 미갱신

T5가 `stage4_context_builder.py` 콜사이트를 추가 발견하여 더 포괄적. **T5 집계(11곳) 기준으로 통합**.

| 키 | 코드 기본값 | YAML 값 | 배율 |
|----|-----------|---------|------|
| `retry.director_max_attempts` | 5 | 10 | 2x |
| `context.mandatory_context_max` | 80,000 | 400,000 | 5x |
| `context.lookback_excerpt_chars` | 500 | 5,000 | 10x |
| `context.lookback_total_chars` | 4,000 | 40,000 | 10x |
| `context.vector_max_results_s4` | 20 | 50 | 2.5x |
| `smart_retrieval.stage4_total_budget` | 50,000 | 300,000 | 6x |
| `smart_retrieval.director_total_budget` | 20,000 | 300,000 | 15x |
| `smart_retrieval.slot_max_chars_default` | 1,500 | 3,000 | 2x |
| `smart_retrieval.dense_k` | 10 | 20 | 2x |
| `smart_retrieval.enabled` | False | true | 기능 비활성화 |
| `smart_retrieval.director_enabled` | False | true | 기능 비활성화 |

**리스크**: YAML 로드 실패 시 컨텍스트 5~15x 축소 + smart_retrieval 비활성화. 런타임 영향 없음 (YAML이 정상 로드되면 기본값 무시).

### Cross-2: T2 Loop Invariants ↔ T1 DI Slots

T2에서 검증한 loop_guard, target_ep=None 경로가 T1의 37개 DI 슬롯 중 `blueprint`, `arc_data` 소비와 정합. **교차 확인 통과**.

### Cross-3: T3 Advisory Chain ↔ T4 FactLedger Read-Only

T3에서 확인한 10개 advisory 전부 read-only + T4에서 확인한 FactLedger write는 post_processor만. **교차 확인 통과 — advisory가 데이터 오염 불가**.

### Cross-4: T4 Attempt Logging ↔ T2 Verdict Routing

T2에서 추적한 4개 exit path (PASS/PWF/REJECT/EMPTY)가 T4에서 확인한 `_record_s4_attempt` 호출과 1:1 매핑. **교차 확인 통과**.

단, EMPTY → DB `verdict="ERROR"` 불일치는 T4에서만 발견. T2 verdict routing에는 영향 없음 (DB 기록 레이블만의 문제).

### Cross-5: T5 Coverage Gap ↔ T3 Advisory Chain

T5에서 발견한 "advisory wiring layer 테스트 없음"은 T3에서 확인한 "advisory 체인 자체는 정상"과 결합:
- **개별 advisor 클래스**: 독립 테스트 있음 (truth_gate, npc_drift 등)
- **wiring layer** (`_advisory_*` wrapper + `_run_advisory_chain`): 테스트 없음
- 런타임 리스크: argument 구성, error swallowing, timeout 처리가 미검증

---

## Pass 3: 오탐 제거 및 최종 분류

### MINOR Findings — 최종 분류

| # | Finding | 트랙 | 분류 | 근거 |
|---|---------|------|------|------|
| M-1 | `_threshold()` 11곳 기본값 YAML 불일치 | T2+T5 | **TRUE POSITIVE** | `[1M-CTX-P0]` 이후 기본값 미갱신. YAML 정상이면 무해하나, YAML 삭제/파싱 실패 시 silent degradation |
| M-2 | smart_retrieval 3개 boolean 기본값 False vs YAML true | T5 | **TRUE POSITIVE** (M-1의 부분집합) | 같은 루트 원인. feature 비활성화 리스크 |
| M-3 | `round_num >= 4` 하드코딩 UI 메시지 | T2 | **TRUE POSITIVE (cosmetic)** | 제어 흐름 영향 없음. UI 텍스트만 부정확 |
| M-4 | EMPTY verdict DB 기록 `"ERROR"` vs 반환 `"EMPTY"` | T4 | **TRUE POSITIVE (cosmetic)** | 분석 쿼리에서 혼동 가능. `reject_reason="empty_candidates"`로 필터 가능 |
| M-5 | NumericDrift 항목 내부 `[MAJOR]` 라벨 vs 전체 tier=INFO | T3 | **KNOWN DESIGN** | 항목별 심각도 vs advisory 전체 tier 구분. 기능적으로 정확 |
| M-6 | quality_gate_score `90` 테스트 하드코딩 2건 | T5 | **TRUE POSITIVE (low risk)** | YAML 값 변경 시 테스트 수동 업데이트 필요 |
| M-7 | 테스트 주석 `1500` (구 slot_max_chars_default) | T5 | **TRUE POSITIVE (cosmetic)** | 주석만. 기능 영향 없음 |

### INFO Findings — 특기사항

| Finding | 트랙 | 비고 |
|---------|------|------|
| TruthGate._fact_ledger 저장만 하고 미사용 | T4 | Dead reference 또는 미래 확장용. 해 없음 |
| 28% 메서드 테스트 미커버 (29/105) | T5 | Advisory wiring layer가 최대 갭 |
| Quality label/signal saves 메인 트랜잭션 외부 | T4 | 비차단 설계. 코어 데이터 무결성 영향 없음 |

---

## 교차 의존 매트릭스

```
         T1(계약)  T2(로직)  T3(자문)  T4(데이터)  T5(테스트)
T1(계약)   —       ✓연동    —        —          —
T2(로직)   ✓연동    —       —        ✓연동       ✓병합
T3(자문)   —       —        —        ✓연동       ✓연동
T4(데이터)  —       ✓연동    ✓연동     —          —
T5(테스트)  —       ✓병합    ✓연동     —          —
```

- **✓병합**: T2+T5 threshold 불일치 동일 루트 원인 → 단일 finding으로 병합
- **✓연동**: 교차검증 수행, 결과 정합

---

## 심각도별 리매디에이션 목록

### MINOR — 권장 조치 (긴급도 낮음)

> 실행 기준 메모: `M-2`는 `M-1`의 부분집합이므로 구현/작업 큐에서는 **동일 remediation unit**으로 처리한다.

| 우선순위 | 항목 | 작업 | 영향 범위 |
|---------|------|------|----------|
| 1 | M-1+M-2: `_threshold()` 기본값 11곳 갱신 | Python 기본값을 YAML 값과 동기화 | stage4_orchestrator, stage4_interview_round, stage4_context_builder |
| 2 | M-3: UI 메시지 하드코딩 | `round_num >= 4` → `round_num >= _max_rounds - 1` | stage4_interview_round.py L1426 |
| 3 | M-4: EMPTY verdict 라벨 | `verdict="ERROR"` → `verdict="EMPTY"` | stage4_interview_round.py L1438 |
| 4 | M-6: 테스트 하드코딩 90 | `_threshold("scoring.quality_gate_score", 90)` 사용 또는 상수 참조 | test_stage4_interview_round.py 2건 |
| 5 | M-7: 구 값 주석 | `1500` → `3000` | test_stage4_interview_round.py L2483 |

### DEFERRED — 테스트 커버리지 확충

| 항목 | 설명 |
|------|------|
| Advisory wiring layer | `_run_advisory_chain()` + 8개 `_advisory_*()` wrapper 통합 테스트 |
| Pre-director validation | `_run_pre_director_validation()` 단위 테스트 |
| WritingDirective setup | `_setup_writing_directive()` 단위 테스트 |
| Post-processor persistence | `_memorize_and_validate()`, `_collect_manager_and_build_delta()`, `_run_post_pass_advisories()` |
| Context builder helpers | `_build_condensed_world_state_summary()`, `_build_condensed_fact_ledger_summary()` 등 6건 |

---

## 요약 통계

| 구분 | 건수 |
|------|------|
| 점검 항목 | 30개 (6+6+6+6+5+1 교차) |
| TRUE POSITIVE | 5건 (M-1~M-4, M-6) |
| TRUE POSITIVE (cosmetic) | 2건 (M-3, M-7) |
| KNOWN DESIGN | 1건 (M-5) |
| CLEAN PASS | 22개 항목 |
| 테스트 커버리지 갭 | 29 메서드 (28%) — DEFERRED |

**결론**: Stage 4 파이프라인은 **CRITICAL/MAJOR 0건**으로 구조적 건전성 확인. 유일한 실질 리스크는 `_threshold()` 기본값 11곳의 YAML 불일치로, YAML 정상 로드 시 무해하며 방어적 기본값 갱신으로 해소 가능.

---

## 산출물 목록

| 파일 | 내용 |
|------|------|
| `TF-S4DD-T1-contract-interface-integrity-findings.md` | Track 1: 계약·인터페이스 정합성 |
| `TF-S4DD-T2-logic-flow-correctness-findings.md` | Track 2: 로직·흐름 정확성 |
| `TF-S4DD-T3-advisory-chain-completeness-findings.md` | Track 3: 자문 체인 완전성 |
| `TF-S4DD-T4-data-integrity-findings.md` | Track 4: 데이터 무결성 |
| `TF-S4DD-T5-test-config-alignment-findings.md` | Track 5: 테스트·설정 정합 |
| `TF-S4DD-consolidated-3pass-audit.md` | 본 문서 (3pass 감리 최종) |
