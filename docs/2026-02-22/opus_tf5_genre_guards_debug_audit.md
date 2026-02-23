# Opus TF-5: Genre Guards Debug Audit (TF-H)

> 감사일: 2026-02-23  
> 범위: `modules/core/genre_guards/base_guard.py`, `modules/core/genre_guards/wuxia_guard.py`, `modules/core/genre_guards/hunter_guard.py`, `modules/core/genre_guards/investment_guard.py`, `modules/core/genre_guards/alt_history_guard.py`, `modules/core/genre_guards/composer_guard.py`, `modules/core/genre_guards/cooking_guard.py`, `modules/core/genre_guards/medical_guard.py`, `modules/core/genre_guards/sports_guard.py`, `modules/core/genre_guards/actor_guard.py`, `modules/core/genre_guards/fantasy_guard.py`, `modules/core/genre_guards/style_guard.py`, `modules/core/genre_guards/work_guard.py`, `modules/core/genre_guards/__init__.py`  
> 호출 경로 확인: `modules/validation/validation_orchestrator.py` → `modules/validation/consistency_validator.py` → `BaseGuard` 검증 메서드

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 0 |

### [H-1] 상태-행동 정당화 판정이 원고 전체 전역 매칭으로 처리되어 불가능 행동을 오검증 PASS시킴 — HIGH
- **위치**: `modules/core/genre_guards/base_guard.py:348`, `modules/core/genre_guards/base_guard.py:351`, `modules/core/genre_guards/base_guard.py:353`, `modules/validation/consistency_validator.py:114`, `modules/validation/consistency_validator.py:292`, `modules/validation/validation_orchestrator.py:214`
- **코드 인용**:
```python
# base_guard.py
matches = re.findall(pattern, manuscript)
if matches:
    has_justification = any(re.search(jp, manuscript) for jp in justifications)
    if not has_justification:
        violations.append(...)
```
```python
# consistency_validator.py
state_check = self._check_state_action_consistency(manuscript, actual_truth)
...
return self.guard.check_state_action_consistency(manuscript, current_state)
```
- **현상**: 불가능 행동 패턴이 매칭되어도, 원고 아무 위치에나 정당화 문구가 1회 존재하면 해당 패턴 위반이 통째로 제거된다.
- **재현 시나리오**: 1문단에서 "코치 지도"가 언급되고, 10문단에서 부상 상태의 금지 행동이 발생하면 실제 행동 근거가 없어도 `has_justification=True`로 처리되어 위반 미기록.
- **영향**: Consistency 단계의 unjustifiable 위반이 누락되어 REJECT되어야 할 원고가 PASS/경고로 통과할 수 있다.
- **수정 제안**: 정당화 패턴을 원고 전역이 아니라 `matches`별 근접 윈도우(예: ±120자)에서 평가하고, 매칭 단위로 위반을 산출한다.

### [H-2] 미해결 갈등 검증이 NPC 단위가 아닌 원고 전역 해소 키워드로 판정되어 고구마 위반을 누락함 — MEDIUM
- **위치**: `modules/core/genre_guards/base_guard.py:617`, `modules/core/genre_guards/base_guard.py:646`, `modules/core/genre_guards/base_guard.py:648`, `modules/validation/consistency_validator.py:195`
- **코드 인용**:
```python
# base_guard.py
for npc_name, npc_data in karma_matrix.items():
    ...
    has_resolution_in_manuscript = any(re.search(rp, manuscript) for rp in resolution_patterns)
    if resolved or has_resolution_in_manuscript:
        continue
```
- **현상**: NPC별 루프 안에서 해소 여부를 판단하지만, 해소 패턴 검색은 NPC 무관하게 원고 전역 1회 매칭만으로 true가 된다.
- **재현 시나리오**: A NPC는 복수 완료, B NPC는 적대 상태 유지+동행인 경우, 원고에 "복수" 단어가 있으면 B NPC도 해결된 것으로 간주되어 위반이 사라진다.
- **영향**: unresolved_conflict 경고/점수(`goguma_score`)가 누락되어 카타르시스 결함이 검증 단계에서 지속된다.
- **수정 제안**: 해소 패턴을 `f"{npc_name}.*(해소패턴)|(해소패턴).*{npc_name}"`처럼 NPC 연계 패턴으로 제한한다.

### [H-3] 빌런 반응 검증이 일반 반응 키워드 전역 매칭을 허용해 타 인물 반응을 빌런 반응으로 오인함 — MEDIUM
- **위치**: `modules/core/genre_guards/base_guard.py:793`, `modules/core/genre_guards/base_guard.py:805`, `modules/core/genre_guards/base_guard.py:809`, `modules/core/genre_guards/base_guard.py:814`, `modules/validation/consistency_validator.py:221`
- **코드 인용**:
```python
# base_guard.py
has_response = any(re.search(rp, manuscript) for rp in villain_specific_response)
if not has_response:
    has_response = any(re.search(rp, manuscript) for rp in response_patterns)
...
if villain_mentioned and not has_response:
    violations.append(...)
```
- **현상**: 빌런 특이 반응이 없을 때, 원고의 아무 반응 키워드("분노", "당황" 등)만 있어도 `has_response=True`가 되어 위반이 사라진다.
- **재현 시나리오**: 조연이 분노하는 장면만 있고 빌런은 무반응인 회차에서도, 일반 패턴 매칭으로 빌런 대응이 있었다고 판정된다.
- **영향**: "무능한 빌런 위험" 경고가 누락되어 대립축 긴장도 저하를 검증이 잡아내지 못한다.
- **수정 제안**: 일반 반응 패턴 사용 시에도 빌런명 근접 조건(동일 문장/±N자)을 강제하거나, 빌런 특이 패턴만 유효 반응으로 인정한다.

## 비고
- `modules/core/genre_guards/__init__.py:54-56`의 미지원 장르 `WuxiaGuard` 폴백은 코드 주석(`[ContractR84]`)과 경고 로그가 있어 의도된 호환 동작으로 분류.
- `modules/core/genre_guards/work_guard.py`, `modules/core/genre_guards/style_guard.py`의 래퍼 위임 구조는 필드/메서드 위임이 일관되며, 이번 라운드에서는 직접 결함으로 확정하지 않음.
