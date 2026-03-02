const { app, BrowserWindow, ipcMain, dialog, shell, Menu } = require("electron");
const path = require("path");
const fs = require("fs");
const ofs = require("original-fs");
const { execFileSync, spawn } = require("child_process");

let mainWindow;

function getAppSourceDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "pulso-app");
  }
  return path.join(__dirname, "../../dist-electron-build/win-unpacked");
}

function copyRecursiveSync(src, dest) {
  if (!ofs.existsSync(src)) return;
  const stat = ofs.statSync(src);
  if (!stat.isDirectory()) {
    const destDir = path.dirname(dest);
    ofs.mkdirSync(destDir, { recursive: true });
    ofs.copyFileSync(src, dest);
    return;
  }
  if (ofs.existsSync(dest)) {
    const destStat = ofs.statSync(dest);
    if (destStat.isFile()) ofs.unlinkSync(dest);
    else ofs.rmSync(dest, { recursive: true });
  }
  ofs.mkdirSync(dest, { recursive: true });
  const items = ofs.readdirSync(src);
  for (const item of items) {
    copyRecursiveSync(path.join(src, item), path.join(dest, item));
  }
}

function ensureDir(dirPath) {
  const norm = path.normalize(dirPath);
  if (fs.existsSync(norm)) {
    const stat = fs.statSync(norm);
    if (!stat.isDirectory()) throw new Error(`"${norm}" existe como arquivo. Escolha outro caminho.`);
    return;
  }
  try {
    fs.mkdirSync(norm, { recursive: true });
  } catch (e) {
    if (e.code === "ENOTDIR") {
      const parent = path.dirname(norm);
      if (fs.existsSync(parent)) {
        const pstat = fs.statSync(parent);
        if (!pstat.isDirectory()) throw new Error(`"${parent}" não é uma pasta. Escolha um caminho válido.`);
      }
    }
    throw e;
  }
}

function tryInstall(installPathNorm) {
  const sourceDir = path.normalize(getAppSourceDir());
  const destDir = path.join(installPathNorm, "Pulso");

  if (fs.existsSync(destDir)) {
    const destStat = fs.statSync(destDir);
    if (destStat.isFile()) {
      throw Object.assign(new Error("Já existe um arquivo chamado 'Pulso' neste local. Renomeie ou escolha outra pasta."), { code: "ENOTDIR" });
    }
    fs.rmSync(destDir, { recursive: true });
  }
  fs.mkdirSync(destDir, { recursive: true });
  copyRecursiveSync(sourceDir, destDir);
  return path.join(destDir, "Pulso.exe");
}

function getFallbackPaths() {
  const paths = [];
  try { paths.push(app.getPath("desktop")); } catch (_) {}
  try { paths.push(app.getPath("documents")); } catch (_) {}
  if (process.platform === "win32") {
    const localAppData = process.env.LOCALAPPDATA || path.join(app.getPath("home"), "AppData", "Local");
    paths.push(path.join(localAppData, "Pulso"));
  }
  try { paths.push(path.join(app.getPath("home"), "Pulso")); } catch (_) {}
  return paths;
}

ipcMain.handle("perform-install", async (_, installPath) => {
  const sourceDir = path.normalize(getAppSourceDir());
  const fallbackPaths = getFallbackPaths();

  if (!fs.existsSync(sourceDir)) {
    return { ok: false, error: "Arquivos do aplicativo não encontrados. Execute 'npm run build:electron' na raiz do projeto primeiro.", rawError: `sourceDir não existe: ${sourceDir}` };
  }
  const srcStat = fs.statSync(sourceDir);
  if (!srcStat.isDirectory()) {
    return { ok: false, error: "A pasta de origem do aplicativo está incorreta. Reconstrua o instalador com 'npm run installer:build'.", rawError: `sourceDir não é pasta: ${sourceDir}` };
  }

  const rawPath = String(installPath || "").trim().replace(/[/\\]+$/, "");
  const defaultPath = fallbackPaths[0] || path.join(app.getPath("home"), "Pulso");
  let installPathNorm = rawPath ? path.resolve(rawPath) : defaultPath;

  if (!fs.existsSync(installPathNorm)) {
    try {
      fs.mkdirSync(installPathNorm, { recursive: true });
    } catch (e) {
      installPathNorm = defaultPath;
    }
  }
  let installStat;
  try {
    installStat = fs.statSync(installPathNorm);
  } catch (e) {
    installPathNorm = defaultPath;
    installStat = fs.statSync(installPathNorm);
  }
  if (!installStat.isDirectory()) {
    installPathNorm = defaultPath;
  }

  let exePath;
  try {
    exePath = tryInstall(installPathNorm);
  } catch (err) {
    const tried = [installPathNorm];
    for (const fp of fallbackPaths) {
      if (tried.includes(fp)) continue;
      try {
        exePath = tryInstall(fp);
        break;
      } catch (e2) {
        console.error("perform-install (fallback falhou):", fp, e2?.code, e2?.message);
      }
    }
    if (!exePath) {
      const raw = err?.message || String(err);
      const code = err?.code || "";
      const rawError = `[${code}] ${raw}`;
      console.error("perform-install (tryInstall falhou):", rawError);
      return { ok: false, error: rawError, rawError, rawCode: code };
    }
  }

  try {
    const destDir = path.dirname(exePath);

    if (!fs.existsSync(exePath)) {
      return { ok: false, error: "Pulso.exe não foi encontrado após a cópia. O build do app principal pode estar incompleto. Execute 'npm run build:electron' na raiz do projeto e tente novamente." };
    }

    if (process.platform === "win32") {
      try {
        const desktop = app.getPath("desktop");
        const shortcutPath = path.join(desktop, "Pulso.lnk");
        const ps = [
          "$WshShell = New-Object -ComObject WScript.Shell",
          `$s = $WshShell.CreateShortcut('${shortcutPath.replace(/'/g, "''")}')`,
          `$s.TargetPath = '${exePath.replace(/'/g, "''")}'`,
          `$s.WorkingDirectory = '${destDir.replace(/'/g, "''")}'`,
          `$s.IconLocation = '${exePath.replace(/'/g, "''")},0'`,
          "$s.Save()",
        ].join("; ");
        execFileSync("powershell", ["-NoProfile", "-Command", ps], { windowsHide: true });
      } catch (e) {
        console.warn("Atalho na área de trabalho não criado:", e?.message);
      }
    }

    return { ok: true, installPath: destDir, exePath };
  } catch (err) {
    const raw = err?.message || String(err);
    const code = err?.code || "";
    const rawError = `[${code}] ${raw}`;
    console.error("perform-install (catch final):", rawError);
    return { ok: false, error: rawError, rawError, rawCode: code };
  }
});

ipcMain.handle("open-path", async (_, filePath) => {
  if (!filePath) return;
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".exe" && fs.existsSync(filePath)) {
    spawn(filePath, { cwd: path.dirname(filePath), detached: true, stdio: "ignore" }).unref();
  } else {
    await shell.openPath(filePath);
  }
});

ipcMain.handle("close-installer", () => {
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.close();
});

ipcMain.handle("get-default-install-path", () => {
  return app.getPath("desktop");
});

ipcMain.handle("select-install-dir", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openDirectory", "createDirectory"],
    title: "Escolher pasta de instalação",
  });
  if (!result.canceled && result.filePaths[0]) return result.filePaths[0];
  return null;
});

function createWindow() {
  Menu.setApplicationMenu(null);
  mainWindow = new BrowserWindow({
    width: 720,
    height: 560,
    minWidth: 600,
    minHeight: 480,
    frame: false,
    autoHideMenuBar: true,
    backgroundColor: "#0a0a0f",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  ipcMain.on("window-minimize", () => mainWindow?.minimize());
  ipcMain.on("window-maximize", () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize();
    else mainWindow?.maximize();
  });
  ipcMain.on("window-close", () => mainWindow?.close());
  ipcMain.handle("window-is-maximized", () => mainWindow?.isMaximized() ?? false);

  const distPath = path.join(__dirname, "../dist/index.html");
  const distExists = fs.existsSync(distPath);

  if (distExists) {
    mainWindow.loadFile(distPath);
  } else {
    mainWindow.loadURL("http://localhost:5174");
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (mainWindow === null) createWindow();
});
