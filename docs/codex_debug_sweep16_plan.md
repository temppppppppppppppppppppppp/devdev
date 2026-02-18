# Debug Sweep 16 — DI 누락 + Guard 위임 + 로깅 레벨

## Execution Status (2026-02-17)

- A-1 completed:
  - `main_a.py`
    - `Stage4Context(...)` 직접 주입 경로에 `pass_rate_monitor=getattr(self, "pass_rate_monitor", None)` 추가.
- A-2 completed:
  - `modules/core/genre_guards/work_guard.py`
  - `modules/core/genre_guards/style_guard.py`
    - `__getattr__` fallback 추가.
    - V46.1 9개 메서드(`get_authority_hierarchy`, `check_authority_delegation` 등)를 `self._base`로 명시 위임.
- A-3 completed:
  - `modules/domain/agents/chief_writer.py`
    - 컨텍스트 캐시 활성화 로그 레벨 `warning -> info`.
- A-4 completed:
  - `modules/domain/agents/chief_writer.py`
    - 후보 타임아웃 로그 레벨 `info -> warning`.
- B-1 completed:
  - `modules/core/genre_guards/base_guard.py`
    - `get_genre_name`, `get_v20_purism_prompt` abstract return annotation을 `-> str`로 수정.
- B-2 completed:
  - `modules/core/prompt_builder.py`
    - `extract_npc_profiles`, `get_character_traits`에 `_app is None` guard 추가.
- B-3 completed:
  - `modules/domain/agents/analyst.py`
    - `_validate_arc_with_state_tracker()` dead code 정리 후 `return []`로 단순화.

- Added tests:
  - `tests/test_stage4_interview_round.py`
    - `main_a.py`의 `pass_rate_monitor` 주입 라인 존재 검증 추가.
  - `tests/test_genre_guard.py`
    - WorkGuard/StyleGuard V46.1 위임 검증 추가.
    - BaseGuard abstract return annotation 검증 추가.
  - `tests/test_prompt_builder.py`
    - `_app=None`일 때 `extract_npc_profiles`, `get_character_traits` 안전 반환 검증 추가.
  - `tests/test_stage2_pipeline.py`
    - `_validate_arc_with_state_tracker()`가 빈 리스트 반환하는지 검증 추가.
  - `tests/test_chief_writer.py`
    - 캐시 활성화/타임아웃 로그 레벨 소스 검증 추가.

- Verification:
  - `python -m pytest tests/test_stage4_interview_round.py tests/test_chief_writer.py tests/test_genre_guard.py tests/test_prompt_builder.py tests/test_stage2_pipeline.py -q -x` -> `235 passed`
  - `python -m pytest tests/ -q -p no:capture` -> `1938 passed, 68 xfailed, 1 warning`

## Context

Sweep 15(7건) 완료 후, 5-에이전트 병렬 탐색으로 미탐색 대형 모듈 전면 스윕:
main_a.py, chief_writer, prompt_builder, db_manager, project_manager, genre_guards, HUD, vec_memory, analyst, optimizer.
수동 코드 검증으로 **확인된 실제 버그 7건** 정리.

---

## A-1 (CRITICAL): Stage4Context에 `pass_rate_monitor` 주입 누락

**파일**: `main_a.py:2916-2942`

**문제**:
```python
# L2916 — Stage4Context 직접 생성자 호출
self._stage4_orch.ctx = Stage4Context(
    ui=self.ui,
    current_project=self.current_project,
    # ... 12개 확장 속성 + 7개 콜백 ...
    pacing_analyzer=getattr(self, "pacing_analyzer", None),
    # ❌ pass_rate_monitor 누락!
)
```
- `Stage4Context.__slots__`에 `pass_rate_monitor` 존재 (stage4_context.py:37)
- `from_app()` (L126)에서는 `pass_rate_monitor=getattr(app, "pass_rate_monitor", None)` 추출
- 직접 생성자 호출 시 누락 → 기본값 None
- `stage4_interview_round.py:631`에서 None guard → **모든 Stage 4 기록이 자동 스킵**
- 영향: `get_arc_difficulty()`, `get_patch_effectiveness()`, `generate_reverse_feedback_stage4_to_2()` 전부 데이터 없음

**수정** — L2933 뒤에 추가:
```python
    pacing_analyzer=getattr(self, "pacing_analyzer", None),
    pass_rate_monitor=getattr(self, "pass_rate_monitor", None),
```

**테스트**: Stage4Context 생성자 호출 시 pass_rate_monitor 파라미터 포함 여부 검증

---

## A-2 (HIGH): WorkGuard/StyleGuard V46.1 메서드 위임 누락 → AttributeError

**파일**: `modules/core/genre_guards/work_guard.py`, `modules/core/genre_guards/style_guard.py`

**문제**:
- Guard 체인: GenreGuard → WorkGuard → StyleGuard (컴포지션, 상속 아님)
- 두 래퍼 모두 5개 메서드만 `self._base`에 위임:
  `get_genre_name`, `get_impossible_actions`, `get_justification_patterns`, `get_hierarchy_rules`, `check_state_action_consistency`
- V46.1 메서드 9개가 위임되지 않음:
  `get_authority_hierarchy`, `get_delegation_patterns`, `check_authority_delegation`,
  `get_hostile_action_types`, `get_resolution_patterns`, `check_unresolved_conflict`,
  `get_protagonist_victory_patterns`, `get_villain_response_patterns`, `check_villain_response`
- `consistency_validator.py:172`에서 `self.guard.check_authority_delegation()` 호출
- `stage4_orchestrator.py:631`에서 `guard=getattr(self.ctx.sys, "guard", None)` — 최외곽 guard 전달
- WorkGuard/StyleGuard가 활성이면 → `AttributeError: 'StyleGuard' object has no attribute 'check_authority_delegation'`

**수정** — 두 파일 모두에 `__getattr__` 추가:
```python
# work_guard.py — 위임 메서드 블록 뒤에 추가
def __getattr__(self, name):
    """미구현 메서드는 base guard로 위임."""
    return getattr(self._base, name)

# style_guard.py — 동일
def __getattr__(self, name):
    """미구현 메서드는 base guard로 위임."""
    return getattr(self._base, name)
```

---

## A-3 (MEDIUM): `chief_writer.py:230` 캐시 활성화 성공이 WARNING

**파일**: `modules/domain/agents/chief_writer.py:230`

**문제**:
```python
# 현재
logging.warning(f"📦 [V61.7] 컨텍스트 캐시 활성 (ep{ep_num}, {len(common_context)}자)")
# 수정
logging.info(f"📦 [V61.7] 컨텍스트 캐시 활성 (ep{ep_num}, {len(common_context)}자)")
```
- 캐시 활성화 **성공** 이벤트 → INFO 적절

---

## A-4 (MEDIUM): `chief_writer.py:272` 타임아웃 실패가 INFO

**파일**: `modules/domain/agents/chief_writer.py:272`

**문제**:
```python
# 현재
logging.info(f"⏰ [V61.3] 후보 {strategy} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")
# 수정
logging.warning(f"⏰ [V61.3] 후보 {strategy} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")
```
- 후보 생성 **타임아웃** (성능 저하 이벤트) → WARNING 적절

---

## B-1 (LOW): `base_guard.py:49,166` abstract method 리턴 타입 `-> None`

**파일**: `modules/core/genre_guards/base_guard.py:49,166`

**문제**:
```python
# 현재
@abstractmethod
def get_genre_name(self) -> None:  # ← 실제 구현체는 str 반환
    pass

@abstractmethod
def get_v20_purism_prompt(self) -> None:  # ← 동일
    pass
```
- 모든 서브클래스가 `-> str` 반환
- 타입 체커 계약 위반

**수정**:
```python
@abstractmethod
def get_genre_name(self) -> str:
    pass

@abstractmethod
def get_v20_purism_prompt(self) -> str:
    pass
```

---

## B-2 (LOW): `prompt_builder.py:898,915` self._app None 체크 누락

**파일**: `modules/core/prompt_builder.py:898,915`

**문제**:
```python
# L898 — extract_npc_profiles()
if not self._app.current_project:  # ← self._app이 None이면 AttributeError

# L915 — get_character_traits()
if not self._app.current_project:  # ← 동일
```
- L850의 `build_validation_context()`는 `if app and hasattr(...)` 패턴으로 올바르게 방어
- 동일 클래스 내 불일치

**수정**:
```python
# L898
if not self._app or not self._app.current_project:
    return npcs

# L915
if not self._app or not self._app.current_project:
    return traits
```

---

## B-3 (LOW): `analyst.py:1434-1452` 데드 코드 정리

**파일**: `modules/domain/agents/analyst.py:1434-1452`

**문제**:
```python
# L1435 — V70 주석이 이미 dead code로 표시
# [V70] NOTE: StateTracker()는 인자 없이 호출 불가 — 항상 except로 빠짐 (dead code)
tracker = StateTracker()
```
- `_validate_arc_with_state_tracker()` 전체가 비기능
- V70에서 인지됐지만 미정리 상태

**수정** — 메서드 body를 간소화:
```python
def _validate_arc_with_state_tracker(self, arc_data: dict) -> list:
    """[V49.3] StateTracker를 사용하여 Arc 설계의 상태 일관성 검증"""
    # [V70] StateTracker는 preset_registry/llm_client 없이 의미 있는 검증 불가
    return []
```

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `main_a.py` | 1줄 추가 (pass_rate_monitor 주입) |
| A-2 | `modules/core/genre_guards/work_guard.py` | `__getattr__` 3줄 추가 |
| A-2 | `modules/core/genre_guards/style_guard.py` | `__getattr__` 3줄 추가 |
| A-3 | `modules/domain/agents/chief_writer.py` | 1줄 (warning→info) |
| A-4 | `modules/domain/agents/chief_writer.py` | 1줄 (info→warning) |
| B-1 | `modules/core/genre_guards/base_guard.py` | 2줄 (타입 어노테이션) |
| B-2 | `modules/core/prompt_builder.py` | 2줄 (None 체크 추가) |
| B-3 | `modules/domain/agents/analyst.py` | ~18줄 → 2줄 (데드 코드 정리) |

**총 ~15줄 변경 + 18줄 삭제**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| Stage4Context.from_app() 미사용 (일관성) | ✗ 설계 | 직접 생성자가 더 명시적. 문제는 pass_rate_monitor 누락뿐 (A-1) |
| `execute_update()` 커밋 누락 | ✗ 설계 | 저수준 execute 래퍼. 호출자가 커밋 관리 (reflexion_manager.py:99 확인) |
| SQL 인젝션 `reset_after()` | ✗ 오탐 | 테이블명이 하드코딩 리스트에서 제공 |
| `commit_episode_factory` 교착 | ✗ 오탐 | RLock(재진입 가능) 사용. 같은 스레드 내 중첩 acquire 안전 |
| `chief_writer.py:304-307` Future.cancel() 무효 | ✗ 설계 | Sweep 3에서 이미 인지 (G2), 타임아웃으로 제한. cancel()은 best-effort |
| `chief_writer.py:459` 캐스케이딩 .get() None | ✗ 극저확률 | LLM JSON에 `"title": null` 반환 시에만 발생. 실전 확률 극히 낮음 |
| `vec_memory.py:301` off-by-one | ✗ 오탐 | `range(max_results)` 최대 인덱스가 `len-1` 이내. 에이전트 자체 계산으로 확인 |
| `stage2_optimizer.py:235` 0 나누기 | ✗ 오탐 | `len >= 3` 가드가 빈 문자열 차단 |
| WorkGuard regex 에러 silent skip | ✗ 설계 | YAML 사용자 오류에 대한 graceful degradation. WARNING 로깅으로 충분 |
| `cumulative_bible_cache` 레이스 | ✗ 오탐 | 캐시 무효화가 `save_episode_bible` 내부 (L473)에서 lock 하에 실행 |
| FantasyGuard V46.1 미구현 | ✗ 설계 | BaseGuard 기본 구현이 빈 값 반환 → 검증 스킵 (의도된 설계) |
| HunterGuard `realm` falsy trap | ✗ 오탐 | `realm = "E"` 는 truthy → violation 미발생. 정상 동작 |
| preset_registry None 경고 | ✗ 오탐 | Stage 0 → Stage 4 순서가 보장됨. preset_registry는 항상 초기화 상태 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_stage4_interview_round.py tests/test_chief_writer.py tests/test_genre_guards.py tests/test_prompt_builder.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```
