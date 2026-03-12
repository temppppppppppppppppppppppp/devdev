# UI 시스템 전수 조사

작성일: 2026-03-09
기준: 현재 저장소 실측 코드 기준
인코딩 전제: UTF-8

## 1. 요약

이 저장소의 UI는 단일 계층이 아니다. 현재 실사용 또는 유지 대상 UI는 아래 6종으로 나뉜다.

1. `main_a.py` 기반 CLI/TUI
2. `geuldobi-desktop/` 기반 Electron 데스크톱 UI
3. `modules/api/` 기반 FastAPI 브리지 UI 백엔드
4. `tools2/` 기반 Streamlit 보조 대시보드
5. `test_mode/` + `lite_mode/` 기반 Selenium 브리지형 대체 UI
6. `UI/` 폴더의 그래픽/에셋 저장소

실제 운영 주 UI는 현재 `CLI/TUI + Electron 데스크톱 + FastAPI 브리지` 조합이다. 반면 `tools2`는 독립 운영용 보조 대시보드이고, `lite_mode`는 내부 파이프라인 UI가 아니라 외부 Gemini 웹 UI를 자동화하는 별도 실행계다. `UI/` 폴더는 코드가 아니라 아트 자산 저장소다.

## 2. UI 계층 인벤토리

| 계층 | 상태 | 진입점 | 역할 |
|------|------|--------|------|
| CLI/TUI | 운영 중 | `main_a.py` | 장르 선택, 프로젝트 선택, 메인 메뉴, Stage 실행 |
| Desktop Renderer | 운영 중 | `geuldobi-desktop/src/index.html` | 버튼 기반 실행 패널, 설정/프로젝트/재료 관리, 로그 표시 |
| Desktop Main Process | 운영 중 | `geuldobi-desktop/src/main.js` | Electron 창 관리, backend 자동 기동, IPC 중계 |
| API Bridge | 운영 중 | `modules/api/bridge_server.py` | `/run`, `/stop`, `/status`, `/events`, 프롬프트 응답 |
| Streamlit Dashboards | 보조 도구 | `tools2/*.py` | Arc/성능/스튜디오 시각화 |
| Lite Selenium UI | 별도 시스템 | `test_mode/main_lite.py`, `lite_mode/bridge/*` | 외부 Gemini 웹 UI 자동화 |
| `UI/` 폴더 | 자산 저장소 | 폴더 자체 | 런타임 UI 코드 없음 |

## 3. 1차 UI: CLI/TUI

### 3.1 진입 구조

- 메인 진입점: `main_a.py`
- 표시/로그 렌더러: `modules/core/studio_visualizer.py`
- 입력 보조 서비스: `modules/core/services/ui_service.py`
- Stage 0/1 서브메뉴 캡슐화: `modules/core/stage01_helpers.py`
- 스피너/진행 표시: `modules/core/spinners.py`, `modules/core/stage0/spinner.py`

### 3.2 사용자 흐름

1. 장르 선택
2. 프로젝트 선택
3. 메인 메뉴 표시
4. Stage 0 / 1 / 2 / 3 / 4 / One-Stop / 운영 메뉴 실행

`main_a.py` 메인 메뉴 키는 다음과 같다.

- `0`: Stage 0
- `1`: Stage 1
- `2`: Stage 2
- `3`: Stage 3
- `4`: Stage 4
- `5`: Exit
- `6`: One-Stop
- `44`: Rollback
- `77`: Wipe
- `88`: Reset
- `99`: Rewind

### 3.3 표시 방식

- `StudioVisualizer.title()`는 상단 타이틀 패널을 그림
- `StudioVisualizer.menu()`는 메뉴 번호 선택 UI를 그림
- `StudioVisualizer.log()`는 콘솔 출력과 `UI` 로거 기록을 동시에 수행
- `UIService.get_int_input()`은 숫자 입력 검증을 담당
- `StageSpinner`/`FancySpinner`가 Rich Live 기반 진행 UI를 담당

### 3.4 특징

- CLI는 여전히 엔진의 기준 UI다.
- 데스크톱 앱도 결국 `main_a.py`를 subprocess로 구동한다.
- 입력은 대부분 `input()` 기반이며, 브리지 계층이 이를 감지해 GUI 프롬프트로 변환한다.

## 4. 2차 UI: Electron 데스크톱

### 4.1 구성

- 메인 프로세스: `geuldobi-desktop/src/main.js`
- 보안 브리지: `geuldobi-desktop/src/preload.js`
- 렌더러 UI: `geuldobi-desktop/src/index.html`
- 스플래시: `geuldobi-desktop/src/splash/splash.html`, `splash.js`, `splash.css`
- 빌드 설정: `geuldobi-desktop/package.json`

### 4.2 창 구조

- Splash Window
  - backend `/status`를 1초 간격으로 폴링
  - 상태가 `idle`이면 메인 윈도우로 전환
- Main Window
  - 상단 프로젝트/설정 바
  - 좌측 실행 패널
  - 우측 사무실 캔버스 + 로그 패널

### 4.3 렌더러 주요 UI 블록

#### 상단 바

- 프로젝트 선택 드롭다운
- 새 프로젝트 버튼
- 작업 폴더 열기 버튼
- 설정 버튼

#### 실행 패널

카테고리형 아코디언 구조다.

- 재료 넣기
  - Bible 파일 목록/추가/삭제/새로고침
  - Treatment 파일 목록/추가/삭제/새로고침
- 상품 생산
  - 장르설정
  - Stage 0 토글 + Stage 0 서브메뉴
  - Arc 설계
  - Blueprint
  - 원고 생산
  - One-Stop
- 운영
  - Rollback
  - Wipe
  - Reset
  - Rewind
  - Stop

#### 우측 패널

- 사무실 캔버스
  - 에이전트 스프라이트 및 상태 연출
- 상태 배지
  - 준비 상태
  - RUNNING/PASS/REJECT 표시
- 로그 패널
  - 검색
  - PASS/REJECT 필터
  - 실시간 stdout/event 표시

#### 모달/오버레이

- 설정 사이드 패널
- 장르 선택 모달
- 비투자물 경고 확인 모달
- 새 프로젝트 생성 모달
- Mode B 프롬프트 다이얼로그

### 4.4 설정 탭 구조

- API 키
  - Key 1 필수
  - 추가 Key 2~9
  - Slack Webhook
- 모델
  - CW/Director/Analyst 드롭다운
- 프로젝트
  - 현재 장르
  - 작가 지시사항 textarea
  - 작품 가드 YAML textarea
- 시스템
  - 타임아웃
  - 키 순환 간격
  - 품질 게이트 점수
  - 원고 목표 길이
  - Skip/Mute

### 4.5 데스크톱 실행 흐름

1. Electron이 backend를 자동 기동
2. Splash가 `/status` 폴링
3. backend 준비 시 메인 화면 전환
4. 렌더러가 WebSocket `ws://127.0.0.1:8300/events` 연결
5. 사용자가 버튼 클릭
6. `preload.js` → `main.js` IPC → FastAPI `/run`
7. backend가 `main_a.py` 실행
8. stdout/event가 WebSocket으로 렌더러 로그에 반영
9. 프롬프트가 감지되면 prompt dialog로 응답

## 5. 3차 UI: FastAPI 브리지

### 5.1 목적

`modules/api/bridge_server.py`는 GUI가 엔진을 직접 다루지 않고 HTTP/WS로 실행하도록 만든 중간 계층이다.

### 5.2 엔드포인트

- `POST /run`
- `POST /stop`
- `GET /status`
- `WS /events`
- `POST /run/{run_id}/input`

### 5.3 내부 책임 분해

- `bridge_server.py`
  - 요청 수신
  - WS 브로드캐스트
  - PromptBroker 연결
- `process_runner.py`
  - `main_a.py` 또는 `engine.exe` subprocess 실행
  - stdout/stderr 수집
  - stdin prefeed / 실시간 응답 전달
- `run_validator.py`
  - 허용 key/sub_key 검증
- `risk_approval.py`
  - 위험 키 승인 정책
- `prompt_classifier.py`
  - CLI 프롬프트를 구조화된 입력 타입으로 변환
- `prompt_broker.py`
  - pending prompt 생명주기 관리

### 5.4 Mode A / Mode B

- Mode A
  - stdin을 실행 전에 한 번에 주입
  - 단순/예측 가능한 메뉴 실행에 적합
- Mode B
  - stdin을 열어 둔 채 stdout 프롬프트를 감지
  - GUI 다이얼로그로 사용자 응답을 받아 다시 stdin으로 전달

현재 브리지 키는 사실상 전부 Mode B 대상이다.

## 6. 4차 UI: Streamlit 보조 대시보드

### 6.1 파일

- `tools2/arc_dashboard.py`
- `tools2/performance_dashboard.py`
- `tools2/studio_dashboard.py`

### 6.2 역할

- Arc 편집/시각화
- 승인/거절 데이터 기반 성능 모니터링
- 프로젝트 상태 조회용 스튜디오형 대시보드

### 6.3 상태

- Electron/CLI 주 경로와 통합되어 있지 않다.
- 독립 실행형 도구다.
- 운영 보조 또는 내부 분석용 성격이 강하다.

## 7. 5차 UI: Lite / Selenium 브리지

### 7.1 진입점

- `test_mode/main_lite.py`
- `lite_mode/bridge/runner.py`
- `lite_mode/bridge/gemini_driver.py`
- `lite_mode/bridge/ui_discovery.py`

### 7.2 성격

이 계층은 글도비 내부 UI가 아니라, 외부 `gemini.google.com` 웹 UI를 Selenium으로 자동화하는 별도 시스템이다.

### 7.3 특징

- Chrome remote debugging 전제
- API 키 없이 Gemini 웹 UI 자동화
- `UIDiscovery`가 DOM을 분석해 셀렉터를 추적
- 외부 웹 UI 변경에 영향을 크게 받음

운영 UI 조사 문서에는 포함하되, 주 시스템 UI와는 분리해 보는 것이 맞다.

## 8. `UI/` 폴더 실체

`UI/` 폴더에는 `.html`, `.js`, `.css`, `.py` 실행 코드가 없었다.

포함물은 다음 성격이다.

- 캐릭터/인테리어 스프라이트
- RPG Maker 계열 타일셋
- 압축본/설치본 에셋

즉, 이 폴더는 런타임 UI 모듈이 아니라 아트 자산 저장소다.

## 9. 사용자 입력 지점 정리

### 9.1 CLI 직접 입력

- 장르 선택
- 프로젝트 선택
- 메인 메뉴 키
- Stage 0 서브메뉴
- 확인/취소
- 숫자 범위 입력
- 개행 종료 멀티라인 입력

### 9.2 데스크톱에서 흡수한 입력

- 장르 모달
- 프로젝트 드롭다운
- 새 프로젝트 모달
- 설정 패널
- Mode B 프롬프트 다이얼로그

### 9.3 데스크톱에서 아직 엔진에 실배선되지 않은 입력

코드 실측 기준, 아래 항목은 UI에는 존재하지만 엔진 파일/실행 설정으로 연결되지 않았다.

- 모델 탭의 `chief_writer/director/analyst` 선택값
- 프로젝트 탭의 `authorDirectives`
- 프로젝트 탭의 `workGuardYaml`
- 시스템 탭의 `qualityGate`
- 시스템 탭의 `targetLength`

이 값들은 현재 `AppData`의 `settings.json`에만 저장되거나, UI 메모리 상태로만 남고 실제 `config/models.yaml`, `{project}/config/author_directives.txt`, `{project}/work_guard.yaml`, 엔진 런타임 설정으로 쓰이지 않는다.

## 10. 구현-표시 괴리

### 10.1 README와 실구현 불일치

`README.md`는 현재도 다음처럼 적고 있다.

- 인터페이스: CLI 전용 (웹 UI 없음)

하지만 실제 저장소에는 아래가 이미 존재한다.

- Electron 데스크톱 UI
- FastAPI 브리지
- WebSocket 이벤트 스트림
- Streamlit 보조 대시보드

즉 README의 인터페이스 설명은 최신 상태가 아니다.

### 10.2 데스크톱 설정 문구와 실제 저장 경로 불일치

데스크톱 설정 UI는 다음 저장 위치를 안내한다.

- `config/models.yaml`
- `{project}/config/author_directives.txt`
- `{project}/work_guard.yaml`

그러나 현재 구현은 `geuldobi-desktop/src/main.js`의 `SETTINGS_PATH` 즉 `%LOCALAPPDATA%/Geuldobi/settings.json`에만 저장한다. 개별 목표 파일로 write-through 하지 않는다.

### 10.3 장르 지속성 정책

장르는 저장은 하지만 앱 재시작 시 다시 로드하지 않는다. 코드에 "잘못된 장르로 작업 방지" 주석과 함께 intentionally disabled 되어 있다.

결과:

- 프로젝트는 복원됨
- 장르는 매번 다시 설정해야 함

이것은 의도된 안전장치이지만 UX 관점에서는 혼란 지점이다.

### 10.4 위험 작업 승인 정책의 UI 우회

`bridge_server.py`는 데스크톱 모드(`GEULDOBI_DESKTOP_MODE=1`)일 때 위험 키 `44/77/88/99`에 대해 `approval_id` 없이 자동 승인한다.

즉 현재 데스크톱 UI의 파괴적 작업 확인은 이중 승인 체계가 아니라 단순 confirm 창이다.

### 10.5 Stage 0 기능 가용성 차이

CLI의 Stage 0은 다음을 실제 제공한다.

- 컨셉 → Bible 생성
- 역설계
- Bible JSON 임포트
- Block 확장
- 스타일 레퍼런스 분석

반면 데스크톱 UI는 `2~5`를 "(개선 중)"으로 표시하고 경고 confirm 뒤 실행시키는 구조다. 즉 엔진 기능과 GUI 표현이 완전히 일치하지 않는다.

## 11. 유지보수 관점 분류

### A. 운영 핵심 UI

- `main_a.py`
- `modules/core/studio_visualizer.py`
- `modules/core/services/ui_service.py`
- `modules/core/stage01_helpers.py`
- `modules/api/*`
- `geuldobi-desktop/src/*`

### B. 운영 보조 UI

- `tools2/arc_dashboard.py`
- `tools2/performance_dashboard.py`
- `tools2/studio_dashboard.py`

### C. 별도 실험/대체 UI

- `test_mode/main_lite.py`
- `lite_mode/bridge/*`

### D. 비코드 자산

- `UI/`

## 12. 권장 문서 SSOT

UI 문서의 기준점은 아래 순서로 잡는 것이 맞다.

1. 엔진 입력/출력 진실원천: `main_a.py`
2. GUI 실행 계약: `modules/api/bridge_server.py`, `process_runner.py`
3. 데스크톱 실제 UI: `geuldobi-desktop/src/index.html`, `main.js`, `preload.js`
4. 보조 대시보드: `tools2/*.py`

즉 앞으로 UI 관련 문서를 갱신할 때는 `README`보다 위 4개 계층을 우선 확인해야 한다.

## 13. 우선 정리 과제

### P0

- README의 "CLI 전용" 문구 교정
- 데스크톱 설정 패널에서 실제 반영되지 않는 항목에 "미연결" 표시 추가 또는 배선 구현
- 위험 작업 승인 정책을 UI confirm 수준인지, 실제 dual-control인지 명확히 문서화

### P1

- 데스크톱에서 장르/프로젝트/Stage 0 기능 가용성 매트릭스를 문서와 일치시키기
- `tools2` 대시보드를 운영 문서에서 "보조 도구"로 명시
- `UI/` 폴더를 런타임 UI와 자산 저장소로 구분 표기

### P2

- 데스크톱 설정의 project-level 파일 편집 기능 실배선
- Mode B 프롬프트 유형/옵션 매핑표 별도 문서화
- Lite Selenium 계층을 내부 운영 문서에서 별도 부록으로 분리

## 14. 결론

현재 시스템은 겉보기보다 UI 층이 많다. 하지만 엔진의 진짜 입력 원천은 아직 `main_a.py`이며, 데스크톱 앱은 이를 감싼 orchestrated shell이다. 유지보수 우선순위는 Electron 화면 자체보다도, `CLI ↔ FastAPI ↔ Electron` 간 계약 불일치와 "표시만 되고 실제 반영되지 않는 설정"을 정리하는 쪽에 두는 것이 맞다.

## 15. 추가 감리 및 개선 반영

### 15.1 추가 전수 조사 범위

이번 추가 감리는 `geuldobi-desktop/src/index.html`의 데스크톱 렌더러를 중심으로 다시 수행했다.

- 사무실 캔버스 렌더링 루프
- WebSocket 이벤트 수신부
- stdout → 로그 → 말풍선 연결부
- 상태 배지/효과 배너/최근 클릭 표시부
- `geuldobi-desktop/src/sprites/*` 및 `UI/char_preview/*` 자산 확인
- `docs/2026-03-05/codex-ui-webgal-light-proposal.md`의 pixel-agents/Office Chic 가이드 대조

### 15.2 추가 감리에서 확인한 품질 갭

기존 데스크톱 UI는 "실행은 되지만 현재 무슨 일이 벌어지는지 직관적으로 읽기 어렵다"는 문제가 명확했다.

- 캔버스가 단순 상태 연출 위주라 현재 단계, 현재 작업, 입력 대기 상태를 한눈에 읽기 어려움
- 로그와 말풍선 연결이 사실상 `Manager`/`Director` 일부 패턴에만 국한됨
- `Writer`/`Analyst`/`Critic`는 살아 있는 에이전트처럼 보이기보다 장식에 가까움
- 픽셀 오피스 배경 중앙 화이트보드가 비어 있어 상태 전달에 쓰이지 않음
- 로그 패널이 plain text 위주라 어떤 에이전트/단계에서 나온 로그인지 빠르게 식별하기 어려움

### 15.3 자산/레퍼런스 확인 결과

- 현재 런타임은 `geuldobi-desktop/src/sprites/*.png`의 pixel sprite를 직접 사용 중이다.
- `UI/char_preview/matched_3pose.png` 기준, `walk/sit` 조합은 런타임 품질 개선에 재활용 가능하다고 판단했다.
- `docs/2026-03-05/codex-ui-webgal-light-proposal.md`에 적힌 Office Chic 원칙과 pixel-agents 레퍼런스 방향은 현 구조와 충돌하지 않는다.
- 따라서 이번 개선은 새 프레임워크 도입이 아니라, 기존 캔버스/로그/스프라이트 상태 머신을 강화하는 쪽이 맞다.

### 15.4 이번 패치에 실제 반영한 개선

반영 파일: `geuldobi-desktop/src/index.html`

- 사무실 패널 하단에 미션 카드 4종 추가
  - 현재 파이프라인
  - 현재 작업
  - 프롬프트 대기 상태
  - 최근 Director 판정
- 파이프라인 스트립 추가
  - `Stage 0 → Stage 2 → Stage 3 → Stage 4 → One-Stop` 진행 위치 시각화
- 에이전트 상태 보드 추가
  - 각 에이전트의 역할, 현재 상태, 마지막 발화를 별도 카드로 표시
- 실시간 이벤트 피드 추가
  - 로그 전체와 별도로 "중요 이벤트 요약"만 추려서 표시
- 로그 패널 메타 강화
  - 에이전트 칩
  - 스테이지 칩
  - verdict 배지
- stdout 라우팅 확장
  - `Writer`, `Analyst`, `Critic`, `Manager`, `Director` 모두 로그 패턴에 따라 상태/말풍선 갱신
- 프롬프트 상태 연결
  - Mode B 입력 대기 시 HUD와 말풍선, 이벤트 피드에 동시에 반영
- 캔버스 연출 강화
  - 중앙 화이트보드를 live status board로 사용
  - active agent → wall board → Director 방향의 pixel data flow 추가
  - desk monitor glow 추가
  - 에이전트별 `sit/walk` 중심 pose 분기 추가

### 15.5 3-pass 감리 결과

#### Pass 1. 상태 전달성

점검 기준:

- 현재 단계가 텍스트 없이도 읽히는가
- 입력 대기/실행 중/판정 상태가 서로 구분되는가
- 로그와 사무실 오브젝트가 같은 사건을 가리키는가

조치:

- 미션 카드/파이프라인 스트립/프롬프트 상태 카드 추가
- 로그 메타 칩과 이벤트 피드 추가

결과:

- 기존 대비 "지금 뭐 하는 중인지" 해석 비용이 크게 줄었다고 판단

#### Pass 2. 에이전트 가시성

점검 기준:

- `Writer/Analyst/Critic`가 실제 작업 주체처럼 보이는가
- 말풍선이 특정 에이전트와 연결되는가
- 오피스 애니메이션이 정보 전달을 방해하지 않는가

조치:

- 5개 에이전트 전부 상태/버블/역할 카드 연결
- `walk/sit` pose 분기와 화면 glow, data flow 추가

결과:

- "장식용 픽셀 캐릭터" 느낌이 줄고, 작업자 패널 느낌이 강화됨

#### Pass 3. 회귀/안정성

점검 기준:

- 기존 Mode B 프롬프트 흐름이 유지되는가
- 로그 필터/검색이 계속 동작하는가
- 렌더러 JS가 문법적으로 깨지지 않는가

조치:

- 로그 DOM 변경 후 검색 대상을 전체 row text로 확장
- 프롬프트 open/resolve/timeout마다 상태 동기화 추가
- 별도 문법 파싱 검증 수행

결과:

- 치명 회귀는 확인하지 못했고, 남은 리스크는 "실기동 시 애니메이션 체감 튜닝" 정도로 축소됨

### 15.6 잔여 리스크

- 현재 에이전트 라우팅은 stdout 패턴 기반이므로, 로그 문구가 크게 바뀌면 일부 버블 연결 품질이 떨어질 수 있다.
- 데스크톱 UI에는 여전히 엔진에 실배선되지 않은 설정 항목이 존재한다.
- 오피스 캔버스는 여전히 단일 HTML 파일 내 inline script 구조라, 이후 분리 리팩터링 여지는 남아 있다.
