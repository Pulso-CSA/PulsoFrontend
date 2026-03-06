/**
 * Abre o instalador NSIS gerado pelo electron-builder (Windows).
 * Uso: node scripts/open-installer.cjs
 * Ou após o build: npm run build:electron && node scripts/open-installer.cjs
 */
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");

const rootDir = path.join(__dirname, "..");
const pkgPath = path.join(rootDir, "package.json");
const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
const version = pkg.version || "0.0.0";
const productName = (pkg.build && pkg.build.productName) || "Pulso";
const installerName = `${productName} Setup ${version}.exe`;
const installerPath = path.join(rootDir, "dist-electron-build", installerName);

if (process.platform !== "win32") {
  console.log("open-installer: apenas Windows. Instalador em:", installerPath);
  process.exit(0);
}

if (!fs.existsSync(installerPath)) {
  console.error("Instalador não encontrado:", installerPath);
  console.error("Execute primeiro: npm run build:electron");
  process.exit(1);
}

console.log("Abrindo instalador:", installerPath);
// No Windows, usar "start" para abrir o .exe (como duplo clique) e exibir a janela do instalador
if (process.platform === "win32") {
  spawn("cmd", ["/c", "start", '""', installerPath], {
    stdio: "ignore",
    detached: true,
    cwd: rootDir,
    windowsHide: false,
  }).unref();
} else {
  const child = spawn(installerPath, [], {
    stdio: "ignore",
    detached: true,
    cwd: rootDir,
    shell: true,
  });
  child.unref();
}
