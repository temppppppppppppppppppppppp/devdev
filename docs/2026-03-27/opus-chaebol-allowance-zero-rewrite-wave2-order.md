# OPUS Chaebol Allowance Zero Rewrite — Wave 2 Order

Date: 2026-03-27
Track: narrative pipeline
Status: pending
Scope: single-work OPUS order for `chaebol_allowance_zero`, Wave 2 only

## 1. Order Intent

This order fixes the target to `chaebol_allowance_zero` and asks OPUS to complete exactly one bounded unit:

- `TR rewrite — Wave 2 (Block 16-35)`

Current lane truth:

- family: `blockguide`
- entry type: existing `TR + BI` pair in `_quarantine`
- density-recovery rewrite plan: **complete** (verdict: mixed)
- Wave 1 (Block 7-15): **complete** (8/8 quality gate PASS)
- path truth: **resolved** (`_quarantine` pair is sole live authority)
- the current task is the second execution wave of the density-recovery plan
- Block 16-35 was chosen as Wave 2 because it follows the already-rewritten Wave 1 band and covers the 호텔→공장→병원진입 domain transition

This is not a planning order. This is a bounded rewrite execution order.

## 2. Authority Chain

This order inherits from:

1. `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md` — rewrite plan (SSOT)
2. `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md` — Wave 1 order (pattern reference)
3. `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md` — 4-axis audit findings

Do not re-plan. Follow the plan. Wave 1 rewrite quality is the new density benchmark alongside Block 1-6.

## 3. Non-Negotiable Rules

- UTF-8 only
- read plan + Wave 1 result + audit evidence before doing anything else
- one work, one owner, one wave
- no same-work concurrent editing
- no code or system edits
- rewrite Block 16-35 only — do not touch Block 1-15 or Block 36-70
- do not redesign BI in this run
- do not promote to active path in this run
- do not change arc boundaries or block count
- preserve all 6 fixed creative anchors
- preserve capital continuity chain (capital_before == previous block capital_after)
- preserve foreshadow/callback structure integrity

## 4. Canonical Target

- work_id: `chaebol_allowance_zero`
- TR: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_chaebol_allowance_zero.json` (read-only reference)

Output: overwrite Block 16-35 (array index 15-34) in the canonical TR file.

## 5. Wave 2 Context

| Field | Value |
| ---- | ---- |
| Blocks | 16-35 (20 blocks) |
| Domain Progression | 호텔 백오브하우스(B16-20) → 공장/제조(B21-30) → 병원 진입(B31-35) |
| Capital Range | 17억(B16 entry) → 91억(B35 exit) |
| Loss Blocks | B16 (17→13), B25 (47→45), B35 (94→91) |
| Benchmark | Block 1-6 (original) + Block 7-15 (Wave 1 rewritten) |
| Adjacent Context | Read Block 15 (Wave 1 exit) and Block 36 (Wave 3 entry) for transition continuity |
| Time Span | 2018년 9월 ~ 2019년 하반기 |

### Current Opponents in Block 16-35

Block 16-35에서 윤석진이 거의 전 블록에 걸쳐 동일 archetype으로 반복 등장한다. 이것이 Wave 2의 핵심 문제다.

Rewrite 시 opponent roster 요건:
- 윤석진 등장은 20블록 중 최대 5블록으로 제한
- 나머지 15블록에는 최소 6명의 서로 다른 개별 적대자 배치
- 적대자 유형 혼합 필수: 가문 내부(서도윤, 노현주, 작은어머니 라인) + 외부 실무(공장장, 급식업체, 물류사, 위생검사관, 은행 심사역 등) + 도메인 전환 시 신규 적대자
- 공장/제조 도메인(B21-30) 진입 시 완전히 새로운 적대자 최소 3명 도입

## 6. Rewrite Contract

### 6.1 Mandatory Field Changes

20블록 각각에 적용:

| Field | Requirement |
| ---- | ---- |
| `content.context` | 전면 리라이트. "직전 [제목]에서 X억까지 맞춰 둔 판이 이번 한 번의 흔들림으로 꺾일 수 있다" 삭제. "일회성 민원이 아니라 다음 계약 문장을 누가 쓰느냐의 싸움" 삭제. benchmark band 수준의 구체적 공간/시각/물리적 상황 + 도메인 고유 디테일 |
| `content.event_villain` | 전면 리라이트. "가문 재무 위치에서 [제목]를 가볍게 본다" 삭제. "비용표 숫자만 맞추면" 삭제. 적대자의 구체적 행동/대사/동기. 20블록에 걸친 지능 진화 |
| `content.solution` | 전면 리라이트. "기억를 떠올리며 병목이 터질 순서를 다시 계산" 삭제. "한 장 표로 묶어" 삭제. "반복 수익과 통제권으로 재정의" 삭제. 블록마다 독립된 operational 전술 |
| `content.reward` | 전면 리라이트. "X억에서 Y억로 [늘/줄]어난다. 이번 증가는 단순 수수료가 아니라" 패턴 삭제. 블록 고유 성취 + 대가 |
| `stakes` | 전면 리라이트. "[도메인] 구간에서 다시 외부 수습꾼으로 밀려난다" 삭제. "다음 블록의 문장도 상대가 먼저 쓰게 된다" 삭제. 블록 고유 위험 |
| `power_shift` | 전면 리라이트. "기준표와 책임선을 다시 쓰는 운영 설계자" 삭제. "작은 방해만으로는 그를 지울 수 없다" 삭제. 블록 고유 변화 |
| `genre_ext.opponent.weakness_exploited` | 전면 리라이트. 적대자 고유 맹점. "비용표 숫자만 맞추면 현장 권력도 계속 재무실 아래에 묶여 있다고 믿는 CFO 시야" 같은 반복 삭제 |
| `genre_ext.historical_event` | 20블록 중 최소 5블록에 non-null 배치. 2018-2020 한국 경제: 최저임금 인상(2018-2019), 일본 수출규제(2019.7), 코로나19(2020.1~), 부동산 규제 강화, 공급망 교란 등 |
| `foreshadow` | 전면 리라이트. "[블록제목] 기준 메모는 다음 협상에서 더 비싼 기준표가 된다" 삭제. 블록 고유 복선 |
| `callback` | 전면 리라이트. "[이전블록]에서 남긴 [제목] 기준 메모를 이번 '[블록제목]'의 첫 기준표로 다시 꺼낸다" 삭제. 실제 이전 블록 이벤트와의 구체적 연결 |

### 6.2 보존 필드

| Field | Rule |
| ---- | ---- |
| `block_id` | 유지 (Block 16-35) |
| `title` | 유지 — 기존 제목 보존 |
| `genre_ext.capital_before` / `capital_after` / `capital_delta` / `profit_loss` | 유지 — 기존 자본 수치 보존 |
| `genre_ext.deal_type` | 유지 — 기존 값 보존 |
| `time_span` | 유지 — 기존 시간선 보존 |
| `pov_character` | 유지 — 윤재이 고정 |

### 6.3 Scene Injection Minimum

모든 20개 블록이 충족해야 한다:

| 요소 | 최소 요건 |
| ---- | ---- |
| 직접 대화 | 블록당 2회 이상 |
| 공간/감각 묘사 | 블록당 2개 이상 (도메인 전환 시 새 공간의 고유 감각) |
| 주인공 내면 | 블록당 1개 이상 (전생 기억의 구체적 실패/비용 장면) |
| 상대 반응 | 블록당 1개 이상 (구체적, 단순 패배 선언 불가) |
| 시간 압박 | 블록당 구체적 데드라인 1개 |
| 구체적 실물 아이템 | 블록당 최소 2건 |

### 6.4 Repetition Kill Rules

이 Wave에서 아래 문장/패턴이 단 한 번이라도 등장하면 **실패**:

**context 템플릿:**
1. `"직전 '[제목]'에서 X억까지 맞춰 둔 판이 이번 한 번의 흔들림으로 꺾일 수 있다"` — 또는 이 구조의 변형
2. `"전생 기억 속에서도 바로 이런 [도메인] 병목 하나가 더 큰 계열사 운영권 전쟁으로 번졌고"` — 또는 변형
3. `"이번 일을 일회성 민원이 아니라 다음 계약 문장을 누가 쓰느냐의 싸움으로 본다"` — 또는 변형

**event_villain 템플릿:**
4. `"[이름]은 가문 재무 위치에서 이번 '[블록제목]'를 가볍게 본다"` — 또는 변형
5. `"비용표 숫자만 맞추면 현장 권력도 계속 재무실 아래에 묶여 있다고 믿는 CFO 시야"` — 또는 변형
6. `"시간을 끌고 책임선을 흐리는 쪽이 자기에게 유리하다고 계산하며"` — 또는 변형
7. `"재이가 여기서 한 발 늦으면 다시는 이 구간에 발을 못 붙일 거라 믿는다"` — 또는 변형

**solution 템플릿:**
8. `"기억를 떠올리며 병목이 터질 순서를 다시 계산한다"` — 또는 "순서를 다시 계산" 패턴
9. `"이번 블록의 실물 자료를 한 장 표로 묶어"` — 또는 "한 장 표로 묶어" 패턴
10. `"상대가 비용으로만 보던 것을 반복 수익과 통제권으로 재정의한다"` — 또는 "통제권으로 재정의" 패턴
11. `"이번 구간에서 만들어 낸 데이터와 인력, 지급 조건을 다음 계약까지 이어지는 구조로 묶고"` — 또는 변형

**stakes 템플릿:**
12. `"[도메인] 구간에서 다시 외부 수습꾼으로 밀려난다"` — 또는 변형
13. `"지금까지 모은 자료와 사람은 돈으로 환산되기도 전에 흩어지고, 다음 블록의 문장도 상대가 먼저 쓰게 된다"` — 또는 변형

**power_shift 템플릿:**
14. `"[도메인]의 기준표와 책임선을 다시 쓰는 운영 설계자로 보이기 시작한다"` — 또는 변형
15. `"이제는 작은 방해만으로는 그를 지울 수 없다고 느낀다"` — 또는 변형

**foreshadow/callback 템플릿:**
16. `"[블록제목] 기준 메모는 다음 협상에서 더 비싼 기준표가 된다"` — 또는 변형
17. `"[이전블록]에서 남긴 [제목] 기준 메모를 이번 '[블록제목]'의 첫 기준표로 다시 꺼낸다"` — 또는 변형

**regression_ext:**
18. `"재이의 정보 출처를 의심한다"` — 또는 변형. regression_hint 내 포함 시에도 실패

### 6.5 Solution Diversity Requirement

20개 solution은 블록마다 독립된 operational 전술을 사용해야 한다.

Wave 1 사례 (이미 검증된 독립 전술):
- 분실률 역대조 / 유령인력 증빙 / 법률 리프레이밍 / 법인 분리 / 원가 입찰 / 미끼 정보 유출 / 폐기율 실증 / CCTV-POS 대조 / 유휴공간 재패키징

Wave 2에서도 이 수준 — 20개 블록에 20개 서로 다른 전술. 동일 전술 2회 사용 시 실패.

### 6.6 Villain Intelligence Evolution

- 윤석진이 등장할 때마다 이전 패배에서 배운 새로운 방어/공격 전략 사용
- 서도윤이 등장할 때마다 이전보다 정교한 방해 시도
- 공장 도메인 진입(B21~) 시 완전히 새로운 적대자가 새로운 유형의 위협을 가져와야 함
- 20블록에 걸쳐 적대자의 전체 지능 수준이 점진적으로 상승 — B35의 적대자는 B16의 적대자보다 확실히 영리해야 한다

### 6.7 Domain Transition Density

호텔→공장 전환은 이 Wave의 핵심 서사 이벤트:
- 전환 블록(~B21)에서 재이가 왜 공장으로 가는지의 operational 논리 명시
- 장례식장→호텔 전환(Wave 1)처럼 구체적 사업 연결고리 (예: 호텔 세탁이 산업세탁으로 확장, 급식이 공장급식으로 확장)
- "그냥 다음 도메인으로 넘어간다" 식의 점프 금지

## 7. Fixed Creative Anchors

| Anchor | Wave 2 적용 |
| ---- | ---- |
| Support-system cashflow warfare | 호텔 위생/정산 → 공장 급식/폐기물/세탁 → 병원 진입. B2B 일상경비 조임점 |
| Moneyline > inheritance | 상속 대신 현금흐름 장악이 성장 엔진 |
| No family bailout | 가문 자금 무상 지원 없음 |
| Business growth + office power profile | B2B 계약/운영 단위에서 권한 확보 |
| 호텔→공장→병원 transition | 이 Wave의 3개 도메인 전환이 서사적 사건 |
| Concrete operational detail | benchmark band + Wave 1 수준의 실물 디테일 |

Known drift to avoid:
- 주식/M&A spectacle 전환
- 모든 사업을 "운영사업" 하나로 뭉뚱그리기
- cashflow warfare를 추상적 권력 게임으로 대체
- 공장 도메인을 호텔과 동일한 "백오브하우스" 프레임으로 처리

## 8. Mandatory Reads

Read these before rewriting:

1. `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md` — 전체 플랜
2. `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md` — 4축 감사
3. `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` — 현재 TR (Block 1-15 benchmark + Block 16-35 target + Block 36 context)
4. `bible/_quarantine/0_bi_chaebol_allowance_zero.json` — BI 참조 (read-only, plot_roadmap 확인)
5. `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md` — Wave 1 오더 (pattern/quality reference)

## 9. Deliverable

- 수정된 TR JSON: `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` (Block 16-35 덮어쓰기)

산출물은 TR JSON 파일 수정 1건뿐이다. 별도 보고서는 이 Wave에서 생산하지 않는다.

## 10. Quality Gate (Wave 완료 시 자가 검증)

Wave 2 완료 후 아래 9개 게이트를 자가 검증하라:

1. **템플릿 반복 0**: §6.4의 18개 금지 패턴이 Block 16-35 어디에도 없음
2. **대화 최소치**: 20개 블록 전부 직접 화법 2회 이상
3. **감각 디테일 최소치**: 20개 블록 전부 감각 묘사 2개 이상
4. **주인공 내면 최소치**: 20개 블록 전부 구체적 내면 비트 1개 이상
5. **실물 아이템 최소치**: 20개 블록 전부 구체적 실물 2건 이상
6. **solution 독립성**: 20개 블록의 solution이 서로 다른 operational 전술을 사용. 동일 구조 반복 0
7. **자본 연속성**: capital_before/after 체인 무결성 유지 (Block 15 exit → Block 16 entry … Block 35 exit → Block 36 entry)
8. **historical event 주입**: 최소 5블록에 non-null historical_event 배치
9. **opponent 다양성**: 윤석진 최대 5블록, 서로 다른 개별 적대자 최소 6명, 공장 도메인 신규 적대자 최소 3명

9개 전부 통과 시에만 Wave 2 완료로 인정.

## 11. Stop Conditions

Stop immediately and report if:

- Block 16-35의 기존 내용이 예상 구조와 다른 경우
- BI 참조 데이터와 비동기화된 경우
- solution 리라이트가 plot_roadmap 시퀀스를 파괴하는 경우
- Block 15(Wave 1 exit) 또는 Block 36과의 연결성이 끊기는 경우
- foreshadow/callback 구조가 파괴되는 경우
- 어떤 블록에서든 quality gate를 통과하지 못하는 경우

## 12. Expected Next Unit After This Wave

| 결과 | Next Unit |
| ---- | ---- |
| Wave 2 quality gate 전부 통과 | **TR rewrite — Wave 3 (Block 36-70)** |
| Quality gate 부분 실패 | Wave 2 보수 후 재검증 |
| 구조적 blocker 발견 | Plan 수정 → 재계획 |

## 13. Handoff Format

```text
work_id: chaebol_allowance_zero
current_stage: audit_or_repair
finished_unit: TR rewrite — Wave 2 (Block 16-35)
changed_files: ...
quality_gate: [pass/fail per gate]
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target: chaebol_allowance_zero 단일 work_id 고정
- scope: Block 16-35 only — 다른 블록 수정 없음
- plan 상속: density-recovery rewrite plan §6-8 + Wave 1 패턴 참조
- creative anchor 보존 체크리스트 포함

### Pass 2. Operational Usefulness

- 18개 반복 패턴 금지 명시적 열거 (현재 TR Block 16, 20, 30에서 직접 추출)
- 장면 주입 최소치 정량 지정
- solution 독립성 요건 명시 (20개 unique 전술)
- villain intelligence evolution 요건 명시
- domain transition density 요건 명시
- opponent 다양성 요건 수치 지정
- quality gate 9개 명시

### Pass 3. Integrity

- 산출물: TR JSON 파일 수정 1건만
- UTF-8 only
- 코드/시스템 수정 없음
- 1-wave scope only
- 보존 필드 명시

Confidence:
- 95% that Wave 2 (Block 16-35) is the correct second rewrite unit
- kill rules are extracted from actual TR content at Block 16, 20, 30
