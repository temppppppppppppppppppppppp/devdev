const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("geuldobiDesktop", {
  // Splash → Main 전환
  getSplashConfig: () => ipcRenderer.invoke("splash:get-config"),
  notifyBackendReady: () => ipcRenderer.send("splash:backend-ready"),
  onAppReady: (handler) => ipcRenderer.on("app:ready", (_, payload) => handler(payload)),

  // Bridge API — HTTP 경유 (main process fetch)
  runKey: (key, subKey, inputs) =>
    ipcRenderer.invoke("bridge:run", { key, subKey, inputs }),
  stopRun: () => ipcRenderer.invoke("bridge:stop"),
  getStatus: () => ipcRenderer.invoke("bridge:status"),

  // Backend URL (renderer에서 직접 WebSocket 연결용)
  getBackendUrl: () => ipcRenderer.invoke("bridge:get-url"),

  // 설정 영속화 (AppData JSON)
  saveSettings: (settings) => ipcRenderer.invoke("bridge:save-settings", settings),
  loadSettings: () => ipcRenderer.invoke("bridge:load-settings"),

  // 재료 파일 관리 (bible / treatments)
  listMaterialFiles: (folder) => ipcRenderer.invoke("material:list-files", folder),
  importMaterialFile: (folder) => ipcRenderer.invoke("material:import-file", folder),
  deleteMaterialFile: (folder, fileName) => ipcRenderer.invoke("material:delete-file", folder, fileName),

  // Mode B: 프롬프트 응답 (bridge HTTP 경유)
  resolvePrompt: (runId, promptId, value) =>
    ipcRenderer.invoke("bridge:resolve-prompt", { runId, promptId, value }),

  // 프로젝트 관리
  listProjects: () => ipcRenderer.invoke("project:list"),
  createProject: (name) => ipcRenderer.invoke("project:create", name),

  // 작업 폴더
  openWorkspaceFolder: () => ipcRenderer.invoke("workspace:open-folder"),
  getWorkspacePath: () => ipcRenderer.invoke("workspace:get-path"),
});
