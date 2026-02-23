# Opus TF-5: Continuity Inspector Chain Debug Audit (TF-I)

> 감사일: 2026-02-23  
> 범위: `modules/domain/agents/continuity_arc.py`, `modules/domain/agents/continuity_blueprint.py`, `modules/domain/agents/continuity_manuscript.py`, `modules/domain/agents/consensus_validator.py`  
> 호출 추적: `modules/domain/agents/continuity_inspector.py` 위임 경로(`inspect_arc`, `inspect`, `inspect_manuscript`)

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 0 |

### [I-1] Arc 중복 획득 검증에서 `current_inventory`를 선필터에 포함해 실제 중복 획득을 누락함 — HIGH
- **위치**: `modules/domain/agents/continuity_arc.py:691`, `modules/domain/agents/continuity_arc.py:712`, `modules/domain/agents/continuity_arc.py:721`, `modules/domain/agents/continuity_arc.py:734`, `modules/domain/agents/continuity_inspector.py:374`
- **코드 인용**:
```python
current_joint = current_arc.get("joint_docs", {})
...
all_existing_items = prev_inventory_items + current_inventory_items + list(usage_items)
...
for curr_item in current_acquisitions:
    for owned_item in all_existing_items:
        if self._ci._is_same_item(curr_item, owned_item):
            is_already_owned = True
```
- **현상**: "현재 Arc에서 획득 시도한 아이템"이 `joint_docs.physical_inventory`에도 있으면 중복 검사 전에 제거된다.
- **재현 시나리오**: Arc 2에서 이미 획득한 `백근도`를 Arc 3 `state_constraints.protagonist_items`에 다시 넣고 `joint_docs.physical_inventory`에도 동일 아이템이 있으면, `duplicate_acquisition` 루프(`:734`)에 도달하지 못한다.
- **영향**: cross-arc 중복 획득이 사전검증에서 누락되어 REJECT 근거가 약화된다.
- **수정 제안**: 선필터의 비교군에서 `current_inventory_items`를 제외하고, `prev_inventory_items + usage_items`만 사용한다.

### [I-2] Blueprint 미수여 소지 검증이 키워드 단위 매칭이라 다른 수여물을 동일 권한으로 오인함 — MEDIUM
- **위치**: `modules/domain/agents/continuity_blueprint.py:337`, `modules/domain/agents/continuity_blueprint.py:341`, `modules/domain/agents/continuity_blueprint.py:344`, `modules/domain/agents/continuity_inspector.py:337`
- **코드 인용**:
```python
grant_keywords = ["패", "권", "인장", "직위", "자격", "서"]
...
if keyword in possession:
    was_granted = False
    for granted_item, g_ep in granted_items.items():
        if keyword in granted_item:
            was_granted = True
```
- **현상**: 동일 "키워드"만 포함되면 다른 개체여도 수여된 것으로 간주된다.
- **재현 시나리오**: 이전 화에서 `철혈사자패`만 수여됐는데 현재 화에서 `가주권`을 소지하면, `권` 키워드 일치로 `was_granted=True` 처리될 수 있다.
- **영향**: `premature_possession` CRITICAL 사전감지가 누락되어 LLM 검증 입력 품질이 떨어진다.
- **수정 제안**: 키워드 포함 검사 대신 `self._ci._is_same_item()` 기반의 개체 비교로 변경한다.

### [I-3] 원고 미획득 아이템 판정이 부분 문자열 허용이라 유사 문자열을 획득 완료로 오판함 — MEDIUM
- **위치**: `modules/domain/agents/continuity_manuscript.py:417`, `modules/domain/agents/continuity_manuscript.py:500`, `modules/domain/agents/continuity_manuscript.py:501`, `modules/domain/agents/continuity_inspector.py:416`
- **코드 인용**:
```python
if item and not self._is_item_acquired(item, all_acquired_items):
    critical_violations.append(...)
```
```python
for acquired in acquired_items:
    if item in acquired or acquired in item:
        return True
```
- **현상**: 완전 동일 아이템이 아니어도 부분 문자열이면 획득 완료로 처리한다.
- **재현 시나리오**: 이전 화 `철혈사자패` 보유 기록이 있을 때 현재 화 `사자패 복제본` 사용이 등장하면 부분 문자열 조건으로 통과될 수 있다.
- **영향**: `unowned_item_usage` CRITICAL 감지가 약화되어 실제 연속성 위반이 누락된다.
- **수정 제안**: `_is_item_acquired()`를 부분 문자열 비교 대신 정규화된 정확 매칭 + 동의어 테이블 비교로 제한한다.

## 비고
- `modules/domain/agents/consensus_validator.py`는 파일 주석상 `UnifiedArcValidator` 대체 대상(`unified_arc_validator.py:17-22`)으로 명시되어, 본 라운드에서는 신규 확정 이슈로 채택하지 않음.
- SafeDict 전환(`format_map`)은 `continuity_arc.py:364`, `continuity_blueprint.py:223`, `continuity_manuscript.py:278`, `consensus_validator.py:299`에서 정상 적용 확인.
