/**
 * Motor local Pulso CSA: uvicorn app.pulso_csa_local.main em 127.0.0.1:porta dinâmica.
 * Código: sempre PulsoFrontend/pulso-csa-api (versionado neste repo) ou cópia em resources/ no instalador.
 * Overrides opcionais: PULSO_API_ROOT ou ficheiro manual em userData.
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
/** Pasta api resolvida (cwd do uvicorn). */
let lastResolvedApiRoot = null;
/** Últimas linhas stderr do subprocesso (diagnóstico). */
let lastEngineStderrTail = "";
/** Interpretador Python usado no último arranque. */
let lastResolvedPythonExe = null;

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

function isValidApiCwd(dir) {
  return dir && fs.existsSync(path.join(dir, "app", "pulso_csa_local", "main.py"));
}

/**
 * Resolve pasta api (cwd do uvicorn).
 * Ordem: PULSO_API_ROOT → ficheiro manual → pulso-csa-api/ na raiz do frontend → resources/PulsoAPI/api (empacotado).
 */
function resolveApiRoot(appRoot, userDataDir, isPackaged, resourcesPath) {
  const envRoot = (process.env.PULSO_API_ROOT || "").trim();
  if (envRoot && fs.existsSync(envRoot)) {
    return path.resolve(envRoot);
  }

  if (userDataDir) {
    try {
      const manualFile = path.join(userDataDir, "pulso-csa-pulsoapi-root.txt");
      if (fs.existsSync(manualFile)) {
        const raw = fs.readFileSync(manualFile, "utf-8");
        const line = raw
          .split(/\r?\n/)
          .map((l) => l.trim())
          .find((l) => l && !l.startsWith("#"));
        if (line) {
          const cleaned = line.replace(/^["']|["']$/g, "").trim();
          const resolved = path.resolve(cleaned);
          if (fs.existsSync(resolved)) return resolved;
        }
      }
    } catch {
      /* ignore */
    }
  }

  if (appRoot) {
    const embedded = path.join(appRoot, "pulso-csa-api");
    if (isValidApiCwd(embedded)) {
      return path.resolve(embedded);
    }
  }

  if (isPackaged && resourcesPath) {
    const bundled = path.join(resourcesPath, "PulsoAPI", "api");
    if (fs.existsSync(bundled) && fs.existsSync(path.join(bundled, "app"))) {
      return path.resolve(bundled);
    }
  }

  return null;
}

function readEmbeddedPythonExeFromConfig(userData) {
  if (!userData) return null;
  try {
    const cfgPath = path.join(userData, "pulso-runtime-config.json");
    if (!fs.existsSync(cfgPath)) return null;
    const j = JSON.parse(fs.readFileSync(cfgPath, "utf-8"));
    const exe = (j.pythonExe || "").trim();
    if (exe && fs.existsSync(exe)) return exe;
  } catch {
    /* ignore */
  }
  return null;
}

function resolvePythonExecutable(appRoot, isPackaged, resourcesPath, userData) {
  if (process.env.PULSO_LOCAL_PYTHON && fs.existsSync(process.env.PULSO_LOCAL_PYTHON)) {
    return process.env.PULSO_LOCAL_PYTHON;
  }
  /** Instalador: Python + pip já vêm em resources/python (bundle pré-build). */
  if (isPackaged && resourcesPath) {
    const win = process.platform === "win32";
    const rel = win
      ? path.join("python", "python.exe")
      : path.join("python", "bin", "python3");
    const bundled = path.join(resourcesPath, rel);
    if (fs.existsSync(bundled)) return bundled;
  }
  const fromSetup = readEmbeddedPythonExeFromConfig(userData);
  if (fromSetup) return fromSetup;
  return process.platform === "win32" ? "python" : "python3";
}

/** npm / node para workflows JS no CSA (preview, autocorrect, tests). */
function prependBundledRuntimePath(env, resourcesPath) {
  if (!resourcesPath) return;
  const win = process.platform === "win32";
  const parts = [];
  const pyRoot = path.join(resourcesPath, "python");
  const pyExe = win ? path.join(pyRoot, "python.exe") : path.join(pyRoot, "bin", "python3");
  if (fs.existsSync(pyExe)) {
    parts.push(pyRoot);
    const scripts = win ? path.join(pyRoot, "Scripts") : path.join(pyRoot, "bin");
    if (fs.existsSync(scripts)) parts.push(scripts);
  }
  const nodeRoot = path.join(resourcesPath, "node");
  const nodeOk = win ? fs.existsSync(path.join(nodeRoot, "node.exe")) : fs.existsSync(path.join(nodeRoot, "bin", "node"));
  if (nodeOk) {
    parts.push(win ? nodeRoot : path.join(nodeRoot, "bin"));
  }
  if (parts.length === 0) return;
  const prefix = parts.join(path.delimiter);
  env.PATH = `${prefix}${path.delimiter}${env.PATH || ""}`;
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

function appendEngineProcessLog(kind, chunk) {
  const s = typeof chunk === "string" ? chunk : chunk.toString();
  if (!s) return;
  if (kind === "stderr") {
    lastEngineStderrTail = (lastEngineStderrTail + s).slice(-8000);
  }
  if (logFilePath) {
    try {
      const line = `[${new Date().toISOString()}] [${kind}] ${s}`;
      fs.appendFileSync(logFilePath, line, "utf-8");
    } catch {
      /* ignore */
    }
  }
}

async function startLocalEngine(app, appRoot, browserWindow) {
  stopLocalEngine();
  lastStartError = null;
  lastEngineStderrTail = "";
  lastResolvedPythonExe = null;
  const isPackaged = app.isPackaged;
  const resourcesPath = isPackaged ? process.resourcesPath : null;
  const userData = app.getPath("userData");
  initPaths(userData);

  const apiRoot = resolveApiRoot(appRoot, userData, isPackaged, resourcesPath);
  lastResolvedApiRoot = apiRoot;
  if (!apiRoot) {
    lastStartError = "PULSO_API_ROOT_MISSING";
    console.error(
      "Pulso local: falta pulso-csa-api/ na raiz do projeto (ou cópia em resources no instalador). " +
        "Opcional: PULSO_API_ROOT ou pulso-csa-pulsoapi-root.txt em userData.",
    );
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

  const py = resolvePythonExecutable(appRoot, isPackaged, resourcesPath, userData);
  lastResolvedPythonExe = py;
  const env = {
    ...process.env,
    PYTHONUNBUFFERED: "1",
    /** Windows: evita UnicodeEncodeError (charmap) em print/log com emoji no stdout. */
    PYTHONIOENCODING: "utf-8",
    ...(process.platform === "win32" ? { PYTHONUTF8: "1" } : {}),
    PULSO_CSA_LOCAL: "1",
    /** Só 127.0.0.1: sem Mongo/.env igual à cloud, auth+plano não podem bloquear o CSA. */
    PULSO_LOCAL_DESKTOP_ENTITLEMENT_GRACE: "1",
    PULSO_LOCAL_SECRET: localSecret,
    PULSO_ALLOWED_ROOTS_FILE: allowRootsPath,
    PULSO_LOCAL_LOG_FILE: logFilePath,
  };
  /** Evita escrita de __pycache__ em resources (instalação pode ser só leitura). */
  if (isPackaged) {
    const pyc = path.join(userData, "pulso-csa-pycache");
    try {
      fs.mkdirSync(pyc, { recursive: true });
      env.PYTHONPYCACHEPREFIX = pyc;
    } catch {
      env.PYTHONDONTWRITEBYTECODE = "1";
    }
  }
  env.PYTHONPATH = [apiRoot, path.join(apiRoot, "app"), env.PYTHONPATH || ""].filter(Boolean).join(path.delimiter);
  if (isPackaged && resourcesPath) {
    prependBundledRuntimePath(env, resourcesPath);
  }
  const userEnvFile = path.join(userData, "pulso-csa-user.env");
  if (fs.existsSync(userEnvFile)) {
    env.PULSO_CSA_USER_ENV = userEnvFile;
  }
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

  appendEngineProcessLog("meta", `spawn ${py} ${args.join(" ")} cwd=${apiRoot}\n`);

  child = spawn(py, args, {
    cwd: apiRoot,
    env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  child.stdout?.on("data", (d) => {
    const s = d.toString();
    appendEngineProcessLog("stdout", s);
    if (s.trim()) console.log("[pulso-csa-local]", s.trim().slice(0, 500));
  });
  child.stderr?.on("data", (d) => {
    const s = d.toString();
    appendEngineProcessLog("stderr", s);
    if (s.trim()) console.error("[pulso-csa-local]", s.trim().slice(0, 500));
  });
  child.on("error", (err) => {
    appendEngineProcessLog("stderr", `spawn error: ${err && err.message ? err.message : String(err)}\n`);
    console.error("[pulso-csa-local] spawn error", err);
  });
  child.on("exit", (code) => {
    console.warn("pulso-csa-local exit", code);
    appendEngineProcessLog("meta", `exit code=${code}\n`);
    child = null;
    localPort = 0;
    browserWindow?.webContents?.send("pulso-local-engine-stopped", code ?? 0);
  });

  localPort = port;

  /** Primeiro arranque com deps pesadas (LangChain, etc.) pode exceder 2 min. */
  const healthWaitMs = isPackaged ? 600000 : 240000;
  const deadline = Date.now() + healthWaitMs;
  const http = require("http");
  while (Date.now() < deadline) {
    if (child === null) {
      lastStartError = "ENGINE_EXITED";
      break;
    }
    const ok = await new Promise((resolve) => {
      const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on("error", () => resolve(false));
      req.setTimeout(4000, () => {
        req.destroy();
        resolve(false);
      });
    });
    if (ok) break;
    await new Promise((r) => setTimeout(r, 500));
  }

  if (lastStartError === "ENGINE_EXITED") {
    stopLocalEngine();
    return { ok: false, error: lastStartError };
  }

  const finalCheck = await new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/health`, (res) => resolve(res.statusCode === 200));
    req.on("error", () => resolve(false));
    req.setTimeout(5000, () => {
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
 * @param {{ isPackaged?: boolean, folderPath?: string, appRoot?: string, userDataDir?: string, resourcesPath?: string|null }} opts
 */
function getLocalDiagnostics(opts = {}) {
  const ud = opts.userDataDir || null;
  if (ud && !allowRootsPath) {
    initPaths(ud);
  }

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

  const appRoot = (opts.appRoot || "").trim();
  const resourcesPath = opts.resourcesPath || null;
  const embeddedCsa = appRoot ? path.join(appRoot, "pulso-csa-api") : null;
  const bundledApi =
    opts.isPackaged && resourcesPath ? path.join(resourcesPath, "PulsoAPI", "api") : null;
  const manualPulsoapiFile = ud ? path.join(ud, "pulso-csa-pulsoapi-root.txt") : null;
  const envPulsoApiRoot = (process.env.PULSO_API_ROOT || "").trim() || null;
  const bundledPy = opts.isPackaged && resourcesPath ? path.join(resourcesPath, "python", "python.exe") : null;
  const bundledNodeDir = opts.isPackaged && resourcesPath ? path.join(resourcesPath, "node") : null;

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
    pulsoApiCandidates: [
      embeddedCsa ? { path: embeddedCsa, exists: isValidApiCwd(embeddedCsa) } : null,
      bundledApi ? { path: bundledApi, exists: fs.existsSync(bundledApi) } : null,
    ].filter(Boolean),
    manualPulsoapiFile,
    envPulsoApiRoot,
    frontendRoot: appRoot || null,
    bundledPythonPath: bundledPy,
    bundledPythonExists: Boolean(bundledPy && fs.existsSync(bundledPy)),
    bundledNodeDir,
    bundledNodeExists: Boolean(
      bundledNodeDir &&
        fs.existsSync(
          process.platform === "win32"
            ? path.join(bundledNodeDir, "node.exe")
            : path.join(bundledNodeDir, "bin", "node"),
        ),
    ),
    resolvedPythonExe: lastResolvedPythonExe || null,
    lastEngineStderrTail: lastEngineStderrTail.trim() ? lastEngineStderrTail.trim().slice(-6000) : null,
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
  computeApiRoot: resolveApiRoot,
  resolvePythonExecutable,
  readEmbeddedPythonExeFromConfig,
};
