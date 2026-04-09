# material-side opening pacing false-pass — 전량 처리 계획

Date: 2026-04-09
Status: ready for execution approval
Scope: `material_ssot` material-side benchmark / harness / active pair inventory
Envelope: planning and audit design only; no `TR`, `BI`, `work_guard` payload mutation in this document

---

## 0. 한 줄 결론

`chaebol_allowance_zero`의 opening pacing failure는 **개별 pair 문제 + benchmark false pass + harness blind spot**이 겹친 사건으로 본다.

따라서 해결도 1건 로컬 수정이 아니라 아래 4축 전량 처리로 간다.

1. false authority 동결
2. benchmark / harness law 패치
3. active inventory opening pacing 전량 재감리
4. `pair 02` false-pass archive 고정 + 나머지 실패 pair만 bounded repair

---

## 1. 왜 전량 처리인가

이번 이슈는 단순히 `pair 02`가 느리다는 수준으로 끝나지 않는다.

### 1.1 pair-level failure

- `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
  - `B07`: `장례식장 세탁실`
  - `B08`: `밤새는 청소팀`
  - `B09`: `첫 월 반복매출`
  - `B10`: `도련님 대신 대표` + 호텔 BOH 진입 자격자
- opening macro battlefield가 장례식장 축에 과도하게 머문다.
- 웹소설 opening pacing 기준에서 `첫 월 반복매출`과 형의 눈빛 전환이 `B09/B10`인 것은 느린 축에 속한다.

### 1.2 work_guard threshold mismatch

- `work_guards/02_chaebol_allowance_zero.yaml`
  - `1화 내 첫 사이다`
  - `3화 내 간판 폭발 (장례 특수 끝 후 첫 월 반복매출 증명 -> 형의 눈빛 전환)`
- 현재 live TR은 이 threshold를 문자 그대로 충족하지 않는다.

### 1.3 benchmark false pass

- `docs/2026-04-07/10pair_true_benchmark_terminal02_pair02_report.md`
  - WG threshold를 evidence anchor로 인용
  - 동시에 `#2/#3/#4/#5/#6` strict window만으로 `GREENPLUS` exemplar처럼 판정
- 즉, report가 자기 근거와 live pair를 교차 검증하지 못했다.

### 1.4 spec / harness blind spot

- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
  - opening strict window와 `no-cider`에는 강하지만
  - `opening macro battlefield residence cap`은 없다.
- `docs/blockguide/treatment-production-harness-v2.md`
  - `location` 반복 금지와 장소 다양화는 강하지만
  - micro-location 다변화와 macro-battlefield progression을 분리해서 강제하지 않는다.

결론:

- pair 02만 고쳐도 같은 종류의 false pass가 다른 pair에서 재발할 수 있다.
- 따라서 **전량 재감리 + 법 패치**가 먼저다.

---

## 2. 전량 처리 범위

전량 처리 대상은 현재 operator registry에 있는 benchmark-fresh live inventory 전체로 잡는다.

기준 문서:

- `material_ssot/00_governance/production-pair-operational-registry-v1.md`
- `docs/2026-04-07/01_10_canonical_pair_manifest.md`

### 2.1 우선 전량 재감리 대상

- `01` `투자물_골든_카나리아 테스트_canonical_v1`
- `02` `chaebol_allowance_zero`
- `03` `chaebol_ent_empire`
- `04` `defense_defect_engineer`
- `07` `office_checkup_next_day`
- `08` `pantech_cyworld_reborn`
- `09` `wuxia_heavenly_physician`
- `jangyeongshil_industrial_revolution`
- `manual_meridian_archivist`

### 2.2 직접 수정 우선순위 후보

- 1순위: `chaebol_allowance_zero` alias / registry demotion + negative exemplar archive
- 2순위: opening pacing re-audit에서 `macro battlefield overstay`가 잡히는 pair
- 3순위: benchmark report가 WG threshold를 인용하면서 실제 블록 번호 검증을 누락한 pair

### 2.3 이번 wave에서 직접 수정하지 않는 것

- fresh pitch / canon promotion lane
- Stage 0 preprocess authority bundle
- system-track runtime / DB / app code

---

## 3. 원인 분류

이번 wave는 모든 findings를 아래 4 bucket으로만 분류한다.

### Bucket A. pair actual pacing failure

정의:

- opening macro battlefield에 과도하게 체류
- public scale-up / 대표 장면 / 간판 폭발 / battlefield shift가 늦음
- 독자가 `돈은 벌고 있는데 판이 안 커진다`로 읽는 경우

처리:

- pair repair lane
- 단, `pair 02`는 이번 wave에서 repair-first가 아니라 archive-first로 처리한다.

### Bucket B. benchmark report false pass

정의:

- WG / BI / TR anchor를 인용했지만 절대 블록 번호로 교차 검증하지 못함
- strict window 판정과 report conclusion이 실제 live pair와 어긋남

처리:

- report invalidate
- alias 보류 또는 철회
- fresh re-benchmark mandatory

### Bucket C. benchmark spec blind spot

정의:

- current spec으로는 `cider`와 token은 많은데 opening pacing은 느린 pair가 통과 가능

처리:

- benchmark spec patch

### Bucket D. production harness blind spot

정의:

- micro-location diversification은 통과하지만 macro-battlefield progression은 느린 draft가 통과 가능

처리:

- production harness patch
- 10-block self-audit axis 강화

---

## 4. 즉시 동결 규칙

전량 처리 시작과 동시에 아래를 적용한다.

### 4.1 alias freeze

- `GREENPLUS_chaebol_allowance_zero.md`는 즉시 withdrawn historical snapshot으로 간주한다.
- 본 pair를 opening exemplar, first-block conversion exemplar, authority-ticket exemplar로 인용 금지.
- 본 pair는 `negative exemplar / false-pass archive`로만 인용 가능하다.

### 4.2 shelf freeze

- current positive alias 전체를 삭제하지는 않는다.
- 다만 `opening pacing clean`이라는 의미로는 아무 pair도 새로 인용하지 않는다.
- 전량 re-audit이 끝나기 전에는 `benchmark-fresh`를 곧바로 `opening pacing trustworthy`로 읽지 않는다.

### 4.3 promotion freeze

- benchmark alias refresh
- exemplar 추가
- family baseline citation

위 3개는 opening pacing re-audit closeout 전까지 동결한다.

---

## 5. 법 패치 workstream

### 5.1 benchmark spec patch

대상:

- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`

추가해야 할 규칙:

1. `opening macro battlefield residence cap`
   - opening promise의 main battlefield가 `B2~B8` 이상 같은 축에 머물면 자동 경고
   - `B2~B6` 안에 first expansion proof 또는 next battlefield ticket가 없으면 cap 발동
2. `WG threshold reconciliation`
   - report가 WG의 `1화`, `3화`, `ARC 종료` 표현을 인용하면
   - 반드시 absolute block numbers로 환산표를 적는다
   - 환산 불가 또는 live pair 불일치면 PASS 불가
3. `micro-location != macro-battlefield`
   - 배식 라인 / 주차관제실 / 세탁실 / 청소팀 대기실이 달라도
   - 모두 같은 opening battlefield(`장례식장 운영축`)일 수 있음을 명시
4. `signboard explosion gate`
   - `간판 폭발`, `첫 월 반복매출`, `형의 눈빛 전환`, `공식 대표/입장권` 계열은
   - opening conversion grade에서 same-window 또는 declared WG threshold 충족 여부를 별도 체크
5. `false-pass self-check`
   - WG threshold를 인용했는가
   - 그 threshold가 실제 TR block numbers와 맞는가
   - 보고서 conclusion이 그 mismatch를 무시하지 않았는가

### 5.2 external-model benchmark harness patch

대상:

- `material_ssot/00_governance/external-model-benchmark-operation-harness-v1.md`

추가해야 할 규칙:

1. `gate 6 is anchored in BI + TR 1~3 only`를 유지하되
2. `WG threshold quoted -> absolute block verification required`를 새 hard law로 추가
3. `opening macro battlefield map`을 pair sequence 필수 step에 추가
4. `report says GREEN/GREENPLUS while WG threshold is visibly late`면 return-to-sender

### 5.3 production harness patch

대상:

- `docs/blockguide/treatment-production-harness-v2.md`

추가해야 할 규칙:

1. `opening battlefield map` 필수
2. `macro-battlefield shift` 필수
3. `10블록 자체 감리` 6축에 opening pacing 축 추가
4. `location 다양화`와 `battlefield progression`을 별도 점검
5. opening zone에서 `public scale-up / signboard event / representative recognition / next-stage ticket`가 너무 늦으면 FAIL

---

## 6. 전량 재감리 workstream

### 6.1 pair별 필수 산출물

`pair 02`를 제외한 active inventory 대상 pair에 대해 아래 1장짜리 bounded audit를 만든다.

`pair 02`는 별도 triage/archive 문서가 이미 존재하므로, Phase 3에서는 추가 repair-first audit로 중복 처리하지 않는다.

필수 섹션:

1. pair identity
2. opening macro battlefield map (`B1~B12`)
3. WG threshold map (`1화`, `3화`, `ARC 종료`)
4. actual trigger block numbers
5. benchmark report consistency check
6. verdict

### 6.2 verdict 종류

- `keep`
  - current alias 유지 가능
- `keep but report rewrite`
  - live pair는 통과 가능하나 benchmark report가 잘못 씀
- `downgrade`
  - current alias 유지 불가
- `repair first`
  - live pair를 먼저 고쳐야 함
- `archive_negative_exemplar`
  - false-pass memory로 보존하고, 이번 wave에서는 repair target으로 올리지 않는다

### 6.3 pair 02 archive point

- `장례식장 운영축`이 opening main battlefield로 몇 블록 지속되는가
- `첫 월 반복매출`이 실제 몇 블록에서 체감되는가
- `형의 눈빛 전환`이 실제 몇 블록에서 발생하는가
- `호텔 BOH 진입`이 token인지 real battlefield shift인지
- WG의 `3화 내 간판 폭발`과 실제 TR이 합치하는가
- 이 5개는 repair 스펙이 아니라 `negative exemplar caption`으로 보관한다.

### 6.4 전량 audit 순서

1. `07` `office_checkup_next_day`
2. `08` `pantech_cyworld_reborn`
3. `03` `chaebol_ent_empire`
4. `04` `defense_defect_engineer`
5. `01` `투자물_골든_카나리아 테스트_canonical_v1`
6. `09` `wuxia_heavenly_physician`
7. `jangyeongshil_industrial_revolution`
8. `manual_meridian_archivist`

이 순서는 `current exemplar shelf -> adjacent modern business lanes -> cross-family control sample -> current GREEN shelf` 순서다.

---

## 7. pair repair / archive workstream

### 7.1 기본 원칙

- `docs/narrative-router/material-revival-ladder-harness.md`를 따른다.
- 기본값은 `lite audit -> top 3 repair -> recheck`다.
- full-wave surgery는 pair별로 별도 승인 없이는 금지한다.
- 단, `pair 02`는 이 기본 원칙의 예외로 archive-first다.

### 7.2 pair 02 archive ruling

현재 ruling:

1. `pair 02`는 이번 wave에서 repair candidate가 아니다.
2. historical `GREENPLUS` snapshot을 withdrawn 처리하고 `negative exemplar / false-pass archive`로 남긴다.
3. future revival이 필요하면 별도 operator order에서 새 repair lane을 여는 방식으로만 다룬다.
4. 이번 wave에서는 pair 02를 통해 `무엇이 false pass였는가`를 고정하는 것이 목적이다.

중요:

- pair 02를 자동 repair lane으로 되돌리지 않는다.
- 법이 바뀌고 나서도 revival 여부는 별도 승인 없이는 열지 않는다.

---

## 8. closeout workstream

### 8.1 문서 closeout

재감리 및 archive / repair 종료 후 아래를 갱신한다.

- `material_ssot/00_governance/production_pair_grade_aliases/*.md`
- `material_ssot/00_governance/production-pair-operational-registry-v1.md`
- `docs/2026-04-08/production-pair-benchmark-freshness-wave.md` 또는 후속 closeout 문서

### 8.2 exemplar closeout

아래 둘은 분리해서 다시 고른다.

1. `first-block conversion exemplar`
2. `opening pacing clean exemplar`

이번 사건 이후에는 둘을 같은 shelf로 자동 취급하지 않는다.

### 8.3 금지

- pair 02를 무수정 상태로 exemplar 복귀
- spec patch 없이 registry만 갱신
- pair report false pass를 놔둔 채 freshness만 current 유지
- pair 02를 별도 승인 없이 re-audit rescue candidate로 자동 복귀

---

## 9. 실행 순서

### Phase 1. containment

산출물:

- 본 문서
- `pair 02` withdrawn false-pass archive note

완료 기준:

- pair 02 exemplar 사용 중단
- pair 02 negative exemplar archive 고정

### Phase 2. law patch

산출물:

- benchmark spec patch
- benchmark operation harness patch
- blockguide production harness patch

완료 기준:

- opening macro battlefield / WG threshold reconciliation / signboard explosion gate가 문서에 모두 반영

### Phase 3. inventory re-audit

산출물:

- pair별 opening pacing bounded audit 8건

완료 기준:

- 각 pair가 `keep / keep but report rewrite / downgrade / repair first` 중 하나로 분류됨

### Phase 4. bounded repairs

산출물:

- repair note
- 필요한 경우 TR/BI bounded patch

완료 기준:

- downgrade / repair-first pair만 최소 수정 후 재검증 통과

### Phase 5. re-benchmark and republish

산출물:

- fresh benchmark reports
- alias refresh
- registry refresh

완료 기준:

- current positive shelf가 opening pacing 기준까지 포함한 상태로 재발행

---

## 10. 추천 첫 실행 단위

가장 먼저 할 것은 아래 3건이다.

1. `pair 02 false-pass triage` 문서 작성
2. `production-pair-benchmark-spec-v1.md` opening pacing patch
3. `treatment-production-harness-v2.md` opening macro-battlefield patch

이 3건이 끝나야 전량 re-audit이 의미가 생긴다.

---

## 11. 3-Pass Audit Note

Pass 1:

- 현재 pair 02 live TR, WG, benchmark report, freshness registry를 직접 대조해 문제를 분리했다.

Pass 2:

- 다른 active pairs의 opening location distribution을 함께 읽어 이번 사건이 pair-local인지 law-level blind spot인지 비교했다.

Pass 3:

- 실행 순서를 `containment -> law patch -> inventory re-audit -> bounded repair -> republish`로 단순화해 실제 operator order로 바로 옮길 수 있게 정리했다.

Confidence:

- 0.96
