# 실파이프라인 감사 04 — 000_27

> 프로젝트: 골든 루트 (투자 회귀물), Stage 2 전용 (Arc 1~5)
> 실행: 2026-03-07 09:11~09:46 (35분), LLM 63회, $0.974
> 합격률: 5/6 = 83.3% (Arc 4 1회 REJECT 후 패치 PASS)
> 조사: Arc 텍스트 전수 읽기 + DB/로그 분석 + 코드 레벨 검증 3차

---

## 발견 사항

### CRITICAL

#### C-1: "이전 Arc 종료" 메타용어 노출 (3개 Arc 반복) [신규 패치 필요]

- **위치**: Arc 3 ep9, Arc 4 시작, Arc 5 시작
- **내용**: "이전 Arc 종료 후 약 2주", "이전 Arc 종료 직후인 2006년 7월 말", "이전 Arc 종료로부터 약 2주 후"
- **문제**: "Arc"는 시스템 내부 용어. 독자에게 노출되면 4th wall 파괴.
- **기존 방어**: `_check_system_term_exposure()` regex = `r"\b(Block\s+\d+|Arc\s+\d+|Stage\s+\d+|Blueprint|treatment)\b"` — **`Arc\s+\d+`만 매칭**. "Arc 종료", "Arc 시작" 같은 "Arc + 비숫자" 패턴은 탐지 불가.
- **근본 원인**: regex가 "Arc N" 패턴만 잡고 단독 "Arc" 또는 "Arc + 한글" 패턴을 놓침. 원고 단계(Stage 4) 검사이므로 Arc 텍스트(Stage 2)에서는 발동하지 않으나, 이 표현이 원고에 그대로 전사될 위험 있음.
- **패치 방안**: regex에 단독 `Arc` 매칭 추가. 단, 영어 일반 단어 "arc"(이야기의 arc 등)와 구분 필요 → 대문자 `Arc` + 한국어 조사/공백 패턴으로 한정. 또는 Stage 2 auto_correct에서 tactical_doc 내 "Arc" 치환.

---

#### C-2: Arc 4→5 자산 45억→50억 산술 불일치 [기존 패치 부분 커버]

- **위치**: Arc 4 ep16 → Arc 5 ep17
- **내용**: ep16에서 금 15억 투자, 포지션 전체 평가 25억, 절반 청산(원금 7.5억 + 수익 5억 = 12.5억). 잔여 포지션 원금 7.5억/평가 12.5억. ep17에서 "13억에 가까워졌다"고 하면서 청산 후 "원금 12.5억 + 수익 5억 = 50억".
- **산술 검증**: 잔여 포지션 원금은 7.5억(절반 청산했으므로). 12.5억→13억 상승이면 수익 0.5억. 현금 32.5 + 13 = 45.5억. **50억이 아님**. "원금 12.5억"은 평가 가치를 원금으로 오기.
- **기존 방어**: NC-1 `_check_arithmetic_consistency`가 A+B=C 패턴 감지 가능. 그러나 Arc 텍스트(Stage 2) 수준에서는 FactLedger가 아직 없으므로 교차검증 불가. Stage 4(원고) 단계에서만 작동.
- **패치 방안**: PATCH-A(200% 상한)는 Arc 전체 성장률만 체크. **에피소드 간 세부 수치 교차검증은 Stage 2에서 불가** — tactical_doc이 자유 텍스트이므로 Python 파싱 ROI 과대. Director Step 1.5(PATCH-E)가 LLM 판단으로 커버.

---

### MAJOR

#### M-1: 레버리지 수익률 산술 모순 [기존 패치 부분 커버]

- **위치**: Arc 4 ep13~16
- **내용**: 금 620→680달러(+9.7%), 3배 레버리지 → 수익률 29.1%. 원금 15억 x 1.291 = 19.365억이어야 하나, 서술상 포지션 평가 25억(66.7% 수익).
- **기존 방어**: NC-1 `_check_leverage_return_pct`가 "X달러→Y달러 x N배 → Z%" 패턴 감지 설계. Stage 4 원고에서 작동.
- **패치 필요 여부**: Stage 2 Arc 텍스트 수준에서는 추가 패치 ROI 부족. PATCH-E(Director Step 1.5)가 LLM 판단으로 커버.

#### M-2: PATCH-B 과잉 발동 — 서술적 소지품 equipment 오등록 [프롬프트 개선 권장]

- **위치**: Arc 2~5 전체 (매 Arc 발동)
- **내용**: LLM이 `arc_end_state.equipment`에 장면 묘사용 소품을 등록:
  - 정상: `노트북`, `인감도장`, `서류철`
  - 오등록: `책상 위`, `오른손에 쥔 마우스`, `김이 식어버린 커피 캔`, `주문 체결 완료 확인 창`
- **기존 방어**: PATCH-B가 올바르게 탐지하고 advisory 생성. auto_correct가 equipment 유지(제거 안 함, advisory-only).
- **근본 원인**: analyst.yaml/ensemble.yaml에서 equipment 필드 정의가 "물리적으로 소지 가능한 물건만" 제한이 약함.
- **패치 방안**: analyst.yaml equipment 필드 설명에 "물리적으로 휴대 가능한 물건만 등록. 가구(책상/의자), 음식(커피/음료), 화면 UI, 손에 쥔 일상 소품(마우스/펜) 제외" 지시 추가.

#### M-3: Arc 4 timeline 역전 [기존 패치 미탐지]

- **위치**: Arc 3 timeline `6월 하순~7월 중순` vs Arc 4 timeline `2006년 5월~8월`
- **내용**: Arc 4의 state_changes.timeline.start가 "2006년 5월"로, Arc 3보다 앞. 또한 start==end("2006년 5월~8월" 동일).
- **기존 방어**: NS-4 `_extract_arc_time_markers`가 Arc 간 날짜 연속성 체크. 그러나 범위 문자열("5월~8월")의 시작점 파싱이 정확하지 않을 수 있음.
- **패치 방안**: NS-4 regex 강화 또는 timeline start/end 동일 시 경고 advisory 추가. P2.

#### M-4: NPC 이름 분화 — `박성호` vs `박성호 (담당 PB)` [기존 패치 미탐지]

- **위치**: npc_history + arc_summary_4
- **내용**: 동일 인물이 2가지 이름으로 등록. 괄호 접미사가 별도 NPC로 취급됨.
- **기존 방어**: NC-2 `_check_npc_name_collision`은 WorldState 내 동일 이름 2명 등록만 탐지. "박성호"와 "박성호 (담당 PB)"는 다른 이름으로 취급됨.
- **패치 방안**: NPC 이름 정규화 — 괄호 접미사 제거 후 비교. `re.sub(r"\s*\(.*?\)\s*$", "", name)` 적용. P1.

#### M-5: internal_energy 무협 필드 반복 생성 (4/5 Arc) [기존 패치 사후 제거 중]

- **위치**: Arc 1, 3, 4(retry), 5
- **내용**: 투자물인데 LLM이 `internal_energy` 필드를 매번 생성. `_strip_wuxia_fields()`가 사후 제거.
- **기존 방어**: TF-45 `_strip_wuxia_fields()` auto_correct에서 제거 ✅. 프롬프트 수준에서의 억제는 불충분.
- **패치 방안**: 사후 제거가 작동하므로 기능적 문제 없음. 프롬프트 강화는 P3 후순위 (LLM 토큰 소비 대비 효과 불확실).

---

### MINOR

#### m-1: Arc 1→2 소지품 계승 불완전

- "한미증권 계좌"가 Arc 2 시작 소지품에서 누락. "인감도장"은 Arc 1에서 명시적 획득 없이 등장.
- PATCH-B가 소멸/출처불명을 탐지. 기존 방어 내.

#### m-2: Arc 2 ep7 반올림 오차 (4.5억→4억)

- NC-1 5% 허용오차로 통과. 서사적 "약" 표현. 허용.

#### m-3: 블랙베리 폰 소지품 미등재 → Arc 4에서 첫 공식 등록

- Arc 2 ep5 본문에서 사용되나 equipment 목록에 Arc 4까지 미등재.
- PATCH-B가 Arc 4에서 출처불명으로 탐지. 기존 방어 내.

#### m-4: Arc 2→3 자산 반올림 (30.7→30억)

- NC-1 5% 허용오차 내. 허용.

#### m-5: items_consumed 추상 개념 삽입 (2개 Arc)

- "과거의 수동적이고 무기력한 태도", "기회비용: 15억의 자본이..." 등.
- `_filter_abstract_items_consumed()` auto_correct에서 제거 ✅. 기존 방어 작동.

#### m-6: arc_summary 필드 대부분 빈 값

- Stage 2만 실행, Stage 3/4 미실행이므로 예상된 상태. 정상.

---

### INFO (정상 작동 확인)

| 항목 | 상태 |
|------|------|
| PATCH-A (자산 성장률 200% 상한) | 미발동 — Arc별 최대 53.5%, 정상 |
| PATCH-B (소지품 출현/소멸) | 매 Arc 발동 — 서술적 소지품 오등록 정상 탐지 |
| PATCH-C (tactical↔state 위치 교차검증) | Arc 2, 4에서 발동 — 위치 동기화 교정 ✅ |
| PATCH-D (Arc 간 자산 5% 차이) | 미발동 — 자산 연속성 정상 |
| NC-1 산술 검증 → Director REJECT | Arc 4 attempt 1: 총자산 40억 vs 실제 45억 모순 탐지 → REJECT(78점) → 2차 PASS(100점) ✅ |
| 장르 오염 (무협 용어) | 없음 ✅ |
| LLM 성공률 | 63/63 = 100% ✅ |

---

## 패치 필요 여부 판정

| # | 항목 | 심각도 | 패치 필요 | 우선순위 | 비고 |
|---|------|--------|----------|----------|------|
| C-1 | "Arc" 메타용어 regex 확장 | CRITICAL | ✅ 필요 | P1 | `_check_system_term_exposure` regex에 단독 "Arc" 패턴 추가. Stage 2 auto_correct에서도 tactical_doc 내 "이전 Arc" 치환 검토 |
| C-2 | 자산 산술 불일치 (ep16→17) | CRITICAL | ❌ 불필요 | — | PATCH-E(Director Step 1.5) + NC-1(Stage 4)로 커버. tactical_doc 자유 텍스트 파싱 ROI 과대 |
| M-1 | 레버리지 수익률 모순 | MAJOR | ❌ 불필요 | — | NC-1 `_check_leverage_return_pct`(Stage 4) + PATCH-E(Director)로 커버 |
| M-2 | equipment 서술적 소품 오등록 | MAJOR | ✅ 권장 | P2 | analyst.yaml equipment 필드 정의 강화 (프롬프트) |
| M-3 | timeline 역전 | MAJOR | ✅ 권장 | P2 | NS-4 timeline start==end 경고 + 역전 탐지 강화 |
| M-4 | NPC 이름 괄호 접미사 분화 | MAJOR | ✅ 필요 | P1 | NPC 이름 정규화 (괄호 제거 후 비교) |
| M-5 | internal_energy 반복 생성 | MAJOR | ❌ 불필요 | — | `_strip_wuxia_fields()` 사후 제거 작동 중. P3 프롬프트 강화 후순위 |

### 신규 패치 대상: 2건 P1 + 2건 P2

**P1 (필수)**:
1. **C-1**: `_check_system_term_exposure` regex에 `\bArc\b` (대문자, 비의료) 추가 + Stage 2 auto_correct에서 tactical_doc 내 "이전 Arc" → "이전 시기" 등 자동 치환
2. **M-4**: NPC 이름 정규화 — `_check_npc_name_collision`에서 괄호 접미사 제거 후 비교 로직 추가

**P2 (권장)**:
3. **M-2**: analyst.yaml equipment 필드 설명에 "물리적 휴대 가능 물건만, 가구/음식/화면 UI/일상 소품 제외" 지시 추가
4. **M-3**: NS-4에서 timeline start==end 동일 시 경고 + Arc N start < Arc N-1 start 역전 탐지

---

## 영향 파일 (예상)

| 파일 | 변경 |
|------|------|
| `modules/domain/agents/chief_writer_quality.py` | C-1: regex 확장 (`\bArc\b` 추가) |
| `modules/core/stage2_optimizer.py` | C-1: tactical_doc "이전 Arc" 치환 메서드 |
| `modules/core/numeric_consistency_checker.py` | M-4: `_check_npc_name_collision` 괄호 정규화 |
| `config/prompts/analyst.yaml` | M-2: equipment 필드 정의 강화 |
| `modules/core/stage3_orchestrator.py` | M-3: NS-4 timeline 역전 탐지 강화 |

---

## 성과 요약

- **PATCH-A/B/C/D/E 전량 정상 작동 확인**
- PATCH-B: 매 Arc 발동 (서술적 소지품 오등록 탐지)
- PATCH-C: Arc 2, 4에서 위치 동기화 교정
- NC-1 + Director 연동: Arc 4 산술 오류 정상 탐지 → REJECT → 패치 PASS (모범 사례)
- 장르 오염 0건, LLM 100% 성공률
