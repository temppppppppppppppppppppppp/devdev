# Memory ROI Boost Plan

- Date: 2026-02-21
- Goal: 단기/장기 기억 회수율을 낮은 비용으로 빠르게 개선
- Scope: 기존 구조 유지, 최소 변경으로 체감 품질 상승

## 1. Why this plan

현재 시스템은 벡터 검색 중심이며, 임베딩 실패 시 빈 컨텍스트로 빠지는 구간이 있다.  
리팩토링급 개편 전에, 작은 변경으로 장기 기억 회수율과 안정성을 먼저 올린다.

## 2. Guiding principles

- Keep architecture: 대규모 스키마 변경 없이 시작
- Improve retrieval quality first: 저장량보다 회수 정확도 우선
- Graceful fallback: 임베딩/외부 API 실패 시에도 검색 공백 최소화
- Measurable rollout: 지표 확인 후 단계적으로 확장

## Blind Spots (Current System)

### B1. Memory contamination prevention (Truth Gate)

- Gap:
  생성된 요약/상태가 검증 없이 장기 메모리로 저장될 수 있다.
- Risk:
  중간 산출물 오류가 장기 기억으로 굳어 downstream 품질 저하를 유발한다.

### B2. Episode-level embedding bias

- Gap:
  사실상 화 단위 저장/검색 중심이며 scene/event chunk retrieval이 없다.
- Risk:
  "관련 장면은 맞지만 화 전체는 덜 관련"인 경우를 놓친다.

### B3. Missing temporal/arc weighting

- Gap:
  검색 우선순위가 유사도 중심이고 최근성/arc 연속성 가중치가 약하다.
- Risk:
  유사하지만 현재 맥락과 먼 오래된 기억이 상위에 노출될 수 있다.

### B4. Weak entity normalization layer

- Gap:
  `entity_names`가 문자열 기반 저장이라 별칭/오탈자/호칭 변형에 취약하다.
- Risk:
  동일 인물이 다른 표기로 분산 저장되어 회수율이 떨어진다.

### B5. Low evidence confidence visibility

- Gap:
  retrieval 결과에 점수/근거 출처가 충분히 노출되지 않는다.
- Risk:
  Writer/Director가 어떤 기억을 더 신뢰해야 하는지 판단하기 어렵다.

### B6. Embedding model drift readiness

- Gap:
  임베딩 모델/차원 변경 시 재색인 정책이 명시적이지 않다.
- Risk:
  장기 운영 중 검색 품질이 갑자기 떨어져도 원인 추적/복구가 느려진다.

### B7. Missing memory-only offline benchmark set

- Gap:
  "이 쿼리면 이 과거 화가 나와야 한다" 형태의 골든셋이 약하다.
- Risk:
  개선/퇴보를 정량적으로 비교하기 어렵다.

## 3. High-ROI quick wins (P0)

### P0-1. Multi-query 결과 선택 로직 개선

- Problem:
  `retrieve_multi_query_context()`가 에피소드 번호 기준 샘플링으로 관련도 높은 후보를 놓칠 수 있음.
- Change:
  거리(distance) 기반 정렬 후 상위 결과를 채택하고, 이후에만 다양성(에피소드 분산) 보정.
- Target:
  `modules/core/vec_memory.py:324`
- Effort:
  Small (0.5 day)
- Expected impact:
  High (관련도 높은 기억 회수 증가)

### P0-2. 임베딩 실패 시 keyword SQL fallback

- Problem:
  임베딩 실패 시 `""` 반환으로 컨텍스트 공백 발생.
- Change:
  임베딩 실패 시 `episode_meta(summary/event_types/entity_names)` 기반 LIKE 검색 fallback 추가.
- Target:
  `modules/core/vec_memory.py:279`
  `modules/core/vec_memory.py:301`
- Effort:
  Small-Medium (0.5~1 day)
- Expected impact:
  High (외부 API 불안정 구간 방어)

### P0-3. 저장 요약 구조 정규화

- Problem:
  summary 텍스트 형식이 일정하지 않아 검색 품질 흔들림.
- Change:
  저장 직전 summary를 4-slot으로 통일:
  `사건 | 인물 | 장소 | 결말`.
- Target:
  `modules/core/stage4_post_processor.py:178`
  `modules/core/vec_memory.py:241`
- Effort:
  Small (0.5 day)
- Expected impact:
  Medium-High (키워드/의미 검색 모두 안정화)

### P0-4. 검색 개수 설정 소폭 상향

- Problem:
  결과 수 제한이 낮아 누락 가능성 존재.
- Change:
  설정 기반으로 `vector_max_results_s2/s4`를 소폭 상향하고 모니터링.
- Target:
  `config/settings/validation.yaml`
- Effort:
  Very Small (0.2 day)
- Expected impact:
  Medium (recall 개선, 비용 소폭 증가)

## 4. Execution plan

### Phase A (Day 1)

- Implement: P0-1, P0-2
- Add tests:
  - 임베딩 실패 fallback 동작
  - distance 우선 선택 검증
- Files:
  `tests/test_vec_memory.py`

### Phase B (Day 2)

- Implement: P0-3, P0-4
- Add tests:
  - summary 정규화 포맷
  - Stage2/Stage4 retrieval 결과 안정성
- Files:
  `tests/test_stage2_preflight.py`
  `tests/test_stage4_context_builder.py`

### Phase C (Day 3)

- Dry run + metric check
- Rollout: 설정값 점진 적용

## 5. Metrics and acceptance criteria

- Retrieval coverage:
  최근 30화 기준 필요한 과거 사건 회수율 상승
- Empty-context rate:
  임베딩 실패 시 빈 문자열 반환율 감소
- Consistency:
  동일 입력 재실행 시 retrieval block 변동폭 감소
- Latency:
  Stage2/Stage4 지연 증가가 허용 범위 내 유지

Acceptance (minimum):
- Empty-context rate 50% 이상 감소
- 장기 회수 누락 케이스 재현 테스트 통과
- 기존 회귀 테스트 무손상

## 6. Risk and rollback

- Risk:
  fallback LIKE 검색이 노이즈를 늘릴 수 있음
- Mitigation:
  상위 N 제한 + 간단 점수 기준 + dedup

- Risk:
  결과 수 상향으로 토큰/지연 증가
- Mitigation:
  설정 플래그로 즉시 복구 가능

Rollback:
- 설정값 즉시 원복
- fallback 경로 feature flag off

## 7. Additional directions (beyond quick wins)

### D1. Light hybrid retrieval (next step)

- Dense + sparse 결합 점수(RRF) 도입
- 대규모 스키마 변경 없이 시작 가능
- 이후 FTS 도입 여부는 지표 보고 결정

### D2. Memory quality observability

- 로그 필드 추가:
  query, dense hit count, fallback used, selected episodes
- "기억 저장 성공률"보다 "기억 회수 성공률"을 핵심 지표로 전환

### D3. Episodic memory curation

- 중요 사건/인물 태그 우선 보존
- 회수 실패 빈도가 높은 패턴을 자동 태깅
- 요약 품질 저하 화 자동 재인덱싱 후보로 큐잉

### D4. Budget-aware context policy

- 예산/토큰 상황에 따라 context 길이 자동 조절
- 낮은 예산에서도 핵심 기억 블록 우선 주입

### D5. Mid-term refactor path (optional)

- 필요 시 별도 문서의 리팩토링급 플랜으로 확장:
  `docs/codex_hybrid_retrieval_refactor_plan.md`

## 8. Priority summary

1. P0-1 distance-first selection
2. P0-2 embedding-failure fallback
3. P0-3 summary normalization
4. P0-4 retrieval-size tuning
5. D1 hybrid fusion (next)

이 순서로 진행하면, 큰 공사 없이도 장기 기억 체감 품질을 가장 빠르게 끌어올릴 수 있다.
