# Lane 2 — Pairs 03, 04 TR/BI Consistency Audit

Date: 2026-04-06
Lane: 2
Assigned Pairs: 03, 04
Family Overlay: blockguide (both)
Scope: read-only bounded audit — TR/BI pair consistency only

---

## Pair 03: chaebol_ent_empire

### Pair Verdict: **clean**

### Severity Summary

| Severity | Count | Note |
| --- | --- | --- |
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 0 | — |
| P3 | 2 | naming noise, minor metadata |

### Findings

1. **Artifact truth: PASS**
   - TR: `treatments/03_chaebol_ent_empire_tr_block_070_draft.json` — exists, UTF-8 OK, JSON parses, `_schema: tr.v1`, `_total_blocks: 70`
   - BI: `bible/03_bi_chaebol_ent_empire.json` — exists, UTF-8 OK, JSON parses, `_schema_version: 2.1`

2. **Pair identity truth: PASS**
   - Both files clearly represent the same work: "쓰레기통 상속" (권태하 + 세령컬처웍스 엔터 empire)
   - TR: `protagonist_config → is_regressor: false`, `name: 권태하`
   - BI: `protagonist_config → is_regressor: false`, `name: 권태하`, `incarnation_type: 일반인`
   - BI repair note explicitly confirms 회귀자→비회귀 정정 완료 (2026-03-27)

3. **Core narrative truth: PASS**
   - Protagonist engine aligned: TR Block 1 `스타 감지` (선천적 감각) = BI `CoreIdentity.edge` 동일
   - Desire aligned: TR `인정이 아니라 표준` (Block 70) = BI `grand_objective: 남들이 결국 따라 하게 되는 구조`
   - Growth resource: TR `120억 → 6800억` capital arc = BI `FinanceHUD.portfolio_history` 동일 궤적 (127억 → 6800억)
   - Main antagonistic pressure: TR 권도현/한도윤/백승문/마커스 리 = BI `KeyNPCs` 동일 인물 동일 역할

4. **Late-pair carry: PASS**
   - TR Block 63 경영권 탈취 → Block 68 시장 폭로 → Block 69 자체 플랫폼 → Block 70 산업 표준 확정
   - BI `portfolio_history` Block 63 (3200억, 경영권 탈취), Block 68 (5112억, 시장 폭로), Block 70 (6800억, 산업 표준)
   - BI `foreshadow_map` F-005 (비방송→팬덤 플랫폼), F-006 (한도윤 장부→폭로) 모두 harvested 상태로 late-block 회수 반영
   - BI `opponent_transition_plan` 존재, ARC-01부터 구간별 적대축 전환 명시

5. **Family overlay truth (blockguide): PASS**
   - BI `_genre: entertainment_media`, `genre_profile_primary: entertainment_media_profile`, `genre_profile_secondary: business_growth_profile` — blockguide 프로파일 적합
   - BI `FinanceHUD` — Resource-Power HUD로 자본·팬덤·IP자산·영향력 추적, 실수치 포함 (120억→6800억)
   - BI `business_lines` — 아이돌/배우/스트리머/F&B/팬덤커머스/글로벌 투어 7개 라인 명시
   - BI `company_state` — 스타 IP 대기업 상태 명시

6. **P3: minor naming noise** (severity P3)
   - TR `genre_ext.type` 전 블록 `"investment"` 유지 — blockguide 0A 호환성 불변조건 범위이므로 pair mismatch 아님. 다만 BI의 `entertainment_media` primary와 키 이름 차이 존재
   - BI `npc_timeline`에서 강이현 `active_blocks: 1-60`으로 표기되어 있으나, TR에서는 Block 51-58까지 ORBIT 핵심으로 활발히 등장 후 Block 59-70 구간에서는 직접 등장 빈도 감소 — 범위 표기 자체는 정확

**Next-step hint**: genre_ext.type 호환 키를 BI primary profile과 일치시키는 것은 코드/시스템 단의 호환성 작업이며, 현재 pair consistency에는 영향 없음.

---

## Pair 04: defense_defect_engineer

### Pair Verdict: **clean**

### Severity Summary

| Severity | Count | Note |
| --- | --- | --- |
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 0 | — |
| P3 | 2 | minor metadata, arc_section gaps |

### Findings

1. **Artifact truth: PASS**
   - TR: `treatments/04_defense_defect_engineer_tr_block_070_draft.json` — exists, UTF-8 OK, JSON parses, `_schema: tr.v1`, `_total_blocks: 70`, `_work_id: defense_defect_engineer`
   - BI: `bible/04_bi_defense_defect_engineer.json` — exists, UTF-8 OK, JSON parses, `_schema_version: 2.0`, `_work_id: defense_defect_engineer`

2. **Pair identity truth: PASS**
   - Both files: "밀린 막내아들은 방산을 독점한다" / 하준영 / 현무그룹 방산 계열
   - TR: `protagonist_config` 없으나 `regression_ext.incarnation_type: 회귀자`, `pov_character: 하준영` 전 블록 일관
   - BI: `protagonist_config.incarnation_type: 회귀자`, `protagonist_config.name` 없으나 `FinanceHUD.Protagonist.actual_truth.name: 하준영`
   - 동일 work_id, 동일 주인공, 동일 회귀자 설정

3. **Core narrative truth: PASS**
   - Protagonist engine: TR `결함선·비리선 판독 (붉은 선)` = BI `protagonist_config.special_talent.name` 동일
   - Desire: TR Block 1 `승계·규격 독점` + `안전은 명분` = BI `CommercialCode.success_device` / `execution_doctrine` 동일 문구
   - Growth resource: TR `개인 영향 지분 1.4% → 19.6%` + 10대 전장 = BI `FinanceHUD.portfolio_history` (1.4%→2.6%→4.8%→6.7%→8.9%→11.2%→13.7%→19.6%) + `GenreRules.resource_axis` 10축 동일
   - Main antagonistic pressure: TR 하성우/민태수/윤문희/DDTC = BI `npc_timeline` 하성우(장남주적), 민태수(CFO쿠데타), 윤문희(계모여론전) 동일

4. **Late-pair carry: PASS**
   - TR Block 68 ITAR 예외허가 1차 배치 통과 → Block 69 후계 지분 스왑 (15.8%→19.6%) → Block 70 "준영 없는 방산" 공식 확인
   - BI `plot_roadmap` Block 69 (19.6%, 후계 지분 스왑·가문 거부권·방산 실질 후계 공개 고정) — TR과 완전 일치
   - BI `FinanceHUD.portfolio_history` 최종 entry: Block 69, 19.6% — TR Block 70 최종 지분과 일치
   - BI `control_axis` 4축 ("준영 없는 한국 방산이 못 굴러가는 상태") — TR Block 70의 결론과 정확히 대응
   - BI `payoff_axis` 6축 (지분 확대/규격 장악/정비권 독점/수출 현금흐름/승계 명분/적대자 무릎) — TR 전 블록 보상 패턴과 일치

5. **Family overlay truth (blockguide): PASS**
   - BI `GenreRules.primary_profile: business_growth_profile` — 방산 운영권·규격·납품·수출이 주 전장, 적합
   - BI `GenreRules.selection_rationale` — investment_market 부적합 근거 명시, business_growth 선택 이유 설명
   - BI `FinanceHUD._description` — "시험권·규격권·정비권·수출금융 통제력 함께 보여주는 Resource-Power HUD"
   - BI `business_lines` — 시험평가/규격/복합재/수출/정비 5축, "회사 단위가 아니라 권한·규격·돈줄 단위로 분리" 명시
   - BI `hud_interpretation` — capital/deal_type/resource_power_hud/business_lines/company_state 전부 blockguide 호환 해석 포함
   - BI `do_not_fake` 11항목 — 방산 도메인 특유의 구체적 금기선 명시 (방사청 시험평가 루프, 규격 문구, ITAR 구조, 오프셋, SPV 등)

6. **P3: minor metadata gaps** (severity P3)
   - TR `plot_roadmap` 일부 블록의 `arc_section` 필드가 빈 문자열 (`""`) — Block 6, 7, 8 등 초반 일부. pair consistency에는 영향 없으나 런타임 arc 라우팅 시 참고 필요
   - BI `protagonist_config`에 `name` 필드 부재 — `FinanceHUD.Protagonist.actual_truth.name: 하준영`으로 커버되나 스키마 정합성 관점에서는 미비

**Next-step hint**: TR의 빈 `arc_section` 필드 보충은 TR 품질 개선 시 함께 처리 가능. BI `protagonist_config.name` 추가는 최소 패치.

---

## Lane 2 Summary Table

| Pair | TR exists | BI exists | Same work | Protagonist match | Engine match | Late-carry | Family overlay | Verdict | Max severity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 03 | Y | Y | Y | Y | Y | Y | Y | **clean** | P3 |
| 04 | Y | Y | Y | Y | Y | Y | Y | **clean** | P3 |

Both pairs are pair-consistent. No P0/P1/P2 issues found. Only minor P3 metadata noise in both cases.
