# 10pair True Benchmark Terminal 09 Pair 09 Report

Date: 2026-04-07
Status: active
Document Type: read-only true benchmark audit report
Canonical Path: `docs/2026-04-07/10pair_true_benchmark_terminal09_pair09_report.md`
Parent Order: `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
Prompt: `docs/2026-04-07/10pair_true_benchmark_terminal09_pair09_prompt.md`

## Pair Identity

- pair id: `09`
- slug: `wuxia_heavenly_physician`
- family: `wuxguide`
- BI: `bible/09_bi_wuxia_heavenly_physician.json`
- TR: `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` (`_total_blocks: 70`, `blocks` length 70)
- WG: `work_guards/09_wuxia_heavenly_physician.yaml`
- canonical resolution: `docs/2026-04-07/01_10_canonical_pair_manifest.md` row `09`
- subgenre: wuxia / 의무일체 침의

## Evidence Anchor Table

| Anchor | Source | Value (extracted, no raw full read) |
| --- | --- | --- |
| `one_line_truth` | WG | 무공 자질 없는 명문 무가 막내가 침술=무공의 의무일체를 개척해, 치료할 수 있는 손의 희소가치로 가문·무림·독역의 관문을 동시에 장악한다 |
| early promise | WG `evaluation_thresholds` | `3~6화 내 형 치료 성공 + 조건부 공인 의원 자격 획득`; 첫 치료 직후 호칭·접근권·보호 태도 변화 |
| `success_device` (semantic) | WG `protagonist_weapon` + `mandatory_scene_engines` | 진단→처방→시술→경과 4단계가 온전히 구동되며 활침 고유 인과 증명; 활침=살침 동일 기술 증명; 치료 성공 직후 평가 수정 찍힘 |
| `cider_point` (semantic, wuxguide doctrine) | WG `evaluation_thresholds` + `tracking_slots` | 호칭·자격·접근권·경계 수위 변화; 보호패; 경지 7단계 (침의→혈의→맥의→신의→의성→의신→천의); 독역 치료 독점 병목 |
| `CommercialCode` semantic equivalent | WG `business_axes` + `control_axes` | 가문 공인 의원 자격, 약방·서고 접근권, 의선 반열, 독역 치료 독점권, 가주 발언권 — wuxguide의 토큰 사다리 |
| `mandatory_scene_engines` | WG | (1) 진단→처방→시술→경과 4단계 치료 씬 (2) 활침=살침 이중 레이어 의술 비무 (3) 치료 성공 직후 호칭·자격·접근권·경계 수위 변화 |
| `evaluation_thresholds` | WG | 3~6화 내 형 치료 + 조건부 공인 의원 / 첫 치료 직후 호칭·접근권·보호 변화 / 큰 피해 직후 즉시 새 경지 돌파 또는 다음 카드 |
| `custom_rules` / `tracking_slots` | WG | 치료=자기이익 연결 의무 / 반격 예약 없는 손해 금지 / 독역 역전 법칙 보존 / 저평가→고평가 / 가문 권한 축출→공인→발언권 / 경지 7단계 / 독역 치료 독점 병목 |
| `forbidden_flattenings` (cap risk anchors) | WG | 회개물 스타트, 인정 구걸, 자기연민 호구, 한 줄 기적치료, 의술 비무를 일반 전투로 환원, 약재 추상화, 위기 빈손 무대응 |
| TR `block 2` reward (anchor) | TR | `조건부 공인 의원` 자격 + 가문 내 공식 침 자리 + 소풍의 보호 약속 + 혜란 200년 의무일체 조사 착수 |
| TR `block 3` reward (anchor) | TR | 마을 독역 환자 일시 완화 + `약방 조건부 접근권` + 매화 약재 파트너 확보 |
| TR `block 4` reward (anchor) | TR | `행동 감시 → 보고 수령` 격상 (가문 방어 공인 정찰) + 독역 핵심 메커니즘 관찰 |
| TR `block 5` reward (anchor) | TR | 의무일체 의식적 발현 첫 성공 + `의념 원리 manual` + 백무명 첫 접촉 + 어머니 inheritance clue |
| TR `block 6` reward (anchor) | TR | `서고 의서 접근권` 조건부 허가 + 의무일체 7단계 경지 체계 확인 + 천의 최종 경지 인지 |

## P0 Hard Gates

Scoring window: gates `1~5` use TR blocks `2~6` only (block 1 deliberately excluded by spec; block 7+ may only confirm linkage). Gate `6` is the only gate that legitimately reads TR blocks `1~3` against BI anchors. Spec source: `production-pair-benchmark-spec-v1.md` §4.1.

| Gate | Definition | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | `first-block visible cider` — TR `2~6` contain at least one visible reward readers can count or feel | PASS | TR `2` `조건부 공인 의원` 자격; TR `3` `약방 조건부 접근권` + 매화 약재 파트너; TR `4` `행동 감시 → 보고 수령` 격상; TR `5` 의념 원리 + 어머니 단서; TR `6` `서고 의서 접근권` + 7경지 지도 — 다중 visible reward, no later-payoff dependency |
| 2 | `protagonist-only proof` — TR `2~6` make `저건 쟤라서 가능했다` undeniable | PASS | TR `5`에서 백무명이 `네 어머니 닮은 자질`로 의무일체 자질 확정 — 200년 단절 + 의맥 보유자 한정; TR `6`에서 7단계 경지 체계가 의맥 전용임 확정; 활침을 통한 내공 발현은 200년 단절 기술 — 대체 불가 |
| 3 | `evaluation revision` — weighted observer reevaluates protagonist inside TR `2~6` | PASS | TR `2`: 가주 진천웅이 직접 `조건부 공인 의원` 자격 부여 (가문 최상위 평가 수정); TR `4`: 장로회 시선이 `행동 감시 → 보고 수령`으로 성격 변경; TR `6`: 가주가 한 발 더 나아가 서고 의서 접근권 허가 — 두 단계 누적, 동일 블록 내 receipt |
| 4 | `visible reward token` — TR `2~6` land at least one wuxguide token (rank / elder protection / manual access / treasure / realm step / reputation / inheritance clue) | PASS | rank: TR `2` 조건부 공인 의원; protection: TR `2` 소풍의 `형이 앞으로도 지켜줄게`; manual access: TR `5` 의념 원리, TR `6` 서고 의서 접근권; inheritance clue: TR `5` 어머니 의맥 시사, TR `6` 7경지 체계 + 천의 인지; reputation: TR `4` 가문 공인 정찰 임무 격상 — 토큰 5종이 TR `2~6` 안에 동시 점등 |
| 5 | `block 1 → block 2 gate linkage` — reward earned by TR `≤6` opens the next gate; TR `7+`는 confirmation 전용 | PASS | TR `6`의 의념 원리·서고 의서 접근권이 TR `7` `첫 비무 — 침으로 혈도를 봉쇄`에서 그대로 활용되어 장로진 표정 변화 + 진무강 `저것이 사술인가 의술인가` 흔들림으로 다음 평가축이 열린다. TR `7`은 backfill이 아닌 downstream confirmation으로만 인용 |
| 6 | `BI/TR early conversion alignment` — BI early promise, `cider_point`, `success_device`가 TR `1~3` 안에 가시적으로 살아 있음 | PASS | (a) BI `CoreIdentity.initial_goal` = `형의 끊어진 경맥을 살려 내고, 그 증명을 딛고 가문 공인 의원 자격과 진료 기반을 확보한다` → TR `1`에서 형 경맥 복원 + TR `2`에서 가주가 직접 조건부 공인 의원 자격 발급으로 동일 블록 변환 완료. (b) BI `CommercialCode.killing_points[0]` = `침이 곧 무공 — 전무후무한 전투 시스템` → TR `1`에서 침끝 푸른 기운으로 경맥을 잇는 의무일체 첫 발현으로 즉시 선언. (c) BI `CommercialCode.do_not_fake` `진단→처방→시술→경과` success_device → TR `1` (합곡·내관·극천 진단→침→경과)·TR `3` (마을 독역 환자 진단→약초+침→경과)에서 4단계 시퀀스 가동. (d) WG/BI cider_point semantic = `호칭·자격·접근권·경계 수위 변화` → TR `2` 자격, TR `3` 약방 접근권, TR `2` 진무강 경계 변화로 TR `1~3` 안에 한 번에 점등. **BI summary echo가 아니라 TR 초입을 sharpen하는 amplification으로 작동 — gate 6 통과** |

P0 verdict: **all six hard gates PASS**. RED 자동 회피, 그러나 grade는 후술 cap rule + cider scan에 의해 별도 결정.

## Full-Block Cider Scan

Scan basis: blockwise extraction of `title / content.{context,solution,reward} / stakes / power_shift / relationship_delta` only. Ledger applies wuxguide cider doctrine: same-block receipt = visible reward token, weighted reevaluation, protection, manual/treasure access, realm step, reputation shift, explicit next-card materially felt now. Pain / training / recovery / setup / explanation alone is `false`. Ambiguous evidence is downgraded.

- total TR blocks: `70`
- no-cider blocks: `3`
- exact no-cider block numbers: `13, 28, 29`
- longest no-cider drought: `2` (blocks `28 → 29` consecutive)
- isolated no-cider block: `13`

### Window Summary

- `1~10` opening establishment — strong cider cadence: block `1` 의무일체 첫 발현 + 형 경맥 복원, `2` 조건부 공인 의원, `3` 약방 접근권, `4` 정찰 임무 격상, `5` 의념 원리 + 어머니 단서, `6` 서고 의서 접근권 + 7경지 지도, `7` 첫 비무 승리, `8~10` 침의 완성 단계 누적. all blocks in window pass.
- `11~20` 혈의 단계 + 약침 탄생 — 대부분 강한 cider; **block `13`은 아버지 2차 치료 실패 + 약침 결합법 `착상`에 그쳐 same-block receipt가 관념적 next-card 약속 수준 (`아직 실험 단계에도 이르지 못한 착상일 뿐`)** → strict 판정 `false`. block `16` 약침 완성·혈의 완성·큰형이 처음 고개 숙임 등 강한 회복.
- `21~30` 신의 단계 + 첫 거대 좌절 — block `28` 경맥 3개 손상·내공 25→15갑자·정확도 88→78·2개월 활동 금지로 same-block receipt 없음(서역행 동기 = later promise) → `false`; block `29` 분업 체계·매화 성장은 workaround setup-only로 `false`. **2-block drought `28~29`가 본 페어의 최장 무수확 구간**. 단, 손상 → 다음 windows로 자력 회복 예약은 살아 있음.
- `31~40` 천축 수련 + 살침 맹아 — block `32` 비경 80% 회복 + 자가 경맥 정비 manual 획득 + 동서 융합 체계 기반(realm 회복 + manual access)으로 cider 회복; block `39`는 2주 침체 안에서 5세 아이 침술 재성공 + 살침 doctrine seed로 same-block receipt 확보. 윈도 전반 회복세.
- `41~50` 의성 단계 + 인적 손실 — block `42` 살침 첫 실전 + 사마련 도주 + `의성 입문` realm step (강); block `45` 큰형 전사 + 백무명 영구 퇴장의 큰 피해와 동시에 `의무일체 200년 기억 단편` manual 전수로 동일 블록 receipt 성립; block `49`는 가주의 직접 고백·5년 냉대 해소·`의성 완성` flag로 weighted reevaluation receipt 성립 (cider true). 윈도 통과.
- `51~60` 의신 단계 + 칠성침법 빌드업 — 회복·정리·다음 카드 누적이 블록마다 receipt를 동반. 윈도 통과.
- `61~70` 천의 개안 + 클라이맥스 — block `65` 정(情)의 침 발현 + 3경맥 재생 + 7침 조건 해독 + `천의 개안 직전`; block `69` 칠성침법 7침 완성 + 천의무쌍 + 적 치료로 무림 대전 종결. 모두 동일 블록 receipt를 안고 결말까지 cider 라인 보존.

## Active Cap Rules

Spec source: `production-pair-benchmark-spec-v1.md` §6.

| Cap Rule | Status | Anchor |
| --- | --- | --- |
| `any no-cider block in the full-block cider scan: YELLOW ceiling` | **ACTIVE** | blocks `13, 28, 29` (3건) |
| `rewardless pain blocks 2 in a row: GREEN ceiling` | inactive | block `28`은 pain-only지만 block `29`는 본문에서 분업 체계 + 매화 성장 `workaround setup-only`로 분류 — `rewardless pain` 2연속이 아니라 `pain → workaround setup` 조합이므로 본 캡 미점등 |
| `major defeat without next card in the same or next block: YELLOW ceiling` | **ACTIVE** | block `28` 경맥 3개 손상 + 내공 25→15갑자라는 major defeat의 다음 카드(라지브 소개·천축행)는 block `30` 이후로 밀림 — `same or next block` 요건 미충족 |
| `no visible cider inside block 1: YELLOW ceiling` | inactive | TR `1`은 형 경맥 복원 + 의무일체 첫 발현 + 백무명 관찰자 점등으로 same-block receipt 보유 |
| `first concrete token lands at TR block 7+: YELLOW ceiling` | inactive | 첫 토큰은 TR `2` (조건부 공인 의원) |
| `no-cider drought 6+ blocks: YELLOW ceiling` | inactive | 최장 drought는 length 2 (`28~29`) |
| `BI acts as summary echo only: GREEN ceiling` | inactive | gate 6 evidence 참조 — BI가 TR `1~3`을 amplify |
| `early reward is asset-only and lacks status or authority shift: GREEN ceiling` | inactive | TR `2` 가주 직접 자격 + TR `4` 임무 격상 = status/authority shift |
| `wins rely on stupid opposition: GREEN ceiling` | inactive | 큰형/장로회/사마련 모두 incentive-driven |
| `domain texture is generic enough to swap with another lane: GREEN ceiling` | inactive | 침/경혈/경지/독역/약재 도메인 묘사 구체 |
| `protagonist passivity across a key arc: YELLOW ceiling` | inactive | 70블록 전 구간 능동 |
| forbidden_flattening / canonical lexicon 위반 | inactive | mandatory_lexicon 전 항목 정확 사용, 한 줄 기적치료/일반 전투 환원/약재 추상화 미관측 |

요약: YELLOW ceiling 캡 2건 (`any no-cider block`, `major defeat without next card in same/next block`) 동시 점등. GREEN ceiling 캡은 모두 inactive. 최상위 ceiling은 **YELLOW**.

## P1 Score Table

Spec source: `production-pair-benchmark-spec-v1.md` §5. 10 axes × `0 / 1 / 2`, total `20`.

| # | Axis | Score | Rationale |
| --- | --- | --- | --- |
| 1 | protagonist innocence | **2** | 옵닝 약점은 무공 자질 부재 + 가문 냉대 = `inherited bad frame` + `previous-era criteria`. 게으름·자초가 아님 (Opening Innocence Rule clean) |
| 2 | protagonist-only proof clarity | **2** | 어머니 의맥 + 200년 단절 의무일체 + 활침=살침 동일 기술 보유 — 대체 불가성이 TR `1·5·6·42·65·69`에서 누적 명시 |
| 3 | evaluation revision visibility | **2** | TR `2` 가주의 직접 결정 + TR `4` 장로회 시선 성격 변경 + TR `6` 가주의 추가 양보 — explicit and weighted |
| 4 | visible reward token strength | **2** | rank·protection·manual·inheritance clue·reputation 5종이 TR `2~6` 안에 concrete force로 동시 점등 |
| 5 | block1 → block2 linkage | **2** | TR `1` 의무일체 발현 → TR `2` 가주가 동일 사건을 기반으로 자격 발급, clean next-gate opening |
| 6 | rational opposition | **2** | 큰형 사술 의심(가문 보호 인센티브), 장로회 감시(가문법 정합), 독문 사마련(해독제 사업 인센티브), 좌천명(흡독공 야심) — 모두 incentive-driven, era-valid |
| 7 | domain truth density | **2** | 합곡·내관·극천·중완·풍지·태연·기해·백회 등 실제 경혈명, 약침·청심연·약왕곡 약재, 7경지 사다리, 독역 역전 법칙 — concrete domain truth가 엔진을 끌고 감 |
| 8 | repeatable loop clarity | **2** | `진단→처방→시술→경과 → 평가/접근권 수정` 루프가 TR `1·3·4·7·16·39·42·65·69`에서 반복 가동, 무림 적용 시 `의술 비무` 변형도 일관 |
| 9 | BI amplification power | **2** | BI `CommercialCode.killing_points`·`taboo_rules` (사랑하는 자 치료 금기 → 정의 침; 7번째 침 생명 대가 → 살침+활침 일체)가 TR `65/69` 결착을 sharpen — summary echo 아님 |
| 10 | blockwise cider continuity | **0** | 3건 no-cider (`13/28/29`) 존재 — axis 정의 `0 = one or more no-cider blocks` 직격 |

**Total: 18 / 20** (raw). axis 10 단독 0점이 cider 무수확 3건을 정확히 반영.

## Provisional Grade

**YELLOW** (raw 18/20 → ceiling-locked YELLOW)

- §8 grade decision table에 따르면 raw `17~20`은 GREENPLUS 대역, raw `13~16`은 GREEN 대역. 본 페어 raw score는 `18`이므로 점수만으로는 GREENPLUS 후보.
- 그러나 §6 cap rule 중 **`any no-cider block in the full-block cider scan: YELLOW ceiling`** + **`major defeat without next card in same/next block: YELLOW ceiling`** 두 건이 동시에 ACTIVE이며, §8.3 `YELLOW` 기준 `any YELLOW ceiling rule triggered, or any no-cider block exists`에 직접 해당.
- 따라서 raw 18/20에도 불구하고 ceiling이 GREENPLUS와 GREEN을 모두 잠그며 최종 등급은 `YELLOW`로 강제.
- P0 6 gates는 모두 PASS이므로 RED·RED-review-lane 위험은 없음. 본 등급은 페어 엔진의 결함이 아닌 cider cadence의 국소 실패에 의해 결정된 ceiling-bound YELLOW이다.

## Top 3 Repair Units

페어가 YELLOW이므로 alias note 대신 bounded repair units를 제시한다 (full-wave 수술 금지).

1. **block `13` 약침 결합법 same-block receipt 보강**
   - 현재 상태: 아버지 2차 치료 실패 + 약침 `착상일 뿐` (later promise)
   - 보강 방향: 동일 블록 안에서 매화가 즉석 약초 1종을 들고 와 첫 약침 prototype을 비공식 환자 1명에게 시험 성공시키거나, 혜란이 가문 약방에서 약초 1세트 confidential 반출권을 따 와 다음 블록의 카드로 reader가 즉시 손에 잡게 한다
   - 캡 해제 효과: cider scan 무수확 1건 제거
2. **block `28` 손해 동시 카드 보강**
   - 현재 상태: 경맥 3개 손상·내공 급락만 있고 same-block receipt가 `서역행 동기`라는 미래 약속 한 줄
   - 보강 방향: WG `custom_rules`의 `반격 예약 없는 손해 금지`를 동일 블록에 강제 — 손상 직후 엽천수가 천축 라지브 소개장(=`다음 카드`)을 그 자리에서 손에 쥐어주고, 매화가 약왕곡 약초 1점을 즉시 확보한다는 보고를 들고 들어와 손해를 같은 블록 안에서 부분 상쇄
3. **block `29` workaround → reevaluation 전환**
   - 현재 상태: 진단+처방 분업 체계 + 매화 성장만 있고 가문/무림 시선이 받아주는 receipt가 없어 setup-only
   - 보강 방향: 동일 블록 안에서 장로 1명 또는 정파 의선 채널이 분업 체계를 `의원-약사 표준 모델`로 공식 인정 (호칭·접근권·평가 수정 1줄)하여 분업 자체를 `weighted reevaluation receipt`로 격상

위 3건만 처리해도 cider scan 무수확 0건이 가능하고, full-wave TR 재집필 없이 GREEN 진입 가능성이 열린다.

## Concise Rationale

- pair `09` `wuxia_heavenly_physician`은 wuxguide family doctrine을 정면으로 받아내는 강한 페어이다. P0 6 gates 전체가 PASS이며, 특히 신설 정규화된 gate `6` (`BI/TR early conversion alignment`) 역시 BI `CoreIdentity.initial_goal`·`CommercialCode.killing_points[0]`·`do_not_fake` success_device가 TR `1~3`에서 가시적으로 살아 있어 amplification으로 통과한다. block `2` 가주 직접 평가 수정과 block `6` 서고 의서 접근권은 wuxguide token 사다리에서 가장 묵직한 두 단계가 6블록 이내에 안정적으로 떨어진 사례이다.
- P1 10 axes × 0/1/2 환산 결과 raw score는 **18 / 20**이며, axis 10 (`blockwise cider continuity`) 단독 `0`이 본 페어의 유일한 약점을 정확히 지목한다. 나머지 9 axis는 모두 만점으로, protagonist innocence·only-proof·rational opposition·domain truth·BI amplification 모두 GREENPLUS 자질을 갖춘 상태다.
- 그러나 §6 cap rule의 `any no-cider block: YELLOW ceiling`과 `major defeat without next card in same/next block: YELLOW ceiling`이 동시에 ACTIVE이며, §8.3 YELLOW 조항이 raw score와 무관하게 우선 적용된다. 따라서 raw 18/20임에도 ceiling-bound로 최종 grade는 **YELLOW**로 확정된다.
- 끌어올림 비용은 매우 낮다 — 본 페어의 ceiling은 `13 / 28 / 29` 3블록 국소 결함에서 발생하며, 위 `Top 3 Repair Units` 만으로 cider scan 무수확 0건 + cap rule 동시 해제가 가능하다. 그 시점에서 raw 18/20은 그대로 GREEN/GREENPLUS 대역으로 풀려난다. full-wave 수술은 금지하며, 본 보고서는 어떤 페어 파일도 변형하지 않았다.

read-only true benchmark audit complete; no pair files mutated
