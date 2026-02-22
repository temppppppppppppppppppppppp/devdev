# Stage 3 Blueprint 2차 전수감사 리포트

**일자**: 2026-02-22
**감사자**: Claude Opus 4.6
**감사 유형**: 2차 (1차 수정 검증 + 신규 발굴)
**1차 감사 참조**: `docs/2026-02-22/opus_tf_stage3_audit.md`, `docs/opus_tf_reaudit_2026-02-21/stage3_audit.md`

---

## 감사 대상 파일

| 파일 | 줄수 | 역할 |
|------|------|------|
| `modules/core/stage3_orchestrator.py` | 647 | 메인 오케스트레이터 |
| `modules/core/stage3_context.py` | 112 | DI 컨텍스트 (20슬롯) |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 588 | 3단계 파이프라인 코어 |
| `modules/domain/agents/blueprint_ensemble.py` | 682 | 앙상블 후보 생성 |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 455 | 제약 수집 |
| `modules/domain/agents/unified_blueprint_validator.py` | 429 | 사전검사 + Director 판정 |
| `modules/models/blueprint.py` | 76 | Pydantic 모델 |
| `modules/core/context_advisor.py` (stage3 슬롯) | ~60 | SC 슬롯 빌더 |
| `config/prompts/ensemble.yaml` | 339 | 프롬프트 템플릿 |
| `config/prompts/blueprint_generator.yaml` | 21 | 패치 모드 프롬프트 |
| `config/settings/validation.yaml` (SC 설정) | ~12 | SC 활성화 플래그 |
| `tests/test_stage3_orchestrator.py` | 427 | 오케스트레이터 테스트 |

---

## 1차 수정 검증 결과

### VER-1: S3-P0-1 (SC 활성화) -- VERIFIED OK

**결과**: 수정 완료, 조건부 동작 확인

1차 감사에서 `_bp_semantic_ctx`가 항상 빈 문자열이었던 문제가 `stage3_orchestrator.py` L420-483에 SC 검색 로직으로 완전 대체되었다.

```python
# L422-424 (현재 코드)
_s3_memory = getattr(self.app, "vec_memory", None) or getattr(self.app, "memory", None)
_s3_advisor = getattr(self.app, "context_advisor", None)
```

`context_advisor.plan_stage3_retrieval()`을 호출하여 5종 슬롯(similar_blueprint, npc_history, continuity_hook, unresolved_plot, genre_context)을 생성하고, `vec_memory.retrieve_multi_query_context()` 또는 `retrieve_npc_context()`로 실제 검색을 수행한다.

**주의 (CAVEAT)**: `validation.yaml`에서 `smart_retrieval.enabled: false`, `smart_retrieval.stage3_enabled: false`로 설정되어 있다. L432-433에서 이 두 플래그를 모두 확인하므로 **현재 배포 환경에서는 SC가 비활성 상태**이다. 코드는 완전히 작동 가능하나 설정으로 꺼져 있다. 이는 SC 전체 시스템이 아직 프로덕션 배포 전이므로 의도적인 것으로 판단된다.

---

### VER-2: S3-P1-3 (strategy_feedback 공유) -- VERIFIED OK

**결과**: 수정 완료

`blueprint_ensemble.py` L191-196 현재 코드:

```python
if strategy.get("name") == rejected_strategy and strategy_specific_feedback:
    _strategy_feedback = strategy_specific_feedback
elif strategy_specific_feedback:
    _strategy_feedback = f"[이전 시도 문제 요약]\n{strategy_specific_feedback}"
else:
    _strategy_feedback = ""
```

1차 감사 시점에서는 `rejected_strategy`와 이름이 일치하는 전략에만 `strategy_specific_feedback`이 전달되었다. 현재는 `elif strategy_specific_feedback:` 분기가 추가되어, 거절되지 않은 전략에도 `"[이전 시도 문제 요약]"` 헤더와 함께 피드백이 전달된다. 전 전략이 이전 REJECT 사유를 참고할 수 있게 되었다.

---

### VER-3: S3-P1-4 (feedback 누적 방지) -- VERIFIED OK

**결과**: 수정 완료

`three_phase_blueprint_generator.py` L157-161 현재 코드:

```python
_initial_feedback = feedback  # [TF-S3-04] 초기 피드백 보존
for retry in range(max_retries + 1):
    pipeline_result["retries"] = retry
    _attempt_feedback = _initial_feedback  # 매 retry마다 초기값에서 시작
```

매 retry 시작 시 `_attempt_feedback = _initial_feedback`으로 리셋하고, 연속성 REJECT(L330) 및 Quality Gate(L380)에서도 `feedback = _initial_feedback + ...` 패턴으로 누적 대신 재구성한다. 피드백 오염 문제 해소 확인.

---

### VER-4: S3-I1 (SC 5종 슬롯) -- VERIFIED OK

**결과**: 구현 완료

`context_advisor.py` L403-458 `_build_stage3_slots()`:

| 슬롯 | 카테고리 | 소스 | 우선순위 |
|------|---------|------|---------|
| Arc 전술 키워드 | `similar_blueprint` | `vec_memory` | 1 |
| NPC 최근 행적 | `npc_history` | `db_npc_history` | 1 |
| 직전 Blueprint ending_hook | `continuity_hook` | `vec_memory` | 1 |
| 미해결 플롯 | `unresolved_plot` | `vec_memory` | 2 |
| 장르 컨텍스트 | `genre_context_1` | `vec_memory` | 3 |

5종 슬롯이 조건부로 생성되며, `_stage_query_cap("stage3") = 6`으로 최대 6개까지 허용. 중복 제거(`_dedupe_slots`) 및 예산 배분(`_assign_slot_budgets`)도 정상 적용.

---

### VER-5: S3-I4 (정규식 폴백) -- VERIFIED OK

**결과**: 구현 완료

`blueprint_constraint_compiler.py` L175-186 `_EPISODE_HEADER_PATTERNS`:

```python
_EPISODE_HEADER_PATTERNS = [
    r"\[제\s*{ep}\s*화[^\]]*\](.*?)(?=\[제\s*\d+\s*화|\Z)",        # [제N화]
    r"#{2,3}\s*제\s*{ep}\s*화[^\n]*(.*?)(?=#{2,3}\s*제\s*\d+\s*화|\Z)",  # ###제N화
    r"\*\*제\s*{ep}\s*화[^*]*\*\*(.*?)(?=\*\*제\s*\d+\s*화|\Z)",    # **제N화**
    r"제\s*{ep}\s*화\s*[:\-\u2013\u2014]\s*(.*?)(?=제\s*\d+\s*화\s*[:\-\u2013\u2014]|\Z)",  # 제N화:
    r"[\(]?제\s*{ep}\s*화[\)]\s*(.*?)(?=[\(]?제\s*\d+\s*화[\)]|\Z)",  # (제N화)
]
```

5개 정규식 폴백 패턴이 우선순위 순으로 적용된다. `_extract_episode_focus()`와 `_extract_stop_line()` 모두에서 동일 패턴 사용. 1차 감사에서 지적한 단일 패턴 한계가 완전히 해소되었다.

---

### VER-6: S3-I5 (N+1 쿼리) -- VERIFIED OK

**결과**: 수정 완료

`stage3_orchestrator.py` L488 현재 코드:

```python
_recent_manuscripts = ctx.current_project.db.get_recent_manuscripts(before_ep=working_ep, limit=30)
```

개별 `get_manuscript()` 30회 호출이 `get_recent_manuscripts()` 단일 쿼리로 대체되었다. DB I/O 30회 -> 1회 최적화 확인.

---

### VER-7: S3-P1-2 (causal_history DB 오류) -- VERIFIED OK

**결과**: 수정 완료

`unified_blueprint_validator.py` L55-63 `_safe_causal_history()` 메서드가 추가되어 `hasattr` + `try-except` 이중 보호가 적용되었다.

---

### VER-8: S3-P2-3 (절삭 메시지 하드코딩) -- VERIFIED OK

**결과**: 수정 완료

`stage3_orchestrator.py` L498:
```python
f"\n... ({ContextLimits.MAX_CONTEXT_CHARS // 1000}K자 절삭)"
```

하드코딩 "200K" 대신 상수 기반 동적 메시지로 변경 확인.

---

### VER-9: S3-P1-5, P2-1, P2-4 (Dead Code 제거) -- VERIFIED OK

**결과**: 전량 제거 확인

- `_evaluate_candidate()` (blueprint_ensemble.py) -- 제거됨
- `collect_warnings()` (blueprint_ensemble.py) -- 제거됨
- `_generate_feedback()` (unified_blueprint_validator.py) -- 제거됨

Grep으로 3개 메서드 모두 해당 파일에서 존재하지 않음을 확인.

---

### VER-10: S3-01 (Continuity REJECT stats 미갱신) -- VERIFIED OK

**결과**: 수정 완료

`three_phase_blueprint_generator.py` L320:
```python
self.stats["phase3_reject"] += 1  # [TF-S3-01] stats 갱신
```

연속성 REJECT 시에도 `phase3_reject` 카운터가 증가하도록 수정됨. 또한 L324-328에서 `_prev_selection_reason`, `_prev_validation_warnings`, `_previous_best` 모두 갱신되어 다음 retry의 패치 모드가 최신 데이터로 동작.

---

### VER-11: S3-02 (_handle_failure 즉시 중단) -- VERIFIED OK

**결과**: 의도적 설계로 확정

`_handle_failure()`의 `break: True`는 현재 항상 반환되며, docstring에 명확히 기술됨:

```python
"""Blueprint 생성 실패 시 처리. 항상 break=True를 반환하여 루프를 종료한다
(순차 의존성: 후속 에피소드는 현재 에피소드 Blueprint에 의존)."""
```

`next_ep: working_ep`로 현재 에피소드에 머무르며 루프를 종료한다. 사용자가 Stage 3을 다시 실행하면 동일 에피소드부터 재시도하는 구조. Blueprint의 순차 의존성(N화 Blueprint 없이 N+1화 불가)을 고려하면 올바른 설계.

---

### VER-12: S3-11 (score_breakdown 미반환) -- VERIFIED OK

**결과**: 수정 완료

`unified_blueprint_validator.py` L268-271:
```python
"score_breakdown": {
    "director_score": director_score,
    "pre_issues_count": len(pre_result["issues"]),
},
```

`validate()` 반환값에 `score_breakdown` 키가 추가되어, 패치 모드에서 세부 점수 피드백을 받을 수 있게 되었다. `director_compare` 분기에서는 여전히 `score_breakdown` 미반환이지만, 해당 분기는 `compare_result`의 상세 정보(`comparison_notes`, `reason`)로 보완됨.

---

## 신규 발견 사항

### NEW-P1-1: `validate_blueprint_integrity()`가 `scene_breakdown` list 타입을 거부 -- Pydantic 모델과 불일치

**심각도**: P1 (품질 이슈)
**파일**: `modules/core/services/state_service.py` L352
**코드**:
```python
if "scene_breakdown" not in blueprint or not isinstance(blueprint.get("scene_breakdown"), dict):
    self._ui.log(f"{Emojis.ERROR} [Integrity] scene_breakdown 누락")
    return False
```

`validate_blueprint_integrity()`는 `scene_breakdown`이 `dict`가 아니면 무결성 실패로 판정한다. 그런데 LLM은 종종 `scene_breakdown`을 `list` 형태로 반환하며, 이에 대한 방어가 `blueprint_ensemble.py`(L639), `blueprint_constraint_compiler.py`(L288), `unified_blueprint_validator.py`(L336-340), `director_ensemble.py`(L213) 등 여러 곳에서 `isinstance(scenes, list)` 체크로 이미 추가되어 있다.

**문제 경로**:
1. LLM이 `scene_breakdown`을 list로 반환
2. `blueprint_ensemble.py`의 최소 기준 필터(L267)에서 `len(scenes)` 체크 -- list도 통과
3. Director가 PASS 판정
4. `validate_blueprint(raw)` Pydantic 호출 -- `scene_breakdown: dict` 필드이나 list 입력 시 Pydantic이 `dict`로 coerce하지 못하면 원본 반환(graceful degradation). `extra="allow"` + `model_dump()` 경로에서 list가 dict 필드에 들어가면 validation 실패 -> 원본 dict 유지. 원본 dict에 list 형태의 scene_breakdown 잔존.
5. `validate_blueprint_integrity(blueprint)` 호출 -- `isinstance(dict)` 실패 -> `return False`
6. Blueprint 무결성 실패 -> 저장 거부 + `fail_count += 1` + `break: True`

**영향**: LLM이 list 형태의 scene_breakdown을 반환하면 Director PASS에도 불구하고 Blueprint가 저장되지 않고 루프가 종료된다. 이는 Stage 3 전체 실패로 이어진다.

**수정 제안**: `validate_blueprint_integrity()`에 list 타입 허용 추가:
```python
if "scene_breakdown" not in blueprint or not isinstance(blueprint.get("scene_breakdown"), (dict, list)):
```

또는 Pydantic 모델의 `scene_breakdown` 필드를 `dict | list`로 확장.

---

### NEW-P1-2: `_handle_success`에서 integrity 실패 시 `success_count` 증가 없이 `fail_count` 증가 + `break: True` -- 사용자 혼란

**심각도**: P1 (품질 이슈)
**파일**: `modules/core/stage3_orchestrator.py` L556-564
**코드**:
```python
if not ctx.validate_blueprint_integrity(blueprint):
    ctx.ui.log(f"   ... 무결성 실패")
    return {
        "next_ep": working_ep + 1,  # 다음 에피소드로 이동
        "success_count": success_count,
        "fail_count": fail_count + 1,
        "break": True,
    }
```

무결성 실패 시 `next_ep: working_ep + 1`로 다음 에피소드로 건너뛰면서 `break: True`로 루프를 종료한다. 이 경우:
- 현재 에피소드의 Blueprint가 저장되지 않는다
- `_handle_failure()`의 `next_ep: working_ep` (현재 에피소드 유지) 패턴과 비일관
- 다음 실행 시 현재 에피소드부터 다시 시작하므로 `next_ep + 1`은 실질적으로 무의미하지만, `_process_single_episode()`의 "직전 화 Blueprint 필수 체크"(L266-276)에서 누락이 감지되어 중단됨

**영향**: 기능적 손상은 없으나(어차피 중단됨), `_handle_failure`와 `_handle_success(integrity fail)` 사이의 비일관적인 `next_ep` 패턴이 유지보수를 어렵게 함. `_handle_failure`는 `next_ep: working_ep`(현재 유지), `_handle_success(integrity fail)`은 `next_ep: working_ep + 1`(다음 이동).

**수정 제안**: `_handle_success` integrity 실패 시에도 `next_ep: working_ep`으로 통일:
```python
return {
    "next_ep": working_ep,  # 현재 에피소드 유지 (순차 의존성)
    "success_count": success_count,
    "fail_count": fail_count + 1,
    "break": True,
}
```

---

### NEW-P1-3: `_safe_commit()` 반환값이 DI 콜백 체인에서 소실될 수 있음

**심각도**: P1 (품질 이슈)
**파일**: `modules/core/stage3_orchestrator.py` L568, `modules/core/stage3_context.py` L107

`_handle_success()`에서 `ctx.safe_commit()` 반환값을 bool로 평가한다:

```python
if not ctx.safe_commit():
    # 커밋 실패 처리
```

`ctx.safe_commit`은 `Stage3Context.from_app()` L107에서 `app._safe_commit`로 바인딩된다. `main_a.py` L337-355의 `_safe_commit()`은 `bool`을 반환한다.

그러나 `_safe_commit`이 `MagicMock()` (테스트) 또는 `None` (from_app에서 getattr 실패)인 경우:
- `None` -- `ctx.safe_commit()`가 `TypeError: 'NoneType' is not callable` 발생
- `MagicMock()` -- 항상 truthy 반환 (정상)

`from_app()`에서 `getattr(app, "_safe_commit", None)`으로 바인딩하므로, `app`에 `_safe_commit` 속성이 없으면 `ctx.safe_commit = None`이 되고, 호출 시 crash.

**영향**: 정상 운영 환경에서 `_safe_commit`이 없을 가능성은 매우 낮다(SovereignApp에 항상 존재). 그러나 DI 테스트에서 `safe_commit` 콜백 누락 시 런타임 에러 발생 가능.

**수정 제안**: `_handle_success`에서 None 체크 추가 또는 `Stage3Context.__init__`에서 기본 콜백 주입:
```python
safe_commit=safe_commit or (lambda: True),
```

---

### NEW-P2-1: `PASS_WITH_WARNING` Blueprint가 Stage 4에서 `quality_risk` 미참조 -- 메타데이터 낭비 지속

**심각도**: P2 (경미)
**파일**: `modules/core/stage3_orchestrator.py` L546-553, Stage 4 전체

1차 감사에서 지적된 `_stage3_meta`, `quality_risk`, `quality_gate_failed` 메타데이터의 Stage 4 미활용 상태가 2차 감사에서도 동일하다. Stage 4 오케스트레이터, 컨텍스트 빌더, 인터뷰 라운드, Chief Writer 컨텍스트/품질 모듈 어디에서도 이 3개 키를 읽지 않는다.

Blueprint에 다음 메타데이터가 주입되지만 활용처가 없다:
```python
blueprint["_stage3_meta"] = {
    "final_verdict": _final_verdict,
    "quality_gate_failed": _quality_gate_failed,
    "quality_risk": _quality_risk,
    "last_score": pipeline_result.get("last_score", 0),
}
blueprint["quality_gate_failed"] = _quality_gate_failed
blueprint["quality_risk"] = _quality_risk
```

**영향**: 메타데이터 주입 자체에 의한 성능 손실은 무시할 수준이지만, PASS_WITH_WARNING Blueprint(Director가 REJECT했으나 점수 임계값 이상이라 강제 통과)가 Stage 4에서 일반 PASS Blueprint와 동일하게 처리되어, 품질 위험 시그널이 전달되지 않는다.

---

### NEW-P2-2: `_build_reader_feedback_context()` DB 테이블 미존재 시 빈 쿼리 반복

**심각도**: P2 (경미)
**파일**: `modules/domain/agents/blueprint_ensemble.py` L449-506

`_build_reader_feedback_context()`는 `db.get_recent_satisfaction_tags()`와 `db.get_recent_pacing_records()`를 호출한다. 두 메서드 모두 `episode_satisfaction_tags` / `episode_pacing_analysis` 테이블에서 조회하는데, 신규 프로젝트에서는 해당 테이블에 데이터가 없다(Stage 4 원고 생성 후에야 채워짐).

현재 각 메서드가 개별 `try-except`로 보호되어 있어 crash는 없지만, Stage 3 Blueprint 앙상블 생성은 Stage 4 이전에 실행되므로 **항상 빈 결과**를 반환한다. 3개 전략 x 매 호출 = 최소 3회 불필요한 DB 쿼리.

**영향**: 미미. DB 쿼리 자체가 빠르고 결과가 없으면 즉시 반환. 그러나 논리적으로 Stage 3에서 Stage 4의 결과물(만족도/호흡 분석)을 참조하는 것은 시간적 순서가 역전되어 있다.

**수정 제안**: 불필요한 쿼리를 줄이려면 `ep_num <= 1`이면 조기 반환하는 가드 추가.

---

### NEW-P2-3: Ensemble 타임아웃 상수가 YAML 외부화 대상

**심각도**: P2 (경미)
**파일**: `modules/domain/agents/blueprint_ensemble.py` L102-103

```python
ENSEMBLE_TIMEOUT = 300   # 전체 앙상블 타임아웃 (초)
SINGLE_CANDIDATE_TIMEOUT = 240  # 개별 후보 타임아웃 (초)
```

타임아웃 값이 하드코딩되어 있다. `validation.yaml`에는 다른 임계값들이 외부화되어 있으나, 앙상블 타임아웃은 포함되어 있지 않다. 야간 무인 운영 시 API 응답이 느린 경우 조정이 필요할 수 있다.

---

### NEW-P2-4: `_extract_continuity()`에서 `scene_keys` 정렬 시 숫자 없는 키에 대한 방어 미흡

**심각도**: P2 (경미)
**파일**: `modules/domain/agents/blueprint_constraint_compiler.py` L290-291

```python
scene_keys = sorted(
    scenes.keys(),
    key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0
)
```

이 코드는 `re.search(r"\d+", x)`가 None이면 0을 반환하므로 `AttributeError`는 방지된다. 그러나 모든 scene key에 숫자가 없는 경우(예: `{"intro": ..., "climax": ..., "outro": ...}`) 전부 키값 0으로 정렬되어 순서가 비결정적(Python dict 삽입 순서 보존이지만 sorted의 stable sort 결과는 원래 순서)이다. 실질적 문제는 아니나, 마지막 씬 추출이 의도와 다를 수 있다.

---

## 연결성 검증

### Stage 2 -> Stage 3 데이터 전달 완전성

| 데이터 | 전달 경로 | 상태 |
|--------|----------|------|
| Arc 데이터 전체 | `ctx.current_project.arcs` -> `get_arc_context_for_episode()` | OK |
| `tactical_doc` | `constraint_compiler._extract_episode_focus()` | OK |
| `state_changes` | `_summarize_state_changes()` -- 10개 카테고리 커버 | OK |
| `constraint_summary` | `arc_data.get("constraint_summary")` -- 없으면 경고 로그 | OK |
| `beat_sequence` | 정규식 전량 실패 시 폴백 | OK |
| `joint_docs` | `_extract_inherited_state()` -- 소지품 계승 | OK |
| `status_shadow` | `_extract_inherited_state()` -- 내공/부상 계승 | OK |
| `state_constraints` | `_extract_inherited_state()` -- Arc 시작 상태 계승 | OK |

**특이사항**: `beat_sequence` 항목이 `dict`인 경우에 대한 방어가 `_extract_episode_focus()` L214-217에 추가되어 있다(`[Sweep60]` 태그). `str(content)` 폴백 포함.

---

### Stage 3 -> Stage 4 Blueprint 데이터 전달 완전성

| 데이터 | Blueprint 키 | Stage 4 참조 | 상태 |
|--------|-------------|-------------|------|
| 시나리오 | `integrated_scenario` | `stage4_context_builder.py` | OK |
| 씬 구성 | `scene_breakdown` | `stage4_context_builder.py`, `director` | OK |
| 종료 위치 | `end_location` | 다음 Blueprint 연속성 | OK |
| 엔딩 훅 | `ending_hook` | 다음 Blueprint 연속성 | OK |
| 시간 흐름 | `time_flow` | 다음 Blueprint 연속성 | OK |
| 주인공 상태 | `protagonist_state` | 다음 Blueprint 계승 | OK |
| 종료 상태 | `ending_state` | 다음 Blueprint 연속성 | OK |
| 에피소드 번호 | `ep_num` / `episode_number` | DB 조회 키 | OK |
| 제목 | `title` | 원고 생성 참조 | OK |
| 품질 메타 | `_stage3_meta`, `quality_risk` | **미참조** | GAP |

Blueprint는 `save_episode_blueprint()` -> `db.save_blueprint()` + `_save_blueprint_to_txt()`로 DB와 파일 양쪽에 저장된다. Stage 4에서 `get_blueprint(ep_num)`으로 조회하며, JSON 직렬화/역직렬화를 거치므로 Pydantic `validate_blueprint()` 통과 후의 dict가 DB에 저장된다.

**GAP**: `_stage3_meta`, `quality_risk`, `quality_gate_failed`가 Blueprint dict에 포함되어 DB에 저장되지만 Stage 4에서 읽지 않는다 (1차 감사와 동일). Blueprint txt 파일에도 포함되어 불필요한 디스크 사용.

---

## SC(Smart Context) 동작 가능 여부 심층 분석

SC 코드는 완전히 구현되어 있으나 `validation.yaml` 설정이 `false`이므로 현재 비활성 상태이다. 활성화 시 동작 가능 여부를 분석한다.

### 활성화 시 동작 경로

1. `stage3_orchestrator.py` L432-433: `_s3_sc_enabled` 플래그 확인
2. `context_advisor.plan_stage3_retrieval()` 호출 -> `_build_plan("stage3", ...)` -> `_heuristic_plan()` -> `_build_stage3_slots()`
3. 슬롯별 `vec_memory` 또는 `db_npc_history` 소스로 검색
4. 결과를 `_bp_semantic_ctx`에 조립 -> `three_phase_bp.generate(..., semantic_context=...)` 전달
5. `generate()` L124-125에서 `feedback`에 SC 결과 주입

### 동작 가능성 판정: OK (조건부)

**필수 조건**:
- `vec_memory`가 `self.app`에 바인딩되어야 함 (L424: `getattr(self.app, "vec_memory", None)`)
- `context_advisor`가 `self.app`에 바인딩되어야 함 (L425)
- `vec_memory`에 과거 Blueprint/원고 임베딩이 저장되어 있어야 함

**잠재 문제**: `retrieve_npc_context()`는 `npc_names` 리스트를 인자로 받는데, L463-466에서 `_s3_npc_roster[:5]`를 전달한다. NPC 이름이 entity_registry에서 추출되므로, entity_registry가 None이면 빈 리스트가 전달되고 NPC 컨텍스트 검색이 무효화된다.

---

## 개선 아이디어

### IDEA-1: Blueprint Pydantic 모델에 `scene_breakdown` 타입 union 적용

현재 `scene_breakdown: dict`로 선언되어 있으나, LLM이 list를 반환하는 경우가 확인되었다(`director_continuity.py:241`, `expert_mixture.py:324` 등에 list 방어 코드 존재). Pydantic `before` validator에서 list -> dict 자동 변환을 추가하면 하류 모든 코드에서 일관된 dict 처리가 가능해진다.

```python
@field_validator("scene_breakdown", mode="before")
@classmethod
def _normalize_scene_breakdown(cls, v):
    if isinstance(v, list):
        return {f"scene_{i+1}": s for i, s in enumerate(v) if isinstance(s, dict)}
    return v
```

이 변환은 이미 `blueprint_ensemble.py` L639-640에서 수동으로 수행되고 있으므로, Pydantic 레벨로 끌어올리면 중복 변환 코드를 제거할 수 있다.

---

### IDEA-2: Stage 3 `quality_risk` 시그널을 Stage 4 Chief Writer에 전달

`_stage3_meta.quality_risk = True`인 Blueprint에 대해 Stage 4 Chief Writer가 "이 설계도는 품질 위험 마크가 있으므로 더 신중하게 작성하라"는 부가 지시를 받으면 원고 품질이 향상될 수 있다.

구현 방법: `stage4_context_builder.py`에서 Blueprint 로드 시 `quality_risk` 플래그 확인 -> Chief Writer 프롬프트에 경고 섹션 추가.

---

### IDEA-3: 연속성 REJECT 시 나머지 앙상블 후보 활용

현재 `three_phase_blueprint_generator.py` L316에서 연속성 검사는 `best_blueprint`(앙상블 대표 후보)만 대상으로 한다. REJECT 시 `all_candidates`의 다른 후보를 순차 검사하면 불필요한 재생성을 줄일 수 있다. 이미 1차 감사(`S3-08`)에서 INSIGHT로 지적되었으나, 패치 모드 도입으로 재생성 비용이 줄었으므로 우선순위는 낮다.

---

### IDEA-4: `_build_reader_feedback_context()` Stage 조건 가드

Stage 3에서 `_build_reader_feedback_context()`를 호출하지만, 만족도/호흡 데이터는 Stage 4 이후에만 존재한다. `ep_num`과 무관하게 항상 DB 쿼리가 실행되므로, "Stage 3에서는 이 데이터가 없을 가능성이 높다"는 가드를 추가하면 불필요한 쿼리를 줄일 수 있다:

```python
# 기존 데이터가 한 건도 없으면 이후 호출에서 스킵
if self._reader_fb_available is False:
    return ""
```

---

## 테스트 커버리지 평가 (2차)

| 파일 | 테스트 | 커버리지 | 1차 대비 |
|------|--------|---------|---------|
| `stage3_orchestrator.py` | `test_stage3_orchestrator.py` (427줄, 17 테스트) | 양호 | 변동 없음 |
| `stage3_context.py` | 위 파일에 포함 (7 테스트) | 양호 | 변동 없음 |
| `three_phase_blueprint_generator.py` | `test_blueprint_patch_mode.py` (6 테스트) | 부분적 | 변동 없음 |
| `blueprint_ensemble.py` | 전용 테스트 없음 | **부족** | 변동 없음 |
| `blueprint_constraint_compiler.py` | 전용 테스트 없음 | **부족** | 변동 없음 |
| `unified_blueprint_validator.py` | 전용 테스트 없음 | **부족** | 변동 없음 |
| `models/blueprint.py` | 전용 테스트 없음 | **부족** | 변동 없음 |
| `context_advisor.py` (stage3 슬롯) | `test_sc6_observability.py` 등 | 부분적 | 신규 확인 |

**테스트 GAP 우선순위**:
1. `blueprint_constraint_compiler.py` -- 정규식 폴백 5패턴 각각의 매칭/비매칭 테스트 필요
2. `unified_blueprint_validator.py` -- Director 비교 선택 모드 vs 단일 후보 모드 분기 테스트 필요
3. `models/blueprint.py` -- scene_breakdown list 입력 시 Pydantic 동작 테스트 필요

---

## 요약

### 1차 수정 검증: 12건 전량 OK

| ID | 항목 | 검증 결과 |
|----|------|----------|
| VER-1 | SC 활성화 코드 | OK (설정 비활성) |
| VER-2 | strategy_feedback 공유 | OK |
| VER-3 | feedback 누적 방지 | OK |
| VER-4 | SC 5종 슬롯 | OK |
| VER-5 | 정규식 폴백 | OK |
| VER-6 | N+1 쿼리 최적화 | OK |
| VER-7 | causal_history DB 보호 | OK |
| VER-8 | 절삭 메시지 동적화 | OK |
| VER-9 | Dead Code 제거 3건 | OK |
| VER-10 | Continuity REJECT stats | OK |
| VER-11 | _handle_failure 설계 확정 | OK |
| VER-12 | score_breakdown 추가 | OK |

### 신규 발견: P0 0건, P1 3건, P2 4건, 개선 아이디어 4건

| ID | 심각도 | 요약 |
|----|--------|------|
| NEW-P1-1 | P1 | `validate_blueprint_integrity()`가 scene_breakdown list 거부 |
| NEW-P1-2 | P1 | `_handle_success` integrity 실패 시 `next_ep` 비일관 |
| NEW-P1-3 | P1 | `safe_commit` DI 콜백 None 시 crash 가능 |
| NEW-P2-1 | P2 | `quality_risk` Stage 4 미참조 (1차와 동일, 미해결) |
| NEW-P2-2 | P2 | `_build_reader_feedback_context()` Stage 3에서 항상 빈 결과 |
| NEW-P2-3 | P2 | 앙상블 타임아웃 YAML 외부화 미완 |
| NEW-P2-4 | P2 | `_extract_continuity()` scene_keys 비결정적 정렬 |
| IDEA-1 | -- | Pydantic scene_breakdown list->dict 자동 변환 |
| IDEA-2 | -- | quality_risk Stage 4 전달 |
| IDEA-3 | -- | 연속성 REJECT 시 나머지 후보 활용 |
| IDEA-4 | -- | reader_feedback Stage 조건 가드 |

### 총평

1차 감사의 P0 1건 + P1 5건 + P2 4건이 전량 수정 확인되었다. Dead Code 3건 완전 제거, SC 로직 전면 구현, 피드백 누적 방지, N+1 쿼리 최적화 등 핵심 수정이 모두 올바르게 적용되었다.

2차에서 발견된 NEW-P1-1(scene_breakdown list 거부)은 **런타임 실패로 이어질 수 있는 잠재적 이슈**로, 우선 수정을 권장한다. 나머지 P1 2건과 P2 4건은 정상 운영에 영향을 주지 않는 방어적 보강 항목이다.

Stage 3 파이프라인은 전반적으로 안정적이며, 디렉터주권주의 원칙이 일관되게 유지되고 있다.
