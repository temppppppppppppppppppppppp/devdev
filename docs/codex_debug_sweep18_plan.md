# Debug Sweep 18 — Stale DI + Schema 탈락 + 초기화 오류

## Execution Status (2026-02-17)

- A-1 completed:
  - `modules/core/stage4_orchestrator.py`
    - `ctx` setter에서 lazy 서브모듈 캐시(`_post_processor`, `_context_builder`, `_interview_round`) 무효화 추가.
    - ctx 교체 후 서브모듈이 stale ctx를 잡는 문제 해결.
- A-2 completed:
  - `modules/domain/agents/base_agent.py`
    - quota/rate-limit 폴백 경로의 `fallback_config_params`에 `response_schema` 복사 추가.
- A-3 completed:
  - `modules/core/stage0/style_extractor.py`
    - `StyleGuide.__post_init__` 리스트 필드 판별을 `str(f.type) == "list[str]"`로 수정.
    - 런타임(GenericAlias)과 문자열 어노테이션 환경을 모두 수용.
- A-4 completed:
  - `main_a.py`
    - Stage 2 종료 동기화에 `self._state_tracker_loaded_arcs` write-back 추가.
- B-1 completed:
  - `modules/core/stage2_optimizer.py`
    - `relationship_history` 계산 데드 코드 제거.
- B-2 completed:
  - `modules/domain/agents/state_extractor.py`
    - LLM 추출 실패 시 fallback 경고 로그 추가.
- B-3 completed:
  - `modules/validation/action_scene_evaluator.py`
    - `OUTCOME_KEYWORDS` 중복 `"피"` 제거.

- Added tests:
  - `tests/test_sweep18.py` (신규)
    - Stage4 ctx 교체 시 서브모듈 재생성 검증
    - BaseAgent quota 폴백 시 `response_schema` 유지 검증
    - StyleGuide 리스트 필드 초기화 검증
    - main_a Stage2 loaded_arcs write-back 라인 검증
    - Stage2Optimizer dead-code 호출 제거 검증
    - StateExtractor fallback 경고 로그 검증
    - ActionSceneEvaluator 결과 키워드 중복 없음 검증

- Verification:
  - `python -m pytest tests/test_stage4_orchestrator.py tests/test_stage2_pipeline.py tests/test_genre_guard.py tests/test_sweep18.py -q -x` -> `154 passed`
  - `python -m pytest tests/ -q -p no:capture` -> `1955 passed, 68 xfailed, 1 warning`

## Context

Sweep 17(7건) 완료 후, 5-에이전트 병렬 탐색으로 미탐색 대형 영역 전면 스윕:
stage0(style_extractor, reverse_expander, preset_registry), base_agent, hud_utils, martial_manager,
prompt_builder, stage2_optimizer, state_extractor, vec_memory, action_scene_evaluator,
main_a DI 주입 포인트, Stage2/4 Context 슬롯 매칭.
수동 코드 검증으로 **확인된 실제 버그 7건** 정리.

---

## A-1 (CRITICAL): Stage4 서브모듈 3종 — ctx 교체 시 Stale 참조 유지

**파일**: `modules/core/stage4_orchestrator.py:242-268`, `stage4_post_processor.py:17-18`, `stage4_context_builder.py:23-24`, `stage4_interview_round.py:11-12`

**문제**:
```python
# stage4_orchestrator.py L242-244 — ctx setter
@ctx.setter
def ctx(self, value):
    self._ctx = value
    # ❌ 캐싱된 서브모듈은 리셋되지 않음!

# L249-250 — lazy init (한 번 생성되면 계속 재사용)
if self._post_processor is None:
    self._post_processor = Stage4PostProcessor(self.ctx)  # ← 생성 시점의 ctx 스냅샷 저장

# stage4_post_processor.py L17-18
def __init__(self, ctx) -> None:
    self.ctx = ctx  # ← 직접 저장 (host.ctx 위임 아님)
```

**재현 시나리오**:
1. 첫 번째 에피소드 → `main_a.py:2916` `_stage4_orch.ctx = Stage4Context(...)` → 서브모듈 lazy-init → 올바른 ctx
2. 두 번째 에피소드 → `_stage4_orch.ctx = Stage4Context(...)` → `self._ctx` 갱신됨
3. **하지만** `_post_processor`, `_context_builder`, `_interview_round` 이미 캐싱됨 → OLD ctx 유지
4. `post_processor.process_pass_result()`: OLD `world_state`, `fact_ledger`, `state_tracker` 사용
5. 결과: 2화부터 **모든 후처리가 1화의 세계 상태로 동작** — 연속성 파괴

**비교** — Stage2는 올바른 패턴 사용:
```python
# stage2_finalizer.py L13-18 (올바른 패턴)
def __init__(self, host) -> None:
    self.host = host
@property
def ctx(self):
    return self.host.ctx  # ← 항상 최신 ctx 반환
```

**수정** — ctx setter에 서브모듈 리셋 추가 (3줄):
```python
@ctx.setter
def ctx(self, value):
    self._ctx = value
    # 서브모듈이 새 ctx를 사용하도록 캐시 무효화
    self._post_processor = None
    self._context_builder = None
    self._interview_round = None
```

**테스트**: ctx 교체 후 서브모듈이 새 ctx를 사용하는지 검증
- `orch.ctx = new_ctx` → `orch.post_processor.ctx is new_ctx` 확인

---

## A-2 (HIGH): `base_agent.py` — 할당량 폴백 시 `response_schema` 탈락

**파일**: `modules/domain/agents/base_agent.py:462-474`

**문제**:
```python
# L295-304 — 메인 config (response_schema 포함)
config_params = {
    "temperature": temperature,
    "max_output_tokens": 8192,
    "top_p": 0.95,
    "response_mime_type": "application/json",
}
if response_schema:
    config_params["response_schema"] = response_schema  # ✅

# L462-474 — 폴백 config (response_schema 누락!)
fallback_config_params = {
    "temperature": temperature,
    "max_output_tokens": 8192,
    "top_p": 0.95,
    "response_mime_type": "application/json",
    # ❌ response_schema 없음!
}
```
- 메인 모델 할당량/Rate Limit 소진 → 폴백 모델 전환 시 `response_schema` 미포함
- `response_schema`는 Gemini의 JSON 구조 강제 기능 — 없으면 비정형 JSON 반환
- V0128 검증 등 구조화 출력에 의존하는 모든 호출이 폴백 시 비정형 응답 수신
- `_extract_json_robust()`가 best-effort 파싱하지만 필드 누락/타입 불일치 가능

**수정** — L474 앞에 추가:
```python
if response_schema:
    fallback_config_params["response_schema"] = response_schema
```

**테스트**: `ask()` 호출 시 quota 폴백 발생 시 config에 `response_schema` 포함 검증

---

## A-3 (HIGH): `StyleGuide.__post_init__` — 타입 비교 항상 False → None 리스트 미초기화

**파일**: `modules/core/stage0/style_extractor.py:55-58`

**문제**:
```python
@dataclass
class StyleGuide:
    # ... 필드 정의 ...
    forbidden_expressions: list[str] = None
    sample_sentences: list[str] = None
    sample_dialogues: list[str] = None
    signature_expressions: list[str] = None
    reference_works: list[str] = None

    def __post_init__(self) -> None:
        for f in fields(self):
            if f.type == list[str] and getattr(self, f.name) is None:
                #    ↑ f.type은 문자열 "list[str]"
                #    ↑ list[str]은 types.GenericAlias 객체
                #    ↑ "list[str]" == list[str] → 항상 False!
                setattr(self, f.name, [])
```
- `f.type`는 **문자열** `"list[str]"` (dataclass introspection 결과)
- `list[str]`는 **GenericAlias** 객체
- 비교가 항상 False → `setattr()` 절대 실행 안 됨
- 결과: `forbidden_expressions`, `sample_sentences` 등이 `None`으로 유지
- `to_prompt()` 등에서 `None` 리스트를 순회/슬라이싱하면 `TypeError`

**수정**:
```python
def __post_init__(self) -> None:
    for f in fields(self):
        if f.type == "list[str]" and getattr(self, f.name) is None:
            setattr(self, f.name, [])
```

**테스트**: `StyleGuide()` 기본 생성 시 모든 `list[str]` 필드가 `[]`로 초기화되는지 검증

---

## A-4 (MEDIUM): `_state_tracker_loaded_arcs` Write-back 누락 → V62.5 증분 최적화 무력화

**파일**: `main_a.py:2197-2201`, `modules/core/stage2_context.py:213`

**문제**:
```python
# main_a.py L2197-2201 — Stage 2 완료 후 write-back
_s2_ctx = self._stage2_orch.ctx
if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
    self.state_tracker = _s2_ctx.state_tracker
    # ❌ self._state_tracker_loaded_arcs = _s2_ctx.state_tracker_loaded_arcs  누락!

# stage2_context.py L213 — from_app() 스냅샷
state_tracker_loaded_arcs=getattr(app, "_state_tracker_loaded_arcs", None),
# ← app._state_tracker_loaded_arcs는 항상 None (write-back 없으므로)

# stage2_orchestrator.py L153-156 — V62.5 증분 판단
existing_tracker_arcs = self.ctx.state_tracker_loaded_arcs or 0
if (
    self.ctx.state_tracker is None
    or existing_tracker_arcs == 0        # ← 항상 True (never written back)
    or existing_tracker_arcs > len(all_refined_arcs)
):
    self.ctx.state_tracker = StateTracker(...)  # ← 매번 처음부터 재구축
```
- `state_tracker_loaded_arcs`가 ctx에만 기록되고 app에 write-back 안 됨
- 다음 Stage 2 호출 시 `from_app()` 스냅샷 = None → `existing_tracker_arcs = 0` → 항상 리셋
- V62.5 증분 업데이트(`full_extract_from_arcs(new_arcs_to_load)`)가 **항상 전체 Arc에 대해 실행**
- 영향: 불필요한 LLM 호출 (Arc 개수 × StateExtractor 호출)

**수정** — `main_a.py:2201` 뒤에 추가:
```python
    self.state_tracker = _s2_ctx.state_tracker
    self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)
```

**테스트**: Stage 2 완료 후 `app._state_tracker_loaded_arcs`가 Arc 수와 일치하는지 검증

---

## B-1 (MEDIUM): `stage2_optimizer.py:423` — `relationship_history` 데드 코드

**파일**: `modules/core/stage2_optimizer.py:423`

**문제**:
```python
# L419-423 — amplify_constraints()
item_history = self._build_item_history(prev_arcs)
grant_history = self._build_grant_history(prev_arcs)
relationship_history = self._build_relationship_history(prev_arcs)  # ← 결과 미사용!

# L425-451 — 프롬프트 빌드
prompt = """..."""
if item_history:       # ✅ 사용됨
    prompt += ...
if grant_history:      # ✅ 사용됨
    prompt += ...
# relationship_history → 어디서도 참조되지 않음 ❌
```
- `_build_relationship_history()` (L514-543)는 모든 Arc를 순회하며 관계 변화 히스토리 구축
- 구축 결과가 프롬프트에 포함되지 않고 폐기됨 — 불필요한 연산

**수정**: L423 삭제.

**테스트**: `amplify_constraints()` 호출 시 `_build_relationship_history`가 호출되지 않는지 검증

---

## B-2 (LOW): `state_extractor.py:246` — LLM 추출 실패 Silent Swallow

**파일**: `modules/domain/agents/state_extractor.py:246-251`

**문제**:
```python
except Exception as e:
    # 실패 시 기본 추출 (Python 기반)
    result = self._fallback_extraction(arc_data)
    # ❌ e가 바인딩되었으나 로깅 없음 — LLM 실패가 완전히 투명
    self._state_cache[cache_key] = result
    return result
```
- LLM 상태 추출 실패 (네트워크 오류, JSON 파싱 오류, 예기치 않은 응답) 시 예외가 silent swallow
- Python 폴백은 정상 동작하지만, **왜** 폴백이 발동했는지 진단 불가
- Sweep 1차 Phase 1 C-1~5 silent swallow 로깅 패턴과 동일한 문제

**수정**:
```python
except Exception as e:
    logging.warning(f"[StateExtractor] LLM 추출 실패 (fallback 사용): {e}")
    result = self._fallback_extraction(arc_data)
    self._state_cache[cache_key] = result
    return result
```

---

## B-3 (LOW): `action_scene_evaluator.py` — 중복 키워드 → 점수 부풀림

**파일**: `modules/validation/action_scene_evaluator.py:94,110`

**문제**:
```python
OUTCOME_KEYWORDS = [
    "맞",
    "피",      # ← L94
    "부딪",
    ...
    "상처",
    "피",      # ← L110 (중복!)
    "부상",
    ...
]
```
- `"피"` 가 리스트에 **2회** 등장
- `_check_outcome_clarity()`: `sum(1 for kw in self.OUTCOME_KEYWORDS if kw in scene)` — 중복 키워드가 2회 카운트
- `outcome_count` 부풀림 → `outcome_clarity` 점수 상승 → 실제보다 높은 평가

**수정**: L110의 중복 `"피"` 삭제.

**테스트**: `OUTCOME_KEYWORDS`에 중복 항목이 없는지 검증 (`len(set(OUTCOME_KEYWORDS)) == len(OUTCOME_KEYWORDS)`)

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/core/stage4_orchestrator.py` | 3줄 추가 (ctx setter 리셋) |
| A-2 | `modules/domain/agents/base_agent.py` | 2줄 추가 (response_schema 복사) |
| A-3 | `modules/core/stage0/style_extractor.py` | 1줄 수정 (타입 비교 문자열) |
| A-4 | `main_a.py` | 1줄 추가 (write-back) |
| B-1 | `modules/core/stage2_optimizer.py` | 1줄 삭제 (데드 코드) |
| B-2 | `modules/domain/agents/state_extractor.py` | 1줄 추가 (로깅) |
| B-3 | `modules/validation/action_scene_evaluator.py` | 1줄 삭제 (중복 키워드) |

**총 ~10줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `catharsis_timer.py:157` float vs int 비교 | ✗ 설계 | 가중치 카타르시스 점수가 좌절 횟수를 초과하는지 판단 — 가중치 적용이 의도. `net_score > 0`과 동치 아님 |
| `manuscript_validator.py:284` scene coverage 0% | ✗ 설계 | dict-valued scene은 키워드 추출 불가 → 0% 표시가 올바른 경고. scene_breakdown이 dict인 경우는 구 버전 Blueprint만 해당 |
| `project_manager.py:779` implicit None return | ✗ 오탐 | `save_v20_anchor` 내부에서 예외 시 except 블록으로 이동 → `return False` 도달. `save_v20_anchor`가 False 반환하는 경우는 존재하지 않음 (항상 True 또는 예외) |
| `reverse_expander.py:441` ep_num index off-by-one | ✗ 설계 | `_generate_drafts`에서 1-based contiguous ep_num 생성이 보장됨. 외부 입력은 `_load_from_path` 경로에만 해당하며, 해당 경로에서 episode_bibles 미사용 |
| `martial_manager.py:336` UnboundLocalError 위험 | ✗ 극저확률 | `convert_to_numeric`은 int/float/None만 반환. KeyError/RuntimeError 발생 경로 없음 |
| `prompt_builder.py:541` self._app None guard | ✗ 오탐 | `generate_arc_context_v60`는 반드시 Stage 2 내부에서 호출. Stage 2 진입 시 `_app`이 항상 바인딩됨 |
| `prompt_builder.py:814` LRU vs min-key | ✗ 설계 | 에피소드 순차 진행 시 min-key ≈ LRU. 과거 에피소드 재방문은 기획상 미지원 |
| `base_agent.py:878,961` process_node(None) | ✗ 극저확률 | LLM 응답에 `"null"` JSON 문자열 확률 극히 낮음. `_extract_json_robust`가 빈 dict 반환으로 graceful 처리 |
| `base_agent.py:339,357` 네트워크 재시도 5회 제한 | ✗ 설계 | `MAX_CONTINUATIONS` 루프는 응답 분할 재조립용. 네트워크 재시도는 내부 `time.sleep` 후 `continue`로 동일 attempt 내 처리. 22회 재시도는 단일 attempt 내에서 달성 |
| `preset_registry.py:507` 미인식 타입 raw value 반환 | ✗ 설계 | 미인식 타입은 사용자 정의 타입 — raw value 유지가 의도된 동작 |
| `vec_memory.py:362` bare except pass | ✗ 설계 | KNN 메타 로드는 보조 정보. 실패 시 빈 메타 반환이 의도 (VecMemory 핵심 동작 불변) |
| `stage2_orchestrator.py:741` callback None guard | ✗ 오탐 | `write_audit_summary`는 `from_app()`에서 항상 바인딩. Stage2Orchestrator는 app 없이 사용되지 않음 |
| `stage2_context.py:228` cumulative_state_cache 동기화 | ✗ 부분 | `sync_cache_key_to_app`은 key만 동기화하지만, `PromptBuilder`는 key+value 모두 확인. key 불일치 시 캐시 miss → fresh compute. 실질적 stale data 가능성은 동일 arc_count 재실행 시에만 해당하며, 이는 정상 운영에서 발생하지 않음 |
| `style_extractor.py:677` re-raise traceback 손실 | ✗ 무해 | 호출자가 `except Exception` → `return {}` 처리. traceback 필요 없는 경로 |
| `stage4_context.py:24` 슬롯 주석 "11종" | ✗ 문서 | 런타임 영향 없는 주석 불일치. 코드는 올바르게 13종 선언 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_stage4_orchestrator.py tests/test_stage2_pipeline.py tests/test_genre_guard.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```
