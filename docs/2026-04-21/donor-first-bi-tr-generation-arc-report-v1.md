# Donor-First BI/TR Generation Arc Report V1

Date: 2026-04-21
Status: active
Scope: material-side 기준 `donor-first` 방식으로 fresh work의 `BI/TR`를 생성할 때 필요한 arc 계층, artifact flow, stage-safe 운영안을 정리한 아이디어 보고서
Source Anchors:
- `C:\Users\wjjo\Desktop\글도비\material_ssot\README.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\stage-read-order.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\donor-review-and-adoption-contract-v1.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-benchmark-spec-v1.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\20_pitch\pitch-philosophy.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\20_pitch\cider-doctrine-v1.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\20_pitch\investment-opening-pacing-spec-v1.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\20_pitch\work-guard-translation-map.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\20_pitch\canon\canonical_pitch_template_v1.md`
- `C:\Users\wjjo\Desktop\글도비\material_ssot\20_pitch\canon\smart_new_hire.md`
- `C:\Users\wjjo\Desktop\재료 생산 R&D 랩\docs\2026-04-21\chaebol-investment-4donor-parallel-usage-report-v1.md`
Document Audit:
- Pass 1: complete
- Pass 2: complete
- Pass 3: complete
- Estimated Confidence: 95%

## 1. 질문 재정의

질문은 `기존 BI/TR을 만든 뒤 donor를 적용할까`가 아니다.

더 정확한 질문은 아래다.

- `fresh work`를 만들 때 donor를 upstream engine으로 먼저 고르고
- 그 donor law를 소재와 family에 맞게 번역한 뒤
- 그 번역 결과로 `BI/TR`를 처음부터 생성할 수 있는가

판정은 `가능하다` 쪽이다.

다만 조건이 있다.

- donor를 곧바로 `BI/TR`에 복사하면 안 된다.
- donor와 block 사이에 `arc translation layer`가 반드시 필요하다.
- canonical home은 여전히 `Phase0`와 `work_guard`여야 한다.

즉 정답은 `donor-first direct copy`가 아니라 `donor-first translated generation`이다.

## 2. Executive Verdict

- `fresh work`에는 donor-first 생성 방식이 오히려 더 적합하다.
- 하지만 donor만으로 바로 `BI/TR`를 찍으면 중간 설계층이 비어 버린다.
- 그 빈 층이 바로 `arc grammar`다.

한 줄로 줄이면 아래다.

`donor law -> arc ladder -> block contract -> BI/TR emission`

이 네 단계가 있어야 donor-first가 stage-safe하게 굴러간다.

## 3. 왜 Arc가 필요한가

### 3.1 donor만으로는 너무 추상적이다

`불행재벌`, `막둥이`, `흙수저`, `주식의 신` 같은 donor는 모두 강한 doctrine을 준다.

하지만 donor가 바로 알려 주는 것은 보통 아래다.

- reward cadence
- proof / receipt / next gate
- protagonist role shift
- helper / witness / operator 구조
- contamination ban

반대로 donor만으로는 아래가 자동으로 나오지 않는다.

- 이 작품에서 첫 번째 전장이 어디서 끝나는가
- block 몇 개가 모여 어떤 named battlefield shift를 만드는가
- `BI`에는 무엇을 저장하고 `TR`에는 무엇을 실행할 것인가

즉 donor는 엔진이지만, 설계도 전체는 아니다.

### 3.2 block만으로는 너무 국소적이다

material-side에서 `TR block`은 `2~6화`짜리 planning bundle이다. [material_ssot/README.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/README.md:82)

또 opening benchmark는 엄격하게 `TR blocks 2~6` 안에서

- protagonist-only proof
- evaluation revision
- visible reward token
- next gate opening

을 요구한다. [production-pair-benchmark-spec-v1.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/00_governance/production-pair-benchmark-spec-v1.md:44)

즉 block은 실행 단위로는 충분히 촘촘하지만, 그 위의 큰 방향을 스스로 제공하지는 않는다.

### 3.3 그래서 중간층이 필요하다

arc는 여기서 `장편 서사의 거대한 챕터 이름`이 아니다.

여기서 필요한 arc는 아래 역할을 맡는 번역층이다.

- donor law를 작품-specific battlefield로 변환
- 여러 block을 하나의 named advance로 묶음
- `BI`가 기억해야 할 큰 질서와 `TR`이 실행해야 할 작은 payback을 분리

## 4. 권장 계층 구조

### 4.1 Layer 1: Donor Law

여기서는 `core donor 1개 + specialist donor 1개 이하`만 허용한다.

- `core donor`
  작품의 주 엔진
- `specialist donor`
  빠진 한 축만 보강

권장 예시는 아래다.

- family / heir / authority work:
  `불행재벌 core + 막둥이 specialist`
- founder / business-expansion work:
  `흙수저 core + 주식의 신 specialist`

여기서 끝내면 안 된다.
이 단계는 아직 annex 또는 donor review 단계다.

### 4.2 Layer 2: Macro Arc Ladder

macro arc는 `여러 TR block`을 묶는 named battlefield shift다.

이 층에서 결정해야 하는 것은 아래다.

- opening에서 어떤 macro battlefield를 점령하는가
- 그 다음 battlefield는 어떤 종류의 gate로 열린 것인가
- reward token이 다음 arc에서 어떻게 resource나 authority로 재사용되는가

좋은 macro arc 문법 예시는 아래다.

- `진입 arc`
- `첫 proof/receipt arc`
- `첫 seat or authority arc`
- `확장 / counterplay arc`
- `상위 gate / second battlefield arc`

macro arc는 `BI`가 기억해야 하는 큰 엔진에 가깝다.

### 4.3 Layer 3: Bundle Arc

bundle arc는 `TR block 하나`에 해당하는 미니 arc다.

각 bundle arc는 최소한 아래를 가져야 한다.

- block-specific proof
- same-block receipt
- receipt kind
- next gate contribution

이건 사실상 `canonical pitch`의 `first_block_cider_ledger`와 같은 문법으로 이미 workspace에 들어와 있다. [canonical_pitch_template_v1.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/20_pitch/canon/canonical_pitch_template_v1.md:41)

핵심은 이거다.

- `block`은 서브 장면 묶음이 아니라 `same-block payback unit`이다.
- 따라서 block 하나는 작은 arc처럼 설계해야 한다.

### 4.4 Layer 4: Episode-Side Sell-In

serialized episode 관점에서는 하나의 bundle arc가 대략 `2~6화`로 펼쳐질 수 있다.

다만 investment-family / business-power opener는 더 빠르게 압축해야 한다.

- 건강한 기본값:
  `1~3화` 안에 첫 proof / reevaluation / ticket
- `4화`는 soft ceiling
- `5화+`는 느린 opening 의심

이 원칙은 [investment-opening-pacing-spec-v1.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/20_pitch/investment-opening-pacing-spec-v1.md:46)과 맞닿아 있다.

즉 `TR blocks 2~6`와 `serialized episodes 1~3`는 서로 다른 단위지만, operator는 두 리듬을 동시에 번역해야 한다.

## 5. Stage-Safe Generation Model

이 모델은 stage chain을 바꾸지 않는다.

공식 체인은 그대로 유지한다.

- `리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성`

다만 각 단계에서 donor-first를 아래처럼 처리한다.

### 5.1 Research

수집 대상:

- 소재 truth
- family truth
- candidate donor set
- contamination red lines

산출:

- material pack
- donor review note

여기서 donor를 고른다.
하지만 아직 canonical law로 쓰지 않는다.

### 5.2 Pitch

여기서 donor를 `generalized law`로 번역한다.

필수 질문:

- core donor는 누구인가
- specialist donor는 필요한가
- first-block cider는 무엇인가
- opening reward vector는 무엇인가
- first reward가 어떤 next gate를 여는가

pitch는 이미 `first_block_cider_ledger`와 `phase0_handoff_note`를 요구한다. [pitch-philosophy.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/20_pitch/pitch-philosophy.md:168)

즉 donor-first 생성은 pitch 단계에서 이미 가능하다.

### 5.3 Phase0

여기가 핵심이다.

Phase0는 donor를 block architecture로 바꾸는 실제 번역층이 되어야 한다.

권장 포함 항목:

- `macro_arc_ladder`
- `opening_bundle_contract`
- `bundle_role_map`
- `resource_ladder`
- `authority_carrier_map`
- `contamination_guard`

이 중 donor 이름은 annex에 두고, canonical Phase0에는 번역 결과만 둔다.

### 5.4 work_guard

`work_guard`는 donor packet을 집어넣는 곳이 아니다.

여기에는 오직 압축 결과만 둔다. [work-guard-translation-map.md](/C:/Users/wjjo/Desktop/글도비/material_ssot/20_pitch/work-guard-translation-map.md:38)

즉 donor-first 작품의 `work_guard`는 보통 아래만 가진다.

- `tracking_slots`
- `mandatory_scene_engines`
- `forbidden_flattenings`
- `evaluation_thresholds`
- `custom_rules`

### 5.5 TR

TR은 donor를 설명하는 곳이 아니다.

TR은 `bundle arc`를 실행하는 곳이다.

각 block은 아래 형태로 읽혀야 한다.

- this block proves one specific thing
- this block cashes one specific receipt
- this block opens one specific next gate

### 5.6 BI

BI는 block-by-block scene plan을 저장하는 곳이 아니다.

BI는 아래를 저장하는 곳이다.

- macro arc law
- protagonist role shift law
- reward token taxonomy
- helper / witness / operator taxonomy
- resource ladder
- authority carrier taxonomy
- contamination bans

즉 donor-first 작품이라면 `BI`는 큰 arc 질서를, `TR`은 block 실행 질서를 담당해야 한다.

## 6. 제안 Artifact 분업

새 stage root를 만들 필요는 없다.

대신 아래 분업을 쓰는 것이 좋다.

### 6.1 Annex: `donor_adoption_packet`

목적:

- core donor / specialist donor 기록
- adopted / rejected 근거
- contamination guard 기록

이건 canonical home이 아니라 provenance annex다.

### 6.2 Canonical Pitch

목적:

- one-line premise
- core engine
- repeatable loop
- internal arc
- first-block cider ledger

이 단계에서 opening translation은 이미 잠겨야 한다.

### 6.3 Canonical Phase0

목적:

- macro arc ladder
- bundle arc contract
- opening bundle contract
- shared handoff for `BI/TR`

이 문서가 사실상 donor-first generation의 진짜 뼈대다.

### 6.4 `work_guard`

목적:

- Phase0에서 살아남아야 하는 engine만 짧게 압축

### 6.5 BI

목적:

- arc law와 taxonomy 보존

### 6.6 TR

목적:

- block execution

## 7. 권장 설계 포맷

실무적으로는 아래 포맷이 가장 유효하다.

### 7.1 Macro Arc Row

- `arc_id`
- `arc_name`
- `battlefield`
- `entry_condition`
- `representative_reward`
- `next_gate_type`
- `dominant_resource`

### 7.2 Bundle Arc Row

- `block_no`
- `block_function`
- `proof_scene`
- `same_block_receipt`
- `receipt_kind`
- `reevaluation_weight`
- `next_gate_output`

### 7.3 BI Arc Map

- `arc_name`
- `protagonist_role_shift`
- `resource_conversion`
- `authority_carrier`
- `opposition_mode`
- `contamination_watch`

이 세 장이 있으면 `BI`와 `TR`이 같은 upstream skeleton에서 나올 수 있다.

## 8. 도메인별 적용 예시

### 8.1 Family / Heir Work

추천 donor:

- core: `불행재벌`
- specialist: `막둥이`

macro arc 예시:

1. `가문 진입`
2. `첫 private proof`
3. `첫 seat / naming`
4. `family board inversion`
5. `public steering`

bundle arc에서 강하게 봐야 하는 것:

- private room proof
- same-block status shift
- named authority receipt
- next adult gate

### 8.2 Founder / Business-Expansion Work

추천 donor:

- core: `흙수저`
- specialist: `주식의 신`

macro arc 예시:

1. `seed capture`
2. `first proof / first witness`
3. `first asset install`
4. `first platform or document authority`
5. `adjacent vertical opening`

bundle arc에서 강하게 봐야 하는 것:

- execution move
- observer tone shift
- asset or authority token
- next battlefield ticket

## 9. 무엇을 새로 만들고 무엇을 만들지 말아야 하나

### 9.1 만들어야 하는 것

- donor-first annex packet
- Phase0의 arc ladder
- bundle arc contract
- BI/TR shared upstream skeleton

### 9.2 만들지 말아야 하는 것

- donor 이름이 박힌 canonical BI
- donor proper noun이 가득한 canonical Phase0
- `TR`보다 더 위에 또 다른 stage root
- `arc`라는 이름만 붙은 vague 문서
- `opening arc` 같은 말을 쓰고 absolute block number를 비워 두는 설계

## 10. 가장 중요한 운영 규칙

### 10.1 arc는 선택이 아니라 번역층이다

donor-first를 하려면 arc는 필요하다.

하지만 그 arc는 거대한 문학 이론이 아니라 아래 역할만 하면 된다.

- donor law를 battlefield로 번역
- block에 역할을 배정
- `BI`와 `TR`가 같은 skeleton을 공유하게 만듦

### 10.2 block은 mini arc여야 한다

각 block은 `same-block receipt`가 있어야 한다.

즉 `proof only`, `setup only`, `later payoff only` block은 donor-first에서도 실패다.

### 10.3 BI와 TR은 동시에 나와야 한다

`BI 먼저 -> TR 나중` 또는 `TR 먼저 -> BI 보정`보다,

- 같은 Phase0 arc ladder에서
- `BI arc map`
- `TR block map`

를 동시에 분기시키는 편이 더 낫다.

## 11. Immediate Pilot Proposal

가장 안전한 파일럿은 아래다.

1. 소재 하나 선정
2. core donor 1개 선정
3. specialist donor 1개 이하 선정
4. donor adoption packet 작성
5. canonical pitch에 `first_block_cider_ledger` 작성
6. Phase0에 `macro_arc_ladder + bundle arc contract` 작성
7. `work_guard`에 tracking slots 압축
8. 같은 skeleton에서 `BI arc map`과 `TR block map` 동시 생성
9. opening benchmark로 `TR blocks 2~6` 검증

이 파일럿이 통과하면 donor-first generation은 개념 검토를 넘어 operator path가 된다.

## 12. Final Verdict

`도너를 뼈대로 삼아 소재를 고르고 BI/TR을 바로 만든다`는 방향은 맞다.

하지만 그 문장을 stage-safe하게 다시 쓰면 아래가 된다.

`도너를 core engine으로 고르고, arc ladder로 번역하고, 그 Phase0 skeleton에서 BI와 TR을 동시에 생성한다.`

즉 필요한 것은 `arc를 만들까 말까`가 아니라,

- donor 위에
- 어떤 arc grammar를 두고
- 그 arc를 어떤 block contract로 내릴 것인가

를 명시하는 것이다.

이 보고서 기준으로는 `donor-first BI/TR generation`은 충분히 실전 가능한 안이다.
다만 성공 조건은 `direct donor copy`가 아니라 `Phase0 arc translation`이다.
