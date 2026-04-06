# WorkGuard Validator + Checklist Spec

- Date: 2026-04-06
- Status: team-ready draft after 3-pass self-audit
- Scope: material-side and downstream handoff audit design
- Type: no-code spec

## 1. Purpose

`work_guard.yaml`는 `TR`이나 `BI`처럼 서사 산출물이 아니다.

대신 작품 정체성이 downstream으로 갈수록 변질되지 않게 막는 `runtime rule artifact`다.

그래서 `BI/TR`처럼 완전히 같은 감리 구조를 복제하는 것보다,

- 기계가 잡아야 하는 것
- 사람이 잡아야 하는 것
- `TR` 이후 drift로 다시 확인해야 하는 것

을 나눠서 설계하는 편이 맞다.

이 문서는 그 `work_guard` 전용 validator/checklist 운영 spec을 정의한다.

주의:

- 이 spec은 기존 엔진 내 shape validation을 대체하지 않는다
- 그 위에 material/operator용 manual audit layer를 추가 정의하는 문서다

## 2. Current Reality

현재 레포에는 이미 아래가 있다.

### 2.1 Existing machine validation

- `work_guard.yaml` shape validation
- YAML parse/load failure rejection
- 주요 field type validation
- 일부 manuscript warning check

Evidence:

- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L22)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L83)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L835)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L864)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L993)

### 2.2 Existing readiness summary

- project support summary surface
- valid / invalid / error summary
- slot/profile/role-fit count exposure

Evidence:

- [project_support.py](../../modules/core/project_support.py#L270)

### 2.3 Existing runtime semantic drift surfacing

- Director review에서 `work identity drift`를 `open_review`에 표면화

Evidence:

- [director.yaml](../../config/prompts/director.yaml#L124)

## 3. Missing Piece

현재 없는 것은 `BI/TR`처럼 material/operator가 직접 돌리는 `work_guard` 전용 실전 감리 패키지다.

정확히 말하면 아래가 비어 있다.

- freeze 전 `manual PASS/HOLD/REJECT checklist`
- `Phase0 -> work_guard` 번역 품질 감리 규칙
- `work_guard -> TR` drift audit 기준
- operator가 보기 쉬운 one-page pass/fail rubric

즉 지금은 `엔진 내부 검증`은 있지만, `재료팀 운영 검증`은 아직 없다.

## 4. Design Goal

`work_guard` 감리는 세 층으로 나눈다.

1. `Shape Validator`
2. `Freeze Checklist`
3. `Drift Audit`

한 줄 요약:

- 기계는 형식을 막는다
- 사람은 철학 번역 품질을 본다
- `TR` 이후에는 실제 drift가 났는지 다시 본다

Out of scope:

- 문장 미감 자체의 품질 감리
- `TR` 연속성/씬 밀도 전반 감리
- `BI` canonical completeness 감리

즉 이 spec은 `work_guard다운가`를 보는 문서지, `TR/BI 전체 품질`을 대신 보지 않는다.

## 5. Proposed Artifact Set

### 5.1 WG-V1 Shape Validator

역할:

- YAML 파싱 가능 여부 확인
- 필수 field 존재 / 타입 / 빈 값 확인
- 지나치게 generic한 placeholder 감지

입력:

- freeze 대상 `config/work_guard.yaml`
- 또는 freeze 직전 draft yaml

경로 원칙:

- 런타임 적용본은 언제나 `{project}/config/work_guard.yaml`
- `work_guards/` 아래 yaml은 템플릿/원본 라이브러리로만 본다

성격:

- machine-first
- fast fail
- hard gate

현재 구현 상태:

- 일부 이미 존재
- 신규 운영 spec에서는 이것을 공식 `V1`로 부른다

### 5.2 WG-V2 Freeze Checklist

역할:

- `Phase0 truth`가 `work_guard`에 제대로 번역됐는지 판단
- protagonist-first 철학 drift 여부 확인
- freeze 전 manual audit 수행

입력:

- `phase0_design`
- `work_guard draft`
- 필요 시 upstream law docs

성격:

- human-first
- PASS / HOLD / REJECT
- `TR` 생성 전 반드시 수행

### 5.3 WG-V3 Drift Audit

역할:

- freeze된 `work_guard`가 실제 `TR`에 살아 있는지 확인
- `mandatory_scene_engines`, `tracking_slots`, `forbidden_flattenings` drift 확인

입력:

- frozen `work_guard`
- early `TR` block or first draft

성격:

- human-led, prompt-assisted 가능
- Director `work identity drift`와 같은 축

현실 적용 메모:

- 전용 `WG-V3` 도구가 아직 없으면 Director `open_review`의 `work identity drift`를 임시 audit lane으로 사용한다

## 6. Recommended Operating Sequence

권장 운영 순서는 아래다.

1. `Phase0 truth`를 잠근다
2. `work_guard draft`를 생성한다
3. `WG-V1 Shape Validator`를 통과시킨다
4. `WG-V2 Freeze Checklist`로 PASS/HOLD/REJECT를 준다
5. PASS면 `work_guard freeze`
6. freeze된 `work_guard` 기준으로 `TR`을 생성한다
7. 첫 블록 또는 초기 draft에서 `WG-V3 Drift Audit`를 수행한다

한 줄로 압축하면:

- `Phase0 -> WG-V1 -> WG-V2 -> freeze -> TR -> WG-V3`

## 7. WG-V1 Shape Validator Spec

freeze 최소 키셋은 아래다.

- `work_identity.one_line_truth`
- `work_identity.tracking_slots`
- `work_identity.mandatory_scene_engines`
- `work_identity.forbidden_flattenings`
- `work_identity.protagonist_weapon`

### 7.1 Hard Fail Conditions

아래는 즉시 FAIL이다.

- YAML parse 실패
- root structure 불량
- `work_identity` mapping 부재 또는 타입 오류
- `one_line_truth` 부재 또는 빈 값
- `tracking_slots` 타입 오류
- `mandatory_scene_engines` 타입 오류
- `forbidden_flattenings` 타입 오류
- `protagonist_evaluation` 타입 오류

### 7.2 Soft Fail / HOLD Conditions

아래는 shape는 맞지만 freeze 전 HOLD다.

- `tracking_slots`가 0개
- `mandatory_scene_engines`가 0개
- `forbidden_flattenings`가 너무 얕거나 비어 있음
- 값이 모두 지나치게 generic함
- upstream philosophy 원문을 장문으로 복붙함

### 7.3 Recommended Basic Counts

- `tracking_slots`: 2~4개
- `mandatory_scene_engines`: 2~3개
- `forbidden_flattenings`: 4~8개
- `protagonist_weapon`: 최소 1개 이상
- `admiration_axes`: 최소 2개 이상

이 숫자는 문법 강제가 아니라 operator 권장선이다.

## 8. WG-V2 Freeze Checklist

`WG-V2`는 `이 작품의 철학이 work_guard에 살아 있나`를 본다.

아래 체크리스트는 전부 `yes / no / weak`로 판정한다.

### 8.1 Protagonist Truth

- `one_line_truth`가 이 작품의 protagonist-first 한 줄 진실을 담고 있는가
- generic theme 소개가 아니라 주인공 장악 판타지를 말하는가
- 독자가 `왜 이 작품의 주인공이 멋있는가`가 바로 읽히는가

### 8.2 Tracking Slots

- `tracking_slots`가 단순 성장 로그가 아니라 서열/통제/평가 수정 축인가
- 각 slot이 반복 추적 가능한 형태인가
- `성장`, `성공`, `열심히 함` 같은 generic slot으로 흐르지 않았는가

### 8.3 Mandatory Scene Engines

- 첫 블록 3~6화 내 간판 장면의 형태가 들어 있는가
- `저건 쟤라서 가능했다`가 scene engine으로 번역되어 있는가
- 단순 규모 큰 이벤트가 아니라 주인공 고유 유능함이 드러나는 구조인가

### 8.4 Forbidden Flattenings

- 회개물 스타트
- 비굴한 해명/인정 구걸
- 자기연민 소비
- success 이후 pure punishment spiral
- 주인공 고유성 없는 대형 성과
- 활약 후 태도 변화 없음
- 위기 때 빈손/무대응/무보상

위 항목 중 작품에 치명적인 drift가 충분히 들어 있는가를 본다.

### 8.5 Protagonist Weapon

- 주인공만의 독점적 유능함이 명시되어 있는가
- `판을 먼저 읽는 능력`, `허가 병목을 짚는 판단`, `정보격차 활용`처럼 인과가 보이는가
- 누구에게나 적용될 generic competence로 흐르지 않았는가

### 8.6 Reward Vector

- 초반 보상이 `돈`보다 `서열 변화` 쪽으로 잡혀 있는가
- 주인공 재평가 방식이 `admiration_axes`에 들어 있는가
- 주변의 태도 변화가 영수증처럼 찍히게 설계되어 있는가

### 8.7 Crisis Doctrine

- 주인공이 위기를 먼저 읽는 축이 살아 있는가
- 대응 수단을 쥐고 들어가는 구조가 살아 있는가
- 최소 피해 통제 철학이 보이는가
- 큰 피해가 있다면 고평가/찬사/다음 카드가 붙게 설계되어 있는가

### 8.8 Translation Discipline

- upstream law 문서를 장문 복붙하지 않았는가
- 대신 작품별 doctrine으로 압축되었는가
- `작가 교육문`이 아니라 `runtime rule`로 번역되었는가

## 9. WG-V2 Verdict Rule

### PASS

아래가 모두 성립해야 한다.

- protagonist-first truth가 선명하다
- 첫 블록 간판 장면 엔진이 보인다
- tracking / reward / crisis doctrine이 살아 있다
- 금지 drift가 충분히 막혀 있다
- generic 문구보다 작품 특유의 doctrine이 앞선다

### HOLD

아래 중 하나면 HOLD다.

- 형식은 맞지만 generic하다
- 주인공 고유성보다 산업/소재 소개가 앞선다
- scene engine은 있는데 reward vector가 약하다
- drift 금지 목록이 얕다
- upstream truth가 압축되지 않고 덜 정리됐다

### REJECT

아래 중 하나면 REJECT다.

- protagonist-first truth가 안 보인다
- 주인공 고유 유능함이 안 보인다
- 첫 블록 임팩트 장면이 guard에 안 잡힌다
- 회개/비굴/자기연민/운빨 생존 같은 금지 drift를 사실상 허용한다
- `work_guard`가 runtime doctrine이 아니라 generic memo 수준이다

## 10. WG-V3 Drift Audit

`WG-V3`는 `frozen work_guard`와 실제 `TR` 사이의 이탈을 본다.

최소 점검축은 아래다.

- 핵심 `tracking_slots`가 `TR`에서 통째로 사라지지 않았는가
- `mandatory_scene_engines`가 첫 블록에서 실제 장면으로 찍히는가
- `forbidden_flattenings` 중 치명 drift가 발생하지 않았는가
- 주인공 고유 무기가 결과의 원인으로 보이는가
- 활약 뒤 태도 변화가 영수증처럼 남는가

판정은 아래처럼 단순화한다.

- `PASS`: 살아 있다
- `DRIFT-WARN`: 약해졌다
- `DRIFT-FAIL`: 사실상 사라졌다

## 11. Suggested Minimal Operator Sheet

실전에서는 아래 7문항만 먼저 보면 된다.

1. `one_line_truth`를 읽었을 때 주인공 장악 판타지가 바로 보이는가
2. `tracking_slots`가 성장 로그가 아니라 서열/통제/재평가 축인가
3. 첫 블록 간판 장면이 `mandatory_scene_engines`에 잡혀 있는가
4. `저건 쟤라서 가능했다`가 `protagonist_weapon`으로 명시되어 있는가
5. `forbidden_flattenings`가 우리 치명 drift를 충분히 막고 있는가
6. 초반 보상이 자산 증가보다 태도 변화/서열 변화로 잡혀 있는가
7. 위기 철학이 `선독 -> 대비 -> 최소 피해 -> 보상`으로 번역되어 있는가

이 7개 중 2개 이상이 `no`면 HOLD, 3개 이상이 치명적 `no`면 REJECT로 본다.

## 12. Recommended Future Packaging

코드 수정 없이 운영만 할 때는 아래 패키지가 가장 ROI가 높다.

1. 이 spec 문서
2. 한 장짜리 `WG-V2 freeze checklist`
3. 한 장짜리 `WG-V3 drift audit card`

반대로 바로 코드로 들어갈 때는 아래 순서가 좋다.

1. `WG-V1` shape validator contract 정리
2. CLI or script 추가
3. UI/bridge summary에 verdict surface 추가
4. 필요하면 narrative-router readiness 승격 검토

## 13. Recommendation

오늘 기준 추천은 이거다.

- `BI/TR`처럼 완전히 동일한 감리 체계를 복제하지 않는다
- 대신 `WG-V1 / WG-V2 / WG-V3` 3단 구조로 분리한다
- material 팀은 우선 `WG-V2 freeze checklist`부터 운영한다
- downstream drift가 체감되면 `WG-V3`를 정식 감리 단계로 승격한다

한 줄 결론:

- `work_guard`는 BI/TR처럼 "산출물 자체 품질 감리"보다 `철학 번역 품질 + drift 방지 감리`에 더 최적화된 validator가 맞다
