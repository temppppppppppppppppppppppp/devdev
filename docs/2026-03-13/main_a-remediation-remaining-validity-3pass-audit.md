# main_a Remaining Remediation Validity 3pass Audit

> 작성일: 2026-03-13
> 상태: `executed / PASS3 completed`
> 조사 모드: `read-only code and test verification / no code edits / UTF-8 only`
> 대상 SSOT:
> - `main_a-retry-feedback-detail-remediation-execution-ssot.md`
> - `main_a-persistence-narrative-detail-remediation-execution-ssot.md`
> - `main_a-facade-shim-detail-remediation-execution-ssot.md`

## 목적

세 execution SSOT가 아직 `execution-ready`로 남아 있는데, 이것이 실제 미완료 때문인지, 아니면 문서 상태만 stale인지 현재 코드베이스 기준으로 3pass 재감리한다.

## 결론 요약

- `retry-feedback` SSOT: 현재 코드베이스 기준으로 남은 remediation 항목이 유효하다고 보기 어렵다. 문서 상태가 stale일 가능성이 높다.
- `persistence-narrative` SSOT: 현재 코드베이스 기준으로 남은 remediation 항목이 유효하다고 보기 어렵다. 문서 상태가 stale일 가능성이 높다.
- `facade-shim` SSOT: 문서 상태만 stale인 것은 아니다. 남은 항목 중 일부는 현재 코드베이스에서도 여전히 유효하다.
  - 여전히 유효: `FS-E4 / MFS-T4-001`
  - 부분 유효: `FS-E5 / MFS-T4-002`
  - 이미 해소됨: `FS-E5 / MFS-T3-03`

## PASS 기록

### PASS 1. SSOT remaining package inventory

- 세 SSOT 모두 header가 아직 `execution-ready`다.
- `retry-feedback`는 `RF-E1`~`RF-E4`가 문서상 미종결 상태다.
- `persistence-narrative`는 `PN-E1`~`PN-E5`가 문서상 미종결 상태다.
- `facade-shim`은 `FS-E4`, `FS-E5`가 문서상 남아 있다.

### PASS 2. current code / test evidence check

실코드와 회귀 테스트를 남은 acceptance 기준으로 대조했다.

- focused regression:
  - `pytest -q tests/test_main_a_retry_feedback.py tests/test_feedback_system.py tests/test_stage2_context.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage2_finalizer.py tests/test_arc_difficulty.py tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py tests/test_main_a_persistence_helpers.py tests/test_project_service.py tests/test_stage01_helpers.py tests/test_stage2_orchestrator.py tests/test_stage4_context_builder.py`
  - 결과: `423 passed`
- residual facade gap confirmation:
  - `pytest -q tests/test_stage4_cv_context.py tests/test_ui_service.py tests/test_stage3_orchestrator.py`
  - 결과: `92 passed`

### PASS 3. residual validity re-check

- `retry-feedback`와 `persistence-narrative`는 테스트/코드 근거가 SSOT acceptance와 대체로 합치한다.
- `facade-shim`은 일부 acceptance가 실제 코드에서 아직 닫히지 않았고, 관련 테스트도 그 gap을 잡지 못한다.

## Finding Ledger

| ID | Sev | 상태 | 대상 | 요약 |
|----|-----|------|------|------|
| `RRV-01` | `P2` | confirmed | `retry-feedback` SSOT | 코드/테스트 기준으로 `RF-E1`~`RF-E4`는 대부분 이미 반영되어 있고, 문서 상태만 stale일 가능성이 높다 |
| `RRV-02` | `P2` | confirmed | `persistence-narrative` SSOT | 코드/테스트 기준으로 `PN-E1`~`PN-E5`는 대부분 이미 반영되어 있고, 문서 상태만 stale일 가능성이 높다 |
| `RRV-03` | `P1` | confirmed | `facade-shim` SSOT | `FS-E4 / MFS-T4-001`은 현재 코드에서도 여전히 live issue다. Stage4 `_build_cv_context()`가 `npc_profiles`를 빈 dict로 고정한다 |
| `RRV-04` | `P2` | confirmed | `facade-shim` SSOT | `FS-E5`는 부분 stale이다. `MFS-T3-03`은 해소됐지만 `MFS-T4-002`는 아직 남아 있다. UI table title이 여전히 고정 `10권`이다 |
| `RRV-05` | `P3` | confirmed | 문서 상태 | `retry-feedback`, `persistence-narrative`용 acceptance 문서가 없어 code-complete와 doc-complete가 분리돼 보인다 |

## SSOT별 판정

### 1. Retry Feedback

판정:

- 현재 코드베이스 기준 `remaining valid work: none found`
- 분류: `document stale / code likely complete`

근거:

- facade wrapper와 retry helper surface가 live 상태다.
  - `main_a.py:694`
  - `main_a.py:765`
  - `main_a.py:771`
  - `main_a.py:779`
  - `main_a.py:787`
- Stage2 callback contract와 missing-callback tier 구분이 구현/테스트돼 있다.
  - `modules/core/stage2_context.py:89`
  - `tests/test_stage2_context.py:172`
- rejection taxonomy와 `specific_issue` 반영이 구현/테스트돼 있다.
  - `main_a.py:818`
  - `tests/test_main_a_retry_feedback.py:17`
  - `tests/test_stage2_finalizer.py:188`
- `current_arc_no` fallback semantics, multi-arc energy parity, minimal context wiring 테스트가 있다.
  - `tests/test_prompt_builder.py:509`
  - `tests/test_feedback_system.py:315`
  - `tests/test_stage2_preflight.py:268`
- Stage4 -> Stage3 external feedback 및 Stage4 -> Stage2 semantic failure 보존 테스트가 있다.
  - `tests/test_stage4_orchestrator.py:737`
  - `tests/test_arc_difficulty.py:53`
  - `tests/test_stage2_preflight_helpers.py:1054`
- 전용 acceptance 문서는 없다. 따라서 문서 상태는 stale로 보인다.

판정 메모:

- `RF-E1`~`RF-E4`는 현재 코드와 회귀 테스트가 SSOT acceptance를 사실상 충족하는 쪽에 가깝다.
- 문서 기준 미종결이지만, 현 코드베이스 기준 “남은 implementation 작업”으로 재등록할 근거는 약하다.

### 2. Persistence Narrative

판정:

- 현재 코드베이스 기준 `remaining valid work: none found`
- 분류: `document stale / code likely complete`

근거:

- protagonist source와 protagonist dedupe 보정이 구현/테스트돼 있다.
  - `main_a.py:2160`
  - `main_a.py:2204`
  - `tests/test_main_a_persistence_helpers.py:19`
  - `tests/test_main_a_persistence_helpers.py:32`
- arc mapping과 nullable callback 방어가 구현/테스트돼 있다.
  - `main_a.py:2682`
  - `tests/test_main_a_persistence_helpers.py:42`
- preset restore / cache persistence failure handling이 구현/테스트돼 있다.
  - `main_a.py:391`
  - `main_a.py:1316`
  - `tests/test_main_a_persistence_helpers.py:57`
  - `tests/test_main_a_persistence_helpers.py:69`
- Stage01 boundary helper decoupling과 fail-closed validation 테스트가 있다.
  - `main_a.py:2811`
  - `tests/test_stage01_helpers.py:568`
  - `tests/test_stage01_helpers.py:590`
  - `tests/test_stage01_helpers.py:612`
- narrative summary lifecycle와 sparse `ep_range` persistence 테스트가 있다.
  - `main_a.py:3483`
  - `main_a.py:3537`
  - `modules/core/services/project_service.py:118`
  - `tests/test_main_a_persistence_helpers.py:129`
  - `tests/test_main_a_persistence_helpers.py:149`
- `safe_commit_async -> bool` contract와 negative regression도 살아 있다.
  - `main_a.py:428`
  - `modules/core/stage2_finalizer.py:1094`
  - `tests/test_stage2_finalizer.py:126`
  - `tests/e2e/test_l3_stage2_realproject.py:151`
  - `tests/e2e/test_l3_golden_route.py:173`
- 전용 acceptance 문서는 없다. 따라서 문서 상태는 stale로 보인다.

판정 메모:

- `PN-E1`~`PN-E5`는 현재 코드와 회귀 테스트가 SSOT acceptance를 사실상 충족하는 쪽에 가깝다.
- 현 코드베이스 기준 별도 remediation package를 다시 열 사유는 약하다.

### 3. Facade Shim

판정:

- 현재 코드베이스 기준 `remaining valid work: yes`
- 분류: `partial stale / partial live`

#### 3A. 이미 닫힌 항목

- `FS-E2`와 `FS-E3`는 acceptance 문서가 존재한다.
  - `docs/2026-03-13/main_a-facade-shim-detail-remediation-fs-e2-acceptance.md`
  - `docs/2026-03-13/main_a-facade-shim-detail-remediation-fs-e3-acceptance.md`
- `MFS-T3-03`은 현재 코드에서 해소됐다.
  - `modules/core/stage3_orchestrator.py:1487`

#### 3B. 여전히 유효한 잔여 항목

1. `FS-E4 / MFS-T4-001`

- live Stage4 CV context가 아직 `npc_profiles`를 빈 dict로 시작한다.
  - `modules/core/stage4_interview_round.py:3536`
- 현 시점에서 이 값을 실제 facade/populated source로 채운 흔적은 같은 함수 블록에서 보이지 않는다.
- `ConsistencyValidator`는 `npc_profiles`를 소비하지만, Stage4 live path는 여전히 bypass 위험이 있다.
- `tests/test_stage4_cv_context.py`는 `protagonist_name`, `prev_hud`, `karma_matrix` 위주이며 `npc_profiles` 검증이 없다.

2. `FS-E5 / MFS-T4-002`

- operator-facing volume table title이 아직 고정 `10권`이다.
  - `modules/core/services/ui_service.py:95`
- `tests/test_ui_service.py`는 render 여부만 보고 title semantics를 잠그지 않는다.
  - `tests/test_ui_service.py:117`
  - `tests/test_ui_service.py:125`

판정 메모:

- `facade-shim` SSOT는 “전부 문서 stale”가 아니다.
- 현재 코드베이스 기준 남은 실작업은 다음 둘이다.
  - Stage4 `npc_profiles` live population
  - dynamic volume table title

## 문서 상태 감사

- 존재:
  - `main_a-facade-shim-detail-remediation-fs-e2-acceptance.md`
  - `main_a-facade-shim-detail-remediation-fs-e3-acceptance.md`
- 부재:
  - `main_a-retry-feedback-detail-remediation-*acceptance*.md`
  - `main_a-persistence-narrative-detail-remediation-*acceptance*.md`

따라서 문서 상태 해석은 아래가 맞다.

- `retry-feedback`: code-complete 가능성 높음, doc-complete 아님
- `persistence-narrative`: code-complete 가능성 높음, doc-complete 아님
- `facade-shim`: code-complete 아님, 일부 doc-complete

## 최종 정리

현재 코드베이스 기준으로 실제 남은 remediation work는 `facade-shim` 쪽 2개뿐이다.

1. `FS-E4 / MFS-T4-001`: Stage4 `_build_cv_context()`의 `npc_profiles` live population
2. `FS-E5 / MFS-T4-002`: `show_volume_table()`의 고정 `10권` operator title 제거

그 외 두 SSOT(`retry-feedback`, `persistence-narrative`)는 구현보다 문서 상태 갱신과 acceptance 문서화가 우선이다.
