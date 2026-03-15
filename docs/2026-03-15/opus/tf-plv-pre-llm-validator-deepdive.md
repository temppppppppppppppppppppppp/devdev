# TF-PLV: PreLLMValidator 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | PreLLMValidator: vocabulary, prose rhythm, dialogue detection, genre sensitivity, POV consistency, error handling |
| Source files | `modules/validation/pre_llm_validator.py` (516줄), `modules/validation/dialogue_utils.py` (34줄), `modules/validation/threshold_helper.py` (24줄) |
| TF Items | 14 (CRITICAL 2 / IMPORTANT 7 / INSIGHT 5) |

---

## 1. Executive Summary

PreLLMValidator는 Tier 0.25 게이트로서 LLM 호출 전 Python 기반 사전 검증을 수행한다. V60.56에서 REJECT 권한이 제거되어 현재는 항상 `passed=True`를 반환하고, 결과는 advisory로 LLM에 전달된다. ValidationOrchestrator에서의 실제 점수 영향은 `score_deduction > 0`일 때 **-1점**으로 제한된다 (TF-C01 대원칙 존중).

핵심 발견:
- **Dead code path**: 병렬 검증 경로(`_validate_parallel_body`)에 `passed=False` 분기가 남아 있어 도달 불가능한 REJECT 로직이 존재
- **대사 감지 사각지대**: ―(dash) 스타일 대사가 `_check_dialogue_presence`에서 카운트되지 않음 (dialogue_utils는 따옴표 계열만 처리)
- **문장 분리 결함**: `[.!?]\s+` 패턴이 한국어 서술 구조와 불일치 - 마침표 뒤 공백 없이 줄바꿈하는 일반적 패턴 미포착
- **장르 민감도 부재**: 10개 검사 중 감각 묘사(#4) 1개만 장르 분기 존재, 나머지 9개는 장르 불문
- **에러 핸들링 부재**: 전체 516줄에 try/except 0건

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                    +-----------------------+
                    |  ValidationOrchestrator |
                    |  (validation_orchestrator.py)  |
                    +-----------+-----------+
                                |
                     validate_v59() / validate_parallel_v59()
                                |
                    +-----------v-----------+
                    | TIER 0.25: PreLLMValidator |
                    |  (pre_llm_validator.py)    |
                    +-----------+-----------+
                                |
          +---------------------+---------------------+
          |                     |                     |
     validate()           _threshold()         dialogue_utils
     (L46-L140)        (threshold_helper.py)   (dialogue_utils.py)
          |
          +---> #1  _check_word_repetition     (L142-L187)  +3점
          +---> #2  _check_extreme_sentence    (L189-L218)  +2점
          +---> #3  _check_dialogue_presence   (L220-L240)  +5점
          +---> #4  _check_sensory_presence    (L242-L269)  +2점
          +---> #5  _check_body_physics        (L271-L292)  +4점
          +---> #6  _check_time_progression    (L294-L318)  +1점
          +---> #7  _check_sentence_endings    (L320-L344)  +1점
          +---> #8  _check_npc_naming          (L346-L388)  +2점
          +---> #9  _check_structural_repetition (L390-L424) +1점
          +---> #10 _check_pov_consistency     (L426-L485)  +2점
                                                            ----
                                                     max: 23점
                                                     cap: 10점
                                |
                    +-----------v-----------+
                    |  Result dict:            |
                    |  passed: True (always)   |
                    |  advisory_issues: [...]   |
                    |  warnings: [...]          |
                    |  score_deduction: 0-10    |
                    +-----------+-----------+
                                |
                    Orchestrator scoring:
                    score_deduction > 0 => -1점 only (TF-C01)

     Separate call path:
     ChiefWriterQuality._check_pov_consistency()
       => PreLLMValidator(pov=...).check_pov_consistency()  (L384-L387)
```

---

## 3. TF Items

### TF-PLV-01: Dead REJECT branch in parallel validation path -- CRITICAL

- **Location**: `validation_orchestrator.py:L1185-L1188`
- **Description**: `_validate_parallel_body`에서 `pre_llm_result["passed"]`를 검사하여 False면 REJECT 결과를 반환하는 분기가 존재한다. 그러나 `PreLLMValidator.validate()`는 V60.56 이후 항상 `passed=True`를 반환한다 (L133). 이 분기는 도달 불가능한 dead code이다.
- **Evidence**:
  ```python
  # validation_orchestrator.py L1185-L1188
  if not pre_llm_result["passed"]:
      return self._build_reject_result_v59(
          "PRE-LLM", pre_llm_result, self._generate_pre_llm_feedback(pre_llm_result)
      )
  ```
  대조:
  ```python
  # pre_llm_validator.py L133
  "passed": True,  # [V60.56] 항상 통과, LLM이 최종 판단
  ```
  sync 경로(`_validate_sync_body` L380-L391)는 이 패턴을 올바르게 제거했지만, parallel 경로는 여전히 old REJECT 로직을 유지하고 있다.
- **Impact**: 코드 이해 혼란. 향후 유지보수자가 이 분기를 실제 동작으로 오해할 수 있다. `_generate_pre_llm_feedback`과 `_build_reject_result_v59`의 PRE-LLM 경로도 dead code.
- **Suggested fix direction**: parallel 경로를 sync 경로와 동일하게 정리. `if not pre_llm_result["passed"]` 분기 제거.

---

### TF-PLV-02: Dash-style dialogue (―) not counted in dialogue presence check -- CRITICAL

- **Location**: `pre_llm_validator.py:L220-L240`, `dialogue_utils.py:L7-L14`
- **Description**: `_check_dialogue_presence`는 `count_dialogue_segments()`를 사용하여 대사 수를 센다. `dialogue_utils.py`의 `_DIALOGUE_PATTERNS`는 6가지 따옴표 패턴(큰따옴표, 스마트따옴표, 작은따옴표 계열, 낫표「」, 겹낫표『』)만 처리한다. 한국 소설에서 매우 빈번하게 사용되는 ―(em dash) 스타일 대사는 완전히 누락된다.
- **Evidence**:
  ```python
  # dialogue_utils.py L7-L14 - ― 패턴 없음
  _DIALOGUE_PATTERNS = (
      r'"[^"\n]+?"',
      r'\u201c[^\u201d\n]+\u201d',
      r"'[^'\n]{5,}'",
      r"\u2018[^\u2019\n]{5,}\u2019",
      r"\u300c[^\u300d\n]+\u300d",
      r"\u300e[^\u300f\n]+\u300f",
  )
  ```
  반면 `_check_pov_consistency` (L431)는 `―[^\n]+` 패턴으로 ― 대사를 인식하여 제거한다. 즉, 같은 파일 내에서 ― 대사의 존재를 알고 있지만, 대사 카운트에는 반영하지 않는다.
- **Impact**: ― 스타일 대사만 사용하는 원고에서 대사 부족 오탐 발생. 이 검사의 score_deduction은 +5점으로 10개 검사 중 최대이며, advisory_issues에 추가되어 LLM 판단에 불필요한 노이즈를 생성한다.
- **Suggested fix direction**: `dialogue_utils.py`에 `r"―[^\n]+"` 패턴을 추가하거나, `_check_dialogue_presence` 내에서 ― 대사를 별도 카운트하여 합산.

---

### TF-PLV-03: Dead code in _check_dialogue_presence (L222-L224) -- IMPORTANT

- **Location**: `pre_llm_validator.py:L222-L224`
- **Description**: `_check_dialogue_presence`의 첫 3줄에서 수동으로 큰따옴표/유니코드 따옴표를 세고 `dialogue_pairs`를 계산하지만, 바로 다음 줄(L227)에서 `count_dialogue_segments(manuscript)`로 덮어쓴다. L222-L224의 결과는 사용되지 않는 dead code이다.
- **Evidence**:
  ```python
  # L222-L224: 결과가 즉시 덮어씌워짐
  dialogue_count = manuscript.count('"') + manuscript.count("\u201c") + manuscript.count("\u201d")
  dialogue_pairs = dialogue_count // 2  # 쌍으로 계산

  # L227: dialogue_pairs 재할당
  dialogue_pairs = count_dialogue_segments(manuscript)
  ```
- **Impact**: 코드 가독성 저하. 리팩토링 시 혼란 유발. 성능상 미미한 낭비(3회 불필요한 string scan).
- **Suggested fix direction**: L222-L224 제거. 주석 "1000자당 최소 1.5회의 대사 필요" (L226)도 실제 계산 `len(manuscript) / 700`과 불일치 (700자당 1회 = 1000자당 ~1.43회).

---

### TF-PLV-04: Sentence splitting pattern misaligned with Korean prose -- IMPORTANT

- **Location**: `pre_llm_validator.py:L193`, `L392`
- **Description**: `_check_extreme_sentence_length`과 `_check_structural_repetition` 모두 `re.split(r"[.!?]\s+", manuscript)`로 문장을 분리한다. 한국어 소설에서는:
  1. 마침표 뒤에 줄바꿈(`\n`)이 오는 경우가 매우 빈번 -- `\s+`는 `\n`을 포함하므로 이 부분은 OK
  2. 그러나 마침표 뒤에 **공백 없이** 다음 문장이 바로 시작되는 경우(`다.그때`)도 흔함 -- 이는 분리 실패
  3. 한국어 문장 종결어미 `~다`, `~요`, `~죠` 뒤에 마침표가 없는 문체도 존재
  4. 인용 부호 내부의 `.!?`도 분리 대상이 됨

  추가로, 이 패턴은 `…`(말줄임표)를 처리하지 않는다. 한국 소설에서 `...`이나 `…`는 문장 경계로 사용되지만, 이 패턴은 `.`만 매칭하므로 `...` 뒤의 분리가 비정상적으로 동작할 수 있다.
- **Evidence**:
  ```python
  # L193, L392 동일 패턴
  sentences = re.split(r"[.!?]\s+", manuscript)
  ```
- **Impact**: 문장 수 과소 측정 시 CV 값이 왜곡되어 prose rhythm 검사의 정확도 저하. structural repetition에서도 문장 경계 오류로 인한 FP/FN 발생.
- **Suggested fix direction**: 한국어에 적합한 문장 분리 패턴으로 교체. 예: `re.split(r'(?<=[.!?…])\s*(?=\S)', manuscript)` 또는 `kss`(Korean Sentence Splitter) 라이브러리 사용 검토.

---

### TF-PLV-05: Sensory check has genre branch only for wuxia -- IMPORTANT

- **Location**: `pre_llm_validator.py:L242-L269`
- **Description**: `_check_sensory_presence`는 장르 분기가 `wuxia`에만 존재한다 (L252-L253). `hunter`, `investment`, `fantasy` 장르에는 장르 특화 감각 키워드가 없다. 이는 다음 문제를 야기한다:
  1. Investment 장르: 사무실/금융 장면에서 시각/촉각 묘사가 부족할 수 있으나, "시세", "차트", "화면" 같은 시각적 키워드가 누락
  2. Hunter 장르: "마나", "오라", "던전", "포탈" 같은 장르 특화 감각어 누락
  3. Fantasy 장르: "마력", "주문", "빛줄기" 같은 감각어 누락
- **Evidence**:
  ```python
  # L252-L253: wuxia만 분기
  if self.genre == "wuxia":
      sensory_keywords["martial"] = ["기혈", "내공", "기운", "살기", "검기", "파동", "기감"]
  ```
- **Impact**: 비무협 장르에서 감각 묘사 오탐 확률 증가. 특히 투자 장르에서 금융 분석 장면은 전통적 감각 묘사와 무관하므로, `missing_count > 3` 임계값을 쉽게 초과할 수 있다.
- **Suggested fix direction**: 각 장르별 감각 키워드 셋 추가. 또는 장르별 `missing_count` 임계값 차등 적용.

---

### TF-PLV-06: NPC name fuzzy matching produces combinatorial false positives -- IMPORTANT

- **Location**: `pre_llm_validator.py:L366-L378`
- **Description**: `_check_npc_naming`은 NPC 이름의 각 글자 위치에 대해 `[가-힣]` 와일드카드로 대체한 정규식을 생성하여 유사 이름을 찾는다. 이 방식에는 두 가지 문제가 있다:
  1. **False positive 폭발**: 2글자 NPC 이름 "소림"의 경우, 위치 0에서 `[가-힣]림` 패턴은 "나림", "가림", "두림" 등 모든 `?림` 패턴을 매칭한다. 3글자 이름이면 3개 패턴, 각각이 11,172개 한글 음절 중 하나를 매칭한다.
  2. **부분 문자열 매칭**: `re.findall`은 단어 경계를 고려하지 않으므로, "소림사" 안의 "소림"이나 "림사" 같은 부분 문자열도 매칭된다.
- **Evidence**:
  ```python
  # L372-L378
  for i in range(len(correct_name)):
      pattern = re.escape(correct_name[:i]) + r"[가-힣]" + re.escape(correct_name[i + 1:])
      similar_names = re.findall(pattern, manuscript)
      for found in similar_names:
          if found != correct_name:
              inconsistencies.append((found, correct_name))
  ```
- **Impact**: NPC 수가 많고 이름이 2글자인 경우 다수의 오탐 발생 가능. `inconsistencies[:3]`으로 최대 3개 제한되지만, 오탐 3개가 warning으로 보고되어 LLM에 노이즈 전달.
- **Suggested fix direction**: 단어 경계 조건 추가 (`\b` 대신 한국어 적합한 경계 패턴 사용). 또는 Levenshtein distance 1 기반의 정확한 유사 이름 매칭으로 전환.

---

### TF-PLV-07: No error handling -- zero try/except in 516 lines -- IMPORTANT

- **Location**: `pre_llm_validator.py` 전체
- **Description**: 전체 516줄에 `try/except` 블록이 단 하나도 없다. 10개 검사 메서드 중 어느 하나에서 예외가 발생하면 `validate()` 전체가 실패한다. 특히:
  1. `_check_word_repetition` L144: 빈 문자열이면 early return하지만, `None`이 들어오면 `re.findall`에서 TypeError
  2. `_check_extreme_sentence_length` L192: `import statistics` 지연 임포트 -- 실패 가능성 낮으나 비표준
  3. `_check_npc_naming` L349-L359: `context` dict 구조가 예상과 다를 때 (e.g., npc_profiles가 리스트) KeyError/TypeError 가능
- **Evidence**: `grep -c "try\|except\|raise" pre_llm_validator.py` => 0건
- **Impact**: ValidationOrchestrator에서 PreLLMValidator 호출이 uncaught exception으로 전체 검증 파이프라인을 중단할 수 있다. Orchestrator 측에서도 PreLLMValidator 호출에 try/except가 없다 (L380-L391).
- **Suggested fix direction**: `validate()` 메서드 내부에서 각 검사를 try/except로 감싸고, 개별 실패 시 해당 검사만 skip하도록 개선. 또는 최소한 `validate()` 전체를 try/except로 감싸서 default pass-through 반환.

---

### TF-PLV-08: Dialogue minimum threshold overly aggressive for long manuscripts -- IMPORTANT

- **Location**: `pre_llm_validator.py:L228`
- **Description**: `expected_min = max(3, int(len(manuscript) / 700))`으로 대사 최소 기준을 계산한다. 5,000자 원고에서 `expected_min = 7`, 10,000자 원고에서 `expected_min = 14`, 15,000자(MAX 한도) 원고에서 `expected_min = 21`이 된다. 이 기준은:
  1. 액션/전투 집중 에피소드에서 대사가 적을 수 있음 (장르 불문)
  2. 독백/내면 서술 중심 에피소드에서 대사가 적을 수 있음
  3. 700자당 1개라는 비율이 장르/상황에 따라 지나치게 높음

  또한 이 검사의 score_deduction이 +5점으로 10개 검사 중 최대이며, `issues`(advisory_issues)에 추가되므로 LLM에 강한 시그널로 전달된다.
- **Evidence**:
  ```python
  # L228 - 700자당 1개 대사 요구
  expected_min = max(3, int(len(manuscript) / 700))
  ```
- **Impact**: 전투 장면이나 내면 독백 중심 에피소드에서 빈번한 오탐. 특히 `ManuscriptLimits.MAX=15000`에서 21개 대사를 요구하는 것은 과도하다.
- **Suggested fix direction**: 장르/장면 유형별 차등 임계값 적용. 또는 기준을 완화 (1000자당 1개 = max(3, int(len/1000))). 임계값을 `_threshold()` 경유로 YAML 설정 가능하게 변경.

---

### TF-PLV-09: get_summary references dead REJECT path -- IMPORTANT

- **Location**: `pre_llm_validator.py:L487-L515`
- **Description**: `get_summary()`의 L497-L498에서 `result["passed"]`가 False인 경우의 분기가 존재한다. 그러나 `validate()`는 항상 `passed=True`를 반환하므로 이 경로는 도달 불가능하다. 또한 L500-L504에서 `critical_issues`를 출력하지만, `validate()`는 항상 `critical_issues: []`를 반환한다.
- **Evidence**:
  ```python
  # L497-L504: 도달 불가능 분기
  if result["passed"]:
      lines.append(f"  통과 (경고 {len(result['warnings'])}개)")
  else:
      lines.append(f"  REJECT (이슈 {len(result['critical_issues'])}개)")  # dead

  if result["critical_issues"]:  # always empty
      lines.append("\n  Critical Issues:")
      for issue in result["critical_issues"]:
          ...
  ```
- **Impact**: 코드 고고학적 잔재. V60.56 REJECT 제거 시 정리되지 않은 부분. 직접적 기능 장애는 없으나 유지보수 혼란.
- **Suggested fix direction**: dead REJECT 분기 및 `critical_issues` 처리 코드 제거. `get_summary()`를 advisory-only 모드에 맞게 단순화.

---

### TF-PLV-10: POV dialogue removal regex inconsistency with dialogue_utils -- INSIGHT

- **Location**: `pre_llm_validator.py:L429-L431` vs `dialogue_utils.py:L7-L14`
- **Description**: `_check_pov_consistency`에서 대화를 제거하는 정규식이 `dialogue_utils.py`의 패턴과 불일치한다:
  - POV 체크: `["""][^"""]*["""]` + `―[^\n]+`
  - dialogue_utils: `"..."`, `\u201c...\u201d`, `'...'`, `\u2018...\u2019`, `\u300c...\u300d`, `\u300e...\u300f`

  POV 체크의 정규식 `["""][^"""]*["""]`은 `"`, `\u201c`, `\u201d`를 하나의 문자 클래스로 합쳐서 매칭하므로, `"...\u201d` 같은 불일치 쌍도 제거한다 (더 관대). 그러나 `'...'` (작은따옴표 계열)과 `\u300c...\u300d` (낫표)는 POV 체크에서 제거 대상이 아니므로, 이 유형의 대사 내부에 "나는" 등이 포함되면 POV 위반으로 오탐될 수 있다.
- **Impact**: 작은따옴표나 낫표로 감싼 대사 내부의 1인칭 표현이 POV 위반으로 잡힐 수 있음. 실제 한국 소설에서 작은따옴표 대사는 드물지만, 낫표 「」는 일부 작품에서 사용됨.
- **Suggested fix direction**: `dialogue_utils.extract_dialogue_segments()`를 재사용하여 대사 영역을 제거하거나, 최소한 낫표 패턴을 POV 제거 대상에 추가.

---

### TF-PLV-11: Docstring/comment count mismatch -- "9가지" vs "10가지" -- INSIGHT

- **Location**: `pre_llm_validator.py:L5 vs L31 vs L48`
- **Description**: 파일 내에서 검사 수에 대한 표현이 일관되지 않는다:
  - L5: "10가지 Python 기반 검사"
  - L31: "원고 검증 전 **9가지** Python 기반 검사"
  - L48: "**9가지** 검증 실행"
  - L139: `"check_count": 10`

  V70에서 10번 POV 체크가 추가되었지만 docstring 2곳이 갱신되지 않았다.
- **Impact**: 문서 정확성. 기능 장애 없음.
- **Suggested fix direction**: L31, L48의 "9가지"를 "10가지"로 수정.

---

### TF-PLV-12: Word repetition stopword list is minimal and not genre-aware -- INSIGHT

- **Location**: `pre_llm_validator.py:L151-L170`
- **Description**: 불용어 목록이 17개로 매우 제한적이다. 한국어 기본 불용어(조사, 접속사, 대명사)만 포함되어 있고, 장르별 고빈도 단어가 포함되지 않았다:
  - 무협: "무공", "검", "장문인", "내공" 등은 15회 이상 반복될 수 있는 도메인 용어
  - 서술 관련: "그녀", "그의", "자신의" 같은 고빈도 서술어 누락
  - 2글자 regex `[가-힣]{2,}`: 조사("에서", "으로", "에게")도 2글자 이상이므로 카운트 대상이 됨

  15회 임계값은 5,000자 원고 기준으로 합리적이나, 15,000자 원고에서는 도메인 용어가 15회를 초과하기 쉬움.
- **Impact**: 장르 특화 용어가 반복으로 잘못 감지될 수 있음. 그러나 advisory-only이고 실제 점수 영향은 -1점이므로 실질적 피해는 제한적.
- **Suggested fix direction**: 장르별 불용어 확장. 또는 임계값을 원고 길이에 비례하도록 동적 조정 (`max(15, len(manuscript) // 500)`).

---

### TF-PLV-13: Body physics check is extremely narrow -- INSIGHT

- **Location**: `pre_llm_validator.py:L271-L292`
- **Description**: `_check_body_physics`는 "손 3개 동시 사용" 패턴 하나만 검사한다. I-07 수정으로 부상-행동 모순 검사가 `continuity_validator`로 이관된 후, 이 메서드는 사실상 1개 패턴만 남았다.

  "왼손/오른손/양손"이 20자 내에 3번 등장하는 패턴은 매우 드물며, 실제 발동 확률이 극히 낮다. 또한 `re.DOTALL`을 사용하므로 줄바꿈을 넘어 매칭할 수 있어 서로 다른 문단의 독립된 행동도 하나로 합칠 수 있다.
- **Evidence**:
  ```python
  triple_action = re.findall(
      r"(왼손|오른손|양손).{0,20}(왼손|오른손|양손).{0,20}(왼손|오른손|양손)",
      manuscript, re.DOTALL,
  )
  ```
- **Impact**: 이 검사의 실효성이 거의 없다. score_deduction +4점이 할당되어 있지만, 발동 확률이 매우 낮아 사실상 inert 코드이다.
- **Suggested fix direction**: 제거하거나, `re.DOTALL` 제거하여 같은 문단 내에서만 매칭. 또는 유의미한 물리 위반 패턴을 추가 (예: 동시에 두 곳에 존재하는 모순).

---

### TF-PLV-14: Time progression check uses first-occurrence-only logic -- INSIGHT

- **Location**: `pre_llm_validator.py:L304-L311`
- **Description**: "같은 날" 다음에 "며칠 후"가 오는 시간 역행을 감지하지만, `manuscript.find()`는 **첫 번째** 출현 위치만 반환한다. 원고에서 "같은 날"이 두 번 이상 등장하면, 첫 번째 "같은 날"과 첫 번째 "며칠 후"의 위치만 비교하므로 정확한 순서 위반을 감지하지 못할 수 있다.

  또한 검사 대상 시간 표현이 9가지로 제한적이며 (L296), "새벽", "정오", "자정", "해질녘" 같은 시간대 표현이나 구체적 시간 ("세 시진 후" 등 무협 시간 단위)은 포함되지 않았다.
- **Evidence**:
  ```python
  # L308-L311: 첫 출현만 비교
  same_day_idx = manuscript.find("같은 날")
  days_later_idx = manuscript.find("며칠 후")
  if same_day_idx >= 0 and days_later_idx >= 0 and days_later_idx < same_day_idx:
      violations.append("시간 흐름 역행 (며칠 후 → 같은 날)")
  ```
- **Impact**: 실질적으로 매우 특정한 케이스만 감지 (첫 "며칠 후"가 첫 "같은 날"보다 앞에 올 때). 다중 출현 시 오탐/미탐 가능. 다만 advisory-only이므로 실질적 피해 제한적.
- **Suggested fix direction**: 모든 출현 위치를 수집하여 순서 관계를 분석. 시간 표현 목록 확장 및 장르별 시간 단위 추가.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | Score Impact | FP Risk |
|----|-------|----------|----------|-------------|---------|
| TF-PLV-01 | Dead REJECT branch in parallel path | CRITICAL | orchestrator.py:L1185-L1188 | 없음 (dead) | 없음 |
| TF-PLV-02 | Dash-style dialogue not counted | CRITICAL | pre_llm_validator.py:L220-L240, dialogue_utils.py:L7-L14 | +5 deduction | HIGH |
| TF-PLV-03 | Dead code in dialogue presence (L222-L224) | IMPORTANT | pre_llm_validator.py:L222-L224 | 없음 | 없음 |
| TF-PLV-04 | Korean sentence splitting misaligned | IMPORTANT | pre_llm_validator.py:L193, L392 | +2/+1 deduction | MEDIUM |
| TF-PLV-05 | Genre branch only for wuxia in sensory check | IMPORTANT | pre_llm_validator.py:L252-L253 | +2 deduction | MEDIUM |
| TF-PLV-06 | NPC name fuzzy matching FP explosion | IMPORTANT | pre_llm_validator.py:L366-L378 | +2 deduction | HIGH |
| TF-PLV-07 | Zero error handling in 516 lines | IMPORTANT | pre_llm_validator.py 전체 | 파이프라인 중단 | N/A |
| TF-PLV-08 | Dialogue threshold too aggressive for long manuscripts | IMPORTANT | pre_llm_validator.py:L228 | +5 deduction | MEDIUM-HIGH |
| TF-PLV-09 | get_summary dead REJECT path | IMPORTANT | pre_llm_validator.py:L497-L504 | 없음 | 없음 |
| TF-PLV-10 | POV dialogue removal inconsistent with dialogue_utils | INSIGHT | pre_llm_validator.py:L429-L431 | +2 deduction | LOW |
| TF-PLV-11 | Docstring count mismatch (9 vs 10) | INSIGHT | pre_llm_validator.py:L31, L48 | 없음 | 없음 |
| TF-PLV-12 | Stopword list minimal and genre-blind | INSIGHT | pre_llm_validator.py:L151-L170 | +3 deduction | LOW-MEDIUM |
| TF-PLV-13 | Body physics check near-inert | INSIGHT | pre_llm_validator.py:L271-L292 | +4 deduction (theoretical) | LOW |
| TF-PLV-14 | Time progression first-occurrence-only | INSIGHT | pre_llm_validator.py:L304-L311 | +1 deduction | LOW |

### Severity Summary
- **CRITICAL**: 2건 (TF-PLV-01, TF-PLV-02)
- **IMPORTANT**: 7건 (TF-PLV-03 ~ TF-PLV-09)
- **INSIGHT**: 5건 (TF-PLV-10 ~ TF-PLV-14)

### False Positive Risk Assessment
- **최대 FP 유발 검사**: #3 대사 부족 (dash dialogue 미감지 + 공격적 임계값) -- score_deduction +5
- **두 번째 FP 유발**: #8 NPC 이름 일관성 (조합적 와일드카드 매칭) -- score_deduction +2
- **세 번째 FP 유발**: #4 감각 묘사 (비무협 장르에서 장르 키워드 부재) -- score_deduction +2
- **실질 점수 영향**: Orchestrator에서 `score_deduction > 0 => -1점`으로 제한 (TF-C01)되므로, FP의 최종 점수 영향은 경미. 그러나 advisory_issues/warnings가 LLM에 전달되어 불필요한 수정 지시를 유발할 수 있음.

---

## 5. 핵심 코드 참조 (Appendix)

### A. validate() 반환값 구조 (L132-L140)
```python
return {
    "passed": True,  # [V60.56] 항상 통과
    "critical_issues": [],  # [V60.56] 항상 빈 리스트
    "advisory_issues": advisory_issues,  # issues 리스트 그대로
    "warnings": warnings,
    "score_deduction": min(10, score_deduction),  # cap 10
    "reason": f"Advisory - 참고사항 {len(advisory_issues)}개, 경고 {len(warnings)}개",
    "check_count": 10,
}
```

### B. Orchestrator에서 PreLLMValidator 결과 소비 (sync path)
```python
# validation_orchestrator.py L380-L391
if self.use_pre_llm and self.pre_llm:
    pre_llm_result = self.pre_llm.validate(manuscript, validation_context)
    results["pre_llm_result"] = pre_llm_result
    # passed 체크 없음 (sync path) -- advisory만

# L596-L600: 점수 반영
if _pre_llm and _pre_llm.get("score_deduction", 0) > 0:
    pre_llm_adjustment = -1  # [TF-C01] 대원칙 존중: 최대 -1점
```

### C. dialogue_utils.py 전체 패턴 (L7-L14)
```python
_DIALOGUE_PATTERNS = (
    r'"[^"\n]+?"',        # 직선 큰따옴표
    r'\u201c[^\u201d\n]+\u201d',  # 스마트 큰따옴표
    r"'[^'\n]{5,}'",      # 직선 작은따옴표 (5자 이상)
    r'\u2018[^\u2019\n]{5,}\u2019',  # 스마트 작은따옴표
    r'\u300c[^\u300d\n]+\u300d',   # 낫표 「」
    r'\u300e[^\u300f\n]+\u300f',   # 겹낫표 『』
)
# 누락: ―(em dash) 스타일 대사
```

### D. score_deduction 적립표
| 검사 | 조건 | 적립 | 분류 |
|------|------|------|------|
| #1 과다 반복 단어 | has_issue | +3 | issues (advisory) |
| #2 문장 길이 극단화 | has_issue | +2 | warnings |
| #3 대사 절대 부족 | missing | +5 | issues (advisory) |
| #4 감각 묘사 누락 | missing_count > 3 | +2 | warnings |
| #5 신체 물리학 | violations | +4 | issues (advisory) |
| #6 시간 흐름 비논리 | violations | +1 | warnings |
| #7 문장 끝 형식 | inconsistency > 0.5 | +1 | warnings |
| #8 NPC 이름 불일치 | inconsistencies | +2 | warnings |
| #9 반복 구조 | repetition > 0.6 | +1 | warnings |
| #10 POV 일관성 | has_issue (pov set) | +2 | warnings |
| **합계 최대** | | **23** | **cap: 10** |

---

*Generated by TF audit process. Baseline: bbb00a77. Read-only investigation -- no code modifications.*
