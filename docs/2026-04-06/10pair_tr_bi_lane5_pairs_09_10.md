# Lane 5 — Pairs 09 & 10 TR/BI Consistency Audit

Date: 2026-04-06
Lane: 5
Scope: read-only bounded audit — pairs 09, 10 only
Family overlay: wuxguide (pair 09), blockguide (pair 10)

## Assigned Pairs

| Pair | TR | BI |
| --- | --- | --- |
| `09` | `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` | `bible/09_bi_wuxia_heavenly_physician.json` |
| `10` | `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` | `bible/10_bi_jaebeol3se_loss_line.json` |

---

## Pair 09 — wuxia_heavenly_physician (wuxguide)

### Verdict: `clean`

### Severity Summary

- P0: 0
- P1: 0
- P2: 0
- P3: 1

### Findings

1. **Artifact truth — PASS**
   - TR: 70 blocks, valid JSON, UTF-8 OK
   - BI: `_schema_version: 2.0`, valid JSON, UTF-8 OK
   - BI `_source_tr` correctly points to `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json`
   - BI `_family: "wuxguide"` correctly declared

2. **Pair identity — PASS**
   - TR protagonist: 진소백(陳小白), 17세, 진가장 막내, 무공 자질 전무, 의원
   - BI `protagonist_config.name`: 진소백(陳小白) — identical
   - BI `MasterBible.ProjectData.CoreIdentity.protagonist`: 진소백 — identical
   - Work title: TR `title` field absent at root (blocks carry it via content), BI `MetaInfo.title`: 천의무쌍(天醫武雙) — consistent with TR Block 69 title "천의무쌍"
   - `_work_id`: `wuxia_heavenly_physician` in both

3. **Core narrative — PASS**
   - Protagonist engine: 의무일체(醫武一體) — 침술=무공. TR Block 1에서 첫 발현, Block 69에서 7침 완성. BI `CoreIdentity.true_strength`: 의맥(醫脈) — 일치
   - Growth axis: 침의→혈의→맥의→신의→의성→의신→천의 7단계. TR `martial_ext.realm_*` fields track this block-by-block. BI `MartialHUD.realm_history`: 70블록 전체 추적, TR과 일치
   - Antagonistic pressure: 독역 + 사파 독문(사마련) + 좌천명(흑막). TR에서 Block 10~69까지 전개. BI `FactionMap.rival_factions`: 독문/무림맹 암부/마교 — TR과 일치
   - Core premise: 독역(내공 높을수록 치명적) → 의원 가치 급상승. TR과 BI 모두 동일 전제 유지

4. **Late-pair carry — PASS**
   - TR Block 69: 칠성침법 7침 완성, 좌천명을 "치료"하여 승리 — BI `MartialHUD.realm_history` Block 69: "천의 완성 (100%, 7침)"
   - TR Block 70: 에필로그, 천하 유람, 의무일체 전수 — BI `MartialHUD.realm_history` Block 70: "천의 (100%, 무량)"
   - BI arcs ARC-07 "천의의 길" (blocks 61-70) correctly reflects TR endgame escalation
   - BI `internal_energy_curve`: B70 "무량" — TR Block 70 `martial_ext.internal_energy_after: "무량(無量)"` — 일치

5. **Wuxguide overlay — PASS**
   - `MartialHUD` present and complete: realm, internal_energy, martial_arts (6종), faction_status, equipment, jianghu_reputation — 전체 추적
   - No `FinanceHUD` pollution — blockguide semantics 미침투
   - Realm system: 7단계 경지 체계 정확
   - Faction/sect continuity: 진가장→무림맹 대의원→천하 유랑 의원 — TR과 BI 모두 추적
   - Jianghu reputation: TR `jianghu_reputation.after` fields → BI `jianghu_reputation.jianghu_title: "천의무쌍"` — 일치

6. **P3: BI Seeds — seed_block/payoff_block 비구체적** (minor)
   - BI `Seeds[*].seed_block`: 빈 문자열 `""`
   - BI `Seeds[*].payoff_block`: `"(단서)→(회수)→(완결)"` 형태로 구간만 기술, 구체 블록 번호 미기재
   - TR에는 해당 복선-회수가 블록 단위로 정확히 기재되어 있으므로 실질 불일치 아님
   - Anchor: `BI: Seeds[*].seed_block`, `BI: Seeds[*].payoff_block`
   - Next step: BI Seeds에 TR의 구체 블록 번호 backfill 권장

---

## Pair 10 — jaebeol3se_loss_line (blockguide)

### Verdict: `mixed`

### Severity Summary

- P0: 0
- P1: 0
- P2: 2
- P3: 1

### Findings

1. **Artifact truth — PASS (with note)**
   - TR: valid JSON, UTF-8 OK, **57 blocks** (Block 1~57)
   - BI: `_schema_version: 2.0`, valid JSON, UTF-8 OK
   - 파일명 `_tr_block_070_draft`이나 실제 블록 수는 57개

2. **Pair identity — PASS**
   - TR protagonist: 도진우, 28세, 도성그룹 전략금융실 말석
   - BI `CoreIdentity.protagonist`: 도진우 — identical
   - BI `CoreIdentity.edge`: 손실선 판독 — TR Block 1~4의 trigger set A 감지와 일치
   - `_work_id`: `jaebeol3se_loss_line` — BI에 명시
   - Work slug/title: BI `MetaInfo.title: "재벌 3세는 손실선을 먼저 읽는다"` — TR content와 일치

3. **Core narrative — PASS (blocks 1~57)**
   - Protagonist engine: 손실선 판독 → 권한 회수 → dual-lane (내부 방어 + 외부 공개 데이터 포지션). TR과 BI 일치
   - Growth axis: 말석→배석→서명→의결→총괄 + capital 0→200억+. TR Block 45~57에서 산업 레벨로 확장. BI `capital_curve`와 방향 일치
   - Antagonistic pressure: 도현석(사촌 형) — 무시→경계→본격 대응→전략적 공존. TR과 BI `opponent_transition_plan` 일치
   - ContaminationGuard: insider-trading 금지, dual-lane 혼선 금지 — BI에 명시, TR `genre_ext`에서 일관 준수 (모든 외부 데이터가 `공개` 표기)

4. **P2: TR 블록 수 부족 — BI 후반부 미반영**
   - TR: Block 57 "다음 파동"에서 종료 (ARC-04 중반)
   - BI arcs: ARC-05 "관제탑" (blocks 61-70) — 대응 TR 블록 없음
   - BI `capital_curve`: Block 59 "파일럿에서 정식 펀드 전환", Block 68 "최종 위기 방어 후 합산" — 대응 TR 블록 없음
   - BI `defeat_blocks`: [63, 67] — 대응 TR 블록 없음
   - 실질적으로 BI의 ARC-05 전체와 ARC-04 후반(Block 58~60)이 TR에 미반영
   - Anchor: `TR: blocks[] (57개)`, `BI: arcs[4] (ARC-05, block_range "61-70")`
   - Next step: TR Block 58~70 생산 필요. BI는 이미 해당 구간의 설계를 포함하고 있으므로 BI 수정 불필요

5. **P3: _sync_manifest.tr_block_count 오류**
   - BI `_sync_manifest.tr_block_count: 5` — 실제 TR 블록 수 57과 불일치
   - Anchor: `BI: _sync_manifest.tr_block_count`
   - Next step: 값을 실제 블록 수로 갱신 (현재 57, 최종 목표 70)

6. **Blockguide overlay — PASS**
   - Resource-Power HUD: `capital_curve` 7개 체크포인트, 0→리스크 체계 총괄
   - Operating arena: 도성그룹 → 산업 공급망 → 글로벌 리스크
   - Business domain: 배터리 공급망, 해상보험, 리스크 관리
   - TR `genre_ext` 필드: `capital_before/after`, `deal_type`, `leverage_used`, `business_sector` — 전 블록 일관 기재
   - No MartialHUD pollution — wuxguide semantics 미침투
   - `CommercialCode`: cider_point, success_device, attitude — BI에 명시, TR 전개와 부합

---

## Lane 5 Summary Table

| Pair | Verdict | P0 | P1 | P2 | P3 | Key Issue |
| --- | --- | --- | --- | --- | --- | --- |
| `09` | `clean` | 0 | 0 | 0 | 1 | BI Seeds에 구체 블록 번호 미기재 (실질 불일치 아님) |
| `10` | `mixed` | 0 | 0 | 2 | 1 | TR 57/70 블록 — BI ARC-05 전체 미반영 + sync_manifest 오류 |
