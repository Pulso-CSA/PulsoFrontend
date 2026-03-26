const { app, BrowserWindow, Menu, ipcMain, shell, nativeImage } = require("electron");
const path = require("path");
const fs = require("fs");

/** Windows: obrigatório para o ícone correto na barra de tarefas / atalhos (evita logo genérico do Electron). */
if (process.platform === "win32") {
  app.setAppUserModelId("com.pulso.app");
}

let mainWindow;

/** Caminhos candidatos ao ícone (Windows: preferir .ico — PNG na barra de tarefas costuma falhar). */
function resolveWindowIconPaths() {
  const appRoot = path.join(__dirname, "..");
  const candidates = [];
  if (process.platform === "win32" && app.isPackaged) {
    candidates.push(path.join(process.resourcesPath, "pulso-icon.ico"));
    candidates.push(path.join(path.dirname(process.execPath), "resources", "pulso-icon.ico"));
  }
  candidates.push(path.join(appRoot, "build", "icon.ico"));
  if (!app.isPackaged) {
    candidates.push(path.join(appRoot, "public", "favicon.ico"));
    candidates.push(path.join(appRoot, "public", "App.png"));
  }
  if (app.isPackaged) {
    candidates.push(path.join(appRoot, "public", "App.png"));
    candidates.push(path.join(appRoot, "public", "favicon.ico"));
  }
  const seen = new Set();
  const out = [];
  for (const p of candidates) {
    if (!p || seen.has(p)) continue;
    seen.add(p);
    out.push(p);
  }
  return out;
}

/** nativeImage para BrowserWindow (obrigatório no Windows para o ícone da janela/overlay). */
function resolveWindowIcon() {
  for (const p of resolveWindowIconPaths()) {
    try {
      if (!fs.existsSync(p)) continue;
      const img = nativeImage.createFromPath(p);
      if (!img.isEmpty()) return img;
    } catch {
      /* próximo */
    }
  }
  return undefined;
}

/** Token opcional: útil para repo privado ou limites da API; público não exige. */
function applyGithubTokenToAutoUpdater() {
  try {
    const { autoUpdater } = require("electron-updater");
    const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
    if (token) {
      autoUpdater.requestHeaders = {
        ...autoUpdater.requestHeaders,
        Authorization: `token ${token}`,
      };
    }
  } catch (_) {
    /* electron-updater indisponível */
  }
}

/** Mensagem quando a API do GitHub não devolve feed de release (404, etc.). */
function formatUpdateAccessHint() {
  return (
    "Não foi possível obter atualizações no GitHub (resposta 404 ou recurso ausente). " +
    "Repositório público não exige token; pode ser rede instável, limite de requisições da API ou release sem os artefatos corretos — tente novamente mais tarde. " +
    "Somente se o repositório for privado: configure GH_TOKEN ou GITHUB_TOKEN (PAT com escopo repo) e reinicie o aplicativo."
  );
}

function setupAutoUpdater() {
  try {
    const { autoUpdater } = require("electron-updater");
    autoUpdater.autoDownload = false;
    autoUpdater.autoInstallOnAppQuit = true;

    applyGithubTokenToAutoUpdater();

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
      let message = err?.message || "Erro desconhecido";
      if (String(message).includes("404") || String(message).toLowerCase().includes("not found")) {
        message = formatUpdateAccessHint();
      } else if (message.length > 280) {
        message = message.slice(0, 260).trim() + "...";
      }
      mainWindow?.webContents?.send("update-error", message);
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
    icon: resolveWindowIcon(),
    show: false,
  });

  // Links / window.open com _blank não abrem outra janela Electron (ícone por defeito);
  // abrem no navegador por defeito — mesmo comportamento esperado para URLs externas.
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const u = new URL(url);
      if (u.protocol === "http:" || u.protocol === "https:") {
        shell.openExternal(url);
      }
    } catch {
      /* URL inválida — não criar janela */
    }
    return { action: "deny" };
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
      applyGithubTokenToAutoUpdater();
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
        message = formatUpdateAccessHint();
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
      applyGithubTokenToAutoUpdater();
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

  mainWindow.once("ready-to-show", () => {
    const icon = resolveWindowIcon();
    if (icon) mainWindow.setIcon(icon);
    mainWindow.show();
  });
  mainWindow.on("closed", () => { mainWindow = null; });
}

const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    createWindow();
    setupAutoUpdater();
  });
}
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
app.on("activate", () => {
  if (mainWindow === null) createWindow();
});
