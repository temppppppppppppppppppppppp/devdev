const { contextBridge, ipcRenderer } = require("electron");
const { PRELOAD_METHOD_CHANNELS } = require("./desktop_control_plane_contract");

contextBridge.exposeInMainWorld("geuldobiDesktop", {
  // Splash → Main 전환
  getSplashConfig: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.getSplashConfig),
  notifyBackendReady: () => ipcRenderer.send(PRELOAD_METHOD_CHANNELS.live.notifyBackendReady),
  onAppReady: (handler) => ipcRenderer.on(PRELOAD_METHOD_CHANNELS.live.onAppReady, (_, payload) => handler(payload)),

  // Bridge API — HTTP 경유 (main process fetch)
  runKey: (key, subKey, inputs, approvalId = null) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.runKey, { key, subKey, inputs, approvalId }),
  stopRun: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.stopRun),
  // Dead-candidate compatibility surface. No active renderer consumer today.
  getStatus: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.deadCandidate.getStatus),
  getQualitySummary: (project, lookback = 5) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.getQualitySummary, { project, lookback }),
  getQualityDashboard: (project, lookback = 5) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.getQualityDashboard, { project, lookback }),
  getSafeOpsPreview: (project) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.getSafeOpsPreview, { project }),
  saveQualityReview: (project, epNum, operatorLabel, note = "") =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.saveQualityReview, { project, epNum, operatorLabel, note }),

  // Backend URL (renderer에서 직접 WebSocket 연결용)
  getBackendUrl: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.getBackendUrl),
  getCliContract: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.getCliContract),

  // 설정 영속화 (AppData JSON)
  saveSettings: (settings) => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.saveSettings, settings),
  loadSettings: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.loadSettings),

  // 재료 파일 관리 (bible / treatments)
  listMaterialFiles: (folder) => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.listMaterialFiles, folder),
  importMaterialFile: (folder) => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.importMaterialFile, folder),
  deleteMaterialFile: (folder, fileName) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.deleteMaterialFile, folder, fileName),

  // Mode B: 프롬프트 응답 (bridge HTTP 경유)
  resolvePrompt: (runId, promptId, value) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.resolvePrompt, { runId, promptId, value }),

  // 프로젝트 관리
  listProjects: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.listProjects),
  createProject: (name) => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.createProject, name),
  loadProjectConfigSurfaces: (project) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.loadProjectConfigSurfaces, project),
  saveProjectConfigSurfaces: (project, authorDirectives = "", workGuardYaml = "") =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.saveProjectConfigSurfaces, {
      project,
      authorDirectives,
      workGuardYaml,
    }),
  listWorkGuardTemplates: (genre = "") =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.listWorkGuardTemplates, { genre }),
  applyWorkGuardTemplate: (project, templatePath) =>
    ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.applyWorkGuardTemplate, { project, templatePath }),

  // 작업 폴더
  openWorkspaceFolder: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.live.openWorkspaceFolder),
  // Dead-candidate compatibility surface. No active renderer consumer today.
  getWorkspacePath: () => ipcRenderer.invoke(PRELOAD_METHOD_CHANNELS.deadCandidate.getWorkspacePath),
});
