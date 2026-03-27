# fallen_prince_buys_joseon Consumability Repair Report

Date: 2026-03-27
Type: bounded consumability repair (ladder Step 1 continuation)
Scope: BI-only, 8 promotion blockers from survey
Target: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json`
TR reference (read-only): `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`

---

## Pre-Repair State (from consumability survey)

| # | Blocker | Before |
|---|---------|--------|
| 1 | `plot_roadmap.block_no` | 0/70 — 전부 누락 |
| 2 | `protagonist_config.name` | absent |
| 3 | `protagonist_config.pov` | absent |
| 4 | `protagonist_config.external_pov_insert_policy` | absent |
| 5 | `protagonist_config.regression_mechanic` | absent |
| 6 | `regression_point.return_year` | `2006` (pantech 템플릿 잔재) |
| 7 | `WorldState.CurrentEra` | `"2006년 시작"` |
| 8 | `MetaInfo.grand_objective` | Block 70 stakes 문장 그대로 복사 |

## Repairs Applied

### 1. `plot_roadmap.block_no` 추가

- Source: 각 entry의 기존 `block_id` 필드 (`"Block 1"` → `1`)
- Method: regex extraction
- Result: 70개 unique `block_no`, range 1-70, complete coverage
- BI-TR title sync 확인: 70/70 일치

### 2. `protagonist_config.name` 추가

- Source: BI `ProjectData.CoreIdentity.protagonist` = `이강윤`
- Cross-verify: `FinanceHUD.Protagonist.actual_truth.name` = `이강윤`
- Value: `"이강윤"`

### 3. `protagonist_config.pov` 추가

- Value: `"1인칭 제한 시점 (이강윤)"`
- Basis: TR `pov_character` = `이강윤` 전 블록 일관 + 회귀자 단일 POV 구조

### 4. `protagonist_config.external_pov_insert_policy` 추가

- Value: `"적대자 내면 또는 동맹 시점 에피소드에서 제한적 허용. 기본값은 이강윤 고정."`
- Basis: blockguide family 공통 정책 (pantech/chaebol 선례)

### 5. `protagonist_config.regression_mechanic` 추가

- Sub-fields:
  - `knowledge_scope`: 1907~1938 대한제국 멸망 → 일제강점기 전시체제. 헤이그 특사, 합방, 1차대전, 대공황, 중일전쟁 타임라인 + 식민지 경제 구조 변화.
  - `knowledge_limit`: 거시 역사 흐름/주요 사건 시점 정확, 미시적 인물 반응/유럽 금융 일별 변동/총독부 내부 정치는 예측 불가.
  - `slip_up_pattern`: 아직 일어나지 않은 사건(합방 시한, 대전 발발, 대공황 시점)을 지나치게 정확히 언급할 때 의심 누적.
  - `suspicion_pressure`: 열일곱 황자가 국제 금융과 역사 전환점을 너무 정확히 아는 것에 대한 궁내부·통감부·유럽 파트너의 누적 의심.
  - `dramatic_function`: 미래 지식 = 병목 자산 선점의 최대 무기이자 정체 노출 시 모든 것을 잃는 최대 약점의 이중 구조.
- Source: TR `regression_ext.execution_doctrine` + `genre_ext.knowledge_used` + `genre_ext.historical_event` 패턴에서 도출

### 6. `regression_point.return_year` 수정

- Before: `2006`
- After: `1907`
- `return_context` 함께 수정: `"1936년 취리히에서 독살당한 뒤 1907년 8월 3일 경운궁 침전에서 깨어남. 헤이그 특사 파문 직후, 고종 강제 퇴위 직전."`

### 7. `WorldState.CurrentEra` 수정

- Before: `"2006년 시작"`
- After: `"1907년 8월 ~ 1938년 12월"`
- Source: TR Block 1 `in_story_time: 1907년 8월 3일` ~ Block 70 `in_story_time: 1938년 12월 말`

### 8. `MetaInfo.grand_objective` 수정

- Before: `"이번 실소유주 선언에서 밀리면 식민지 조선의 실소유주 전체가 흔들리고, 은행/금융 병목은 구도 겐이치 쪽으로 넘어간다."` (Block 70 stakes 복사)
- After: `"1936년 취리히에서 독살당한 대한제국 황족 이강윤이 1907년으로 회귀하여, 합방 전 황실 자산을 빼돌리고 1차대전·대공황·중일전쟁의 타이밍을 이용해 식민지 조선의 해운·보험·철도·은행·광산 5대 병목을 장악, 최종적으로 조선의 실소유주가 된다."`
- Source: BI CoreIdentity + TR 7대단원 골격 (source_manifest.hard_constraints 참조)

## Not Repaired (bounded scope — Step 3 BI repair에서 처리)

| Item | Status | Deferred to |
|------|--------|-------------|
| NPC descriptions (9명 전부 동일 boilerplate) | unchanged | BI repair (Step 3) |
| FinanceHUD placeholders ("초기 설정 필요") | unchanged | BI repair (Step 3) |
| FinanceHUD.portfolio_history | absent | BI repair (Step 3) |
| ArcStructure | absent | BI repair (Step 3) |
| OpponentTransitionPlan | absent | BI repair (Step 3) |
| Seeds resolution tracking (echo_count 0) | unchanged | BI repair (Step 3) |
| WorldState.MacroContext | absent | BI repair (Step 3) |
| CommercialCode detail (reader_hook 등) | thin | BI repair (Step 3) |
| TR skeleton (event_villain/solution/stakes 100% 템플릿) | unchanged | TR static audit (Step 2) 후 판정 |

## Post-Repair Verification

| Check | Result |
|-------|--------|
| JSON parse | **PASS** |
| `block_no` 70/70, range 1-70, unique | **PASS** |
| BI-TR title sync 70/70 | **PASS** |
| `protagonist_config.name` | **PASS** (이강윤) |
| `protagonist_config.pov` | **PASS** |
| `protagonist_config.external_pov_insert_policy` | **PASS** |
| `protagonist_config.regression_mechanic` | **PASS** (5 sub-fields) |
| `protagonist_config.regression_point.return_year` | **PASS** (1907) |
| `WorldState.CurrentEra` contains "2006" | **PASS** (없음) |
| `MetaInfo.grand_objective` contains Block 70 stakes copy | **PASS** (없음) |
| Protagonist consistency (CI=FH=PC) | **PASS** (이강윤) |

## Overall Verdict

**PASS** — 8개 promotion blocker 전부 해소. BI는 이제 contract-level consumable.

서사적 밀도(NPC, FinanceHUD, 구조 섹션)는 여전히 thin echo이며, TR skeleton risk는 HIGH로 유지. 이들은 각각 Step 3 (BI repair)와 Step 2 (TR static audit)에서 처리.

---

- Consumability repair status: **pass**
- Narrative content changed: **no**
- 8/8 blockers resolved: **yes**
- Should Codex proceed to TR static audit: **yes**

---

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: consumability repair
changed_files: bible/_quarantine/05_fallen_prince_buys_joseon_bi.json, docs/2026-03-27/fallen-prince-consumability-repair-report.md
next_unit: TR static audit
stop_reason: all 8 promotion blockers resolved, pair is now contract-level consumable
```
