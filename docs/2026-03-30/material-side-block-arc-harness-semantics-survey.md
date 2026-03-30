# Material-Side Block / Arc Harness Semantics Survey

Date: 2026-03-30
Status: final (3-pass audited)
Document Type: bounded harness semantics survey
Canonical Path: `docs/2026-03-30/material-side-block-arc-harness-semantics-survey.md`
Temp Mirror Path: none
Commit State:
- Baseline Commit: `e52c061ac1f3fdb95a4b1149b4ea66243961656a`
- Baseline Dirty Summary: `dirty: tracked narrative docs and stage0 harness docs, tracked chaebol TR/BI artifacts, many pre-existing untracked temp/reference assets`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: 97%
Scope:
- `전처리_ssot` material-side harness semantics
- Stage 0 -> blockguide handoff terminology
- `block`, `macro arc`, `episode checkpoint`, `opening representative spike` vocabulary
- harness wording that can contaminate `phase0_design`
Out of Scope:
- runtime code normalization
- episode artifact generation lanes
- work-level TR/BI/body repair
- family-wide redesign

Source Evidence:
- `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
- `전처리_ssot/docs/stage0_material_collection_harness.md`
- `전처리_ssot/docs/stage0_source_manifest_harness.md`
- `docs/narrative-router/what-how-craft-harness.md`
- `docs/blockguide/treatment-planning-harness.md`
- `docs/blockguide/treatment-production-harness-v2.md`
- `treatments/office_checkup_next_day_phase0_design.json`

---

## 1. Executive Verdict

현재 문제의 본질은 `재료 사이드 하네스`가 `block`을 노골적으로 `화`라고 정의해서가 아니다.

문제는 아래 두 가지다.

1. Stage 0 하네스가 `episode checkpoint`와 `block-scale extraction`을 한 문장 안에서 섞어 쓴다.
2. Stage 0 하네스가 `blockguide macro arc`를 명시적으로 재정의하지 않은 채 downstream 표현을 부분 차용한다.

그 결과, material 수집/manifest 작성 단계에서 다음 오염이 쉽게 발생한다.

- `ep1`에서 본 장면 = `Block 1` 전체라고 착각
- `Block 1 spike`를 episode-sized beat로 축소
- `arc`를 10블록 대단원이 아니라 느슨한 이야기 덩어리로 오해

즉 이번 lane의 수정 대상은 runtime 코드가 아니라 하네스 문구와 handoff 계약이다.

---

## 2. Stable Meanings To Preserve

### 2.1 `block`

이 lane에서 `block`은 `2~6화 분량의 이야기 덩어리`다.

Evidence:

- `docs/narrative-router/what-how-craft-harness.md:124`
  - `1 block ~= 5화`
  - `Block 1`은 이미 `2~6화권`

운영 해석:

- Stage 0는 block-scale 연료를 모아야지, single-episode beat sheet를 만드는 단계가 아니다.

### 2.2 `macro arc`

이 lane에서 `arc`는 기본적으로 `10블록 대단원`을 뜻해야 한다.

Evidence:

- `docs/blockguide/treatment-planning-harness.md:758`
  - `7대단원 한 줄 골격`
- `docs/blockguide/treatment-planning-harness.md:759`
  - `각 10블록 묶음`
- `docs/blockguide/treatment-production-harness-v2.md:430`
  - `7개 대단원(각 10블록)`
- `docs/blockguide/treatment-production-harness-v2.md:484`
  - `대단원 7개, 각 대단원에 10블록 슬롯 개요`

운영 해석:

- 재료 사이드 하네스에서는 `arc`라고만 쓰지 말고, 가능하면 `macro arc` 또는 `대단원`으로 고정하는 편이 안전하다.

### 2.3 `episode checkpoint`

Stage 0 수집에서 `ep1`, `ep5`, `ep10` 같은 표현은 설계 단위가 아니라 참고 원고를 읽기 위한 sampling anchor다.

운영 해석:

- `episode checkpoint`는 source reading anchor
- `block`은 설계 추출 단위
- 둘은 같지 않다

---

## 3. Confirmed Material-Side Drift

### 3.1 Stage 0 Integrated Order Has No Explicit Semantics Table

`SSOT_stage0_preprocess_integrated_order.md`는 Stage 0의 산출물, 단계 판정, stop/go는 잘 잠가 놓았지만, `block / macro arc / episode checkpoint`를 구분하는 전용 표가 없다.

Evidence:

- `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
  - Stage 0 산출물/단계 규칙은 상세함
  - 그러나 block-scale과 source checkpoint를 구분하는 dedicated term contract는 부재

영향:

- Stage 0 문서만 먼저 읽는 운영자/에이전트는 downstream의 `10블록 대단원` 규약을 알기 전에 자기 해석을 넣기 쉽다.

### 3.2 Material Collection Harness Mixes Episode Sampling And Block Extraction

`stage0_material_collection_harness.md`에는 아래와 같은 혼합 표현이 있다.

Evidence:

- `전처리_ssot/docs/stage0_material_collection_harness.md:160`
  - `ep1 또는 Block 1을 직접 못 읽었는데`
- `전처리_ssot/docs/stage0_material_collection_harness.md:178`
  - `Block 1 spike`, `first reward`, `초반 30화 확장축`

문제:

- `ep1`과 `Block 1`은 동일 증거 단위가 아니다.
- source sampling에서 `ep1`을 읽는 것은 valid하다.
- 그러나 거기서 추출하는 설계 재료는 `opening block spike`, `block-scale first reward retention`처럼 번역되어야 한다.

즉 현재 문구는 `reference reading anchor`와 `design extraction unit`을 혼동하게 만든다.

### 3.3 Source Manifest Harness Encourages Good Extraction But Leaves Scale Implicit

`stage0_source_manifest_harness.md`는 `Slim Reference Card` 기반 extraction을 요구하는 점은 좋다. 다만 block-scale 전환 규칙이 명시적으로 없다.

Evidence:

- `전처리_ssot/docs/stage0_source_manifest_harness.md:106`
  - `Block 1 spike / first reward / authority gain route`

문제:

- 이 표현은 downstream blockguide 문맥에서는 맞다.
- 하지만 Stage 0 문맥에서는 먼저 `source-level episode evidence -> block-scale synthesis` 번역 규칙을 선언해야 한다.

없으면 다음 둘 중 하나가 발생한다.

- `Block 1 spike`를 episode 1의 작은 장면으로 축소
- 반대로 ep1에서 본 인상 하나를 Block 1 전체로 과대 일반화

### 3.4 Downstream BlockGuide Already Separates Structure Unit And Execution Unit

문제의 근원은 downstream blockguide core가 아니라 upstream material-side wording이다.

Evidence:

- `docs/blockguide/treatment-production-harness-v2.md:28-30`
  - `10블록은 대단원 구조/감리 창(window)일 뿐, 출력 단위가 아니다`
  - `70블록 일괄 생성이나 10블록 일괄 생성은 금지`
- `docs/blockguide/treatment-production-harness-v2.md:249`
  - `내부 실행 단위는 항상 Block 1개`

해석:

- downstream은 이미 `10블록 대단원`과 `실행 단위 Block 1개`를 분리한다.
- 따라서 이번 wave는 blockguide 전체 재설계보다, Stage 0가 downstream 의미를 오염 없이 handoff하도록 고치는 것이 ROI가 높다.

### 3.5 Live Phase 0 Symptom Already Points Toward Better Vocabulary

현재 `office_checkup_next_day_phase0_design.json`은 opening macro arc 내부의 대표 폭발을 `ARC-01 대표 스파이크` 수준으로 읽는 것이 더 자연스럽다.

Evidence:

- `treatments/office_checkup_next_day_phase0_design.json`
  - `ARC-01` block slot 7 function: `ARC-01 대표 스파이크`

해석:

- operator가 실제 설계 단계에 들어가면 이미 `block 1 one-episode spike`보다 `opening arc representative spike`가 더 안전한 표현이라는 감각을 사용하고 있다.
- 하네스도 이 방향으로 vocabulary를 정규화하는 편이 일관적이다.

---

## 4. Harness-Only Semantics Table

| Term | Locked Meaning | Allowed Use In Material-Side Harness | Disallowed Shortcut |
| --- | --- | --- | --- |
| `block` | 2~6화 분량의 서사 덩어리 | planning fuel, opening block, reward retention, authority gain route | `block = episode` |
| `macro arc` / `대단원` | 10블록 구조 단위 | Phase 0 골격, 입구/출구, block_slots 묶음 | runtime episode bundle 의미로 사용 |
| `episode checkpoint` | source reading anchor | `ep1`, `ep5`, `ep10`, `last` 같은 원고 sampling | 설계 단위처럼 직접 승격 |
| `opening representative spike` | opening macro arc 안의 간판 폭발 | Stage 0 reference extraction, Phase 0 arc function | `ep1 장면 = Block 1 전체` |
| `TR Block 1 spike` | 실제 TR 첫 블록 안의 대표 폭발 | downstream planning/production에서만 명시 | Stage 0에서 무번역 차용 |

---

## 5. Direct Answers

### Q1. 이번 수정 lane에서 `block`을 화처럼 취급해야 하나

아니다.

이번 lane에서 `block`은 끝까지 `이야기 덩어리`다. Stage 0는 그 block를 채울 재료와 방향을 고정하는 단계다.

### Q2. 이번 lane에서 `arc = 10블록`은 유지해야 하나

유지해야 한다.

다만 Stage 0 문서에서는 `arc` 단독 표기보다 `macro arc` 또는 `대단원`으로 명시하는 쪽이 안전하다.

### Q3. 이번 lane에서 제거해야 할 컨텍스트는 무엇인가

이번 문맥에서는 episode artifact generation lane을 의사결정 중심에서 빼야 한다.

즉 이번 wave는:

- runtime arc math
- episode artifact repair
- downstream prose lane

이 아니라,

- Stage 0 material collection
- source_manifest extraction
- Phase 0 macro-arc handoff wording

을 바로잡는 문서 작업이다.

---

## 6. Harness-Only Repair Shape

### 6.1 Primary Targets

1. `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
2. `전처리_ssot/docs/stage0_material_collection_harness.md`
3. `전처리_ssot/docs/stage0_source_manifest_harness.md`

### 6.2 Required Changes

1. Stage 0 엔트리 문서에 `block / macro arc / episode checkpoint` semantics table 추가
2. material collection 문서에 `source sampling -> block-scale extraction` 번역 규칙 추가
3. source manifest 문서에 `opening representative spike`와 `TR Block 1 spike`의 구분 추가
4. `ep1 또는 Block 1` 같은 병치 표현 제거 또는 번역 note 부착

### 6.3 Explicit Non-Goals

- runtime code 수정
- `modules/`, `scripts/`, `tests/` 패치
- 작품별 TR/BI 본문 수정
- blockguide 70블록 구조 재설계

---

## 7. Final Judgment

이번 문제는 `runtime normalization`보다 먼저 `material-side harness normalization`으로 처리하는 게 맞다.

이유:

- operator 오해가 Stage 0에서 먼저 생긴다
- downstream blockguide core는 이미 `10블록 구조`와 `실행 단위`를 상당 부분 분리하고 있다
- 지금 필요한 것은 새로운 구조가 아니라, 하네스가 `block != episode`, `macro arc = 10 blocks`를 먼저 말하게 만드는 것이다

따라서 다음 문서는 code patch 계획이 아니라, `하네스 전용 execution SSOT`여야 한다.
