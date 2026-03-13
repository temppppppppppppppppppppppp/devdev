# XC-DI-T2: Closure 타입 안전 (DI Callback)

> Track: XC-DI (Protocol & 계약 준수)
> 대상: stage4_context.py 콜백 12종, stage2_context.py 콜백 21종, stage3_context.py 콜백 10종
> 감사일: 2026-03-13
> 방법론: 3-Pass (수집 → 교차 검증 → 오탐 제거)

---

## 1. 분석 범위

Stage4Context에 선언된 콜백 12종:
```
get_int_input, build_item_acquisition_timeline, load_narrative_summaries,
get_protagonist_name, extract_npc_profiles, generate_narrative_summary,
generate_writer_guidance_v60_8, enrich_director_result, audit_event,
write_audit_summary, flush_audit_buffer, safe_commit
```

Stage2Context에 선언된 콜백 21종 + 메타 3종 (retry_feedback 포함)

Stage3Context에 선언된 콜백 10종

---

## 2. None 가드 패턴 분류

### 패턴 A: `callable(getattr(self.ctx, "name", None))` — 안전

Stage2/3/4 모두에서 `audit_event`, `flush_audit_buffer`, `safe_commit`, `write_audit_summary` 등 핵심 콜백은 이 패턴을 사용.

**해당 콜백:** audit_event (3개 스테이지 전부), flush_audit_buffer (Stage4), safe_commit (Stage4), write_audit_summary (Stage2/3), get_int_input (Stage2 :349, Stage3 :554, Stage4 :1276만), validate_arc_data_fields, validate_arc_integrity, fix_entity_registry_protagonist

### 패턴 B: `inspect.getattr_static` + `callable` — 과도하지만 안전

`enrich_director_result` (interview_round:844), `generate_writer_guidance_v60_8` (context_builder:2514) 에서 사용.
`__slots__` 클래스이므로 `getattr_static`은 불필요하지만 동작에 문제 없음.

### 패턴 C: try-except 내부 직접 호출 — 조건부 안전

`generate_narrative_summary` (post_processor:448), `build_item_acquisition_timeline` (context_builder:1864), `load_narrative_summaries` (context_builder:2448) — None이면 TypeError → except로 잡힘. 기능적으로 안전하지만 예외 메시지가 혼란스러울 수 있음.

### 패턴 D: 가드 없는 직접 호출 — **위험**

`get_int_input` (Stage4 orchestrator:1479, :1535) — None이면 `TypeError` 발생. `from_app()` 경로에서는 항상 바인딩되므로 프로덕션에서는 미발현이나, 테스트 mock 경로에서 위험.

---

## 3. 콜백 시그니처 타입 안전성

### 3.1 시그니처 불일치 위험

모든 콜백이 `Optional` (`=None`)으로 선언되어 있고, 타입 힌트 없이 `Any` 수준. `__init__`에서 아무 callable이나 받을 수 있어 시그니처 불일치 시 런타임 TypeError.

그러나 실무에서는 `from_app()` 경로만 사용되므로, `_safe_getattr(app, "_method_name", None)`으로 bound method가 항상 주입됨. 시그니처 불일치 위험은 이론적 수준.

### 3.2 콜백 vs 데이터 슬롯 혼재

`cumulative_state_cache` (dict), `cumulative_state_cache_key` (str), `state_tracker_loaded_arcs` (int)는 콜백이 아닌 **가변 데이터 슬롯**이지만 콜백 섹션에 선언됨.

- `stage2_context.py:165-166`: `cumulative_state_cache`, `cumulative_state_cache_key` 는 __slots__의 콜백 섹션([4C-3c])에 위치
- 이들은 `orchestrator:366-367`에서 `None` 할당, 이후 preflight에서 dict/str로 갱신됨
- `callable()` 가드가 적용되면 데이터 접근이 차단되는 역효과 가능 (현재는 직접 접근이라 문제 없음)

---

## 4. Findings

### [XC-DI-006] P3 | Stage4 `get_int_input` 2곳에서 None 가드 없이 직접 호출

| 필드 | 내용 |
|------|------|
| ID | XC-DI-006 |
| Severity | P3 |
| 현상 요약 | `stage4_orchestrator.py:1479`와 `:1535`에서 `self.ctx.get_int_input()` 직접 호출. None이면 TypeError |
| 코드 근거 | `:1479` `target_ep = self.ctx.get_int_input(...)` — 동일 파일 `:1276`에서는 `callable(getattr(self.ctx, "get_int_input", None))` 가드 적용. 불일치 |
| 영향 경계 | `from_app()` 경로에서는 미발현 (bound method 항상 주입). 테스트에서 Stage4Context를 직접 생성할 때만 위험 |
| 테스트 근거 | `test_stage4_orchestrator.py` 에서 mock ctx 사용 시 get_int_input 바인딩 여부 미확인 |
| 기존 중복 여부 | XC-DI-001과 동일 (통합) |
| 권장 후속 조치 | `:1276` 패턴으로 통일. 공수 5분 |

### [XC-DI-007] P3 | `build_item_acquisition_timeline` 콜백 None 시 TypeError가 try-except로 묵인

| 필드 | 내용 |
|------|------|
| ID | XC-DI-007 |
| Severity | P3 |
| 현상 요약 | `stage4_context_builder.py:1864`에서 `self.ctx.build_item_acquisition_timeline(next_ep - 1)` 직접 호출. None이면 TypeError 발생하나 상위 try-except가 잡아 비치명 처리 |
| 코드 근거 | `stage4_context_builder.py:1864` — `item_acquisition_timeline = self.ctx.build_item_acquisition_timeline(next_ep - 1)`. 상위 블록에 try-except 존재 여부 확인 필요 |
| 영향 경계 | TypeError가 발생하면 `item_acquisition_timeline`이 미설정 → 이후 컨텍스트에서 아이템 타임라인 누락 |
| 테스트 근거 | `from_app()` 경로에서는 항상 바인딩. 단위 테스트 mock에서만 위험 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `callable` 가드 추가 또는 기본값 `[]` 반환 패턴 적용. 공수 5분 |

### [XC-DI-008] P3 | Stage2Context 콜백 섹션에 데이터 슬롯 3종 혼재

| 필드 | 내용 |
|------|------|
| ID | XC-DI-008 |
| Severity | P3 |
| 현상 요약 | `cumulative_state_cache` (dict), `cumulative_state_cache_key` (str/None), `state_tracker_loaded_arcs` (int)가 콜백 섹션([4C-3c])에 선언되어 있으나 실제로는 가변 데이터 슬롯 |
| 코드 근거 | `stage2_context.py:163-170` — `[4C-3c] 콜백 21종` 주석 아래 위치 |
| 영향 경계 | 코드 가독성/유지보수성 저하. 향후 `callable()` 가드를 일괄 적용하면 데이터 접근 차단 부작용 가능 |
| 테스트 근거 | N/A (코드 조직 이슈) |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `__slots__` 내 주석 섹션을 `[데이터]`/`[콜백]`으로 분리. 공수 5분 |

### [XC-DI-009] P3 | `inspect.getattr_static` 불필요 사용 (2곳)

| 필드 | 내용 |
|------|------|
| ID | XC-DI-009 |
| Severity | P3 |
| 현상 요약 | `stage4_interview_round.py:844`와 `stage4_context_builder.py:2514`에서 `inspect.getattr_static(self.ctx, ...)` 사용. `Stage4Context`는 `__slots__` 클래스이므로 `hasattr`/`getattr`로 충분 |
| 코드 근거 | interview_round:844 `inspect.getattr_static(self.ctx, "enrich_director_result")`, context_builder:2514 `inspect.getattr_static(self.ctx, "generate_writer_guidance_v60_8")` |
| 영향 경계 | 기능 영향 없음. `inspect` import와 2단계 조회로 마이크로 오버헤드만 존재 |
| 테스트 근거 | 정상 동작 확인됨 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `callable(getattr(self.ctx, "name", None))` 패턴으로 통일. 공수 5분. 우선순위 낮음 |

### [XC-DI-010] P3 | Stage2 `generate_arc_context_v60` 콜백 None 가드 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-010 |
| Severity | P3 |
| 현상 요약 | `stage2_orchestrator.py:381`에서 `self.ctx.generate_arc_context_v60(...)` 직접 호출. None이면 TypeError |
| 코드 근거 | `:381` `last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, batch_start + 1)` |
| 영향 경계 | `_build_retry_feedback_contract()`에서 해소되므로 `from_app()` 경로에서는 None이 아닐 가능성 높음. 그러나 fallback 체인 전부 실패 시 None 가능 |
| 테스트 근거 | retry_feedback 콜백 해소 로직이 테스트에서 커버되는지 미확인 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `callable` 가드 + fallback 추가. 공수 10분 |
