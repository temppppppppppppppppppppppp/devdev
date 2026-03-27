# fallen_prince_buys_joseon Pair Consumability Survey

Date: 2026-03-27
Type: bounded consumability survey (ladder Step 1)
Target pair:
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json`
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`

---

## 1. Pair Admission

| Check | Result |
|-------|--------|
| TR JSON parse | **PASS** |
| BI JSON parse | **PASS** |
| TR block count | 70 |
| BI MasterBible top keys | 9 (ProjectData, protagonist_config, FinanceHUD, WorldState, AssetLibrary, Seeds, HistoricalEvents, GenreRules, plot_roadmap) |
| Pair identity | `fallen_prince_buys_joseon` — BI CoreIdentity.protagonist=이강윤, FinanceHUD.name=이강윤, TR pov_character=이강윤 (일관) |
| UTF-8 integrity | **PASS** |

**Pair admission: PASS**

---

## 2. BI Standalone Roadmap Readiness

| Check | Result |
|-------|--------|
| `plot_roadmap` exists | Yes (70 entries) |
| `block_no` present | **0/70** — 전부 누락 |
| Title sync TR↔BI (Block 1-10) | **PASS** (10/10 일치) |
| Roadmap entry key set | 15 keys per entry (block_id, title, content, stakes, power_shift, relationship_delta, foreshadow, callback, emotional_beat, tension_level, pov_character, location, time_span, genre_ext, regression_ext) |

**BI roadmap readiness: FAIL** — `block_no` 전무. Stage 2 preflight에서 `block_no`를 읽으므로 promotion blocker.

---

## 3. Runtime Protagonist Keys

| Key | Status |
|-----|--------|
| `protagonist_config.name` | **MISSING** |
| `protagonist_config.world_origin` | OK (현대인) |
| `protagonist_config.incarnation_type` | OK (회귀자) |
| `protagonist_config.pov` | **MISSING** |
| `protagonist_config.external_pov_insert_policy` | **MISSING** |
| `protagonist_config.regression_mechanic` | **MISSING** |
| `protagonist_config.regression_point` | Present but incorrect — `return_year: 2006` (should be 1907), `return_context: "사업/승계 의사결정 직전"` (generic boilerplate) |

Protagonist name consistency:
- CoreIdentity.protagonist: 이강윤
- FinanceHUD.name: 이강윤
- protagonist_config.name: **MISSING**

**Protagonist keys: FAIL** — 4 keys missing, 1 key with incorrect value. Multiple promotion blockers.

---

## 4. Embedded Roadmap Warnings

### 4.1 BI Density Gaps

| Section | Status |
|---------|--------|
| FinanceHUD.total_assets | `"초기 설정 필요"` — placeholder |
| FinanceHUD.liquid_cash | `"초기 설정 필요"` — placeholder |
| FinanceHUD.stocks | `[]` — empty |
| FinanceHUD.inventory | `[]` — empty |
| FinanceHUD.portfolio_history | **absent** |
| NPC descriptions | **1 unique out of 9** — all identical boilerplate `"블록 진행 과정에서 관계 변화가 누적되는 핵심 인물"` |
| NPC arc_summary | **absent** |
| NPC suspicion_count | **absent** |
| NPC key_blocks | **absent** |
| Seeds | 10 entries, all `echo_count: 0` — no resolution tracking |
| WorldState.MacroContext | **absent** |
| WorldState.KarmaMatrix | `{}` — empty |
| ArcStructure | **absent** |
| OpponentTransitionPlan | **absent** |
| BackHalfTechIdentityAnchors (equivalent) | **absent** |
| PayoffTrack | **absent** |
| CommercialCode detail | 3 generic fields, no `reader_hook` or `vicarious_satisfaction` |

**BI is a thin auto-generated echo.** 구조적 보강(BI repair) 없이는 Stage 2 이상 진행 불가.

### 4.2 TR Template Repetition (Skeleton Indicators)

| Pattern | Frequency |
|---------|-----------|
| event_villain contains `"주도권을 넓히기 전에"` | **70/70** |
| event_villain contains `"문서와 인허가, 가격표를 먼저 잠그려 든다"` | **70/70** |
| solution contains `"자신에게 유리한 순서로 재배치한다"` | **70/70** |
| stakes contains `"쪽으로 넘어간다"` | **70/70** |

모든 블록의 event_villain, solution, stakes가 동일 문장 템플릿으로 채워져 있음.

### 4.3 TR Content Length Uniformity

| Field | Min | Max | Avg | Stdev |
|-------|-----|-----|-----|-------|
| context | 104 | 157 | 126 | 13 |
| solution | 135 | 184 | 155 | 10 |

Stdev이 극히 낮음 — 템플릿 채우기의 전형적 신호. pantech_cyworld_reborn의 context stdev 42와 비교하면 1/3 수준.

---

## 5. Contract Field Coverage (Block 1-10)

| Check | Result |
|-------|--------|
| All 14 required block fields present | **PASS** (10/10 blocks) |
| content sub-fields (context, event_villain, solution, reward) | **PASS** (10/10 blocks) |
| genre_ext present | **PASS** (10/10) |
| regression_ext present | **PASS** (10/10) |
| genre_ext.source_binding present | **PASS** (material_bank.db AH-* 소스 바인딩) |
| genre_ext.historical_event present | **PASS** (역사 이벤트 매핑) |

**Field coverage: PASS** — 모든 필드가 존재하지만, 내용이 템플릿 채우기.

---

## 6. Schema Drift Check

| Check | Result |
|-------|--------|
| BI top-level keys within expected range | **PASS** (9 baseline keys, 0 additive) |
| No corrupted nested structures | **PASS** |
| JSON value types valid | **PASS** |
| regression_point year | **DRIFT** — `return_year: 2006` (should be 1907 per work setting) |
| MetaInfo.grand_objective | **DRIFT** — Block 70 stakes 문장이 그대로 복사됨 ("이번 실소유주 선언에서 밀리면...") |
| WorldState.CurrentEra | **DRIFT** — `"2006년 시작"` (should be 1907) |

**Schema drift: minor structural drift in 3 fields** — template generation이 work-specific 값을 주입하지 못한 흔적.

---

## 7. Skeleton Risk Preliminary Assessment

### 7.1 What Works (skeleton이 아닌 부분)

1. **Title diversity**: 70/70 unique titles — "피 맛과 계약서", "거울 속 열일곱", "금고 열쇠", "헤이그의 잔금" 등 제목 수준의 변주는 존재
2. **deal_type diversity**: 70/70 unique — "회귀 후 자산 선점 선언", "궁중 동선 은닉", "금고 분리 확보", "밀사 경로 전용" 등
3. **Location diversity**: 69/70 unique — "경운궁 침전", "내장원 복도", "인천항 하역 부두" 등
4. **Historical event mapping**: 각 블록에 역사 이벤트가 매핑됨 (헤이그 특사, 정미7조약, 합방 등)
5. **source_binding**: material_bank.db AH-* 소스 6개가 블록별로 바인딩됨
6. **Foreshadow cross-references**: 블록 간 구체적 번호 참조 존재 ("Block 69에서 취리히 독살", "Block 3의 금고 열쇠는 Block 68까지")
7. **Capital trajectory**: 4억 → 1조6,400억, deal_type별 변주 존재
8. **Relationship delta**: 99개 delta, 9 unique targets, 분포 합리적 (소피 아들러 24, 윤창식 19, 한예담 14)

### 7.2 What Is Skeleton (기계적 반복)

1. **event_villain 100% 템플릿**: 70/70 블록이 `"X은 강윤이 Y로 황실 자산 주도권을 넓히기 전에 문서와 인허가, 가격표를 먼저 잠그려 든다"`
2. **solution 100% 템플릿**: 70/70 블록이 `"~를 구조화하고, ~ 쪽 문서를 자신에게 유리한 순서로 재배치한다"`
3. **stakes 100% 템플릿**: 70/70 블록이 `"이번 X에서 밀리면 ~ 전체가 흔들리고, ~ 병목은 Y 쪽으로 넘어간다"`
4. **Content length uniformity**: context avg 126 stdev 13, solution avg 155 stdev 10 — 템플릿 slot-fill
5. **Opponent diversity low**: 11 unique opponents / 70 blocks — 적대자 회전이 매우 제한적
6. **Context depth absent**: 구체적 오브젝트, 촉각 디테일, 대화 마커가 Block 1-10에서 거의 없음

### 7.3 Skeleton Risk Rating

**HIGH**

TR은 **뼈대(deal_type, title, location, historical_event, foreshadow cross-ref, capital trajectory)**는 살아 있지만, **살(event_villain, solution, stakes, context depth)**은 100% 템플릿이다. pantech_cyworld_reborn의 TR과 비교하면:

| Metric | pantech_cyworld_reborn | fallen_prince_buys_joseon |
|--------|----------------------|--------------------------|
| Context stdev | 42 | 13 |
| Solution template repetition | 0/70 | 70/70 |
| event_villain template | 0/70 | 70/70 |
| Opponent unique | 68/70 | 11/70 |
| deal_type unique | 28/70 | 70/70 |
| Foreshadow resolution | 60% (82/137) | Unknown (echo_count 0) |

결론: **뼈대를 살릴 수 있지만, 살은 전면 재작성이 필요**. 이는 BI repair(Step 3) 수준이 아니라, TR static audit(Step 2) 후 판정이 "consumable but skeleton-likely" 또는 "regenerate TR first"가 될 가능성이 높음.

---

## 8. Overall Consumability Verdict

**PASS WITH WARNINGS**

Pair는 소비 가능(JSON parse, field coverage, title sync 모두 pass)하지만 다음 blocker들이 존재:

### Promotion Blockers (consumability repair 필요)

1. `plot_roadmap.block_no` 전무 (0/70)
2. `protagonist_config.name` 누락
3. `protagonist_config.pov` 누락
4. `protagonist_config.external_pov_insert_policy` 누락
5. `protagonist_config.regression_mechanic` 누락
6. `protagonist_config.regression_point.return_year` 오류 (2006 → 1907)
7. `WorldState.CurrentEra` 오류 ("2006년 시작" → 1907)
8. `MetaInfo.grand_objective` Block 70 stakes 복사 오류

### Structural Issues (BI repair / TR audit에서 처리)

1. BI는 thin auto-generated echo — NPC boilerplate, FinanceHUD placeholder, 구조적 섹션 부재
2. TR은 HIGH skeleton risk — event_villain/solution/stakes 100% 템플릿
3. TR opponent diversity 극히 낮음 (11/70)

---

## 9. Next Unit Recommendation

**consumability repair** — 위의 promotion blocker 8개를 최소 패치로 해소.

Repair 범위:
1. `plot_roadmap`에 `block_no` 추가 (70개)
2. `protagonist_config`에 `name`, `pov`, `external_pov_insert_policy`, `regression_mechanic` 추가
3. `protagonist_config.regression_point.return_year` → 1907 수정
4. `WorldState.CurrentEra` → "1907년 8월 ~ 1936년" 수정
5. `MetaInfo.grand_objective` → work에 맞는 문장으로 교체

Repair 후 next: **TR static audit** (Step 2) — skeleton risk HIGH이므로 "regenerate TR first" 판정이 나올 가능성을 미리 인지할 것.

---

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: pair consumability survey
changed_files: docs/2026-03-27/fallen-prince-pair-consumability-survey.md
next_unit: consumability repair
stop_reason: survey complete — pair consumable but 8 promotion blockers found, HIGH skeleton risk confirmed
```
