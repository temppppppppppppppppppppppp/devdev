# [MFS-T2] State Service / Validation Findings

> 작성일: 2026-03-13
> 상태: `PASS3 complete`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-facade-shim-detail-full-survey-audit-order.md`
> 테스트 확인:
> - `pytest -q tests/test_state_service.py` -> `41 passed in 1.73s`
> - `pytest -q tests/test_stage2_context.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py` -> `60 passed in 2.32s`

이 문서는 `main_a.py`의 state-service / validation shim 표면을 `StateService`, `Stage2Context`, Stage2/3/4 consumer, 관련 테스트와 교차 대조한 결과다. 조사 중 코드 직접 수정은 하지 않았다.

---

## 조사 범위

- `main_a.py`: state service / validation shim
- `modules/core/services/state_service.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py`

## 필수 근거

- `tests/test_state_service.py`
- `modules/core/services/state_service.py`
- `modules/core/stage2_context.py`
- `tests/test_stage2_context.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`

## PASS 기록

- PASS 1: `5`개 후보 수집
  - 후보 1: `Stage2Finalizer`가 기대하는 `validate_arc_data_fields` repair hook가 실제 `Stage2Context`에는 없다.
  - 후보 2: `main_a -> Stage2/3/4 Context -> consumer` 바인딩 레이어가 MagicMock 분할 테스트에 의존한다.
  - 후보 3: `_extract_block_index()`, `_extract_pattern_keywords()`, `_pattern_presence_check()`, `_build_validation_context()`, `_load_genre_references()`는 현재 consumer graph가 없다.
  - 후보 4: `validate_arc_integrity()`의 falsy-check는 empty container를 missing key로 분류한다.
  - 후보 5: `validate_blueprint_integrity()`는 soft schema만 검사한다.
- PASS 2: `2`개 후보 제거
  - 후보 4 제거: `docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md`의 `[T1-10]`과 중복. facade contract 신규 이슈가 아니라 state_service 내부 코드 냄새에 가깝다.
  - 후보 5 제거: `docs/2026-03-12/TF-S3-context-contract-audit.md`에서 Stage3 soft schema 리스크로 이미 다뤘다.
- PASS 3: `3`개 확정
  - `P1 1건`, `P2 1건`, `P3 1건`

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MFS-T2-001 | P1 | confirmed | `Stage2Context.from_app` / `Stage2Finalizer.run_finalize` | `main_a`가 export한 `_validate_arc_data_fields()` repair hook가 실제 Stage2 context에 바인딩되지 않아 production Stage2 repair path가 죽어 있다 |
| MFS-T2-002 | P2 | confirmed | `main_a.py` facade shim / `Stage2Context` / `Stage3Context` / `Stage4Context` | live consumer들은 facade bound method가 아니라 MagicMock callback으로 검증돼 shim rename/signature drift를 놓칠 수 있다 |
| MFS-T2-003 | P3 | confirmed | `main_a.py` dormant shim set | 여러 T2 shim이 현재 runtime consumer 없이 service unit test로만 유지돼 facade surface 대비 실제 coverage가 과장돼 있다 |

## Findings

### [MFS-T2-001] `validate_arc_data_fields` repair hook가 Stage2 production graph에서 도달 불가

1. ID  
   `MFS-T2-001`
2. Severity  
   `P1`
3. 현상 요약  
   `main_a.py`는 `_validate_arc_data_fields()`를 `StateService` thin delegate로 export하지만, 실제 Stage2가 사용하는 `Stage2Context`는 이 callback 슬롯을 정의하지도 않고 `from_app()`에서 주입하지도 않는다. 그 결과 `Stage2Finalizer`의 repair-before-audit 경로는 테스트에서는 보이지만 production Stage2 graph에서는 영구적으로 비활성이다.
4. 코드 근거  
   - `main_a.py:2573`, `main_a.py:3640`, `main_a.py:3883`은 실제 Stage2 진입 시마다 `Stage2Context.from_app(self)`를 주입한다.
   - `main_a.py:2780-2782`는 `_validate_arc_data_fields()`를 `self._state_service.validate_arc_data_fields()`로 export한다.
   - `modules/core/stage2_context.py:46-100`의 `__slots__`, `modules/core/stage2_context.py:132-156`의 `__init__`, `modules/core/stage2_context.py:210-258`의 `from_app()` 어디에도 `validate_arc_data_fields`가 없다.
   - `modules/core/stage2_finalizer.py:905-916`은 `callable(getattr(self.ctx, "validate_arc_data_fields", None))`일 때만 repair hook를 호출한다.
5. downstream 영향 경계  
   Stage2 finalization 경계에 한정된다. `StateService.validate_arc_data_fields()`가 복구할 수 있는 `tactical_doc`, `beat_sequence`, `joint_docs`, `status_shadow`, `arc_drive`, `hybrid_composition`, `ep_count`, `ep_end` 보정이 실제 Stage2 run에서는 적용되지 않고, 이후 fallback repair 또는 `validate_arc_integrity()` hard gate로 바로 넘어간다. 즉 deterministic repair가 retry / `integrity_fail`로 승격될 수 있다.
6. 현재 테스트 근거 또는 테스트 부재  
   - `tests/test_stage2_finalizer.py:265-301`은 `finalizer.ctx`를 `MagicMock`로 두고 `validate_arc_data_fields`를 수동 주입해 helper 우선 경로를 녹색으로 만든다.
   - `tests/test_stage2_context.py`는 `Stage2Context` slot 집합을 검증하지만 `validate_arc_data_fields` 부재가 Stage2 finalizer semantics와 충돌하는지 보지 않는다.
   - 위 테스트들은 모두 통과했지만, 통과 자체가 이 drift를 가린다. 실제 실행 결과는 상단 테스트 실행 기록 참조.
7. 기존 문서와의 중복 여부  
   `related-but-new-facade-surface`  
   `docs/2026-03-13/four-project-1arc-merged-remediation-postfix-3pass-closure.md`는 MagicMock realism 문제를 다뤘지만, 실제 `main_a -> Stage2Context -> Stage2Finalizer` graph에서 callback slot 자체가 빠졌다는 점은 닫지 않았다.
8. 권장 후속 조치  
   `Stage2Context`에 `validate_arc_data_fields` 슬롯/생성자 인자/`from_app()` 바인딩을 추가하고, `Stage2Context.from_app(real_app)`를 사용한 finalizer regression test를 별도로 잠가야 한다.

### [MFS-T2-002] live validation shim 바인딩이 분할 테스트에만 잠겨 있다

1. ID  
   `MFS-T2-002`
2. Severity  
   `P2`
3. 현상 요약  
   `_validate_arc_mapping()`, `_validate_arc_integrity()`, `_validate_blueprint_integrity()`, `_build_item_acquisition_timeline()`은 모두 live consumer가 존재하지만, 현재 테스트는 `StateService`/`PromptBuilder` 구현 단위와 `Stage2/3/4` consumer 단위를 MagicMock로 분리해 검증한다. 따라서 `main_a.py`의 bound-method 이름, 시그니처, delegate 대상이 drift해도 consumer 테스트와 service 테스트가 동시에 녹색으로 남을 수 있다.
4. 코드 근거  
   - `main_a.py:2651-2653`, `main_a.py:2670-2691`, `main_a.py:2788-2794`는 live shim export를 제공한다.
   - `modules/core/stage2_context.py:236-241`은 `_validate_arc_mapping`, `_validate_arc_integrity`를 Stage2 callback으로 포획한다.
   - `modules/core/stage3_context.py:116-117`은 `_validate_arc_data_fields`, `_validate_blueprint_integrity`를 Stage3 callback으로 포획한다.
   - `modules/core/stage4_context.py:171-177`, `modules/core/stage4_context_builder.py:1863`은 `_build_item_acquisition_timeline()`을 Stage4 context에서 사용한다.
5. downstream 영향 경계  
   Stage2의 mapping correction / integrity gate, Stage3의 blueprint save gate, Stage4의 item timeline context에 영향을 준다. 현재 코드에서는 이름이 맞아 동작하지만, facade boundary audit 관점에서는 regression 검출력이 약하다.
6. 현재 테스트 근거 또는 테스트 부재  
   - `tests/test_state_service.py:80-357`은 `StateService` 구현을 직접 검증하지만 `main_a` bound method나 context binding은 보지 않는다.
   - `tests/test_stage2_context.py:91-106`은 일부 callback만 pinning하며 `validate_arc_mapping`, `validate_arc_integrity`는 검증하지 않는다.
   - `tests/test_stage2_validation_pipeline.py:31`, `tests/test_stage2_finalizer.py:30`은 context callback을 `MagicMock`로 주입한다.
   - `tests/test_stage3_orchestrator.py:806-811`, `tests/test_stage3_orchestrator.py:909-931`은 `_validate_blueprint_integrity`를 `MagicMock`로 pinning한다.
   - `tests/test_stage4_context.py:162-179`, `tests/test_stage4_context_builder.py:32-34`는 `_build_item_acquisition_timeline`을 `MagicMock` callback으로 대체한다.
7. 기존 문서와의 중복 여부  
   `related-but-new-facade-surface`  
   `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`는 Stage2 retry-feedback callback pinning 공백을 다뤘다. 이번 finding은 state-service validation shim과 Stage3/Stage4 consumer까지 포함한 `main_a` facade bound-method surface를 별도로 고정한다.
8. 권장 후속 조치  
   `main_a`의 실제 bound method를 가진 app stub 또는 lightweight app fixture를 사용해 `Stage2Context.from_app()`, `Stage3Context.from_app()`, `Stage4Context.from_app()` 이후 consumer가 real delegate를 타는 회귀 테스트를 추가해야 한다.

### [MFS-T2-003] T2 facade 일부는 현재 consumer graph가 없는 dormant surface다

1. ID  
   `MFS-T2-003`
2. Severity  
   `P3`
3. 현상 요약  
   `_extract_block_index()`, `_extract_pattern_keywords()`, `_pattern_presence_check()`, `_build_validation_context()`, `_load_genre_references()`는 `main_a.py`에 facade로 남아 있지만 현재 `modules/` consumer graph에서 호출되지 않는다. 실제 사용 흔적은 `StateService` 내부 구현 또는 `tests/test_state_service.py`뿐이다.
4. 코드 근거  
   - 정의 위치: `main_a.py:2666-2679`, `main_a.py:2685-2691`, `main_a.py:2784-2786`
   - `modules/core/stage2_context.py:236-241`는 이들 helper를 callback으로 노출하지 않는다.
   - repo-wide search 기준 `modules/`/`tests/`에서 위 helper 이름들은 정의부와 `tests/test_state_service.py` 외 호출처가 없다.
5. downstream 영향 경계  
   현재 확인된 runtime consumer는 없다. 영향은 즉시 런타임 오동작보다는 stale API surface, audit noise, future refactor ambiguity, facade coverage 과장에 가깝다.
6. 현재 테스트 근거 또는 테스트 부재  
   `tests/test_state_service.py:60-156`, `tests/test_state_service.py:290-357`가 underlying service behavior는 확인하지만 `main_a` facade export나 실제 consumer는 검증하지 않는다.
7. 기존 문서와의 중복 여부  
   `none`
8. 권장 후속 조치  
   실제 consumer를 다시 연결할 계획이 없다면 dormant facade를 축소하거나, 유지가 필요하다면 어떤 consumer가 써야 하는지 문서와 테스트에 명시해야 한다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `load_genre_references()` success path | 미잠금 | 현재 `tests/test_state_service.py:290-299`는 missing-file path만 본다. 장르별 파일 fallback, `reference_loaded`/`reference_load_error` audit payload를 잠그는 테스트가 필요하다 |
| `validate_blueprint_integrity()` list→dict normalization | 부분 잠금 | 구현(`modules/core/services/state_service.py:358-368`)은 존재하지만 테스트는 non-dict / missing-key / happy path만 본다. 다만 soft schema 자체는 기존 Stage3 감사 문서와 중복되므로 신규 finding으로는 승격하지 않았다 |
| `_build_item_acquisition_timeline()` real facade path | 미잠금 | `PromptBuilder` 단위 테스트와 Stage4 context MagicMock 테스트는 있으나, `main_a` bound method를 통한 Stage4ContextBuilder real path 테스트는 없다 |

## PASS1 -> PASS2 -> PASS3 요약

- PASS1 후보 `5`건을 수집했다.
- PASS2에서 기존 문서와 중복되는 `2`건을 제거했다.
  - `validate_arc_integrity()` falsy-check smell -> `already-covered-do-not-reopen`
  - Stage3 blueprint soft schema -> `already-covered-do-not-reopen`
- PASS3에서 `3`건을 확정했다.
  - `MFS-T2-001` `P1`
  - `MFS-T2-002` `P2`
  - `MFS-T2-003` `P3`

## 마감 체크

- 코드 근거 포함: `Yes`
- downstream 영향 경계 포함: `Yes`
- 현재 테스트 근거 또는 테스트 부재 포함: `Yes`
- 기존 문서와의 중복 여부 포함: `Yes`
