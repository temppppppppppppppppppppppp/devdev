# main_a Control Plane Detail Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 문서 역할: [main_a-control-plane-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md), [main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md) 기준으로 `main_a.py` control plane 수정 범위와 순서를 잠그는 단일 실행 SSOT
> 금지사항: 본 문서는 코드 수정, 테스트 실행, rerun 기록 문서가 아니다. 범위 고정, 우선순위 잠금, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- [main_a-control-plane-detail-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md)
- [main_a-control-plane-detail-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md)
- [main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md)
- [MCP-T1-boot-project-binding-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MCP-T1-boot-project-binding-findings.md)
- [MCP-T2-agent-bootstrap-di-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md)
- [MCP-T3-menu-stage-entry-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MCP-T3-menu-stage-entry-findings.md)
- [MCP-T4-destructive-ops-recovery-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MCP-T4-destructive-ops-recovery-findings.md)
- [MCP-T5-control-contract-regression-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/MCP-T5-control-contract-regression-findings.md)

## 2. Executive Summary

이번 실행 오더의 목표는 `main_a.py` 주변 control plane을 다시 단일 SSOT로 맞추는 것이다. 범위는 `boot/project binding`, `destructive op / recovery`, `desktop-runner external contract`, `stage entry / DI / observability`, `bootstrap status / protocol / regression trust`의 5개 축으로 고정한다.

이번 오더는 총건수 15를 다시 세는 문서가 아니다. 재감리에서 확정된 15개 finding을 실제 수정 묶음으로 변환하고, 다음 순서를 고정한다.

1. boot/root binding 복구
2. destructive op / shutdown safety 복구
3. desktop-runner control contract 정렬
4. stage entry / DI / observability 정렬
5. bootstrap status / protocol / regression hardening

## 3. Scope

포함:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/project_manager.py](C:/Users/User/Desktop/글도비/modules/core/project_manager.py)
- [modules/core/system.py](C:/Users/User/Desktop/글도비/modules/core/system.py)
- [modules/core/runtime_paths.py](C:/Users/User/Desktop/글도비/modules/core/runtime_paths.py)
- [modules/core/services/project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)
- [modules/core/db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- [modules/core/foreshadow_tracker.py](C:/Users/User/Desktop/글도비/modules/core/foreshadow_tracker.py)
- [modules/core/stage3_context.py](C:/Users/User/Desktop/글도비/modules/core/stage3_context.py)
- [modules/core/stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [modules/core/stage4_post_processor.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)
- [modules/api/process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- [modules/api/run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)
- [modules/protocols/app_services.py](C:/Users/User/Desktop/글도비/modules/protocols/app_services.py)
- [modules/core/services/ui_service.py](C:/Users/User/Desktop/글도비/modules/core/services/ui_service.py)
- [modules/core/services/state_service.py](C:/Users/User/Desktop/글도비/modules/core/services/state_service.py)
- [geuldobi-desktop/src/index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- 관련 테스트와 contract 문서

제외:

- Stage 2/3/4 내부 알고리즘 품질 개선 전반
- prompt 내용 재설계
- desktop 렌더러 구조 개편
- packaged installer QA
- bridge HTTP surface 확장

## 4. 실행 원칙

### 원칙 A. bound project root가 먼저다

- `resolve_projects_root()`와 `current_project.paths.root`가 한번 정해지면 boot, legacy fallback, runner, UI가 같은 root를 봐야 한다.
- 상대 `projects/` 문자열이나 root `.env` 재오염은 허용하지 않는다.

### 원칙 B. destructive op는 `false-return`과 `partial commit`을 동시에 가질 수 없다

- service가 실패를 반환하면 DB와 runtime이 함께 rollback되거나, 최소한 구조화된 partial result로 상위가 정합 복구를 강제해야 한다.
- app-level cleanup은 DB semantics를 덮어쓰면 안 된다.

### 원칙 C. external contract drift는 backend 내부 순수성보다 먼저 닫는다

- desktop label, validator 허용 범위, runner stdin sequence, `main_a.py` 메뉴 의미가 다르면 운영자가 잘못된 실행을 하게 된다.
- 이 구간은 단순 문서 문제가 아니라 실제 실행 surface로 취급한다.

### 원칙 D. wrapper-level source mismatch도 제품 결함으로 본다

- resume banner, Stage 4 prompt floor, manual context injection처럼 "실행은 되지만 의미가 틀린" 경계는 P2/P3라도 실제 수정 범위에 포함한다.

### 원칙 E. 테스트는 각 Work Package의 종료 조건이다

- 이번 오더에서 regression 추가는 후속 정리가 아니라 acceptance 자체다.
- 기존 green test가 drift를 놓친 finding은 같은 package 안에서 behavioral seam test로 교체 또는 보강한다.

## 5. Package Map

| Work Package | 포함 finding |
|--------------|--------------|
| `CP-E1` Boot / Root Binding Recovery | `MCP-T1-001`, `MCP-T1-002`, `MCP-T2-03` |
| `CP-E2` Destructive Ops / Shutdown Safety | `MCP-T4-001`, `MCP-T4-002`, `MCP-T4-003` |
| `CP-E3` Desktop / Runner Contract Alignment | `MCP-T5-001`, `MCP-T5-002` |
| `CP-E4` Stage Entry / DI / Observability Alignment | `MCP-T2-02`, `MCP-T3-01`, `MCP-T3-02`, `MCP-T3-03` |
| `CP-E5` Bootstrap Status / Protocol / Regression Hardening | `MCP-T2-01`, `MCP-T5-003`, `MCP-T5-004` |

## 6. Work Packages

### CP-E1. Boot / Root Binding Recovery

대상 finding:

- `MCP-T1-001`
- `MCP-T1-002`
- `MCP-T2-03`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/project_manager.py](C:/Users/User/Desktop/글도비/modules/core/project_manager.py)
- [modules/core/system.py](C:/Users/User/Desktop/글도비/modules/core/system.py)
- [modules/core/runtime_paths.py](C:/Users/User/Desktop/글도비/modules/core/runtime_paths.py)

구현 원칙:

- `ProjectContext`는 생성 시 root `.env`를 다시 덮어쓰지 않는다.
- boot 시점 credential과 runtime service credential은 같은 snapshot을 사용한다.
- `main_a.py::_select_project()`, `StudioSystem.boot_v20_project()`, legacy JSON fallback path는 모두 `resolve_projects_root()`와 `current_project.paths.root`를 단일 SSOT로 사용한다.
- `_PROJECTS_DIR = "projects"` 직접 참조는 이 package 범위에서 제거하거나 adapter로 격리한다.

acceptance:

- project-local `.env` 로드 후 `ProjectContext`, `VecMemory`, boot 후속 helper가 같은 credential boundary를 본다.
- `GEULDOBI_PROJECTS_ROOT`가 지정된 환경에서 menu selection, `ProjectContext.paths.root`, legacy fallback path가 모두 동일 root를 사용한다.
- non-default root에서 stale JSON/log artifact를 잘못 가져오는 fallback이 남지 않는다.

필수 테스트:

- 기존: [test_runtime_paths.py](C:/Users/User/Desktop/글도비/tests/test_runtime_paths.py), [test_project_support.py](C:/Users/User/Desktop/글도비/tests/test_project_support.py), [test_project_manager_hud_helpers.py](C:/Users/User/Desktop/글도비/tests/test_project_manager_hud_helpers.py)
- 신규:
  - `project .env -> boot -> VecMemory/api client` 일관성 regression
  - explicit `GEULDOBI_PROJECTS_ROOT` + non-workspace CWD binding regression
  - V50 legacy fallback path root binding regression

### CP-E2. Destructive Ops / Shutdown Safety

대상 finding:

- `MCP-T4-001`
- `MCP-T4-002`
- `MCP-T4-003`

대상 파일:

- [modules/core/services/project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)
- [modules/core/db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/foreshadow_tracker.py](C:/Users/User/Desktop/글도비/modules/core/foreshadow_tracker.py)

구현 원칙:

- `reset_after()`는 service 최종 판정과 같은 트랜잭션 경계에 묶거나, 상위가 복구 가능한 구조화 결과를 반환한다.
- rewind/rollback 후처리는 `clear() -> save_to_db()`처럼 DB semantics를 파괴하는 방식으로 정리하지 않는다.
- shutdown은 `best effort save`와 `unconditional close`를 분리해 anchor save failure가 DB close를 막지 못하게 한다.

acceptance:

- `reset_stage_2()`, `rewind_stage_2()`, `rollback_episode()`는 failure after destructive mutation에서 split-brain을 남기지 않는다.
- rollback/rewind 이후 target 이전 foreshadow가 보존된다.
- `save_v20_anchor("bible")` 또는 `save_anchor("genre_info")` 실패가 나도 `memory.close()`, DB commit/close는 실행된다.

필수 테스트:

- 기존: [test_project_service.py](C:/Users/User/Desktop/글도비/tests/test_project_service.py), [test_main_a_rollback.py](C:/Users/User/Desktop/글도비/tests/test_main_a_rollback.py)
- 신규:
  - `failure after reset_after` partial-commit regression
  - foreshadow preservation regression
  - shutdown anchor failure close-guarantee regression

### CP-E3. Desktop / Runner Contract Alignment

대상 finding:

- `MCP-T5-001`
- `MCP-T5-002`

대상 파일:

- [geuldobi-desktop/src/index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- [modules/api/process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- [modules/api/run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- 필요 시 [modules/core/stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)

구현 원칙:

- Stage 0 `sub_key`는 frontend, validator, runner, backend helper가 같은 번호 체계를 공유하게 만든다.
- 구현 선택지는 둘뿐이다.
  - bridge/runner translation layer를 둔다.
  - backend mode numbering을 external contract에 맞게 재정렬한다.
- 단, 어느 쪽을 택하든 desktop label과 실제 handler 매핑이 다르면 실패다.
- boot confirm `y`는 실제 confirm prompt가 존재할 때만 소비되게 바꾼다. invalid menu retry에 기대는 구조는 금지한다.

acceptance:

- Stage 0 submenu label -> `sub_key` -> backend handler가 1:1로 일치한다.
- `작품가드`가 bridge contract 상 표현 가능하다.
- `stored_genre absent / same / mismatch` 3개 boot case 모두 runner가 deterministic하게 입력을 소비한다.

필수 테스트:

- 기존: [test_process_runner.py](C:/Users/User/Desktop/글도비/tests/test_process_runner.py), [test_process_runner_stage0_inputs.py](C:/Users/User/Desktop/글도비/tests/test_process_runner_stage0_inputs.py), [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py), [test_frontend_stage0_connectivity.py](C:/Users/User/Desktop/글도비/tests/test_frontend_stage0_connectivity.py)
- 신규:
  - Stage 0 parity integration test
  - boot confirm conditional-consumption integration test

### CP-E4. Stage Entry / DI / Observability Alignment

대상 finding:

- `MCP-T2-02`
- `MCP-T3-01`
- `MCP-T3-02`
- `MCP-T3-03`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/core/stage3_context.py](C:/Users/User/Desktop/글도비/modules/core/stage3_context.py)
- [modules/core/stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [modules/core/stage4_context.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context.py)
- [modules/core/stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [modules/core/stage4_post_processor.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)
- [modules/core/project_manager.py](C:/Users/User/Desktop/글도비/modules/core/project_manager.py)

구현 원칙:

- Stage 3 smart retrieval은 `ctx`만으로 동작 가능해야 한다. hidden `self.app` 의존은 허용하지 않는다.
- manuscript head SSOT는 하나로 고정한다. resume banner와 Stage 2/3 entry floor가 서로 다른 source를 보면 안 된다.
- Stage 4 interactive `limit_mode=True` prompt는 current production head를 반영한 floor를 써야 한다.
- Stage 4 wrapper는 `Stage4Context.from_app(self)`를 기본으로 사용하거나, 최소한 `session_logger` 포함 필수 슬롯을 빠짐없이 전달한다.

acceptance:

- Stage 3 retrieval path가 `context_advisor`, retrieval memory, genre를 injected context에서 읽는다.
- `DB manuscript row 존재 + draft file 누락` 상태에서도 resume banner와 Stage 2/3 entry floor가 같은 값을 본다.
- 이미 완료된 episode target은 prompt 단계에서 차단되거나 early return으로 닫힌다.
- menu/canary Stage 4 실행에서 `ctx.session_logger`가 유지된다.

필수 테스트:

- 기존: [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py), [test_run_stage4_canary.py](C:/Users/User/Desktop/글도비/tests/test_run_stage4_canary.py), [test_stage4_context.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context.py), [test_resume_status.py](C:/Users/User/Desktop/글도비/tests/test_resume_status.py)
- 신규:
  - Stage 3 context-only retrieval regression
  - resume/banner vs Stage entry head parity regression
  - completed target input guard regression
  - `main_a` Stage 4 wrapper session logger propagation regression

### CP-E5. Bootstrap Status / Protocol / Regression Hardening

대상 finding:

- `MCP-T2-01`
- `MCP-T5-003`
- `MCP-T5-004`

대상 파일:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [modules/protocols/app_services.py](C:/Users/User/Desktop/글도비/modules/protocols/app_services.py)
- [modules/core/services/ui_service.py](C:/Users/User/Desktop/글도비/modules/core/services/ui_service.py)
- [modules/core/services/state_service.py](C:/Users/User/Desktop/글도비/modules/core/services/state_service.py)
- 관련 control-plane 테스트

구현 원칙:

- `_attach_agents()`는 bare `bool` 대신 partial failure를 식별 가능한 상태를 제공한다.
- `_init_v50_modules()`는 transaction-like subgroup init 또는 명시적 partial failure ledger를 가진다.
- protocol 이름과 실제 구현 의미가 다르면 둘 중 하나를 맞춘다.
  - protocol을 실제 facade 의미로 좁힌다.
  - 또는 service 구현/이름을 protocol 의미에 맞춘다.
- source-string assertion은 축소하고 behavior/contract test로 대체한다.

acceptance:

- V50 optional module 일부만 붙은 hybrid graph를 bootstrap success 하나로 숨기지 않는다.
- `UIServiceProtocol`, `StateServiceProtocol`와 실제 extracted service의 관계가 문서/테스트/이름 중 적어도 하나로 명시적으로 정렬된다.
- source-string test를 지워도 실제 behavior seam regression이 남아 동일 위험을 감지한다.

필수 테스트:

- 기존: [test_protocols_services.py](C:/Users/User/Desktop/글도비/tests/test_protocols_services.py)
- 신규:
  - partial V50 init failure status regression
  - actual implementation vs protocol parity test
  - source-string 대체 behavioral contract tests

## 7. 권장 실행 순서

1. `CP-E1`
- root / credential / fallback path는 다른 package가 기대는 baseline이다.

2. `CP-E2`
- destructive op safety는 수정 중간 상태에서도 데이터 손실을 막는 안전장치다.

3. `CP-E3`
- operator-facing contract drift를 먼저 닫아 잘못된 메뉴 실행을 차단한다.

4. `CP-E4`
- Stage 3/4 wrapper, DI, observability를 같은 묶음으로 정리한다.

5. `CP-E5`
- bootstrap status와 protocol/test trust gap을 마지막에 정리해 구조를 고정한다.

## 8. Public Contracts To Preserve

- `GEULDOBI_PROJECTS_ROOT` 우선 root resolution 규약
- `/run` request의 `key / sub_key / inputs` envelope
- CLI `main_a.py`의 메인 메뉴 key 체계
- `current_project.get_latest_episode_number()`의 `next episode` 반환 의미
- Stage 4 `limit_mode`, `target_ep` 외부 호출 surface
- existing bridge/process runner boot lifecycle

## 9. Verification Plan

공통:

- package별 focused pytest
- 관련 기존 회귀군 전체 재실행
- 필요 시 temp project / temp root ad-hoc 재현

패키지 종료 검증:

- `CP-E1`: runtime path, boot binding, fallback migration
- `CP-E2`: destructive op partial-failure, foreshadow preservation, shutdown close guarantee
- `CP-E3`: Stage 0 mapping parity, boot confirm consumption
- `CP-E4`: Stage 3 context seam, resume/head parity, Stage 4 target guard, session logger propagation
- `CP-E5`: bootstrap partial status, protocol parity, behavioral regression replacement

최종 종료 조건:

- 15개 finding이 모두 코드 또는 테스트 acceptance로 닫힌다.
- 새 regression이 기존 green surface를 대체하거나 보강한다.
- 재감리 문서가 지적한 `normalization note` 외 추가 open blocker가 남지 않는다.

## 10. Out of Scope Notes

- Stage 3/4 내용 품질 자체 개선
- prompt 문구 리라이트 전반
- desktop UI 미관 개편
- package/build/release 파이프라인 변경
- unrelated repo-wide refactor
