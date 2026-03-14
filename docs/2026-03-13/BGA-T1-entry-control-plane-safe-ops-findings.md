# [BGA-T1] Entry / Control Plane / Safe Ops Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `backend-global-full-survey-master-audit-order.md`
> 실행 요약: `PASS1 후보 5건 -> PASS2 제거 3건 -> PASS3 확정 2건`

---

## 조사 범위

- `main_a.py`
  - `boot()`
  - `_select_project()`
  - `_run_main_process()`
  - `_one_stop_pipeline_frontier_lag()`
- `modules/api/process_runner.py`
- `modules/api/run_validator.py`
- `modules/api/bridge_server.py`
- `modules/core/system.py`
- `modules/core/project_manager.py`
- `modules/core/runtime_paths.py`
- `docs/implementation/prompt-map-v1.json`
- `geuldobi-desktop/src/index.html`

## 필수 근거

- 읽은 테스트:
  - `tests/test_runtime_paths.py`
  - `tests/test_project_support.py`
  - `tests/test_stage_transition.py`
  - `tests/test_process_runner.py`
  - `tests/test_process_runner_stage0_inputs.py`
  - `tests/test_run_validator.py`
  - `tests/test_api_contract.py`
- 읽은 참조 문서:
  - `docs/2026-03-12/backend-health-full-survey-3pass-audit.md`
  - `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md`
  - `docs/2026-03-13/main_a-live-wiring-contract-detail-consolidated-findings.md`
- 실행 검증:
  - `pytest -q tests/test_runtime_paths.py tests/test_project_support.py tests/test_stage_transition.py tests/test_process_runner.py tests/test_process_runner_stage0_inputs.py tests/test_run_validator.py`
  - 결과: `113 passed in 2.57s`
  - `pytest -q tests/test_api_contract.py`
  - 결과: `55 passed in 0.56s`
- 정적 교차 검증:
  - `main_a.py`, `process_runner.py`, `run_validator.py`, `bridge_server.py`, `prompt-map-v1.json`, `index.html` key/sub_key/mode 흐름 grep

## PASS 기록

- PASS 1:
  - 후보 1: boot/project root 바인딩이 여전히 `GEULDOBI_PROJECTS_ROOT` SSOT를 우회하는가
  - 후보 2: 프로젝트별 `.env`가 여전히 root `.env`로 재오염되는가
  - 후보 3: `/run key=7` Frontier Lag 경로가 prompt-map과 같은 interactive contract를 공유하는가
  - 후보 4: `/run key=5`가 여전히 외부 실행 surface에 노출되어 있는가
  - 후보 5: Stage 0 `sub_key=0` cancel 허용과 desktop UI가 의미상 충돌하는가
- PASS 2:
  - 후보 1 제거: `main_a.py::_get_projects_root()`와 `StudioSystem.boot_v20_project(..., projects_root=...)`, `ProjectContext(root_dir=...)` 경로로 root binding drift는 현재 코드에서 해소됐다.
  - 후보 2 제거: `ProjectContext.__init__`에서 무경로 `load_dotenv()`가 제거되어 project `.env` 재오염 시나리오는 현재 코드 기준 재현되지 않는다.
  - 후보 5 제거: Stage 0 `sub_key=0`은 main menu 복귀용 cancel semantics로 해석 가능하고, 현재 근거만으로는 desktop/UI contract 결함까지 올릴 정도의 오동작 증거가 부족했다.
- PASS 3:
  - 확정 2건만 `BGA-T1-*`로 채택

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| `BGA-T1-001` | `P1` | confirmed | `modules/api/process_runner.py`, `modules/api/bridge_server.py`, `docs/implementation/prompt-map-v1.json`, `main_a.py::_one_stop_pipeline_frontier_lag()` | `/run key=7` Frontier Lag이 prompt-broker Mode B 대상에서 빠져 interactive 계약이 무너진다 |
| `BGA-T1-002` | `P2` | confirmed | `modules/api/run_validator.py`, `modules/api/bridge_server.py`, `docs/implementation/prompt-map-v1.json`, `geuldobi-desktop/src/index.html` | `/run`이 UI 전용 `key=5` 종료 경로를 일반 실행 키로 공개한다 |

## Final Findings

### [BGA-T1-001] P1 - `key=7` Frontier Lag이 Mode B에서 누락되어 `/run` interactive contract가 깨진다

1. ID
   - `BGA-T1-001`
2. Severity
   - `P1`
3. 현상 요약
   - `/run` 표면에서는 `key=7` Frontier Lag을 일반 실행 키로 허용하고 desktop UI도 별도 버튼을 노출한다.
   - 그런데 `ProcessRunner.MODE_B_KEYS`에는 `7`이 빠져 있어, 이 경로만 PromptBroker 기반 interactive mode가 아니라 Mode A 사전 주입 경로로 실행된다.
   - 반면 실제 `main_a.py::_one_stop_pipeline_frontier_lag()`는 batch size, skip/stop 선택, continue 확인, 메뉴 복귀 입력까지 여러 interactive prompt를 요구한다.
   - 결과적으로 key 7은 `prompt-map-v1.json`이 선언한 interactive contract를 bridge/runtime에서 실제로 충족하지 못한다.
4. 코드 근거
   - `docs/implementation/prompt-map-v1.json` key `7`은 `onestop_batch_count`, `onestop_fail_action`, `onestop_continue` 3단계를 요구한다.
   - `modules/api/process_runner.py:79` `MODE_B_KEYS = {"0","1","2","3","4","5","6","44","77","88","99"}`로 `7`이 누락돼 있다.
   - `modules/api/process_runner.py:285`는 key가 `MODE_B_KEYS`에 없으면 Mode A를 선택한다.
   - `main_a.py:3774`, `main_a.py:3883`, `main_a.py:3901`, `main_a.py:3961`은 Frontier Lag 경로가 실제 사용자 입력을 요구함을 보여 준다.
   - `geuldobi-desktop/src/index.html:2830`은 Frontier Lag 버튼을 `data-key="7"`로 노출한다.
5. downstream 영향 경계
   - bridge `/run` 호출
   - desktop Frontier Lag 버튼
   - PromptBroker / `/run/{run_id}/input` interactive 체계
   - One-Stop Frontier Lag 자동화 경로 전체
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_api_contract.py`는 key `7`을 정상 키로 수락한다.
   - `tests/test_process_runner.py`와 `tests/test_run_validator.py`는 현재 green이지만, key `7`이 Mode B로 들어가 PromptBroker 단계를 거치는지 검증하는 테스트는 없다.
   - 즉, 현재 회귀망은 `key=7 accepted`까지만 잠그고 `key=7 interactive contract honored`는 잠그지 못한다.
7. 기존 문서와의 중복 여부
   - `related-but-new-control-plane-surface`
   - 기존 `MCP-T5-*`는 external control contract drift를 넓게 다뤘지만, 현재 코드 기준 `key=7`의 Mode B 누락과 prompt-map 충돌은 별도 재확인이 필요했다.
8. 권장 후속 조치
   - `MODE_B_KEYS`에 `7`을 포함해 Frontier Lag을 key `6`과 같은 interactive broker 경로에 올린다.
   - 회귀 테스트를 추가한다: `key=7 -> runner mode B -> prompt_request 단계 발생` 검증.
   - `prompt-map-v1.json`, desktop 버튼, runner mode selection을 하나의 SSOT로 묶는 검증을 추가한다.

### [BGA-T1-002] P2 - `/run`이 UI 전용 `key=5` 종료 경로를 일반 실행 키로 공개한다

1. ID
   - `BGA-T1-002`
2. Severity
   - `P2`
3. 현상 요약
   - desktop UI는 runtime 중지에 별도 `stop` action을 사용하고, prompt-map은 key `5`를 `ui_only_action: exit_app`으로 기록한다.
   - 그런데 backend `/run` validator는 `5`를 일반 허용 key로 처리하고, API contract test도 이를 정상 실행 키로 고정한다.
   - 그 결과 일반 `/run` surface만으로 앱 종료 시퀀스를 호출할 수 있고, 이는 `stop current run`과 `exit app`의 control-plane 의미를 섞는다.
4. 코드 근거
   - `docs/implementation/prompt-map-v1.json` key `5`는 `ui_only_action: "exit_app"`로 선언돼 있다.
   - `modules/api/run_validator.py:25`는 `ALLOWED_KEYS`에 `"5"`를 포함한다.
   - `modules/api/bridge_server.py:1287`은 validator 통과 후 별도 제한 없이 `runner.start(key=key, ...)`를 호출한다.
   - `tests/test_api_contract.py:254`는 key `5`를 일반 accepted key로 회귀 고정한다.
   - `geuldobi-desktop/src/index.html:2854`, `geuldobi-desktop/src/index.html:6556`은 UI가 종료가 아니라 `data-action="stop"` runtime 제어를 별도 경로로 사용함을 보여 준다.
5. downstream 영향 경계
   - `/run` 외부 호출자 전부
   - desktop/bridge action semantics
   - operator가 이해하는 `stop` vs `exit` 의미 구분
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_api_contract.py`는 현 구조를 green으로 고정한다.
   - 그러나 `/run`이 `exit_app`을 노출하면 안 된다는 테스트는 없다.
   - `tests/test_process_runner.py`도 key `5`를 외부 control-plane 금지 대상으로 다루지 않는다.
7. 기존 문서와의 중복 여부
   - `none`
   - 기존 조사 문서는 Stage 0 sub_key나 boot confirm drift에 집중했고, `key=5`의 public `/run` 노출 자체를 독립 finding으로 잠그지 않았다.
8. 권장 후속 조치
   - `/run` public contract에서 key `5`를 제거하거나, 내부 cleanup 전용 경로로 격리한다.
   - UI/bridge는 계속 `stop` action을 런타임 제어 SSOT로 사용하고, 앱 종료는 별도 operator-only action으로 분리한다.
   - 회귀 테스트를 추가한다: `/run key=5` rejected 또는 privileged-only 처리 검증.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| boot/project root가 `GEULDOBI_PROJECTS_ROOT` SSOT를 우회한다 | removed | `main_a.py::_get_projects_root()`, `StudioSystem.boot_v20_project(..., projects_root=...)`, `ProjectContext(root_dir=...)` 경로로 현재는 root binding이 일치한다. |
| 프로젝트별 `.env`가 `ProjectContext` 초기화 중 root `.env`로 재오염된다 | removed | 현재 `ProjectContext.__init__`에는 무경로 `load_dotenv()`가 없다. 이전 control-plane finding은 현재 코드 기준 stale이다. |
| Stage 0 `sub_key=0` cancel 허용이 desktop UI와 즉시 충돌한다 | removed | UI가 cancel 버튼을 노출하지 않는 건 사실이지만, 현재 근거만으로 run-time 오동작까지는 확정할 수 없다. |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `key=7` Frontier Lag Mode B 경로 | 테스트 공백 | `runner.start(key=\"7\")`에서 prompt broker가 실제로 `prompt_request`를 발행하는지 검증 |
| `key=5` public `/run` 노출 정책 | 테스트 공백 | `/run key=5`를 rejected 또는 privileged-only로 강제하는 계약 테스트 |
| entry contract stale 문서 정리 | 부분 공백 | 구 `MCP-T1-*` root/env binding finding이 현재 코드 기준 해소됐음을 별도 재감리 또는 closure note로 남길지 결정 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
