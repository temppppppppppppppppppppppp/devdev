# OPUS Chaebol Allowance Zero Rewrite — Wave 1 Order

Date: 2026-03-27
Track: narrative pipeline
Status: pending
Scope: single-work OPUS order for `chaebol_allowance_zero`, Wave 1 only

## 1. Order Intent

This order fixes the target to `chaebol_allowance_zero` and asks OPUS to complete exactly one bounded unit:

- `TR rewrite — Wave 1 (Block 7-15)`

Current lane truth:

- family: `blockguide`
- entry type: existing `TR + BI` pair in `_quarantine`
- density-recovery rewrite plan: **complete** (verdict: mixed)
- path truth: **resolved** (`_quarantine` pair is sole live authority)
- the current task is the first execution wave of that plan
- Block 7-15 was chosen as Wave 1 because it is the template-repetition entry point and the smallest bounded scope with the clearest benchmark band (Block 1-6) for quality comparison

This is not a planning order. This is a bounded rewrite execution order.

## 2. Authority Chain

This order inherits from:

1. `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md` — rewrite plan (SSOT for how to rewrite)
2. `docs/2026-03-27/opus-chaebol-allowance-zero-density-rewrite-plan-order.md` — plan order context
3. `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md` — 4-axis audit findings

Do not re-plan. Follow the plan as written.

## 3. Non-Negotiable Rules

- UTF-8 only
- read plan + audit evidence before doing anything else
- one work, one owner, one wave
- no same-work concurrent editing
- no code or system edits
- rewrite Block 7-15 only — do not touch Block 1-6 or Block 16-70
- do not redesign BI in this run
- do not promote to active path in this run
- do not change arc boundaries or block count
- preserve all 6 fixed creative anchors
- preserve capital continuity chain (capital_before == previous block capital_after)
- preserve foreshadow payoff timing (Block 12 VIP번호표 payoff must survive)

## 4. Canonical Target

- work_id: `chaebol_allowance_zero`
- TR: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_chaebol_allowance_zero.json` (read-only reference)

Output: overwrite Block 7-15 (array index 6-14) in the canonical TR file.

## 5. Wave 1 Context

| Field | Value |
| ---- | ---- |
| Blocks | 7-15 (9 blocks) |
| Domain Transition | 장례식장(B7-10) → 호텔 백오브하우스(B11-15) |
| Capital Range | 4억(B7 entry) → 17억(B15 exit) |
| Loss Block | B12 (12억→11억) — strategic loss, pattern must survive |
| Benchmark Band | Block 1-6 (density reference, do not modify) |
| Adjacent Context | Read Block 6 (exit) and Block 16 (entry) for transition continuity |

### Current Opponents in Block 7-15

| Block | Opponent | Type |
|-------|----------|------|
| 7 | 강미선 | 장례 세탁실 반장 |
| 8 | 오형택 | 청소 외주 소장 |
| 9 | 노현주 | 가문 법무 |
| 10 | 서도윤 | 가문 오너 라인 |
| 11 | 윤석진 | 가문 재무 |
| 12 | 서도윤 | 가문 오너 라인 |
| 13 | 김태석 | 주차장 야간반장 |
| 14 | 나영수 | 연회장 외주 총괄 |
| 15 | 윤석진 | 가문 재무 |

Opponent roster may be adjusted during rewrite, but the mix of external operators (B7-8, B13-14) and family power players (B9-10, B11-12, B15) must remain balanced. Do not collapse all opponents into one type.

## 6. Rewrite Contract

### 6.1 Mandatory Field Changes

Each of the 9 blocks (7-15) must have:

| Field | Requirement |
| ---- | ---- |
| `content.context` | 전면 리라이트. 감각 디테일 + 시간 압박 주입. 장소명만 나열 불가. benchmark band처럼 구체적 공간/시각/물리적 상황 묘사 |
| `content.event_villain` | 전면 리라이트. 적대자의 구체적 행동/대사/동기로 교체. "가볍게 본다" 일변도 패턴 삭제 |
| `content.solution` | 전면 리라이트. 템플릿 문장 전면 삭제. 블록마다 독립된 operational 전술. benchmark band 수준의 구체성 (구체적 행동 / 실물 도구 / 상대 대응과 좌절 / 비용·대가 / 다음 블록 레버리지) |
| `content.reward` | Heavy edit. 블록 고유 성취 + 대가 명시. 추상적 "운영권" 반복 불가 |
| `stakes` | Heavy edit. 블록 고유 위험 명시. "현금흐름에서 밀려 죽는다" 반복 불가 |
| `power_shift` | Heavy edit. protagonist/antagonist 모두 블록 고유 변화 |
| `genre_ext.opponent.weakness_exploited` | 전면 리라이트. "[직책]로서 [제목]를 단순한 잡무나 비용으로 보고" 템플릿 삭제. 적대자 고유 맹점 적용 |
| `genre_ext.historical_event` | 9블록 중 최소 2블록에 non-null 배치. 2018 한국 경제 맥락 활용 (최저임금 인상, 식자재 원가 급등, 위탁급식 시장 재편 등) |

### 6.2 보존 필드

| Field | Rule |
| ---- | ---- |
| `block_id` | 유지 (Block 7-15) |
| `title` | 유지 — 기존 제목 보존 |
| `genre_ext.capital_before` / `capital_after` | 유지 — 기존 자본 수치 보존. 연속성 체인 유지 |
| `genre_ext.deal_type` | 유지 — 기존 값 보존 |
| `time_span` | 유지 — 기존 시간선 보존 |
| `pov_character` | 유지 — 윤재이 고정 |
| `foreshadow` / `callback` | 유지 — 기존 복선 구조 보존. Block 12의 VIP번호표 payoff 필수 생존 |
| `genre_ext.capital_delta` / `profit_loss` | 유지 — 기존 수치 보존 |

### 6.3 Scene Injection Minimum

모든 9개 블록이 아래를 충족해야 한다:

| 요소 | 최소 요건 |
| ---- | ---- |
| 직접 대화 | 블록당 2회 이상 (윤재이 1, 상대 1) |
| 공간/감각 묘사 | 블록당 2개 이상 감각 디테일 (시각/후각/청각/촉각 중 택) |
| 주인공 내면 | 블록당 1개 이상 (전생 기억의 구체적 실패 장면 또는 비용 인식. 일반적 회상 불가) |
| 상대 반응 | 블록당 1개 이상 (구체적 반응, 단순 패배 선언 불가) |
| 시간 압박 | 블록당 구체적 데드라인 1개 (benchmark band 수준: "조문객 첫날 오전", "12시간 window" 등) |
| 구체적 실물 아이템 | 블록당 최소 2건 (영수증, 계약서, 출입 기록, 식자재 명세서, 린넨 장부 등) |

### 6.4 Repetition Kill Rules

이 Wave에서 아래 문장/패턴이 단 한 번이라도 등장하면 **실패**:

1. `"그는 먼저 전생의 파산은 회장실이 아니라 장례식장, 호텔, 식당 같은 생활비 누수에서 먼저 시작됐다는 기억를 떠올리며"` — 또는 이 문장의 변형
2. `"그는 먼저 호텔 객실보다 린넨, 주차, 미니바 같은 백오브하우스가 더 끊기지 않는 현금흐름을 만든다는 기억를 떠올리며"` — 또는 이 문장의 변형
3. `"병목이 터질 순서를 다시 계산한다"` — 또는 "순서를 다시 계산" 패턴
4. `"이번 블록의 실물 자료를 한 장 표로 묶어"` — 또는 "한 장 표로 묶어" 패턴
5. `"[X]를 단순한 [Y] 잡무나 비용으로 보고, [Z]가 다음 운영권과 정산권으로 이어진다는 사실을 읽지 못한다"` — weakness_exploited 템플릿
6. `"직전 블록에서 X억까지 맞춰 둔 판이 이번 한 번의 흔들림으로 꺾일 수 있다"` — stakes 템플릿
7. `"재이의 정보 출처를 의심한다"` — 70회 반복된 거짓 긴장 패턴. regression_ext 내 포함 시에도 실패

### 6.5 Solution Diversity Requirement

Block 7-15의 9개 solution은 블록마다 독립된 operational 전술을 사용해야 한다.

benchmark band 사례:
- B1: 법률 해석 재프레이밍
- B2: 응급 배식 물류 구축
- B3: VIP 동선 재설계 + 증거 전술
- B4: 계약 구조 반전 + 위협
- B5: 자산 번들링 + 신뢰 구축
- B6: 포렌식 정산 대조

Block 7-15에서도 이 수준의 전술 독립성이 필요하다. "데이터 번들링 → 비용을 통제로 재정의" 단일 패턴을 9번 반복하면 실패.

### 6.6 Villain Intelligence Evolution

적대자가 패배에서 학습하는 흔적이 있어야 한다:

- Block 9 노현주가 Block 1에서 당한 "유언 해석 틈" 공격을 기억하고 다른 방어를 시도해야 한다
- Block 10/12 서도윤이 반복 등장 시 이전 패배에서 전략을 바꿔야 한다
- Block 11/15 윤석진이 동일 약점으로 두 번 당하면 안 된다 — 두 번째 등장 시 다른 공격 벡터 사용

## 7. Factual Blocker Fixes (Wave 1 병행)

이 Wave에서 함께 해소해야 할 factual blockers:

| # | Item | Fix Direction |
|---|------|--------------|
| 1 | Block 13 opponent mismatch | 4축 감사에서 지적된 불일치 확인 후 수정. 현재 김태석(주차장 야간반장)이 맥락상 적절한지 검증 |
| 2 | "재이의 정보 출처를 의심한다" 70회 반복 | Block 7-15 구간에서 이 패턴을 의미 있는 추적 escalation으로 교체. 의심이 구체적 행동으로 이어지는 장면 최소 1회 |

2006 regression hint vs 2018 story start gap은 Wave 1 범위(B7-15) 내에서 직접 해소 가능한 경우에만 처리. 불가능하면 Wave 2로 이월.

## 8. Fixed Creative Anchors

이 작품의 정체성 — rewrite에서 절대 훼손 불가:

| Anchor | Wave 1 적용 |
| ---- | ---- |
| Support-system cashflow warfare | 장례식장 세탁/청소/배식 → 호텔 린넨/주차/미니바/연회장. 일상경비 조임점이 전쟁터 |
| Moneyline > inheritance | 상속 대신 현금흐름 장악이 성장 엔진 |
| No family bailout | 가문 자금 무상 지원 없음. 재이는 자력으로 운영권 확보 |
| Business growth + office power profile | B2B 계약/운영 단위에서 권한 확보. 추상적 권력 게임 불가 |
| Funeral → Hotel transition | B7-10 장례식장 마무리 → B11-15 호텔 백오브하우스 진입. 도메인 전환이 이 Wave의 서사적 사건 |
| Concrete operational detail | benchmark band 수준의 실물 디테일. skeleton plot 불가 |

Known drift to avoid:
- 주식/M&A spectacle 전환
- 모든 사업을 "운영사업" 하나로 뭉뚱그리기
- cashflow warfare를 추상적 권력 게임으로 대체

## 9. Mandatory Reads

Read these before rewriting:

1. `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md` — 전체 플랜
2. `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md` — 4축 감사
3. `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` — 현재 TR (최소 Block 1-6 benchmark + Block 7-15 target + Block 16 context)
4. `bible/_quarantine/0_bi_chaebol_allowance_zero.json` — BI 참조 (read-only, plot_roadmap 확인)
5. `treatments/audit_reports/chaebol_allowance_zero_full_retry_vs_failed_audit.md` — retry 보존 항목 확인

## 10. Deliverable

- 수정된 TR JSON: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` (Block 7-15 덮어쓰기)

산출물은 TR JSON 파일 수정 1건뿐이다. 별도 보고서는 이 Wave에서 생산하지 않는다.

## 11. Quality Gate (Wave 완료 시 자가 검증)

Wave 1 완료 후 아래 8개 게이트를 자가 검증하라:

1. **템플릿 반복 0**: §6.4의 7개 금지 패턴이 Block 7-15 어디에도 없음
2. **대화 최소치**: 9개 블록 전부 직접 화법 2회 이상
3. **감각 디테일 최소치**: 9개 블록 전부 감각 묘사 2개 이상
4. **주인공 내면 최소치**: 9개 블록 전부 구체적 내면 비트 1개 이상
5. **실물 아이템 최소치**: 9개 블록 전부 구체적 실물 2건 이상
6. **solution 독립성**: 9개 블록의 solution이 서로 다른 operational 전술을 사용. 동일 구조 반복 0
7. **자본 연속성**: capital_before/after 체인 무결성 유지 (Block 6 exit 4억 → Block 7 entry 4억 … Block 15 exit 17억 → Block 16 entry 17억)
8. **historical event 주입**: 최소 2블록에 non-null historical_event 배치

8개 전부 통과 시에만 Wave 1 완료로 인정.

## 12. Stop Conditions

Stop immediately and report if:

- Block 7-15의 기존 내용이 plan에서 기술한 것과 구조적으로 다른 경우 (예: 필드 이름 불일치)
- BI 참조 데이터가 Block 7-15 구간과 비동기화된 경우
- solution 리라이트가 plot_roadmap의 해당 시퀀스를 파괴하는 경우
- 리라이트 후 인접 블록(6, 16)과의 연결성이 끊기는 경우
- foreshadow/callback 구조가 파괴되는 경우 (특히 Block 12 VIP번호표)
- 어떤 블록에서든 quality gate를 통과하지 못하는 경우

## 13. Expected Next Unit After This Wave

| 결과 | Next Unit |
| ---- | ---- |
| Wave 1 quality gate 전부 통과 | **TR rewrite — Wave 2 (Block 16-35)** |
| Quality gate 부분 실패 | Wave 1 보수 후 재검증 |
| 구조적 blocker 발견 | Plan 수정 → 재계획 |

## 14. Handoff Format

```text
work_id: chaebol_allowance_zero
current_stage: audit_or_repair
finished_unit: TR rewrite — Wave 1 (Block 7-15)
changed_files: ...
quality_gate: [pass/fail per gate]
next_unit: ...
stop_reason: ...
```

## 15. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target: chaebol_allowance_zero 단일 work_id 고정
- scope: Block 7-15 only — 다른 블록 수정 없음
- plan 상속: density-recovery rewrite plan의 §6-8 지침을 구체화, 재계획 없음
- creative anchor 보존 체크리스트 포함

### Pass 2. Operational Usefulness

- 7개 반복 패턴 금지 명시적 열거 (현재 TR에서 직접 추출한 실제 문장)
- 장면 주입 최소치 정량 지정 (대화/감각/내면/실물/시간압박)
- solution 독립성 요건 명시
- villain intelligence evolution 요건 명시
- quality gate 8개 명시

### Pass 3. Integrity

- 산출물: TR JSON 파일 수정 1건만
- UTF-8 only
- 코드/시스템 수정 없음
- 1-wave scope only
- 보존 필드 명시 (자본 수치, 제목, 시간선, 복선)

Confidence:
- 96% that Wave 1 (Block 7-15) is the correct first rewrite unit
- kill rules are extracted from actual TR content, not hypothesized
