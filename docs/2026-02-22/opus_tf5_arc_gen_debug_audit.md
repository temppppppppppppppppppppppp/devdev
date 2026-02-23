# Opus TF-5: Arc/Blueprint Generation Debug Audit (TF-J)

> 감사일: 2026-02-23  
> 범위: `modules/domain/agents/analyst.py`, `modules/domain/agents/four_phase_arc_generator.py`, `modules/domain/agents/arc_corrector.py`, `modules/domain/agents/block_enricher.py`, `modules/domain/agents/state_extractor.py`, `modules/domain/agents/weaver.py`  
> 호출 경로 확인: `modules/core/stage2_preflight.py` → `modules/domain/agents/four_phase_arc_generator.py` → `modules/domain/agents/unified_arc_validator.py`

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 0 |
| LOW | 0 |

### [J-1] pre_collected_items 최적화 경로에서 dict 아이템이 문자열 직렬화되어 중복 획득 CRITICAL 검사가 우회됨 — HIGH
- **위치**: `modules/core/stage2_preflight.py:751`, `modules/domain/agents/four_phase_arc_generator.py:205`, `modules/domain/agents/four_phase_arc_generator.py:386`, `modules/domain/agents/unified_arc_validator.py:351`, `modules/domain/agents/unified_arc_validator.py:368`, `modules/domain/agents/unified_arc_validator.py:360`
- **코드 인용**:
```python
# four_phase_arc_generator.py
_acq = _prev.get("state_constraints", {}).get("items_acquired", [])
if isinstance(_acq, list):
    _pre_items.update((str(i) if isinstance(i, dict) else i).strip() for i in _acq if i)
...
verdict, validation_result = self.validator.validate(..., pre_collected_items=_pre_items, ...)
```
```python
# unified_arc_validator.py
if pre_collected_items is not None:
    prev_items = pre_collected_items
...
item_str = item.strip() if isinstance(item, str) else str(item)
if item_str in prev_items:
```
```python
# unified_arc_validator.py (비최적화 경로)
prev_items.update(
    (item.get("name", item.get("item", "")) if isinstance(item, dict) else str(item).strip())
    for item in acquired if item
)
```
- **현상**: 최적화 경로(`pre_collected_items` 전달)에서는 dict 아이템을 `str(dict)`로 저장하고, 비교도 그대로 `str(item)`로 수행한다.
- **재현 시나리오**: 이전 Arc가 `{"name": "철검"}` 형태로 저장되고 현재 Arc가 `"철검"` 문자열로 같은 아이템을 획득하면, `"{'name': '철검'}" != "철검"`이라 CRITICAL 중복 검출이 누락된다.
- **영향**: Stage2에서 REJECT되어야 할 중복 획득 Arc가 PASS로 넘어가며 연속성 무결성이 깨진다.
- **수정 제안**: `_pre_items` 구축 시 dict를 `name/item` 기준으로 정규화하고, 비교 전에 양쪽을 동일 정규화 함수로 변환한다.

### [J-2] pre_collected_grants 경로에서 수여물 타입 정규화가 생략되어 중복 수여 CRITICAL 검사가 우회됨 — HIGH
- **위치**: `modules/domain/agents/four_phase_arc_generator.py:208`, `modules/domain/agents/four_phase_arc_generator.py:386`, `modules/domain/agents/unified_arc_validator.py:389`, `modules/domain/agents/unified_arc_validator.py:401`
- **코드 인용**:
```python
# four_phase_arc_generator.py
_grt = _prev.get("state_constraints", {}).get("grants_received", [])
if isinstance(_grt, list):
    _pre_grants.update((str(g) if isinstance(g, dict) else g).strip() for g in _grt if g)
...
verdict, validation_result = self.validator.validate(..., pre_collected_grants=_pre_grants, ...)
```
```python
# unified_arc_validator.py
if pre_collected_grants is not None:
    prev_grants = pre_collected_grants
...
grant_str = grant.strip() if isinstance(grant, str) else str(grant)
if grant_str in prev_grants:
```
- **현상**: 수여물도 최적화 경로에서는 dict/str 혼합 정규화가 생략되고 raw 문자열 비교로만 판정된다.
- **재현 시나리오**: 이전 Arc 수여물이 dict 구조(`{"name": "지휘권"}`)이고 현재 Arc가 `"지휘권"` 문자열인 경우, 동일 수여물이어도 매칭 실패로 중복이 감지되지 않는다.
- **영향**: 수여물 중복 방지가 깨져 권한/직위 재수여 같은 CRITICAL 연속성 위반이 통과될 수 있다.
- **수정 제안**: `pre_collected_grants`도 아이템과 동일하게 canonical name 추출 함수를 통일 적용한다.

## 비고
- `modules/domain/agents/analyst.py`의 Arc 생성 경로는 파일 주석/호출 구조상 레거시 fallback 성격이 명시되어 있어, 이번 라운드에서는 활성 경로 결함으로 확정하지 않음.
- `modules/domain/agents/block_enricher.py`, `modules/domain/agents/arc_corrector.py`는 파일 내부 취약 지점은 있으나, 본 라운드에서 프로덕션 호출 경로를 추가 확인하지 못한 항목은 확정 이슈로 분류하지 않음.
