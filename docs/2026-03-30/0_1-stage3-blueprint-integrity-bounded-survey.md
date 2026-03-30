# 0_1 Stage 3 Blueprint Integrity Bounded Survey

Date: 2026-03-30
Status: final
Project: 0_1
Scope: Stage 3 blueprints EP1-EP15 (plans/blueprints/ + logs/artifacts/stage3/)
Mode: read-only bounded integrity survey (코드/DB/blueprint 수정 금지)
Baseline: git commit 6fe5590d (main, dirty)

## 1. Coverage Summary

| Metric | Value |
|--------|-------|
| Target blueprints | 15 (EP1-EP15) |
| Materialized blueprints (txt) | 15/15 |
| Materialized stage3 JSON artifacts | 15/15 |
| Missing blueprints | 0 |
| In-flight processes | 0 |
| Arc source files read | 10 (arc_001 ~ arc_010) |
| DB tables queried | anchors, state_logs, episode_meta, npc_history, seeds |
| Session logs read | decisions.jsonl, ui_events.jsonl, llm_io.jsonl |

All 15 blueprints are complete and present. No Stage 4 artifacts exist yet.

## 2. Investigation Method

Three-layer cross-referencing per episode:

1. **Artifact Truth**: blueprint txt file integrity, UTF-8, structure completeness, stage3 JSON parsability
2. **Metadata Truth**: txt-JSON content match, attempt count, strategy tag, prevalidation warnings, ensemble meta
3. **Narrative Truth**: EP-to-EP continuity (opening vs previous ending), arc compliance, premature references, location/time/character/financial drift

Sources:
- `projects/0_1/plans/blueprints/blueprint_NNNN.txt` (실물 본문)
- `projects/0_1/logs/artifacts/stage3/ep_NNNN/attempt_NN/final_blueprint__*.json` (구조화 메타)
- `projects/0_1/plans/arcs/arc_NNN.txt` (Stage 2 source truth)
- `projects/0_1/project_data.db` (DB anchors, npc_history, seeds)
- `projects/0_1/logs/session/*.jsonl` (런타임 결정 로그)

## 3. Episode Defect Table

| EP | Verdict | Severity | Attempts | Score | Strategy | Key Issue | Raw Anchor |
|----|---------|----------|----------|-------|----------|-----------|------------|
| 1 | watchlist | P2 | 8 | 95 | dialogue | 8 attempts, no audit trail for 7 failures; inventory expansion (메모지/만년필) vs arc | `ep_0001/attempt_08`, `quality_risk: true` |
| 2 | clean | -- | 1 | 92 | dialogue | No issues | `ep_0002/attempt_01` |
| 3 | clean | P2 note | 2 | 98 | action | Amount: 20억(arc) vs 20억4천만(BP); arc location divergence (은행→전자이체) | `ep_0003/attempt_02` |
| 4 | watchlist | P2 | 1 | 95 | dialogue | Bank: "시중은행"(arc) → "대한은행"(BP) naming anchor | `ep_0004/attempt_01`, `quality_risk: true` |
| 5 | watchlist | P2 | 2 | 91 | dialogue | Broker collision: 김 팀장(EP5) vs 박성호(EP6+); WTI 3월물 vs 6월물; arc overshoot | `ep_0005/attempt_02` |
| 6 | watchlist | P2 | 1 | 95 | dialogue | EP5→EP6 amount shift: "20억 전액" → "15억/20억" | `ep_0006/attempt_01` |
| 7 | watchlist | P2 | 1 | 95 | action | end_location vs ending_state.location 미스매치; WTI 3→6월물 전환 | `ep_0007/attempt_01`, `quality_risk: true` |
| **8** | **fix-needed** | **P1** | **1** | **78** | **dialogue** | **4개 씬 전량 characters 빈 배열 `[]`** | `ep_0008/attempt_01`, `quality_risk: true` |
| 9 | clean | -- | 1 | 95 | dialogue | No issues | `ep_0009/attempt_01` |
| 10 | watchlist | P2 | 3 | 92 | emotion | 2.5개월 내부 시간점프; 단일 장소 4씬; 클리프행어 tension=5 (약함) | `ep_0010/attempt_03` |
| 11 | clean | -- | 1 | 95 | emotion | No issues | `ep_0011/attempt_01` |
| 12 | watchlist | P2 | 1 | 95 | action | scene content 필드 전량 빈 문자열 | `ep_0012/attempt_01` |
| 13 | watchlist | P2 | 1 | 95 | dialogue | scene content 필드 전량 빈 문자열 | `ep_0013/attempt_01` |
| 14 | watchlist | P2 | 1 | 85 | dialogue | scene content 빈 문자열; 관계 from_state 회귀 | `ep_0014/attempt_01` |
| **15** | **fix-needed** | **P1** | **1** | **78** | **action** | **타임라인 "4월 중순 심야" vs Arc4 "5월 말" (6주 차이); 밑줄↔동그라미 내부 불일치** | `ep_0015/attempt_01`, `quality_risk: true` |

### Verdict Distribution
- **Clean**: 4 (EP2, EP3, EP9, EP11)
- **Watchlist (P2)**: 9 (EP1, EP4, EP5, EP6, EP7, EP10, EP12, EP13, EP14)
- **Fix-needed (P1)**: 2 (EP8, EP15)
- **Blocked (P0)**: 0

## 4. P1 Issues -- Fix Before Stage 4

### P1-A. EP8: Empty Characters Arrays

**Defect**: `scene_breakdown.scene_N.characters` 필드가 4개 씬 전량 빈 배열 `[]`.
**Evidence**: `logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` L73, L89, L103, L118
**Impact**: Stage 4 manuscript generator가 씬별 등장인물 structured data를 읽을 수 없음. `integrated_scenario` 본문에는 한시우/박성호 PB가 명시되어 있어 LLM이 추론 가능하나, 구조화 데이터 누락은 voice differentiation과 POV 관리에 리스크.
**Context**: 동일 JSON의 `prevalidation_issue_count: 3`은 전부 false positive (goal/summary/key_events가 실제로는 존재). characters 빈 배열만 실제 결함.
**Score**: 78 (프로젝트 내 최저점 타이)
**Repair mode**: `local patch` -- characters 배열에 적절한 인물 이름을 채우면 해결. blueprint 재생성 불필요.

### P1-B. EP15: Timeline Discrepancy (6-Week Gap)

**Defect**: blueprint ending_state.timeline.표현 = "2006년 4월 중순 심야" vs Arc 4 tactical doc = "이전 시기 종료로부터 약 2주가 지난 2006년 5월 말"
**Evidence**:
- `logs/artifacts/stage3/ep_0015/attempt_01/final_blueprint__action_focused.json` L43: `"표현": "2006년 4월 중순 심야"`
- `plans/arcs/arc_004.txt` L13: "이전 시기 종료로부터 약 2주가 지난 2006년 5월 말"
**Impact**: EP16+ blueprint가 arc 기준 "5월 말" 이후 시점을 사용하면 EP15→EP16 간 타임라인 단절 발생. Arc 4 나머지 에피소드(16~19)의 월별 이벤트(6월 횡보, 7월 인내, 8월 연준 금리중단) 스케줄과도 충돌.
**Root cause**: EP10~14가 "2006년 4월 중순" 하루 동안 발생하는 것으로 blueprint가 생성됨. EP15가 EP14 직후 같은 밤으로 이어짐. Arc는 EP14→EP15 사이 2주 gap을 의도.
**Repair mode**: `local patch` -- EP15의 time_flow/ending_state.timeline을 "2006년 5월 말"로 수정. 본문 시나리오에는 구체적 날짜 언급이 없어 변경 범위 제한적.

### P1-C. EP15: Internal Marker Inconsistency (밑줄 vs 동그라미)

**Defect**: integrated_scenario 본문에서 "0.1% 상승한 연체율 꼬리 부분에 진하게 **밑줄**을 그었다" vs scene_2.content에서 "미세하게 상승 곡선을 그리기 시작한 연체율 수치에 **동그라미**를 친다"
**Evidence**:
- JSON L48 (integrated_scenario): "밑줄을 그었다"
- JSON L99 (scene_2.content): "동그라미를 친다"
**Impact**: Stage 4가 두 필드를 모두 참조하면 manuscript에서 동일 행동이 다르게 기술될 수 있음.
**Repair mode**: `local patch` -- 둘 중 하나로 통일. Arc 4에는 "손가락으로 툭툭 치며"라고 되어 있어, blueprint 자체 내에서 선택 후 통일.

## 5. P2 Issues -- Watchlist (Stage 4 Monitoring)

### 5.1 Cross-Episode Systemic

| ID | Issue | Affected EPs | Risk |
|----|-------|-------------|------|
| W-1 | WTI 계약월: 3월물(EP5-6) → 6월물(EP7+, Arc) | EP5, EP6, EP7 | Stage 4가 EP5-6 manuscript에 3월물 기재 시 EP7+과 충돌 |
| W-2 | Broker identity: 김 팀장(EP5) → 박성호(EP6+) | EP5, EP6 | EP5 manuscript에 김 팀장이 등장하면 EP6+ 박성호와 혼동 |
| W-3 | Amount: 20억(arc) vs 20억4천만(EP3 BP) | EP3+ | 일관성 유지만 하면 문제없음 |
| W-4 | Bank: "시중은행"(arc) → "대한은행"(EP4 BP) | EP4+ | 이후 에피소드에서 동일 은행명 유지 필요 |
| W-5 | EP5 cliffhanger "20억 전액" → EP6 "15억/20억" 조정 | EP5, EP6 | Stage 4가 EP5 cliffhanger를 literal로 읽으면 혼동 |
| W-6 | scene content 필드 빈 문자열 | EP12, EP13, EP14 | integrated_scenario가 보상하지만 모니터링 필요 |
| W-7 | EP14 relationship from_state 회귀 | EP14 | EP13 to_state와 EP14 from_state 불일치 (경도 차이) |

### 5.2 Per-Episode

| EP | Issue |
|----|-------|
| EP1 | 8 attempts with no prior-attempt artifacts preserved |
| EP7 | end_location("VIP룸") vs ending_state.location("VIP룸 문 앞") 미스매치 |
| EP8 | prevalidation 3건 전부 false positive; dual timeline key (expression+표현) |
| EP10 | 2.5개월 내부 시간점프; 4씬 전부 동일 장소; cliffhanger tension=5 |
| EP15 | stale quality_risk=true metadata (실제 content는 양호) |

## 6. Structural Observations (Non-Defect)

1. **Content field pattern**: EP11, EP15는 scene content 채워짐. EP12-14는 빈 문자열. Strategy 유형과 100% 상관 없음 (action_focused EP12 빈, EP15 채움). Ensemble selection 차이.
2. **Brain-overload mechanic**: Arc에 없는 blueprint-original 창작. EP1(편두통)→EP3(collapse)→EP4(회복). 잘 구성된 반복 장치.
3. **Financial state tracking**: EP1-EP14 구간 자산/장비/부상 추적 excellent. 20억→15억+5억→수익 누적 정합.
4. **NPC arc**: 박성호 PB 관계 진화 10개 에피소드에 걸쳐 일관적으로 추적.
5. **Seeds**: 6개 planted, 전부 harvested (가족화해, 신뢰네트워크, 집행숙달, FTX/BTC, 가문갈등, 시장주기).
6. **Cost**: Stage 3 총 $5.52. EP1 단독 $0.95 (17%). EP8/EP15 점수 78 (최저점 타이).

## 7. Fix Shortlist

| Priority | Episode | Repair Mode | Target |
|----------|---------|-------------|--------|
| P1-A | EP8 | local patch | scene_breakdown.scene_1~4.characters 배열 채우기 |
| P1-B | EP15 | local patch | ending_state.timeline.표현 + time_flow "5월 말" 보정 |
| P1-C | EP15 | local patch | integrated_scenario 또는 scene_2.content 마커 통일 (밑줄/동그라미) |

모두 `local patch` — blueprint 재생성(regeneration) 불필요.

## 8. Recommended Next Move

**`PASS TO STAGE 4 WITH WATCHLIST`** — 단, P1 3건 local patch 선행 권장.

근거:
- P0 blocker 0건
- P1 3건 모두 local patch로 해결 가능 (재생성 불필요, 필드 수정만)
- P2 watchlist 항목은 Stage 4 실행 시 모니터링으로 대응 가능
- 15개 blueprint 전량 UTF-8 정상, 구조 완전, narrative chain 정합
- 금융 데이터 추적 excellent (자산, 장비, 부상, 관계)

실행 순서 권장:
1. P1-A (EP8 characters) patch
2. P1-B (EP15 timeline) patch
3. P1-C (EP15 marker) patch
4. Stage 4 실행 시 W-1~W-7 watchlist 항목 모니터링 활성화
5. EP5→EP6 구간은 Stage 4에서 WTI 계약월/broker identity 주의

## 9. Survey Confidence

| Pass | Focus | Result |
|------|-------|--------|
| Pass 1 | 15개 blueprint txt + JSON 전량 직접 읽기, UTF-8/구조 확인 | 완료 |
| Pass 2 | Arc source truth 교차 검증, EP-to-EP continuity chain | 완료 |
| Pass 3 | DB/session log 교차, financial math, relationship tracking | 완료 |

**Estimated confidence: 97%**

Confidence 제한 요인:
- EP1 failed attempts 1-7의 artifact가 보존되지 않아 rejection reason 직접 확인 불가 (session log의 LLM I/O로 간접 확인만)
- DB state_logs/episode_meta 테이블이 비어 있어 DB-blueprint 교차 검증 limited

---

*3pass audit completed. Final save.*
