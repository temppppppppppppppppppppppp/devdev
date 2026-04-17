# Golden Canary Deepclone Probe A Opus Opening TR Launch Order

Date: 2026-04-17
Status: final
Scope: `golden_canary_deepclone_probe_a` opening `TR 2~6` bounded rewrite launch order for an external model
Mode: `repair mode`
Envelope: `tr_continue`
Recommended Model: `Opus`

## Operator Verdict

지금은 `canary`를 여러 개 돌릴 때가 아니다.

지금 가장 효율적인 외부 모델 사용법은 아래 하나뿐이다.

- `Opus`
- `repair mode`
- `golden_canary_deepclone_probe_a`
- `opening TR 2~6 bounded rewrite only`
- `write scope = current live TR file only`

즉 지금은 `benchmark`가 아니라 `Probe A opening rewrite`를 외부 모델에 좁게 맡기는 단계다.

## Why This Is The Right External Task

현재 `Probe A`는 아래 upstream 준비가 끝났다.

- donor doctrine packet 작성 완료
- `Phase0` rewrite 완료
- `work_guard` rewrite 완료

반면 live `TR`의 opening body는 아직 baseline 흔적이 강하다.

직접 확인한 현재 상태는 이렇다.

- `Block 2~5 reward`가 baseline canonical과 사실상 동일하다
- opening `proof -> private receipt -> named seat -> next ticket` 체인이 아직 Probe A doctrine만큼 선명하지 않다
- 따라서 지금 외부 모델이 가장 잘할 일은 `TR 2~6`의 opening chain만 좁게 다시 쓰는 것이다

이 작업은 `runtime canary`보다 싸고, 결과 해석도 쉽다.

## Terminal Guidance

- 기본 권장: `1 terminal = 1 target`
- 이번 작업의 권장 폭:
  - `Terminal A`: `Opus` bounded rewrite
  - `Terminal B`: 로컬 static compare / audit 대기
  - 나머지 터미널: 비워두거나 다른 실험 금지

지금 단계에서는 `Probe A canary`, `baseline canary`, `Probe B 착수`를 동시에 열지 않는다.

## Exact Read Stack

외부 모델에는 아래 순서로 읽게 한다.

1. [docs/blockguide/delegation-bootstrap.md](C:\Users\wjjo\Desktop\글도비\docs\blockguide\delegation-bootstrap.md:1)
2. [material_ssot/00_governance/delegation-envelope-spec-v1.md](C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\delegation-envelope-spec-v1.md:1)
3. [docs/blockguide/treatment-production-harness-v2.md](C:\Users\wjjo\Desktop\글도비\docs\blockguide\treatment-production-harness-v2.md:1)
4. [docs/2026-04-17/golden-canary-deepclone-process-direction-adversarial-3pass-audit.md](C:\Users\wjjo\Desktop\글도비\docs\2026-04-17\golden-canary-deepclone-process-direction-adversarial-3pass-audit.md:1)
5. [docs/2026-04-17/golden-canary-deepclone-donor-doctrine-packet-context.md](C:\Users\wjjo\Desktop\글도비\docs\2026-04-17\golden-canary-deepclone-donor-doctrine-packet-context.md:1)
6. [treatments/preprocess/golden_canary_deepclone_probe_a/deepclone_donor_doctrine_packet.json](C:\Users\wjjo\Desktop\글도비\treatments\preprocess\golden_canary_deepclone_probe_a\deepclone_donor_doctrine_packet.json:1)
7. [treatments/phase0/golden_canary_deepclone_probe_a_phase0_design.json](C:\Users\wjjo\Desktop\글도비\treatments\phase0\golden_canary_deepclone_probe_a_phase0_design.json:1)
8. [work_guards/golden_canary_deepclone_probe_a.yaml](C:\Users\wjjo\Desktop\글도비\work_guards\golden_canary_deepclone_probe_a.yaml:1)
9. [treatments/golden_canary_deepclone_probe_a_tr_block_070_draft.json](C:\Users\wjjo\Desktop\글도비\treatments\golden_canary_deepclone_probe_a_tr_block_070_draft.json:1)

## Exact Write Scope

허용 write는 딱 하나다.

- [treatments/golden_canary_deepclone_probe_a_tr_block_070_draft.json](C:\Users\wjjo\Desktop\글도비\treatments\golden_canary_deepclone_probe_a_tr_block_070_draft.json:1)

금지:

- `Phase0` 수정
- `work_guard` 수정
- `BI` 수정
- `reference_selection` 수정
- 문서 파일 수정
- 새 파일 생성
- `Block 7+` continuation

## Mutation Boundary

이 오더는 `opening TR 2~6` rewrite다.

정확한 boundary:

- 주 mutation target: `Block 2`, `Block 3`, `Block 4`, `Block 5`, `Block 6`
- `Block 1`은 가급적 수정 금지
- `Block 7+`는 절대 수정 금지
- JSON schema, block count, block id, block number는 유지

즉 `same container, same boundary, stronger opening chain`이 목표다.

## Required Rewrite Goals

### Global Goal

`TR 2~6` 안에서 아래 체인을 더 또렷하게 만든다.

- thesis
- first execution
- public proof
- private receipt
- named seat / exception lane / priority response
- next ticket

돈을 버는 것만으로 닫지 말고, `구조 자산`이 opening 안에서 visible하게 잠겨야 한다.

### Block-Level Intent

`Block 2`

- 첫 execution을 더 강한 `entry pressure`로 시작
- `WTI thesis`가 바로 사건으로 보이게 유지
- reward는 단순 수익 전환을 넘어서 `PB tone shift + same-day VIP handling or priority line opening`이 더 선명해야 한다

`Block 3`

- 에콰도르 촉매와 partial exit는 유지
- reward는 `첫 수익 확정`만이 아니라 `exception account / rule-side seat`가 더 reader-facing해야 한다
- PB와 리스크팀이 관찰자에서 witness로 바뀌는 느낌이 살아야 한다

`Block 4`

- 금 포지션은 `워밍업 수익`보다 `이름 붙은 자리`나 `조직도 안 좌석`을 잠그는 장면이 더 명확해야 한다
- same-block receipt를 더 분명히 준다

`Block 5`

- 가족 테이블은 humiliation 소비보다 `structural signboard`로 써야 한다
- 형들이 `막내가 돈을 벌었대` 수준이 아니라 `무시하던 막내의 법인 라인이 이상하게 크다`는 구조 신호를 감지하는 쪽이 낫다
- 다음 전장 입장권의 문턱이 visible해야 한다

`Block 6`

- 조선/철강 매수는 유지 가능
- reward는 `국제 거래 라인의 이름표`와 `다음 bigger battlefield 입구`를 더 명시적으로 잠가야 한다
- `코스피 더 간다`류 군중 광기와 protagonist의 exit doctrine이 대조되어야 한다

## Non-Negotiable Constraints

- donor 사건, 인물명, 조직명 직접 복제 금지
- `검은 기운`, `한국 재벌 정치 실명 skin`, `무기명 채권 사건` 직접 차용 금지
- `public proof`만 있고 `private receipt` 없는 종료 금지
- `next ticket`만 띄우고 opening receipt를 비우는 공중부양 금지
- `수익 숫자`만 올리고 observer tone shift / seat / access 변화가 사라지는 패턴 금지
- `TR block = published episode 1개`처럼 얇게 쓰는 것 금지

## Output Contract

외부 모델의 목표는 평가 report가 아니다.

필수 결과:

- live `TR` 파일을 bounded rewrite한 최종본

선택 결과:

- 아주 짧은 operator note 3줄 이내
  - 어떤 블록을 건드렸는지
  - proof/receipt를 어떻게 당겼는지
  - contamination guard를 어떻게 지켰는지

금지 결과:

- benchmark grade
- pair score
- full canary recommendation
- BI 착수

## Copy-Paste Launch Prompt

```text
You are in repair mode, not benchmark mode.

Target work_id:
golden_canary_deepclone_probe_a

Exact envelope:
tr_continue

Exact task:
Rewrite only the opening TR bundle so that TR blocks 2~6 better reflect the already-rewritten donor doctrine packet, Phase0, and work_guard.

Exact read order:
1. docs/blockguide/delegation-bootstrap.md
2. material_ssot/00_governance/delegation-envelope-spec-v1.md
3. docs/blockguide/treatment-production-harness-v2.md
4. docs/2026-04-17/golden-canary-deepclone-process-direction-adversarial-3pass-audit.md
5. docs/2026-04-17/golden-canary-deepclone-donor-doctrine-packet-context.md
6. treatments/preprocess/golden_canary_deepclone_probe_a/deepclone_donor_doctrine_packet.json
7. treatments/phase0/golden_canary_deepclone_probe_a_phase0_design.json
8. work_guards/golden_canary_deepclone_probe_a.yaml
9. treatments/golden_canary_deepclone_probe_a_tr_block_070_draft.json

Exact write scope:
- treatments/golden_canary_deepclone_probe_a_tr_block_070_draft.json only

Exact mutation boundary:
- touch Block 2, Block 3, Block 4, Block 5, Block 6 only
- do not continue Block 7+
- do not rewrite BI, Phase0, work_guard, or docs
- preserve schema, block ids, block count, and overall container shape

Primary rewrite goal:
Make the opening chain clearer inside TR 2~6:
thesis -> first execution -> public proof -> private receipt -> named seat / exception lane / priority response -> next ticket

Important:
- do not settle for profit-only rewards
- make observer tone shift and private receipt reader-visible
- do not copy donor names, donor scenes, Korean real-politics skin, black-aura gimmicks, or bearer-bond style events
- do not turn TR block into a thin single-episode beat

Block intent:
- Block 2: stronger entry pressure, first execution, same-day PB tone shift and VIP/priority handling
- Block 3: partial exit plus exception-account / rule-side receipt and witness conversion
- Block 4: named seat / organization-side seat locking, not just another profit beat
- Block 5: family-table signboard as structural recognition, not humiliation-first noise
- Block 6: global desk nameplate and next battlefield ticket, with exit doctrine contrast

Return shape:
- write the updated TR file only
- optional short note in 3 lines max: touched blocks / proof-receipt tightening / contamination guard
```

## Operator Close

`Opus`에 던질 거면 지금은 이것만 던진다.

- `Probe A opening rewrite 1건`
- `TR 2~6 only`
- `single terminal`

그 다음 순서는 고정이다.

1. 로컬 static compare
2. `S2 late-risk audit`
3. 그 뒤에만 `baseline vs Probe A` bounded canary 검토
