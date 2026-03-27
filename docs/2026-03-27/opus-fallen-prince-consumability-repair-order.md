# OPUS Fallen Prince Consumability Repair Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `fallen_prince_buys_joseon`

## 1. Order Intent

This order fixes the target to `fallen_prince_buys_joseon` and asks OPUS to advance exactly one revival-ladder unit.

Current lane truth:
- family: `blockguide`
- entry type: existing `TR + BI` pair revival
- current pair location: `_quarantine`
- smallest remaining unproven step: `consumability repair` (ladder Step 1 continuation)

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not regenerate TR — this is minimum contract patch only
- do not redesign BI from scratch — structural BI repair is Step 3
- do not touch narrative content (context, solution, event_villain, stakes, etc.)
- do not promote to active path in the same run
- do not run Stage 2/3/4 in the same run
- repair BI only — do not modify TR in this run

## 3. Canonical Target

- work_id: `fallen_prince_buys_joseon`
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json`
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json` (read-only reference)

Only the BI file is modified in this run.

## 4. Proven Prior Steps

1. Pair consumability survey:
   - `docs/2026-03-27/fallen-prince-pair-consumability-survey.md`
   - verdict: `pass with warnings` — 8 promotion blockers, HIGH skeleton risk

## 5. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-27/fallen-prince-pair-consumability-survey.md` (전문 — blocker 목록이 이 오더의 repair scope)
5. `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-repair-report.md` (format reference)

## 6. Immediate Goal

Execute exactly one bounded `consumability repair` for `fallen_prince_buys_joseon`.

Repair scope: survey에서 발견된 **8개 promotion blocker만** 최소 패치. 그 이상 손대지 않는다.

## 7. Repair Spec

### 7.1 `plot_roadmap.block_no` 추가 (blocker #1)

- Source: each entry's existing `block_id` field (e.g., `"Block 1"` → `1`)
- Method: regex extraction, 동일 로직으로 `pantech_cyworld_reborn`에서 검증 완료
- Expected: 70개 unique `block_no`, range 1-70

### 7.2 `protagonist_config.name` 추가 (blocker #2)

- Source: BI `ProjectData.CoreIdentity.protagonist` = `이강윤`
- Cross-verify: `FinanceHUD.name` = `이강윤`
- Value: `"이강윤"`

### 7.3 `protagonist_config.pov` 추가 (blocker #3)

- Value: `"1인칭 제한 시점"`
- Basis: TR `pov_character` = `이강윤` + work는 회귀자 단일 POV 구조

### 7.4 `protagonist_config.external_pov_insert_policy` 추가 (blocker #4)

- Value: `"적대자 내면 또는 동맹 시점 에피소드에서 제한적 허용"`
- Basis: blockguide family 공통 정책 (pantech/chaebol 선례 동일)

### 7.5 `protagonist_config.regression_mechanic` 추가 (blocker #5)

- Derive from: TR `regression_ext` 필드 패턴 + BI `protagonist_config.regression_point`
- Expected sub-fields (pantech 선례 기준):
  - `type`: 회귀 유형 (e.g., "사망 후 과거 회귀")
  - `trigger`: 회귀 트리거 (e.g., "사망")
  - `return_target`: 회귀 도착 시점/상황
  - `knowledge_scope`: 미래 지식 범위
  - `slip_up_mechanic`: 의심 누적 메커니즘
- **중요**: 이 work는 1907년 대한제국/구한말 배경. TR의 역사 이벤트(헤이그 특사, 정미7조약, 합방)와 일관되게 작성할 것

### 7.6 `protagonist_config.regression_point.return_year` 수정 (blocker #6)

- Current: `2006` (오류 — pantech 템플릿 잔재)
- Correct: `1907`
- Basis: work 배경은 1907년 대한제국, TR historical_event 매핑과 일관

### 7.7 `WorldState.CurrentEra` 수정 (blocker #7)

- Current: `"2006년 시작"` (오류)
- Correct: `"1907년 8월 ~ 1936년"` (또는 TR/BI에서 도출되는 정확한 시간 범위)
- Basis: TR Block 1 time_span + Block 70 time_span에서 전체 시간 범위 도출

### 7.8 `MetaInfo.grand_objective` 수정 (blocker #8)

- Current: Block 70 stakes 문장 그대로 복사 (템플릿 오류)
- Correct: work의 grand objective에 맞는 문장으로 교체
- Basis: BI `ProjectData.CoreIdentity` + TR 전체 아크에서 도출
- 예시 방향: "몰락한 황족 이강윤이 1907년으로 회귀하여 대한제국의 자산을 지키고 근대 금융 제국을 건설한다" (정확한 문구는 BI/TR에서 도출)

## 8. Repair Rules

- **minimum patch only**: 위 8개 blocker만 수정, 그 외 필드는 건드리지 않는다
- **no narrative content modification**: context, event_villain, solution, stakes, title 등 서사 필드 불변
- **no NPC repair**: NPC boilerplate는 BI repair(Step 3)에서 처리
- **no FinanceHUD repair**: placeholder 해소는 BI repair(Step 3)에서 처리
- **no structural section addition**: ArcStructure, OpponentTransitionPlan 등은 BI repair(Step 3)
- **no TR modification**: TR은 이 런에서 read-only
- source of truth for values: BI 자체 내부 + TR cross-reference만 사용, 외부 추론 최소화

## 9. Post-Repair Verification

Repair 후 반드시 확인:

1. BI JSON 파싱 정상
2. `plot_roadmap.block_no` 70/70 존재, range 1-70, unique
3. BI-TR title sync 70/70
4. `protagonist_config` 5개 필드 모두 존재 (`name`, `pov`, `external_pov_insert_policy`, `regression_mechanic`, `regression_point`)
5. `protagonist_config.regression_point.return_year` == 1907
6. `WorldState.CurrentEra`에 "2006" 문자열 없음
7. `MetaInfo.grand_objective`에 Block 70 stakes 복사 문장 없음
8. 수정하지 않은 필드들이 변경되지 않았는지 diff 확인

## 10. Deliverable

Save exactly one main report:

- `docs/2026-03-27/fallen-prince-consumability-repair-report.md`

The report should include:
- target pair paths
- pre-repair state (8 blockers)
- each repair applied (source, method, result)
- not repaired (bounded scope — NPC, FinanceHUD, structural sections deferred to Step 3)
- post-repair verification result
- overall verdict: `pass` or `partial`

## 11. Stop Conditions

Stop immediately and report if any of the following occurs:

- BI file is missing or corrupted
- a blocker requires information not derivable from BI/TR (ask, don't guess)
- repair would require touching narrative content
- repair would require TR modification
- post-repair verification fails
- confidence falls below 95%

## 12. Expected Next Unit After This Order

- if repair passes: `TR static audit` (ladder Step 2)
- if repair is partial (some blockers unresolvable): report remaining blockers, recommend targeted fix

Note: TR static audit will face HIGH skeleton risk. The survey already forecasts a likely verdict of "consumable but skeleton-likely" or "regenerate TR first". This is expected and does not block the current repair.

## 13. Handoff Format

End with this exact flat report:

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: consumability repair
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + revival-ladder boundaries
- repair scope is bounded to 8 specific blockers from survey
- no narrative content modification
- no TR modification
- no structural BI redesign

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `consumability repair`
- all 8 blockers are enumerated with source, method, expected value
- post-repair verification checklist is explicit
- pantech consumability repair report provides proven format reference
- HIGH skeleton risk is acknowledged as downstream (Step 2), not this run's scope

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded repair step

Confidence:
- 97% that `consumability repair` is the correct next OPUS unit for this pair
