const electron = require("electron");
const app = electron.app;
const BrowserWindow = electron.BrowserWindow;
const ipcMain = electron.ipcMain;
const { dialog } = electron;
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

if (!app || !BrowserWindow || !ipcMain) {
  throw new Error(
    `Electron main API unavailable: keys=${Object.keys(electron).join(",")}`
  );
}

const SPLASH_WIDTH = 400;
const SPLASH_HEIGHT = 260;
const SPLASH_FALLBACK_MS = 8000; // uvicorn 기동 대기 포함
const STATUS_BASE_URL = "http://127.0.0.1:8300";
const SPIKE_AUTOCLOSE_MS = Number(process.env.SPIKE_AUTOCLOSE_MS || "0");

let mainWindow = null;
let splashWindow = null;
let didSwitchToMain = false;
let fallbackTimer = null;
let firstRun = false;
let backendProcess = null;

// ─── 앱 경로 ─────────────────────────────────────────────────────────────────

function getLocalAppDataRoot() {
  if (process.platform === "win32" && process.env.LOCALAPPDATA) {
    return process.env.LOCALAPPDATA;
  }
  return path.join(os.homedir(), "AppData", "Local");
}

function getAppDir() {
  return path.join(getLocalAppDataRoot(), "Geuldobi");
}

/** 작업 폴더 — 내 문서/글도비 (사용자가 쉽게 찾을 수 있는 경로) */
function getWorkspaceDir() {
  if (app.isPackaged) {
    const documentsDir = app.getPath("documents");
    return path.join(documentsDir, "글도비");
  }
  // 개발 모드: 프로젝트 루트 그대로
  return path.resolve(__dirname, "..", "..");
}

const SETTINGS_PATH = path.join(getAppDir(), "settings.json");

function ensureFirstRunFlag() {
  const appDir = getAppDir();
  const markerFile = path.join(appDir, ".first_run");

  fs.mkdirSync(appDir, { recursive: true });
  if (!fs.existsSync(markerFile)) {
    fs.writeFileSync(markerFile, new Date().toISOString(), "utf8");
    return true;
  }
  return false;
}

// ─── Backend (uvicorn) 자동기동 ──────────────────────────────────────────────
let backendRestartCount = 0;
const MAX_BACKEND_RESTARTS = 2;

function startBackend() {
  if (backendProcess) return;

  const isDev = !app.isPackaged;

  let cmd, args, cwd;

  if (isDev) {
    // 개발 모드: python -m uvicorn 직접 실행
    const backendCwd = path.resolve(__dirname, "..", "..");
    cmd = process.env.PYTHON_PATH || "python";
    args = ["-m", "uvicorn", "modules.api.bridge_server:app", "--port", "8300", "--log-level", "info"];
    cwd = backendCwd;
    console.log(`[backend] DEV mode — python at ${cwd}`);
  } else {
    // 배포 모드: PyInstaller 빌드된 backend.exe 실행
    const resourcesPath = process.resourcesPath;
    cmd = path.join(resourcesPath, "backend", "backend.exe");
    args = [];
    // 작업 디렉토리는 내 문서/글도비 (사용자 접근 용이)
    const workspace = getWorkspaceDir();
    fs.mkdirSync(workspace, { recursive: true });
    cwd = workspace;
    console.log(`[backend] PROD mode — ${cmd}, workspace=${cwd}`);
  }

  try {
    backendProcess = spawn(cmd, args, {
      cwd,
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUNBUFFERED: "1",
        GEULDOBI_DESKTOP_MODE: "1",
        ...(app.isPackaged ? {
          GEULDOBI_WORKSPACE: getWorkspaceDir(),
          GEULDOBI_ENGINE_EXE: path.join(process.resourcesPath, "engine", "engine.exe"),
        } : {}),
      },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });

    backendProcess.stdout.on("data", (data) => {
      console.log(`[backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on("data", (data) => {
      // uvicorn logs to stderr by default
      console.log(`[backend] ${data.toString().trim()}`);
    });

    backendProcess.on("error", (err) => {
      console.error(`[backend] spawn error: ${err.message}`);
      backendProcess = null;
    });

    // 기동 타임아웃 — 15초 내 stdout 없으면 경고
    const startupTimer = setTimeout(() => {
      if (backendProcess && backendProcess.exitCode === null) {
        console.warn("[backend] startup slow (>15s), check logs");
      }
    }, 15000);

    backendProcess.on("exit", (code, signal) => {
      console.log(`[backend] exited code=${code} signal=${signal}`);
      backendProcess = null;
      // 예기치 않은 종료 시 자동 재시작 (최대 2회)
      if (code !== 0 && code !== null && !app.isQuitting && backendRestartCount < MAX_BACKEND_RESTARTS) {
        backendRestartCount++;
        console.log(`[backend] unexpected exit, restarting in 2s... (${backendRestartCount}/${MAX_BACKEND_RESTARTS})`);
        setTimeout(() => {
          if (!backendProcess && !app.isQuitting) {
            startBackend();
          }
        }, 2000);
      } else if (backendRestartCount >= MAX_BACKEND_RESTARTS) {
        console.error("[backend] max restarts reached, giving up");
      }
    });
  } catch (err) {
    console.error(`[backend] failed to start: ${err.message}`);
    backendProcess = null;
  }
}

function stopBackend() {
  if (!backendProcess) return;
  const pid = backendProcess.pid;
  console.log(`[backend] stopping pid=${pid}...`);
  try {
    if (process.platform === "win32") {
      // Windows: taskkill로 프로세스 트리 종료 (동기 대기)
      const tk = spawn("taskkill", ["/pid", String(pid), "/t", "/f"], {
        windowsHide: true,
      });
      tk.on("error", (err) => console.error(`[backend] taskkill error: ${err.message}`));
      tk.on("exit", (code) => {
        if (code !== 0) console.warn(`[backend] taskkill exited with code ${code}`);
      });
    } else {
      backendProcess.kill("SIGTERM");
    }
  } catch (err) {
    console.error(`[backend] stop error: ${err.message}`);
  }
  backendProcess = null;
}

// ─── 윈도우 생성 ─────────────────────────────────────────────────────────────

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 720,
    show: false,
    backgroundColor: "#f8fafc",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, "index.html"));
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: SPLASH_WIDTH,
    height: SPLASH_HEIGHT,
    frame: false,
    resizable: false,
    movable: true,
    minimizable: false,
    maximizable: false,
    fullscreenable: false,
    alwaysOnTop: true,
    backgroundColor: "#f8fafc",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  splashWindow.once("ready-to-show", () => {
    splashWindow.show();
    console.log("splash window shown");
  });

  splashWindow.loadFile(path.join(__dirname, "splash", "splash.html"));
  splashWindow.on("closed", () => {
    splashWindow = null;
  });
}

function switchToMain(reason) {
  if (didSwitchToMain) return;
  didSwitchToMain = true;

  if (fallbackTimer) {
    clearTimeout(fallbackTimer);
    fallbackTimer = null;
  }

  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close();
  }

  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show();
    mainWindow.focus();
    mainWindow.webContents.send("app:ready", { reason });
    console.log(`switched to main window (${reason})`);
  }
}

function bootstrapWindows() {
  firstRun = ensureFirstRunFlag();
  createMainWindow();
  createSplashWindow();

  fallbackTimer = setTimeout(() => {
    switchToMain("fallback-timeout");
  }, SPLASH_FALLBACK_MS);
}

// ─── Splash IPC ──────────────────────────────────────────────────────────────

ipcMain.handle("splash:get-config", () => {
  return {
    firstRun,
    fallbackMs: SPLASH_FALLBACK_MS,
    statusBaseUrl: STATUS_BASE_URL
  };
});

ipcMain.on("splash:backend-ready", () => {
  switchToMain("backend-idle");
});

// ─── Bridge API IPC 핸들러 ──────────────────────────────────────────────────

async function bridgeFetch(urlPath, options = {}) {
  const url = `${STATUS_BASE_URL}${urlPath}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.error(`Bridge HTTP ${res.status}: ${url}`, text.slice(0, 200));
      return { ok: false, code: `HTTP_${res.status}`, message: `서버 오류 (${res.status})`, data: null };
    }
    return await res.json();
  } catch (err) {
    console.error(`Bridge fetch failed: ${url}`, err.message);
    return { ok: false, code: "NETWORK_ERROR", message: err.message, data: null };
  }
}

ipcMain.handle("bridge:run", async (_, { key, subKey, inputs }) => {
  const body = { key };
  if (subKey) body.sub_key = subKey;
  if (inputs && Object.keys(inputs).length > 0) body.inputs = inputs;
  return bridgeFetch("/run", { method: "POST", body: JSON.stringify(body) });
});

ipcMain.handle("bridge:stop", async () => {
  return bridgeFetch("/stop", { method: "POST" });
});

ipcMain.handle("bridge:status", async () => {
  return bridgeFetch("/status");
});

ipcMain.handle("bridge:get-url", () => {
  return { wsUrl: "ws://127.0.0.1:8300/events", httpUrl: STATUS_BASE_URL };
});

ipcMain.handle("bridge:get-quality-summary", async (_, { project, lookback = 5 }) => {
  const safeProject = String(project || "").trim();
  const safeLookback = Number.isFinite(Number(lookback)) ? Number(lookback) : 5;
  return bridgeFetch(
    `/quality/summary?project=${encodeURIComponent(safeProject)}&lookback=${encodeURIComponent(String(safeLookback))}`
  );
});

ipcMain.handle("bridge:resolve-prompt", async (_, { runId, promptId, value }) => {
  return bridgeFetch(`/run/${encodeURIComponent(runId)}/input`, {
    method: "POST",
    body: JSON.stringify({ prompt_id: promptId, value }),
  });
});

// ─── 설정 영속화 IPC ─────────────────────────────────────────────────────────

ipcMain.handle("bridge:save-settings", async (_, settings) => {
  try {
    const dir = path.dirname(SETTINGS_PATH);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2), "utf8");
    return { ok: true };
  } catch (err) {
    console.error("Settings save failed:", err.message);
    return { ok: false, message: err.message };
  }
});

ipcMain.handle("bridge:load-settings", async () => {
  try {
    if (!fs.existsSync(SETTINGS_PATH)) return null;
    const raw = fs.readFileSync(SETTINGS_PATH, "utf8");
    try {
      return JSON.parse(raw);
    } catch (parseErr) {
      console.error("Settings JSON corrupted, resetting:", parseErr.message);
      // 깨진 파일 백업 후 삭제
      const backupPath = SETTINGS_PATH + ".bak";
      try { fs.renameSync(SETTINGS_PATH, backupPath); } catch (_) {}
      return null;
    }
  } catch (err) {
    console.error("Settings load failed:", err.message);
    return null;
  }
});

// ─── 재료 파일 관리 IPC ──────────────────────────────────────────────────────

function getEngineRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "engine");
  }
  return path.resolve(__dirname, "..", "..");
}

function getMaterialRoot() {
  // 패키징 모드: 내 문서/글도비 (사용자 접근 용이), 개발 모드: 엔진 루트
  if (app.isPackaged) {
    return getWorkspaceDir();
  }
  return getEngineRoot();
}

ipcMain.handle("material:list-files", async (_, folder) => {
  if (folder !== "bible" && folder !== "treatments") {
    return { ok: false, files: [], message: "invalid folder" };
  }
  try {
    const dir = path.join(getMaterialRoot(), folder);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      return { ok: true, files: [] };
    }
    const entries = fs.readdirSync(dir)
      .filter(f => !f.startsWith("."))
      .map(f => {
        const stat = fs.statSync(path.join(dir, f));
        return { name: f, size: stat.size, isDir: stat.isDirectory() };
      });
    return { ok: true, files: entries };
  } catch (err) {
    return { ok: false, files: [], message: err.message };
  }
});

ipcMain.handle("material:import-file", async (_, folder) => {
  if (folder !== "bible" && folder !== "treatments") {
    return { ok: false, message: "invalid folder" };
  }
  if (!mainWindow || mainWindow.isDestroyed()) {
    return { ok: false, message: "윈도우가 준비되지 않았습니다" };
  }
  const result = await dialog.showOpenDialog(mainWindow, {
    title: folder === "bible" ? "Bible 파일 선택" : "Treatment 파일 선택",
    filters: [
      { name: "JSON / 텍스트", extensions: ["json", "txt"] },
      { name: "모든 파일", extensions: ["*"] }
    ],
    properties: ["openFile", "multiSelections"]
  });
  if (result.canceled || result.filePaths.length === 0) {
    return { ok: false, message: "cancelled" };
  }
  const destDir = path.join(getMaterialRoot(), folder);
  fs.mkdirSync(destDir, { recursive: true });
  const imported = [];
  const errors = [];
  for (const src of result.filePaths) {
    const fname = path.basename(src);
    const dest = path.join(destDir, fname);
    try {
      fs.copyFileSync(src, dest);
      imported.push(fname);
    } catch (copyErr) {
      console.error(`[material] copy failed: ${fname}`, copyErr.message);
      errors.push(fname);
    }
  }
  if (errors.length > 0 && imported.length === 0) {
    return { ok: false, message: `파일 복사 실패: ${errors.join(", ")}` };
  }
  return { ok: true, imported };
});

ipcMain.handle("material:delete-file", async (_, folder, fileName) => {
  if (folder !== "bible" && folder !== "treatments") {
    return { ok: false, message: "invalid folder" };
  }
  // 경로 탈출 방지
  if (fileName.includes("..") || fileName.includes("/") || fileName.includes("\\")) {
    return { ok: false, message: "invalid filename" };
  }
  try {
    const filePath = path.join(getMaterialRoot(), folder, fileName);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
    return { ok: true };
  } catch (err) {
    return { ok: false, message: err.message };
  }
});

// ─── 프로젝트 관리 IPC ────────────────────────────────────────────────────────

function getProjectsDir() {
  if (app.isPackaged) {
    return path.join(getWorkspaceDir(), "projects");
  }
  return path.join(getEngineRoot(), "projects");
}

ipcMain.handle("project:list", async () => {
  try {
    const dir = getProjectsDir();
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      return { ok: true, projects: [] };
    }
    const entries = fs.readdirSync(dir)
      .filter(f => {
        try {
          return fs.statSync(path.join(dir, f)).isDirectory();
        } catch { return false; }
      });
    // main_a.py iterdir() 순서와 동일하게 유지 (정렬 없음)
    return { ok: true, projects: entries };
  } catch (err) {
    return { ok: false, projects: [], message: err.message };
  }
});

ipcMain.handle("project:create", async (_, name) => {
  if (!name || typeof name !== "string") {
    return { ok: false, message: "프로젝트 이름을 입력하세요" };
  }
  // 안전한 이름만 허용
  const safeName = name.trim().replace(/[<>:"/\\|?*]/g, "_");
  if (!safeName) {
    return { ok: false, message: "유효하지 않은 이름입니다" };
  }
  try {
    const dir = path.join(getProjectsDir(), safeName);
    if (fs.existsSync(dir)) {
      return { ok: false, message: "이미 존재하는 프로젝트입니다" };
    }
    fs.mkdirSync(dir, { recursive: true });
    return { ok: true, name: safeName };
  } catch (err) {
    return { ok: false, message: err.message };
  }
});

// ─── 작업 폴더 열기 IPC ──────────────────────────────────────────────────────

ipcMain.handle("workspace:open-folder", async () => {
  const dir = app.isPackaged ? getWorkspaceDir() : path.resolve(__dirname, "..", "..");
  fs.mkdirSync(dir, { recursive: true });
  const { shell } = electron;
  shell.openPath(dir);
  return { ok: true, path: dir };
});

ipcMain.handle("workspace:get-path", async () => {
  const dir = app.isPackaged ? getWorkspaceDir() : path.resolve(__dirname, "..", "..");
  return { ok: true, path: dir };
});

// ─── 앱 수명주기 ─────────────────────────────────────────────────────────────

app.whenReady().then(() => {
  // 1. uvicorn 백엔드 기동 (splash가 폴링으로 감지)
  startBackend();

  // 2. 윈도우 생성
  bootstrapWindows();

  if (Number.isFinite(SPIKE_AUTOCLOSE_MS) && SPIKE_AUTOCLOSE_MS > 0) {
    setTimeout(() => {
      console.log(`auto-close after ${SPIKE_AUTOCLOSE_MS}ms`);
      app.quit();
    }, SPIKE_AUTOCLOSE_MS);
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      didSwitchToMain = false;
      bootstrapWindows();
    }
  });
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  app.isQuitting = true;
  stopBackend();
});
