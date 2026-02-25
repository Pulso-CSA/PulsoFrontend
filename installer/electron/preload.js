const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("pulsoInstaller", {
  selectInstallDir: () => ipcRenderer.invoke("select-install-dir"),
  getDefaultInstallPath: () => ipcRenderer.invoke("get-default-install-path"),
  close: () => ipcRenderer.invoke("close-installer"),
  performInstall: (installPath) => ipcRenderer.invoke("perform-install", installPath),
  openPath: (filePath) => ipcRenderer.invoke("open-path", filePath),
});

contextBridge.exposeInMainWorld("electronAPI", {
  minimize: () => ipcRenderer.send("window-minimize"),
  maximize: () => ipcRenderer.send("window-maximize"),
  close: () => ipcRenderer.send("window-close"),
  isMaximized: () => ipcRenderer.invoke("window-is-maximized"),
});
