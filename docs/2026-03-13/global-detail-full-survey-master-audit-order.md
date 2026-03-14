# 전역 전량 디테일 전수조사 마스터 오더

> 작성일: 2026-03-13
> Prefix: `GDFS`
> 상태: `execution-ready`
> 역할: 기존 거시 감사와 개별 detail audit 결과를 baseline으로 삼고, 현재 live workspace 전체를 **세부 디테일 단위**로 다시 잠그는 최상위 조사 오더
> 방식: `baseline harvest -> active surface inventory -> 6-track parallel sweep -> cross-track dedupe -> consolidated 3PASS re-audit`
> 금지: 코드 수정, closed finding 무근거 재오픈, UTF-8 이외 인코딩 경유

---

## 0. 문서 역할

- 이 문서는 `조사 오더`다. 코드 수정 오더가 아니다.
- 이번 조사 목표는 새 총건수 만들기가 아니라, **live consumer가 실제로 밟는 디테일 표면**을 전역 단위로 잠그는 것이다.
- `전역 전량`의 의미는 `현재 살아 있는 코드/설정/문서/테스트/아티팩트 표면 전량`이다.
- `docs/이전`, 백업 zip, 과거 스크랩, 폐기된 temp는 기본적으로 조사 대상이 아니다.
- 단, live code가 읽거나 operator가 실제로 쓰는 경우에는 archived/tombstoned 자산도 조건부 조사 대상이 된다.
- 모든 문서는 `UTF-8 only`다. 물음표 삼연속 치환 흔적이나 replacement character 흔적, 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.

---

## 1. 왜 지금 이 문서가 필요한가

- 거시 건강성, 스테이지별 감사, cross-cut 트랙 감사는 이미 많이 수행됐다.
- 지금 남는 문제는 대개 `메서드 내부 fallback`, `필드명 drift`, `artifact sink mismatch`, `operator-facing label 오판`, `temp/residue 누출`, `문서-코드 미세 불일치` 같은 디테일 층이다.
- 오늘자 detail 문서들은 강하지만 subsystem별로 흩어져 있다.
- 따라서 이번 문서는:
  - 이미 조사된 detail track은 baseline으로 흡수하고
  - 아직 열리지 않았거나, 서로 사이에 낀 경계(surface gap)만 다시 열고
  - 전역 기준에서 `중복 없는 retained open set`을 재구성하는 역할을 맡는다.

---

## 2. 선행 baseline 문서

아래 문서를 먼저 읽고 시작한다.

1. `docs/2026-03-13/OPUS-TF-5terminal-detail-master-audit-order.md`
2. `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md`
3. `docs/2026-03-13/stage0-full-survey-3pass-audit-order.md`
4. `docs/2026-03-13/S3D-full-survey-audit-order.md`
5. `docs/2026-03-13/runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
6. `docs/2026-03-13/XC-6track-merged-remediation-execution-ssot.md`
7. `docs/2026-03-13/today-detail-sideeffect-connectivity-liverun-checklist.md`
8. `docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md`

해석 규칙:

- 위 문서 중 `3pass final / re-audit`가 이미 있는 경우, 기본값은 `baseline truth`다.
- baseline을 재오픈할 수 있는 조건은 아래 4개뿐이다.
  - `live-code-changed`: 현재 코드가 baseline 시점 이후 바뀌었다.
  - `artifact-contradiction`: 현재 runtime/log/artifact가 baseline 판단과 충돌한다.
  - `new-consumer-scope`: 당시 조사 범위 밖이던 live consumer가 새로 드러났다.
  - `operator-surface-mismatch`: 내부는 닫혔지만 operator-facing 표면이 여전히 거짓 신호를 만든다.
- 위 4개 중 하나를 명시하지 못하면 재오픈 금지다.

---

## 3. 전역 조사 범위 계약

### 3.1 기본 포함 범위

- `main_a.py`, `modules/`, `tests/`
- `scripts/`, `lite_mode/`, `tools/`, `tools2/`, `main_tools/`
- `config/`, `work_guards/`, `전처리_ssot/contracts/`, `전처리_ssot/docs/`
- `docs/implementation/`, `docs/2026-03-13/`의 당일 운용 문서
- `geuldobi-desktop/`, 루트 `main.js`
- `treatments/`, `bible/`, `projects/`, `logs/`

### 3.2 조건부 포함 범위

- 루트 `temp-*` 파일
- `MagicMock/`
- `build/`, `dist/` 산출물
- `projects/test/` 같은 테스트 산출물

조건:

- live code가 읽는다
- operator가 오늘 실제 검증에 사용한다
- current issue의 증거로 참조된다

### 3.3 기본 제외 범위

- `docs/이전/`
- 백업 zip, 백업 txt, 스냅샷 사본
- 외부 데이터셋 전체
- 현재 import/실행 경로와 무관한 폐기 실험물

### 3.4 디테일 단위 정의

이번 조사에서 허용되는 최소 단위는 아래 중 하나다.

- 메서드/분기
- 스키마 필드/키
- DB 컬럼/아티팩트 row
- API 엔드포인트/IPC 메시지
- 테스트 assert/fixture/xfail
- 문서 계약 항목 1개
- CLI 인자/스크립트 실행 경로

매크로 주장 금지:

- `Stage 3가 불안하다`, `UI가 좀 어긋난다`처럼 정확한 locus가 없는 문장은 finding으로 채택하지 않는다.
- 반드시 `파일/라인/필드/엔드포인트/아티팩트 키` 중 하나를 찍어야 한다.

---

## 4. 공통 조사 규약

### 4.1 공통 모드

- `read-only`
- `evidence-first`
- `UTF-8 only`
- `code + test + doc + artifact cross-check`
- `baseline-aware`

### 4.2 공통 태그

후보 finding에는 아래 태그 중 1개 이상을 붙인다.

- `wiring`
- `contract`
- `artifact`
- `utf8`
- `operator-surface`
- `fallback`
- `side-effect`
- `residue`
- `test-illusion`
- `stale-ssot`

### 4.3 3PASS 프로토콜

#### PASS 1 - 후보 수집

- active surface inventory를 만든다.
- 각 파일/표면을 읽고 디테일 후보를 기록한다.
- 후보마다 `HIGH/MED/LOW` 확신도를 붙인다.
- 기존 문서에서 이미 닫힌 항목도 일단 잡을 수 있지만, 이 단계에서는 `candidate`일 뿐이다.

#### PASS 2 - 교차 검증

- 코드 근거 재확인
- 관련 테스트/문서/아티팩트 대조
- baseline 중복 여부 확인
- `의도적 설계`, `이미 닫힘`, `live path 아님`, `증거 부족`을 오탐으로 제거

#### PASS 3 - 최종 확정

- retained finding만 `P0~P3` severity를 부여한다.
- 각 finding은 아래 8개 필드를 가진다.
  1. ID
  2. Severity
  3. 현상 요약
  4. 정확한 코드/문서/아티팩트 근거
  5. downstream 영향 경계
  6. 현재 테스트 또는 부재 근거
  7. baseline과의 관계
  8. 권장 후속 조치

### 4.4 Severity 기준

- `P0`: 데이터 손실, 거짓 완료, operator 오판을 즉시 일으키는 치명 경로
- `P1`: live path에서 의미 있는 contract/evidence drift가 남아 있는 경우
- `P2`: 품질 저하, 유지보수 위험, false green을 만드는 디테일 결함
- `P3`: 정보성 debt, label drift, readability 문제

### 4.5 오탐 제거 코드

- `FP-1`: 문서화된 의도적 설계
- `FP-2`: 현재 테스트/검증으로 이미 잠김
- `FP-3`: live consumer 부재
- `FP-4`: 다른 트랙과 교차 검증 후 정상
- `FP-5`: 스타일 차이, 표현 차이, non-functional variance

---

## 5. 6개 글로벌 트랙

## T1. Live Code Hidden Branch Detail

- 범위:
  - `main_a.py`
  - `modules/core/`
  - `modules/domain/`
  - `modules/validation/`
- 초점:
  - silent fallback
  - `except/pass` 또는 약한 fail-open
  - stage handoff field loss
  - default branch drift
  - context write-back 누락
- 우선 읽을 baseline:
  - `OPUS-TF-5terminal-detail-master-audit-order.md`
  - `OPUS-TF-5terminal-deep-dive-master-audit-order.md`
  - `stage0-full-survey-3pass-audit-order.md`
  - `S3D-full-survey-audit-order.md`
- 산출물:
  - `docs/2026-03-13/GDFS-T1-live-code-hidden-branch-findings.md`

## T2. Persistence / Artifact / Evidence Layer Detail

- 범위:
  - `logs/`
  - `projects/*/project_data.db`
  - `treatments/`, `bible/`
  - runtime summary/jsonl/attempt tables
  - stage output sidecars
- 초점:
  - sink mismatch
  - stale artifact
  - partial rollback/partial commit
  - artifact provenance drift
  - UTF-8 오염
  - operator-facing evidence contradiction
- 우선 읽을 baseline:
  - `runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
  - `XC-6track-merged-remediation-execution-ssot.md`
- 산출물:
  - `docs/2026-03-13/GDFS-T2-persistence-artifact-evidence-findings.md`

## T3. Config / Contract / Prompt / SSOT Drift

- 범위:
  - `config/`
  - `work_guards/`
  - `전처리_ssot/contracts/`
  - `전처리_ssot/docs/`
  - `docs/implementation/`
  - live 운영 문서
- 초점:
  - dead key / dead field
  - schema drift
  - prompt key mismatch
  - document rot
  - SSOT vs code divergence
  - stale threshold / stale port / stale field naming
- 우선 읽을 baseline:
  - `ui-frontend-backend-connectivity-remediation-execution-ssot.md`
  - `today-detail-sideeffect-connectivity-liverun-checklist.md`
  - blockguide / 전처리 SSOT 문서군
- 산출물:
  - `docs/2026-03-13/GDFS-T3-config-contract-ssot-drift-findings.md`

## T4. UI / API / Desktop / Operator Surface

- 범위:
  - `modules/api/`
  - `geuldobi-desktop/`
  - 루트 `main.js`
  - operator-facing dashboard/review/safe-ops surface
- 초점:
  - API/IPC/WS message drift
  - frontend/backend contract mismatch
  - port/endpoint/response shape drift
  - Electron security posture
  - operator label/summary false green
- 우선 읽을 baseline:
  - `ui-frontend-backend-connectivity-remediation-execution-ssot.md`
  - `runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
- 산출물:
  - `docs/2026-03-13/GDFS-T4-ui-api-desktop-operator-surface-findings.md`

## T5. Test / Canary / Runtime Proof

- 범위:
  - `tests/`
  - smoke/canary/rerun 스크립트
  - `projects/test/`
  - quality gate / runbook / checklist
- 초점:
  - mock-only green
  - xfail residue
  - runtime proof 부재
  - test-contract drift
  - limited canary hard gate 미잠금
  - code closed but runtime open
- 우선 읽을 baseline:
  - `today-detail-sideeffect-connectivity-liverun-checklist.md`
  - `docs/2026-03-12/stage4-canary-execution-runbook.md`
  - `docs/2026-03-12/stage4-live-rerun-checklist.md`
- 산출물:
  - `docs/2026-03-13/GDFS-T5-test-canary-runtime-proof-findings.md`

## T6. Tools / Lite Mode / Legacy Live Consumer / Residue

- 범위:
  - `lite_mode/`
  - `tools/`, `tools2/`, `main_tools/`
  - `scripts/`
  - 루트 `temp-*`
  - `MagicMock/`
- 초점:
  - hidden live consumer
  - legacy helper still wired
  - destructive script risk
  - temp file leak
  - residue misread as live defect
  - direct API/DB bypass path
- 우선 읽을 baseline:
  - `OPUS-TF-5terminal-deep-dive-master-audit-order.md`
  - `main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`
- 산출물:
  - `docs/2026-03-13/GDFS-T6-tools-lite-mode-live-consumer-residue-findings.md`

---

## 6. 전역 실행 순서

1. `baseline ledger freeze`
   - 기존 detail 문서에서 이미 닫힌 항목, 아직 열린 항목, 범위 밖 항목을 먼저 구분한다.
2. `active surface inventory`
   - 현재 실제 live consumer가 밟는 코드/문서/아티팩트 표면 목록을 잠근다.
3. `T1~T6 병렬 조사`
   - 각 트랙은 자체 3PASS를 수행한다.
4. `cross-track dedupe`
   - 같은 루트코즈를 여러 트랙이 잡으면 가장 증거가 풍부한 문서로 병합한다.
5. `global retained open set 정리`
   - reopen 사유 없는 항목 제거
   - subsystem 내부 issue와 전역 issue 분리
6. `통합본 3PASS 재감리`
   - 전역 기준으로 severity 재분류
   - execution-ready 여부를 판정한다.

---

## 7. compaction 대응 / 연속 진행 규칙

컨텍스트 compaction 이후에도 이 오더를 끊기지 않게 재개하려면 아래 순서를 강제한다.

### 7.1 재개 시 최우선 재오픈 문서

1. 본 문서 `global-detail-full-survey-master-audit-order.md`
2. 마지막으로 수정된 `GDFS-T*` 개별 트랙 문서
3. `global-detail-full-survey-consolidated-findings.md`가 있으면 그 문서
4. `global-detail-full-survey-consolidated-findings-3pass-reaudit.md`가 있으면 그 문서

### 7.2 재개 판단 기준

- 기억으로 현재 위치를 추정하지 않는다.
- 아래 4개 중 가장 최근에 실제 파일로 남아 있는 지점을 재개 포인터로 삼는다.
  1. 마지막 완료된 트랙 문서
  2. 마지막 완료된 PASS 로그
  3. 마지막 갱신된 retained open set
  4. 통합본의 마지막 반영 시점

### 7.3 Resume Packet 최소 슬롯

매 트랙 문서와 통합 문서는 말미에 가능하면 아래 6개 슬롯을 남긴다.

1. `Current phase`
2. `Last completed pass`
3. `Last completed surface`
4. `Next surface`
5. `Reopen reason codes used`
6. `Stop gate or blocker`

### 7.4 연속 진행 규칙

- 정지 게이트가 없으면 다음 미완료 트랙으로 바로 이동한다.
- 트랙 안에서는 `PASS 1 -> PASS 2 -> PASS 3`를 끊지 않는다.
- 중간에 compaction이 발생해도 동일 트랙의 같은 PASS부터 재시작하지 말고, 파일에 남은 마지막 PASS 상태부터 재개한다.
- baseline reopen은 compaction 이후에도 reason code 없이 허용되지 않는다.

---

## 8. 중복 처리 규칙

- Stage별 전용 detail 문서는 그 subsystem의 1차 truth다.
- `GDFS-*`는 그 문서를 복사 재포장하지 않는다.
- `GDFS-*`에 새로 올라오는 항목은 반드시 아래 중 하나여야 한다.
  - 기존 문서들이 놓친 `cross-surface` 문제
  - 현재 코드/아티팩트 기준으로 새로 생긴 문제
  - operator-facing false green/false pass 문제
  - 기존 finding의 정확한 루트코즈/영향 경계 재고정

병합 규칙:

- 같은 root cause면 `가장 구체적인 코드 근거 + 가장 넓은 영향 경계`를 가진 문서로 통합한다.
- 같은 현상이라도 `코드 문제`와 `operator-surface 문제`가 분리되면 별도 유지 가능하다.
- baseline과 충돌하는 reopen finding은 반드시 reopen reason code를 본문에 적는다.

---

## 9. 산출물

### 트랙 문서

1. `docs/2026-03-13/GDFS-T1-live-code-hidden-branch-findings.md`
2. `docs/2026-03-13/GDFS-T2-persistence-artifact-evidence-findings.md`
3. `docs/2026-03-13/GDFS-T3-config-contract-ssot-drift-findings.md`
4. `docs/2026-03-13/GDFS-T4-ui-api-desktop-operator-surface-findings.md`
5. `docs/2026-03-13/GDFS-T5-test-canary-runtime-proof-findings.md`
6. `docs/2026-03-13/GDFS-T6-tools-lite-mode-live-consumer-residue-findings.md`

### 통합 문서

7. `docs/2026-03-13/global-detail-full-survey-consolidated-findings.md`
8. `docs/2026-03-13/global-detail-full-survey-consolidated-findings-3pass-reaudit.md`
9. `docs/2026-03-13/global-detail-full-survey-master-audit-order.md` ← 본 문서
10. `docs/2026-03-13/global-detail-full-survey-remediation-execution-ssot.md`

---

## 10. 정지 게이트

아래 상황에서는 해당 트랙을 즉시 멈추고 원인을 기록한다.

- UTF-8 파싱 실패 또는 물음표 삼연속 치환 흔적 / replacement character 흔적 탐지
- destructive script를 실제 실행해야만 판단 가능한 경우
- 현재 worktree 변경과 조사 결론이 직접 충돌하는 경우
- live artifact가 사라져 증거가 성립하지 않는 경우
- baseline 문서와 현재 코드 사이에 어느 쪽이 진실인지 결정할 증거가 없는 경우

정지 시 기록해야 할 것:

1. 어디서 멈췄는가
2. 왜 멈췄는가
3. 추가로 필요한 증거는 무엇인가
4. 임시로 어떤 판단을 보류했는가

---

## 11. 종료 조건

아래를 모두 만족해야 본 오더가 닫힌다.

1. `GDFS-T1~T6` 문서가 모두 존재한다.
2. 각 문서가 `PASS1 -> PASS2 -> PASS3` 축약 로그를 가진다.
3. 모든 retained finding이 정확한 locus와 baseline 관계를 가진다.
4. 전역 통합본이 `code / contract / artifact / ui / test / tools` 6축 ledger를 재구성한다.
5. open `P0/P1`은 전부 owner surface와 후속 실행 경로를 가진다.
6. `전역 live surface 중 미분류 영역 없음` 상태가 문서상 명시된다.

---

## 12. 초기 상태

- 본 문서는 `execution-ready`다.
- 트랙 문서와 통합본은 초기 상태를 `template / not executed`로 본다.
- baseline harvest 전에는 어떤 finding도 확정으로 취급하지 않는다.
- 이번 오더는 기존 세부 조사 문서를 무효화하지 않는다.
- 이번 오더의 목적은 `오늘 기준 global retained detail surface`를 다시 잠그는 것이다.

---

## 13. 실행 상태 스냅샷

- `2026-03-13` 현재 상태:
  - `GDFS-T1~T6` 완료
  - `global-detail-full-survey-consolidated-findings.md` 완료
  - `global-detail-full-survey-consolidated-findings-3pass-reaudit.md` 완료
  - `global-detail-full-survey-remediation-execution-ssot.md` 완료
- 전역 retained open set:
  - `21건`
  - `P1 6 / P2 14 / P3 1 / P0 0`
- compaction 이후 재개 우선순위:
  1. 본 문서
  2. `global-detail-full-survey-remediation-execution-ssot.md`
  3. `global-detail-full-survey-consolidated-findings.md`
  4. `global-detail-full-survey-consolidated-findings-3pass-reaudit.md`
  5. 마지막으로 수정된 `GDFS-T*` 문서
- 다음 surface:
  - `global-detail-full-survey-remediation-execution-ssot.md`
  - 후속이 열리면 재조사가 아니라 위 SSOT 기준 implementation / verification 턴으로 분기한다.
