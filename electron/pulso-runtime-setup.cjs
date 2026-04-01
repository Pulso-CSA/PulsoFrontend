/**
 * Assistente de ambiente (Electron): Python embed (Windows), pip, Ollama, ficheiro user .env (OpenAI / flags).
 */
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");
const { spawn, spawnSync } = require("child_process");

const PYTHON_EMBED_WIN_URL =
  "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip";
const GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py";

/** Alinhado aos defaults em PulsoAPI (ollama_client) — nomes de modelo Ollama. */
const DEFAULT_OLLAMA_MODELS = [
  "qwen2.5-coder:3b-base-q4_K_M",
  "mistral:7b-instruct-q4_K_M",
];

function userEnvPath(userData) {
  return path.join(userData, "pulso-csa-user.env");
}

function runtimeConfigPath(userData) {
  return path.join(userData, "pulso-runtime-config.json");
}

function writeRuntimeConfig(userData, patch) {
  const p = runtimeConfigPath(userData);
  let cur = {};
  try {
    if (fs.existsSync(p)) cur = JSON.parse(fs.readFileSync(p, "utf-8"));
  } catch {
    /* ignore */
  }
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify({ ...cur, ...patch }, null, 0), "utf-8");
}

function readRuntimePythonExe(userData) {
  try {
    const p = runtimeConfigPath(userData);
    if (!fs.existsSync(p)) return null;
    const j = JSON.parse(fs.readFileSync(p, "utf-8"));
    const exe = (j.pythonExe || "").trim();
    if (exe && fs.existsSync(exe)) return exe;
  } catch {
    /* ignore */
  }
  return null;
}

function downloadToFile(urlStr, dest, onProgress) {
  return new Promise((resolve, reject) => {
    const u = new URL(urlStr);
    const lib = u.protocol === "https:" ? https : http;
    const file = fs.createWriteStream(dest);
    const req = lib.get(urlStr, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302 || res.statusCode === 307) {
        const next = res.headers.location;
        file.close();
        try {
          fs.unlinkSync(dest);
        } catch {
          /* ignore */
        }
        if (!next) {
          reject(new Error("Redirect sem Location"));
          return;
        }
        const abs = next.startsWith("http") ? next : new URL(next, urlStr).href;
        downloadToFile(abs, dest, onProgress).then(resolve).catch(reject);
        return;
      }
      if (res.statusCode !== 200) {
        file.close();
        try {
          fs.unlinkSync(dest);
        } catch {
          /* ignore */
        }
        reject(new Error(`Download HTTP ${res.statusCode}`));
        return;
      }
      const total = parseInt(res.headers["content-length"] || "0", 10);
      let done = 0;
      res.on("data", (chunk) => {
        done += chunk.length;
        if (total > 0 && onProgress) onProgress(done / total);
      });
      res.pipe(file);
      file.on("finish", () => file.close(() => resolve()));
    });
    req.on("error", (e) => {
      file.close();
      try {
        fs.unlinkSync(dest);
      } catch {
        /* ignore */
      }
      reject(e);
    });
  });
}

function expandZipWindows(zipPath, destDir) {
  fs.mkdirSync(destDir, { recursive: true });
  const z = zipPath.replace(/'/g, "''");
  const d = destDir.replace(/'/g, "''");
  const r = spawnSync(
    "powershell.exe",
    ["-NoProfile", "-Command", `Expand-Archive -LiteralPath '${z}' -DestinationPath '${d}' -Force`],
    { encoding: "utf-8", windowsHide: true },
  );
  if (r.status !== 0) {
    throw new Error((r.stderr || r.stdout || "Expand-Archive falhou").slice(0, 500));
  }
}

function fixEmbeddedPythonPth(embedRoot) {
  const files = fs.readdirSync(embedRoot);
  const pthName = files.find((f) => f.endsWith("._pth"));
  if (!pthName) throw new Error("Ficheiro ._pth do Python embed não encontrado.");
  const pthFile = path.join(embedRoot, pthName);
  let text = fs.readFileSync(pthFile, "utf-8");
  text = text.replace(/#\s*import\s+site/gi, "import site");
  if (!/^\s*import\s+site\s*$/m.test(text)) {
    text = `${text.trimEnd()}\nimport site\n`;
  }
  fs.writeFileSync(pthFile, text, "utf-8");
}

function runProcess(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const c = spawn(cmd, args, {
      windowsHide: true,
      ...opts,
    });
    let out = "";
    let err = "";
    c.stdout?.on("data", (d) => {
      out += d.toString();
    });
    c.stderr?.on("data", (d) => {
      err += d.toString();
    });
    c.on("error", reject);
    c.on("close", (code) => {
      if (code === 0) resolve({ stdout: out, stderr: err });
      else reject(new Error(`exit ${code}: ${(err || out).slice(0, 800)}`));
    });
  });
}

function detectOllamaCli() {
  if (process.platform === "win32") {
    const r = spawnSync("where.exe", ["ollama"], { encoding: "utf-8", windowsHide: true });
    return r.status === 0;
  }
  const r = spawnSync("which", ["ollama"], { encoding: "utf-8" });
  return r.status === 0;
}

function envFileHasNonEmptyKey(filePath, key) {
  if (!fs.existsSync(filePath)) return false;
  const text = fs.readFileSync(filePath, "utf-8");
  const re = new RegExp(`^\\s*${key}\\s*=\\s*(\\S+)`, "m");
  const m = text.match(re);
  return Boolean(m && m[1] && m[1].trim().length > 0);
}

function readEnvBool(filePath, key) {
  if (!fs.existsSync(filePath)) return false;
  const text = fs.readFileSync(filePath, "utf-8");
  const re = new RegExp(`^\\s*${key}\\s*=\\s*(.+)$`, "im");
  const m = text.match(re);
  if (!m) return false;
  const v = m[1].trim().replace(/^["']|["']$/g, "");
  return ["1", "true", "yes"].includes(v.toLowerCase());
}

function readEnvRawValue(filePath, key) {
  if (!fs.existsSync(filePath)) return "";
  const text = fs.readFileSync(filePath, "utf-8");
  const re = new RegExp(`^\\s*${key}\\s*=\\s*(.*)$`, "im");
  const m = text.match(re);
  if (!m) return "";
  return m[1].trim().replace(/^["']|["']$/g, "");
}

function mergeUserEnvFile(filePath, vars) {
  let lines = [];
  if (fs.existsSync(filePath)) {
    lines = fs.readFileSync(filePath, "utf-8").split(/\r?\n/);
  }
  const keysUpper = new Set(Object.keys(vars).map((k) => k.toUpperCase()));
  const kept = lines.filter((l) => {
    const m = l.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=/);
    if (!m) return true;
    return !keysUpper.has(m[1].toUpperCase());
  });
  const added = [];
  for (const [k, v] of Object.entries(vars)) {
    if (v === undefined || v === null) continue;
    const s = String(v).trim();
    if (s === "") continue;
    added.push(`${k}=${s}`);
  }
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, [...kept.filter((l) => l !== undefined), ...added].join("\n") + "\n", "utf-8");
}

function removeUserEnvKeys(filePath, keys) {
  if (!fs.existsSync(filePath)) return;
  const ku = new Set(keys.map((k) => k.toUpperCase()));
  const lines = fs.readFileSync(filePath, "utf-8").split(/\r?\n/);
  const kept = lines.filter((l) => {
    const m = l.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=/);
    if (!m) return true;
    return !ku.has(m[1].toUpperCase());
  });
  fs.writeFileSync(filePath, kept.join("\n") + (kept.length ? "\n" : ""), "utf-8");
}

function checkPythonImport(pythonExe, mod) {
  try {
    const r = spawnSync(pythonExe, ["-c", `import ${mod}`], {
      encoding: "utf-8",
      windowsHide: true,
      timeout: 120000,
    });
    return r.status === 0;
  } catch {
    return false;
  }
}

function getStatus({ userData, appRoot, isPackaged, resourcesPath, computeApiRoot }) {
  const apiRoot = computeApiRoot(appRoot, userData, isPackaged, resourcesPath);
  const reqFile = apiRoot ? path.join(apiRoot, "requirements.txt") : null;
  const py = readRuntimePythonExe(userData);
  const uenv = userEnvPath(userData);
  return {
    platform: process.platform,
    supportsEmbeddedPythonDownload: process.platform === "win32",
    apiRoot,
    requirementsFileExists: Boolean(reqFile && fs.existsSync(reqFile)),
    embeddedPythonPath: py,
    embeddedPythonOk: Boolean(py),
    pipUvicornOk: Boolean(py && apiRoot && checkPythonImport(py, "uvicorn")),
    ollamaCliAvailable: detectOllamaCli(),
    userEnvPath: uenv,
    userEnvExists: fs.existsSync(uenv),
    openAiKeyConfigured: envFileHasNonEmptyKey(uenv, "OPENAI_API_KEY"),
    useOllamaForced: readEnvBool(uenv, "USE_OLLAMA"),
    defaultOllamaModels: DEFAULT_OLLAMA_MODELS,
    ollamaHost: readEnvRawValue(uenv, "OLLAMA_HOST") || "http://127.0.0.1:11434",
  };
}

async function installEmbeddedPythonWindows(userData, onProgress) {
  const embedRoot = path.join(userData, "pulso-embedded-python", "3.11.9-amd64");
  const pythonExe = path.join(embedRoot, "python.exe");
  if (fs.existsSync(pythonExe)) {
    fixEmbeddedPythonPth(embedRoot);
    onProgress?.("done", "Python embutido já instalado.", 1);
    writeRuntimeConfig(userData, { pythonExe, embeddedPythonVersion: "3.11.9" });
    return { ok: true, pythonExe, alreadyHad: true };
  }

  const dlDir = path.join(userData, "pulso-embedded-python", "downloads");
  fs.mkdirSync(dlDir, { recursive: true });
  const zipPath = path.join(dlDir, "python-embed.zip");

  onProgress?.("download", "A transferir Python 3.11 (embed)…", 0);
  await downloadToFile(PYTHON_EMBED_WIN_URL, zipPath, (p) =>
    onProgress?.("download", "A transferir Python 3.11 (embed)…", p),
  );

  onProgress?.("extract", "A extrair…", 0);
  if (fs.existsSync(embedRoot)) fs.rmSync(embedRoot, { recursive: true, force: true });
  fs.mkdirSync(embedRoot, { recursive: true });
  expandZipWindows(zipPath, embedRoot);

  onProgress?.("configure", "A configurar pip (import site)…", 0.9);
  fixEmbeddedPythonPth(embedRoot);

  const getPipPath = path.join(embedRoot, "get-pip.py");
  onProgress?.("get_pip", "A transferir get-pip.py…", 0.92);
  await downloadToFile(GET_PIP_URL, getPipPath);

  onProgress?.("get_pip", "A instalar pip…", 0.95);
  await runProcess(pythonExe, [getPipPath], { cwd: embedRoot });

  writeRuntimeConfig(userData, { pythonExe, embeddedPythonVersion: "3.11.9" });
  onProgress?.("done", "Python e pip prontos.", 1);
  return { ok: true, pythonExe };
}

async function runPipInstallRequirements(
  { userData, appRoot, isPackaged, resourcesPath, computeApiRoot, onLine },
  pulsoLocal,
) {
  const apiRoot = computeApiRoot(appRoot, userData, isPackaged, resourcesPath);
  if (!apiRoot) return { ok: false, error: "PULSO_API_ROOT_MISSING" };
  const req = path.join(apiRoot, "requirements.txt");
  if (!fs.existsSync(req)) return { ok: false, error: "REQUIREMENTS_MISSING" };

  const pythonExe =
    readRuntimePythonExe(userData) ||
    pulsoLocal.resolvePythonExecutable(appRoot, isPackaged, resourcesPath, userData);
  if (!pythonExe) return { ok: false, error: "PYTHON_NOT_FOUND" };
  const looksLikePath = pythonExe.includes(path.sep) || /\.exe$/i.test(pythonExe);
  if (looksLikePath && !fs.existsSync(pythonExe)) {
    return { ok: false, error: "PYTHON_NOT_FOUND" };
  }

  onLine?.("pip install --upgrade pip\n");
  await new Promise((resolve, reject) => {
    const c = spawn(pythonExe, ["-m", "pip", "install", "--upgrade", "pip"], {
      cwd: apiRoot,
      windowsHide: true,
    });
    c.stdout?.on("data", (d) => onLine?.(d.toString()));
    c.stderr?.on("data", (d) => onLine?.(d.toString()));
    c.on("error", reject);
    c.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`pip upgrade exit ${code}`))));
  });

  onLine?.("pip install -r requirements.txt (pode demorar vários minutos)…\n");
  await new Promise((resolve, reject) => {
    const c = spawn(pythonExe, ["-m", "pip", "install", "-r", "requirements.txt"], {
      cwd: apiRoot,
      windowsHide: true,
    });
    c.stdout?.on("data", (d) => onLine?.(d.toString()));
    c.stderr?.on("data", (d) => onLine?.(d.toString()));
    c.on("error", reject);
    c.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`pip install exit ${code}`))));
  });

  return { ok: true };
}

async function pullOllamaModels(models, onLine) {
  if (!detectOllamaCli()) {
    return { ok: false, error: "OLLAMA_CLI_MISSING" };
  }
  const list = models && models.length ? models : DEFAULT_OLLAMA_MODELS;
  for (const m of list) {
    onLine?.(`ollama pull ${m}\n`);
    await new Promise((resolve, reject) => {
      const shell = process.platform === "win32";
      const c = spawn("ollama", ["pull", m], { shell, windowsHide: true });
      c.stdout?.on("data", (d) => onLine?.(d.toString()));
      c.stderr?.on("data", (d) => onLine?.(d.toString()));
      c.on("error", reject);
      c.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`ollama pull ${m} exit ${code}`))));
    });
  }
  return { ok: true };
}

function saveUserLlmSettings(userData, { openAiKey, useOllama, ollamaHost }) {
  const p = userEnvPath(userData);
  if (openAiKey !== undefined) {
    if (openAiKey && String(openAiKey).trim()) {
      mergeUserEnvFile(p, { OPENAI_API_KEY: String(openAiKey).trim() });
    } else {
      removeUserEnvKeys(p, ["OPENAI_API_KEY"]);
    }
  }
  if (useOllama !== undefined) {
    if (useOllama) mergeUserEnvFile(p, { USE_OLLAMA: "1" });
    else removeUserEnvKeys(p, ["USE_OLLAMA"]);
  }
  if (ollamaHost !== undefined && String(ollamaHost).trim()) {
    mergeUserEnvFile(p, { OLLAMA_HOST: String(ollamaHost).trim() });
  }
  return { ok: true, path: p };
}

module.exports = {
  getStatus,
  installEmbeddedPythonWindows,
  runPipInstallRequirements,
  pullOllamaModels,
  saveUserLlmSettings,
  userEnvPath,
  DEFAULT_OLLAMA_MODELS,
};
