const electron = require("electron");
const app = electron.app;
const BrowserWindow = electron.BrowserWindow;
const ipcMain = electron.ipcMain;
const { dialog } = electron;
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { attachConsoleRelay } = require("./console_relay");
const {
  IPC_CHANNELS,
  BRIDGE_MANAGED_ROUTES,
  buildRunInputRoute,
} = require("./desktop_control_plane_contract");

if (!app || !BrowserWindow || !ipcMain) {
  throw new Error(
    `Electron main API unavailable: keys=${Object.keys(electron).join(",")}`
  );
}

const DEBUG_LOG_PATH = path.join(
  process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"),
  "Geuldobi",
  "electron-main.log"
);

function debugLog(...parts) {
  const line = `[${new Date().toISOString()}] ${parts
    .map((part) => {
      if (part instanceof Error) return `${part.name}: ${part.message}\n${part.stack || ""}`;
      if (typeof part === "string") return part;
      try {
        return JSON.stringify(part);
      } catch {
        return String(part);
      }
    })
    .join(" ")}\n`;
  try {
    fs.mkdirSync(path.dirname(DEBUG_LOG_PATH), { recursive: true });
    fs.appendFileSync(DEBUG_LOG_PATH, line, "utf8");
  } catch {
    // Ignore debug logging failures.
  }
}

process.on("uncaughtException", (err) => {
  debugLog("uncaughtException", err);
});

process.on("unhandledRejection", (reason) => {
  debugLog("unhandledRejection", reason);
});

debugLog("main.js boot", {
  pid: process.pid,
  packaged: app.isPackaged,
  resourcesPath: process.resourcesPath,
  cwd: process.cwd(),
});

const SPLASH_WIDTH = 400;
const SPLASH_HEIGHT = 260;
const SPLASH_FALLBACK_MS = 8000; // uvicorn 기동 대기 포함
const STATUS_BASE_URL = "http://127.0.0.1:8300";
const EVENTS_WS_URL = "ws://127.0.0.1:8300/events";
const PACKAGED_RUNTIME_MODEL = "source_bundle_primary";
const DESKTOP_BRIDGE_TRANSPORT = Object.freeze({
  networkErrorCode: "NETWORK_ERROR",
  httpErrorPrefix: "HTTP_",
  envelopeVersion: "desktop_bridge_v1",
});
const SPIKE_AUTOCLOSE_MS = Number(process.env.SPIKE_AUTOCLOSE_MS || "0");
const CLI_CONTRACT = Object.freeze({
  defaultGenreIndex: 3,
  projectIndexBase: 1,
  projectSort: "lexical",
  genreIndexMap: Object.freeze({
    wuxia: 1,
    hunter: 2,
    investment: 3,
    fantasy: 4,
    composer: 5,
    cooking: 6,
    alt_history: 7,
    actor: 8,
    sports: 9,
    medical: 10,
  }),
});

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
    debugLog("startBackend", { cmd, args, cwd });
    backendProcess = spawn(cmd, args, {
      cwd,
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUNBUFFERED: "1",
        GEULDOBI_DESKTOP_MODE: "1",
        ...(app.isPackaged ? {
          GEULDOBI_PACKAGED_RUNTIME_MODEL: PACKAGED_RUNTIME_MODEL,
          GEULDOBI_WORKSPACE: getWorkspaceDir(),
          GEULDOBI_PROJECTS_ROOT: path.join(getWorkspaceDir(), "projects"),
        } : {}),
      },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });

    backendProcess.stdout.on("data", (data) => {
      console.log(`[backend] ${data.toString().trim()}`);
      debugLog("backend stdout", data.toString().trim());
    });

    backendProcess.stderr.on("data", (data) => {
      // uvicorn logs to stderr by default
      console.log(`[backend] ${data.toString().trim()}`);
      debugLog("backend stderr", data.toString().trim());
    });

    backendProcess.on("error", (err) => {
      console.error(`[backend] spawn error: ${err.message}`);
      debugLog("backend error", err);
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
      debugLog("backend exit", { code, signal });
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
    debugLog("startBackend failed", err);
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

  debugLog("createMainWindow", {
    preload: path.join(__dirname, "preload.js"),
    html: path.join(__dirname, "index.html"),
  });
  attachConsoleRelay(mainWindow.webContents, {
    windowName: "mainWindow",
    logFn: debugLog,
  });
  mainWindow.webContents.on("did-finish-load", () => {
    debugLog("mainWindow did-finish-load");
  });
  mainWindow.webContents.on("did-fail-load", (_event, code, description, url, isMainFrame) => {
    debugLog("mainWindow did-fail-load", { code, description, url, isMainFrame });
  });
  mainWindow.webContents.on("render-process-gone", (_event, details) => {
    debugLog("mainWindow render-process-gone", details);
  });
  mainWindow.loadFile(path.join(__dirname, "index.html")).catch((err) => {
    debugLog("mainWindow loadFile rejected", err);
  });
  mainWindow.on("closed", () => {
    debugLog("mainWindow closed");
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
    debugLog("splashWindow ready-to-show");
  });

  attachConsoleRelay(splashWindow.webContents, {
    windowName: "splashWindow",
    logFn: debugLog,
  });
  splashWindow.webContents.on("did-finish-load", () => {
    debugLog("splashWindow did-finish-load");
  });
  splashWindow.webContents.on("did-fail-load", (_event, code, description, url, isMainFrame) => {
    debugLog("splashWindow did-fail-load", { code, description, url, isMainFrame });
  });
  splashWindow.webContents.on("render-process-gone", (_event, details) => {
    debugLog("splashWindow render-process-gone", details);
  });
  splashWindow.loadFile(path.join(__dirname, "splash", "splash.html")).catch((err) => {
    debugLog("splashWindow loadFile rejected", err);
  });
  splashWindow.on("closed", () => {
    debugLog("splashWindow closed");
    splashWindow = null;
  });
}

function switchToMain(reason) {
  if (didSwitchToMain) return;
  didSwitchToMain = true;
  debugLog("switchToMain", { reason });

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
  debugLog("bootstrapWindows", { firstRun });
  createMainWindow();
  createSplashWindow();

  fallbackTimer = setTimeout(() => {
    debugLog("fallbackTimer fired");
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
  debugLog("ipc splash:backend-ready");
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
      let backendPayload = null;
      const text = await res.text().catch(() => "");
      if (text) {
        try {
          backendPayload = JSON.parse(text);
        } catch {
          backendPayload = null;
        }
      }
      console.error(`Bridge HTTP ${res.status}: ${url}`, text.slice(0, 200));
      return {
        ok: false,
        code: `${DESKTOP_BRIDGE_TRANSPORT.httpErrorPrefix}${res.status}`,
        message: `?쒕쾭 ?ㅻ쪟 (${res.status})`,
        data: {
          envelope_version: DESKTOP_BRIDGE_TRANSPORT.envelopeVersion,
          namespace: "desktop_transport",
          transport_status: res.status,
          url_path: urlPath,
          backend_code: typeof backendPayload?.code === "string" ? backendPayload.code : null,
          backend_message: typeof backendPayload?.message === "string" ? backendPayload.message : null,
        },
      };
      return { ok: false, code: `HTTP_${res.status}`, message: `서버 오류 (${res.status})`, data: null };
    }
    return await res.json();
  } catch (err) {
    console.error(`Bridge fetch failed: ${url}`, err.message);
    return {
      ok: false,
      code: DESKTOP_BRIDGE_TRANSPORT.networkErrorCode,
      message: err.message,
      data: {
        envelope_version: DESKTOP_BRIDGE_TRANSPORT.envelopeVersion,
        namespace: "desktop_transport",
        transport_status: null,
        url_path: urlPath,
        backend_code: null,
        backend_message: null,
      },
    };
  }
}

ipcMain.handle(IPC_CHANNELS.bridge.run, async (_, { key, subKey, inputs, approvalId }) => {
  const body = { key };
  if (subKey) body.sub_key = subKey;
  if (inputs && Object.keys(inputs).length > 0) body.inputs = inputs;
  if (typeof approvalId === "string" && approvalId.trim()) {
    body.approval_id = approvalId.trim();
  }
  return bridgeFetch(BRIDGE_MANAGED_ROUTES.run, { method: "POST", body: JSON.stringify(body) });
});

ipcMain.handle(IPC_CHANNELS.bridge.stop, async () => {
  return bridgeFetch(BRIDGE_MANAGED_ROUTES.stop, { method: "POST" });
});

// Dead-candidate compatibility surface. No active renderer consumer today.
ipcMain.handle(IPC_CHANNELS.bridge.status, async () => {
  return bridgeFetch(BRIDGE_MANAGED_ROUTES.status);
});

ipcMain.handle(IPC_CHANNELS.bridge.getUrl, () => {
  return { wsUrl: EVENTS_WS_URL, httpUrl: STATUS_BASE_URL };
});

ipcMain.handle(IPC_CHANNELS.bridge.getCliContract, () => {
  return CLI_CONTRACT;
});

ipcMain.handle(IPC_CHANNELS.bridge.getQualitySummary, async (_, { project, lookback = 5 }) => {
  const safeProject = String(project || "").trim();
  const safeLookback = Number.isFinite(Number(lookback)) ? Number(lookback) : 5;
  return bridgeFetch(
    `${BRIDGE_MANAGED_ROUTES.qualitySummary}?project=${encodeURIComponent(safeProject)}&lookback=${encodeURIComponent(
      String(safeLookback)
    )}`
  );
});

ipcMain.handle(IPC_CHANNELS.bridge.getQualityDashboard, async (_, { project, lookback = 5 }) => {
  const safeProject = String(project || "").trim();
  const safeLookback = Number.isFinite(Number(lookback)) ? Number(lookback) : 5;
  return bridgeFetch(
    `${BRIDGE_MANAGED_ROUTES.qualityDashboard}?project=${encodeURIComponent(safeProject)}&lookback=${encodeURIComponent(
      String(safeLookback)
    )}`
  );
});

ipcMain.handle(IPC_CHANNELS.bridge.getSafeOpsPreview, async (_, { project }) => {
  const safeProject = String(project || "").trim();
  return bridgeFetch(`${BRIDGE_MANAGED_ROUTES.safeOpsPreview}?project=${encodeURIComponent(safeProject)}`);
});

ipcMain.handle(IPC_CHANNELS.bridge.saveQualityReview, async (_, { project, epNum, operatorLabel, note = "" }) => {
  return bridgeFetch(BRIDGE_MANAGED_ROUTES.qualityReview, {
    method: "POST",
    body: JSON.stringify({
      project,
      ep_num: epNum,
      operator_label: operatorLabel,
      note,
    }),
  });
});

ipcMain.handle(IPC_CHANNELS.bridge.resolvePrompt, async (_, { runId, promptId, value }) => {
  return bridgeFetch(buildRunInputRoute(runId), {
    method: "POST",
    body: JSON.stringify({ prompt_id: promptId, value }),
  });
});

// ─── 설정 영속화 IPC ─────────────────────────────────────────────────────────

ipcMain.handle(IPC_CHANNELS.bridge.saveSettings, async (_, settings) => {
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

ipcMain.handle(IPC_CHANNELS.bridge.loadSettings, async () => {
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

ipcMain.handle(IPC_CHANNELS.material.listFiles, async (_, folder) => {
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

ipcMain.handle(IPC_CHANNELS.material.importFile, async (_, folder) => {
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

ipcMain.handle(IPC_CHANNELS.material.deleteFile, async (_, folder, fileName) => {
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

function sanitizeProjectName(name) {
  if (typeof name !== "string") {
    return "";
  }
  return name.trim().replace(/[<>:"/\\|?*]/g, "_");
}

function getProjectRoot(projectName) {
  const safeName = sanitizeProjectName(projectName);
  if (!safeName) {
    throw new Error("유효한 프로젝트 이름이 필요합니다");
  }
  return path.join(getProjectsDir(), safeName);
}

function getProjectConfigDir(projectName) {
  return path.join(getProjectRoot(projectName), "config");
}

function getWorkGuardLibraryDir() {
  if (app.isPackaged) {
    return path.join(getWorkspaceDir(), "work_guards");
  }
  return path.resolve(__dirname, "..", "..", "work_guards");
}

function getProjectConfigSurfaces(projectName) {
  const configDir = getProjectConfigDir(projectName);
  return {
    configDir,
    authorDirectivesPath: path.join(configDir, "author_directives.txt"),
    workGuardPath: path.join(configDir, "work_guard.yaml"),
  };
}

function listWorkGuardTemplates(genre = "") {
  const libraryRoot = path.resolve(getWorkGuardLibraryDir());
  const requestedGenre = String(genre || "").trim().toLowerCase().replace(/[^a-z0-9_]/g, "");
  const candidateRoots = [];
  if (requestedGenre) {
    candidateRoots.push(path.join(libraryRoot, requestedGenre));
  }
  candidateRoots.push(libraryRoot);

  const seen = new Set();
  const templates = [];
  for (const root of candidateRoots) {
    if (!fs.existsSync(root)) continue;
    const entries = fs.readdirSync(root, { withFileTypes: true })
      .filter((entry) => entry.isFile() && /\.(ya?ml)$/i.test(entry.name))
      .sort((left, right) => left.name.localeCompare(right.name));
    for (const entry of entries) {
      const fullPath = path.resolve(root, entry.name);
      if (seen.has(fullPath)) continue;
      seen.add(fullPath);
      const relativePath = path.relative(libraryRoot, fullPath);
      const scope = path.dirname(relativePath) === "." ? "common" : path.dirname(relativePath).replace(/\\/g, "/");
      templates.push({
        path: fullPath,
        relativePath: relativePath.replace(/\\/g, "/"),
        label: relativePath.replace(/\\/g, "/"),
        scope,
      });
    }
  }
  return templates;
}

function resolveWorkGuardTemplatePath(templatePath) {
  const libraryRoot = path.resolve(getWorkGuardLibraryDir());
  const resolved = path.resolve(String(templatePath || ""));
  const relative = path.relative(libraryRoot, resolved);
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative) || !fs.existsSync(resolved)) {
    throw new Error("유효한 work_guard template 경로가 아닙니다.");
  }
  if (!/\.(ya?ml)$/i.test(resolved)) {
    throw new Error("work_guard template는 YAML 파일이어야 합니다.");
  }
  return resolved;
}

function getDefaultAuthorDirectives() {
  return "# 절대 지시 사항을 입력하세요.\n";
}

ipcMain.handle(IPC_CHANNELS.project.list, async () => {
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
      })
      .sort();
    // main_a.py _select_project와 동일한 lexical sort를 사용해 1-based index drift를 막는다.
    return { ok: true, projects: entries };
  } catch (err) {
    return { ok: false, projects: [], message: err.message };
  }
});

ipcMain.handle(IPC_CHANNELS.project.create, async (_, name) => {
  if (!name || typeof name !== "string") {
    return { ok: false, message: "프로젝트 이름을 입력하세요" };
  }
  // 안전한 이름만 허용
  const safeName = sanitizeProjectName(name);
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

ipcMain.handle(IPC_CHANNELS.project.loadConfigSurfaces, async (_, projectName) => {
  try {
    const { authorDirectivesPath, workGuardPath } = getProjectConfigSurfaces(projectName);
    const authorDirectives = fs.existsSync(authorDirectivesPath)
      ? fs.readFileSync(authorDirectivesPath, "utf8")
      : getDefaultAuthorDirectives();
    const workGuardYaml = fs.existsSync(workGuardPath)
      ? fs.readFileSync(workGuardPath, "utf8")
      : "";
    return { ok: true, authorDirectives, workGuardYaml };
  } catch (err) {
    return { ok: false, message: err.message, authorDirectives: "", workGuardYaml: "" };
  }
});

ipcMain.handle(IPC_CHANNELS.project.saveConfigSurfaces, async (_, payload = {}) => {
  try {
    const project = typeof payload.project === "string" ? payload.project : "";
    const { configDir, authorDirectivesPath, workGuardPath } = getProjectConfigSurfaces(project);
    fs.mkdirSync(configDir, { recursive: true });

    const authorDirectives = typeof payload.authorDirectives === "string"
      ? payload.authorDirectives
      : getDefaultAuthorDirectives();
    const workGuardYaml = typeof payload.workGuardYaml === "string" ? payload.workGuardYaml : "";

    fs.writeFileSync(authorDirectivesPath, authorDirectives, "utf8");
    fs.writeFileSync(workGuardPath, workGuardYaml, "utf8");
    return { ok: true };
  } catch (err) {
    return { ok: false, message: err.message };
  }
});

ipcMain.handle(IPC_CHANNELS.project.listWorkGuardTemplates, async (_, payload = {}) => {
  try {
    const genre = typeof payload.genre === "string" ? payload.genre : "";
    return {
      ok: true,
      templates: listWorkGuardTemplates(genre),
      libraryRoot: getWorkGuardLibraryDir(),
    };
  } catch (err) {
    return { ok: false, templates: [], message: err.message };
  }
});

ipcMain.handle(IPC_CHANNELS.project.applyWorkGuardTemplate, async (_, payload = {}) => {
  try {
    const project = typeof payload.project === "string" ? payload.project : "";
    const templatePath = resolveWorkGuardTemplatePath(payload.templatePath);
    const { configDir, workGuardPath } = getProjectConfigSurfaces(project);
    fs.mkdirSync(configDir, { recursive: true });
    const workGuardYaml = fs.readFileSync(templatePath, "utf8");
    fs.writeFileSync(workGuardPath, workGuardYaml, "utf8");
    return {
      ok: true,
      workGuardYaml,
      templatePath,
      relativePath: path.relative(getWorkGuardLibraryDir(), templatePath).replace(/\\/g, "/"),
    };
  } catch (err) {
    return { ok: false, message: err.message, workGuardYaml: "" };
  }
});

// ─── 작업 폴더 열기 IPC ──────────────────────────────────────────────────────

ipcMain.handle(IPC_CHANNELS.workspace.openFolder, async () => {
  const dir = app.isPackaged ? getWorkspaceDir() : path.resolve(__dirname, "..", "..");
  fs.mkdirSync(dir, { recursive: true });
  const { shell } = electron;
  shell.openPath(dir);
  return { ok: true, path: dir };
});

// Dead-candidate compatibility surface. No active renderer consumer today.
ipcMain.handle(IPC_CHANNELS.workspace.getPath, async () => {
  const dir = app.isPackaged ? getWorkspaceDir() : path.resolve(__dirname, "..", "..");
  return { ok: true, path: dir };
});

// ─── 앱 수명주기 ─────────────────────────────────────────────────────────────

app.whenReady().then(() => {
  debugLog("app.whenReady");
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
    debugLog("app activate", { windowCount: BrowserWindow.getAllWindows().length });
    if (BrowserWindow.getAllWindows().length === 0) {
      didSwitchToMain = false;
      bootstrapWindows();
    }
  });
});

app.on("window-all-closed", () => {
  debugLog("window-all-closed");
  stopBackend();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  debugLog("before-quit");
  app.isQuitting = true;
  stopBackend();
});
