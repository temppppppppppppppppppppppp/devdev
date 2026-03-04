# Feature Activation Audit 결과

> 분석일: 2026-03-04
> 대상: projects/000000, 세션 로그 8개

## 1. Advisory Chain 활성화 현황

| 모듈 | 발화 건수 | 호출/추정 | 비고 |
|---|---:|---:|---|
| FlashbackVerifier | 6 | - | `FlashbackVerifier` + `Director` 동시 포함 줄 |
| NpcDriftAdvisor | 0 | 0/0 (비발화 추정 0) | `NpcDriftAdvisor` 포함 줄 자체가 0 |
| InfoParadoxChecker | 4 | - | `InfoParadoxChecker` + `Director` 동시 포함 줄 |
| TruthGate | 0 | - | `TruthGate` + `Director` 동시 포함 줄 0 |
| RelationshipDriftAdvisor | 0 | - | `RelationshipDrift`/`RelDrift` + `Director` 동시 포함 줄 0 |
| LongTermRepetitionAdvisor | 0 | - | `LongTermRep`/`장기 반복` + `Director` 동시 포함 줄 0 |
| NumericDriftAdvisor | 0 | - | `NumericDrift`/`수치 추적` + `Director` 동시 포함 줄 0 |

## 2. VecMemory 히트율

전체 집계:
- `[VecMem]` 줄 수: 219
- `hits>=1`: 123줄
- `hits=0`: 33줄
- `hits` 미기록: 63줄
- 히트율(known only): 78.85% (123/156)
- 히트율(all `[VecMem]` lines): 56.16% (123/219)

`hits=0` 기반 쿼리 타입 집계:

| 쿼리 타입(앞 15자) | 히트 | 미스 | 히트율 |
|---|---:|---:|---:|
| 장르 맥락 키워드: 포트폴리 | 0 | 7 | 0.00% |
| 장르 맥락 키워드: 레버리지 | 0 | 7 | 0.00% |
| 아크 전술 연속성: [제 1 | 0 | 5 | 0.00% |
| 관계 변화 이력: 한정호,  | 0 | 5 | 0.00% |
| 한시우 한정호 한태준 한태민 | 24 | 2 | 92.31% |
| 장면1: 한미증권을 나선 한 | 0 | 2 | 0.00% |
| 아크 전술 연속성: 제 5화 | 0 | 2 | 0.00% |
| 관계 변화 이력: 박성호 | 0 | 2 | 0.00% |
| 장면1: 한시우가 다이닝룸에 | 0 | 1 | 0.00% |

## 3. 합격률 통계 (1차 시도 기준)

기준:
- `episode_production.jsonl`의 시도 키 최소값을 1차로 간주
- 탐지된 최소 시도값: `round=0`
- 1차 시도 표본 수: 35

| 구간 | 1차 합격률 |
|---|---:|
| 1~10 | 83.33% (15/18) |
| 11~20 | 72.73% (8/11) |
| 21~25 | 83.33% (5/6) |

추가 수치:
- 전체 1차 합격률: 80.00% (28/35)
- 1차 불합격 수: 7
- 실패 최다 에피소드 TOP3: ep2(1), ep7(1), ep8(1)

실제 사용 키:
- episode: `ep`
- verdict: `verdict`
- attempt: `round`
- score: `score`

`quality_metrics.jsonl` score 분포:
- count: 82
- min/max/avg: 0.00 / 100.00 / 59.95
- bins: `<60`=32, `60-69`=0, `70-79`=5, `80-89`=1, `90+`=44

## 4. Director 호출 분포

| prompt_len 구간 | 건수 | response_len=2 건수 |
|---|---:|---:|
| <1000 | 0 | 0 |
| 1000~4999 | 30 | 13 |
| 5000~19999 | 27 | 0 |
| 20000+ | 18 | 0 |

추가 수치:
- `call_start agent=Director`: 75
- `call_success agent=Director`: 74
- `response_len=2`: 13
- start-success 매칭 실패: start 미매칭 1, success 미매칭 0

## 5. 결론 (숫자 기반 사실만)

- Advisory 발화 0건 모듈 수: 5/7 (`NpcDriftAdvisor`, `TruthGate`, `RelationshipDriftAdvisor`, `LongTermRepetitionAdvisor`, `NumericDriftAdvisor`)
- Advisory 발화 합계: 10건 (`FlashbackVerifier` 6, `InfoParadoxChecker` 4)
- VecMemory `hits=0` 쿼리 최다 2개: `장르 맥락 키워드: 포트폴리` 7건, `장르 맥락 키워드: 레버리지` 7건
- Director `response_len=2` 비율 최고 구간: `1000~4999`에서 43.33% (13/30)
- JSON 파싱 실패: `episode_production` 0건, `quality_metrics` 0건
- 필드 누락 제외: `episode_production` 8건, `quality_metrics` 0건
