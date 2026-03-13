# [MCP-T5] Control Contract / Regression Findings

> 작성일: 2026-03-13
> 상태: `PASS 3 complete / confirmed`
> 조사 모드: `static / read-only / code-and-test verification`
> 기준 오더: `main_a-control-plane-detail-full-survey-audit-order.md`
> 검증 실행: `pytest tests/test_process_runner.py tests/test_process_runner_stage0_inputs.py tests/test_runtime_paths.py tests/test_protocols_services.py tests/test_audit_service.py tests/test_ui_service.py tests/test_state_service.py tests/test_project_service.py tests/test_resume_status.py tests/test_sweep19.py` -> `137 passed`

---

## 조사 범위

- `modules/core/services/ui_service.py`
- `modules/core/services/audit_service.py`
- `modules/core/services/state_service.py`
- `modules/core/services/project_service.py`
- `modules/protocols/app_services.py`
- `modules/api/process_runner.py`
- 관련 desktop/bridge reference docs and regression tests

## 필수 근거

- `tests/test_process_runner.py`
- `tests/test_runtime_paths.py`
- `tests/test_protocols_services.py`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`

## PASS 기록

- PASS 1: 후보 6건 식별
  - Stage 0 sub_key numbering drift
  - boot confirm 입력의 조건부/무조건 주입 불일치
  - protocol/service semantic drift
  - source-string regression surface
  - lexical project ordering coupling
  - key whitelist duplication
- PASS 2: 후보 2건 제거
  - lexical project ordering coupling은 `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`의 `F-FE-03`으로 이미 포착된 범용 ordinal coupling과 중복
  - key whitelist duplication은 실제 retained issue인 `MCP-T5-001` Stage 0 sub_key miswire에 흡수
- PASS 3: 최종 4건 확정

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MCP-T5-001 | P1 | confirmed | `process_runner.py`, `stage01_helpers.py`, `run_validator.py`, desktop Stage 0 menu | desktop/bridge의 `Stage 0 sub_key` 계약이 `main_a.py` 실제 메뉴 번호와 어긋나 잘못된 Stage 0 핸들러를 실행한다 |
| MCP-T5-002 | P2 | confirmed | `process_runner.py::_build_stdin_sequence`, `main_a.py::boot`, `studio_visualizer.py::menu` | runner가 조건부 장르 불일치 확인 입력을 무조건 주입해, 같은 장르/신규 프로젝트에서는 invalid menu retry에 기대어 동작한다 |
| MCP-T5-003 | P2 | confirmed | `app_services.py`, `ui_service.py`, `state_service.py`, `tests/test_protocols_services.py` | protocol 이름과 추출된 service 구현의 의미가 갈라졌는데 테스트는 mock/StateTracker만 검증해 refactor safety를 과대평가한다 |
| MCP-T5-004 | P3 | confirmed | `tests/test_resume_status.py`, `tests/test_sweep19.py`, `tests/test_frontend_stage0_connectivity.py` | control-plane 회귀망이 source-string assertion에 과의존해 의미적 드리프트는 놓치고 리팩터링 저항만 키운다 |

---

## Findings

### [MCP-T5-001] Stage 0 sub_key contract가 desktop/bridge와 `main_a.py` 사이에서 어긋난다

1. ID
- `MCP-T5-001`

2. Severity
- `P1`

3. 현상 요약
- desktop Stage 0 submenu는 `data-sub-key="1".."6"`을 각각 `기존 방식 / 역설계 / Bible import / Block 확장 / 스타일 분석 / 작품가드`로 라벨링한다.
- 그러나 `main_a.py -> _phase_0_recovery()`가 실제로 읽는 번호는 `1=기존 방식`, `2=컨셉 생성`, `3=역설계`, `4=Bible import`, `5=Block 확장`, `6=스타일 분석`, `7=작품가드`다.
- `ProcessRunner`는 sub_key를 번역하지 않고 그대로 stdin에 넣고, `/run` validator와 prompt-map은 `7`을 아예 허용하지 않는다.
- 결과적으로 desktop에서 `역설계(2)`를 누르면 실제로는 `컨셉 생성`, `Bible import(3)`는 `역설계`, `Block 확장(4)`은 `Bible import`, `스타일 분석(5)`은 `Block 확장`, `작품가드(6)`는 `스타일 분석`으로 라우팅된다.
- 진짜 `작품가드` 선택지인 `7`은 bridge contract 상 표현 불가능하다.

4. 코드 근거
- desktop 라벨/번호: `geuldobi-desktop/src/index.html:2781-2797`
- 메인 메뉴에서 Stage 0 진입: `main_a.py:2153-2154`
- 실제 Stage 0 번호 체계: `modules/core/stage01_helpers.py:56-64`, `modules/core/stage01_helpers.py:74-90`
- sub_key 무가공 전달: `modules/api/process_runner.py:599-609`, `modules/api/process_runner.py:629-638`
- `sub_key == "5"`에만 스타일 캐시 추가 입력 주입: `modules/api/process_runner.py:602-606`, `modules/api/process_runner.py:632-636`
- validator가 `7`을 차단: `modules/api/run_validator.py:27`, `modules/api/run_validator.py:71-77`
- API stub/contract도 `0..6`만 정상으로 취급: `tests/test_api_contract.py:46`, `tests/test_api_contract.py:242-246`, `tests/test_run_validator.py:34-39`, `tests/test_run_validator.py:78-80`
- Stage 0 보강 closure 문서의 intended mapping: `docs/2026-03-13/stage0-work-guard-style-cache-remediation-postfix-3pass-closure.md:35-38`
- `mode=6 -> manage_work_guard`는 helper 테스트로도 고정됨: `tests/test_stage01_helpers.py:448-459`

5. downstream 영향 경계
- desktop Stage 0 submenu
- `bridge_server -> run_validator -> ProcessRunner -> main_a.py` stdin contract
- `Stage01Helpers.phase_0_recovery()`와 `stage_0_extended()`
- Bible 생성/역설계/import/block extension/style analysis/work guard 관련 파일과 DB anchor

6. 현재 테스트 근거 또는 테스트 부재
- 존재하는 테스트는 잘못된 bridge-side 계약을 오히려 고정한다: `tests/test_frontend_stage0_connectivity.py:7-18`, `tests/test_process_runner_stage0_inputs.py:11-29`, `tests/test_run_validator.py:34-39`, `tests/test_run_validator.py:78-80`
- backend 실제 번호 체계와 frontend sub_key label을 대조하는 parity test는 없다.
- 특히 `sub_key="5"`는 desktop에서 스타일 분석으로 보이지만 실제 backend에서는 Block 확장으로 들어가고, runner가 붙이는 `cache_choice`는 Block 확장 입력에 오염된 stdin으로 소비된다.

7. 기존 문서와의 중복 여부
- `duplicate status: related-but-new-control-plane-surface`
- `stage0-work-guard-style-cache` 문서는 CLI/내부 mode 정합성과 work_guard 진입점 자체를 닫았지만, desktop `/run` sub_key 매핑까지는 재감리하지 않았다.

8. 권장 후속 조치
- Stage 0 sub_key SSOT를 한 곳으로 고정하고 frontend/prompt-map/run-validator/process_runner가 그 정의를 공유하게 만든다.
- 선택지는 둘 중 하나다.
- `frontend 1..6 -> backend 1,3,4,5,6,7` 번역 레이어를 bridge/runner에 추가한다.
- 또는 `_phase_0_recovery()` 번호 체계를 desktop 계약에 맞게 다시 정렬한다.
- 이후 `desktop label -> process_runner stdin -> Stage01Helpers target handler`를 한 번에 검증하는 integration test를 추가한다.

### [MCP-T5-002] boot confirm contract가 조건부인데 runner는 무조건 `y`를 주입한다

1. ID
- `MCP-T5-002`

2. Severity
- `P2`

3. 현상 요약
- `main_a.py.boot()`는 저장된 장르가 있고 현재 선택 장르와 다를 때만 `계속하시겠습니까? (y/n)`를 묻는다.
- 반면 `ProcessRunner._build_stdin_sequence()`는 Mode A/B 모두에서 이 확인 입력 `y`를 항상 넣는다.
- stored genre가 없거나 같은 장르인 정상 프로젝트에서는 이 `y`가 실제 확인 프롬프트로 소비되지 않고 메인 메뉴의 첫 번째 잘못된 입력으로 흘러간다.
- 현재는 `StudioVisualizer.menu()`가 raw input을 그대로 넘기고 `_run_main_process()`가 invalid choice를 조용히 무시해 다음 줄을 다시 읽으므로 우연히 복구된다.
- 즉 현재 동작은 명시적 계약이 아니라 `invalid menu retry`라는 부수효과에 기대고 있다.

4. 코드 근거
- 무조건 `y` 주입: `modules/api/process_runner.py:597-599`, `modules/api/process_runner.py:625-627`
- 실제 confirm이 조건부인 boot 경로: `main_a.py:1016-1025`
- menu가 raw input을 그대로 소비: `modules/core/studio_visualizer.py:69-73`
- invalid choice 명시 처리 없이 루프만 반복: `main_a.py:2151-2185`
- runner 테스트도 이 무조건 `y`를 정답으로 잠금: `tests/test_process_runner.py:72-84`, `tests/test_process_runner.py:113-124`

5. downstream 영향 경계
- desktop 모든 실행 키의 boot path
- `prompt_request` 타이밍과 stdout tail diagnostics
- 메뉴 입력 규칙이 stricter해질 미래 refactor
- `process_runner -> main_a.py` interactive contract 전체

6. 현재 테스트 근거 또는 테스트 부재
- runner 단위 테스트는 unconditional `y`를 기대하므로 현재 contract drift를 검출하지 못한다.
- `stored_genre 없음 / 동일 / 불일치` 3개 케이스를 실제 boot와 함께 검증하는 integration test는 없다.

7. 기존 문서와의 중복 여부
- `duplicate status: related-but-new-control-plane-surface`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`의 `F-FE-03`은 숫자 ordinal coupling 일반론을 다뤘고, 이 finding은 그 안에서도 boot confirm의 조건부/무조건 입력 mismatch를 별도 control-plane bug로 확정한 것이다.

8. 권장 후속 조치
- Mode B에서는 실제 prompt 감지 후에만 confirm을 쓰도록 바꾸고, Mode A는 stored genre mismatch 여부를 미리 계산할 수 없으면 pre-seeded `y`를 제거하거나 explicit handshake 단계로 분리한다.
- `stored_genre absent`, `stored_genre same`, `stored_genre mismatch`를 각각 재현하는 runner integration test를 추가한다.

### [MCP-T5-003] protocol 이름과 추출된 service 구현이 분리됐는데 회귀망은 이를 검증하지 않는다

1. ID
- `MCP-T5-003`

2. Severity
- `P2`

3. 현상 요약
- `UIServiceProtocol`은 `log/title`만 요구하지만 실제 `UIService` 추출 구현은 `select_bible/select_treatment/show_volume_table/get_int_input`만 제공한다.
- `StateServiceProtocol`은 사실상 `StateTracker` facade의 50+ 메서드를 모델링하지만, 실제 `modules/core/services/state_service.py`의 `StateService`는 검증/패턴 보조 14개 메서드만 가진다.
- 파일 헤더는 둘 다 protocol과 연결돼 보이도록 적혀 있고, 테스트 파일명도 `서비스 Protocol 테스트`라서 추출된 service 구현이 protocol로 보호된다는 인상을 준다.
- 하지만 실제 테스트는 `MockUI`, `MockAudit`, `StateTracker`만 본다. 따라서 service extraction/DI refactor가 잘못돼도 protocol suite는 계속 초록일 수 있다.

4. 코드 근거
- `UIServiceProtocol`: `modules/protocols/app_services.py:20-32`
- 실제 `UIService` 공개 메서드: `modules/core/services/ui_service.py:14-138`
- `StateServiceProtocol`: `modules/protocols/app_services.py:115-201`
- 실제 `StateService` 공개 메서드: `modules/core/services/state_service.py:19-369`
- protocol 테스트가 mock/StateTracker만 검증: `tests/test_protocols_services.py:60-84`, `tests/test_protocols_services.py:92-119`, `tests/test_protocols_services.py:228-250`
- `main_a.py`는 별도 extracted service를 들고 있지만 context는 여전히 `app.ui`, `state_tracker`, `_audit_event` 등 legacy surface를 함께 사용: `main_a.py:280-317`, `main_a.py:2655-2798`

5. downstream 영향 경계
- Phase 4 service extraction 후속 refactor
- protocol 기반 runtime/type check
- context builder 및 orchestrator 의존성 주입 설계
- 유지보수자가 보는 문서/테스트 신뢰도

6. 현재 테스트 근거 또는 테스트 부재
- `tests/test_protocols_services.py`는 protocol 존재성과 구조적 서브타입 가능성만 본다.
- `UIService`, `AuditService`, `StateService` 구현체를 protocol과 대조하는 테스트는 없다.
- 결과적으로 `AuditService`처럼 실제로 맞는 구현과 `UIService`/`StateService`처럼 의미가 다른 구현이 동일한 녹색 신호 아래 섞여 있다.

7. 기존 문서와의 중복 여부
- `duplicate status: none`

8. 권장 후속 조치
- protocol 이름을 실제 의미에 맞게 재명명하거나 (`StudioUIProtocol`, `StateTrackerProtocol` 등), 추출된 helper service용 별도 protocol을 만든다.
- `tests/test_protocols_services.py`를 `actual impl conforms / actual impl intentionally does not conform`까지 분기해 semantic drift를 명시적으로 잠근다.

### [MCP-T5-004] control-plane 회귀망이 source-string assertion에 과의존한다

1. ID
- `MCP-T5-004`

2. Severity
- `P3`

3. 현상 요약
- 일부 회귀 테스트가 실제 동작이 아니라 `main_a.py`와 frontend 소스에 특정 문자열이 존재하는지만 확인한다.
- 이 방식은 helper extraction, 변수명 변경, call-site 이동 같은 비행동적 리팩터링을 곧바로 붉게 만들지만, 정작 `MCP-T5-001` 같은 의미적 contract drift는 놓친다.
- 현재 T5 범위에서 source-string 계열 테스트는 control-plane 정합성보다 코드 모양 보존에 더 가깝다.

4. 코드 근거
- resume status call-site를 source text로 검증: `tests/test_resume_status.py:45-48`
- boot null-guard를 source text로 검증: `tests/test_sweep19.py:11-20`
- frontend Stage 0 submenu도 backend mapping이 아니라 HTML 문자열만 확인: `tests/test_frontend_stage0_connectivity.py:7-18`

5. downstream 영향 경계
- `main_a.py` thin delegate 정리
- helper/service extraction
- frontend markup cleanup
- control-plane refactor 전반의 CI 신호 품질

6. 현재 테스트 근거 또는 테스트 부재
- 이번 조사에서 관련 테스트는 모두 통과했지만, 더 높은 위험의 semantic contract drift인 `MCP-T5-001`은 검출하지 못했다.
- behavioral seam을 타는 integration/contract test가 부족하다.

7. 기존 문서와의 중복 여부
- `duplicate status: none`

8. 권장 후속 조치
- source-string assertion은 최소화하고, 실제 선택지 테이블/핸들러 매핑/runner stdin 결과를 검증하는 behavior test로 대체한다.
- 특히 `Stage 0 submenu label -> sub_key -> backend handler`, `boot conditional confirm`, `resume status hook`는 실행 결과 중심 테스트로 옮긴다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| desktop -> bridge -> runner -> `main_a.py` live E2E | 미실행 | 실제 `/run` 호출로 `Stage 0` sub_key와 boot confirm 소비 순서를 end-to-end 재현 |
| packaged mode interactive replay | 미실행 | frozen backend + desktop packaged 환경에서 동일 contract 재검증 |
| protocol/service parity | 미검증 | actual implementation 객체를 protocol과 직접 대조하는 focused test |

## PASS 요약

- PASS1 후보 6건 -> PASS2 제거 2건 -> 최종 4건
- retained 최고 위험도는 `MCP-T5-001(P1)`이며, 이는 wrong stage target과 unintended Stage 0 mutation으로 이어질 수 있다.
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`의 기존 `F-FE-03`은 유지하되, 이번 문서는 그 일반론 아래에서 실제 miswired Stage 0/control-plane 사례를 신규 확정했다.
