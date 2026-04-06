# WorkGuard Translation Map

Date: 2026-04-06
Status: active
Scope: canonical bridge from `20_pitch` house law into runtime-safe `work_guard.yaml`

## 1. Role

- convert `pitch philosophy` and `protagonist-first constitution` into a compact downstream rule shape
- define what belongs in `work_guard.yaml` and what must stay in upstream philosophy docs
- prevent late-stage prompt stuffing by translating house law into short runtime slots
- give operators one stable bridge from `20_pitch` truth to downstream guard semantics

Important operational note:

- full philosophy text remains canonical in upstream `20_pitch` law docs
- `work_guard.yaml` must carry only the compressed, work-specific runtime doctrine
- this document governs the translation rule, not the live project config path itself
- reviewed final yaml may be published into the Stage 0-visible `work_guards/` library lane after `WG-V2 PASS`
- preferred publish lanes are `work_guards/<genre>/<work_id>.yaml` and fallback `work_guards/<work_id>.yaml`

Companion audit pack:

- use the dated operator docs below when translating and auditing a live work-specific `work_guard`
- `docs/2026-04-06/work-guard-validator-checklist-spec.md`
- `docs/2026-04-06/wg-v2-freeze-checklist.md`
- `docs/2026-04-06/wg-v3-drift-audit-card.md`
- recommended operator order:
  - `translation map -> WG-V2 freeze checklist -> work_guard freeze -> TR -> WG-V3 drift audit`

## 2. Core Rule

전체 철학 문서는 `material_ssot/20_pitch`에 둔다.

`work_guard.yaml`에는 그 원문을 넣지 않는다.

`work_guard.yaml`에는 아래만 넣는다.

- 작품별로 압축된 doctrine
- 실제 Stage2/Stage3/Stage4가 소비할 수 있는 짧은 슬롯
- 살아남아야 할 장면 엔진
- 절대 평탄화되면 안 되는 금지 패턴

한 줄 요약:

- `헌법은 20_pitch`
- `작전명령서는 work_guard.yaml`

## 3. What Belongs Where

### 3.1 Keep In Upstream Law Docs

- 1조~24조 전체 문장
- 왜 이런 철학이 필요한지에 대한 설명
- 예시와 반례
- 작가 교육용 설명
- selection / rejection rationale

### 3.2 Put Into `work_guard.yaml`

- 이 작품에서 특히 중요한 2~4개의 추적축
- 이 작품에서 반드시 반복 확인되어야 하는 2~3개의 장면 엔진
- 이 작품에서 독자가 주인공을 어떻게 고평가해야 하는지
- 이 작품이 절대 드리프트하면 안 되는 평탄화 금지 항목
- 주인공 고유 무기와 장악 축

### 3.3 Never Put Directly Into `work_guard.yaml`

- 장문의 철학 설명
- 조항 번호 원문 전체
- “왜 그런가”에 대한 교육용 해설
- 장면별 TR 수준 세부계획
- 문체 시범문 자체

## 4. Field Map

### `work_identity.work_id`

여기에 넣는 것:

- canonical `work_id`
- publish된 library guard의 내부 식별자

원칙:

- published work-specific guard는 가능하면 이 값을 채운다
- 파일명이 `work_guards/<work_id>.yaml` 또는 `work_guards/<genre>/<work_id>.yaml`라면 내부 `work_id`도 같은 값을 쓰는 편이 좋다
- 이 값은 block/scene 식별자가 아니라 작품 식별자다

좋은 예:

- `office_checkup_next_day`
- `chaebol_ent_empire`

### `work_identity.one_line_truth`

여기에 넣는 것:

- `promise_to_reader`
- 이 작품의 protagonist-first 한 줄 진실

좋은 형태:

- `저평가된 말단이 정보격차와 결재권 회수로 모두가 허락을 구하는 관문이 된다`

피해야 할 형태:

- `권력과 인간의 욕망을 그리는 이야기`
- `성장과 시련을 다룬다`

### `work_identity.tracking_slots`

여기에 넣는 것:

- 계속 추적해야 하는 상승 축
- 서열 변화
- 통제권 회수
- opening reward vector의 반복형

권장 개수:

- 2~4개

좋은 예:

- `저평가 -> 고평가 전환`
- `허가권/결재권 회수`
- `주인공 없이 못 움직이는 병목 형성`
- `적의 경계 수위 상승`

피해야 할 예:

- `열심히 함`
- `성장`
- `성공`

### `work_identity.mandatory_scene_engines`

여기에 넣는 것:

- `저건 쟤라서 가능했다`를 증명하는 장면 엔진
- 첫 블록 간판 장면의 반복 가능한 형태
- 평가 수정이 찍히는 장면 유형

권장 개수:

- 2~3개

좋은 예:

- `회의/협상에서 판 읽기와 우선순위 선점`
- `위기 징후 선독 후 최소 피해 통제`
- `결재선/승인권/호출권이 주인공 쪽으로 이동하는 장면`

피해야 할 예:

- `액션`
- `감동`
- `성장 이벤트`

### `work_identity.forbidden_flattenings`

여기에 넣는 것:

- 우리 철학에서 금지한 drift
- 특히 downstream에서 가장 자주 망가지는 패턴

권장 개수:

- 4~8개

우선 추천 항목:

- `회개물 스타트`
- `비굴한 해명/인정 구걸`
- `자기연민 소비`
- `success -> pure punishment spiral`
- `주인공 고유성 없는 대형 성과`
- `운빨 생존을 실력처럼 처리`
- `활약 후 태도 변화 없음`
- `위기 때 빈손/무대응/무보상`

### `work_identity.mandatory_lexicon`

여기에 넣는 것:

- 독자가 보상과 장악을 몸으로 느끼게 하는 도메인 어휘
- visible reward token

좋은 예:

- `결재`
- `승인권`
- `보고선`
- `지분`
- `호출`
- `입장권`
- `장문`
- `보호패`

### `work_identity.protagonist_weapon`

여기에 넣는 것:

- 주인공만의 고유 무기
- 독자가 `저건 쟤밖에 못 한다`고 느끼는 인과

좋은 예:

- `정보격차를 읽는 감각`
- `규격/허가 병목을 짚는 판단`
- `상대보다 먼저 위기를 읽는 예측력`
- `타이밍을 놓치지 않는 개입 능력`

### `work_identity.business_axes`

여기에 넣는 것:

- 이 작품에서 실제로 굴러가는 사업/운영 축
- `controllable_growth_resource`의 산업 측면

좋은 예:

- `승인`
- `표준`
- `프로젝트 소유권`
- `현금흐름`
- `공급선`

### `work_identity.control_axes`

여기에 넣는 것:

- 주인공이 장악해야 하는 권한 축
- 독자가 느낄 서열 변화의 제도적 형태

좋은 예:

- `결재선`
- `호출권`
- `입장권`
- `배정권`
- `관문 통행료`

### `work_identity.protagonist_evaluation.admiration_axes`

여기에 넣는 것:

- 작품이 주인공을 어떤 방식으로 멋있게 보여줄지
- 독자가 느껴야 할 고평가 축

권장 개수:

- 3~5개

좋은 예:

- `남들보다 먼저 읽음`
- `비굴하지 않음`
- `손실을 통제함`
- `결과로 인정 강제`
- `판을 잘못 읽히게 만드는 여유`

### `work_identity.protagonist_evaluation.forbidden_praise_patterns`

여기에 넣는 것:

- 이 작품이 쓰면 안 되는 칭찬 방식
- 주인공을 약하게 만드는 praise frame

권장 예:

- `불쌍해서 챙겨준다`
- `착해서 인정한다`
- `성실해서 언젠가 보답받는다`
- `우연히 잘 풀렸다`
- `참고 견뎌서 대단하다`

### `work_identity.protagonist_evaluation.observer_tiers`

여기에 넣는 것:

- 누가 주인공을 먼저 재평가할지
- 평가 수정의 계층 순서

좋은 예:

- `동료`
- `실무 책임자`
- `적대 경쟁자`
- `윗선`
- `외부 파트너`

### `work_identity.protagonist_evaluation.evaluation_thresholds`

여기에 넣는 것:

- 어느 순간부터 태도 변화가 찍혀야 하는지
- 고평가 영수증의 기준점

좋은 예:

- `3~6화 내 간판 장면 1회`
- `첫 승리 직후 호칭/자리/결재선 변화`
- `큰 피해 뒤 즉시 찬사 또는 다음 카드 확보`

### `work_identity.role_fit_constraints`

여기에 넣는 것:

- 주인공 외 인물들이 작품 철학을 훼손하지 않도록 막는 제약
- 특히 “남이 대신 다 해주는” 문제 방지

좋은 예:

- `상사는 주인공 대신 핵심 추론을 완성하지 않는다`
- `조력자는 감화 이전에 계산으로 붙는다`
- `적은 바보처럼 져주지 않는다`

### `custom_rules`

여기에 넣는 것:

- 다른 필드에 안 예쁘게 들어가지만 반드시 살아야 하는 짧은 규칙

좋은 예:

- `위기는 피해 연출보다 우선순위 선택권 증명으로 사용한다`
- `설명이 리듬을 깨면 운이 좋군으로 절감할 수 있다`
- `반격 예약 없는 손해는 금지`

## 5. Constitution -> WorkGuard Quick Map

### 5.1 조형 조항

- `결핍은 있어도 과실은 없다`
  - `forbidden_flattenings`
  - `custom_rules`
- `오만할 수 있어도 비굴하면 안 된다`
  - `admiration_axes`
  - `forbidden_praise_patterns`
- `자기연민 금지`
  - `forbidden_flattenings`

### 5.2 첫 승리와 보상

- `첫 승리는 평가 수정`
  - `tracking_slots`
  - `mandatory_scene_engines`
  - `evaluation_thresholds`
- `3~6화 간판 장면`
  - `mandatory_scene_engines`
  - `protagonist_weapon`
  - `evaluation_thresholds`
- `돈보다 서열 변화`
  - `control_axes`
  - `mandatory_lexicon`
  - `tracking_slots`

### 5.3 관계 조항

- `사랑보다 고평가`
  - `observer_tiers`
  - `admiration_axes`
- `인정은 강제`
  - `tracking_slots`
  - `mandatory_scene_engines`
- `조력자는 계산으로 붙는다`
  - `role_fit_constraints`

### 5.4 위기 조항

- `먼저 읽는다`
  - `admiration_axes`
  - `mandatory_scene_engines`
- `빈손으로 들어가지 않는다`
  - `mandatory_scene_engines`
  - `custom_rules`
- `최소 피해 통제`
  - `admiration_axes`
  - `evaluation_thresholds`
- `큰 피해 뒤 보상`
  - `evaluation_thresholds`
  - `tracking_slots`

### 5.5 설명과 오해 조항

- `운이 좋군으로 절감 가능`
  - `custom_rules`
- `자기 해설 금지`
  - `forbidden_flattenings`
- `잘못 읽히는 주인공`
  - `admiration_axes`
  - `observer_tiers`

### 5.6 리듬과 반격 조항

- `자원보다 리듬`
  - `custom_rules`
- `반격 예약 없는 손해 금지`
  - `forbidden_flattenings`
  - `evaluation_thresholds`

## 6. Operator Recipe

`pitch -> work_guard.yaml`로 옮길 때는 이 순서가 가장 안전하다.

1. `promise_to_reader`를 `one_line_truth` 1문장으로 줄인다.
2. `controllable_growth_resource`를 `business_axes`와 `control_axes`로 나눈다.
3. `information_gap + competence_process`를 `protagonist_weapon`으로 압축한다.
4. `opening_reward_vector + first_block_reward`를 `tracking_slots` 2~4개로 바꾼다.
5. `episodes_1_to_3_impact + first_block_problem`을 `mandatory_scene_engines` 2~3개로 바꾼다.
6. 철학 위반 패턴을 `forbidden_flattenings`로 적는다.
7. 고평가 방식은 `protagonist_evaluation.*`로 적는다.
8. 나머지 잔여 규칙만 `custom_rules`에 넣는다.

## 7. Recommended Size Budget

`work_guard.yaml`은 짧을수록 좋다.

권장 예산:

- `one_line_truth`: 1문장
- `tracking_slots`: 2~4개
- `mandatory_scene_engines`: 2~3개
- `admiration_axes`: 3~5개
- `forbidden_praise_patterns`: 3~5개
- `observer_tiers`: 3~5개
- `evaluation_thresholds`: 2~4개
- `custom_rules`: 2~5개

이유:

- 런타임은 결국 compact focus를 뽑아 Stage2/Stage3/Stage4에 재배치한다
- 너무 많으면 살아남지 못하고, 오히려 작품 정체성이 흐려진다

## 8. Minimal Example

```yaml
work_identity:
  work_type: investment
  one_line_truth: 저평가된 말단이 정보격차와 결재권 회수로 모두가 허락을 구하는 관문이 된다
  protagonist_weapon:
    - 정보격차를 먼저 읽는 판단
    - 위기 징후를 남보다 빨리 감지하는 감각
  business_axes:
    - 현금흐름
    - 승인
    - 프로젝트 소유권
  control_axes:
    - 결재선
    - 호출권
    - 입장권
  mandatory_lexicon:
    - 결재
    - 승인권
    - 보고선
    - 지분
  forbidden_flattenings:
    - 회개물 스타트
    - 비굴한 해명
    - 자기연민 소비
    - success -> pure punishment spiral
    - 주인공 고유성 없는 대형 성과
  tracking_slots:
    - 저평가 -> 고평가 전환
    - 허가권/결재권 회수
    - 주인공 없이 못 움직이는 병목 형성
  mandatory_scene_engines:
    - 회의/협상에서 판 읽기와 우선순위 선점
    - 위기 징후 선독 후 최소 피해 통제
    - 첫 승리 직후 호칭/자리/결재선 변화
  protagonist_evaluation:
    admiration_axes:
      - 남들보다 먼저 읽음
      - 비굴하지 않음
      - 손실을 통제함
      - 결과로 인정 강제
    forbidden_praise_patterns:
      - 불쌍해서 챙겨준다
      - 착해서 인정한다
      - 우연히 잘 풀렸다
    observer_tiers:
      - 동료
      - 실무 책임자
      - 경쟁자
      - 윗선
    evaluation_thresholds:
      - 3~6화 내 간판 장면 1회
      - 첫 승리 직후 호칭/자리/결재선 변화
      - 큰 피해 뒤 즉시 다음 카드 확보
  role_fit_constraints:
    - name: 조력자 선행 금지
      role: 조력자
      disallowed_actions:
        - 주인공 대신 핵심 추론 완성
        - 이유 없는 선의 지원
      exceptions:
        - 계산상 주인공 편에 서는 선택
custom_rules:
  - 위기는 피해 연출보다 우선순위 선택권 증명으로 사용한다
  - 반격 예약 없는 손해는 금지
  - 설명이 리듬을 깨면 운이 좋군으로 절감할 수 있다
```

## 9. Practical Conclusion

실무적으로는 이렇게 보면 된다.

- `20_pitch`는 철학 원문과 bridge rule의 보관소
- preprocess 4-pack은 authority registration
- `work_guard.yaml`은 runtime translation
- reviewed final publish는 Stage 0이 바로 볼 수 있는 `work_guards/` visible lane으로 간다

즉, downstream에 철학을 넘기는 일의 본체는 `문서를 읽게 하는 것`보다 `문서를 work_guard 문법으로 번역하는 것`이다.
