/**
 * Motor local Pulso CSA: uvicorn app.pulso_csa_local.main em 127.0.0.1:porta dinâmica.
 * Dev: Python no PATH. Empacotado: resources/python (ver README em resources/python).
 */
const { spawn } = require("child_process");
const fs = require("fs");
const net = require("net");
const path = require("path");
const crypto = require("crypto");

let child = null;
let localSecret = "";
let localPort = 0;
let allowRootsPath = "";
let logFilePath = "";
/** Último código de falha ao arrancar (ex.: PULSO_API_ROOT_MISSING, HEALTH_TIMEOUT). */
let lastStartError = null;
/** Pasta PulsoAPI/api resolvida no último arranque bem-sucedido ou tentativa. */
let lastResolvedApiRoot = null;

function initPaths(userDataDir) {
  if (!userDataDir) return;
  allowRootsPath = path.join(userDataDir, "pulso-allowed-roots.json");
  logFilePath = path.join(userDataDir, "logs", "pulso-csa-local.log");
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => {
      const addr = s.address();
      const p = typeof addr === "object" && addr ? addr.port : 0;
      s.close(() => resolve(p));
    });
    s.on("error", reject);
  });
}

function resolveApiRoot(appRoot) {
  if (process.env.PULSO_API_ROOT && fs.existsSync(process.env.PULSO_API_ROOT)) {
    return process.env.PULSO_API_ROOT;
  }
  const sibling = path.resolve(appRoot, "..", "PulsoAPI", "api");
  if (fs.existsSync(sibling)) return sibling;
  return null;
}

function resolvePythonExecutable(appRoot, isPackaged, resourcesPath) {
  if (process.env.PULSO_LOCAL_PYTHON && fs.existsSync(process.env.PULSO_LOCAL_PYTHON)) {
    return process.env.PULSO_LOCAL_PYTHON;
  }
  if (isPackaged && resourcesPath) {
    const win = process.platform === "win32";
    const rel = win
      ? path.join("python", "python.exe")
      : path.join("python", "bin", "python3");
    const bundled = path.join(resourcesPath, rel);
    if (fs.existsSync(bundled)) return bundled;
  }
  return process.platform === "win32" ? "python" : "python3";
}

function readAllowRoots() {
  try {
    if (!allowRootsPath || !fs.existsSync(allowRootsPath)) return [];
    const raw = fs.readFileSync(allowRootsPath, "utf-8").trim();
    if (!raw) return [];
    const j = JSON.parse(raw);
    if (Array.isArray(j)) return [...new Set(j.map(String))];
    if (j && Array.isArray(j.roots)) return [...new Set(j.roots.map(String))];
  } catch {
    /* ignore */
  }
  return [];
}

function writeAllowRoots(roots) {
  if (!allowRootsPath) return;
  const dir = path.dirname(allowRootsPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(allowRootsPath, JSON.stringify(roots, null, 0), "utf-8");
}

function registerAllowedRoot(dirPath) {
  const p = (dirPath || "").trim();
  if (!p) return { ok: false };
  if (!allowRootsPath) return { ok: false, error: "PATHS_NOT_INIT" };
  const roots = readAllowRoots();
  if (!roots.includes(p)) {
    roots.push(p);
    writeAllowRoots(roots);
  }
  return { ok: true, roots };
}

async function pickProjectFolder(browserWindow) {
  const { dialog } = require("electron");
  const r = await dialog.showOpenDialog(browserWindow, {
    properties: ["openDirectory", "createDirectory"],
  });
  if (r.canceled || !r.filePaths || !r.filePaths[0]) return null;
  const chosen = r.filePaths[0];
  registerAllowedRoot(chosen);
  return chosen;
}

function stopLocalEngine() {
  if (child && !child.killed) {
    try {
      child.kill("SIGTERM");
    } catch {
      /* ignore */
    }
  }
  child = null;
  localPort = 0;
}

async function startLocalEngine(app, appRoot, browserWindow) {
  stopLocalEngine();
  lastStartError = null;
  const isPackaged = app.isPackaged;
  const resourcesPath = isPackaged ? process.resourcesPath : null;
  const userData = app.getPath("userData");
  initPaths(userData);

  const apiRoot = resolveApiRoot(appRoot);
  lastResolvedApiRoot = apiRoot;
  if (!apiRoot) {
    lastStartError = "PULSO_API_ROOT_MISSING";
    console.error("Pulso local: PulsoAPI/api não encontrado. Defina PULSO_API_ROOT ou coloque PulsoAPI ao lado de PulsoFrontend.");
    return { ok: false, error: lastStartError };
  }
  const logDir = path.dirname(logFilePath);
  if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });

  localSecret = crypto.randomBytes(24).toString("hex");
  const port = await getFreePort();
  if (!port) {
    lastStartError = "NO_PORT";
    return { ok: false, error: lastStartError };
  }

  const py = resolvePythonExecutable(appRoot, isPackaged, resourcesPath);
  const env = {
    ...process.env,
    PYTHONUNBUFFERED: "1",
    PULSO_CSA_LOCAL: "1",
    PULSO_LOCAL_SECRET: localSecret,
    PULSO_ALLOWED_ROOTS_FILE: allowRootsPath,
    PULSO_LOCAL_LOG_FILE: logFilePath,
  };
  if (!app.isPackaged) {
    env.PULSO_LOCAL_RELAX_ROOT_ALLOWLIST = "1";
  }
  const args = [
    "-m",
    "uvicorn",
    "app.pulso_csa_local.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    String(port),
    "--log-level",
    "info",
  ];

  child = spawn(py, args, {
    cwd: apiRoot,
    env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  child.stdout?.on("data", (d) => {
    const s = d.toString();
    if (s.trim()) console.log("[pulso-csa-local]", s.trim().slice(0, 500));
  });
  child.stderr?.on("data", (d) => {
    const s = d.toString();
    if (s.trim()) console.error("[pulso-csa-local]", s.trim().slice(0, 500));
  });
  child.on("exit", (code) => {
    console.warn("pulso-csa-local exit", code);
    child = null;
    localPort = 0;
    browserWindow?.webContents?.send("pulso-local-engine-stopped", code ?? 0);
  });

  localPort = port;

  const deadline = Date.now() + 120000;
  const http = require("http");
  while (Date.now() < deadline) {
    const ok = await new Promise((resolve) => {
      const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on("error", () => resolve(false));
      req.setTimeout(1500, () => {
        req.destroy();
        resolve(false);
      });
    });
    if (ok) break;
    await new Promise((r) => setTimeout(r, 400));
  }

  const finalCheck = await new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/health`, (res) => resolve(res.statusCode === 200));
    req.on("error", () => resolve(false));
    req.setTimeout(2000, () => {
      req.destroy();
      resolve(false);
    });
  });

  if (!finalCheck) {
    lastStartError = "HEALTH_TIMEOUT";
    stopLocalEngine();
    return { ok: false, error: lastStartError };
  }

  lastStartError = null;
  return {
    ok: true,
    baseUrl: `http://127.0.0.1:${port}`,
    token: localSecret,
    allowRootsPath,
  };
}

function getLocalConfig() {
  if (!localPort || !localSecret) return null;
  return {
    baseUrl: `http://127.0.0.1:${localPort}`,
    token: localSecret,
  };
}

/**
 * Estado para o painel de diagnóstico no frontend (Electron).
 * @param {{ isPackaged?: boolean, folderPath?: string }} opts
 */
function getLocalDiagnostics(opts = {}) {
  const roots = readAllowRoots();
  const fp = (opts.folderPath || "").trim();
  const norm = (s) => s.replace(/[/\\]+$/g, "").toLowerCase();
  const fpNorm = fp ? norm(fp) : "";
  const folderInAllowlist =
    fpNorm === ""
      ? null
      : roots.some((r) => {
          const rn = norm(String(r));
          return rn === fpNorm || fpNorm.startsWith(rn + "\\") || fpNorm.startsWith(rn + "/");
        });

  return {
    engineRunning: Boolean(child && !child.killed && localPort > 0),
    config: getLocalConfig(),
    lastStartError,
    apiRoot: lastResolvedApiRoot,
    allowRootsPath: allowRootsPath || null,
    allowedRootCount: roots.length,
    allowedRootsPreview: roots.slice(0, 12),
    logFilePath: logFilePath || null,
    folderInAllowlist,
    isPackaged: Boolean(opts.isPackaged),
    relaxAllowlistInDev: !opts.isPackaged,
  };
}

module.exports = {
  initPaths,
  startLocalEngine,
  stopLocalEngine,
  getLocalConfig,
  getLocalDiagnostics,
  pickProjectFolder,
  registerAllowedRoot,
};
