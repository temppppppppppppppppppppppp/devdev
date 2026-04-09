# 기존 실전 준비 BI/TR pair 신뢰 리셋 컨텍스트

Date: 2026-04-09
Status: active operator context
Scope: 현재 repo의 기존 live `BI/TR` pair를 어떻게 읽어야 하는지에 대한 신뢰 해석 문서
Audience: material-side operator, benchmark operator, pair citation operator

---

## 0. 한 줄 결론

현재 시점에서 **기존 실전 준비 `BI/TR` pair를 자동 신뢰하면 안 된다.**

더 정확히 말하면:

- `schema pass`는 shape 정합일 뿐이다.
- `benchmark-fresh`는 benchmark artifact 존재를 뜻할 뿐이다.
- `GREENPLUS/GREEN` alias는 pair마다 다시 읽어야 하며, 적어도 opening pacing과 block density 권위는 전수 재감리 전까지 조건부다.

이번 컨텍스트의 직접 원인은 `pair 02`의 false pass지만, 해석 변경 범위는 `pair 02` 하나로 끝나지 않는다.

---

## 1. 왜 신뢰를 리셋했는가

이번 리셋은 취향 문제가 아니라 **운영 권위 충돌** 때문이다.

핵심 트리거:

- `chaebol_allowance_zero`가 opening pacing 기준으로 false pass로 판정됐다.
- `work_guard`는 `1화 내 첫 사이다`, `3화 내 간판 폭발`을 말했는데 live `TR`은 `B09/B10`에 핵심 전환이 밀려 있었다.
- benchmark report는 그 threshold를 인용하면서도 `GREENPLUS`를 유지했다.
- production harness는 `location` 다양화는 잡았지만 `macro-battlefield overstay`는 잡지 못했다.

즉, 기존 `실전 준비됨` 판정에는 아래 4층이 섞여 있었다.

1. live pair 자체의 pacing 문제
2. benchmark report false pass
3. benchmark spec blind spot
4. production harness blind spot

이 4층이 분리되지 않은 상태에서 붙은 positive shelf는 지금 그대로 신뢰할 수 없다.

---

## 2. 현재 바뀐 법

현재 컨텍스트는 아래 법 패치를 이미 반영한 뒤의 상태다.

### 2.1 benchmark law

`material_ssot/00_governance/production-pair-benchmark-spec-v1.md`는 이제:

- `WG/canon timing -> absolute block reconciliation`을 요구한다.
- `micro-location != macro-battlefield`를 명시한다.
- opening main battlefield가 `B2~B8`을 먹고 핵심 signboard / representative beat가 `B9+`로 밀리면 cap을 건다.
- `TR block`을 published episode 1개가 아니라 `2~6화`로 펼쳐질 planning bundle로 읽게 한다.

### 2.2 production law

`docs/blockguide/treatment-production-harness-v2.md`는 이제:

- `TR block = episode` 오독을 금지한다.
- `TR block 1개 ~= downstream 2~6화 분량`을 기본 생산 감각으로 둔다.
- opening 10블록 감리에서 `macro_battlefield`, `signboard timing`, `episode-bundle density`를 같이 본다.

### 2.3 registry law

`material_ssot/00_governance/production-pair-operational-registry-v1.md`와 alias surfaces는 이제:

- `pending_refresh`를 단순 material touch뿐 아니라 `withdrawn false-pass historical snapshot`에도 쓸 수 있게 읽는다.
- `pair 02`를 `negative exemplar / false-pass archive`로 내렸다.
- `benchmark-fresh = opening pacing trustworthy`라는 자동 해석을 금지한다.

---

## 3. 지금 무엇을 신뢰하지 말아야 하나

현재 컨텍스트에서 접어야 하는 신뢰는 아래와 같다.

### 3.1 금지 해석

- `GREENPLUS니까 실전 opening clean하다`
- `benchmark-fresh니까 현재 baseline으로 바로 써도 된다`
- `schema pass니까 pair quality도 pass다`
- `location이 많이 바뀌었으니 opening이 빠르다`
- `TR block = episode 1개`라고 보고 얇은 beat를 여러 block으로 쪼개도 된다

### 3.2 특히 금지

- `pair 02`를 opening exemplar로 쓰기
- `pair 02`를 first-block conversion benchmark로 쓰기
- `pair 02`를 authority-ticket benchmark 보완 슬롯으로 쓰기
- `benchmark-fresh current`라는 말만 보고 pair를 family baseline으로 자동 인용하기

---

## 4. 지금 무엇까지는 조건부로 신뢰 가능한가

이번 신뢰 리셋은 "모든 pair가 다 무효"라는 뜻은 아니다.

다만 신뢰 단위를 잘라서 읽어야 한다.

### 4.1 여전히 읽을 수 있는 것

- `schema pass`
  - pair가 현재 normalization contract 상 형태 정합은 맞춘다는 뜻
- family/domain material
  - 업계축, power loop, reward vocabulary, world hooks 같은 재료 참고 가치
- 일부 pair의 local strength
  - 예: proof scene 정밀도, authority ticket 감각, domain truth density

### 4.2 아직 유보해야 하는 것

- opening pacing authority
- first-block conversion exemplar 권위
- `GREENPLUS` shelf 전반의 자동 신뢰
- `실전 준비됨`을 downstream episode pacing까지 포함하는 말로 읽는 것

정리하면:

- **부분 재료/shape/reference 가치**는 남아 있다.
- **운영 권위/실전 baseline 권위**는 현재 재감리 전까지 보수적으로 읽어야 한다.

---

## 5. 현재 pair별 운영 해석

### 5.1 `chaebol_allowance_zero`

현재 해석:

- `withdrawn false-pass historical snapshot`
- `negative exemplar / false-pass archive`
- baseline, exemplar, promotion-target support로 사용 금지

이 pair는 지금 "좋은 pair"로 쓰는 것이 아니라, "어떻게 false pass가 생겼는지"를 기억하는 용도로 보존한다.

### 5.2 나머지 current positive alias pair

현재 해석:

- 자동 폐기 대상은 아니다.
- 하지만 opening pacing / block density 권위는 **조건부**다.
- 전량 opening re-audit이 끝나기 전에는 `current family baseline` 인용을 더 보수적으로 해야 한다.

즉:

- `keep until disproven`이 아니라
- `usable with caution until re-audited`에 가깝다.

### 5.3 unslotted `GREEN` pair

현재 해석:

- 여전히 top-tier exemplar shelf는 아니다.
- numbered-slot pair보다 더 보수적으로 읽는다.
- 다만 이번 trust reset의 직접 false-pass 중심축은 아니다.

---

## 6. 운영자가 지금 따라야 할 해석 규칙

현재 시점의 간단 규칙은 아래다.

1. pair를 인용할 때는 먼저 registry의 `benchmark_freshness`, `operator use`, withdrawn note를 확인한다.
2. `GREENPLUS/GREEN` filename만 보고 positive shelf로 읽지 않는다.
3. opening 판단에서는 `macro_battlefield`, `absolute block timing`, `episode-bundle density`를 같이 본다.
4. `TR block`을 1화 단위로 읽지 않는다.
5. `benchmark-fresh`를 `실전 opening trustworthy`로 번역하지 않는다.
6. doubt가 생기면 pair를 칭찬 문장보다 bounded audit 대상으로 먼저 올린다.

---

## 7. 현재 컨텍스트의 실제 의미

이번 문서가 말하는 것은 "기존 BI/TR pair는 전부 못 쓴다"가 아니다.

실제 의미는 아래다.

- 기존 positive shelf를 **무비판적으로 신뢰하는 시대는 끝났다.**
- 현재 pair들은 `shape truth`, `material truth`, `operator authority truth`를 분리해서 읽어야 한다.
- 특히 opening pacing, first-block conversion, episode-bundle density는 재검증 전까지 보수적으로 본다.
- `pair 02`는 수리 대기 exemplar가 아니라 반면교사 아카이브로 남긴다.

---

## 8. 다음 행동

이 컨텍스트 문서 이후의 실무 동작은 아래 순서를 권장한다.

1. 기존 positive alias pair를 인용할 때마다 registry reading부터 확인
2. active inventory 8개 pair opening re-audit 진행
3. `keep / keep but report rewrite / downgrade / repair first / archive_negative_exemplar` 중 하나로 재분류
4. re-audit closeout 전까지는 `opening pacing clean exemplar`를 신규 확정하지 않음

---

## 9. Source Context

이 문서는 아래 현재 문맥을 합쳐 요약한다.

- `docs/2026-04-09/material-side-opening-pacing-false-pass-full-remediation-plan.md`
- `docs/2026-04-09/chaebol_allowance_zero_opening_pacing_false_pass_triage.md`
- `material_ssot/00_governance/production-pair-operational-registry-v1.md`
- `material_ssot/00_governance/pre-new-pitch-operational-readiness-v1.md`
- `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
- `docs/blockguide/treatment-production-harness-v2.md`

---

## 10. 3-Pass Audit Note

Pass 1:

- current registry, triage, remediation plan, readiness, benchmark law를 다시 묶어 신뢰 리셋의 직접 근거를 정리했다.

Pass 2:

- `완전 불신`과 `조건부 신뢰`를 분리해 운영자가 과잉 폐기나 과잉 신뢰 둘 다 하지 않게 정리했다.

Pass 3:

- 앞으로 컨텍스트 없이도 바로 읽히도록 `무엇을 믿지 말아야 하는가`, `무엇까지는 조건부로 믿을 수 있는가`, `지금의 행동 규칙`을 한 문서에 고정했다.

Confidence:

- 0.97
