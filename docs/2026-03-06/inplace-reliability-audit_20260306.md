# InPlace Patch 신뢰성 조사 보고서 (2026-03-06)

> 범위: S2 Arc / S3 Blueprint / S4 Manuscript InPlace 패치 전 경로
> 기준: pipeline-run-audit-01 (001_260306) 실전 가동 결과

---

## 1. 조사 동기

pipeline-run-audit-01에서 InPlace-Diff 로깅을 최초 가동하여 Arc 1(37줄), Arc 3(28줄) diff를 확인함. InPlace가 실제로 무엇을 바꾸는지 투명하게 확인할 수 있게 되었으나, InPlace 자체의 구조적 신뢰성에 대한 전면 조사 필요성이 제기됨.

---

## 2. 조사 범위

| 영역 | 파일 | 대상 메서드 |
|------|------|-----------|
| S4 원고 | `stage4_interview_round.py` | `_execute_pass_with_fix_loop` |
| S4 원고 | `chief_writer.py` | `inplace_patch`, `_unwrap_manuscript_text` |
| S2 Arc | `four_phase_arc_generator.py` | `_inplace_patch_arc` |
| S2 Arc | `stage2_finalizer.py` | PASS_WITH_FIX 루프 |
| S3 Blueprint | `three_phase_blueprint_generator.py` | `_inplace_patch_blueprint` |

---

## 3. S4 (원고) 평가: 견고

S4 InPlace는 TF-47/TF-46/TF-35/PF-3 4대 방어층을 갖춤.

### 방어 메커니즘 요약

| 계층 | 메커니즘 | 위치 |
|------|---------|------|
| 1 | JSON 3-stage 파싱 폴백 (전체→rfind→regex→unwrap) | `chief_writer.py` L832-909 |
| 2 | TF-47: rfind position 0 보호 (전체 삭제 방지) | `chief_writer.py` L860 |
| 3 | 최소 길이 검사 (2000자 미만 → break) | `stage4_interview_round.py` L1305-1308 |
| 4 | 재심사 루프 최대 3회 + 5가지 탈출 조건 | `stage4_interview_round.py` L1240-1430 |
| 5 | PF-3: PASS_WITH_FIX 소진 시 마지막 패치본 추적 | `stage4_interview_round.py` L1415-1428 |

### S4 잔여 위험

| ID | 위험 | 수준 | 비고 |
|----|------|------|------|
| S4-R1 | PASS_WITH_FIX 반복 시 state_updates 완전 교체 | LOW | Director 재평가가 최신 값 생산, 설계 의도 |
| S4-R2 | InPlace 후 self-critique 미실행 | LOW | Director 재심사가 대체 역할 |
| S4-R3 | 150KB 초과 원고 → smart_truncate | INFO | 경고 로깅 있음, 실전 미발생 |

**S4 결론: 패치 불필요.**

---

## 4. S2/S3 (Arc/Blueprint) 평가: P1 3건 발견 + 패치 완료

### 발견 이슈

#### P1-1: 30KB JSON 절단 → 깨진 JSON으로 LLM 호출

**심각도**: P1

**증상**: `_full_json[:30000]`으로 JSON을 강제 절단하면 닫는 괄호가 누락되어 유효하지 않은 JSON이 LLM에 전달됨. LLM이 손상된 JSON을 수정 시도하면 `_extract_json_robust()` 폴백 실행, 일부 필드만 추출되거나 전체 실패.

**영향**: S2 `_inplace_patch_arc()` L845, S3 `_inplace_patch_blueprint()` L694

**수정**: 30KB 초과 시 `return None` (full rewrite 폴백). 절단된 JSON으로 InPlace 시도하는 것보다 전면 재생성이 안전.

#### P1-2: Top-level only merge → 중첩 dict 서브키 손실

**심각도**: P1

**증상**: `for key, val in original.items(): if key not in result: result[key] = val` — top-level 키만 복원. LLM이 `state_constraints`를 반환하되 `arc_start_state`를 누락하면, `state_constraints` 자체는 result에 있으므로 원본 `arc_start_state`가 복원되지 않음.

**시나리오**:
```
원본: state_constraints: {arc_start_state: {...}, arc_end_state: {...}}
LLM:  state_constraints: {arc_end_state: {수정됨}}
병합: state_constraints: {arc_end_state: {수정됨}}  ← arc_start_state 영구 손실!
```

**영향**: S2 L877-879, S3 L749-751

**수정**: 1-depth deep merge 적용. dict 값에 대해 서브키 레벨까지 원본 복원.
```python
elif isinstance(val, dict) and isinstance(result[key], dict):
    for sub_key, sub_val in val.items():
        if sub_key not in result[key]:
            result[key][sub_key] = sub_val
```

#### P2-1: S2 InPlace 후 Pydantic 검증 누락

**심각도**: P2

**증상**: S3는 `validate_blueprint(result)` 호출(L758)하지만, S2 `_inplace_patch_arc()`는 Pydantic 검증 없이 result를 반환. Director 재심사에 미검증 Arc가 전달될 수 있음.

**수정**: `validate_arc(result)` 호출 추가 (graceful degradation — 실패해도 원본 반환).

### 패치 내역

| 파일 | 변경 | 줄수 |
|------|------|------|
| `four_phase_arc_generator.py` L839-845 | 30KB 절단 → `return None` | 3줄 |
| `four_phase_arc_generator.py` L877-879 | 1-depth deep merge 추가 | 3줄 |
| `four_phase_arc_generator.py` L885 | `validate_arc(result)` 추가 | 2줄 |
| `three_phase_blueprint_generator.py` L688-694 | 30KB 절단 → `return None` | 3줄 |
| `three_phase_blueprint_generator.py` L749-751 | 1-depth deep merge 추가 | 3줄 |

### 테스트

| 테스트 | 검증 |
|--------|------|
| `test_arc_over_30kb_returns_none` | 30KB 초과 Arc → None 반환 |
| `test_blueprint_over_30kb_returns_none` | 30KB 초과 Blueprint → None 반환 |
| `test_arc_under_30kb_proceeds` | 30KB 이하면 정상 LLM 호출 |
| `test_arc_preserves_arc_start_state` | deep merge: arc_start_state 복원 |
| `test_arc_patched_subkey_not_overwritten` | deep merge: LLM 값 우선 보존 |
| `test_blueprint_preserves_missing_subkeys` | S3 deep merge: 씬 키 복원 |
| `test_arc_inplace_calls_validate_arc` | S2 Pydantic 검증 호출 확인 |

---

## 5. S4 vs S2/S3 차이 비교

| 항목 | S4 (원고) | S2 (Arc) | S3 (Blueprint) |
|------|-----------|----------|----------------|
| 데이터 형태 | 텍스트 | JSON dict | JSON dict |
| 절단 보호 | 150KB 경고 + smart_truncate | ~~30KB 절단~~ → **return None** | ~~30KB 절단~~ → **return None** |
| 파싱 보호 | 3-stage JSON 폴백 + unwrap | `_extract_json_robust` | `_extract_json_robust` |
| 필드 복원 | N/A (텍스트) | ~~top-level only~~ → **1-depth merge** | ~~top-level only~~ → **1-depth merge** + scene_breakdown 씬 키 복원 |
| Pydantic 검증 | N/A | ~~없음~~ → **validate_arc 추가** | validate_blueprint 있음 |
| 최소 길이 검사 | 2000자 (YAML 설정 가능) | 없음 (None 반환으로 대체) | 없음 (None 반환으로 대체) |
| state_updates merge | PASS=merge, PWF=replace | 호출자(stage2_finalizer) 관리 | 호출자(three_phase) 관리 |
| 재심사 루프 | 최대 3회 + 5 탈출 조건 | 최대 3회 + 4 탈출 조건 | 최대 3회 + 4 탈출 조건 |

---

## 6. 정상 동작 확인

| 기능 | S4 | S2 | S3 |
|------|-----|-----|-----|
| 재심사 루프 수렴 (최대 3회) | OK | OK | OK |
| REJECT 시 원본 보존 | OK | OK | OK |
| 빈 응답 → 폴백 | OK | OK | OK |
| InPlace-Diff 로깅 | OK (신규) | OK (신규) | OK (신규) |

---

## 7. 잔여 P2 유보 항목

| ID | 설명 | 이유 |
|----|------|------|
| R-P2-1 | S3 재심사 시 patch 이력 미주입 (S2는 story_context에 주입) | Director가 독립 평가하므로 영향 제한적 |
| R-P2-2 | PASS_WITH_FIX 반복 시 동일 fix_scope → 동일 오류 반복 가능 | 최대 3회 제한으로 수렴 보장, 실전 빈도 낮음 |
| R-P2-3 | S4 PASS_WITH_FIX state_updates 완전 교체 | Director 재평가 모델, 설계 의도 |
