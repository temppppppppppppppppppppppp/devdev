# GMR-G Live Surface vs Legacy Surface Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- active Electron entry는 `geuldobi-desktop/package.json`의 `"main": "src/main.js"`다.
- `geuldobi-desktop/main.js`와 루트 `main.js`가 별도 존재한다.
- `UI/`는 압축파일, 이미지, reference asset 중심이다.
- `lite_mode/`, `test_mode/`는 별도 실행/자동화 표면을 유지한다.

## PASS 2 교차 검증

- `package.json` shipping files는 `src/**/*`만 포함한다.
- `UI/` 경로는 runtime code reference보다 asset/archive 성격이 강하다.
- 기존 2026-03-13 문서군도 `UI/`를 reference archive, `geuldobi-desktop/main.js`를 shadow copy로 분류하는 방향과 일치한다.

## PASS 3 최종 findings

### [GMR-G-001] `UI/`는 runtime UI code가 아니라 reference asset archive로 분류하는 것이 맞다

- Severity: `closed / non-finding`
- Evidence:
  - `UI/` 파일 인벤토리
  - `geuldobi-desktop/src/*`가 실제 UI 코드
- Note:
  - 이후 문서에서 `UI/`를 앱 코드처럼 적으면 오탐이 늘어난다.

### [GMR-G-002] shadow main files와 alternate automation surface가 유지보수 혼선을 만든다

- Severity: `P2`
- Evidence:
  - `geuldobi-desktop/package.json:5`
  - `geuldobi-desktop/main.js`
  - 루트 `main.js`
  - `lite_mode/`, `test_mode/`
- Why macro risk:
  - active desktop shell, stale desktop shell, 별도 자동화 shell이 함께 남아 있다.
  - 시스템 설명 문서가 이 구분을 놓치면 live path와 테스트 path를 혼동하기 쉽다.

### [GMR-G-003] `lite_mode/`와 `test_mode/`는 주 시스템 UI가 아니라 별도 자동화 surface다

- Severity: `P2`
- Evidence:
  - 디렉터리 구조
  - `docs/2026-03-09/ui-system-audit.md`와 현재 파일 표면 교차 확인
- Why macro risk:
  - 운영 UI, 데스크톱 UI, 외부 웹 자동화 UI를 한 층으로 취급하면 정책/품질 판단이 오염된다.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
