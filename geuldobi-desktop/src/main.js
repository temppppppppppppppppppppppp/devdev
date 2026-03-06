const electron = require("electron");
const app = electron.app;
const BrowserWindow = electron.BrowserWindow;
const ipcMain = electron.ipcMain;
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
const SPLASH_FALLBACK_MS = 3000;
const STATUS_BASE_URL = "http://127.0.0.1:8300";
const SPIKE_AUTOCLOSE_MS = Number(process.env.SPIKE_AUTOCLOSE_MS || "0");

let mainWindow = null;
let splashWindow = null;
let didSwitchToMain = false;
let fallbackTimer = null;
let firstRun = false;

function getLocalAppDataRoot() {
  if (process.platform === "win32" && process.env.LOCALAPPDATA) {
    return process.env.LOCALAPPDATA;
  }
  return path.join(os.homedir(), "AppData", "Local");
}

function ensureFirstRunFlag() {
  const appDir = path.join(getLocalAppDataRoot(), "Geuldobi");
  const markerFile = path.join(appDir, ".first_run");

  fs.mkdirSync(appDir, { recursive: true });
  if (!fs.existsSync(markerFile)) {
    fs.writeFileSync(markerFile, new Date().toISOString(), "utf8");
    return true;
  }
  return false;
}

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
    console.log("SPIKE-4: splash window shown");
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
    console.log(`SPIKE-4: switched to main window (${reason})`);
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

app.whenReady().then(() => {
  bootstrapWindows();

  if (Number.isFinite(SPIKE_AUTOCLOSE_MS) && SPIKE_AUTOCLOSE_MS > 0) {
    setTimeout(() => {
      console.log(`SPIKE-4: auto-close after ${SPIKE_AUTOCLOSE_MS}ms`);
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
  if (process.platform !== "darwin") {
    app.quit();
  }
});
