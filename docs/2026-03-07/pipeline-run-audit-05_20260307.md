# Pipeline Run Audit 05 — 000_01 (Post-Patch Run)

> 실행: 2026-03-07 10:48~11:28 (40분)
> 프로젝트: `projects/000_01` (골든루트 투자물, Block 1~5, Arc 5개, Ep 1~25)
> 모델: gemini-2.5-pro (718K tok, $1.34) + gemini-2.5-flash (189K tok, $0.05) = $1.38
> LLM 호출: 76회, 성공률 100%, 재시도 0회
> 전수조사: 3회 + TF 심층 2회 + 인과 확정 조사 1회 (Arc 5개 전문 + runtime_audit 19건 + decisions 16건 + Treatment Block 1~5 교차검증 + 코드 경로 추적 + 에피소드별 이벤트 출처 대조)

---

## 1. 실행 요약

| Arc | Ep 범위 | 에피소드 수 | 시도 | 최종 점수 | 비고 |
|-----|---------|-----------|------|-----------|------|
| 1 | 1~6 | **6** | 2 | 100 | 1차 REJECT(85, 자본금 계산 오류) → 패치 → PASS |
| 2 | 7~10 | **4** | 1 | 100 | 1차 PASS |
| 3 | 11~15 | 5 | 3 | 100 | 1차 REJECT(40, V61 Entity 불일치 3건) → 2차 REJECT(40, 동일) → 3차 PASS |
| 4 | 16~20 | 5 | 1 | 98 | PASS_WITH_FIX(98) → InPlace 패치 → PASS |
| 5 | 21~25 | 5 | 1 | 100 | 1차 PASS |

- **합격률**: 5/8 = 62.5% (1차 통과 3/5 = 60%)
- **auto_correct 발동**: 8회 (Arc당 평균 1.6회)
- **패치 모드 사용**: Arc 1 (score 85 → partial rewrite)
- **에피소드 분배 불균등**: Arc 1=6화, Arc 2=4화, Arc 3~5=5화 (총 25화 일치)

---

## 2. TF 심층 조사 결과

### TF-A (P0, CRITICAL): Director PASS 시 NS-3-B + Phase 3 Validator 전체 bypass

**코드 경로**: `four_phase_arc_generator.py:650-710`

**현상**: Director가 `compare_and_select_arc()`에서 PASS 또는 PASS_WITH_FIX를 반환하면 L687/L710에서 **즉시 `return`**. Phase 2.55(L742, `_check_arc_end_state` + NS-3-B)와 Phase 3 Validator(L770)에 **도달하지 않음**.

```
Phase 2 (Ensemble) → Phase 2.5 (location 강제) → Phase 2.6 (Director)
                                                      ↓ PASS → return (L687)
                                                      ↓ PASS_WITH_FIX → return (L710)
                                                      ↓ REJECT → continue
Phase 2.55 (NS-3-B + arc_end_state 점검)  ← Director REJECT 시에만 도달
Phase 3 (Validator)                        ← Director REJECT 시에만 도달
```

**영향**: Arc 3의 `total_assets=131억` vs Treatment `capital_after=30억` (337% 괴리)를 NS-3-B가 감지할 수 있었으나, Director가 100점 PASS를 줬기 때문에 NS-3-B가 **실행조차 되지 않음**. DB 로그 검증:
- `llm_calls` 76건 중 NS-3-B 관련 흔적 0건
- `stage_attempts` Arc 3 attempt 3: `verdict=PASS, score=100, fix_scope=inplace`

**근본 원인**: Director PASS 경로가 Python 검증 체인을 완전히 우회하는 구조. 대원칙 3(Director 주권주의)과 충돌하지만, **Python 사실 검증(산술/수치 교차검증)은 LLM 판단이 아닌 사실 확인이므로 Director 주권 범위 밖**.

**패치 방안**:
- (A) NS-3-B를 Phase 2.6 Director 선택 **직전**(L650 직전)으로 이동. 경고를 `compare_and_select_arc()` 컨텍스트에 주입하여 Director가 참고.
- (B) Director PASS 반환 후, `return` 전에 NS-3-B만 실행. 괴리 > 임계값(예: 100%) 시 REJECT 강제 (Python 사실 검증이므로 대원칙 위반 아님).
- **권장**: (A) — Director에 정보 제공 후 판단 위임. 대원칙 3 완전 준수.

---

### TF-B (P0, CRITICAL): Block 경계 제약 부재 — LLM 이벤트 흡수/선취 무방비

**코드 경로**: `config/prompts/ensemble.yaml:48-49`

**현상**: ensemble.yaml의 `{curr_block}` 섹션 헤더는 `[현재 블록 DNA]`이지만, **"이 블록의 사건만 사용하라"**, **"다른 블록의 이벤트를 선취하지 마라"** 같은 경계 제약 지시문이 없음.

**영향**:
- Arc 1(6화)이 Block 1 + Block 2 이벤트(WTI 진입)를 흡수
- Arc 2(4화)가 Block 2~3 이벤트(WTI 전량 청산)를 조기 소화
- Arc 3에서 Block 3 소재(WTI 부분 익절) 소진 → LLM이 100억 대여금 + 이세진 영입을 창작하여 소재 부족 보충

**근본 원인 체인**:
```
Block 1 content 1,368자(1000~1500구간) → Analyst target=5화, 스키마 "3~7" → LLM 6화 선택
→ Block 1 핵심 이벤트 4개 vs 6화 → 2화 부족분을 Block 2 이벤트로 충당 (Ep 5: PB 만남, Ep 6: WTI 진입)
→ Arc 2에서 Block 2 잔여 소재만으로 WTI 전량 청산 → Block 3-4 이벤트 진부화
→ Arc 3에서 콘텐츠 진공 → 100억 대여금 + 이세진 NPC 창작
```

**패치 방안**:
- (A) ensemble.yaml에 Block 경계 제약 규칙 추가:
  ```
  [블록 경계 규칙]
  - 현재 블록 DNA에 명시된 사건만 이 Arc에서 다루어라.
  - 다른 블록의 핵심 사건(event_villain, solution, reward)을 선취하거나 조기 소화하지 마라.
  - 블록 DNA에 없는 대규모 사건(자금 유입, 핵심 NPC 등장 등)을 독자 창작하지 마라.
  ```
- (B) Treatment Block N의 핵심 키워드를 "이 Arc에서만 다룰 사건" 목록으로 프롬프트 주입
- **권장**: (A) + (B) 병행. (A)는 일반 규칙, (B)는 구체적 사건 리스트.

---

### TF-C (P1, MAJOR): genre_ext.capital_after 강제력 부재

**코드 경로**: `arc_ensemble.py:496-507`

**현상**: genre_ext 가이드가 `"Arc 설계 시 반드시 반영하세요"`라는 모호한 지시로만 전달. capital_after=30억이라고 알려줘도 LLM이 131억으로 설정 가능. **advisory일 뿐 REJECT 트리거가 아님**.

**DB 검증** (NS-3-B는 `total_assets` 우선 검색 — LLM이 capital=현금, total_assets=전체자산으로 분리):
```
Arc 1: total_assets="18억 6천만" vs capital_after="20억"  → -7% (허용)
Arc 2: total_assets="32억 3천만" vs capital_after="23억"  → +40% 괴리
Arc 3: total_assets="131억 3천만" vs capital_after="30억" → +337% 괴리
Arc 4: total_assets="136억 3천만" vs capital_after="45억" → +203% 괴리
Arc 5: total_assets="141억 3천만" vs capital_after="50억" → +183% 괴리
```

**NS-3-B 키 검색 순서**: `("total_assets", "assets", "capital", "total_capital")` 순. LLM이 `capital`(현금)과 `total_assets`(전체자산) 둘 다 생성하여 값이 다름(Arc 4: capital=116억, total_assets=136억). Treatment `capital_after`는 전체자산 의미이므로 `total_assets`와 비교가 적절하나, 키 이름 혼동이 괴리율 판단에 영향.

**패치 방안**:
- (A) genre_ext_guide 지시문 강화: `"반드시 반영"` → `"arc_end_state의 capital 값은 이 범위 이내여야 합니다: {capital_after}"`
- (B) NS-3-B를 TF-A 패치와 연동하여 Director 선택 전에 실행, 경고를 Director 컨텍스트에 주입
- (C) NS-3-B 키 검색: `capital`을 `total_assets`보다 우선 검색 (투자물에서 capital이 더 직관적)

---

### TF-D (P1, MAJOR): Episode 수 결정 로직 — content length 기반 편향

**코드 경로**: `analyst.py:653-663, 869`

**현상**: Analyst가 content 길이로 ep_count를 추정:
```python
if content_len < 500: original_guess = 4  # → 3화
elif content_len < 1000: original_guess = 5  # → 4화
elif content_len < 1500: original_guess = 6  # → 5화
else: original_guess = 7  # → 6화 (max)
# target = max(3, min(7, original_guess - 1))
```

Block 1 content 1,368자(1000~1500 구간) → analyst target=5, 스키마 "3~7" → LLM 6화 선택 → Block 2 이벤트까지 흡수해야 6화 분량 확보.

**범위 불일치**: 코드상 하드 클램프는 3-7 (`MIN_EPISODES_PER_ARC=3, MAX_EPISODES_PER_ARC=7`). Pacing guide 텍스트는 "Blitz:2-3 / Standard:3-4 / Epic:5-6". 유저 의도는 **2-6 범위**인데 실제 MAX가 7.

**영향**: Block 1이 6화를 받으면 해당 블록의 소재만으로는 부족 → 인접 블록 이벤트 흡수.

**패치 방안**:
- (A) `MAX_EPISODES_PER_ARC`를 6으로 변경 (유저 의도 반영)
- (B) `original_guess - 1` 로직 제거 → content 길이와 무관하게 Treatment block의 이벤트 밀도로 결정
- (C) Treatment block에 `recommended_ep_count` 필드 추가, Analyst가 이를 우선 참조
- **권장**: (A) — 즉시 적용 가능, 부작용 최소.

---

### TF-E (P2, MINOR): items_acquired 전 Arc 미등록 — PATCH-B 다발 원인

**DB 검증**: 5개 Arc 전부 `items_acquired = []` (빈 배열). LLM이 `equipment`에는 아이템을 넣으면서 `items_acquired`를 비워서 반환.

**영향**: auto_correct에서 `[PATCH-B] 출처 불명 소지품` 경고가 5개 Arc 전부에서 발동. equipment에 있지만 items_acquired에 미등록이므로 "출처 불명"으로 판정.

**패치 방안**:
- (A) ensemble.yaml 스키마 설명 강화: items_acquired에 "이 Arc에서 새로 등장한 아이템은 반드시 여기에도 기입"
- (B) auto_correct에서 equipment diff → items_acquired 자동 보충 (Python, LLM 판단 불필요)

---

### TF-F (INFO): NPC 창작 — 모순 관점 평가

**전제**: NPC 창작 자체는 허용. **모순 관점에서만** 평가.

| NPC | 창작 여부 | 모순 유무 | 상세 |
|-----|----------|----------|------|
| 이세진 (Arc 3~5) | 창작 | **모순** | Treatment "마이클 첸"(Block 7, 해외 파트너)을 대체. 합류 시점·인물 배경·역할이 Treatment과 불일치. Block 3 시점에 핵심 파트너가 이미 합류 → Block 7 마이클 첸 등장 시 역할 충돌 가능 |
| 다니엘 킴 (Arc 3 att.1) | 창작 → REJECT 후 소멸 | 해당 없음 | V61에서 걸러짐 |
| 박성호 (Arc 2~4) | Treatment 등록 | 정합 | Treatment Block 2~4에서 등장, 역할 일치 |

**핵심 모순**: "이세진"이 마이클 첸의 역할(파생상품 전문가, 핵심 파트너)을 선취. 향후 Block 7에서 마이클 첸이 등장할 때 역할 중복 발생. Treatment의 NPC 등장 시점 계획이 무력화됨.

---

## 2.5. 왜 지랄이 나는가 — 99% 확신 인과 분석

> 에피소드별 이벤트 출처 대조 + DB 실측 + 코드 경로 추적으로 확정.

### 핵심 결론

**Arc 1이 Block 2 이벤트를 흡수**한 것이 모든 문제의 시발점. 이후 도미노처럼 무너졌다.

### Step 1: Arc 1이 왜 6화를 받았나

```
Block 1 enriched content → _extract_content_parts() → 1,368자
analyst.py L653-660:
  1000 < 1368 < 1500 → original_guess = 6
  target_ep_count = max(3, min(7, 6-1)) = 5
```

Python은 **5화**를 권장했다. 하지만:
- `ensemble.yaml L71`: `"ep_count": "3~7 중 사건 밀도에 맞게 결정"`
- `pacing_guide`: `"시스템 권장: 5화 (Blitz:2-3 / Standard:3-4 / Epic:5-6)"` — **feedback일 뿐, 스키마 제약이 아님**
- LLM이 6화를 선택. JSON 스키마가 "3~7"을 허용하므로 **위반이 아님**.

### Step 2: 6화를 채우려면 Block 1 소재가 부족했다

Block 1의 핵심 이벤트 4개:

| 에피소드 | 이벤트 | 출처 |
|---------|--------|------|
| 1화 | 2024년 죽음 → 2006년 회귀 | **Block 1** context |
| 2화 | 아버지 서재 — "투자사 차리겠다" 선언 | **Block 1** event_villain |
| 3화 | 자산 정리 → 20.3억, SW인베스트먼트 법인 설립 | **Block 1** solution |
| 4화 | 여의도 사무실, 블룸버그 터미널, 싱가포르 UOB 계좌 (비용 1.7억 → 18.6억) | **Block 1** reward 확장 |
| **5화** | **PB 박성호 만남, WTI 3x 레버리지 매수 계획** | **Block 2** event_villain |
| **6화** | **이란 핵 뉴스, WTI 18.3억 3x 롱 진입 (55억 포지션)** | **Block 2** solution + reward |

**Arc 1 Ep 5-6은 Block 2의 이벤트를 그대로 사용했다.** 코드에서 이를 막는 장치는 **없다**:
- `ensemble.yaml`에 "이 블록의 이벤트만 사용하라"는 지시문 없음
- `arc_draft_validator.py`에 블록 경계 검증 없음
- Director는 서사 품질만 판단 — 이벤트 출처를 검증하지 않음

### Step 3: Arc 2에서 Block 2 이벤트가 이미 소진된 상태

Arc 2는 Block 2를 받지만, Block 2의 핵심 이벤트(WTI 진입)는 **Arc 1 Ep 5-6에서 이미 수행됨**.

Arc 2가 받은 상태:
```
arc_start_state.capital = "3천만 원" (유동 현금)
arc_start_state.total_assets = "18억 6천만" (현금 + WTI 포지션 18.3억)
```

Block 2 content의 이벤트들:
- "법인 설립 완료, 계좌 개설" → **Arc 1 Ep 3-4에서 이미 수행**
- "박성호 PB 만남" → **Arc 1 Ep 5에서 이미 수행**
- "이란 핵 농축 재개, 유가 60→65" → **Arc 1 Ep 6에서 이미 수행**
- **Block 2의 4개 핵심 이벤트 중 3개가 Arc 1에 의해 선소비됨**

Arc 2 LLM은 남은 소재로 4화를 채워야 함 → 독자 창작 발생:
- Ep 7: OPEC 증산 루머 + 마진콜 위기 (Block 2에 **없는** 이벤트)
- Ep 8: 증거금 추가 투입, V자 반등 (Block 2에 **없는** 이벤트)
- Ep 9: WTI 78달러 전량 청산 → 32.3억 (Block 4 이벤트 선취)
- Ep 10: 박성호 충성 + 아버지 통화 + 서브프라임 힌트

**자본 계산**: 18.3억 × 3x leverage × WTI 30% 상승(60→78) ≈ 16.5억 수익 → 총 34.8억. 비용 차감 → **32.3億**. LLM은 레버리지 수익률을 정직하게 계산했다. 문제는 Block 2 목표(23億)와의 괴리인데, 이는 **Arc 1이 너무 큰 포지션(18.3億 전액)을 이미 잡았기 때문**. Treatment는 더 작은 포지션/낮은 레버리지를 전제했다.

Director: **PASS (score 100)** → NS-3-B bypass → **40% 괴리 무감지**.

### Step 4: Arc 3에서 콘텐츠 진공 → 100億 대여금 창작

Arc 3은 Block 3을 받지만:

| Block 3 이벤트 | 상태 |
|---------------|------|
| "유가 70달러 횡보" | **무의미** — Arc 2에서 WTI 전량 청산 완료, 보유 포지션 없음 |
| "에콰도르 석유사 계약 해지 → 유가 상승" | **무의미** — 이미 WTI 전부 나감 |
| "부분 익절 15億→20億" | **불가능** — 청산 완료, 부분 익절할 포지션 없음 |
| "박성호 PB 태도 변화" | **완료** — Arc 2 Ep 10에서 이미 충성 맹세 |

**Block 3의 4개 핵심 이벤트가 전부 stale(진부화)**. LLM에게는 **콘텐츠 진공** 상태.

LLM의 대응: 자체 이벤트 창작으로 5화 채움
- Ep 11: 서브프라임 준비, 퀀트 전문가 물색 (Block 3에 없음)
- Ep 12: **이세진 영입** (Block 3에 없음 — Block 7의 "마이클 첸" 역할 선취)
- Ep 13: 이세진의 시험 과제 (Block 3에 없음)
- Ep 14: 아버지에게 **100億 대여금** 요청 (Block 3에 없음)
- Ep 15: 대여금 수령 → 자본 31.3+100 = **131.3億** (Block 3 목표 30億 대비 337% 괴리)

Director: V61 Entity REJECT ×2 → 3차 PASS (score 100) → NS-3-B bypass → **337% 괴리 무감지**.

### Step 5: 도미노 요약

```
[Step 1] analyst → 5화 권장, 스키마 "3~7" → LLM 6화 선택
         ↓ (+1화 부족분)
[Step 2] Arc 1 Ep 5-6 → Block 2 이벤트 흡수 (PB 만남 + WTI 진입)
         ↓ (Block 2 이벤트 3/4 선소비)
[Step 3] Arc 2 → 잔여 소재 부족 → 마진콜 독자 창작 + WTI 전량 청산
         ↓ (Block 3-4 이벤트 진부화: 보유 포지션 없음)
         ↓ Director PASS (100) → NS-3-B skip → 40% 괴리 통과
[Step 4] Arc 3 → 콘텐츠 진공 → 이세진 + 100億 대여금 창작
         ↓ Director PASS (100) → NS-3-B skip → 337% 괴리 통과
[Step 5] Arc 4-5 → 괴리된 궤도에서 계속 주행 (+91億 유지)
```

### 누가/무엇이 이 체인을 끊을 수 있었나

| 방어선 | 가능했나 | 왜 실패했나 |
|--------|---------|-----------|
| analyst target_ep_count=5 | 권장만 함 | ensemble.yaml 스키마 "3~7" → LLM 무시 가능 |
| ensemble.yaml 블록 경계 규칙 | **존재하지 않음** | `{curr_block}` 헤더만 있고 "이 블록만" 지시 없음 |
| genre_ext_guide "반드시 반영" | advisory only | `arc_ensemble.py:503` 텍스트 지시만, REJECT 트리거 아님 |
| NS-3-B Python 검증 | **실행 안 됨** | Director PASS → L687/L710 return → L747 미도달 |
| Director 심사 | 서사 품질만 봄 | 자본 40-337% 괴리를 감지하는 능력/지시 없음 |
| arc_draft_validator | 블록 경계 미검증 | 아이템/NPC/구조만 검증, 이벤트 출처 미검증 |

### 결론: 4개 버그의 연쇄, 단일 버그가 아님

**어느 하나만 고쳐도 체인이 끊어진다**:
- TF-D 수정(MAX=6) → Block 1이 5화 → Block 2 이벤트 흡수 안 함
- TF-B 수정(경계 규칙) → LLM이 Block 2 이벤트 사용 불가
- TF-C 수정(강제력) → LLM이 capital_after 목표 준수
- TF-A 수정(NS-3-B 실행) → Arc 2에서 40% 괴리 감지 → REJECT → 궤도 복귀

**가장 효과적인 패치 순서**: TF-B(경계) > TF-A(NS-3-B) > TF-D(MAX=6) > TF-C(강제력)
- TF-B는 근본 원인(이벤트 흡수)을 차단
- TF-A는 안전망(괴리 감지)을 복원
- 둘 다 해야 2중 방어

---

## 3. 기존 발견 사항 (전수조사 기반)

### P0-2: 자본금 Treatment 대비 대폭 괴리 (Arc 2~5 전파)

(TF-A, TF-B, TF-C에서 근본 원인 3건 식별 — 상세는 TF 섹션 참조)

| 구간 | Treatment 자본 | Arc 자본 | 괴리 | 근본 원인 |
|------|---------------|----------|------|----------|
| Block/Arc 1 종료 | 20억 | 18억 6천만 (total_assets) | -1.4억 | 허용 범위 (WTI 미실현 포함) |
| Block/Arc 2 종료 | 23억 (미실현) | 31억 3천만 (실현) | **+8억** | TF-B: Block 경계 부재 → WTI 전량 조기 청산 |
| Block/Arc 3 종료 | 30억 | 131억 3천만 | **+101억** | TF-B: 소재 고갈 → 100억 대여금 창작 |
| Block/Arc 4 종료 | 45억 | 136억 3천만 | **+91억** | 전파 |
| Block/Arc 5 종료 | 50억 | 141억 3천만 | **+91억** | 전파 |

**근본 원인 체인 (TF 통합)**:
```
TF-D: Block 1 content 1,368자 → analyst target=5, 스키마 "3~7" → LLM 6화 선택
  → TF-B: Block 경계 없음 → Ep 5-6에서 Block 2 이벤트 흡수 (PB 만남 + WTI 진입)
    → Arc 2: 잔여 소재로 WTI 전량 청산 (Block 3-4 이벤트 진부화)
      → Arc 3: 콘텐츠 진공 → 100억 대여금 + 이세진 NPC 창작
        → TF-A: Director PASS → NS-3-B skip → 337% 괴리 무감지
          → Arc 4~5: 괴리 궤도 유지
```

### P1-1: 여의도/강남 위치 혼동 지속 (Arc 1~3)

| Arc | Arc 위치 | Treatment 위치 | 정합 |
|-----|---------|---------------|------|
| 1 (Block 1) | 성북동 → **여의도** 사무실 | 성북동 본가 | Block 1에 사무실 위치 미명시 |
| 2 (Block 2) | **여의도** 사무실 | 여의도, 한미증권 VIP룸 (방문지) | LLM이 방문지를 사무실로 혼동 |
| 3 (Block 3) | **여의도** → 강남 역삼동 | **강남** SW인베스트먼트 | 시작 불일치, 종료 시 이전 fabricate |
| 4~5 | 강남 | 강남 | 정합 |

### P1-2: PATCH-B 출처 불명 소지품 전 Arc 발동

**근본 원인**: TF-E 참조 — items_acquired 전 Arc 빈 배열.

### P2-1: Arc 3 V61 Entity 명칭 불일치 2회 REJECT

"[V61] Entity 명칭 불일치 3건"으로 2회 연속 REJECT (score 40). 3차에서 PASS. 구체적 불일치 Entity 로그 미기재.

### P2-2: auto_correct 이전 Arc 소지품 소멸 반복

Arc 2~5에서 이전 Arc 소지품 소멸 경고 반복. 투자물 장르 특성(문서/계약서 빈번 변경)으로 과민 반응 가능성.

### P2-3: internal_energy 필드 잔존 (Arc 4, 5)

DB 검증: Arc 4 arc_end_state에 `internal_energy: 0` 잔존. TF-45 auto_correct가 Arc 1,3에서는 제거 성공했으나 Arc 4에서 제거 실패. Arc 5에서는 "시작 내공 수정: 100% → 0%" 값 보정만 발생.

---

## 4. 긍정적 발견

| 항목 | 상태 |
|------|------|
| C-1 메타용어 치환 | Arc 2~5에서 "이전 Arc" → "이전 시기" 정상 치환 (4/5 Arc) |
| 무협 필드 제거 | internal_energy 필드 Arc 1,3에서 자동 제거 (Arc 4,5 잔존 — P2-3) |
| items_consumed 추상 제거 | Arc 1에서 추상 개념 2건 자동 제거 (양 시도 모두) |
| LLM 성공률 | 76/76 = 100%, 재시도 0회 |
| 비용 효율 | $1.38 / 40분 (5 Arc, 25 에피소드) |
| 서사 품질 | Arc 2 마진콜 위기, Arc 3 이세진 영입, Arc 4~5 투자+가족 갈등 묘사 우수 |
| Arc 내부 일관성 | auto_correct 이후 각 Arc 내부 위치/상태 정합 유지 |
| PASS_WITH_FIX 작동 | Arc 4에서 정상 InPlace 패치 + PASS 전환 확인 |
| auto_correct 위치 동기화 | Arc간 위치 불일치를 Arc 내부에서 자동 보정 |

---

## 5. 패치 우선순위 (TF 통합)

| ID | 심각도 | 제목 | 파일 | 난이도 |
|----|--------|------|------|--------|
| TF-A | **P0 CRITICAL** | Director PASS 시 NS-3-B bypass — Phase 2.6 직전으로 이동 | `four_phase_arc_generator.py` L650 | 중 |
| TF-B | **P0 CRITICAL** | Block 경계 제약 규칙 추가 — 이벤트 흡수/선취 방지 | `ensemble.yaml` L48 | 저 |
| TF-C | P1 MAJOR | genre_ext.capital_after 강제력 강화 + NS-3-B 키 순서 | `arc_ensemble.py` L503 + `four_phase_arc_generator.py` L132 | 저 |
| TF-D | P1 MAJOR | MAX_EPISODES_PER_ARC 7→6 (유저 의도 2-6 범위) | `constants.py` L330 | 즉시 |
| TF-E | P2 MINOR | items_acquired 빈 배열 방지 — 스키마 설명 강화 | `ensemble.yaml` 스키마 | 저 |
| TF-F | INFO | NPC 등장 시점 제약 — Treatment NPC 목록 프롬프트 주입 | `arc_ensemble.py` | 중 |
| P1-1 | P1 MAJOR | Treatment 거점 위치 Arc 프롬프트 주입 | `arc_ensemble.py` | 중 |
| P2-1 | P2 MINOR | V61 reject_reason 상세화 | 로깅 | 저 |
| P2-2 | P2 MINOR | 투자물 소지품 연속성 감도 조절 | auto_correct | 저 |
| P2-3 | P2 MINOR | TF-45 internal_energy 잔존 Arc 4,5 조사 | `stage2_optimizer.py` | 저 |

---

## 6. 재현 조건

```
프로젝트: 골든루트 (투자물)
블록: Block 1~5
Arc: 5개 (에피소드 1~25)
실행 시각: 2026-03-07 10:48
모델: gemini-2.5-pro + gemini-2.5-flash
```

---

## Appendix A: runtime_audit 이벤트 요약

| 이벤트 유형 | 횟수 | 비고 |
|------------|------|------|
| v60_25_auto_correct | 8 | 위치 동기화, 무협 필드 제거, 아이템 정리 |
| stage2_patch_mode | 1 | Arc 1, attempt 2 (prev_score 85) |
| db_commit | 5 | Arc별 1회 |
| v60_10_state_extracted | 5 | Arc별 1회, items_tracked 4→9 증가 |

## Appendix B: Agent 호출 분포

| Agent | 호출 | 평균 ms | 비고 |
|-------|------|---------|------|
| ArcEnsembleGenerator | 23 | 78,011 | 가장 느림 (max 94s) |
| Director | 23 | 36,309 | |
| PreflightChecker | 10 | 34,332 | |
| Analyst | 9 | 34,497 | |
| StateExtractor | 5 | 29,679 | |
| Weaver | 5 | 19,706 | |
| UnifiedArcValidator | 1 | 17,944 | |

## Appendix C: Treatment vs Arc 자본 궤적

```
Treatment:  20억 → 23억(미실현) → 30억 → 45억 → 50억
Arc(t.a.):  18.6억 → 32.3억(실현) → 131.3억 → 136.3억 → 141.3억
괴리:       -1.4   → +9.3          → +101.3   → +91.3    → +91.3
(t.a. = total_assets, NS-3-B 비교 대상)

근본 원인 체인 (§2.5 상세 참조):
 TF-D: Block 1 1,368자 → analyst 5화, 스키마 "3~7" → LLM 6화
 → TF-B: 경계 없음 → Ep 5-6 Block 2 흡수 (PB+WTI진입)
   → Arc 2: 잔여 소재 → WTI 전량 청산 32.3億 (+9.3億, 40%)
     → Arc 3: 콘텐츠 진공 → 100億 대여금 131.3億 (+101億, 337%)
       → TF-A: Director PASS → NS-3-B skip → 괴리 무감지
         → Arc 4-5: 괴리 궤도 유지 (+91億)
```

## Appendix D: Treatment vs Arc NPC 대응

| Treatment NPC | 등장 Block | Arc NPC | 모순 평가 |
|--------------|-----------|---------|----------|
| 한시우 (주인공) | 전체 | 한시우 | 정합 |
| 한정호 (아버지) | 1,5 | 한정호 | Arc 3에서 100억 대여 — Treatment에 없는 이벤트이나 NPC 자체는 정합 |
| 한태준 (큰형) | 1,5 | 한태준 | 정합 |
| 한태민 (둘째형) | 1,5 | 한태민 | 정합 |
| 박성호 (PB) | 2,3,4 | 박성호 | 정합 |
| 마이클 첸 (파트너) | **Block 7** (미도달) | **미등장** | — |
| — | — | **이세진** (Arc 3 창작) | **모순**: 마이클 첸 역할 선취 (파생상품 전문가, 핵심 파트너). Block 7 합류 시 역할 충돌 |

## Appendix E: TF-A 코드 경로 상세

```python
# four_phase_arc_generator.py L650-750 (현재 구조)

# Phase 2.6: Director 선택
if director and all_candidates:
    _dir_result = director.compare_and_select_arc(...)
    if _dir_decision == "PASS":
        return best_arc, pipeline_result      # ← L687: 즉시 반환
    elif _dir_decision == "PASS_WITH_FIX":
        return best_arc, pipeline_result      # ← L710: 즉시 반환
    else:
        continue                              # REJECT → retry

# Phase 2.55: NS-3-B + arc_end_state 점검  ← Director PASS 시 미도달
best_arc = self._check_arc_end_state(best_arc)
_ns3b_warning = _check_arc_vs_block_targets(best_arc, curr_block, arc_no)

# Phase 3: Validator                        ← Director PASS 시 미도달
verdict, validation_result = self.validator.validate(...)
```

**수정안 (권장 — TF-A 패치)**:
```python
# Director 선택 직전에 NS-3-B 실행
_ns3b_warning = _check_arc_vs_block_targets(best_arc_or_candidates[0], curr_block, arc_no)
if _ns3b_warning:
    # Director 컨텍스트에 주입
    _ns3b_context = f"[NS-3-B 수치 목표 괴리 경고]\n{_ns3b_warning}"
    # compare_and_select_arc에 advisory로 전달

if director and all_candidates:
    _dir_result = director.compare_and_select_arc(
        ..., advisory=_ns3b_context  # 추가
    )
```

## Appendix F: DB arc_end_state 키 구조 (실측)

| Arc | arc_end_state 키 목록 |
|-----|---------------------|
| 1 | location, equipment, injuries, **capital**, **total_assets**, portfolio_position |
| 2 | location, equipment, injuries, **capital**, **total_assets**, portfolio_position |
| 3 | location, equipment, injuries, **capital**, **total_assets**, portfolio_position |
| 4 | location, equipment, injuries, **internal_energy**(잔존), **capital**, **total_assets**, portfolio_position |
| 5 | location, equipment, injuries, **capital**, **total_assets**, portfolio_position |

- LLM이 스키마에 없는 `portfolio_position` 키를 자체 추가 (5개 Arc 전부)
- `capital`과 `total_assets` 양쪽 생성 (스키마는 `{state_constraints_genre_field}` = `"capital"` 하나만 지정)
- NS-3-B 키 검색 순서 `("total_assets", "assets", "capital", "total_capital")` → `total_assets` 우선 사용

## Appendix G: 에피소드별 이벤트 출처 대조 (인과 확정 근거)

> Arc 전술서(arc_NNN.txt) vs Treatment Block content 교차 대조.

### Arc 1 (Block 1) — 6화

| Ep | 이벤트 | 출처 Block | 정합 |
|----|--------|-----------|------|
| 1 | 2024년 죽음 → 2006년 회귀 | Block 1 context | O |
| 2 | 아버지 서재 — "투자사 차리겠다" | Block 1 event_villain | O |
| 3 | 자산 정리 20.3億, 법인 설립 의뢰 | Block 1 solution | O |
| 4 | 여의도 사무실, 블룸버그 터미널, 싱가포르 계좌 (비용 1.7億) | Block 1 reward 확장 | O |
| **5** | **PB 박성호 만남, WTI 3x 레버리지 계획** | **Block 2** event_villain | **X** |
| **6** | **이란 핵 뉴스, WTI 18.3億 3x 롱 진입** | **Block 2** solution+reward | **X** |

### Arc 2 (Block 2) — 4화

| Ep | 이벤트 | 출처 Block | 정합 |
|----|--------|-----------|------|
| 7 | WTI 횡보 + **OPEC 증산 루머 → 마진콜 위기** | **독자 창작** | **X** |
| 8 | 증거금 3천만 추가 투입 + V자 반등 | **독자 창작** | **X** |
| 9 | WTI 78달러 전량 청산 → 32.3億 | Block 4 context (78달러 전량 정리) | **선취** |
| 10 | 박성호 충성맹세 + 아버지 통화 + 서브프라임 힌트 | Block 3 reward (PB 태도) + Block 5 (연말) | **혼합** |

### Arc 3 (Block 3) — 5화

| Ep | 이벤트 | Block 3 이벤트 | 정합 |
|----|--------|---------------|------|
| 11 | 서브프라임 준비, 퀀트 물색 | Block 3: 유가 70달러 횡보, 에콰도르 | **X** (진공) |
| 12 | **이세진 영입** | Block 3: PB 익절 권유, 거절 | **X** (NPC 창작) |
| 13 | 이세진 시험 과제 통과 | Block 3: 에콰도르 사태 유가 상승 | **X** (전부 무시) |
| 14 | 아버지에게 **100億 대여금** 요청 | Block 3: 부분 익절 15→20億 | **X** (이벤트 대체) |
| 15 | 대여금 수령 → 131.3億, CDS 숏 구축 | Block 3: PB 태도 변화 | **X** (전부 무시) |

Block 3 이벤트 사용률: **0/4 (0%)**. WTI 포지션이 Arc 2에서 전량 청산되어 Block 3의 "부분 익절" 이벤트가 실행 불가능.

### Block content_len vs target_ep_count vs actual_ep_count

| Block | content_len | analyst target | LLM 실제 | 차이 | 비고 |
|-------|-------------|---------------|---------|------|------|
| 1 | 1,368 | **5** | **6** | **+1** | 스키마 "3~7" 허용 범위 |
| 2 | 783 | 4 | 4 | 0 | 일치 |
| 3 | 646 | 4 | 5 | +1 | |
| 4 | 478 | **3** | **5** | **+2** | 소재 대비 과다 |
| 5 | 744 | 4 | 5 | +1 | |
| **합계** | | **20** | **25** | **+5** | target 대비 25% 초과 |

---

**감리 결과**: TF 심층 2회 + 인과 확정 조사 1회 완료. P0 2건(TF-A, TF-B), P1 3건(TF-C, TF-D, P1-1), P2 4건, INFO 1건.

**인과 확정 (99%+ 확신)**: §2.5에서 에피소드별 이벤트 출처 대조로 확정. TF-D(6화)→TF-B(이벤트 흡수)→콘텐츠 진공→창작→TF-A(NS-3-B bypass) 순서 연쇄. **어느 1건만 패치해도 체인 차단 가능**. 최우선: TF-B(블록 경계) + TF-A(NS-3-B 위치 이동).
