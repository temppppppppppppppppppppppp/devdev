# Advisory 재감사 결과

> 감사일: 2026-03-04
> 검사 마커: `→` (U+2192)
> 대상 세션: 8개

## Task 1: 모듈별 발화 건수

| 모듈 | 발화 건수 | 실행 가능 에피수 | Guard 0건 가능성 |
|------|---:|---:|---|
| NpcDriftAdvisor | 0 | 1~25 (25) | 없음 |
| TruthGate | 0 | 1~25 (25) | 없음 |
| RelationshipDriftAdvisor | 0 | 5~25 (21) | 있음 (1~4 제외) |
| LongTermRepetitionAdvisor | 0 | 20~25 (6) | 있음 (1~19 제외) |
| NumericDriftAdvisor | 0 | 5,10,15,20,25 (5) | 있음 (5의 배수 외 제외) |

발화 있는 모듈 인용 (최대 3건):
- 없음 (5개 대상 모듈 발화 0건)

## Task 2: 발화 내용 상세

(발화 있는 모듈만)

| 모듈 | 세션 파일 | 에피소드 | 발화 건수 |
|------|---------|--------|---:|
| 해당 없음 | - | - | 0 |

## Task 3: response_len=2 교집합 확인

- response_len=2 에피소드 목록: 없음
  - `episode_production.jsonl`에서 `response_len` 필드가 있는 레코드: 0건
  - `episode_production.jsonl` 전체 레코드 중 `response_len` 필드 없음: 60건
- Task 1 발화 에피소드 목록: 없음
- 교집합: 없음

## 확인된 사실 요약

- NpcDriftAdvisor 실제 발화 건수: 0건
- TruthGate 실제 발화 건수: 0건
- RelationshipDriftAdvisor 실제 발화 건수: 0건
- LongTermRepetitionAdvisor 실제 발화 건수: 0건 (20화 이상 대상)
- NumericDriftAdvisor 실제 발화 건수: 0건 (5,10,15,20,25화 대상)
- 이전 감사 "0건 판정" 번복 여부: 번복 0건 / 유지 5건

---

## 체크리스트

- [x] 코드 수정 없음
- [x] 검색 명령어 미사용
- [x] `→` (U+2192) 마커로 검사 (ASCII `->` 아님)
- [x] 8개 세션 파일 전량 확인
- [x] 발화 줄 전체 인용 포함 (해당 없음으로 명시)
- [x] 출력 파일 경로 준수
