# 글도비 데스크톱 — 개발·빌드·배포 가이드

> 비개발자도 설치할 수 있는 Windows 데스크톱 앱.
> Python 설치 불필요 — 전체 바이너리로 배포. 소스 코드 비공개.

---

## 1. 전체 구조 한눈에 보기

```
사용자가 설치한 앱/
├── Geuldobi.exe                ← Electron (UI 담당)
└── resources/
    ├── backend/
    │   └── backend.exe         ← FastAPI 서버 (PyInstaller)
    └── engine/
        └── engine.exe          ← 글도비 파이프라인 (PyInstaller, 소스 비공개)
```

**역할 분담:**
| 구성요소 | 뭘 하나 | 기술 |
|----------|---------|------|
| `Geuldobi.exe` | 창 띄우고, 버튼 누르면 백엔드에 명령 보냄 | Electron |
| `backend.exe` | HTTP/WebSocket 서버. UI 명령 받아서 engine.exe 실행 | FastAPI + PyInstaller |
| `engine.exe` | 글도비 파이프라인 바이너리 (main_a.py + modules + config 번들) | PyInstaller |

**앱 실행 흐름:**
```
1. 사용자가 Geuldobi.exe 더블클릭
2. Electron이 backend.exe를 자동 실행 (백그라운드)
3. Splash 화면이 "준비 중..." 표시
4. backend.exe가 준비되면 → 메인 화면 전환
5. 사용자가 "Stage 4 실행" 버튼 클릭
6. backend.exe가 python.exe로 main_a.py 실행
7. 실시간 로그가 WebSocket으로 UI에 표시
8. 완료되면 결과 표시
```

---

## 2. 개발 모드 (지금 쓰는 방식)

### 사전 요구사항

- **Node.js 18+** — [nodejs.org](https://nodejs.org) 에서 LTS 설치
- **Python 3.10+** — 이미 설치되어 있음
- pip 패키지: `pip install fastapi uvicorn websockets`

### 실행

```bash
cd geuldobi-desktop
npm start
```

이러면:
- Electron이 뜨면서 `python -m uvicorn`을 직접 실행함
- Python이 시스템에 깔려있어야 동작함
- 개발할 때만 이렇게 씀

### 개발 모드에서 확인할 것

| 확인 항목 | 어떻게 |
|-----------|--------|
| Splash → Main 전환 | 앱 켜면 3초 내 메인 화면으로 넘어가야 함 |
| 로그 패널 | 하단에 실시간 로그가 찍혀야 함 |
| 설정 저장/로드 | 설정 모달에서 API 키 입력 → 저장 → 앱 재시작 → 키가 남아있어야 함 |
| Stage 실행 | Run 버튼 누르면 하단 로그에 main_a.py 출력이 나와야 함 |

---

## 3. 릴리스 빌드 (배포용 .exe 만들기)

### 사전 요구사항 (빌드 머신에만 필요)

```bash
# 1. PyInstaller 설치
pip install pyinstaller

# 2. Electron Builder 설치 (이미 package.json에 있음)
cd geuldobi-desktop
npm install
```

### 빌드 실행

```powershell
cd build
powershell -ExecutionPolicy Bypass -File build_release.ps1
```

**이 한 줄이 자동으로 하는 것:**

| 단계 | 뭘 하나 | 결과물 |
|------|---------|--------|
| Step 1 | 내장 Python 다운로드 + pip 패키지 설치 | `python-embed/` 폴더 |
| Step 2 | bridge_server를 PyInstaller로 빌드 | `dist/backend/backend.exe` |
| Step 3 | Electron Builder로 설치 파일 생성 | `geuldobi-desktop/dist/Geuldobi Setup 1.0.0.exe` |

### 빌드 결과물

```
geuldobi-desktop/dist/
└── Geuldobi Setup 1.0.0.exe    ← 이걸 사용자에게 주면 됨 (~300MB)
```

### 첫 빌드 시 시간

| 단계 | 소요 시간 | 비고 |
|------|-----------|------|
| 내장 Python 다운로드 | 1~2분 | 캐시됨 (2회차부터 스킵) |
| pip 패키지 설치 | 2~5분 | numpy, google-genai 등 |
| PyInstaller | 1~3분 | |
| Electron Builder | 2~5분 | |
| **합계** | **~15분** | 2회차부터 ~5분 |

---

## 4. 사용자에게 전달하기

### 사용자가 할 일

1. `Geuldobi Setup 1.0.0.exe` 더블클릭
2. 설치 경로 선택 (기본값 OK)
3. 설치 완료 → 바탕화면 아이콘 클릭
4. 첫 실행 시 설정에서 Gemini API 키 입력

### 사용자가 안 해도 되는 것

- ~~Python 설치~~ → 내장됨
- ~~pip install~~ → 내장됨
- ~~터미널 열기~~ → 필요 없음
- ~~코드 수정~~ → 필요 없음

### 사용자 데이터 위치

```
내 문서\글도비\                ← 작업 폴더 (앱에서 "작업 폴더" 버튼으로 바로 열기 가능)
├── bible\                    ← Bible 파일
├── treatments\               ← Treatment 파일
└── projects\                 ← 프로젝트별 데이터 (DB, 원고 등)

%LOCALAPPDATA%\Geuldobi\      ← 앱 설정 (숨김 경로, 사용자가 직접 건드릴 필요 없음)
├── settings.json             ← API 키, 설정 등
└── .first_run                ← 최초 실행 마커
```

작업물은 **내 문서\글도비** 폴더에 저장됨 — 탐색기에서 바로 찾을 수 있음.
앱 상단 "작업 폴더" 버튼을 누르면 탐색기가 해당 폴더를 바로 열어줌.

---

## 5. 파일별 역할 설명

### Electron 쪽 (UI)

```
geuldobi-desktop/
├── src/
│   ├── main.js          ← Electron 메인 프로세스 (창 관리, 백엔드 기동/종료)
│   ├── preload.js       ← 보안 브릿지 (renderer ↔ main 통신 채널 정의)
│   ├── index.html       ← 메인 UI (캔버스 애니메이션 + 로그 패널 + 설정 모달)
│   └── splash/
│       ├── splash.html  ← 스플래시 화면
│       ├── splash.js    ← 백엔드 준비 감지 (1초마다 /status 폴링)
│       └── splash.css   ← 스플래시 스타일
└── package.json         ← 의존성 + electron-builder 빌드 설정
```

### Python 백엔드 쪽 (API)

```
modules/api/
├── bridge_server.py     ← FastAPI 앱 (POST /run, /stop, GET /status, WS /events)
├── process_runner.py    ← main_a.py subprocess 관리 (시작/종료/stdout 수집)
├── run_validator.py     ← 실행 요청 검증 (허용 키, 상태 체크)
└── risk_approval.py     ← 위험 작업 승인 게이트 (리셋/롤백 등)
```

### 빌드 쪽

```
build/
├── backend_entry.py         ← PyInstaller 진입점 (frozen 모드 환경변수 설정)
├── backend.spec             ← PyInstaller 빌드 설정
├── prepare_python_embed.ps1 ← 내장 Python 자동 준비 스크립트
└── build_release.ps1        ← 마스터 빌드 스크립트 (전체 자동화)
```

---

## 6. 통신 구조

```
┌─────────────────────────────────────────────────┐
│  Electron (Geuldobi.exe)                        │
│                                                 │
│  ┌──────────┐  IPC   ┌──────────┐               │
│  │ index.html│◄─────►│ main.js  │               │
│  │ (renderer)│       │ (main)   │               │
│  └────┬─────┘       └──────────┘               │
│       │                                         │
│       │ WebSocket (ws://127.0.0.1:8300/events)  │
│       ▼                                         │
└───────┼─────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  backend.exe (FastAPI)                │
│  POST /run  → ProcessRunner.start()  │
│  POST /stop → ProcessRunner.stop()   │
│  GET /status                         │
│  WS /events → 실시간 stdout 전송     │
└───────┬───────────────────────────────┘
        │ subprocess (stdin pre-feed)
        ▼
┌───────────────────────────────────────┐
│  python.exe main_a.py                 │
│  (내장 Python으로 파이프라인 실행)    │
│  stdout → backend → WS → UI 로그     │
└───────────────────────────────────────┘
```

**포트:** `8300` (고정, localhost 전용)

**통신 방식:**
- **UI → 백엔드**: HTTP (main.js가 fetch로 중계)
- **백엔드 → UI**: WebSocket (실시간 로그 스트리밍)
- **백엔드 → main_a.py**: subprocess stdin/stdout

---

## 7. 개발 vs 배포 모드 차이

| 항목 | 개발 모드 (`npm start`) | 배포 모드 (설치된 .exe) |
|------|------------------------|------------------------|
| 백엔드 실행 | `python -m uvicorn ...` | `backend.exe` |
| main_a.py 실행 | 시스템 Python | 내장 `python-embed/python.exe` |
| 판별 기준 | `app.isPackaged === false` | `app.isPackaged === true` |
| 설정 저장 | `%LOCALAPPDATA%/Geuldobi/` | 동일 |
| 코드 위치 | 프로젝트 폴더 그대로 | `resources/engine/` |

**`main.js`가 자동으로 판별** — 코드 변경 없이 두 모드 모두 동작.

---

## 8. 원격 패치 (나중에)

electron-builder 기반이므로 `electron-updater` 추가만 하면 됨:

```bash
cd geuldobi-desktop
npm install electron-updater
```

`main.js`에 추가:
```javascript
const { autoUpdater } = require("electron-updater");

app.whenReady().then(() => {
  autoUpdater.checkForUpdatesAndNotify();
  // ... 기존 코드
});
```

**패치 대상별 전략:**

| 패치 대상 | 방법 | 재시작 필요 |
|-----------|------|------------|
| UI (index.html) | electron-updater (전체 업데이트) | O |
| engine/ (Python 코드) | engine/ 폴더만 교체 (부분 패치) | O (백엔드 재기동) |
| backend.exe | electron-updater (전체 업데이트) | O |
| 설정/프롬프트 YAML | engine/config/ 교체 | O |

---

## 9. 트러블슈팅

### "백엔드 미감지 — 오프라인 모드" 로그가 뜸

- **개발 모드**: Python에 `fastapi`, `uvicorn` 설치 확인 → `pip install fastapi uvicorn websockets`
- **배포 모드**: `resources/backend/backend.exe`가 있는지 확인
- 포트 8300이 다른 프로그램에 점유됐는지 확인 → `netstat -ano | findstr 8300`

### 빌드가 실패함

```
# PyInstaller 실패 시
pip install --upgrade pyinstaller

# Electron Builder 실패 시
cd geuldobi-desktop
rm -rf node_modules
npm install
```

### 앱은 뜨는데 Stage 실행이 안 됨

- 설정에서 Gemini API 키가 입력됐는지 확인
- `resources/engine/main_a.py`가 있는지 확인
- 내장 Python 경로 확인: `resources/python-embed/python.exe`

### 설정이 저장 안 됨

- `%LOCALAPPDATA%\Geuldobi\` 폴더 쓰기 권한 확인
- 앱을 관리자 권한으로 실행해볼 것

---

## 10. 버전 올리기

`package.json`의 `version` 필드를 수정하면 설치 파일 이름에 반영됨:

```json
"version": "1.0.1"
```

→ `Geuldobi Setup 1.0.1.exe` 생성

빌드 후 해당 .exe를 사용자에게 전달하거나, 나중에 auto-update 서버에 올리면 됨.
