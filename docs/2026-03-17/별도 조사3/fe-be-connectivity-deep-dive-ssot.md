# FE-BE 연결성 전면 딥다이브 — 통합 SSOT

> 작성일: 2026-03-17
> 범위: Electron Desktop ↔ FastAPI Bridge 전구간
> 코드 변경: 없음 (문서 전용)

---

## 1. 목적

프론트엔드(Electron)와 백엔드(FastAPI)의 **폴더 트리가 다르게 보인다**는 우려에서 출발한 전면 조사.
기존 계약 문서 6건(api-contract-v1.yaml, event-schema-v1.json, desktop-ipc-surface-contract-v1.json, desktop-runtime-contract-v1.json, prompt-map-v1.json, control_plane_contract.py)을 **관통하는 단일 정합성 검증 문서**로서 기능한다.

---

## 2. 핵심 발견 요약

### 발견 1 — 폴더 트리 차이는 의도적 2중 루트 설계

| 모드 | Engine Root | Workspace Root |
|------|------------|----------------|
| 개발 | `Desktop/글도비/` (repo root) | 동일 |
| 배포 | `{resourcesPath}/engine/` (읽기 전용) | `{Documents}/글도비/` (사용자 쓰기) |

환경변수 4개(`GEULDOBI_DESKTOP_MODE`, `GEULDOBI_PACKAGED_RUNTIME_MODEL`, `GEULDOBI_WORKSPACE`, `GEULDOBI_PROJECTS_ROOT`)로 브리지.

### 발견 2 — 옵션 전달은 정상

- 장르맵 10개: FE `CLI_CONTRACT.genreIndexMap` ↔ BE `_GENRE_INDEX_TO_TYPE` 완전 일치
- 프로젝트 인덱스: 양측 모두 `lexical sort` + 1-based indexing
- camelCase→snake_case 변환: `main.js` IPC 핸들러에서 수동 매핑 (6개 필드)

### 발견 3 — 암묵적 파일시스템 계약

재료(bible/treatments)와 프로젝트 config는 **API 엔드포인트 없이** 파일시스템 직접 공유:
- FE: `getMaterialRoot()` / `getProjectRoot()` → 직접 `fs.readFileSync`/`fs.writeFileSync`
- BE: `resolve_workspace_root()` → `pathlib.Path` 기반 직접 접근

### 발견 4 — 하드코딩 동기화

FE/BE 양측에 **독립적 하드코딩** 존재:
- 장르맵 (`main.js:117-133` ↔ `process_runner.py:92-103`)
- 품질 리뷰 레이블 (`bridge_server.py:60-67`)
- 실행 키 화이트리스트 (`control_plane_contract.py:5-14`)
- 동기화 보장: 테스트 코드 (`test_bridge_server_http_contract.py`, `test_bridge_quality_summary.py`)

---

## 3. 7-Track 분석 개요

| Track | 주제 | 확신도 | 핵심 결론 |
|-------|------|--------|-----------|
| A | 전송 토폴로지 | 98% | IPC→HTTP→WS 3계층 분리, 단일 포트(8300) |
| B | 경로 해석 정합성 | 97% | 2중 루트 설계 정상, workspace-seed 초기화 안전 |
| C | 옵션 전달 정합성 | 98% | 장르맵·프로젝트 인덱스·정렬 순서 완전 일치 |
| D | IPC-HTTP 계약 교차 검증 | 97% | 22 IPC 채널 → 9 HTTP 엔드포인트 매핑 정상 |
| E | 데이터 흐름 생애주기 | 96% | 5단계 파이프라인 추적 완료 |
| F | 오류 복원력 | 96% | 3중 오류 봉쇄 (IPC envelope, HTTP envelope, WS reconnect) |
| G | 보안 격리 | 97% | contextIsolation+preload bridge+CSP+경로 탈출 방지 |

---

## 4. 관통 매트릭스: 계약 문서 6건 × 7-Track 교차 검증

```
                          Track-A  Track-B  Track-C  Track-D  Track-E  Track-F  Track-G
api-contract-v1.yaml        ●        ○        ○        ●        ●        ●        ○
event-schema-v1.json        ●        ○        ○        ●        ●        ○        ○
desktop-ipc-surface-v1      ●        ○        ●        ●        ●        ●        ●
desktop-runtime-v1          ●        ●        ○        ●        ○        ●        ●
prompt-map-v1.json          ○        ○        ●        ●        ●        ○        ○
control_plane_contract.py   ○        ○        ●        ●        ●        ●        ○

● = 직접 관련  ○ = 간접/무관
```

---

## 5. 아키텍처 전체 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                     Electron Renderer (index.html)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ 장르/프로젝트  │  │ 실행 제어     │  │ 품질 대시보드          │   │
│  │ 선택 UI       │  │ 시작/중지     │  │ 리뷰/요약/분석         │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
│─────────┼─────────────────┼──────────────────────┼───────────────│
│         │   window.geuldobiDesktop (preload.js)   │               │
│         │     contextBridge.exposeInMainWorld      │               │
│─────────┼─────────────────┼──────────────────────┼───────────────│
│         ▼                 ▼                      ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              IPC Layer (ipcRenderer.invoke)               │   │
│  │  bridge:run  bridge:stop  bridge:status  material:*       │   │
│  │  project:*   bridge:get-quality-*  bridge:save-*          │   │
│  └──────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────┘
                              │ ipcMain.handle()
┌─────────────────────────────┼───────────────────────────────────┐
│              Electron Main Process (main.js)                     │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │           camelCase → snake_case 변환                      │   │
│  │           bridgeFetch() → HTTP 127.0.0.1:8300             │   │
│  │           파일시스템 직접 접근 (material, config)             │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────┐  ┌───┴───────────────┐                   │
│  │ 파일시스템 직접 처리 │  │ HTTP/WS 프록시     │                   │
│  │ material:*         │  │ bridge:*           │                   │
│  │ project:*          │  │ (POST/GET/WS)      │                   │
│  │ settings:*         │  │                    │                   │
│  └───────────────────┘  └───┬───────────────┘                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │ fetch() / WebSocket
┌─────────────────────────────┼───────────────────────────────────┐
│              FastAPI Backend (bridge_server.py)                   │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │  POST /run          → ProcessRunner → main_a.py           │   │
│  │  POST /stop         → ProcessRunner.stop()                │   │
│  │  GET  /status       → Runner state snapshot               │   │
│  │  GET  /quality/*    → QualityDashboard + DBManager        │   │
│  │  POST /quality/rev  → DBManager.save_observation()        │   │
│  │  WS   /events       → WSManager broadcast                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────┐  ┌───┴───────────────┐                   │
│  │ runtime_paths.py   │  │ process_runner.py  │                   │
│  │ resolve_*_root()   │  │ stdin/stdout relay │                   │
│  │ GEULDOBI_* env     │  │ prompt_broker.py   │                   │
│  └───────────────────┘  └───────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 리스크 & 권고

### 현재 리스크 (낮음)

| # | 리스크 | 심각도 | 상태 |
|---|--------|--------|------|
| R1 | 장르맵 양측 하드코딩 drift 가능성 | 낮음 | 테스트가 동기화 보장 |
| R2 | camelCase→snake_case 수동 매핑 누락 가능 | 낮음 | 현재 6필드 모두 정상 |
| R3 | workspace-seed 초회 복사 실패 시 빈 프로젝트 | 낮음 | copyMissingTree 재시도 안전 |
| R4 | CSP에 `unsafe-inline` 포함 | 중간 | 단일파일 SPA 특성상 불가피 |

### 권고 사항

1. **장르맵 단일 소스**: 현재 양측 하드코딩이지만 테스트 커버리지로 충분. 추후 공유 JSON 고려 가능
2. **camelCase 변환 자동화**: 현재 수동 매핑이 안전하고 명시적. 자동 변환 도입 시 예측 불가 필드명 문제 주의
3. **WSManager 연결 제한**: 현재 무제한 WS 연결 허용. 데스크톱 단일 사용자이므로 실질 리스크 없음

---

## 7. 3-Pass 감리 기록

| Pass | 항목 | 결과 |
|------|------|------|
| 1차 (구조) | 7-Track 분류 누락 없음, 매트릭스 셀 정합 | ✅ |
| 2차 (증거) | 코드 경로·라인번호 교차 확인 완료 | ✅ |
| 3차 (모순) | Track 간 상충 결론 없음, 리스크 평가 일관 | ✅ |

최종 확신도: **97%**

---

## 8. 개별 Track 문서 목록

| 파일명 | 내용 |
|--------|------|
| `track-a-transport-topology.md` | 전송 토폴로지 — IPC/HTTP/WS 3계층 |
| `track-b-path-resolution.md` | 경로 해석 정합성 — 2중 루트 + 환경변수 |
| `track-c-option-relay.md` | 옵션 전달 정합성 — 장르맵·인덱스·정렬 |
| `track-d-contract-parity.md` | IPC-HTTP 계약 교차 검증 |
| `track-e-data-flow-lifecycle.md` | 데이터 흐름 생애주기 |
| `track-f-error-resilience.md` | 오류 복원력 |
| `track-g-security-containment.md` | 보안 격리 |
