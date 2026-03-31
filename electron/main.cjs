const { app, BrowserWindow, Menu, ipcMain, shell, nativeImage } = require("electron");
const path = require("path");
const fs = require("fs");
const pulsoLocal = require("./pulso-local-engine.cjs");

/** Windows: obrigatório para o ícone correto na barra de tarefas / atalhos (evita logo genérico do Electron). */
if (process.platform === "win32") {
  app.setAppUserModelId("com.pulso.app");
}

let mainWindow;

function registerPulsoLocalIpcOnce() {
  if (registerPulsoLocalIpcOnce.done) return;
  registerPulsoLocalIpcOnce.done = true;
  ipcMain.handle("pulso-local-get-config", () => pulsoLocal.getLocalConfig());
  ipcMain.handle("pulso-local-pick-folder", async () => {
    const w = mainWindow && !mainWindow.isDestroyed() ? mainWindow : null;
    return pulsoLocal.pickProjectFolder(w);
  });
  ipcMain.handle("pulso-local-register-root", (_, rootPath) => pulsoLocal.registerAllowedRoot(rootPath));
}
registerPulsoLocalIpcOnce.done = false;

/** Caminhos candidatos ao ícone (Windows: .ico com vários tamanhos; PNG na barra costuma falhar). */
function resolveWindowIconPaths() {
  const appRoot = path.join(__dirname, "..");
  const candidates = [];
  if (process.platform === "win32") {
    if (app.isPackaged) {
      // extraResources (package.json): fora do asar — mais fiável para barra de tarefas / overlay
      candidates.push(path.join(process.resourcesPath, "pulso-icon.ico"));
      candidates.push(path.join(path.dirname(process.execPath), "resources", "pulso-icon.ico"));
      try {
        candidates.push(path.join(app.getAppPath(), "public", "pulso-icon.ico"));
      } catch {
        /* ignora */
      }
    }
    // Dev e empacotado: cópia em public/ (mesmo conteúdo que build/icon.ico)
    candidates.push(path.join(appRoot, "public", "pulso-icon.ico"));
  }
  candidates.push(path.join(appRoot, "build", "icon.ico"));
  if (!app.isPackaged) {
    candidates.push(path.join(appRoot, "public", "favicon.ico"));
    candidates.push(path.join(appRoot, "public", "App.png"));
  }
  if (app.isPackaged) {
    candidates.push(path.join(appRoot, "public", "favicon.ico"));
    candidates.push(path.join(appRoot, "public", "App.png"));
  }
  const seen = new Set();
  const out = [];
  for (const p of candidates) {
    if (!p || seen.has(p)) continue;
    seen.add(p);
    try {
      out.push(path.resolve(p));
    } catch {
      out.push(p);
    }
  }
  return out;
}

/**
 * Windows: createFromPath/caminho em string para BrowserWindow falham frequentemente na barra de tarefas
 * (ficheiros dentro do .asar ou limitações do shell). readFileSync + createFromBuffer é o padrão fiável.
 */
function loadNativeImageFromFile(filePath) {
  try {
    if (!filePath || !fs.existsSync(filePath)) return undefined;
    const buf = fs.readFileSync(filePath);
    if (!buf?.length) return undefined;
    const img = nativeImage.createFromBuffer(buf);
    return img.isEmpty() ? undefined : img;
  } catch {
    return undefined;
  }
}

/** nativeImage (buffer) — preferir no Windows para barra de tarefas / janela sem moldura. */
function resolveWindowIconNativeImage() {
  for (const p of resolveWindowIconPaths()) {
    const img = loadNativeImageFromFile(p);
    if (img) return img;
  }
  return undefined;
}

/** Fallback createFromPath (macOS/Linux ou último recurso). */
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

function resolveWindowIconPathString() {
  for (const p of resolveWindowIconPaths()) {
    try {
      if (fs.existsSync(p)) return p;
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
  /** No Windows usar só NativeImage vinda de buffer — evita logo do Electron na barra de tarefas. */
  const windowIcon =
    process.platform === "win32"
      ? resolveWindowIconNativeImage() ?? resolveWindowIcon()
      : resolveWindowIconPathString() ?? resolveWindowIcon();

  if (process.platform === "win32" && app.isPackaged && !windowIcon) {
    console.warn(
      "Pulso: ícone da janela não carregado (verifique extraResources pulso-icon.ico em resources/)."
    );
  }

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
    ...(windowIcon ? { icon: windowIcon } : {}),
    show: false,
  });

  if (process.platform === "win32" && windowIcon && !windowIcon.isEmpty()) {
    const applyTaskbarIcon = () => {
      try {
        mainWindow.setIcon(windowIcon);
      } catch {
        /* ignora */
      }
    };
    applyTaskbarIcon();
    mainWindow.once("ready-to-show", applyTaskbarIcon);
    mainWindow.once("show", applyTaskbarIcon);
  }

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
    const p = resolveWindowIconPathString();
    const img = resolveWindowIcon();
    if (process.platform === "win32") {
      if (p) mainWindow.setIcon(p);
      else if (img) mainWindow.setIcon(img);
    } else if (img) {
      mainWindow.setIcon(img);
    }
    mainWindow.show();
  });
  mainWindow.on("closed", () => { mainWindow = null; });

  registerPulsoLocalIpcOnce();
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

  app.whenReady().then(async () => {
    pulsoLocal.initPaths(app.getPath("userData"));
    const appRoot = path.join(__dirname, "..");
    const started = await pulsoLocal.startLocalEngine(app, appRoot, null);
    if (!started.ok) {
      console.warn("pulso-csa-local não iniciou:", started.error);
    }

    createWindow();
    setupAutoUpdater();
  });

  app.on("before-quit", () => {
    pulsoLocal.stopLocalEngine();
  });
}
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
app.on("activate", () => {
  if (mainWindow === null) createWindow();
});
