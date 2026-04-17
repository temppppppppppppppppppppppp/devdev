# Golden Canary Deepclone Probe A Bootstrap

Date: 2026-04-17
Status: active
Scope: `golden_canary_deepclone_probe_a` upstream-only deep-cloning probe bootstrap
Source Anchors:
- `C:\Users\wjjo\Desktop\글도비\treatments\phase0\투자물_골든_카나리아 테스트_canonical_v1_phase0_design.json`
- `C:\Users\wjjo\Desktop\글도비\treatments\01_tr_투자물_골든_카나리아 테스트_canonical_v1.json`
- `C:\Users\wjjo\Desktop\글도비\bible\01_bi_투자물_골든_카나리아 테스트_canonical_v1.json`
- `C:\Users\wjjo\Desktop\글도비\work_guards\01_투자물_골든_카나리아 테스트_canonical_v1.yaml`
- `C:\Users\wjjo\Desktop\글도비\narrative_ssot\50_projects\golden_canary_deepclone_probe_a\10_reference_selection\reference_selection.json`
- `C:\Users\wjjo\Desktop\글도비\treatments\preprocess\golden_canary_deepclone_probe_a\material_bundle_summary.json`
- `C:\Users\wjjo\Desktop\재료 생산 R&D 랩\docs\2026-04-17\bulhaeng-chaebol-ep0052-0101-session-context.md`
- `C:\Users\wjjo\Desktop\재료 생산 R&D 랩\artifacts\2026-04-17\bulhaeng-chaebol-ep0101-close-reading-ledger.json`

## 1. 목적

이 probe는 `투자물_골든_카나리아 테스트_canonical_v1` 정본을 건드리지 않고, deep-cloning donor doctrine을 `upstream only`로 실험하기 위한 복제 실험판이다.

이번 bootstrap의 목적은 세 가지다.

- baseline과 분리된 새 `work_id`를 만든다
- deep-cloning doctrine을 반영한 `reference_selection -> Stage0 preprocess` 경로를 잠근다
- canonical Phase0/TR/BI/work_guard를 새 probe 경로로 seed copy해 비교 출발점을 만든다

이 문서는 `Fork A`만 다룬다. `Stage3 lane packet` 실험은 아직 포함하지 않는다.

## 2. 생성된 probe 자산

### 2.1 work_id / scaffold

- `work_id`: `golden_canary_deepclone_probe_a`
- project scaffold:
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/`

### 2.2 upstream probe 자산

- intake:
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/00_intake/intake_meta.json`
- deepclone-aware reference selection:
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/10_reference_selection/reference_selection.json`
- contamination guard:
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/10_reference_selection/contamination_guard.json`
- generated Stage0 preprocess:
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/20_preprocess/source_manifest.json`
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/20_preprocess/profile_lock.json`
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/20_preprocess/material_bundle_summary.json`
  - `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/20_preprocess/phase0_ready_snapshot.json`
- shared preprocess mirror:
  - `treatments/preprocess/golden_canary_deepclone_probe_a/`

### 2.3 seed pair mirror

- phase0 seed:
  - `treatments/phase0/golden_canary_deepclone_probe_a_phase0_design.json`
- TR seed:
  - `treatments/golden_canary_deepclone_probe_a_tr_block_070_draft.json`
- BI seed:
  - `bible/0_bi_golden_canary_deepclone_probe_a.json`
- work_guard seed:
  - `work_guards/golden_canary_deepclone_probe_a.yaml`

project scaffold 내부에도 seed pair를 mirror해 두었다.

- `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/30_planning/phase0_design.json`
- `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/40_production/tr_block_070_draft.json`
- `narrative_ssot/50_projects/golden_canary_deepclone_probe_a/50_bi/0_bi_golden_canary_deepclone_probe_a.json`

## 3. 이번 probe에서 바꾼 것

이번 `Fork A`는 `upstream-only` probe이므로, canonical pair의 서사 본문을 아직 donor doctrine 방향으로 직접 재작성하지 않았다.

실제로 바꾼 것은 아래다.

- `reference_selection`에 probe용 work identity와 contamination rule을 고정했다
- opening bundle contract를 `proof/receipt/named-seat` 체인 중심으로 재서술했다
- Stage0 preprocess를 새 probe selection에서 다시 생성했다
- canonical pair를 새 `work_id` 경로로 복제해 baseline 비교용 seed로 고정했다

즉 현재 상태는 `baseline mirror + upstream doctrine rewrite`다.

## 4. deep-cloning 반영 방식

이번 probe는 donor 장면을 복사하지 않는다. 반영 단위는 구조 doctrine이다.

주요 반영 축은 아래다.

- scene pressure를 opening entry pressure로 읽는다
- proof scene과 receipt timing을 opening bundle contract 중심으로 앞당겨 읽는다
- observer tier 이동을 `PB tone shift -> named seat -> next ticket` 체인으로 읽는다
- bridge/payoff rhythm을 `TR 2~6` opening 설계 기준으로 압축한다

직접 donor-specific 요소는 금지한다.

- donor 인물명, 조직명, 검은 기운 gimmick, 재벌가 정치 구도
- donor의 특정 불법 금융/수급 조작 디테일
- donor 사건을 거의 그대로 대응시키는 scene copy

## 5. 현재 판정

현재 probe는 `Stage0 manual audit PASS`까지 닫혔다.

현재 상태:

- Stage0 preprocess artifact 4종 존재
- `phase0_ready_snapshot.manual_audit_pass == true`
- seed phase0/TR/BI/work_guard 존재
- `work_guard`: `WG-V1 PASS`
- copied Phase0/TR/BI: UTF-8 JSON parse OK

참고:

- 자세한 verdict는 `golden-canary-deepclone-probe-a-stage0-manual-audit.md`에 잠갔다

## 6. baseline 비교 기준

baseline은 아래 canonical pair다.

- `treatments/phase0/투자물_골든_카나리아 테스트_canonical_v1_phase0_design.json`
- `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json`
- `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json`
- `work_guards/01_투자물_골든_카나리아 테스트_canonical_v1.yaml`

1차 비교는 opening `TR 2~6`에 둔다.

비교 질문은 다섯 가지다.

- thesis -> proof -> receipt 체인이 더 선명해졌는가
- PB tone shift와 named-seat 전환이 더 빨리 visible해졌는가
- signboard / next-ticket 판정이 덜 애매해졌는가
- 자산 증가가 observer / authority 이동으로 더 잘 환전되는가
- donor smell만 짙어지고 canonical 고유성은 죽지 않았는가

## 7. 다음 스텝

1. canonical pair와 probe pair의 opening `TR 2~6` 차이를 정적 비교한다
2. upstream-only probe가 의미 있으면 그다음 `Fork B`에서 `Stage3 lane packet` 실험으로 확장한다
3. compare 결과가 빈약하면 upstream doctrine packet을 다시 줄이거나 재정렬한다

한 줄 결론:

`golden_canary_deepclone_probe_a`는 지금 기준으로 "정본을 건드리지 않은 upstream-only deep-cloning probe" 부트스트랩과 Stage0 manual audit까지 끝났고, 다음 의사결정 포인트는 opening 2~6 static compare다.
