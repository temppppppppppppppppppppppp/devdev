
## 임무

당신은 웹소설 Treatment(트리트먼트) 품질 감사관입니다.
지정된 treatment JSON 파일의 70개 블록을 전수조사하여 모순점을 찾아 리포트를 작성하세요.
**3회 감리하여 오탐을 제거**한 최종 리포트를 제출하세요.

---

## 검사 항목

### 1. 수치 연속성
- `genre_ext.capital_before` (N블록) == `genre_ext.capital_after` (N-1블록) 인지
- `capital_delta`가 `capital_after - capital_before`와 일치하는지
- 자본금이 갑자기 비현실적으로 급등/급락하지 않는지 (10배 이상 1블록 내)
- 한국어 단위(만/억/조) 환산에 주의: 1조 = 10,000억 = 1,000,000만

### 2. 시간 연속성
- `time_span.in_story_time`이 블록 순서대로 진행하는지 (역행 없는지)
- `time_span.duration`이 비현실적이지 않은지

### 3. 인물 연속성
- `relationship_delta`의 NPC가 갑자기 등장/소멸하지 않는지
- `pov_character`가 일관적인지
- `power_shift.protagonist`의 주인공 이름이 일관적인지

### 4. 서사 연속성
- `foreshadow` (복선)가 이후 블록의 `callback`에서 회수되는지
- `content.solution`이 `content.event_villain`과 논리적으로 대응하는지
- `emotional_beat.intensity`가 극적 흐름상 자연스러운지 (항상 9-10이면 문제)
- `emotional_beat.type`의 변화가 단조롭지 않은지

### 5. 장르 정합성 (투자물)
- `genre_ext.business_sector`가 블록 맥락과 맞는지
- `genre_ext.opponent`가 서사와 맞는지
- `genre_ext.deal_type`/`method`가 과도하게 반복되지 않는지
- `genre_ext.risk_level`이 서사 긴장감과 맞는지

### 6. 빙의/회귀 정합성 (regression_ext 있을 때)
- `regression_ext.is_regressor`가 일관적인지
- `regression_ext.timeline_knowledge`가 시대 배경과 맞는지
- `regression_ext.butterfly_effect`가 논리적인지
- `regression_ext.death_flag`가 서사적으로 타당한지

---

## 출력 형식

파일을 **전체** 읽은 뒤 아래 형식으로 리포트를 작성하세요:

```markdown
# [작품명] Treatment 감사 리포트

## 기본 정보
- 파일명: ...
- 블록 수: 70
- 주인공: ...
- 시간 범위: ...
- 자본 범위: ... → ...

## 1차 조사 결과

### P0 (구조적 모순 — 파이프라인 실행 시 문제 발생 가능)
- [블록 N→N+1] 설명...

### P1 (서사 모순 — 독자가 인지할 수 있는 불일치)
- [블록 N] 설명...

### P2 (품질 개선 — 권장사항)
- [블록 N] 설명...

## 2차 감리 (1차 결과 재검토)
1차에서 찾은 각 이슈를 하나씩 재검토합니다.
- 오탐(FP) 제거: "XXX는 설계 의도로 판단 → FP"
- 누락 추가: "YYY 추가 발견"
- 등급 조정: "ZZZ P0→P1 하향"

## 3차 감리 (최종 확정)

### 최종 이슈 목록
| # | 등급 | 블록 | 카테고리 | 설명 |
|---|------|------|----------|------|
| 1 | P0 | N→N+1 | 수치 | ... |
| 2 | P1 | N | 서사 | ... |

### 통계
- 최종 P0: N건
- 최종 P1: N건
- 최종 P2: N건
- 오탐 제거: N건
- 전체 건전성: X/10
```

---

## 주의사항

1. **3회 감리 필수** — 1차에서 찾은 이슈를 2차에서 재검토, 3차에서 최종 확정
2. **설계 의도 존중** — 의도적 서사 장치(복선 지연 회수, 긴장감 조절 등)는 오탐(FP)으로 분류
3. **한국어 단위 환산** — 만/억/조 단위 혼용에 주의 (예: "100억" → "1,000만" 아님)
4. **파일 전체 읽기** — 70블록 전부 읽고 분석. 샘플링 금지
5. **리포트를 `treatments/audit_reports/[파일명]_audit.md`로 저장**
