# UI 구조개편 실행 SSOT

작성일: 2026-03-12  
문서 역할: 글도비 데스크톱 UI 구조개편의 단일 실행 기준서  
상태: draft-fixed / execution-ready  
기준 정책: 단기 땜질보다 정보구조 재편을 우선한다

## 1. 목적

이번 구조개편의 목적은 세 가지다.

1. `사무실`을 우측 복합 대시보드에서 분리해 몰입형 화면으로 되돌린다.
2. `Run / Quality / Project / Settings` 책임을 분리해 레이아웃 과적재를 해소한다.
3. UI 표면과 실제 backend wiring 사이의 빈 계약을 정리한다.

이번 문서는 "어떤 방향이 좋아 보이는가"가 아니라 "어떤 순서로 무엇을 바꿀 것인가"를 잠그는 실행 SSOT다.

## 2. 현재 문제 정의

현재 UI는 아래 문제가 한 원인에서 함께 발생한다.

- `사무실` 캔버스가 짧아졌다.
- `Artifact Ladder` 하단이 안 보인다.
- 로그를 접어도 우측 컬럼 전체는 여전히 답답하다.
- 실행 패널이 기본 펼침이라 좌측 밀도가 과하다.
- `모델` 탭은 실제 제어판처럼 보이지만 런타임 wiring이 없다.
- `작품가드`는 backend에 연결돼 있지만 진입 위치가 `설정 > 프로젝트` 탭 안쪽이라 준비 플로우와 분리돼 있다.

구조적 원인은 명확하다.

- 우측 컬럼 전체가 `overflow: hidden`이다. `geuldobi-desktop/src/index.html:94`
- `사무실` 패널 내부에 `canvas + quality + retrieval + result + trend + agent board + live feed`가 모두 붙어 있다. `geuldobi-desktop/src/index.html:2613`
- 좌측 실행 패널 아코디언은 기본 펼침이며 자동 접기나 상태 기억이 없다. `geuldobi-desktop/src/index.html:7039`
- 모델 탭 UI는 존재하지만 `config/models.yaml` 저장/로드 wiring이 없다. `geuldobi-desktop/src/index.html:2890`, `geuldobi-desktop/src/main.js:380`

## 3. 목표 구조

최종 정보구조는 아래 5개 상위 surface로 고정한다.

1. `Run`
- 역할: 실행 패널, stop, 로그, 즉시 실행 관련 조작
- 포함: 재료 넣기, 상품 생산, 운영, 로그
- 기본 정책: 각 실행 섹션은 기본 접힘

2. `Office`
- 역할: 몰입형 사무실 캔버스와 핵심 HUD
- 포함: office canvas, Pipeline, Current Task, Prompt, Last Verdict, status badge
- 제외: Artifact Ladder, Retrieval, Trend, Calibration, Event Feed의 장문 분석 surface

3. `Quality`
- 역할: 분석/감리/후속행동 판단 화면
- 포함: Quality Radar, Artifact Ladder, Retrieval Inspector, Run Result Summary, Episode Trend, Failure Watch, Calibration Desk
- 기본 정책: 세로 스크롤 허용

4. `Project`
- 역할: 작품 준비 surface
- 포함: 장르, Bible/Treatment, 작가 지시사항, 작품가드, 작품 정체성 도우미
- 정책: `작품가드`를 `설정`이 아니라 `프로젝트 준비` surface로 승격

5. `Settings`
- 역할: 시스템/키/모델/앱 설정
- 포함: API 키, 시스템 슬라이더, 모델
- 정책: 모델은 실제 wiring 전에는 read-only 또는 명시적 stub 상태로 표시

## 4. 설계 원칙

### 4.1 국룰 원칙

이번 개편은 아래 국룰로 고정한다.

- 한 화면은 한 가지 주책임만 가진다.
- 캔버스/연출 surface와 분석/감리 surface를 같은 세로 축에 쌓지 않는다.
- UI에서 수정 가능한 항목은 실제 저장/적용 경로가 있어야 한다.
- 실제 저장/적용 경로가 없으면 수정 UI처럼 보이게 두지 않는다.
- 프로젝트 준비 입력은 프로젝트 surface에 모은다.
- 실행 surface와 설정 surface를 섞지 않는다.
- 기본값은 펼침보다 접힘을 우선한다.
- 장문/다카드 surface는 독립 스크롤 영역을 가진다.

### 4.2 변경 금지선

이번 구조개편에서 아래는 건드리지 않는다.

- Stage 0~4 실행 의미론
- CLI contract 번호 의미
- 브리지 API semantics
- canary/runtime audit payload schema
- 엔진 내부 생성 품질 로직

즉 이번 작업은 "UI 구조개편 + surface wiring 정리"이지, 파이프라인 정책 변경이 아니다.

## 5. 현재 구조에서 고정되는 사실

아래 사실은 이번 설계의 출발점으로 고정한다.

1. 실행 패널은 현재 `재료 넣기 / 상품 생산 / 운영` 3개 큰 카테고리로 이미 묶여 있다. `geuldobi-desktop/src/index.html:2497`
2. `사무실` 패널은 현재 단일 page 안의 거대 복합 패널이다. `geuldobi-desktop/src/index.html:2613`
3. `Artifact Ladder`는 quality dashboard payload의 일부로 이미 backend에서 제공된다. `modules/api/bridge_server.py:1164`
4. `작품가드`는 실제로 `{project}/config/work_guard.yaml`에 저장되고 backend가 읽는다. `geuldobi-desktop/src/main.js:606`, `main_a.py:1051`
5. `작가 지시사항`은 `{project}/config/author_directives.txt`로 저장되고 agent prompt에 주입된다. `geuldobi-desktop/src/main.js:606`, `modules/core/project_manager.py:110`, `modules/domain/agents/base_agent.py:558`
6. `모델` 탭은 현재 UI surface만 있고, `models.yaml` 저장/로드 wiring은 없다. `geuldobi-desktop/src/index.html:6885`, `geuldobi-desktop/src/main.js:380`

## 6. 실행 범위

### 6.1 포함

- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- 필요 시 `modules/api/bridge_server.py`
- 필요 시 `config/models.yaml` 연결면
- 필요 시 프로젝트 surface load/save IPC

### 6.2 제외

- 새로운 시각 테마 대개편
- 스프라이트/아트 교체
- 엔진의 Stage 알고리즘 수정
- full/live rerun 정책 변경

## 7. Work Package

## WP-1. 정보구조 재편

목표:
- `Run / Office / Quality / Project / Settings` 상위 구조 확정

작업:
- 단일 우측 컬럼 구조를 해체
- `Office`와 `Quality`를 분리
- `Run`과 `Project`의 경계를 명확히 분리

완료 조건:
- `Artifact Ladder`가 `Office`에서 제거된다.
- `Office` 페이지는 캔버스/HUD 중심이 된다.
- `Quality` 페이지는 장문 분석 surface를 수용한다.

## WP-2. 실행 패널 정리

목표:
- 좌측 실행 패널을 기본 접힘 구조로 바꾼다.

작업:
- `재료 넣기`, `상품 생산`, `운영` 기본 collapsed
- 마지막 열림 상태 기억 여부 결정
- `Stage 0` 진입과 `Project` 준비 surface 관계 정리

완료 조건:
- 앱 첫 진입 시 실행 패널이 전체 확장 상태가 아니다.
- 사용자가 필요한 섹션만 열어 쓰는 흐름이 된다.

## WP-3. Office surface 분리

목표:
- `사무실`을 몰입형 전용 surface로 복원한다.

작업:
- `officeCanvas`와 핵심 HUD만 남긴다.
- 필요 시 `full-height office` 전용 route/tab/view를 만든다.
- 분석 카드와 장문 리스트는 제거한다.

완료 조건:
- 사무실 높이 손실의 구조적 원인이 제거된다.
- Office 화면은 스크롤형 데이터 대시보드가 아니다.

## WP-4. Quality surface 독립

목표:
- 분석성 surface를 하나의 독립 화면으로 옮긴다.

작업:
- `Quality Radar`
- `Artifact Ladder`
- `Retrieval Inspector`
- `Run Result Summary`
- `Episode Trend`
- `Failure Watch`
- `Calibration Desk`

완료 조건:
- `Artifact Ladder` 하단 미노출 문제가 구조적으로 제거된다.
- `Quality` 화면은 세로 스크롤이 가능하다.

## WP-5. Project surface 승격

목표:
- `Bible / Treatment / 작가 지시사항 / 작품가드`를 프로젝트 준비 surface로 재배치한다.

작업:
- `재료 넣기`와 `작품가드`를 같은 준비 단계 surface에서 다루게 한다.
- 최소한 `작품가드` 진입점을 `Project` 상위 화면으로 올린다.
- `설정` 탭 안쪽에 묻어 있던 project-specific 입력을 떼어낸다.

완료 조건:
- 사용자가 `Bible/Treatment`를 넣는 흐름에서 `작품가드` 존재를 놓치지 않는다.
- project-specific surface와 app-global settings가 분리된다.

## WP-6. 모델 surface 정리

목표:
- 모델 탭의 거짓 affordance를 제거한다.

선택지는 둘 중 하나만 허용한다.

1. 실제 wiring
- `models.yaml` read/write IPC 추가
- 저장 후 앱 재기동 정책 명시

2. read-only 고정
- 현재 값 표시만 하고 수정 UI처럼 보이지 않게 변경
- "실제 설정 파일은 `config/models.yaml`" 경고 명시

완료 조건:
- 사용자가 모델을 바꿨다고 착각하는 상태가 제거된다.

내 권고:
- 이번 구조개편에서는 `read-only 고정`이 먼저다.
- 이유: 구조개편과 설정 editor 구현을 한 번에 묶으면 범위가 커진다.

## 8. 구현 순서

순서는 아래로 고정한다.

1. `WP-1` 정보구조 확정
2. `WP-3` Office 분리
3. `WP-4` Quality 독립
4. `WP-2` 실행 패널 기본 접힘
5. `WP-5` Project surface 승격
6. `WP-6` 모델 surface 정리

이 순서를 뒤집지 않는다.

이유:
- `사무실`과 `Artifact Ladder` 문제는 구조를 나누기 전엔 임시응급처치밖에 안 된다.
- 모델/작품가드 문제는 surface 재배치 후 손대는 편이 더 적은 수정으로 끝난다.

## 9. 수용 기준

아래를 만족해야 구조개편 완료로 본다.

1. `Office` 화면에 `Artifact Ladder`가 없다.
2. `Quality` 화면에서 `Artifact Ladder` 전체가 스크롤로 접근 가능하다.
3. `Run` 화면의 각 실행 카테고리는 기본 접힘이다.
4. `작품가드`는 `Project` 준비 surface에서 보인다.
5. `모델` 화면은 실제 저장되거나, 아니면 read-only로 명확히 표시된다.
6. `Run`/`Office`/`Quality`/`Project`/`Settings` 역할이 문서와 코드에서 일치한다.

## 10. 검증 시나리오

### 구조 검증

- 첫 진입 시 `Run` 화면에서 실행 카테고리가 기본 접힘인지
- `Office` 진입 시 캔버스와 핵심 HUD가 주 화면인지
- `Quality` 진입 시 `Artifact Ladder` 전체 접근이 가능한지
- `Project` 진입 시 `Bible`, `Treatment`, `작가 지시사항`, `작품가드`를 같은 흐름에서 볼 수 있는지

### 계약 검증

- `author_directives.txt` 저장/로드가 그대로 유지되는지
- `work_guard.yaml` 저장/로드가 그대로 유지되는지
- backend의 quality dashboard payload 구조를 UI 분리 후에도 그대로 소비하는지
- run/stop/status/WebSocket 흐름이 surface 분리 후에도 유지되는지

### 오해 방지 검증

- 모델 탭에서 수정 가능한 UI가 실제 반영 없이 남아 있지 않은지
- `작품가드`가 여전히 `설정 구석`에 묻혀 있지 않은지

## 11. 비목표

이번 SSOT는 아래를 목표로 하지 않는다.

- 디자인 테마 리뉴얼
- 애니메이션 품질 상향
- 아트 리소스 전면 교체
- 모바일 반응형 우선 대응
- 엔진 실행 로직 리디자인

## 12. 리스크와 판단

### 리스크 1. 단일 파일 거대 renderer

- 현재 `index.html`이 크고 책임이 과다하다.
- 그래서 페이지 분리는 DOM/CSS/JS 관심사 분리를 같이 요구할 가능성이 높다.

판단:
- 구조개편 자체는 필요하다.
- 다만 구현 시 `route/tab abstraction` 또는 section renderer 분할을 병행하는 편이 안전하다.

### 리스크 2. 모델 탭 범위 팽창

- `models.yaml` 편집기 구현까지 들어가면 이번 작업이 설정 인프라 개편으로 커진다.

판단:
- 먼저 read-only 정리로 닫고, 후속 문서로 분리하는 편이 맞다.

### 리스크 3. Project surface와 Run surface 경계

- `Bible/Treatment`는 준비 surface이면서 실행 전제조건이다.

판단:
- `Run` 안에 재료 import가 남아 있더라도, 최소한 `Project`에서 같은 데이터를 다룰 수 있어야 한다.
- 최종적으로는 `Project`를 준비 SSOT로 두고, `Run`은 실행만 담당하는 쪽이 더 건강하다.

## 13. 참고 문서

- `docs/2026-03-12/ui-feedback-response-survey.md`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`
- `docs/2026-03-12/today-code-health-ui-build-roadmap.md`

## 14. 최종 결론

이번 UI 구조개편은 `스크롤 조금 추가`, `접기 버튼 몇 개 추가`로 닫지 않는다.

정답은 아래로 고정한다.

- `사무실`은 별도 surface로 분리
- `Quality`는 독립 분석 surface로 분리
- `Project`는 준비 surface로 승격
- `Run`은 실행만 담당
- `Settings`는 앱 전역 설정만 담당
- `모델`은 실제 wiring 전까지 read-only 또는 명시적 stub 처리

즉 이번 구조개편의 본질은 미관 수정보다 `정보구조 재편과 계약 정리`다.
