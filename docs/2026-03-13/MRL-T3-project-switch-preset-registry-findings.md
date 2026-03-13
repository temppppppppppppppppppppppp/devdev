# [MRL-T3] Project Switch / Preset Registry Findings

> 작성일: 2026-03-13
> 상태: `3pass executed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`

---

## 조사 범위

- `main_a.py`
  - `boot()`
  - `_restore_preset_registry()`
  - preset / genre / state-tracker 재바인딩 경로
- `modules/core/services/project_service.py`
  - `_restore_runtime_state()`
  - `reset_stage_2()`
  - `rewind_stage_2()`
  - `rollback_episode()`
  - `wipe_production_data()`
- 직접 downstream
  - `modules/core/project_manager.py`
  - `modules/core/stage0/preset_registry.py`
  - `modules/domain/agents/state_tracker.py`
  - `modules/domain/agents/state_tracker_npc.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage3_orchestrator.py`

## 필수 근거

- `tests/test_project_service.py`
- `tests/property/test_db_rollback_props.py`
- `modules/core/services/project_service.py`
- `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`
- 추가 확인
  - `tests/chaos/test_partial_commit.py`
  - `tests/integration/test_patch_wiring.py`
  - `tests/test_process_runner.py`
  - `tests/test_stage2_context.py`
  - `tests/test_stage2_pipeline.py`
  - `tests/test_stage3_orchestrator.py`
  - `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`
  - `docs/2026-02-23/opus_tf7_patch_order.md`

## PASS 기록

- PASS 1: 완료
  - 후보 5건 수집
  - stale preset, helper bypass, genre/preset truth-source split, destructive recovery partial-success masking, config rebound drift 가능성을 분리했다.
- PASS 2: 완료
  - 관련 테스트
    - `pytest -q tests/test_project_service.py tests/property/test_db_rollback_props.py tests/chaos/test_partial_commit.py tests/integration/test_patch_wiring.py tests/test_stage2_context.py tests/test_stage2_pipeline.py tests/test_stage3_orchestrator.py`
    - 결과: `207 passed in 5.79s`
  - ad hoc verification 2건 수행
    - `PresetRegistry(base_genre='investment')`와 `StateTracker` 조합이 `capital` 필드는 만들고 `internal_energy`는 만들지 않는지 확인
    - malformed `preset_state` + 기존 preset 보유 상태에서 `rollback_episode()`가 `True`를 반환하면서 기존 preset을 유지하는지 확인
  - `MPN-T1-001`, `MDH-T4-004`, `MCP-T5-002`, `MCP-T4` coverage gap과 중복 여부 교차 검증
- PASS 3: 완료
  - PASS1 후보 5건 -> PASS2 제거 3건 -> 최종 2건

## Executive Summary

- boot 경로는 `selected_genre`와 `preset_state`를 별도 truth source로 읽고, 장르 불일치 경고에서 사용자가 계속을 선택해도 둘을 재정렬하지 않는다. 그 결과 preset schema와 genre-bound runtime config가 서로 다른 장르를 볼 수 있다.
- destructive recovery 경로는 preset restore 실패를 성공 판정에 반영하지 않는다. rollback/reset/wipe는 preset 복원 실패 후에도 성공 로그와 `True`를 반환해 partial runtime restore를 은닉한다.

## PASS 2 제거 항목

| 후보 | 판정 | 이유 |
|----|----|----|
| `_restore_preset_registry()` no-data/malformed path가 stale preset을 남긴다 | 제거 | `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`의 `MPN-T1-001`에서 이미 닫힌 항목이다. 이번 문서에서는 동일 결함을 재오픈하지 않고 lifecycle 의미만 별도로 평가했다. |
| boot 인라인 restore와 callback restore가 중복 구현이라 drift 위험이 있다 | 제거 | `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`의 `MDH-T4-004`가 이미 helper bypass 관점으로 고정했다. |
| `models.yaml` / `settings.json` project-local config가 rollback/wipe 뒤 잘못 rebinding된다 | 제거 | 현재 조사 범위에서는 destructive op가 같은 `current_project` 내부에서만 동작하며, project-local config 경로가 실제로 다른 프로젝트 source로 바뀌는 증거를 확인하지 못했다. config rebound 이슈는 genre/preset split에 한정해 retained 했다. |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MRL-T3-001 | P1 | retained | `main_a.py::boot`, `preset_registry`, Stage 2/3/4 tracker init | 장르 불일치 continue 경로가 `selected_genre`와 `preset_registry.base_genre`를 다른 truth source로 남겨 preset schema와 genre-bound runtime config가 분리된다 |
| MRL-T3-002 | P2 | retained | `project_service.py::_restore_runtime_state`, destructive recovery entrypoints | preset restore 실패가 recovery success 판정에 반영되지 않아 rollback/reset/wipe가 partial runtime restore를 성공처럼 숨긴다 |

---

## [MRL-T3-001] P1 | boot/project switch가 `selected_genre`와 `preset_registry`를 서로 다른 truth source로 유지한다

**Severity**

- `P1`

**현상 요약**

boot는 먼저 사용자가 고른 `selected_genre`로 프로젝트를 연 뒤, 별도로 DB `preset_state`에서 `preset_registry`를 복원한다. 이후 `genre_info`가 다르더라도 경고 후 계속 진행할 수 있는데, 이 분기에서 `selected_genre`와 `preset_registry.base_genre`를 맞추는 재바인딩이 없다. 결과적으로 HUD/Guard/genre-specific extract는 현재 선택 장르를 쓰고, preset schema와 일부 tracker label은 저장된 preset 장르를 쓴다.

**코드 근거**

- `main_a.py:1044-1055`
  - boot가 먼저 `self.selected_genre = self._select_genre()`를 수행하고 그 장르로 프로젝트를 연다.
- `main_a.py:1080-1089`
  - 같은 boot 안에서 DB `preset_state`를 읽어 `self.preset_registry`를 별도로 복원한다.
- `main_a.py:1096-1109`
  - `genre_info` 불일치 시 경고만 하고, 사용자가 `y`를 고르면 `selected_genre`/`preset_registry` 어느 쪽도 재정렬하지 않는다.
- `main_a.py:1118-1129`
  - HUD와 Guard는 `self.selected_genre["type"]` 기준으로 다시 바인딩된다.
- `modules/core/stage0/preset_registry.py:457-491,720-739`
  - `PresetRegistry`는 `base_genre`와 `active_presets` 순서로 필드 스키마를 구성한다.
- `modules/core/stage2_orchestrator.py:242-255`
  - `StateTracker(preset_registry=self.ctx.preset_registry, ...)`로 tracker를 만들고, arc extract 장르만 `self.ctx.selected_genre`에서 읽는다.
- `modules/core/stage3_orchestrator.py:635-640`
  - Stage 3 lazy init도 같은 패턴을 반복한다.
- `main_a.py:3483-3491`
  - Stage 4 직행 lazy init 역시 `preset_registry`와 `selected_genre`를 따로 소비한다.
- `modules/domain/agents/state_tracker.py:177-180,254-266`
  - tracker 기본 필드는 `preset_registry`에서 만들고, genre argument는 별도로 받는다.
- `modules/domain/agents/state_tracker_npc.py:538-540,2114-2119`
  - skill label 등 일부 downstream는 `preset_registry.base_genre`를 직접 참조한다.

**downstream 영향 경계**

- 저장된 프로젝트가 `investment` preset을 갖고 있는데 사용자가 `wuxia`로 계속 진행하면, HUD/Guard/genre-specific extract는 `wuxia` 기준으로 움직이면서 tracker 필드와 preset prompt schema는 `investment` 필드를 유지할 수 있다.
- project switch 직후, 다음 Stage 2/3/4 진입, Stage 4 direct boot에서 같은 split-brain이 반복될 수 있다.
- 이 경로는 단순 UI 경고가 아니라 runtime object graph의 truth source가 둘로 갈라지는 문제라 다음 작업 결과를 오염시킨다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_process_runner.py:114-146`
  - mismatch일 때 confirm 입력을 주입하는지만 검증하고, confirm 이후 runtime alignment는 보지 않는다.
- `tests/test_stage2_pipeline.py:65-83`
  - `selected_genre`와 `preset_registry`를 단순 mock으로 제공하지만 두 값의 일치 invariant는 검증하지 않는다.
- `tests/test_stage3_orchestrator.py:983-1000`
  - `Stage3Context.from_app()`가 두 슬롯을 전달하는지만 확인한다.
- ad hoc verification
  - `PresetRegistry(base_genre='investment')`로 만든 `StateTracker`는 `capital` 필드를 만들고 `internal_energy`는 만들지 않았다.
  - 같은 재현에서 downstream genre 인자는 별도 `selected_genre='wuxia'`라고 가정할 수 있어, tracker schema와 genre path가 다른 source를 보는 구조가 실제 코드로 확인됐다.

**기존 문서와의 중복 여부**

- `duplicate status`: `related-but-new-runtime-lifecycle-surface`
- 관련 문서
  - `docs/2026-03-13/MCP-T5-control-contract-regression-findings.md`의 `MCP-T5-002`는 mismatch confirm 입력 시퀀스 문제다.
  - 이번 finding은 confirm 이후 실제 runtime graph가 어떻게 split되는지에 관한 신규 lifecycle surface다.
  - `docs/2026-02-23/opus_tf7_patch_order.md:83-92`는 restart/rollback 뒤 preset 재사용을 요구했지만, `selected_genre`와 preset truth source 정렬 조건은 정의하지 않았다.

**권장 후속 조치**

- boot/project switch에서 `selected_genre`, `genre_info`, `preset_registry.base_genre` 중 하나를 단일 authoritative source로 고정한다.
- mismatch confirm을 유지할 거면, continue 시 `preset_registry`를 선택 장르 기준으로 재구성하거나 반대로 `selected_genre`를 저장된 project 장르로 재바인딩해야 한다.
- 회귀 테스트를 추가한다.
  - stored `genre_info/preset_state=investment`, selected `wuxia`, confirm=`y`일 때 Stage 2/3/4 진입 전 `selected_genre["type"] == preset_registry.base_genre`
  - mismatch continue 후 tracker 필드셋과 HUD 장르가 같은 source를 보는지 검증

---

## [MRL-T3-002] P2 | destructive recovery가 preset restore failure를 성공처럼 숨긴다

**Severity**

- `P2`

**현상 요약**

`ProjectService._restore_runtime_state()`는 preset restore callback을 non-blocking으로 처리한다. 그런데 `reset_stage_2()`, `rewind_stage_2()`, `rollback_episode()`, `wipe_production_data()`는 이 호출 뒤 즉시 성공 로그를 남기고 `True`를 반환한다. 실제 app callback인 `_restore_preset_registry()`는 malformed payload를 내부에서 log-only 처리하고 기존 `self.preset_registry`를 그대로 둘 수 있으므로, destructive recovery가 partial runtime restore 상태를 성공으로 포장한다.

**코드 근거**

- `main_a.py:318-330`
  - `ProjectService`에 `preset_registry_restorer=self._restore_preset_registry`를 주입한다.
- `modules/core/services/project_service.py:63-99`
  - `_restore_runtime_state()`는 `_load_from_db()` 뒤 `preset_registry_restorer()`를 호출하지만, 예외는 `"restore failed (ignored)"`로 삼키고 상태 반환값도 없다.
- `main_a.py:379-389`
  - `_restore_preset_registry()`는 `from_json(...)` 실패를 log-only 처리하며 기존 `self.preset_registry`를 비우지 않는다.
- `modules/core/project_manager.py:141-146`
  - `_load_from_db()`는 `_preset_state_raw`만 채우고 app-level `preset_registry` 재구성 자체는 callback에 의존한다.
- `modules/core/services/project_service.py:192-195`
  - `reset_stage_2()`는 `_restore_runtime_state(1)` 뒤 성공 로그를 남기고 `True`를 반환한다.
- `modules/core/services/project_service.py:259-262`
  - `rewind_stage_2()`도 동일하다.
- `modules/core/services/project_service.py:347-351`
  - `rollback_episode()`도 동일하다.
- `modules/core/services/project_service.py:404-407`
  - `wipe_production_data()`도 동일하다.

**downstream 영향 경계**

- operator는 rollback/reset/wipe가 완전히 끝났다고 보지만, 실제 app memory 안의 `preset_registry`는 이전 프로젝트/이전 stage의 값을 그대로 들고 있을 수 있다.
- `_restore_runtime_state()`는 `state_tracker`를 무효화하므로, 다음 Stage 2/3/4 진입 시 새 tracker가 stale `app.preset_registry`를 다시 소비할 위험이 있다.
- 즉 DB는 되감겼는데 runtime preset schema는 되감기지 않은 partial restore가 success verdict 뒤에 남는다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_project_service.py:53-60`
  - 기본 fixture가 `preset_registry_restorer`를 아예 주입하지 않는다.
- `tests/property/test_db_rollback_props.py:23-34`
  - invariant helper용 최소 서비스도 `preset_registry_restorer=None`이다.
- `tests/integration/test_patch_wiring.py:419-428,489-498`
  - emotion/state-delta wiring만 보고 preset restorer는 `None`이다.
- `tests/chaos/test_partial_commit.py:23-34`
  - partial commit chaos fixture 역시 preset restorer를 비운다.
- ad hoc verification
  - malformed `preset_state.discovered_fields`를 가진 synthetic app에 실제 `_restore_preset_registry` 로직을 연결해 `rollback_episode()`를 실행한 결과, 메서드는 `True`를 반환했고 preset restore failure log 뒤에 rollback success log가 이어졌으며 `preset_registry`는 기존 값 `OLD`로 남았다.

**기존 문서와의 중복 여부**

- `duplicate status`: `related-but-new-runtime-lifecycle-surface`
- 관련 문서
  - `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`의 `MPN-T1-001`은 stale preset retention 자체를 다뤘다.
  - `docs/2026-03-13/MCP-T4-destructive-ops-recovery-findings.md`는 preset restore callback test gap을 coverage gap으로 남겼다.
  - 이번 finding은 실제 recovery success verdict가 partial preset restore를 숨긴다는 lifecycle contract 문제를 신규로 고정한다.

**권장 후속 조치**

- `_restore_runtime_state()`가 `preset_restore_ok`, `preset_restore_reason` 같은 구조화 결과를 반환하도록 바꾼다.
- 최소한 malformed/no-data/exception 경로에서는 `app.preset_registry`를 명시적으로 초기화하고, recovery 메서드가 partial-success를 구분하도록 한다.
- 회귀 테스트를 추가한다.
  - `rollback_episode()` + malformed `preset_state` -> stale preset clear 또는 structured partial result 검증
  - `reset_stage_2()` / `wipe_production_data()`에 실제 `preset_registry_restorer`를 연결한 상태에서 success/failure surface 검증

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| mismatch continue 후 runtime alignment | 테스트 부재 | boot 경로에서 `selected_genre`, `genre_info`, `preset_registry.base_genre` 일치 invariant를 검증하는 regression test |
| destructive op + real preset restorer wiring | 테스트 부재 | `preset_registry_restorer=self._restore_preset_registry`를 실제로 연결한 unit/integration test |
| rollback 후 다음 Stage 2/3/4 진입 | 테스트 부재 | malformed/no-data preset restore 뒤 tracker가 어떤 schema를 쓰는지 보는 e2e/regression test |

## 마감 체크

- stale preset 자체 재오픈: 하지 않음 (`MPN-T1-001`로 정리)
- helper bypass 재오픈: 하지 않음 (`MDH-T4-004`로 정리)
- genre/preset truth-source split: lifecycle finding 1건 확정
- destructive recovery partial-success masking: lifecycle finding 1건 확정

## 최종 판정

- 최종 retained finding: `2건`
  - `P1`: 1건
  - `P2`: 1건
  - `P3`: 0건
- 본 문서는 `template / not executed`가 아니라 `executed T3 finding set`이다.
