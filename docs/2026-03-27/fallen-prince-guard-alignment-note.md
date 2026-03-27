# Fallen Prince Guard-Alignment Note

Date: 2026-03-27
work_id: `fallen_prince_buys_joseon`
unit: `guard-alignment synthesis`
author: order-OPUS (coordinator)

---

## 1. Primary Runtime Guard

**`investment`**

Evidence (Sub-OPUS-A runtime truth ledger):

| Check | Status | Source |
|---|---|---|
| `profile_lock.primary_profile` | ✅ `investment_market_profile` | `profile_lock.json:2` |
| `BI._genre` | ✅ `investment` | `05_fallen_prince_buys_joseon_bi.json:5` |
| `BI.HUD root` | ✅ `FinanceHUD` | `05_fallen_prince_buys_joseon_bi.json:48` |
| survey verdict alignment | ✅ consistent | survey line 220: investment is current best-fit primary guard |

Note: survey frames investment-primary as "necessary under current system maturity" rather than "the work's sole genre truth." This is compatible — the runtime lane is investment because the system's investment protections (Stage 3 capital continuity, four-phase arithmetic advisory, manuscript financial-number checks) are materially stronger than alt-history protections. The semantic hybrid identity is preserved via overlay.

---

## 2. Mandatory Overlay Contract (`alt_history`)

Extracted by Sub-OPUS-B. Four axes:

### 2.1 AH-* Source-Manifest Discipline

- All 70 blocks tagged `type: alt_history_investment` with explicit source binding
- Core AH sources pinned: `AH-1905-1910-KR_ROYAL_ASSETS_EXILE-B01`, `AH-1907-1936-EU_FINANCE_PORTS-B01`, `AH-1910-1938-KR_COLONIAL_ASSET_TAKEOVER-B01`
- Support AH sources required: `AH-1900-1950-BANKING_FX-B01`, `AH-1900-1950-MARINE_INSURANCE-B01`, `AH-1900-1950-RAIL_INFRA-B01`
- Each block must cite exactly one source in `source` field — no free-floating narrative

### 2.2 1907-1938 Historical Timeline Anchoring

- Entry point locked: 1907-08-03, 취리히 호텔 → 경운궁 침전
- Knowledge scope: 1907~1938 대한제국 멸망 → 일제강점기 전시체제
- Mandatory event boundaries: 헤이그 특사(1907) → 정미7조약(1907.7) → 합방(1910.8) → 1차대전(1914-18) → 대공황(1929) → 중일전쟁(1937)
- No skip of documented crisis points

### 2.3 Joseon / Imperial / Colonial Institution Plausibility

- Institutional hierarchy: 궁내부 → 내장원 → 통감부 → 총독부 경제국
- 황실 자산 구조: 내장원 금고, 역둔토, 이동 가능 현금성 자산
- 통감부(1907-1910 재정 감시) / 총독부(1910+ 식민지 경제 통제) 제도적 분리
- Colonial asset takeover gates: 토지조사사업 등기, 철도·전기·항만 관할, 조선은행 결제선, 광업권 허가
- 외국인 소유권 조사·몰수 정책 as genuine blocking event

### 2.4 Social Class / Court Rank / Faction / Public Trust

- Protagonist position locked: "열일곱 황자" (17세 표면 / 30+ 내면)
- Access hierarchy by earned trust, not coincidence: 한예담 → 헨드릭 판데르벨트 → 소피 아들러
- Cumulative suspicion mechanics: slip_up_pattern 추적
- Power from 5대 병목 독점 (해운·보험·철도·은행·광산), not political backing
- 1938 final position = 채권자 지위, not 복위

---

## 3. Protected Live Artifact Assumptions

The following must NOT be changed by any worker before or during the next unit:

| Artifact | Field/Value | Why |
|---|---|---|
| `profile_lock.json` | `primary_profile = investment_market_profile` | runtime guard anchor |
| `05_fallen_prince_buys_joseon_bi.json` | `_genre = investment` | BI root truth |
| `05_fallen_prince_buys_joseon_bi.json` | `FinanceHUD` as HUD root | HUD routing |
| `source_manifest.json` | all AH-* source entries | overlay discipline |
| `genre_ext.type` | `alt_history_investment` | hybrid identity preservation |

---

## 4. Explicit Do-Not-Flip List

- ❌ `alt_history`를 primary runtime guard로 승격하지 마라 — runtime contract replacement 없이는 Stage 3 capital continuity packet, 4-phase investment arithmetic advisory, manuscript financial-number checks, investment runtime helper protection이 전부 탈락한다
- ❌ `JoseonHUD` 전환을 당연한 다음 단계처럼 서술하지 마라 — HUD root 전환은 런타임 가드 교체 비용을 수반한다
- ❌ 순수 현대 금융물로 평탄화하지 마라 — AH-* source binding, 1907-1938 타임라인, 조선/황실/식민지 골격이 소멸한다
- ❌ duplicate BI path (`05_bi_fallen_prince_buys_joseon.json`)를 surveyed live authority 위로 승격하지 마라

---

## 5. Final Verdict

**`pass`**

Rationale:
- 3/3 runtime truth checks confirmed (profile lock, BI genre, HUD root)
- survey verdict is consistent with artifact stack
- overlay contract is extractable and concrete across 4 axes
- no stop condition triggered
- no artifact contradicts surveyed authority

---

## 6. Next Unit

**`investment-primary arc1 densification`**

Rationale (Sub-OPUS-C):
- TR audit: spine 보존 가치 높음 (deal_type 70종, 역사 31년, source_binding 6개), but prose 100% 템플릿 → 서사 재작성 필수
- Densification order: Arc 1을 canary로 spine-보존 prose densification 실행 가능성 확인
- Guard alignment은 clean하므로 overlay-contract note only는 불필요, hybrid-guard patch proposal은 코드 스코프이므로 이번 서사 연속 트랙에서 제외
- 즉시 arc1 densification 진행 시 downstream BI repair 체인이 템플릿 오염으로부터 보호됨

---

## 7. Operating Sentence for Downstream Workers

> `fallen_prince_buys_joseon`의 primary runtime guard는 `investment`다. `alt_history`는 mandatory overlay contract로서 AH-* source discipline, 1907-1938 timeline anchoring, Joseon/imperial/colonial institution plausibility, social class/trust checks를 강제한다. 이 둘의 전복은 runtime contract replacement를 수반하므로, 다음 worker는 `investment-primary arc1 densification`을 overlay 의무 하에서 수행하라.

---

## 8. 3-Pass Self Audit

### Pass 1. Contract Alignment
- ✅ one work_id: `fallen_prince_buys_joseon`
- ✅ one bounded unit: `guard-alignment synthesis`
- ✅ no code edits
- ✅ no pair edits
- ✅ no duplicate survey expansion

### Pass 2. Operational Usefulness
- ✅ primary guard explicit: `investment`
- ✅ overlay contract explicit: 4-axis checklist
- ✅ next-unit singular and actionable: `investment-primary arc1 densification`
- ✅ live authority path fixed

### Pass 3. Integrity
- ✅ saved under `docs/2026-03-27/`
- ✅ UTF-8 only
- ✅ duplicate BI path not elevated

---

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: guard-alignment synthesis
changed_files: docs/2026-03-27/fallen-prince-guard-alignment-note.md
next_unit: investment-primary arc1 densification
stop_reason: clean pass — no stop condition triggered
```
