const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  minimize: () => ipcRenderer.send("window-minimize"),
  maximize: () => ipcRenderer.send("window-maximize"),
  close: () => ipcRenderer.send("window-close"),
  isMaximized: () => ipcRenderer.invoke("window-is-maximized"),
  checkForUpdates: () => ipcRenderer.invoke("check-for-updates"),
  onUpdateAvailable: (cb) => {
    const fn = (_, info) => cb(info || {});
    ipcRenderer.on("update-available", fn);
    return () => ipcRenderer.removeListener("update-available", fn);
  },
  onUpdateDownloaded: (cb) => {
    ipcRenderer.on("update-downloaded", cb);
    return () => ipcRenderer.removeListener("update-downloaded", cb);
  },
  onUpdateProgress: (cb) => {
    const fn = (_, percent) => cb(percent ?? 0);
    ipcRenderer.on("update-progress", fn);
    return () => ipcRenderer.removeListener("update-progress", fn);
  },
  onUpdateError: (cb) => {
    const fn = (_, msg) => cb(msg || "Erro desconhecido");
    ipcRenderer.on("update-error", fn);
    return () => ipcRenderer.removeListener("update-error", fn);
  },
  downloadUpdate: () => ipcRenderer.invoke("update-download"),
  quitAndInstall: () => ipcRenderer.invoke("update-quit-and-install"),
  openUninstall: () => ipcRenderer.invoke("open-uninstall"),
  saveReport: (filePath, content) => ipcRenderer.invoke("save-report", filePath, content),
  getLocalApiConfig: () => ipcRenderer.invoke("pulso-local-get-config"),
  getLocalDiagnostics: (folderPath) =>
    ipcRenderer.invoke("pulso-local-get-diagnostics", { folderPath: folderPath ?? "" }),
  pickProjectFolder: () => ipcRenderer.invoke("pulso-local-pick-folder"),
  registerAllowedRoot: (rootPath) => ipcRenderer.invoke("pulso-local-register-root", rootPath),
});
