# Director 모듈 코드 점검 이슈 리포트

> **스캔 범위**: `modules/domain/agents/director*.py` (7개, ~4,003 LOC) + `modules/core/pre_director*.py` (4개, ~1,665 LOC)
> **총 코드량**: ~5,668 LOC · **발견 이슈**: 12건

---

## 이슈 요약 테이블

| # | 심각도 | 파일 | 라인 | 제목 |
|---|--------|------|------|------|
| 1 | 🔴 Critical | `director_auditor.py` | 322-675 | `audit_manuscript()` 354줄 God Method |
| 2 | 🟡 Medium | `director_auditor.py` | 101-188 | `assess_character_logic()` 인라인 프롬프트 50줄 |
| 3 | 🟡 Medium | `director_continuity.py` | 41-114 | `validate_entity_consistency()` 인라인 프롬프트 44줄 |
| 4 | 🟡 Medium | `director_continuity.py` | 338-558 | 충돌 검사 메서드 3개 간 중복 로직 |
| 5 | 🟡 Medium | `director_ensemble.py` | 111-142, 481-503 | 인라인 프롬프트 2개 (비교 선택, 긴급 검토) |
| 6 | 🟡 Medium | `director_auditor.py` | 849 | `concurrent.futures` 함수 내부 import |
| 7 | 🟡 Medium | `director.py` | 10-16 | 프롬프트 이중 re-export (3곳에서 중복 참조) |
| 8 | 🟢 Minor | `director_continuity.py` | 197 | `_validate_blueprint_completeness_v60()` 내부 `import re` |
| 9 | 🟢 Minor | `director_auditor.py` | 817-821 | `_safe_int_score()` 메서드 내부 중복 정의 |
| 10 | 🟢 Minor | `director_grading.py` | 전역 | 매직 넘버 하드코딩 다수 |
| 11 | 🟢 Minor | `pre_director_checklist.py` | 431-444 | 서브모듈 위임 stub 5개 (one-liner 포워딩) |
| 12 | 🟢 Minor | `director.py` | 19-341 | Facade 클래스 25+ 위임 메서드 (thin wrapper 과다) |

---

## 상세 설명

### 🔴 Critical

#### #1 — `audit_manuscript()` 354줄 God Method

**파일**: [`director_auditor.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_auditor.py#L322-L675)

`audit_manuscript()`은 13개 파라미터를 받아 8단계 순차 검증을 수행하는 거대 메서드:

1. 분량 체크 (min/max)
2. Blueprint 완전성 검증
3. Genre-specific validation
4. Character logic assessment
5. Entity consistency check
6. V0128 3-Tier validation
7. Manuscript history conflict check
8. Protagonist config compliance

**문제점**:
- 354줄 단일 메서드 — 단위 테스트 불가능
- 8개 독립 검증 단계가 하나의 오케스트레이션 함수에 결합
- 각 단계의 결과를 `dict`에 누적하면서 조건 분기가 중첩

**리팩터링 제안**:
```python
# 각 단계를 ValidationStep 프로토콜로 분리
class ValidationStep(Protocol):
    def run(self, ctx: AuditContext) -> StepResult: ...

# 오케스트레이터가 단계 리스트를 순회
steps = [LengthCheck(), BlueprintCheck(), GenreCheck(), ...]
for step in steps:
    result = step.run(ctx)
    if result.blocking:
        return result.to_audit_result()
```

---

### 🟡 Medium

#### #2 — `assess_character_logic()` 인라인 프롬프트 50줄

**파일**: [`director_auditor.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_auditor.py#L101-L188)

캐릭터 논리 검증 프롬프트가 Python 코드 안에 f-string으로 50줄 이상 인라인됨.
`director_prompts.py`에 프롬프트를 집중 관리하는 패턴이 이미 있음에도 이 프롬프트는 이관되지 않았음.

---

#### #3 — `validate_entity_consistency()` 인라인 프롬프트 44줄

**파일**: [`director_continuity.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L71-L114)

Entity 명칭 검증 프롬프트가 44줄 f-string으로 인라인됨.
역시 `director_prompts.py`로 이관해야 일관성 유지 가능.

---

#### #4 — 충돌 검사 메서드 3개 간 중복 로직

**파일**: [`director_continuity.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L338-L763)

아래 3개 메서드가 동일한 "CRITICAL 충돌 → CONFLICT, 그 외 → PASS (warnings_only)" 판정 로직을 복제:

| 메서드 | 라인 | 용도 |
|--------|------|------|
| `check_manuscript_history_conflicts()` | 338-443 | 직접 역사 참조 |
| `check_manuscript_history_with_cache()` | 445-558 | 캐시 기반 역사 |
| `check_manuscript_continuity_with_cache()` | 664-763 | 캐시 기반 연속성 |

**중복 패턴** (각 메서드에 동일하게 반복):
```python
critical_count = sum(1 for c in conflicts if isinstance(c, dict) and c.get("severity") == "CRITICAL")
if decision == "CONFLICT" and critical_count > 0:
    return {"decision": "CONFLICT", "conflicts": conflicts, ...}
else:
    return {"decision": "PASS", "conflicts": conflicts, "warnings_only": True, ...}
```

**리팩터링 제안**: `_classify_conflict_result(decision, conflicts)` 헬퍼 메서드로 추출.

---

#### #5 — 인라인 프롬프트 2개 (Ensemble / Quick Judge)

**파일**: [`director_ensemble.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L111-L142)

- `compare_and_select_blueprint()` L111-142: 32줄 비교 선택 프롬프트
- `quick_judge_single()` L481-503: 22줄 긴급 검토 프롬프트

두 프롬프트 모두 `director_prompts.py`에 등록하지 않고 코드에 직접 포함됨.
`select_and_judge_ensemble()`은 이미 `PromptLoader`를 사용하므로 일관성 위반.

---

#### #6 — `concurrent.futures` 함수 내부 import

**파일**: [`director_auditor.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_auditor.py#L849-L850)

```python
# L849-850 (함수 내부)
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError
```

`_strategic_audit_with_self_consistency()` 호출 시마다 import가 재실행됨.
표준 라이브러리이므로 파일 상단으로 이동해도 부하 없음.

---

#### #7 — 프롬프트 이중 re-export

**파일**: [`director.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director.py#L10-L16)

```python
# L10-16
from .director_prompts import ENSEMBLE_SELECTION_PROMPT as _ENSEMBLE_PROMPT
from .director_prompts import MANUSCRIPT_HISTORY_CONFLICT_PROMPT as _HISTORY_CONFLICT_PROMPT

ENSEMBLE_SELECTION_PROMPT = _ENSEMBLE_PROMPT        # 모듈 레벨 re-export
# ...
class Director:
    ENSEMBLE_SELECTION_PROMPT = _ENSEMBLE_PROMPT     # 클래스 레벨 re-export (L248)
```

동일 프롬프트가 3곳에서 참조됨:
1. `director_prompts.py` (원본)
2. `director.py` 모듈 레벨 상수
3. `Director` 클래스 속성

실제 사용은 `PromptLoader`를 통하므로 L10-16, L248의 re-export는 불필요한 레거시.

---

### 🟢 Minor

#### #8 — `_validate_blueprint_completeness_v60()` 내부 `import re`

**파일**: [`director_continuity.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_continuity.py#L197)

파일 상단에 이미 `import re`가 없으나, L8에 `import json`만 있고 `re`는 메서드 최초 호출 시 import됨.
→ 파일 상단 import 영역에 `import re` 추가 권장.

---

#### #9 — `_safe_int_score()` 중복 정의

**파일**: [`director_auditor.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_auditor.py#L817-L821)

`_strategic_audit_with_self_consistency()` 내부에 `_safe_int_score()`가 로컬 함수로 정의됨.
`director_ensemble.py`의 모듈 레벨 `_safe_int()`과 동일한 역할.
→ 공통 유틸리티로 통합 가능.

---

#### #10 — 매직 넘버 하드코딩 (`director_grading.py`)

**파일**: [`director_grading.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director_grading.py)

등급 기준선, 가중치, 보너스/감점 수치 등이 코드 전체에 하드코딩:
- `base_pass_threshold = 60`
- 가중치 딕셔너리 `QUALITY_WEIGHTS`
- Adaptive threshold 계산의 `± 5`, `× 0.8` 등

현재 `threshold_helper.py`를 통한 외부 설정이 가능하나 일부 값만 적용됨.
→ 모든 임계값을 `threshold_helper` 또는 설정 파일로 일원화 권장.

---

#### #11 — Pre-Director stub 포워딩 5개

**파일**: [`pre_director_checklist.py`](file:///c:/Users/User/Desktop/글도비/modules/core/pre_director_checklist.py#L431-L444)

```python
def _check_narrative_flow(self, manuscript, context):
    ...  # → self.narrative_checker._check_narrative_flow(...)
def _check_npc_behavior_jump(self, manuscript, context):
    ...  # → self.narrative_checker._check_npc_behavior_jump(...)
```

5개 메서드가 서브모듈로의 1줄 포워딩만 수행. V64 분해 시 생성된 호환성 레이어.
호출부가 이미 서브모듈 직접 참조로 전환된 경우 제거 가능.

---

#### #12 — Facade 클래스 thin wrapper 과다

**파일**: [`director.py`](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/director.py#L19-L341)

`Director` 클래스의 341줄 중 ~200줄이 아래 패턴의 위임 메서드:
```python
def method_name(self, ...):
    """위임 → SubModule"""
    return self._sub_module.method_name(...)
```

25개 이상의 thin wrapper가 존재. V64 분해 과도기에서 발생한 호환성 레이어.
**인터페이스 안정화 후 `__getattr__` 위임 또는 직접 참조로 전환 고려**.

---

## 아키텍처 관찰 (긍정적)

| 항목 | 설명 |
|------|------|
| **V64 God Object 분해** | Director → 5개 전문 클래스 분리 완료. 책임 분리 양호. |
| **Pre-Director 2-Layer 방어** | Python 기반 사전 체크 → LLM 기반 심층 검증 구조. 비용 절감 효과적. |
| **Self-Consistency 투표** | 전략 감사에 3회 투표 + 다수결. LLM 환각 방어에 효과적. |
| **Adaptive Threshold** | Arc 위치, 재시도 횟수에 따른 동적 기준선 조정. |
| **PromptLoader 도입** | 일부 프롬프트(`ENSEMBLE_SELECTION`, `MANUSCRIPT_HISTORY_CONFLICT`)가 외부 파일로 분리. |
| **캐싱 전략** | Manuscript/Blueprint 컨텍스트 캐싱으로 LLM 비용 절감. |
