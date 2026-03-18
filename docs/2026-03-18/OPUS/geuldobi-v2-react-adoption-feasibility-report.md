# 글도비 v2 프론트엔드 React 도입 타당성 보고서

> **작성일**: 2026-03-18
> **요청**: 현재 프론트엔드 프레임워크 현황 + React 도입 타당성 평가
> **근거**: S2 (BE-FE SSOT), S3 (프론트엔드 SSOT), 코드 실측

---

## 1. 현재 프론트엔드 현황

### 1.1 기술 스택

| 항목 | 현재 값 |
|------|---------|
| **프레임워크** | **없음 (바닐라 JavaScript)** |
| 번들러 | 없음 (webpack/vite 없음) |
| 트랜스파일러 | 없음 (TypeScript/Babel 없음) |
| 패키지 매니저 | npm (dependencies: lucide 1개만) |
| 데스크톱 셸 | Electron 40.8.0 |
| 빌드 | electron-builder 25.1.8 (NSIS, Windows) |
| 외부 라이브러리 | lucide ^0.577.0 (아이콘) — **유일** |

### 1.2 파일 구조

```
geuldobi-desktop/src/           총 9,723행
├── index.html          8,266행  ← 전체의 85%. CSS+HTML+JS 인라인 모놀리스
├── main.js             1,009행  ← Electron 메인 프로세스 + IPC 핸들러 25개
├── preload.js             96행  ← contextBridge IPC 브릿지
├── desktop_control_plane_contract.js  96행  ← IPC 채널 상수
├── console_relay.js       56행  ← 콘솔 릴레이
├── splash/splash.js       89행  ← 스플래시 폴링
├── splash/splash.html     27행  ← 스플래시 마크업
└── splash/splash.css      84행  ← 스플래시 스타일
```

### 1.3 index.html 내부 분해

| 영역 | 행수 | 비중 |
|------|------|------|
| CSS (인라인 `<style>`) | ~2,765 | 33% |
| HTML 마크업 | ~714 | 9% |
| JavaScript (인라인 `<script>`) | ~4,778 | 58% |

### 1.4 JS 코드 특성 (index.html 내부)

| 지표 | 수치 | 의미 |
|------|------|------|
| 함수/화살표 함수 | 134개 | 중형 SPA급 |
| innerHTML 사용 | 50회 | DOM 직접 조작 (React의 가장 큰 대체 대상) |
| addEventListener | 63회 | 이벤트 바인딩 수동 관리 |
| setInterval/setTimeout | 5회 | 타이머 기반 갱신 |
| 전역 상태 변수 | 13개 | officeState(30+ 하위 필드) + 12개 분산 let |
| escapeHtml 유틸리티 | 1개 | ~95% innerHTML에서 사용, ~5% 미사용 |
| silent .catch(() => {}) | 8곳 | 에러 삼킴 패턴 |

### 1.5 현재 아키텍처의 장단점

**장점**:
- 빌드 단계 0 — 수정 → 새로고침 즉시 반영
- 의존성 1개(lucide) — 공급망 리스크 극소
- Electron contextIsolation=true, nodeIntegration=false — 보안 경계 명확
- 전체 코드가 1 파일 — 검색/이해 단순

**단점**:
- 8,266행 단일 파일 — 협업/분할 불가
- 50회 innerHTML 수동 DOM 조작 — XSS 표면, 유지보수 부담
- 13개 전역 상태 — 상태 흐름 추적 어려움
- 63개 addEventListener — 해제 0건 (메모리 누수 잠재)
- CSS/HTML/JS 분리 불가 — 스타일 변경이 코드 전체에 영향
- 테스트 불가 — 컴포넌트 단위 테스트 구조 없음

---

## 2. React 도입 시나리오 분석

### 2.1 시나리오 A: 전면 재작성 (Big Bang)

```
현재: index.html (8,266행 모놀리스)
  ↓ 전면 재작성
목표: React + TypeScript + Vite
  src/
  ├── App.tsx
  ├── components/
  │   ├── Office/        (오피스 캔버스, 에이전트 보드)
  │   ├── Mission/       (미션 카드, 품질 신호)
  │   ├── Console/       (로그 스트림, 프롬프트 UI)
  │   ├── Settings/      (API 키, 프로젝트 설정)
  │   └── Quality/       (품질 대시보드, 레이더)
  ├── hooks/
  │   ├── useWebSocket.ts    (WS 연결 + 자동 재연결)
  │   ├── useIPC.ts          (preload 브릿지 래핑)
  │   └── useOfficeState.ts  (전역 상태 → zustand/jotai)
  ├── store/
  │   └── officeStore.ts     (13개 전역 → 단일 스토어)
  └── types/
      └── events.ts          (WS 이벤트 타입 정의)
```

| 항목 | 추정 |
|------|------|
| 작업량 | **3-5주** (1인 FE 기준) |
| 리스크 | 높음 — 기존 동작 회귀 가능, QA 전면 재필요 |
| 이점 | 컴포넌트화, 타입 안전, 테스트 가능, 협업 가능 |
| 빌드 체인 추가 | Vite + TypeScript + React + electron-vite |
| 번들 크기 변화 | ~150KB (React) + ~50KB (zustand) 추가 |

### 2.2 시나리오 B: 점진적 마이그레이션 (Strangler Fig)

```
Phase 1 (1주): 빌드 체인 도입
  - Vite + electron-vite 설정
  - index.html을 entry point로 유지
  - CSS를 별도 파일로 분리 (2,765행)

Phase 2 (1주): React 루트 설치
  - <div id="react-root"> 추가
  - 새 기능만 React 컴포넌트로 작성
  - 기존 바닐라 JS 코드는 그대로 유지

Phase 3 (2-3주): 점진적 전환
  - 독립 영역부터 React 컴포넌트화:
    1. Settings 패널 (가장 독립적)
    2. Quality Dashboard (데이터 표시 위주)
    3. Console/Log Stream (리스트 렌더링)
    4. Mission Board (카드 컴포넌트)
    5. Office Canvas (마지막 — 가장 복잡)
  - 각 전환 시 기존 바닐라 코드 삭제

Phase 4 (1주): 전역 상태 마이그레이션
  - officeState → zustand/jotai 스토어
  - 13개 분산 let → 단일 스토어
```

| 항목 | 추정 |
|------|------|
| 작업량 | **5-7주** (1인 FE 기준, 각 Phase 검증 포함) |
| 리스크 | 중간 — 기존 동작 유지하며 점진적 전환 |
| 이점 | 회귀 리스크 최소화, 중간 릴리스 가능 |
| 단점 | 전환 기간 동안 바닐라+React 혼재 |

### 2.3 시나리오 C: 프레임워크 미도입 (현상 유지 + 구조화)

```
Phase 1: 파일 분리
  - index.html → index.html + office.js + mission.js + console.js + settings.js + quality.js
  - CSS → styles.css 분리

Phase 2: 모듈 패턴
  - 즉시 실행 함수(IIFE) 또는 ES Module로 네임스페이스 분리
  - 전역 상태를 단일 객체로 통합

Phase 3: 최소 라이브러리
  - lit-html (2KB) 또는 htm+preact (4KB) — 템플릿 리터럴 기반 렌더링
  - innerHTML 50건 → tagged template 전환
```

| 항목 | 추정 |
|------|------|
| 작업량 | **1-2주** (파일 분리 + 모듈화) |
| 리스크 | 낮음 — 기존 코드 재배치, 동작 변경 최소 |
| 이점 | 빠르고, 빌드 체인 불필요, 의존성 최소 유지 |
| 단점 | 근본적 한계 미해결 (타입 없음, 테스트 어려움, 컴포넌트 미분리) |

---

## 3. 의사결정 매트릭스

| 기준 | 가중치 | A (전면 재작성) | B (점진적) | C (현상 유지) |
|------|--------|---------------|-----------|-------------|
| 개발 기간 | 25% | 3-5주 (**4**) | 5-7주 (**2**) | 1-2주 (**9**) |
| 회귀 리스크 | 25% | 높음 (**3**) | 중간 (**6**) | 낮음 (**9**) |
| 장기 유지보수성 | 20% | 최상 (**10**) | 상 (**8**) | 하 (**3**) |
| 협업 가능성 | 15% | 최상 (**10**) | 상 (**8**) | 중하 (**4**) |
| 현재 릴리스 영향 | 15% | 차단 (**1**) | 부분 차단 (**5**) | 무영향 (**10**) |
| **가중 점수** | 100% | **5.15** | **5.50** | **7.05** |

---

## 4. 권장안

### 4.1 단기 (지금 ~ 1.6.0 릴리스): **시나리오 C**

현재 **1.6.0 릴리스가 최우선** (memo.md 계획). React 도입은 릴리스를 차단한다.

즉시 실행 가능한 최소 개선:
1. CSS 분리 (`index.html` → `index.html` + `styles.css`) — 2,765행 감소
2. JS를 3-4개 파일로 분리 (office.js, console.js, settings.js, quality.js)
3. `officeState` + 12개 분산 let → 단일 `AppState` 객체 통합

예상 결과: 8,266행 → 4개 파일 각 1,000-2,000행, 협업 기초 마련.

### 4.2 중기 (1.6.0 이후 ~ 2.0.0): **시나리오 B Phase 1-2**

1.6.0 안정화 후 빌드 체인(Vite + electron-vite) 도입, React 루트 설치. 새 기능은 React로, 기존은 유지.

### 4.3 장기 (2.0.0 이후): **시나리오 B Phase 3-4**

점진적으로 바닐라 → React 전환. Office Canvas가 마지막 (가장 복잡하고 Canvas API 의존).

### 4.4 비권장: 시나리오 A

전면 재작성은 현 단계에서 **리스크 대비 이점 불충분**:
- 1인 개발 체제에서 3-5주 FE 차단 = 백엔드 개발 중단
- 현재 FE가 **기능적으로 동작** (보안 이슈 1 HIGH 있으나 로컬 전용이므로 수용 가능)
- 2.0.0 목표 4월 달성 가능성에 치명적 영향

---

## 5. React 도입 시 기술 선택 권장

React를 최종적으로 도입한다면:

| 항목 | 권장 | 이유 |
|------|------|------|
| 프레임워크 | **React 19** | 최신 안정, Electron 호환 검증 |
| 언어 | **TypeScript 5.x** | 8,266행 규모에서 타입 안전 필수 |
| 번들러 | **Vite 6 + electron-vite** | Electron 특화, HMR 지원 |
| 상태 관리 | **zustand** (3KB) | 경량, 보일러플레이트 최소, 현재 officeState 패턴과 유사 |
| CSS | **CSS Modules** 또는 **Tailwind** | 현재 인라인 CSS 2,765행 분리 필요 |
| 테스트 | **Vitest + Testing Library** | Vite 네이티브 통합 |
| IPC 래퍼 | 커스텀 훅 `useIPC()` | preload.js의 `window.geuldobiDesktop` 래핑 |
| WS 래퍼 | 커스텀 훅 `useWebSocket()` | 현재 수동 WS 관리 → 자동 재연결 + 타입 이벤트 |

---

## 6. 수치 비교 요약

| 지표 | 현재 (바닐라) | React 전환 후 (예상) |
|------|-------------|-------------------|
| 소스 파일 수 | 3 (main.js, preload.js, index.html) | ~30-50 (컴포넌트 파일) |
| 최대 파일 크기 | 8,266행 | ~200-400행/파일 |
| innerHTML 직접 조작 | 50회 | **0회** (JSX 가상 DOM) |
| addEventListener 수동 바인딩 | 63회 | **0회** (React 이벤트 시스템) |
| 전역 상태 변수 | 13개 분산 | 1개 스토어 (zustand) |
| 단위 테스트 가능성 | 불가 | **가능** (Testing Library) |
| 타입 안전 | 없음 | **전면** (TypeScript) |
| 번들 크기 추가 | 0 | ~200KB (React+zustand+lucide) |
| 빌드 시간 추가 | 0 | ~3-5초 (Vite HMR) |
| 의존성 수 | 1 (lucide) | ~15-20 (React 에코시스템) |

---

## 7. 결론

**현재 프레임워크**: 없음 (바닐라 JS 8,266행 모놀리스).

**React 도입 판단**: 장기적으로 **필요**하나, 현 시점에서는 **시기상조**.

- **지금**: 파일 분리 + 모듈화 (시나리오 C, 1-2주)
- **1.6.0 이후**: Vite + React 루트 설치 (시나리오 B Phase 1-2, 2주)
- **2.0.0 이후**: 점진적 컴포넌트 전환 (시나리오 B Phase 3-4, 3-4주)
- **전면 재작성**: 비권장 (1인 체제에서 3-5주 차단, 릴리스 목표 위협)
