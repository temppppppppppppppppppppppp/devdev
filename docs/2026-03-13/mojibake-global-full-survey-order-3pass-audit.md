# Mojibake Global Full Survey Order - 3Pass Audit

- 작성일: 2026-03-13
- 상태: `execution-ready`
- 조사 모드: `static` / `read-only`
- 대상 범위: vendor·bundle·cache를 제외한 worktree 전역 텍스트 파일
- 실행 스캐너: `scripts/mojibake_global_survey.py`

## Executive Summary

이번 오더는 어제자 `docs/2026-03-12/mojibake-full-survey-execution-order-ssot.md`를 그대로 재사용하지 않는다. 그 문서는 `UTF-8 decode fail`과 `U+FFFD` 중심으로 잘 짜여 있었지만, 오늘 요청의 범위인 "전역 전수 조사"를 닫기에는 세 가지가 부족했다.

1. archived log, untracked root text, historical generated artifact가 baseline에서 빠질 수 있다.
2. `???` 다량 잔존처럼 `U+FFFD` 없이도 이미 의미를 잃은 payload를 별도 버킷으로 강제하지 않았다.
3. literal mention, placeholder, console display artifact를 오탐 버킷으로 잠그는 규칙은 있었지만, 실제 대량 후보 파일에 대한 재현 가능한 분류 절차가 약했다.

그래서 오늘 오더는 `UTF-8 strict read + U+FFFD + ???/?? candidate + producer surface inventory`를 한 번에 수집하고, 결과를 JSON evidence로 남긴 뒤 사람 검토를 붙이는 방식으로 보강한다.

## Scope

### 포함

- root 기준 모든 텍스트성 파일
- `main_a.py`, `main.js`, `modules/`, `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/src/`
- `docs/`, `config/`, `treatments/`, `bible/`, `projects/`, `test_material/`, `lite_mode/`, `test_mode/`, `build/`
- tracked 여부와 무관한 현재 worktree 파일

### 제외

- `.git`, cache, `node_modules`
- `dist`, `python-embed`, packaged bundle inventory
- null byte 포함 binary

## Investigation Buckets

### G1. Stored artifact corruption

- 질문:
  - UTF-8 strict decode가 실제로 실패하는 파일이 있는가
  - 저장된 payload 안에 `U+FFFD`가 남아 있는가
  - line sample 수준에서 실제 문장/로그가 깨졌는가

### G2. Question-mark corruption candidates

- 질문:
  - `???`, `??`가 placeholder가 아니라 의미 손실 흔적인가
  - user-facing JSON/Markdown/TXT payload에 대량 잔존하는가
  - 동일 계열 파일 묶음 전체가 같이 손상되었는가

### G3. Live source and prompt surfaces

- 질문:
  - 소스 코드의 docstring/log/prompt literal이 이미 깨져 있는가
  - 깨진 문자열이 live wrapper/test를 통해 실제 호출 surface에 도달하는가

### G4. Producer and fallback surfaces

- 질문:
  - `cp949`, `errors="replace"`, `errors="ignore"`, `PYTHONIOENCODING`, `Set-Content`, `Add-Content`, `Out-File`가 어디에 남아 있는가
  - 현재 artifact corruption과 이어질 수 있는 producer path가 있는가

### G5. False-positive buckets

- 아래는 단독으로 finding으로 올리지 않는다.
  - 문서가 예시로 literal `�` 또는 `???`를 적은 경우
  - regex/test fixture placeholder
  - console rendering only
  - vendor/bundle inventory

## Execution Steps

1. `python -X utf8 scripts/mojibake_global_survey.py --output docs/2026-03-13/mojibake-global-full-survey-evidence.json`
2. `utf8_fail`, `fffd`, `q3/q2` 상위 후보를 bucket별로 샘플링한다.
3. live source 후보는 consumer/test grep으로 실제 소비 여부를 확인한다.
4. archived log와 historical artifact는 root-cause surface와 연결 가능한지 본다.
5. literal mention / placeholder / console artifact를 Pass 3에서 제거한다.

## 3Pass Audit

### Pass 1 - Coverage Audit

판정: `reinforced`

- 기존 오더 대비 보강:
  - tracked file only 해석을 금지하고 worktree 전역으로 확대
  - `projects/`, `test_material/`, root `.txt/.log`를 명시 포함
  - vendor/bundle 제외 규칙을 path 단위로 고정
- 실행 근거:
  - 스캐너는 suffix allowlist와 directory exclusion을 동시에 사용한다.
  - JSON evidence에 `text_files_scanned`, `excluded_dir_names`, `bucket_counts`를 남긴다.

### Pass 2 - False Positive Audit

판정: `reinforced`

- 기존 오더 대비 보강:
  - `U+FFFD`만이 아니라 `???/??`도 후보로 수집하되 즉시 finding으로 승격하지 않는다.
  - literal mention과 corruption을 line sample로 분리한다.
  - console artifact는 파일 strict-read 결과와 분리한다.
- 실행 근거:
  - suspicious file마다 line sample 3개를 남긴다.
  - UTF-8 decode fail 파일은 `cp949/euc-kr/latin-1` preview를 같이 남긴다.

### Pass 3 - Execution Readiness Audit

판정: `execution-ready`

- blocker 없음
- 스캐너 출력만으로 끝내지 않고, 상위 후보를 사람이 다시 열어 `confirmed/rejected/runtime-only`로 재판정한다.
- live code 후보는 반드시 consumer/test evidence를 붙인다.

## Reinforced Decision Rules

### confirmed

- UTF-8 strict decode fail이 실제 저장 파일에서 확인됨
- `U+FFFD`가 literal example이 아니라 artifact 본문에 존재함
- `???/??`가 user-facing payload 전체에 퍼져 있고 동일 계열 파일에서도 반복됨
- 깨진 문자열이 live source surface에서 실제 반환/로그/프롬프트로 소비됨

### rejected

- literal example
- placeholder fixture
- regex escape
- console-only artifact
- vendor/bundle surface

### runtime-only

- 현재 저장 파일은 멀쩡하지만 producer path가 future corruption risk를 남김

## Completion Criteria

- evidence JSON 생성
- bucket G1~G5 전량 커버
- top candidates manual sample 확인
- final report에서 `confirmed/rejected/runtime-only`와 confidence ledger를 함께 제출
