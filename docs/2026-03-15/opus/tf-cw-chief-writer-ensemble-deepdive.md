<!-- [참고자료] -->
# TF-CW: ChiefWriter 3전략 앙상블 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | ChiefWriter 3-strategy ensemble: candidate generation, self-critique, ranking, final selection |
| Source files | chief_writer.py:1891줄, chief_writer_quality.py:1289줄 |
| TF Items | 14 (CRITICAL 2 / IMPORTANT 6 / INSIGHT 6) |

## 1. Executive Summary

ChiefWriter의 3전략 앙상블 시스템은 `generate_ensemble()` (L289-602)을 중심으로 balanced/narrative/tension 3전략을 `ThreadPoolExecutor`로 병렬 실행하고, 각 후보에 Self-Critique (최대 3라운드)를 적용한 뒤 Director에게 반환하는 구조다. 총체적으로 robust한 방어 체계를 갖추고 있으며, 전면 실패 시 단일 폴백 + error_fallback dict 반환이라는 3단계 방어가 존재한다. 그러나 몇 가지 중요한 엣지 케이스가 식별되었다.

핵심 발견: (1) error_fallback 후보가 `error: True`인 채로 반환되어 downstream에서 빈 원고가 Director에게 전달될 수 있다 -- 이는 downstream의 error 필드 검사 여부에 의존한다. (2) Self-Critique의 `_fix_manuscript_issues`에서 LLM 수정 결과의 JSON 파싱에 성공했지만 content가 비정상적으로 짧은 경우에도 수정본을 반환한다. (3) 누수 방지(leakage sanitization)가 전략 지시문(`[전략 A: 균형]` 등), `writing_strategy` 필드, 프롬프트 래퍼 마커(`### [AUTHOR'S ABSOLUTE DIRECTIVES]`) 등 내부 시스템 마커를 필터링하지 않는다.

전반적으로 ChiefWriter 앙상블 시스템은 프로덕션 안정성 면에서 성숙한 구현이나, error-candidate 전파 경로와 leakage 필터 갭이 가장 우선적으로 보완해야 할 영역이다.

## 2. Architecture / Data Flow Diagram (ASCII)

```
generate_ensemble() [L289-602]
    |
    +-- _prefetch_manuscripts() [L367]          DB 배치 캐시
    +-- context_builder.build_common_context()  [L370-409]  공통 컨텍스트
    +-- _get_or_create_context_cache()          [L413-425]  Gemini 캐시 (optional)
    +-- _select_ensemble_strategies()           [L429-433]  전략 선택 (full/reduced/single)
    |
    +-- ThreadPoolExecutor(max_workers=3) [L440]
    |   |
    |   +-- future[0]: _generate_single_candidate("balanced")  [L604-777]
    |   +-- future[1]: _generate_single_candidate("narrative")
    |   +-- future[2]: _generate_single_candidate("tension")
    |   |
    |   +-- as_completed(timeout=ENSEMBLE_TIMEOUT=600s) [L476]
    |       |
    |       +-- future.result(timeout=SINGLE_CANDIDATE_TIMEOUT=540s) [L480]
    |       |   |
    |       |   +-- SUCCESS: candidates.append(result)
    |       |   +-- FutureTimeoutError: append error stub
    |       |   +-- Exception: append error stub
    |       |
    |       +-- FutureTimeoutError (ensemble): use partial results [L528]
    |       +-- finally: cancel all futures [L537]
    |
    +-- Exception (entire TPE block): log, continue [L539]
    |
    +-- Filter: valid_candidates = [c for c if not c.get("error")] [L554]
    |   |
    |   +-- ALL FAILED: single fallback retry [L556-581]
    |       +-- fallback success: candidates = [fallback]
    |       +-- fallback fail: candidates = []
    |
    +-- STILL EMPTY: error_fallback dict [L584-597] (error=True, manuscript="")
    |
    +-- validate_manuscript_candidate() [L600]   Pydantic ingress
    +-- _annotate_candidate_diversity() [L601]   3-gram Jaccard
    |
    RETURN candidates: list[dict]


_generate_single_candidate() [L604-777]
    |
    +-- Build prompt (strategy config + common_context) [L634-686]
    +-- LLM call: ask() or _ask_with_cached_context() [L667-686]
    +-- sanitize_leakage() [L689]                       누수 필터
    +-- _extract_json_robust() [L691]                   JSON 파싱
    +-- quality_gate.apply_self_critique() [L719-728]   Self-Critique (max 3 rounds)
    |   |
    |   +-- _evaluate_with_rubric()            사전 Rubric (>=3.5 → skip 가능)
    |   +-- _check_ending_hook_presence()      게이트 검사
    |   +-- _check_system_term_exposure()      메타 월
    |   +-- for round in 1..3:
    |   |   +-- _self_critique()               17개 검사 항목
    |   |   +-- severity == "low" → break
    |   |   +-- rubric >= 3.5 (R2+) → break
    |   |   +-- _fix_manuscript_issues()       LLM 수정 호출
    |   +-- return critiqued_manuscript
    |
    +-- Re-extract content from critiqued result [L731-749]
    +-- Remove patch_state_updates leak [L752-754]
    +-- Return candidate dict [L756-769]
    +-- Exception: return None [L771-777]
```

## 3. TF Items

### TF-CW-01: Error Fallback 후보가 error=True 상태로 Downstream 전파 -- CRITICAL

- **Location**: `chief_writer.py:L584-602`
- **Description**: 모든 전략 + 단일 폴백이 실패하면 L584-597에서 `error=True, manuscript=""` 인 error_fallback dict를 생성한다. L600에서 `validate_manuscript_candidate()`를 통과시키지만, `ManuscriptCandidate` 모델은 `error: bool = False`를 기본값으로 가지므로 `error=True`도 유효하게 통과한다. 이 후보가 Director에게 전달되면 빈 원고("")를 평가하게 된다.
- **Evidence**:
  ```python
  # L584-597
  if not candidates:
      candidates = [
          {
              "strategy": "error_fallback",
              ...
              "manuscript": "",
              ...
              "error": True,
          }
      ]
  # L600 — Pydantic 검증은 error=True를 통과시킴
  candidates = [validate_manuscript_candidate(c) for c in candidates]
  ```
  `stage4_interview_round.py`에서는 candidates를 받은 후 `error` 필드를 직접 검사하는 코드가 없다 (grep 결과 확인). Director가 빈 원고를 평가하는 비정상 경로가 열린다.
- **Impact**: Director가 빈 원고에 대해 평가를 시도하여 LLM 비용 낭비 + 무의미한 REJECT/PASS 판정. 최악의 경우 빈 원고가 PASS되어 저장될 수 있다.
- **Suggested fix direction**: `generate_ensemble()` 반환 직전에 `error=True`인 후보를 필터링하거나, error_fallback 시 명시적 예외를 발생시켜 stage4에서 즉시 "모든 후보 실패" 처리 경로로 진입하도록 한다.

---

### TF-CW-02: Self-Critique _fix_manuscript_issues에서 수정본이 MIN_LENGTH 미달이어도 반환 -- IMPORTANT

- **Location**: `chief_writer_quality.py:L1138-1161`
- **Description**: `_fix_manuscript_issues()`에서 LLM 수정 결과를 JSON 파싱한 후, content 길이가 `MIN_LENGTH` 미만이면 경고 로그만 찍고 수정본을 그대로 반환한다(L1155). 원본 보존으로 폴백하지 않는다. 이로 인해 Self-Critique가 원고를 "축소 수정"하여 분량 기준 미달 원고가 생성될 수 있다.
- **Evidence**:
  ```python
  # L1143-1158
  try:
      _fixed_parsed = json.loads(fixed)
      _fixed_content = _fixed_parsed.get("content", "") if isinstance(_fixed_parsed, dict) else ""
      if isinstance(_fixed_content, str):
          _fc_len = len(_fixed_content)
          _min = int(ManuscriptLimits.MIN_LENGTH)
          if _fc_len < _min:
              logging.warning(...)  # 경고만, 폴백 없음
      return fixed  # <-- MIN_LENGTH 미만이어도 수정본 반환
  except (json.JSONDecodeError, ValueError, TypeError):
      return manuscript  # JSON 파싱 실패 시에만 원본 유지
  ```
- **Impact**: Self-Critique가 과도하게 삭제하여 원고 분량이 4,000자 미만으로 떨어질 수 있다. 다만 후속 Self-Critique 라운드에서 `manuscript_length` 이슈가 재감지되어 다시 확장 시도가 일어나므로, 실질적 위험은 최종 라운드(R3)에서만 발생.
- **Suggested fix direction**: `_fc_len < _min` 일 때 `return manuscript` (원본 유지)로 폴백하거나, 수정본과 원본 중 긴 쪽을 선택하는 로직 추가.

---

### TF-CW-03: Leakage 필터가 전략 지시문/시스템 마커를 제거하지 않음 -- IMPORTANT

- **Location**: `chief_writer_quality.py:L32-77`, `chief_writer.py:L72-104`
- **Description**: `sanitize_leakage()`는 `Beat 3/4`, `continuation_text`, `future_hint`, `next_episode`, `spoiler` 키와 영문 괄호 병기만 제거한다. 그러나 LLM 출력에 다음 시스템 내부 마커가 포함될 수 있으며, 이들은 필터링되지 않는다:
  - 전략 지시문: `[전략 A: 균형]`, `[전략 B: 서사 강조]`, `[전략 C: 몰입감 극대화]`
  - JSON 필드: `"writing_strategy": "balanced"` (프롬프트 출력 형식에 포함)
  - 프롬프트 래퍼: `### [AUTHOR'S ABSOLUTE DIRECTIVES]`, `### [TASK]`, `### [FORMAT]`
  - `[Strategy-Specific Feedback]` 블록 마커 (L641)
  - `key_scenes_covered` 필드 (시스템 내부 추적용 데이터)
- **Evidence**:
  ```python
  # chief_writer_quality.py L47-55 -- banned_keys가 제한적
  banned_keys = [
      "Beat 3", "Beat 4", "continuation_text", "scene_summary",
      "future_hint", "next_episode", "spoiler",
  ]
  ```
  한편 `_check_system_term_exposure()` (L403-444)가 `Block N`, `Stage N`, `Blueprint`, `treatment`, `Arc` 등의 본문 내 노출은 감지하지만, 이것은 Self-Critique 검사일 뿐 필터가 아니다. 감지해도 _fix에서 LLM이 제거하지 못할 수 있다.
- **Impact**: 최종 원고에 `writing_strategy` 같은 JSON 메타 필드나 전략 지시문 텍스트가 잔존하여 독자에게 노출될 수 있다. 실제로는 `_extract_json_robust()` + content 필드 추출 과정에서 대부분 걸러지나, content 필드 자체에 해당 텍스트가 섞일 경우 통과.
- **Suggested fix direction**: `sanitize_leakage()`에 전략 지시문 정규식 제거, `writing_strategy`/`key_scenes_covered` 같은 메타 키의 값이 content에 혼입된 경우 제거하는 텍스트 레벨 필터 추가.

---

### TF-CW-04: ThreadPool 전체 타임아웃 시 미완료 future의 결과 누락 (silent drop) -- IMPORTANT

- **Location**: `chief_writer.py:L528-538`
- **Description**: `as_completed(timeout=ENSEMBLE_TIMEOUT)` 전체 타임아웃 발생 시, L528에서 `FutureTimeoutError`를 잡고 "완료된 후보만 사용"이라는 경고를 로깅한 뒤, L537의 `finally`에서 모든 future를 `cancel()`한다. 그러나 `cancel()`은 RUNNING 상태의 future에는 무효(L472-474 주석 참조)이므로, 타임아웃된 RUNNING future의 LLM 호출이 백그라운드에서 계속 실행된다. 결과는 소비되지 않으며 리소스(스레드 + API 쿼터)를 낭비한다.
- **Evidence**:
  ```python
  # L471-474 -- 코드 자체에 이미 알려진 제한이 주석으로 명시됨
  # [Sweep300-R41] 알려진 제한: as_completed(timeout=T)는 soft bound.
  # Python ThreadPoolExecutor는 실행 중인 스레드를 강제 중단할 수 없으므로,
  # LLM API 호출이 T초를 초과하면 실제 대기 시간 > T가 될 수 있다.
  ```
  그러나 이 "알려진 제한"에 대한 대응책이 없다. executor가 `with` 블록을 벗어나면 `shutdown(wait=True)`가 호출되어 RUNNING future가 완료될 때까지 블로킹한다.
- **Impact**: `ENSEMBLE_TIMEOUT`(600초) 후에도 RUNNING future가 있으면 `with` 블록 종료 시 추가 대기가 발생한다. 야간 무인 운영에서 예상보다 긴 정체를 유발할 수 있다. 다만 `SINGLE_CANDIDATE_TIMEOUT`(540초) < `ENSEMBLE_TIMEOUT`(600초) 이므로 개별 future가 먼저 타임아웃될 가능성이 높아 실질적 위험은 제한적.
- **Suggested fix direction**: `ThreadPoolExecutor` 사용 시 `executor.shutdown(wait=False, cancel_futures=True)` (Python 3.9+)를 명시적으로 호출하거나, `with` 블록 대신 수동 관리로 전환. 또는 LLM API 레벨 타임아웃을 `SINGLE_CANDIDATE_TIMEOUT`보다 짧게 설정.

---

### TF-CW-05: _generate_single_candidate의 None 반환이 생성 성공 후보에서 제외됨 -- INSIGHT

- **Location**: `chief_writer.py:L481-482, L693-694, L771-777`
- **Description**: `_generate_single_candidate()`는 세 가지 경우에 `None`을 반환한다: (a) JSON 파싱 실패(L693-694), (b) exception catch(L771-777). `generate_ensemble()`에서는 L481 `if result:`로 필터하므로 None은 candidates에 추가되지 않는다. 그러나 이 경우 해당 전략에 대한 error stub도 생성되지 않아, 아래의 `valid_candidates` 필터(L554)에서 "0 valid"로 판정되어 단일 폴백 경로로 진입한다.
- **Evidence**:
  ```python
  # L478-509 -- result가 None이면 append 안 됨, error stub도 안 됨
  try:
      result = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)
      if result:  # None이면 skip
          candidates.append(result)
  except FutureTimeoutError:
      candidates.append({...error stub...})
  except Exception as e:
      candidates.append({...error stub...})
  ```
  이것은 정상 동작이지만, 3개 전략 중 2개가 정상 응답을 반환했는데 그 중 하나가 JSON 파싱에 실패하여 None이 된 경우, 유효 후보가 1-2개만 되어 다양성이 저하된다. 로깅도 `_generate_single_candidate` 내부에서만 이뤄져 `generate_ensemble` 레벨에서는 "몇 개가 None이었는지" 알기 어렵다.
- **Impact**: 다양성 저하는 Director 선택의 질에 영향. 실질적 크래시나 데이터 손실은 없음.
- **Suggested fix direction**: None 반환 시에도 `generate_ensemble` 레벨에서 경고 로그 + operator_log 추가. 어떤 전략이 None을 반환했는지 명시.

---

### TF-CW-06: Self-Critique 루프는 hard cap 3회로 종결 -- 무한루프 불가 확인 -- INSIGHT (양성)

- **Location**: `chief_writer_quality.py:L123, L196`
- **Description**: `MAX_CRITIQUE_ROUNDS = 3` (L123)으로 하드캡이 설정되어 있으며, `for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1)` (L196)로 반복한다. 또한 다음 조기 종료 조건들이 있다:
  - `has_issues == False` (L210) → break
  - `severity == "low"` (L219) → break
  - Rubric >= 3.5 + MIN_LENGTH 충족 (L223-227, R2 이후) → break
  - 사전 Rubric >= 3.5 + MIN_LENGTH → 루프 진입 전 반환 (L139-159)
- **Evidence**: 루프 진입/종료 경로 모두 bounded. 무한루프 불가능.
- **Impact**: 없음. 정상 설계.
- **Suggested fix direction**: 없음. 현재 설계 양호.

---

### TF-CW-07: validate_manuscript_candidate() Pydantic 실패 시 raw dict 그대로 반환 -- IMPORTANT

- **Location**: `modules/models/manuscript.py:L43-50`, `chief_writer.py:L600`
- **Description**: `validate_manuscript_candidate()`는 Pydantic 검증 실패 시 원본 raw dict를 그대로 반환한다(L49-50). 이는 graceful degradation 의도이나, 예상치 못한 키나 타입(예: `manuscript`가 int인 경우)이 downstream으로 전파될 수 있다.
- **Evidence**:
  ```python
  def validate_manuscript_candidate(raw: dict) -> dict:
      try:
          mc = ManuscriptCandidate.model_validate(raw)
          return mc.model_dump()
      except Exception as e:
          logger.warning(...)
          return raw  # 검증 실패해도 원본 그대로 전달
  ```
- **Impact**: 타입 불일치 후보가 Director에게 전달되어 `.get("manuscript")` 등에서 예상치 못한 타입이 반환될 수 있다. 다만 ManuscriptCandidate의 `extra="allow"` + 기본값 설정으로 대부분의 경우 정상 통과하므로 실질적 위험은 낮음.
- **Suggested fix direction**: 실패 시 raw dict 대신 기본값이 채워진 dict를 반환하는 방어적 패턴 검토.

---

### TF-CW-08: 앙상블 전체 크래시 시 candidates가 빈 상태로 error_fallback까지 도달 -- CRITICAL

- **Location**: `chief_writer.py:L539-546, L554-597`
- **Description**: L539-546의 외부 `except` 블록에서 `ThreadPoolExecutor` 전체가 크래시하면 `candidates`는 L428에서 초기화된 빈 리스트 `[]` 그대로이다. 이후 L554에서 `valid_candidates`도 빈 리스트 → L556의 단일 폴백도 _outside_ TPE이므로 별도 실행되지만, 이 폴백 자체도 같은 근본 원인(예: 네트워크 단절)으로 실패할 가능성이 높다. L584의 error_fallback으로 귀결되면 `manuscript=""`인 후보가 반환된다.

  특히 L539의 `except Exception as e`는 `KeyboardInterrupt`, `SystemExit`은 잡지 않으므로 강제 종료 시에는 정상 전파되지만, `MemoryError` 같은 비표준 예외도 잡히지 않아 여기서는 문제가 아니다.
- **Evidence**:
  ```python
  # L438-546
  try:
      with ThreadPoolExecutor(...) as executor:
          ...
  except Exception as e:  # TPE 전체 크래시
      logging.error(...)    # 로그만 찍고 계속 진행
  # candidates는 여전히 []
  ```
  이후 L554-597의 로직이 빈 candidates를 처리하지만, 최종적으로 빈 원고를 가진 error_fallback이 반환된다. TF-CW-01과 합쳐지면 빈 원고가 Director까지 도달한다.
- **Impact**: 네트워크 단절이나 API 장애 시 빈 원고가 Director까지 전달되어 불필요한 LLM 호출 + 잠재적 빈 원고 저장.
- **Suggested fix direction**: error_fallback 반환 시 generate_ensemble()이 명시적 예외를 raise하여 stage4에서 "전면 실패" 처리 경로를 통해 해당 라운드를 건너뛰게 하는 것이 보다 안전. 또는 error_fallback dict에 특수 sentinel 키를 추가하여 stage4에서 감지.

---

### TF-CW-09: 전략 temperature 조정에서 NaN/Inf 방어 없음 -- INSIGHT

- **Location**: `chief_writer.py:L156-166`
- **Description**: `_build_strategy_execution_plan()`에서 share 값에 기반하여 temperature를 조정한다. `shares`가 DB에서 올 때 비정상 값(NaN, Inf)이 포함될 수 있으나, `float()` 변환 시 NaN/Inf가 그대로 전파된다. `round(base - 0.05, 2)` 같은 연산에서 NaN이면 NaN이 temperature로 설정된다.
- **Evidence**:
  ```python
  # L158-166
  base = float(self.ENSEMBLE_STRATEGIES[name]["temperature"])
  share = shares.get(name, 0.0)
  adjusted = base
  if share >= 0.5:
      adjusted = max(0.1, round(base - 0.05, 2))
  # share가 NaN이면 >= 0.5도 False, <= 0.15도 False → adjusted = base로 유지
  ```
  실제로 share가 NaN이면 모든 비교가 False가 되어 `adjusted = base`로 유지되므로 실질적 위험은 없다. 하지만 base 자체가 비정상이면(ENSEMBLE_STRATEGIES 딕셔너리를 외부에서 수정한 경우) 문제가 될 수 있다.
- **Impact**: 실질적 위험 매우 낮음. ENSEMBLE_STRATEGIES는 클래스 상수이므로 정상적 사용에서 base가 비정상일 수 없다.
- **Suggested fix direction**: 방어적 프로그래밍으로 `max(0.1, min(1.0, adjusted))` 클램핑을 모든 경로에 적용하면 안전.

---

### TF-CW-10: _generate_single_candidate에서 strategy_temperature가 0이면 0.0 temperature 사용 -- INSIGHT

- **Location**: `chief_writer.py:L635-639`
- **Description**: `strategy_temperature`가 `0` (int) 또는 `0.0` (float)이면 `isinstance(strategy_temperature, (int, float))`가 True이므로 `float(0)` = `0.0`이 temperature로 사용된다. Temperature 0은 Gemini API에서 결정론적(greedy) 디코딩을 의미하며, 3전략 앙상블의 다양성 목적과 상충한다.
- **Evidence**:
  ```python
  _temperature = (
      float(strategy_temperature)
      if isinstance(strategy_temperature, (int, float))
      else float(strategy_config["temperature"])
  )
  ```
  `_build_strategy_execution_plan()`의 adjusted_temperatures에서 `max(0.1, ...)` 하한이 있어 0.0은 반환되지 않는다(L161). 그러나 외부에서 직접 `strategy_temperature=0`을 전달하면 통과.
- **Impact**: 현재 호출 경로에서는 `_strategy_temperatures.get(strategy)` → None(키 없음) 또는 0.1 이상이므로 실질적 위험 없음.
- **Suggested fix direction**: `_temperature = max(0.1, _temperature)` 하한 추가.

---

### TF-CW-11: Rubric 평가의 조기 종료 경쟁 조건 -- IMPORTANT

- **Location**: `chief_writer_quality.py:L137-164`
- **Description**: `apply_self_critique()`에서 초기 Rubric 점수가 >= 3.5이고 MIN_LENGTH를 충족하면, `_self_critique()`를 한 번 호출하여 high/medium 이슈가 없을 때 즉시 반환한다(L158-159). 그러나 이 경로에서는 **게이트 검사(L167-194)를 건너뛴다**. 게이트 검사에는 `ending_hook` 존재 확인과 `system_term_exposure` 검사가 포함되어 있다.
- **Evidence**:
  ```python
  # L137-159
  rubric_score = self._evaluate_with_rubric(current_manuscript, genre_name)
  if rubric_score >= 3.5 and current_content_length >= int(ManuscriptLimits.MIN_LENGTH):
      _structural = self._self_critique(...)
      _medium_plus = [i for i in _structural["issues"] if i.get("severity") in ("medium", "high")]
      if not _medium_plus:
          return current_manuscript  # 게이트 검사(L167-194) 건너뜀!
  # L167-194: 게이트 검사 (ending_hook + system_term_exposure)
  ```
  `_self_critique()` 내부에서도 `_check_ending_hook_presence()`와 `_check_system_term_exposure()`를 호출하지만(L304, L310), 이 결과는 `_structural["issues"]`에 포함된다. `ending_hook`은 severity="medium"이므로 `_medium_plus`에 잡히지만, 이슈가 0건이면 게이트 검사 없이 통과한다.

  실제로는 `_self_critique` 내부의 체크(L304, L310)와 게이트 검사(L169, L176)가 동일한 함수를 호출하므로 중복 검사다. 게이트 검사를 건너뛰어도 `_self_critique` 내부에서 이미 검출되므로 실질적 갭은 없다. **단, 분량 게이트(L172-173)는 `_self_critique` 내부의 분량 체크(L331-344)와 기준이 다르다**: 게이트는 `len(current_manuscript) < 5000` (JSON 전체 길이)이고, Self-Critique는 `len(content) < TARGET_LENGTH` (content 필드 길이)이다.
- **Impact**: JSON wrapper 포함 전체 길이가 5,000자 이상이지만 content 필드가 TARGET_LENGTH 미만인 edge case에서 게이트 검사 우회 가능. 실질적 위험은 Self-Critique 내부 검사로 커버되므로 낮음.
- **Suggested fix direction**: 조기 종료 경로에서도 게이트 검사를 먼저 실행하도록 순서 재배치. 또는 분량 기준을 content 길이로 통일.

---

### TF-CW-12: _annotate_candidate_diversity가 error 후보도 포함하여 다양성 계산 -- INSIGHT

- **Location**: `chief_writer.py:L210-265, L601`
- **Description**: L601에서 `_annotate_candidate_diversity(candidates)`를 호출할 때, candidates에 error stub(`manuscript=""`)이 포함되어 있을 수 있다. L216에서 `manuscript.strip()`이 빈 문자열이면 `indexed_texts`에 추가되지 않으므로 다양성 계산에서는 제외된다. 그러나 L259-264에서 모든 candidate의 `metadata`에 diversity 정보를 주입하므로, error stub의 metadata도 갱신된다.
- **Evidence**:
  ```python
  # L216-218
  manuscript = str(candidate.get("manuscript", "") or "").strip()
  if manuscript:
      indexed_texts.append((idx, manuscript))
  # 빈 원고 → indexed_texts에 미포함 → 다양성 계산에서 제외
  ```
- **Impact**: 없음. 빈 원고는 다양성 계산에서 올바르게 제외됨. metadata 갱신도 무해.
- **Suggested fix direction**: 없음. 현재 설계 양호.

---

### TF-CW-13: patch_with_feedback에서 single_strategy=_rejected_strategy 설정으로 단일 후보만 생성 -- INSIGHT

- **Location**: `chief_writer.py:L1676`
- **Description**: `patch_with_feedback()`는 `single_strategy=_rejected_strategy`를 설정하여 `generate_ensemble()`을 호출한다(L1676). 이는 이전에 REJECT된 전략 하나만으로 재생성하라는 의도이나, `_rejected_strategy`가 빈 문자열이면 `_select_ensemble_strategies()`에서 `single_strategy=""`가 되어 full 3전략 앙상블이 실행된다.
- **Evidence**:
  ```python
  # L1656
  _rejected_strategy = str(previous_attempt.get("selected_strategy_key", "") or "")
  # L1676
  single_strategy=_rejected_strategy,
  # _select_ensemble_strategies L184-186
  if single_strategy:  # "" is falsy → full 앙상블로 진행
      target = [name for name in strategies if name == single_strategy]
      return (target or ["balanced"]), {}
  ```
- **Impact**: `selected_strategy_key`가 누락된 previous_attempt에서 의도치 않게 3전략 앙상블이 실행되어 비용 3배 + 시간 증가. 하지만 결과물의 질은 오히려 나아질 수 있으므로 순수한 비용 이슈.
- **Suggested fix direction**: `_rejected_strategy`가 빈 문자열일 때 명시적으로 `"balanced"`를 기본값으로 사용하거나, 의도된 동작이면 주석으로 명시.

---

### TF-CW-14: State Mutation 분석 -- 공유 상태 변경 없음 확인 -- IMPORTANT (양성)

- **Location**: `chief_writer.py` 전체
- **Description**: ChiefWriter의 3전략 병렬 실행에서 공유 상태 mutation을 분석한 결과:
  - `_generate_single_candidate()`는 `self`의 어떤 필드도 쓰지 않는다. 읽기 전용으로 `ENSEMBLE_STRATEGIES`, `PROMPT_TEMPLATE_OUTPUT`, `quality_gate`, `context_builder`에 접근.
  - `quality_gate.apply_self_critique()`와 `_fix_manuscript_issues()`도 `self.host`의 읽기 전용 메서드만 호출.
  - `self.host.ask()` (LLM 호출)는 내부적으로 thread-safe한 API client를 사용.
  - `self._manuscript_cache`는 `_prefetch_manuscripts()`에서 TPE 시작 전에 한 번만 채워지고, 이후 읽기 전용.

  **단, `self._context_builder`와 `self._quality_gate`는 lazy init이다** (L279-287). 3개 worker thread가 동시에 첫 접근하면 경쟁 조건으로 인스턴스가 여러 번 생성될 수 있다. 그러나 `generate_ensemble()`의 L370에서 `self.context_builder`를 먼저 호출하므로 TPE 시작 전에 초기화가 완료된다.
- **Evidence**:
  ```python
  # L370 -- TPE(L440) 전에 호출되므로 lazy init 경쟁 없음
  common_context = self.context_builder.build_common_context(...)
  ```
- **Impact**: 현재 코드 흐름에서 스레드 안전성 문제 없음.
- **Suggested fix direction**: 없음. 현재 설계에서 TPE 시작 전 lazy init이 완료되므로 안전.

## 4. Summary Matrix

| ID | Severity | Category | Location | 1-line description |
|----|----------|----------|----------|--------------------|
| TF-CW-01 | CRITICAL | Fallback | L584-602 | error_fallback 후보(manuscript="", error=True)가 Director까지 전파 |
| TF-CW-02 | IMPORTANT | Self-Critique | quality:L1138-1158 | _fix_manuscript_issues에서 MIN_LENGTH 미달 수정본을 원본 대신 반환 |
| TF-CW-03 | IMPORTANT | Leakage | quality:L32-77 | sanitize_leakage가 전략 지시문/시스템 마커를 필터링하지 않음 |
| TF-CW-04 | IMPORTANT | ThreadPool | L528-538 | 전체 타임아웃 시 RUNNING future가 백그라운드 지속 + shutdown(wait=True) 블로킹 |
| TF-CW-05 | INSIGHT | Observability | L481-482 | None 반환 전략에 대한 generate_ensemble 레벨 로깅 부재 |
| TF-CW-06 | INSIGHT | Self-Critique | quality:L123,L196 | Self-Critique 루프 hard cap 3회 — 무한루프 불가 (양성 확인) |
| TF-CW-07 | IMPORTANT | Validation | manuscript.py:L43-50 | Pydantic 실패 시 raw dict 그대로 반환 (타입 불일치 전파 가능) |
| TF-CW-08 | CRITICAL | Crash Path | L539-546 | TPE 전체 크래시 → 빈 candidates → error_fallback → 빈 원고 Director 전달 |
| TF-CW-09 | INSIGHT | Temperature | L156-166 | temperature 조정에서 NaN 방어 없으나 실질적 위험 없음 |
| TF-CW-10 | INSIGHT | Temperature | L635-639 | strategy_temperature=0이면 greedy 디코딩, 현재 경로에서 미발생 |
| TF-CW-11 | IMPORTANT | Self-Critique | quality:L137-164 | Rubric 조기 종료 시 게이트 검사 건너뜀 (실질적 갭은 제한적) |
| TF-CW-12 | INSIGHT | Diversity | L210-265 | error 후보도 diversity에 포함되나 빈 원고는 올바르게 제외됨 (양성) |
| TF-CW-13 | INSIGHT | Cost | L1676 | patch_with_feedback에서 빈 rejected_strategy → 의도치 않은 3전략 실행 |
| TF-CW-14 | IMPORTANT | Thread Safety | 전체 | 공유 상태 mutation 없음 + lazy init 경쟁 없음 확인 (양성) |

## 5. 핵심 코드 참조 (Appendix)

### chief_writer.py 주요 함수 시그니처 및 위치

| Function | Line | Purpose |
|----------|------|---------|
| `ChiefWriter.__init__()` | L110 | 초기화 (캐시, lazy init 필드) |
| `_load_strategy_bias()` | L120 | DB에서 전략별 최근 PASS 비중 조회 |
| `_build_strategy_execution_plan()` | L148 | 전략 실행 순서 + temperature 보정 계산 |
| `_select_ensemble_strategies()` | L174 | 전략 세트 해결 (full/reduced/single) |
| `_build_char_ngrams()` | L201 | 3-gram 생성 (다양성 분석용) |
| `_annotate_candidate_diversity()` | L210 | 후보 간 Jaccard 유사도 계산 |
| `generate_ensemble()` | L289 | **핵심**: 3전략 병렬 생성 + 폴백 + 검증 |
| `_generate_single_candidate()` | L604 | 단일 후보: LLM 호출 + Self-Critique + Leakage |
| `regenerate_with_feedback()` | L799 | Director 피드백 반영 재생성 |
| `inplace_patch()` | L1330 | LLM 1회 호출 in-place 수정 |
| `_attempt_structural_inplace_patch()` | L1190 | scene-aware 구조적 패치 시도 |
| `patch_with_feedback()` | L1551 | 원본 보존 + 피드백 지적사항만 수정 |
| `_build_retry_history_feedback()` | L1704 | 누적 REJECT 히스토리 요약 |
| `_prefetch_manuscripts()` | L1796 | DB 배치 캐시 (최근 N화) |
| `invalidate_manuscript_cache()` | L1824 | 캐시 무효화 |

### chief_writer_quality.py 주요 함수 시그니처 및 위치

| Function | Line | Purpose |
|----------|------|---------|
| `sanitize_leakage()` | L32 | 출력 누수 방지 필터 |
| `apply_self_critique()` | L94 | Self-Critique 다중 라운드 (max 3) |
| `_self_critique()` | L241 | 17개 검사 항목 실행 |
| `_fix_manuscript_issues()` | L1091 | LLM 기반 이슈 수정 |
| `_evaluate_with_rubric()` | L1163 | 4차원 Rubric 품질 점수 (1.0~4.0) |
| `_check_system_term_exposure()` | L403 | 시스템 용어 노출 감지 |
| `_check_arithmetic_consistency()` | L446 | 산술 모순 감지 |
| `_check_ending_hook_presence()` | L882 | ending_hook 키워드 매칭 |
| `_check_pov_consistency_critique()` | L374 | POV 일관성 자가 점검 |
| `_check_motivation_consistency()` | L715 | 동기/약속 방치 감지 |
| `_count_recent_cliches()` | L1257 | 최근 N화 클리셰 빈도 |

### 상수 참조

| Constant | Value | Location |
|----------|-------|----------|
| `ENSEMBLE_TIMEOUT` | 600s (default) | L63 |
| `SINGLE_CANDIDATE_TIMEOUT` | 540s (default) | L64 |
| `MAX_CRITIQUE_ROUNDS` | 3 | quality:L123 |
| `ManuscriptLimits.MIN_LENGTH` | 4000 | constants.py |
| `ManuscriptLimits.TARGET_LENGTH` | 5000 | constants.py |
| Rubric early-exit threshold | 3.5 | quality:L139 |
| `CLICHE_WINDOW` | 10 | quality:L18 |
