# OPUS TF 5-Terminal Deep-Dive Remediation Execution SSOT

## Execution Status Update (2026-03-13)

- Status: `execution-in-progress` -> `R-1` through `R-6` implemented in codebase
- R-4: API/Desktop contract aligned to runtime states `idle/starting/running/stopping/error`, and real `bridge_server` HTTP tests were added
- R-5: misleading pytest-style lite-mode probe renamed to `manual_ui_discovery_probe.py`; manual-only boundaries were documented for lite-mode and operator tools
- R-6: shared context cache namespaces now include project-scoped `ep` / `arc` tokens to reduce cross-project cache reuse
- Validation:
  - `python -m pytest -q tests/test_run_validator.py tests/test_api_contract.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_base_agent.py tests/test_tier4_ensemble_caching.py`
  - Result: `194 passed in 4.26s`

- 작성일: 2026-03-13
- 상태: `execution-ready`
- 문서 역할: [OPUS-TF-5terminal-deep-dive-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings.md)와 [OPUS-TF-5terminal-deep-dive-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings-3pass-reaudit.md)를 기준으로, 3차 심층 감사에서 확정된 신규 ledger와 historical open gap을 실제 조치 패키지로 잠그는 단일 실행 SSOT
- 문서 성격: 본 문서는 코드 수정 기록이나 테스트 실행 보고가 아니다. 범위 고정, 우선순위 잠금, 패키지 분할, acceptance 정의까지만 담당한다.
- 금지사항: 총건수 확대 해석, 새 finding 추정 삽입, 코드 미수정 상태에서 완료 선언, 기존 1차·2차 ledger의 중복 재보고

## 1. 기준 문서

- [OPUS-TF-5terminal-deep-dive-master-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md)
- [OPUS-TF-5terminal-deep-dive-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-execution-ssot.md)
- [OPUS-TF-5terminal-deep-dive-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings.md)
- [OPUS-TF-5terminal-deep-dive-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings-3pass-reaudit.md)
- [S-T1-stage0-ui-flow-deep-dive-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/S-T1-stage0-ui-flow-deep-dive-findings.md)
- [S-T2-cross-stage-root-cause-deep-dive-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/S-T2-cross-stage-root-cause-deep-dive-findings.md)
- [S-T3-lite-mode-tools-deep-dive-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/S-T3-lite-mode-tools-deep-dive-findings.md)
- [S-T4-api-desktop-deep-dive-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/S-T4-api-desktop-deep-dive-findings.md)
- [S-T5-security-performance-scale-deep-dive-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/S-T5-security-performance-scale-deep-dive-findings.md)

## 2. 목표

이번 실행 SSOT의 목표는 신규 심층 ledger `11건`과, deep-dive에서 새 ID로 재흡수되지 않은 historical open gap `2건`을 뒤섞지 않고 실제 수정 순서와 종료 조건으로 고정하는 것이다.

설명:

- `T2-001`은 historical root-cause remains이지만, 이번 심층 감사에서 `S-T1-002`, `S-T2-001`로 구체 위치와 책임 경계가 다시 식별됐으므로 별도 historical 추가 카운트로 세지 않는다.
- 반면 `T3-003`, `T3-004`는 새 deep-dive ID가 부여되지 않은 채 test gap으로 남아 있어 별도 historical open gap으로 유지한다.

이번 SSOT가 닫아야 하는 축은 아래 6개다.

1. Desktop 위험 키 승인 경계 복구
2. Stage 0 복구 경로 메뉴 단일화와 silent wrong result 제거
3. `plot_roadmap`를 save patch가 아니라 생성기 산출물 계약으로 승격
4. API/Desktop 검증 경로를 실서버 계약과 다시 맞춤
5. Lite Mode / Tools / 수동 DB 도구군을 production 경계 밖으로 격리
6. 글로벌 context cache namespace를 프로젝트 단위로 정리

이번 SSOT는 "심층 감사에서 코드가 이미 수정됐다"는 전제를 두지 않는다. 반대로, 아직 수정되지 않은 상태를 기준으로 **무엇을 어떤 순서로 닫아야 하는지**만 잠근다.

## 3. 실행 원칙

### 원칙 A. P1 승인 경계와 silent wrong result를 가장 먼저 닫는다

- `S-T4-001`은 Desktop 경로에서 risk approval dual-control을 약화시킨다.
- `S-T1-001`은 사용자 선택이 조용히 기본값으로 변질되는 silent wrong result다.
- 둘 다 "장애보다 늦게 보이는 오동작"이라 우선순위를 가장 높게 둔다.

### 원칙 B. Stage 0 handoff는 save hook이 아니라 생성기 계약으로 닫는다

- `S-T1-002`, `S-T2-001`의 핵심은 저장 직전 패치가 handoff 계약을 대신하고 있다는 점이다.
- 호출자 보정이 아니라 생성 결과 자체가 Stage 2 입력 스키마를 만족해야 한다.

### 원칙 C. 테스트 갭은 후속이 아니라 동시 종료 조건이다

- `S-T4-002`와 historical `T3-003`, `T3-004`는 "나중에 보강" 항목이 아니다.
- 승인 경계와 handoff 경계를 고쳤다면 같은 패키지에서 실경로 테스트도 함께 닫아야 한다.

### 원칙 D. Lite/Tools는 기능 확장이 아니라 경계 명시가 우선이다

- `S-T3-*`의 본질은 새 기능 부족이 아니라 host-bound 수동 도구가 production abstraction을 우회한다는 점이다.
- 따라서 1차 목표는 "고도화"가 아니라 `manual-only`, `legacy`, `archive` 구분과 직접 mutation 축소다.

### 원칙 E. scale debt는 마지막이지만 누락하지 않는다

- `S-T5-001`은 즉시 P1은 아니지만, 멀티프로젝트 배치에서 성능/격리 cross-talk를 만든다.
- 상위 경계를 닫은 뒤 별도 패키지로 정리한다.

## 4. Remediation Work Packages

### R-1. Desktop 위험 키 승인 경계 복구

대상 finding:

- `S-T4-001`

대상 파일:

- [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js)
- [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py)
- 관련 계약 문서: [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml)

구현 원칙:

- Desktop IPC 표면에 `approval_id`를 명시적으로 포함한다.
- `GEULDOBI_DESKTOP_MODE=1`이라는 이유만으로 위험 키를 auto-approve하지 않는다.
- Desktop 전용 우회가 필요하다면 implicit bypass가 아니라 operator-confirmed fallback으로 분리한다.
- OpenAPI 문서, preload 시그니처, main process body, backend risk gate가 같은 계약을 보게 한다.

acceptance:

- Desktop `runKey()` 계열에서 위험 키 호출 시 `approval_id`를 실제로 전달할 수 있다.
- `bridge_server`는 desktop mode에서도 `approval_id` 없는 위험 키를 거절하거나, 별도 명시적 승인 경로만 허용한다.
- 승인 필요 키 `44/77/88/99`에 대해 Desktop 실경로 테스트가 존재한다.
- 문서/API/IPC가 동일한 승인 계약을 사용한다.

### R-2. Stage 0 복구 경로 메뉴 단일화

대상 finding:

- `S-T1-001`
- `S-T1-003`

대상 파일:

- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- [__init__.py](C:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py)
- [project_support.py](C:/Users/User/Desktop/글도비/modules/core/project_support.py)
- 관련 테스트:
  - [test_stage0_pov.py](C:/Users/User/Desktop/글도비/tests/test_stage0_pov.py)
  - [test_stage01_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage01_helpers.py)

구현 원칙:

- `phase_0_recovery()`는 본체 `StageZeroManager`와 동일한 상수/정규화 경로를 사용한다.
- 외부 시점 삽입 정책 문자열은 display text와 stored value를 분리해 관리한다.
- 주인공 설정 메뉴는 구현 2개를 유지하지 않고 하나의 canonical helper 또는 상수 집합으로 수렴시킨다.
- 깨진 한글 리터럴에 의존하는 alias 매핑을 제거한다.

acceptance:

- Stage 0 복구 경로에서 정책 메뉴 `[1]/[2]/[3]` 선택이 각각 `금지/제한적 허용/적극 허용`으로 정확히 저장된다.
- 본체 메뉴와 helper 메뉴가 동일한 선택지와 저장값 집합을 사용한다.
- helper 경로 전용 회귀 테스트가 추가돼 본체 테스트만으로는 놓치던 drift를 차단한다.

### R-3. `plot_roadmap` 생성기 계약 승격

대상 finding:

- `S-T1-002`
- `S-T2-001`

대상 파일:

- [__init__.py](C:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py)
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- [story_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py)
- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)
- [stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- 관련 테스트:
  - [test_stage01_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage01_helpers.py)
  - [test_reverse_expander_g2.py](C:/Users/User/Desktop/글도비/tests/test_reverse_expander_g2.py)

구현 원칙:

- `generate_from_concept()` 반환물 자체가 `plot_roadmap`를 포함하도록 만든다.
- 역설계/복구 경로도 Stage 2가 기대하는 최소 `plot_roadmap` 스텁을 반환물에서 보장한다.
- `_ensure_plot_roadmap()`는 생성기 계약을 보완하는 안전망으로만 남기거나, 생성기 내로 흡수해 책임을 축소한다.
- save 이전 예외 경로나 in-memory consumer도 불완전 Bible을 보지 않게 한다.

acceptance:

- Stage 0 생성 직후 in-memory Bible에 `plot_roadmap`가 존재한다.
- Stage01Helpers save hook을 거치지 않아도 Stage 2가 계약 필드를 읽을 수 있다.
- save hook dependent contract가 아니라 generator-owned contract라는 점이 테스트로 고정된다.

### R-4. API/Desktop 실경로 계약 테스트 복구

대상 finding:

- `S-T4-002`
- historical open gap: `T3-003`
- historical open gap: `T3-004`

대상 파일:

- [test_api_contract.py](C:/Users/User/Desktop/글도비/tests/test_api_contract.py)
- [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py)
- [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)
- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- [validation_orchestrator.py](C:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py)
- [test_stage3_orchestrator.py](C:/Users/User/Desktop/글도비/tests/test_stage3_orchestrator.py)
- [test_validation.py](C:/Users/User/Desktop/글도비/tests/test_validation.py)

구현 원칙:

- RouterStub 중심 계약 테스트를 실제 `bridge_server` 또는 최소한 실제 런타임과 동일한 상태모델로 전환한다.
- `waiting_input` 같은 과거 상태를 더 이상 canonical contract로 유지하지 않는다.
- Blueprint→Stage 4 handoff 필드 계약과 advisory 병렬 경로는 단순 mock가 아니라 실경계 기준 회귀 테스트를 가진다.
- R-1 승인 경계 테스트와 R-3 handoff 테스트를 같은 계약군으로 묶어, "수정은 됐는데 검증은 옛 스텁" 상태를 금지한다.

acceptance:

- API 계약 테스트가 실제 서버 상태모델 `idle/starting/running/stopping/error`를 기준으로 돌아간다.
- Desktop 위험 키 승인 경계와 API 계약 테스트가 같은 요청/응답 계약을 사용한다.
- Blueprint handoff와 advisory 병렬 실행에 대한 cross-stage 회귀 테스트가 존재한다.

### R-5. Lite Mode / Tools / 수동 DB 도구군 격리

대상 finding:

- `S-T3-001`
- `S-T3-002`
- `S-T3-003`
- `S-T3-004`

대상 파일:

- [ui_discovery.py](C:/Users/User/Desktop/글도비/lite_mode/bridge/ui_discovery.py)
- [gemini_driver.py](C:/Users/User/Desktop/글도비/lite_mode/bridge/gemini_driver.py)
- [test_ui_discovery.py](C:/Users/User/Desktop/글도비/lite_mode/test_ui_discovery.py)
- [normalize_arcs_db.py](C:/Users/User/Desktop/글도비/tools/normalize_arcs_db.py)
- [db_porter.py](C:/Users/User/Desktop/글도비/tools/db_porter.py)
- [fix_future_items.py](C:/Users/User/Desktop/글도비/tools/fix_future_items.py)
- [make_BP.py](C:/Users/User/Desktop/글도비/tools/make_BP.py)
- [concat_txt.py](C:/Users/User/Desktop/글도비/tools/concat_txt.py)
- [expand_ep15.py](C:/Users/User/Desktop/글도비/tools2/expand_ep15.py)
- [blueprint_editor.py](C:/Users/User/Desktop/글도비/main_tools/blueprint_editor.py)

구현 원칙:

- Lite Mode raw Gemini 경로는 production router 대체 경로가 아니라 `manual-only`로 명시한다.
- `test_*.py` 이름을 가진 live-network 진단 스크립트는 테스트 스위트 밖으로 이동하거나 수동 진단임을 명확히 한다.
- 절대경로/특정 작품 하드코딩/직접 DB mutation 스크립트는 `legacy`, `archive`, `manual_ops` 등 격리 폴더로 분리한다.
- `blueprint_editor.py`는 DBManager 우회 수동 도구임을 문서화하고, 최소한 대상 DB/백업/복구 책임을 명시한다.

acceptance:

- CI/pytest 관점에서 수동 네트워크 스크립트가 테스트로 오인되지 않는다.
- host-bound 및 direct-mutation 도구가 production-support 도구와 분리된다.
- Lite Mode와 보조 도구의 운영 등급이 문서/경로/네이밍에서 드러난다.

### R-6. 글로벌 context cache namespace 하드닝

대상 finding:

- `S-T5-001`

대상 파일:

- [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py)
- [chief_writer.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py)
- [blueprint_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py)
- [arc_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/arc_ensemble.py)
- [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py)
- [analyst.py](C:/Users/User/Desktop/글도비/modules/domain/agents/analyst.py)

구현 원칙:

- context cache namespace는 회차/아크 번호만이 아니라 실제 프로젝트 식별자를 포함하도록 통일한다.
- 전역 50-entry LRU가 프로젝트 간 상호 축출을 만드는지 관측 포인트를 추가한다.
- scale debt를 정합성 버그처럼 과장하지 않되, 배치/멀티프로젝트 환경에서의 비용 문제는 별도 acceptance로 묶는다.

acceptance:

- 주요 agent 호출부가 같은 namespace 규칙을 사용한다.
- cache miss/hit/eviction 로그 또는 측정 지표가 프로젝트 단위로 분리 가능하다.
- 멀티프로젝트 환경에서 동일 `ep/arc` 번호 충돌 가능성이 설계상 제거된다.

## 5. 실행 순서

실행 순서는 아래로 고정한다.

1. `R-1 Desktop 위험 키 승인 경계 복구`
2. `R-2 Stage 0 복구 경로 메뉴 단일화`
3. `R-3 plot_roadmap 생성기 계약 승격`
4. `R-4 API/Desktop 실경로 계약 테스트 복구`
5. `R-5 Lite Mode / Tools / 수동 DB 도구군 격리`
6. `R-6 글로벌 context cache namespace 하드닝`

순서 고정 이유:

- `R-1`, `R-2`는 신규 P1 두 건을 직접 닫는다.
- `R-3`는 신규 P2이지만 historical root-cause 핵심이라 상위 우선순위다.
- `R-4`는 상위 수정의 검증 경계를 복구하는 패키지다.
- `R-5`, `R-6`는 격리/scale 계열이므로 상위 계약이 닫힌 뒤 수행한다.

## 6. 패키지별 완료 조건

### C-1. P1 해소 조건

- `S-T4-001`, `S-T1-001`이 각각 코드/테스트/문서 기준으로 닫힌다.
- Desktop 위험 키와 Stage 0 외부 시점 정책이 모두 "사용자 선택 그대로" 반영된다.

### C-2. generator-owned handoff 조건

- `plot_roadmap`가 save hook이 아니라 생성기 반환물에서 보장된다.
- Stage 0→Stage 2 handoff는 helper 보정 없이도 계약 필드를 만족한다.

### C-3. 실경로 검증 조건

- RouterStub 기준 테스트만 녹색인 상태를 허용하지 않는다.
- Desktop 승인, API 상태모델, Blueprint handoff, advisory 병렬 경로가 실제 런타임 기준 회귀 테스트를 가진다.

### C-4. 격리 조건

- Lite Mode와 host-bound 도구군이 production support와 구분된다.
- 수동 네트워크/DB 도구는 실행 위험이 경로/네이밍/문서에 드러난다.

### C-5. scale debt 조건

- global cache namespace 규칙이 통일된다.
- 프로젝트 간 cache cross-talk를 관측할 최소 수단이 존재한다.

## 7. 비목표

- deep-dive ledger 외 신규 심층 finding 추정 추가
- 1차/2차 전체 수정 오더 재작성
- live rerun 결과를 본 문서에 선반영
- 코드 미수정 상태에서 "완료" 판정
- deep-dive와 무관한 product roadmap 확장

## 8. Confidence Gate

이번 실행 SSOT는 아래 조건을 만족할 때 `95%` 확신도로 잠근다.

1. 신규 P1 `2건`과 신규 P2 `8건`, 신규 P3 `1건`이 전부 패키지에 배정된다.
2. historical open gap `T3-003`, `T3-004`가 누락 없이 테스트/계약 패키지에 흡수된다.
3. 기존 resolved/carry-over 항목을 새 remediation 대상으로 잘못 재삽입하지 않는다.
4. 각 패키지가 `대상 finding`, `대상 파일`, `구현 원칙`, `acceptance`를 모두 가진다.
5. 본 문서에 대한 3PASS 감리 문서가 별도로 존재하고 최종 확신도 `95%`를 명시한다.

## 9. 다음 단계

본 문서 다음 작업 순서는 아래와 같다.

1. 본 SSOT 기준으로 실제 코드 수정 오더를 실행
2. 패키지별 테스트 증거를 수집
3. 실행 결과를 별도 remediation completion report로 문서화
4. 필요시 live rerun / narrow e2e를 후속 검증으로 추가
