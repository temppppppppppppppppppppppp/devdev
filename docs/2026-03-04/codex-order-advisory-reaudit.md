# Codex Order: Advisory 모듈 재감사 (`→` 마커)

> **목적**: 이전 감사에서 `->` (ASCII)로 검색했으나 실제 코드 마커는 `→` (U+2192). `→`로 재검색하여 5개 모듈의 실제 발화 건수를 확정한다.
> **출력(고정)**: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/advisory-reaudit-result.md`
> **분석 방식**: 파일 직접 읽기만. 셸 명령어(`rg`, `grep` 등) 금지.

---

## 0) 강제 제약

- 코드 수정, 설정 변경, 파일 생성(출력 파일 제외), 파일 삭제 금지.
- 결론 섹션: 확인된 사실만. 개선안/추천/의견 금지.
- 숫자는 직접 셀 것. 추정·예측 금지.

---

## 배경

이전 Feature Activation Audit에서:
- 검색어: `NpcDriftAdvisor->Director`, `TruthGate->Director` 등 (`->` ASCII)
- 실제 코드 마커: `[NpcDriftAdvisor→Director]`, `[TruthGate→Director]` 등 (`→` U+2192)
- 결과: 5개 모듈 발화 0건으로 집계 — 이는 검색 오류일 가능성이 있음

본 재감사는 `→`를 포함한 실제 마커로 재집계한다.

---

## 대상 파일 (순서대로)

```
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_133915.log
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_142438.log
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_144516.log
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_144702.log
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_145148.log
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_150048.log
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_150114.log
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_151852.log
```

---

## Task 1: 5개 모듈 실제 발화 건수 집계

각 로그 파일을 읽고, 아래 5개 마커 문자열을 포함하는 줄을 전부 찾는다.

### 검색 마커 (정확히 이 문자열을 포함하는 줄)

```
[NpcDriftAdvisor→Director]
[TruthGate→Director]
[RelationshipDriftAdvisor→Director]
[LongTermRepetitionAdvisor→Director]
[NumericDriftAdvisor→Director]
```

**중요**: `→`는 유니코드 U+2192 (RIGHTWARDS ARROW). `->` (ASCII 두 글자)가 아님.

### 집계 방식

각 마커마다:
1. 8개 세션 파일에서 해당 마커를 포함하는 줄을 모두 찾는다.
2. 줄 수를 센다 (= 발화 건수).
3. 발화가 있는 경우: 해당 줄 전체를 최대 3건까지 인용한다 (에피소드 번호 확인용).
4. 발화가 0건인 경우: 0건으로 기록하고 다음 마커로 진행.

### 에피소드 조건부 Guard 참고 (실행 가능 화수)

집계 시 아래 Guard 조건을 참고하여 0건이 Guard 때문인지 판단한다:

| 모듈 | Guard 조건 | 실행 가능 조건 |
|------|-----------|-------------|
| NpcDriftAdvisor | 없음 (매 화) | 전 화수 |
| TruthGate | 없음 (매 화) | 전 화수 |
| RelationshipDriftAdvisor | `next_ep < 5: return []` | 5화 이상 |
| LongTermRepetitionAdvisor | `next_ep < 20: return []` | 20화 이상 |
| NumericDriftAdvisor | `next_ep % 5 != 0: return []` | 5의 배수 화만 (5·10·15·20·25화) |

대상 세션은 1~25화 범위로 추정됨.

---

## Task 2: 발화 있는 모듈 — 내용 확인

Task 1에서 발화 건수 1건 이상인 모듈에 대해서만 수행한다.

각 발화 줄에서 다음을 확인하여 기록한다:
1. 에피소드 번호 (줄에서 ep 번호 추출, 없으면 "확인불가")
2. 발화 건수 숫자 (`%d건` 부분)
3. 세션 파일명

---

## Task 3: Director 응답 길이 2 재확인

이전 감사에서 `response_len=2`가 13건 (전량 1K~5K 구간)으로 집계됐다.
이 중 advisory 모듈 발화와 같은 에피소드에서 발생한 건이 있는지 확인한다.

방법:
- `episode_production.jsonl` 파일에서 `response_len` 필드가 2인 레코드를 찾는다.
- 해당 레코드의 에피소드 번호를 추출한다.
- Task 1에서 발화가 확인된 에피소드와 겹치는 건이 있으면 기록한다.
- 겹치는 건이 없거나 발화가 없으면 "교차 없음"으로 기록한다.

파일 경로:
```
C:/Users/wjjo/Desktop/글도비/projects/000000/logs/episode_production.jsonl
```

---

## 출력 형식 (고정)

```markdown
# Advisory 재감사 결과

> 감사일: 2026-03-04
> 검색 마커: → (U+2192)
> 대상 세션: 8개

## Task 1: 모듈별 발화 건수

| 모듈 | 발화 건수 | 실행 가능 화수 | Guard 0건 가능성 |
|------|---:|---:|---|
| NpcDriftAdvisor | N | 전 화수 | 없음 |
| TruthGate | N | 전 화수 | 없음 |
| RelationshipDriftAdvisor | N | 5화 이상 | 있음 (1~4화 제외) |
| LongTermRepetitionAdvisor | N | 20화 이상 | 있음 (1~19화 제외) |
| NumericDriftAdvisor | N | 5의 배수 화 | 있음 (5 배수 외 화 제외) |

발화 있는 모듈 인용 (최대 3건):
- [모듈명]: (줄 전체 인용)

## Task 2: 발화 내용 상세

(발화 있는 모듈만)

| 모듈 | 세션 파일 | 에피소드 | 발화 건수 |
|------|---------|--------|---:|
| ... | ... | ep? | N |

## Task 3: response_len=2 교차 확인

- response_len=2 에피소드 목록: (ep 번호 나열)
- Task 1 발화 에피소드 목록: (ep 번호 나열)
- 교차: (있음/없음, 있으면 ep 번호)

## 확인된 사실 요약

- NpcDriftAdvisor 실제 발화 건수: N건
- TruthGate 실제 발화 건수: N건
- RelationshipDriftAdvisor 실제 발화 건수: N건
- LongTermRepetitionAdvisor 실제 발화 건수: N건 (20화 이상 대상)
- NumericDriftAdvisor 실제 발화 건수: N건 (5·10·15·20·25화 대상)
- 이전 감사 "0건" 판정 번복 여부: (번복 N건 / 유지 N건)
```

---

## 체크리스트

- [ ] 코드 수정 없음
- [ ] 셸 명령어 미사용
- [ ] `→` (U+2192) 마커로 검색 (ASCII `->` 아님)
- [ ] 8개 세션 파일 전량 확인
- [ ] 발화 줄 전체 인용 포함
- [ ] 출력 파일 경로 준수
