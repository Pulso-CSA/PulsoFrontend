const { app, BrowserWindow, Menu, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");

let mainWindow;

function setupAutoUpdater() {
  try {
    const { autoUpdater } = require("electron-updater");
    autoUpdater.autoDownload = false;
    autoUpdater.autoInstallOnAppQuit = true;

    autoUpdater.on("update-available", (info) => {
      mainWindow?.webContents?.send("update-available", { version: info?.version });
    });

    autoUpdater.on("update-downloaded", () => {
      mainWindow?.webContents?.send("update-downloaded");
    });

    autoUpdater.on("download-progress", (progress) => {
      mainWindow?.webContents?.send("update-progress", progress.percent);
    });

    autoUpdater.on("error", (err) => {
      mainWindow?.webContents?.send("update-error", err?.message || "Erro desconhecido");
    });

    if (app.isPackaged) {
      autoUpdater.checkForUpdates().catch(() => {});
    }
  } catch (_) {
    // electron-updater não disponível em dev
  }
}

app.commandLine.appendSwitch("disable-gpu-sandbox");
app.commandLine.appendSwitch("no-sandbox");

function createWindow() {
  Menu.setApplicationMenu(null);
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#0a0a0f",
    frame: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.cjs"),
    },
    icon: (() => {
      const base = app.isPackaged ? app.getAppPath() : path.join(__dirname, "..");
      const icoPath = path.join(base, "public", "favicon.ico");
      const pngPath = path.join(base, "public", "App.png");
      return (fs.existsSync(icoPath) ? icoPath : pngPath);
    })(),
    show: false,
  });

  ipcMain.on("window-minimize", () => mainWindow?.minimize());
  ipcMain.on("window-maximize", () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize();
    else mainWindow?.maximize();
  });
  ipcMain.on("window-close", () => mainWindow?.close());
  ipcMain.handle("window-is-maximized", () => mainWindow?.isMaximized() ?? false);

  ipcMain.handle("update-download", async () => {
    try {
      const { autoUpdater } = require("electron-updater");
      await autoUpdater.downloadUpdate();
    } catch (e) {
      mainWindow?.webContents?.send("update-error", e?.message || "Erro ao baixar");
    }
  });

  ipcMain.handle("update-quit-and-install", () => {
    const { autoUpdater } = require("electron-updater");
    autoUpdater.quitAndInstall(false, true);
  });

  const isDev = !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL("http://localhost:8080");
  } else {
    const indexPath = path.join(app.getAppPath(), "dist", "index.html");
    mainWindow.loadFile(indexPath).catch((err) => {
      console.error("Erro ao carregar app:", err);
    });
  }

  mainWindow.once("ready-to-show", () => mainWindow.show());
  mainWindow.on("closed", () => { mainWindow = null; });
}

app.whenReady().then(() => {
  createWindow();
  setupAutoUpdater();
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (mainWindow === null) createWindow(); });
