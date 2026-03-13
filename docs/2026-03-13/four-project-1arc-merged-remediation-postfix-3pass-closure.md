# 4프로젝트 1Arc 병합 수정 Post-Fix 3PASS Closure

> 작성일: 2026-03-13
> 상태: issue-found-and-responded
> 기준 SSOT: `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md`
> 선행 감리: `docs/2026-03-13/four-project-1arc-merged-remediation-3pass-audit.md`
> 범위: `E-3 Stage 2 integrity debt hardening`, `E-4 state_tracker skip semantics 재평가`

---

## 0. 요약

이번 tranche에서는 SSOT 기준으로 실제 코드 수정이 필요한 범위를 `E-3`, `E-4`로 좁혀 실행했다.

- `03`형 `Stage 2 integrity debt`는 proof-only로 닫지 않고, deterministic repair와 integrity fail 신호를 더 분명하게 남기도록 보강했다.
- `state_tracker 없음` 로그는 early-arc benign skip과 실제 tracker gap을 구분하도록 바꿨다.
- 3PASS 중 실제 이슈가 발견됐고, 같은 턴에서 대응했다.
- 따라서 이번 문서는 `최종 closed` 문서가 아니라, `문제 발견 -> 대응 완료 -> follow-up 2PASS 필요` 상태를 기록한다.

---

## 1. 실행 내용

### 1.1 `E-3` Stage 2 integrity debt hardening

수정 파일:

- `modules/core/stage2_finalizer.py`

핵심 변경:

- `validate_arc_data_fields` helper가 존재할 경우, custom missing-field fallback보다 먼저 호출하도록 보강
- helper가 복구 실패(`None`)를 반환하면 retry로 fail-closed 처리
- deterministic 기본값 주입 audit를 `data_missing`에서 `field_repair`로 분리
- critical field 누락이 임계치를 넘으면 `integrity_fail` audit를 명시적으로 남김

의도:

- `03`형 런에서 보였던 `data_missing`, `integrity_fail`의 의미를 구분하고
- “복구 가능한 구조 결손”과 “복구 불가한 integrity 문제”를 분리한다.

### 1.2 `E-4` state tracker skip semantics 재평가

수정 파일:

- `modules/domain/agents/unified_arc_validator.py`

핵심 변경:

- `prev_arcs`가 없는 early-arc 상황은 `info`로 benign skip 처리
- `prev_arcs`는 있는데 `state_tracker`가 없을 때만 `warning`으로 남김

의도:

- 기존 `state_tracker 없음 — 사망 NPC 체크 skip` 단일 warning은 benign early-arc와 wiring gap을 구분하지 못했다.
- fresh proof 단계에서 진짜 결함을 더 잘 드러내도록 로그 의미론을 정리했다.

### 1.3 테스트/fixture 보정

수정 파일:

- `tests/test_stage2_finalizer.py`
- `tests/test_arc_retry.py`
- `tests/test_unified_arc_validator.py`

핵심 변경:

- `MagicMock`가 `validate_arc_data_fields` 속성을 가짜로 만들어 helper 경로가 오염되지 않도록 `None`을 명시
- 신규 regression 추가:
  - helper 우선 호출 경로
  - fallback `field_repair` 분류
  - dead-NPC skip semantics 구분

---

## 2. 검증

### 2.1 문법 확인

```text
python -m py_compile modules/domain/agents/unified_arc_validator.py modules/core/stage2_finalizer.py tests/test_stage2_finalizer.py tests/test_unified_arc_validator.py tests/test_arc_retry.py
```

- 결과: 통과

### 2.2 focused regression

```text
pytest -q tests/test_stage2_finalizer.py tests/test_state_service.py tests/test_unified_arc_validator.py tests/test_arc_retry.py
```

- 결과: `67 passed in 2.40s`

---

## 3. Post-Fix 3PASS 감리

### Pass 1. SSOT 범위 대조

확인 항목:

- 이번 변경이 `E-3`, `E-4` 범위를 넘어서지 않았는가
- 기존에 닫힌 POV / Stage 4 provenance 축을 다시 건드리지 않았는가

판정:

- 적합
- `03`형 integrity debt와 `state_tracker` 로그 의미론에만 집중했고, 다른 closure 범위를 재개방하지 않았다.

### Pass 2. 구현 품질 감리

확인 항목:

- `validate_arc_data_fields` 우선 호출이 실제 fallback semantics를 깨지 않는가
- `field_repair` / `integrity_fail` 분리가 충분히 방어 가능한가
- `state_tracker` skip semantics가 실제로 benign case와 defect case를 분리하는가

발견 이슈:

1. 테스트 fixture realism 결함
   - `MagicMock` 기본 동작 때문에 `validate_arc_data_fields`가 실제로는 없는 컨텍스트에서도 callable처럼 보일 수 있었다.
   - 이 상태로는 새로운 helper 우선 경로가 테스트에서 과잉 발동한다.

2. 회귀 기대치 drift
   - fallback repair 검증이 기존 `data_missing` 분류를 전제로 하면 새 semantics와 충돌한다.

판정:

- 문제 있음
- 하지만 둘 다 구현 방향 자체의 오류라기보다 test/fixture와 기대치 정렬 문제다.

### Pass 3. 오탐 제거 감리

검토한 오탐 후보:

- `field_repair` 도입이 과한 것 아닌가
- `state_tracker` warning 완화가 결함 은닉 아닌가

오탐 제거 결과:

- `field_repair`는 과하지 않다. 기존 `data_missing`은 deterministic default injection과 integrity debt를 같은 bucket에 넣어 postmortem 해석을 흐렸다.
- `state_tracker` 완화도 과하지 않다. `prev_arcs`가 전혀 없는 early-arc에서 dead NPC check를 skip하는 것은 benign이고, warning 유지가 오히려 노이즈였다.

최종 판정:

- 문제는 존재했으나, 방향 오류가 아니라 fixture realism / 기대치 drift 문제로 정리된다.
- 대응 후 follow-up 2PASS가 필요하다.

---

## 4. 3PASS에서 발견된 문제와 대응

### 대응 1. `validate_arc_data_fields` fixture realism 보강

대응 파일:

- `tests/test_stage2_finalizer.py`
- `tests/test_arc_retry.py`

대응 내용:

- `ctx.validate_arc_data_fields = None`을 명시해, helper가 없는 컨텍스트에서는 새 경로가 자동 발동하지 않도록 했다.

### 대응 2. fallback repair 기대치 보정

대응 파일:

- `tests/test_stage2_finalizer.py`

대응 내용:

- deterministic repair audit의 기대치를 `data_missing`이 아니라 `field_repair`로 맞췄다.

---

## 5. 현재 상태

- 코드 변경은 반영 완료
- focused regression은 green
- 3PASS 중 발견된 문제는 대응 완료
- 최종 closure는 아직 아니며, `follow-up 2PASS`로 retained finding 잔존 여부를 다시 확인해야 한다.

---

## 6. 중간 확신도

- `70`: SSOT 범위 구현 완료
- `+10`: focused regression `67 passed`
- `+5`: integrity/fallback semantics 분리 확인
- `+5`: benign skip vs tracker gap 분리 확인
- `-5`: 3PASS 중 fixture realism / expectation drift 발견

중간 확신도: `85%`

이 값은 의도적으로 낮게 둔다. follow-up 2PASS에서 대응 후 잔존 문제 없음이 확인되어야 `95%`로 올릴 수 있다.
