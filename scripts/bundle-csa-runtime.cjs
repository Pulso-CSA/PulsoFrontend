/**
 * Windows (build do instalador Pulso):
 * 1) Python 3.11 embeddable oficial + get-pip + pip install -r pulso-csa-api/requirements.txt
 * 2) Node.js win-x64 portátil (node.exe, npm.cmd, npx) para workflows CSA (npm install / npm run dev / npm run build)
 *
 * Saída: build/bundled-runtime/win/python e build/bundled-runtime/win/node
 * O hook after-pack copia para resources/ do .exe.
 *
 * Env:
 *   PULSO_SKIP_CSA_RUNTIME_BUNDLE=1 — não gera bundle (build rápido; after-pack não exige artefactos)
 *   PULSO_FORCE_REBUNDLE=1 — refazer pip/Node mesmo se build/bundled-runtime/win/.complete existir
 */
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");
const { execFileSync, spawnSync } = require("child_process");

const ROOT = path.join(__dirname, "..");
const OUT_WIN = path.join(ROOT, "build", "bundled-runtime", "win");
const PY_DIR = path.join(OUT_WIN, "python");
const NODE_DIR = path.join(OUT_WIN, "node");

const PYTHON_VERSION = "3.11.9";
const PYTHON_ZIP = `python-${PYTHON_VERSION}-embed-amd64.zip`;
const PYTHON_URL = `https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_ZIP}`;

const NODE_VERSION = "20.18.3";
const NODE_ZIP = `node-v${NODE_VERSION}-win-x64.zip`;
const NODE_URL = `https://nodejs.org/dist/v${NODE_VERSION}/${NODE_ZIP}`;

const GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py";

function download(url, destFile) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(destFile);
    const lib = url.startsWith("https") ? https : http;
    const req = lib.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        download(res.headers.location, destFile).then(resolve).catch(reject);
        return;
      }
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode} ao obter ${url}`));
        return;
      }
      res.pipe(file);
      file.on("finish", () => file.close(resolve));
    });
    req.on("error", (e) => {
      try {
        fs.unlinkSync(destFile);
      } catch {
        /* ignore */
      }
      reject(e);
    });
  });
}

function expandZip(zipPath, destDir) {
  fs.mkdirSync(destDir, { recursive: true });
  const z = zipPath.replace(/'/g, "''");
  const d = destDir.replace(/'/g, "''");
  execFileSync(
    "powershell.exe",
    ["-NoProfile", "-NonInteractive", "-Command", `Expand-Archive -LiteralPath '${z}' -DestinationPath '${d}' -Force`],
    { stdio: "inherit", cwd: ROOT },
  );
}

function fixPythonPth() {
  const entries = fs.readdirSync(PY_DIR);
  const pth = entries.find((f) => f.endsWith("._pth"));
  if (!pth) {
    console.warn("bundle-csa-runtime: ficheiro ._pth não encontrado — pip pode falhar");
    return;
  }
  const p = path.join(PY_DIR, pth);
  let txt = fs.readFileSync(p, "utf-8");
  if (txt.includes("#import site")) {
    txt = txt.replace("#import site", "import site");
  } else if (!txt.includes("import site")) {
    txt = txt.trimEnd() + "\r\nimport site\r\n";
  }
  fs.writeFileSync(p, txt, "utf-8");
}

function flattenNodeExtract() {
  const entries = fs.readdirSync(NODE_DIR);
  if (entries.length === 1 && fs.statSync(path.join(NODE_DIR, entries[0])).isDirectory()) {
    const inner = path.join(NODE_DIR, entries[0]);
    const tmp = path.join(OUT_WIN, "_node_flat");
    fs.renameSync(inner, tmp);
    fs.rmSync(NODE_DIR, { recursive: true, force: true });
    fs.renameSync(tmp, NODE_DIR);
  }
}

function main() {
  if (process.env.PULSO_SKIP_CSA_RUNTIME_BUNDLE === "1") {
    console.log("bundle-csa-runtime: ignorado (PULSO_SKIP_CSA_RUNTIME_BUNDLE=1)");
    process.exit(0);
  }

  if (process.platform !== "win32") {
    console.log("bundle-csa-runtime: só Windows — ignorado nesta plataforma.");
    process.exit(0);
  }

  const completeMarker = path.join(OUT_WIN, ".complete");
  const nodeExeCheck = path.join(NODE_DIR, "node.exe");
  const pyExeCheck = path.join(PY_DIR, "python.exe");
  if (
    process.env.PULSO_FORCE_REBUNDLE !== "1" &&
    fs.existsSync(completeMarker) &&
    fs.existsSync(pyExeCheck) &&
    fs.existsSync(nodeExeCheck)
  ) {
    console.log("bundle-csa-runtime: a reutilizar artefactos em", OUT_WIN, "(PULSO_FORCE_REBUNDLE=1 para forçar)");
    process.exit(0);
  }

  const requirements = path.join(ROOT, "pulso-csa-api", "requirements.txt");
  if (!fs.existsSync(requirements)) {
    console.error("bundle-csa-runtime: falta pulso-csa-api/requirements.txt");
    process.exit(1);
  }

  fs.mkdirSync(OUT_WIN, { recursive: true });
  const tmpDir = path.join(OUT_WIN, "_downloads");
  fs.mkdirSync(tmpDir, { recursive: true });

  const zipPy = path.join(tmpDir, PYTHON_ZIP);
  const zipNode = path.join(tmpDir, NODE_ZIP);
  const getPip = path.join(tmpDir, "get-pip.py");

  console.log("bundle-csa-runtime: a transferir Python embeddable…");
  fs.rmSync(PY_DIR, { recursive: true, force: true });

  (async () => {
    await download(PYTHON_URL, zipPy);
    expandZip(zipPy, PY_DIR);
    fixPythonPth();

    console.log("bundle-csa-runtime: a instalar pip…");
    await download(GET_PIP_URL, getPip);
    const rPip = spawnSync(path.join(PY_DIR, "python.exe"), [getPip], {
      cwd: PY_DIR,
      stdio: "inherit",
      env: { ...process.env, PYTHONPATH: "" },
    });
    if (rPip.status !== 0) {
      console.error("bundle-csa-runtime: get-pip falhou");
      process.exit(1);
    }

    console.log("bundle-csa-runtime: pip install -r requirements.txt (pode demorar vários minutos)…");
    const rReq = spawnSync(
      path.join(PY_DIR, "python.exe"),
      ["-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
      { cwd: ROOT, stdio: "inherit" },
    );
    if (rReq.status !== 0) process.exit(1);

    const rDeps = spawnSync(
      path.join(PY_DIR, "python.exe"),
      ["-m", "pip", "install", "-r", requirements],
      { cwd: ROOT, stdio: "inherit" },
    );
    if (rDeps.status !== 0) {
      console.error("bundle-csa-runtime: pip install -r requirements.txt falhou");
      process.exit(1);
    }

    console.log("bundle-csa-runtime: a transferir Node.js portátil…");
    fs.rmSync(NODE_DIR, { recursive: true, force: true });
    fs.mkdirSync(NODE_DIR, { recursive: true });
    await download(NODE_URL, zipNode);
    expandZip(zipNode, NODE_DIR);
    flattenNodeExtract();

    if (!fs.existsSync(path.join(NODE_DIR, "node.exe"))) {
      console.error("bundle-csa-runtime: node.exe não encontrado após extrair Node");
      process.exit(1);
    }

    fs.writeFileSync(completeMarker, new Date().toISOString(), "utf-8");
    console.log("bundle-csa-runtime: concluído →", OUT_WIN);
    try {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    } catch {
      /* ignore */
    }
    process.exit(0);
  })().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}

main();
