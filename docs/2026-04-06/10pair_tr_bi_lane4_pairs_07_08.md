# Lane 4 — Pairs 07, 08 TR/BI Consistency Audit

Date: 2026-04-06
Lane: 4
Assigned Pairs: 07, 08
Family Overlay: blockguide (both)
Audit Type: read-only bounded pair consistency audit
Order: `docs/2026-04-06/10pair_tr_bi_consistency_5lane_parallel_order.md`

---

## Pair 07: office_checkup_next_day

**TR**: `treatments/07_office_checkup_next_day_tr_block_070_draft.json`
**BI**: `bible/07_bi_office_checkup_next_day.json`

### Pair Verdict: `mixed`

### Severity Summary

| Severity | Count |
| --- | --- |
| P0 | 0 |
| P1 | 0 |
| P2 | 2 |
| P3 | 2 |

### Findings

**1. BI `FinanceHUD.financial_status` end-state mismatch (P2)**

- TR Block 70 `genre_ext.capital_after`: `Lv8 경영기획팀장 + 그룹 구조조정 TF 실무총괄 + 전략실/대표 보고 + 라인 선택권 + 조감 = 자연스러운 도구 + 다음 아침`
- BI `FinanceHUD.Protagonist.actual_truth.financial_status.mobilizable_capital`: 동일 문자열 그대로 복사
- BI `financial_status.company_state`: `사수 퇴사 후 혼자 남은 팀 막내, 잡무 담당, 인사평가 B0` — **Block 1 초기 상태가 Block 70 완료 시점에도 그대로 남아 있음**
- BI가 start-state와 end-state를 분리하지 않고 초기값을 최종 HUD에 고정한 구조적 드리프트
- Next step: BI `financial_status.company_state`를 Block 70 기준 end-state로 갱신

**2. BI `protagonist_config.incarnation_type` 오기 (P2)**

- TR: 시혁은 회귀자가 아니다. Block 2에서 건강검진 후 감각이 발현되는 현실밀착형 능력물
- TR `regression_ext.is_regressor`: 전 블록 `false`
- BI `protagonist_config.incarnation_type`: `회귀자`
- TR-BI 사이에 주인공 기원 분류가 직접 모순
- Next step: BI `incarnation_type`을 `현대인(비회귀)` 또는 `능력 발현형`으로 수정

**3. BI `KeyNPCs` 한시혁 중복 등재 (P3)**

- BI `AssetLibrary.KeyNPCs[0]`과 `KeyNPCs[1]` 모두 `name: 한시혁, role: 주인공`
- 첫 번째는 grand_objective 수준 서술, 두 번째는 block-level turning points 서술
- 기능 충돌은 없으나 중복이 pair 품질 인상을 낮춤
- Next step: 두 NPC 항목을 하나로 병합

**4. BI `MartialHUD` 존재 (P3)**

- BI에 `MartialHUD` 섹션이 포함되어 있으나 blockguide 작품에 무의미
- `_alias_note: main_a.py 호환용 alias`로 명시되어 있어 런타임 호환 용도
- 내용은 `FinanceHUD.Protagonist.actual_truth`의 부분 복사이며 의미 충돌 없음
- Next step: 런타임 호환이 불필요해지면 제거 가능. 현재는 무해

### One-line Summary

Pair 07은 동일 작품이며 주인공 엔진·적대 구조·7-arc 성장선이 TR-BI 간 정렬되어 있으나, BI `incarnation_type`이 `회귀자`로 잘못 기재되어 있고 `company_state`가 초기값에 고정되어 end-state를 반영하지 못하는 구조적 드리프트가 있다.

---

## Pair 08: pantech_cyworld_reborn

**TR**: `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json`
**BI**: `bible/08_bi_pantech_cyworld_reborn.json`

### Pair Verdict: `clean`

### Severity Summary

| Severity | Count |
| --- | --- |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 2 |

### Findings

**1. BI `_schema_version` 2.1 vs TR `_schema` tr.v1 — 스키마 명명 불일치 (P3)**

- TR: `_schema: "tr.v1"`
- BI: `_schema_version: "2.1"`, `_schema_description` 포함
- BI가 TR보다 스키마 메타데이터가 풍부. 기능 충돌 없으나 cross-pair 표준화 시 정리 대상
- Next step: 스키마 메타데이터 네이밍을 pair 전체에서 통일

**2. BI `_creation_note`에서 `plot_roadmap은 live TR 전량 복사이며 BI 레벨에서 재창작하지 않았다` 자기선언 (P3)**

- BI `_creation_note`: TR 전량 복사 선언
- 실제 BI 구조를 보면 `ArcSheets`, `KeyNPCs`, `Seeds`, `FinanceHUD.portfolio_history` 등이 TR block-level 데이터에서 추출·재구조화되어 있어, 단순 복사보다는 구조적 재편성이 이루어짐
- 다만 BI 독자 부가가치(TR에 없는 새 분석축)는 제한적
- Next step: `_creation_note`의 자기선언을 실제 BI 부가가치 수준에 맞게 갱신

**3. 주인공 엔진 정합성 — 완전 정렬 확인**

- TR Block 1 `protagonist`: 윤도현 — BI `CoreIdentity.protagonist`: 윤도현
- TR Block 1 `edge`: 2006~2024 한국 IT 거시 타임라인 지식 — BI `CoreIdentity.edge`: 동일 4축 결합
- TR Block 1 `desire`: 팬택+싸이월드 결합 — BI `CoreIdentity.desire`: 동일
- TR Block 70 endgame: 생활계정 그룹 공식 선포 + 승계 확보 — BI `MetaInfo.grand_objective`: 동일 목표
- 정합성 완전

**4. late-pair carry — 완전 정렬 확인**

- TR Block 70 `capital_after`: 7,790억 — BI `portfolio_history` Block 70: 7,790억
- TR Block 70 callback: Block 1 `벽돌 더미 속 지도` 표현 회수 — BI `CommercialCode.reader_hook`: 동일 구조
- TR Block 70 regression_ext `death_flag.choice_made`: 생활계정 그룹 공식 선포 — BI `protagonist_config.regression_mechanic` 전체 구조와 정합
- endgame pressure 및 최종 방향이 TR-BI 간 완전 일치

**5. blockguide family overlay — 정합 확인**

- BI `genre_profiles`: primary `investment_market_profile`, secondary `tech_startup_profile` — TR `genre_ext` 전체 투자 메커니즘과 정합
- BI `FinanceHUD` Resource-Power HUD: 0억→7,790억 portfolio_history 14 decline 포함 — TR block-level capital 추적과 일치
- BI `active_domain_lines`: arc별로 TR front_sector와 정합

### One-line Summary

Pair 08은 TR-BI 간 주인공 엔진, 투자 성장선, 회귀 메카닉, 적대 구조, endgame 수미상관이 매우 높은 수준으로 정렬된 clean pair다. BI가 TR 구조를 충실히 재편성하고 있으며, 스키마 메타데이터 명명과 자기선언 문구만 정리하면 된다.

---

## Lane 4 Summary Table

| Pair | Verdict | P0 | P1 | P2 | P3 | Key Issue |
| --- | --- | --- | --- | --- | --- | --- |
| 07 | `mixed` | 0 | 0 | 2 | 2 | `incarnation_type` 오기 (회귀자→비회귀), `company_state` 초기값 고정 |
| 08 | `clean` | 0 | 0 | 0 | 2 | 스키마 메타 명명 불일치, `_creation_note` 자기선언 과소 |
