# OPUS TF 5-Terminal Deep-Dive Execution SSOT

- 작성일: 2026-03-13
- 상태: `execution-ready`
- 문서 역할: [OPUS-TF-5terminal-deep-dive-master-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md)를 실제 수행 순서, 산출물, 교차 검증 규칙으로 잠그는 단일 실행 SSOT
- 문서 성격: 본 문서는 심층 감사 결과 보고서가 아니다. 아직 `S-T1~S-T5` 결과 문서는 존재하지 않으며, 이 문서는 그 결과를 생산하기 위한 `audit-execution` 기준면이다.
- 금지사항: 코드 수정, 테스트 수정, 패키지 업데이트, live 공격 실행, 실제 DB 변형은 이 문서 범위 밖이다.

## 1. 기준 문서

- [OPUS-TF-5terminal-deep-dive-master-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md)
- [OPUS-TF-5terminal-consolidated-findings-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-consolidated-findings-3pass-reaudit.md)
- [OPUS-TF-5terminal-detail-consolidated-findings-5pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-detail-consolidated-findings-5pass-reaudit.md)
- [OPUS-TF-T1-infrastructure-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md)
- [OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md)
- [T3-stage3-4-pipeline-audit-report.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T3-stage3-4-pipeline-audit-report.md)
- [T4-quality-advisory-audit-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T4-quality-advisory-audit-findings.md)
- [OPUS-TF-T5-domain-auxiliary-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T5-domain-auxiliary-findings.md)
- [CLAUDE.md](C:/Users/User/Desktop/글도비/CLAUDE.md)

## 2. 목표

이번 오더의 목표는 새로운 수정 오더를 만드는 것이 아니라, 3차 심층 감사를 다음 네 가지 기준으로 실행 가능하게 고정하는 것이다.

1. 아직 조사되지 않은 35% 영역을 실제로 덮는다.
2. 1차/2차에서 이미 확정된 finding을 다시 세지 않는다.
3. 터미널별 결과를 최종 취합본까지 끊김 없이 연결한다.
4. 결과 문서가 최종적으로 95% 확신도 재감리를 통과할 수 있게 증거 형식을 선행 고정한다.

## 3. 산출물 잠금

이번 실행 SSOT에서 생성되어야 하는 파일은 아래로 고정한다.

### 터미널별 결과

- `docs/2026-03-13/S-T1-stage0-ui-flow-deep-dive-findings.md`
- `docs/2026-03-13/S-T2-cross-stage-root-cause-deep-dive-findings.md`
- `docs/2026-03-13/S-T3-lite-mode-tools-deep-dive-findings.md`
- `docs/2026-03-13/S-T4-api-desktop-deep-dive-findings.md`
- `docs/2026-03-13/S-T5-security-performance-scale-deep-dive-findings.md`

### 마스터 취합

- `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings.md`
- `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings-3pass-reaudit.md`

### 즉시 에스컬레이션

- `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-p0-escalation-ledger.md`

### 후속 실행 문서

- 본 문서: `OPUS-TF-5terminal-deep-dive-execution-ssot.md`
- 본 문서 감리: `OPUS-TF-5terminal-deep-dive-execution-3pass-audit.md`

## 4. 공통 실행 원칙

### 원칙 A. 신규 발견만 채택한다

- 1차 `[T*-*]`, 2차 `[D-T*-*]`와 동일 표면이면 중복 보고 금지.
- 같은 theme이라도 코드 경로, 수정 표면, 런타임 영향 지점이 다르면 신규 finding으로 유지할 수 있다.

### 원칙 B. 대원칙 위반은 루트코즈를 함께 닫는다

- `디렉터 주권주의` 위반 여부는 `CLAUDE.md` 기준으로 최종 판정한다.
- P0/P1 추적 건은 “현상 재진술”이 아니라 `파일:라인`, `상류->하류 경로`, `수정 영향 범위`가 함께 있어야 한다.

### 원칙 C. 정적 스캔과 교차 표를 같이 남긴다

- 이번 심층 감사는 단순 목록화가 아니다.
- T2, T4, T5는 각각 `핸드오프 대조표`, `엔드포인트/IPC 대조표`, `보안/성능 요약표`를 남겨야 한다.

### 원칙 D. P0는 즉시 에스컬레이션하고 취합본을 기다리지 않는다

- SQL 인젝션, XSS, 인증 우회, 데이터 영구 손상성 경로 등 P0는 개별 터미널 보고 즉시 별도 에스컬레이션한다.
- 즉시 에스컬레이션은 `OPUS-TF-5terminal-deep-dive-p0-escalation-ledger.md`에 먼저 기록하고, 이후 최종 취합본 Section A에도 재편입한다.
- 다만 마스터 취합본에도 동일 ID를 다시 편입해야 한다.

### 원칙 E. 결과 없는 가정은 문서화하지 않는다

- deep-dive 결과 문서가 아직 없으므로, 실행 SSOT 단계에서는 예상 건수나 severity 분포를 쓰지 않는다.
- 증거 없는 “미완” 또는 “부패” 단정도 금지한다.

## 5. 실행 순서

실행 순서는 아래로 고정한다.

1. **Baseline Freeze**
2. **Terminal 1, 3, 4, 5 1차 스캔 병행**
3. **Terminal 2 교차 스테이지 추적**
4. **터미널별 3PASS 종료**
5. **마스터 중복 제거 및 취합**
6. **최종 통합본 3PASS 재감리**

### Step 1. Baseline Freeze

수집 항목:

- `CLAUDE.md` 대원칙과 테스트 기준선
- 1차/2차 재감리 최종본
- 현재 워크스페이스 파일 수 기준이 필요한 항목

목적:

- T1~T5가 같은 baseline에서 신규 여부를 판정하도록 고정한다.

### Step 2. T1/T3/T4/T5 병행 스캔

배치 이유:

- T1(Stage 0), T3(Lite Mode/Tools), T4(API/Desktop), T5(보안/성능)는 코드 표면이 겹치지 않아 병행성이 높다.
- T2는 이들 결과를 일부 입력으로 다시 참조해야 하므로 후행 배치한다.

필수 산출:

- 각 터미널의 PASS1 후보 ledger
- 중복 가능성 표시
- 교차 요청이 필요한 경계 파일 목록

### Step 3. T2 교차 추적

선행 조건:

- T1의 Stage 0 루트코즈 메모
- T4의 API/Desktop 프로토콜 메모
- T5의 guard/timeout/security 메모

필수 산출:

- 미해결 7건의 루트코즈 확정 여부
- 5개 handoff 대조표
- 3개 write-back 동기화 표

### Step 4. 터미널별 3PASS 종료

터미널 문서는 아래 요건을 공통으로 만족해야 한다.

- 헤더에 범위/방법/작성일 명시
- finding ID는 `[S-TN-SEQ]`
- PASS1 후보 수, PASS2 제거 수, PASS3 확정 수 기재
- 기존 1차/2차 ID와의 중복 여부 기재
- 오탐 제거 사유 표 기재

### Step 5. 마스터 취합

취합 규칙:

- T2의 미해결 7건 추적 결과는 Section A로 우선 배치
- 신규 발견은 P0->P3 순으로 편성
- T5 보안/성능 요약표와 T4 프로토콜 대조표는 원형 보존
- 삭제 권고/레거시 판정은 T3 결과를 중심으로 묶는다

### Step 6. 최종 재감리

최종 통합본은 최소 3PASS 재감리를 거쳐야 하며, 95% 확신도 미달이면 문서 보정 후 재감리한다.

## 6. 터미널별 완료 조건

### E-T1. Stage 0

완료 조건:

- 메뉴 입력 검증, 6-모드 분기, 장르/POV 전파, Work Guard, Reverse Expander, Style Extractor, Story Expander 폴백, Preset Registry가 모두 범위에 포함된다.
- `T2-001`의 Stage 0 측 루트코즈 실마리가 문서에 남는다.
- 테스트 6개와 코드 경로의 커버리지 갭이 분리 기록된다.

### E-T2. 교차 스테이지

완료 조건:

- 미해결 7건이 전부 `루트코즈 확정 / 오탐 / 추가조사 필요` 중 하나로 분류된다.
- handoff 5개와 write-back 3개가 표 형태로 정리된다.
- 대원칙 3과 4 관련 건은 `CLAUDE.md` 직접 대조가 포함된다.

### E-T3. Lite Mode & Tools

완료 조건:

- Lite Mode 생존 여부, Tool 레거시 여부, DB 직접 조작 위험, 삭제 권고 목록이 분리된다.
- `blueprint_editor.py`의 외부 에디터 호출과 경로 검증이 포함된다.

### E-T4. API & Desktop

완료 조건:

- 9개 라우트와 WS `/events`가 모두 점검된다.
- `api-contract-v1.yaml` 대조표와 IPC 메시지 대조표가 들어간다.
- `root main.js / geuldobi-desktop/main.js / src/main.js` 3개 파일의 역할 구분이 명시된다.

### E-T5. 보안·성능·스케일

완료 조건:

- 보안 취약점 요약표, 성능 병목 Top 5, 스케일링 한계점 표가 포함된다.
- SQL 인젝션/경로 조작/XSS/프롬프트 인젝션은 방어 여부가 명시된다.
- 기존 플래그 6건의 심층 추적 결과가 포함된다.

## 7. 교차 검증 책임선

| 경계 | 1차 책임 | 2차 책임 | 산출물 |
|------|----------|----------|--------|
| Stage 0 메뉴 -> Stage 2 handoff | T1 | T2 | `plot_roadmap` 루트코즈 메모 + handoff 표 |
| Stage 3 -> Stage 4 Blueprint 계약 | T2 | T4 | Blueprint 필드 대조표 + API/IPC 영향 메모 |
| API surface -> Desktop protocol | T4 | T5 | 엔드포인트 표 + 보안 표 |
| Work Guard / path I/O | T1 | T5 | 파일 I/O 안전 메모 + 경로 조작 검증 |
| singleton / project contamination | T5 | T2 | 스케일링 표 + write-back 표 |

## 8. 문서 형식 규칙

### finding 본문 필수 필드

- `ID`
- `Severity`
- `파일`
- `현상`
- `증거`
- `영향`
- `기존 보고서와의 관계`
- `수정 영향 범위` 또는 `추가 조사 범위`

### 표 필수 항목

- T2: `상류 필드 / 하류 소비 필드 / 상태 / 비고`
- T4: `엔드포인트 / contract / backend / desktop / 상태`
- T5: `벡터 / 현재 방어 / 잔여 리스크 / 판정`

## 9. 최종 통합본 구성 잠금

최종 파일 [OPUS-TF-5terminal-deep-dive-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings.md)은 아래 6개 섹션을 고정한다.

- Section A: 미해결 P0/P1 추적 결과
- Section B: 신규 발견 P0->P3
- Section C: 보안 취약점 요약표
- Section D: 성능 병목 + 스케일링 한계
- Section E: 삭제 권고 / 레거시 판정
- Section F: 프로토콜 / handoff 대조표

## 10. confidence gate

이번 실행 SSOT의 최종 종료 조건은 아래다.

1. 터미널별 결과 문서 5개가 모두 존재한다.
2. 최종 통합본이 존재한다.
3. 통합본 재감리 문서 `OPUS-TF-5terminal-deep-dive-consolidated-findings-3pass-reaudit.md`가 존재한다.
4. 재감리 문서가 `95%` 이상 확신도를 명시한다.
5. 1차/2차 중복 제거 ledger가 재구성 가능하다.
6. P0 발견 시 `OPUS-TF-5terminal-deep-dive-p0-escalation-ledger.md`에 즉시 기록된다.

## 11. 비목표

- 3차 심층 감사와 동시에 코드 수정까지 수행하지 않는다.
- 아직 존재하지 않는 심층 finding을 선반영하지 않는다.
- grand total 추정치를 먼저 쓰고 나중에 맞추는 방식은 사용하지 않는다.
- 1차/2차 전체 finding 재정리를 다시 반복하지 않는다.

## 12. 다음 단계

이 문서가 잠그는 다음 작업은 아래 순서다.

1. 터미널별 `S-T1~S-T5` 문서 생산
2. 마스터 통합본 생산
3. 통합본 3PASS 재감리
4. 95% 확신도 미달 시 문서 보정 후 재감리
