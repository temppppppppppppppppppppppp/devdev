# 10pair True Benchmark Terminal 04 Pair 04 Report

Date: 2026-04-07
Status: active
Document Type: read-only true benchmark audit
Canonical Path: `docs/2026-04-07/10pair_true_benchmark_terminal04_pair04_report.md`
Parent Order: `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
Source Prompt: `docs/2026-04-07/10pair_true_benchmark_terminal04_pair04_prompt.md`

## Pair Identity

- pair id: `04`
- slug: `defense_defect_engineer`
- family: `blockguide`
- canonical via: `docs/2026-04-07/01_10_canonical_pair_manifest.md`
- BI: `bible/04_bi_defense_defect_engineer.json`
- TR: `treatments/04_defense_defect_engineer_tr_block_070_draft.json` (`_total_blocks: 70`)
- WG: `work_guards/04_defense_defect_engineer.yaml`
- one-line truth (WG): 버림패 막내아들이 결함선 한 줄로 시험평가권·규격 문구·정비권·수출금융을 자기 손에 묶어, 방사청·군·해외 파트너가 준영을 안 거치면 납품도 수출도 못 굴리는 방산 후계 관문이 된다.
- canonical scope rule: pair `04` is the only `defense_defect_engineer` axis with all three of BI/TR/WG aligned; no override invoked.

## Evidence Anchor Table

| Anchor | Source | Value (compressed) |
| --- | --- | --- |
| `one_line_truth` | WG `work_identity.one_line_truth` | 결함선 한 줄로 시험평가권·규격 문구·정비권·수출금융을 묶어 방산 후계 관문이 된다 |
| BI `cider_point` | BI `MasterBible/ProjectData/CommercialCode/cider_point` | 2024 버림패 → 2010 회귀, 시험평가권·규격 문구·정비권·수출금융·SPV·ITAR 우회·감사장부 10대 전장을 자기 손에 묶는 역전감 |
| BI `success_device` | BI `MasterBible/ProjectData/CommercialCode/success_device` | 회사가 아니라 병목을 먹는다 / 안전은 명분, 목적은 승계·규격 독점 / "준영 없는 한국 방산" 수렴 |
| BI early promise = TR opening axis | BI CommercialCode ↔ TR B2 solution | TR B2: '계열사 매각 = 5년 뒤 경쟁사 규격 종속' 즉시 발화 → BI promise visibly alive at TR block 2 |
| `mandatory_scene_engines` | WG `work_identity.mandatory_scene_engines` | 결함선/비리선 발화 → 안전 명분으로 시험 순서·규격 문구·정비권 재배치 → 공개 증명 → 체감형 보상(지분/운영권/시험권/규격권/정비권) |
| `evaluation_thresholds` | WG `protagonist_evaluation.evaluation_thresholds` | 1화 내 이사회 붉은 선 발화 → 매각 저지 거래; Block 1 완료 시 1.4%→2.6% + 시험평가 접근권 + 감사장부 확보 |
| `tracking_slots` | WG `work_identity.tracking_slots` | 개인 영향 지분 1.4% → 4.8% → 8.9% → 13.7% → 19.6%; 권한 축 회수 누적; 저평가 → 고평가 전환 |
| `custom_rules` | WG `custom_rules` | 안전은 명분; 위기는 우선순위 선택권 증명; 반격 예약 없는 손해 금지; 보상은 지분/운영권/시험권/규격권/정비권 중 1종 체감 |
| `CommercialCode equivalent` | BI `MasterBible/ProjectData/CommercialCode` | 동일 상속 — cider/success/promise 한 묶음으로 BI 안에서 명시화 |
| capital tracking (TR) | TR `genre_ext.capital_before/after/delta` per block | 1.4% (B1) → 19.6% (B69); WG threshold 1.4→2.6 (B10), 4.8 (B20), 8.9 (B40), 13.7 (B60), 19.6 (B69) 모두 도달 |

## P0 Hard Gates

P0 anchors restricted to TR blocks `2~6` for gates `1~4`, per benchmark spec §2.1 and prompt non-negotiable.

| # | Gate | Verdict | TR Anchor (block-numbered) | Evidence |
| --- | --- | --- | --- | --- |
| 1 | first-block visible cider | PASS | TR B2 | 안건 4번 호명 즉시 결함선/비리선 발화 → '매각 안건 결재 보류 + 48시간 대체 근거 제출권' 확보. 이사회장 분위기 전환을 reader-countable 사이다 비트로 박는다. |
| 2 | protagonist-only proof | PASS | TR B2 (보강 TR B5) | 결함선·비리선은 회귀 후 각성 능력으로 접촉 대상에만 발화 (WG `protagonist_weapon` + B5에서 능력 제약 재확인). '저건 쟤라서만 가능했다'가 B2 solution 한 줄(빔 보고서 위에서 결재선·미소·하중표가 동시에 붉어짐)에서 굳어진다. |
| 3 | evaluation revision | PASS | TR B2, TR B4 | B2 `relationship_delta`: 하도진 — '막내를 아직 아이로 보는 회장' → '막내의 목소리를 처음 경영자의 목소리로 들은 회장'. B4: 정해윤 — '관찰자' → '회장 시험의 전달자'. 둘 다 weighted observer (회장·비서실장) 재평가. |
| 4 | visible reward token | PASS | TR B2, TR B4, TR B6 | B2 = 결재 보류 + 48시간 대체 근거권 (approval/entry ticket). B4 = 48시간 조건 설계권 +0.1%p (조건 명세 확보). B6 = 감사 명분 채권 회수권 기초 +0.2%p. 모두 blockguide 토큰군(approval/authority/access shift)에 정확히 해당. |
| 5 | block1 → block2 gate linkage | PASS | TR B6 → TR B7 → TR B8 | B6 reward(채권 회수권 기초)과 B4 reward(48시간 조건 설계권)가 B7(시험일정 봉쇄, 패배 #2) → B8('시험평가대대 안건 1차 근거 제공자' 진입)을 직접 연다. B7+는 backfill이 아니라 downstream confirmation. |
| 6 | BI/TR early conversion alignment | PASS | BI `CommercialCode` ↔ TR B1~B3 | BI cider_point의 '시험평가권·규격 문구·감사장부' 키워드가 B2 solution(시험평가권 진입)과 B6 reward(감사 명분 채권 회수)에 동일 어휘로 살아 있다. BI success_device의 '안전은 명분' 원칙이 B2/B6 모두 'solution'에서 명문화되어 있어 BI는 echo가 아니라 contract source로 동작 중. |

P0 verdict: **6/6 PASS**, all anchors live inside TR `2~6` (gate 5 confirmed by `7~8`, not rescued by them).

## Full-Block Cider Scan

- total TR blocks: **70**
- no-cider blocks: **13**
- exact no-cider block numbers: **B1, B3, B5, B7, B11, B19, B24, B31, B43, B49, B55, B63, B67**
- longest no-cider drought: **1 block** (every no-cider block is isolated; no two consecutive)
- cider blocks: **57 / 70 (≈81%)**

Cider doctrine applied: a block scores `has_cider: true` only when it lands a procurement / standard / approval / control / authority shift the reader can count *inside the same block*. Defect-analysis or domain explanation alone does not qualify (per WG forbidden_flattenings + watchpoint).

No-cider rationale (block-by-block):

- **B1** — 회귀 직후 판독 준비. setup-only intro; capital 0.0%p; deal_type `판독 준비`; reward 명시 = '돈도 권한도 얻지 못한다'.
- **B3** — 패배 #1 (요구 범위 반으로 접힘). 공개 모욕 감수, capital 0.0%p; B2 거래의 일부 회수에 그쳐 자체적으로는 token이 없음. 48시간 유예 자체는 B2에서 이미 발급된 토큰의 잔향.
- **B5** — 정비로그 서버 앞. 능력 매핑 quiet, capital 0.0%p, 'wait-only / setup-only' 카테고리. 결함선 분포 지도 자체는 다음 블록으로 가는 도구이며 same-block 영수증 없음.
- **B7** — 패배 #2 (시험일정 동결). -0.1%p, deal_type `재접선 문 확보` — 확보가 아니라 재접선 가능성만 남김.
- **B11** — 패배 #3 (협력사 이탈). -0.1%p, 카드 축적만 발생.
- **B19** — 패배 #4 (시험일정 재봉쇄). -0.1%p, 동선 재편만.
- **B24** — 패배 #5 (열처리 사고 책임 전가 유예). -0.2%p, 카드 첫 활용이지만 결과는 방어로 수렴.
- **B31** — 패배 #6 (국감 폭로). -0.2%p, 방어 동작.
- **B43** — 패배 #7 (중동 시제기 사고). -0.2%p, 신뢰 방어.
- **B49** — 패배 #8 (수출금융 심사 지연). -0.1%p, 설계 방어.
- **B55** — 패배 #9 (SPV 추적 노출). -0.3%p, 차명 SPV 방어.
- **B63** — 패배 #10 (가문 쿠데타, 공개 패배 프레임). -0.2%p, 방어.
- **B67** — 패배 #11 (유럽 인증 반려). -0.2%p, 2종 방어 카드 동시 가동.

Note: 모든 패배 블록은 직후 블록(B4/B8/B12/B20/B25/B32/B44/B50/B56/B64/B68)에서 즉시 회복 + 권한 회수 카드를 받으므로, '반격 예약 없는 손해 금지' (WG custom_rule) 위반은 없음. 단, doctrine상 same-block receipt가 없으면 `has_cider: false`로 잡히는 것은 막을 수 없다.

Window summaries:

- **B1~10**: 4 no-cider (B1·B3·B5·B7) / 6 cider. ARC-01 회귀 직후 → 매각 저지 거래 → 전략조정실 위임까지 P0 토큰이 B2/B4/B6/B8/B9/B10에 연이어 박혀 있고, B10에서 '전략조정실 실권 + 시험평가 접근권 + 채권 회수권 공식 위임'으로 WG threshold(2.6%)를 정확히 찍는다. 단, intro/quiet/패배 블록이 윈도우 내 4개로 가장 빽빽한 구간.
- **B11~20**: 2 no-cider (B11·B19) / 8 cider. 규격 초안 의견권(B12) → 협력사 연합(B13) → 방사청 서명 의무(B14) → 복합재 기술 접근(B15) → 시험 순서 재배치 공식화(B16) → 차명 SPV 설계(B17) → 채권 회수권 공식 집행(B18) → 규격 초안 첫 문장 삽입(B20, Phase0 체크포인트). cider 밀도 매우 높음.
- **B21~30**: 1 no-cider (B24) / 9 cider. 복합재 라인 정지권/감사장부 3차/SPV 설립까지 control axis가 끊김 없이 누적, B30에서 SPV 본 설립 Phase0 체크포인트.
- **B31~40**: 1 no-cider (B31) / 9 cider. 국감 방어 직후 곧바로 두 번째 규격 문장 삽입(B37) + 카르텔 국회 축 무력화(B40) Phase0. 정치/방산 규제 양축이 분리되어 굴러간다.
- **B41~50**: 2 no-cider (B43·B49) / 8 cider. 중동 진입 → 수출금융 패키지 1차 합의 → 오프셋 역제안 → 정비거점 선매입(B50, Phase0). +0.8%p로 최대 단일 블록 도약 발생.
- **B51~60**: 1 no-cider (B55) / 9 cider. ITAR 압박을 미국 없는 대체설계 + 공동규격 역제안 두 트랙으로 흡수, B60(Phase0)에서 ITAR 부분 전환 + 유럽 인증 진입 +0.9%p.
- **B61~70**: 2 no-cider (B63·B67) / 8 cider. 후계 지분 스왑 완성(B69, +3.8%p Phase0 최종 체크포인트) → B70 '준영 없는 방산' 구조 공식 가동, BI cider_point의 '준영 없는 한국 방산' 어휘가 그대로 결제됨.

Drought verdict: 13 no-cider blocks 모두 단일 블록으로 흩어져 있어 '6+ drought' cap rule은 발화하지 않는다. 그러나 spec §2.3 / §6의 '하나라도 no-cider면 YELLOW ceiling' 룰은 그대로 발화한다.

## Active Cap Rules

- **YELLOW ceiling — any no-cider block in full-block cider scan** (spec §6, §2.3): 13개 no-cider 블록(B1, B3, B5, B7, B11, B19, B24, B31, B43, B49, B55, B63, B67)이 존재하므로 발화. 이 페어는 GREEN/GREENPLUS 진입 불가.
- 그 외 cap 발화 없음:
  - rewardless pain blocks 2 in a row: 미발화 (모든 패배 단일, 직후 회복).
  - no-cider drought 6+: 미발화 (최장 drought = 1).
  - major defeat without next card in same/next block: 미발화 (모든 패배 직후 회복 카드 부착).
  - early reward asset-only: 미발화 (B2/B4/B6 모두 권한·결재·접근권 토큰).
  - wins rely on stupid opposition: 미발화 (하성우/민태수/윤문희 모두 era-rational).
  - BI summary echo only: 미발화 (BI가 contract source로 동작).
  - domain texture generic: 미발화 (시험평가권/규격 문구/정비권/SPV/ITAR/오프셋 어휘 밀도 매우 높음).
  - protagonist passivity across key arc: 미발화.
- Opening innocence rule (§4.3): 회귀 시점의 몰락은 '장식용 막내 / 가문 라인 정치 / 14년 전 결재선 종속'에서 발생, current-protagonist fault 아님 → acceptable.

## P1 Score Table

| Axis | Score | Rationale |
| --- | --- | --- |
| protagonist innocence | 2 | 회귀 시점 몰락은 가문 정치 + 시험평가권·규격권·정비권 상실 누적의 결과(WG `evaluation_thresholds` 14년 순서). 게으름·자초 붕괴 없음. |
| protagonist-only proof clarity | 2 | 결함선·비리선은 접촉 대상에만 발화(WG `protagonist_weapon`); B2에서 빔 보고서 위 결재선·미소·하중표가 동시에 붉어지는 장면이 '쟤라서만 가능' 낙인. |
| evaluation revision visibility | 2 | 회장 하도진(B2), 정해윤(B4), 윤소라(B8), 박성우(B12·B14), 고준명(B6), 하성우(B11→B20), 민태수(B61) 등 weighted 관찰자 다수가 단계별 재평가. |
| visible reward token strength | 2 | B2 결재 보류/48시간 대체 근거권, B4 48시간 조건 설계권, B6 채권 회수권 기초, B10 전략조정실 실권 + 시험평가 접근권, B20 규격 초안 첫 문장. concrete + force. |
| block1 → block2 linkage | 2 | B6 채권 회수권 → B7-8 시험평가대대 진입 → B10 전략조정실 위임. 다음 게이트가 reward로만 열린다 (WG custom_rule '다음 블록은 이전 보상으로만 열린다' 충실 이행). |
| rational opposition | 2 | 하성우·민태수·윤문희 모두 '이전 시대 정답을 쥔 사람의 합리적 견제' (WG role_fit_constraints 통과). 무능 캐리커처 없음. |
| domain truth density | 2 | 시험평가권/규격 문구/정비권/수출금융/차명 SPV/오프셋/ITAR/감사장부/열처리/협력사 채권 등 mandatory_lexicon 13항이 TR 전 구간에 빈번 발화. lane swap 불가. |
| repeatable loop clarity | 2 | 접촉 → 결함선/비리선 발화 → 안전 명분 포장 → 시험순서/규격/정비권 재배치 → 공개 증명 → 체감형 보상. WG `mandatory_scene_engines` 3-스텝 루프 그대로 반복, ARC-01~07 동일 패턴. |
| BI amplification power | 2 | BI CommercialCode가 cider_point/success_device를 명문화, custom_rules·tracking_slots·evaluation_thresholds 모두 TR 블록 단위 행동을 직접 규율. WG threshold 4단(2.6/4.8/8.9/13.7/19.6%)이 TR B10/B20/B40/B60/B69에 정확히 찍힘. |
| blockwise cider continuity | 0 | 13 no-cider blocks. spec §5 정의상 '하나 이상 no-cider' = `0`. |

Total: **18 / 20**

## Provisional Grade

**YELLOW** — 점수만 보면 18/20으로 GREENPLUS 밴드(17~20)에 들어가지만, '하나라도 no-cider 블록이 있으면 YELLOW ceiling' cap rule이 발화하여 강제로 YELLOW로 캡 처리된다. P0 6/6 통과·9개 P1 축 만점·BI/TR contract alignment 우수·페이즈0 체크포인트 5개 정확 도달이라는 강한 신호와, defeat 블록 11개·intro/quiet 블록 2개에서 same-block receipt가 빠지는 doctrine-level 비용이 동시에 존재한다. '강한 YELLOW / GREEN 직전' 등급으로 읽는 것이 정확하다. promotion 전 bounded repair 권장.

## Top 3 Repair Units or Alias Note

Top 3 repair units (bounded — full-wave surgery 금지):

1. **defeat-block same-block receipt 부착** (B3, B7, B11, B19, B24, B31, B43, B49, B55, B63, B67)
   - 현재 모든 패배는 직후 블록에서 회복되지만, 같은 블록 안에서는 reader-countable 토큰이 비어 있다. WG `evaluation_thresholds` '큰 피해 뒤 즉시 다음 카드 확보'를 *same-block* 단위로 끌어내려, 각 패배 블록 reward 필드에 최소 1종 카드(예: B3의 '48시간 유예권 명문화 메모'를 정해윤이 회장 결재선에 공식 등록, B11의 '협력사 이탈자 명단 → 감사장부 새 페이지 등록' 등)를 명시하면 13 → 2까지 no-cider 수가 급감한다.
   - 우선 처치 대상: 손실폭이 가장 큰 B55(-0.3%p)와 공개 패배 프레임 B63(-0.2%p) — 이 둘이 same-block receipt를 받으면 후반 사이다 곡선 체감이 가장 크게 살아난다.

2. **B5 (정비로그 서버 앞) quiet 처리 격상**
   - 현재 deal_type `정비로그 선별 접촉` + capital 0.0%p로 setup-only로 잡힌다. 능력 제약 매핑은 유지하되, 같은 블록 안에 small access-shift token 1종(예: 당직 엔지니어가 출입 대장에 '전략조정실 상무보 명의' 첫 등록 → 이후 B8/B16 시험 순서 재배치 시 동일 출입 라인이 자동 통과)을 부착하면 B5가 'recovery asset that materially offsets same-block setup cost'로 즉시 전환된다.

3. **B1 (회귀 직후 복도) 영수증 한 줄 첨부**
   - 회귀 프롤로그 성격상 capital 변동은 0.0%p가 자연스럽지만, '대기실에서 정해윤의 시야 가장자리에 14년 메모 가장자리를 의도적으로 노출 → B4 정해윤 first 의심선 점화의 사전 영수증' 같이 *future-prep token*을 same-block에서 발행하도록 reward 필드 한 줄을 보강하면 B1도 has_cider: true로 잡힐 수 있다. 본문 길이 변화 최소.

Alias note (보조): repair 후 13 → 0 no-cider blocks가 달성되면 P1 18/20·P0 6/6·cap 미발화 조합으로 GREENPLUS 승격 후보가 된다. 현 시점 alias는 'production-ready engine, capped by defeat-block same-block receipt doctrine — bounded repair 후 재감리'로 기록.

Residual risk 메모(repair와 무관): WG forbidden_flattenings '결함선 만능 예지 사용 금지' / '안전 위장으로 자기이익 흐림' 두 항목은 후반 ARC(특히 B60~B69 후계 지분 스왑) 진입 시 재검토 필요 — 현 TR은 통과하지만 surgery 시 새로 도입되는 보상 비트가 '안전 위장' 톤을 강화하지 않도록 주의.

## Concise Rationale

이 페어는 본문 doctrine과 BI/TR contract alignment 측면에서 현재 10pair 중 매우 단단한 축에 속한다. P0 6/6 PASS는 TR `2~6` 안에서 회귀 → 결함선/비리선 발화 → 매각 안건 결재 보류 → 48시간 조건 설계권 → 채권 회수권 기초 → 전략조정실 위임 → 시험평가 접근권 →… 사슬이 끊김 없이 박혀 있고, BI CommercialCode의 cider_point/success_device가 단순 echo가 아니라 매 블록 solution/reward 어휘를 직접 규율한다는 사실에서 나온다. WG threshold 4단(2.6%·4.8%·8.9%·13.7%·19.6%)이 TR B10/B20/B40/B60/B69에 정확히 찍히는 것도 contract source가 살아 있다는 강한 신호다.

YELLOW 캡은 '내용이 약해서'가 아니라 '13개 no-cider 블록이 있어서'로 발화한다. 그 13개의 정체는 1개의 회귀 프롤로그(B1), 1개의 quiet 능력 매핑(B5), 그리고 11개의 패배 블록(B3·B7·B11·B19·B24·B31·B43·B49·B55·B63·B67)이다. 패배 블록은 모두 직후 블록에서 회복 카드를 받으므로 '반격 예약 없는 손해 금지' WG custom_rule을 어기지 않는다. 단, spec §2.3은 same-block 단위로 receipt를 요구하므로, 'doctrine 상 카운트는 no-cider'와 'narrative 상 패배는 즉시 갚힌다'가 분리되어 있을 뿐이다. 따라서 본 보고서는 vibe로 GREEN을 추론해 올리지 않고 doctrine을 그대로 적용해 YELLOW로 캡 처리한다.

복구 비용은 작다. 패배 블록 reward 필드 한 줄씩 + B5 access-shift token 1종 + B1 future-prep token 1종이면 no-cider 수가 0에 수렴한다. full-wave surgery는 금지이며 그럴 필요도 없다. 현재 페어는 '강한 YELLOW / repair 후 GREEN~GREENPLUS 후보'로 읽는다.

read-only true benchmark audit complete; no pair files mutated
