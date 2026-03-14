# Backend Global Full Survey Master Audit Order

> 작성일: 2026-03-13
> 트랙: backend global blind spot and contract convergence audit
> 상태: `executed / pass-with-normalization-note`
> 목적: 현재 코드베이스의 백엔드 전역 표면을 `entry -> stage runtime -> persistence/recovery -> observability/artifact -> bridge/operator surface` 전체 lifecycle 관점에서 전면 전량 조사한다.
> 방식: `5-terminal 분할`, 실제 실행은 `T1 -> T2 -> T3 -> T4 -> T5 -> 통합본 -> 3PASS 재감리` 순차 고정

---

## 0. 문서 역할

- 이 문서는 `백엔드 전역 전량 전수 조사`의 상위 마스터 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 기존 세부 오더를 폐기하지 않고, `전역 백엔드` 관점에서 재배열하고 누락 축을 잠그는 문서다.
- 결과 문서가 채워지기 전까지 어떤 finding도 확정으로 간주하지 않는다.
- 모든 문서는 `UTF-8` 고정이다. 물음표 치환 흔적이나 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.

---

## 1. 왜 별도 마스터 오더가 필요한가

기존에는 아래 문서들이 각각 강한 범위를 커버했다.

- `docs/2026-03-10/TF-BE-backend-full-audit.md`
- `docs/2026-03-12/backend-health-full-survey-execution-ssot.md`
- `docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-facade-shim-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-retry-feedback-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-persistence-narrative-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`
- `docs/2026-03-13/runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-DI-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-DB-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-MEM-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-ERR-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-LLM-detail-full-survey-audit-order.md`

그러나 현재는 세부 트랙이 충분히 많아졌고, 아래 질문이 하나의 마스터 오더로 잠겨 있지 않다.

- 백엔드 전체를 기준으로 아직 안 잠긴 blind spot이 남아 있는가
- 이미 닫힌 세부 finding이 다른 트랙과 합쳐질 때 전역 P0/P1 위험으로 승격되는가
- `main_a.py`, services, DI, DB, provider, runtime artifact, bridge가 같은 사실과 같은 lifecycle을 보존하는가
- 정적 read-only 조사만으로 닫을 수 있는 것과 runtime proof가 필요한 것을 명확히 분리했는가

본 문서는 그 전역 판정을 위한 단일 SSOT다.

---

## 2. 공통 조사 규약

### 2.1 조사 모드

- `static`
- `read-only`
- `code-and-test verification`
- `source-report cross-check`
- `artifact-proof cross-check`
- `UTF-8 only`

### 2.2 금지 사항

- 코드 직접 수정 금지
- 임시 patch 금지
- 테스트 수정 금지
- live/full rerun, canary 재실행, destructive op 실험 금지
- 기존 문서에서 이미 닫힌 항목을 근거 없이 재오픈 금지

### 2.3 3PASS 프로토콜

#### PASS 1 - 전역 표면 수집

- 담당 터미널 범위의 코드, 테스트, 세부 오더, 감리 결과를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- 후보마다 `existing`, `cross-track`, `net-new`, `runtime-only` 태그를 붙인다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 세부 문서 근거, tracked artifact를 함께 대조한다.
- 기존 세부 트랙 finding은 그대로 복제하지 말고, 전역 백엔드 의미에서 왜 다시 살아나는지 설명해야 한다.
- 2차 근거가 부족하면 `finding`으로 올리지 않고 `open question` 또는 `runtime-only`로 내린다.

#### PASS 3 - 전역 확정

- 확정 항목만 `[BGA-TN-SEQ]` 형식으로 채택한다.
- 각 터미널 문서 말미에 `PASS1 후보 -> PASS2 제거 -> PASS3 확정` 요약을 남긴다.
- 마스터 통합본에서는 중복을 제거하고 전역 severity를 다시 매긴다.

### 2.4 finding 기록 형식

각 finding은 아래 8개 필드를 반드시 가진다.

1. ID
2. Severity (`P0`, `P1`, `P2`, `P3`)
3. 현상 요약
4. 코드 근거
5. downstream 영향 경계
6. 현재 테스트 근거 또는 테스트 부재
7. 기존 문서와의 중복 여부
8. 권장 후속 조치

### 2.5 Severity 기준

- `P0`: boot/recovery/persistence/bridge 경계에서 즉시 크래시, 데이터 손실, 잘못된 삭제, 회복 불가 오염
- `P1`: 잘못된 stage target, 잘못된 verdict/attempt lineage, silent destructive op, 잘못된 runtime 복구
- `P2`: facade/DI/provider/config/observability contract drift, 숨은 optional hook 실패, cross-track 의미 불일치
- `P3`: stale docs, brittle test, log label drift, operator readability 저하

---

## 3. 전역 조사 범위

### 포함

- `main_a.py`
- `modules/api`
- `modules/core`
- `modules/domain`
- `modules/protocols`
- `config`
- backend-facing `build`, `scripts`, `docs/implementation`
- 관련 `tests`
- tracked `logs`, `project_data.db`, `projects/*` 산출물 중 백엔드 계약 검증에 필요한 표면

### 제외

- 순수 UI 미관과 레이아웃 문제
- Electron renderer 스타일 품질
- signed installer/SmartScreen/배포 평판
- 실제 장편 생성 품질 자체의 미학적 평가

---

## 4. 마스터 조사 질문

이번 전역 오더는 아래 질문을 닫는 데 목적이 있다.

1. 진입점, 메뉴, runner, bridge는 같은 작업 의미를 공유하는가
2. Stage 0~4와 helper/service/DI/facade는 실제 live path에서 같은 계약을 유지하는가
3. DB, in-memory state, runtime recovery, destructive op은 같은 lifecycle graph를 보존하는가
4. provider/router/config/telemetry는 실행 환경이 바뀌어도 같은 의미를 보존하는가
5. operator가 보는 로그, audit summary, JSONL, DB sink, artifact는 같은 사실을 재구성할 수 있는가

---

## 5. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 | 우선 참조 세부 오더 |
|---------|------|-----------|----------------------|
| T1 | Entry / control plane / safe ops | boot, project binding, dispatch, destructive menu, bridge entry | `main_a-control-plane`, `main_a-live-wiring-contract`, `backend-health` |
| T2 | Persistence / DB / memory / recovery | DB transaction, state restore, rollback, wipe/reset, runtime recovery | `main_a-persistence-narrative`, `main_a-runtime-recovery-lifecycle`, `XC-DB`, `XC-MEM`, `XC-ERR` |
| T3 | Facade / helper / DI / live consumer | facade shim, retry-feedback, dormant helper, callback binding, protocol drift | `main_a-facade-shim`, `main_a-retry-feedback`, `main_a-dormant-helper-live-consumer`, `XC-DI` |
| T4 | Stage contract / provider / config / context | Stage 0~4 contract continuity, provider/router, model config, work-guard/style/context | `stage0-full-survey`, `stage2-detail-deep-dive`, `XC-LLM`, `backend-health` |
| T5 | Observability / artifact / bridge regression | runtime evidence layers, sink alignment, process runner, operator-facing proof, regression gaps | `runtime-observability-provenance-artifact`, `ui-frontend-backend-connectivity`, `stage4-*log*`, `logging-hardening` |

---

## 6. Terminal 1 - Entry / Control Plane / Safe Ops

### 담당 범위

- `main_a.py`
- `modules/api/process_runner.py`
- `modules/api/bridge_server.py`
- `modules/core/project_manager.py`
- `modules/core/project_support.py`
- `modules/core/services/project_service.py`

### 핵심 검사 포인트

1. `boot -> project select -> menu dispatch -> shutdown` 계약이 실제 entry surface마다 같은가
2. destructive menu와 service layer가 대상 범위, preview, 결과 의미를 공유하는가
3. lexical project ordering, root resolution, `.env`/config reload가 runner/bridge와 드리프트 없이 이어지는가
4. thin delegate가 실질 구현을 덮어쓰거나 우회하지 않는가
5. 기존 control-plane 세부 트랙이 놓친 `전역 백엔드 entry risk`가 남아 있는가

### 필수 근거

- `docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-live-wiring-contract-detail-full-survey-audit-order.md`
- `docs/2026-03-12/backend-health-full-survey-execution-ssot.md`
- `tests/test_runtime_paths.py`
- `tests/test_project_support.py`
- `tests/test_stage_transition.py`

### 산출물

- `docs/2026-03-13/BGA-T1-entry-control-plane-safe-ops-findings.md`

---

## 7. Terminal 2 - Persistence / DB / Memory / Recovery

### 담당 범위

- `modules/core/db_manager.py`
- `modules/core/services/project_service.py`
- `modules/core/vec_memory.py`
- `modules/core/failure_analyzer.py`
- runtime state restore / rollback / rewind / wipe path 전체

### 핵심 검사 포인트

1. DB state와 in-memory state가 rollback/recovery 이후 같은 사실을 보존하는가
2. destructive op 성공 판정이 실제 runtime restore 성공과 분리되어 있지 않은가
3. lifecycle graph 기준 `boot -> project switch -> restore -> rollback -> next boot` 사이의 blind spot이 남아 있는가
4. exception swallow, partial rollback, cache invalidation 누락이 전역 backend 위험으로 승격되는가
5. 기존 XC/`main_a` 세부 트랙 결과를 합치면 신규 P0/P1이 생기는가

### 필수 근거

- `docs/2026-03-13/main_a-persistence-narrative-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-DB-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-MEM-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-ERR-detail-full-survey-audit-order.md`
- `tests/test_db_manager.py`
- `tests/test_db_integrity_recovery.py`
- `tests/test_state_service.py`

### 산출물

- `docs/2026-03-13/BGA-T2-persistence-db-memory-recovery-findings.md`

---

## 8. Terminal 3 - Facade / Helper / DI / Live Consumer

### 담당 범위

- `main_a.py` facade/helper/callback 표면
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/protocols/app_services.py`
- `modules/core/services/*`

### 핵심 검사 포인트

1. facade/helper가 실제 live consumer를 가지는가, 아니면 test-only/dormant/bypassed surface인가
2. DI slot, callback binding, protocol, thin wrapper가 같은 semantic contract를 공유하는가
3. retry-feedback, audit callback, validation shim이 green test 뒤에 semantic drift를 숨기지 않는가
4. `main_a.py` export surface와 downstream context/service가 이름만 같고 의미가 다르지 않은가
5. 세부 helper 트랙을 합쳤을 때 `binding-broken live surface`가 남아 있는가

### 필수 근거

- `docs/2026-03-13/main_a-facade-shim-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-retry-feedback-detail-full-survey-audit-order.md`
- `docs/2026-03-13/main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`
- `docs/2026-03-13/XC-DI-detail-full-survey-audit-order.md`
- `tests/test_stage2_context.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_protocols_services.py`

### 산출물

- `docs/2026-03-13/BGA-T3-facade-helper-di-live-consumer-findings.md`

---

## 9. Terminal 4 - Stage Contract / Provider / Config / Context

### 담당 범위

- `modules/core/stage0/**`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_*`
- `modules/core/stage3_*`
- `modules/core/stage4_*`
- `modules/domain/agents/base_agent.py`
- `modules/core/llm_router.py`
- `modules/core/llm_generate.py`
- `config/models.yaml`
- `config/system.yaml`

### 핵심 검사 포인트

1. Stage 0 style/work-guard/context가 Stage 2/3/4 consumer까지 실질적으로 이어지는가
2. provider/router/model config/telemetry가 config SSOT와 실행 경로에서 같은 의미를 가지는가
3. stage contract continuity와 provider/config drift가 결합해 생기는 전역 backend risk가 있는가
4. one-stop 또는 wrapper 경로가 개별 stage 계약을 조용히 우회하지 않는가
5. read-only 조사 기준에서 `quality 문제`가 아니라 `backend contract 문제`로 올릴 수 있는 항목만 남겼는가

### 필수 근거

- `docs/2026-03-13/stage0-full-survey-3pass-audit-order.md`
- `docs/2026-03-13/stage2-detail-deep-dive-3pass-audit-order.md`
- `docs/2026-03-13/XC-LLM-detail-full-survey-audit-order.md`
- `docs/2026-03-12/backend-health-full-survey-execution-ssot.md`
- `tests/test_stage0_work_guard_style_cache.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_base_agent.py`

### 산출물

- `docs/2026-03-13/BGA-T4-stage-contract-provider-config-context-findings.md`

---

## 10. Terminal 5 - Observability / Artifact / Bridge Regression

### 담당 범위

- `modules/core/session_logger.py`
- `modules/core/artifact_logging.py`
- `modules/core/metrics_collector.py`
- `modules/core/pass_rate_monitor.py`
- `modules/api/process_runner.py`
- operator-facing runtime artifact and backend-facing desktop bridge surface

### 핵심 검사 포인트

1. operator가 보는 JSONL/summary/DB/log/artifact가 같은 attempt/verdict/rationale을 보존하는가
2. process runner, bridge, runtime artifact가 entry/control plane과 같은 사실을 노출하는가
3. 테스트가 helper green만 보장하고 operator-facing regression은 놓치지 않는가
4. observability thinness가 전역 backend 판단을 왜곡할 정도인가
5. 기존 UI 연계 문서 중 backend contract에 속하는 항목이 아직 마스터 백엔드 관점에서 닫히지 않았는가

### 필수 근거

- `docs/2026-03-13/runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
- `docs/2026-03-13/ui-frontend-backend-connectivity-remediation-3pass-audit.md`
- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- `docs/2026-03-13/stage4-9ep-log-full-survey-3pass-final-audit.md`
- `docs/2026-03-13/logging-hardening-moderate-remediation-execution-ssot.md`
- `tests/test_session_logger.py`
- `tests/test_artifact_logging.py`
- `tests/test_bridge_quality_summary.py`

### 산출물

- `docs/2026-03-13/BGA-T5-observability-artifact-bridge-regression-findings.md`

---

## 11. 마스터 통합 규칙

### 11.1 기존 finding 재사용 규칙

- 기존 세부 문서의 finding을 그대로 복붙하지 않는다.
- 아래 셋 중 하나를 만족할 때만 마스터 finding으로 승격한다.
  1. 둘 이상의 세부 트랙을 합쳐야만 보이는 전역 위험이다.
  2. 세부 트랙에서는 `P2/P3`였지만 백엔드 전체 lifecycle 기준에서는 `P1` 이상이다.
  3. 세부 문서가 닫힌 뒤 최근 코드/문서 변경으로 다시 살아난다.

### 11.2 마스터 최종 산출물

- `docs/2026-03-13/backend-global-full-survey-consolidated-findings.md`
- `docs/2026-03-13/backend-global-full-survey-consolidated-findings-3pass-reaudit.md`

### 11.3 마스터 통합본 필수 섹션

1. Executive Summary
2. 조사 범위와 제외 범위
3. T1~T5 Pass 1 요약
4. T1~T5 Pass 2 교차 검증
5. 중복 제거 및 전역 severity 재배정
6. 확정 findings
7. 기각 findings
8. runtime-only / open question
9. 확신도 ledger
10. 다음 단계

---

## 12. 완료 기준

- T1~T5 전량 커버
- 각 터미널 문서가 `PASS1 후보 -> PASS2 제거 -> PASS3 확정` 요약을 가진다
- 마스터 통합본이 중복 제거와 전역 severity 재배정을 끝낸다
- `entry/control plane`, `persistence/recovery`, `facade/DI`, `stage/provider/config`, `observability/bridge` 5축이 모두 닫힌다
- 최종 확신도 `95%` 또는 read-only 조사로 방어 가능한 상한에 도달한다

---

## 13. 기본 가정

- 이번 단계는 오더 문서 작성과 전역 조사 기준 잠금까지만 수행한다.
- 실제 코드 수정은 별도 remediation 오더에서 다룬다.
- frontend/UI 문서는 `backend-facing contract`를 입증하는 범위에서만 보조 증거로 사용한다.

---

## 14. 현재 조사 현황

- 조사 현황: `완료`
- 완료 단계:
  - 직접 참조 하위 오더 6건 UTF-8/경고 문구 정규화 완료
  - 마스터 오더 UTF-8 clean 재검증 완료
  - 순차 실행 순서 `T1 -> T2 -> T3 -> T4 -> T5 -> 통합본 -> 3PASS 재감리` 고정
  - `T1` 조사 완료 (`BGA-T1-entry-control-plane-safe-ops-findings.md`)
  - `T2` 조사 완료 (`BGA-T2-persistence-db-memory-recovery-findings.md`)
  - `T3` 조사 완료 (`BGA-T3-facade-helper-di-live-consumer-findings.md`)
  - `T4` 조사 완료 (`BGA-T4-stage-contract-provider-config-context-findings.md`)
  - `T5` 조사 완료 (`BGA-T5-observability-artifact-bridge-regression-findings.md`)
  - 통합본 작성 완료 (`backend-global-full-survey-consolidated-findings.md`)
  - `3PASS` 재감리 완료 (`backend-global-full-survey-consolidated-findings-3pass-reaudit.md`)
- 진행 앵커:
  - `docs/2026-03-13/backend-global-full-survey-progress-ledger.md`
  - 직전 완료 결과 문서
- 다음 시작점:
  - `후속 remediation order 분리 또는 사용자 지시 대기`
