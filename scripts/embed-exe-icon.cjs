/**
 * Incorpora o ícone no Pulso.exe após o build (workaround para signAndEditExecutable: false).
 * Usa o pacote rcedit que tem binário próprio, evitando o winCodeSign 7z problemático.
 */
const path = require("path");
const fs = require("fs");

const rootDir = path.join(__dirname, "..");
const exePath = path.join(rootDir, "dist-electron-build", "win-unpacked", "Pulso.exe");
const iconPath = path.join(rootDir, "build", "icon.ico");

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
    const { rcedit } = await import("rcedit");
    await rcedit(exePath, {
      icon: iconPath,
      "version-string": {
        FileDescription: "Pulso - Dashboard Operacional Inteligente",
        ProductName: "Pulso",
        CompanyName: "Pulso Tech",
      },
    });
    console.log("Ícone incorporado em Pulso.exe com sucesso.");
  } catch (err) {
    console.error("embed-exe-icon:", err?.message || err);
    process.exit(1);
  }
}

main();
