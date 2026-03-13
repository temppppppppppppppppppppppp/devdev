# main_a 5-Track Merged Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 문서 역할: 5개 상세 전수조사 트랙의 consolidated findings / 3pass re-audit를 기준으로 `main_a.py` 주변 cross-cut remediation 범위, 순서, acceptance를 하나의 실행 SSOT로 잠그는 통합 오더
> 금지사항: 본 문서는 코드 수정 기록, rerun 결과 로그, closure 보고서가 아니다. 범위 고정, 우선순위 잠금, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
- `main_a-live-wiring-contract-detail-consolidated-findings.md`
- `main_a-live-wiring-contract-detail-consolidated-findings-3pass-reaudit.md`
- `main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`
- `main_a-dormant-helper-live-consumer-detail-consolidated-findings.md`
- `main_a-dormant-helper-live-consumer-detail-consolidated-findings-3pass-reaudit.md`
- `main_a-cross-stage-semantic-preservation-detail-full-survey-audit-order.md`
- `main_a-cross-stage-semantic-preservation-detail-consolidated-findings.md`
- `main_a-cross-stage-semantic-preservation-detail-consolidated-findings-3pass-reaudit.md`
- `main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`
- `main_a-runtime-recovery-lifecycle-detail-consolidated-findings.md`
- `main_a-runtime-recovery-lifecycle-detail-consolidated-findings-3pass-reaudit.md`
- `runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
- `runtime-observability-provenance-artifact-detail-consolidated-findings.md`
- `runtime-observability-provenance-artifact-detail-consolidated-findings-3pass-reaudit.md`

## 2. Executive Summary

이번 실행 오더의 목표는 `main_a.py` 기준 5개 전수조사 트랙을 다시 분리해서 처리하는 것이 아니라,
중복 원인 축을 하나의 remediation 순서로 재배열하는 것이다. 대상 트랙은 `MLW`, `MDH`, `MCS`, `MRL`, `ROP`이며,
확정된 전체 finding은 `총 72건 (P0 3 / P1 21 / P2 36 / P3 12)`이다.

이번 문서는 72건을 다시 세는 문서가 아니다. 이미 확정된 finding들을 아래 5개 실행 묶음으로 압축하고,
다음 순서를 고정한다.

1. live entry / context slot baseline 복구
2. cross-stage semantic handoff 정규화
3. boot / destructive recovery / preset-cache lifecycle closure
4. evidence / provenance / structured sink alignment
5. proof-quality / dormant cleanup / regression hardening

`MRL-T5` rerun blocker는 2026-03-13 기준 해제됐고, 현재 단계는 조사 재개가 아니라 실행 오더로 넘어가는 단계로 본다.

## 3. Scope

포함:

- `main_a.py`
- `modules/core/stage0/*`, `stage01_helpers.py`, `stage2_*`, `stage3_*`, `stage4_*`
- `modules/core/services/project_service.py`, `modules/core/db_manager.py`, `modules/core/project_manager.py`, `modules/core/runtime_paths.py`
- `modules/core/session_logger.py`, `modules/core/soft_failure.py`, `modules/core/artifact_logging.py`, `modules/core/pass_rate_monitor.py`
- `modules/core/project_support.py`, `modules/core/quality_sidecar_bootstrap.py`, `modules/api/bridge_server.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- 관련 focused regression test, canary proof, runtime artifact refresh 문서

제외:

- prompt / narrative quality 자체의 전면 재설계
- desktop UI 미관, packaging, release pipeline 변경
- main_a 5트랙 범위 밖의 unrelated repo-wide refactor
- 현재 워크스페이스 바깥 historical artifact 전체 영구 backfill

## 4. 실행 원칙

### 원칙 A. real runtime contract가 mock green보다 먼저다

- `SimpleNamespace`, spec-less mock, source-string assertion, exact-name grep은 acceptance의 보조 근거일 뿐이다.
- 실제 `app -> context factory -> orchestrator -> sink` 경로가 green이 아니면 close로 보지 않는다.

### 원칙 B. semantic payload는 경계를 지나도 shape를 잃으면 안 된다

- `Stage4 -> Stage3 -> Stage2` 경계에서 reject 의미가 bypass, rewrite, difficulty-only collapse로 바뀌면 실패다.
- 상위 stage가 가진 `failure_category`, `selection_reason`, `verdict_reason`, `fix_scope`, `contradictions`류 의미는 하위 stage에서 재구성 문자열로 대체하지 않는다.

### 원칙 C. destructive recovery success는 next-boot proof까지 포함한다

- same-process success만으로 recovery 완료를 선언하지 않는다.
- `emotion_history`, `world_state`, `fact_ledger`, preset registry, cache/history는 다음 boot에서도 같은 truth를 보여야 한다.

### 원칙 D. evidence layer는 하나의 사건을 하나의 이야기로 남겨야 한다

- session log, `stage_attempts`, `director_selections`, `runtime_audit_summary`, `soft_failures.jsonl`, operator-facing support payload가 서로 다른 사실을 말하면 안 된다.
- sink가 여러 개여도 join key와 degraded-completion truth는 단일해야 한다.

### 원칙 E. dormant cleanup은 live/dormant 재분류가 끝난 뒤에 한다

- live callback을 dormant처럼 정리한 뒤 dead-code cleanup을 하면 실제 contract를 지워 버릴 수 있다.
- 먼저 live surface를 복구하고, 그 다음 truly dead helper와 stale proof를 정리한다.

## 5. Package Map

| Work Package | 포함 finding anchor |
|--------------|---------------------|
| `MX-E1` Live Entry / Context Slot Recovery | `MLW-T3-001`, `MLW-T1-001`, `MLW-T2-003`, `MLW-T4-001`, `MLW-T5-001`, `MDH-T1-01` |
| `MX-E2` Cross-Stage Semantic Handoff Normalization | `MCS-T1-001`, `MCS-T1-002`, `MCS-T2-001`, `MCS-T2-002`, `MCS-T2-003`, `MCS-T3-001`, `MCS-T3-002`, `MCS-T4-001` |
| `MX-E3` Boot / Recovery / Preset / Cache Lifecycle Closure | `MRL-T1-001`, `MRL-T2-001`, `MRL-T3-001`, `MRL-T4-001`, `MRL-T5-001`, `MDH-T4-003`, `MDH-T4-004`, `MDH-T4-005` |
| `MX-E4` Evidence / Provenance / Structured Sink Alignment | `ROP-T1-001`, `ROP-T1-002`, `ROP-T2-001`, `ROP-T2-002`, `ROP-T3-001`, `ROP-T3-002`, `ROP-T4-001`, `ROP-T4-002` |
| `MX-E5` Proof / Dormant Cleanup / Regression Hardening | `MLW-T5-002`, `MLW-T5-003`, `MLW-T5-004`, `MDH-T5-001`, `MDH-T5-002`, `MDH-T5-003`, `MCS-T5-001`, `MCS-T5-002`, `MCS-T5-003`, `MCS-T5-004`, `MRL-T5-002`, `MRL-T5-003`, `ROP-T5-001`, `ROP-T5-002`, `MDH-T4-001`, `MDH-T4-002` |

## 6. Work Packages

### MX-E1. Live Entry / Context Slot Recovery

대상 finding:

- `MLW-T3-001`
- `MLW-T1-001`
- `MLW-T2-003`
- `MLW-T4-001`
- `MLW-T5-001`
- `MDH-T1-01`

대상 파일:

- `main_a.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_interview_round.py`
- `modules/protocols/app_services.py`

구현 원칙:

- `Stage2Context.from_app()`, `Stage3Context.from_app()`, `Stage4Context.from_app()`는 실사용 slot parity를 같은 수준으로 맞춘다.
- Stage4 real entry는 manual slot 조립, hidden `self.app`, surrogate wrapper에 기대지 않고 factory 경로 하나로 닫는다.
- MDH에서 live로 재분류된 Stage4 callback pair는 실제 runtime/canary path에서 도달 가능해야 한다.
- wrapper, protocol, runtime bridge가 각자 다른 callback 계약을 해석하는 split-brain을 허용하지 않는다.

acceptance:

- real `app -> Stage4Context.from_app() -> Stage4 orchestrator/post-processor` 경로가 빠진 slot 없이 동작한다.
- Stage2/Stage3/Stage4 consumer가 같은 live slot 집합을 사용하고 `self.app` 직접 참조가 필수 경로에서 제거되거나 명시적 adapter로 격리된다.
- Stage4 callback live surface가 더 이상 dormant inventory에 의존하지 않고 실호출 경로로 증명된다.
- menu entry, canary entry, wrapper entry 모두 `session_logger`, audit relay, retrieval/db handle을 보존한다.

필수 테스트:

- 기존: `tests/test_stage4_context.py`, `tests/test_stage4_orchestrator.py`, `tests/test_stage4_post_processor.py`, `tests/test_stage3_orchestrator.py`, `tests/test_run_stage4_canary.py`
- 신규:
  - real-app Stage4 entry regression
  - `from_app()` slot parity regression
  - live Stage4 callback reachability regression
  - wrapper/canary `session_logger` propagation regression

### MX-E2. Cross-Stage Semantic Handoff Normalization

대상 finding:

- `MCS-T1-001`
- `MCS-T1-002`
- `MCS-T2-001`
- `MCS-T2-002`
- `MCS-T2-003`
- `MCS-T3-001`
- `MCS-T3-002`
- `MCS-T4-001`

대상 파일:

- `main_a.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/feedback_system.py`
- `modules/core/db_manager.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`

구현 원칙:

- full regeneration과 inplace patch는 같은 structured reject payload 계약을 공유한다.
- `Stage3 -> Stage2` reverse feedback는 live producer가 실제로 기록하는 source를 읽어야 하며 수동 주입용 dead branch로 남기지 않는다.
- `reason-count` 문자열, difficulty-only carrier, generic 3줄 권고문은 structured upstream semantics의 대체재가 될 수 없다.
- shared summary / future context / past summary trim 정책은 하나의 precedence 표로 고정한다.

acceptance:

- Stage4 manuscript reject가 full regeneration path와 inplace patch path 모두에서 structured handoff를 남긴다.
- Stage3 reject 누적이 Stage2 preflight에서 실제로 감지되고, upstream 의미를 보존한 상태로 retry planning에 주입된다.
- `Stage4 -> Stage2` hard cutoff 아래에서도 semantic handoff가 사라지지 않거나, 명시적 no-handoff 이유가 남는다.
- past summary / future context / shared context trim에서 현재 정책과 실제 런타임 출력이 일치한다.

필수 테스트:

- 기존: `tests/test_stage2_preflight.py`, `tests/test_stage2_preflight_helpers.py`, `tests/test_stage3_orchestrator.py`, `tests/test_feedback_system.py`, `tests/test_stage4_interview_round.py`
- 신규:
  - `Stage4 -> Stage3` full-regeneration structured handoff regression
  - inplace patch semantic preservation regression
  - `Stage3 -> Stage2` producer-consumer integration regression
  - difficulty-only collapse regression
  - summary/context precedence regression

### MX-E3. Boot / Recovery / Preset / Cache Lifecycle Closure

대상 finding:

- `MRL-T1-001`
- `MRL-T2-001`
- `MRL-T3-001`
- `MRL-T4-001`
- `MRL-T5-001`
- `MDH-T4-003`
- `MDH-T4-004`
- `MDH-T4-005`

대상 파일:

- `main_a.py`
- `modules/core/services/project_service.py`
- `modules/core/db_manager.py`
- `modules/core/project_manager.py`
- `modules/core/runtime_paths.py`
- `modules/core/system.py`
- `modules/core/foreshadow_tracker.py`
- 관련 destructive-op / boot / preset / cache-history 테스트

구현 원칙:

- boot path, project switch path, destructive recovery path가 서로 다른 truth source를 보지 않게 만든다.
- recovery result는 성공/실패/partial-failure를 구조화해서 surface하고 silent success를 금지한다.
- `_load_v50_history`, `_restore_preset_registry`, `diversity_engine` 같은 helper/slot은 live면 실제 공급 경로를 만들고, 아니면 계약에서 제거한다.
- boot 인라인 복제 로직과 service callback 로직은 하나의 helper contract로 수렴시킨다.

acceptance:

- boot 후 project object, selected genre, preset registry, cache/history가 같은 truth source를 본다.
- reset/rewind/rollback/wipe 이후 `emotion_history`, `world_state`, `fact_ledger`, preset registry가 same-process와 next-boot 모두에서 정합하게 복구된다.
- preset restore failure, world/fact recovery failure, cache/history restore failure는 success로 숨겨지지 않는다.
- Stage4 optional slot인 `diversity_engine`은 live 공급 경로가 생기거나 optional contract에서 제거된다.

필수 테스트:

- 기존: `tests/test_project_service.py`, `tests/test_main_a_rollback.py`, `tests/test_runtime_paths.py`, `tests/test_stage_transition.py`, `tests/integration/test_patch_wiring.py`
- 신규:
  - destructive recovery next-boot regression
  - preset restore partial-failure regression
  - `world_state` / `fact_ledger` recovery-failure surfacing regression
  - boot vs destructive-op helper parity regression
  - `diversity_engine` live-slot contract regression

### MX-E4. Evidence / Provenance / Structured Sink Alignment

대상 finding:

- `ROP-T1-001`
- `ROP-T1-002`
- `ROP-T2-001`
- `ROP-T2-002`
- `ROP-T3-001`
- `ROP-T3-002`
- `ROP-T4-001`
- `ROP-T4-002`

대상 파일:

- `main_a.py`
- `modules/core/session_logger.py`
- `modules/core/soft_failure.py`
- `modules/core/services/audit_service.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/db_manager.py`
- `modules/core/artifact_logging.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage0/__init__.py`
- `modules/core/stage01_helpers.py`
- `modules/core/project_support.py`
- `modules/api/bridge_server.py`
- `modules/core/quality_sidecar_bootstrap.py`

구현 원칙:

- Stage3 decision row, `stage_attempts`, `director_selections`, session log, runtime summary는 join key를 공유해야 한다.
- degraded completion과 soft failure는 summary sink와 sidecar sink에서 같은 truth를 남겨야 한다.
- `runtime_audit_summary.json`는 단순 count 파일이 아니라 sink completeness를 판독할 수 있는 digest를 제공해야 한다.
- Stage0 POV provenance는 raw `pov`만 노출하는 구 경로를 넘어서 `effective_pov` 중심으로 operator-facing support surface를 갱신한다.

acceptance:

- Stage3/Stage4 evidence를 session log 단독, DB 단독, summary 단독으로 읽어도 서로 join 가능하거나 명시적 부족 사유가 보인다.
- `soft_failures.jsonl`과 `runtime_audit_summary.json`이 degraded completion을 서로 다르게 기록하지 않는다.
- current Stage0 style guide / cache / support payload / bridge detail이 `selected_primary_pov`, `effective_pov`, provenance freshness를 현재 계약대로 보존한다.
- current-code defect와 stale historical artifact debt가 generation/version tag로 구분된다.

필수 테스트:

- 기존: `tests/test_stage3_orchestrator.py`, `tests/test_stage4_post_processor.py`, `tests/test_audit_service.py`, `tests/test_db_manager.py`, `tests/test_stage0_pov.py`, `tests/test_stage0_work_guard_style_cache.py`, `tests/test_project_support.py`, `tests/test_quality_sidecar_bootstrap.py`
- 신규:
  - session decision `attempt_key` regression
  - degraded-completion sink alignment regression
  - runtime summary structured-digest regression
  - bridge/sidecar `effective_pov` regression

### MX-E5. Proof / Dormant Cleanup / Regression Hardening

대상 finding:

- `MLW-T5-002`
- `MLW-T5-003`
- `MLW-T5-004`
- `MDH-T5-001`
- `MDH-T5-002`
- `MDH-T5-003`
- `MCS-T5-001`
- `MCS-T5-002`
- `MCS-T5-003`
- `MCS-T5-004`
- `MRL-T5-002`
- `MRL-T5-003`
- `ROP-T5-001`
- `ROP-T5-002`
- `MDH-T4-001`
- `MDH-T4-002`

대상 파일:

- `main_a.py`
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage2_preflight.py`
- `tests/test_project_service.py`
- `tests/test_main_a_rollback.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_stage4_canary_tools.py`
- `tests/test_stage0_pov.py`
- `tests/test_stage0_work_guard_style_cache.py`
- `tests/test_project_support.py`
- `tests/test_db_manager.py`
- `tests/integration/test_patch_wiring.py`
- 관련 proof / closure / follow-up 문서

구현 원칙:

- `inspect.getsource`, source-string assertion, exact-name grep, surrogate app smoke는 primary proof에서 내린다.
- canary hard gate는 count, path, row existence뿐 아니라 rationale/provenance completeness를 직접 검사해야 한다.
- stale proof 문서와 archive path는 code/test acceptance와 같은 turn에서 갱신한다.
- truly dead-chain helper는 live surface 정렬이 끝난 뒤 제거 또는 quarantine한다.

acceptance:

- 핵심 contract가 source-string, exact helper name, `SimpleNamespace` surrogate 하나만으로 PASS되지 않는다.
- canary/report/doc chain이 current workspace path와 current artifact generation을 기준으로 green을 낸다.
- Stage4 live entry, recovery next-boot, Stage3 rationale sink, Stage0 POV provenance에 fresh proof artifact가 각각 존재한다.
- `_ignite_quad_cache_system()`, `_is_cache_alive()` 같은 dead-chain helper는 더 이상 live coverage처럼 읽히지 않는다.

필수 테스트:

- 기존: package별 기존 회귀군 전체
- 신규:
  - source-string 대체 behavioral seam tests
  - canary rationale/provenance gate regression
  - archive path / doc freshness regression
  - dead-chain helper non-coverage regression

## 7. 권장 실행 순서

1. `MX-E1`
- live entry와 context slot이 안정되지 않으면 뒤 패키지의 semantic / evidence proof가 전부 흔들린다.

2. `MX-E2`
- handoff payload를 먼저 정규화해야 recovery와 sink alignment가 의미 있는 데이터를 본다.

3. `MX-E3`
- destructive recovery와 next-boot lifecycle은 중간 실행 단계에서도 split-brain을 막는 안전장치다.

4. `MX-E4`
- sink와 provenance alignment는 stable runtime semantics 위에서 정리해야 한다.

5. `MX-E5`
- proof hardening과 dead-chain cleanup은 실제 live contract가 잠긴 뒤 마지막에 닫는다.

## 8. Public Contracts To Preserve

- `Stage2Context.from_app()`, `Stage3Context.from_app()`, `Stage4Context.from_app()`의 explicit slot contract
- Stage4 reject payload의 structured semantics
- destructive op의 success / failure / partial-failure surface
- `stage_attempts` / `director_selections` / session log / runtime summary 간 join key semantics
- Stage0 style / POV provenance의 `effective_pov` operator-facing 의미

## 9. Verification Plan

공통:

- package별 focused pytest
- live runtime proof와 next-boot proof를 분리해 둘 다 남긴다
- canary proof와 문서 proof는 current workspace artifact를 직접 참조한다

패키지 종료 검증:

- `MX-E1`: real-app Stage4 entry + callback reachability green
- `MX-E2`: `Stage4 -> Stage3 -> Stage2` structured payload roundtrip green
- `MX-E3`: destructive recovery same-process + next-boot green
- `MX-E4`: evidence sink joinability + `effective_pov` support surface green
- `MX-E5`: canary/doc/archive freshness + behavioral regression replacement green

최종 종료 조건:

- 5트랙의 72개 finding이 code acceptance, regression acceptance, artifact acceptance 중 하나로 모두 닫힌다.
- stale doc claim, archive path drift, surrogate proof가 open blocker로 남지 않는다.
- 본 SSOT 이후의 문서는 full-survey 재실행이 아니라 postfix closure / follow-up audit 문서로 넘어간다.

## 10. Out of Scope Notes

- prompt 내용 품질과 narrative 결과물 자체의 전면 개선
- desktop UI 미관/배포/패키징
- historical artifact 전체 영구 재수복
- 본 5트랙과 직접 연결되지 않는 unrelated module cleanup
