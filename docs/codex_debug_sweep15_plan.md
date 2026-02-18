# Debug Sweep 15 — NPC 검사 비활성화 + Null Guard + 데드 코드

## Execution Status (2026-02-17)

- A-1 completed:
  - `modules/validation/pre_llm_validator.py`
    - `_check_npc_naming()`에서 잘못된 `len(pattern)` 분기 제거.
    - `found in manuscript` 중복 조건 제거.
- A-2 completed:
  - `modules/domain/agents/chief_writer_quality.py`
    - `_check_hud_consistency()`에 `hud_report` null guard 추가.
    - `_check_justification_gaps()`에 `hud_report` null guard 추가.
- A-3 completed:
  - `modules/core/stage4_context_builder.py`
    - `sys.hud`가 `None`일 때도 안전하게 `hud_report` 빈 문자열로 처리.
- B-1 completed:
  - `modules/validation/pre_llm_validator.py`
    - 사용되지 않던 `unconscious_action` regex 계산 제거.
- B-2 completed:
  - `modules/core/stage2_validation_pipeline.py`
    - DraftValidator 시작 로그 레벨 `warning -> info` 조정.
- B-3 completed:
  - `modules/core/stage4_orchestrator.py`
    - `_RoundContext` 타입 어노테이션 `current_inventory/current_martial_arts: str -> list`.
- B-4 completed:
  - `modules/core/fact_ledger.py`
    - `get_stats()`의 alive/dead 집계에 `isinstance(v, dict)` guard 추가.

- Added tests:
  - `tests/test_pre_llm_validator.py`
  - `tests/test_fact_ledger.py`
  - `tests/test_chief_writer_quality.py` (None HUD guard 2건 추가)
  - `tests/test_stage4_context_builder.py` (`sys.hud=None` fallback 케이스 추가)
  - `tests/test_stage4_orchestrator.py` (`_RoundContext` annotation 검증 추가)

- Verification:
  - `pytest -q tests/test_pre_llm_validator.py tests/test_stage4_context_builder.py tests/test_stage4_orchestrator.py tests/test_chief_writer_quality.py tests/test_fact_ledger.py tests/test_stage2_validation_pipeline.py -x` -> `107 passed`
  - Expanded regression set (23 modules) -> `370 passed`

## Context

Sweep 14(7건) 완료 후, 5-에이전트 병렬 탐색으로 미탐색 영역 전면 스윕:
stage2_validation_pipeline, chief_writer 서브모듈, stage4 post/context, continuity/world_state/fact_ledger, validation 3종.
수동 코드 검증으로 **확인된 실제 버그 7건** 정리.

---

## A-1 (HIGH): `_check_npc_naming()` NPC 이름 일관성 검사 완전 비활성화

**파일**: `modules/validation/pre_llm_validator.py:373`

**문제**:
```python
for i in range(len(correct_name)):
    pattern = correct_name[:i] + r"[가-힣]" + correct_name[i + 1 :]
    if len(pattern) == len(correct_name):  # ← 항상 False
        similar_names = re.findall(pattern, manuscript)
```
- `[가-힣]` 정규식 클래스는 문자열 길이 5자 (`[`, `가`, `-`, `힣`, `]`)
- 원본 1자를 5자로 대체 → `len(pattern)` 항상 `len(correct_name) + 4`
- 조건이 항상 False → `re.findall()` 절대 실행 안 됨
- 결과: NPC 이름 오타 감지 기능이 완전히 비활성화

**예시**: `correct_name = "소연"` (2자)
- `i=0`: pattern = `"[가-힣]연"` → len=5, 5 != 2 → False
- `i=1`: pattern = `"소[가-힣]"` → len=5, 5 != 2 → False

**수정**:
```python
for i in range(len(correct_name)):
    pattern = correct_name[:i] + r"[가-힣]" + correct_name[i + 1 :]
    similar_names = re.findall(pattern, manuscript)
    for found in similar_names:
        if found != correct_name:
            inconsistencies.append((found, correct_name))
```
- `len(pattern)` 조건 제거 (regex 매치 결과는 항상 `correct_name`과 동일 길이)
- `found in manuscript` 중복 체크 제거 (`re.findall`이 이미 manuscript에서 찾은 결과)

---

## A-2 (MEDIUM): `chief_writer_quality.py` hud_report null guard 누락 — 2개 메서드

**파일**: `modules/domain/agents/chief_writer_quality.py:178,249,251`

**문제**:
```python
# L178 — _check_hud_consistency()
is_weak = any(kw in hud_report for kw in weak_keywords)  # TypeError if hud_report is None

# L249 — _check_justification_gaps()
if "나약" in hud_report or "중독" in hud_report:  # TypeError if None
# L251
if "reputation" in hud_report.lower():  # AttributeError if None
```
- 두 메서드 모두 `hud_report: str` 타입 힌트이나 null guard 없음
- 호출 체인: `generate_ensemble(hud_report=...)` → `apply_self_critique()` → `_self_critique()` → L145/L153
- 현재는 `stage4_context_builder.py:151`에서 `else ""` 폴백으로 방어되지만, `get_v20_hud_report()`가 None 반환 시 크래시

**수정**:
```python
def _check_hud_consistency(self, content: str, hud_report: str) -> list:
    """HUD 모순 체크"""
    issues = []
    if not hud_report:
        return issues
    # ... 기존 코드 ...

def _check_justification_gaps(self, content: str, hud_report: str) -> list:
    """정당화 누락 체크"""
    issues = []
    if not hud_report:
        return issues
    # ... 기존 코드 ...
```

---

## A-3 (MEDIUM): `stage4_context_builder.py:151` sys.hud None 체크 누락

**파일**: `modules/core/stage4_context_builder.py:151`

**문제**:
```python
# L151 — None 체크 누락
hud_report = self.ctx.sys.hud.get_v20_hud_report() if hasattr(self.ctx.sys, "hud") else ""

# L156 — 올바른 패턴 (같은 메서드 내)
if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
```
- L151: `hasattr`만 체크 → `sys.hud`가 `None`이면 `None.get_v20_hud_report()` → AttributeError
- L156: `hasattr AND truthy` 패턴으로 올바르게 방어
- 동일 메서드 내에서 불일치

**수정**:
```python
hud_report = self.ctx.sys.hud.get_v20_hud_report() if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud else ""
```

---

## B-1 (LOW): `pre_llm_validator.py:282` 데드 코드 — unused regex result

**파일**: `modules/validation/pre_llm_validator.py:282-283`

**문제**:
```python
unconscious_action = re.findall(r"(기절|의식을 잃|잠든).{0,30}(일어나|눈을 떴다|말했다)", manuscript)
# 이건 정상적인 각성 과정일 수 있으므로 체크 안 함
```
- regex 실행 후 결과를 `unconscious_action`에 저장하지만 어디서도 사용하지 않음
- 주석이 "체크 안 함"이라고 명시 — 불필요한 regex 연산

**수정**: 2줄 삭제.

---

## B-2 (LOW): `stage2_validation_pipeline.py:66` 프로세스 시작 메시지가 WARNING 레벨

**파일**: `modules/core/stage2_validation_pipeline.py:66`

**문제**:
```python
# 현재
logging.warning("🔬 [무기 #3] DraftValidator 사전 검증...")
# 수정
logging.info("🔬 [무기 #3] DraftValidator 사전 검증...")
```
- 프로세스 **시작** 알림 (성공/실패 아님) → INFO 적절

---

## B-3 (LOW): `stage4_orchestrator.py:173-174` _RoundContext 타입 어노테이션 불일치

**파일**: `modules/core/stage4_orchestrator.py:173-174`

**문제**:
```python
# 현재 (dataclass 필드)
current_inventory: str      # ← 실제로 list 반환
current_martial_arts: str   # ← 실제로 list 반환
```
- `stage4_context_builder.py:154-166`에서 `list`로 생성: `current_inventory = []`, `current_martial_arts = []`
- `_RoundContext`에 `str`로 어노테이션 → 타입 불일치

**수정**:
```python
current_inventory: list
current_martial_arts: list
```

---

## B-4 (LOW): `fact_ledger.py:503-504` get_stats() isinstance 가드 누락

**파일**: `modules/core/fact_ledger.py:503-504`

**문제**:
```python
# get_stats() — 가드 없음
"alive": sum(1 for v in chars.values() if v.get("status") == "alive"),

# to_summary() L368 — 가드 있음 (비교)
alive = {k: v for k, v in chars.items() if isinstance(v, dict) and v.get("status") == "alive"}
```
- `to_summary()`에는 `isinstance(v, dict)` 가드가 있지만 `get_stats()`에는 없음
- 데이터 손상 시 `v`가 dict가 아니면 `v.get("status")` AttributeError

**수정**:
```python
"alive": sum(1 for v in chars.values() if isinstance(v, dict) and v.get("status") == "alive"),
"dead": sum(1 for v in chars.values() if isinstance(v, dict) and v.get("status") == "dead"),
```

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/validation/pre_llm_validator.py` | 조건문 제거 + 중복 체크 제거 (~4줄 수정) |
| A-2 | `modules/domain/agents/chief_writer_quality.py` | null guard 2줄 추가 |
| A-3 | `modules/core/stage4_context_builder.py` | 1줄 수정 (조건 추가) |
| B-1 | `modules/validation/pre_llm_validator.py` | 2줄 삭제 |
| B-2 | `modules/core/stage2_validation_pipeline.py` | 1줄 (warning→info) |
| B-3 | `modules/core/stage4_orchestrator.py` | 2줄 (타입 어노테이션) |
| B-4 | `modules/core/fact_ledger.py` | 2줄 수정 (isinstance 추가) |

**총 ~14줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `_fallback_first_candidate` candidates[0] 빈 리스트 | ✗ 오탐 | `compare_and_select_blueprint` L44에 `if not candidates:` 가드 존재 |
| `director_auditor.py:809,817` 경계값 오류 | ✗ 설계 | 경계값 → Self-Consistency 추가 평가 유도, 의도된 설계 |
| `state_tracker.py:186` arc null guard | ✗ 오탐 | `list[dict]` 타입 힌트, 호출자가 항상 유효한 arc 전달 |
| `state_tracker_npc.py:525,534` 얕은 복사 | ✗ 오탐 | NPC 레지스트리 엔트리는 flat dict (중첩 mutable 없음) |
| `stage4_post_processor.py:444` 함수 객체 체크 | ✗ 정상 | DI 슬롯 패턴 — `get_protagonist_name`이 None일 수 있어 호출 전 존재 확인 |
| `stage4_post_processor.py:217,174` 타입 가드 누락 | ✗ 오탐 | L158~456 전체가 try-except 블록 내부 |
| `stage2_validation_pipeline.py:509,515` 빈 dict 폴시 트랩 | ✗ 설계 | `{}` = "수정 없음" 의미, falsy 체크가 의도에 부합 |
| `world_state.py:204` 빈 문자열 매칭 | ✗ 오탐 | L201 `if plot_desc:` 가드가 빈 문자열 차단 |
| `batch_validator.py:133` sync 예외 처리 누락 | ✗ 오탐 | `validate_one()` 내부에 try-except 완비 → `executor.map` 예외 불가 |
| `stage2_validation_pipeline.py:173` validate_arc_mapping None 반환 | ✗ 오탐 | 호출 시점에 `refined_arc`는 이미 LLM 검증 완료된 dict |
| `chief_writer_quality.py:403-406` 대화 비율 elif 중복 범위 | ✗ 정상 | elif 카스케이드 → 실행은 상호배타적 |
| `pre_llm_validator.py:370` regex O(N²) 성능 | ✗ 무효 | A-1에 의해 코드 자체가 실행 안 됨 (len 조건 항상 False) |
| `fact_ledger.py:47` DB 로드 실패 로깅 레벨 | ✗ 설계 | DB 로드 실패는 warning 적절 (폴백이 있어도 주의 필요) |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_pre_llm_validator.py tests/test_stage4_context_builder.py tests/test_stage4_orchestrator.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```
