# TR-BI Hybrid Salvage Plan

> 인코딩: UTF-8
> 작성일: 2026-03-10
> 상태: 실행 문서
> 목적: `기업물 + 재벌물 + 투자물` 혼합 기획 의도가 `investment` 공용 템플릿으로 평탄화된 `TR/BI`를 수습하기 위한 기준선 고정

---

## 0. 전제 수정

이 사안은 `BI가 먼저 TR을 오염시켰다`로 보기 어렵다.

현재 작업 흐름이 실질적으로 `TR 생성 -> BI 동기화`라면, 더 정확한 진단은 아래다.

1. 상위 컨셉/기획 입력이 이미 `investment` 템플릿 쪽으로 기울어졌다.
2. `treatment-production-harness-v2.md`가 그 방향을 더 강하게 고정했다.
3. 이후 `BI`는 `TR`을 동기화하며 그 결과를 굳혔다.

즉 원인축은 `BI 단독`이 아니라 `상위 기획 + treatment 하네스 + TR 결과물`이다.

---

## 1. 현재 판정

### 1.1 정합성 우위

현재 `TR`과 직접 정합한 쌍은 아래 3개다.

- `03_chaebol_ent_empire_tr_block_070_draft.json` <-> `03_chaebol_ent_empire_bi.json`
- `04_defense_defect_engineer_tr_block_070_draft.json` <-> `04_defense_defect_engineer_bi.json`
- `08_us_ai_exile_monopoly_tr_block_070_draft.json` <-> `08_us_ai_exile_monopoly_bi.json`

근거:

- Block 1 제목/상황/주인공 설정이 직접 이어진다.
- 현재 파이프라인 상 `TR`을 즉시 소비하려면 이 3개가 안전하다.

### 1.2 작품 정체성 우위

장르 정체성/개성만 놓고 보면 아래 3개가 더 강하다.

- `09_bi_chaebol_ent_empire_entertainment.json`
- `10_bi_defense_defect_engineer_defense_business.json`
- `11_bi_us_ai_exile_monopoly_ai_business.json`

판정:

- `03/04/08` = 현재 실행 정본
- `09/10/11` = 더 선명한 장르 정체성을 가진 승격 후보

---

## 2. 무엇이 잘못 눌렸는가

### 2.1 하네스 영향

`docs/blockguide/treatment-production-harness-v2.md`는 아래 축을 강하게 고정한다.

- `capital_before / capital_after`
- `deal_type`
- `성장률`
- `투자물 거래 유형 확장 (15종+)`

이 구조는 `기업물/재벌물/엔터물/방산물/AI사업물`도 쉽게 `투자 실행 단위`로 번역하게 만든다.

### 2.2 실제 결과

현재 `03/04/08` 계열 BI는 장르 고유성보다 `investment` 프레임이 먼저 보인다.

예:

- `03_chaebol_ent_empire_bi.json`
  - `_genre = investment`
  - `genre_archetype = investment + chaebol + business strategy`
- `04_defense_defect_engineer_bi.json`
  - 방산물 고유 무기보다 투자/경영 템플릿이 더 전면에 배치됨
- `08_us_ai_exile_monopoly_bi.json`
  - AI 사업물보다 투자 템플릿으로 먼저 읽힘

반면 `09/10/11`은 각 장르의 핵심 무기가 더 앞에 서 있다.

---

## 3. 수습 원칙

### 3.1 지금 당장 하지 말 것

- `03/04/08`을 바로 삭제하거나 덮어쓰지 않는다.
- `09/10/11`을 현재 `TR`에 바로 꽂지 않는다.
- 번호 체계를 다시 흔들지 않는다.

### 3.2 지금 바로 할 것

1. `03/04/08`은 `legacy-executable pair`로 본다.
2. `09/10/11`은 `promotion candidate bible`로 본다.
3. 이후 재생성은 `09/10/11 -> 신규 TR` 방향으로 간다.
4. 기존 `TR`을 억지로 `09/10/11`에 맞춰 수선하지 않는다.

이유:

- 현재 `TR`은 이미 `03/04/08`과 블록 단위로 물려 있다.
- `09/10/11`은 설정과 장르 무게중심이 달라 직접 patch보다 `재생성`이 안전하다.

---

## 4. 작품별 판정

### 4.1 03 vs 09

- `03`은 현재 `TR`과 정합함
- `09`는 엔터물 정체성이 더 강함

권장:

- 단기: `03` 유지
- 중기: `09`를 정본 후보로 승격하고 `TR` 재생성

### 4.2 04 vs 10

- `04`는 현재 `TR`과 정합함
- `10`은 방산 사업물로서 훨씬 자연스러움

권장:

- 단기: `04` 유지
- 중기: `10` 기반으로 신규 `TR` 생성

### 4.3 08 vs 11

- `08`은 현재 `TR`과 정합함
- `11`은 AI 사업물 정체성이 더 명확함

권장:

- 단기: `08` 유지
- 중기: `11` 기반으로 신규 `TR` 생성

---

## 5. 다음 실행 순서

### Step 1. 하네스 보정 문서 작성

목표:

- `기업물 + 재벌물 + 투자물` 혼합형 treatment 하네스 작성
- `investment` 단일 프레임 과압축을 막는 규칙 추가

필수 보정 포인트:

- `deal_type`를 투자행위뿐 아니라 장르 고유 행위로 확장
- `capital` 외에 `통제권/규격권/팬덤/지식재산/정치적 레버리지` 축 병행
- `genre_ext.type = investment` 일괄 고정을 금지

### Step 2. 09/10/11 승격 후보 검토표 작성

각 작품마다 아래만 비교한다.

- title
- genre_archetype
- logline
- protagonist edge
- desire
- crisis
- commercial code

### Step 3. 후보 1개씩 신규 TR 재생성

원칙:

- 기존 `03/04/08 TR` 수정이 아니라
- `09/10/11` 기준 신규 `TR` 생성

### Step 4. 신규 TR 확정 후 BI 재동기화

순서:

- 신규 `TR` 확정
- 그 다음 `BI` 동기화

즉 `TR -> BI` 순서를 유지하되, 입력 SSOT를 바꾼다.

---

## 6. 최종 결론

현재 문제는 `TR이 혼자 잘못 잡힌 것`이 아니다.

더 정확히는:

- 혼합 장르 의도는 있었지만
- 실제 생산축에서는 `investment` 공용 템플릿이 우세했고
- 현재 `03/04/08`은 그 결과물로서 실행 정합성은 높지만 장르 개성은 약하다
- `09/10/11`은 장르 개성이 더 강하므로 차기 정본 후보로 보는 것이 타당하다

따라서 수습은 아래 순서가 맞다.

1. 현재 정본을 성급히 뒤집지 않는다.
2. `09/10/11`을 승격 후보로 고정한다.
3. 하네스를 먼저 보정한다.
4. 그 다음 `09/10/11` 기반으로 `TR`을 새로 뽑는다.
5. 마지막에 `BI`를 다시 동기화한다.
