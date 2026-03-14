# Backend Global Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 확신도 목표: `95%`
> 기준 조사:
> - `backend-global-full-survey-master-audit-order.md`
> - `backend-global-full-survey-consolidated-findings.md`
> - `backend-global-full-survey-consolidated-findings-3pass-reaudit.md`
> 문서 역할: 3PASS 재감리까지 끝난 전역 백엔드 retained open set을 `실행 단위`, `순서`, `acceptance`, `gate`로 다시 잠그는 remediation 실행 오더
> 금지사항: 본 문서는 코드 수정 기록, postfix closure, rerun 결과 보고서가 아니다. 범위 고정과 실행 순서 잠금만 담당한다.

## Executive Summary

- 이번 실행 범위는 전역 통합 retained set `12건 (P0 1 / P1 3 / P2 8)`을 remediation unit `6개`로 재배열하는 것이다.
- 목표는 `live Stage 4 path`, `destructive lifecycle truth`, `attempt-level evidence chain`, `entry/control plane contract`, `stage/provider/config continuity`, `proof net`을 다시 같은 SSOT로 맞추는 것이다.
- 권장 순서는 `BGR-E1 -> BGR-E3 -> BGR-E4 -> BGR-E2 -> BGR-E5 -> BGR-E6`다.
- 이번 턴의 산출물은 문서뿐이며, 실제 코드 수정은 이 SSOT를 기준으로 한 후속 execution 턴에서만 수행한다.

## Scope

포함:

- `main_a.py`
- `modules/api/process_runner.py`
- `modules/api/bridge_server.py`
- `modules/api/run_validator.py`
- `modules/core/services/project_service.py`
- `modules/core/session_logger.py`
- `modules/core/services/audit_service.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/llm_generate.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/stage0/style_extractor.py`
- 관련 focused pytest, property/chaos regression, canary gate, artifact-proof 문서

제외:

- narrative quality 전면 재설계
- desktop renderer 미관 수정
- unrelated repo-wide refactor
- full pipeline live rerun을 전제로 한 closure 선언
- 배포/installer/release pipeline 변경

## Baseline Retained Set -> Execution Unit Mapping

| Finding | Severity | Execution Unit | 실행 의미 |
|---------|----------|----------------|-----------|
| `BGA-G-001` | `P0` | `BGR-E1` | Stage 4 live path import crash 제거 |
| `BGA-G-002` | `P1` | `BGR-E2` | public `/run` Frontier Lag contract 정렬 |
| `BGA-G-003` | `P1` | `BGR-E3` | destructive success semantics 복구 |
| `BGA-G-004` | `P1` | `BGR-E4` | session decision join chain 복구 |
| `BGA-G-005` | `P2` | `BGR-E2` | ui-only exit action containment |
| `BGA-G-006` | `P2` | `BGR-E3` | post-reset contamination window closure |
| `BGA-G-007` | `P2` | `BGR-E5` | Stage 3 DI ctx authority normalization |
| `BGA-G-008` | `P2` | `BGR-E5` | model config SSOT convergence |
| `BGA-G-009` | `P2` | `BGR-E5` | provider helper return contract normalization |
| `BGA-G-010` | `P2` | `BGR-E5` | Stage 0 excerpt budget guard |
| `BGA-G-011` | `P2` | `BGR-E4` | operator proof surface structured proof화 |
| `BGA-G-012` | `P2` | `BGR-E6` | backend-wide live proof net hardening |

## Public Contracts To Preserve

- `POST /run`, `POST /stop`, `GET /status`, `POST /run/{run_id}/input`, `GET /quality/dashboard`, `GET /quality/summary`, `GET /safe-ops/preview` route는 유지한다.
- `ProcessRunner`의 runtime diagnostics key set인 `key`, `sub_key`, `mode`, `duration_ms`, `last_prompt_step`, `stdout_tail`, `stderr_tail`, `failure_phase`는 유지한다.
- `Stage2Context.from_app()`, `Stage3Context.from_app()`, `Stage4Context.from_app()` 기반 context factory 방향은 유지한다.
- `attempt_key`, `candidate_key`, `artifact_path`의 기본 naming contract와 `logs/artifacts/**`, `logs/runtime_audit_summary.json`, `logs/soft_failures.jsonl`, `session/*.jsonl` 경로는 backward-compatible하게 유지한다.
- `ProjectService` destructive op public API 이름은 유지하되, 결과 semantics는 더 엄격하게 만든다.

## Execution Principles

### 원칙 A. live path 복구가 proof net보다 먼저다

- import-time crash와 live context build가 막힌 상태에서는 proof net 확장을 먼저 하지 않는다.
- `BGR-E1`이 green이 되기 전 `BGR-E6`는 close로 보지 않는다.

### 원칙 B. destructive success는 next-boot truth를 포함해야 한다

- same-process success만으로 destructive op 성공을 선언하지 않는다.
- `world_state`, `fact_ledger`, `emotion_history`, agent cache는 다음 boot 또는 즉시 다음 read에서도 같은 truth를 보여야 한다.

### 원칙 C. evidence layer는 attempt 단위로 join 가능해야 한다

- session JSONL, DB sink, pass-rate, runtime summary, dashboard가 같은 attempt를 같은 key로 재구성할 수 있어야 한다.
- 한 sink만 읽으면 전혀 다른 사실이 보이는 상태는 허용하지 않는다.

### 원칙 D. stage/provider/config drift는 helper convenience로 정당화하지 않는다

- `response.raw`, import-time config snapshot, oversized excerpt direct injection처럼 helper가 편해서 생긴 우회는 close 기준이 아니다.
- 실행 경계에서 normalized contract가 우선이다.

### 원칙 E. gate는 마지막에 묶되 blind spot은 명시적으로 pin한다

- 모든 unit이 끝난 뒤 official proof net을 넓힌다.
- 그 전까지는 `현재 gate가 무엇을 못 본다`를 테스트 이름 수준으로 명시한다.

## Execution Units

### BGR-E1. Live Stage 4 Path Recovery

목표:

- `Stage4Context` import-time crash를 제거하고, real app-bound Stage 4 live path를 다시 테스트 가능 상태로 복구한다.

대상 finding:

- `BGA-G-001`

핵심 작업:

- `Stage4Context` slot/property 충돌을 제거해 import collection blocker를 없앤다.
- manual Stage 4 entry와 `from_app()` entry가 같은 live context contract를 보도록 정렬한다.
- Stage 4 관련 regression이 injected context 우회 없이 real factory path를 타도록 최소 회귀를 보강한다.

비포함:

- Stage 4 narrative logic 개선
- Stage 4 observability 전면 재설계

acceptance:

- `tests/test_stage4_context.py` collection blocker가 사라진다.
- `Stage4Context.from_app()` 경로가 import/build 수준에서 정상 동작한다.
- Stage 4 live auto-build path를 직접 타는 focused regression이 green이다.

### BGR-E3. Destructive Lifecycle Closure

목표:

- destructive op의 success semantics를 runtime restored truth와 다시 일치시키고, post-reset contamination window를 닫는다.

대상 finding:

- `BGA-G-003`
- `BGA-G-006`

핵심 작업:

- restore 경로의 partial failure를 structured result로 surface한다.
- `world_state`, `fact_ledger`, preset registry, `emotion_history`, `BaseAgent._context_caches` 정합화 순서를 하나의 destructive lifecycle로 통일한다.
- same-process cleanup과 next-boot verification이 같은 truth를 보도록 helper boundary를 정리한다.

비포함:

- DB schema 대개편
- unrelated project bootstrap 리팩터

acceptance:

- destructive op가 restore partial failure를 success로 숨기지 않는다.
- reset/rollback/wipe 뒤 stale tracker residue와 agent cache residue가 남지 않는다.
- focused property/chaos regression과 next-boot equivalent regression이 green이다.

### BGR-E4. Evidence Chain And Operator Proof Surface

목표:

- `decisions.jsonl`, DB sink, summary artifact, desktop dashboard가 같은 attempt truth를 복원할 수 있게 맞춘다.

대상 finding:

- `BGA-G-004`
- `BGA-G-011`

핵심 작업:

- Stage 3 / Stage 4 `decisions.jsonl`에 attempt join에 필요한 최소 metadata를 같은 policy로 싣는다.
- `runtime_audit_summary.json`을 heartbeat artifact로만 둘지, structured digest로 키울지 하나의 방향으로 고정한다.
- `/quality/dashboard`에 operator proof 상태를 표현하는 필드를 추가하고 regression으로 잠근다.

비포함:

- observability sink 종류 추가
- 대형 metrics 플랫폼 연동

acceptance:

- session decision row 하나만으로 같은 attempt의 DB/artifact sink를 join할 수 있다.
- runtime summary 또는 대체 proof artifact가 structured sink 상태를 명시한다.
- quality dashboard가 proof 상태를 health와 분리해 surface한다.

### BGR-E2. Entry / Control Plane Contract Normalization

목표:

- public runner/bridge/menu contract를 실제 interactive surface와 다시 일치시킨다.

대상 finding:

- `BGA-G-002`
- `BGA-G-005`

핵심 작업:

- Frontier Lag key `7`이 prompt-map, desktop, `/run`, `ProcessRunner.MODE_B_KEYS`에서 같은 의미를 가지게 맞춘다.
- `ui_only_action: exit_app`인 key `5`를 public backend action contract에서 제외하거나 명시적 internal contract로 격리한다.
- run validator, prompt map, desktop surface가 같은 action inventory를 보도록 회귀를 추가한다.

비포함:

- menu UX 재설계
- 새로운 menu action 추가

acceptance:

- `/run`에서 허용되는 key set이 prompt-map과 desktop action inventory와 일치한다.
- ui-only action은 public API에서 직접 호출되지 않는다.
- focused runner/bridge/API contract regression이 green이다.

### BGR-E5. DI / Config / Provider / Context Continuity

목표:

- stage/context/provider/config contract drift를 하나의 runtime SSOT로 수렴시킨다.

대상 finding:

- `BGA-G-007`
- `BGA-G-008`
- `BGA-G-009`
- `BGA-G-010`

핵심 작업:

- Stage 3 lazy init이 injected ctx를 덮어쓰지 않게 authority를 정렬한다.
- models config loader를 project-local / root / import-time snapshot 중 하나의 정책으로 통일한다.
- provider helper 반환 contract를 normalized response 중심으로 정렬한다.
- Stage 0 `reference_excerpt`에 Stage 4 downstream budget guard를 추가한다.

비포함:

- multi-provider 전면 도입
- Stage 0 style system 재설계

acceptance:

- ctx-injected tracker가 app global에 의해 덮어씌워지지 않는다.
- `main_a`, `AIModels`, `BaseAgent`가 같은 models config policy를 따른다.
- helper caller가 provider native raw shape에 묶이지 않는다.
- large `reference_excerpt`에서도 Stage 4 prompt 필수 구간 budget이 보존된다.

### BGR-E6. Backend-Wide Proof Net Hardening

목표:

- injected test path와 Stage 4 only canary에 남아 있는 blind spot을 줄이고, real app-bound multi-stage proof net을 official gate로 끌어올린다.

대상 finding:

- `BGA-G-012`

핵심 작업:

- real `app -> context factory -> orchestrator -> sink` 경로를 타는 regression을 추가한다.
- canary scope를 Stage 4 only 증명에서 multi-stage observability proof로 넓히거나 별도 Stage 3 proof gate를 만든다.
- current green gate가 못 보는 blind spot을 테스트 이름과 acceptance 수준에서 제거한다.

비포함:

- full suite mega-gate化
- 긴 live generation rerun의 상시 mandatory화

acceptance:

- live auto-build path와 multi-stage observability contract를 직접 pin하는 regression이 존재한다.
- Stage 3 join-key regression 또는 Stage 4 live context regression이 official gate에서 false green으로 남지 않는다.
- canary/proof summary가 backend-wide proof 범위를 정확히 설명한다.

## Recommended Execution Order

1. `BGR-E1`
- 현재 유일한 `P0`이며, Stage 4 live path와 관련 회귀 수집 자체를 막고 있다.

2. `BGR-E3`
- destructive success semantics는 data/state truth 문제라 다음 unit들의 proof 신뢰도에도 직접 영향을 준다.

3. `BGR-E4`
- attempt evidence chain을 먼저 복구해야 이후 gate hardening 결과를 operator가 해석할 수 있다.

4. `BGR-E2`
- public `/run` drift는 isolated fix라 dependency는 낮지만, 앞선 state/evidence truth가 안정된 뒤 고정하는 편이 안전하다.

5. `BGR-E5`
- provider/config/context continuity는 범위가 넓고 P2 축이므로 앞선 emergency/lifecycle surface 이후에 묶는 것이 효율적이다.

6. `BGR-E6`
- blind spot hardening은 앞선 실제 결함 수정이 끝난 뒤 공식 gate를 넓히는 마지막 단계로 둔다.

## Verification Plan

- focused pytest
  - `tests/test_stage4_context.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_stage4_context_builder.py`
  - `tests/test_project_service.py`
  - `tests/test_main_a_rollback.py`
  - `tests/test_state_service.py`
  - `tests/property/test_db_rollback_props.py`
  - `tests/chaos/test_partial_commit.py`
  - `tests/test_session_logger.py`
  - `tests/test_failure_analyzer.py`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_process_runner.py`
  - `tests/test_process_runner_stage0_inputs.py`
  - `tests/test_api_contract.py`
  - `tests/test_run_validator.py`
  - `tests/test_llm_router.py`
  - `tests/test_config_manager.py`
  - plus `BGR-E1~E6` 신규 focused regression
- static inventory
  - `rg`로 key inventory, context factory usage, runtime summary fields, attempt metadata fields, models loader usage를 재검증
- artifact-proof
  - canary summary와 quality dashboard payload가 새로운 proof status를 실제로 보존하는지 확인
- closure gate
  - postfix 3PASS에서 unresolved `P0` 0건, unresolved `P1` 0건, confidence `95%` 이상 방어

## Exit Criteria

1. Stage 4 live path import/build blocker가 제거된다.
2. destructive op success는 runtime restored truth와 next-boot truth를 함께 보장한다.
3. attempt-level evidence chain이 session JSONL부터 dashboard/proof artifact까지 재구성 가능하다.
4. public entry/control plane key inventory가 prompt-map과 동일하다.
5. Stage/context/provider/config contract drift가 동일 SSOT로 수렴한다.
6. official proof net이 real app-bound multi-stage blind spot을 false green 없이 대표한다.
7. postfix 3PASS에서 `P0 0`, `P1 0`을 방어한다.

## Compaction / Resume Packet

- `Current phase`: `remediation execution order authored`
- `Last completed pass`: `backend-global consolidated findings 3PASS re-audit`
- `Last completed surface`: `retained set -> execution unit mapping`
- `Next surface`: `backend-global-remediation-execution-3pass-audit.md`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `implementation not started`
