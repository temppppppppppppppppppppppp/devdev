# WG-V3 Drift Audit Card

- Date: 2026-04-06
- Status: operator-ready after 3-pass self-audit
- Scope: frozen `work_guard` to early `TR` drift audit
- Parent spec: [work-guard-validator-checklist-spec.md](C:/Users/wjjo/Desktop/글도비/docs/2026-04-06/work-guard-validator-checklist-spec.md)

## Purpose

이 카드는 freeze된 `work_guard`가 실제 `TR` 초반 블록에서 살아 있는지 보는 `post-freeze drift audit card`다.

이 문서는 아래만 본다.

- `tracking_slots`가 실제로 움직이는가
- `mandatory_scene_engines`가 장면으로 찍히는가
- `forbidden_flattenings` 위반이 발생했는가
- 주인공 고유 무기와 보상 벡터가 결과의 원인으로 남는가

이 문서는 `TR` 문장력 전체 감리나 `BI` completeness 감리를 대신하지 않는다.

## When To Run

아래 중 하나에서 수행한다.

- 첫 블록 초안 완료 직후
- early `TR` draft 검토 직후
- Director `open_review`에서 `work identity drift`가 의심될 때

권장 최소 audit window는 `첫 블록 3~6화`다.

## Input

- freeze된 `{project}/config/work_guard.yaml`
- early `TR` draft 또는 첫 블록
- 필요 시 Director `open_review`
- 필요 시 [wg-v2-freeze-checklist.md](C:/Users/wjjo/Desktop/글도비/docs/2026-04-06/wg-v2-freeze-checklist.md)

## Audit Rule

각 항목을 `PASS / WARN / FAIL`로 표기한다.

예외:

- 8번은 Director `open_review`가 아직 없으면 `N/A` 허용

여기서 뜻은 아래와 같다.

- `PASS`: guard doctrine이 실제로 살아 있다
- `WARN`: 살아는 있지만 약해졌다
- `FAIL`: 사실상 사라졌거나 반대로 갔다

## Checklist

### 1. Tracking Slot Survival

- 핵심 `tracking_slots`가 `TR`에서 실제 사건과 반응으로 드러나는가
- slot이 통째로 사라지거나 generic 성장 로그로 치환되지 않았는가

### 2. Signature Scene Realization

- `mandatory_scene_engines`가 실제 장면으로 구현되었는가
- 첫 블록 간판 장면이 `저건 쟤라서 가능했다`를 증명하는가

### 3. Protagonist Weapon Causality

- 결과의 원인이 `protagonist_weapon`으로 읽히는가
- 대형 성과가 단순 사건 규모, 우연, 외부 구원으로 처리되지 않았는가

### 4. Reward Receipt

- 활약 뒤 `태도 변화 / 서열 변화 / 경계 상승 / 허락 요청` 같은 영수증이 남는가
- 성과는 있는데 재평가가 안 찍히는 구조로 약화되지 않았는가

### 5. Crisis Doctrine Survival

- 위기에서 `선독 -> 대비 -> 최소 피해 통제 -> 보상` 구조가 살아 있는가
- 주인공이 빈손 피해자나 무대응 수습 담당처럼 보이지 않는가

### 6. Forbidden Flattenings

- 아래 drift가 실제로 발생하지 않았는가

- `회개물 스타트`
- `비굴한 해명/인정 구걸`
- `자기연민 소비`
- `success -> pure punishment spiral`
- `주인공 고유성 없는 대형 성과`
- `활약 후 태도 변화 없음`
- `위기 때 빈손/무대응/무보상`

### 7. Work Specificity Retention

- `TR`가 여전히 이 작품만의 장악 판타지를 유지하는가
- 산업/소재 설명이 작품 정체성을 덮어버리지 않았는가

### 8. Director Drift Surface

- Director `open_review`에 `work identity drift`가 찍혔는가
- 찍혔다면 원인이 `slot 소실 / scene engine 누락 / flattening 위반` 중 무엇인지 바로 연결되는가

## Verdict

### PASS

- `FAIL` 없음
- `WARN` 2개 이하
- 2번, 3번, 4번이 모두 `PASS`

### DRIFT-WARN

- `FAIL` 없이 `WARN` 3개 이상
- 또는 2번, 3번, 4번 중 하나라도 `WARN`
- 또는 Director `open_review`에 경미한 `work identity drift`가 반복 표면화됨

### DRIFT-FAIL

- `FAIL` 1개 이상
- 또는 2번, 3번, 4번 중 하나라도 `FAIL`
- 또는 `tracking_slots`/`mandatory_scene_engines`가 통째로 사라짐
- 또는 `forbidden_flattenings` 위반이 명백함

## Common Drift Patterns

- scene engine은 남았는데 reward receipt가 사라짐
- 주인공 성과는 있는데 원인이 주인공 고유 무기가 아님
- 위기는 있는데 선독/대비 없이 그냥 당함
- 보상은 있는데 자산 증가만 있고 태도 변화가 없음
- 소재 설명이 늘어나면서 장악 판타지가 흐려짐

## Action Rule

### PASS

- 그대로 다음 `TR` 작업 진행

### DRIFT-WARN

- `TR` 우선 보정
- 필요 시 다음 블록 전 `mandatory_scene_engines`와 `reward receipt`를 강화

### DRIFT-FAIL

- `TR` 보정 후 재감리
- drift 원인이 `TR`만의 문제인지, `work_guard` 자체 truth가 잘못 잠겼는지 먼저 판정
- upstream truth가 바뀐 경우에는 `TR` 수정 전에 `work_guard`부터 재동결

## Minimal 5-Question Fast Check

시간이 없으면 아래 5문항만 먼저 본다.

1. 첫 블록에서 `mandatory_scene_engines`가 실제 장면으로 찍혔는가
2. 결과의 원인이 `protagonist_weapon`으로 보이는가
3. 활약 뒤 태도 변화 영수증이 찍혔는가
4. `tracking_slots`가 실제 사건 축으로 살아 있는가
5. 치명 `forbidden_flattenings` 위반이 없는가

이 5개 중 1개라도 `NO`면 최소 `DRIFT-WARN`, 2개 이상이면 `DRIFT-FAIL` 우선 검토로 본다.
