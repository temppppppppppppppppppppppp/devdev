# Mojibake Full Survey Execution Order SSOT

- 작성일: 2026-03-12
- 상태: execution-ready
- 문서 역할: 시스템 전역 `mojibake` 전용 전수조사 오더 SSOT
- 금지사항: 코드 수정 금지, 테스트 실행 금지, canary/live/full rerun 금지
- 허용 범위: 읽기, 검색, diff, UTF-8 디코드 점검, 로그/산출물/문서 열람, 감사 문서 작성

## 1. 목적

이 문서는 시스템 전역을 대상으로 `mojibake` 문제만 집중 조사하기 위한 실행 기준 문서다. 여기서 말하는 mojibake는 단순히 콘솔에 글자가 이상하게 보이는 현상이 아니라, 파일/로그/산출물/프롬프트/런타임 텍스트가 잘못된 인코딩 경로를 지나 의미를 잃거나 문자 무결성이 파손된 상태를 뜻한다.

이번 조사의 목표는 아래 두 가지를 분리해서 다루는 것이다.

1. 실제 파일/산출물의 문자 파손
2. 콘솔/터미널/뷰어 표시 문제로 인한 오탐

## 2. 기준선

- 조사 기준일: 2026-03-12
- 조사 모드: static / read-only
- 현재 baseline:
  - worktree 전수 UTF-8 읽기 점검 결과 `UTF8_FAIL = 0`
  - `U+FFFD` 포함 파일 수 `0`
- 위 baseline은 현재 저장된 파일 상태가 당장 광범위하게 깨져 있음을 뜻하지 않는다.
- 그럼에도 별도 조사를 여는 이유는 producer 경로와 fallback 경로에 mojibake 위험면이 남아 있기 때문이다.

## 3. 참고 문서

- [backend-health-full-survey-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/backend-health-full-survey-execution-ssot.md)
- [backend-health-full-survey-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/backend-health-full-survey-3pass-audit.md)
- [system-wide-full-survey-3pass-master-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md)
- [today-code-health-ui-build-roadmap.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/today-code-health-ui-build-roadmap.md)
- [docs/blockguide/bi-production-harness-v1.md](C:/Users/User/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)

## 4. 조사 범위

### 포함

- tracked Python, Markdown, JSON, YAML, HTML, JS, PS1, TXT 등 텍스트성 파일 전체
- `main_a.py`와 backend stage/orchestrator/helper 전체
- `modules/api`, `modules/core`, `modules/domain`의 텍스트 입출력 경로
- `geuldobi-desktop/src` 및 Electron main/preload의 텍스트 브리지 경로
- `docs/`, `scripts/`, `config/`, `treatments/`, `bible/`, `projects/*/logs|drafts|memory` 중 tracked 텍스트 산출물

### 제외

- 바이너리 파일
- `node_modules`, `.git`, 캐시 디렉토리
- PyInstaller/Electron이 생성한 3rd-party inventory 산출물 자체
- SmartScreen, 서명, 배포 평판 이슈

## 5. 고정 조사 버킷

### M1. 입력 인입과 폴백

- 대상: [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py), [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py), [project_manager.py](C:/Users/User/Desktop/글도비/modules/core/project_manager.py)
- 질문:
  - UTF-8 실패 시 `cp949`, `euc-kr`, `errors="replace"` 폴백이 어디서 발생하는가
  - 폴백 후 `U+FFFD`를 탐지하거나 차단하는가
  - 폴백이 저장 경로까지 전파되는가, 아니면 읽기 복구로만 끝나는가

### M2. 런타임 stdout/stderr/콘솔 브리지

- 대상: [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py), [geuldobi-desktop/src/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- 질문:
  - `PYTHONIOENCODING=utf-8`과 `TextIOWrapper(..., errors="replace")`가 어떤 콘솔/로그 surface를 보호하는가
  - 콘솔 표시 이상이 파일 파손으로 오판될 수 있는 경로가 있는가

### M3. 문서/스크립트 작성 경로

- 대상: [scripts/e2e_menu_smoke.ps1](C:/Users/User/Desktop/글도비/scripts/e2e_menu_smoke.ps1), [docs/blockguide/bi-production-harness-v1.md](C:/Users/User/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md), PowerShell 작성 경로 전반
- 질문:
  - `Set-Content`, `Out-File`, 임시 리다이렉션이 UTF-8/BOM/콘솔 코드페이지 문제를 유발하는가
  - 문서가 이미 경고한 금기사항이 실제 스크립트에 남아 있는가

### M4. 로그/아티팩트/DB 변환 경로

- 대상: [audit_service.py](C:/Users/User/Desktop/글도비/modules/core/services/audit_service.py), [metrics_collector.py](C:/Users/User/Desktop/글도비/modules/core/metrics_collector.py), [pass_rate_monitor.py](C:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py), [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- 질문:
  - JSONL/JSON/TXT 쓰기 경로가 UTF-8로 고정되어 있는가
  - 텍스트 정규화 과정이 문자 손실을 일으키지 않는가
  - sink 간 동일 텍스트가 다른 문자 상태로 기록될 가능성이 있는가

### M5. 프롬프트/설정/지원 자산

- 대상: [prompt_loader.py](C:/Users/User/Desktop/글도비/modules/core/prompt_loader.py), [project_support.py](C:/Users/User/Desktop/글도비/modules/core/project_support.py), [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml)
- 질문:
  - 프롬프트와 YAML/JSON 설정이 UTF-8 전제로 일관되게 읽히는가
  - style/work-guard/author directives가 다른 인코딩 경로를 거치지 않는가

### M6. 문서와 감사 산출물

- 대상: `docs/2026-03-12/*`, `docs/stage_map/*`, tracked 감사 문서 전반
- 질문:
  - 감사 문서 자체가 깨져 보일 때 그것이 파일 파손인지 콘솔 출력 문제인지 구분 가능한가
  - 문서 생성/수정 프로세스에서 인코딩 손상이 재현 가능한가

### M7. 패키징과 배포 텍스트 경로

- 대상: [build_release.ps1](C:/Users/User/Desktop/글도비/build/build_release.ps1), [backend_entry.py](C:/Users/User/Desktop/글도비/build/backend_entry.py), [geuldobi-desktop/package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- 질문:
  - packaged 환경에서 stdout/stderr/log 파일이 UTF-8로 유지되는가
  - build 산출물 inventory의 encoding 관련 문자열이 실제 mojibake와 구분되는가

## 6. 판정 규칙

### confirmed

아래 중 하나라도 만족하고, producer 경로 근거가 붙으면 `confirmed`로 올린다.

- UTF-8 전제 파일이 UTF-8로 디코드 실패
- durable artifact에 `U+FFFD`가 포함되고 placeholder 정책이 아님
- 동일 텍스트가 저장 surface마다 다른 문자 상태로 기록됨
- 잘못된 인코딩 변환의 결과로 해석되는 전형적 깨짐 패턴이 producer 경로와 함께 확인됨

### rejected

아래는 단독으로는 finding으로 올리지 않는다.

- PowerShell/터미널에서만 깨져 보이고 파일 자체는 UTF-8로 정상 읽힘
- 3rd-party build inventory에 `cp949`, `encoding` 문자열이 존재함
- 바이너리 파일/압축물에서 추출된 인벤토리 문자열
- 의도된 입력 복구용 `cp949` 폴백 존재 자체

### runtime-only

- 콘솔/GUI/packaged runtime에서만 재현 가능하고 현재 read-only 조사로 닫히지 않는 항목

## 7. 조사 흐름

### Pass 1. 전량 인벤토리와 baseline 확보

- 텍스트 파일 전수 UTF-8 읽기 성공/실패 집계
- `U+FFFD` 포함 파일 집계
- 인코딩 관련 코드 경로 인벤토리화
- 고위험 producer 경로 목록 작성

### Pass 2. 교차 검증

- 각 주장마다 최소 2개 증거 계층 확보
- 증거 계층:
  1. 실제 파일 내용
  2. producer 코드 경로
  3. 관련 운영/감사 문서
  4. tracked 로그/산출물

### Pass 3. 오탐 제거

- 콘솔 표시 문제와 파일 파손을 분리
- 3rd-party build inventory를 조사 결과에서 분리
- deliberate fallback과 실제 문자 손실을 분리
- retained finding만 severity 부여

## 8. 증거 ledger 형식

모든 claim은 아래 필드로 기록한다.

- id
- bucket
- file_ref
- claim
- evidence_type
- evidence_summary
- status (`confirmed`, `rejected`, `runtime-only`)
- severity (`P0`, `P1`, `P2`, `Observation`)
- confidence_delta

## 9. 최종 산출물 형식

최종 실행 감리 문서는 아래 순서를 따른다.

1. Executive Summary
2. Baseline
3. Pass 1 전량 인벤토리
4. Pass 2 교차 검증
5. Pass 3 오탐 제거
6. 확정 findings
7. 기각 findings
8. 확신도 ledger
9. 잔여 불확실성
10. coverage 표

## 10. 확신도 정책

- 시작점: `70`
- 전체 버킷 인벤토리 완료: `+10`
- baseline scan과 producer 경로 2중 근거 확보: `+10`
- 오탐 제거 완료: `+5`
- 콘솔-vs-파일 구분 규칙이 실제 사례로 검증됨: `+5`
- runtime-only 항목, GUI/packaged 미검증 항목별 `-1~-5`

read-only로 닫히지 않는 항목이 남으면 `95%`를 억지로 맞추지 않고 방어 가능한 상한에서 멈춘다.

## 11. 완료 기준

- 버킷 M1~M7 전량 커버
- 실제 파일 파손과 표시 문제를 분리한 evidence index 작성
- `confirmed`, `rejected`, `runtime-only`가 모두 근거와 함께 닫힘
- 최종 확신도 `95%` 또는 방어 가능한 상한 도달

## 12. 기본 가정

- 모든 텍스트성 소스는 UTF-8이 기준이다.
- `cp949` 폴백은 존재 자체로는 결함이 아니다.
- 콘솔에 한글이 깨져 보이는 현상은 파일 파손의 충분조건이 아니다.
- 이번 단계는 오더 문서와 그 감리 문서 확정까지만 수행한다. 실제 전수조사 실행은 후속 지시에서 진행한다.
