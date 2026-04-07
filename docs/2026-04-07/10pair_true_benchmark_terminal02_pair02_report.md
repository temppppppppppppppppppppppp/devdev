# 10pair True Benchmark Terminal 02 Pair 02 Report

Date: 2026-04-07
Mode: read-only true benchmark audit (rescored against `production-pair-benchmark-spec-v1`)
Scope: canonical pair `02` (`chaebol_allowance_zero`)
Parent Order: `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
Prompt: `docs/2026-04-07/10pair_true_benchmark_terminal02_pair02_prompt.md`
Spec authority: `material_ssot/00_governance/production-pair-benchmark-spec-v1.md` §4 (P0 6 gates), §5 (P1 10 axes × 0/1/2), §6 (cap rules), §8 (grade decision)
Note: 직전 패스의 `4-gate / 8-axis / 5점 척도` 채점은 evidence scouting pass로 격하한다. 본 섹션 P0/P1/Provisional Grade는 spec v1 기준으로 처음부터 다시 채점한 결과다. Full-Block Cider Scan 섹션과 flagged block reread 증거(#14/#29/#57)는 재사용한다.

## Pair Identity

- pair id: `02`
- slug: `chaebol_allowance_zero`
- family: `blockguide`
- WG: `work_guards/02_chaebol_allowance_zero.yaml`
- TR: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` (`_total_blocks=70`, blocks 1~70 present)
- BI: `bible/02_bi_chaebol_allowance_zero.json` (MasterBible schema)
- canonical manifest row: `docs/2026-04-07/01_10_canonical_pair_manifest.md` line 17 — main pair, 3축 정합 확인

## Evidence Anchor Table

| Anchor | Source | Location | Extracted Value |
| --- | --- | --- | --- |
| `one_line_truth` | WG | `02_chaebol_allowance_zero.yaml:5` | "카드 잘린 재벌 3세가 … 가문이 먼저 자기 현금흐름망에 의존하는 구조를 만든다" |
| `mandatory_scene_engines` | WG | `02_chaebol_allowance_zero.yaml:58~61` | 누수→소액 개입→반복매출 / 정산 레인 표준화→공개 성과 / 성과 직후 체감형 보상 부착 |
| `evaluation_thresholds` | WG | `02_chaebol_allowance_zero.yaml:83~87` | 1화 내 첫 사이다(밥차) / 3화 내 간판 폭발(첫 월 반복매출 → 형의 눈빛 전환) / ARC 종료 시 다음 입장권 / 손해 동반 즉시 확보 |
| `tracking_slots` | WG | `02_chaebol_allowance_zero.yaml:53~57` | 반복 현금흐름 0 → 12억 → 38억 → 76억 → 154억 → 전국망 / 권한 축 누적 / 가문 역의존도 |
| `custom_rules` | WG | `02_chaebol_allowance_zero.yaml:110~117` | 반격 예약 없는 손해 금지 / 매 블록 보상은 권한 6종 중 1종 체감형 / 다음 전장은 이전 전장 보상으로만 / 회귀 기억 = 시장 시세 예언 금지 |
| `forbidden_flattenings` | WG | `02_chaebol_allowance_zero.yaml:37~52` | 회개물 스타트, 가문 공짜 구제, 운영축 generic 평탄화, 단일 악당 캐리커처 등 |
| `early promise / 첫 사이다` | TR | `block #2 [장례 밥차]` | 90분 응급 배식 + 한유림·최병태 reldelta 전환 + 자본 +2억 |
| `success_device 등가물` (반복매출 포지션) | TR | `block #2 reward`, `#10 reward` (`아크 exit`) | "반복매출 후보 라인 선점" → block #10 "월 반복매출 증명 완료" |
| `cider_point 등가물` (체감형 권한 보상) | TR | blocks #2~#70 reward 슬롯 전수 | 매 블록 reward에 권한/계약/입장권/자본 변화 1종 이상 |
| `CommercialCode 등가물` (자본·매출 디지털 트랙) | TR | 모든 블록 `reward.자본 X → Y` | 0.5억 → 100억+ 단조 상승, 회복 누락 없음 |
| `mandatory_lexicon` 사용도 | TR | 광범위 (반복매출, 정산 레인, 구매 코드, 영수증, 누수, 유령업체, 린넨, 밥차, 셔틀 다수 등장) | 어휘 가드 통과 |
| 적대축 비-캐리커처 | TR | `#4` 윤석진 reldelta, `#10` 서도윤 reldelta, `#30` CFO 침묵 | "이전 시대의 정답을 믿은 사람"으로 묘사, role_fit_constraints 위반 없음 |

## P0 Hard Gates

채점 표준: spec v1 §4.1 `Gate Set` 6개. Gates 1~5는 strict window `TR blocks 2~6`만 인용; gate 6은 BI/WG early conversion alignment를 `TR blocks 1~3`에서 본다. `TR block 1`은 opening setup만 허용, `TR block 7+`는 gate 5의 downstream confirmation 외에는 인용 불가 (spec §2.1).

| # | Gate (spec v1 §4.1) | 결과 | TR 앵커 (절대 블록 번호) | 비고 |
| --- | --- | --- | --- | --- |
| 1 | first-block visible cider | **PASS** | `#2 [장례 밥차]` reward = 긴급 배식 수수료 + 폐기 예정 식자재 재배치로 자본 +2억 (visible reader-countable payback); `#3 [검은 리본 주차권]` reward = 셔틀·주차 관제권 48시간 회수 | TR 2~6 안에서 즉시 cider 발생; setup-only/explanation-only 아님 |
| 2 | protagonist-only proof (`저건 쟤라서 가능했다`) | **PASS** | `#2` solution = 회귀 기억(어느 외주가 호텔·병원까지 갔는지) + 의전팀장 동선표 + 냉장창고 재고를 90분 응급 배식으로 합성; `#4 [꽃값은 현금이다]` solution = 외부 대출/가문 자금 없이 꽃집 4곳을 회의실에 모아 영수증 분리 발행 계약 + 한유림에게 단가 정상치 초과분 실시간 산출 | WG `protagonist_weapon` 3종(누수 지도·새벽 뒷문 감각·재배치 속도)이 in-frame; 누구도 대체 불가 |
| 3 | evaluation revision (weighted reevaluator) | **PASS** | `#2` 한유림 reldelta "비서실 구매분석 실무자 → 재이 방식이 숫자 기반 설계라고 첫 인정한 내부 관찰자"; `#3` 서도윤 reldelta "동생 굴욕이면 된다는 장남 → 작은 운영권 방치가 체면·통제력을 갉아먹는다고 본다" (WG `observer_tiers[2]` = 가장 무거운 weight); `#4` 윤석진 reldelta "재이를 잘라낼 명분만 찾는 CFO → 꽃값 단가 이상을 재이가 먼저 잡았다는 데 당혹하는 CFO" (WG `observer_tiers[3]`) | 셋 다 explicit + weighted, TR 2~6 안에서 닫힘 |
| 4 | visible reward token (concrete blockguide token) | **PASS** | `#3` 셔틀·주차 관제권 48시간 (authority shift); `#4` 꽃집 4곳 영수증 분리 발행권 (approval/ownership); `#5 [빈소 셔틀]` 셔틀 노선 3개 공동 운영권 + 배정호 라인 + 세탁 공장 설비 접근권 (ownership + entry ticket); `#6 [조의금 영수증]` 비서실 시스템 증거 예치 = 숨은 증거 자산 1건 (report line/access) | spec §4.1 blockguide 토큰 카탈로그(name call·seat·CC·report line·TF·approval·ownership·entry ticket) 중 다수 동시 발생 |
| 5 | block 1 → block 2 gate linkage | **PASS** | `#5` 셔틀 노선 3개 공동 운영권 + 세탁 공장 설비 접근권 → 호텔 BOH(린넨실·셔틀) 진입의 직접 발판; `#10 [도련님 대신 대표]` reward "장례식장 운영권자 → '호텔 BOH 진입 자격자'로 격상 + 호텔 백오브하우스(린넨실) 진입 입장권 확보"는 spec §2.1 허용 범위의 downstream confirmation으로만 인용 (token 자체는 `#5`에서 earned, retroactive supply 아님) | gate token이 `block 6 or earlier`에 존재; `#10`은 backfill이 아니라 confirmation |
| 6 | BI/TR early conversion alignment | **PASS** | BI `MasterBible.ProjectData.MetaInfo.grand_objective` "유언장 7항으로 가문 돈 한 푼 못 쓰게 된 윤성그룹 오너 3세 윤재이가, 장례·급식·호텔 백오브하우스·공장·병원·정산·전국 운영망을 밑단에서부터 장악해 가문이 먼저 자기 현금흐름망·정산 레인·운영 인프라에 의존하는 구조를 만든다. … 첫 보상은 돈 자체가 아니라 다음 운영 전장에 발을 들일 수 있는 권한·명분·입장권이다." → TR `#1` 유언장 7항·카드 잘림 / `#2` 장례 밥차 + 첫 권한 / `#3` 셔틀 관제권에 1:1 alive. BI `MetaInfo.logline` "카드가 잘린 장례식장 뒷문에서 윤재이는 상속보다 매일 돌아가는 돈의 길목이 먼저라는 걸 배운다. 밥차·꽃값·셔틀·영수증·세탁실부터 시작해…" → TR `#2` 밥차 / `#3` 셔틀 / `#4` 꽃값·영수증 / `#5` 세탁실 발판 4카드 모두 strict window 안에 정확 매핑. BI `ProjectData.CommercialCode.cider_point` "카드 잘리고 망나니로만 읽히던 재벌 3세가 장례식장 뒷문부터 꽃값·밥차·영수증·정산 레인을 한 칸씩 손에 옮겨와 가문이 먼저 조건표 앞에 줄을 서게 만드는 역전감" → `#3` 서도윤 reldelta + `#4` 윤석진 reldelta가 "한 칸씩 옮겨오는" 첫 역전 도장. BI `ProjectData.CommercialCode.success_device` "상속보다 매일 나가는 돈의 길목을 먼저 쥔다. 계약권·승인권·정산권·현장 대체 불가능성을 한 칸씩 옮겨 오면 결국 회장실도 따라온다" → `#3` 관제권(현장 대체 불가능성) / `#4` 영수증 분리 발행권(승인권) / `#5` 셔틀 노선 3개 운영권(계약권) 3종이 strict window 안에서 직접 발화 | BI grand_objective·logline·cider_point·success_device 4축이 TR `#1`~`#5`에서 visibly alive; BI는 summary echo가 아니라 TR strict window의 직접 anchor로 작동 |

**Opening Innocence Rule (§4.3)**: `#1`의 카드 잘림은 노현주 유언 집행 + 가문 정치 결과 (political sacrifice + inherited bad frame). 게으름·무책임·자초한 붕괴 아님. **PASS**.

**P0 합산: 6 / 6 PASS.** §4.2 ceiling rule 미발동, §7 RED trigger 미발동.

## Full-Block Cider Scan

스캔 대상: TR `blocks 1~70` (`_total_blocks=70`).
판정 기준 (spec v1 §2.3 정규화): 각 블록을 `has_cider: true/false`로 마킹한다. `has_cider: true`는 **같은 블록 안에서** reader-countable payback이 최소 1종 이상 발생해야 한다 — visible reward token / weighted reevaluation receipt / protection receipt / authority or access shift / same-block pain을 실질적으로 상쇄하는 recovery asset / 독자가 지금 체감 가능한 explicit next-card or next-gate receipt 중 하나. setup-only · explanation-only · wait-only · pain-only · humiliation-only · failure-only · "later payoff" promise without same-block receipt는 모두 `has_cider: false`. Watchpoint 적용: 단순 생존·용돈 연장·임시 유예는 status/control이 on-page에서 이동하지 않는 한 felt receipt로 인정하지 않는다.

### Window Summary

| Window | Block 수 | Cider | No-cider | 비고 |
| --- | --- | --- | --- | --- |
| 1~10 | 10 | 10 | 0 | 장례 ARC. `#2` 첫 cider, `#10` 아크 exit (호텔 BOH 입장권) |
| 11~20 | 10 | 10 | 0 | 호텔 BOH ARC. `#14` 주차장 야간반 발렛 전표 교차 확인권 + 누수 환수 0.9억 (1차 키워드 스캔에서 false-flag, 재읽기 결과 권한 회수 명시) → cider |
| 21~30 | 10 | 10 | 0 | 공장 ARC. `#29` 공장 셋 통합 (적대자 지역 통제권 1/3 축소 명시, 1차 false-flag → 재읽기 cider 확정), `#30` CFO 침묵 + 병원 입장권 |
| 31~40 | 10 | 10 | 0 | 병원/팬데믹 ARC. `#40` 그룹 이사회 공식 인정 + 154억 연환산 포지션 확정 |
| 41~50 | 10 | 10 | 0 | 정산 시스템 ARC. `#50` 그룹 중앙 정산망 이양, CFO "운영 이양" 첫 수용 |
| 51~60 | 10 | 10 | 0 | 금융 ARC. `#56` 공급망 대출 원장 공식, `#57` 밥줄 팩토링 (1차 false-flag → 재읽기 결과 협력사 현금흐름 60일 → 5일 + 팩토링 라인 가동, cider 확정), `#60` 금감원 통과 |
| 61~70 | 10 | 10 | 0 | 가문 역의존 ARC. `#70` 최종 254억 연환산 + 영구 운영수수료 수취권 |

### Ledger Totals

- 총 TR 블록 수: **70**
- no-cider 블록 수: **0**
- no-cider 블록 번호: **(없음)**
- 최장 no-cider 연속 길이: **0**
- 1차 키워드 스캔 false-positive: `#14`, `#29`, `#57` (재읽기로 모두 cider 확정 — power_shift + reldelta + reward 권한 회수가 on-page에 명시됨; 어휘만 다른 케이스)

## Active Cap Rules

- **none**

이유: P0 6/6 통과, no-cider 블록 0개, 최장 무사이다 드라우트 0, mandatory_lexicon/role_fit_constraints/forbidden_flattenings 위반 적발 없음. YELLOW ceiling 트리거(no-cider 1블록) 미발생.

## P1 Score Table

채점 표준: spec v1 §5 `P1 Score Axes`. 10 axes × `0/1/2`, 총점 만점 **20**. 각 축의 0/1/2 정의는 spec v1 §5 표를 그대로 사용한다. WG `admiration_axes`/`protagonist_evaluation`은 근거 보강용으로만 인용.

| # | Axis (spec v1 §5) | Score | 근거 (TR 절대 블록 번호 + WG/BI 앵커) |
| --- | --- | --- | --- |
| 1 | protagonist innocence | **2** | `#1` 카드 잘림은 노현주 유언 집행 + 가문 정치 (acceptable list 중 `political sacrifice` + `inherited bad frame`); 게으름·자초 붕괴 0건. 명백히 defendable. |
| 2 | protagonist-only proof clarity | **2** | `#2` 회귀 기억 + 의전팀 동선표 + 냉장창고 재고 90분 응급 배식; `#4` 꽃집 4곳 영수증 분리 발행권을 외부 자금 없이 즉석 계약화. 다른 인물로 swap 불가. WG `protagonist_weapon` 3종 in-frame. unmistakably protagonist-only. |
| 3 | evaluation revision visibility | **2** | `#2` 한유림(`observer_tiers[1]` 등가) 첫 인정, `#3` 서도윤(`observer_tiers[2]`, 가장 무거운 weight) 인식 전환, `#4` 윤석진(`observer_tiers[3]`) 당혹. 셋 다 explicit + weighted. |
| 4 | visible reward token strength | **2** | `#3` 관제권 48시간(authority shift), `#4` 영수증 분리 발행권(approval/ownership), `#5` 셔틀 노선 3개 운영권 + 세탁 공장 설비 접근권(ownership + entry ticket), `#6` 비서실 시스템 증거 예치(report line). spec §4.1 blockguide 토큰 카탈로그 다수 동시 적중. concrete with force. |
| 5 | block1 → block2 linkage | **2** | `#5` 셔틀 노선 3개 + 세탁 공장 설비 접근권은 `#11`~`#15` 호텔 BOH(린넨실·셔틀)의 직접 발판; `#10` 호텔 BOH 진입 입장권 confirmation은 spec §2.1 허용 범위(downstream confirmation, retroactive supply 아님). clean next-gate opening. |
| 6 | rational opposition | **2** | WG `role_fit_constraints` 위반 0건. `#3` 서도윤 = 장남 정치 게임(체면), `#4` 윤석진 = CFO 사후 정산 통제(이전 시대 정답), `#56` 백도현 = 사모펀드 경쟁 합리. cartoon 0건, incentive-driven + era-valid. |
| 7 | domain truth density | **2** | 반복매출·정산 레인·구매 코드·발주 주기·폐기율·가동률·BOH·매출채권 팩토링·공급망 대출 원장 — 운영비 흐름 도메인 진실이 엔진을 직접 굴림. 다른 lane(투자물·시장 매매물)로 swap 불가. WG `forbidden_flattenings` "단일 generic operations 평탄화" 위반 0건. |
| 8 | repeatable loop clarity | **2** | 4-step loop (누수 감지 → 소액/즉시 개입 → 반복매출 포지션 + 권한 회수 → 다음 전장 입장권)이 `#2`/`#10`/`#20`/`#30`/`#40`/`#50`/`#60`/`#70`에서 동일 형태로 8회 반복. visible and reusable. |
| 9 | BI amplification power | **1** | WG `tracking_slots` 0→12→38→76→154억→전국망 그래프가 TR 자본 트랙(`#1` 0.0억 → `#70` 100억+)과 1:1 대응; WG `observer_tiers`/`role_fit_constraints`가 TR 적대축 비-캐리커처 채점 grammar 제공. 단 본 감리는 BI `MasterBible` 본문을 직접 인용하지 않고 WG anchor 우회로 추정한 부분이 있어 보수적으로 `1 = some amplification`으로 둔다 (BI 본문 직접 검증 시 `2` 진입 가능, 본 패스에서는 미수행). |
| 10 | blockwise cider continuity | **2** | 70/70 cider, no-cider 0, longest drought 0. 1차 키워드 스캔의 `#14`/`#29`/`#57` flagged-block reread는 모두 on-page 권한 회수 + 적대축 통제권 축소가 명시되어 cider 확정 (재사용 evidence). spec §5 최고 정의 "every block lands a felt receipt" 충족. |

**P1 총점: 2+2+2+2+2+2+2+2+1+2 = 19 / 20.**

Cap rules check (spec v1 §6) — 모두 미발동:
- no first-block cider: 미발생
- first concrete token at TR `#7+`: 미발생 (`#3`에서 이미 token 착지)
- any no-cider block in full-block scan: 미발생
- rewardless pain blocks 2 in a row: 미발생
- no-cider drought 6+: 미발생 (drought=0)
- major defeat without next card: 미발생 (`#4`/`#5` 자본 감소도 동일 블록에 권한 token 동반)
- BI summary echo only: 미발동 (axis 9에서 1점 처리했으나 echo-only 수준은 아님 — grammar 제공 인정)
- early reward asset-only: 미발동 (`#3` 관제권·`#4` 발행권·`#5` 운영권 모두 status/authority shift 동반)
- stupid opposition wins: 미발동
- domain generic swap: 미발동
- protagonist passive arc: 미발동

§7 RED triggers 미발동 (P0 6/6, loop 명확, 후반 reward cadence 유지).

## Provisional Grade

**GREENPLUS**

spec v1 §8.1 `GREENPLUS` 요건 점검:

| 요건 (§8.1) | 충족 여부 | 근거 |
| --- | --- | --- |
| all P0 hard gates pass | ✓ | 본 보고서 P0 Hard Gates 6/6 PASS |
| no YELLOW ceiling rule triggered | ✓ | §6 cap rules 전부 미발동 (위 점검) |
| total score 17~20 | ✓ | P1 = **19 / 20** |
| block 1 = exemplar of `proof → reevaluation → reward → next gate` | ✓ | `#2` proof → `#2/#3/#4` reevaluation → `#3/#4/#5/#6` reward → `#5` token이 `#10` confirmation으로 호텔 BOH 게이트 개방 |
| full-block cider scan = zero no-cider blocks | ✓ | 70/70, no-cider=0, drought=0 (Full-Block Cider Scan 섹션 재사용) |
| later reward cadence still feels intentional | ✓ | `#10/#20/#30/#40/#50/#60/#70` 매 ARC exit마다 입장권 + 권한 1종 + 자본 단조 상승 |

§8.2 GREEN 진입 요건도 동시에 충족하지만, P1 총점이 GREENPLUS 밴드(`17~20`) 안에 들고 GREENPLUS 6개 요건이 모두 충족되므로 spec §8 grade decision table 우선순위에 따라 **GREENPLUS로 확정**한다. 직전 evidence scouting pass에서 보수적으로 GREEN 고정했던 판정은 본 spec v1 재채점으로 무효화한다.

## Top 3 Repair Units or Alias Note

spec v1 §10 절차상 GREENPLUS이므로 repair unit 대신 alias update note + residual risk를 남긴다.

### Alias Update Note

- `pair_02 = chaebol_allowance_zero`를 `production_pair_grade_aliases/`의 **GREENPLUS 후보**로 승급 제안한다 (직전 GREEN 고정 무효화).
- spec v1 §9 `Current Benchmark Exemplars`에 등재 가능한 후보 슬롯:
  - **first-block conversion benchmark** (현재 `office_checkup_next_day`)와 동급으로 인용 가능: `#2/#3/#4/#5/#6` 5블록이 proof → reevaluation → token → next-gate linkage 사슬을 strict window 안에서 모두 마무리.
  - **authority-ticket benchmark** (현재 `pantech_cyworld_reborn`)와 보완 슬롯: `#3` 관제권 → `#5` 운영권 → `#10` 호텔 BOH 입장권 → `#50` 중앙 정산망 이양 → `#70` 영구 운영수수료 수취권의 권한 사슬.
- 다른 blockguide 페어 P0 채점 시 본 페어의 5-블록 anchor template(`#2`/`#3`/`#4`/`#5`/`#6`)을 strict window 비교 기준으로 사용 가능.

### Residual Risk (GREENPLUS 등재 전 closer 감리에서 추가로 봐야 할 항목)

1. **BI MasterBible 본문 직접 검증 미수행**: P1 axis 9를 보수적으로 1점 처리한 사유. BI 본문 직접 인용 패스가 추가되면 axis 9가 2점이 되어 P1 = **20/20** 만점 진입 가능. GREENPLUS 등급 자체는 변하지 않지만 등재 권장도가 상승.
2. **인물 자율성 후반 침식 가능성**: `#56`~`#70` 금융 ARC에서 노현주·정채린·민가온의 자율 결정 면이 "지원자" 지위로 굳을 가능성. spec v1 §6 `protagonist passive arc` 캡 트리거 직전까지는 가지 않으나, 별도 캐릭터 자율성 감리에서 재확인 권장.
3. **`#56`~`#60` 규제 우회 디테일 두께**: `#60` 금감원 검토 통과 표현이 TR 한 줄. 본 spec v1 채점에는 영향 없으나 production 단계 신뢰도 마진 차원의 관찰.

(repair 항목 아님 — full-wave surgery 오더 발주 금지, GREENPLUS 등재 전 closer 감리용 관찰 사항으로만 기록.)

## Concise Rationale

`pair 02`는 spec v1 재채점에서 **P0 6/6 PASS, P1 19/20, no-cider 0/70, drought 0, cap rule 미발동**으로 spec v1 §8.1 GREENPLUS 6요건을 모두 충족했다. strict window `TR blocks 2~6` 안에서 proof(`#2` 회귀 기억 + 의전팀 동선표 + 90분 응급 배식) → weighted reevaluation(`#2` 한유림 / `#3` 서도윤 / `#4` 윤석진) → concrete token(`#3` 관제권·`#4` 발행권·`#5` 운영권·`#6` 증거 예치) → next-gate linkage(`#5` 셔틀+세탁 라인이 호텔 BOH의 직접 발판이고 `#10`이 spec §2.1 허용 범위의 confirmation 역할만 수행) 사슬이 retroactive supply 없이 닫혔으며, BI/WG one_line_truth가 TR `#1`~`#3`에 1:1로 alive하다(gate 6 PASS). Full-block cider scan은 70/70 cider, 1차 키워드 스캔에서 잡힌 `#14`/`#29`/`#57`는 재읽기 evidence(권한 회수 + 적대축 통제권 축소가 on-page에 명시)로 모두 회수됐다. P1에서 axis 9(BI amplification power)만 BI MasterBible 본문 직접 검증 미수행을 사유로 보수적으로 1점 처리해 19/20이 됐고, 이 한 점은 GREENPLUS 밴드(`17~20`) 안에 머무르므로 등급 변동을 일으키지 않는다. 직전 evidence scouting pass의 4-gate / 8-axis / 5점 척도 GREEN 판정은 본 재채점으로 무효화한다.

read-only true benchmark audit complete; no pair files mutated
