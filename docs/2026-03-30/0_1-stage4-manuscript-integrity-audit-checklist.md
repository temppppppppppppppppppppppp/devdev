# 0_1 Stage 4 Manuscript Integrity Audit Checklist

Date: 2026-03-30
Status: ready-for-use
Project: `0_1`
Purpose: Stage 4 run 완료 직후 원고 실물을 빠르게 감리하기 위한 bounded checklist

## 1. Use This Only After The Run Stops

이 문서는 `run in-flight` 중간 판단용이 아니다.

사용 시점:

1. Stage 4 프로세스 종료 확인
2. `drafts/`와 `logs/` flush 완료 확인
3. 그 뒤 read-only 감리

## 2. Raw Evidence Read Order

### Artifact truth

반드시 먼저 본다.

- `projects/0_1/drafts/ep_*.txt`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/artifacts/stage4/ep_*/attempt_*/`

### Metadata truth

그다음 본다.

- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/runtime_audit.jsonl`
- `projects/0_1/logs/session/ui_events.jsonl`
- 필요 시 `projects/0_1/logs/session/llm_io.jsonl`

### Narrative truth

마지막으로 직접 읽는다.

- blueprint opening/ending/state beat와 manuscript 본문 비교
- hook 연결, 숫자, 관계, 장소, timeline drift 확인

## 3. Episode Verdict Rubric

- `clean`
  - 즉시 수정 필요 이슈 없음
- `watchlist`
  - 품질 저하 또는 잠재 모순이 있으나 Stage 4 blocker는 아님
- `fix-needed`
  - Stage 5 또는 다음 wave로 넘기기 전에 local/manual patch 필요
- `blocked`
  - 구조 파손, 핵심 continuity 붕괴, 잘못된 canon override 등으로 즉시 멈춰야 함

Severity:

- `P0`
  - blocker
- `P1`
  - fix-before-next-step
- `P2`
  - watchlist

## 4. Must-Check Families

### 4.1 Numeric / Currency

우선순위 높음.

확인 항목:

- KRW-authoritative 흐름에서 USD capital/deployment drift 재발 여부
- `총자산`, `자본`, `증거금`, `유동성`, `잔고`, `수익` 수치 drift
- blueprint 수치와 manuscript 수치 충돌 여부
- HUD/원고/blueprint 간 숫자 정합성

판정:

- 상품 가격표시(`700달러`) 자체는 허용
- capital/deployment 단위 오류는 `P1`

### 4.2 Timeline

확인 항목:

- blueprint `time_flow`와 manuscript opening 시점 일치 여부
- arc tactical의 월/주/일 gap이 원고에서 반영됐는지
- `이전 화 ending -> 현재 화 opening` 시점 점프 자연성

판정:

- 한 달 jump 누락, 월 단위 drift는 기본 `P1`

### 4.3 Identity / Naming

확인 항목:

- broker identity drift (`김 팀장` ↔ `박성호`)
- bank / institution naming drift
- contract month drift (`WTI 3월물` ↔ `6월물`)

판정:

- 핵심 인물/자산명 drift는 기본 `P1`
- 단순 서술 variation은 `P2`

### 4.4 Blueprint Coverage

확인 항목:

- Stage 3의 주요 scene goal / hook / ending beat가 manuscript에 실제 반영됐는지
- Stage 3 watchlist였던 `scene content` empty가 원고에서 비어 있는 beat로 번졌는지
- scene가 통째로 생략되거나 합쳐져도 narrative obligation이 보존됐는지

판정:

- 핵심 beat 누락은 `P1`
- 밀도 저하만 있으면 `P2`

### 4.5 Relationship / State

확인 항목:

- relationship `from_state` 회귀가 실제 대사/서술에 반영됐는지
- location / inventory / injury / status continuity
- 시작 상태와 본문이 충돌하지 않는지

판정:

- canon regression은 `P1`
- 약한 톤 흔들림은 `P2`

## 5. Episode Review Order

가장 효율적인 순서:

1. `EP17`
   - 숫자/통화 단위 drift family 재발 여부
2. `EP20`
   - timeline family 재발 여부
3. `EP18-19`
   - Stage 3 empty scene content bleed 여부
   - relationship regression bleed 여부
4. 나머지
   - sampled sweep

## 6. Output Format

감리 결과는 아래 4단으로 정리한다.

1. Coverage summary
- 조사한 원고 개수
- missing 개수
- in-flight 여부

2. Episode defect table
- episode
- verdict
- severity
- 핵심 이유 1줄
- raw anchor

3. Fix shortlist
- `P1` 이상만
- repair mode
  - `local patch`
  - `manual repair`
  - `bounded regeneration`

4. Final verdict
- `PASS FOR NEXT STEP`
- `PASS WITH WATCHLIST`
- `PATCH SPECIFIC EPISODES FIRST`
- `BLOCKED`

## 7. P1 Trigger Lines

아래 중 하나면 기본 `P1`이다.

- 숫자/통화 단위가 canon과 직접 충돌
- timeline month/week gap 누락
- identity drift가 plot logic를 흔듦
- 핵심 scene beat 누락
- relationship/state regression이 명시적 모순으로 드러남

## 8. Non-Goals

- 코드 원인 분석
- validator root cause survey
- Stage 4 run 중 live intervention
- 문장 polish 위주의 미적 평가

## 9. 3-Pass Audit

### Pass 1

- raw evidence read order와 verdict rubric이 실제 감리 흐름과 맞는지 확인

### Pass 2

- Stage 3 watchlist와 Stage 4 예상 failure family 연결 확인

### Pass 3

- repair mode와 escalation 기준이 과하거나 부족하지 않은지 점검

Final judgment:

- Stage 4 결과 감리용 runbook으로 충분
