<!-- [참고자료] -->
# TF-SV: ScoringValidator 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | ScoringValidator: score calculation, genre weights, thresholds, LLM integration |
| Source files | `modules/validation/scoring_validator.py` (1,275줄) |
| Related files | `modules/validation/validation_orchestrator.py`, `modules/validation/threshold_helper.py`, `modules/validation/dialogue_utils.py` |
| TF Items | 14 (CRITICAL 2 / IMPORTANT 7 / INSIGHT 5) |

---

## 1. Executive Summary

ScoringValidator는 TIER 2 검증기로서 Python 기반 4개 평가(prose_rhythm, vocabulary_diversity, sensory_balance, show_dont_tell, 각 max=5, 합계 20점)와 LLM 기반 6개 평가(character_consistency, emotion_arc, dialogue_quality, commercial_appeal, pattern_diversity, reader_satisfaction, 합계 80점)를 합산하여 총 100점 만점으로 원고 품질을 평가한다.

`validate()` 메서드는 원시 점수를 합산하고, `validate_v59()` 메서드는 장르별 가중치를 적용한 후 +-1점 캡으로 최종 점수를 산출한다. ValidationOrchestrator에서 호출되며, 적응형 임계값(adaptive threshold), Self-Consistency 다수결 투표, 이전 Tier 결과에 의한 감점 등이 외부에서 추가된다.

주요 발견:
- **CRITICAL**: LLM에 전달되는 원고가 3,000자로 절단되어 4,000~15,000자 원고의 75~80%가 평가에서 누락됨
- **CRITICAL**: `validate_v59()`의 weighted_percentage vs raw_total 비교에서 단위 불일치로 인해 +-1점 캡이 의도와 다르게 작동할 수 있음
- **IMPORTANT**: 7건의 점수 무결성, 에러 핸들링, 투명성 관련 문제

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                        +------------------------------+
                        | ValidationOrchestrator       |
                        | (validation_orchestrator.py) |
                        +------------------------------+
                           |                        |
                    [sync path]              [async/parallel path]
                           |                        |
              +------ scoring.pass_threshold 주입 ------+
              |   (adaptive threshold 또는 config 값)    |
              +------------------------------------------+
                           |
                  +--------v--------+
                  | ScoringValidator |
                  | .validate_v59() |
                  +--------+--------+
                           |
              +------------+------------+
              |                         |
     +--------v--------+      +--------v--------+
     | .validate()     |      | validate_v59    |
     | (base method)   |      | 장르 가중치 적용  |
     +--------+--------+      +--------+--------+
              |                         |
     +--------+--------+      (weighted_score = raw * weight)
     |                 |      (delta cap = +-1점)
     v                 v
+----------+   +----------+
| Python   |   | LLM      |
| Scores   |   | Scores   |
| (20/100) |   | (80/100) |
+----------+   +----------+
     |              |
     |    +---------+---------+
     |    |                   |
     |    v                   v
     | [LLM 호출 성공]    [LLM 실패]
     |    |                   |
     |    v                   v
     | _parse_and_clamp    _fallback_llm_scores
     | (0 <= score <= max)  (휴리스틱 기반)
     |    |                   |
     +----+-------------------+
              |
              v
     +------------------+
     | all_scores merge |
     | {**python, **llm}|
     +--------+---------+
              |
              v
     _safe_score() 합산
     total_score = sum(...)
              |
              v
     passed = (total >= threshold)

Python 평가 항목 (max 5 each, total 20):
+-------------------+--------------------+
| prose_rhythm(5)   | CV(문장길이 변동)   |
| vocab_diversity(5)| TTR(어휘다양성)     |
| sensory_balance(5)| 오감묘사 비율       |
| show_dont_tell(5) | 직접서술 빈도       |
+-------------------+--------------------+

LLM 평가 항목 (configurable, default total 80):
+-------------------------+-----+
| character_consistency   |  15 |
| emotion_arc             |  15 |
| dialogue_quality        |  15 |
| commercial_appeal       |  15 |
| pattern_diversity       |  10 |
| reader_satisfaction     |  10 |
+-------------------------+-----+

validate_v59() 후처리:
+-------------------------------------------+
| 1. base validate() 호출                    |
| 2. 장르 가중치 적용 (GENRE_WEIGHTS dict)    |
| 3. weighted_percentage 산출                |
| 4. +-1점 캡: capped = raw + clamp(delta)   |
| 5. capped >= threshold → PASS/FAIL        |
+-------------------------------------------+

Orchestrator 후처리:
+-------------------------------------------+
| 1. CONTINUITY advisory 감점 (max -15)      |
| 2. BLOCKING advisory 감점 (max -20)        |
| 3. CONSISTENCY 감점                        |
| 4. Pre-LLM 감점 (max -1)                  |
| 5. Catharsis 조정 (-5 ~ 0)                 |
| 6. Action 조정 (-3 ~ +2)                  |
| 7. 최종: PASS / CONDITIONAL_PASS / REJECT  |
+-------------------------------------------+
```

---

## 3. TF Items

### TF-SV-01: LLM 원고 절단 — 3,000자 제한으로 75~80% 원고 누락 -- CRITICAL

- **Location**: `scoring_validator.py:L17, L98-L116, L189`
- **Description**: `_sanitize_manuscript()` 메서드가 원고를 `_SANITIZE_MAX_CHARS = 3000`자로 절단한다. 그러나 프로덕션 원고는 `ManuscriptLimits.MIN_LENGTH = 4000`, `TARGET_LENGTH = 5000`, `MAX_LENGTH = 15000`이므로, 최소한 1,000자(25%)에서 최대 12,000자(80%)가 LLM 평가에서 누락된다.
- **Evidence**:
  ```python
  # L17
  _SANITIZE_MAX_CHARS = int(_threshold("scoring.sanitize_max_chars", 3000))

  # L116
  return sanitized[:_SANITIZE_MAX_CHARS]

  # L189 — LLM 호출 직전
  safe_manuscript = self._sanitize_manuscript(manuscript)
  ```
- **Impact**: LLM은 원고의 앞부분만 보고 전체 품질을 평가한다. 후반부의 캐릭터 일관성 붕괴, 감정선 급변, 대화 품질 저하 등을 전혀 감지하지 못한다. 특히 클리프행어나 결말 품질(commercial_appeal, reader_satisfaction)은 원고 후반에 집중되므로 구조적으로 과대평가된다.
- **반면**: Python 평가 4개(prose_rhythm, vocabulary_diversity, sensory_balance, show_dont_tell)는 `_sanitize_manuscript()`를 거치지 않고 전체 원고를 대상으로 한다 (L168-L178). LLM/Python 평가 간 평가 범위 불일치.
- **Suggested fix direction**: `_SANITIZE_MAX_CHARS`를 최소 `ManuscriptLimits.TARGET_LENGTH` (5,000)로 상향하거나, LLM 모델의 컨텍스트 윈도우(Gemini 2.5 Pro: 1M tokens)를 고려하여 15,000자까지 허용. 또는 원고 앞/중/뒤 구간을 샘플링하여 전달하는 방식으로 개선.

---

### TF-SV-02: weighted_percentage vs raw_total 단위 불일치로 +-1점 캡 오작동 위험 -- CRITICAL

- **Location**: `scoring_validator.py:L945-L962`
- **Description**: `validate_v59()`에서 `weighted_percentage`는 백분율(0~100%)이고 `raw_total`은 합산 점수(0~100점)이다. 두 값이 동일 스케일(0~100)이므로 코드 주석에서 "단위 차이가 안전하게 흡수됨"이라 주장하지만, 실제로는 의미가 다르다.

  가중치 적용 시 `weighted_max_total`이 100이 아닐 수 있다 (장르 가중치가 1.0이 아닌 항목이 다수). 예를 들어 wuxia의 경우:
  - Python 4항목 가중치 합: 1.2 + 1.0 + 1.3 + 1.0 = 4.5 (기본 4.0 대비 +0.5)
  - LLM 6항목 가중치 합: 1.0 + 0.9 + 1.0 + 1.1 + 1.1 + 1.3 = 6.4 (기본 6.0 대비 +0.4)
  - weighted_max = 5*1.2 + 5*1.0 + 5*1.3 + 5*1.0 + 15*1.0 + 15*0.9 + 15*1.0 + 15*1.1 + 10*1.1 + 10*1.3 = 6+5+6.5+5+15+13.5+15+16.5+11+13 = 107
  - 따라서 weighted_percentage = weighted_total/107 * 100

  만약 모든 항목이 만점이면: raw_total=100, weighted_total=107, weighted_percentage=100%. delta=100-100=0, cap 무관. 정상.

  그러나 부분 점수일 때: raw_total=70이면 weighted_total은 약 75 정도(가중치 높은 항목이 잘 나왔을 때), weighted_percentage=75/107*100=70.1%. delta=round(70.1)-70=0. 거의 영향 없음. 이 경우는 안전.

  **하지만** 역방향 시나리오에서: 가중치가 높은 항목(reader_satisfaction 1.3, sensory_balance 1.3)이 낮고, 가중치 낮은 항목(emotion_arc 0.9)이 높은 경우, weighted_percentage가 raw_total보다 유의미하게 낮아질 수 있다. delta=-3 정도면 cap으로 인해 -1점만 적용되어, 장르 맥락 반영이 사실상 무효화된다.

- **Evidence**:
  ```python
  # L948
  weighted_percentage = weighted_total / weighted_max_total * 100
  # L960-961
  _genre_delta = round(weighted_percentage) - raw_total
  capped_score = raw_total + max(-1, min(1, _genre_delta))
  ```
- **Impact**: +-1점 캡은 장르 가중치의 의미를 거의 소거한다. 가중치 범위가 0.8~1.5로 20~50%까지 차이나는데, 최종 점수에 미치는 영향은 +-1점으로 제한된다. 이는 V59 장르별 가중치 시스템의 설계 의도(장르 맥락 반영)와 모순될 수 있다.
- **Suggested fix direction**: 캡의 의도가 "Python 판단 최소화"(대원칙 #1)라면 현재 설계가 의도적일 수 있으나, 그 경우 GENRE_WEIGHTS 딕셔너리 자체가 거의 죽은 코드가 된다. 캡 범위를 +-3 정도로 확장하거나, 장르 가중치를 LLM 프롬프트에 반영하여 LLM 자체가 장르 맥락을 고려하도록 하는 것이 더 효과적.

---

### TF-SV-03: Fallback 점수가 중간값으로 고정되어 품질 문제를 은폐 -- IMPORTANT

- **Location**: `scoring_validator.py:L307-L370`
- **Description**: LLM 호출 실패 시 `_fallback_llm_scores()` 메서드가 실행된다. 이 메서드는 6개 항목 중 대부분을 중간 수준의 안전한 점수로 반환한다:
  - pattern_diversity: 항상 min(10, 6) = 6/10
  - reader_satisfaction: 항상 min(10, 5) = 5/10
  - character_consistency: min(15, len/300) — 4000자 원고면 13/15
  - emotion_arc: min(15, 8 + markers/5) — 보통 9~13/15
  - commercial_appeal: min(15, 8 + len/500) — 4000자면 16→15/15

  총합: 약 48~52점 (fallback만). Python 점수 12~18점 추가하면 총 60~70점. pass_threshold=70이면 경계선.

- **Evidence**:
  ```python
  # L334 — 항상 고정값
  pattern_score = min(score_breakdown["pattern_diversity"], 6)
  # L337 — 항상 고정값
  satisfaction_score = min(score_breakdown["reader_satisfaction"], 5)
  ```
- **Impact**: LLM 실패 시 품질 판별이 불가능해지고, 중간 점수가 반환되어 CONDITIONAL_PASS로 통과할 수 있다. reason 필드에 "LLM 없음 - Fallback 추정치" 표시가 있지만, 이를 읽는 호출자(ValidationOrchestrator)가 이를 특별히 처리하지 않는다.
- **Suggested fix direction**: Fallback 결과에 `"degraded": True` 플래그를 추가하고, Orchestrator에서 degraded 평가 시 CONDITIONAL_PASS로 캡하거나 로그에 경고 강화.

---

### TF-SV-04: NaN/Infinity 방어 미비 -- IMPORTANT

- **Location**: `scoring_validator.py:L144-L153, L162, L472-L476, L541-L549`
- **Description**: `_safe_score()` 함수(L144-L151)는 `float(s)` 변환에 성공하면 그대로 합산한다. 그러나 `float("nan")`, `float("inf")`도 변환에 성공한다. NaN이 하나라도 섞이면 `total_score`이 NaN이 되어 `passed = NaN >= 70` 이 `False`를 반환하지만, percentage 계산(L162)에서 `NaN / 100 * 100 = NaN`이 반환되어 하위 시스템에 전파된다.

  마찬가지로 `_evaluate_prose_rhythm()`의 CV 계산(L476)에서 `mean_len=0`이면 `cv=0`으로 안전하게 처리되지만, `statistics.stdev()`가 매우 유사한 값들에서 부동소수점 정밀도 문제로 극소값을 반환할 수 있다(이는 실질적 위험은 낮음).

  `_evaluate_vocabulary_diversity()`의 TTR 샘플링(L541-549)에서 `statistics.mean(ttr_samples)`는 빈 리스트일 때 `StatisticsError`를 발생시키지만, L545에서 `if not ttr_samples`로 가드되어 있어 안전.

- **Evidence**:
  ```python
  # L144-151: NaN/Inf 미방어
  def _safe_score(v):
      if not isinstance(v, dict):
          return 0
      s = v.get("score", 0)
      try:
          return float(s)  # float("nan"), float("inf") 모두 성공
      except (TypeError, ValueError):
          return 0
  ```
- **Impact**: LLM이 score를 "NaN" 또는 "Infinity" 문자열로 반환할 가능성은 낮지만, 방어가 없다. `response_mime_type="application/json"` 설정(L260)으로 JSON 파싱되므로 NaN 문자열은 "NaN" string으로 파싱되어 `float("NaN")`이 성공한다. 또한 L290-298의 클램핑에서 `int(_val["score"])`는 `int(float("nan"))`에서 `ValueError`를 발생시키므로 score=0으로 대체된다. 따라서 `validate()` 내 `_safe_score`에서의 NaN 위험은 LLM 결과가 클램핑을 거친 후에는 완화되지만, `validate()`가 직접 호출될 경우(validate_v59를 거치지 않는 경로)에는 클램핑이 적용되지 않는다.
- **Suggested fix direction**: `_safe_score()`에 `math.isfinite()` 체크 추가:
  ```python
  import math
  def _safe_score(v):
      ...
      f = float(s)
      return f if math.isfinite(f) else 0
  ```

---

### TF-SV-05: validate() 직접 호출 시 LLM 점수 클램핑 미적용 -- IMPORTANT

- **Location**: `scoring_validator.py:L118-L166 vs L290-L298`
- **Description**: LLM 점수 클램핑(`score = max(0, min(int(score), int(max)))`)(L290-298)은 `_calculate_llm_scores()` 내부에서 수행된다. 이는 `validate()`와 `validate_v59()` 모두에 적용된다.

  **그러나** 문제는 `validate()`가 `_calculate_llm_scores()`를 호출하기 전에 반환되는 Python 점수(L135)에는 클램핑이 없다는 점이 아니라, Python 점수는 코드에서 직접 계산되므로 안전하다. 문제는 `validate()`의 반환값에서 `percentage` 계산이다:

  ```python
  # L162
  "percentage": (total_score / max_score) * 100,
  ```

  여기서 `max_score = 100`으로 하드코딩되어 있다(L154). 만약 `_get_score_breakdown()`에서 validation.yaml 설정으로 LLM 항목 max를 변경했다면(예: character_consistency=20), 실제 max가 100이 아닐 수 있다. 그러나 Python 항목 max(5*4=20)는 하드코딩되어 있어 변경 불가능하므로, LLM 항목 합계가 80이 아니게 되면 percentage 계산이 부정확해진다.

- **Evidence**:
  ```python
  # L154: 하드코딩된 max
  max_score = 100
  # L372-381: 동적으로 로드되는 LLM 항목 max
  def _get_score_breakdown(self) -> dict[str, int]:
      for key, default in self.DEFAULT_SCORE_BREAKDOWN.items():
          value = _threshold(f"scoring.breakdown.{key}", default)
          breakdown[key] = max(1, int(value))
  ```
- **Impact**: validation.yaml에서 `scoring.breakdown.*` 값을 변경하면 실제 max 합계와 하드코딩된 `max_score=100` 사이에 불일치 발생. percentage가 100%를 초과하거나 실제보다 낮게 계산될 수 있다.
- **Suggested fix direction**: `max_score`를 동적으로 계산: `max_score = sum(Python max들) + sum(_get_score_breakdown().values())`

---

### TF-SV-06: 장르 매칭 실패 시 silent fallback to wuxia -- IMPORTANT

- **Location**: `scoring_validator.py:L903-L904`
- **Description**: `validate_v59()`에서 장르를 결정할 때 `self.genre` 또는 `validation_context.get("genre", "wuxia")`를 사용한다. 미지의 장르(예: "romance")가 전달되면 `GENRE_WEIGHTS.get(genre, self.GENRE_WEIGHTS["wuxia"])`로 wuxia 가중치가 적용된다. 이 fallback은 로그 없이 조용히 발생한다.
- **Evidence**:
  ```python
  # L903
  genre = self.genre or validation_context.get("genre", "wuxia")
  # L904
  weights = self.GENRE_WEIGHTS.get(genre, self.GENRE_WEIGHTS["wuxia"])
  ```
- **Impact**: 새 장르 추가 시 GENRE_WEIGHTS에 엔트리를 빠뜨리면, 해당 장르가 무협 가중치로 평가된다. 요리 장르에 무협의 sensory_balance 1.3, reader_satisfaction 1.3 가중치가 적용되는 것은 의미가 다르다.
- **Suggested fix direction**: 알 수 없는 장르일 때 WARNING 로그 + 기본 가중치(모든 항목 1.0) 사용.

---

### TF-SV-07: 오감 묘사 키워드 false positive 위험 -- IMPORTANT

- **Location**: `scoring_validator.py:L582-L616`
- **Description**: `_evaluate_sensory_balance()`에서 사용하는 키워드가 매우 짧고 일반적이다:
  - visual: "보" (모든 "보다", "보호", "보물" 등에 매칭)
  - auditory: "들" (모든 "들어", "들판" 등에 매칭)
  - tactile: "부드" (부드럽다뿐 아니라 부드러운/부드러웠다 등 OK, 그러나 "부드" 자체는 정확)
  - gustatory: "달", "써" (달리다, 써먹다 등 매칭)
  - gustatory: "시" (모든 "시간", "시작", "시련" 등에 매칭)

  특히 "시"가 gustatory(미각)로 분류되는데, 한국어에서 "시"는 극히 일반적인 음절이다. 이로 인해 gustatory 카운트가 부풀려지고, visual_ratio가 낮아져서 인위적으로 높은 점수를 받게 된다.

- **Evidence**:
  ```python
  # L587
  "gustatory": ["맛", "달", "써", "짜", "시"],
  ```
  "시"를 포함하는 일반 단어: 시간, 시작, 시련, 시야, 시선, 시체, 시장, 시대, 시점 등.
  4000자 원고에서 "시"는 수십 회 출현 가능 → gustatory 카운트 대폭 증가.
- **Impact**: 미각 묘사가 실제보다 과대 집계되어 감각 균형이 좋다고 오판. sensory_balance 점수 인플레이션. 무협/판타지 등 미각 묘사가 거의 없는 장르에서도 "시작", "시간" 등의 일반 단어로 인해 미각이 감지됨.
- **Suggested fix direction**: 키워드를 최소 2음절 이상으로 확장하거나 정규식으로 경계 조건 추가. 예: "시다", "신맛" 대신 "시"는 제거. "달콤", "달다"로 교체. "들리", "들었" 등으로 세분화.

---

### TF-SV-08: show_dont_tell의 pre_reject 신호가 미활용 -- IMPORTANT

- **Location**: `scoring_validator.py:L725`
- **Description**: `_evaluate_show_dont_tell()`의 반환값에 `"pre_reject": ratio > 5 or total_sensory < 3` 플래그가 포함되어 있다. 이 플래그는 극심한 직접 서술이나 감각 묘사 절대 부족을 나타내는 강력한 신호이다. 그러나 이 값은 `_calculate_python_scores()`의 결과 dict에 포함될 뿐, `validate()`나 `validate_v59()`에서 참조되지 않는다. 최종 결과의 breakdown에는 포함되지만, PASS/FAIL 판정에는 영향을 미치지 않는다.
- **Evidence**:
  ```python
  # L725
  "pre_reject": ratio > 5 or total_sensory < 3,
  ```
  이 값을 참조하는 코드가 scoring_validator.py 내에 없음.
- **Impact**: 극심한 품질 문제가 있어도 다른 항목의 높은 점수로 보완되면 PASS 가능. pre_reject가 True인 상황은 명백한 품질 문제인데 활용되지 않음.
- **Suggested fix direction**: `validate()`에서 pre_reject 체크 후 total_score에서 추가 감점하거나, breakdown에 warning 플래그로 Orchestrator에 전달.

---

### TF-SV-09: Guard 메서드 오류 시 bare except + silent pass -- IMPORTANT

- **Location**: `scoring_validator.py:L433-L434, L449-L450`
- **Description**: `_generate_dynamic_context()`에서 Guard의 `get_impossible_actions()`와 `get_justification_patterns()` 호출 시 `except (AttributeError, Exception): pass`로 모든 예외를 조용히 무시한다. `Exception`은 `AttributeError`를 포함하므로 `(AttributeError, Exception)`은 단순히 `Exception`과 동일하다. Guard가 잘못된 데이터를 반환하거나 내부 오류가 발생해도 LLM에 불완전한 컨텍스트가 전달되어, 캐릭터 일관성 평가의 정확도가 저하된다.
- **Evidence**:
  ```python
  # L433-434
  except (AttributeError, Exception):
      pass  # Guard 메서드 오류 시 조용히 무시
  # L449-450
  except (AttributeError, Exception):
      pass  # Guard 메서드 오류 시 조용히 무시
  ```
- **Impact**: Guard 로직의 버그나 데이터 문제가 완전히 은폐된다. LLM이 "불가능한 행동" 목록 없이 캐릭터 일관성을 평가하면 부정확한 점수가 산출된다.
- **Suggested fix direction**: `logging.debug()` 또는 `logging.warning()`으로 예외를 기록하고, `except Exception`으로 단순화.

---

### TF-SV-10: 문장 분리 로직의 한국어 부적합성 -- INSIGHT

- **Location**: `scoring_validator.py:L732-L736`
- **Description**: `_split_sentences()`가 `re.split(r"[.!?]\s+", text)`로 문장을 분리한다. 한국어 웹소설에서는:
  1. 마침표 뒤에 공백 없이 바로 줄바꿈하는 경우가 많음 ("했다.\n다음 날")
  2. 한국어 마침표 대용인 "~", "..." 사용 빈도가 높음
  3. 대화 종결("라고 말했다.")에서 따옴표 안의 문장부호로 잘못 분리될 수 있음
  4. "했다. 그리고" (공백 1개)는 매칭되지만, "했다.그리고" (공백 없음)는 매칭 안 됨

  이로 인해 `_evaluate_prose_rhythm()`의 CV 계산에서 문장 길이 분포가 왜곡되어 리듬 점수가 부정확해질 수 있다.
- **Evidence**:
  ```python
  # L735
  sentences = re.split(r"[.!?]\s+", text)
  ```
- **Impact**: prose_rhythm 점수(max 5점)의 정확도 저하. 그러나 전체 100점 중 5점이므로 최종 판정에 대한 영향은 제한적.
- **Suggested fix direction**: 한국어에 적합한 문장 분리: `re.split(r'[.!?…~]+[\s\n]+|[.!?…~]+$', text)` 또는 줄바꿈도 분리 기준에 포함.

---

### TF-SV-11: Self-Consistency 다수결에서 random 사용으로 비결정적 결과 -- INSIGHT

- **Location**: `validation_orchestrator.py:L760-L769`
- **Description**: Self-Consistency 평가에서 소프트 마진 적용 시 `random.random() < 0.5`로 50% 확률로 멀티보팅 확대 여부를 결정한다. 동일 원고, 동일 조건에서 실행할 때마다 결과가 달라질 수 있다.
- **Evidence**:
  ```python
  # L764-769 (validation_orchestrator.py)
  if ambiguous_lower - soft_margin <= first_score < ambiguous_lower:
      if random.random() < 0.5:
          effective_lower = ambiguous_lower - soft_margin
  ```
- **Impact**: 점수가 68~72 또는 85~87 구간에 있을 때, 같은 원고가 1-vote 평가를 받기도 하고 3-vote 평가를 받기도 한다. 이는 재현성을 해치지만, LLM 자체의 비결정성이 이미 존재하므로 추가적 비결정성의 상대적 영향은 크지 않다.
- **Suggested fix direction**: `random.seed(hash(manuscript[:100]))`로 원고 기반 결정적 시드를 사용하거나, soft_margin을 제거하고 명확한 구간 경계만 사용.

---

### TF-SV-12: 장르별 가중치 합이 10.0이 아니어서 weighted_max 불균형 -- INSIGHT

- **Location**: `scoring_validator.py:L751-L882`
- **Description**: 각 장르의 10개 항목 가중치 합이 서로 다르다:
  - wuxia: 1.2+1.0+1.3+1.0+1.0+0.9+1.0+1.1+1.1+1.3 = **10.9**
  - hunter: 1.0+0.9+1.1+1.2+1.1+1.0+0.9+1.3+1.0+1.2 = **10.7**
  - investment: 0.9+1.2+0.8+1.1+1.2+1.2+1.1+1.0+1.2+0.8 = **10.5**
  - fantasy: 1.1+1.1+1.2+1.1+1.1+1.0+0.9+1.2+1.0+1.2 = **10.9**
  - cooking: 1.0+1.1+1.5+1.2+1.0+1.0+0.9+1.0+1.1+1.1 = **10.9**
  - composer: 1.3+1.2+1.2+1.1+1.0+1.3+0.9+0.9+1.0+1.0 = **10.9**
  - alt_history: 1.0+1.3+1.0+1.0+1.3+1.1+1.2+0.9+1.1+1.0 = **10.9**
  - actor: 1.0+1.1+1.0+1.3+1.2+1.2+1.2+1.0+0.9+1.0 = **10.9**
  - sports: 1.3+1.1+1.2+1.1+1.0+1.1+0.8+1.1+1.0+1.2 = **10.9**
  - medical: 0.9+1.3+1.1+1.2+1.2+1.2+1.1+0.9+1.0+1.0 = **10.9**

  investment가 10.5로 가장 낮고 나머지 대부분이 10.9이다. 이 차이는 `weighted_max_total`에 반영되어 weighted_percentage 계산에 영향을 준다. 그러나 TF-SV-02의 +-1점 캡으로 인해 최종 점수에 대한 영향은 사실상 무시할 수 있다.

- **Impact**: 이론적으로 장르 간 공정성에 영향. 실질적으로는 +-1점 캡 때문에 무시 가능.
- **Suggested fix direction**: 가중치 합이 10.0이 되도록 정규화하거나, 가중치를 상대적 비율로만 사용하고 합산 후 100점 만점으로 정규화.

---

### TF-SV-13: Orchestrator에서 scoring.pass_threshold 직접 변경 -- thread safety 위험 -- INSIGHT

- **Location**: `validation_orchestrator.py:L361-L372, L1160-L1174`
- **Description**: ValidationOrchestrator가 `self.scoring.pass_threshold`를 직접 변경하여 적응형 임계값을 적용한다. try/finally로 복원을 보장하지만, 병렬 경로(L1254-L1269)에서 `self.scoring.validate_v59()`가 ThreadPoolExecutor 내에서 실행될 때, 동일 `self.scoring` 인스턴스의 `pass_threshold`가 경합 상태(race condition)에 노출될 수 있다.

  현재 구현에서는 하나의 ValidationOrchestrator 인스턴스가 동시에 여러 validate 호출을 받는 시나리오가 없어 보이지만, 향후 멀티스레드 환경에서 문제가 될 수 있다.
- **Evidence**:
  ```python
  # validation_orchestrator.py L365
  self.scoring.pass_threshold = adaptive_threshold
  # L372
  self.scoring.pass_threshold = _original_threshold
  ```
- **Impact**: 현재는 안전하지만, 향후 동시성 확장 시 위험. pass_threshold가 예기치 않게 변경되면 PASS/FAIL 판정이 뒤집힐 수 있다.
- **Suggested fix direction**: `pass_threshold`를 인스턴스 속성이 아닌 `validate_v59()` 메서드의 파라미터로 전달.

---

### TF-SV-14: 점수 breakdown 감사 추적 부족 -- INSIGHT

- **Location**: `scoring_validator.py:L157-L166, L964-L980`
- **Description**: `validate()` 반환값에 breakdown이 포함되지만, 다음 정보가 누락된다:
  1. 어떤 항목이 Python 평가이고 어떤 항목이 LLM 평가인지 구분 없음
  2. LLM fallback이 사용되었는지 여부가 최종 결과 dict에 없음 (reason 필드에만 표시)
  3. `validate_v59()`에서 `capped_score`가 `raw_total`과 다를 때, 캡이 적용되었는지 여부가 명시적으로 기록되지 않음
  4. adaptive threshold가 적용되었는지 여부는 Orchestrator 레벨에서만 기록됨

- **Evidence**:
  ```python
  # L141: Python/LLM 구분 없이 단순 merge
  all_scores = {**python_scores, **llm_scores}
  # L157-166: degraded 플래그 없음
  return {
      "tier": "SCORING",
      "passed": passed,
      ...
  }
  ```
- **Impact**: 디버깅 시 점수가 낮은 원인을 추적하기 어려움. 특히 LLM fallback 사용 여부를 알 수 없으면 점수 신뢰도를 판단할 수 없음.
- **Suggested fix direction**: 반환 dict에 `"evaluation_source": {"python": [...], "llm": [...], "degraded": False}` 메타데이터 추가.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | 핵심 위험 |
|----|-------|----------|----------|----------|
| TF-SV-01 | LLM 원고 3,000자 절단 | CRITICAL | L17,L116,L189 | LLM이 원고의 20~25%만 평가 |
| TF-SV-02 | weighted_percentage +-1점 캡 설계 의문 | CRITICAL | L945-L962 | 장르 가중치 시스템 사실상 무효화 |
| TF-SV-03 | Fallback 점수 중간값 고정 | IMPORTANT | L307-L370 | LLM 실패 시 품질 문제 은폐 |
| TF-SV-04 | NaN/Infinity 방어 미비 | IMPORTANT | L144-L153 | total_score NaN 전파 가능 |
| TF-SV-05 | max_score=100 하드코딩 | IMPORTANT | L154,L162 | YAML 설정 변경 시 percentage 오류 |
| TF-SV-06 | 미지의 장르 → silent wuxia fallback | IMPORTANT | L903-L904 | 새 장르 추가 시 잘못된 가중치 |
| TF-SV-07 | 오감 키워드 false positive | IMPORTANT | L582-L616 | "시" 등 일반 음절이 미각으로 집계 |
| TF-SV-08 | pre_reject 신호 미활용 | IMPORTANT | L725 | 극심한 품질 문제 미감지 |
| TF-SV-09 | Guard 예외 silent pass | IMPORTANT | L433-L450 | Guard 버그 완전 은폐 |
| TF-SV-10 | 한국어 문장 분리 부적합 | INSIGHT | L732-L736 | prose_rhythm 정확도 저하 |
| TF-SV-11 | Self-Consistency random 비결정성 | INSIGHT | VO:L760-L769 | 재현성 저하 |
| TF-SV-12 | 장르별 가중치 합 불균형 | INSIGHT | L751-L882 | 장르 간 공정성 이론적 편향 |
| TF-SV-13 | pass_threshold 직접 변경 | INSIGHT | VO:L361-L372 | 향후 동시성 위험 |
| TF-SV-14 | 점수 breakdown 감사 추적 부족 | INSIGHT | L157-L166 | 디버깅 어려움 |

(VO = validation_orchestrator.py)

---

## 5. 핵심 코드 참조 (Appendix)

### A. 점수 합산 로직 (validate, L118-L166)

```python
def validate(self, manuscript: str, validation_context: dict) -> dict:
    python_scores = self._calculate_python_scores(manuscript, validation_context)  # 20점
    llm_scores = self._calculate_llm_scores(manuscript, validation_context)        # 80점
    all_scores = {**python_scores, **llm_scores}

    def _safe_score(v):
        if not isinstance(v, dict): return 0
        s = v.get("score", 0)
        try: return float(s)          # <-- NaN/Inf 미방어 (TF-SV-04)
        except (TypeError, ValueError): return 0

    total_score = sum(_safe_score(v) for v in all_scores.values())
    max_score = 100                    # <-- 하드코딩 (TF-SV-05)
    passed = total_score >= self.pass_threshold
```

### B. LLM 원고 절단 (_sanitize_manuscript, L98-L116)

```python
def _sanitize_manuscript(self, text: str) -> str:
    sanitized = text.replace("{", "{{").replace("}", "}}")
    sanitized = "".join(char for char in sanitized if char.isprintable() or char in "\n\r\t")
    return sanitized[:_SANITIZE_MAX_CHARS]  # <-- 3000자 (TF-SV-01)
```

### C. 장르 가중치 캡 (validate_v59, L945-L962)

```python
weighted_percentage = weighted_total / weighted_max_total * 100  # 백분율
_genre_delta = round(weighted_percentage) - raw_total            # 백분율 - 점수
capped_score = raw_total + max(-1, min(1, _genre_delta))         # +-1점 캡
passed = capped_score >= self.pass_threshold
```

### D. Fallback 고정 점수 (_fallback_llm_scores, L334-L337)

```python
pattern_score = min(score_breakdown["pattern_diversity"], 6)     # 항상 6/10
satisfaction_score = min(score_breakdown["reader_satisfaction"], 5)  # 항상 5/10
```

### E. 오감 키워드 false positive (L582-L588)

```python
senses = {
    "visual": ["보", "빛", "색", ...],     # "보"=1음절
    "gustatory": ["맛", "달", "써", "짜", "시"],  # "시"=모든 "시*" 단어에 매칭
}
counts[sense] = sum(manuscript.count(kw) for kw in keywords)  # 부분 문자열 매칭
```

### F. Guard 예외 silent pass (L433-L434)

```python
except (AttributeError, Exception):  # Exception이 AttributeError 포함
    pass  # 로그 없음
```
