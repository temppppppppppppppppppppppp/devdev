# 0_1 Stage 3 Blueprint Fix Execution SSOT

Date: 2026-03-30
Status: closed
Canonical Path: docs/2026-03-30/0_1-stage3-blueprint-fix-execution-ssot.md
Temp Mirror Path: docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md
Baseline Commit: 6fe5590d
Baseline Dirty Summary: many deleted project files + modified config/models.yaml, style_guide.json, stage4_canary_tools.py, world_state.py
Source Survey Docs: docs/2026-03-30/0_1-stage3-blueprint-integrity-bounded-survey.md
Evidence Artifacts: projects/0_1/logs/artifacts/stage3/ep_0008/, projects/0_1/logs/artifacts/stage3/ep_0015/, projects/0_1/plans/arcs/arc_004.txt

## 1. Intent

P1 결함 3건을 local patch로 수정하여 Stage 4 manuscript 생성 진입을 가능하게 한다.
Blueprint 재생성(regeneration) 없이, 기존 artifact의 특정 필드만 수정한다.

## 2. Bug List

| ID | Episode | Severity | Description |
|----|---------|----------|-------------|
| P1-A | EP8 | P1 | scene_breakdown 4개 씬 전량 `characters: []` — 빈 배열 |
| P1-B | EP15 | P1 | ending_state.timeline.표현 "2006년 4월 중순 심야" — Arc 4 "5월 말"과 6주 차이 |
| P1-C | EP15 | P1 | integrated_scenario "밑줄" vs scene_2.content "동그라미" — 동일 행동 불일치 |

## 3. Authority / Source Contract

| Source | Authority Level | Usage |
|--------|----------------|-------|
| plans/arcs/arc_004.txt | Primary (Stage 2 output) | EP15 timeline 정본 기준 |
| logs/artifacts/stage3/ep_0008/ JSON | Primary (Stage 3 output) | EP8 수정 대상 |
| logs/artifacts/stage3/ep_0015/ JSON | Primary (Stage 3 output) | EP15 수정 대상 |
| plans/blueprints/blueprint_0008.txt | Derived (JSON → txt 복사본) | EP8 수정 후 동기화 필요 |
| plans/blueprints/blueprint_0015.txt | Derived (JSON → txt 복사본) | EP15 수정 후 동기화 필요 |
| project_data.db | Read-only during this fix | 수정 대상 아님 |

## 4. Affected Episodes

| Episode | Fix Scope | Fields Touched |
|---------|-----------|----------------|
| EP8 | P1-A | scene_breakdown.scene_1~4.characters |
| EP15 | P1-B | ending_state.timeline.표현, time_flow |
| EP15 | P1-C | integrated_scenario 또는 scene_2.content (마커 통일) |

## 5. Repair Mode Recommendation

### P1-A: EP8 Characters (local patch)

**Action**: 4개 씬의 `characters` 배열을 채운다.

Evidence-based character assignments (integrated_scenario + scene goal/summary에서 추출):
- scene_1: `["한시우", "박성호 PB"]` — VIP룸 밖, 박성호가 경악하며 한시우의 뒷모습 관찰
- scene_2: `["한시우"]` — 카페에서 혼자 블룸버그 확인
- scene_3: `["박성호 PB"]` — 파생상품 데스크에서 계좌 확인 (한시우 부재, side_glimpse)
- scene_4: `["한시우", "박성호 PB"]` — 전화 통화

**Touched files**:
1. `projects/0_1/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json`
2. `projects/0_1/plans/blueprints/blueprint_0008.txt`

### P1-B: EP15 Timeline (local patch)

**Action**: timeline 필드를 Arc 4 기준으로 보정.

변경:
- `ending_state.timeline.표현`: "2006년 4월 중순 심야" → "2006년 5월 말 심야"
- `time_flow`: "늦은 저녁 → 심야" → "2006년 5월 말 늦은 저녁 → 심야"

**Rationale**: Arc 4 tactical doc이 "이전 시기 종료로부터 약 2주가 지난 2006년 5월 말"로 명시. EP14 ending이 "4월 중순 늦은 저녁"이므로, EP15 시작점을 "5월 말"로 이동하면 arc와 정합. integrated_scenario 본문에는 구체적 월/날짜 언급이 없어 본문 수정 불필요.

**Touched files**:
1. `projects/0_1/logs/artifacts/stage3/ep_0015/attempt_01/final_blueprint__action_focused.json`
2. `projects/0_1/plans/blueprints/blueprint_0015.txt`

### P1-C: EP15 Marker (local patch)

**Action**: 마커 행동을 하나로 통일.

선택지:
- Option A: scene_2.content의 "동그라미를 친다" → "밑줄을 그었다"로 통일 (integrated_scenario 기준)
- Option B: integrated_scenario의 "밑줄을 그었다" → "동그라미를 친다"로 통일 (scene content 기준)

**Recommendation**: Option A (integrated_scenario 기준). 이유:
1. integrated_scenario가 Stage 4에서 primary narrative source
2. Arc 4에서는 "손가락으로 툭툭 치며"이므로 어느 쪽이든 arc와 다르지만, blueprint 내부 일관성이 우선
3. "밑줄"이 더 구체적이고 시각적으로 명확

**Touched files** (P1-B와 동일):
1. `projects/0_1/logs/artifacts/stage3/ep_0015/attempt_01/final_blueprint__action_focused.json`
2. `projects/0_1/plans/blueprints/blueprint_0015.txt`

## 6. Touched-File Candidate Set

| File | Patches |
|------|---------|
| `projects/0_1/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` | P1-A |
| `projects/0_1/plans/blueprints/blueprint_0008.txt` | P1-A (txt 동기화) |
| `projects/0_1/logs/artifacts/stage3/ep_0015/attempt_01/final_blueprint__action_focused.json` | P1-B, P1-C |
| `projects/0_1/plans/blueprints/blueprint_0015.txt` | P1-B, P1-C (txt 동기화) |

총 4개 파일, JSON 2개 + txt 2개.

## 7. Validation / Closure Criteria

### Per-Fix Validation

| Fix | Validation |
|-----|-----------|
| P1-A | EP8 JSON의 4개 씬 characters 배열이 비어있지 않음. blueprint_0008.txt와 JSON 내용 일치. |
| P1-B | EP15 JSON ending_state.timeline.표현에 "5월 말" 포함. time_flow에 "5월 말" 포함. blueprint_0015.txt와 JSON 내용 일치. |
| P1-C | EP15 JSON integrated_scenario와 scene_2.content의 마커 행동이 동일 단어 사용. |

### Global Validation

1. 수정 후 4개 파일 모두 valid UTF-8
2. 수정 후 2개 JSON 파일 모두 valid JSON (python -m json.tool)
3. 수정 후 blueprint txt와 JSON의 integrated_scenario 필드가 byte-identical
4. 수정 후 EP8→EP9, EP15→(future EP16) 연결고리 보존 확인
5. 수정이 다른 에피소드의 blueprint에 영향 없음 확인

### Closure

- P1 3건 전부 validation pass → execution SSOT status를 `completed`로 변경
- temp mirror 삭제
- Stage 4 진입 가능 선언

## 8. Execution Order

1. P1-A: EP8 characters patch (JSON → txt sync)
2. P1-B: EP15 timeline patch (JSON → txt sync)
3. P1-C: EP15 marker patch (JSON → txt sync) — P1-B와 같은 파일이므로 동시 수행 가능
4. Validation: UTF-8, JSON validity, content match, chain continuity
5. Closure

예상 소요: 단일 턴.

## 9. Non-Goals / Guardrails

- P2 watchlist 항목은 이 SSOT에서 수정하지 않음
- Blueprint 재생성(regeneration) 금지
- DB 수정 금지
- 다른 에피소드의 blueprint 수정 금지
- Stage 4 실행은 이 SSOT 범위 밖

---

*3pass audit completed. Estimated confidence: 96%. Final save.*

## 10. Closure Update

Date: 2026-03-31
Closure Audit: `docs/2026-03-31/0_1-stage3-blueprint-fix-closure-audit.md`
Closure Evidence: `docs/2026-03-31/0_1-stage3-blueprint-fix-closure-evidence.json`
Status Rationale:
- authoritative EP8 and EP15 JSON artifacts already held the intended P1 repairs
- the remaining live mismatch was the stale derived mirror `projects/0_1/plans/blueprints/blueprint_0008.txt`
- this closure synchronized the EP8 txt mirror to the authoritative JSON and revalidated EP15 alignment
- UTF-8 and JSON validity checks passed for the touched lane artifacts

Residuals:
- no residual inside this bounded artifact-fix lane
- next queue item is `stage3-blueprint-validator-hardening`
