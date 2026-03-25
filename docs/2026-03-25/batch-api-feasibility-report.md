# Batch API 활용 가능성 보고서

**작성일**: 2026-03-25
**대상 시스템**: 글도비 (Wuxia Studio) — 컨텍스트 누적형 장편소설 자동 생산 파이프라인
**결론**: **활용 불가능** (구조적 불가)

---

## 1. Batch API란

| 제공사 | API명 | 할인율 | 응답 SLA | 특징 |
|--------|--------|--------|----------|------|
| Google (Gemini) | BatchGenerateContent | 50% | 최대 24시간 | 비동기, 파일 기반 I/O |
| OpenAI | Batch API | 50% | 최대 24시간 | JSONL 업로드, 폴링 |
| Anthropic | Message Batches | 50% | 최대 24시간 | 10,000건/배치 한도 |

**공통 요건**: 모든 요청의 입력을 사전에 확정하여 일괄 제출 → 비동기 처리 → 결과 수거.

---

## 2. 글도비 파이프라인 구조 요약

```
Stage 2 (Arc 설계)
  │  Arc 1→5 순차 정제, Director 검수
  ▼
Stage 3 (Blueprint 생성)
  │  에피소드 1→N 순차, 앙상블 3종 병렬 + Validator
  ▼
Stage 4 (원고 생산)
  │  에피소드 1→N 순차, 라운드 최대 5회
  │  ├─ ChiefWriter 앙상블 (3종 병렬)
  │  ├─ Python 사전검증
  │  ├─ Advisory 체인 (9종 병렬, 7 LLM + 2 Python)
  │  └─ Director 판정 → PASS | PASS_WITH_FIX | REJECT(재시도)
  ▼
완성 원고 + 상태 갱신 (StateTracker, WorldState, FactLedger)
```

**에피소드당 LLM 호출 수**: 7~13회 (1라운드 기준), REJECT 시 최대 5라운드 반복.

---

## 3. 불가능 판정 — 5대 구조적 이유

### 3-1. 순차 의존 체인 (Sequential Dependency Chain)

```
Blueprint(N) ──▶ ChiefWriter(N) ──▶ Advisory(N) ──▶ Director(N)
                                                        │
                          ┌─────────────────────────────┘
                          ▼
                StateTracker / WorldState / FactLedger 갱신
                          │
                          ▼
                Blueprint(N+1) ──▶ ChiefWriter(N+1) ──▶ ...
```

**에피소드 N+1의 입력은 에피소드 N의 출력에 의존한다.**

- `StateTracker`: NPC 생사, 별칭, 성격 변화 이력
- `WorldState`: 세계 법칙, 세력 판도, 지명
- `FactLedger`: 수치 사실 (나이, 수량, 날짜)
- `ChainLink`: 에피소드 간 연결고리

→ N을 완료하기 전에는 N+1의 프롬프트를 **조립할 수 없다**.
→ Batch API의 전제조건("모든 입력 사전 확정")이 **원천 불충족**.

### 3-2. 비결정적 재시도 루프 (Non-deterministic Retry)

```
Round 1: ChiefWriter → Advisory → Director → REJECT (피드백 생성)
Round 2: ChiefWriter(피드백 포함) → Advisory → Director → PASS_WITH_FIX
```

- Director 판정 결과에 따라 후속 라운드의 **존재 자체가 결정**됨
- REJECT 시 피드백이 다음 라운드 프롬프트에 삽입됨
- 라운드 수 예측 불가 (1~5회) → 배치 요청 건수 자체를 사전에 확정 불가

### 3-3. 앙상블 출력 → 후속 입력 즉시 소비

```python
# chief_writer.py — 3종 병렬 생성
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(generate, strategy): strategy ...}
# 완료 즉시 → Director 선택 → 선택된 원고로 Advisory 체인 진입
```

앙상블 3종은 이미 ThreadPoolExecutor로 **실시간 병렬** 처리 중이다.
이들을 Batch API로 전환하면:
- 실시간 병렬(~3분) → 비동기 배치(최대 24시간)
- **속도 역행**: 현재보다 수백 배 느려짐
- 앙상블 결과를 Director가 즉시 소비해야 하므로 **대기 비용 발생**

### 3-4. Advisory 체인도 동일 구조

```python
# stage4_interview_round.py — 9종 병렬 Advisory
with ThreadPoolExecutor(max_workers=9, thread_name_prefix="advisory") as executor:
    # TruthGate, NpcDrift, Flashback, InfoParadox, RelDrift,
    # LongTermRep, StyleSignal (LLM 7종) + NumericDrift, NumericConsistency (Python 2종)
```

- 이미 9-way 실시간 병렬 (60s/건, 전체 300s 타임아웃)
- Advisory 결과 → Director 판정 프롬프트에 **즉시 삽입**
- Batch API 전환 시: 9건 배치 제출 → 최대 24시간 대기 → Director 진행
  → **에피소드 1편 생산에 24시간+** 소요

### 3-5. 컨텍스트 캐싱이 이미 상위 호환

| 비교 항목 | Batch API | 컨텍스트 캐싱 (현행) |
|-----------|-----------|---------------------|
| 비용 할인 | 50% | 생성 25% + **읽기 90%** |
| 응답 지연 | 최대 24시간 | **실시간** (수 초) |
| 적용 에이전트 | - | ChiefWriter, ArcEnsemble, BprintEnsemble, DirectorEnsemble, DirectorContinuity |
| 캐시 TTL | - | 600s (intra-ep) / 1800s (cross-ep) |
| 순차 호환 | 불가 | **완전 호환** |

컨텍스트 캐싱은 50K자 이상의 반복 컨텍스트를 캐시하여 **읽기 비용 90% 할인**을 실시간으로 제공한다. Batch API의 50% 할인보다 **비용 효율이 높으면서 지연이 없다**.

---

## 4. 이론적 적용 가능 시나리오 (비현실적)

유일하게 Batch API 적용이 **논리적으로 가능한** 경우를 검토한다.

### 4-A. 멀티 프로젝트 동시 생산

```
Project A Episode 1 ─┐
Project B Episode 1 ─┤── Batch 제출 (서로 독립)
Project C Episode 1 ─┘
```

- 서로 다른 프로젝트의 동일 단계 호출을 묶어 배치 제출
- **전제 조건**: 3개 이상 프로젝트를 동시 운영 + 24시간 지연 수용
- **현실성**: 글도비는 단일 프로젝트 순차 생산 워크플로 → **해당 없음**

### 4-B. 사전 평가용 대량 검증

```
기완성 원고 100편 ── Batch 제출 ── 품질 점수 일괄 수집
```

- 이미 생산 완료된 원고를 사후 분석하는 비실시간 작업
- Advisory 체인을 배치로 돌려 품질 메트릭 수집
- **가능은 하나**: 생산 파이프라인과 무관한 별도 유틸리티

### 4-C. 프롬프트 A/B 테스트

```
Prompt Variant A ─┐
Prompt Variant B ─┤── Batch 제출 (동일 입력, 다른 프롬프트)
Prompt Variant C ─┘
```

- 프롬프트 개선 실험 시 동일 입력에 대해 여러 프롬프트 변형을 배치 평가
- **가능은 하나**: 개발/실험 단계 전용, 생산 파이프라인 외부

---

## 5. 수치 비교 요약

### 에피소드 1편 생산 시간 (Stage 4 기준)

| 구분 | 현행 (실시간 병렬) | Batch API 전환 시 |
|------|-------------------|-------------------|
| ChiefWriter 앙상블 | ~3분 (3종 병렬) | 최대 24시간 |
| Advisory 체인 | ~1분 (9종 병렬) | 최대 24시간 |
| Director 판정 | ~30초 | ~30초 (이건 단건) |
| REJECT 재시도 | +4~12분/라운드 | +24시간/라운드 |
| **1편 합계 (1라운드)** | **~8~12분** | **~48시간** |
| **1편 합계 (3라운드)** | **~25~35분** | **~72시간+** |

### 비용 비교 (에피소드당)

| 구분 | 정가 대비 | 비고 |
|------|-----------|------|
| Batch API | 50% 할인 | 24시간 SLA |
| 컨텍스트 캐싱 (현행) | 생성 75% + **읽기 10%** | 실시간, 5개 에이전트 적용 |
| 컨텍스트 캐싱 실효 할인 | **~60-70%** (반복 컨텍스트 비율 감안) | Batch API보다 우위 |

---

## 6. 결론

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   Batch API는 글도비 생산 파이프라인에 적용 불가능하다.  │
│                                                          │
│   근본 원인: 컨텍스트 누적 순차 의존 구조                │
│   - 에피소드 N의 출력이 N+1의 입력을 결정               │
│   - 재시도 루프로 호출 건수 자체가 비결정적              │
│   - 이미 실시간 병렬(ThreadPoolExecutor)로 최적화 완료   │
│   - 컨텍스트 캐싱이 비용/속도 양면에서 상위 호환        │
│                                                          │
│   Batch API 전환 시:                                     │
│   - 속도: ~300배 저하 (12분 → 48시간+)                   │
│   - 비용: 현행 캐싱 대비 열위 (50% vs ~60-70%)          │
│   - 아키텍처: 순차 의존 체인 해소 불가                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Batch API가 유효한 시스템**: 입력이 사전 확정된 대량 독립 요청 (번역, 분류, 임베딩, 사후 분석)
**글도비가 해당하지 않는 이유**: 출력→입력 순환 의존 + 비결정적 분기 + 실시간 상태 누적

---

*이 보고서는 코드 분석 기반이며, 코드 수정 사항 없음.*
