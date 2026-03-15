# TF-DE: Director Ensemble 판정 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | Director Ensemble: verdict logic, contradiction firewall, adaptive threshold, vote aggregation |
| Source files | director_ensemble.py:1,439줄 |
| TF Items | 12 (CRITICAL 2 / IMPORTANT 6 / INSIGHT 4) |

---

## 1. Executive Summary

`DirectorEnsembleSelector` (director_ensemble.py)는 3가지 주요 판정 경로를 포함한다:

1. **Blueprint 비교 선택** (`compare_and_select_blueprint`, L201-426): Stage 3 Blueprint 후보 비교
2. **Arc 비교 선택** (`compare_and_select_arc`, L500-800): Stage 2 Arc 후보 비교
3. **원고 앙상블 판정** (`select_and_judge_ensemble`, L802-1383): Stage 4 원고 3후보 최종 판정

핵심 발견:
- **"앙상블"이라는 이름과 달리, 실제로 독립적 ensemble member 투표가 아니라 단일 LLM 호출**이 후보 A/B/C를 모두 읽고 단일 판정을 내린다. 즉 multi-agent voting이 아닌 single-judge 패턴이다.
- Contradiction Firewall은 LLM 자체가 `contradiction_check` 필드에 보고한 모순에만 반응하므로, LLM이 모순을 감지하지 못하면 방화벽이 작동하지 않는다.
- 적응형 임계값은 retry_count 증가에 따라 최대 -10점까지 완화되지만, Director REJECT 주권이 Python 승격을 차단하므로 실질적 gaming 위험은 제한적이다.
- Dead code가 존재한다 (`_fallback_arc_selection` L789-800).

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                        Stage 4: select_and_judge_ensemble()
                        =====================================

  [3 Candidate Manuscripts]    [validation_results]    [mandatory_context]
         |                          |                        |
         v                          v                        v
  +-------------------+    +------------------+    +-------------------+
  | Length Gate        |    | Python warnings  |    | Advisory context  |
  | (MIN_LENGTH=4000) |    | per candidate    |    | (NumericConsist,  |
  +--------+----------+    +--------+---------+    | TruthGate, etc.)  |
           |                        |               +--------+----------+
           v                        v                        |
    qualified_indices          info_a/b/c                     |
           |                     |                           |
           +----------+----------+---------------------------+
                      |
                      v
            +---------+---------+
            | Single LLM Call   |  <-- NOT multi-agent voting!
            | (Director)        |  temperature=0.1, thinking=high
            | Reads all 3       |
            | candidates at once|
            +---------+---------+
                      |
                      v
            +---------+---------+
            | JSON Parse        |
            | _extract_json_    |
            |    robust()       |
            +----+----+---------+
                 |    |
        (parse OK)  (parse FAIL)
                 |    |
                 |    +---> REJECT, score=0
                 v
   +-------------+------------------+
   |  Post-Processing Pipeline      |
   |                                |
   |  1. V60.97 Swap Guard          |  L1076-1086
   |     (unqualified -> swap)      |
   |                                |
   |  2. NC-3B score_breakdown      |  L1098-1108
   |     reconciliation             |
   |                                |
   |  3. V60.97 swap penalty        |  L1110-1112
   |     (score=50, CONDITIONAL)    |
   |                                |
   |  4. SCM single-candidate cap   |  L1114-1118
   |     (score >= 95 -> cap 90)    |
   |                                |
   |  5. V75-C Contradiction        |  L1120-1150
   |     Firewall                   |
   |     CRITICAL>=1 -> REJECT      |
   |     MAJOR>=2    -> REJECT      |
   |     score cap: 44              |
   |                                |
   |  6. NC-1 numeric consistency   |  L1152-1191
   |     review (advisory only)     |
   |                                |
   |  7. NC-3 consistency checklist |  L1193-1242
   |     (ISSUE 3+ -> pw cap 3)    |
   |                                |
   |  8. Adaptive Decision          |  L1244-1250
   |     (threshold from grading)   |
   |                                |
   |  9. Director Sovereignty       |  L1252-1262
   |     (REJECT cannot be flipped  |
   |      by Python)                |
   |                                |
   +---------+---------------------+
             |
             v
      Final verdict + metadata
      (PASS / PASS_WITH_FIX / REJECT)


        Stage 2: compare_and_select_arc()
        ===================================

  [N Arc Candidates]   [quality_flags]
         |                    |
         v                    |
  Single LLM Call             |
  (temperature=0.3)           |
         |                    |
         v                    v
  JSON Parse --> _apply_candidate_quality_gate()
         |
         v
  Final: PASS / REJECT / PASS_WITH_FIX


        Stage 3: compare_and_select_blueprint()
        ==========================================

  [N Blueprint Candidates]
         |
    len==0 -> REJECT
    len==1 -> _evaluate_single_blueprint() -> always REJECT (TF-36)
    len>=2 -> Single LLM Call (temperature=0.3)
         |
         v
  JSON Parse -> result dict
  (fallback on exception: _fallback_first_candidate -> also REJECT)
```

---

## 3. TF Items

### TF-DE-01: Dead Code in `_fallback_arc_selection` — IMPORTANT

- **Location**: `director_ensemble.py:L789-L800`
- **Description**: `_fallback_arc_selection()` 메서드에서 L788의 `return _arc_compare_fallback_result(candidates)` 이후에 도달 불가능한(unreachable) 코드가 11줄 존재한다. 이 dead code는 `decision: "PASS"`, `score: 75`를 반환하는 오래된 "auto-PASS 폴백" 로직이다. 현재는 `_arc_compare_fallback_result()`가 `decision: "REJECT"`, `score: 0`을 반환하므로 실제 동작에는 영향이 없지만, dead code의 내용이 현재 정책(폴백=REJECT)과 정반대(폴백=PASS)인 점은 유지보수 혼란의 원인이다.
- **Evidence**:
  ```python
  # L784-800
  @staticmethod
  def _fallback_arc_selection(candidates: list[dict]) -> dict:
      """[TF-47] LLM 실패 시 Python 폴백 — 첫 번째 후보 PASS 반환."""  # <-- docstring도 틀림
      logging.warning(" [TF-47] 폴백 — 첫 번째 후보 선택 (Python)")
      return _arc_compare_fallback_result(candidates)   # <-- 여기서 반환
      best = candidates[0] if candidates else None       # <-- DEAD CODE
      return {
          "decision": "PASS",       # <-- 현재 정책과 반대!
          "selected_index": 0,
          "selected_arc": best,
          "score": 75,              # <-- 현재는 0
          ...
      }
  ```
- **Impact**: 유지보수 혼란. docstring이 "PASS 반환"이라고 명시하지만 실제는 REJECT를 반환. 향후 리팩터링 시 docstring만 보고 잘못된 가정을 할 수 있음.
- **Suggested fix direction**: L789-800 dead code 삭제, docstring을 "REJECT 반환"으로 수정.

---

### TF-DE-02: Contradiction Firewall Depends Entirely on LLM Self-Report — CRITICAL

- **Location**: `director_ensemble.py:L1120-1150`
- **Description**: Contradiction Firewall(V75-C)은 LLM 응답의 `contradiction_check.found_contradictions` 필드에서 severity를 읽어 CRITICAL >= 1 또는 MAJOR >= 2이면 강제 REJECT한다. 그러나 이 데이터의 유일한 출처는 **동일한 LLM 호출**이다. LLM이 모순을 감지하지 못하면(hallucination, 주의 분산, 컨텍스트 초과 등) `found_contradictions`가 빈 배열로 반환되고 방화벽은 작동하지 않는다.

  즉, **방화벽의 센서와 판정자가 동일 주체**이므로, 센서가 실패하면 방화벽도 무력화된다.
- **Evidence**:
  ```python
  # L1122-1123: LLM 자체 보고에만 의존
  _contradiction_check = result.get("contradiction_check", {})
  if isinstance(_contradiction_check, dict):
      _found = _contradiction_check.get("found_contradictions", [])
  ```
  `result`는 L1055의 `self._d._extract_json_robust(response)` — 즉 동일 LLM 호출 결과이다.
- **Impact**: 높음. LLM이 모순을 놓치면(특히 긴 컨텍스트에서 주의 분산이 심한 경우), Python mandatory_context에 포함된 advisory 경고가 있어도 방화벽이 작동하지 않음. Python 측 advisory(TruthGate, NumericConsistency 등)는 L1152-1191에서 로깅만 하고 방화벽을 트리거하지 않음.
- **Suggested fix direction**: Python advisory(TruthGate CRITICAL 등)가 CRITICAL을 보고한 경우, LLM 응답과 무관하게 방화벽을 트리거하는 "이중 잠금(dual-lock)" 패턴 도입. 예: mandatory_context 파싱으로 Python CRITICAL 카운트를 별도 추출하여 firewall에 합산.

---

### TF-DE-03: Adaptive Threshold Gaming — Retry-Based Decay — IMPORTANT

- **Location**: `director_grading.py:L529-535`, `director_ensemble.py:L1244-1262`
- **Description**: 적응형 임계값은 retry_count에 따라 완화된다:
  - retry >= 2: base - 5
  - retry >= 3: base - 10

  base_pass_threshold 기본값은 60이고, 범위 제한은 [45, 85]. 즉 최악의 경우 threshold가 45까지 내려갈 수 있다. 그러나 **L1254-1256의 Director 주권 규칙**이 방어 역할을 한다: `original_verdict == "REJECT"`이면 Python이 CONDITIONAL_PASS로 승격해도 다시 REJECT로 되돌린다.

  그러나 gaming 시나리오가 완전히 차단되지는 않는다:
  1. LLM이 borderline 점수(예: 62)를 지속적으로 반환하면서 verdict를 "PASS"로 설정하는 경우
  2. retry가 누적되면서 threshold가 55 -> 50으로 하락
  3. 62점 + PASS verdict이면 adaptive_decision은 PASS를 유지 (score >= threshold이므로)
  4. L1259의 경로: `adjusted=True`이고 `original_verdict=="PASS"`이면 `final_verdict = original_verdict = "PASS"`

  **그러나** 프롬프트가 "90점 미만이면 반드시 REJECT" (director.yaml L244)을 명시하므로, 정상적인 LLM 동작에서는 62점+PASS가 동시에 반환될 가능성이 낮다.
- **Evidence**:
  ```python
  # director_grading.py L529-535
  if retry_count >= 3:
      base -= 10
      reason_parts.append("3+회재시도(-10점)")
  elif retry_count >= 2:
      base -= 5
      reason_parts.append("2회재시도(-5점)")
  ```
- **Impact**: 중간. retry가 실질적으로 threshold를 낮추지만, Director 주권 규칙 + 프롬프트 90점 기준이 이중 방어. 만약 LLM이 프롬프트를 무시하고 낮은 점수에 PASS를 주면 통과될 수 있음.
- **Suggested fix direction**: `apply_adaptive_decision`에서 score < 90이고 `original_decision == "PASS"`인 경우 경고 로깅 + 선택적 downgrade를 고려. 현재는 LLM 판정을 100% 신뢰.

---

### TF-DE-04: Single Candidate Mode (SCM) — Insufficient Bias Correction — IMPORTANT

- **Location**: `director_ensemble.py:L882-883, L950-957, L1114-1118`
- **Description**: 분량 기준 통과 후보가 1개뿐일 때(SCM):
  1. L950-957: 프롬프트에 경고 문구 주입 ("경쟁 부재로 인한 과대 평가를 경계하세요")
  2. L1114-1118: score >= 95이면 90으로 캡

  문제점:
  - **캡이 95부터만 적용**: 94점은 그대로 통과. 단일 후보에 대한 과대 평가 경향을 고려하면 캡이 너무 관대.
  - **비교 부재에 대한 구조적 보정 없음**: 3후보 비교 시에는 "상대적으로 나은 후보"를 골라야 하므로 자연스럽게 엄격해지지만, 단일 후보는 비교 없이 독립 평가를 받으므로 LLM이 "이 정도면 괜찮다"고 판정할 확률이 높다.
  - 프롬프트 경고 문구는 소프트 시그널이므로 LLM이 무시할 수 있다.
- **Evidence**:
  ```python
  # L1114-1118
  if _scm_single_candidate and score >= 95:
      _scm_old = score
      score = min(score, 90)
      logging.info(f"[SCM] 단일 후보 점수 보정: {_scm_old} → {score}")
  ```
- **Impact**: 중간. 단일 후보 시 PASS 편향이 존재할 수 있으며, 95점 캡만으로는 91-94 구간의 과대 평가를 잡지 못함.
- **Suggested fix direction**: SCM 시 일률적으로 score에 -5 penalty를 적용하거나, 캡을 85로 낮추는 것을 고려. 또는 SCM 시 별도의 "확증 편향 방지" 질문을 추가 LLM 호출로 수행.

---

### TF-DE-05: PASS/REJECT/PASS_WITH_FIX Branch Completeness — Verdict Undefined Edge Case — IMPORTANT

- **Location**: `director_ensemble.py:L1252-1262`
- **Description**: `apply_adaptive_decision`이 반환하는 `final_verdict`는 다음 값을 가질 수 있다: `"PASS"`, `"REJECT"`, `"PASS_WITH_FIX"`, `"CONDITIONAL_PASS"`. L1252-1262의 분기 로직을 분석하면:

  ```
  adaptive_result["decision"] 가능 값:
    - "PASS" (원래 PASS, score >= threshold)
    - "REJECT" (원래 REJECT, score < threshold)
    - "CONDITIONAL_PASS" (score >= threshold인데 원래 REJECT, 또는 그 반대)
    - "PASS_WITH_FIX" (원래 PASS_WITH_FIX, score >= threshold)

  final_verdict 결정 (L1252-1262):
    if final_verdict == "CONDITIONAL_PASS":
        if original_verdict == "REJECT":     -> REJECT  (Director 주권)
        elif v60_97_swapped:                 -> REJECT  (swap 패널티)
        elif adjusted and original in (PASS, PASS_WITH_FIX):
                                             -> original_verdict (PASS or PASS_WITH_FIX)
        else:                                -> "PASS"  (L1262)
  ```

  **Edge case**: `adaptive_result["decision"] == "CONDITIONAL_PASS"`이면서 `adjusted == False`인 상황. `apply_adaptive_decision` (director_grading.py L562-580)를 보면, `adjusted=True`가 설정되는 경우는 반드시 `new_decision == "CONDITIONAL_PASS"`일 때뿐. 따라서 `CONDITIONAL_PASS + adjusted=False`는 불가능... **단, v60_97_swapped 경우 L1110-1112에서 original_verdict을 직접 "CONDITIONAL_PASS"로 덮어쓰고**, adaptive_decision의 입력으로 들어간다. 이 때 adaptive가 CONDITIONAL_PASS를 그대로 반환하면 L1253이 True가 되지만, `adjusted`는 adaptive 내부의 조정 여부를 나타내므로 False일 수 있다.

  `v60_97_swapped=True` + `adaptive adjusted=False`이면:
  - L1253: True (CONDITIONAL_PASS)
  - L1254: `original_verdict == "CONDITIONAL_PASS"` (아닌 "REJECT") -> 아래로
  - L1257: `v60_97_swapped=True` -> **REJECT** (정상)

  따라서 이 경로는 방어됨. 하지만 **모든 CONDITIONAL_PASS 분기가 명시적으로 문서화되어 있지 않으며**, `else: final_verdict = "PASS"` (L1262)는 catch-all로서 의도치 않은 PASS를 생산할 수 있는 위험 경로이다.
- **Evidence**:
  ```python
  # L1259-1262: else 분기가 catch-all PASS
  elif adaptive_result.get("adjusted") and original_verdict in ("PASS", "PASS_WITH_FIX"):
      final_verdict = original_verdict
  else:
      final_verdict = "PASS"   # <-- catch-all: 이 경로가 언제 도달하는지 명확하지 않음
  ```
- **Impact**: 중간. 현재 코드 흐름에서는 이 else 분기에 도달하는 정상적 경로가 존재하지만, 향후 변경 시 의도치 않은 PASS가 발생할 수 있음. 방어적 프로그래밍 부재.
- **Suggested fix direction**: L1262의 else를 `logging.warning`과 함께 명시적으로 어떤 조건에서 도달하는지 주석 추가. 또는 모든 조합을 명시적 if/elif로 분기.

---

### TF-DE-06: NC-3B Score Reconciliation Can Inflate Score — IMPORTANT

- **Location**: `director_ensemble.py:L1098-1108`
- **Description**: `score_breakdown` 합산이 LLM이 직접 반환한 `score`와 다를 때, breakdown 합산을 우선한다. 이는 LLM이 "합산을 실수했을 때" breakdown을 진실로 간주하는 정책이다. 그러나:

  1. LLM이 의도적으로 보수적인 total score를 줬는데 breakdown이 낙관적인 경우, breakdown이 우선되어 **점수가 상승**할 수 있다.
  2. `_sb_sum > 0` 조건만 있고, `_sb_sum > 100`인 경우도 `max(0, min(100, _sb_sum))`으로 100까지 허용된다.
  3. LLM이 breakdown에 불필요한 추가 키를 넣으면 합산에 포함된다: `sum(v for v in _sb_raw.values() if isinstance(v, int | float))` — `_CANONICAL_SCORE_KEYS` 외의 키도 합산됨.
- **Evidence**:
  ```python
  # L1099-1108
  _sb_raw = result.get("score_breakdown", {})
  if isinstance(_sb_raw, dict) and _sb_raw:
      _sb_sum = sum(v for v in _sb_raw.values() if isinstance(v, int | float))
      # ^^ _CANONICAL_SCORE_KEYS 필터 없이 모든 numeric value 합산
      if _sb_sum != score and _sb_sum > 0:
          score = max(0, min(100, _sb_sum))
  ```
- **Impact**: 중간. LLM이 예상 외 키를 포함하면 합산이 팽창. 예: `{"continuity_contradiction": 35, "blueprint_coverage": 20, "quality_engagement": 20, "length": 10, "python_warnings": 10, "bonus_creativity": 15}` -> 합산 110 -> cap 100.
- **Suggested fix direction**: `_sb_raw.values()` 대신 `_CANONICAL_SCORE_KEYS`에 해당하는 값만 합산. 또는 알 수 없는 키가 있으면 경고 로깅.

---

### TF-DE-07: Blueprint Single Candidate Always REJECT (TF-36) — INSIGHT

- **Location**: `director_ensemble.py:L474-481`
- **Description**: `_evaluate_single_blueprint()`는 모든 Python 사전검증(dead NPC, scene count, length)을 통과해도 L476에서 **무조건 REJECT (score=55)**를 반환한다. 이는 [TF-36] 대원칙("LLM 미호출 상태의 단일 후보 자동 PASS 금지")에 의한 것이다.

  이 설계는 fail-closed 원칙을 따르며 안전하지만, **실질적으로 Blueprint 단일 후보는 절대 통과할 수 없다**는 의미이다. 단일 후보가 compare_and_select_blueprint에 진입하면(L222-229), `_evaluate_single_blueprint`이 호출되어 항상 REJECT된다. LLM 비교 호출은 후보가 2개 이상일 때만 이루어진다.
- **Evidence**:
  ```python
  # L474-481
  logging.warning(" [대원칙3] _evaluate_single_blueprint: Director LLM 미호출 — fail closed")
  return {
      "decision": "REJECT",
      "score": 55,
      "reason": "Director LLM 미호출 상태의 단일 후보 자동 PASS 금지",
      ...
  }
  ```
- **Impact**: 낮음 (의도된 설계). 단일 Blueprint 후보는 Stage 3에서 항상 거부되어 재생성을 요구함.
- **Suggested fix direction**: 현재 설계가 안전하므로 유지. 단, 단일 후보에 대해서도 LLM 호출로 평가하는 옵션을 향후 도입 가능.

---

### TF-DE-08: Error Handling — Exception Swallows Differ Across Methods — IMPORTANT

- **Location**: `director_ensemble.py:L422-426, L780-782, L1004-1008, L1052-1054, L1416-1427`
- **Description**: 각 판정 경로의 예외 처리가 일관되지 않다:

  | 메서드 | 예외 시 동작 | score | decision |
  |--------|-------------|-------|----------|
  | `compare_and_select_blueprint` L422 | `_fallback_first_candidate` -> `_evaluate_single_blueprint` -> **항상 REJECT** | 55 | REJECT |
  | `compare_and_select_arc` L780 | `_arc_compare_fallback_result` | 0 | REJECT |
  | `select_and_judge_ensemble` (legacy) L1006 | `response = ""` -> 파싱 실패 -> REJECT | 0 | REJECT |
  | `select_and_judge_ensemble` (cache) L1052 | `response = ""` -> 파싱 실패 -> REJECT | 0 | REJECT |
  | `quick_judge_single` L1416 | **예외 미포착** | N/A | 예외 전파 |

  **`quick_judge_single`** (L1385-1439)은 `self._d.ask()` 호출(L1416)에 try/except가 없다. LLM 호출이 네트워크 오류 등으로 실패하면 예외가 호출자까지 전파된다.
- **Evidence**:
  ```python
  # L1416: try/except 없음
  response = self._d.ask(prompt, temperature=0.1, thinking_level="low")
  result = self._d._extract_json_robust(response)
  ```
- **Impact**: 중간. `quick_judge_single`은 "냉동인간 Writer용 간소 검토"이므로 사용 빈도가 낮지만, 호출 시 예외가 전파되면 상위 루프가 중단될 수 있음.
- **Suggested fix direction**: `quick_judge_single`에도 try/except 추가, 실패 시 `{"verdict": "REJECT", "score": 30, "reason": "LLM 호출 실패"}` 반환.

---

### TF-DE-09: No True Multi-Agent Voting — Single LLM Judge Architecture — CRITICAL

- **Location**: `director_ensemble.py:L802-1055` (전체 `select_and_judge_ensemble`)
- **Description**: 클래스 이름 `DirectorEnsembleSelector`와 메서드 이름 `select_and_judge_ensemble`은 여러 ensemble member가 독립적으로 투표하고 결과를 집계하는 구조를 암시한다. 그러나 실제 구현은:

  1. **단일 LLM 호출** (L1005 또는 L1042-1051)이 3개 원고를 모두 읽고 단일 JSON 응답을 반환
  2. 해당 JSON에서 `selected`, `verdict`, `score`를 추출
  3. Python 후처리(방화벽, 적응형 임계값 등)를 적용

  **투표 메커니즘이 존재하지 않는다.** 다수결, 가중 투표, 다양한 관점의 독립 평가 등이 없다. "앙상블"이라는 이름은 **후보 원고가 앙상블로 생성된 것**을 의미하지, 판정 프로세스가 앙상블인 것은 아니다.

  이것이 문제인 이유:
  - 단일 LLM 판정은 특정 편향(첫 번째 후보 선호, 길이 편향, recency bias 등)에 취약
  - 한 번의 hallucination이 최종 결과를 결정
  - 독립적 평가자 간 교차 검증이 없으므로 모순 감지 성능이 단일 판정에 의존
- **Evidence**: L1005의 `response = self._d.ask(prompt, ...)` — 단일 호출. `for member in ensemble_members:` 같은 반복 호출이나 투표 집계 로직이 전혀 없음.
- **Impact**: 높음. 구조적 한계. 단일 판정자의 실패가 최종 판정에 직결됨. 교차 검증이 없어 모순 감지 신뢰도가 낮음.
- **Suggested fix direction**: 장기적으로 3-5개 독립 LLM 호출(다른 temperature, 다른 프롬프트 관점)의 투표 집계 도입을 고려. 단기적으로는 현재 Python advisory가 부분적 교차 검증 역할을 하므로, advisory CRITICAL 결과를 방화벽에 직접 연결(TF-DE-02 수정)하여 보완.

---

### TF-DE-10: Feedback Propagation — Verdict Result is Fire-and-Forget — INSIGHT

- **Location**: `director_ensemble.py:L1347-1383`, `stage4_interview_round.py:L1911-1924`
- **Description**: `select_and_judge_ensemble`의 반환값은 풍부한 메타데이터를 포함한다 (score_breakdown, contradiction_types, consistency_checklist, numeric_consistency_review 등). 호출자(stage4_interview_round.py L1930-1948)는 이 결과를 사용하지만, **다음 라운드의 판정에 직접 피드백하지 않는다**. 즉:

  - Round N의 Director 판정 결과가 Round N+1의 Director 프롬프트에 포함되지 않음
  - Writer가 "이전 판정에서 지적된 모순을 수정했는지" 검증하는 메커니즘이 Director 측에 없음
  - 적응형 임계값은 retry_count만 보고, 이전 판정의 구체적 피드백은 고려하지 않음

  다만, `fix_scope`와 `feedback`은 Stage 4 재시도 루프에서 Writer에게 전달되어 수정의 방향성을 제공한다. 이것은 간접 피드백이다.
- **Evidence**: `stage4_interview_round.py:L1911-1924` — 호출 시 이전 판정 결과를 파라미터로 전달하지 않음.
- **Impact**: 낮음. 현재 설계에서는 Writer가 피드백을 받아 수정하고, Director는 새로운 원고를 독립적으로 평가하는 방식. 이전 판정과의 비교는 수행하지 않음.
- **Suggested fix direction**: 향후 개선으로, 이전 라운드의 `contradiction_types`와 `action_items`를 다음 Director 호출의 mandatory_context에 주입하여 "이전 지적사항이 해결되었는지" 확인하는 체크리스트를 추가.

---

### TF-DE-11: V60.97 Swap Can Bypass LLM Selection — INSIGHT

- **Location**: `director_ensemble.py:L1076-1086`
- **Description**: LLM이 선택한 후보(예: B)가 분량 기준 미달(`qualified_indices`에 없음)인 경우, Python이 자동으로 가장 긴 qualified 후보로 교체한다. 이는 합리적인 방어이지만:

  1. 교체 후 score가 50으로 강제 설정 (L1111)
  2. original_verdict이 "CONDITIONAL_PASS"로 변경 (L1112)
  3. 최종적으로 REJECT로 확정 (L1257-1258)

  따라서 swap이 발생하면 **무조건 REJECT**이 된다. LLM의 판정을 완전히 무시하는 것이다. 이는 안전 측면에서 합리적이지만, LLM이 의도적으로 분량이 짧지만 품질이 높은 후보를 선택한 경우에도 거부된다.
- **Evidence**:
  ```python
  # L1110-1112
  if v60_97_swapped:
      score = 50
      original_verdict = "CONDITIONAL_PASS"
  ```
- **Impact**: 낮음 (의도된 안전 설계). qualified_indices 필터가 MIN_LENGTH 기준이므로 4000자 미만 후보에만 적용.
- **Suggested fix direction**: 현재 설계 유지. 4000자 이하 원고는 서사 밀도가 부족하므로 REJECT이 합리적.

---

### TF-DE-12: Quality Gate on Arc Decision — Asymmetric force_pass_with_fix Logic — INSIGHT

- **Location**: `director_ensemble.py:L128-162, L778`
- **Description**: `_apply_candidate_quality_gate()`는 Arc 판정 후 적용된다(L778). 이 게이트의 로직:
  - `force_reject` -> 무조건 REJECT
  - `force_pass_with_fix` -> **오직 decision이 "PASS"일 때만** PASS_WITH_FIX로 전환

  `force_pass_with_fix`가 `decision == "REJECT"`인 경우에는 동작하지 않는다 (L148 조건). 이는 의도적인 설계로 보이지만(REJECT는 유지), `decision == "PASS_WITH_FIX"`인 경우에도 동작하지 않는다. 즉 이미 PASS_WITH_FIX인 판정에는 quality_flag의 추가 피드백이 병합되지 않는다.
- **Evidence**:
  ```python
  # L148: PASS인 경우에만 적용
  elif quality_flag.get("force_pass_with_fix") and decision == "PASS":
      decision = "PASS_WITH_FIX"
  ```
- **Impact**: 낮음. 이미 PASS_WITH_FIX인 판정에 추가 게이트 피드백을 병합하지 않지만, 판정 자체는 변경되지 않으므로 안전 측면에서 문제없음.
- **Suggested fix direction**: `decision == "PASS"` -> `decision in ("PASS", "PASS_WITH_FIX")`로 확장하면 이미 PASS_WITH_FIX인 경우에도 게이트 피드백이 병합됨. 선택적 개선.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | Category |
|----|-------|----------|----------|----------|
| TF-DE-01 | Dead code in `_fallback_arc_selection` | IMPORTANT | L784-800 | Code Hygiene |
| TF-DE-02 | Contradiction Firewall depends on LLM self-report | CRITICAL | L1120-1150 | Safety / Reliability |
| TF-DE-03 | Adaptive threshold gaming via retry decay | IMPORTANT | L1244-1262 + grading L529 | Security |
| TF-DE-04 | SCM insufficient bias correction | IMPORTANT | L882, L1114-1118 | Fairness / Bias |
| TF-DE-05 | Verdict catch-all PASS in else branch | IMPORTANT | L1252-1262 | Correctness |
| TF-DE-06 | NC-3B score reconciliation can inflate score | IMPORTANT | L1098-1108 | Scoring Integrity |
| TF-DE-07 | Blueprint single candidate always REJECT | INSIGHT | L474-481 | Design Intent |
| TF-DE-08 | Exception handling inconsistency across methods | IMPORTANT | L422,780,1006,1052,1416 | Error Handling |
| TF-DE-09 | No true multi-agent voting | CRITICAL | L802-1055 (entire method) | Architecture |
| TF-DE-10 | Feedback is fire-and-forget | INSIGHT | L1347-1383 | Feedback Loop |
| TF-DE-11 | V60.97 swap unconditionally REJECT | INSIGHT | L1076-1112 | Design Intent |
| TF-DE-12 | Quality gate asymmetric force_pass_with_fix | INSIGHT | L128-162 | Edge Case |

---

## 5. 핵심 코드 참조 (Appendix)

### A. Contradiction Firewall (V75-C) — L1120-1150

```python
_contradiction_check = result.get("contradiction_check", {})
if isinstance(_contradiction_check, dict):
    _found = _contradiction_check.get("found_contradictions", [])
    if isinstance(_found, list) and _found:
        _critical_count = sum(
            1 for c in _found if isinstance(c, dict) and str(c.get("severity", "")).upper() == "CRITICAL"
        )
        _major_count = sum(
            1 for c in _found if isinstance(c, dict) and str(c.get("severity", "")).upper() == "MAJOR"
        )
        firewall_triggered = False
        if _critical_count >= 1:
            firewall_triggered = True
        elif _major_count >= 2:
            firewall_triggered = True
        if firewall_triggered:
            original_verdict = "REJECT"
            score = min(score, 44)  # adaptive floor=45 미만
```

**방화벽 트리거 조건**:
- CRITICAL >= 1: 즉시 REJECT
- MAJOR >= 2: 즉시 REJECT
- MAJOR 1건: 방화벽 미발동 (LLM 자율 판단)
- MINOR: 방화벽 무관 (감점만)

**score cap 44의 의미**: adaptive threshold 최저값이 45 (`_ADAPTIVE_BASE_MIN`)이므로, 44점은 어떤 적응형 완화로도 PASS될 수 없다.

### B. Adaptive Decision Pipeline — L1244-1262

```python
adaptive_result = self._d.apply_adaptive_decision(
    score=score, original_decision=original_verdict,
    arc_pos=arc_pos, total_eps=total_eps, retry_count=retry_count,
)
final_verdict = adaptive_result["decision"]
if final_verdict == "CONDITIONAL_PASS":
    if original_verdict == "REJECT":
        final_verdict = "REJECT"            # Director 주권
    elif v60_97_swapped:
        final_verdict = "REJECT"            # Swap 패널티
    elif adaptive_result.get("adjusted") and original_verdict in ("PASS", "PASS_WITH_FIX"):
        final_verdict = original_verdict    # 원래 판정 복원
    else:
        final_verdict = "PASS"              # Catch-all
```

**적응형 임계값 범위**: [45, 85] (director_grading.py L14-15)
**base_pass_threshold**: 60 (director.py L50)
**최대 완화**: -10 (retry >= 3) + -5 (도입부) = 45

### C. NC-3B Score Reconciliation — L1098-1108

```python
_sb_raw = result.get("score_breakdown", {})
if isinstance(_sb_raw, dict) and _sb_raw:
    _sb_sum = sum(v for v in _sb_raw.values() if isinstance(v, int | float))
    if _sb_sum != score and _sb_sum > 0:
        score = max(0, min(100, _sb_sum))
```

**문제**: `_sb_raw.values()` 전체를 합산하므로 canonical 5개 키 외의 추가 키도 합산됨.

### D. SCM (Single Candidate Mode) — L882, L950-957, L1114-1118

```python
# 감지
_scm_single_candidate = len(qualified_indices) == 1

# 프롬프트 주입
if _scm_single_candidate:
    _scm_prefix = (
        "\n\n⚠️ [단일 후보 경고] 분량 기준 통과 후보가 1개뿐입니다. "
        "절대 기준으로 독립 평가하세요. 경쟁 부재로 인한 과대 평가를 경계하세요.\n"
    )

# 점수 캡
if _scm_single_candidate and score >= 95:
    score = min(score, 90)
```

### E. Verdict 결정 전체 흐름 (Stage 4)

```
LLM score (0-100)
    |
    v
NC-3B reconciliation (breakdown 합산 우선)
    |
    v
V60.97 swap? -> score=50, verdict=CONDITIONAL_PASS
    |
    v
SCM cap (>=95 -> 90)
    |
    v
Contradiction Firewall (CRITICAL/MAJOR -> score<=44, REJECT)
    |
    v
NC-3 checklist (ISSUE 3+ -> python_warnings cap 3)
    |
    v
Adaptive decision (threshold 기반 CONDITIONAL_PASS 판정)
    |
    v
Director 주권 (REJECT 불가역)
    |
    v
Final verdict
```
