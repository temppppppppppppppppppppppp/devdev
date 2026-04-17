# Golden Canary Deepclone Process Direction Adversarial 3-Pass Audit

Date: 2026-04-17
Status: final
Scope: `golden_canary_deepclone_probe_a` next-step direction freeze before any new canary wave
Source Anchors:
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-17\golden-canary-deepclone-probe-a-bootstrap.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-17\golden-canary-deepclone-probe-a-stage0-manual-audit.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-17\stage3-generator-genre-aware-surface-diversification-context.md`
- `C:\Users\wjjo\Desktop\글도비\narrative_ssot\50_projects\golden_canary_deepclone_probe_a\10_reference_selection\reference_selection.json`
- `C:\Users\wjjo\Desktop\재료 생산 R&D 랩\README.md`
- `C:\Users\wjjo\Desktop\재료 생산 R&D 랩\docs\2026-04-17\bulhaeng-chaebol-ep0052-0101-session-context.md`
- `C:\Users\wjjo\Desktop\재료 생산 R&D 랩\artifacts\2026-04-17\bulhaeng-chaebol-ep0101-close-reading-ledger.json`

## Executive Verdict

지금 가장 효율적인 방향은 `바로 canary를 여러 개 돌리는 것`이 아니다.

더 정확히는 아래 순서가 맞다.

1. deep-cloning doctrine을 `upstream packet`으로 먼저 고정한다
2. `Probe A`의 `Phase0 + work_guard + opening TR 2~6`를 실제로 다시 쓴다
3. 그 뒤 정적 비교를 먼저 한다
4. 정적 비교에서 유의미한 차이가 확인된 뒤에만 bounded canary로 간다
5. 그때도 처음에는 `baseline vs Probe A` 두 개만 병렬로 돌린다

이 순서가 맞는 이유는 현재 `Probe A`가 아직 `runtime에서 deep-cloning 효과를 검증할 상태`가 아니기 때문이다.

## Core Finding

현재 `Probe A`는 `Stage0 manual audit PASS`까지는 닫혔다. 그러나 narrative substance 기준으로는 아직 `upstream-only seed copy probe`에 가깝다.

실제 상태는 이렇다.

- `reference_selection`과 Stage0 preprocess는 probe doctrine 방향으로 다시 잠겼다
- 하지만 `Phase0 / TR / BI / work_guard`는 아직 비교용 seed copy 비중이 크다
- 현재 canonical 대비 probe pair diff는 거의 경로/식별자 수준에 가깝고, narrative opening compare나 runtime canary를 바로 돌릴 정도의 독립 변수는 아직 부족하다

직접 확인한 현재 diff 성격도 이 판단을 지지한다.

- `Phase0` 차이는 현재 `_work_id` 수준이 핵심이다
- `TR` 차이도 현재 `_work_id`, `_phase0_ref`, `_authority_chain` 같은 참조 경로 정리에 가깝다

즉 지금 `Probe A`는 `deep-cloning 효과가 narrative body에 실질 반영된 실험군`이라기보다, `그 실험을 담을 준비가 된 probe shell`에 더 가깝다

따라서 지금 canary를 여러 개 돌리면, `deep-cloning이 먹혔는지`가 아니라 `거의 같은 서사를 두 번 돌린 결과`만 얻게 될 가능성이 높다.

## Recommended Process

### Step 0. Owner Split Freeze

이번 실험은 owner를 섞지 않고 분리해서 봐야 한다.

- `deep-cloning` owner:
  - donor doctrine을 어떤 계약으로 바꿀지
- `upstream` owner:
  - `Phase0 / work_guard / opening TR`에 그 doctrine을 어떻게 실제 반영할지
- `S2` owner:
  - 이번 화 핵심과 proof/receipt/hook을 얼마나 빨리 packet으로 압축하는지
- `S3` owner:
  - 받은 packet으로 서로 다른 합법 후보를 실제로 만드는지

즉 이번 wave의 1차 질문은 `deep-cloning -> upstream`이 유효한가다.
아직 `deep-cloning -> Stage3 runtime`을 먼저 묻는 단계가 아니다.

### Step 1. Donor Doctrine Packet Freeze

`불행을 보는 재벌집 손자` actual-read 산출물에서 raw donor scene을 직접 베끼지 말고, 다음 필드만 slim doctrine packet으로 뽑는다.

- `entry_pressure`
- `episode_function`
- `proof_scene`
- `receipt_type`
- `hook_type`
- `bridge_vs_payoff`
- `observer / authority 이동 패턴`

이 packet의 역할은 `좋은 작품이 opening에서 무엇을 빨리 보여주는가`를 요약하는 것이다.

즉 이번 단계에서는 donor 사건을 복제하지 않고, 아래만 잠근다.

- proof가 얼마나 빨리 visible해야 하는가
- receipt가 어떤 종류여야 하는가
- authority or observer 이동이 어떻게 reader-facing이어야 하는가
- bridge와 payoff의 비율을 opening에서 어떻게 잡아야 하는가

### Step 2. Probe A Realization

그 다음에야 `Probe A`를 실제 비교 가능 상태로 만든다.

추천 realization 최소 단위는 아래다.

- `Phase0` 재작성
- `work_guard` 재작성
- `opening TR 2~6`만 bounded rewrite

지금 단계에서 `BI 전체 재작성`이나 `full run`은 비효율적이다.

이유:

- 실험 질문은 opening cadence다
- deep-cloning doctrine이 opening proof/receipt를 진짜 개선하는지만 먼저 보면 된다
- 후반부까지 다 손보면 독립 변수가 너무 많아진다

### Step 3. Static Compare First

다음 게이트는 runtime이 아니라 정적 비교다.

비교 범위는 `canonical vs Probe A opening TR 2~6`로 제한한다.

비교 질문은 아래 6개로 고정한다.

- thesis가 더 빨리 독자에게 visible한가
- proof가 더 빨리 발생하는가
- receipt가 더 reader-facing한가
- PB tone shift / named seat / signboard가 더 명확한가
- next-ticket이 덜 공중에 뜨는가
- donor smell만 짙어지고 카나리아 고유성은 죽지 않았는가

### Step 4. S2 Packet Audit Before Runtime

정적 비교가 좋아 보여도 바로 canary로 가지 않는다.

먼저 `S2 packet audit`를 끼운다.

봐야 할 것은 이거다.

- `must_focus`가 opening proof를 늦게 밀어내지 않는가
- `episode_details`가 이벤트를 두껍게 설명만 하고 늦게 소모하지 않는가
- `tactical_doc` 안에 mission truth가 prose로만 묻히지 않는가
- proof / receipt / hook이 각 화의 packet에서 앞쪽에 살아 있는가

즉 `deep-cloning이 upstream 설계는 좋아졌는데, S2에서 다시 늦어지는지`를 여기서 걸러야 한다.

### Step 5. First Runtime Gate

위 4단계까지 통과했을 때만 bounded canary로 간다.

처음 canary는 `여러 개`가 아니라 아래 두 개만 추천한다.

- `baseline`
- `Probe A`

동일한 bounded window, 동일한 조건으로 비교한다.

지금 단계에서 `Probe B`, `Stage3 lane packet`, `genre-aware surface diversification`, `S3 code patch`까지 같이 열면 owner가 섞여 버린다.

### Step 6. Probe B Only If Needed

`Probe A`가 정적 비교에서 좋아지고 runtime도 최소한 긍정 신호가 있으면, 그때 `Probe B`로 넘어간다.

`Probe B`의 질문은 그때부터다.

- deep-cloning doctrine이 `S3 lane packet`으로도 유효한가
- `action / emotion / dialogue` 3분기를 donor-inspired lane으로 바꾸면 실제로 더 좋아지는가

즉 `Probe B`는 2차 실험이지 1차 실험이 아니다.

## Why This Is More Efficient

이 순서가 효율적인 이유는 세 가지다.

### 1. 불필요한 canary 낭비를 막는다

현재 `Probe A`는 아직 runtime 비교에 적합한 narrative delta가 작다.

이 상태에서 canary를 여러 개 돌리면 실험비는 크고 해석력은 낮다.

### 2. owner를 섞지 않는다

한 번에 `upstream + S2 + S3`를 같이 흔들면, 나중에 좋아져도 왜 좋아졌는지 알 수 없다.

이번 wave는 `deep-cloning -> upstream`만 먼저 본다.

### 3. 실패해도 빨리 접을 수 있다

`opening TR 2~6 static compare`에서 별 신호가 없으면, 큰 runtime 실험 없이도 빨리 중지할 수 있다.

즉 `cheap gate -> expensive gate` 순서다.

## Parallel Canary Guidance

사용자가 병렬 canary를 돌릴 수 있는 환경을 이미 열어둔 것은 좋다. 다만 지금 당장은 쓰지 않는 편이 맞다.

추천 규칙:

- `지금`: canary 병렬 실행 비추천
- `Probe A opening rewrite + static compare + S2 packet audit` 이후:
  - `baseline 1개`
  - `Probe A 1개`
  이 2개만 병렬

초기부터 3개 이상 병렬 canary를 추천하지 않는 이유:

- 현재 실험 질문은 분기 수를 늘리는 것이 아니라, 독립 변수를 선명하게 유지하는 것이다
- baseline / Probe A 두 개만으로도 1차 결론은 충분하다

## Pass 1. Scope Attack

질문:
지금 정말 next step이 canary인가, 아니면 아직 너무 이른가?

반대 가설:
Stage0 PASS까지 닫혔으니 바로 runtime으로 가도 된다.

판단:
아니다.

이유:

- 현재 문서들 스스로도 `Probe A`를 아직 `upstream-only probe bootstrap`으로 정의한다
- `opening 2~6 static compare`가 다음 step으로 이미 잠겨 있다
- 실제 probe pair는 아직 narrative content보다 seed copy 성격이 강하다

Pass 1 verdict:
`지금 canary-first는 scope miss다.`

## Pass 2. Evidence Attack

질문:
혹시 지금도 canary를 돌리면 뭔가 의미 있는 signal이 나오지 않는가?

반대 가설:
runtime은 언제나 정적 비교보다 더 많은 것을 보여준다.

판단:
이번 건에서는 그렇지 않다.

이유:

- 현재 probe는 preprocess 쪽이 더 많이 바뀌었고, pair artifact narrative body는 아직 본격 rewrite 전이다
- 이 상태의 runtime은 `deep-cloning doctrine의 효과`보다 `기존 canonical seed의 재실행 결과`에 더 가깝게 해석될 위험이 크다
- 실험 질문과 비용이 안 맞는다

Pass 2 verdict:
`지금 runtime은 신호 대비 노이즈가 크다.`

## Pass 3. Sequence Attack

질문:
더 빠른 길이 있는가?

가능한 나쁜 지름길:

- 바로 canary 3개 이상 병렬 실행
- `Probe B`까지 먼저 열기
- `S3 lane packet` 코드를 먼저 고치기
- full BI/full run으로 바로 확대하기

왜 나쁜가:

- owner가 섞인다
- 실패해도 어디가 원인인지 모르게 된다
- 비교군 대비 비용만 커진다

더 좋은 지름길:

- `Probe A opening rewrite`
- `static compare`
- `S2 packet audit`
- 그 뒤 `baseline vs Probe A` 두 개만 병렬 canary

Pass 3 verdict:
`가장 빠른 길은 canary를 먼저 많이 돌리는 것이 아니라, upstream delta를 먼저 선명하게 만드는 것이다.`

## Final Recommendation

다음 오더는 아래 형태가 가장 맞다.

1. `deep-cloning donor doctrine packet 추출/정리`
2. `golden_canary_deepclone_probe_a Phase0 + work_guard + opening TR 2~6 bounded rewrite`
3. `canonical vs Probe A opening TR 2~6 static compare`
4. `S2 packet late-risk audit`
5. 필요 시 `baseline vs Probe A` bounded canary 2개 병렬

이번 턴 기준 추천하지 않는 것:

- 지금 바로 canary 여러 개 병렬
- `Probe B` 즉시 진입
- `S3` 코드 수정 먼저 시작
- full BI/full run 비교

한 줄 결론:

`지금은 canary wave가 아니라, Probe A를 실제 비교 가능한 opening delta 상태로 만든 뒤 정적 비교와 S2 packet 감리를 선행하는 것이 가장 효율적이다.`
