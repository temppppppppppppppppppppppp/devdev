# [MFS-T4] UI / Stage01 Presentation Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 complete`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-facade-shim-detail-full-survey-audit-order.md`
> 실행 검증: `pytest tests/test_prompt_builder.py tests/test_ui_service.py tests/test_stage4_context.py tests/test_stage01_helpers.py tests/test_state_service.py tests/test_stage4_cv_context.py tests/test_stage4_interview_round.py -q` → `250 passed`

이 문서는 `Terminal 4 - Prompt / NPC / UI Presentation Shim` 실행 결과다. 조사 중 코드 직접 수정은 수행하지 않았다.

---

## 조사 범위

- `main_a.py`
  - `_extract_npc_profiles()`
  - `_get_character_traits()`
  - `_load_character_archetypes()`
  - `_get_archetype_reference_for_npcs()`
  - `_show_volume_table()`
- `modules/core/prompt_builder.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage4_context.py`
- 교차 확인에 사용한 실제 Stage4 consumer
  - `modules/core/stage4_interview_round.py`
  - `modules/validation/consistency_validator.py`

## 필수 근거

- `tests/test_prompt_builder.py`
- `tests/test_ui_service.py`
- `tests/test_stage4_context.py`
- `docs/stage_map/stage1.md`

## PASS 기록

### PASS 1 - 표면 수집

- 후보 1: Stage4 live validation context가 `main_a.py` NPC facade 표면을 실제로 소비하는지 점검
- 후보 2: `_show_volume_table()`가 Stage 1 문서 기대와 같은 operator-facing 의미를 유지하는지 점검
- 후보 3: `extract_npc_profiles()`의 exact-name 매칭이 alias/별호를 누락하는지 점검
- 후보 4: `Stage4Context.from_app()`가 T4 helper를 직접 DI하는지 점검

### PASS 2 - 교차 검증

- 후보 3 제거
  - `extract_npc_profiles()` exact-name 매칭 자체는 취약하지만, 현재 Stage4 live consumer는 이 helper를 전혀 호출하지 않는다.
  - 현재 문제는 alias 누락보다 `facade는 남아 있는데 consumer graph가 helper를 우회한다`는 계약 드리프트 쪽이 더 직접적이다.
- 후보 4 제거
  - `Stage4Context.from_app()`의 미주입은 단독 finding보다 `Stage4 live path가 NPC facade를 소비하지 않는다`는 확정 finding의 근거로 흡수하는 편이 정확하다.

### PASS 3 - 최종 확정

- 확정 finding 2건
- Severity tally
  - `P1`: 1건
  - `P3`: 1건

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MFS-T4-001` | `P1` | confirmed | `Stage4InterviewRound._build_cv_context`, `main_a.py` NPC facade | Stage4 live validation path가 `main_a.py` NPC facade를 우회하고 `npc_profiles`를 빈 dict로 넘겨 NPC attitude 검사를 사실상 비활성화한다. |
| `MFS-T4-002` | `P3` | confirmed | `UIService.show_volume_table`, `Stage01Helpers.stage_1_volumes`, `main_a.py._show_volume_table` | `_show_volume_table()` 경유 UI가 실제 권 수와 무관하게 `10권` 고정 타이틀을 출력해 Stage 1 완료 표시의 의미를 왜곡한다. |

## 상세 Findings

### MFS-T4-001

1. ID
   `MFS-T4-001`
2. Severity
   `P1`
3. 현상 요약
   `main_a.py`는 `_extract_npc_profiles()`, `_get_character_traits()`, `_load_character_archetypes()`, `_get_archetype_reference_for_npcs()`를 facade로 유지하지만, 실제 Stage4 manuscript validation 경로는 이 표면을 사용하지 않는다. live consumer인 `Stage4InterviewRound._build_cv_context()`는 `npc_profiles`를 빈 dict로 초기화한 채 `ConsistencyValidator.validate()`에 넘기고, `ConsistencyValidator._check_attitude_transition()`은 `npc_profiles`가 비면 즉시 PASS로 빠진다. 결과적으로 NPC facade 표면이 살아 있어도 Stage4의 NPC 태도 전환 검사는 facade와 분리된 채 약화된다.
4. 코드 근거
   - `main_a.py:2697-2711`
     - `_extract_npc_profiles()`, `_get_character_traits()`, `_load_character_archetypes()`, `_get_archetype_reference_for_npcs()`가 모두 `StateService` thin delegate로 남아 있다.
   - `modules/core/prompt_builder.py:894-938`
     - `build_validation_context()`는 `MasterBible.AssetLibrary.KeyNPCs`를 읽어 `context["npc_profiles"]`를 채운다.
   - `modules/core/prompt_builder.py:961-991`
     - `extract_npc_profiles()`와 `get_character_traits()`는 별도 helper로 남아 있으나 live Stage4 path에서 재사용되지 않는다.
   - `modules/core/stage4_context.py:95-101`, `modules/core/stage4_context.py:171-177`
     - `Stage4Context.from_app()`는 `get_int_input`, `build_item_acquisition_timeline`, `flush_audit_buffer`, `safe_commit` 등 7개 callback만 DI하고 T4 NPC helper는 연결하지 않는다.
   - `modules/core/stage4_interview_round.py:3477-3485`
     - `_build_cv_context()`가 `npc_profiles`를 `{}`로 시작한다.
   - `modules/core/stage4_interview_round.py:2110`
     - 조립된 `_cv_context`가 그대로 `consistency_validator.validate(_cv_ms, _cv_context)`에 전달된다.
   - `modules/validation/consistency_validator.py:412-423`
     - `_check_attitude_transition()`는 `npc_profiles`가 비거나 dict가 아니면 `{"passed": True, "violations": []}`로 즉시 종료한다.
5. downstream 영향 경계
   - 직접 영향은 Stage4 원고 후보 검증 중 `ConsistencyValidator`의 NPC 태도 전환 체크다.
   - `main_a.py` facade 쪽에서 NPC helper 의미를 바꿔도 live Stage4 path는 변하지 않으므로, facade와 실제 validation semantics가 계속 분리될 수 있다.
   - `npc_profiles`를 통해 활성화돼야 하는 NPC 관계/태도 drift 검출이 약해져, 경계선 원고가 더 높은 점수 또는 더 적은 경고로 통과할 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_prompt_builder.py:453-457`
     - `extract_npc_profiles()`와 `get_character_traits()`는 `app=None` 가드만 본다.
   - `tests/test_state_service.py:153-225`
     - facade가 `PromptBuilder` 또는 파일 로딩에 위임되는지만 검증한다.
   - `tests/test_stage4_context.py:140-191`
     - `Stage4Context`는 7개 callback 존재/부재만 검증하고 T4 NPC helper surface는 다루지 않는다.
   - `tests/test_stage4_cv_context.py:133-341`
     - `protagonist_name`, `prev_hud`, `karma_matrix`, `villain_context`는 검증하지만 `npc_profiles` populate 여부는 검증하지 않는다.
   - `tests/test_stage4_interview_round.py:365-421`
     - `time_warnings`, `blueprint_text`는 확인하지만 `npc_profiles` contract는 확인하지 않는다.
   - 위 관련 테스트들은 현재 전부 통과한다. 즉 회귀 테스트가 live NPC facade bypass를 잡지 못한다.
7. 기존 문서와의 중복 여부
   `related-but-new-facade-surface`
   - `docs/2026-02-25/tf_runtime_diagnosis.md`는 Stage4 validation context의 `npc_profiles` 미주입을 runtime 문제로 언급했다.
   - 이번 finding은 그보다 한 단계 더 나가, `main_a.py` facade surface가 여전히 존재하는데도 live Stage4 consumer graph가 그 facade를 전혀 사용하지 않는다는 계약 드리프트를 확정한다.
8. 권장 후속 조치
   - Stage4 live `_cv_context`가 `PromptBuilder/StateService`와 동일한 NPC sourcing contract를 쓰도록 정렬하거나, 반대로 현재 비사용 facade를 공식적으로 제거 또는 deprecated 처리한다.
   - `tests/test_stage4_cv_context.py` 또는 `tests/test_stage4_interview_round.py`에 `npc_profiles` non-empty population과 `ConsistencyValidator` input parity를 고정하는 회귀 테스트를 추가한다.
   - `_extract_npc_profiles()`와 `build_validation_context()["npc_profiles"]` 중 어느 의미가 SSOT인지 문서로 명시한다.

### MFS-T4-002

1. ID
   `MFS-T4-002`
2. Severity
   `P3`
3. 현상 요약
   `_show_volume_table()`는 Stage 1 완료 후 operator가 결과를 확인하는 presentation callback인데, 실제 UI 구현은 테이블 제목을 항상 `10권 전략 설계 상업성 성적표`로 고정한다. Stage 1은 실제 아크 수에 따라 1권 등 비-10권 결과도 정상 생성할 수 있으므로, callback 출력이 저장된 `final_volumes`와 다른 의미를 보여준다.
4. 코드 근거
   - `main_a.py:2796-2798`
     - `_show_volume_table()`는 `UIService.show_volume_table()` thin delegate다.
   - `modules/core/stage01_helpers.py:836-839`
     - Stage 1 완료 시 `save_v20_anchor("volumes", final_volumes)` 후 즉시 `app._show_volume_table(final_volumes)`를 호출한다.
   - `modules/core/services/ui_service.py:86-101`
     - 테이블 제목이 `📊 [V20] 10권 전략 설계 상업성 성적표`로 하드코딩돼 있다.
   - `docs/stage_map/stage1.md:28`, `docs/stage_map/stage1.md:70`, `docs/stage_map/stage1.md:125`
     - Stage 1 map은 `_show_volume_table(final_volumes)`를 operator completion check로 명시한다.
5. downstream 영향 경계
   - DB 저장과 메모리 갱신은 이미 끝난 뒤라 flow control 자체를 막지는 않는다.
   - 다만 Stage 1 완료 확인용 UI가 실제 결과 개수를 잘못 라벨링해 운영자 판단과 감리 로그를 오염시킬 수 있다.
   - 특히 소형 fixture, partial roadmap, 비-10권 프로젝트에서 presentation drift가 즉시 드러난다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_ui_service.py:116-127`
     - `console.print`가 한 번 호출되는지만 확인하고 제목 문자열이나 권 수 동적 반영은 검증하지 않는다.
   - `tests/test_stage01_helpers.py:519-544`
     - 성공 경로에서 `save_v20_anchor("volumes", ...)`만 확인하고 `_show_volume_table()` 호출이나 전달 payload는 검증하지 않는다.
   - `tests/test_stage01_helpers.py:519-544`는 1권 fixture를 사용하지만, 이 조건에서도 UI 타이틀 mismatch는 검출되지 않는다.
7. 기존 문서와의 중복 여부
   `none`
8. 권장 후속 조치
   - 테이블 제목을 `len(volumes)` 기반 동적 문구로 바꾸거나, 최소한 권 수를 특정하지 않는 중립 제목으로 변경한다.
   - `tests/test_ui_service.py`에 제목 문자열 검증을 추가한다.
   - `tests/test_stage01_helpers.py`에 `_show_volume_table(final_volumes)` 호출과 1권 fixture 대응을 고정하는 회귀 테스트를 추가한다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `main_a.py` T4 facade 직접 회귀 | 없음 | `main_a._extract_npc_profiles()` / `main_a._show_volume_table()`를 직접 호출하는 facade-level regression test |
| genre reference helper live consumer | 불명확 | `_load_character_archetypes()` / `_get_archetype_reference_for_npcs()`가 실제 프롬프트 조립에 쓰이는지 확인하는 runtime 또는 integration 근거 |

## PASS 요약

- PASS1 후보: 4건
- PASS2 제거: 2건
  - alias exact-match 문제는 live consumer 부재로 단독 확정 보류
  - `Stage4Context` 미주입은 standalone defect가 아니라 `MFS-T4-001` 근거로 흡수
- PASS3 확정: 2건
  - `MFS-T4-001` `P1`
  - `MFS-T4-002` `P3`

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
