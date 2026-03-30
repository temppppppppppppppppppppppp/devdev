# 0_1 Stage 3 Blueprint Integrity Bounded Survey (EP16-EP20)

Date: 2026-03-30
Status: final
Project: 0_1
Scope: Stage 3 blueprints EP16-EP20 (plans/blueprints/ + logs/artifacts/stage3/)
Mode: read-only bounded integrity survey (코드/DB/blueprint 수정 금지)
Baseline Commit: 9ad4efcc (main, dirty — EP16 untracked, EP15 patched)
Prior Survey: docs/2026-03-30/0_1-stage3-blueprint-integrity-bounded-survey.md (EP1-EP15)

## 1. Coverage Summary

| Metric | Value |
|--------|-------|
| Target blueprints | 5 (EP16-EP20) |
| Materialized blueprints (txt) | 5/5 |
| Materialized stage3 JSON artifacts | 5/5 |
| Missing blueprints | 0 |
| Arc source files | arc_004.txt (EP16-19), arc_005.txt (EP20) |
| Session decisions | 5/5 entries in decisions.jsonl |

## 2. Investigation Method

EP1-15 survey와 동일한 3-layer cross-referencing:
1. **Artifact Truth**: JSON 파싱, UTF-8, 구조 완전성, characters/content/key_events 필드
2. **Metadata Truth**: JSON↔txt 내용 일치, attempt count, strategy, prevalidation, score
3. **Narrative Truth**: EP-to-EP hook 연결, arc 준수, timeline, 금융 데이터, relationship chain

## 3. Episode Defect Table

| EP | Verdict | Severity | Attempts | Score | Strategy | Key Issue | Raw Anchor |
|----|---------|----------|----------|-------|----------|-----------|------------|
| 16 | watchlist | P2 | 10 | 84 | action | 10 attempts; prevalidation false-positive 패턴 | `ep_0016/attempt_10` |
| **17** | **fix-needed** | **P1** | **3** | **88** | **emotion** | **"3,500만 달러" 금융 단위 오류 — arc는 원화 기준, $35M은 총자산 45억 원 대비 10배 이상 과다** | `ep_0017/attempt_03` |
| 18 | watchlist | P2 | 1 | 92 | dialogue | scene content 필드 5/5 전량 빈 문자열 | `ep_0018/attempt_01` |
| 19 | watchlist | P2 | 1 | 95 | emotion | scene content 빈 문자열 4/4; relationship from_state 회귀 | `ep_0019/attempt_01` |
| **20** | **fix-needed** | **P1** | **1** | **85** | **action** | **timeline "8월 9일" vs Arc 5 "9월" — 1개월 gap 누락; 총자산 50억 미명시** | `ep_0020/attempt_01` |

### Verdict Distribution
- **Clean**: 0
- **Watchlist (P2)**: 3 (EP16, EP18, EP19)
- **Fix-needed (P1)**: 2 (EP17, EP20)
- **Blocked (P0)**: 0

## 4. P1 Issues — Fix Before Stage 4

### P1-D. EP17: Financial Unit Error ($35M)

**Defect**: integrated_scenario에 "WTI 익절로 확보했던 3,500만 달러 중 500만 달러를 추가 증거금으로 즉각 투입"

**Evidence**:
- `logs/artifacts/stage3/ep_0017/attempt_03/final_blueprint__emotion_focused.json` L62 (scene_1.content)
- 동일 텍스트가 integrated_scenario에도 포함
- `plans/blueprints/blueprint_0017.txt` L7에서 동일 텍스트 확인

**Why it's wrong**:
- Arc 4 전체가 원화(₩) 기준: "15억 원의 증거금", "5억 원의 확정 수익", "45억 원"
- 3,500만 달러 = $35M ≈ 332억 원 (2006년 환율 ~950원/$ 기준) — 총자산 45억 원의 7.4배
- 500만 달러 = $5M ≈ 47.5억 원 — 추가 증거금이 총자산을 초과
- LLM이 원유/금 선물의 USD 거래 단위를 과잉 적용하여 arc의 KRW 체계와 충돌

**Impact**: Stage 4 manuscript에 "$35M" 기재 시 "45억 원 총자산" 서사와 직접 모순.

**Repair mode**: `local patch` — "3,500만 달러" → arc 기준 원화 수치로 교체. 추정: "WTI 익절로 확보했던 현금 중 5억 원을 추가 증거금으로 즉각 투입" 정도가 arc와 정합.

### P1-E. EP20: Timeline 1-Month Gap Missing

**Defect**: blueprint time_flow = "2006년 8월 9일 오전 → 8월 9일 오후", ending_state.timeline.표현 = "2006년 8월 9일 오후"

**Evidence**:
- `logs/artifacts/stage3/ep_0020/attempt_01/final_blueprint__action_focused.json` L21, L126
- `plans/arcs/arc_005.txt` L14: "이전 시기 종료로부터 1개월이 지난 2006년 9월"

**Why it's wrong**:
- EP19 ending = "2006년 8월 9일 오전"
- Arc 5 EP20 시작 = "이전 시기 종료로부터 1개월이 지난 2006년 9월"
- Blueprint는 EP19와 같은 날(8월 9일)에 계속 진행 — arc 의도 1개월 gap 무시
- **EP15 P1-B와 동일 결함 유형** (arc timeline vs blueprint timeline 불일치)

**Impact**: EP21+ blueprint가 arc 기준 "2006년 12월"을 사용하면 EP20→EP21 간 타임라인 불연속 발생. Arc 5의 나머지 에피소드(21~23) 타임라인 전체가 위협받음.

**Repair mode**: `local patch` — time_flow와 ending_state.timeline을 "2006년 9월"로 보정. integrated_scenario 본문에 "8월 9일 오전"이라는 구체적 날짜가 명시되어 있으므로, 시나리오 도입부에서 "9월 초" 등으로 시간 점프 삽입이 필요하며, EP15보다 수정 범위가 넓음.

### P1-E 부가 이슈: 총자산 미명시

Arc 5 EP20 tactical은 "총자산은 정확히 50억 원의 100% 현금 유동성으로 전환"을 명시. Blueprint는 "막대한 유동성"이라고만 기술하고 50억 원 수치를 기재하지 않음. 단독으로는 P2지만, timeline 수정과 함께 보정 시 50억 원도 삽입 권장.

## 5. P2 Issues — Watchlist (Stage 4 Monitoring)

### 5.1 Cross-Episode Systemic

| ID | Issue | Affected EPs | Risk |
|----|-------|-------------|------|
| W-8 | scene content 빈 문자열 패턴 | EP18, EP19 | integrated_scenario가 보상하지만 Stage 4 scene-level rendering 시 빈 content 참조 위험 |
| W-9 | relationship from_state 회귀: EP18 to_state "완벽한 경악" → EP19 from_state "경외하지만 반신반의" | EP19 | EP18에서 "완벽한 경악"까지 갔는데 EP19에서 "반신반의"로 후퇴 |
| W-10 | EP17 description 필드 중복: content와 description이 동일 텍스트 | EP17, EP20 | 비정상은 아니지만 불필요한 중복 |

### 5.2 Per-Episode

| EP | Issue |
|----|-------|
| EP16 | 10 attempts — 이전 9 attempt의 artifact 미보존, rejection reason 추적 불가 |
| EP16 | prevalidation 3건 전부 false positive (goal/summary/key_events 실제 존재) |
| EP18 | scene content 5건 전량 빈 문자열 (description 필드에 내용 존재) |
| EP19 | scene content 4건 전량 빈 문자열 (description 필드에 내용 존재) |
| EP20 | Arc 5 종료 소지품에 "2007년 코스피 주도주 분석 리포트 초안" 포함되어야 하나 blueprint equipment 누락 |
| EP20 | Director verdict reason "청산 지시 관련 내부 모순 수정 필요" — Director가 부분적 문제 감지했으나 PASS |

## 6. Structural Observations (Non-Defect)

1. **Hook 연결 품질**: EP15→16→17→18→19→20 전구간 ending_hook→다음 화 opening이 문자 그대로 일치. Excellent.
2. **Arc 4 완주**: EP16-19가 Arc 4(EP15-19) 4개 에피소드를 커버. 금 횡보→FOMC 금리동결→폭등→익절 arc 완결.
3. **Arc 5 진입**: EP20이 Arc 5(EP20-23) 첫 에피소드. 한태준 추격 서브플롯 개시.
4. **한태준 NPC 등장**: EP20에서 새 NPC(한태준, 비서실장) 등장. relationship_changes에 한태준 기록.
5. **EP16 10 attempts**: 프로젝트 최다 시도. 이전 최다는 EP1의 8 attempts. 금 가격 급락 → 마진콜이라는 복잡한 금융 시나리오가 LLM 생성 난이도를 높인 것으로 추정.
6. **Description 필드 패턴**: EP17, EP19, EP20에서 scene에 `description` 필드 추가 등장. EP1-15에는 없던 필드. LLM ensemble strategy 차이로 추정. Pydantic `extra="allow"`로 허용됨.

## 7. EP16-20 vs EP1-15 비교

| Metric | EP1-15 | EP16-20 |
|--------|--------|---------|
| P1 issues | 3건 (EP8 characters, EP15 timeline×2) | 2건 (EP17 금융단위, EP20 timeline) |
| P2 watchlist | 9 EPs | 3 EPs |
| Clean | 4 EPs | 0 |
| Characters empty | EP8 4/4건 | **0건** — 전량 populated |
| Scene content empty | EP12-14 | EP18-19 (패턴 지속) |
| Timeline drift | EP15 (6주) | EP20 (1개월) |
| Max attempts | EP1 (8) | EP16 (10) |
| Hook quality | 13/14 연결 | 5/5 연결 (100%) |
| Avg score | 90.5 | 88.8 |

핵심 차이:
- **Characters 문제 해소**: EP8의 빈 배열 문제가 EP16-20에서는 재발하지 않음
- **Timeline drift 재발**: EP15와 동일 유형이 EP20에서 재발 — validator hardening 미적용 상태에서 예측 가능한 결과
- **새 결함 유형**: 금융 단위 오류 (EP17) — EP1-15에는 없던 유형

## 8. Fix Shortlist

| Priority | Episode | Repair Mode | Target |
|----------|---------|-------------|--------|
| P1-D | EP17 | local patch | "3,500만 달러/500만 달러" → arc 기준 원화 수치 교체 |
| P1-E | EP20 | local patch (범위 넓음) | time_flow/ending_state.timeline "9월" 보정 + integrated_scenario 시간 점프 삽입 + 50억 원 명시 |

**EP17**: JSON + txt 2파일 수정. 금액 문자열 치환만.
**EP20**: JSON + txt 2파일 수정. 시나리오 본문에 "8월 9일"이 명시되어 있어 단순 필드 교체가 아닌 본문 수정 필요. EP15보다 수정 범위 넓음.

## 9. Recommended Next Move

**`HOLD FOR P1 PATCH`** — P1 2건 수정 후 Stage 4 진행 가능.

근거:
- P0 blocker 0건
- P1 2건 모두 local patch 가능 (재생성 불필요)
- EP17은 금액 문자열 치환 (단순)
- EP20은 시나리오 본문 시간 점프 삽입 필요 (EP15보다 넓음)
- P2 watchlist는 Stage 4 모니터링으로 대응 가능
- Characters 빈 배열 재발 없음

## 10. Survey Confidence

| Pass | Focus | Result |
|------|-------|--------|
| Pass 1 | 5개 blueprint JSON + txt 전량 직접 읽기, UTF-8/구조 확인 | 완료 |
| Pass 2 | Arc 4/5 source truth 교차 검증, EP-to-EP hook/timeline chain | 완료 |
| Pass 3 | decisions.jsonl 교차, 금융 데이터 검증, relationship chain, 소지품 추적 | 완료 |

**Estimated confidence: 96%**

Confidence 제한 요인:
- EP16 failed attempts 1-9의 artifact 미보존 (rejection reason 직접 확인 불가)
- EP17 "3,500만 달러"의 정확한 의도 (원화 혼동 vs USD 계좌 설정)를 LLM I/O 없이 100% 특정 불가 — 다만 arc와의 불일치는 확실

---

*3pass audit completed. Final save.*
