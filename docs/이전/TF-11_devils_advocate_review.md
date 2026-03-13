# TF-11 회의론 검토 (Devil's Advocate)

> 작성일: 2026-02-24
> 검토 대상: `docs/TF-11_output_gateway_design.md`
> 검토 방법: 코드 실독 기반 반론 + 대안 분석

---

## 핵심 반론

### 반론 1: ROI 과대 추정 -- 기존 방어 코드가 이미 핵심 경계를 커버한다

TF-11은 "65개 경계 중 Pydantic 적용은 3곳(4.6%)"이라는 통계로 위기감을 조성한다. 그러나 이 통계는 **Pydantic만을 검증으로 인정**하고, 기존의 ad-hoc 방어 코드를 무시한다.

**실제 기존 방어 코드 현황**:

1. **`isinstance(result, dict)` 체크**: 에이전트 파일 21개에서 32회 수행 (`modules/domain/agents/` 전체). 파싱 실패의 1차 방어선이 이미 존재한다.

2. **`parsing_error` 키 체크**: 8개 파일에서 17회 수행. `_extract_json_robust()`의 에러 시그널을 각 호출부가 개별 검사한다.

3. **`tactical_doc` 타입 강제 변환**: 12개 파일에서 32회 `isinstance(tactical_doc, dict)` 또는 유사 체크 수행. `analyst.py` L376-379, `arc_ensemble.py`의 `_safe_tactical_str()` (L667-692, 26줄), `arc_draft_validator.py` L372-373, `blueprint_constraint_compiler.py` L193, L245, `continuity_arc.py` L247-248, `unified_blueprint_validator.py` L198-199 등.

4. **`_ensure_required_fields()` 패턴**: `arc_ensemble.py` L602-665 (64줄)에서 Arc의 필수 필드 6개 + 하위 필드를 빠짐없이 보장한다. `state_constraints`, `joint_docs`, `status_shadow`, `state_changes`의 하위 구조까지 기본값 주입.

5. **ChiefWriter의 수동 타입 강제**: `chief_writer.py` L460-472에서 `content` 필드의 str/list/dict 3가지 타입을 모두 처리한다.

6. **UnifiedArcValidator의 fail-closed 방어**: L553-568에서 파싱 실패 시 REJECT + CRITICAL 이슈를 자체 구성하여 반환한다. Gateway 없이도 안전하다.

**계산**: 65개 경계 중 실제로 **무방비인 경계가 몇 개인가?**

- Pydantic 적용: 3곳 (chief_writer L382, stage2_finalizer L358, three_phase_bp_gen)
- isinstance(dict) + parsing_error 체크: 대부분의 호출부
- _ensure_required_fields: ArcEnsemble
- 수동 타입 강제: ChiefWriter, Analyst 등

TF-11이 P0로 지정한 ArcEnsemble(B1)과 ChiefWriter(B3)는 **이미 가장 두꺼운 방어 코드를 가진 경계**이다. Gateway를 추가하면 기존 방어 코드와 **이중 실행**될 뿐, 새로운 버그를 잡지 못한다.

**근거 코드**:
```
# arc_ensemble.py L482-489 -- 이미 3중 방어
result = self._extract_json_robust(result)        # 1) JSON 파싱
if not isinstance(result, dict) or result.get("parsing_error"):  # 2) 타입+에러 체크
    return None
result = self._ensure_required_fields(result, ...)  # 3) 필수 필드 보장 (64줄)

# chief_writer.py L454-472 -- 이미 4중 방어
data = self._extract_json_robust(response)         # 1) JSON 파싱
if not isinstance(data, dict) or ... data.get("parsing_error"):  # 2) 타입+에러 체크
    return None
# L460-472: content 타입 강제 변환 (str/list/dict)  # 3) 수동 정규화
candidates = [validate_manuscript_candidate(c) ...]  # 4) Pydantic 검증 (L382)
```

Gateway는 이 체인에 5번째 레이어를 추가할 뿐이다.

---

### 반론 2: BaseAgent 비대화는 실질적 문제다 -- "60줄"은 과소추정

TF-11은 R6 리스크에서 "`_normalize_output()`은 얇은 디스패처"라고 주장한다. 그러나 설계문서 자체를 보면:

- `_normalize_output()`: ~15줄
- `_SCHEMA_REGISTRY`: ~10줄
- `_safe_validate()`: ~10줄
- `_normalize_validation_result()`: ~18줄
- `_normalize_director_decision()`: ~17줄

이것만으로 이미 ~70줄이다. 여기에 import문, 로깅, 에러 핸들링, docstring을 추가하면 실질적으로 **80-100줄**이다.

`base_agent.py`는 현재 **1,402줄**이다. 이 파일은 이미:
- `ask()`: L305-671 (367줄)
- `_extract_json_robust()`: L1000-1123 (124줄)
- `_ask_with_cached_context()`: L1273-1342 (70줄)
- `_get_or_create_context_cache()`: L1180-1271 (92줄)
- 키 순환 로직: L160-237 (78줄)

BaseAgent가 "에이전트 기반 클래스"라는 이름과 달리 실질적으로 **API 클라이언트 + JSON 파서 + 캐시 매니저 + 키 순환기 + 네트워크 복원력 엔진**의 역할을 한다. 여기에 "출력 정규화 게이트웨이"까지 추가하면 **6번째 책임**이 된다. 단일 책임 원칙(SRP) 위반이 심화될 뿐이다.

TF-11은 "향후 B-1 패턴으로 별도 모듈 추출 가능"이라고 하지만, B-1 패턴 분할(stage4, chief_writer, stage2 분할) 경험을 보면 각각 **수백 줄의 코드 + 수십 개의 테스트**가 필요했다. "가능하다"와 "할 것이다"는 다르다.

---

### 반론 3: Graceful Degradation은 위험한 자기기만이다

TF-11의 핵심 설계 원칙 중 하나가 "graceful degradation 유지 -- 검증 실패 시 원본 반환"이다. 이것이 문제인 이유:

**현재 Pydantic 적용 3곳이 이미 이 문제를 보여준다**:

```python
# modules/models/arc.py L206-217
def validate_arc(raw: dict) -> dict:
    try:
        arc = ArcData.model_validate(raw)
        return arc.model_dump()
    except Exception as e:
        logger.warning("[Pydantic] Arc 검증 실패 -- 원본 dict 유지: %s", e)
        return raw  # <-- 검증 실패해도 원본 그대로 통과!
```

Gateway의 `_safe_validate()`도 동일한 패턴이다:

```python
def _safe_validate(model_cls, raw: dict) -> dict:
    try:
        return model_cls.model_validate(raw).model_dump()
    except Exception:
        logger.warning("[Gateway] %s 검증 실패 -- 원본 유지", model_cls.__name__)
        return raw  # <-- 동일 패턴
```

이 패턴의 결과:
1. `tactical_doc`이 dict로 오면 -> Pydantic 검증 **성공** (ArcData는 `tactical_doc: str | dict = ""`로 정의, 두 타입 모두 허용)
2. 필수 키 `arc_no`가 없으면 -> Pydantic 검증 **실패** -> 원본 반환 -> downstream에서 KeyError
3. `extra="allow"` 때문에 오타 키(`tacticl_doc`)도 -> Pydantic 검증 **성공**

**Gateway가 실제로 잡을 수 있는 버그 클래스**:
- `arc_no`가 str인데 int가 필요한 경우 -> Pydantic이 자동 변환 (coerce)
- `ep_count`가 누락된 경우 -> `default=5`로 채움
- `state_constraints`가 누락된 경우 -> `default_factory=dict`로 빈 dict

그런데 이 중 첫째는 Python의 duck typing에서 큰 문제가 아니고(`.get()` 패턴에서), 둘째와 셋째는 **`_ensure_required_fields()`가 이미 하는 일**이다.

TF-11 설계문서 스스로도 R2에서 이 문제를 인식하면서 "Phase 5에서 `strict=True` 옵션 추가"라고 미래로 미룬다. 그 Phase 5가 오기 전까지 Gateway는 **"로깅만 하는 비싼 레이어"**에 불과하다.

---

### 반론 4: "~120줄" 추정은 비현실적이다

TF-11의 Phase 0-3 수정량 추정:
- Phase 0: ~60줄 (base_agent.py)
- Phase 1: 2줄 (ArcEnsemble + ChiefWriter)
- Phase 2: 2줄 (BlueprintEnsemble + UnifiedArcValidator)
- Phase 3: ~12줄 (DirectorAuditor 5곳)
- **합계: ~120줄**

이 추정이 무시하는 것들:

1. **Phase 0-T (테스트)**: "~80줄"이라고 하지만 Gateway 자체 테스트 + 각 정규화 함수의 엣지케이스 테스트를 포함하면 **최소 150줄**. Pydantic 모델의 기존 테스트(`test_pydantic_models.py`)와 정합성 확인도 필요하다.

2. **Phase 1-T (회귀 테스트)**: "~40줄"이지만, ArcEnsemble과 ChiefWriter의 기존 테스트에서 Gateway 경유 시 동작 변경 여부를 확인해야 한다. 기존 mock 패턴이 `_extract_json_robust()` 반환값을 직접 제어하는 경우, Gateway 추가로 mock 수정이 필요해진다.

3. **기존 방어 코드와의 중복 정리**: Gateway를 추가하면 기존 `_ensure_required_fields()` 64줄, ChiefWriter의 수동 타입 강제 13줄을 제거할 것인가, 유지할 것인가? 제거하면 추가 변경, 유지하면 이중 실행.

4. **새 Pydantic 모델 작성**: Phase 5에서 `ValidationResult`, `DirectorDecision` 모델 ~60줄 추가. 그러나 `DirectorAuditor`의 5개 `.ask()` 호출이 각각 **다른 스키마**를 기대한다 (TF-11 문서 B6에서 스스로 인정). 단일 `director_decision` 모델로는 불가능하고, 실제로는 3-5개 모델이 필요하다.

5. **평탄화 엔진 경합 처리**: R1 리스크에서 "평탄화가 발동하지 않는 정상 경로에서만 Pydantic 적용"이라고 하는데, 이 분기 로직 자체가 ~20줄 추가. `_extract_json_robust()` 내부에서 `process_node` 진입 여부를 외부에 알려주는 시그널이 현재 없으므로, 반환값에 메타데이터를 추가하거나 별도 플래그가 필요하다.

**현실적 추정**: Phase 0-3 코드 ~120줄 + 테스트 ~250줄 + 기존 코드 조정 ~50줄 = **~420줄**. 문서가 주장하는 것의 3.5배이다.

---

### 반론 5: 더 단순한 대안이 존재한다

#### 대안 A: `_extract_json_robust()` 반환값에 타입 힌트 + TypedDict

Gateway를 도입하지 않고, 기존 `_extract_json_robust()`의 반환 타입을 명시하는 것만으로 IDE 수준의 타입 체크가 가능하다:

```python
class ParsedArc(TypedDict, total=False):
    arc_no: int
    ep_start: int
    ep_end: int
    tactical_doc: str
    # ...

class ParsedResult(TypedDict, total=False):
    parsing_error: bool
    content: str
    # ...
```

이 방식의 장점:
- 런타임 오버헤드 제로
- 기존 코드 무변경
- mypy/pyright로 `.get()` 오남용 감지
- 수정량: 타입 정의 ~50줄 + import 변경 ~20줄

단점:
- 런타임 검증 없음 (하지만 기존 ad-hoc 방어 코드가 이를 커버)

#### 대안 B: `_ensure_required_fields()` 패턴을 표준화

ArcEnsemble의 `_ensure_required_fields()` 64줄이 **이미 Gateway가 하려는 일을 한다**. 이 패턴을 각 에이전트별로 표준화하는 것이 Gateway보다 가볍다:

```python
# 각 에이전트에 자기 출력 스키마의 ensure 메서드 작성
# ArcEnsemble -> _ensure_required_fields (이미 있음)
# ChiefWriter -> _ensure_manuscript_fields (현재 L460-472를 메서드로 추출)
# UnifiedArcValidator -> _ensure_validation_fields (새로 작성, ~15줄)
# DirectorAuditor -> _ensure_decision_fields (새로 작성, ~15줄)
```

이 방식의 장점:
- 각 에이전트가 자기 출력 스키마를 가장 잘 안다 (BaseAgent에 집중하지 않음)
- BaseAgent 비대화 방지
- 기존 코드 패턴과 일관성 유지
- 수정량: 신규 ~60줄 + 기존 코드 리팩터 ~20줄

단점:
- 중앙 집중 관리가 아니므로 적용 누락 가능 (하지만 Gateway도 opt-in 방식이므로 동일)

#### 대안 C: Gemini `response_schema` 확대 적용

현재 `response_schemas.py`에 9개 스키마가 정의되어 있지만 `analyst.py` 1곳에서만 사용된다. 이 스키마를 ArcEnsemble, BlueprintEnsemble의 `ask()` 호출에 적용하면 **LLM 출력 자체가 타입 정합**된다:

```python
# 현재: ask(prompt, temperature=0.5)
# 변경: ask(prompt, temperature=0.5, response_schema=ARC_DESIGN_SCHEMA)
```

이 방식의 장점:
- Python 측 검증 불필요 (API 레벨 강제)
- 수정량: 호출부 1줄 변경 x 5곳 = 5줄
- LLM이 스키마에 맞게 출력하므로 파싱 에러 자체가 감소

단점:
- Gemini API에 종속 (다른 LLM 이식성 감소)
- 동적 키를 가진 스키마에는 제한적 (TF-10에서 확인된 문제)
- 모든 경계에 적합한 스키마가 정의되어 있지 않음

---

## 수용 가능한 부분

TF-11 설계가 완전히 틀린 것은 아니다. 수용할 수 있는 부분:

1. **문제 진단은 정확하다**: 65개 경계에서 타입 검증이 체계적으로 없다는 분석, LLM 출력의 비결정성이 downstream 에러를 유발한다는 진단은 맞다.

2. **경계 전수 조사(Section 1)는 가치 있다**: Tier 1-5 경계 맵은 시스템 이해에 큰 도움이 된다. 이 맵 자체는 Gateway 도입 여부와 무관하게 유지해야 할 자산이다.

3. **TOP 5 우선순위 선정은 타당하다**: ArcEnsemble(B1)과 ChiefWriter(B3)가 가장 높은 리스크인 것은 맞다. 다만 이 두 경계가 이미 가장 두꺼운 방어를 가지고 있다는 사실은 별개의 문제이다.

4. **TF-10 통합 방안은 깔끔하다**: `episode_details: list[dict] = Field(default_factory=list)` 추가는 Gateway와 무관하게 ArcData 모델에 적용 가치가 있다.

5. **R1 리스크(평탄화 충돌) 식별은 중요하다**: `process_node()`가 중첩 dict를 파괴하는 문제는 Gateway와 무관하게 `_extract_json_robust()` 자체의 구조적 결함이다. 이 문제는 별도로 대응해야 한다.

---

## 결론: 수정 후 진행

### 판정 근거

TF-11의 문제 진단은 정확하지만, 제안된 해결책(BaseAgent에 Gateway 메서드 추가)은 **ROI가 낮고, 기존 방어 코드와 중복되며, BaseAgent의 책임을 과도하게 확장**한다.

### 권장 수정 방향

**Gateway를 BaseAgent에 넣지 말고, 3가지 경량 조치를 대신 적용**:

1. **`_ensure_required_fields()` 패턴 표준화** (대안 B)
   - ArcEnsemble의 기존 패턴을 ChiefWriter, UnifiedArcValidator, DirectorAuditor에 복제
   - 각 에이전트가 자기 출력을 보장 (BaseAgent 비대화 방지)
   - 추정 수정량: ~60줄 신규 + ~20줄 리팩터

2. **Gemini `response_schema` 확대 적용** (대안 C)
   - `response_schemas.py`에 이미 정의된 9개 스키마 중 ARC_DESIGN_SCHEMA, BLUEPRINT_SCHEMA를 실제 호출에 적용
   - ArcEnsemble, BlueprintEnsemble의 `ask()` 호출에 `response_schema` 파라미터 추가
   - 추정 수정량: ~5줄

3. **ArcData 모델에 `episode_details` 필드 추가** (TF-10 통합)
   - TF-11의 Section 4 제안을 그대로 적용
   - `episode_details: list[dict] = Field(default_factory=list)`
   - 추정 수정량: 1줄 + 테스트 ~10줄

**이 3가지 조치의 총 수정량**: ~100줄. Gateway의 추정 420줄 대비 **76% 절감**이며, 핵심 리스크(B1 Arc 타입 오류, B3 content 타입 오류)에 대한 방어 효과는 동등하다.

### Gateway가 정당화되는 시점

향후 다음 조건이 충족되면 Gateway 재검토를 권장한다:
- `_extract_json_robust()`의 평탄화 엔진(`process_node`)을 제거하거나 opt-in으로 변경한 후 (R1 리스크 해소)
- BaseAgent에서 캐싱/키순환 로직을 별도 모듈로 분리한 후 (SRP 회복)
- 위 3가지 경량 조치 적용 후에도 타입 관련 프로덕션 버그가 반복될 경우

---

**문서 끝**
