# chaebol_allowance_zero opening pacing false-pass triage

Date: 2026-04-09
Status: ready as negative exemplar archive
Scope: pair `02` failure triage only
Target:
- `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- `bible/02_bi_chaebol_allowance_zero.json`
- `work_guards/02_chaebol_allowance_zero.yaml`
- `docs/2026-04-07/10pair_true_benchmark_terminal02_pair02_report.md`
- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
- `docs/blockguide/treatment-production-harness-v2.md`

---

## 0. 한 줄 판정

`chaebol_allowance_zero`는 현재 상태에서 **opening pacing 기준의 false pass**로 본다.

원인은 하나가 아니라 아래 4층이 겹친 결과다.

1. live pair opening pacing failure
2. benchmark report false pass
3. benchmark spec blind spot
4. production harness blind spot

이번 triage의 primary classification은 `handoff_false_pass`다.
secondary classification은 `production_density_failure`다.

---

## 1. 사실 확정

### 1.1 live TR opening 흐름

opening 핵심 블록:

- `B01`: 잘린 카드
- `B02`: 장례 밥차
- `B03`: 검은 리본 주차권
- `B04`: 꽃값은 현금이다
- `B05`: 빈소 셔틀
- `B06`: 조의금 영수증
- `B07`: 장례식장 세탁실
- `B08`: 밤새는 청소팀
- `B09`: 첫 월 반복매출
- `B10`: 도련님 대신 대표
- `B11`: 객실보다 린넨

핵심 관찰:

- `B02~B08`이 사실상 같은 opening macro battlefield인 `장례식장 운영축` 안에 머문다.
- `첫 월 반복매출`은 `B09`에서야 공식화된다.
- 형의 눈빛 전환과 `호텔 BOH 진입 자격자` 급 표면 보상은 `B10`에서 나온다.
- 진짜 호텔 현장 진입은 `B11`부터다.

즉:

- same-block cider는 많다.
- 하지만 opening battlefield progression과 signboard explosion timing은 늦다.

### 1.2 work_guard 기준

`work_guards/02_chaebol_allowance_zero.yaml`의 opening threshold:

- `1화 내 첫 사이다`
- `3화 내 간판 폭발 (장례 특수 끝 후 첫 월 반복매출 증명 -> 형의 눈빛 전환)`
- `각 ARC 완료 시 다음 운영 전장 입장권 체감형 보상`

핵심 관찰:

- `1화 내 첫 사이다`는 `B02`로 충족 가능하다.
- 하지만 `3화 내 간판 폭발`은 현재 live TR 기준으로 `B09/B10`에 걸쳐 있다.
- 따라서 WG threshold와 live TR 사이에 명백한 timing mismatch가 있다.

### 1.3 benchmark report 판정

`docs/2026-04-07/10pair_true_benchmark_terminal02_pair02_report.md`는:

- WG threshold를 evidence anchor로 인용한다.
- 동시에 strict window `#2/#3/#4/#5/#6`만으로 opening chain이 닫혔다고 본다.
- 결과를 `GREENPLUS`로 확정한다.

핵심 문제:

- 보고서는 `3화 내 간판 폭발`이라는 WG threshold를 적어 놓고
- 실제 `첫 월 반복매출 -> 형의 눈빛 전환`이 `B09/B10`인 사실을 판정에 반영하지 않았다.

이는 단순 취향 차이가 아니라 **근거 인용과 결론이 충돌하는 false pass**다.

### 1.4 spec / harness 구조 문제

`production-pair-benchmark-spec-v1.md`는:

- strict window `2~6`
- no-cider zero
- later reward cadence

에는 강하지만, 아래는 hard gate가 아니다.

- opening macro battlefield residence cap
- WG `1화/3화/ARC 종료` 언어의 absolute block reconciliation
- micro-location diversification과 macro-battlefield progression 구분

`treatment-production-harness-v2.md`도:

- `location` 반복 금지
- 장소 다양화

는 강하지만,

- `장례식장 배식 라인`
- `장례식장 주차관제실`
- `장례식장 지하 세탁실`
- `장례식장 청소팀 대기실`

처럼 micro-location만 바뀌고 macro battlefield가 그대로인 opening overstay는 직접 FAIL로 잡지 못한다.

---

## 2. triage classification

### 2.1 primary

`handoff_false_pass`

이유:

- benchmark report가 WG threshold를 인용하고도 live TR block timing mismatch를 잡지 못했다.
- positive alias가 report 논리 위에 올라가 operational shelf까지 갔다.

### 2.2 secondary

`production_density_failure`

이유:

- 각 블록의 영수증은 살아 있어도 opening pacing density가 떨어진다.
- 독자가 `돈의 길목은 잡는데 판이 안 커진다`로 읽을 opening zone이 길다.

### 2.3 contributing gaps

- `benchmark_spec_gap`
- `production_harness_gap`

이 둘은 현재 triage taxonomy의 정식 failure label은 아니지만, 원인 층으로는 분리해서 기록한다.

---

## 3. operator ruling

### 3.1 immediate ruling

- `pair 02`를 현재 상태 그대로 opening exemplar로 쓰지 않는다.
- `pair 02`를 `first-block conversion benchmark`로 인용하지 않는다.
- `pair 02`를 `authority-ticket benchmark` 보완 슬롯으로 인용하지 않는다.

### 3.2 alias reading

- 현재 `GREENPLUS` alias는 **withdrawn historical snapshot**으로 읽는다.
- 이 pair는 positive shelf가 아니라 `negative exemplar / false-pass archive`로 보관한다.
- 이 triage가 살아 있는 동안 `GREENPLUS = opening pacing clean`이라는 해석은 금지한다.

### 3.3 next admissible step

다음 단계는 아래 순서만 허용한다.

1. benchmark law patch
2. production harness patch
3. pair 02 alias / registry demotion and negative exemplar archive
4. active inventory opening pacing re-audit
5. pair 02는 본 wave에서 repair target으로 자동 복귀시키지 않는다

pair 02 live `TR/BI`를 rescue lane으로 바로 넣지 않는다. 이번 wave의 우선 목적은 `false pass memory`를 남기고, 같은 착오가 다른 pair에서 반복되지 않게 하는 것이다.

---

## 4. exact failure statement

이 pair의 문제를 가장 짧게 압축하면 이렇다.

`same-block cider는 살아 있지만, opening macro battlefield가 장례식장 축에 과체류하고, WG가 요구한 3화 내 간판 폭발은 live TR에서 B09/B10으로 밀렸는데도 benchmark가 GREENPLUS를 줬다.`

---

## 5. closure condition

이 triage가 닫히려면 아래 4개가 전부 필요하다.

1. benchmark spec에 opening pacing 법 반영
2. production harness에 opening macro-battlefield 법 반영
3. pair 02 historical `GREENPLUS` snapshot이 alias / registry에서 withdrawn 처리
4. pair 02가 negative exemplar / false-pass archive로 운영 surfaces에 고정

하나라도 빠지면 close 불가.

---

## 6. 3-Pass Audit Note

Pass 1:

- live TR `B1~B12`, WG threshold, benchmark report 핵심 결론을 직접 대조했다.

Pass 2:

- pair 문제와 report/spec/harness 문제를 서로 다른 층으로 분리했다.

Pass 3:

- operator가 바로 행동할 수 있도록 `primary label`, `withdrawn-historical ruling`, `closure condition`까지 한 문서에 고정했다.

Confidence:

- 0.97
