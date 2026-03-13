# Mojibake Full Survey 3-Pass Final Audit

- 작성일: 2026-03-12
- 대상 SSOT: [mojibake-full-survey-execution-order-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/mojibake-full-survey-execution-order-ssot.md)
- 조사 모드: static / read-only
- 최종 상태: closed
- 최종 확신도: `95%`

## Executive Summary

시스템 전역 `mojibake` 전수조사 결과, 현재 저장된 worktree 자체에서 광범위한 문자 파손은 확인되지 않았다.

- UTF-8 읽기 실패 파일: `0`
- `U+FFFD` 포함 파일: `0`
- Python producer 경로의 `open/read_text/write_text` 중 `encoding` 누락 후보: `0`

따라서 현재 핵심 리스크는 “이미 저장소가 깨져 있다”가 아니라 “특정 producer 경로가 새 mojibake를 만들 수 있다” 쪽이다. 그중 실제 retained finding은 Stage 0 입력 폴백 1건과 PowerShell 작성 경로 1건이다. 콘솔 출력 계층의 `replace/ignore`는 오탐 또는 runtime-only 계층으로 내렸다.

## 1. Baseline

### B1. 현재 저장 파일 파손 baseline

- read-only UTF-8 전수 읽기 결과 `UTF8_FAIL = 0`
- read-only replacement char 탐지 결과 `U+FFFD = 0`

해석:

- 저장된 텍스트 파일 기준으로는 현재 대규모 mojibake가 이미 굳어져 있다고 볼 근거가 없다.

### B2. Python I/O 경로 baseline

- `modules/`, `scripts/`, `build/`, [main_a.py](C:/Users/User/Desktop/글도비/main_a.py) 전역 AST 스캔 결과:
  - `open()` text mode에서 `encoding` 누락 후보 `0`
  - `Path.read_text()/write_text()/open()`에서 `encoding` 누락 후보 `0`

해석:

- 핵심 Python producer는 이미 UTF-8 명시 관행이 강하게 자리 잡고 있다.

## 2. Pass 1 - 사실 수집

### P1-1. Stage 0 입력 인입에는 fail-open mojibake risk가 남아 있다

직접 근거:

- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)
  - `utf-8` 실패 시 `cp949`
  - `cp949`도 실패하면 `encoding="utf-8", errors="replace"`
  - `U+FFFD` 포함 시 경고만 남기고 계속 진행
- [stage0.md](C:/Users/User/Desktop/글도비/docs/stage_map/stage0.md)
  - `utf-8 -> cp949 -> utf-8(errors="replace")` 폴백 문서화

1차 결론:

- malformed 입력이 들어오면 문자 손실이 경고만 찍힌 채 raw draft로 유입될 수 있다.

### P1-2. PowerShell 쓰기 경로는 문서 정책과 환경 민감성이 남아 있다

직접 근거:

- [e2e_menu_smoke.ps1](C:/Users/User/Desktop/글도비/scripts/e2e_menu_smoke.ps1)
  - `Set-Content -Encoding UTF8`
  - `Add-Content -Encoding UTF8`
- [bi-production-harness-v1.md](C:/Users/User/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)
  - Windows PowerShell 5.x에서 `Set-Content -Encoding UTF8` 경로를 피하라고 명시

1차 결론:

- 현재 스모크 하네스 작성 경로는 core backend producer는 아니지만, PowerShell 런타임 버전에 따라 BOM/표시/저장 차이가 생길 여지를 남긴다.

### P1-3. 콘솔 출력 경로는 durable corruption보다 diagnostic masking 문제에 가깝다

직접 근거:

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
  - `TextIOWrapper(..., encoding="utf-8", errors="replace")`
- [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
  - `PYTHONIOENCODING=utf-8`
- [geuldobi-desktop/src/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
  - backend spawn env에 `PYTHONIOENCODING=utf-8`
- [run_stage4_smoke.py](C:/Users/User/Desktop/글도비/scripts/run_stage4_smoke.py)
  - `UnicodeEncodeError` 시 `cp949` + `errors="ignore"`로 출력 폴백

1차 결론:

- 주된 위험은 저장 파일 파손이 아니라, console-only surface에서 일부 문자가 사라져 운영자가 원인을 오판할 수 있다는 점이다.

## 3. Pass 2 - 교차 검증

### C1. "저장소가 이미 광범위하게 깨져 있다"는 주장은 반증된다

교차 근거:

- 실측 baseline: UTF-8 읽기 실패 `0`, `U+FFFD` `0`
- Python I/O AST 스캔: `encoding` 누락 후보 `0`

판정:

- `rejected`

해석:

- 현재는 latent producer risk 조사이지, existing corpus repair 상황은 아니다.

### C2. Stage 0 fail-open 경로는 실제 producer risk다

교차 근거:

- 코드: [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)
- 문서: [stage0.md](C:/Users/User/Desktop/글도비/docs/stage_map/stage0.md)

판정:

- `confirmed`

해석:

- deliberate fallback이더라도 `errors="replace"` 이후 경고만 하고 진행하는 구조는 실제로 durable mojibake를 만들 수 있다.

### C3. PowerShell 작성 경로는 policy drift이지만 핵심 파이프라인 결함으로 단정하긴 이르다

교차 근거:

- 스크립트: [e2e_menu_smoke.ps1](C:/Users/User/Desktop/글도비/scripts/e2e_menu_smoke.ps1)
- 문서 정책: [bi-production-harness-v1.md](C:/Users/User/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)

판정:

- `confirmed`

해석:

- 위험은 실재하지만 환경 의존성이 크고 스모크 하네스 범위라 core P1까지는 올리지 않았다.

### C4. 콘솔 fallback은 오탐 생성면이지 파일 파손의 직접 근거는 아니다

교차 근거:

- 코드: [main_a.py](C:/Users/User/Desktop/글도비/main_a.py), [run_stage4_smoke.py](C:/Users/User/Desktop/글도비/scripts/run_stage4_smoke.py)
- baseline: 저장 파일 파손 지표 `0`

판정:

- `confirmed`

해석:

- 출력층에서 문자를 `replace/ignore`하는 것은 진단 가시성 문제다. 파일 파손 finding과는 분리하는 것이 맞다.

## 4. Pass 3 - 오탐 제거

### R1. `cp949` 문자열이 보이면 바로 mojibake 결함이다

기각 사유:

- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)의 `cp949`는 복구용 폴백이다.
- producer 문맥 없이 문자열 존재만으로는 finding이 아니다.

상태:

- `rejected`

### R2. build inventory에 `encoding`, `cp949`가 많으니 배포 산출물은 이미 깨졌다

기각 사유:

- build inventory는 3rd-party/packaging metadata다.
- durable user text 파손의 직접 근거가 아니다.

상태:

- `rejected`

### R3. PowerShell에서 글자가 깨져 보였으니 파일도 깨졌다

기각 사유:

- 콘솔 출력과 파일 바이트는 별도 층이다.
- 현재 baseline이 이를 반증한다.

상태:

- `rejected`

## 5. 확정 Findings

### F1. P1 - Stage 0 입력 인입이 `errors="replace"` 이후 fail-open으로 진행된다

- subsystem: Stage 0 ingest
- claim: UTF-8와 cp949 모두 실패한 입력이 `errors="replace"`로 읽힌 뒤 경고만 남기고 계속 진행되므로, 문자 손실이 downstream artifact에 durable하게 유입될 수 있다.
- direct evidence:
  - [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)
  - [stage0.md](C:/Users/User/Desktop/글도비/docs/stage_map/stage0.md)
- counter-evidence review:
  - 경고와 `U+FFFD` 탐지는 존재한다.
  - 그러나 차단하지 않으므로 producer risk는 남는다.
- why_not_false_positive:
  - 단순 문자열 존재가 아니라 실제 ingest 코드가 그렇게 동작한다.
- user impact:
  - 깨진 draft가 Stage 0 이후 전 단계로 전파될 수 있다.
- status:
  - `confirmed`

### F2. P2 - PowerShell smoke harness 작성 경로가 문서 정책과 drift 상태다

- subsystem: smoke scripts / docs policy
- claim: [e2e_menu_smoke.ps1](C:/Users/User/Desktop/글도비/scripts/e2e_menu_smoke.ps1)는 `Set-Content`/`Add-Content -Encoding UTF8`를 사용하지만, 내부 문서는 Windows PowerShell 5.x에서 이 경로를 피하라고 경고한다.
- direct evidence:
  - [e2e_menu_smoke.ps1](C:/Users/User/Desktop/글도비/scripts/e2e_menu_smoke.ps1)
  - [bi-production-harness-v1.md](C:/Users/User/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)
- counter-evidence review:
  - PowerShell 7 계열이나 특정 실행 환경에서는 실제 문제가 없을 수 있다.
  - core backend artifact producer는 아니다.
- why_not_false_positive:
  - 스크립트와 정책 문서가 직접 충돌한다.
- user impact:
  - 환경에 따라 smoke input/output JSON 기록의 문자 안정성이 흔들릴 수 있다.
- status:
  - `confirmed`

## 6. Observations

### O1. Console fallback이 운영 진단 가시성을 낮출 수 있다

- 대상:
  - [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
  - [run_stage4_smoke.py](C:/Users/User/Desktop/글도비/scripts/run_stage4_smoke.py)
- 내용:
  - `errors="replace"` 또는 `errors="ignore"`가 console-only surface에서 문자를 떨어뜨릴 수 있다.
- 판정:
  - `Observation`

### O2. 현재 저장 corpus는 clean baseline이다

- 대상:
  - 전수 UTF-8 읽기 집계
  - `U+FFFD` 탐지
  - Python I/O AST scan
- 내용:
  - 현 시점의 시스템 전역 텍스트 파일은 mojibake 잔존이 아니라 producer risk가 본질이다.
- 판정:
  - `Observation`

## 7. 잔여 불확실성

- packaged GUI, 외부 편집기, 실제 shell codepage 조합에서만 드러나는 runtime-only 문자 깨짐
- 비 UTF-8 입력 파일이 실제 운영 투입될 때 Stage 0 fail-open 경로가 어느 정도 자주 밟히는지

## 8. 확신도 Ledger

- 기본 점수: `70`
- 전체 baseline 실측 완료: `+10`
- Python I/O encoding 누락 전수 스캔 완료: `+10`
- producer 경로 2중 근거 확보: `+10`
- 오탐 제거 완료: `+5`
- packaged GUI / 외부 편집기 runtime 미검증: `-5`
- live malformed-input 재현 미검증: `-5`

최종 확신도: `95%`

## 9. 최종 결론

- 상태: `closed`
- P0: `0`
- P1: `1`
- P2: `1`
- Observation: `2`

현재 시스템 전역의 `mojibake` 문제는 “이미 저장된 파일이 대량 파손되었다”가 아니라, `Stage 0 fail-open ingest`와 `PowerShell smoke harness policy drift` 두 축으로 요약된다. 실제 실행 단계에서는 이 두 축을 우선 처리하는 것이 맞다.
