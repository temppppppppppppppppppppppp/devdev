const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("geuldobiDesktop", {
  getSplashConfig: () => ipcRenderer.invoke("splash:get-config"),
  notifyBackendReady: () => ipcRenderer.send("splash:backend-ready"),
  onAppReady: (handler) => ipcRenderer.on("app:ready", (_, payload) => handler(payload))
});
