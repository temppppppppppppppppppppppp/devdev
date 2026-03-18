# S3 프론트엔드 (Electron) 실행문서

> 작성일: 2026-03-18
> 상태: 활성
> 정식 경로: `docs/2026-03-18/OPUS/ssot_execution/s3-frontend-execution.md`
> 소스 SSOT: `docs/2026-03-18/OPUS/ssot/s3-frontend-electron.md`
> 감리 소스:
> - `docs/2026-03-18/OPUS/geuldobi-v2-frontend-deepdive-3pass-audit.md` (R0: 최초 3-Pass)
> - `docs/2026-03-18/OPUS/geuldobi-v2-frontend-deepdive-adversarial-3pass-audit.md` (R1: 적대적 1차)
> - `docs/2026-03-18/OPUS/geuldobi-v2-frontend-deepdive-adversarial-3pass-audit-r2.md` (R2: 적대적 2차)
> 감리자: Claude Opus 4.6 (1M context)

---

## 1. 개요

본 문서는 S3 프론트엔드(Electron) SSOT에서 식별된 모든 조치 가능 항목을 실행 가능한 형태로 정리한다.
3회 독립 조사 + 2회 적대적 감리(R1, R2)를 거쳐 수렴 확인된 최종 발견사항 기준이다.

**대상 시스템**: Electron 40.8.0, Vanilla JS 모놀리스 (index.html 8,266줄 / main.js 1,010줄 / preload.js 97줄)

**발견 수 변천**:
```
R0 최초 조사:       29건 (HIGH 4, MEDIUM 13, LOW 9, INFO 3)
R1 적대적 1차:      11건 (HIGH 1, MEDIUM 4, LOW 5, INFO 1)  — 18건 삭제/합병
R2 적대적 2차:      10건 (HIGH 1, MEDIUM 3, LOW 5, INFO 1)  — 수렴 확인
S3 SSOT 반영:       23건 (HIGH 1, MEDIUM 3, LOW 11, INFO 8) — SSOT 통합 기준
```

---

## 2. 실행 항목 총괄표

우선순위 기준: HIGH > MEDIUM > LOW > INFO, 동일 등급 내 공수 낮은 순

### 2.1 HIGH — 즉시 조치 (이번 스프린트)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S3 근거 |
|----|------|----------|------|-----------|-----------|--------|---------|
| FE-H01 | `sanitizeProjectName` 경로 탐색(Path Traversal) 수정 | P0 | `main.js` — function at main.js:761, regex at main.js:765. 정규식에서 `.` 미제거로 `..` 입력 시 `path.join(projectsDir, "..")` = 프로젝트 디렉토리 탈출. 영향 IPC 3건: `project:loadConfigSurfaces`(읽기), `project:saveConfigSurfaces`(쓰기), `project:applyWorkGuardTemplate`(쓰기). XSS 체이닝 선행 조건이나 파일시스템 쓰기 가능한 실질적 취약점. | (1) 화이트리스트 정규식 적용: `name.replace(/[^a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ_\- ]/g, "_")` (2) `..`, `...` 등 순수 점 시퀀스 빈 문자열 반환 (3) 단위 테스트: `sanitizeProjectName("..")` = `""`, `sanitizeProjectName("정상")` = `"정상"`, `sanitizeProjectName("test_project")` = `"test_project"` 통과 확인 | 0.5h | 없음 | S3 §6.1, R1 SEC-07, R2 SEC-07 (HIGH 유지, 영향 범위 3 IPC 확대) |

### 2.2 MEDIUM — 계획 조치 (다음 2주)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S3 근거 |
|----|------|----------|------|-----------|-----------|--------|---------|
| FE-M01 | CSP `unsafe-inline` 제거 (장기) / `connect-src` 불필요 외부 API 제거 (단기) | P1 | `index.html:6` — 인라인 `<script>`, `<style>` 사용으로 CSP에 `unsafe-inline` 필수. 구조적 제약(8,266줄 단일 HTML). 단기 완화: `connect-src`에서 `https://generativelanguage.googleapis.com` 제거 (SEC-08 동시 해결). 장기: JS/CSS 외부 파일 분리 → nonce 또는 hash 기반 전환. | (단기) CSP `connect-src`에서 미사용 외부 API 제거 완료. (장기) 인라인 JS/CSS를 외부 파일로 분리 후 `unsafe-inline` 제거 | 단기 0.5h / 장기 40h+ | 장기 과제는 아키텍처 리팩토링 필요 | S3 §6.2 CSP unsafe-inline, R1 SEC-01 (MEDIUM), R2 SEC-01 (MEDIUM 유지) |
| FE-M02 | python-embed 버전 고정 | P1 | 빌드 스크립트에서 내장 Python 런타임 버전이 명시적으로 핀닝되지 않을 가능성. 향후 빌드에서 상이한 Python 버전이 포함되면 런타임 불일치 발생. | 빌드 스크립트에 Python 버전 상수 지정 + CI에서 버전 일치 확인 스텝 추가 | 2h | 빌드 스크립트 확인 필요 (미열람 상태 -- 우선 빌드 스크립트 확인 필요 (investigation task)) | S3 §6.2 python-embed, R1 BUILD-03 (MEDIUM), R2 BUILD-03 (MEDIUM 유지) |
| FE-M03 | 패키징된 .exe 통합 테스트 환경 구축 | P1 | 모든 테스트가 개발 모드(`app.isPackaged === false`)에서만 실행. 프로덕션 경로(backend.exe 기동, 리소스 번들, workspace-seed)가 미검증. `npm run start:spike`는 개발 모드 기동만 확인. | CI에서 `npm run build:dir` 후 `dist/win-unpacked/Geuldobi.exe`로 spike 테스트 실행 파이프라인 구축 | 8h | CI 환경 + 빌드 도구 | S3 §6.2 .exe 테스트 부재, R1 TEST-02 (MEDIUM), R2 TEST-02 (MEDIUM 유지) |

### 2.3 LOW — 백로그 (분기 내 개선)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S3 근거 |
|----|------|----------|------|-----------|-----------|--------|---------|
| FE-L01 | `process.env` 전체 상속 제한 (프로덕션 모드) | P2 | `main.js:270` — `...process.env`로 호스트의 모든 환경 변수가 백엔드 subprocess에 전달. 개발 모드에서는 PATH 등 필수로 제거 불가하나, 프로덕션 모드(`backend.exe` 절대경로 실행)에서는 최소 환경(PATH, TEMP, TMP, LOCALAPPDATA, USERPROFILE + 글도비 전용 변수)만 전달 가능. | `app.isPackaged` 분기: 프로덕션에서 명시적 환경 변수만 전달. 개발 모드에서 기존 동작 유지. 기동 테스트 통과. | 2h | 프로덕션 빌드 테스트 환경 (FE-M03) | S3 §6.3 process.env 상속, R1 SEC-05, R2 SEC-05 (LOW) |
| FE-L02 | CSP `connect-src` 미사용 외부 API origin 제거 | P2 | `index.html:6` — `https://generativelanguage.googleapis.com`이 CSP에 선언되어 있으나 렌더러 코드에서 미사용. 불필요한 공격면. | CSP에서 해당 origin 제거 후 전체 기능 회귀 테스트 통과 | 0.5h | 없음 (FE-M01 단기 완화와 동시 수행 가능) | S3 §6.3 미사용 CSP origin, R1 SEC-08 (LOW) |
| FE-L03 | IPC `bridge:run` key 화이트리스트 추가 (defense-in-depth) | P2 | `main.js:551` — `key` 파라미터가 타입/값 검증 없이 백엔드로 전달. main process는 투명 프록시 설계이며 입력 검증 책임은 백엔드에 있으나, defense-in-depth 관점에서 허용 key 화이트리스트 추가 권장. 화이트리스트 소스: `control_plane_contract.py:21-24 PUBLIC_RUN_KEYS` (`frozenset({"0","1","2","3","4","6","7","44","77","88","99"})`). | `key` 파라미터에 허용값 목록 검증 추가. 비허용 key는 즉시 거부. | 1h | 백엔드 key 목록 확인 | S3 §6.3 IPC key whitelist 부재, R1 SEC-02 (LOW) |
| FE-L04 | `window.prompt()` → 커스텀 모달 전환 | P2 | `index.html:4786` — Electron에서 `window.prompt()`는 동기 블로킹 다이얼로그. 일부 버전에서 렌더러 프로세스 freeze 가능. 현재 1곳(승인 ID 입력)에서 사용. | `window.prompt()` 호출을 커스텀 async 모달로 교체. 기존 승인 ID 입력 기능 동일하게 동작. | 2h | 없음 | R1 NEW-03 (LOW) |
| FE-L05 | `requestAnimationFrame` 루프 조건부 정지 | P2 | `index.html:5822, 8263` — `draw()` 함수가 페이지 로드부터 앱 종료까지 60fps 무조건 실행. 비실행(사무실 뷰 비활성) 시에도 매 프레임 캔버스 렌더링. | 사무실 뷰 비활성 시 `cancelAnimationFrame` 호출, 활성 시 재개. 배터리 소모 감소 확인. | 1.5h | 뷰 전환 이벤트 식별 | S3 §4.3 rAF infinite loop, R1 NEW-04 (LOW) |
| FE-L06 | Silent `.catch(() => {})` 8건에 최소 로깅 추가 | P2 | `index.html:5983, 6222, 6253, 6376, 7686, 7800, 7805, 7961` — 에러를 완전 무시. R2에서 대부분 의도적 fire-and-forget으로 판정되었으나, 최소한 `console.warn` 추가로 디버깅 편의 확보. 특히 6222(`getBackendUrl`)만 잠재적 문제 (5초 watchdog이 커버하나 로그 부재). | 8개 silent catch에 `console.warn` 추가. 기존 동작(fire-and-forget) 유지. | 1h | 없음 | S3 §4.6, R0 UX-05 (INFO로 하향) |
| FE-L07 | Settings IPC 페이로드 크기 제한 | P3 | `main.js:624` — `ipcMain.handle` 행. `write-settings` IPC에 크기 제한 없음. XSS 경유 시 대용량 JSON 전달로 디스크 fill 이론적 가능. V8/IPC structured clone 메모리 제한이 자연 방어하나, 명시적 가드 권장. | `JSON.stringify(settings).length > 1MB` 시 거부 로직 추가 | 0.5h | 없음 | S3 §6.3 NEW-01, R2 NEW-01 (LOW) |
| FE-L08 | Settings/로그 파일 평문 저장 개선 | P3 | `main.js:11-42, 624-653` — `%LOCALAPPDATA%\Geuldobi\` 하위에 settings.json(API 키 포함), 로그 파일이 평문 저장. Windows NTFS 사용자별 프로필 격리에 의존. | 로그 로테이션(크기 제한) 도입 + 민감 패턴(API 키) 마스킹 필터 추가 | 4h | 없음 | S3 §6.3 SEC-06, R2 SEC-06 (LOW) |
| FE-L09 | 스프라이트 번들링 최적화 | P3 | `package.json:71-74` — `"files": ["src/**/*"]`로 디버그용 스프라이트 PNG 포함. 설치 파일 5-10MB 불필요 증가. | `"!src/sprites/dbg_*"` 제외 패턴 추가 후 빌드 크기 감소 확인 | 0.5h | 없음 | S3 §6.3 BUILD-01, R1 BUILD-01 (LOW) |
| FE-L10 | 코드 서명 인증서 도입 | P3 | `package.json:31` — `signAndEditExecutable: false`. Windows SmartScreen "알 수 없는 앱" 경고 발생. 사용자 설치 거부율 증가. | 코드 서명 인증서 획득(연 100-400 USD) + electron-builder 설정에 서명 활성화 | 4h + 비용 | 예산 승인 | S3 §6.3 BUILD-02, R1 BUILD-02 (LOW) |
| FE-L11 | IPC E2E 테스트 환경 구축 | P3 | IPC invoke → 메인 핸들러 → HTTP fetch → 응답 경로의 통합 테스트 부재. 계약 기반 정적 테스트는 존재하나, 미테스트 채널: `bridge:run`, `bridge:stop`, `material:import-file`, `material:delete-file`, `project:saveConfigSurfaces`, `project:applyWorkGuardTemplate` | Spectron/Playwright 기반 E2E 테스트 환경 구축 + 핵심 IPC 채널 6건 통합 테스트 작성 | 16h | 테스트 프레임워크 선정 | S3 §6.3 TEST-01, R1 TEST-01 (LOW) |

### 2.4 INFO — 모니터링/참고

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S3 근거 |
|----|------|----------|------|-----------|-----------|--------|---------|
| FE-I01 | 500ms `setInterval` DOM 재구성 개선 | P4 | `index.html:8163-8166` — `renderMissionBoard()` + `renderAgentBoard()` 500ms마다 `innerHTML = ""` 전체 재생성. 5개 카드, 현대 브라우저에서 무시 가능 수준. | 상태 변경 이벤트 기반 업데이트로 전환 (미착수 허용) | 4h | 없음 | S3 §4.4, R2 UX-02 (INFO) |
| FE-I02 | Lucide 전체 번들 경량화 | P4 | `package.json:23` — `lucide ^0.577.0` 전체 설치(~600KB), 실제 사용 아이콘 1개(`pen-line`). 런타임 영향 없음. | SVG 인라인 또는 `lucide-static`으로 전환 | 1h | 없음 | S3 §6.4 Lucide full bundle |
| FE-I03 | 단일 파일 모놀리스 분리 | P4 | `index.html` 8,266줄에 CSS/HTML/JS 공존. 유지보수 부담. FE-M01(CSP unsafe-inline 제거)과 동일 장기 과제. | JS/CSS를 외부 파일로 분리 | 40h+ | FE-M01과 동시 진행 | S3 §6.4 단일 파일 모놀리스 |
| FE-I04 | addEventListener 63건 / removeEventListener 0건 (MISS-01) | P4 | 63개 `addEventListener`, 0개 `removeEventListener`. SPA 구조에서 모든 리스너가 고정 DOM 요소에 1회만 바인딩되므로 메모리 누수 없음. 향후 동적 요소 추가 시 주의 필요. | 향후 동적 요소 리스너 추가 시 cleanup 패턴 문서화 | 0h (현재 조치 불필요) | 없음 | S3 §6.4 MISS-01, R2 MISS-01 (INFO) |
| FE-I05 | Electron 보안 패치 정기 적용 체계 | P4 | `package.json:19` — Electron ^40.8.0 (Chromium 130 기반). 정기적 CVE 확인 필요. `^` 범위로 마이너 자동 적용되나, 메이저 업그레이드 체계 미비. | `npm audit` 월 1회 실행 + Electron 릴리스 노트 모니터링 프로세스 수립 | 1h/월 (정기) | 없음 | S3 §6.3 DEP-01 |
| FE-I06 | `_ws.onerror` 빈 핸들러 | P4 | `index.html:6221` — `_ws.onerror = () => {};`. WebSocket spec상 `onerror` 후 항상 `onclose` 발생하며, `onclose`에서 재연결/로그/UI 업데이트 모두 처리. 실질적 기능 누락 없음. | 디버깅 편의를 위해 `console.warn` 추가 (선택) | 0.25h | 없음 | S3 §4.6, R2 UX-04 (INFO) |
| FE-I07 | 포트 8300 충돌 처리 | P4 | `main.js:107` — 포트가 이미 사용 중이면 백엔드 기동 실패. splash에서 30초 후 실패 메시지(단, 8초 fallback이 먼저 발동). | 기동 전 포트 가용성 확인 또는 동적 포트 할당 | 3h | 없음 | R1 TEST-03 (LOW, INFO급 빈도) |
| FE-I08 | `extraResources` 무필터 번들링 | P4 | `package.json:41-70` — `filter: ["**/*"]`로 로그/백업/임시 파일 포함 가능. | `"!*.log"`, `"!*.tmp"`, `"!*.bak"` 제외 추가 | 0.5h | 없음 | R1 BUILD-04 (LOW) |

---

## 3. 공수 총괄

| 등급 | 건수 | 추정 총 공수 |
|------|------|-------------|
| HIGH | 1 | 0.5h |
| MEDIUM | 3 | 단기 11h + 장기 40h+ |
| LOW | 11 | 33h + 비용(코드 서명) |
| INFO | 8 | 50h+ (대부분 장기/선택) |
| **합계** | **23** | **단기 실행 ~45h + 장기 80h+** |

---

## 4. 삭제/기각 항목 (근거 포함)

R0 → R2 감리 과정에서 오탐 또는 과대평가로 삭제된 항목의 기록이다.

| 원 ID | 원 등급 | 삭제 사유 | 판정 라운드 |
|--------|---------|-----------|------------|
| SEC-03 | MEDIUM | `encodeURIComponent`가 `/`를 `%2F`로 인코딩 — HTTP 라우터가 경로 구분자로 해석하지 않아 경로 탈출 불가 | R1 |
| SEC-04 | LOW | localhost HTTP는 Electron 표준 패턴. 동일 시스템 공격자는 이미 전체 접근 보유 | R1 |
| SEC-09 | LOW | `taskkill /t`가 트리 종료 시도. Windows 부모 종료 시 대부분 자식 정리 | R1 |
| SEC-10 | LOW | 파일 임포트 덮어쓰기 — OS 다이얼로그가 사용자 의도 확인 선행 | R1 |
| SEC-11 | LOW | Windows symlink 생성에 관리자 권한 필요 (개발자 모드 예외). 공격 시나리오 비현실적 | R1 |
| UX-01 | HIGH→LOW | `escapeHtml` 적용률 ~95%. 미적용 3건은 `Number()` 변환 또는 상수 맵으로 보호. 백엔드가 자체 코드 | R1 |
| UX-03 | MEDIUM | JavaScript 단일 스레드 이벤트 루프에서 진정한 race condition 불가 | R1 |
| DEAD-01 | INFO | `workspace:get-path` 채널 — 의도적 보존 확인 (테스트에서 dead candidate로 표기) | R0 |

---

## 5. Severity Progression 추적 (R0 → R1 → R2 → 실행문서)

| 이슈 | R0 | R1 | R2 | 실행문서 | 변동 근거 |
|------|-----|-----|-----|---------|-----------|
| SEC-07 sanitizeProjectName | HIGH (R0) / MEDIUM (SSOT) | HIGH | HIGH | **HIGH** | Node.js 실행으로 경로 탈출 재확인. 3개 IPC 영향. |
| SEC-01 CSP unsafe-inline | HIGH | MEDIUM | MEDIUM | **MEDIUM** | `contextIsolation`이 Node.js API 차단. 피해 범위 bridge API 한정. |
| SEC-05 process.env 상속 | HIGH | MEDIUM | LOW | **LOW** | 개발 모드에서 제거 불가(PATH 필수). 프로덕션만 개선 가능. |
| SEC-02 bridge:run 미검증 | CRITICAL→MEDIUM | LOW | LOW | **LOW** | main은 투명 프록시. 입력 검증 책임은 백엔드. |
| SEC-06 평문 저장 | MEDIUM | LOW | LOW | **LOW** | Windows NTFS 사용자 프로필 격리 의존. |
| SEC-08 CSP connect-src | MEDIUM | LOW | LOW | **LOW** | 코드에서 미사용. 제거로 공격면 축소. |
| NEW-01 Settings IPC 크기 | MEDIUM (R1) | — | LOW | **LOW** | IPC structured clone + V8 메모리 제한이 자연 방어. |
| UX-02 500ms setInterval | MEDIUM | LOW | INFO | **INFO** | 5개 카드는 무시 가능 수준. |
| UX-04 onerror 공백 | MEDIUM | INFO (R2) | INFO | **INFO** | `onclose`가 동일 기능 수행. |
| UX-05 catch 무시 | MEDIUM | INFO (R2) | INFO | **INFO** (FE-L06으로 통합) | 대부분 의도적 fire-and-forget. |
| BUILD-03 python-embed | HIGH | MEDIUM | MEDIUM | **MEDIUM** | 빌드 스크립트 미확인. |
| TEST-02 .exe 테스트 | HIGH | MEDIUM | MEDIUM | **MEDIUM** | spike는 개발 모드만 커버. |
| BUILD-01 sprites 번들 | MEDIUM | LOW | LOW | **LOW** | 실제 canvas에 사용되는 sprite 존재. dbg_ 접두사만 제외. |
| BUILD-02 코드 서명 | MEDIUM | LOW | LOW | **LOW** | 비용 결정 — 기술 문제 아님. |
| TEST-01 IPC E2E | MEDIUM | LOW | LOW | **LOW** | 계약 테스트 존재하므로 E2E 부재는 보완적. |
| MISS-01 addEventListener 누수 | — | — | INFO | **INFO** | SPA 구조, 고정 DOM 바인딩, 메모리 누수 없음 확인. |

---

## 6. 긍정적 발견 (건전한 설계 요소)

감리 과정에서 확인된 올바른 설계를 기록한다. 향후 리팩토링 시 이 설계 원칙을 유지해야 한다.

| 항목 | 상태 | 비고 |
|------|------|------|
| `contextIsolation: true` | 정상 | 모든 윈도우에서 일관 적용 |
| `nodeIntegration: false` | 정상 | 렌더러의 Node.js API 접근 차단 |
| `webSecurity` 기본값 유지 | 정상 | 명시적 비활성화 없음 |
| IPC 계약 문서화 | 정상 | `desktop_control_plane_contract.js` 통합 관리 |
| Dead candidate 명시적 표기 | 정상 | 테스트에서 의도적 보존 검증 |
| 계약 기반 테스트 커버리지 | 정상 | preload/CSP/transport/packaging 계약 테스트 완비 |
| 설정 백업 자동 생성 | 정상 | `settings.json.bak` 자동 보존 |
| 경로 탈출 방지 (material delete) | 정상 | `..`, `/`, `\` 검증 적용 |
| 경로 탈출 방지 (WorkGuard template) | 정상 | `path.relative` + `startsWith("..")` + `isAbsolute` + 확장자 검증 — 완전한 방어 |
| 개발/프로덕션 모드 자동 전환 | 정상 | `app.isPackaged` 기반 분기 |
| 렌더러 콘솔 릴레이 | 정상 | warn/error만 선별 전달 (info 필터링) |

---

## 7. 감리 이력

### 7.1 3-Pass 기본 감리 (본 실행문서 작성 시)

| Pass | 관점 | 수행 내용 | 발견 |
|------|------|----------|------|
| Pass 1 | 완전성 검증 | S3 SSOT의 모든 항목(HIGH 1, MEDIUM 3, LOW 11, INFO 4)이 실행문서에 반영되었는지 전수 대조 | 누락 없음 확인. R0/R1/R2 소스에서 INFO급 추가 항목 7건(FE-I01~I08) 통합 반영. |
| Pass 2 | 우선순위/공수 정합성 | 각 항목의 우선순위가 severity와 일치하는지, 추정 공수가 상세 내용과 부합하는지 검증 | FE-L06(silent catch)의 추정 공수를 1h로 상향 (8건 개별 수정 필요). FE-L11(IPC E2E) 16h로 상향 (프레임워크 구축 포함). |
| Pass 3 | 의존성/실행순서 검증 | 의존성 체인이 올바른지, 순환 의존이 없는지 확인 | FE-L01(process.env)이 FE-M03(.exe 테스트)에 의존 — 프로덕션 모드 테스트 환경이 선행되어야 환경변수 필터링 검증 가능. 순환 없음. |

### 7.2 5-Pass 적대적 감리 (본 실행문서 작성 시)

| Pass | 관점 | 공격 시도 | 결과 |
|------|------|----------|------|
| Pass 1 | 누락 공격 | "S3 SSOT §6.3에서 LOW 11건이라 했는데, 실행문서에 LOW가 11건 맞는가?" | FE-L01~L11 = 11건 확인. S3 SSOT의 LOW 카테고리(process.env 상속, 미사용 CSP origin, IPC key whitelist 부재, window.prompt blocking, rAF infinite loop, NEW-01, SEC-06, BUILD-01, BUILD-02, TEST-01, DEP-01) 전수 매칭됨. |
| Pass 2 | Severity 과소평가 공격 | "FE-L01(process.env)이 LOW가 맞는가? R0에서 HIGH였다." | R2 적대적 감리에서 개발 모드 PATH 필수 + 프로덕션 모드만 개선 가능 + supply chain 공격 한정으로 LOW 판정. 2회 독립 적대적 감리 수렴 결과를 존중. 다만, 프로덕션 환경에서 AWS_SECRET_ACCESS_KEY 등이 backend.exe에 전달되는 시나리오는 여전히 유효하므로 "프로덕션 모드에서만" 조건부 P2로 실행 등록 완료. |
| Pass 3 | 완료기준 모호성 공격 | "FE-H01의 완료기준이 충분히 구체적인가? 단위 테스트 케이스가 명시되어 있는가?" | 화이트리스트 정규식 + `..`/`...` 방어 + 단위 테스트 3건 명시. 추가로 `sanitizeProjectName("../../etc")` = `"______etc"` (탈출 불가) 테스트 케이스 보강 필요 — 완료기준에 반영 완료. |
| Pass 4 | 의존성 누락 공격 | "FE-M01(CSP unsafe-inline)의 장기 과제가 FE-I03(모놀리스 분리)과 동일 작업인데 별도로 계상되어 있지 않는가?" | FE-I03 상세에 "FE-M01과 동시 진행" 의존성 명시 완료. 공수 이중 계상 아님 (FE-I03 공수 = "FE-M01 장기 과제에 포함"으로 해석). |
| Pass 5 | 삭제 항목 복원 공격 | "삭제된 UX-01(innerHTML escapeHtml)이 정말 안전한가? 백엔드가 해킹되면?" | R1 전수 대조: 미이스케이프 3건 중 실질 위험 사례 0건(Number 변환, 상수 맵, 하드코딩 HTML). 백엔드 해킹 시나리오는 S3 프론트엔드 범위 외(백엔드 보안은 별도 SSOT). FE-L06(silent catch)에서 에러 로깅 추가하면 백엔드 이상 응답 조기 감지 가능. 삭제 유지. |

### 7.3 감리 결과 요약

- 3-Pass 기본 감리: 누락 0건, 공수 2건 보정, 의존성 1건 확인
- 5-Pass 적대적 감리: 복원 0건, 완료기준 1건 보강(FE-H01 테스트 케이스 추가), Severity 변경 0건
- **최종 판정: 실행문서 확정. 추가 감리 불필요.**

---

## 8. 실행 로드맵

```
Week 1 (즉시):
  [FE-H01] sanitizeProjectName 수정 ─────────── 0.5h
  [FE-L02] CSP connect-src 외부 API 제거 ──────── 0.5h (FE-M01 단기 완화)

Week 2-3:
  [FE-M02] python-embed 버전 고정 ───────────── 2h
  [FE-L04] window.prompt → 커스텀 모달 ─────── 2h
  [FE-L05] rAF 조건부 정지 ────────────────── 1.5h
  [FE-L06] silent catch 로깅 추가 ──────────── 1h
  [FE-L07] Settings IPC 크기 제한 ──────────── 0.5h
  [FE-L09] sprites 번들 최적화 ─────────────── 0.5h

Week 4-6:
  [FE-M03] .exe 통합 테스트 환경 구축 ────────── 8h
  [FE-L01] process.env 필터링 (프로덕션) ───── 2h (FE-M03 완료 후)
  [FE-L03] bridge:run key 화이트리스트 ─────── 1h
  [FE-L08] 평문 저장 개선 ─────────────────── 4h

분기 내 (백로그):
  [FE-L10] 코드 서명 ──────────────────────── 4h + 비용
  [FE-L11] IPC E2E 테스트 ──────────────────── 16h
  [FE-I01~I08] INFO 항목들 ─────────────────── 필요 시 착수
```

---

## 9. 부록: 관련 SSOT 참조

| 참조 | 내용 |
|------|------|
| S1 | 전체 아키텍처 개관 — 프론트엔드 위치 확인 |
| S2 | BE-FE 연결 — IPC 프로토콜 전체 스펙, bridgeFetch 상세 |
| S3 | 프론트엔드 (Electron) SSOT — 본 실행문서의 원본 |
| S4 | LLM 통합 — WebSocket 경유 실시간 스트리밍 관련 |
| S5 | Stage 0-2 내부 — 프론트엔드에서 트리거하는 파이프라인 시작점 |

---

*끝 — S3 프론트엔드 (Electron) 실행문서*
