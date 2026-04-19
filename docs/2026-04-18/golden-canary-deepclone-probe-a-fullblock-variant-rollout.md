# Golden Canary Deepclone Probe A Full-Block Variant Rollout

Date: 2026-04-18
Status: final
Scope: Freeze the operating decision for a `Probe-style doctrine rollout`, then bootstrap a new variant `work_id` by copying the current `golden_canary_deepclone_probe_a` pair and preprocess bundle before any blockwise rewrites.
Source Anchors:
- [static cause hypothesis](C:\Users\PC\Desktop\글도비\docs\2026-04-18\golden-canary-deepclone-probe-a-static-cause-hypothesis.md:1)
- [opening static compare](C:\Users\PC\Desktop\글도비\docs\2026-04-17\golden-canary-deepclone-probe-a-opening-static-compare.md:1)
- [Probe A source_manifest](C:\Users\PC\Desktop\글도비\treatments\preprocess\golden_canary_deepclone_probe_a\source_manifest.json:1)
- [Probe A work_guard](C:\Users\PC\Desktop\글도비\work_guards\golden_canary_deepclone_probe_a.yaml:1)

## Executive Decision

이번 오더의 공식 명칭은 `Probe-style doctrine rollout`로 고정한다.

- 새 variant `work_id`는 `golden_canary_deepclone_probe_a_fullblock_v1`로 둔다.
- authority seed는 현재 `golden_canary_deepclone_probe_a`의 `Phase0 + TR + BI + preprocess + work_guard` 전체다.
- 이번 턴의 1단위는 `full-block bootstrap copy`다.
- 이번 턴은 `전 블럭 rewrite 완료`가 아니라 `전 블럭 rollout용 seed variant 동결`까지만 한다.

## Why This Form

지금까지의 bounded evidence는 `Probe A`의 이득이 `좋은 훅 1개`가 아니라 `bundle effect`에 가깝다는 쪽을 지지한다.

- sharper material contract
- richer retrieval anchors
- safer bridge surface
- more persistent structural receipts

따라서 다음 단계는 기존 canonical을 바로 치환하는 것이 아니라, 현재 Probe A 번들을 seed로 삼아 `작품 단위 variant`를 분기하는 것이 가장 안전하다.

## Rollout Contract

### 1. Variant, Not Replacement

- `golden_canary_deepclone_probe_a_fullblock_v1`는 canonical replacement가 아니다.
- 이 variant는 `Probe A doctrine`을 전 블럭 범위로 확장할 수 있는지 검증하기 위한 material-side branch다.
- 기존 `golden_canary_deepclone_probe_a`는 opening-centered upstream probe로 남긴다.

### 2. Translate, Do Not Copy

- donor doctrine은 `pressure -> proof -> receipt -> next-hook cadence`만 번역한다.
- donor의 scene order, proper noun, organization, politics skin, black-aura gimmick, direct event copy는 금지한다.
- reward는 숫자 자랑보다 `seat / receipt / authority / access` 같은 구조 자산으로 번역한다.

### 3. Bootstrap Scope

이번 bootstrap copy는 아래 surface를 그대로 seed로 가져온다.

- `Phase0`
- `TR draft`
- `BI`
- `work_guard`
- `treatments/preprocess/<work_id>/` bundle

단, copy 후에는 metadata와 notes를 새 variant 기준으로 다시 고정한다.

### 4. Freeze Meaning

`freeze`의 의미는 아래와 같다.

- 새 `work_id`가 material-side SSOT에서 독립 식별자를 가진다.
- copied surfaces가 `opening-only probe`가 아니라 `full-block rollout seed`라는 뜻을 명시한다.
- 이후 blockwise rewrite는 이 seed 위에서만 진행한다.

## Immediate Execution Order

1. 현재 `golden_canary_deepclone_probe_a` pair를 새 `work_id`로 복제한다.
2. copied `Phase0`, `TR`, `BI`, `work_guard`, preprocess metadata의 `work_id`를 variant 기준으로 치환한다.
3. preprocess notes와 readiness snapshot에 `full-block rollout seed` 성격을 명시한다.
4. stale old-`work_id` reference가 새 variant 내부에 남지 않았는지 점검한다.

## Non-Goals

- 이번 턴에 TR 전 블럭을 다시 쓰지 않는다.
- 이번 턴에 BI 전면 재감리를 끝냈다고 선언하지 않는다.
- 이번 턴에 `Probe A`의 전면 채택 우위를 최종 확정하지 않는다.
- 이번 턴에 canonical pair를 덮어쓰지 않는다.

## Working Interpretation

이번 variant는 `딥클로닝 전면 적용본`이라기보다 아래 정의가 더 정확하다.

`현재 Probe A 번역 doctrine을 작품 전 블럭으로 확장하기 위한 bootstrap variant`

즉, 복사본의 목적은 백업이 아니라 `doctrine-carrying seed`를 만드는 것이다.

## Pass 1

- 요청한 작업 단위를 `문서화 후 variant bootstrap 진행`으로 축소해 고정했다.
- `full-block rollout`이 `full rewrite`와 다르다는 점을 명시했다.
- canonical replacement가 아니라 variant branch라는 점을 앞단에 배치했다.

## Pass 2

- source authority를 현재 Probe A pair와 preprocess/work_guard로 제한했다.
- donor contamination 금지선을 explicit하게 적었다.
- bootstrap scope와 non-goals를 분리해 과장 결론을 막았다.

## Pass 3

- 다음 실행 순서가 그대로 작업 checklist가 되도록 재정렬했다.
- variant naming, authority seed, freeze meaning을 바로 참조할 수 있게 압축했다.
- 문서만 읽어도 왜 copy가 필요한지와 어디까지가 이번 턴 범위인지 드러나게 다듬었다.

Confidence: 97/100
