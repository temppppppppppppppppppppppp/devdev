# main_a Control Plane Detail Full Survey Audit Order

> 작성일: 2026-03-13
> 트랙: `main_a.py` control plane blind spot audit
> 상태: `execution-ready`
> 목적: `main_a.py` 자체와 그 직접 downstream 경계에서, 아직 별도 심층 오더로 잠기지 않은 부팅, 디스패치, 상태 복구, 파괴적 조작 계약을 전량 조사한다.
> 방식: 5-terminal 분할, 각 터미널 자체 3PASS, 통합본 3PASS 재감리

---

## 0. 문서 역할

- 이 문서는 기존 `OPUS-TF-5terminal`의 연장선 3차/4차가 아니다.
- 이 문서는 `main_a.py` 중심 신규 조사축이며, finding namespace도 `MCP-*`로 완전히 분리한다.
- 이 문서는 실제 코드 수정 오더가 아니라, `main_a.py` control plane 조사 실행 오더다.
- 결과 문서가 채워지기 전까지는 어떤 finding도 확정으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서들은 아래 축을 각각 다뤘다.

- `OPUS-TF-5terminal-master-audit-order.md`: 핵심 프로덕션 전역 거시 건강성
- `OPUS-TF-5terminal-detail-master-audit-order.md`: 미열거 파일과 경계 디테일
- `OPUS-TF-5terminal-deep-dive-master-audit-order.md`: Stage 0 내부 메뉴, cross-stage, Lite Mode, API/Desktop, 보안/성능
- `one-stop-lookahead-execution-ssot.md`, `one-stop-frontier-lag-execution-ssot.md`: one-stop 파생 모드
- `stage0-work-guard-style-cache-remediation-execution-ssot.md`: Stage 0 work_guard/style cache
- `ui-frontend-backend-connectivity-remediation-execution-ssot.md`: desktop UI connectivity

그러나 아래 축은 아직 별도 조사 오더로 잠겨 있지 않다.

- `main_a.py`의 boot-to-menu control plane
- `main_a.py`와 service/orchestrator entrypoint 사이의 thin-delegate 계약
- destructive operation의 runtime invariant
- `process_runner -> main_a.py` project/menu contract
- protocol/facade/source-string test 의존성까지 포함한 control-plane regression surface

---

## 2. 공통 조사 규약

### 2.1 조사 모드

- `static`
- `read-only`
- `code-and-test verification`
- `source-report cross-check`

### 2.2 3PASS 프로토콜

#### PASS 1 - 초벌 스캔

- 담당 범위의 public entrypoint, helper, service, test를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- 기존 문서와 겹치는 표면인지 먼저 표시한다.

#### PASS 2 - 교차 검증

- 코드 근거, 테스트 근거, 기존 오더/감리 문서를 함께 대조한다.
- 기존 문서에서 이미 닫힌 항목은 재오픈 금지다.
- 기존 문서와 표면은 비슷하지만 `main_a.py control contract` 자체가 문제면 신규 finding으로 승격 가능하다.

#### PASS 3 - 최종 확정

- 확정 항목만 `[MCP-TN-SEQ]` 형식으로 채택한다.
- 보고서 말미에 `PASS1 후보 N건 -> PASS2 제거 M건 -> 최종 K건` 요약을 남긴다.
- 미확정 사항은 `coverage gap` 또는 `open question`으로 분리한다.

### 2.3 finding 기록 형식

각 finding은 아래 8개 필드를 반드시 가진다.

1. ID
2. Severity (`P0`, `P1`, `P2`, `P3`)
3. 현상 요약
4. 코드 근거
5. downstream 영향 경계
6. 현재 테스트 근거 또는 테스트 부재
7. 기존 문서와의 중복 여부
8. 권장 후속 조치

### 2.4 Severity 기준

- `P0`: 부팅 불가, 데이터 손실, 대규모 잘못된 삭제, 회복 불가 상태 파손
- `P1`: 잘못된 프로젝트/에피소드 경계, 잘못된 destructive op, 잘못된 stage target, 잘못된 boot binding
- `P2`: 계약 드리프트, 캐시/상태 동기화 누락, 취약한 facade, 테스트-코드 불일치
- `P3`: 관측성, 로그 명확성, 유지보수성, source-string brittle test 의존

---

## 3. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Boot / project binding / startup config | `boot()`, genre/project binding, `.env`, model config, guard binding |
| T2 | Agent bootstrap / lazy load / DI wiring | `_attach_agents()`, `_init_core_agents()`, `_init_v50_modules()`, cache/bootstrap |
| T3 | Main menu dispatch / stage entry / resume semantics | `_run_main_process()`, `_show_resume_status()`, `_stage_2_arcs()`, `_stage_3_batch_blueprinting()`, `_stage_4_v2_chief_writer()` |
| T4 | Destructive ops / rollback invariants / shutdown | `_reset_stage_2()`, `_rewind_stage_2()`, `_rollback_episode()`, `_wipe_production_data()`, `_shutdown_app()`, `ProjectService` |
| T5 | External contracts / regression surface | `UIService`, `AuditService`, `StateService`, `ProjectService`, `app_services.py`, `process_runner.py` |

---

## 4. Terminal 1 - Boot / Project Binding / Startup Config

### 담당 범위

- `main_a.py`
  - `boot()`
  - `_select_genre()`
  - `_select_project()`
  - `_load_models_yaml()`
  - `_get_agent_model_map()`
  - `_check_vector_db_lock()`
- 직접 downstream
  - `modules/core/system.py`
  - `modules/core/project_manager.py`
  - `modules/core/project_support.py`
  - `modules/core/genre_guards/work_guard.py`
  - `modules/core/prompt_loader.py`

### 핵심 검사 포인트

1. 장르 선택과 프로젝트 선택이 실제 boot contract와 일치하는가
2. project `.env` reload가 기존 runtime object를 부분 파손 없이 재구성하는가
3. `boot_v20_project()` 이후 `current_project`, `genre_info`, `guard`, `memory`, logger, metrics 경계가 일관적인가
4. `work_guard.yaml` 존재/부재가 baseline boot를 막지 않는가
5. `models.yaml` precedence가 project-local -> root fallback 순서를 지키는가
6. vector DB lock gate가 boot 중단 조건을 과소/과대 판정하지 않는가
7. lexical project sort contract가 bridge/process runner 가정과 일치하는가

### 필수 근거

- `tests/test_runtime_paths.py`
- `tests/test_project_support.py`
- `tests/test_project_manager_hud_helpers.py`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`

### 산출물

- `docs/2026-03-13/MCP-T1-boot-project-binding-findings.md`

---

## 5. Terminal 2 - Agent Bootstrap / Lazy Load / DI Wiring

### 담당 범위

- `main_a.py`
  - `_attach_agents()`
  - `_init_core_agents()`
  - `_init_v50_modules()`
  - `_ignite_quad_cache_system()`
  - `_load_v50_history()`
- 직접 downstream
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/services/*`

### 핵심 검사 포인트

1. lazy import 실패가 non-blocking이어야 할 경계와 boot stop 경계를 혼동하지 않는가
2. optional module partial-fail 후 app attribute graph가 깨지지 않는가
3. JSON -> DB migration hook가 idempotent하고 side effect 범위가 명확한가
4. Stage 2/3/4 orchestrator context 주입 전에 필요한 runtime module이 모두 준비되는가
5. `current_project`, `selected_genre`, `sys.api_client`가 각 agent/service에 일관되게 전달되는가
6. conditional module registration이 downstream context builder contract와 맞는가

### 필수 근거

- `tests/test_stage_transition.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_protocols_services.py`

### 산출물

- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`

---

## 6. Terminal 3 - Main Menu Dispatch / Stage Entry / Resume Semantics

### 담당 범위

- `main_a.py`
  - `_run_main_process()`
  - `_show_resume_status()`
  - `_stage_2_arcs()`
  - `_stage_3_batch_blueprinting()`
  - `_stage_4_v2_chief_writer()`
- 직접 downstream
  - `modules/core/stage2_context.py`
  - `modules/core/stage3_context.py`
  - `modules/core/stage4_context.py`

### 핵심 검사 포인트

1. 메뉴 번호, 라벨, 실제 dispatch가 어긋나지 않는가
2. resume status 계산이 blueprint/manuscript progress를 잘못 표시하지 않는가
3. Stage 2/3/4 진입 직전 context injection 순서가 정확한가
4. `limit_mode`, `target_ep`가 wrapper와 orchestrator 사이에서 의미 드리프트 없이 유지되는가
5. error/cancel path가 stage entry를 부분 실행 상태로 남기지 않는가
6. `main_a.py` thin delegate가 이미 이전 refactor로 이관된 내부 로직을 다시 덮어쓰지 않는가

### 필수 근거

- `tests/test_resume_status.py`
- `tests/test_stage_transition.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_run_stage4_canary.py`

### 산출물

- `docs/2026-03-13/MCP-T3-menu-stage-entry-findings.md`

---

## 7. Terminal 4 - Destructive Ops / Rollback Invariants / Shutdown

### 담당 범위

- `main_a.py`
  - `_reset_stage_2()`
  - `_rewind_stage_2()`
  - `_rollback_episode()`
  - `_wipe_production_data()`
  - `_shutdown_app()`
- 직접 downstream
  - `modules/core/services/project_service.py`
  - runtime tracker/cache objects referenced by `main_a.py`

### 핵심 검사 포인트

1. destructive op confirm/cancel gating이 실제 삭제 범위와 일치하는가
2. DB, draft files, vector memory, tracker, world state, fact ledger, emotion tracker, state delta, foreshadow, preset restore invariant가 유지되는가
3. safe commit 실패 시 partial cleanup 상태가 남는가
4. shutdown 시 metrics/session/audit flush 실패가 non-blocking인지, 정말 non-blocking이어야 하는지
5. app-level cache invalidation과 service-level rollback invariant가 같은 의미를 바라보는가

### 필수 근거

- `tests/test_main_a_rollback.py`
- `tests/test_project_service.py`
- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `tests/integration/test_patch_wiring.py`

### 산출물

- `docs/2026-03-13/MCP-T4-destructive-ops-recovery-findings.md`

---

## 8. Terminal 5 - External Contracts / Regression Surface

### 담당 범위

- `modules/core/services/ui_service.py`
- `modules/core/services/audit_service.py`
- `modules/core/services/state_service.py`
- `modules/core/services/project_service.py`
- `modules/protocols/app_services.py`
- `modules/api/process_runner.py`
- 관련 desktop/bridge reference docs and tests

### 핵심 검사 포인트

1. facade method와 실제 service implementation 사이에 drift가 없는가
2. protocol conformance가 이름상 통과하지만 실제 semantic contract는 어긋나지 않는가
3. `process_runner -> main_a.py`가 기대하는 project ordering과 menu numbering이 안전하게 고정돼 있는가
4. source-string assertion test가 refactor 내성 없이 brittle contract가 되지 않았는가
5. main process, desktop bridge, CLI contract가 서로 다른 selection semantics를 기대하지 않는가

### 필수 근거

- `tests/test_process_runner.py`
- `tests/test_runtime_paths.py`
- `tests/test_protocols_services.py`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`

### 산출물

- `docs/2026-03-13/MCP-T5-control-contract-regression-findings.md`

---

## 9. 명시적 제외 범위

아래 항목은 참조 근거로만 사용하고, 이번 조사 본체로 재포장하지 않는다.

- `Stage 0` 내부 메뉴 심층
- `frontier lag`, `lookahead`
- `UI connectivity`, work_guard template UI
- `Stage 2/3/4` 내부 알고리즘 심층
- desktop IPC 세부 구현

제외 근거 문서:

- `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md`
- `docs/2026-03-13/one-stop-lookahead-execution-ssot.md`
- `docs/2026-03-13/one-stop-frontier-lag-execution-ssot.md`
- `docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md`
- `docs/2026-03-13/stage0-work-guard-style-cache-remediation-execution-ssot.md`

---

## 10. 통합 산출물 규칙

### 터미널 결과 문서

- `docs/2026-03-13/MCP-T1-boot-project-binding-findings.md`
- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`
- `docs/2026-03-13/MCP-T3-menu-stage-entry-findings.md`
- `docs/2026-03-13/MCP-T4-destructive-ops-recovery-findings.md`
- `docs/2026-03-13/MCP-T5-control-contract-regression-findings.md`

### 통합 문서

- `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md`
- `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md`

### 중복 처리 규칙

- 기존 OPUS, frontier-lag, UI-connectivity 문서에서 이미 닫힌 항목은 재오픈 금지
- 단, `main_a.py` control contract 자체가 별도 문제면 신규 `MCP-*` finding 가능
- 신규 finding에는 `duplicate status`를 반드시 적는다:
  - `none`
  - `related-but-new-control-plane-surface`
  - `already-covered-do-not-reopen`

---

## 11. 실행 완료 판정

아래를 모두 만족해야 이번 오더가 닫힌다.

1. T1-T5 문서가 모두 존재한다.
2. 각 문서가 `PASS1 -> PASS2 -> PASS3` 요약을 가진다.
3. 각 finding이 코드 근거, 테스트 근거, downstream 경계, 중복 여부를 모두 가진다.
4. 통합본이 터미널별 ledger와 severity 합계를 재구성한다.
5. 통합본 재감리 문서가 최종 SSOT 승격 가능 여부를 명시한다.

---

## 12. 초기 상태

- 본 오더 문서는 `execution-ready`다.
- 터미널 결과 문서와 통합 문서는 본 오더와 함께 생성되지만, 초기 상태는 모두 `template / not executed`다.
- 결과 문서가 채워지기 전에는 이 트랙에서 확정 finding이 없는 상태로 본다.
