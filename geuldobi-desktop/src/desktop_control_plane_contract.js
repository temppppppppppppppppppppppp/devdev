"use strict";

const IPC_CHANNELS = Object.freeze({
  splash: Object.freeze({
    getConfig: "splash:get-config",
    backendReady: "splash:backend-ready",
  }),
  app: Object.freeze({
    ready: "app:ready",
  }),
  bridge: Object.freeze({
    run: "bridge:run",
    stop: "bridge:stop",
    status: "bridge:status",
    getUrl: "bridge:get-url",
    getCliContract: "bridge:get-cli-contract",
    getQualitySummary: "bridge:get-quality-summary",
    getQualityDashboard: "bridge:get-quality-dashboard",
    getSafeOpsPreview: "bridge:get-safe-ops-preview",
    saveQualityReview: "bridge:save-quality-review",
    resolvePrompt: "bridge:resolve-prompt",
    saveSettings: "bridge:save-settings",
    loadSettings: "bridge:load-settings",
  }),
  material: Object.freeze({
    listFiles: "material:list-files",
    importFile: "material:import-file",
    deleteFile: "material:delete-file",
  }),
  project: Object.freeze({
    list: "project:list",
    create: "project:create",
    loadConfigSurfaces: "project:load-config-surfaces",
    saveConfigSurfaces: "project:save-config-surfaces",
    listWorkGuardTemplates: "project:list-work-guard-templates",
    applyWorkGuardTemplate: "project:apply-work-guard-template",
  }),
  workspace: Object.freeze({
    openFolder: "workspace:open-folder",
    getPath: "workspace:get-path",
  }),
});

const PRELOAD_METHOD_CHANNELS = Object.freeze({
  live: Object.freeze({
    getSplashConfig: IPC_CHANNELS.splash.getConfig,
    notifyBackendReady: IPC_CHANNELS.splash.backendReady,
    onAppReady: IPC_CHANNELS.app.ready,
    runKey: IPC_CHANNELS.bridge.run,
    stopRun: IPC_CHANNELS.bridge.stop,
    getStatus: IPC_CHANNELS.bridge.status,
    getQualitySummary: IPC_CHANNELS.bridge.getQualitySummary,
    getQualityDashboard: IPC_CHANNELS.bridge.getQualityDashboard,
    getSafeOpsPreview: IPC_CHANNELS.bridge.getSafeOpsPreview,
    saveQualityReview: IPC_CHANNELS.bridge.saveQualityReview,
    getBackendUrl: IPC_CHANNELS.bridge.getUrl,
    getCliContract: IPC_CHANNELS.bridge.getCliContract,
    saveSettings: IPC_CHANNELS.bridge.saveSettings,
    loadSettings: IPC_CHANNELS.bridge.loadSettings,
    listMaterialFiles: IPC_CHANNELS.material.listFiles,
    importMaterialFile: IPC_CHANNELS.material.importFile,
    deleteMaterialFile: IPC_CHANNELS.material.deleteFile,
    resolvePrompt: IPC_CHANNELS.bridge.resolvePrompt,
    listProjects: IPC_CHANNELS.project.list,
    createProject: IPC_CHANNELS.project.create,
    loadProjectConfigSurfaces: IPC_CHANNELS.project.loadConfigSurfaces,
    saveProjectConfigSurfaces: IPC_CHANNELS.project.saveConfigSurfaces,
    listWorkGuardTemplates: IPC_CHANNELS.project.listWorkGuardTemplates,
    applyWorkGuardTemplate: IPC_CHANNELS.project.applyWorkGuardTemplate,
    openWorkspaceFolder: IPC_CHANNELS.workspace.openFolder,
  }),
  deadCandidate: Object.freeze({
    getWorkspacePath: IPC_CHANNELS.workspace.getPath,
  }),
});

const BRIDGE_MANAGED_ROUTES = Object.freeze({
  run: "/run",
  stop: "/stop",
  status: "/status",
  qualitySummary: "/quality/summary",
  qualityDashboard: "/quality/dashboard",
  safeOpsPreview: "/safe-ops/preview",
  qualityReview: "/quality/review",
});

function buildRunInputRoute(runId) {
  return `${BRIDGE_MANAGED_ROUTES.run}/${encodeURIComponent(runId)}/input`;
}

module.exports = {
  IPC_CHANNELS,
  PRELOAD_METHOD_CHANNELS,
  BRIDGE_MANAGED_ROUTES,
  buildRunInputRoute,
};
