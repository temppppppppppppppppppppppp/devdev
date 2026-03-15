# TF-CA: ContinuityArc 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | ContinuityArc: cross-arc contradictions, temporal/spatial validation, NPC state, single-arc checks |
| Source files | continuity_arc.py:1013줄 |
| TF Items | 14 (CRITICAL 3 / IMPORTANT 7 / INSIGHT 4) |

---

## 1. Executive Summary

ContinuityArcValidator는 Stage 2에서 Arc 설계 후 Arc 간 + 단일 Arc 내 모순을 검증하는 모듈이다. Python 사전 검사(advisory only) + LLM 정밀 검증의 2-Phase 아키텍처를 사용한다.

**핵심 발견 사항:**

1. **NPC 사망 상태가 Arc 수준 검증에서 완전 누락** (CRITICAL): `continuity_arc.py`는 NPC 사망/생존 상태를 전혀 검사하지 않는다. `state_tracker_npc.py`에 `check_dead_npc_appearance()` 메서드가 존재하지만, `continuity_arc.py`에서 호출하지 않으며 LLM 프롬프트에도 NPC 사망 관련 검증 항목이 없다.

2. **LLM 실패 시 무조건 PASS** (CRITICAL): LLM 호출이 실패하거나 JSON 파싱이 실패하면 검증 결과를 PASS로 반환하여, 모순이 있는 Arc가 통과할 수 있다.

3. **Python 사전 검사에 REJECT 권한 없음** (CRITICAL by design, but risk): V60.56에서 의도적으로 Python의 REJECT 권한을 제거했으나, LLM 실패 시 Python이 감지한 critical violation도 단순 warning으로 전환되어 소실된다.

4. **공간/시간 검증이 LLM에 100% 위임** (IMPORTANT): 장소 이동 타당성, 시간 일관성 검증에 Python 레벨 사전 검사가 전혀 없다. LLM 프롬프트에는 "장소 이동이 물리적으로 가능한가?" 항목이 있지만 강제력이 약하다.

5. **Arc 요약 절삭으로 정보 손실 가능** (IMPORTANT): `tactical_doc[:50000]`, `last_ep_content[:4000]`, `_tac_summary[:4500]` 등 여러 곳에서 하드코딩된 절삭이 발생한다.

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
Stage 2: Arc 설계 완료
          |
          v
+---------------------------------------------------+
| ContinuityInspector.inspect_arc() [facade]         |
|   -> ContinuityArcValidator.inspect_arc()          |
+---------------------------------------------------+
          |
          |  arc_no <= 1 or no prev_arcs?
          |----YES----> _inspect_intra_arc_only()
          |                  |
          |                  v
          |             _check_intra_arc_consistency()
          |                  |
          |                  v
          |             Return (PASS or REJECT)
          |
          |----NO-----> Continue full validation
          |
          v
+---------------------------------------------------+
| Phase 1: Python Precheck (Advisory Only)           |
| _arc_python_precheck()                             |
|   +-- 중복 획득 검사 (regex + _is_same_item)       |
|   +-- 단일 Arc 내 모순 (_check_intra_arc_consistency)|
|   +-- 상태 연속성 검사 (부상 키워드 매칭)          |
|   |                                                |
|   | [!] REJECT 권한 없음 (V60.56)                  |
|   | [!] NPC 사망 검사 없음                          |
|   | [!] 공간/시간 검사 없음                          |
+---------------------------------------------------+
          |
          v
+---------------------------------------------------+
| Phase 1.5: Joint Docs Auto-Correction             |
| _extract_accurate_joint_docs()                     |
|   +-- LLM call: 마지막 화에서 종료 상태 추출       |
|   +-- confidence LOW이면 원본과 merge              |
|   +-- 실패 시 원본 유지 (non-blocking)             |
+---------------------------------------------------+
          |
          v
+---------------------------------------------------+
| Phase 1.6: Arc Start State Auto-Correction         |
|   +-- prev_arc.arc_end_state vs current_arc 비교   |
|   +-- needs_correction이면 current_arc 직접 mutate |
|   +-- internal_energy, injuries, location, equip   |
+---------------------------------------------------+
          |
          v
+---------------------------------------------------+
| Phase 2: LLM Precision Validation                  |
| ARC_CONTINUITY_INSPECTION_PROMPT                   |
|   +-- 7 Steps: Item/Grant/State/Intra/Setting/     |
|   |            Entity/Final Judgment                |
|   +-- temperature=0.1                              |
|   +-- JSON output parsing                          |
|   |                                                |
|   | [!] LLM 실패 -> PASS 반환                      |
|   | [!] JSON 파싱 실패 -> PASS + confidence=0.0    |
+---------------------------------------------------+
          |
          v
+---------------------------------------------------+
| Post-processing                                    |
|   +-- Python advisory를 warnings로 병합            |
|   +-- Joint Docs 수정 정보 포함                    |
|   +-- intra_arc 위반 완화 (V60.13)                 |
|   +-- cross-arc CRITICAL/MAJOR만 REJECT 유지       |
+---------------------------------------------------+
          |
          v
      Return result
```

---

## 3. TF Items

### TF-CA-01: NPC 사망 상태가 Arc 수준 검증에서 완전 누락 -- CRITICAL

- **Location**: `continuity_arc.py` 전체 (1013줄 중 관련 코드 0줄)
- **Description**: `continuity_arc.py`는 NPC의 사망/생존 상태를 전혀 검사하지 않는다. `state_tracker_npc.py`에는 `check_dead_npc_appearance()` (L460), `check_dead_npc_in_blueprint()` (L1420), `check_dead_npc_in_manuscript()` (L1519)가 구현되어 있지만, Arc 수준에서는 호출되지 않는다.
- **Evidence**: `continuity_arc.py`에서 "dead", "사망", "죽" 등의 키워드 검색 결과 0건. `_arc_python_precheck()`의 검증 항목은 (1) 중복 획득, (2) 단일 Arc 내 모순, (3) 상태 연속성(부상만)의 3가지뿐이다.
- **Impact**: Arc 설계 시 이전 Arc에서 죽은 NPC를 살아있는 것처럼 등장시키는 오류가 통과할 수 있다. LLM 프롬프트(L21-158)에도 NPC 사망 검증 항목이 없어 LLM도 이를 별도로 체크하지 않을 가능성이 높다.
- **Suggested fix direction**: `_arc_python_precheck()`에 `check_dead_npc_appearance()` 호출 추가. LLM 프롬프트에 "#### 6.5 NPC 생존/사망 연속성" 항목 추가. `state_tracker_npc.py`의 `get_dead_npc_summary()`를 프롬프트에 주입.

---

### TF-CA-02: LLM 실패 시 무조건 PASS 반환 -- CRITICAL

- **Location**: `continuity_arc.py:L456-L474`
- **Description**: `inspect_arc()`의 메인 LLM 호출이 `except Exception`으로 잡히며, 모든 경우에 `"decision": "PASS"`를 반환한다. Python precheck에서 critical_violations를 발견했더라도, LLM이 실패하면 그 violations는 warnings 배열에만 들어가고 decision은 여전히 PASS이다.
- **Evidence**:
```python
# L456-474
except Exception as e:
    logging.warning(f" [ContinuityInspector] Arc LLM 검증 실패: {e}")
    if python_check.get("warnings"):
        return {
            "decision": "PASS",
            "severity": "MINOR",
            ...
            "violations": [],   # <-- critical_violations가 여기에 없음
            ...
        }
    return {
        "decision": "PASS",
        "severity": "NONE",
        "violations": [],
        ...
    }
```
- **Impact**: 네트워크 오류, API quota 초과, 타임아웃 등으로 LLM 호출이 실패하면 어떤 모순이 있든 Arc가 통과한다. 상위 호출측(`stage2_validation_pipeline.py` L749-765)에서도 ContinuityInspector 예외 시 advisory 전환을 하므로 이중 fail-open이 발생한다.
- **Suggested fix direction**: LLM 실패 시 `python_check`에 critical_violations가 있으면 최소 `"decision": "REJECT"` 또는 `"RETRY"` 반환 검토. 또는 `severity` 필드를 `"UNKNOWN"`으로 설정하여 호출측이 재시도를 결정할 수 있도록 하기.

---

### TF-CA-03: JSON 파싱 실패 시 PASS + confidence=0.0 반환 -- CRITICAL

- **Location**: `continuity_arc.py:L384-L393`
- **Description**: LLM이 응답했지만 JSON 파싱이 실패하면, 수동 검수 경고를 포함한 PASS 결과를 반환한다. `confidence: 0.0`과 `parsing_error: True`가 포함되지만 decision은 PASS이다.
- **Evidence**:
```python
# L384-393
if not isinstance(result, dict):
    logging.warning(" [V60.74] JSON 파싱 실패 - 수동 검수 권장")
    result = {
        "decision": "PASS",
        "severity": "NONE",
        "violations": [],
        "warnings": ["[V60.74] LLM 응답 파싱 실패 - 수동 검수 필요"],
        "confidence": 0.0,
        "parsing_error": True,
    }
```
- **Impact**: LLM이 REJECT를 의도했지만 출력 형식 오류로 파싱 실패한 경우, 모순 있는 Arc가 통과한다. "수동 검수 권장"이라는 warning은 자동 파이프라인에서 사실상 무시된다.
- **Suggested fix direction**: 파싱 실패 시 LLM 재호출(temperature 조정 또는 다른 모델) 또는 `decision: "RETRY"` 반환. 호출측이 재시도 로직을 구현하도록 인터페이스 확장.

---

### TF-CA-04: 공간/시간 검증이 Python 사전 검사에 완전 부재 -- IMPORTANT

- **Location**: `continuity_arc.py:L571-L769` (`_arc_python_precheck` 메서드 전체)
- **Description**: Python 사전 검사는 아이템 중복 획득, 단일 Arc 내 모순, 부상 상태 연속성만 검사한다. 장소 이동 타당성(텔레포트 감지), 시간 경과 일관성에 대한 검사가 전혀 없다.
- **Evidence**: `_arc_python_precheck`에서 location/위치/거리/이동/시간 관련 키워드 검색 결과 0건. 유일한 위치 정보 사용은 Phase 1.6의 `correct_location` 대입(L330, L349)뿐이며, 이는 단순히 이전 Arc 종료 위치를 현재 Arc 시작 위치로 복사하는 것이다.
- **Impact**: 이전 Arc 종료 시 "무림맹 본부(하남)"에 있었는데 현재 Arc 시작 시 아무 설명 없이 "북해빙궁"에 있는 등의 텔레포트 오류가 Python 레벨에서 감지되지 않는다. LLM 프롬프트(L65, L99)에 관련 항목이 있지만 LLM 판단에만 의존한다.
- **Suggested fix direction**: `_arc_python_precheck`에 위치 연속성 검사 추가: `prev_arc.joint_docs.final_location`과 `current_arc.state_constraints.arc_start_state.location` 비교 → 불일치 시 advisory 경고 생성.

---

### TF-CA-05: intra-arc 위반 자동 완화 메커니즘의 과도한 관용 -- IMPORTANT

- **Location**: `continuity_arc.py:L428-L452`
- **Description**: LLM이 REJECT를 판정했더라도 cross-arc CRITICAL/MAJOR 위반이 없고, 모든 위반이 `intra_arc_contradiction` 또는 `setting_inconsistency`이며, `start_state_corrected`가 True이면 REJECT를 PASS로 완화한다. 이 완화는 Arc Start State 자동 수정과 결합되어 있어, start state 수정이 일어나면 intra-arc 모순이 자동으로 무시된다.
- **Evidence**:
```python
# L438-452
if result.get("decision") == "REJECT" and not has_critical_cross_arc:
    intra_only = violations and all(
        isinstance(v, dict) and v.get("type") in ["intra_arc_contradiction", "setting_inconsistency"]
        for v in violations
    )
    if intra_only and start_state_corrected:
        result["decision"] = "PASS"
        result["severity"] = "MINOR"
        ...
        result["violations"] = []
```
- **Impact**: `start_state_corrected`는 이전 Arc와 현재 Arc의 상태가 한 필드라도 다르면 True가 된다(L338-343). 이는 거의 항상 True이므로, 사실상 모든 intra-arc 위반이 자동 완화된다. 예를 들어 Arc 내에서 같은 무기를 두 번 획득하는 CRITICAL intra_arc_contradiction도 PASS로 변환된다.
- **Suggested fix direction**: `start_state_corrected`와 intra-arc 위반 완화를 분리. intra-arc 위반 중 CRITICAL 등급은 완화하지 않도록 조건 추가. 또는 `needs_correction` 로직을 더 엄격하게 하여 실질적 변경이 있을 때만 True로 설정.

---

### TF-CA-06: `_is_same_item()` 초보수적 정확 매칭의 FN 위험 -- IMPORTANT

- **Location**: `continuity_inspector.py:L248-L264` (continuity_arc.py에서 L702, L715에서 호출)
- **Description**: `_is_same_item()`은 공백 제거 + 소문자 변환 후 완전 일치만 True를 반환한다. 한국어에서 흔한 부분 명칭 변형(예: "백근 대도" vs "백근도", "철혈사자패" vs "사자패", "만독비급" vs "독비급")은 모두 다른 아이템으로 판정된다.
- **Evidence**:
```python
# continuity_inspector.py L248-264
def _is_same_item(self, item1: str, item2: str) -> bool:
    item1_normalized = "".join(item1_clean.lower().split())
    item2_normalized = "".join(item2_clean.lower().split())
    if item1_normalized == item2_normalized:
        return True
    return False  # 어떤 유사도 검사도 없음
```
- **Impact**: 중복 획득 검사에서 아이템 명칭이 약간이라도 다르면 중복을 감지하지 못한다 (False Negative). V60.55에서 의도적으로 초보수적 접근을 택했으나(FP 방지), 그 대가로 FN이 발생한다. LLM 검증이 이를 보완해야 하지만 LLM에도 한계가 있다.
- **Suggested fix direction**: 부분 문자열 포함 관계(one contains the other) 검사를 선택적으로 추가하되, 최소 4글자 이상에만 적용. 또는 LLM advisory로 "유사 아이템" 후보를 제시하여 LLM이 최종 판단.

---

### TF-CA-07: Arc 요약 내 tactical_doc 절삭으로 정보 손실 -- IMPORTANT

- **Location**: `continuity_arc.py:L371, L537, L946`
- **Description**: 세 곳에서 하드코딩된 문자열 절삭이 발생한다:
  - L371: `tactical_doc[:50000]` — LLM 프롬프트에 주입되는 현재 Arc 전술서
  - L537: `last_ep_content[:4000]` — Joint Docs 추출용 마지막 화 내용
  - L946: `_tac_summary[:4500]` — 이전 Arc 요약
- **Evidence**:
```python
# L371
tactical_doc=self._ci._escape_braces(tactical_doc[:50000]),
# L537
last_ep_content=self._ci._escape_braces(last_ep_content[:4000])
# L946
{_tac_summary[:4500]}
```
- **Impact**: 5화 이상의 긴 Arc에서 tactical_doc이 50,000자를 초과하면 마지막 화의 정보가 잘릴 수 있다. `_tac_summary[:4500]`는 이전 Arc 요약이 4,500자 이후 잘리므로, 후반부 핵심 사건이 LLM에 전달되지 않을 수 있다. 이는 LLM이 cross-arc 모순을 놓치는 원인이 된다.
- **Suggested fix direction**: 절삭 전에 핵심 키워드(획득/수여/사망/부상 등) 포함 문장을 우선 보존하는 smart truncation 적용. 또는 절삭 발생 시 warning 로그 추가.

---

### TF-CA-08: `_check_intra_arc_consistency`의 미사용 변수 및 제한적 검증 범위 -- IMPORTANT

- **Location**: `continuity_arc.py:L771-L873`
- **Description**:
  1. L775: `arc.get("ep_start", 1)` 호출 결과를 변수에 할당하지 않음 (dead code)
  2. 부상→전투 검사(L823-837)는 "회복/치료/휴식"만 체크하여 "약 복용", "영약", "주화입마 해소" 등 무협 장르 특유의 회복 방식을 놓침
  3. 복장 일관성 검사(L839-871)는 "비단/명주/화려한" vs "허름한/낡은/무명/삼베"의 이진 분류만 하여, "갑옷→일반 옷" 등 다른 복장 변화를 놓침
- **Evidence**:
```python
# L775 - dead code
arc.get("ep_start", 1)  # 반환값 미사용

# L826 - 제한적 회복 패턴
if re.search(action_pattern, next_content) and not re.search(r"(?:회복|치료|휴식)", next_content):
    # "영약 복용", "약을 먹", "운기조식" 등 누락
```
- **Impact**: Dead code는 사소하지만 유지보수 혼란 유발. 회복 패턴 누락으로 정상적인 회복 후 전투도 위반으로 잡힐 수 있다 (False Positive). 반대로 복장 검사의 좁은 범위로 많은 불일치가 놓칠 수 있다 (False Negative).
- **Suggested fix direction**: L775 dead code 제거. 회복 패턴에 "영약|약을 먹|운기조식|조식|요양" 추가. 복장 패턴 확장.

---

### TF-CA-09: `_format_prev_arcs`에서 `ep_start`/`ep_end` 타입 안전성 부재 -- IMPORTANT

- **Location**: `continuity_arc.py:L889, L906-916`
- **Description**: `ep_start`와 `ep_end`는 `arc.get("ep_start", "?")`로 추출되어 문자열 `"?"`이 될 수 있다. 이후 L908에서 `isinstance(ep_start, int)` 체크가 있지만, L918에서 `ep_start != ep_end` 비교 시 둘 다 `"?"`이면 False로 평가되어 첫 화 요약만 사용된다.
- **Evidence**:
```python
# L889
ep_start = arc.get("ep_start", "?")
ep_end = arc.get("ep_end", "?")
# ...
# L918
if _first_ep_tac and _last_ep_tac and ep_start != ep_end:
    _tac_summary = f"[{ep_start}화] {_first_ep_tac}\n[{ep_end}화] {_last_ep_tac}"
```
- **Impact**: `ep_start`/`ep_end`가 `"?"`일 때 `extract_episode_tactical`에 `ep_num=1`이 전달되어(L908 fallback) 첫 화의 내용이 추출된다. 실제 마지막 화 내용이 누락되면 LLM에 불완전한 이전 Arc 요약이 전달된다.
- **Suggested fix direction**: `ep_start`/`ep_end`에 대한 int 변환 시도 및 실패 시 explicit fallback 적용. 또는 Arc 데이터 유효성 검증을 inspect_arc 진입점에서 수행.

---

### TF-CA-10: acquire_patterns 정규식의 한국어 조사 의존 FP/FN -- IMPORTANT

- **Location**: `continuity_inspector.py:L82-88` (continuity_arc.py L794, L625에서 사용)
- **Description**: 아이템 획득 패턴이 한국어 조사 "을/를"에 의존한다. 한국어에서 조사 생략, "~은/는" 사용, "~이/가" 사용 등 다양한 변형이 존재하지만 패턴이 이를 커버하지 못한다.
- **Evidence**:
```python
# continuity_inspector.py L83
r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:획득|챙기|얻|주워\s*들|가져)",
```
  - FN 사례: "백근도가 손에 들어왔다" → "을/를" 없으므로 미감지
  - FN 사례: "백근도 획득" → 조사 없이 바로 동사, 미감지
  - FP 사례: "적의 칼을 빼앗아 챙기다" → "칼"이 2글자이므로 캡처됨 (단순 전투 행위인데 획득으로 오인)
- **Impact**: 아이템 목록의 불완전성은 중복 획득 검사의 정확도를 직접 좌우한다. FN은 중복 검사 누락, FP는 불필요한 advisory 생성으로 이어진다.
- **Suggested fix direction**: 조사 없는 직접 연결 패턴 추가 (`([가-힣]{2,25})\s+획득`). 2글자 캡처에 대한 컨텍스트 검증 강화 (무기/패/서적 류 접미사 확인).

---

### TF-CA-11: `prev_inventory` 과 `prev_status` 루프 덮어쓰기 -- INSIGHT

- **Location**: `continuity_arc.py:L634-L635`
- **Description**: `prev_inventory`와 `prev_status`는 이전 Arc 루프(L585-L635)에서 매 iteration마다 덮어쓰여져 항상 마지막 Arc의 값만 남는다. 변수명이 "prev"이므로 모든 이전 Arc의 데이터를 유지할 것 같지만, 실제로는 직전 Arc의 joint_docs와 status_shadow만 보존된다.
- **Evidence**:
```python
# L634-635 (루프 내부)
prev_inventory = arc_joint       # 매 iteration 덮어쓰기
prev_status = arc_status         # 매 iteration 덮어쓰기
```
- **Impact**: 의도된 동작(직전 Arc만 필요)이라면 논리적으로 맞지만, 변수명과 루프 위치가 혼란을 유발한다. 코드 유지보수 시 오해의 소지가 있다.
- **Suggested fix direction**: 루프 밖에서 `prev_arcs[-1]`로 직접 접근하거나, 변수명을 `last_arc_inventory`, `last_arc_status`로 변경.

---

### TF-CA-12: Phase 1.6 State Auto-Correction이 current_arc를 직접 mutate -- INSIGHT

- **Location**: `continuity_arc.py:L352-L353`
- **Description**: `current_arc["state_constraints"] = curr_state`로 전달받은 딕셔너리를 직접 수정한다. 호출측에서 원본 Arc 데이터를 공유하고 있다면 side effect가 발생한다.
- **Evidence**:
```python
# L352-353
curr_state["arc_start_state"] = corrected_start
current_arc["state_constraints"] = curr_state
start_state_corrected = True
```
- **Impact**: `stage2_validation_pipeline.py`에서 `refined_arc` 딕셔너리가 전달되므로 원본이 수정된다. 이것이 의도된 동작(교정된 값을 반영)이지만, 검증 모듈이 입력을 수정하는 것은 단일 책임 원칙 위반이다. 검증 실패 후 재시도 시 이미 수정된 데이터로 검증하게 되어 다른 결과가 나올 수 있다.
- **Suggested fix direction**: `current_arc`를 deep copy한 후 수정하고, 교정된 값은 반환 결과에만 포함. 또는 mutation이 의도적임을 명시하는 docstring 추가.

---

### TF-CA-13: 부상 상태 연속성 검사의 과도한 단순성 -- INSIGHT

- **Location**: `continuity_arc.py:L746-L752`
- **Description**: 이전 Arc의 `status_shadow.expected_injuries`가 "없음", "경미", ""이 아닌 경우에만 검사하며, 현재 Arc의 tactical_doc에 "부상/회복/치료" 키워드가 하나라도 있으면 통과시킨다. 부상의 심각도, 회복 기간의 합리성 등은 검사하지 않는다.
- **Evidence**:
```python
# L748-752
if prev_injuries and prev_injuries not in ["없음", "경미", ""]:
    if "부상" not in tactical_doc and "회복" not in tactical_doc and "치료" not in tactical_doc:
        warnings.append(...)
```
- **Impact**: "양 팔 골절"이라는 심각한 부상이 기록되어 있어도, tactical_doc 어딘가에 "부상"이라는 단어가 한 번이라도 등장하면 경고가 생성되지 않는다. 부상과 무관한 문맥에서 "부상"이 언급되어도 통과한다. 이 검사의 실효성이 매우 낮다.
- **Suggested fix direction**: 부상 키워드의 위치를 Arc 도입부(첫 화)로 한정. 부상 심각도별 회복 기간 추정 로직 추가. 또는 LLM 프롬프트에 더 구체적인 부상→회복 연속성 검증 항목 추가.

---

### TF-CA-14: `_escape_braces` 중복 에스케이프 방지의 edge case -- INSIGHT

- **Location**: `continuity_arc.py:L371-L376` → `base_agent.py:L1466-L1495`
- **Description**: `_escape_braces()`는 이미 `{{`/`}}`가 있고 단일 `{`/`}`가 없으면 "이미 에스케이프됨"으로 판단하여 skip한다. 그러나 텍스트에 `{{ }}` (이미 에스케이프된 부분)과 `{ }` (아직 안 된 부분)이 혼재하면, 단일 중괄호가 존재하므로 전체를 다시 에스케이프하여 이미 된 부분이 4중 중괄호(`{{{{`)가 된다.
- **Evidence**:
```python
# base_agent.py L1489-1493
has_double = "{{" in text or "}}" in text
has_single = "{" in text.replace("{{", "") or "}" in text.replace("}}", "")
if has_double and not has_single:
    return text  # 이미 에스케이프됨
return text.replace("{", "{{").replace("}", "}}")  # 전체 재에스케이프
```
  혼재 시: `"이미 {{에스케이프}} + 아직 {안됨}"` → replace 후 `"이미 {{{{에스케이프}}}} + 아직 {{안됨}}"` (4중 중괄호 발생)
- **Impact**: `SafeDict`의 `format_map`에서 `{{{{`는 리터럴 `{{`로 렌더링되어 LLM에 불필요한 중괄호가 전달된다. 실제 tactical_doc에 JSON 예시 등이 포함되면 이 edge case가 발동할 수 있으나, LLM이 이를 무시할 수 있으므로 실질적 영향은 제한적이다.
- **Suggested fix direction**: 정규식 기반 선택적 에스케이프 (`re.sub(r'(?<!\{)\{(?!\{)', '{{', text)` 방식)로 교체하여 단일 중괄호만 이중화.

---

## 4. Summary Matrix

| ID | Title | Severity | Category | Python/LLM | FP Risk | FN Risk |
|----|-------|----------|----------|------------|---------|---------|
| TF-CA-01 | NPC 사망 상태 Arc 검증 누락 | CRITICAL | NPC State | 양쪽 누락 | -- | HIGH |
| TF-CA-02 | LLM 실패 시 무조건 PASS | CRITICAL | Error Handling | Python 무력화 | -- | HIGH |
| TF-CA-03 | JSON 파싱 실패 시 PASS | CRITICAL | Error Handling | Python 무력화 | -- | HIGH |
| TF-CA-04 | 공간/시간 Python 검사 부재 | IMPORTANT | Temporal/Spatial | Python 누락 | -- | MEDIUM |
| TF-CA-05 | intra-arc 자동 완화 과도 | IMPORTANT | Single-Arc | Python 완화 | -- | MEDIUM |
| TF-CA-06 | `_is_same_item` FN 위험 | IMPORTANT | Cross-Arc | Python FN | LOW | HIGH |
| TF-CA-07 | tactical_doc 절삭 정보 손실 | IMPORTANT | Arc Summary | LLM 입력 | -- | MEDIUM |
| TF-CA-08 | intra-arc 검증 범위 제한 | IMPORTANT | Single-Arc | Python 제한 | MEDIUM | MEDIUM |
| TF-CA-09 | ep_start/ep_end 타입 안전성 | IMPORTANT | Arc Summary | Python | -- | LOW |
| TF-CA-10 | acquire_patterns 조사 의존 | IMPORTANT | Korean Regex | Python | MEDIUM | HIGH |
| TF-CA-11 | prev_inventory 덮어쓰기 | INSIGHT | Code Quality | Python | -- | -- |
| TF-CA-12 | current_arc 직접 mutate | INSIGHT | Code Quality | Python | -- | -- |
| TF-CA-13 | 부상 연속성 검사 단순성 | INSIGHT | State Continuity | Python | LOW | HIGH |
| TF-CA-14 | _escape_braces edge case | INSIGHT | Prompt Construction | LLM 입력 | -- | LOW |

---

## 5. 핵심 코드 참조 (Appendix)

### A. inspect_arc 진입점 (L227-L474)

핵심 제어 흐름:
- L244: Arc 1이면 `_inspect_intra_arc_only()`로 분기
- L264-279: tactical_doc 없으면 REJECT
- L285-293: Python precheck (advisory only)
- L298-306: Joint Docs auto-correction (LLM)
- L311-356: Arc Start State auto-correction (Python)
- L365-378: LLM 프롬프트 구성
- L380-393: LLM 호출 + JSON 파싱 (실패 시 PASS)
- L396-425: 결과 병합 (Python advisory + correction info)
- L428-452: intra-arc 위반 자동 완화
- L456-474: 예외 catch → PASS

### B. _arc_python_precheck 검증 항목 (L571-L769)

검증하는 것:
1. 중복 획득 (L712-L732): `_is_same_item()` 기반 정확 매칭
2. 단일 Arc 내 모순 (L738-L743): `_check_intra_arc_consistency()` 위임
3. 부상 상태 연속성 (L746-L752): 3개 키워드 검색

검증하지 않는 것:
- NPC 사망/생존 상태
- 장소 이동 물리적 타당성
- 시간 경과 합리성
- 무공/경지 수준 급변
- 관계 변화 일관성

### C. _check_intra_arc_consistency 검증 항목 (L771-L873)

검증하는 것:
1. 에피소드 분할: `\[제\s*(\d+)화[^\]]*\]` 정규식 (L781)
2. Arc 내 중복 획득 (L793-L814): `acquire_patterns` 매칭
3. 부상→전투 연속성 (L823-L837): 6개 부상 키워드 + 5개 행동 키워드
4. 복장 일관성 (L839-L871): 화려한↔허름한 전환 감지

### D. LLM 프롬프트 구조 (L21-L158)

7단계 Chain-of-Thought:
1. 아이템/무기 타임라인 검증
2. 수여물/위상 타임라인 검증
3. 상태 연속성 검증
4. 단일 Arc 내 모순 검증
5. 설정 일관성 검증
6. Entity 명칭 일관성 검증 (V61)
7. 최종 판정

누락된 검증 항목:
- NPC 사망/생존 상태
- 시간 경과 합리성 (명시적 항목 없음)
- 장소 이동 거리/시간 (L65, L99에 언급만 있고 구체적 기준 없음)
- 무공 수련 기간 합리성

### E. 이전 Arc 요약 포맷 (L875-L964)

포함하는 정보:
- `arc_end_state`: internal_energy, injuries, location, equipment
- `joint_docs`: final_location, physical_inventory, world_joint
- `status_shadow`: internal_energy_loss, expected_injuries
- 획득 아이템/수여물 타임라인
- 첫 화/마지막 화 전술 요약 (4500자 제한)

### F. 외부 의존성 참조

| 메서드 | 소스 | 용도 |
|--------|------|------|
| `self._ci.ask()` | `base_agent.py` | LLM 호출 |
| `self._ci._extract_json_robust()` | `base_agent.py` | JSON 파싱 |
| `self._ci._escape_braces()` | `base_agent.py:L1466` | 중괄호 에스케이프 |
| `self._ci._is_same_item()` | `continuity_inspector.py:L248` | 아이템 동일성 판단 |
| `self._ci._filter_distributed_items()` | `continuity_inspector.py:L319` | 분배 아이템 필터 |
| `self._ci._extract_acquisitions()` | `continuity_inspector.py:L198` | 획득 아이템 추출 |
| `self._ci._extract_grants()` | `continuity_inspector.py:L209` | 수여물 추출 |
| `self._ci._format_entity_registry()` | `continuity_inspector.py:L152` | Entity Registry 포맷 |
| `self._ci.acquire_patterns` | `continuity_inspector.py:L82` | 획득 정규식 4개 |
| `self._ci.grant_patterns` | `continuity_inspector.py:L99` | 수여 정규식 5개 |
| `self._ci.usage_patterns` | `continuity_inspector.py:L91` | 사용 정규식 4개 |
| `extract_episode_tactical()` | `tactical_utils.py:L31` | 에피소드별 전술 추출 |
| `SafeDict` | `prompt_loader.py:L22` | 누락 키 보존 포맷팅 |
| `Stage2Limits` | `constants.py:L235` | DEFAULT_EP_COUNT=4 |
