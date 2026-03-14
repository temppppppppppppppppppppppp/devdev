# 전역 거시 remediation 실행 SSOT

> Date: 2026-03-13
> Status: `execution-ready`
> Commit: `d9825a69`
> Workspace State: dirty
> Basis:
> - `global-macro-reset-master-audit-order.md`
> - `global-macro-reset-consolidated-findings-3pass-reaudit.md`
> - `global-macro-reset-remediation-execution-3pass-audit.md`
> Role: 전역 거시 retained open set을 실행 단위, 순서, acceptance, 문서 산출물로 다시 잠그는 단일 SSOT

## 1. Executive Summary

- 현재 전역 거시 조사 기준 `P0`는 없다.
- raw retained `P1`은 `8건`이며, 후속 remediation은 `6개 execution unit`으로 순차 진행하는 것이 맞다.
- 이번 문서는 "코드를 지금 바로 수정했다"는 보고가 아니라, 후속 execution 턴이 같은 순서와 같은 acceptance로 움직이도록 기준을 고정하는 문서다.
- 권장 실행 순서는 `GMR-R1 -> GMR-R2 -> GMR-R3 -> GMR-R4 -> GMR-R5 -> GMR-R6`다.

## 2. Scope

포함:

- `main_a.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/services/project_service.py`
- `modules/core/db_manager.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/bridge_server.py`
- `modules/api/risk_approval.py`
- `modules/api/process_runner.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`
- `modules/core/metrics_collector.py`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/DESKTOP-GUIDE.md`
- `build/build_release.ps1`
- `build/backend_entry.py`
- `docs/stage_map/*`
- 관련 focused regression 문서와 테스트

제외:

- 생성 품질 자체를 높이기 위한 prompt/model 튜닝
- Stage 2~4 창작 알고리즘 전면 재설계
- Electron UI visual redesign
- installer/signing/release publishing
- unrelated refactor

## 3. Non-Negotiables

### 3.1 현재 truth를 뒤집지 않는다

- `main_a.py`는 현재 실질 composition root로 취급한다.
- DB는 현재 durable handoff truth로 취급한다.
- `UI/`는 runtime code가 아니라 reference asset archive로 취급한다.
- desktop/backend는 현재 CLI protocol wrapper control plane으로 취급한다.

### 3.2 모든 execution unit은 3PASS를 강제한다

각 유닛은 아래 순서를 고정한다.

1. PASS 1: source contract 정리 또는 inventory 작성
2. PASS 2: focused regression 또는 정적 검증
3. PASS 3: 문서, runbook, release guide 동기화

### 3.3 한 번에 1유닛만 진행한다

- 의미론이 겹치는 유닛을 병렬로 수정하지 않는다.
- 각 유닛은 `acceptance`와 `evidence`가 닫힌 뒤 다음 유닛으로 넘어간다.

## 4. Retained Set -> Execution Unit Map

| Execution Unit | Primary P1 | Attached finding | 핵심 산출물 |
|---|---|---|---|
| `GMR-R1` | `GMR-A-001` | `GMR-A-002`, `GMR-C-003` | runtime ownership contract |
| `GMR-R2` | `GMR-B-001`, `GMR-E-001` | 없음 | safe-op recovery state matrix |
| `GMR-R3` | `GMR-B-002` | 없음 | DB cursor live inventory |
| `GMR-R4` | `GMR-C-002` | `GMR-E-002`, `GMR-F-002` | Stage 4 PASS artifact contract |
| `GMR-R5` | `GMR-D-002`, `GMR-F-001` | `GMR-D-001` | control-plane approval/provenance SSOT |
| `GMR-R6` | `GMR-H-002` | `GMR-D-003`, `GMR-G-002`, `GMR-G-003`, `GMR-H-001` | shipping reality + live surface guide |

## 5. Execution Units

### GMR-R1. Composition Root / Runtime Ownership Freeze

목표:

- `main_a.py`, `StageXContext.from_app()`, repair seam 사이의 실소유권을 명시적으로 동결한다.

작업:

- `main_a.py`를 façade가 아니라 current composition root로 문서화한다.
- Stage 2, 3, 4 context가 app에서 요구하는 slot, callback, service를 contract 표로 고정한다.
- repair seam을 "stage ownership"과 "downstream compatibility"로 분리 기록한다.

acceptance:

- 후속 문서가 `main_a.py`를 stale shell이나 thin façade로 오기재하지 않는다.
- `from_app()`가 요구하는 live dependency 표가 존재한다.
- repair seam owner와 실행 지점이 구분된다.

필수 산출물:

- `runtime-ownership-contract` 계열 문서 1건

### GMR-R2. Safe-Op Recovery Semantics Standardization

목표:

- rollback, wipe, reset, rewind 이후 상태를 `DB restored / runtime restored / tracker restored / cache invalidated`로 분리해 기록한다.

작업:

- safe-op 결과를 durable side와 runtime side로 나눈 상태 모델을 정의한다.
- `BaseAgent` class cache invalidation을 safe-op semantics와 같은 표에서 다룬다.
- fail-open 복구를 허용할 경우 operator-facing 로그와 summary 형식을 표준화한다.

acceptance:

- safe-op 결과가 단일 "성공" 문자열이 아니라 상태 벡터로 기록된다.
- project switch와 safe-op의 cache invalidation semantics 차이가 명시된다.
- rollback/wipe/reset/rewind별 기대 상태표가 존재한다.

필수 산출물:

- `safe-op-recovery-state-matrix` 계열 문서 1건

### GMR-R3. Persistence Access Contract Inventory

목표:

- `DBManager`의 local cursor 정책과 live shared cursor 사용 지점을 문서와 테스트 기준으로 분리 고정한다.

작업:

- live writer/reader 경로의 cursor 사용 인벤토리를 만든다.
- `legacy shared cursor`, `allowed temporary legacy`, `must migrate`를 분리 표기한다.
- WAL + `check_same_thread=False` 조건에서 조사 우선순위를 정한다.

acceptance:

- `self.cursor`가 어디서 실사용되는지 문서만 읽어도 닫힌다.
- reader/writer path가 local cursor 기준인지 legacy path인지 구분된다.
- 후속 수정이 inventory 기준 없이 산발적으로 들어가지 않는다.

필수 산출물:

- `db-cursor-live-inventory` 계열 문서 1건

### GMR-R4. Stage 4 PASS Artifact Completeness Standardization

목표:

- Stage 4 PASS가 항상 같은 수준의 durable output을 뜻하는 것처럼 보이는 현재 상태를 정리한다.

작업:

- manuscript, episode_bible, state_log, world_state, fact_ledger를 `hard sink`와 `soft sink`로 구분한다.
- PASS 결과와 artifact completeness 상태 코드를 별도로 정의한다.
- advisory completeness와 audit summary completeness를 함께 기록하는 표준을 만든다.

acceptance:

- "PASS"와 "artifact complete"가 분리된 상태 코드로 설명된다.
- soft sink 실패가 허용되는 조건과 operator-facing 결과 문구가 고정된다.
- Stage 4 중단/예외 경로도 summary 깊이를 일정 수준 유지한다.

필수 산출물:

- `stage4-pass-artifact-contract` 계열 문서 1건

### GMR-R5. Control Plane Approval + Provenance Unification

목표:

- approval gate의 live source와 run provenance key를 하나의 control-plane 계약으로 묶는다.

작업:

- `approval_id`가 어디서 생성, 적재, 로드, 검증되는지 source of truth를 정한다.
- `run_id`, audit session, metrics session, engine runtime execution을 연결하는 공통 provenance key 정책을 정의한다.
- desktop/backend가 CLI menu protocol wrapper라는 사실을 계약 문서 상단에 명시한다.

acceptance:

- risk approval record의 live source가 문서에 명시된다.
- 같은 실행을 UI, backend, engine, audit, metrics에서 종단 추적할 수 있는 key 정책이 존재한다.
- approval failure와 transport failure의 경계가 분리된다.

필수 산출물:

- `control-plane-approval-provenance-ssot` 계열 문서 1건

### GMR-R6. Shipping Reality + Live Surface Normalization

목표:

- 문서, 패키지, build, desktop shell, shadow surface가 같은 shipping reality를 보게 만든다.

작업:

- 현재 packaged runtime primary path를 `engine.exe-first`인지 `source-bundle fallback-first`인지 하나로 확정한다.
- `src/main.js`, `geuldobi-desktop/main.js`, 루트 `main.js`, `lite_mode/`, `test_mode/`를 live/shadow/alternate surface로 분류한다.
- desktop `test` 스크립트가 curated subset이라는 사실을 release/test guide에 명시한다.

acceptance:

- shipping guide가 실제 artifact topology와 모순되지 않는다.
- active entry와 shadow surface가 문서 상단에서 구분된다.
- desktop test script가 full regression이 아니라 subset gate임이 명확히 기록된다.

필수 산출물:

- `shipping-reality-live-surface-guide` 계열 문서 1건

## 6. Execution Order And Gates

실행 순서:

1. `GMR-R1`
2. `GMR-R2`
3. `GMR-R3`
4. `GMR-R4`
5. `GMR-R5`
6. `GMR-R6`

유닛 진입 게이트:

- 직전 유닛의 PASS 1, PASS 2, PASS 3 근거 문서가 모두 있어야 한다.
- 새로 생긴 finding이 `P0`면 즉시 현재 SSOT를 중단하고 재발령한다.
- 문서와 테스트가 서로 다른 truth를 말하면 다음 유닛으로 넘어가지 않는다.

유닛 종료 게이트:

- source contract 또는 inventory가 닫혀 있어야 한다.
- focused regression 또는 정적 검증 근거가 있어야 한다.
- operator-facing 문서가 갱신돼 있어야 한다.

## 7. Out Of Scope Risks

- 이번 SSOT는 아직 코드를 수정하지 않았다.
- full regression 전량 실행은 별도 턴에서 닫아야 한다.
- live rerun, packaged smoke, operator rehearsal은 후속 execution 완료 후 별도로 필요하다.

## 8. Final Order

- 현재 판정: `execution-ready`
- 우선 처리: `GMR-R1`, `GMR-R2`, `GMR-R5`
- 문서 성격: 후속 remediation 턴의 단일 기준
- 현재 턴 산출물: 문서만 생성, 코드 직접 수정 없음

## Last Verified

- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
