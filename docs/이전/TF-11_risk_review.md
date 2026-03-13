# TF-11 구현 리스크 검토

> 작성일: 2026-02-24
> 근거: base_agent.py, arc_ensemble.py, four_phase_arc_generator.py, chief_writer.py, blueprint_ensemble.py, models/arc.py, models/manuscript.py 코드 실독 기반

---

## 발견된 엣지 케이스 [심각도 + 근거 코드]

### EC-1. `_ask_with_cached_context()` 경로에서 게이트웨이 우회 [HIGH]

**근거 코드**: `base_agent.py` L1273-1342

`_ask_with_cached_context()`는 `ask()`와 완전히 별개의 경로다. 이 메서드는 `str`을 반환하며, 호출자가 직접 `_extract_json_robust()`를 호출한다. TF-11 설계(Section 3-2-B)는 Gateway를 `_extract_json_robust()` 이후에 삽입하라고 하지만, **삽입 지점이 호출자(에이전트) 쪽이므로 두 경로가 동일하게 처리되려면 각 호출자에서 경로별 1줄씩 추가해야 한다**.

실제 코드를 보면:

- **ArcEnsemble** (`arc_ensemble.py` L474-483): `_ask_with_cached_context()` -> str -> `_extract_json_robust()` (L483). Gateway 삽입 1곳.
- **BlueprintEnsemble** (`blueprint_ensemble.py` L428-435): `_ask_with_cached_context()` -> str -> `_extract_json_robust()` (L435). Gateway 삽입 1곳.
- **ChiefWriter** (`chief_writer.py` L430-454): 분기 존재 -- `cache_name`이 있으면 `_ask_with_cached_context()` (L430), 없으면 `ask()` (L445). **두 경로 모두 L454의 `_extract_json_robust()`를 거치므로** L454 이후에 1줄 추가로 양쪽 모두 커버 가능.

**결론**: ChiefWriter는 문제 없으나, ArcEnsemble/BlueprintEnsemble은 `_ask_with_cached_context()` 전용 경로만 사용하므로 TF-11이 "각 파일 1줄 추가"로 표현한 것은 정확하다. 다만, **`_ask_with_cached_context()`가 캐시 실패 시 내부에서 `self.ask()`를 호출하는 폴백 경로**(L1296-1297, L1341-1342)가 있는데, 이때 `ask()`의 반환값은 역시 `str`이므로 호출자의 `_extract_json_robust()` + Gateway 경로를 동일하게 탄다. **누락 경로 없음. 단, 설계 문서에서 이 폴백 경로를 명시적으로 언급하지 않은 점은 보완 필요.**

---

### EC-2. ASP(Adversarial Self-Play) 경로의 완전한 게이트웨이 우회 [HIGH]

**근거 코드**: `four_phase_arc_generator.py` L355-381 (generate() 내부), L628-655 (patch_arc_with_feedback() 내부)

ASP 경로에서는 `_extract_json_robust()`를 직접 호출하여 Arc를 교체한다:

```python
# L370-377
_asp_arc = self._extract_json_robust(_asp_output)
if not isinstance(_asp_arc, dict) or not _asp_arc:
    _asp_arc = json.loads(_asp_output)
if isinstance(_asp_arc, dict) and _asp_arc.get("tactical_doc"):
    best_arc = _asp_arc  # Gateway 없이 Arc 교체!
```

이 코드는 **`_ensure_required_fields()`도, Pydantic 검증도, Gateway도 거치지 않고** 바로 `best_arc`를 덮어쓴다. ASP가 `tactical_doc`은 반환하지만 `arc_no`/`ep_start`/`ep_end`/`state_constraints` 등 필수 필드가 누락된 dict를 반환하면, 이후 Phase 3(Validate)에서 잡힐 수 있으나, `patch_arc_with_feedback()` 내부의 ASP (L628-655)는 **Phase 3 PASS 이후에 실행**되므로 검증을 완전히 우회한다.

**심각도**: HIGH -- Patch Mode + ASP 조합에서 검증 없는 Arc가 파이프라인 최종 출력이 될 수 있다.

**TF-11 설계의 간과**: TF-11은 B1(ArcEnsemble)과 B24(Stage2Preflight)만 ASP 관련 경계로 식별했으나, `FourPhaseArcGenerator` 내부의 2곳 ASP `_extract_json_robust()` 호출(L370, L644)은 경계 맵에 포함되지 않았다.

---

### EC-3. `_ensure_required_fields()`와 Gateway 이중 기본값 주입 [MEDIUM]

**근거 코드**: `arc_ensemble.py` L602-665, `modules/models/arc.py` L163-203

`_ensure_required_fields()`는 40줄에 걸쳐 다음 방어를 수행한다:
- `arc_no`, `ep_start`, `ep_end`, `ep_count` 주입 (L604-611)
- `state_constraints` 구조 강제 (L614-620)
- `joint_docs` 기본값 (L622-623)
- `status_shadow` 기본값 (L625-630)
- `state_changes` 하위 필드 12개 보장 (L633-663)

ArcData Pydantic 모델은 `state_constraints: dict = Field(default_factory=dict)` 등 단순 빈 dict 기본값을 사용한다. `_ensure_required_fields()`는 `state_constraints` 내부의 `arc_start_state`, `items_acquired` 등 2-depth 구조를 보장하지만 ArcData 모델은 `dict` 타입만 선언하여 내부 구조를 검증하지 않는다.

**충돌 시나리오**: Gateway(`ArcData.model_validate() -> model_dump()`)가 먼저 실행되면 `state_constraints`가 빈 `{}`로 설정된 후, `_ensure_required_fields()`가 다시 구조를 채운다. 반대 순서(현재 코드: L489에서 `_ensure_required_fields` 후 반환)면 Gateway가 이미 채워진 구조를 model_dump()로 재직렬화하는데, `extra="allow"`이므로 추가 키는 보존된다.

**실질 위험**: 낮음 -- 실행 순서가 `_extract_json_robust() -> _normalize_output() -> _ensure_required_fields()`이면 중복이지만 충돌은 아니다. 단, **두 레이어의 기본값이 불일치하면 문제가 된다**. 예: `_ensure_required_fields()`는 `"internal_energy_loss": "0%"`를 설정하지만, ArcData 모델의 `StatusShadow`에는 `internal_energy_loss: str = ""`이 기본값이다. Gateway가 먼저 `""`를 설정하고 `_ensure_required_fields()`가 `"0%"`로 덮어쓰면 문제 없지만, **로직 의도가 불투명해진다**.

**권장**: Gateway 적용 시 `_ensure_required_fields()` 실행 순서를 명확히 문서화하고, 중복되는 기본값 주입 로직은 장기적으로 통합 검토.

---

### EC-4. `_extract_json_robust()` 평탄화 엔진이 ArcData 모델을 파괴하는 구체적 시나리오 [HIGH]

**근거 코드**: `base_agent.py` L1068-1120 (process_node 재귀 평탄화)

TF-11 설계는 R1(평탄화 엔진 충돌)을 HIGH로 식별했으나, 구체적 파괴 시나리오를 제시하지 않았다. 실제 코드를 분석하면:

`process_node()`는 **모든 JSON을 재귀적으로 순회하며 단일 flat dict로 평탄화**한다 (L1070-1115). 핵심 문제:

```python
# L1107-1112
clean_k = str(k).strip("'\" ")
if clean_k not in final_dict or val is not None:
    final_dict[clean_k] = val
```

이 코드는 `state_constraints.arc_start_state.location = "무림맹"`과 최상위 `location = "다른 곳"`이 있으면 **나중에 순회된 값이 이전 값을 덮어쓴다**. `ArcData` 모델은 `state_constraints: dict` 타입이므로, 평탄화된 결과에서 `state_constraints` 키 자체가 중첩 dict가 아니라 마지막으로 만난 값(아마 None 또는 빈 dict)이 될 수 있다.

**그런데 실제 발동 빈도는?**: `json.loads()`가 L1033에서 성공하면 `data`가 정상 dict이고, 그 후 L1117에서 `process_node(data)`가 호출되어 **항상 평탄화가 실행된다**. 이것은 TF-11 설계의 가정("평탄화가 발동하지 않는 정상 경로(L1033 json.loads 성공)")과 모순된다.

**즉, TF-11 설계의 R1 완화 방안이 무효하다.** JSON이 정상 파싱되어도 `process_node()`는 항상 실행되어 중첩 구조를 파괴한다. Gateway에 전달되는 dict는 이미 평탄화된 상태이므로, ArcData Pydantic 모델의 중첩 필드(`state_constraints` 내부의 `arc_start_state` 등)는 검증할 수 없다.

**심각도**: HIGH -- R1 완화 방안의 전제가 틀렸다. 실제로는 모든 `_extract_json_robust()` 호출에서 평탄화가 발생하며, Gateway는 이미 평탄화된 dict를 받게 된다.

---

### EC-5. `schema_hint`가 str인데 설계 문서 코드 예시에서 Type 클래스를 사용 [LOW]

**근거 코드**: TF-11 설계 Section 3-2-C

설계 문서의 API 시그니처는 `schema_hint: str = None`이지만, Section 0(배경)에서 `_normalize_output(raw, schema_hint=ArcData)` 같은 패턴을 언급한다. `ArcData`는 Pydantic 모델 클래스(type)인데 `schema_hint`는 str이다. 이 불일치는 혼란을 유발할 수 있다.

**실질 위험**: 코드 예시(Section 3-3)에서는 `schema_hint="arc"`(str)을 사용하므로 정합. Section 0의 `schema_hint=ArcData`는 설명용 예시이며 실제 API가 아님. 그러나 개발자가 `_normalize_output(result, schema_hint=ArcData)`처럼 호출하면 `_SCHEMA_REGISTRY.get(ArcData)`는 None을 반환하고 패스스루된다. **게이트웨이가 조용히 무효화되는 사일런트 바이패스**.

---

### EC-6. ChiefWriter 후처리 체인과 Gateway의 실행 순서 충돌 [MEDIUM]

**근거 코드**: `chief_writer.py` L451-472

ChiefWriter의 `_generate_single_candidate()`는 다음 순서로 후처리한다:
1. `sanitize_leakage(response)` -- str 처리 (L452)
2. `_extract_json_robust(response)` -- dict 변환 (L454)
3. `isinstance` + `parsing_error` 체크 (L456)
4. `content` 타입 강제 변환 (L460-472) -- str/list/dict 분기
5. `quality_gate.apply_self_critique()` (L482-484)
6. Self-Critique 결과에서 content 재추출 (L487-505)
7. 최종 dict 조립 (L507-519)

**Gateway 삽입 시점 문제**: TF-11은 L454 직후(step 2와 3 사이)에 Gateway를 삽입하라고 제안한다. 그러나 Gateway의 `ManuscriptCandidate` 모델은 `manuscript: str = ""`을 기대하는데, L454 시점의 dict에는 `content` 키가 있지 `manuscript` 키는 없다. LLM 반환값은 `{"content": "본문...", "title": "...", "state_updates": {...}}`이고, `manuscript`로의 변환은 L507-511에서 일어난다.

**즉, Gateway의 ManuscriptCandidate 모델은 L454 시점의 dict와 필드명이 불일치한다.** `content` <-> `manuscript` 매핑이 필요한데, 현재 ManuscriptCandidate 모델에는 이 변환 로직이 없다.

**두 번째 문제**: L382에서 이미 `validate_manuscript_candidate()`가 호출된다:
```python
candidates = [validate_manuscript_candidate(c) for c in candidates]
```
이것은 `_generate_single_candidate()` 반환 후, 최종 dict에 적용된다. Gateway를 L454에 추가하면 **LLM 출력 dict에 1번, 최종 조립 dict에 1번, 총 2번 Pydantic 검증**이 실행되며, 두 번째 검증만이 올바른 스키마(`manuscript` 키 포함)와 매칭된다.

---

### EC-7. `model_dump()` 후 `_ensemble_meta` 등 메타데이터 키 보존 여부 [LOW]

**근거 코드**: `arc_ensemble.py` L297 (`best["_ensemble_meta"] = ensemble_meta`)

ArcEnsemble은 반환 전에 `_ensemble_meta`, `_strategy`, `_score` 등 언더스코어 접두 메타데이터를 주입한다. `_strategy`/`_score`는 L300-303에서 제거되지만, `_ensemble_meta`는 유지된다.

ArcData 모델은 `extra="allow"`이므로 `_ensemble_meta`는 `model_validate()` 시 보존되고, `model_dump()` 시에도 출력된다 (Pydantic v2 기본 동작). **문제 없음.**

단, `by_alias=True`를 사용하면 `RelationshipChange.from_state` (alias="from")이 출력 키명이 변경될 수 있다. TF-11 설계에서 `model_dump()` 호출 시 옵션을 명시하지 않았으므로, 기본 동작(alias 미사용)으로 진행하면 안전하다.

---

## TF-11이 간과한 위험

### 1. `_extract_json_robust()` 평탄화가 항상 실행되는 사실 (EC-4 상세)

TF-11 설계의 R1 완화 방안은 "평탄화가 발동하지 않는 정상 경로(L1033 json.loads 성공)에서만 Pydantic 적용"이라고 기술했으나, 코드를 보면 **json.loads 성공 후에도 L1117에서 process_node(data)가 항상 호출**된다. 정상 파싱 경로와 평탄화 경로는 분리되지 않는다. Gateway가 받는 dict는 항상 평탄화된 상태다.

이것은 근본적 설계 전제의 오류다. 해결 방안:
- **옵션 A**: Gateway를 `_extract_json_robust()` 내부가 아닌 `json.loads()` 성공 직후(L1033), 평탄화 이전에 삽입
- **옵션 B**: `_extract_json_robust()`에 `skip_flatten=True` 파라미터를 추가하고, Gateway 적용 경계에서만 평탄화 스킵
- **옵션 C**: 평탄화를 opt-in으로 전환 (가장 큰 변경이지만 가장 근본적)

### 2. FourPhaseArcGenerator 내부 ASP 경로 2곳 누락 (EC-2 상세)

TF-11 경계 맵(Section 1-C)에 `four_phase_arc_generator.py`의 `_extract_json_robust()` 호출이 없다. 실제로는 L370과 L644에서 `self._extract_json_robust()`를 호출하며, 특히 L644(patch 경로 ASP)는 Phase 3 PASS 이후에 실행되므로 검증 없는 Arc가 최종 출력이 된다.

### 3. ChiefWriter `content` <-> `manuscript` 필드명 불일치 (EC-6 상세)

LLM은 `content` 키를 반환하고, ManuscriptCandidate 모델은 `manuscript` 키를 기대한다. L454 시점에서 Gateway를 적용하면 `manuscript: str = ""`(빈 문자열)로 기본값이 채워지고 `content`는 extra 필드로 보존되지만, `manuscript` 필드를 사용하는 downstream 코드가 빈 문자열을 받게 된다.

### 4. `~120줄` 수정 범위 과소 추정

TF-11은 Phase 0-3까지 ~120줄로 추정했다. 그러나 다음 추가 작업이 필요하다:
- EC-2의 ASP 경로 2곳: +4줄 (FourPhaseArcGenerator)
- EC-4의 평탄화 문제 해결: 최소 +20줄 (옵션 B 기준)
- EC-6의 ManuscriptCandidate 모델 수정 또는 alias 추가: +5줄
- 테스트에서 평탄화 영향 검증: +40줄 이상

실제 예상: ~190줄 (Phase 0-3), 전체 ~360줄.

### 5. ThreadPoolExecutor 환경에서의 안전성 (질문 관점 3번)

Pydantic v2의 `model_validate()`와 `model_dump()`는 **내부적으로 Rust 바이너리(pydantic-core)를 호출하며, GIL 해제 구간이 있을 수 있다**. 그러나 Pydantic 공식 문서에 따르면 모델 인스턴스 생성/직렬화는 thread-safe하다 (각 호출이 독립적인 객체를 생성).

실제 위험은 Pydantic이 아니라 **`_normalize_output()`이 `raw` dict를 in-place 수정하는 경우**다. TF-11의 `_normalize_validation_result()`(Section 3-2-D)와 `_normalize_director_decision()`은 `raw` dict를 직접 수정한다:
```python
raw["verdict"] = raw["decision"]  # in-place 수정
raw["issues"] = []                # in-place 수정
```

ThreadPoolExecutor에서 같은 dict 객체가 여러 스레드에서 공유되지는 않으므로(각 LLM 호출이 독립적인 response를 반환), 실제 race condition 위험은 낮다. 그러나 **방어적 프로그래밍 원칙상 `raw.copy()`를 사용하여 새 dict를 반환하는 것이 안전하다**.

---

## 테스트 보완 필요

### T-1. 평탄화 후 Gateway 검증 테스트 [필수]

```
Given: LLM이 중첩 JSON 반환 (state_constraints.arc_start_state.location 포함)
When: _extract_json_robust()가 평탄화 실행
Then: 평탄화된 dict에서 ArcData.model_validate()가 어떤 결과를 반환하는지 검증
Expected: state_constraints가 빈 dict가 되거나, location이 최상위로 승격
```

### T-2. ASP 경로 Gateway 우회 테스트 [필수]

```
Given: ASP가 tactical_doc만 있는 불완전한 Arc 반환
When: patch_arc_with_feedback() L628-655 실행 (Phase 3 PASS 후)
Then: best_arc가 arc_no, ep_start, ep_end 없이 반환되는지 확인
Expected: 필수 필드 누락 Arc가 최종 출력으로 나감
```

### T-3. ManuscriptCandidate 필드명 불일치 테스트 [필수]

```
Given: LLM 반환 {"content": "본문", "title": "제목", "state_updates": {...}}
When: ManuscriptCandidate.model_validate() 실행
Then: manuscript 필드가 ""(빈 문자열), content가 extra 필드로 보존되는지 확인
Expected: downstream에서 manuscript 대신 content를 사용하는 코드가 깨짐
```

### T-4. `_normalize_validation_result()` verdict/decision 양방향 매핑 [권장]

```
Given: LLM이 {"verdict": "PASS"} 반환 (decision 키 없음)
When: _normalize_director_decision() 실행 (잘못된 hint)
Then: decision = "REJECT"로 강제 (fail-closed)
Expected: verdict="PASS"인데 decision="REJECT"로 충돌 발생
```

### T-5. schema_hint 오타/Type 클래스 전달 시 사일런트 바이패스 [권장]

```
Given: schema_hint=ArcData (str이 아닌 Type 클래스)
When: _SCHEMA_REGISTRY.get(ArcData) 실행
Then: None 반환 -> 패스스루 (Gateway 무효화)
Expected: 로그 경고 없이 조용히 우회
```

### T-6. extra="allow" + model_dump() 키 보존 [권장]

```
Given: ArcData에 _ensemble_meta, repaired 등 미정의 키 존재
When: ArcData.model_validate(raw).model_dump() 실행
Then: 미정의 키가 보존되는지 확인
Expected: Pydantic v2 기본 동작으로 보존되지만, 옵션에 따라 달라질 수 있음
```

---

## 구현 전 선결 조건

### P-1. `_extract_json_robust()` 평탄화 동작 재확인 [BLOCKER]

EC-4에서 확인한 바와 같이, `json.loads()` 성공 후에도 `process_node()`가 항상 실행된다. Gateway가 유의미하려면 **평탄화 이전의 원본 dict**에 Pydantic 검증을 적용해야 한다. 이 문제를 해결하지 않으면 Gateway는 이미 파괴된 구조에 검증을 적용하게 되어 효과가 거의 없다.

선택지:
1. Gateway를 `_extract_json_robust()` 내부 L1033 직후(json.loads 성공 직후)에 삽입 -> 평탄화 이전에 타입 검증
2. 평탄화 로직에 `skip_keys` 파라미터를 추가하여 핵심 중첩 필드를 보존
3. P0 경계(ArcEnsemble, ChiefWriter)에서 `_extract_json_robust()` 대신 `json.loads()` + Gateway 직접 호출

**권장**: 옵션 1. `_extract_json_robust()` 내부에서 `json.loads` 성공 시 Gateway를 적용하고, 평탄화는 Gateway 실패 시 폴백으로만 동작하도록 변경.

### P-2. ManuscriptCandidate 모델의 `content` 필드 추가 [BLOCKER for Phase 1]

LLM 반환 dict의 `content` 키와 ManuscriptCandidate의 `manuscript` 키가 불일치한다. Gateway 적용 전에 모델을 수정해야 한다:
```python
class ManuscriptCandidate(BaseModel):
    content: str = ""        # LLM 반환 키 (추가 필요)
    manuscript: str = ""     # 최종 조립 키
```

또는 `model_validator(mode="before")`로 `content` -> `manuscript` 매핑을 추가.

### P-3. ASP 경로 2곳을 경계 맵에 추가 [SHOULD]

`four_phase_arc_generator.py` L370, L644의 `_extract_json_robust()` 호출을 TF-11 경계 맵에 B26, B27로 추가하고, Gateway 적용 대상으로 포함.

### P-4. `_normalize_validation_result()`와 `_normalize_director_decision()`의 dict 복사 [SHOULD]

in-place 수정 대신 `result = dict(raw)` 복사 후 수정하여 thread-safety 보장.

---

## 결론: 추가 설계 필요

TF-11 설계는 문제 정의(Section 0-2)와 점진적 도입 전략(Section 3-3)이 건전하다. 그러나 다음 3가지 설계 전제 오류로 인해 **현재 상태로는 바로 구현할 수 없다**:

1. **R1 완화 방안의 전제 오류** (EC-4): `_extract_json_robust()` 내부에서 `json.loads` 성공 후에도 평탄화가 항상 실행된다. "정상 경로에서만 Pydantic 적용" 방안이 성립하지 않는다. Gateway 삽입 지점을 재설계해야 한다.

2. **ASP 경로 누락** (EC-2): `FourPhaseArcGenerator` 내부 2곳의 `_extract_json_robust()` 호출이 경계 맵에서 빠졌다. 특히 patch 경로 ASP는 Phase 3 PASS 이후에 실행되어 검증 없는 Arc가 최종 출력될 수 있다.

3. **ManuscriptCandidate 필드명 불일치** (EC-6): LLM 반환값의 `content` 키와 모델의 `manuscript` 키가 다르다. Gateway 적용 전에 모델 수정이 필요하다.

**권장 진행 순서**:

1. P-1 해결: `_extract_json_robust()` 내부 Gateway 삽입 지점 재설계 (평탄화 문제)
2. P-2 해결: ManuscriptCandidate 모델에 `content` 필드 추가 또는 alias 매핑
3. P-3 해결: ASP 경로를 경계 맵에 추가
4. Phase 0 구현 (base_agent.py Gateway 인프라)
5. Phase 1 구현 (P0 경계 적용) + T-1~T-6 테스트
6. 기존 2,537개 테스트 그린 확인 후 Phase 2-3 진행

P-1~P-3 해결 후 TF-11 설계를 보정하면 안전하게 진행 가능하다.
