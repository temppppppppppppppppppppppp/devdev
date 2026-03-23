# 콘솔 로그 최대 표시 정책 — 전역 전수조사 보고서

> **날짜**: 2026-03-23
> **감사 범위**: `modules/` 전체 프로덕션 코드
> **목적**: 주요 판단과 Director–LLM 의사소통이 콘솔(운영자 화면)에서 온전히 보이는지 전수 확인
> **정책 근거**: `AGENTS.md` 정책 결정 사항 제2항 — 콘솔 로그 최대 표시 정책

---

## 1Pass: 사실 수집

### A. Director Thinking 표시 경로 — 3개 Stage 전부 확인

| Stage | 파일 | 라인 | 표시 여부 | 절삭 | 비고 |
|-------|------|------|----------|------|------|
| Stage 4 | `director_ensemble.py` L1215-1217 | `💭 [Director Thinking]\n{thinking}` | **표시됨** | **없음** | `if thinking:` 조건부 |
| Stage 3 | `director_ensemble.py` L1614-1616 | 동일 패턴 | **표시됨** | **없음** | 동일 |
| Stage 2 | `director_ensemble.py` L1877-1879 | 동일 패턴 | **표시됨** | **없음** | 동일 |
| Stage 2 (auditor) | `stage2_finalizer.py` L1830-1833 | `ctx.ui.log(director_thinking)` | **표시됨** | **없음** | REJECT 경로 |

**판정**: Director thinking 전문은 콘솔에 **절삭 없이** 표시된다. 단, `_last_thinking`이 빈 문자열이면 조건부로 생략된다 — 이는 정상 동작(thinking이 없으면 표시할 것이 없음).

### B. Director 판정 요약 — 콘솔 표시 시 절삭 발생

#### Stage 4 (`director_ensemble.py` L1193-1222)

| 필드 | 라인 | 절삭 | 콘솔 표시 |
|------|------|------|----------|
| `selection_reason` | L1198 | **`[:200]`** | `선택 사유: {selection_reason[:200]}` |
| `verdict_reason` | L1200 | **`[:200]`** | `verdict_reason: {verdict_reason[:200]}` |
| `issue` (각각) | L1210 | **`[:150]`** | `이슈: {str(issue)[:150]}` (최대 5건) |
| `open_review` | L1212 | **`[:200]`** | `자유 리뷰: {open_review[:200]}` |
| `score_breakdown` | L1201-1207 | 없음 | 전체 표시 |
| `adaptive_result.reason` | L1213 | 없음 | 전체 표시 |
| `thinking` | L1215-1217 | **없음** | 전체 표시 |

#### Stage 3 (`director_ensemble.py` L1601-1622)

| 필드 | 라인 | 절삭 | 콘솔 표시 |
|------|------|------|----------|
| `reason` | L1607 | **`[:200]`** | `사유: {reason[:200]}` |
| `comparison_notes` | L1609 | **`[:200]`** | `비교: {comparison_notes[:200]}` |
| `contradictions` (각각) | L1611 | **`[:150]`** (최대 3건) | `모순: {str(item)[:150]}` |
| `blueprint_feedback` | L1614 | **`[:200]`** | REJECT/PASS_WITH_FIX만 표시 |
| `thinking` | L1614-1616 | **없음** | 전체 표시 |

#### Stage 2 (`director_ensemble.py` L1864-1885)

| 필드 | 라인 | 절삭 | 콘솔 표시 |
|------|------|------|----------|
| `reason` | L1871 | **`[:200]`** | `사유: {reason[:200]}` |
| `comparison_notes` | L1873 | **`[:200]`** | `비교: {comparison_notes[:200]}` |
| `contradictions` (각각) | L1875 | **`[:150]`** (최대 3건) | `모순: {str(item)[:150]}` |
| `feedback` | L1878 | **`[:200]`** | 비-PASS만 |
| `thinking` | L1877-1879 | **없음** | 전체 표시 |

#### Stage 2 REJECT (`stage2_finalizer.py`)

| 필드 | 라인 | 절삭 | 콘솔 표시 |
|------|------|------|----------|
| `reject_reason` | L1573 | **`[:100]`** | `🎬 [Director REJECT] {reject_reason[:100]}` |
| `base_feedback` | L1574 | **`[:100]`** | `📋 피드백: {base_feedback[:100]}` |
| `contradiction` (각각) | L1827 | **`[:120]`** (최대 5건) | `▸ {str(contradiction)[:120]}` |
| `re_slice_instruction` | L1829 | **`[:150]`** | `🔧 수정지시: {...[:150]}` |
| `fix_instr` | L1907, L2201 | **`[:80]`** | PASS_WITH_FIX 패치 지시 |
| `director_thinking` | L1830-1833 | **없음** | 전체 표시 |

### C. Advisory Chain — 콘솔 가시성 심각하게 부족

#### Stage 4 Advisory 9개 병렬 실행 (`stage4_interview_round.py`)

| Advisory | 생성 라인 | 콘솔 표시 | 문제 |
|----------|----------|----------|------|
| TruthGate | L4590-4612 | `logging.info` **만** (L4612) | `ctx.ui.log` **없음** — 운영자 불가시 |
| NpcDrift | L4630-4662 | `logging.info` **만** | 동일 |
| NumericDrift | L4670-4690 | `logging.info` **만** | 동일 |
| Flashback | L4700-4758 | `logging.info` **만** | 동일 |
| InfoParadox | L4780-4817 | `logging.info` **만** | 동일 |
| RelDrift | L4830-4865 | `logging.info` **만** | 동일 |
| LongTermRep | L4875-4908 | `logging.info` **만** | 동일 |
| NumericConsistency | L4920-4973 | `logging.info` **만** | 동일 |
| StyleSignal | L5020-5062 | `logging.info` **만** (L5061) | 동일 |

**결론**: 9개 Advisory 결과가 전부 `logging.info()`로만 출력된다. **`ctx.ui.log()`를 거치지 않으므로 Rich 콘솔 운영자 화면에 표시되지 않는다.** 유일하게 보이는 것은 `advisory {N}건 경고` 카운트 요약 1줄.

#### Python 검증 advisory — 카운트만 표시

| 항목 | 라인 | 콘솔 표시 |
|------|------|----------|
| BV advisory 카운트 | L3524-3525 | `⚠️ 후보{N} Python 검증 advisory {N}건 → Director에 전달` |
| 개별 BV 경고 내용 | — | **미표시** — 카운트만 |

### D. 점수 변동 — 콘솔 가시성 부분적

#### Firewall 점수 변조 (`director_ensemble.py`)

| 변동 | 라인 | 콘솔 표시 | 문제 |
|------|------|----------|------|
| V60.97 swap → score=50 | L914-916 | **없음** | 점수가 50으로 리셋되는데 콘솔에 안 나옴 |
| SCM 점수 캡 90 | L957-960 | `logging.info` **만** | 운영자 불가시 |
| Firewall fixable → score≤97 | L988-989 | `logging.warning` | WARNING이므로 보일 수 있으나 정확한 캡 값(97) 미표시 |
| Firewall triggered → score≤44 | L1000-1001 | `logging.warning` | 동일, 캡 값(44) 미표시 |
| NC-3B breakdown 불일치 조정 | L906-912 | `logging.warning` | 불일치 로그는 있으나 최종 점수 미표시 |
| NC-3 python_warnings 감점 | L1063-1070 | `logging.info` **만** | 운영자 불가시 |

#### Adaptive Verdict 변환 (`director_ensemble.py` L1075-1091)

| 변환 | 콘솔 표시 | 문제 |
|------|----------|------|
| CONDITIONAL_PASS → REJECT (original=REJECT) | **없음** | 분기 로직 자체가 콘솔에 안 나옴 |
| CONDITIONAL_PASS → REJECT (v60_97_swapped) | **없음** | 동일 |
| CONDITIONAL_PASS → original (adjusted) | **없음** | 동일 |
| CONDITIONAL_PASS → PASS (fallback) | **없음** | 동일 |

최종 verdict는 operator_lines의 첫 줄(L1194)에 표시되지만, **어떤 변환 경로를 거쳐** 그 verdict에 도달했는지는 보이지 않는다.

### E. Silent Decision Paths — `logging.debug()` 또는 `pass`

| 파일 | 라인 | Silent 결정 | 심각도 |
|------|------|------------|--------|
| `stage4_post_pass_runtime.py` L349 | StateTextVerifier flag 로드 실패 → `pass` | MEDIUM |
| `stage4_post_pass_runtime.py` L758 | causal_graph 쓰기 실패 → `logging.debug` | MEDIUM |
| `stage4_post_pass_runtime.py` L776 | causal_graph 읽기 실패 → `logging.debug` | MEDIUM |
| `stage4_post_pass_runtime.py` L808 | state_log 저장 여부 → 조건부 무시 | MEDIUM |
| `stage4_post_pass_runtime.py` L972 | SessionLogger 상태변화 기록 → `pass` | LOW |
| `stage4_interview_round.py` L1926 | ChiefWriter 공유상태 주입 실패 → `logging.debug` | MEDIUM |
| `stage4_director_runtime.py` 여러 곳 | 모듈 None 체크 → `logging.debug` | MEDIUM |
| `pass_rate_monitor.py` L164 | 기록 저장 실패 → `logging.warning` | LOW |

### F. 콘솔 절삭 전수 집계 — 운영자 영향 분류

| 절삭 한도 | 건수 | 대표 사용처 | 운영자 영향 |
|----------|------|-----------|------------|
| `[:80]` | 48+ | 에러 메시지, fix 지시, conflict 메시지 | **HIGH** — 에러/fix 맥락 소실 |
| `[:100]` | 74+ | reject_reason, 생성 실패, 위반 설명 | **HIGH** — 판정 근거 소실 |
| `[:120]` | 12+ | 선택 사유, 모순, verdict_reason | **HIGH** — 비교 분석 맥락 소실 |
| `[:150]` | 18+ | 이슈, 모순, 피드백 | **MEDIUM** — 부분 소실 |
| `[:160]` | 15+ | 이벤트, 설명, action_items | **MEDIUM** |
| `[:200]` | 56+ | 선택 사유, verdict_reason, 피드백, 에러 상세 | **MEDIUM** — 가장 많은 건수 |

---

## 2Pass: 적대적 분류

### CRITICAL 등급 — 판정에 영향을 주는 결정이 콘솔에서 보이지 않음

#### C-01. Advisory Chain 9개 결과 전량 콘솔 미표시

- **근거**: `stage4_interview_round.py` L4590-5062 — 9개 advisory 모두 `logging.info()`만 사용
- **영향**: TruthGate가 3건 경고를 발견하고, NpcDrift가 2건 감지해도, 운영자는 `advisory 5건` 한 줄만 본다. 어떤 유형이 몇 건인지, 무슨 내용인지 전혀 보이지 않는다.
- **위반**: 정책 제2항 — "운영자가 실행 중 판단 근거를 확인해야 하는 로그는 축약·생략하지 않고 최대한 표시"

#### C-02. Firewall 점수 변조 값이 콘솔에 미표시

- **근거**: `director_ensemble.py` L988 (`score≤97`), L1001 (`score≤44`) — `logging.warning`에 verdict 변경만 출력, 변조된 점수 값 자체는 없음
- **영향**: 운영자는 `[V75-C] ... → REJECT 강제`만 보고 점수가 100→44로 떨어진 건 모른다
- **추가**: L914-916의 V60.97 swap score=50 리셋은 아예 콘솔 출력이 없음

#### C-03. Adaptive Verdict 변환 분기가 콘솔에 미표시

- **근거**: `director_ensemble.py` L1075-1091 — `CONDITIONAL_PASS`가 4개 분기 중 하나로 변환되지만, 어느 분기를 탔는지 콘솔에 안 나옴
- **영향**: 최종 verdict만 보이고, adaptive logic이 개입했는지 여부를 운영자가 알 수 없음

### HIGH 등급 — 판정 근거 텍스트가 절삭됨

#### H-01. Stage 4 Director 요약의 `[:200]` 절삭 4건

- **근거**: `director_ensemble.py` L1198, L1200, L1212 — `selection_reason`, `verdict_reason`, `open_review` 각각 200자 절삭
- **실제 길이**: Director LLM 응답의 이 필드들은 통상 300~1000자. 200자면 20~60% 소실.

#### H-02. Stage 2 REJECT 경로의 `[:100]` 절삭 2건

- **근거**: `stage2_finalizer.py` L1573-1574 — `reject_reason[:100]`, `base_feedback[:100]`
- **영향**: REJECT 판정의 핵심 근거가 100자에서 잘림. 100자는 한국어 2~3문장에 불과.

#### H-03. Stage 2 fix 지시 `[:80]` 절삭 2건

- **근거**: `stage2_finalizer.py` L1907, L2201 — PASS_WITH_FIX 패치 지시가 80자
- **영향**: 패치 지시가 구체적이어야 하는데 80자에서 잘리면 "무엇을 수정하라는 건지" 불명확

#### H-04. 이슈/모순 개수 하드코딩 제한

- **근거**: Stage 4 `issues[:5]` (L1208), Stage 3 `contradictions[:3]` (L1611), Stage 2 `contradictions[:3]` (L1875)
- **영향**: 모순이 10건이어도 3건만 보임. 나머지 7건의 존재 자체를 운영자가 모름.

### MEDIUM 등급 — 운영 가시성 부족

#### M-01. 점수 변동의 `logging.info` 전용 출력

- **근거**: `director_ensemble.py` L960 (SCM 보정), L1066 (NC-3 감점) — `logging.info`만 사용
- **영향**: 기본 로그 레벨이 WARNING이면 운영자에게 보이지 않음

#### M-02. `stage4_post_pass_runtime.py`의 `logging.debug` + `pass` 패턴

- **근거**: L349, L758, L776, L972 — 실패를 삼키거나 debug로만 기록
- **영향**: 운영자가 후처리 실패를 모름

#### M-03. Stage 3/4 생성 실패 에러 `[:100]`

- **근거**: `stage3_orchestrator.py` L1614, `stage4_interview_round.py` L1917 등
- **영향**: 에러 메시지가 100자에서 잘려 디버깅 어려움

---

## 3Pass: 판정 및 근거 교차 검증

### 3Pass-1. Thinking 전문 표시 — 검증 통과

코드 근거 3곳(`director_ensemble.py` L1215, L1615, L1879) + 1곳(`stage2_finalizer.py` L1830) 모두:
```python
thinking = getattr(self._d, "_last_thinking", "")
if thinking:
    operator_lines.append(f"💭 [Director Thinking]\n{thinking}")
```
**절삭 없음 확인**. `[:N]` 패턴 부재 확인. **PASS**.

### 3Pass-2. Advisory Chain 콘솔 미표시 — C-01 재확인

`stage4_interview_round.py`에서 `ctx.ui.log`로 advisory 상세를 출력하는 코드 존재 여부를 `ctx.ui.log.*advisory|ctx.ui.log.*TruthGate|ctx.ui.log.*NpcDrift`로 grep:
- 결과: `ctx.ui.log`에 advisory 상세를 넣는 코드 **없음**
- Python 검증 advisory 카운트(L3524-3525)만 `ctx.ui.log` 사용
- 9개 LLM advisory는 `logging.info`만 사용하고 `ctx.ui.log`를 **전혀 거치지 않음**
- **C-01 확정**

### 3Pass-3. Firewall 점수 표시 — C-02 재확인

`director_ensemble.py` L988-989:
```python
state.score = min(state.score, 97)
logging.warning(" [V75-C] %s → PASS_WITH_FIX", state.firewall_reason)
```
`logging.warning` 메시지에 **점수 값이 포함되지 않음** 확인. L1001도 동일:
```python
state.score = min(state.score, 44)
logging.warning(f" [V75-C] {state.firewall_reason} → REJECT 강제")
```
점수 44가 메시지에 없음. **C-02 확정**.

다만 L1194의 최종 출력줄:
```python
f"[Stage4 Director] 원고 앙상블 판정: {final_verdict} (점수: {state.score})"
```
에서 **변조 후의 최종 점수**는 보인다. 그러나 **변조 전 원래 점수**(pre_firewall_score)와의 차이는 보이지 않는다.

### 3Pass-4. 절삭 한도 검증 — H-01~H-04 재확인

`director_ensemble.py`에서 `[:200]` grep 결과: L1198, L1200, L1212, L1607, L1609, L1614, L1871, L1873, L1878 — **9곳** 확인.
`stage2_finalizer.py`에서 `[:100]` grep 결과: L1573, L1574, L3006 — **3곳** 확인.
`[:80]` grep: L1907, L2201 — **2곳** 확인.
**H-01~H-04 전부 확정**.

### 3Pass-5. Silent Decision 재확인 — C-03

`director_ensemble.py` L1082-1091에서 `ctx.ui.log`나 `_operator_log` 호출 존재 여부:
- **없음** 확인. 4개 분기가 모두 silent.
- 유일한 가시적 출력은 L1194의 최종 verdict 줄과 L1213의 `adaptive_result.reason` (비어 있지 않을 때만).
- **C-03 확정**.

### 3Pass-6. 콘솔 vs DB 정합성 — 신규 발견

DB에는 `director_thinking` 전문이 저장되고(Tranche 4에서 구현), `selection_reason`/`verdict_reason`도 절삭 없이 저장된다(Tranche 1에서 구현).
그러나 **콘솔에서는 동일 필드가 `[:200]`으로 잘려서 표시**된다.
→ DB와 콘솔의 정보 레벨이 불일치. DB에는 전문이 있는데 운영자 화면에서는 잘린다.

---

## 종합 판정

### 정책 준수 여부

| 항목 | 정책 요구사항 | 현재 상태 | 판정 |
|------|-------------|----------|------|
| Director Thinking 전문 | 최대한 표시 | 절삭 없이 전체 표시 | **PASS** |
| Advisory 경고 내용 | 최대한 표시 | 카운트만 표시, 상세 미표시 | **FAIL** |
| 판정 사유 (selection/verdict_reason) | 최대한 표시 | `[:200]` 절삭 | **FAIL** |
| 점수 변동 근거 | 최대한 표시 | firewall/adaptive 변동 미표시 또는 값 미포함 | **FAIL** |
| 모순/이슈 상세 | 최대한 표시 | 3~5건 하드코딩 + `[:150]` 절삭 | **FAIL** |
| REJECT 근거 (Stage 2) | 최대한 표시 | `[:100]` 절삭 | **FAIL** |
| 에러/실패 메시지 | 최대한 표시 | `[:80]`~`[:100]` 절삭 | **FAIL** |

### 발견 사항 요약

| ID | 등급 | 요약 | 위치 |
|----|------|------|------|
| C-01 | CRITICAL | Advisory 9개 결과 콘솔 전량 미표시 | `stage4_interview_round.py` L4590-5062 |
| C-02 | CRITICAL | Firewall 점수 변조 값 콘솔 미표시 | `director_ensemble.py` L988, L1001, L914 |
| C-03 | CRITICAL | Adaptive verdict 변환 분기 콘솔 미표시 | `director_ensemble.py` L1075-1091 |
| H-01 | HIGH | Stage 4 판정 요약 `[:200]` 절삭 4곳 | `director_ensemble.py` L1198/1200/1212 |
| H-02 | HIGH | Stage 2 REJECT `[:100]` 절삭 2곳 | `stage2_finalizer.py` L1573-1574 |
| H-03 | HIGH | Stage 2 fix 지시 `[:80]` 절삭 2곳 | `stage2_finalizer.py` L1907/2201 |
| H-04 | HIGH | 이슈/모순 표시 건수 하드코딩 | `director_ensemble.py` `[:5]`/`[:3]` |
| M-01 | MEDIUM | 점수 보정이 `logging.info`만 사용 | `director_ensemble.py` L960/1066 |
| M-02 | MEDIUM | post-pass 실패가 debug/pass로 삼켜짐 | `stage4_post_pass_runtime.py` 4곳 |
| M-03 | MEDIUM | 에러 메시지 `[:100]` 절삭 | `stage3_orchestrator.py`/`stage4` 다수 |

### 콘솔 절삭 전수 집계

- `[:80]` 이하 절삭: **48건+** (에러, fix 지시, conflict)
- `[:100]` 절삭: **74건+** (reject_reason, 생성 실패, 위반)
- `[:120]`~`[:200]` 절삭: **86건+** (선택 사유, verdict_reason, 피드백)
- Advisory 상세 미표시: **9개 카테고리 전량**
- 점수 변조 미표시: **4개 경로**
- Verdict 변환 미표시: **4개 분기**

---

## 첨부: 콘솔 절삭 전수 위치 목록 (운영자 영향 분류)

### 직접 운영자 표시 (`ctx.ui.log` / `_operator_log`) 경유 절삭

```
director_ensemble.py:L1198  selection_reason[:200]     Stage4 선택 사유
director_ensemble.py:L1200  verdict_reason[:200]       Stage4 판정 사유
director_ensemble.py:L1210  str(issue)[:150]           Stage4 이슈 (×5)
director_ensemble.py:L1212  open_review[:200]          Stage4 자유 리뷰
director_ensemble.py:L1607  reason[:200]               Stage3 사유
director_ensemble.py:L1609  comparison_notes[:200]     Stage3 비교
director_ensemble.py:L1611  str(item)[:150]            Stage3 모순 (×3)
director_ensemble.py:L1614  str(feedback)[:200]        Stage3 피드백
director_ensemble.py:L1871  reason[:200]               Stage2 사유
director_ensemble.py:L1873  comparison_notes[:200]     Stage2 비교
director_ensemble.py:L1875  str(item)[:150]            Stage2 모순 (×3)
director_ensemble.py:L1878  str(feedback)[:200]        Stage2 피드백
stage2_finalizer.py:L1573   reject_reason[:100]        Stage2 REJECT 사유
stage2_finalizer.py:L1574   base_feedback[:100]        Stage2 피드백
stage2_finalizer.py:L1827   str(contradiction)[:120]   Stage2 모순 (×5)
stage2_finalizer.py:L1829   re_slice_instruction[:150] Stage2 수정지시
stage2_finalizer.py:L1907   str(fix_instr)[:80]        Stage2 fix 지시
stage2_finalizer.py:L2201   str(fix_instr)[:80]        Stage2 fix 지시
stage3_orchestrator.py:L1614 str(gen_err)[:100]        Stage3 생성 실패
stage4_interview_round.py:L683   fix[:120]             Stage4 fix 상세
stage4_interview_round.py:L3628  _conflict_msg[:80]    Stage4 연속성 충돌
stage4_interview_round.py:L3642  _conflict_msg[:80]    Stage4 역사 충돌
stage4_interview_round.py:L5154  fix_scope_reasoning[:120] Stage4 fix 사유
stage4_interview_round.py:L5157  open_review[:120]     Stage4 리뷰
```

### `logging.warning` 경유 절삭 (WARNING 이상에서 가시)

```
director_ensemble.py:L1578  str(contradiction)[:120]   Stage3 모순
director_ensemble.py:L1846  str(contradiction)[:120]   Stage2 모순
director_ensemble.py:L1814  str(exc)[:80]              Arc 비교 오류
stage4_interview_round.py:L4615  str(_tg_err)[:80]     TruthGate 실패
stage4_interview_round.py:L4665  str(_drift_err)[:80]  NpcDrift 실패
stage4_interview_round.py:L4693  str(_nd_err)[:80]     NumericDrift 실패
stage4_interview_round.py:L4760  str(_fb_err)[:80]     Flashback 실패
stage4_interview_round.py:L4819  str(_ip_err)[:80]     InfoParadox 실패
stage4_interview_round.py:L4867  str(_rd_err)[:80]     RelDrift 실패
stage4_interview_round.py:L4910  str(_ltr_err)[:80]    LongTermRep 실패
stage4_interview_round.py:L4975  str(_nc_err)[:80]     NumericConsistency 실패
stage4_interview_round.py:L5064  str(_sig_err)[:80]    StyleSignal 실패
```

### `logging.info` 전용 — 기본 설정에서 운영자 불가시 가능

```
director_ensemble.py:L960   SCM 점수 보정                INFO
director_ensemble.py:L1066  NC-3 python_warnings 감점    INFO
director_ensemble.py:L1073  consistency_checklist 생략    INFO
director_ensemble.py:L1582  Stage3 comparison_notes      INFO
director_ensemble.py:L1584  Stage3 이유                   INFO
director_ensemble.py:L1587  Stage3 요약줄                 INFO
director_ensemble.py:L1851  Stage2 요약줄                 INFO
stage4_interview_round.py:L4612  TruthGate 경고 건수     INFO
stage4_interview_round.py:L5061  StyleSignal 경고 건수   INFO
```

---

*Generated by Opus TF Audit — 3Pass 적대적 감리 완료, 코드 수정 없음*
