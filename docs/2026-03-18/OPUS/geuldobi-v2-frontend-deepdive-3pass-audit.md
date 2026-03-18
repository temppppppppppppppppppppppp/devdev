# 글도비 데스크톱 프론트엔드 딥다이브 3-Pass 감리 보고서

> **감리일**: 2026-03-18
> **감리 방법론**: 3회 독립 심층 조사 → 3-Pass 교차 감리
> **감리 대상**: `geuldobi-desktop/src/` 전체 (main.js, preload.js, index.html, splash/*, console_relay.js, desktop_control_plane_contract.js)
> **감리자**: Claude Opus 4.6

---

## 목차

1. [감리 방법론](#감리-방법론)
2. [1차 조사: 보안 & IPC 공격면](#1차-조사-보안--ipc-공격면)
3. [2차 조사: 렌더러 UX & 엣지 케이스](#2차-조사-렌더러-ux--엣지-케이스)
4. [3차 조사: 빌드·테스트·데드코드](#3차-조사-빌드테스트데드코드)
5. [3-Pass 교차 감리](#3-pass-교차-감리)
6. [종합 위험 매트릭스](#종합-위험-매트릭스)
7. [권장 패치 우선순위](#권장-패치-우선순위)

---

## 감리 방법론

| Pass | 관점 | 목적 |
|------|------|------|
| **Round 1** | 보안·IPC 공격면 | Electron 보안 표면, IPC 검증, 프로세스 관리, 데이터 노출 |
| **Round 2** | 렌더러·UX 엣지 케이스 | DOM/XSS, 상태 경쟁조건, 에러 UX, 접근성, 성능 |
| **Round 3** | 빌드·테스트·데드코드 | 패키징 무결성, 테스트 커버리지 갭, 의존성, 환경 설정 |
| **Pass 1** | 교차 검증 | 3개 라운드 발견사항 중복 제거 + 심각도 재평가 |
| **Pass 2** | 실증 검증 | 코드 라인 레퍼런스 정확성, 오탐(false positive) 제거 |
| **Pass 3** | 우선순위 결정 | 비즈니스 영향 + 기술 난이도 기반 실행 로드맵 |

---

## 1차 조사: 보안 & IPC 공격면

### SEC-01: CSP `unsafe-inline` 허용 [HIGH]
- **파일**: `src/index.html:6`
- **현상**: `script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'`
- **위험**: XSS 공격 시 인라인 스크립트 실행 가능. Electron 환경에서는 앱 컨텍스트 권한으로 실행됨
- **완화 요인**: `contextIsolation: true` + `nodeIntegration: false`로 Node.js API 접근은 차단
- **권장**: nonce 기반 인라인 스크립트로 전환, 장기적으로 외부 JS 파일 분리

### SEC-02: IPC `bridge:run` 입력 검증 부재 [CRITICAL → MEDIUM 재평가]
- **파일**: `src/main.js:551`
- **현상**: `key`, `subKey`, `inputs` 파라미터가 타입 체크 없이 JSON으로 직렬화되어 백엔드 전송
- **3-Pass 재평가**: 렌더러→메인 IPC는 `contextIsolation` 내부 채널이므로 외부 공격자가 직접 호출 불가. 실질 위험은 XSS를 통한 간접 공격에 한정 → **MEDIUM**
- **권장**: `key` 화이트리스트 검증 + `inputs` 깊이/크기 제한

### SEC-03: IPC `bridge:resolvePrompt` — runId 경로 탈출 [MEDIUM]
- **파일**: `src/main.js:615-620`
- **현상**: `buildRunInputRoute(runId)` 에서 `encodeURIComponent()` 사용. `../` 패턴은 `%2E%2E%2F`로 인코딩되므로 HTTP 경로 탈출은 차단됨
- **3-Pass 재평가**: `encodeURIComponent`가 슬래시를 인코딩하므로 실제 경로 탈출 불가 → 오탐 가능성 있으나, 백엔드의 URL 디코딩 정책에 따라 위험 잔존
- **권장**: UUID/숫자 정규식 검증 추가 (`/^[a-z0-9-]+$/i`)

### SEC-04: 백엔드 HTTP 평문 통신 [MEDIUM → LOW 재평가]
- **파일**: `src/main.js:107-109`
- **현상**: `http://127.0.0.1:8300`, `ws://127.0.0.1:8300/events`
- **3-Pass 재평가**: localhost 전용 통신이며, CSP에서도 `connect-src ws://127.0.0.1:8300`으로 제한. 동일 시스템 내 악성 프로세스의 트래픽 스니핑은 이론적 위험이나, 실질적으로 해당 공격자는 이미 시스템 접근 권한을 보유 → **LOW**
- **유지 사유**: HTTPS 전환은 자체서명 인증서 관리 부담 대비 보안 이득 미미

### SEC-05: `process.env` 전체 상속 [HIGH]
- **파일**: `src/main.js:270` (`...process.env`)
- **현상**: 호스트의 모든 환경 변수가 Python 백엔드 subprocess에 전달
- **위험**: 사용자 PC에 설정된 AWS_ACCESS_KEY, GOOGLE_API_KEY 등이 백엔드 프로세스에 노출
- **3회 조사 일치**: Round 1, Round 3 동일 발견 (교차 확인됨)
- **권장**: 필요 변수만 명시적 전달 (PATH, TEMP 등 최소한의 시스템 변수 + 글도비 전용 변수)

### SEC-06: 설정/로그 파일 평문 저장 + 권한 미설정 [MEDIUM]
- **파일**: `src/main.js:624-653` (settings.json), `src/main.js:11-42` (electron-main.log)
- **현상**: `%LOCALAPPDATA%\Geuldobi\` 하위에 평문 JSON/로그 파일 생성
- **3-Pass 재평가**: Windows NTFS는 기본적으로 사용자별 프로필 격리. 다중 사용자 시스템에서만 위험 → **MEDIUM**
- **권장**: 로그 로테이션(크기 제한) + 민감 패턴 필터링

### SEC-07: `sanitizeProjectName()`에서 `.` 미제거 [HIGH → MEDIUM 재평가]
- **파일**: `src/main.js` (sanitizeProjectName 함수)
- **현상**: `/`, `\` 는 제거하나 `.`은 허용 → `..` 경로 탈출 가능
- **3-Pass 재평가**: 실제 코드 확인 결과 `/`와 `\`는 정규식에서 `_`로 치환되므로 `../` 패턴은 `.._ `가 되어 경로 탈출 불가. 순수 `..` (슬래시 없이)만으로는 `path.join()`에서 상위 이동 불가
- **단**, `..` 이름의 프로젝트 생성 시 `path.join(baseDir, "..")` = `baseDir의 부모` → **경로 탈출 성립**
- **권장**: whitelist 정규식 적용: `name.replace(/[^a-zA-Z0-9가-힣_\- ]/g, "_")`

### SEC-08: CSP `connect-src`에 Google API 노출 [MEDIUM]
- **파일**: `src/index.html:6`
- **현상**: `connect-src ... https://generativelanguage.googleapis.com`
- **위험**: XSS 성공 시 렌더러에서 Google API로 직접 데이터 전송 가능
- **권장**: 외부 API 호출은 메인 프로세스 IPC 경유로 전환

### SEC-09: 백엔드 프로세스 정리 비동기 실행 [LOW]
- **파일**: `src/main.js:332-353`
- **현상**: Windows `taskkill /t /f`가 비동기로 실행되어 `backendProcess = null` 이후 프로세스가 살아있을 수 있음
- **실질 영향**: 앱 종료 시 좀비 프로세스 발생 가능하나, OS가 부모 종료 시 자식도 정리
- **권장**: kill timeout 추가 (5초 후 SIGKILL)

### SEC-10: 재료 파일 임포트 덮어쓰기 [LOW]
- **파일**: `src/main.js:694-731`
- **현상**: 동일 파일명 존재 시 `fs.copyFileSync`로 무조건 덮어쓰기
- **영향**: 사용자 의도치 않은 기존 파일 손실
- **권장**: 중복 파일명 자동 넘버링 또는 확인 다이얼로그

### SEC-11: 파일 삭제 symlink 미검증 [LOW]
- **파일**: `src/main.js:733-750`
- **현상**: `..`, `/`, `\` 검증은 있으나 symlink 타겟 검증 없음
- **3-Pass 재평가**: Windows에서 symlink 생성 자체가 관리자 권한 필요 (개발자 모드 예외). 실질 위험 낮음 → **LOW**

---

## 2차 조사: 렌더러 UX & 엣지 케이스

### UX-01: innerHTML + escapeHtml 일관성 부재 [HIGH]
- **파일**: `src/index.html` (라인 3878, 4083, 4102, 4143 등 50건+)
- **현상**: `escapeHtml()` 유틸리티(라인 3766-3773)가 존재하나, innerHTML 사용 시 일관 적용되지 않음
- **위험**: 백엔드 응답에 악성 페이로드가 포함되면 DOM 조작 가능
- **권장**:
  - 새 데이터 삽입 시 `textContent` 우선 사용
  - 불가피한 innerHTML은 `escapeHtml()` 필수 적용
  - 코드 리뷰 체크리스트에 추가

### UX-02: 500ms setInterval로 대규모 DOM 재생성 [MEDIUM]
- **파일**: `src/index.html:8163-8166`
- **현상**: `renderMissionBoard()` + `renderAgentBoard()`가 500ms마다 실행, 매번 `innerHTML = ""`로 전체 재생성
- **영향**:
  - 초당 2회 전체 레이아웃 재계산 (reflow)
  - 노트북 배터리 소모
  - 50개+ DOM 요소 반복 생성/삭제
- **권장**:
  - 상태 변경 이벤트 기반 업데이트로 전환
  - 또는 diff 기반 부분 업데이트
  - DocumentFragment 활용으로 reflow 최소화

### UX-03: 프롬프트 큐 경쟁 조건 [HIGH]
- **파일**: `src/index.html:6319-6410, 6576`
- **현상**: WebSocket에서 프롬프트 이벤트가 빠르게 연속 수신되면 `_pendingPromptQueue` 조작과 `_showNextQueuedPrompt()` 호출 사이 race condition 가능
- **영향**: 프롬프트 스킵 또는 중복 표시
- **3-Pass 재평가**: JavaScript 단일 스레드 이벤트 루프 특성상 동시 접근은 불가. 다만 비동기 콜백 인터리빙은 가능 → **MEDIUM으로 하향**
- **권장**: 큐 처리를 단일 async 함수로 직렬화

### UX-04: WebSocket onerror 핸들러 공백 [MEDIUM]
- **파일**: `src/index.html:6221`
- **현상**: `_ws.onerror = () => {};` — 에러 발생 시 UI 피드백 없음
- **영향**: 네트워크 문제 시 사용자가 앱 멈춤으로 인지
- **권장**: 에러 로그 기록 + 사용자 알림 배너

### UX-05: catch 블록 무시 패턴 다수 [MEDIUM]
- **파일**: `src/index.html` (라인 6222, 6248 등)
- **현상**: `.catch(() => {})` — 에러 완전 무시
- **영향**: 초기화 실패 시 UI가 "연결 중" 상태에 영구 체류
- **권장**: 최소한 console.error + 사용자 피드백 추가

### UX-06: UI 잠금 해제 후 disabled 상태 불완전 복구 [MEDIUM]
- **파일**: `src/index.html:5211-5226`
- **현상**: `_lockUI(false)` 시 원래 disabled였던 버튼도 활성화될 수 있음
- **완화 요인**: `updateGenreGating()`이 부분 복구
- **권장**: 잠금 전 상태 저장 → 해제 시 복원 패턴 적용

### UX-07: Canvas 히트박스 스케일링 [LOW]
- **파일**: `src/index.html:5638-5656`
- **현상**: CSS 리사이즈 시 좌표계 미스매치 가능
- **완화 요인**: `ResizeObserver`(라인 3579)로 캔버스 크기 동기화됨
- **잔존 위험**: 극단적 비율에서 오정렬 가능

### UX-08: ARIA 라벨 부족 [LOW]
- **파일**: `src/index.html` 전반
- **현상**: `.menu-btn` 35개+, 모달에 `role="dialog"` 없음
- **영향**: 스크린 리더 사용 불가
- **현실적 판단**: 웹소설 작성 도구의 주 사용층이 시각장애인일 가능성 낮음 → 우선순위 하향

### UX-09: 캔버스 60fps 상시 렌더링 [LOW]
- **파일**: `src/index.html:5805-5860`
- **현상**: `requestAnimationFrame` 루프가 실행 중이 아닐 때에도 계속 될 가능성
- **권장**: 비실행 시 `cancelAnimationFrame` 호출

---

## 3차 조사: 빌드·테스트·데드코드

### BUILD-01: `src/sprites/` 불필요한 프로덕션 번들링 [MEDIUM]
- **파일**: `package.json:71-74`
- **현상**: `"files": ["src/**/*"]` → 27개 디버그용 스프라이트 PNG 포함
- **영향**: 설치 파일 5-10MB 불필요 증가
- **권장**: `"!src/sprites/dbg_*"` 제외 패턴 추가

### BUILD-02: `signAndEditExecutable: false` — SmartScreen 경고 [MEDIUM]
- **파일**: `package.json:31`
- **현상**: Windows 코드 서명 미적용 → 설치 시 "알 수 없는 앱" 경고
- **영향**: 사용자 설치 거부율 증가
- **권장**: 코드 서명 인증서 획득 (연 100-400 USD)

### BUILD-03: python-embed 버전 고정 부재 [HIGH]
- **파일**: 빌드 스크립트 (scripts/build_workspace_seed.py, build/ 하위)
- **현상**: 내장 Python 버전이 명시적으로 핀닝되지 않을 가능성
- **영향**: 향후 빌드에서 다른 Python 버전 포함 → 런타임 불일치
- **권장**: 빌드 스크립트에서 Python 버전 상수 지정

### BUILD-04: extraResources `filter: ["**/*"]` [LOW]
- **파일**: `package.json:41-70`
- **현상**: 백엔드/엔진 리소스가 무필터로 번들
- **영향**: 로그·백업·임시 파일이 포함될 수 있음
- **권장**: `"!*.log"`, `"!*.tmp"`, `"!*.bak"` 제외 추가

### TEST-01: IPC 엔드투엔드 테스트 부재 [MEDIUM]
- **상태**: 계약 기반 정적 테스트는 완벽 (preload 메서드 존재, IPC 채널 매핑, CSP 검증)
- **부족**: 실제 IPC invoke → 메인 프로세스 핸들러 → HTTP fetch → 응답 경로의 통합 테스트 없음
- **미테스트 채널**: `bridge:run`, `bridge:stop`, `material:import-file`, `material:delete-file`, `project:saveConfigSurfaces`, `project:applyWorkGuardTemplate`
- **권장**: Spectron/Playwright 기반 E2E 테스트 환경 구축

### TEST-02: Packaged .exe 통합 테스트 부재 [HIGH]
- **현상**: 모든 테스트가 개발 모드(`app.isPackaged === false`)에서 실행
- **영향**: 프로덕션 경로 해석, 리소스 번들, backend.exe 기동 등 검증 불가
- **현재 대안**: `npm run start:spike` (5초 스파이크 테스트)가 기본 기동 확인
- **권장**: CI에서 `npm run build:dir` → 설치 디렉토리에서 스파이크 테스트 실행

### TEST-03: 포트 8300 충돌 처리 없음 [LOW]
- **파일**: `src/main.js:107`
- **현상**: 포트가 이미 사용 중이면 백엔드 기동 실패 → splash에서 30초 후 실패 메시지
- **권장**: 기동 전 포트 가용성 확인 또는 동적 포트 할당

### DEAD-01: `deadCandidate` IPC 채널 [INFO — 의도된 설계]
- **파일**: `src/preload.js:32-34`, `src/main.js:965-968`
- **현상**: `workspace:get-path` 채널이 정의·구현되어 있으나 렌더러에서 미사용
- **확인**: `test_desktop_shadow_hygiene.py`에서 의도적 dead candidate로 표기됨
- **판단**: 정상. 미래 사용 또는 레거시 호환 목적의 의도적 보존

### DEAD-02: lucide 전체 번들 [LOW]
- **파일**: `package.json:23`
- **현상**: `lucide ^0.577.0` 전체 설치 (~600KB) / 실제 사용: `pen-line` 1개 아이콘
- **영향**: 설치 크기 미미한 증가 (런타임 영향 없음)
- **권장**: 장기적으로 `lucide-static` 또는 SVG 인라인으로 전환

### DEP-01: Electron ^40.8.0 보안 패치 [MEDIUM]
- **파일**: `package.json:19`
- **현상**: Chromium 130 기반. 정기적 CVE 확인 필요
- **권장**: `npm audit` 월 1회 실행 + Electron 릴리스 노트 모니터링

---

## 3-Pass 교차 감리

### Pass 1: 교차 검증 — 중복 제거 + 심각도 재평가

| 발견 ID | Round 1 심각도 | Round 2/3 확인 | 최종 심각도 | 근거 |
|---------|---------------|---------------|------------|------|
| SEC-02 | CRITICAL | — | **MEDIUM** | contextIsolation으로 외부 공격자의 직접 IPC 호출 불가 |
| SEC-03 | CRITICAL | — | **MEDIUM** | encodeURIComponent가 슬래시 인코딩 → 실제 탈출 어려움 |
| SEC-04 | CRITICAL | — | **LOW** | localhost 전용 + 같은 시스템 내 공격자는 이미 전체 접근 보유 |
| SEC-05 | HIGH | Round 3 동일 발견 | **HIGH** | 2회 독립 확인. 실질적 민감 변수 누출 위험 |
| SEC-07 | HIGH | — | **MEDIUM** | 슬래시 없는 순수 `..`만 위험이나 실현 경로 제한적 |
| UX-03 | HIGH | — | **MEDIUM** | JS 단일 스레드 이벤트 루프 특성상 동시 접근 불가 |

### Pass 2: 실증 검증 — 오탐 제거

| 발견 ID | 오탐 여부 | 판정 근거 |
|---------|----------|----------|
| SEC-03 | **부분 오탐** | `encodeURIComponent("../status")` = `%2E%2E%2Fstatus` → HTTP 라우터가 디코딩하지 않으면 안전 |
| UX-03 | **부분 오탐** | JavaScript 단일 스레드에서 진정한 race condition 불가, 다만 비동기 콜백 순서 이슈는 잔존 |
| BUILD-01 | **유효** | `src/sprites/dbg_*.png` 파일이 프로덕션 빌드에 포함됨 확인 |
| SEC-11 | **부분 오탐** | Windows에서 symlink 생성에 관리자 권한 필요 (개발자 모드 예외) |

### Pass 3: 우선순위 결정 — 비즈니스 영향 × 기술 난이도

**즉시 패치 (이번 스프린트)**:

| 순위 | 발견 ID | 제목 | 비즈니스 영향 | 난이도 |
|------|---------|------|-------------|--------|
| 1 | SEC-05 | process.env 전체 상속 | 민감 정보 누출 | 낮음 (10줄 변경) |
| 2 | UX-01 | innerHTML escapeHtml 일관성 | XSS 취약점 | 중간 (50건 점검) |
| 3 | SEC-01 | CSP unsafe-inline | XSS 확대 방지 | 높음 (아키텍처 변경) |
| 4 | SEC-07 | sanitizeProjectName `.` 미제거 | 경로 탈출 | 낮음 (정규식 1줄) |

**계획 패치 (다음 2주)**:

| 순위 | 발견 ID | 제목 | 비즈니스 영향 | 난이도 |
|------|---------|------|-------------|--------|
| 5 | UX-04/05 | onerror 공백 + catch 무시 | 사용자 경험 | 낮음 |
| 6 | UX-02 | 500ms DOM 재생성 | 성능/배터리 | 중간 |
| 7 | BUILD-03 | python-embed 버전 핀닝 | 빌드 재현성 | 낮음 |
| 8 | TEST-02 | Packaged .exe 테스트 | 릴리스 신뢰성 | 높음 |

**백로그**:

| 발견 ID | 제목 | 비고 |
|---------|------|------|
| BUILD-01 | sprites 번들 제외 | 크기 최적화 |
| BUILD-02 | 코드 서명 | 비용 발생 |
| UX-06 | UI 잠금 상태 복구 | 엣지 케이스 |
| UX-08 | ARIA 접근성 | 장기 과제 |
| DEAD-02 | lucide 경량화 | 영향 미미 |
| DEP-01 | Electron 보안 패치 | 정기 작업화 |
| TEST-03 | 포트 충돌 처리 | 드문 시나리오 |

---

## 종합 위험 매트릭스

```
        │ 영향: 낮음    │ 영향: 중간    │ 영향: 높음
────────┼──────────────┼──────────────┼──────────────
가능성   │              │              │
높음    │              │ UX-04/05     │ SEC-05
        │              │ UX-02        │ UX-01
────────┼──────────────┼──────────────┼──────────────
중간    │ BUILD-01     │ SEC-01       │ SEC-07
        │ DEAD-02      │ BUILD-03     │ TEST-02
────────┼──────────────┼──────────────┼──────────────
낮음    │ UX-08        │ SEC-02/03    │ SEC-04
        │ UX-07/09     │ BUILD-02     │ SEC-06
        │ TEST-03      │ DEP-01       │ SEC-08
```

---

## 긍정적 발견 (Well-Done 사항)

감리 과정에서 확인된 건전한 설계 요소:

| 항목 | 상태 | 비고 |
|------|------|------|
| `contextIsolation: true` | ✅ | 모든 윈도우에서 일관 적용 |
| `nodeIntegration: false` | ✅ | 렌더러의 Node.js API 접근 차단 |
| `webSecurity` 기본값 유지 | ✅ | 명시적 비활성화 없음 |
| IPC 계약 문서화 | ✅ | `desktop_control_plane_contract.js` 통합 관리 |
| Dead candidate 명시적 표기 | ✅ | 테스트에서 의도적 보존 검증 |
| 계약 기반 테스트 커버리지 | ✅ | preload·CSP·transport·packaging 계약 테스트 완비 |
| 설정 백업 자동 생성 | ✅ | settings.json.bak 자동 보존 |
| 경로 탈출 방지 (material delete) | ✅ | `..`, `/`, `\` 검증 적용 |
| 개발/프로덕션 모드 자동 전환 | ✅ | `app.isPackaged` 기반 분기 |
| 렌더러 콘솔 릴레이 | ✅ | warn/error만 선별 전달 (info 필터링) |

---

## 부록: 발견 ID 색인

| ID | 분류 | 심각도 | 파일 | 라인 |
|----|------|--------|------|------|
| SEC-01 | 보안 | HIGH | src/index.html | 6 |
| SEC-02 | 보안 | MEDIUM | src/main.js | 551 |
| SEC-03 | 보안 | MEDIUM | src/main.js | 615-620 |
| SEC-04 | 보안 | LOW | src/main.js | 107-109 |
| SEC-05 | 보안 | HIGH | src/main.js | 270 |
| SEC-06 | 보안 | MEDIUM | src/main.js | 11-42, 624-653 |
| SEC-07 | 보안 | MEDIUM | src/main.js | sanitizeProjectName |
| SEC-08 | 보안 | MEDIUM | src/index.html | 6 |
| SEC-09 | 보안 | LOW | src/main.js | 332-353 |
| SEC-10 | 보안 | LOW | src/main.js | 694-731 |
| SEC-11 | 보안 | LOW | src/main.js | 733-750 |
| UX-01 | UX | HIGH | src/index.html | 3766+ |
| UX-02 | UX | MEDIUM | src/index.html | 8163-8166 |
| UX-03 | UX | MEDIUM | src/index.html | 6319-6410 |
| UX-04 | UX | MEDIUM | src/index.html | 6221 |
| UX-05 | UX | MEDIUM | src/index.html | 6222, 6248 |
| UX-06 | UX | MEDIUM | src/index.html | 5211-5226 |
| UX-07 | UX | LOW | src/index.html | 5638-5656 |
| UX-08 | UX | LOW | src/index.html | 전반 |
| UX-09 | UX | LOW | src/index.html | 5805-5860 |
| BUILD-01 | 빌드 | MEDIUM | package.json | 71-74 |
| BUILD-02 | 빌드 | MEDIUM | package.json | 31 |
| BUILD-03 | 빌드 | HIGH | 빌드 스크립트 | — |
| BUILD-04 | 빌드 | LOW | package.json | 41-70 |
| TEST-01 | 테스트 | MEDIUM | — | — |
| TEST-02 | 테스트 | HIGH | — | — |
| TEST-03 | 테스트 | LOW | src/main.js | 107 |
| DEAD-01 | 데드코드 | INFO | src/preload.js | 32-34 |
| DEAD-02 | 데드코드 | LOW | package.json | 23 |
| DEP-01 | 의존성 | MEDIUM | package.json | 19 |

---

> **다음 감리 예정**: 백엔드(bridge_server) ↔ 프론트엔드 통합 경로 감리
> **감리 주기 권장**: 주요 릴리스 전 1회 + 분기 1회 정기 감리
