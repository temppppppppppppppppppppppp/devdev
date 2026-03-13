# UI Frontend-Backend Connectivity Remediation Execution SSOT

작성일: 2026-03-13

## Executive Summary

- 이번 실행 범위는 `데스크톱 UI <-> Electron IPC <-> bridge/backend` 연결성 보강이다.
- 범위는 `Stage 0 submenu 계약`, `Stage 0 style cache / work_guard 신규 backend 기능의 UI surface`, `관련 desktop regression gate`로 고정한다.
- 이번 오더는 `renderer monolith 분해`, `CSP 전면 개편`, `패키징/빌드 개편`을 포함하지 않는다.
- 목표는 `사용자가 UI에서 보는 실행 의미`와 `backend가 실제로 수행하는 실행 의미`를 다시 일치시키는 것이다.

## Scope

포함:
- [geuldobi-desktop/src/index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- [geuldobi-desktop/src/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- [geuldobi-desktop/src/preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js)
- [modules/api/process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- desktop/UI 관련 테스트 및 문서 gate

제외:
- renderer monolith 구조 해소
- `unsafe-inline` CSP 제거
- Stage 2~4 본체 로직 변경
- packaged build/version bump

## Baseline Findings

### F1. Stage 0 submenu와 backend mode가 어긋나 있다

- UI는 현재 Stage 0 서브버튼을 아래처럼 노출한다.
  - `sub_key 2`: 컨셉 -> Bible 생성
  - `sub_key 3`: 역설계
  - `sub_key 4`: Bible import
  - `sub_key 5`: Block 확장
  - `sub_key 6`: 스타일 레퍼런스 분석
- 하지만 backend의 실제 `mode -> handler`는 아래다.
  - `2`: 역설계
  - `3`: Bible import
  - `4`: Block 확장
  - `5`: 스타일 레퍼런스 분석
  - `6`: 작품가드 설정
- 따라서 현재 UI는 `2~6` 전 구간이 한 칸씩 밀려 있다.
- 특히 `sub_key 6` 버튼은 화면상 `스타일 레퍼런스 분석`이지만 실제 backend에서는 `작품가드 설정`을 실행한다.

### F2. Stage 0 신규 backend 기능이 UI에 일급 surface로 연결돼 있지 않다

- backend는 이미 `style cache mode(use / refresh / reset)`를 지원한다.
- backend는 이미 `root/work_guards` 라이브러리에서 템플릿을 가져와 `{project}/config/work_guard.yaml`로 쓰는 흐름을 지원한다.
- 하지만 desktop UI는 현재:
  - style cache mode를 명시적으로 선택할 수 없다.
  - work_guard template library를 조회/적용할 수 없다.
  - 설정 탭 raw YAML 편집만 지원한다.

### F3. Stage 0 UI contract용 regression gate가 없다

- 기존 desktop tests는 `Frontier Lag`, `sanitization`, `API contract refresh` 중심이다.
- Stage 0 submenu label/sub_key drift나 Stage 0 신규 UI surface를 잡는 focused regression이 없다.

## Remediation Goals

### R1. Stage 0 submenu를 실제 backend mode와 일치시킨다

- UI 버튼 텍스트와 sub_key를 backend 의미와 맞춘다.
- `작품가드 설정(선택)`을 Stage 0 서브메뉴에 정식 노출한다.
- `개선 중` 경고는 실제 backend 지원 범위를 기준으로만 유지한다.

### R2. style cache mode를 UI에서 명시적으로 선택 가능하게 한다

- Stage 0 `스타일 레퍼런스 분석` 실행 전 `use / refresh / reset` 중 하나를 고를 수 있어야 한다.
- 선택 결과는 backend로 전달되어 deterministic하게 stdin sequence에 반영돼야 한다.
- 기존 prompt fallback은 보조 경로로만 남긴다.

### R3. work_guard template library를 UI에 연결한다

- UI는 `root/work_guards` 템플릿 목록을 읽을 수 있어야 한다.
- 현재 프로젝트에 template를 적용할 수 있어야 한다.
- 실제 런타임 경로는 계속 `{project}/config/work_guard.yaml`로 유지한다.
- work_guard는 필수가 아니라 선택형 준비물이라는 계약을 유지한다.

### R4. regression/test/docs gate를 최신 상태로 맞춘다

- Stage 0 submenu contract test 추가
- style cache mode wiring test 추가
- work_guard template IPC/UI contract test 추가
- desktop package test script에 새 focused regression 반영

## Public Contracts To Preserve

- `window.geuldobiDesktop.runKey(key, subKey, inputs)` surface는 유지
- `bridge:run` / `/run` envelope는 유지
- `{project}/config/work_guard.yaml` runtime path는 유지
- `config/style_references/{genre}/style_guide.json` 공용 캐시 구조는 유지
- 기존 `key 6 One-Stop`, `key 7 Frontier Lag` 계약은 유지

## Implementation Strategy

1. `index.html`
- Stage 0 submenu label/sub_key/meta 정렬
- style cache mode selector 추가
- work_guard template selector/적용 버튼 추가
- project settings 로드/저장 흐름에 template UI 상태 연결

2. `preload.js`
- work_guard template list/apply IPC surface 노출

3. `main.js`
- `work_guards/` 라이브러리 조회 IPC 추가
- 선택 template를 현재 프로젝트 config로 적용하는 IPC 추가

4. `process_runner.py`
- `key=0, sub_key=5(style analysis)`일 때 UI가 보낸 `stage0_style_cache_mode`를 stdin sequence로 주입
- 기존 Mode B prompt 흐름은 깨지지 않게 유지

5. tests
- Stage 0 submenu contract
- style cache mode run input wiring
- work_guard template IPC/UI contract

## Acceptance Criteria

- UI의 Stage 0 서브버튼 의미와 backend mode가 1:1로 일치한다.
- `스타일 레퍼런스 분석`은 UI에서 `use / refresh / reset`를 명시 선택할 수 있다.
- `작품가드 설정(선택)`은 UI에서 template list를 보고 적용할 수 있다.
- work_guard 미선택 프로젝트도 기존처럼 정상 실행된다.
- focused regression이 이 계약을 고정한다.

## Verification Plan

- focused pytest
  - Stage 0 submenu/UI contract tests
  - process runner style cache injection tests
  - desktop work_guard template IPC tests
  - 기존 desktop connectivity regression
- Electron spike
  - desktop boot
  - settings/project 탭 진입
  - Stage 0 submenu rendering
  - bridge status 확인

## Out of Scope Notes

- renderer 전면 리팩터
- CSP strict mode
- packaged installer QA
- live Stage 0/15arc runtime 검증

