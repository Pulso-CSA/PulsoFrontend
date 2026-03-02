const { app, BrowserWindow, Menu, ipcMain, shell } = require("electron");
const path = require("path");
const fs = require("fs");

let mainWindow;

function setupAutoUpdater() {
  try {
    const { autoUpdater } = require("electron-updater");
    autoUpdater.autoDownload = false;
    autoUpdater.autoInstallOnAppQuit = true;

    // Repositório privado no GitHub: precisa de token para listar/baixar releases
    const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
    if (token) {
      autoUpdater.requestHeaders = {
        ...autoUpdater.requestHeaders,
        Authorization: `token ${token}`,
      };
    }

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
app.commandLine.appendSwitch("disable-logging");

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

  ipcMain.handle("check-for-updates", async () => {
    try {
      const { autoUpdater } = require("electron-updater");
      const result = await autoUpdater.checkForUpdates();
      const info = result?.updateInfo;
      const hasUpdate = !!info && !!info.version && info.version !== app.getVersion();

      return {
        ok: true,
        hasUpdate,
        version: info?.version ?? null,
      };
    } catch (e) {
      let message = e?.message || "Erro ao verificar atualizações";
      if (String(message).includes("404") || String(message).toLowerCase().includes("not found")) {
        message =
          "Não foi possível acessar as atualizações (404). " +
          "Se o repositório for privado, configure a variável de ambiente GH_TOKEN com um Personal Access Token do GitHub (escopo repo) e reinicie o aplicativo.";
      }
      mainWindow?.webContents?.send("update-error", message);
      return {
        ok: false,
        error: message,
      };
    }
  });

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

  ipcMain.handle("save-report", async (_, filePath, content) => {
    try {
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(filePath, content, "utf-8");
      return true;
    } catch (e) {
      console.error("save-report error:", e);
      return false;
    }
  });

  ipcMain.handle("open-uninstall", async () => {
    if (process.platform !== "win32") {
      shell.openExternal("https://support.microsoft.com/windows/uninstall-or-remove-apps-in-windows-10-4b55f974-2e13-4e4b-8b0a-15c0e1c1e5a5");
      return;
    }
    const exeDir = path.dirname(process.execPath);
    const uninstaller = path.join(exeDir, "Uninstall Pulso.exe");
    if (fs.existsSync(uninstaller)) {
      require("child_process").spawn(uninstaller, [], { detached: true, stdio: "ignore" }).unref();
      app.quit();
    } else {
      shell.openExternal("ms-settings:appsfeatures");
    }
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
