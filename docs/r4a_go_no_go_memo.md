# Phase 4-R4-a: async/sync 통일 Go/No-Go 결정 메모

> 작성: 2026-02-15, checkpoint `38a5ab5`
> 기준: R3(a–h) 완료, 테스트 218 passed (unit 29 + pipeline 89 + E2E 22 + regression 78)

---

## 1. 현재 상태 요약

### stage2_orchestrator 내 ThreadPoolExecutor (변경 대상)

| 위치 | 용도 | 워커 | 내부 호출 |
|------|------|------|-----------|
| L890 `_preflight_arc_analysis()` | arc_drive + preflight LLM 2개 병렬 | 2 | `weaver.generate_arc_drive()`, `preflight.analyze()` |

- **1곳만 존재** (L890). 나머지 async 키워드(L60, L288, L305, L625 등)는 `asyncio.gather`/`await` 기반.
- 진입점: `main_a.py` L2041 `asyncio.run(stage_2_arcs_async_logic())` (정상 경로)
- 폴백: L2037-2039 — 이미 이벤트 루프가 돌고 있으면 `ThreadPoolExecutor` → `asyncio.run` 래핑

### 호출 체인 경계

```
main_a.py (sync)
  └─ asyncio.run()
       └─ stage_2_arcs_async_logic() [async]
            ├─ throttled_enrich() [async, asyncio.gather]
            ├─ _preflight_arc_analysis() [sync, ThreadPoolExecutor ← 여기]
            ├─ _preflight_enrichment() [sync]
            ├─ _preflight_validation() [sync]
            └─ _preflight_finalize() [async, await]
```

문제: `_preflight_arc_analysis()`는 **sync 메서드** 내부에서 `ThreadPoolExecutor`로 LLM 호출을 병렬화.
이것을 `async def` + `asyncio.gather`로 바꾸려면 **호출자도 await로 변경** 필요.

### 코드베이스 전체 ThreadPoolExecutor 현황

| 파일 | 횟수 | 용도 |
|------|------|------|
| `stage2_orchestrator.py` | **2** | arc_drive+preflight 병렬 (R4 대상) |
| `chief_writer.py` | 3 | 앙상블 3전략 병렬 LLM |
| `consensus_validator.py` | 3 | 3-LLM 합의 투표 병렬 |
| `arc_ensemble.py` | 3 | Arc 후보 병렬 생성 |
| `blueprint_ensemble.py` | 3 | Blueprint 후보 병렬 생성 |
| `director_auditor.py` | 2 | 투표 병렬 |
| `batch_validator.py` | 7 | 검증 배치 병렬 |
| `base_agent.py` | 1 | 타임아웃 래퍼 |
| `block_enricher.py` | 1 | 블록 배치 병렬 |
| `validation_orchestrator.py` | 1 | 검증 병렬 |
| **합계** | **26** | **10파일** |

---

## 2. 리스크/보상 매트릭스

| 항목 | ThreadPoolExecutor 유지 (현재) | asyncio.to_thread 전환 (R4) |
|------|------|------|
| **성능** | 동일 (IO-bound LLM 호출, GIL 영향 없음) | 동일 (이론적 차이 없음) |
| **안정성** | 검증됨 — 프로덕션 동작 중 | 미검증 — 이벤트 루프 중첩 리스크 |
| **디버깅 난이도** | 스택트레이스에 ThreadPool 프레임 포함 | async 스택트레이스 (약간 개선) |
| **롤백 용이성** | N/A | `git revert` 1커밋이면 충분 |
| **테스트 영향** | 현재 218 passed 안정 | E2E + pipeline 89개 재검증 필수 |
| **파급 범위** | 0파일 | stage2만이면 1파일, 전체이면 **10파일 26곳** |
| **코드 복잡도** | 현재 수준 유지 | sync→async 전환 시 시그니처 변경 연쇄 |

---

## 3. Go/No-Go 판단 기준

### 진행 조건 (모두 충족 시 GO)

1. stage2 내 ThreadPoolExecutor가 **실제 성능/안정성 문제를 유발하는 증거**가 있다
2. 전환 대상이 **stage2 1곳에 한정**되어 파급 범위가 통제 가능하다
3. `_preflight_arc_analysis`를 `async def`로 바꿔도 **호출자 변경이 1~2곳**이다
4. E2E + pipeline 89 + regression 78 = **189개 테스트가 전환 후에도 전량 통과**한다

### 중단 조건 (하나라도 해당 시 NO-GO)

1. 성능/안정성 문제의 **실증 데이터가 없다** (현재 해당)
2. 전환 시 **10파일 26곳 전체 통일**이 기대되어 범위가 과도하다
3. `asyncio.to_thread` 전환이 **이벤트 루프 중첩**(nested `asyncio.run`) 문제를 유발한다
4. 전환 후 E2E/pipeline/regression 테스트가 **1건이라도 실패**한다

---

## 4. 결론: NO-GO

1. 현재 ThreadPoolExecutor는 정상 동작 중이며 성능/안정성 문제의 실증 데이터가 없다.
2. stage2만 바꾸면 코드베이스 내 10파일 26곳과의 패턴 불일치가 오히려 혼란을 증가시킨다.
3. 전환의 실질 보상(디버깅 약간 개선)이 리스크(이벤트 루프 중첩, 189개 테스트 재검증)를 정당화하지 못한다.

---

## 5. 대체안 (NO-GO 시 우선 수행)

### 대체안 1: R3 잔여 테스트 커버리지 보강

- ArcCorrector nested branch (can_correct→correct 실패/revalidation 실패)
- SelfReflector mutation path (JSON 파싱 성공/실패)
- Consensus exception path (예외 시 스킵 동작 확인)
- 기대효과: _preflight_validation 내부 경로 거의 완전 커버 (7/~12 → 10+/~12)

### 대체안 2: 관측성 개선

- ThreadPoolExecutor 병렬 구간에 `perf_timer` 측정 추가 (arc_drive vs preflight 소요시간)
- 실측 데이터 축적 후 전환 필요성 재평가 가능
- 기대효과: 향후 GO 결정 시 정량 근거 확보

### 대체안 3: Phase 3 잔여 품질 기능 설계 착수

- 5-C~5-F 백로그 중 ROI 최대 항목 선별
- 구조 개선보다 사용자 체감 품질 향상에 집중
- 기대효과: 리팩토링 피로 해소, 실질적 제품 가치 증가

---

## 6. (참고) 만약 향후 GO로 전환 시 최소 실행 계획

> 현재는 NO-GO이므로 참고용.

| Step | 작업 | 게이트 |
|------|------|--------|
| R4-a | `_preflight_arc_analysis()` 내 ThreadPoolExecutor → `asyncio.gather` + `asyncio.to_thread` | E2E 22 + pipeline 89 passed |
| R4-b | `main_a.py` L2034-2041 진입점 정리 (nested loop 폴백 제거 가능 여부 확인) | SovereignApp import + E2E passed |
| R4-c | (선택) 나머지 9파일 24곳 일괄 전환 | 전체 테스트 passed |

**전제**: R4-a 단독 실행 후 최소 1주 관찰 기간 → 문제 없으면 R4-b/c 진행.
