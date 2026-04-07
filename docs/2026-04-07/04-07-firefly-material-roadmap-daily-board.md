# 04-07 Firefly Material Roadmap Daily Board

Date: 2026-04-07
Status: final
Document Type: daily operating board
Canonical Path: `docs/2026-04-07/04-07-firefly-material-roadmap-daily-board.md`
Temp Mirror Path: `(none - daily operating note only; no docs/temp mirror)`
Track: coordination note bridging material-side work and system roadmap
Mode: operator execution planning only; no queue mutation implied
Source Docs:
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-03/material-ssot-full-absorption-checklist.md`
- `docs/2026-04-06/04-06-stage4-material-daily-roadmap.md`
- `docs/2026-04-06/downstream-philosophy-reference-ingress-survey.md`
- `docs/2026-04-07/stage4-consumer-front-implementation-context.md`

## 1. Answer First

오늘의 전체 사업 병목은 `Firefly를 다시 돌릴 수 있는 live material anchor 부재`다.

오늘의 시스템 queue front는 여전히 `Stage4 consumer`의 `numeric carryover baseline-promotion / owner-boundary`다.

따라서 오늘은 아래처럼 분리해서 치는 것이 가장 빠르다.

1. `재료`: 추상 철학을 끝내고, 실제로 다시 굴릴 수 있는 작품 anchor 1개를 만든다.
2. `로드맵`: 새 lane를 열지 말고, Stage4 numeric seam만 bounded하게 줄인다.
3. `마감`: 하루 결과를 내일 바로 재개 가능한 형태로 남긴다.

## 2. Today North Star

오늘의 북극성 목표:

`Firefly 재가동 조건을 추상 논의가 아니라 단일 material anchor 1개 확보로 바꾼다.`

오늘 끝났다고 볼 수 있는 최소 조건:

- 한 작품 후보가 `selected anchor`로 올라온다.
- 나머지 후보는 `reserve`로 남고 live canon으로 승격하지 않는다.
- 시스템 쪽은 `Stage4 numeric carryover seam`에서 한 단계 전진한다.

## 3. Today's Three Tasks

### Task 1. Material Anchor One-Shot

Goal:

- `material_ssot/20_pitch`의 철학 문서를 실제 생산 anchor 1개로 내린다.

Recommended candidate:

- primary: `material_ssot/20_pitch/intake/fresh_20260406_batch01/01_line_stop_deputy.md`
- reserve 1: `material_ssot/20_pitch/intake/fresh_20260406_batch01/03_manual_meridian_archivist.md`
- reserve 2: `material_ssot/20_pitch/intake/fresh_20260406_batch01/02_permit_window_grade9.md`

Read with:

- `material_ssot/20_pitch/pitch-philosophy.md`
- `material_ssot/20_pitch/pitch-selection-checklist.md`
- `material_ssot/20_pitch/protagonist-first-constitution.md`

Output expectation:

- 오늘 안에 `selected anchor 1개`를 명시한다.
- 가능하면 그 후보를 다음 안정 단위로 바로 tighten한다.
- full canon까지 못 가더라도 아래 4개는 확정한다:
  - why this work now
  - first-block reward vector
  - controllable resource / growth engine
  - what the next stable artifact will be

Done when:

- Firefly 재개 기준이 `재료가 아직 추상적임`에서 `이 anchor를 기준으로 재개 가능`으로 바뀐다.

Stop rule:

- 오늘 여러 작품을 동시에 live canon으로 올리지 않는다.
- Phase0 / TR / BI까지 욕심내지 않는다.
- 철학 문서 추가 확장으로 시간을 태우지 않는다.

### Task 2. Stage4 Numeric Carryover Slice

Goal:

- roadmap front를 유지하면서 `numeric carryover baseline-promotion / owner-boundary` seam만 줄인다.

Primary owner files:

- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/fact_ledger.py`

Working references:

- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-07/stage4-consumer-front-implementation-context.md`

Output expectation:

- on-page numeric change가 다음 baseline으로 승격되는 bounded path를 명확히 한다.
- stale blueprint or packet truth가 active authority를 조용히 덮어쓰지 못하게 한다.
- operator가 어떤 numeric truth가 이겼는지 설명 가능한 provenance를 남긴다.

Done when:

- legitimate numeric carryover가 다음 episode baseline으로 이어진다.
- 같은 숫자를 다음 화에서 다시 phantom mismatch로 흔들지 않는다.
- Stage2 / Stage3 재설계 없이 끝난다.

Stop rule:

- broad contract redesign으로 번지면 중단하고 다시 numeric seam만 남긴다.
- repair lane를 독립 wave처럼 키우지 않는다.

### Task 3. End-Of-Day Carryover Note

Goal:

- 오늘 성과를 내일 바로 이어갈 수 있는 `짧고 강한 상태`로 남긴다.

Must capture:

- Firefly restart condition status
- selected material anchor or explicit no-go reason
- Stage4 numeric seam에서 실제로 전진한 지점
- tomorrow first move one-liner

Recommended shape:

- 10분 메모 한 장이면 충분하다.
- 장문 회고보다 `무엇이 결정됐고 무엇이 아직 열려 있는가`만 남긴다.

Done when:

- 내일 아침 다시 읽을 때 `뭘 먼저 열어야 하는지`가 1분 안에 보인다.

## 4. Recommended Order

오늘 순서는 아래가 가장 낫다.

1. `Task 1`로 Firefly 쪽 실제 병목부터 해소
2. `Task 2`로 roadmap front를 bounded하게 전진
3. `Task 3`로 결과를 압축 정리

단, 아래 예외는 허용한다.

- 만약 IDE momentum이 이미 `Stage4` 파일에 올라와 있다면 `Task 2 -> Task 1 -> Task 3`로 가도 된다.
- 하지만 하루에 heavy tranche 하나만 끝낼 수 있다면 `Task 1`을 우선한다.

## 5. Suggested Timebox

- `Task 1`: 90-150m
- `Task 2`: 180-240m
- `Task 3`: 20-40m

압축판:

- 시간이 부족하면 `Task 1 완료 + Task 2 착수점 확보`까지만 해도 성공이다.

## 6. Explicit Non-Goals

오늘 하지 않을 것:

- 새 execution lane 만들기
- `Stage2`, `Stage3`, `cross-stage`를 front로 승격하기
- material-side 구조론을 더 크게 확장하기
- 복수 작품 동시 승격
- Phase0 / TR / BI까지 한 번에 밀기

## 7. End-Of-Day Success Test

오늘 성공 판정은 아래 셋이면 충분하다.

1. `selected material anchor 1개`가 생겼다.
2. `Stage4 numeric seam`이 넓어지지 않고 좁아졌다.
3. 내일 첫 행동이 메모 없이도 즉시 보인다.

## 8. 3-Pass Audit Note

Pass 1. Scope
- 오늘의 결정을 `사업 병목`과 `시스템 queue front`로 분리해 혼선을 줄였다.

Pass 2. Evidence
- active roadmap, Stage4 front context, material-side absorption 상태, pitch philosophy ingress 문서를 교차 확인했다.

Pass 3. Closure
- 오늘 해야 할 일을 `material anchor 1개`, `Stage4 bounded slice 1개`, `carryover note 1개`로 축소 고정했다.

Estimated Confidence: 96%
