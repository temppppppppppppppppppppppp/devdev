# today roadmap 참고 문서 전량 재감리 3-Pass 감사

작성일: 2026-03-12  
인코딩: UTF-8  
범위: `today-code-health-ui-build-roadmap.md`가 참조하는 문서 전량  
대상 문서 수: 9건  
최종 확신도: `95%`

## Executive Summary

이번 재감리는 로드맵 참고 문서를 다시 묶어 `현재 코드 기준으로 아직 유효한 문제`, `이미 구현되어 정적 기준으로 닫힌 문제`, `처음부터 실행 게이트가 아니었던 문서 주장`을 분리하는 작업이다.

결론은 아래와 같다.

1. `stage4-canary-execution-runbook.md`, `system-wide-full-remediation-execution-plan.md`, `system-wide-full-remediation-3pass-audit.md`는 실행 기준을 주는 문서이지, 현재 시점의 신규 retained finding 원천은 아니다.
2. `stage4-canary-log-audit.md`의 핵심 이슈 중 `candidate_key/artifact_path sink drift`는 코드 수정으로 정적 기준상 구현 반영이 됐다. 다만 `limited canary rerun`이 아직 없으므로 최종 closure는 `runtime gate`로 남는다.
3. `frontend-desktop-bridge-full-survey-3pass-final-audit.md`의 정적 P1 두 건인 `project root split`, `dist/engine build chain`은 현재 코드 기준으로 직접 모순이 해소됐다. 대신 `packaged build smoke 미실행`만 `runtime-only verification gate`로 남는다.
4. `roadmap-external-full-survey-3pass-audit.md`와 `TF-VERTEX-migration-full-audit.md`가 공통으로 지적한 `BUG-PRICE-1`은 아직 열려 있다.
5. `roadmap-external-full-survey-3pass-audit.md`의 `신규 모듈 3개 테스트 부재`는 오탐 축소가 필요했다. 현재 기준으로 `soft_failure`는 직접 테스트가 이미 존재하므로, 실제 direct gap은 `artifact_logging`, `logging_keys` 두 축으로 줄어든다.
6. `TF-S3-context-contract-audit.md`의 관측성 P1 2건과 `stage4-context-contract-full-survey-3pass-audit.md`의 Stage 4 context P2 2건은 현재 코드에서도 유효하다.

최종 retained set은 `P1 5건`, `P2 3건`, `runtime-only gate 2건`, `Observation 3건`으로 정리했다.

## 1. 조사 범위

### 1.1 참고 문서 인벤토리

| 구분 | 문서 | 이번 재감리에서의 역할 |
|---|---|---|
| primary | `stage4-canary-execution-runbook.md` | canary hard gate와 재실행 절차 기준 |
| primary | `system-wide-full-remediation-execution-plan.md` | 과거 work package 배정 기준 |
| primary | `system-wide-full-remediation-3pass-audit.md` | 과거 execution plan 자체의 감리 기준 |
| primary | `stage4-canary-log-audit.md` | canary fail 근거와 Stage 4 retained issue 근거 |
| primary | `frontend-desktop-bridge-full-survey-3pass-final-audit.md` | desktop/bridge/build 연결면 retained issue 근거 |
| support | `roadmap-external-full-survey-3pass-audit.md` | metrics/logging/test/hygiene 외부 전수조사 근거 |
| support | `TF-VERTEX-migration-full-audit.md` | provider/cost 정합성 보조 근거 |
| support | `stage4-context-contract-full-survey-3pass-audit.md` | Stage 4 context contract 보조 근거 |
| support | `TF-S3-context-contract-audit.md` | Stage 3 observability/context 보조 근거 |

### 1.2 이번 재감리의 원칙

- 참고 문서에 적혀 있다는 이유만으로 finding으로 유지하지 않는다.
- 이미 코드에 반영된 항목은 `implemented-static`으로 내린다.
- 정적으로는 닫혔지만 실제 rerun/build 없이는 못 닫는 항목은 `runtime-only gate`로 남긴다.
- 확신이 낮아서 기각하지 않는다. 직접 반증된 항목만 `rejected`로 내린다.

## 2. Pass 1. 문서별 retained inventory

### 2.1 primary 문서

- `stage4-canary-execution-runbook.md`
  - 절차 문서다.
  - retained finding 원천이 아니라 `prepare -> run -> analyze` hard gate 기준 문서로 유지한다.

- `system-wide-full-remediation-execution-plan.md`
  - historical execution mapping 문서다.
  - 현재 worktree에서는 이미 일부 WP가 구현 반영된 상태라, 문서 자체를 다시 open finding 원천으로 쓰면 중복이 생긴다.

- `system-wide-full-remediation-3pass-audit.md`
  - 위 execution plan의 적합성 감사 문서다.
  - 현재 남은 의미는 `과거 계획이 누락 없이 짜였는지`에 대한 근거뿐이다.

- `stage4-canary-log-audit.md`
  - canary FAIL 원장이다.
  - 이 문서의 retained issue는 현재 코드 기준으로 `구현 반영됨/미반영/런타임 검증 필요`로 다시 나눠야 한다.

- `frontend-desktop-bridge-full-survey-3pass-final-audit.md`
  - 정적 desktop contract 감사 문서다.
  - 현재 코드 변경으로 직접 모순이 사라진 항목이 있어 재분류가 필요하다.

### 2.2 support 문서

- `roadmap-external-full-survey-3pass-audit.md`
  - broad survey 문서다.
  - `BUG-PRICE-1`, `artifact_logging`, test gap, hygiene 관찰치를 제공한다.

- `TF-VERTEX-migration-full-audit.md`
  - 오늘 범위 전체를 지휘하는 문서는 아니지만, `BUG-PRICE-1`의 독립 근거를 제공한다.

- `stage4-context-contract-full-survey-3pass-audit.md`
  - Stage 4 patch feedback/context 문제 2건을 유지한다.

- `TF-S3-context-contract-audit.md`
  - Stage 3 observability gap 2건을 유지한다.

## 3. Pass 2. 교차 검증

### 3.1 retained root findings

| ID | 심각도 | root finding | 출처 문서 | 재감리 판정 |
|---|---|---|---|---|
| R-01 | P1 | `BUG-PRICE-1`: `gemini-2.5-pro` `cache_read` 단가 과대 | `roadmap-external`, `TF-VERTEX` | confirmed |
| R-02 | P1 | `artifact_logging.snapshot_logged_artifact()`의 파일 쓰기 예외가 Stage 흐름을 직접 깨뜨릴 수 있음 | `roadmap-external` | confirmed |
| R-03 | P1 | Stage 3 `_bp_semantic_ctx` 관측성 미저장 | `TF-S3` | confirmed |
| R-04 | P1 | Stage 3 `save_stage_attempt()`가 observability 필드를 충분히 전달하지 않음 | `TF-S3` | confirmed |
| R-05 | P1 | `limited Stage 4 canary rerun` 미실행으로 canary umbrella gate가 아직 닫히지 않음 | `stage4-canary-log-audit`, `runbook`, `system-wide remediation docs` | runtime-only gate |
| R-06 | P2 | Stage 4 local patch 루프가 Director feedback를 좁게 전달함 | `stage4-context` | confirmed |
| R-07 | P2 | Stage 4 re-audit story_context에 누적 patch provenance가 충분히 주입되지 않음 | `stage4-context` | confirmed |
| R-08 | P2 | direct unit-test gap은 `artifact_logging`, `logging_keys` 두 축으로 축소됨 | `roadmap-external` | confirmed-narrowed |
| R-09 | Gate | packaged build smoke 미실행으로 desktop/build closure가 아직 runtime 증명되지 않음 | `frontend-desktop-bridge`, `runbook` | runtime-only gate |

### 3.2 정적으로 닫힌 항목

아래 항목은 현재 코드 기준으로 직접 모순이 해소돼 `implemented-static`으로 닫는다.

- `frontend-desktop-bridge`의 `packaged project root split`
  - `bridge_server`가 `GEULDOBI_PROJECTS_ROOT`/`GEULDOBI_WORKSPACE`를 우선 보도록 반영됐다.

- `frontend-desktop-bridge`의 `dist/engine build chain 부재`
  - release script가 `dist/engine`을 staging하고 Electron package가 `python-embed`까지 번들하도록 반영됐다.

- `stage4-canary-log-audit`의 `candidate_key/artifact_path sink drift`
  - 정적 코드와 회귀 테스트 기준으로 반영됐다.
  - 단, 최종 closure는 `R-05 limited canary rerun` 뒤에만 가능하다.

### 3.3 오탐/하향

- `roadmap-external`의 `신규 모듈 3개 테스트 부재`
  - `soft_failure`는 더 이상 gap이 아니다.
  - 현 시점 direct gap은 `artifact_logging`, `logging_keys` 두 축뿐이다.

- `roadmap-external`의 `WorkGuard 인터랙티브 생성 마법사 미구현`
  - 여전히 Observation이다.
  - 실행 게이트나 건강도 blocker로 올리기 어렵다.

- `system-wide remediation execution/audit`
  - 문서 자체는 historical planning evidence다.
  - 현재 open finding 원천으로 중복 승격하지 않는다.

- `TF-VERTEX`의 `리전 가용성 확인 필요`
  - 오늘 로드맵 범위에서는 migration precheck다.
  - active canary/desktop/build gate와 직접 결합하지 않으므로 conditional observation으로 둔다.

## 4. Pass 3. 오탐 제거와 실행 relevance 재분류

### 4.1 오탐 제거 결과

- 제거:
  - `frontend-desktop-bridge`의 정적 P1 2건을 그대로 open으로 유지하는 판단
  - `roadmap-external`의 `soft_failure direct test gap`
  - `system-wide remediation docs`를 live open-finding 원천으로 재사용하는 판단

- 유지:
  - `BUG-PRICE-1`
  - `artifact_logging` write failure
  - Stage 3 observability gap 2건
  - Stage 4 context gap 2건
  - canary rerun gate
  - packaged build smoke gate

### 4.2 최종 retained set

| 심각도 | 항목 수 | 비고 |
|---|---:|---|
| P0 | 0 | 없음 |
| P1 | 5 | code 또는 runtime acceptance 문제 |
| P2 | 3 | observability/context/test gap |
| runtime-only gate | 2 | canary rerun, packaged build smoke |
| Observation | 3 | WorkGuard wizard, stage2 deprecated parameter, Vertex region precheck |

## 5. 확신도 ledger

- `70`: 참고 문서 9건 인벤토리 완료
- `+10`: primary/support 문서 역할 분리 완료
- `+10`: cross-doc root finding 병합 완료
- `+5`: current code 기준으로 static-closed 항목과 runtime-only gate 항목 분리 완료
- `+5`: 오탐 및 scope-overlap 제거 완료
- `-5`: active canary rerun과 packaged build smoke는 아직 미실행

최종 확신도: `95%`

## Final Verdict

이번 재감리의 결론은 단순하다.

- 참고 문서 전량은 다시 읽혔고, 현재 시점의 실질 open set으로 압축됐다.
- `frontend-desktop-bridge`와 `stage4-canary-log-audit`의 일부 static finding은 이미 구현 반영으로 닫혔다.
- 반대로 `BUG-PRICE-1`, `artifact_logging`, `TF-S3 observability`, `Stage 4 context`는 아직 실행 SSOT에 올라가야 할 실질 잔여물이다.
- 따라서 다음 단계는 `참고 문서 재감리 결과만 담은 별도 실행 SSOT`를 만드는 것이다.
