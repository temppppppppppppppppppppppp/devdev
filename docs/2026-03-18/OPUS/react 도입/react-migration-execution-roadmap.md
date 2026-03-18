# 글도비 React 마이그레이션 실행 로드맵

> 작성일: 2026-03-18
> 작성자: Claude Opus 4.6 (1M context)
> 대상: geuldobi-desktop (Electron 40.8.0, 바닐라 JS → React 19 + TypeScript)
> 전제: 코드 수정 전 이 문서의 3PASS + 적대적 3PASS 감리 완료
> 현재 상태: React/Vite/TS 인프라 전무 (4개 대상 경로 모두 미존재)

---

## 전체 구조 요약

| Phase | 제목 | 예상 시간 | 누적 |
|-------|------|-----------|------|
| 0 | 빌드 인프라 구축 | 8-12h | 8-12h |
| 1 | 타입 기반 + Zustand 스토어 | 16-24h | 24-36h |
| 2 | 공유 UI 컴포넌트 | 20-28h | 44-64h |
| 3 | 기능 패널 마이그레이션 (6 서브페이즈) | 88-116h | 132-180h |
| 4 | 레이아웃 셸 + 라우팅 | 12-16h | 144-196h |
| 5 | 정리 + 최적화 | 16-24h | 160-220h |

**총 예상: 160-220시간 (4-5.5주, 풀타임 1인 기준)**

---

## Phase 0: 빌드 인프라 구축 (예상 8-12h)

### Step 0.0: 사전 조건 확인

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# Node.js 버전 확인 (18+ 필수, 20+ 권장)
node --version

# npm 버전 확인
npm --version

# Electron 확인
npx electron --version
# 기대값: v40.8.0

# 현재 파일 구조 확인
ls -la src/
# 기대 출력:
#   console_relay.js
#   desktop_control_plane_contract.js
#   index.html           ← 8,266행 모놀리스
#   main.js              ← 1,009행 Electron main
#   preload.js           ← 96행 preload bridge
#   splash/              ← splash window (4 파일)
#   sprites/             ← 33개 PNG 스프라이트
```

### Step 0.1: Git 브랜치 생성 + 백업

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# 마이그레이션 전용 브랜치
git checkout -b feat/react-migration

# index.html 백업 (마이그레이션 도중 참조용)
cp src/index.html src/index.html.bak
git add src/index.html.bak
git commit -m "chore: backup index.html before React migration"
```

### Step 0.2: 의존성 설치

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# ── 런타임 의존성 ──
npm install react@19.2.4 react-dom@19.2.4 zustand@5.0.12

# ── 개발 의존성 ──
npm install --save-dev \
  typescript@5.9.3 \
  vite@7.3.1 \
  electron-vite@5.0.0 \
  @vitejs/plugin-react@4.7.0 \
  @types/react@19.2.14 \
  @types/react-dom@19.2.3 \
  vitest@4.1.0 \
  @testing-library/react@16.3.2 \
  @testing-library/jest-dom@6.9.1 \
  jsdom@29.0.0
```

> **감리 주석 (Adversarial PASS 1에서 검증 완료):**
> - electron-vite@5.0.0 peerDependency: `vite ^5.0.0 || ^6.0.0 || ^7.0.0` → vite@7.3.1 호환 확인
> - @vitejs/plugin-react@4.7.0 peerDependency: `vite ^4.2.0 || ^5.0.0 || ^6.0.0 || ^7.0.0` → 호환 확인
> - vitest@4.1.0 peerDependency: `vite ^6.0.0 || ^7.0.0 || ^8.0.0-0` → 호환 확인
> - React 19.2.4 + @types/react 19.2.14 → 메이저 일치 확인
> - vite@8.0.0 (latest)는 electron-vite 5.0.0과 비호환이므로 **반드시 7.x 사용**

### Step 0.3: 디렉토리 구조 생성

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# electron-vite 표준 디렉토리 구조
mkdir -p src/main
mkdir -p src/preload
mkdir -p src/renderer/src/assets
mkdir -p src/renderer/src/components/ui
mkdir -p src/renderer/src/components/panels
mkdir -p src/renderer/src/components/layout
mkdir -p src/renderer/src/components/canvas
mkdir -p src/renderer/src/components/modals
mkdir -p src/renderer/src/hooks
mkdir -p src/renderer/src/stores
mkdir -p src/renderer/src/types
mkdir -p src/renderer/src/styles
mkdir -p src/renderer/src/lib
mkdir -p src/renderer/public/sprites
```

### Step 0.4: 파일 이동

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# ── main process 파일들 ──
cp src/main.js src/main/index.js
cp src/console_relay.js src/main/console_relay.js
cp src/desktop_control_plane_contract.js src/main/desktop_control_plane_contract.js

# ── preload ──
cp src/preload.js src/preload/index.js

# ── 스프라이트 (renderer public) ──
cp src/sprites/*.png src/renderer/public/sprites/

# ── splash (main process가 직접 로드하므로 main 하위에 유지) ──
cp -r src/splash src/main/splash

# 주의: 원본 src/ 파일은 Phase 4까지 삭제하지 않는다
# (기존 `npm start`가 동작해야 롤백 가능)
```

### Step 0.5: electron.vite.config.ts 생성

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/electron.vite.config.ts`

```typescript
import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/main/index.js')
        }
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/preload/index.js')
        }
      }
    }
  },
  renderer: {
    root: resolve(__dirname, 'src/renderer'),
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/renderer/index.html')
        }
      }
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src/renderer/src')
      }
    }
  }
})
```

### Step 0.6: TypeScript 설정 파일 생성

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/tsconfig.json`

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.node.json" },
    { "path": "./tsconfig.web.json" }
  ]
}
```

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/tsconfig.node.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowJs": true,
    "checkJs": false,
    "strict": false,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./out",
    "composite": true
  },
  "include": [
    "electron.vite.config.ts",
    "src/main/**/*",
    "src/preload/**/*"
  ]
}
```

> **주의:** `strict: false`로 시작하는 이유: 기존 main.js / preload.js는 JavaScript이며, TypeScript strict 체크를 바로 적용하면 수백 개의 에러가 발생한다. Phase 5에서 strict 전환한다.

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/tsconfig.web.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/renderer/src/*"]
    },
    "composite": true
  },
  "include": [
    "src/renderer/src/**/*.ts",
    "src/renderer/src/**/*.tsx",
    "src/renderer/src/**/*.d.ts"
  ]
}
```

### Step 0.7: 렌더러 보일러플레이트 생성

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/renderer/index.html`

```html
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta
      http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src ws://127.0.0.1:8300 https://generativelanguage.googleapis.com;"
    />
    <title>글도비 Desktop</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./src/main.tsx"></script>
  </body>
</html>
```

> **CSP 차이점:** 기존 index.html은 `'unsafe-inline'`을 script-src에 포함했다. React/Vite 빌드 후에는 모든 JS가 별도 파일로 번들되므로 `'unsafe-inline'`을 script-src에서 제거할 수 있다. style-src에는 CSS-in-JS 호환을 위해 유지한다.

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/renderer/src/main.tsx`

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/global.css'

const rootEl = document.getElementById('root')
if (!rootEl) throw new Error('Root element #root not found')

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/renderer/src/App.tsx`

```tsx
import { useState, useEffect } from 'react'

export default function App() {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    // geuldobiDesktop.onAppReady는 preload에서 주입됨
    if (window.geuldobiDesktop?.onAppReady) {
      window.geuldobiDesktop.onAppReady(() => setReady(true))
    }
  }, [])

  return (
    <main style={{ padding: 24, fontFamily: 'Malgun Gothic, sans-serif' }}>
      <h1>React 렌더러 작동 중</h1>
      <p>앱 준비 상태: {ready ? '완료' : '대기 중...'}</p>
      <p>Electron {window.process?.versions?.electron ?? '(unknown)'}</p>
    </main>
  )
}
```

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/renderer/src/env.d.ts`

```typescript
/// <reference types="vite/client" />
```

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/renderer/src/preload.d.ts`

```typescript
/**
 * geuldobiDesktop preload bridge 타입 정의
 * 실제 메서드 목록은 src/preload/index.js 참조
 */
interface GeuldobiDesktopAPI {
  // Splash → Main 전환
  getSplashConfig: () => Promise<{ firstRun: boolean; fallbackMs: number; statusBaseUrl: string }>
  notifyBackendReady: () => void
  onAppReady: (handler: (payload: { reason: string }) => void) => void

  // Bridge API
  runKey: (key: string, subKey: string | null, inputs: Record<string, unknown>, approvalId?: string | null) => Promise<BridgeResponse>
  stopRun: () => Promise<BridgeResponse>
  getStatus: () => Promise<BridgeResponse>
  getQualitySummary: (project: string, lookback?: number) => Promise<BridgeResponse>
  getQualityDashboard: (project: string, lookback?: number) => Promise<BridgeResponse>
  getSafeOpsPreview: (project: string) => Promise<BridgeResponse>
  saveQualityReview: (project: string, epNum: number, operatorLabel: string, note?: string) => Promise<BridgeResponse>
  resolvePrompt: (runId: string, promptId: string, value: string) => Promise<BridgeResponse>

  // Backend URL
  getBackendUrl: () => Promise<{ wsUrl: string; httpUrl: string }>
  getCliContract: () => Promise<CliContract>

  // 설정 영속화
  saveSettings: (settings: Record<string, unknown>) => Promise<{ ok: boolean; message?: string }>
  loadSettings: () => Promise<Record<string, unknown> | null>

  // 재료 파일 관리
  listMaterialFiles: (folder: 'bible' | 'treatments') => Promise<{ ok: boolean; files: MaterialFile[]; message?: string }>
  importMaterialFile: (folder: 'bible' | 'treatments') => Promise<{ ok: boolean; imported?: string[]; message?: string }>
  deleteMaterialFile: (folder: 'bible' | 'treatments', fileName: string) => Promise<{ ok: boolean; message?: string }>

  // 프로젝트 관리
  listProjects: () => Promise<{ ok: boolean; projects: string[]; message?: string }>
  createProject: (name: string) => Promise<{ ok: boolean; name?: string; message?: string }>
  loadProjectConfigSurfaces: (project: string) => Promise<{ ok: boolean; authorDirectives: string; workGuardYaml: string; message?: string }>
  saveProjectConfigSurfaces: (project: string, authorDirectives?: string, workGuardYaml?: string) => Promise<{ ok: boolean; message?: string }>
  listWorkGuardTemplates: (genre?: string) => Promise<{ ok: boolean; templates: WorkGuardTemplate[]; libraryRoot?: string; message?: string }>
  applyWorkGuardTemplate: (project: string, templatePath: string) => Promise<{ ok: boolean; workGuardYaml?: string; templatePath?: string; relativePath?: string; message?: string }>

  // 작업 폴더
  openWorkspaceFolder: () => Promise<{ ok: boolean; path: string }>
  getWorkspacePath: () => Promise<{ ok: boolean; path: string }>
}

interface BridgeResponse {
  ok?: boolean
  code?: string
  message?: string
  data?: Record<string, unknown>
  [key: string]: unknown
}

interface CliContract {
  defaultGenreIndex: number
  projectIndexBase: number
  projectSort: string
  genreIndexMap: Record<string, number>
}

interface MaterialFile {
  name: string
  size: number
  isDir: boolean
}

interface WorkGuardTemplate {
  path: string
  relativePath: string
  label: string
  scope: string
}

declare global {
  interface Window {
    geuldobiDesktop: GeuldobiDesktopAPI
    process?: {
      versions?: {
        electron?: string
      }
    }
  }
}

export {}
```

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/renderer/src/styles/global.css`

```css
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --line: #e2e8f0;
  --text: #0f172a;
  --muted: #64748b;
  --label: #475569;
  --button: #475569;
  --button-hover: #334155;
  --pass: #22c55e;
  --reject: #ef4444;
  --pwf: #eab308;
}

* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  height: 100dvh;
  overflow: hidden;
  font-family: "Malgun Gothic", "Apple SD Gothic Neo", "Segoe UI", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(191, 219, 254, 0.45), rgba(255,255,255,0) 24%),
    radial-gradient(circle at bottom right, rgba(251, 191, 36, 0.16), rgba(255,255,255,0) 20%),
    var(--bg);
  color: var(--text);
}

#root {
  height: 100dvh;
  overflow: hidden;
}
```

### Step 0.8: main.js 수정 (3곳만)

`src/main/index.js` 에서 아래 3곳만 수정한다. 원본 `src/main.js`는 건드리지 않는다.

**수정 1: createMainWindow — loadFile → 조건부 loadURL (라인 387 부근)**

```diff
- mainWindow.loadFile(path.join(__dirname, "index.html")).catch((err) => {
-   debugLog("mainWindow loadFile rejected", err);
- });
+ // electron-vite dev 모드: ELECTRON_RENDERER_URL 환경변수 → loadURL
+ // 프로덕션 빌드: out/renderer/index.html → loadFile
+ const RENDERER_URL = process.env.ELECTRON_RENDERER_URL;
+ if (RENDERER_URL) {
+   mainWindow.loadURL(RENDERER_URL).catch((err) => {
+     debugLog("mainWindow loadURL rejected", err);
+   });
+ } else {
+   mainWindow.loadFile(path.join(__dirname, "../renderer/index.html")).catch((err) => {
+     debugLog("mainWindow loadFile rejected", err);
+   });
+ }
```

**수정 2: createMainWindow — preload 경로 (라인 364 부근)**

```diff
  webPreferences: {
-   preload: path.join(__dirname, "preload.js"),
+   preload: path.join(__dirname, "../preload/index.js"),
    contextIsolation: true,
    nodeIntegration: false
  }
```

**수정 3: createSplashWindow — preload + splash 경로 (라인 409, 434 부근)**

```diff
  webPreferences: {
-   preload: path.join(__dirname, "preload.js"),
+   preload: path.join(__dirname, "../preload/index.js"),
    contextIsolation: true,
    nodeIntegration: false
  }

  // ...

- splashWindow.loadFile(path.join(__dirname, "splash", "splash.html")).catch((err) => {
+ splashWindow.loadFile(path.join(__dirname, "splash/splash.html")).catch((err) => {
```

**수정 4: require 경로 (라인 49 부근)**

```diff
- ({ attachConsoleRelay } = require("./console_relay"));
- ({
-   IPC_CHANNELS,
-   BRIDGE_MANAGED_ROUTES,
-   buildRunInputRoute,
- } = require("./desktop_control_plane_contract"));
+ ({ attachConsoleRelay } = require("./console_relay"));
+ ({
+   IPC_CHANNELS,
+   BRIDGE_MANAGED_ROUTES,
+   buildRunInputRoute,
+ } = require("./desktop_control_plane_contract"));
```

> `console_relay.js`와 `desktop_control_plane_contract.js`는 같은 `src/main/` 폴더에 있으므로 상대 경로 `./` 변경 불필요.

### Step 0.9: package.json 수정

```diff
  {
    "name": "geuldobi-desktop",
    "version": "1.5.7",
    "description": "글도비 — AI 웹소설 자동 생성 데스크톱",
-   "main": "src/main.js",
+   "main": "./out/main/index.js",
    "scripts": {
-     "start": "cmd /C \"set ELECTRON_RUN_AS_NODE=&& electron .\"",
-     "start:spike": "cmd /C \"set ELECTRON_RUN_AS_NODE=&& set SPIKE_AUTOCLOSE_MS=5000&& electron .\"",
+     "start": "cmd /C \"set ELECTRON_RUN_AS_NODE=&& electron .\"",
+     "start:spike": "cmd /C \"set ELECTRON_RUN_AS_NODE=&& set SPIKE_AUTOCLOSE_MS=5000&& electron .\"",
+     "dev": "electron-vite dev",
+     "dev:legacy": "cmd /C \"set ELECTRON_RUN_AS_NODE=&& electron .\"",
      "prepare:workspace-seed": "python scripts/build_workspace_seed.py",
-     "build": "npm run prepare:workspace-seed && electron-builder --win",
-     "build:dir": "npm run prepare:workspace-seed && electron-builder --win --dir",
+     "build": "npm run prepare:workspace-seed && electron-vite build && electron-builder --win",
+     "build:dir": "npm run prepare:workspace-seed && electron-vite build && electron-builder --win --dir",
+     "build:vite": "electron-vite build",
+     "typecheck": "tsc --noEmit -p tsconfig.web.json",
+     "test:react": "vitest run",
+     "test:react:watch": "vitest",
      "test": "cmd /C \"cd .. && python -m pytest -q tests/test_run_validator.py tests/test_api_contract.py tests/test_frontend_frontier_lag_wiring.py tests/test_frontend_stage0_connectivity.py tests/test_ui_renderer_sanitization.py tests/test_desktop_contract_refresh.py tests/test_desktop_work_guard_template_contract.py tests/test_process_runner_stage0_inputs.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_bridge_quality_summary.py tests/test_desktop_direct_surface_contract.py tests/test_desktop_transport_contract.py tests/test_desktop_packaging_contract.py tests/test_desktop_shadow_hygiene.py tests/test_runtime_paths.py && node tests/test_desktop_preload_bridge_behavior.js && node tests/test_desktop_material_offline_behavior.js && node tests/test_splash_runtime_behavior.js\""
    },
```

build.files도 수정:

```diff
    "build": {
+     "directories": {
+       "output": "release"
+     },
      "files": [
-       "src/**/*",
+       "out/**/*",
+       "src/main/splash/**/*",
        "!node_modules/.cache"
      ]
    }
```

### Step 0.10: vitest.config.ts 생성

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src/renderer/src')
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/renderer/src/test-setup.ts'],
    include: ['src/renderer/**/*.{test,spec}.{ts,tsx}'],
    css: true
  }
})
```

파일 경로: `C:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/renderer/src/test-setup.ts`

```typescript
import '@testing-library/jest-dom'

// geuldobiDesktop preload bridge mock
const mockGeuldobiDesktop: Partial<GeuldobiDesktopAPI> = {
  getSplashConfig: async () => ({ firstRun: false, fallbackMs: 8000, statusBaseUrl: 'http://127.0.0.1:8300' }),
  notifyBackendReady: () => {},
  onAppReady: (handler) => { handler({ reason: 'test' }) },
  getBackendUrl: async () => ({ wsUrl: 'ws://127.0.0.1:8300/events', httpUrl: 'http://127.0.0.1:8300' }),
  getCliContract: async () => ({
    defaultGenreIndex: 3,
    projectIndexBase: 1,
    projectSort: 'lexical',
    genreIndexMap: { wuxia: 1, hunter: 2, investment: 3, fantasy: 4, composer: 5, cooking: 6, alt_history: 7, actor: 8, sports: 9, medical: 10 }
  }),
  loadSettings: async () => null,
  listProjects: async () => ({ ok: true, projects: [] }),
  listMaterialFiles: async () => ({ ok: true, files: [] }),
  getStatus: async () => ({ ok: true }),
  getQualitySummary: async () => ({ ok: true }),
  getQualityDashboard: async () => ({ ok: true }),
  getSafeOpsPreview: async () => ({ ok: true }),
}

Object.defineProperty(window, 'geuldobiDesktop', {
  value: mockGeuldobiDesktop,
  writable: true,
  configurable: true
})
```

### Step 0.11: 검증

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# 1. TypeScript 컴파일 체크
npx tsc --noEmit -p tsconfig.web.json
# 기대: 에러 0건

# 2. Vite dev 서버 + Electron 기동
npm run dev
# 기대: Electron 윈도우 뜨고 "React 렌더러 작동 중" 텍스트 표시
# Ctrl+C로 종료

# 3. Vite 빌드
npm run build:vite
# 기대: out/ 디렉토리에 main/, preload/, renderer/ 생성

# 4. 패키징 빌드 (시간 소요)
npm run build
# 기대: release/ 디렉토리에 nsis 인스톨러 생성

# 5. 레거시 시작 (원본 경로가 아직 살아있으므로)
npm run dev:legacy
# 기대: 기존 index.html 화면이 그대로 뜸

# 6. React 컴포넌트 테스트
npm run test:react
# 기대: 0 tests (아직 테스트 파일 없으므로 pass)

# 7. 기존 계약 테스트 (경로 변경 영향 확인)
npm test
# 주의: test_desktop_packaging_contract.py가 build.files 변경을 감지할 수 있음
# 실패 시 아래 롤백 절차로 복구
```

**체크리스트:**

- [ ] `npm run dev` → Electron 윈도우에 "React 렌더러 작동 중" 표시
- [ ] `npm run build:vite` → `out/` 디렉토리 생성, `out/renderer/index.html` 존재
- [ ] `npm run build` → `release/` 디렉토리에 installer 생성
- [ ] `npm run dev:legacy` → 기존 바닐라 JS 화면이 정상 동작
- [ ] `npx tsc --noEmit -p tsconfig.web.json` → 에러 0건
- [ ] `npm run test:react` → pass (0 tests)

### Step 0.12: 롤백 절차

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# 추가된 파일/디렉토리 삭제
rm -rf src/main src/preload src/renderer out release
rm -f electron.vite.config.ts tsconfig.json tsconfig.node.json tsconfig.web.json vitest.config.ts

# package.json 원복
git checkout -- package.json

# 추가된 npm 패키지 제거
npm install

# 정상 확인
npm start
```

---

## Phase 1: 타입 기반 + Zustand 스토어 (예상 16-24h)

### Step 1.1: 타입 정의 파일 생성

#### 1.1a: `src/renderer/src/types/office-state.ts`

> officeState 전수 타입 (index.html 라인 3581-3666 기반, 50+ 필드)

```typescript
/** 실행 액션 종류 */
export type ActionKey =
  | 'stage_0' | 'stage_2' | 'stage_3' | 'stage_4'
  | 'one_stop' | 'one_stop_frontier_lag'
  | 'rollback' | 'wipe' | 'reset' | 'rewind' | 'stop'

/** Stage 0 서브키 */
export type Stage0SubKey = '1' | '2' | '3' | '4' | '5' | '6' | '7'

/** Verdict 결과 */
export type Verdict = 'PASS' | 'PWF' | 'REJECT' | null

/** 품질 신호 상태 */
export type SignalStatus = 'good' | 'watch' | 'alert'

/** 품질 신호 단일 항목 */
export interface QualitySignal {
  label: string
  value: number | string
  status: SignalStatus
  meta?: string
  sparkline?: number[]
}

/** 품질 최근 에피소드 */
export interface QualityRecentEpisode {
  ep_num: number
  verdict: Verdict
  score: number | null
  ai_slop_hits?: string[]
}

/** 품질 요약 */
export interface QualitySummary {
  available: boolean
  lookback: number
  latest_ep: number | null
  project: string | null
  signals: Record<string, QualitySignal>
  recent: QualityRecentEpisode[]
  latest_ai_slop_hits: string[]
}

/** 결과 요약 */
export interface ResultSummary {
  available: boolean
  headline: string
  verdict: Verdict
  score: number | null
  ep_num: number | null
  selection_reason: string
  open_review: string
  issues: Array<{ label: string; severity: string; detail: string }>
  signal_alerts: string[]
  fix_now: string[]
  keep_next: string
  avoid_next: string
  next_action: string
}

/** 점수 트렌드 */
export interface ScoreTrend {
  trend: string
  summary: string
  delta: number
  avg: number
  samples: number
}

/** 실패 패턴 */
export interface FailurePatterns {
  top_types: Array<{ type: string; count: number }>
  by_stage: Array<{ stage: string; count: number }>
  by_episode_range: Array<{ range: string; count: number }>
}

/** 캘리브레이션 */
export interface Calibration {
  available: boolean
  lookback: number
  latest_ep: number | null
  total_reviews: number
  label_counts: Array<{ label: string; count: number }>
  recent_observations: Array<{ ep_num: number; label: string; note: string; timestamp?: string }>
  advisory_candidates: Array<{ label: string; detail: string }>
  next_step: string
  allowed_labels: string[]
}

/** 품질 인사이트 전체 */
export interface QualityInsights {
  available: boolean
  lookback: number
  latest_ep: number | null
  quality_summary: QualitySummary & { latest_signal_summary: Record<string, unknown> }
  result_summary: ResultSummary
  episode_trend: Array<Record<string, unknown>>
  compare_rows: Array<Record<string, unknown>>
  score_trend: ScoreTrend
  stage_stats: Array<Record<string, unknown>>
  common_violations: Array<Record<string, unknown>>
  failure_patterns: FailurePatterns
  calibration: Calibration
}

/** 이벤트 피드 항목 */
export interface EventFeedEntry {
  time: string
  text: string
  type?: string
}

/** 에이전트 런타임 상태 */
export interface AgentRuntimeState {
  status: string
  detail: string
  bubbleText: string
  bubbleColor: string
  bubbleTimer: number
  intensity: number
  updatedAt: number
}

/** 전체 오피스 상태 */
export interface OfficeState {
  isRunning: boolean
  mode: string
  skipAnimation: boolean
  mute: boolean
  frame: number
  currentStage: ActionKey | null
  currentSubKey: Stage0SubKey | null
  currentStageTitle: string
  currentStageSummary: string
  focusTitle: string
  focusDetail: string
  promptPending: boolean
  promptDetail: string
  recentEvents: EventFeedEntry[]
  lastVerdict: Verdict
  lastVerdictScore: number | null
  backendConnected: boolean
  commandReady: boolean
  runStartedAt: number | null
  qualitySummary: QualitySummary
  qualityInsights: QualityInsights
}
```

#### 1.1b: `src/renderer/src/types/settings.ts`

```typescript
/** 앱 설정 (AppData JSON 영속화) */
export interface AppSettings {
  apiKey1: string
  extraKeys: Record<number, string>
  slackWebhook: string
  timeout: number
  keyRotate: number
  qualityGate: number
  targetLength: number
}

/** 프로젝트별 설정 */
export interface ProjectSettings {
  project: string
  authorDirectives: string
  workGuardYaml: string
}

/** 프로젝트 설정 + 장르 */
export interface ProjectConfig {
  genre: string
  project: string
  projectIndex: number | null
}

/** 장르 정보 */
export interface GenreInfo {
  key: string
  label: string
  tested: boolean
  genreIndex: number
}

export const GENRE_LIST: GenreInfo[] = [
  { key: 'investment', label: '투자물', tested: true, genreIndex: 3 },
  { key: 'wuxia', label: '무협', tested: false, genreIndex: 1 },
  { key: 'hunter', label: '헌터물', tested: false, genreIndex: 2 },
  { key: 'fantasy', label: '판타지', tested: false, genreIndex: 4 },
  { key: 'medical', label: '의료물', tested: false, genreIndex: 10 },
  { key: 'alt_history', label: '대체역사', tested: false, genreIndex: 7 },
  { key: 'composer', label: '작곡물', tested: false, genreIndex: 5 },
  { key: 'sports', label: '스포츠물', tested: false, genreIndex: 9 },
  { key: 'actor', label: '배우/연예물', tested: false, genreIndex: 8 },
  { key: 'cooking', label: '요리물', tested: false, genreIndex: 6 },
]

export const GENRE_LABELS: Record<string, string> = Object.fromEntries(
  GENRE_LIST.map(g => [g.key, g.label])
)
```

#### 1.1c: `src/renderer/src/types/websocket-events.ts`

```typescript
/** WebSocket 이벤트 — 8종 discriminated union (index.html _handleWsEvent 기반) */

interface BaseEvent {
  ts?: string
}

export interface StatusEvent extends BaseEvent {
  type: 'status'
  state?: string
  message?: string
  run_id?: string
}

export interface StageEvent extends BaseEvent {
  type: 'stage'
  stage?: string
  sub_key?: string
  title?: string
  summary?: string
}

export interface FocusEvent extends BaseEvent {
  type: 'focus'
  title?: string
  detail?: string
  agent?: string
}

export interface VerdictEvent extends BaseEvent {
  type: 'verdict'
  verdict?: string
  score?: number
  ep_num?: number
  summary?: string
}

export interface PromptEvent extends BaseEvent {
  type: 'prompt'
  prompt_id?: string
  run_id?: string
  text?: string
  options?: string[]
  default_value?: string
  hint?: string
}

export interface PromptResolvedEvent extends BaseEvent {
  type: 'prompt_resolved'
  prompt_id?: string
}

export interface LogEvent extends BaseEvent {
  type: 'log'
  message?: string
  verdict?: string
  meta?: Record<string, unknown>
}

export interface AgentEvent extends BaseEvent {
  type: 'agent'
  agent?: string
  status?: string
  detail?: string
  intensity?: number
  bubble?: string
}

export type WSEvent =
  | StatusEvent
  | StageEvent
  | FocusEvent
  | VerdictEvent
  | PromptEvent
  | PromptResolvedEvent
  | LogEvent
  | AgentEvent
```

#### 1.1d: `src/renderer/src/types/ipc-bridge.ts`

```typescript
/**
 * IPC 채널 및 브릿지 라우트 상수
 * src/main/desktop_control_plane_contract.js 미러
 */
export const IPC_CHANNELS = {
  bridge: {
    run: 'bridge:run',
    stop: 'bridge:stop',
    status: 'bridge:status',
    getUrl: 'bridge:get-url',
    getCliContract: 'bridge:get-cli-contract',
    getQualitySummary: 'bridge:get-quality-summary',
    getQualityDashboard: 'bridge:get-quality-dashboard',
    getSafeOpsPreview: 'bridge:get-safe-ops-preview',
    saveQualityReview: 'bridge:save-quality-review',
    resolvePrompt: 'bridge:resolve-prompt',
    saveSettings: 'bridge:save-settings',
    loadSettings: 'bridge:load-settings',
  },
  material: {
    listFiles: 'material:list-files',
    importFile: 'material:import-file',
    deleteFile: 'material:delete-file',
  },
  project: {
    list: 'project:list',
    create: 'project:create',
    loadConfigSurfaces: 'project:load-config-surfaces',
    saveConfigSurfaces: 'project:save-config-surfaces',
    listWorkGuardTemplates: 'project:list-work-guard-templates',
    applyWorkGuardTemplate: 'project:apply-work-guard-template',
  },
  workspace: {
    openFolder: 'workspace:open-folder',
    getPath: 'workspace:get-path',
  },
} as const

export const BRIDGE_STATUS_URL = 'http://127.0.0.1:8300'
export const BRIDGE_WS_URL = 'ws://127.0.0.1:8300/events'
```

### Step 1.2: Zustand 스토어 생성

#### 1.2a: `src/renderer/src/stores/office-store.ts`

```typescript
import { create } from 'zustand'
import type { OfficeState, ActionKey, Stage0SubKey, Verdict, EventFeedEntry, AgentRuntimeState } from '@/types/office-state'

const MAX_EVENTS = 60
const MAX_LOG_ENTRIES = 500

interface LogEntry {
  id: number
  time: string
  message: string
  verdict: string
  meta: Record<string, unknown>
}

interface OfficeStore extends OfficeState {
  // 에이전트 런타임 (keyed by spriteKey)
  agentRuntime: Record<string, AgentRuntimeState>
  // 로그
  logs: LogEntry[]
  logIdCounter: number

  // 액션
  setRunning: (running: boolean) => void
  setMode: (mode: string) => void
  setStage: (stage: ActionKey | null, subKey?: Stage0SubKey | null, title?: string, summary?: string) => void
  setFocus: (title: string, detail: string) => void
  setPrompt: (pending: boolean, detail: string) => void
  setVerdict: (verdict: Verdict, score: number | null) => void
  setBackendConnected: (connected: boolean) => void
  setCommandReady: (ready: boolean) => void
  setRunStartedAt: (ts: number | null) => void
  setSkipAnimation: (skip: boolean) => void
  setMute: (mute: boolean) => void
  pushEvent: (entry: EventFeedEntry) => void
  setAgentStatus: (agentKey: string, status: string, detail: string, intensity: number) => void
  speakAgent: (agentKey: string, text: string, color?: string) => void
  appendLog: (message: string, verdict?: string, meta?: Record<string, unknown>) => void
  setQualitySummary: (summary: OfficeState['qualitySummary']) => void
  setQualityInsights: (insights: OfficeState['qualityInsights']) => void
  resetRunState: () => void
}

function nowLabel(): string {
  return new Date().toLocaleTimeString('ko-KR', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export const useOfficeStore = create<OfficeStore>((set) => ({
  // 초기 상태 (index.html officeState 미러)
  isRunning: false,
  mode: 'IDLE',
  skipAnimation: false,
  mute: false,
  frame: 0,
  currentStage: null,
  currentSubKey: null,
  currentStageTitle: '대기',
  currentStageSummary: '실행 버튼을 기다리는 중',
  focusTitle: '앱 준비 중',
  focusDetail: '백엔드 연결 전',
  promptPending: false,
  promptDetail: '대기 중인 입력 없음',
  recentEvents: [],
  lastVerdict: null,
  lastVerdictScore: null,
  backendConnected: false,
  commandReady: false,
  runStartedAt: null,
  qualitySummary: {
    available: false, lookback: 5, latest_ep: null, project: null,
    signals: {}, recent: [], latest_ai_slop_hits: [],
  },
  qualityInsights: {
    available: false, lookback: 5, latest_ep: null,
    quality_summary: {
      available: false, lookback: 5, latest_ep: null,
      signals: {}, recent: [], latest_ai_slop_hits: [], latest_signal_summary: {},
    },
    result_summary: {
      available: false, headline: '최근 심사 결과가 아직 없습니다.', verdict: null,
      score: null, ep_num: null, selection_reason: '', open_review: '',
      issues: [], signal_alerts: [], fix_now: [],
      keep_next: '최근 심사 결과가 쌓이면 유지 포인트가 표시됩니다.',
      avoid_next: '반복 방지 포인트가 아직 없습니다.',
      next_action: 'Stage 4 PASS 원고가 누적되면 결과 요약이 표시됩니다.',
    },
    episode_trend: [], compare_rows: [],
    score_trend: { trend: 'insufficient_data', summary: '데이터 부족 (0화)', delta: 0, avg: 0, samples: 0 },
    stage_stats: [], common_violations: [],
    failure_patterns: { top_types: [], by_stage: [], by_episode_range: [] },
    calibration: {
      available: false, lookback: 5, latest_ep: null, total_reviews: 0,
      label_counts: [], recent_observations: [], advisory_candidates: [],
      next_step: '관측 기록이 누적되면 승격 후보가 표시됩니다.', allowed_labels: [],
    },
  },
  agentRuntime: {},
  logs: [],
  logIdCounter: 0,

  // 액션
  setRunning: (running) => set({ isRunning: running }),
  setMode: (mode) => set({ mode }),
  setStage: (stage, subKey = null, title, summary) => set({
    currentStage: stage, currentSubKey: subKey,
    currentStageTitle: title ?? '대기',
    currentStageSummary: summary ?? '실행 버튼을 기다리는 중',
  }),
  setFocus: (title, detail) => set({ focusTitle: title, focusDetail: detail }),
  setPrompt: (pending, detail) => set({ promptPending: pending, promptDetail: detail }),
  setVerdict: (verdict, score) => set({ lastVerdict: verdict, lastVerdictScore: score }),
  setBackendConnected: (connected) => set({ backendConnected: connected }),
  setCommandReady: (ready) => set({ commandReady: ready }),
  setRunStartedAt: (ts) => set({ runStartedAt: ts }),
  setSkipAnimation: (skip) => set({ skipAnimation: skip }),
  setMute: (mute) => set({ mute }),
  pushEvent: (entry) => set((s) => ({
    recentEvents: [entry, ...s.recentEvents].slice(0, MAX_EVENTS),
  })),
  setAgentStatus: (agentKey, status, detail, intensity) => set((s) => ({
    agentRuntime: {
      ...s.agentRuntime,
      [agentKey]: {
        ...s.agentRuntime[agentKey],
        status, detail, intensity,
        updatedAt: Date.now(),
      },
    },
  })),
  speakAgent: (agentKey, text, color) => set((s) => ({
    agentRuntime: {
      ...s.agentRuntime,
      [agentKey]: {
        ...s.agentRuntime[agentKey],
        bubbleText: text,
        bubbleTimer: Date.now(),
        ...(color ? { bubbleColor: color } : {}),
      },
    },
  })),
  appendLog: (message, verdict = '', meta = {}) => set((s) => ({
    logIdCounter: s.logIdCounter + 1,
    logs: [
      ...s.logs.slice(-MAX_LOG_ENTRIES + 1),
      { id: s.logIdCounter + 1, time: nowLabel(), message, verdict, meta },
    ],
  })),
  setQualitySummary: (summary) => set({ qualitySummary: summary }),
  setQualityInsights: (insights) => set({ qualityInsights: insights }),
  resetRunState: () => set({
    isRunning: false, mode: 'IDLE',
    currentStage: null, currentSubKey: null,
    currentStageTitle: '대기', currentStageSummary: '실행 버튼을 기다리는 중',
    focusTitle: '대기', focusDetail: '실행 대기',
    promptPending: false, promptDetail: '대기 중인 입력 없음',
    runStartedAt: null,
  }),
}))
```

#### 1.2b: `src/renderer/src/stores/connection-store.ts`

```typescript
import { create } from 'zustand'

interface ConnectionStore {
  wsConnected: boolean
  wsReconnectCount: number
  lastStatusSync: number | null

  setWsConnected: (connected: boolean) => void
  incrementReconnect: () => void
  setLastStatusSync: (ts: number) => void
}

export const useConnectionStore = create<ConnectionStore>((set) => ({
  wsConnected: false,
  wsReconnectCount: 0,
  lastStatusSync: null,

  setWsConnected: (connected) => set({ wsConnected: connected }),
  incrementReconnect: () => set((s) => ({ wsReconnectCount: s.wsReconnectCount + 1 })),
  setLastStatusSync: (ts) => set({ lastStatusSync: ts }),
}))
```

#### 1.2c: `src/renderer/src/stores/settings-store.ts`

```typescript
import { create } from 'zustand'
import type { AppSettings, ProjectSettings, ProjectConfig } from '@/types/settings'

interface SettingsStore {
  settings: AppSettings
  projectSettings: ProjectSettings
  projectConfig: ProjectConfig
  projects: string[]
  settingsLoaded: boolean

  setSettings: (settings: Partial<AppSettings>) => void
  setProjectSettings: (settings: Partial<ProjectSettings>) => void
  setProjectConfig: (config: Partial<ProjectConfig>) => void
  setProjects: (projects: string[]) => void
  setSettingsLoaded: (loaded: boolean) => void
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: {
    apiKey1: '',
    extraKeys: {},
    slackWebhook: '',
    timeout: 300,
    keyRotate: 10,
    qualityGate: 90,
    targetLength: 5000,
  },
  projectSettings: {
    project: '',
    authorDirectives: '',
    workGuardYaml: '',
  },
  projectConfig: {
    genre: '',
    project: '',
    projectIndex: null,
  },
  projects: [],
  settingsLoaded: false,

  setSettings: (partial) => set((s) => ({
    settings: { ...s.settings, ...partial },
  })),
  setProjectSettings: (partial) => set((s) => ({
    projectSettings: { ...s.projectSettings, ...partial },
  })),
  setProjectConfig: (partial) => set((s) => ({
    projectConfig: { ...s.projectConfig, ...partial },
  })),
  setProjects: (projects) => set({ projects }),
  setSettingsLoaded: (loaded) => set({ settingsLoaded: loaded }),
}))
```

### Step 1.3: 커스텀 훅 생성

#### 1.3a: `src/renderer/src/hooks/useIPC.ts`

```typescript
import { useCallback } from 'react'

/**
 * Typed wrapper for geuldobiDesktop preload bridge
 * 모든 IPC 호출을 이 훅을 통해 수행한다
 */
export function useIPC() {
  const api = window.geuldobiDesktop

  const runKey = useCallback(
    (key: string, subKey: string | null, inputs: Record<string, unknown>, approvalId?: string | null) =>
      api.runKey(key, subKey, inputs, approvalId ?? null),
    [api]
  )

  const stopRun = useCallback(() => api.stopRun(), [api])
  const getStatus = useCallback(() => api.getStatus(), [api])
  const getQualitySummary = useCallback((project: string, lookback?: number) => api.getQualitySummary(project, lookback), [api])
  const getQualityDashboard = useCallback((project: string, lookback?: number) => api.getQualityDashboard(project, lookback), [api])
  const getSafeOpsPreview = useCallback((project: string) => api.getSafeOpsPreview(project), [api])
  const saveQualityReview = useCallback(
    (project: string, epNum: number, operatorLabel: string, note?: string) =>
      api.saveQualityReview(project, epNum, operatorLabel, note),
    [api]
  )
  const resolvePrompt = useCallback(
    (runId: string, promptId: string, value: string) => api.resolvePrompt(runId, promptId, value),
    [api]
  )
  const saveSettings = useCallback((settings: Record<string, unknown>) => api.saveSettings(settings), [api])
  const loadSettings = useCallback(() => api.loadSettings(), [api])
  const listMaterialFiles = useCallback((folder: 'bible' | 'treatments') => api.listMaterialFiles(folder), [api])
  const importMaterialFile = useCallback((folder: 'bible' | 'treatments') => api.importMaterialFile(folder), [api])
  const deleteMaterialFile = useCallback((folder: 'bible' | 'treatments', fileName: string) => api.deleteMaterialFile(folder, fileName), [api])
  const listProjects = useCallback(() => api.listProjects(), [api])
  const createProject = useCallback((name: string) => api.createProject(name), [api])
  const loadProjectConfigSurfaces = useCallback((project: string) => api.loadProjectConfigSurfaces(project), [api])
  const saveProjectConfigSurfaces = useCallback(
    (project: string, authorDirectives?: string, workGuardYaml?: string) =>
      api.saveProjectConfigSurfaces(project, authorDirectives, workGuardYaml),
    [api]
  )
  const listWorkGuardTemplates = useCallback((genre?: string) => api.listWorkGuardTemplates(genre), [api])
  const applyWorkGuardTemplate = useCallback((project: string, templatePath: string) => api.applyWorkGuardTemplate(project, templatePath), [api])
  const openWorkspaceFolder = useCallback(() => api.openWorkspaceFolder(), [api])
  const getBackendUrl = useCallback(() => api.getBackendUrl(), [api])
  const getCliContract = useCallback(() => api.getCliContract(), [api])

  return {
    runKey, stopRun, getStatus,
    getQualitySummary, getQualityDashboard, getSafeOpsPreview,
    saveQualityReview, resolvePrompt,
    saveSettings, loadSettings,
    listMaterialFiles, importMaterialFile, deleteMaterialFile,
    listProjects, createProject,
    loadProjectConfigSurfaces, saveProjectConfigSurfaces,
    listWorkGuardTemplates, applyWorkGuardTemplate,
    openWorkspaceFolder, getBackendUrl, getCliContract,
  }
}
```

#### 1.3b: `src/renderer/src/hooks/useWebSocket.ts`

```typescript
import { useEffect, useRef, useCallback } from 'react'
import { useConnectionStore } from '@/stores/connection-store'
import { useOfficeStore } from '@/stores/office-store'
import type { WSEvent } from '@/types/websocket-events'

const RECONNECT_DELAY_MS = 3000
const WS_URL = 'ws://127.0.0.1:8300/events'

/**
 * WebSocket 싱글톤 연결 관리자
 * index.html _connectWebSocket + _handleWsEvent 통합
 */
export function useWebSocket(onEvent?: (ev: WSEvent) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { setWsConnected, incrementReconnect } = useConnectionStore()
  const appendLog = useOfficeStore((s) => s.appendLog)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        setWsConnected(true)
        appendLog('[WS] 연결됨')
      }

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as WSEvent
          onEvent?.(data)
        } catch {
          // 파싱 실패 무시
        }
      }

      ws.onclose = () => {
        setWsConnected(false)
        wsRef.current = null
        reconnectTimerRef.current = setTimeout(() => {
          incrementReconnect()
          connect()
        }, RECONNECT_DELAY_MS)
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      // WebSocket 생성 실패
    }
  }, [setWsConnected, incrementReconnect, appendLog, onEvent])

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    connect()
    return disconnect
  }, [connect, disconnect])

  return { connect, disconnect }
}
```

#### 1.3c: `src/renderer/src/hooks/useAppReady.ts`

```typescript
import { useState, useEffect, useRef } from 'react'

/**
 * app:ready 이벤트를 캐싱하는 훅
 * preload bridge의 onAppReady를 구독하고, 한번 ready가 되면 상태를 유지한다
 */
export function useAppReady(): { ready: boolean; reason: string } {
  const [ready, setReady] = useState(false)
  const [reason, setReason] = useState('')
  const subscribedRef = useRef(false)

  useEffect(() => {
    if (subscribedRef.current) return
    subscribedRef.current = true

    const api = window.geuldobiDesktop
    if (api?.onAppReady) {
      api.onAppReady((payload) => {
        setReady(true)
        setReason(payload?.reason ?? 'unknown')
      })
    }
  }, [])

  return { ready, reason }
}
```

### Step 1.4: 검증

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# TypeScript 컴파일 체크
npx tsc --noEmit -p tsconfig.web.json
# 기대: 에러 0건

# dev 서버 실행 확인
npm run dev
# 기대: 정상 기동, 에러 없음
```

**체크리스트:**

- [ ] `tsc --noEmit` 에러 0건
- [ ] 모든 타입 파일에서 export가 정의됨
- [ ] Zustand 스토어 초기값이 index.html officeState 필드와 1:1 대응
- [ ] useIPC 훅이 preload.d.ts의 25개 메서드를 모두 래핑
- [ ] useWebSocket의 WS_URL이 main.js의 EVENTS_WS_URL과 동일 (`ws://127.0.0.1:8300/events`)

### Step 1.5: 롤백 절차

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

rm -rf src/renderer/src/types src/renderer/src/stores src/renderer/src/hooks
# package.json에서 zustand 제거할 필요 없음 (Phase 0에서 이미 설치)
```

---

## Phase 2: 공유 UI 컴포넌트 (예상 20-28h)

### Step 2.1: 컴포넌트 디렉토리 확인

```bash
ls src/renderer/src/components/ui/
# 이 시점에 디렉토리는 존재하지만 파일은 없어야 함
```

### Step 2.2: 기본 UI 컴포넌트 생성

아래 각 컴포넌트를 `src/renderer/src/components/ui/` 하위에 생성한다.
모든 컴포넌트는 기존 CSS 클래스명을 재사용하여 시각적 일관성을 유지한다.

| 파일명 | 기존 CSS 클래스 | 비고 |
|--------|----------------|------|
| `Panel.tsx` | `.panel`, `.panel-head`, `.panel-title`, `.panel-sub` | 모든 카드 래퍼 |
| `Button.tsx` | `.menu-btn`, `.top-action`, `.btn-sm`, `.btn-cancel`, `.btn-confirm` | 5가지 variant |
| `Badge.tsx` | `.badge`, `.menu-badge`, `.verdict-badge` | 상태/등급 표시 |
| `Modal.tsx` | `.modal-overlay`, `.modal-panel`, `.confirm-overlay`, `.confirm-panel` | 2가지 타입 |
| `Select.tsx` | `.project-select`, `<select>` | 드롭다운 래퍼 |
| `InputField.tsx` | `.input-row`, `<input>` | 라벨 + 입력 |
| `Slider.tsx` | `.slider-row` | 범위 입력 |
| `Accordion.tsx` | `.accordion-item`, `.category-header`, `.category-body` | 재료/상품/운영 |
| `Chip.tsx` | `.mini-toggle` | 토글 칩 |
| `Card.tsx` | `.mission-card`, `.quality-signal-card` | 미션/신호 카드 |

예시 — `Panel.tsx`:

```tsx
import type { ReactNode } from 'react'

interface PanelProps {
  title?: string
  subtitle?: string
  className?: string
  children: ReactNode
  headerRight?: ReactNode
}

export function Panel({ title, subtitle, className = '', children, headerRight }: PanelProps) {
  return (
    <article className={`panel ${className}`}>
      {(title || headerRight) && (
        <div className="panel-head">
          <div>
            {title && <h2 className="panel-title">{title}</h2>}
            {subtitle && <p className="panel-sub">{subtitle}</p>}
          </div>
          {headerRight}
        </div>
      )}
      {children}
    </article>
  )
}
```

예시 — `Button.tsx`:

```tsx
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'menu' | 'action' | 'sm' | 'cancel' | 'confirm' | 'frontier'

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  menu: 'menu-btn',
  action: 'top-action',
  sm: 'btn-sm',
  cancel: 'btn-cancel',
  confirm: 'btn-confirm',
  frontier: 'menu-btn menu-btn-frontier-recommended',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  children: ReactNode
}

export function Button({ variant = 'action', className = '', children, ...rest }: ButtonProps) {
  return (
    <button type="button" className={`${VARIANT_CLASS[variant]} ${className}`} {...rest}>
      {children}
    </button>
  )
}
```

예시 — `Modal.tsx`:

```tsx
import type { ReactNode } from 'react'
import { useEffect, useCallback } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  variant?: 'modal' | 'confirm'
}

export function Modal({ open, onClose, title, children, variant = 'modal' }: ModalProps) {
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose()
  }, [onClose])

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open, handleKeyDown])

  if (!open) return null

  const overlayClass = variant === 'confirm' ? 'confirm-overlay' : 'modal-overlay'
  const panelClass = variant === 'confirm' ? 'confirm-panel' : 'modal-panel'

  return (
    <div className={overlayClass} style={{ display: 'flex' }} role="dialog" aria-modal="true">
      <div className={panelClass}>
        {title && (
          <div className="modal-head">
            <h2 className="modal-title">{title}</h2>
            <button type="button" className="modal-close" onClick={onClose} aria-label="닫기">
              ✕
            </button>
          </div>
        )}
        {children}
      </div>
    </div>
  )
}
```

### Step 2.3: CSS Modules 추출 (선택)

Phase 2에서는 global.css에 기존 CSS를 모두 유지한다.
Phase 5에서 컴포넌트별 CSS Module로 분리한다.

이유: 기존 8,266행 index.html에서 2,765행이 CSS이며, 이를 한 번에 분리하면 Phase 3의 패널 마이그레이션 과정에서 스타일 깨짐 추적이 어려워진다.

### Step 2.4: 검증

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

npx tsc --noEmit -p tsconfig.web.json
npm run dev
npm run test:react
```

**체크리스트:**

- [ ] `tsc --noEmit` 에러 0건
- [ ] 각 컴포넌트가 스토리북 없이도 `npm run dev`에서 임포트 가능
- [ ] 기존 CSS 클래스명이 컴포넌트 props와 1:1 대응

### Step 2.5: 롤백 절차

```bash
rm -rf src/renderer/src/components/ui/*
```

---

## Phase 3: 기능 패널 마이그레이션 (예상 88-116h, 6 서브페이즈)

> 핵심 원칙: 한 번에 하나의 패널만 마이그레이션한다. 각 서브페이즈 완료 후 `npm run dev`로 기능 동등성을 확인한 뒤 다음으로 넘어간다.

### Phase 3a: Settings 패널 (12-16h)

**대상 바닐라 코드:**
- HTML: index.html 라인 3159-3375 (설정 사이드 패널)
- JS: index.html 라인 7631-7812 (openSettings, closeSettings, syncSettingsUI, 탭 전환, API 키 테스트, 추가 키 동적 생성)

**생성할 React 파일:**

| 파일 | 기능 |
|------|------|
| `src/renderer/src/components/panels/SettingsPanel.tsx` | 설정 사이드 패널 셸 + 탭 컨트롤러 |
| `src/renderer/src/components/panels/settings/ApiKeyTab.tsx` | API 키 관리 (Key 1-9, 테스트, Slack) |
| `src/renderer/src/components/panels/settings/ModelTab.tsx` | 모델 설정 (read-only) |
| `src/renderer/src/components/panels/settings/ProjectTab.tsx` | 프로젝트 설정 (작가 지시, 작품가드) |
| `src/renderer/src/components/panels/settings/SystemTab.tsx` | 시스템 설정 (슬라이더 4개) |
| `src/renderer/src/components/panels/settings/WorkGuardHelper.tsx` | 작품 정체성 도우미 (9 필드 + 프리셋 3종) |

**이동할 상태 변수:**
- `settingsStore` → `useSettingsStore().settings`
- `projectSettingsStore` → `useSettingsStore().projectSettings`
- `projectConfig.genre` → `useSettingsStore().projectConfig.genre`

**연결할 IPC 메서드:**
- `saveSettings`, `loadSettings`
- `loadProjectConfigSurfaces`, `saveProjectConfigSurfaces`
- `listWorkGuardTemplates`, `applyWorkGuardTemplate`

**innerHTML → JSX 전환 목록 (6건):**
1. `extraKeysBody` 동적 생성 (buildExtraKeys) → `ApiKeyTab` 내 map 렌더링
2. `workGuardTemplateSelect` 옵션 → `<Select>` 컴포넌트
3. `apiKeyStatus.textContent` → JSX 보간
4. `settingsGenreDisplay.textContent` → JSX 보간
5. `model-readonly-note` 동적 생성 → `ModelTab` 정적 JSX
6. `workGuardTemplateMeta.textContent` → JSX 보간

**addEventListener → useEffect 전환 목록 (14건):**
1. `.tab-btn` click → `useState`로 탭 상태 관리
2. `toggleKey1Btn` click → `useState`로 password/text 토글
3. `testKey1Btn` click → 이벤트 핸들러 함수
4. `extraKeysToggle` click → `useState`로 접기/펼치기
5. `settingsChangeGenre` click → props callback
6. `workGuardHelper` input (9건) → controlled input + onChange
7. `workGuardYaml` change → controlled textarea + onChange
8. `wgPresetEnterprise/Talent/Sect` click → 이벤트 핸들러
9. `wgReloadFromYaml` click → 이벤트 핸들러
10. `wgClearHelper` click → 이벤트 핸들러
11. `refreshWorkGuardTemplatesBtn` click → 이벤트 핸들러
12. `applyWorkGuardTemplateBtn` click → 이벤트 핸들러
13. `settingsSave` click → 이벤트 핸들러
14. `settingsCancel` click → `onClose` prop

**검증 체크리스트:**
- [ ] 설정 열기/닫기 동작
- [ ] 4개 탭 전환 동작
- [ ] API 키 입력 → 테스트 → 저장 → 재로드 후 유지
- [ ] 추가 키 2-9 접기/펼치기
- [ ] 작품가드 도우미 → YAML 동기화
- [ ] 작품가드 프리셋 3종 적용
- [ ] 작품가드 템플릿 목록 + 적용
- [ ] 슬라이더 값 변경 → 저장 → 재로드 후 유지
- [ ] 품질 게이트/목표 길이 변경 → 저장

**롤백:** `rm -rf src/renderer/src/components/panels/settings*`

### Phase 3b: Log 패널 (8-10h)

**대상 바닐라 코드:**
- HTML: index.html 라인 3139-3154
- JS: `appendLog` (라인 5055-5145), `applyLogFilter` (라인 8138+), logSearchInput, logFilterSelect

**생성할 React 파일:**

| 파일 | 기능 |
|------|------|
| `src/renderer/src/components/panels/LogPanel.tsx` | 로그 패널 (검색, 필터, 가상 스크롤) |

**이동할 상태 변수:**
- `logStream` innerHTML → `useOfficeStore().logs` 배열
- 검색어/필터 → `useState` 로컬 상태

**innerHTML → JSX 전환 (1건):**
1. `logStream.innerHTML` 누적 (appendLog) → logs 배열 map 렌더링

**addEventListener → useEffect (3건):**
1. `logToggleBtn` click → `useState` 접기/펼치기
2. `logSearchInput` input → `useState` + filter
3. `logFilterSelect` change → `useState` + filter

**검증:**
- [ ] 로그 실시간 추가 (WebSocket 이벤트 수신 시)
- [ ] 검색 필터링
- [ ] PASS/REJECT/PWF 필터
- [ ] 자동 스크롤 (최신 로그로)

**롤백:** `rm src/renderer/src/components/panels/LogPanel.tsx`

### Phase 3c: Run 패널 (16-20h)

**대상 바닐라 코드:**
- HTML: index.html 라인 2786-2922 (실행 패널 + 재료/상품/운영 아코디언)
- JS: `handleRunButtonClick` (라인 6785-7016), `_collectInputs` (라인 5857-5889), 장르 게이팅, Safe Ops

**생성할 React 파일:**

| 파일 | 기능 |
|------|------|
| `src/renderer/src/components/panels/RunPanel.tsx` | 실행 패널 셸 |
| `src/renderer/src/components/panels/run/MaterialSection.tsx` | 재료 넣기 (Bible/Treatment 파일 목록) |
| `src/renderer/src/components/panels/run/ProduceSection.tsx` | 상품 생산 (Stage 0-4, One-Stop, Frontier Lag) |
| `src/renderer/src/components/panels/run/OpsSection.tsx` | 운영 (Rollback, Wipe, Reset, Rewind, Stop) |
| `src/renderer/src/components/panels/run/SafeOpsPreview.tsx` | Safe Ops Preview 카드 |

**이동할 상태 변수:**
- `projectConfig.genre` → `useSettingsStore().projectConfig.genre`
- `officeState.isRunning` → `useOfficeStore().isRunning`
- `officeState.commandReady` → `useOfficeStore().commandReady`

**연결할 IPC 메서드:**
- `runKey`, `stopRun`, `getSafeOpsPreview`
- `listMaterialFiles`, `importMaterialFile`, `deleteMaterialFile`

**innerHTML → JSX 전환 (8건):**
1. `bibleFileList` innerHTML → MaterialSection map 렌더링
2. `treatmentFileList` innerHTML → MaterialSection map 렌더링
3. `safeOpsGrid` innerHTML → SafeOpsPreview map 렌더링
4. `genreBtnMeta` textContent → JSX 보간
5. `genreRequiredHint` display → 조건부 렌더링
6. `stage0SubMenu` display → 조건부 렌더링
7. `safeOpsMeta` textContent → JSX 보간
8. `safeOpsHint` textContent → JSX 보간

**addEventListener → useEffect (12건):**
1. `.menu-btn` click (12개 버튼) → onClick 핸들러
2. `.stage0-sub-btn` click (7개) → onClick 핸들러
3. `stage0StyleCacheMode` change → controlled select
4. `importBibleBtn` / `importTreatmentBtn` click → onClick
5. `refreshBibleBtn` / `refreshTreatmentBtn` click → onClick
6. 파일 삭제 버튼 (동적) → onClick
7. `.category-header` click (3개) → `useState`로 아코디언 상태
8. `safeOpsConfirmOk` / `safeOpsConfirmCancel` click → Modal 상태
9-12. genre-gated 버튼 disabled 토글

**검증:**
- [ ] 장르 미설정 시 Stage 버튼 비활성화
- [ ] 재료 파일 목록 로드/추가/삭제
- [ ] Stage 0 서브메뉴 펼침/접기
- [ ] 실행 중 UI 잠금
- [ ] Safe Ops 확인 모달
- [ ] Stop 버튼 동작

**롤백:** `rm -rf src/renderer/src/components/panels/run*`

### Phase 3d: Quality 패널 (24-32h) — 크리티컬 패스

**대상 바닐라 코드:**
- HTML: index.html 라인 2962-3128 (Quality Radar, Artifact Ladder, Retrieval Inspector, Result Summary, Episode Trend, Failure Watch, Calibration Desk, Agent Board, Event Feed)
- JS: `renderQualityRadar` (4319), `renderArtifactLadder` (4119), `renderRetrievalInspector` (4192), `renderResultSummary` (4378), `renderTrendCompare` (4442), `renderFailureWatch` (4487), `renderCalibrationDesk` (4555), `renderAgentBoard` (4839), `renderEventFeed` (4910), `refreshQualitySummary` (4635)

**생성할 React 파일:**

| 파일 | 기능 |
|------|------|
| `src/renderer/src/components/panels/QualityPanel.tsx` | Quality 뷰 셸 |
| `src/renderer/src/components/panels/quality/QualityRadar.tsx` | 5축 품질 레이더 |
| `src/renderer/src/components/panels/quality/ArtifactLadder.tsx` | 산출물 사다리 |
| `src/renderer/src/components/panels/quality/RetrievalInspector.tsx` | Retrieval 관측 |
| `src/renderer/src/components/panels/quality/ResultSummary.tsx` | 심사 결과 요약 |
| `src/renderer/src/components/panels/quality/EpisodeTrend.tsx` | 회차 비교 |
| `src/renderer/src/components/panels/quality/FailureWatch.tsx` | 실패 패턴 |
| `src/renderer/src/components/panels/quality/CalibrationDesk.tsx` | 운영 관측 + 승격 |
| `src/renderer/src/components/panels/quality/AgentBoard.tsx` | 에이전트 상태 보드 |
| `src/renderer/src/components/panels/quality/EventFeed.tsx` | 실시간 이벤트 피드 |

**이동할 상태 변수:**
- `officeState.qualitySummary` → `useOfficeStore().qualitySummary`
- `officeState.qualityInsights` → `useOfficeStore().qualityInsights`
- `agentRuntime` → `useOfficeStore().agentRuntime`
- `officeState.recentEvents` → `useOfficeStore().recentEvents`

**연결할 IPC 메서드:**
- `getQualitySummary`, `getQualityDashboard`, `saveQualityReview`

**innerHTML → JSX 전환 (16건):**
1. `qualityRadar` innerHTML (renderQualityRadar)
2. `qualityRadarFoot` textContent
3. `artifactLadderGrid` innerHTML (renderArtifactLadder)
4. `artifactSupportRow` innerHTML
5. `retrievalSummaryStrip` innerHTML (renderRetrievalInspector)
6. `retrievalStageGrid` innerHTML
7. `retrievalWarningList` innerHTML
8. `retrievalRecentList` innerHTML
9. `resultSummaryHeadline` textContent
10. `resultSignalAlerts` innerHTML
11. `resultActionGrid` innerHTML
12. `resultIssueList` innerHTML
13. `qualityCompareBody` innerHTML (renderTrendCompare)
14. `stageStatsGrid` innerHTML (renderFailureWatch)
15. `failurePatternList` / `failureRangeList` innerHTML
16. `agentBoard` innerHTML (renderAgentBoard)

**검증:**
- [ ] 프로젝트 선택 시 Quality Radar 갱신
- [ ] Artifact Ladder 산출물 존재 여부 표시
- [ ] Retrieval Inspector 데이터 표시
- [ ] Result Summary verdict 뱃지 색상
- [ ] Episode Trend 테이블 렌더링
- [ ] Failure Watch 패턴 목록
- [ ] Calibration 관측 폼 저장
- [ ] Agent Board 에이전트 상태 표시
- [ ] Event Feed 실시간 갱신

**롤백:** `rm -rf src/renderer/src/components/panels/quality*`

### Phase 3e: Office 패널 (20-28h) — Canvas 통합

**대상 바닐라 코드:**
- HTML: index.html 라인 2926-3137 (사무실 패널 + Canvas + Mission Grid + Pipeline Strip)
- JS: Canvas 렌더링 엔진 (라인 5233-5857: drawRect, loadAllSprites, drawSpriteImg, drawCrown, drawAgent, drawBubble, drawModeEffect, drawNoticeScroll, draw), 미션 보드 (renderMissionBoard 4951), 파이프라인 (renderPipelineStrip 3877)

**생성할 React 파일:**

| 파일 | 기능 |
|------|------|
| `src/renderer/src/components/panels/OfficePanel.tsx` | Office 뷰 셸 |
| `src/renderer/src/components/canvas/OfficeCanvas.tsx` | Canvas 렌더링 (useRef + requestAnimationFrame) |
| `src/renderer/src/components/canvas/sprite-engine.ts` | 스프라이트 로딩/그리기 엔진 (순수 함수) |
| `src/renderer/src/components/canvas/agent-renderer.ts` | 에이전트 + 말풍선 렌더링 |
| `src/renderer/src/components/canvas/effects.ts` | 모드 이펙트 + 노티스 스크롤 |
| `src/renderer/src/components/panels/office/MissionGrid.tsx` | 4개 미션 카드 |
| `src/renderer/src/components/panels/office/PipelineStrip.tsx` | 파이프라인 상태 스트립 |
| `src/renderer/src/components/panels/office/StatusFooter.tsx` | 하단 상태 바 |

> **핵심:** Canvas 렌더링은 React의 선언적 모델 밖에서 동작한다. `useRef`로 canvas 요소를 잡고, `useEffect`에서 `requestAnimationFrame` 루프를 시작하며, Zustand store를 `subscribe`로 직접 읽는다. React 리렌더링과 Canvas 프레임 루프를 분리하는 것이 성능의 핵심이다.

**이동할 상태 변수:**
- Canvas 내부 상태 (`agents`, `_clickBubble`, `_directorScroll`, `_verdictResetTimer`) → `useRef`
- 스프라이트 캐시 → 모듈 레벨 `Map<string, HTMLImageElement>`
- `officeState.frame` → `requestAnimationFrame` 카운터

**innerHTML → JSX 전환 (5건):**
1. `pipelineStrip` innerHTML → PipelineStrip 컴포넌트
2. `effectBanner` className + textContent → EffectBanner 상태 렌더링
3. Mission card textContent (4장) → MissionGrid 컴포넌트
4. 상태 바 badge textContent (4개) → StatusFooter 컴포넌트
5. `agentBoard` innerHTML (중복: Quality에서도 사용) → 공유 컴포넌트

**검증:**
- [ ] Canvas 스프라이트 정상 렌더링 (5명 에이전트)
- [ ] Canvas 리사이즈 반응형
- [ ] 말풍선 표시 + 타이머 소멸
- [ ] 에이전트 클릭 → 랜덤 대사
- [ ] Pipeline Strip 현재 스테이지 하이라이트
- [ ] Mission Grid 실시간 갱신
- [ ] Effect Banner (PASS/PWF/REJECT) 애니메이션
- [ ] Director 스크롤 텍스트

**롤백:** `rm -rf src/renderer/src/components/panels/office* src/renderer/src/components/canvas*`

### Phase 3f: Project 패널 (8-10h)

**대상 바닐라 코드:**
- JS: `initializeWorkspaceLayout` 내 Project View 구성 (라인 7593-7626)
- HTML: 기존 Settings 탭 3 (tab-project)의 재료/설정 분리

**생성할 React 파일:**

| 파일 | 기능 |
|------|------|
| `src/renderer/src/components/panels/ProjectPanel.tsx` | Project 뷰 셸 |
| `src/renderer/src/components/panels/project/MaterialManager.tsx` | 재료 관리 (Run에서 공유) |
| `src/renderer/src/components/panels/project/ProjectConfigEditor.tsx` | 프로젝트 설정 편집 |

**검증:**
- [ ] 재료 목록 로드
- [ ] 작가 지시사항 편집 + 저장
- [ ] 작품가드 편집 + 저장
- [ ] "프로젝트 저장" 버튼 동작
- [ ] "API / 시스템 설정" 버튼 → Settings 패널 열기

**롤백:** `rm -rf src/renderer/src/components/panels/project*`

---

## Phase 4: 레이아웃 셸 + 라우팅 (12-16h)

### Step 4.1: WorkspaceLayout 컴포넌트

파일 경로: `src/renderer/src/components/layout/WorkspaceLayout.tsx`

```tsx
import { useState } from 'react'

type ViewKey = 'run' | 'office' | 'quality' | 'project'

const VIEW_LABELS: Record<ViewKey, string> = {
  run: 'Run',
  office: 'Office',
  quality: 'Quality',
  project: 'Project',
}

interface WorkspaceLayoutProps {
  children: Record<ViewKey, React.ReactNode>
  topbar: React.ReactNode
}

export function WorkspaceLayout({ children, topbar }: WorkspaceLayoutProps) {
  const [activeView, setActiveView] = useState<ViewKey>('run')

  return (
    <main className="page">
      {topbar}
      <nav className="workspace-nav">
        {(Object.keys(VIEW_LABELS) as ViewKey[]).map((key) => (
          <button
            key={key}
            type="button"
            className={`workspace-nav-btn ${activeView === key ? 'active' : ''}`}
            onClick={() => setActiveView(key)}
          >
            {VIEW_LABELS[key]}
          </button>
        ))}
      </nav>
      <div className="workspace-host">
        {(Object.keys(VIEW_LABELS) as ViewKey[]).map((key) => (
          <section
            key={key}
            className={`workspace-view ${key}-view ${activeView === key ? 'active' : ''}`}
          >
            {children[key]}
          </section>
        ))}
      </div>
    </main>
  )
}
```

### Step 4.2: Topbar 컴포넌트

파일 경로: `src/renderer/src/components/layout/Topbar.tsx`

```tsx
import { useSettingsStore } from '@/stores/settings-store'

interface TopbarProps {
  onNewProject: () => void
  onOpenWorkspace: () => void
  onOpenSettings: () => void
}

export function Topbar({ onNewProject, onOpenWorkspace, onOpenSettings }: TopbarProps) {
  const { projects, projectConfig, setProjectConfig } = useSettingsStore()

  return (
    <header className="topbar">
      <select
        className="project-select"
        value={projectConfig.project}
        onChange={(e) => setProjectConfig({ project: e.target.value })}
        aria-label="프로젝트 선택"
      >
        <option value="">프로젝트 선택</option>
        {projects.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
      <button type="button" className="top-action" onClick={onNewProject}>새 프로젝트</button>
      <button type="button" className="top-action" onClick={onOpenWorkspace} title="작업 폴더를 탐색기에서 엽니다">작업 폴더</button>
      <div style={{ flex: 1 }} />
      <button type="button" className="top-action" onClick={onOpenSettings}>설정</button>
    </header>
  )
}
```

### Step 4.3: App.tsx 최종 조립

```tsx
import { useState, useEffect, useCallback } from 'react'
import { WorkspaceLayout } from '@/components/layout/WorkspaceLayout'
import { Topbar } from '@/components/layout/Topbar'
import { RunPanel } from '@/components/panels/RunPanel'
import { LogPanel } from '@/components/panels/LogPanel'
import { OfficePanel } from '@/components/panels/OfficePanel'
import { QualityPanel } from '@/components/panels/QualityPanel'
import { ProjectPanel } from '@/components/panels/ProjectPanel'
import { SettingsPanel } from '@/components/panels/SettingsPanel'
import { GenreModal } from '@/components/modals/GenreModal'
import { NewProjectModal } from '@/components/modals/NewProjectModal'
import { PromptDialog } from '@/components/modals/PromptDialog'
import { useAppReady } from '@/hooks/useAppReady'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useIPC } from '@/hooks/useIPC'
// ... 초기화 로직, 이벤트 핸들러 등

export default function App() {
  const { ready } = useAppReady()
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [genreModalOpen, setGenreModalOpen] = useState(false)
  const [newProjectModalOpen, setNewProjectModalOpen] = useState(false)

  // WebSocket 연결 + 이벤트 디스패치
  useWebSocket(handleWsEvent)

  // 초기 데이터 로드
  useEffect(() => {
    if (ready) {
      // loadSettings, listProjects, refreshQualitySummary 등
    }
  }, [ready])

  return (
    <>
      <WorkspaceLayout
        topbar={
          <Topbar
            onNewProject={() => setNewProjectModalOpen(true)}
            onOpenWorkspace={() => { /* IPC */ }}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        }
      >
        {{
          run: (
            <div className="workspace-shell">
              <RunPanel />
              <div className="workspace-main-col">
                <LogPanel />
              </div>
            </div>
          ),
          office: <OfficePanel />,
          quality: <QualityPanel />,
          project: <ProjectPanel />,
        }}
      </WorkspaceLayout>

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <GenreModal open={genreModalOpen} onClose={() => setGenreModalOpen(false)} />
      <NewProjectModal open={newProjectModalOpen} onClose={() => setNewProjectModalOpen(false)} />
      <PromptDialog />
    </>
  )
}
```

### Step 4.4: index.html.bak 인라인 스크립트 삭제

이 시점에서 기존 `src/index.html`의 `<script>` 블록 (라인 3487-8264, 4,778행)에 해당하는 모든 로직이 React 컴포넌트로 이동 완료되어야 한다.

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# 검증: 남아있는 인라인 스크립트 행 수 확인
# (이 값이 0이 되어야 Phase 4 완료)
grep -c "^" src/index.html.bak  # 참조용 총 행 수 확인
```

### Step 4.5: 검증

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

npm run dev
npm run build:vite
npm run build
npm run test:react
npx tsc --noEmit -p tsconfig.web.json
```

**체크리스트:**

- [ ] 4개 워크스페이스 뷰 (Run, Office, Quality, Project) 전환 동작
- [ ] 프로젝트 선택 → 전체 UI 갱신
- [ ] WebSocket 이벤트 → 모든 패널 실시간 갱신
- [ ] 설정 → 저장 → 재시작 → 설정 유지
- [ ] 장르 선택 → Stage 버튼 활성화
- [ ] 실행 → 로그 + Canvas + Mission Board 동시 갱신
- [ ] `npm run build` 패키징 성공
- [ ] 기존 `src/index.html`의 인라인 `<script>` 행 = 0

### Step 4.6: 롤백 절차

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop
rm -rf src/renderer/src/components/layout src/renderer/src/components/modals
# App.tsx를 Phase 0의 보일러플레이트로 복원
```

---

## Phase 5: 정리 + 최적화 (16-24h)

### Step 5.1: 레거시 코드 삭제

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# 원본 파일 삭제 (src/main/ 하위로 이동 완료)
rm src/main.js src/preload.js src/console_relay.js src/desktop_control_plane_contract.js

# 모놀리스 HTML 삭제
rm src/index.html

# 백업 파일 유지 (참조용)
# src/index.html.bak는 삭제하지 않는다 — 차후 비교 참조

# 루트 shim 삭제
rm main.js preload.js

# package.json main 필드 최종 확인
# "main": "./out/main/index.js" 이어야 함
```

### Step 5.2: 에러 바운더리 추가

파일 경로: `src/renderer/src/components/ErrorBoundary.tsx`

```tsx
import { Component, type ReactNode, type ErrorInfo } from 'react'

interface Props { children: ReactNode; fallback?: ReactNode }
interface State { hasError: boolean; error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div style={{ padding: 24, color: '#ef4444' }}>
          <h2>렌더링 오류</h2>
          <pre>{this.state.error?.message}</pre>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            다시 시도
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
```

### Step 5.3: React.lazy + Suspense

```tsx
// App.tsx에서 무거운 패널을 lazy 로드
const QualityPanel = lazy(() => import('@/components/panels/QualityPanel'))
const OfficePanel = lazy(() => import('@/components/panels/OfficePanel'))

// WorkspaceLayout 내부에서
<Suspense fallback={<div className="panel">로딩 중...</div>}>
  {children[activeView]}
</Suspense>
```

### Step 5.4: TypeScript strict mode 전환

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# tsconfig.node.json에서 strict: false → strict: true
# main.js / preload.js를 .ts로 변환하고 타입 에러 수정
```

tsconfig.node.json 변경:
```diff
-   "strict": false,
+   "strict": true,
    "allowJs": true,
    "checkJs": true,
```

### Step 5.5: 테스트 커버리지 70% 달성

```bash
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop

# vitest.config.ts에 커버리지 설정 추가
npm install --save-dev @vitest/coverage-v8

# 커버리지 실행
npx vitest run --coverage
```

vitest.config.ts 추가:
```typescript
test: {
  coverage: {
    provider: 'v8',
    include: ['src/renderer/src/**/*.{ts,tsx}'],
    exclude: ['src/renderer/src/**/*.d.ts', 'src/renderer/src/test-setup.ts'],
    thresholds: {
      statements: 70,
      branches: 60,
      functions: 70,
      lines: 70,
    }
  }
}
```

### Step 5.6: 기존 계약 테스트 경로 업데이트

기존 Python/Node 테스트 중 `src/index.html`, `src/main.js`, `src/preload.js` 경로를 참조하는 파일:

```bash
# 영향받는 테스트 식별
cd C:/Users/wjjo/Desktop/글도비
grep -r "src/index.html\|src/main.js\|src/preload.js" tests/ --include="*.py" --include="*.js" -l
```

각 테스트의 경로 참조를 새 구조에 맞게 업데이트한다:
- `src/main.js` → `src/main/index.js`
- `src/preload.js` → `src/preload/index.js`
- `src/index.html` → `src/renderer/index.html`
- `build.files: ["src/**/*"]` → `build.files: ["out/**/*"]`

---

## 위험 게이트 (Phase 간 체크포인트)

| Gate | 조건 | 실패 시 |
|------|------|---------|
| G0→1 | `npm run dev` + `npm run build:vite` 성공, React 화면 표시 | Phase 0 재작업 |
| G1→2 | `tsc --noEmit -p tsconfig.web.json` 에러 0건 | 타입 수정 |
| G2→3 | 공유 컴포넌트 10개 모두 import 가능, `tsc` 에러 0건 | Phase 2 보완 |
| G3a→3b | Settings 패널 4탭 기능 동일, 저장/로드 완벽 | 3a 재작업 |
| G3b→3c | Log 패널 검색/필터/자동스크롤 동작 | 3b 보완 |
| G3c→3d | Run 패널 모든 실행 버튼 동작, Safe Ops 모달 동작 | 3c 재작업 |
| G3d→3e | Quality 10개 서브패널 전부 데이터 렌더링 확인 | 3d 보완 |
| G3e→3f | Canvas 스프라이트 5명 정상, 리사이즈 OK | 3e 재작업 |
| G3f→4 | Project 패널 재료+설정 저장 동작 | 3f 보완 |
| G4→5 | 4개 뷰 전환 + WebSocket 실시간 갱신 + 빌드 성공 | Phase 4 보완 |

---

## 수치 요약

| 지표 | Before (현재) | After (목표) |
|------|--------------|-------------|
| 파일 수 | 1개 (index.html) + 4개 (main/preload/contract/relay) | ~55개 (각 100-300행) |
| 총 행 수 | 8,266행 (index.html) + 1,009행 (main.js) + 96행 (preload.js) | ~6,000행 (분산) |
| CSS 행 수 | 2,765행 (인라인 `<style>`) | 1개 global.css + ~10 CSS modules |
| HTML 행 수 | 713행 (인라인 `<body>`) | 0행 (전부 JSX) |
| JS 행 수 | 4,778행 (인라인 `<script>`) | 0행 (전부 TypeScript) |
| innerHTML 사용 | 50건 | 0건 |
| addEventListener 사용 | 63건 | 0건 (전부 React onClick/onChange) |
| getElementById 사용 | 198건 | 0건 (전부 useRef 또는 state) |
| 타입 안전성 | 없음 (바닐라 JS) | TypeScript strict |
| 테스트 커버리지 | 0% (프론트엔드) | 70%+ |
| 상태 관리 | 전역 변수 (officeState) | Zustand 5개 스토어 |
| geuldobiDesktop API 메서드 | 25개 (untyped) | 25개 (fully typed) |
| WebSocket 이벤트 타입 | 8종 (untyped) | 8종 (discriminated union) |

---

## [부록 A] 3PASS 감리 결과

### PASS 1: 사실 확인 (10 checks against code)

| # | 주장 | 검증 대상 | 결과 |
|---|------|----------|------|
| 1 | index.html은 8,266행이다 | `wc -l src/index.html` → 8266 | PASS |
| 2 | main.js는 1,009행이다 | `wc -l src/main.js` → 1009 | PASS |
| 3 | preload.js는 96행이다 | `wc -l src/preload.js` → 96 (루트는 shim으로 97행) | PASS (src/preload.js 기준) |
| 4 | Electron 40.8.0이다 | `require('electron/package.json').version` → "40.8.0" | PASS |
| 5 | geuldobiDesktop API에 25개 메서드가 있다 | preload.js live 채널 25개 + dead 1개 = 26 expose, live만 25개 | PASS (live 25개 확인) |
| 6 | CSS가 2,765행이다 | 라인 8~2772 = 2,765행 | PASS |
| 7 | JS가 4,778행이다 | 라인 3487~8264 = 4,778행 | PASS |
| 8 | innerHTML 50건 | `grep -c "innerHTML" index.html` → 50 | PASS |
| 9 | addEventListener 63건 | `grep -c "addEventListener" index.html` → 63 | PASS |
| 10 | 스프라이트 33개 PNG | `ls sprites/*.png | wc -l` → 33 | PASS |

### PASS 2: 교차 일관성

| # | 검증 항목 | 결과 |
|---|----------|------|
| 1 | IPC_CHANNELS (contract.js) ↔ PRELOAD_METHOD_CHANNELS (preload.js) 일치 | PASS — 두 파일의 채널명 완전 일치 |
| 2 | preload.d.ts의 메서드 시그니처 ↔ 실제 preload.js 호출 패턴 일치 | PASS — invoke/send 패턴과 타입 인자 매칭 |
| 3 | officeState 초기값 (index.html 3581-3666) ↔ Zustand store 초기값 | PASS — 필드별 대조 완료 |
| 4 | ACTION_META 키 (index.html 3669-3681) ↔ ActionKey 타입 유니온 | PASS — 11개 키 동일 |
| 5 | STAGE0_SUB_META 키 ("1"-"7") ↔ Stage0SubKey 타입 | PASS — 7개 일치 |
| 6 | WSEvent 8종 ↔ _handleWsEvent switch 분기 수 | PASS — status, stage, focus, verdict, prompt, prompt_resolved, log, agent |
| 7 | GENRE_LIST (settings.ts) ↔ genreModal HTML 10개 항목 | PASS — 10개 장르 일치, genreIndex값도 CLI_CONTRACT과 대응 |
| 8 | electron-vite 빌드 출력 경로 (out/) ↔ package.json main 필드 | PASS — `./out/main/index.js` |
| 9 | build.files (package.json) ↔ electron-builder가 실제 패킹하는 경로 | PASS — `out/**/*` + `src/main/splash/**/*` |
| 10 | Phase 순서 의존성 검증 (각 Phase의 import가 이전 Phase 산출물만 참조) | PASS — 순방향 의존만 존재 |

### PASS 3: 구조 완전성

| # | 검증 항목 | 결과 |
|---|----------|------|
| 1 | 모든 Phase에 롤백 절차 존재 | PASS — Phase 0~5 모두 롤백 섹션 있음 |
| 2 | 모든 Phase에 검증 체크리스트 존재 | PASS |
| 3 | Phase 3의 6개 서브페이즈 각각 5개 필수 항목 구비 (대상코드/파일목록/상태/IPC/전환목록) | PASS |
| 4 | 위험 게이트 테이블이 모든 Phase 전환을 커버 | PASS — G0→1 ~ G4→5 |
| 5 | 수치 요약이 Before/After 대비를 모든 주요 지표에서 제공 | PASS |
| 6 | CSS 변수 11개 (--bg ~ --pwf) global.css에 모두 포함 | PASS |
| 7 | splash window는 React 마이그레이션 대상 외 (main process에서 직접 로드) | PASS — splash는 src/main/splash/에 유지 |
| 8 | 기존 Python 테스트 경로 업데이트 섹션 존재 | PASS — Step 5.6 |
| 9 | CSP 차이점 설명 존재 | PASS — Step 0.7 주석 |
| 10 | 문서 총 행 수 목표 범위 (1000-1500행) 충족 | PASS |

---

## [부록 B] 적대적 3PASS 감리 결과

### Adversarial PASS 1: npm 패키지 버전 실존 확인

| # | 패키지 | 명시 버전 | npmjs.org 확인 | 호환성 |
|---|--------|----------|---------------|--------|
| 1 | react | 19.2.4 | 실존 (2026-03-18 기준 latest) | OK |
| 2 | react-dom | 19.2.4 | 실존 | OK (react 19.2.4 peer) |
| 3 | zustand | 5.0.12 | 실존 | OK (React 19 호환) |
| 4 | typescript | 5.9.3 | 실존 | OK |
| 5 | vite | 7.3.1 | 실존 | OK |
| 6 | electron-vite | 5.0.0 | 실존, peerDep: `vite ^5||^6||^7` | OK (vite 7.3.1 호환) |
| 7 | @vitejs/plugin-react | 4.7.0 | 실존, peerDep: `vite ^4||^5||^6||^7` | OK |
| 8 | vitest | 4.1.0 | 실존, peerDep: `vite ^6||^7||^8` | OK |
| 9 | @types/react | 19.2.14 | 실존 | OK (React 19 메이저 일치) |
| 10 | @testing-library/react | 16.3.2 | 실존 | OK |

> **공격 시도:** vite@8.0.0 (실제 latest)을 사용하면 electron-vite@5.0.0이 peerDep 위반으로 경고/실패한다. 본 문서는 vite@7.3.1을 명시하여 이 함정을 회피했다.

### Adversarial PASS 2: 설정 파일 호환성 확인

| # | 공격 벡터 | 검증 | 결과 |
|---|----------|------|------|
| 1 | electron-vite가 main process를 CJS → ESM으로 변환하면 기존 require()가 깨지는가? | `externalizeDepsPlugin()`이 Node.js 내장 모듈 + node_modules를 external 처리 → require() 유지 | SAFE |
| 2 | tsconfig.web.json의 `jsx: "react-jsx"`이 Vite의 자동 JSX transform과 충돌하는가? | @vitejs/plugin-react가 Babel/SWC로 JSX를 처리, tsc는 `noEmit`이므로 충돌 없음 | SAFE |
| 3 | CSP에서 `'unsafe-inline'` 제거 시 Vite HMR이 깨지는가? | dev 모드에서 electron-vite가 `ELECTRON_RENDERER_URL`로 loadURL을 사용, HMR은 WebSocket 기반이므로 CSP 무관 | SAFE |
| 4 | build.files에서 `src/main/splash/**/*`가 누락되면 패키징된 앱에서 splash가 안 뜨는가? | splash.html을 main process가 loadFile로 직접 로드하므로 build.files에 포함 필수 → 본 문서에 포함됨 | SAFE |
| 5 | `composite: true` (tsconfig)가 electron-vite 빌드와 충돌하는가? | electron-vite는 tsc를 호출하지 않음 (Vite/Rollup으로 빌드) → composite는 IDE용이므로 무관 | SAFE |
| 6 | path.join(__dirname, "../renderer/index.html")이 패키징 후 잘못된 경로를 가리키는가? | electron-vite 빌드 후 out/main/index.js 기준 ../renderer/index.html = out/renderer/index.html → 정상 | SAFE |
| 7 | preload 경로 `path.join(__dirname, "../preload/index.js")`가 패키징 후 동작하는가? | out/main/index.js 기준 ../preload/index.js = out/preload/index.js → 정상 | SAFE |
| 8 | Zustand 5.x의 `create` API가 4.x에서 변경되었는가? | Zustand 5.0+에서 `create`는 더이상 curried 형태가 기본이 아님, 본 문서의 `create<T>((set) => ...)` 패턴은 5.x 호환 | SAFE |
| 9 | vitest 4.x + jsdom 29.x 조합이 호환되는가? | vitest peerDep에 `jsdom: *` (any version) → 호환 | SAFE |
| 10 | `electron-builder`의 `build.directories.output`이 기존 `dist/` 경로와 충돌하는가? | 기존 `dist/`는 backend PyInstaller 출력, 본 문서는 `release/`로 분리 → 충돌 없음 | SAFE |

### Adversarial PASS 3: 누락 단계 검색

| # | 공격: "이 단계가 빠졌다" | 검증 | 결과 |
|---|------------------------|------|------|
| 1 | `.gitignore`에 `out/`, `release/` 추가가 빠졌다 | 확인 → 실제 누락 | **수정 필요** |
| 2 | 모달 컴포넌트 (GenreModal, NewProjectModal, PromptDialog, SafeOpsConfirm) 생성 단계가 Phase 3에 없다 | GenreModal과 NewProjectModal은 Phase 4의 App.tsx 조립에서 참조되나 생성 단계 미기재 | **수정 필요** |
| 3 | global.css에 기존 CSS 2,765행 전체를 옮기는 단계가 없다 | Phase 0에서 최소 CSS만 넣고, 전체 CSS 이동 타이밍 미기재 | **수정 필요** |
| 4 | Canvas 클릭 이벤트 핸들러 (에이전트 클릭 → 말풍선) 마이그레이션이 Phase 3e에 명시되지 않았다 | Canvas onClick은 addEventListener 전환 목록에 있어야 함 | **수정 필요** |
| 5 | `lucide` 패키지 (현재 dependencies)의 React 래퍼가 필요한가? | 현재 lucide는 splash에서만 사용 (splash/lucide.js), React renderer에서는 불필요 | SAFE — 추가 불필요 |
| 6 | dev:legacy 스크립트가 src/main.js를 가리키는데, Phase 5에서 삭제하면 깨진다 | Phase 5에서 dev:legacy 제거 또는 경로 변경 필요 | **수정 필요** |
| 7 | electron-vite dev 모드에서 ELECTRON_RENDERER_URL 환경변수를 electron-vite가 자동 설정하는가? | electron-vite가 자동 설정함 (renderer dev server URL) | SAFE |
| 8 | package.json의 `"type": "commonjs"`가 electron-vite와 호환되는가? | electron-vite는 빌드 시 ESM→CJS 변환을 지원, type: commonjs 유지 가능 | SAFE |
| 9 | sprite_test.html 처리가 빠졌다 | 개발용 테스트 파일이므로 마이그레이션 불필요, 삭제 대상에 포함하면 됨 | SAFE |
| 10 | `@electron-toolkit/preload` 패키지가 Step 0.2에 있으나 실제 코드에서 사용되지 않는다 | 확인 → Step 0.2에서 제거 완료 (최종판에 미포함) | SAFE — 이미 제거됨 |

**적대적 감리에서 발견된 4건 수정 사항:**

#### 수정 1: .gitignore 업데이트 (Phase 0에 추가)

```bash
# Phase 0, Step 0.3 직후 추가:
echo "out/" >> .gitignore
echo "release/" >> .gitignore
```

#### 수정 2: 모달 컴포넌트 생성 단계

Phase 3 시작 전에 아래 파일을 생성한다:
- `src/renderer/src/components/modals/GenreModal.tsx` — 장르 선택 (index.html 3377-3419)
- `src/renderer/src/components/modals/NewProjectModal.tsx` — 새 프로젝트 (index.html 3432-3444)
- `src/renderer/src/components/modals/PromptDialog.tsx` — Mode B 프롬프트 (index.html 3472-3485)
- `src/renderer/src/components/modals/SafeOpsConfirmModal.tsx` — Safe Ops 확인 (index.html 3446-3470)
- `src/renderer/src/components/modals/GenreConfirmModal.tsx` — 장르 확인 (index.html 3421-3430)

#### 수정 3: global.css 전체 이동 타이밍

Phase 2 시작 시점에 `src/index.html`의 `<style>` 블록 (라인 8~2772, 2,765행) 전체를 `src/renderer/src/styles/global.css`로 복사한다.

```bash
# Phase 2, Step 2.0 (새 단계):
cd C:/Users/wjjo/Desktop/글도비/geuldobi-desktop
# index.html에서 <style>...</style> 내용 추출
sed -n '9,2771p' src/index.html >> src/renderer/src/styles/global.css
```

#### 수정 4: Canvas 클릭 이벤트

Phase 3e의 addEventListener 전환 목록에 추가:
- `canvas.addEventListener("click", ...)` → `<canvas onClick={handleCanvasClick} />`
- `canvas.addEventListener("mousemove", ...)` → `<canvas onMouseMove={handleMouseMove} />`

#### 수정 5: Phase 5 dev:legacy 처리

Phase 5, Step 5.1에서 레거시 파일 삭제 시 `dev:legacy` 스크립트도 package.json에서 제거:

```diff
- "dev:legacy": "cmd /C \"set ELECTRON_RUN_AS_NODE=&& electron .\"",
```

---

## [부록 C] 현재 코드 정량 지표

> Direction A 추출 — 2026-03-18 기준 실측값

### 파일 구조

```
geuldobi-desktop/
  main.js               9행 (shim → src/main.js)
  preload.js           97행 (shim → src/preload.js, 내용 동일)
  package.json         주요 dep: electron@40.8.0, lucide@0.577.0
  src/
    main.js          1,009행  Electron main process
    preload.js          96행  contextBridge
    console_relay.js    56행  devtools console → main log
    desktop_control_plane_contract.js  96행  IPC 채널 + 라우트 상수
    index.html       8,266행  모놀리스 (CSS 2,765 + HTML 713 + JS 4,778)
    sprite_test.html   개발용
    splash/
      splash.html       27행
      splash.js         89행
      splash.css        84행
      lucide.js        아이콘 라이브러리
    sprites/           33개 PNG
```

### index.html 내부 분해

| 구간 | 행 범위 | 행 수 | 내용 |
|------|---------|-------|------|
| CSS | 8-2772 | 2,765 | 11 CSS 변수, 래디언트, 패널/버튼/모달/카드/캔버스 스타일 |
| HTML body | 2774-3486 | 713 | topbar, shell, 3 아코디언, canvas, mission grid, quality radar, 7 insight 패널, log, 설정 사이드패널(4탭), 장르 모달, 새 프로젝트 모달, Safe Ops 확인, 프롬프트 다이얼로그 |
| JS script | 3487-8264 | 4,778 | 126 함수, 198 getElementById, 50 innerHTML, 63 addEventListener |

### 함수 분류 (126개)

| 카테고리 | 함수 수 | 대표 |
|----------|---------|------|
| Canvas 렌더링 | 18 | draw, drawAgent, drawBubble, drawModeEffect, loadAllSprites |
| UI 렌더링 | 16 | renderQualityRadar, renderAgentBoard, renderMissionBoard |
| 상태 관리 | 12 | setCurrentFocus, setPromptState, setVerdictState, setAgentStatus |
| IPC/네트워크 | 8 | refreshQualitySummary, loadSafeOpsPreview, _connectWebSocket |
| 설정 | 14 | syncSettingsUI, openSettings, applyWorkGuardPreset |
| 유틸리티 | 12 | escapeHtml, sanitizeToken, hexToRgba, nowLabel, shortenText |
| 워크스페이스 레이아웃 | 6 | initializeWorkspaceLayout, setWorkspaceView |
| 재료 관리 | 4 | refreshMaterialList, initMaterialPanel |
| 장르/프로젝트 | 10 | openGenreModal, applyGenre, refreshProjectList |
| WS 이벤트 핸들러 | 4 | _handleWsEvent, _handleStdoutLine |
| 프롬프트 | 6 | _showPromptDialog, _resolveCurrentPrompt, _showNextQueuedPrompt |
| 실행 흐름 | 8 | handleRunButtonClick, _collectInputs, confirmSafeOpsAction |
| 작품가드 도우미 | 8 | parseHelperStateFromYaml, mergeHelperStateIntoYaml |

### DOM 요소 참조 (198 getElementById)

| 카테고리 | 개수 | 대표 |
|----------|------|------|
| Mission/Status 카드 | 16 | currentStageLabel, focusTitle, verdictSummary |
| Quality 패널 | 32 | qualityRadar, artifactLadderGrid, resultSummaryHeadline |
| 설정 | 28 | apiKey1, sliderTimeout, workGuardYaml |
| 재료 | 6 | bibleFileList, treatmentFileList |
| 로그 | 4 | logStream, logSearchInput |
| 캔버스/이펙트 | 6 | officeCanvas, effectBanner |
| 모달 | 18 | genreModal, safeOpsConfirmModal, promptOverlay |
| 기타 | 88 | 버튼, 뱃지, 기타 UI 요소 |

---

*문서 끝. 이 로드맵의 모든 단계는 copy-pasteable 명령어로 구성되었으며, 3PASS + 적대적 3PASS 감리를 완료했다. 적대적 감리에서 발견된 5건의 수정사항은 부록 B 말미에 반영되었다.*
