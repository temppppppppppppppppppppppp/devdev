# Pair 07 BI Repair Note

Date: 2026-04-06
Status: complete
Target: `bible/07_bi_office_checkup_next_day.json`
TR touched: no

## P2 Repair (survey-flagged)

### 1. incarnation_type drift

- Before: `"회귀자"`
- After: `"각성"`
- TR truth: `regression_ext.is_regressor = false` across all 70 blocks. 한시혁 is ability-awakened, not a regressor.

### 2. company_state end-state drift

- Before: `"사수 퇴사 후 혼자 남은 팀 막내, 잡무 담당, 인사평가 B0"` (Block 1)
- After: `"경영기획팀장 + 그룹 구조조정 TF 실무총괄, 전략실/대표 보고 라인 확보, 라인 선택권 확보"`
- TR truth: Block 70 end-state. Adjacent capital fields already correct — `company_state` only was stuck.

## P3 Sweep (same actual_truth block, start-state residuals)

| Field | Before | After |
|---|---|---|
| `actual_truth.alias` | "사수 퇴사 후 혼자 남은 팀 막내" | "경영기획팀장 겸 TF 실무총괄" |
| `actual_truth.age` | 29 | 30 (Block 70 = 2026-10) |
| `actual_truth.rank` | "3년차 사원" | "경영기획팀장 + TF 실무총괄" |
| `financial_status.debt` | Block 1 부채 4건 | "초기 부채 전량 해소 + 잔여 리스크 2건" |
| `credentials` | ["3년차 사원", "경영기획팀"] | ["경영기획팀장", "TF 실무총괄"] |
| `public_reputation.identity` | start-state | end-state |
| `public_reputation.wealth_level` | "막내, 잡무, B0" | "Lv8" |
| `public_reputation.perceived_influence` | "저평가" | "결재 3곳 등재, 실권자" |
| `public_reputation.credit_rating` | "약함" | "그룹 레벨 참여" |
| `MartialHUD.alias/rank` | start-state | end-state (호환 shim) |

## KeyNPCs Dedup

- 한시혁 중복 2건 → 1건으로 병합
- block-level turning_points 보존, grand_objective 복사본 제거

## Untouched (correctly start-state)

- `protagonist_config.start_point` — 명시적 start 필드
- `WorldState.starter_company` — 명시적 starter
- `AssetLibrary.StarterCompany` — 명시적 starter

## Validation

- JSON syntax: valid
- TR: untouched
- Plot invention: none

## Expected Verdict

Pair 07: `mixed` → `clean`
