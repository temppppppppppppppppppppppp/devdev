# Debug Sweep 23 — UnboundLocalError + Null Deref + Dead Code

## Context

Sweep 22(4건) 완료 후, 5-에이전트 병렬 탐색으로 대형 코어 파일 집중 스윕:
main_a.py(4,200줄 전/후반), chief_writer.py(2,100줄), stage2+3 오케스트레이터, stage4 오케스트레이터 + director + auditor.
수동 코드 검증으로 **확인된 실제 버그 4건** 정리.

---

## A-1 (HIGH): `stage2_orchestrator.py:134` genre 변수 try 블록 내 초기화 → 예외 시 UnboundLocalError

**파일**: `modules/core/stage2_orchestrator.py:134-140, 534`

**문제**:
```python
# L133 — protagonist_name은 try 바깥 초기화 ✅
protagonist_name = None

# L134-140 — genre는 try 안에서만 초기화 ❌
try:
    genre = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
    protagonist_name = HUDKeys.get_protagonist_name(bible_root, genre)
    if protagonist_name and protagonist_name != "주인공":
        self.ctx.ui.log(f"🔒 [V42] 주인공 이름 락: {protagonist_name}")
except Exception as e:
    self.ctx.ui.log(f"⚠️ [V42] 주인공 이름 추출 실패: {e}")

# L534 — ~400줄 뒤, 메인 루프 안에서 사용
_fin = await self.finalizer.run_finalize(
    ...
    genre=genre,  # ← UnboundLocalError if exception at L135
    ...
)
```
- L135에서 예외 발생 시 `genre` 미초기화 → L534에서 `UnboundLocalError`
- `protagonist_name`은 L133에서 초기화했는데 `genre`만 누락 — copy-paste 실수
- Stage 2 전체 파이프라인 크래시

**수정** — L133 뒤에 추가:
```python
protagonist_name = None
genre = ""  # ← 추가
```

**테스트**: `HUDKeys.get_protagonist_name` 예외 시 Stage2가 크래시 없이 진행하는지 검증

---

## A-2 (HIGH): `main_a.py:2712` manuscripts=None 시 len(None) → TypeError

**파일**: `main_a.py:2710-2712`

**문제**:
```python
manuscripts = self.current_project.db.get_recent_manuscripts(before_ep=up_to_ep + 1, limit=5)
if not manuscripts or len(manuscripts) < 2:  # [V66] 최소 2화로 완화
    self.ui.log(f"   ⚠️ 원고 부족 ({len(manuscripts)}화) - 요약 건너뜀")
    #                              ^^^^^^^^^^^^^^^^^ manuscripts=None → TypeError
```
- `get_recent_manuscripts()`가 None 반환 시, `not None` → True → if 블록 진입
- 로그 메시지 안의 `len(manuscripts)` → `len(None)` → TypeError
- 조건문의 short-circuit은 정상이지만, 로그 메시지에서 크래시

**수정**:
```python
manuscripts = self.current_project.db.get_recent_manuscripts(before_ep=up_to_ep + 1, limit=5) or []
```

**테스트**: `get_recent_manuscripts()` 가 None 반환 시 크래시 없이 "원고 부족 (0화)" 로그 검증

---

## B-1 (MEDIUM): `main_a.py:2610` _get_int_input None 반환 시 KeyError

**파일**: `main_a.py:2603-2610`

**문제**:
```python
choice = self._get_int_input(
    ..., default=1, min_val=1, max_val=10,
)

selected = genres[str(choice)]  # ← choice=None → genres["None"] → KeyError
```
- `_get_int_input()` 반환 타입: `int | None` (L2279)
- default=1 제공이지만, None 반환 가능성 존재 (타입 계약)
- 동일 파일 L2652는 `or 1` 가드 사용: `(self._get_int_input(...) or 1) - 1` — 패턴 불일치
- `str(None)` = `"None"` → `genres["None"]` → KeyError

**수정**:
```python
choice = self._get_int_input(
    ..., default=1, min_val=1, max_val=10,
) or 1
```

**테스트**: `_get_int_input` 가 None 반환 시 default 1 적용 검증

---

## B-2 (LOW): `director_auditor.py:530-531` 도달 불가능한 None 체크 — dead code

**파일**: `modules/domain/agents/director_auditor.py:527-531`

**문제**:
```python
if self._d.use_v0128 and validation_context:  # L527 — validation_context truthy 보장
    expanded_prev_for_v0128 = self._expand_prev_full_text(ep_num, prev_full_text)
    if validation_context is None:  # L530 — ❌ L527에서 truthy 확인 → 절대 None 아님
        validation_context = {}
```
- L527의 `and validation_context`가 truthy 검증 → L530의 None 체크는 도달 불가
- `_audit_with_v0128()`가 L178에서 `validation_context["mode"] = mode` 사용하므로 L527의 truthy 체크는 올바름
- L530-531은 copy-paste dead code

**수정** — L530-531 삭제:
```python
if self._d.use_v0128 and validation_context:
    expanded_prev_for_v0128 = self._expand_prev_full_text(ep_num, prev_full_text)
    if expanded_prev_for_v0128:
        validation_context["expanded_prev_full_text"] = expanded_prev_for_v0128
```

**테스트**: V0128 경로 정상 동작 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/core/stage2_orchestrator.py` | 1줄 추가 (`genre = ""`) |
| A-2 | `main_a.py` | 1줄 수정 (`or []` 추가) |
| B-1 | `main_a.py` | 1줄 수정 (`or 1` 추가) |
| B-2 | `modules/domain/agents/director_auditor.py` | 2줄 삭제 (dead code) |

**총 ~5줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `main_a.py:2652` index out of bounds | ✗ 오탐 | `min_val/max_val` + `or 1` 가드로 bounds 안전 |
| `main_a.py:2615` preset_registry None (STAGE0=False) | ✗ 오탐 | STAGE0 모듈 항상 존재. False는 import 실패 극단 케이스 |
| `chief_writer.py:458` `or` 폴백 패턴 | ✗ 설계 | 빈 content 시 원본 폴백은 의도된 동작 |
| `chief_writer.py:383` bracket 기본값 | ✗ 오탐 | `ENSEMBLE_STRATEGIES["balanced"]`는 클래스 상수, 항상 존재 |
| `chief_writer.py:449` empty list `or` | ✗ 설계 | `KeyNPCs` 빈 리스트면 `Key_NPCs` 시도는 의도된 폴백 |
| `chief_writer.py:677` format KeyError | ✗ 오탐 | YAML 템플릿은 통제된 config. 외부 try-except도 존재 |
| `chief_writer.py:789` db 접근 가드 | ✗ 오탐 | ChiefWriter.context는 항상 ProjectContext (db 보장) |
| `stage3_orchestrator.py:156-157` dict 접근 불일치 | ✗ 오탐 | `.get()` truthy이면 키 존재 보장 → bracket 접근 안전 |
| `director_auditor.py:490` isinstance 불일치 | ✗ 스타일 | 방어적 체크 불일치일 뿐, 동작에 영향 없음 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_stage2_orchestrator.py tests/test_director.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- 완료: A-1 `modules/core/stage2_orchestrator.py`
  - `protagonist_name` 초기화 바로 아래 `genre = ""` 기본값 추가
- 완료: A-2 `main_a.py`
  - `get_recent_manuscripts(...)` 결과를 `or []`로 정규화
- 완료: B-1 `main_a.py`
  - `_get_int_input(...)` 결과에 `or 1` 적용
- 완료: B-2 `modules/domain/agents/director_auditor.py`
  - V0128 분기 내 도달 불가능한 `if validation_context is None` 블록 제거
- 추가 완료(후속 안정화): `modules/domain/agents/analyst.py`
  - `plan_single_volume_v20()`에서 프롬프트 로더가 과도하게 축약된 문자열을 반환해도
    `protagonist_config`(세계 출신/환생 유형) 제약 문구를 프롬프트에 강제 주입하도록 가드 추가

### Tests Added/Updated

- 추가: `tests/test_sweep23.py`
  - Stage2 `genre` 사전 초기화 존재 검사
  - `_generate_narrative_summary()`의 `None manuscripts` 처리 회귀 테스트
  - `_select_genre()`의 `None input` 기본값 처리 회귀 테스트
  - `DirectorQualityAuditor.audit_manuscript()` V0128 블록 dead code 제거 확인
  - `Analyst.plan_single_volume_v20()` 프롬프트가 generic 문자열이어도
    `protagonist_config` 핵심 제약(원시인/회귀자)을 포함하는지 확인

### Pytest Results

1. 계획서의 타깃 테스트 보정 실행
   - 계획서 명령의 `tests/test_stage2_orchestrator.py`, `tests/test_director.py`는 현재 저장소에 없음
   - 대체 실행: `python -m pytest tests/test_stage2_context.py tests/test_director_modules.py tests/test_sweep23.py -q -x`
   - 결과: `86 passed`
2. 전체 테스트 실행
   - `python -m pytest tests/ -q -p no:capture`
   - 결과: `1983 passed, 68 xfailed, 1 warning`
