# Mojibake Full Survey Order 3-Pass Audit

- 작성일: 2026-03-12
- 대상 SSOT: [mojibake-full-survey-execution-order-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/mojibake-full-survey-execution-order-ssot.md)
- 조사 모드: static / read-only
- 최종 상태: closed
- 최종 확신도: `95%`

## Executive Summary

`mojibake` 전용 전수조사 오더 문서는 현재 worktree 기준으로 충분히 실행 가능하다. 가장 중요한 보강점은 아래 두 가지가 명시적으로 잠겼다는 점이다.

- 현재 저장된 파일 파손과 콘솔 표시 깨짐을 구분한다.
- `cp949`/`errors="replace"`/`Set-Content` 같은 고위험 경로를 실제 producer 기준으로 추적한다.

현재 baseline 자체는 비교적 깨끗하다.

- UTF-8 읽기 실패 파일: `0`
- `U+FFFD` 포함 파일: `0`

따라서 이번 오더 문서의 목적은 “이미 대규모 파손이 난 저장소”를 복구하는 것이 아니라, `mojibake 재발·잠복·오탐`을 전량 식별할 수 있는 조사 프레임을 잠그는 데 있다.

## 1. Pass 1 - 사실 수집

### P1-1. 오더 문서는 실제 저장소 상태를 반영한다

직접 근거:

- read-only UTF-8 전수 읽기 집계 결과 `UTF8_FAIL = 0`
- read-only `U+FFFD` 탐지 결과 `0`

판정:

- `confirmed`

해석:

- 조사 문서는 막연한 “한글 깨짐 불안”이 아니라 현재 baseline과 producer 위험면을 분리해서 세워졌다.

### P1-2. 고위험 surface 정의가 실제 코드 경로와 맞는다

직접 근거:

- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py): `utf-8 -> cp949 -> errors='replace'` 폴백과 `U+FFFD` 경고
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py): stdout/stderr UTF-8 wrapper와 `errors="replace"`
- [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py): `PYTHONIOENCODING=utf-8`
- [geuldobi-desktop/src/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js): Electron backend env에 `PYTHONIOENCODING=utf-8`
- [scripts/e2e_menu_smoke.ps1](C:/Users/User/Desktop/글도비/scripts/e2e_menu_smoke.ps1): `Set-Content -Encoding UTF8`
- [docs/blockguide/bi-production-harness-v1.md](C:/Users/User/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md): PowerShell `Set-Content` 위험 경고

판정:

- `confirmed`

해석:

- 버킷 M1~M7은 추상적 카테고리가 아니라 실제 producer 경로에 걸쳐 있다.

### P1-3. 콘솔 오탐 제거 규칙이 필수다

직접 근거:

- 일부 `Get-Content` 출력은 콘솔에서 깨져 보였으나, 같은 파일을 UTF-8 기준으로 직접 읽는 baseline에서는 실패와 `U+FFFD`가 모두 `0`이었다.

판정:

- `confirmed`

해석:

- 이 규칙이 없으면 문서/코드가 멀쩡한데도 PowerShell 화면만 보고 mojibake로 오판할 수 있다.

## 2. Pass 2 - 교차 검증

### P2-1. deliberate fallback과 actual corruption이 분리되어 있다

교차 근거:

- 코드: [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)
- 문서: [docs/stage_map/stage0.md](C:/Users/User/Desktop/글도비/docs/stage_map/stage0.md)

판정:

- `confirmed`

해석:

- `cp949` 언급 자체를 문제로 올리는 문서는 오탐을 양산한다. 현재 오더 문서는 이 점을 적절히 통제한다.

### P2-2. PowerShell 작성 경로는 별도 bucket으로 보는 것이 맞다

교차 근거:

- 코드/스크립트: [scripts/e2e_menu_smoke.ps1](C:/Users/User/Desktop/글도비/scripts/e2e_menu_smoke.ps1)
- 문서 경고: [docs/blockguide/bi-production-harness-v1.md](C:/Users/User/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)

판정:

- `confirmed`

해석:

- mojibake는 Python 코드뿐 아니라 PowerShell 작성/리다이렉션에서도 발생할 수 있으므로 독립 버킷이 필요하다.

### P2-3. packaged/build inventory를 본 조사에서 직접 finding으로 올리면 오탐 위험이 높다

교차 근거:

- build inventory에는 `cp949`, `encoding` 문자열이 다수 존재한다.
- 그러나 이는 3rd-party runtime inventory이며, durable user text 파손의 직접 근거는 아니다.

판정:

- `confirmed`

해석:

- 오더 문서가 build inventory를 조사 범위에서 분리한 것은 맞는 판단이다.

## 3. Pass 3 - 오탐 제거

### R1. "현재 저장소는 이미 광범위한 mojibake 상태다"

기각 사유:

- 실제 UTF-8 읽기 실패 파일 `0`
- 실제 `U+FFFD` 포함 파일 `0`

상태:

- `rejected`

### R2. "`cp949` 문자열이 보이면 바로 결함이다"

기각 사유:

- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py)의 `cp949`는 입력 복구용 폴백이다.
- producer 맥락 없이 문자열 존재만으로는 finding이 될 수 없다.

상태:

- `rejected`

### R3. "PowerShell 화면에서 깨져 보였으니 파일도 깨졌다"

기각 사유:

- 콘솔 표시와 파일 바이트는 별도 층이다.
- UTF-8 직접 읽기 baseline이 이를 반증한다.

상태:

- `rejected`

## 4. 확정 판정

이번 감리에서 남는 결론은 아래뿐이다.

- 오더 문서는 실행 가능한 수준으로 충분히 구체적이다.
- 버킷 구성은 실제 producer 경로와 일치한다.
- 가장 중요한 오탐 제거 규칙인 `콘솔 표시 != 파일 파손`이 문서에 반영되어 있다.
- 별도 blocker는 없다.

## 5. retained observation

### O1. runtime-only surface는 후속 실행 없이는 100% 닫히지 않는다

- packaged GUI, shell codepage, 외부 편집기 저장 경로는 read-only 조사만으로 완전히 닫히지 않는다.
- 이 한계는 SSOT에 이미 `runtime-only` 분류로 반영되어 있으므로 blocker는 아니다.

## 6. 확신도 ledger

- 기본 점수: `70`
- baseline 실측 반영: `+10`
- producer 경로와 버킷 매핑 2중 근거 확보: `+10`
- 오탐 제거 규칙 명문화: `+5`
- build inventory / console false positive 분리 완료: `+5`
- packaged GUI / 외부 편집기 runtime 미검증: `-5`

최종 확신도: `95%`

## 7. 결론

- 상태: `execution-ready`
- blocker: 없음
- 다음 단계: 문서 확정 후 실제 `mojibake 전수조사 실행`

이번 턴은 오더 문서와 그 감리 문서 확정까지만 수행한다. 실제 전수조사 실행은 후속 지시에서 진행한다.
