# 오늘 안의 코드 건강도 소거·UI 재감리·빌드 로드맵

작성일: 2026-03-12  
상태: `1차 canary 완료 / rerun deferred until Track 0 fixes`  
문서 역할: 오늘 남은 작업의 운영 SSOT  
우선순위: `today roadmap > stage4-canary-execution-runbook.md / system-wide-full-remediation-execution-plan.md`  

## 1. 목적

오늘 안에 아래 목표를 순서대로 달성한다.

1. 백엔드 기준 open `P0/P1/P2` 제거
2. 데스크톱/브리지 기준 open `P0/P1/P2` 제거
3. UI/desktop 연결면 3-pass 재감리
4. build 재현성 확인 후 desktop build

핵심 원칙:

- `디자인 개편`보다 `계약면 하드닝`을 우선한다.
- 오늘은 `canary-first`가 아니라 `Track 0 선행 후 limited canary 1회`를 기준으로 움직인다.
- 오늘 목표는 `기능 확장`이 아니라 `건강도 소거 + 재현성 확보 + 빌드 가능 상태`다.

## 2. 상위 문서

- `docs/2026-03-12/stage4-canary-execution-runbook.md`
- `docs/2026-03-12/system-wide-full-remediation-execution-plan.md`
- `docs/2026-03-12/system-wide-full-remediation-3pass-audit.md`
- `docs/2026-03-12/stage4-canary-log-audit.md`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`

조건부 보조 참고 문서:

- `docs/2026-03-12/roadmap-external-full-survey-3pass-audit.md`
  - 적용 조건: 오늘 작업이 `metrics/cost`, `artifact logging`, `test coverage gap`, `WorkGuard/관측성 위생` 축으로 확장될 때만 참조
  - 사용 목적: `BUG-PRICE-1`, `artifact_logging` 파일 I/O 방어, 신규 로깅 모듈 테스트 공백, WorkGuard/디렉터리 잔여물 같은 외부 전수조사 finding을 오늘 로드맵과 교차 검증하는 보조 근거로 사용
  - 사용 제한: 이 문서는 today roadmap의 실행 SSOT가 아니며, canary 판정·desktop/build gate·최종 우선순위를 직접 대체하지 않는다
- `docs/2026-03-12/TF-VERTEX-migration-full-audit.md`
  - 적용 조건: 오늘 작업이 `provider routing`, `config/models.yaml`, `metrics_collector.py`, `base_agent.py` 재개입으로 확장될 때만 참조
  - 사용 목적: Vertex 전환 그 자체가 아니라, 멀티-provider SSOT, 가격표 정합성, direct client 우회 경로, fallback 조건을 재판정할 때 보조 근거로 사용
  - 사용 제한: 이 문서는 today roadmap의 실행 SSOT가 아니다. 리전 가용성 1건 미확인 상태이므로 `desktop/UI/build` 의사결정의 직접 gate로 쓰지 않는다.
- `docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md`
  - 적용 조건: 오늘 작업이 `Stage 4 context contract`, `CW-Director handoff`, `PASS_WITH_FIX local patch feedback`, `patch provenance` 재판정으로 확장될 때 참조
  - 사용 목적: 주요 LLM 입력 지도, `CW`와 `Director`의 목표 정렬성, retained P2 2건(`local patch feedback 축약`, `story_context patch provenance 미주입`)을 근거 기반으로 확인할 때 보조 문서로 사용
  - 사용 제한: 이 문서는 today roadmap의 실행 SSOT가 아니다. 정적 감사 95% 상한 문서이며 active canary 산출물 재판독을 대체하지 않는다.
- `docs/2026-03-12/TF-S3-context-contract-audit.md`
  - 적용 조건: 오늘 작업이 `Stage 3 external contract`, `S3→S4 handoff`, `PASS_WITH_FIX semantics` 재개입으로 확장될 때 참조
  - 사용 목적: Stage 3 컨텍스트 계약과 Stage 4 계약의 접점을 다시 잠그고, Stage 3 쪽 잔여 contract drift가 오늘 작업 범위에 재진입하는지 판정할 때 보조 근거로 사용
  - 사용 제한: 이 문서는 today roadmap의 실행 SSOT가 아니다. Stage 4 canary 판정이나 desktop/build gate를 직접 대체하지 않는다.

## 3. 현재 상태

- `Stage 4 limited canary` 1차 결과 확인 완료. 원인 특정됨.
  - `test_05`: WARN — `pass_rate_monitor` 미동작 (합격률 통계 누락)
  - `test_06`: FAIL — 생산 미시작 (draft 0건)
  - `test_07`: FAIL — `candidate_key` 불일치 2건 + `artifact_path` 불일치 2건 (sink 간 전략명 한글/영문 혼재)
- backend 쪽은 직전 패치와 targeted regression 기준으로 상당수 contract fix가 반영된 상태다. 단, 카나리가 드러낸 sink alignment P1이 열려 있다.
- frontend/desktop 쪽은 최근 감사 기준 `P1 2건`, `P2 2건`, `Observation 1건`이 남아 있다.
- packaged desktop 재현성은 아직 닫히지 않았다.

## 4. 오늘의 완료 조건

오늘 작업을 `완료`로 보려면 아래를 만족해야 한다.

1. canary 결과를 `PASS/WARN/FAIL` 중 하나로 닫는다.
2. backend retained finding 중 open `P0/P1/P2`가 없다.
3. frontend/desktop retained finding 중 open `P0/P1/P2`가 없다.
4. UI/desktop 연결면 재감리 문서가 최신 코드 기준으로 다시 닫힌다.
5. build chain이 `backend + engine + Electron` 기준으로 재현 가능하다.
6. 최소 1회 build smoke 또는 packaged smoke 근거가 남는다.

## 5. 비대상 범위

오늘 범위에서 일부러 제외하는 것:

- 대규모 UI 리디자인
- 신규 기능 추가
- 미관 polish
- low-value 리팩터링
- 카나리아 결과와 무관한 실험적 구조 변경

## 6. Gate A. 카나리아 판정 (원인 특정 완료 → fix 선행)

카나리 1차 결과가 나왔고 원인이 특정됐다. 원인을 아는 상태에서 카나리를 먼저 닫으려고 기다리는 건 ROI가 낮다.

### 판정 결과

- `test_05`: WARN (pass_rate_monitor 미동작)
- `test_06`: FAIL (생산 미시작)
- `test_07`: FAIL (candidate_key/artifact_path sink 불일치 — 전략명 한글/영문 혼재)

### 특정된 원인

1. **candidate_key 네이밍 불일치**: `stage_attempts`/`pass_rate_monitor`는 영문명(`balanced`), `episode_production`은 한글명(`균형 전략`) 사용
2. **artifact_path suffix 불일치**: 기록 지점마다 전략 suffix 규칙 상이
3. **pass_rate_monitor 미동작**: test_05에서 4건 전부 기록 누락

### 변경된 운영 방침

원인이 특정됐으므로 카나리 재실행을 기다리지 않고 **fix 전량 선행** 후 카나리 1회로 검증한다.

```
[기존] 카나리 판정 대기 → backend fix → 카나리 재실행 → frontend fix → build
[변경] backend fix + frontend fix 전량 반영 → 카나리 1회 검증 → build
```

### 분기 규칙 (fix 후 카나리 재실행 시)

#### A-1. 재실행 canary `PASS`

- backend + frontend blocker 전량 닫힌 것으로 간주
- 즉시 build로 이동

#### A-2. 재실행 canary `WARN`

- warn 성격을 분리
- 신규 warn이면 원인 특정 후 추가 fix
- 기존 warn 잔류면 Observation으로 재분류 가능 여부 판정

#### A-3. 재실행 canary `FAIL`

- 1차에서 특정된 원인이 재발했는지 먼저 확인
- 재발이면 fix 누락 — 해당 지점 재패치
- 신규 원인이면 원인 분류 후 추가 burn-down

## 7. Phase 1. Backend Burn-Down

### 목적

- canary가 드러낸 backend root cause와 기존 backend retained finding을 오늘 안에 닫는다.

### 직접 범위

- Stage 4 계약
- PASS_WITH_FIX semantics
- sink alignment
- artifact lineage
- telemetry/DB parity
- runtime defect

### 비직접 범위

- frontend 디자인
- Electron 렌더러 구조 개편

### 완료 조건

- backend open `P0/P1/P2 = 0`
- targeted regression green
- canary failure root cause가 backend에서 더 이상 열려 있지 않음

## 8. Phase 2. Frontend/Desktop P1 제거

### 목적

- 프론트엔드 감사에서 남은 가장 강한 desktop contract 문제를 먼저 닫는다.

### 우선순위

1. packaged project root split 제거
2. release build chain에서 `dist/engine` 계약 고정

### 직접 범위

- `geuldobi-desktop/src/main.js`
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `build/backend_entry.py`
- `build/build_release.ps1`
- packaging 관련 문서

### 완료 조건

- packaged mode에서 project list/create/run/quality/safe-ops/review가 같은 프로젝트 루트를 본다
- build chain이 `backend`, `engine`, `Electron` 자원 계약을 모두 충족한다

## 9. Phase 3. Frontend/Desktop P2 제거

### 목적

- 이후 drift를 낳을 수 있는 숨은 결합과 assurance gap을 제거한다.

### 직접 범위

1. `main_a.py` CLI ordinal 결합 축소 또는 SSOT 잠금
2. Electron/IPC/bridge 회귀망 보강

### 완료 조건

- `genre_index`, `project_index`, key/sub_key contract가 명시적이고 테스트 가능하다
- `/run` 실제 서버, process runner, desktop contract 중 최소 핵심 경로에 회귀 보호막이 생긴다

## 10. Phase 4. UI 재감리 3-Pass

### 목적

- 수정 후 desktop/UI 연결면을 다시 전수조사해서 open finding을 재분류한다.

### Pass 1

- Electron main/preload/index/bridge/build 인벤토리 재수집

### Pass 2

- 코드, 테스트, build script, 문서, 실제 산출물 경로 교차 검증

### Pass 3

- 오탐 제거
- retained finding만 남기기
- confidence ledger 갱신

### 완료 조건

- UI/desktop 재감리 문서 1건
- 확신도 `95%` 또는 실행 가능한 상한
- open `P0/P1/P2 = 0`

## 11. Phase 5. Build

### 목적

- 코드와 문서가 아니라 실제 배포 경로까지 닫는다.

### 권장 순서

1. backend 산출물 생성
2. engine 산출물 생성
3. Electron `--dir` build
4. packaged smoke
5. installer build

### 금지

- installer build를 첫 단계로 바로 가지 않음

### 완료 조건

- `backend.exe`, `engine` 산출물, Electron package 자원이 모두 정렬됨
- 최소 `dir build` 성공
- 가능하면 installer build까지 완료

## 12. 시간 순서 운영안

### Track 0. fix 전량 반영 (backend + frontend)

- 카나리 원인 특정 완료 → fix 선행
- backend sink alignment + frontend P1/P2 전량 수정

### Track 1. 카나리 재실행 (1회)

- fix 전량 반영 후 카나리 1회 실행
- PASS면 즉시 Track 3으로, FAIL이면 원인 재특정 후 추가 fix

### Track 2. P2 + 회귀망

- Track 0에 포함. 별도 대기 없음

### Track 3. UI 재감리

- 수정이 끝난 뒤 바로 실행

### Track 4. build

- 재감리에서 blocker 없을 때만 진행

## 13. 리스크 관리

### 리스크 1. canary가 새 backend root cause를 열어버림

대응:

- frontend 착수보다 backend root cause를 먼저 닫는다

### 리스크 2. desktop P1 해결이 build chain까지 번짐

대응:

- `project root split`과 `engine artifact chain`을 하나의 work package로 묶는다

### 리스크 3. UI 재감리가 다시 새 finding을 열어 일정이 늘어남

대응:

- 오늘은 `P0/P1/P2`만 닫고, Observation은 내일로 넘길 수 있다

### 리스크 4. 빌드가 성공해도 packaged smoke에서 runtime mismatch가 뜸

대응:

- `build success`와 `packaged healthy`를 분리 기록한다

## 14. 의사결정 규칙

오늘은 아래 규칙으로만 판단한다.

1. canary blocker는 항상 최우선
2. backend root cause가 열려 있으면 frontend polish 금지
3. frontend 작업은 `renderer 미관`보다 `desktop contract` 우선
4. build는 `P0/P1/P2 제거` 이후
5. 시간 부족 시 `installer`보다 `dir build + packaged smoke`를 우선한다

## 15. 오늘 남길 산출물

최소 산출물:

1. backend fix 또는 burn-down 문서
2. frontend/desktop fix 문서 또는 execution note
3. UI 재감리 최종 문서
4. build 결과 문서
5. 필요 시 canary postmortem

## 16. 카나리아 성공 기준 후속 참고문서 3-Pass 선별 결과

이 섹션은 `카나리아 PASS`를 전제로 추가로 남길 참고문서 후보를 3-pass로 다시 거른 결과다.

판정 기준:

- 기존 `audit / execution plan / runbook`에 흡수 가능한가
- 오늘의 수정, 재감리, build, handoff에 직접 쓰이는가
- 별도 문서로 분리해야 다음 단계에서 재현성과 의사결정이 빨라지는가

### Pass 1. 필요성 재판정

- `stage4-canary-pass-final-report.md`: 필요.
  - 현재 `stage4-canary-log-audit.md`는 실패 원인과 hard gate 기준 문서다. 실제 `PASS`가 나오면 성공 세션, 하드게이트 결과, 잔여 warn을 별도 성공 보고서로 닫아야 한다.
- `backend-code-health-zero-ledger.md`: 필요.
  - backend `P0/P1/P2 = 0`을 한 장으로 닫아야 frontend/desktop 작업과 build 진행이 독립적으로 판정된다.
- `desktop-contract-remediation-execution-plan.md`: 조건부 필요.
  - desktop P1/P2 수정이 `Electron main + bridge + process runner + build chain`으로 퍼지면 별도 실행 SSOT가 필요하다.
  - 수정이 소규모면 별도 문서로 빼지 않고 당일 execution note에 흡수한다.
- `packaged-desktop-smoke-checklist.md`: 필요.
  - 오늘 로드맵은 `build success`와 `packaged healthy`를 분리 기록하도록 요구한다. 따라서 packaged smoke 체크리스트는 별도 문서로 남기는 편이 맞다.
- `build-reproducibility-runbook.md`: 필요.
  - `backend -> engine -> Electron --dir -> packaged smoke -> installer` 순서를 고정하는 재현 runbook이 있어야 build 결과가 1회성에 그치지 않는다.
- `ui-desktop-rerudit-3pass-final.md`: 조건부 필요.
  - frontend/desktop 코드를 실제로 수정한 경우에만 최종 재감리 문서가 필요하다.
  - 코드 수정이 없으면 기존 `frontend-desktop-bridge-full-survey-3pass-final-audit.md`를 최신 기준 감사 문서로 유지한다.

### Pass 2. 형태 보정

- `stage4-canary-pass-final-report.md`는 성공 판정서 형태로 고정한다.
  - 최소 포함 항목: 세션 ID, source/target project, hard gate 결과, draft/artifact/DB 요약, 잔여 warn, go/no-go 결론
- `backend-code-health-zero-ledger.md`는 issue ledger 형태로 고정한다.
  - 최소 포함 항목: issue ID, 기존 severity, closure evidence, 관련 테스트/로그/문서, residual risk
- `desktop-contract-remediation-execution-plan.md`는 work package 문서로 제한한다.
  - 수정 대상이 1개 work package 수준이면 별도 문서를 만들지 않고 본 로드맵의 실행 노트로 흡수한다.
- `packaged-desktop-smoke-checklist.md`는 체크리스트 형태로 고정한다.
  - 최소 포함 항목: 앱 기동, splash 전환, project list/create, run/stop, quality dashboard, safe ops, review, packaged path 확인
- `build-reproducibility-runbook.md`는 명령/산출물/실패 분기 문서로 고정한다.
  - 최소 포함 항목: prerequisites, build 순서, 기대 산출물, 실패 시 1차 확인 지점
- `ui-desktop-rerudit-3pass-final.md`는 수정 이후에만 만든다.
  - 최소 포함 항목: Pass 1 inventory, Pass 2 cross-check, Pass 3 false-positive 제거, 최종 confidence

### Pass 3. 최종 삽입 결정

`카나리아 PASS` 이후 별도 생성 권장:

1. `docs/2026-03-12/stage4-canary-pass-final-report.md`
2. `docs/2026-03-12/backend-code-health-zero-ledger.md`
3. `docs/2026-03-12/packaged-desktop-smoke-checklist.md`
4. `docs/2026-03-12/build-reproducibility-runbook.md`

조건부 생성:

1. `docs/2026-03-12/desktop-contract-remediation-execution-plan.md`
   - 조건: desktop 수정이 다중 파일, 다중 레이어 work package로 커질 때
2. `docs/2026-03-12/ui-desktop-rerudit-3pass-final.md`
   - 조건: frontend/desktop 코드 수정이 실제로 반영됐을 때

조건부 참고 문서 유지:

1. `docs/2026-03-12/TF-VERTEX-migration-full-audit.md`
   - 이유: provider/migration 조사 문서로서는 유효하지만, 오늘 로드맵의 핵심축인 `canary -> backend burn-down -> desktop contract -> build`를 직접 지휘하는 문서는 아니다.
   - 사용 시점: `models.yaml`, `metrics_collector.py`, `base_agent.py`, direct `genai.Client(...)` 경로를 다시 손댈 때
   - 현재 판정: 참고문서로 유지, 실행 SSOT로 승격하지 않음

별도 문서로 분리하지 않음:

1. `release-go-no-go-checklist.md`
   - 이유: 오늘 범위에서는 `installer`가 선택 과업이다. 필요하면 `build-reproducibility-runbook.md` 말미 gate 섹션으로 흡수한다.
2. `ui-bridge-regression-matrix.md`
   - 이유: 오늘은 회귀망 확장보다 `P0/P1/P2` 소거가 우선이다. 필요하면 `ui-desktop-rerudit-3pass-final.md` 부록으로 넣는다.
3. `deferred-observations-register.md`
   - 이유: Observation만 남는 경우에 한해 `ui-desktop-rerudit-3pass-final.md` 또는 `backend-code-health-zero-ledger.md`의 마지막 섹션으로 흡수하면 충분하다.

결론:

- 후속 참고문서는 `많을수록 좋은 것`이 아니다.
- 오늘 기준으로는 `성공 판정`, `backend zero`, `packaged smoke`, `build 재현성` 네 축은 분리 문서가 필요하다.
- desktop execution plan과 UI 재감리 최종본은 실제 수정 범위가 커질 때만 분리한다.
- 나머지 후보는 별도 파일로 늘리지 않고 기존 문서의 섹션으로 흡수한다.

## 17. 최종 한 줄 기준

오늘의 정답은 아래 순서다.

`backend + frontend fix 전량 반영 -> 카나리 1회 검증 -> UI 3-pass 재감리 -> build`

원인이 특정된 상태에서 카나리를 중간에 끼우는 건 시간 낭비다. fix 전량 선행 후 카나리 1회로 닫는다.
