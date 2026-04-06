# Lane 1 — Pairs 01, 02 TR/BI Consistency Audit

Date: 2026-04-06
Lane: 1
Assigned Pairs: 01, 02
Auditor: Terminal 1
Family Overlay: blockguide (both pairs)
Mode: read-only bounded audit

---

## Pair 01: 투자물_골든_카나리아 테스트

### Verdict: `clean`

### Severity Summary

| Axis | Result |
| --- | --- |
| Artifact Truth | pass |
| Pair Identity Truth | pass |
| Core Narrative Truth | pass |
| Late-Pair Carry | pass |
| Family Overlay Truth | pass |

### Findings

1. **Artifact truth — pass**
   - TR: `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json` exists, UTF-8 decode OK, JSON structure valid, `_schema: "tr.v1"`, `_total_blocks: 60`, blocks array present with Block 1 ~ Block 60
   - BI: `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json` exists, UTF-8 decode OK, JSON structure valid, `_schema_version: "2.1"`, MasterBible structure present

2. **Pair identity truth — pass** `P3 naming noise only`
   - Same numbered pair `01`
   - Same protagonist: `한시우`
   - TR file slug: `투자물_골든_카나리아 테스트`, BI title: `골든 루트 (가제)` — naming divergence is cosmetic (`카나리아 테스트` is the test-run label, `골든 루트` is the in-story title). Both refer to the same work.
   - `BI: CoreIdentity.protagonist` = `한시우`, `TR: blocks[0].pov_character` = `한시우`

3. **Core narrative truth — pass**
   - Protagonist desire/engine: TR Block 1 `한 번도 내 인생을 산 적이 없었다` → 20억→135조 투자 제국. BI `CoreIdentity.desire` = `남의 실패를 대신 갚지 않는 자기 제국을 만든다`. Aligned.
   - Growth resource: TR `genre_ext.capital` tracks 20억→135조 via event-driven trading. BI `FinanceHUD.financial_status.total_assets` = `135조`. BI `investment_style` = `이벤트 드리븐 + 출구 설계 + 통제권 우선`. Aligned.
   - Main antagonistic pressure: TR = 형들(한태준, 한태민)의 후계 싸움 + 시장 광기 + 외부 추적(김도윤). BI `KarmaMatrix` = 한태준(-85, 실패한 경쟁자), 한태민(-80, 무력화). Aligned.
   - Core premise/tone: 회귀 투자물, 냉정한 출구 설계자. TR `CommercialCode.attitude` and BI `CommercialCode.attitude` both = `도덕 딜레마보다 이득과 통제권을 우선하는 냉정한 회귀 투자자`. Exact match.

4. **Late-pair carry — pass**
   - TR Block 60 `골든 루트`: 135조 운용권을 가족 신탁 + 운용 헌장으로 봉인. 가족과 새해, 마이클에게 회귀 비밀은 끝내 미공개.
   - BI `final_goal` = `반복되는 몰락을 끊고, 누구도 조건 없이 건드릴 수 없는 통제권을 만든다`. BI `portfolio_history` 마지막 entry = `block 60, 135조, 골든 루트`.
   - BI가 TR의 endgame 방향(통제권 봉인 + 가족 화해)을 정확히 반영함.

5. **Family overlay truth (blockguide) — pass** `P3 minor`
   - `BI: FinanceHUD` 구조 완비. `mobilizable_capital: 127조`, `total_assets: 135조`, `business_lines` 10개 라인 (원자재→패밀리오피스).
   - `BI: company_state` = `가족 자산과 분리된 135조 운용 체계`. TR Block 60 `solution`과 일치.
   - TR `section_rotation` ARC-01~06. BI `section_rotation` 동일 6개 ARC. 아크 구조 정합.
   - `P3`: BI에 `MartialHUD` 섹션 존재 — `_alias_note: "main_a.py 호환용"`. 런타임 호환 alias이며 의미 충돌 없음.

### One-line next-step suggestion

- 파일명 slug `카나리아 테스트` → 작품 타이틀 `골든 루트`로 정리하면 naming noise 해소.

---

## Pair 02: chaebol_allowance_zero

### Verdict: `clean`

### Severity Summary

| Axis | Result |
| --- | --- |
| Artifact Truth | pass |
| Pair Identity Truth | pass |
| Core Narrative Truth | pass |
| Late-Pair Carry | pass |
| Family Overlay Truth | pass |

### Findings

1. **Artifact truth — pass**
   - TR: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` exists, UTF-8 decode OK, JSON structure valid, `_schema: "tr.v1"`, `_total_blocks: 70`, `_work_id: "chaebol_allowance_zero"`, blocks array Block 1 ~ Block 70
   - BI: `bible/02_bi_chaebol_allowance_zero.json` exists, UTF-8 decode OK, JSON structure valid, `_schema_version: "2.0"`, `_work_id: "chaebol_allowance_zero"`, MasterBible structure present
   - 양쪽 모두 동일한 `_authority_chain` 공유 (BI가 TR을 chain 마지막 항목으로 포함)

2. **Pair identity truth — pass**
   - Same numbered pair `02`
   - Same protagonist: `윤재이`
   - Same work_id: `chaebol_allowance_zero`
   - Same title: `재벌 3세인데 용돈이 0원`
   - `BI: CoreIdentity.protagonist` = `윤재이`, `TR: blocks[0].pov_character` = `윤재이`
   - `BI: protagonist_faction` = `제로라인파트너스 (오너가 3세)`, TR Block 1에서 `제로라인파트너스(자본금 500만원)` 등장. 일치.

3. **Core narrative truth — pass**
   - Protagonist desire/engine: TR Block 1 = 유언장 7항으로 카드 잘린 뒤 운영권 선점. BI `CoreIdentity.desire` = `장례 특수 구간 안에서 첫 월 반복매출을 증명하고, 형 서도윤과 재무실이 윤재이를 다시 처음 보게 만든다`. 동일 엔진.
   - Growth resource: TR `genre_ext` = 운영권 조각 → 반복 현금흐름. BI `investment_style` = `상속보다 매일 나가는 돈의 길목을 먼저 쥔다. 계약권·승인권·정산권·현장 대체 불가능성을 한 칸씩 옮겨 오면 결국 회장실도 따라온다`. 정확히 일치.
   - Main antagonistic pressure: TR = 노현주(유언 집행), 서도윤(형), 최병태(외주 본부). BI `opponent_transition_plan` Phase 1 = 노현주 + 서도윤, Phase 2 = 윤석진 + 서도윤. 적대 구조 일치.
   - Core premise/tone: TR `genre_ext.type: "investment"` 표기이나 실질 내용은 support-system cashflow 장악물. BI `_genre` = `현대 한국 재벌 support-system cashflow × office power 복합 장악물 (투자물 아님)`. BI가 명시적으로 투자물이 아님을 선언. 이 genre label 차이는 TR의 호환 필드명(`investment`)과 BI의 정확한 장르 선언 사이의 의도적 분리이며, blockguide 0A/0C절의 호환 필드 재해석 규칙에 부합함.

4. **Late-pair carry — pass**
   - TR Block 70 `상속보다 센 돈줄`: 상속 포기 + 관문 선택, 연환산 154억 + 영구 수수료 수취권. Block 1 `유언장 7항 카드 차단`이 `상속 포기`로 정반대 의미 완성.
   - BI `final_goal` = `가문이 먼저 자기 현금흐름망·정산 레인·운영 인프라에 의존하는 구조를 고착시켜 상속보다 강한 지배권을 갖는다`. TR endgame과 정확히 일치.
   - BI `portfolio_history` 마지막 entry = `block 70, 100.0억+ (연환산 154억 포지션), 상속보다 센 돈줄`. TR Block 70과 수치/서사 일치.
   - BI `ARC-07` = `가문 역의존 / 현금흐름 지배구조`. TR Block 70 `section_rotation: "ARC-07 endgame - 엔딩"`. 완전 정합.

5. **Family overlay truth (blockguide) — pass**
   - `BI: FinanceHUD._description` = `Resource-Power HUD - 반복 현금흐름, 운영 자산, 정산권, 결재선 접근권, 가문 협상력 추적 (주식 평가액 아님)`. blockguide 0C절 `FinanceHUD = Resource-Power HUD` 재해석 규칙 정확히 반영.
   - `BI: hud_interpretation` 섹션에서 `capital`, `deal_type`, `resource_power_hud`, `business_lines`, `first_block_reward_rule` 명시적 재해석. blockguide 의미에 완벽 부합.
   - `BI: business_lines` = 장례 의전 ~ 영구 수수료까지 30+개 라인. TR의 블록별 확장 경로와 일치.
   - `BI: expansion_order_locked` = 장례(ARC-01) → 급식 → 호텔 BOH → 공장 → 병원 → 정산 → 전국 운영망(ARC-07). TR의 70블록 진행 순서와 정합.
   - `BI: opponent_transition_plan` = 3개 Phase (가문 법무 → 재무실 → 가문 역의존). TR 적대자 전환과 일치.
   - `P3`: `MartialHUD` alias 존재 — 런타임 호환용. 의미 충돌 없음.

### One-line next-step suggestion

- TR `genre_ext.type: "investment"` 필드값을 BI와 맞춰 `support_system_cashflow`로 변경하면 호환 필드 혼동 소지 해소 (단, blockguide 0A절 호환 규칙상 현행도 유효).

---

## Lane 1 Summary Table

| Pair | TR Blocks | BI Schema | Protagonist | Pair Verdict | Highest Severity | Key Finding |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | 60 | 2.1 | 한시우 | `clean` | P3 | 파일명 slug vs 작품 타이틀 naming noise |
| 02 | 70 | 2.0 | 윤재이 | `clean` | P3 | TR `genre_ext.type` 호환 필드명 vs BI 정확 장르 선언 차이 (의도적 분리, 유효) |

Both pairs are **pair-consistent**. No P0, P1, or P2 issues found. Both BIs materially amplify the protagonist engine and core conflict established by their TRs. Family-critical contract anchors (FinanceHUD, business_lines, company_state, expansion arc structure) remain aligned across TR and BI in both pairs.
