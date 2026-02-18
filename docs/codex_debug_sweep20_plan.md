# Debug Sweep 20 — 데이터 필드 오류 + Null Guard + Dead Code

## Context

Sweep 19(8건) 완료 후, 5-에이전트 병렬 탐색으로 미탐색 핵심 모듈 전면 스윕:
stage2 서브모듈 3종, stage4 서브모듈 3종, validation 4종, state_tracker/continuity_inspector 서브모듈, 소형 core 모듈 7종.
수동 코드 검증으로 **확인된 실제 버그 6건** 정리.

---

## A-1 (HIGH): `consistency_validator.py:175` 권위 위임 정당화 체크 — 잘못된 변수 참조

**파일**: `modules/validation/consistency_validator.py:175`

**문제**:
```python
# L117 — state_action 체크 (올바른 패턴: 개별 violation 체크)
for v in state_check["violations"]:
    if v.get("has_justification", False):  # ✅ 개별 violation

# L175 — authority_delegation 체크 (잘못된 패턴: 전체 결과 체크)
for v in authority_check["violations"]:
    if authority_check.get("has_justification", False):  # ❌ 전체 check 결과
```
- L117, L129 (state_action, relation) 모두 `v.get("has_justification")` — 개별 violation 체크
- L175 (authority) 만 `authority_check.get("has_justification")` — 전체 결과 체크
- 명확한 copy-paste 에러
- 결과: 모든 authority 위반이 동일하게 justifiable 또는 unjustifiable로 분류
- 개별 violation의 정당화 여부 무시 → 검증 정확도 저하

**수정**:
```python
# L175
if v.get("has_justification", False):
```

**테스트**: authority_delegation 위반에서 개별 violation의 `has_justification` 플래그가 정상 분류되는지 검증

---

## A-2 (HIGH): `consistency_validator.py:344-348` get_technique_effect_rules() Null → items() 크래시

**파일**: `modules/validation/consistency_validator.py:341-348`

**문제**:
```python
if not asset_library or not isinstance(asset_library, dict):
    if self.guard and hasattr(self.guard, "get_technique_effect_rules"):
        asset_library = self.guard.get_technique_effect_rules()  # ← None 반환 가능
    else:
        return {"passed": True, "violations": []}

for item_name, item_data in asset_library.items():  # ← None.items() → AttributeError
```
- `get_technique_effect_rules()` 가 None 또는 비-dict 반환 시 L348에서 크래시
- guard 메서드 존재 확인(`hasattr`)만 하고 반환값 검증 없음

**수정** — L344 뒤에 null guard 추가:
```python
if self.guard and hasattr(self.guard, "get_technique_effect_rules"):
    asset_library = self.guard.get_technique_effect_rules()
    if not asset_library or not isinstance(asset_library, dict):
        return {"passed": True, "violations": []}
else:
    return {"passed": True, "violations": []}
```

**테스트**: `get_technique_effect_rules()` 가 None 반환 시 안전하게 `{"passed": True}` 반환 검증

---

## A-3 (HIGH): `stage4_post_processor.py:284` time_passed 필드에 location 키 사용

**파일**: `modules/core/stage4_post_processor.py:284`

**문제**:
```python
bible_delta = {
    ...
    "time_passed": state_updates_from_audit.get("location", ""),  # ❌ 잘못된 키
    ...
}
```
- DB 스키마 (`db_manager.py:256`): `time_passed TEXT -- 경과 시간 (예: "같은 날 밤", "3일 후")`
- 코드가 `"location"` 키를 가져와서 `"time_passed"` 필드에 저장
- 결과: time_passed 컬럼에 장소 데이터("무당산", "황실" 등) 저장
- 실제 시간 경과 정보("3일 후" 등)는 소실
- `reverse_expander.py:762`에서 올바르게 `"time_passed": ""`로 초기화 → 불일치

**수정**:
```python
"time_passed": state_updates_from_audit.get("time_passed", ""),
```

**테스트**: `state_updates_from_audit = {"time_passed": "3일 후", "location": "무당산"}` 입력 시 bible_delta의 time_passed가 "3일 후"인지 검증

---

## A-4 (HIGH): `state_tracker_npc.py:1948` bare return → None (리턴 타입 위반)

**파일**: `modules/domain/agents/state_tracker_npc.py:1948`

**문제**:
```python
def cleanup_npc_registry_with_llm(self, arc_no: int) -> list[str]:
    """...
    Returns:
        삭제된 이름 목록 (실패 시 빈 리스트)
    """
    ...
    if not _resp_text:
        logging.info("⚠️ [V69] NPC 정리 LLM 응답 비어있음, 건너뜀")
        return  # ← None 반환! (list[str] 계약 위반)
    ...
    return removed     # ← list[str] ✅
    ...
    except Exception:
        return []        # ← list[str] ✅
```
- 3개 반환 경로 중 L1948만 None 반환
- 호출자(`state_tracker.py`)가 반환값을 리스트로 기대 → `for name in result:` 시 TypeError
- Docstring "실패 시 빈 리스트"와 불일치

**수정**:
```python
return []
```

**테스트**: LLM 응답 비어있을 때 `cleanup_npc_registry_with_llm()`이 `[]` 반환하는지 검증

---

## B-1 (MEDIUM): `state_tracker_npc.py:930` _RE_INJURY_BODY 패턴 완전 비활성화

**파일**: `modules/domain/agents/state_tracker_npc.py:920-939`

**문제**:
```python
# L30-31 — 패턴 정의
_RE_INJURY_DIRECT = re.compile(r"([가-힣]{2,10})...(중상|경상|위독|부상)...")   # 2 groups
_RE_INJURY_BODY = re.compile(r"([가-힣]{2,10})[의]\s*(?:팔|다리|눈|몸)...")      # 1 group ←
_RE_INJURY_REVERSE = re.compile(r"(중상|위독)...\s*([가-힣]{2,10})")             # 2 groups

# L921-924 — 패턴 리스트 (default_state 할당)
injury_patterns = [
    (_RE_INJURY_DIRECT, None),
    (_RE_INJURY_BODY, "중상"),     # default_state="중상" 할당 → 1그룹용 의도
    (_RE_INJURY_REVERSE, None),
]

# L930 — 2그룹 이상만 처리
if len(groups) >= 2:  # ← _RE_INJURY_BODY는 1그룹 → 항상 스킵
    ...
else:
    continue          # ← _RE_INJURY_BODY 매치 전부 버림
```
- `_RE_INJURY_BODY`는 NPC 이름만 캡처 (1그룹), `default_state="중상"` 제공
- L930 조건이 2그룹 이상만 허용 → 1그룹 패턴 완전 스킵
- "강철의 팔이 잘렸다" 등 신체 부상 표현 감지 불가

**수정** — L938-939의 `else: continue` 대신 1그룹 처리 추가:
```python
if len(groups) >= 2:
    if groups[0] in ("중상", "경상", "위독", "부상"):
        state = groups[0]
        npc_name = groups[1]
    else:
        npc_name = groups[0]
        state = default_state or groups[1]
elif len(groups) == 1 and default_state:
    npc_name = groups[0]
    state = default_state
else:
    continue
```

**테스트**: `"강철의 팔이 잘렸다"` 입력 시 `("강철", "중상")` 추출 검증

---

## B-2 (LOW): `stage2_validation_pipeline.py:662` 타입 어노테이션 `str` → `list`

**파일**: `modules/core/stage2_validation_pipeline.py:662`

**문제**:
```python
def _stage2_flow_guard_legacy(self, normalized: str) -> dict:  # ← str 선언
    """[V60.15] 레거시 Flow Guard (폴백용)"""
    ...
    for i in range(1, len(normalized)):  # ← list처럼 사용
        sim = jaccard(normalized[i - 1], normalized[i])  # ← 요소가 문자열
```
- 호출자 L604: `normalized = [self._normalize_flow_text(b) for b in beats if isinstance(b, str)]` → list
- L657: `self._stage2_flow_guard_legacy(normalized)` → list 전달
- 파라미터 타입 `str`이지만 실제로는 `list` 수신 → 타입 계약 위반
- 런타임 동작은 정상 (duck typing)

**수정**:
```python
def _stage2_flow_guard_legacy(self, normalized: list) -> dict:
```

**테스트**: 소스 파일에서 타입 어노테이션이 `list`인지 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/validation/consistency_validator.py` | 1줄 수정 (`authority_check` → `v`) |
| A-2 | `modules/validation/consistency_validator.py` | 2줄 추가 (None/dict guard) |
| A-3 | `modules/core/stage4_post_processor.py` | 1줄 수정 (`"location"` → `"time_passed"`) |
| A-4 | `modules/domain/agents/state_tracker_npc.py` | 1줄 수정 (`return` → `return []`) |
| B-1 | `modules/domain/agents/state_tracker_npc.py` | ~4줄 추가 (1그룹 패턴 처리) |
| B-2 | `modules/core/stage2_validation_pipeline.py` | 1줄 수정 (타입 어노테이션) |

**총 ~10줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `stage2_preflight.py:472,493` async/await 누락 | ✗ 오탐 | `four_phase.generate()`/`patch_arc_with_feedback()`는 동기 메서드. ask() 내부에서 동기 API 호출 |
| `stage2_preflight.py:469` previous_attempt["score"] KeyError | ✗ 오탐 | `_use_patch` 조건에서 `previous_attempt.get("score", 0) >= threshold` 확인 → score 키 보장 |
| `stage4_context_builder.py:444` get_protagonist_name 존재 체크 | ✗ 오탐 | 해당 라인에 코드 없음 (에이전트 라인 번호 오류) |
| `stage4_context_builder.py:75-88` 7화 vs 10화 범위 | ✗ 설계 | 주석 "직전 10화 (기존 3화 제외)" = 10-3 = 7화 의도된 설계 |
| `character_voice.py:130-137` tuple 언패킹 오류 | ✗ 오탐 | `findall` 그룹 → 튜플 리스트 → `for m in group if m` 정상 작동 (비어있지 않은 그룹 추출) |
| `pass_rate_monitor.py:299` dict 구문 에러 | ✗ 오탐 | 유효한 Python 삼항 연산자: `value_if_true if cond else value_if_false` |
| `martial_manager.py:545` 첫 번째 vs 마지막 숫자 | ✗ 불확실 | HUD 데이터는 대부분 단일 숫자("85"). "50→65" 형식 미확인 |
| `semantic_plot_guard.py:284` set 타입 가드 | ✗ 오탐 | `_resolved_keywords`는 내부 생성 set. 외부 역직렬화 경로 없음 |
| `consistency_validator.py:295` 중복 조건 | ✗ 스타일 | `if events and len(events) > 0` 중복이지만 동작에 영향 없음 |
| `stage2_validation_pipeline.py:508` continuity_result None | ✗ 극저확률 | inspect_arc()는 항상 dict 반환. None 반환은 에이전트 자체 프로그래밍 오류 시에만 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_consistency_validator.py tests/test_stage4_post_processor.py tests/test_stage2_validation_pipeline.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- 완료: A-1 `modules/validation/consistency_validator.py`
  - `authority_check.get("has_justification")` -> `v.get("has_justification")`
- 완료: A-2 `modules/validation/consistency_validator.py`
  - `get_technique_effect_rules()` 반환값이 `None`/비-dict일 때 조기 `PASS` 반환 가드 추가
- 완료: A-3 `modules/core/stage4_post_processor.py`
  - `bible_delta["time_passed"]`를 `state_updates_from_audit["time_passed"]`에서 읽도록 수정
- 완료: A-4 `modules/domain/agents/state_tracker_npc.py`
  - 빈 LLM 응답 경로 `return` -> `return []`
- 완료: B-1 `modules/domain/agents/state_tracker_npc.py`
  - `_RE_INJURY_BODY` 1-group 매치(`default_state`) 처리 분기 추가
- 완료: B-2 `modules/core/stage2_validation_pipeline.py`
  - `_stage2_flow_guard_legacy` 시그니처 어노테이션 `normalized: list`로 정정

### Tests Added/Updated

- 추가: `tests/test_consistency_validator.py`
  - authority_delegation 개별 violation 정당화 분류 검증
  - effect rule map `None` 반환 시 안전 PASS 검증
- 추가: `tests/test_state_tracker_npc_sweep20.py`
  - body injury 1-group 패턴에서 `중상` 추출 검증
  - 빈 LLM 응답 시 `[]` 반환 검증
- 수정: `tests/test_stage4_post_processor.py`
  - `time_passed` 필드 매핑 회귀 테스트 추가
- 수정: `tests/test_stage2_validation_pipeline.py`
  - legacy flow guard 어노테이션이 `list`인지 검증 추가

### Pytest Results

1. 계획서 타겟 실행
   - `python -m pytest tests/test_consistency_validator.py tests/test_stage4_post_processor.py tests/test_stage2_validation_pipeline.py -q -x`
   - 결과: `36 passed`
2. sweep20 보강 테스트 포함 타겟 실행
   - `python -m pytest tests/test_consistency_validator.py tests/test_stage4_post_processor.py tests/test_stage2_validation_pipeline.py tests/test_state_tracker_npc_sweep20.py -q -x`
   - 결과: `38 passed`
3. 전체 실행
   - `python -m pytest tests/ -q -p no:capture`
   - 결과: `1969 passed, 68 xfailed, 1 warning`
