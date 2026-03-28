/**
 * Incorpora o ícone em win-unpacked/Pulso.exe (uso manual ou CI legado).
 * O build normal aplica o ícone em after-pack.cjs, antes do NSIS.
 */
const path = require("path");
const fs = require("fs");
const { rceditPulsoExe, getDefaultIconPath } = require("./rcedit-pulso-icon.cjs");

const rootDir = path.join(__dirname, "..");
const exePath = path.join(rootDir, "dist-electron-build", "win-unpacked", "Pulso.exe");
const iconPath = getDefaultIconPath(rootDir);

if (process.platform !== "win32") {
  console.log("embed-exe-icon: apenas Windows. Ignorando.");
  process.exit(0);
}

if (!fs.existsSync(exePath)) {
  console.warn("embed-exe-icon: Pulso.exe não encontrado em", exePath);
  process.exit(0);
}

if (!fs.existsSync(iconPath)) {
  console.warn("embed-exe-icon: icon.ico não encontrado. Execute npm run build:icon primeiro.");
  process.exit(1);
}

async function main() {
  try {
    await rceditPulsoExe(exePath, iconPath);
    console.log("Ícone incorporado em Pulso.exe com sucesso.");
  } catch (err) {
    console.error("embed-exe-icon:", err?.message || err);
    process.exit(1);
  }
}

main();
