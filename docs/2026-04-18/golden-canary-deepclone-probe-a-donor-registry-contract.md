# Golden Canary Deepclone Probe A Donor Registry Contract

Date: 2026-04-18
Status: final
Scope: Define how `golden_canary_deepclone_probe_a_fullblock_v1` can accept multiple donors over time without letting donor-specific surfaces overwrite canonical loop law.
Source Anchors:
- [loop doctrine upgrade plan](C:\Users\PC\Desktop\글도비\docs\2026-04-18\golden-canary-deepclone-probe-a-loop-doctrine-upgrade-plan.md:1)
- [loop abstraction packet](C:\Users\PC\Desktop\글도비\treatments\preprocess\golden_canary_deepclone_probe_a_fullblock_v1\loop_abstraction_packet.json:1)
- [donor registry](C:\Users\PC\Desktop\글도비\treatments\preprocess\golden_canary_deepclone_probe_a_fullblock_v1\donor_registry.json:1)
- [Probe A donor packet](C:\Users\PC\Desktop\글도비\treatments\preprocess\golden_canary_deepclone_probe_a_fullblock_v1\deepclone_donor_doctrine_packet.json:1)

## Executive Decision

이 작품은 이제 `single-donor probe`가 아니라 `multi-donor upgradable system`으로 본다.

단, 전제는 분명하다.

- canonical law는 donor-free여야 한다.
- donor는 `증거`, `예시`, `red flag`, `mapping hint`를 주는 annex다.
- donor를 더 붙인다고 해서 canonical law가 자동으로 바뀌지 않는다.

그래서 이번 contract의 목적은 `donor를 많이 받는 법`이 아니라 `donor를 많이 받아도 안 무너지는 법`을 고정하는 것이다.

## Registry Role

[donor_registry.json](/c:/Users/PC/Desktop/글도비/treatments/preprocess/golden_canary_deepclone_probe_a_fullblock_v1/donor_registry.json:1)의 역할은 아래다.

- 현재 active donor set 기록
- 각 donor의 강점과 약점 기록
- donor별 허용 영향 범위와 금지 영향 범위 기록
- donor 온보딩 규칙 기록
- donor 승격/유지/퇴역 조건 기록

즉 registry는 donor를 쌓는 창고이면서 동시에 `law firewall` 역할을 한다.

## Canonical Precedence

우선순위는 아래로 고정한다.

1. `Phase0`
2. `work_guard`
3. `loop_abstraction_packet`
4. `donor_registry`
5. donor annex packets

핵심은 이거다.

- donor registry도 canonical law 위에 오지 못한다.
- registry는 donor를 정리하지만, 법을 만들지는 않는다.
- donor annex는 registry보다도 아래다.

## Donor Admission Rule

새 donor는 아래 순서로만 들어올 수 있다.

1. donor evidence bundle 확보
2. donor annex packet 작성
3. donor noun -> generalized slot 변환
4. strengths / limits / contamination risks 기록
5. registry에 `candidate` 또는 `active_support`로 등록
6. bounded canary 비교로 실제 효용 검증
7. 필요 시에만 canonical law 승격 검토

즉 `좋아 보이는 donor를 발견했다`만으로는 canonical law를 건드릴 수 없다.

## Allowed Influence

donor가 줄 수 있는 것은 아래다.

- mapping examples
- reward rotation hints
- hook variety hints
- contamination red flags
- benchmark hypotheses

즉 donor는 `법의 재료`는 줄 수 있지만 `법 자체`는 아니다.

## Blocked Influence

donor가 주면 안 되는 것은 아래다.

- donor proper noun의 canonical law 침투
- donor scene order의 direct import
- donor-specific receipt vocabulary의 pseudo-law화
- single-donor 기준 late-game 전체 law 확정
- runtime threshold의 무증거 재설정

## Current Registry Reading

현재 registry의 첫 active donor는 `probe_a_seed_001`이다.

이 donor는 강점이 분명하다.

- proof -> private receipt
- reward as right-to-act
- observer shift
- bridge-first next-gate cadence

하지만 한계도 분명하다.

- opening 쪽 evidence가 late-block evidence보다 강하다
- donor-flavored receipt가 너무 매력적이라 overfit 위험이 있다
- 아직 `master donor` 권위를 줄 수는 없다

즉 현재 registry는 `Probe A를 버리지도 않고, 절대화하지도 않는` 상태다.

## Upgrade Path

멀티-donor 업그레이드는 아래로 간다.

1. 새 donor annex packet 추가
2. registry 등록
3. generalized slot layer에서 충돌 정리
4. loop scorecard로 donor 성능 비교
5. 누적 증거가 충분할 때만 canonical law 조정

따라서 donor가 많아질수록 오히려 registry와 abstraction layer의 중요성이 더 커진다.

## Pass 1

- `다른 donor를 계속 붙여도 되나`라는 질문에 대한 운영 답을 contract 형태로 고정했다.
- donor 다수 수용과 canonical law 보존을 함께 잡았다.

## Pass 2

- registry의 역할을 `창고 + 방화벽`으로 분리해 설명했다.
- allowed influence와 blocked influence를 분명히 나눠 future drift를 막았다.

## Pass 3

- 이 문서만 읽어도 donor onboarding과 law promotion 순서가 바로 보이도록 다듬었다.
- Probe A를 계속 쓰되 절대화하지 않는 현재 스탠스를 명시적으로 닫았다.

Confidence: 97/100
