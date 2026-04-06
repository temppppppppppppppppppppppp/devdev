# WG-V2 Freeze Checklist

- Date: 2026-04-06
- Status: operator-ready after 3-pass self-audit
- Scope: pre-TR manual audit for `work_guard`
- Parent spec: [work-guard-validator-checklist-spec.md](C:/Users/wjjo/Desktop/글도비/docs/2026-04-06/work-guard-validator-checklist-spec.md)

## Purpose

이 체크리스트는 `Phase0 truth -> work_guard draft` 번역이 제대로 됐는지 보는 `freeze 전 manual audit card`다.

이 문서는 `TR/BI 전체 품질`이 아니라 아래만 본다.

- 이 작품의 protagonist-first truth가 `work_guard`에 살아 있는가
- 첫 블록 간판 장면이 guard에 잡혀 있는가
- downstream drift를 막을 금지 규칙이 충분한가

## Input

- `phase0_design`
- freeze 대상 `work_guard draft`
- 참고 라이브러리: [work_guards/README.md](C:/Users/wjjo/Desktop/글도비/work_guards/README.md)
- 필요 시 [work-guard-translation-map.md](C:/Users/wjjo/Desktop/글도비/material_ssot/20_pitch/work-guard-translation-map.md)

실제 runtime 적용본 기준 경로는 `{project}/config/work_guard.yaml`이다.

## Hard Gate

아래 중 하나면 체크리스트 진행 전 바로 `HOLD`다.

- `work_identity.one_line_truth` 없음
- `work_identity.tracking_slots` 없음
- `work_identity.mandatory_scene_engines` 없음
- `work_identity.forbidden_flattenings` 없음
- `work_identity.protagonist_weapon` 없음

## Checklist

각 항목을 `YES / WEAK / NO`로 표기한다.

### 1. One-Line Truth

- `one_line_truth`를 읽었을 때 이 작품의 주인공 장악 판타지가 바로 보이는가
- generic theme가 아니라 `왜 이 주인공이 멋있는가`가 읽히는가

### 2. Protagonist-First Purity

- 주인공이 `결핍은 있어도 과실은 없는` 방향으로 읽히는가
- 회개물, 자기합리화, 자업자득 스타트로 drift하지 않았는가

### 3. Tracking Slots

- `tracking_slots`가 성장 로그가 아니라 `서열 변화 / 통제권 회수 / 재평가` 축인가
- `성장`, `성공`, `열심히 함` 같은 generic slot으로 흐르지 않았는가

### 4. Signature Scene Engine

- 첫 블록 3~6화 내 간판 장면이 `mandatory_scene_engines`에 잡혀 있는가
- 그 장면이 `저건 쟤라서 가능했다`를 증명하는 구조인가

### 5. Protagonist Weapon

- `protagonist_weapon`이 주인공 고유 인과를 말하는가
- 누구에게나 붙일 수 있는 generic competence가 아닌가

### 6. Reward Vector

- 초반 보상이 자산 증가보다 `태도 변화 / 서열 변화 / 허락 요청 / 경계 상승`으로 잡혀 있는가
- 활약 뒤 영수증이 사람들의 반응으로 찍히게 되어 있는가

### 7. Crisis Doctrine

- 위기에서 `선독 -> 대비 -> 최소 피해 통제 -> 보상` 구조가 읽히는가
- 주인공이 빈손으로 맞는 피해자처럼 보이지 않는가

### 8. Forbidden Flattenings Coverage

- `forbidden_flattenings`가 치명 drift를 충분히 막고 있는가
- 최소한 아래 중 다수가 포함되는가

- `회개물 스타트`
- `비굴한 해명/인정 구걸`
- `자기연민 소비`
- `success -> pure punishment spiral`
- `주인공 고유성 없는 대형 성과`
- `활약 후 태도 변화 없음`
- `위기 때 빈손/무대응/무보상`

### 9. Translation Discipline

- upstream 철학 문서를 장문 복붙하지 않았는가
- 교육용 설명문이 아니라 runtime doctrine으로 압축되었는가

### 10. Work Specificity

- 이 `work_guard`를 다른 작품에 그대로 붙이면 어색할 정도로 작품 특유성이 있는가
- 소재 설명보다 작품의 장악 판타지가 앞서는가

## Verdict

### PASS

- `NO` 없음
- `WEAK` 2개 이하
- 4번, 5번, 6번이 모두 `YES`

### HOLD

- `NO` 1~2개
- 또는 `WEAK` 3개 이상
- 또는 4번, 5번, 6번 중 하나라도 `WEAK`

### REJECT

- `NO` 3개 이상
- 또는 4번, 5번, 6번 중 하나라도 `NO`
- 또는 주인공 고유 유능함과 첫 블록 간판 장면이 사실상 안 보임

## Common HOLD Reasons

- 구조는 맞지만 너무 generic하다
- scene engine은 있는데 reward vector가 약하다
- 주인공 고유 무기보다 산업/소재 소개가 먼저 보인다
- 금지 drift 목록이 얕다
- 작품 철학이 runtime doctrine으로 압축되지 않았다

## Freeze Rule

`HOLD`나 `REJECT`면 `TR` 생성으로 넘어가지 않는다.

운영 순서는 아래를 따른다.

- `Phase0 -> WG-V2 PASS -> work_guard freeze -> TR`
