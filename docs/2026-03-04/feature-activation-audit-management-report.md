# Feature Activation Audit 경영 보고

---

## 1. 보고 개요

| 항목 | 내용 |
|------|------|
| 분석일 | 2026-03-04 |
| 대상 프로젝트 | projects/000000 |
| 세션 로그 | 8개 (session_20260303_133915 ~ session_20260303_151852) |
| 메트릭 파일 | episode_production.jsonl, quality_metrics.jsonl |
| 분석 기준 | Python open() + 문자열 처리, 자동 검색 커맨드 미사용 |

---

## 2. 핵심 지표 요약표

### Advisory 모듈별 발화 건수

| 모듈 | 발화 건수 |
|------|---:|
| FlashbackVerifier | 6 |
| InfoParadoxChecker | 4 |
| NpcDriftAdvisor | 0 |
| TruthGate | 0 |
| RelationshipDriftAdvisor | 0 |
| LongTermRepetitionAdvisor | 0 |
| NumericDriftAdvisor | 0 |
| **합계** | **10** |

### VecMemory Hit/Miss/Unknown

| 구분 | 건수 | 비율 |
|------|---:|---:|
| Hit (hits≥1) | 123 | 56.16% |
| Miss (hits=0) | 33 | 15.07% |
| Unknown (hits 미기록) | 63 | 28.77% |
| **전체 [VecMem] 줄 수** | **219** | **100.00%** |
| 히트율 (known only, 156건 기준) | — | 78.85% |
| 히트율 (전체 219건 기준) | — | 56.16% |

### 1차 합격률

| 구간 | 표본 수 | 합격 수 | 1차 합격률 |
|------|---:|---:|---:|
| 1~10화 | 18 | 15 | 83.33% |
| 11~20화 | 11 | 8 | 72.73% |
| 21~25화 | 6 | 5 | 83.33% |
| **전체** | **35** | **28** | **80.00%** |

### Director prompt_len 구간별 건수 및 response_len=2

| prompt_len 구간 | 호출 건수 | response_len=2 건수 | response_len=2 비율 |
|------|---:|---:|---:|
| 1,000 미만 | 0 | 0 | — |
| 1,000~4,999 | 30 | 13 | 43.33% |
| 5,000~19,999 | 27 | 0 | 0.00% |
| 20,000 이상 | 18 | 0 | 0.00% |
| **전체** | **75** | **13** | **17.33%** |

---

## 3. 상세 결과

### 3-1. Advisory Chain

- 전체 7개 모듈 중 발화 실적이 있는 모듈: **2개** (FlashbackVerifier, InfoParadoxChecker)
- 발화 실적이 없는 모듈: **5개** (NpcDriftAdvisor, TruthGate, RelationshipDriftAdvisor, LongTermRepetitionAdvisor, NumericDriftAdvisor)
- NpcDriftAdvisor: 발화 마커(`NpcDriftAdvisor` 포함 줄) 자체가 0건
- 전체 발화 합계: 10건 (FlashbackVerifier 6건, InfoParadoxChecker 4건)

### 3-2. VecMemory

히트율 0.00% 쿼리 타입 (전수):

| 쿼리 타입 (앞 15자) | 히트 | 미스 | 히트율 |
|---|---:|---:|---:|
| 장르 맥락 키워드: 포트폴리 | 0 | 7 | 0.00% |
| 장르 맥락 키워드: 레버리지 | 0 | 7 | 0.00% |
| 아크 전술 연속성: [제 1 | 0 | 5 | 0.00% |
| 관계 변화 이력: 한정호, | 0 | 5 | 0.00% |
| 장면1: 한미증권을 나선 한 | 0 | 2 | 0.00% |
| 아크 전술 연속성: 제 5화 | 0 | 2 | 0.00% |
| 관계 변화 이력: 박성호 | 0 | 2 | 0.00% |
| 장면1: 한시우가 다이닝룸에 | 0 | 1 | 0.00% |

히트율 0.00% 이외 쿼리 타입:

| 쿼리 타입 (앞 15자) | 히트 | 미스 | 히트율 |
|---|---:|---:|---:|
| 한시우 한정호 한태준 한태민 | 24 | 2 | 92.31% |

### 3-3. 합격률 통계

- 전체 1차 합격률: **80.00%** (28/35)
- 1차 불합격 건수: 7
- 실패 최다 에피소드 TOP3: ep2 (1건), ep7 (1건), ep8 (1건)
- quality_metrics.jsonl score 분포 (82건):

| score 구간 | 건수 |
|---|---:|
| 0~59 | 32 |
| 60~69 | 0 |
| 70~79 | 5 |
| 80~89 | 1 |
| 90~100 | 44 |
| 최솟값 / 최댓값 / 평균 | 0.00 / 100.00 / 59.95 |

### 3-4. Director 호출 분포

- call_start agent=Director: **75건**
- call_success agent=Director: **74건**
- response_len=2 전체: **13건** (전체 대비 17.33%)
- response_len=2는 1,000~4,999자 구간에서만 발생 (해당 구간 내 비율 43.33%)

---

## 4. 데이터 품질

| 항목 | 건수 |
|------|---:|
| JSON 파싱 실패 (episode_production) | 0 |
| JSON 파싱 실패 (quality_metrics) | 0 |
| 필드 누락 제외 (episode_production) | 8 |
| 필드 누락 제외 (quality_metrics) | 0 |
| call_start↔call_success 매칭 실패 | 1 |

- 실제 사용 키: episode=`ep`, verdict=`verdict`, attempt=`round`, score=`score`
- 탐지된 최소 시도값: `round=0` (1차 시도 기준으로 처리)

---

## 5. 확인된 사실 요약

- Advisory 7개 모듈 중 5개(71.43%)는 분석 대상 전 세션에서 발화 건수 0건이다.
- VecMemory 히트율 0.00% 쿼리 타입은 8종이며, 이 중 최다 미스는 `장르 맥락 키워드` 2종(각 7건)이다.
- 전체 1차 합격률은 80.00%(28/35)이며, 11~20화 구간이 72.73%로 3개 구간 중 최저다.
- Director 호출 75건 중 response_len=2는 13건(17.33%)이며, 전량 1,000~4,999자 구간에서 발생했다.
- quality_metrics score 분포는 0~59 구간 32건(39.02%)과 90~100 구간 44건(53.66%)으로 양극화되어 있다.
