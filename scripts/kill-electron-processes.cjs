/**
 * Encerra processos Pulso/Electron antes do build.
 * Evita erro "The process cannot access the file because it is being used by another process".
 */
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

if (process.platform !== "win32") {
  process.exit(0);
}

const processes = ["Pulso.exe", "electron.exe"];
let killed = false;

for (const proc of processes) {
  try {
    execSync(`taskkill /F /IM ${proc}`, { stdio: "pipe", windowsHide: true });
    console.log(`  Encerrado: ${proc}`);
    killed = true;
  } catch {
    // Processo não existe - ignorar
  }
}

if (killed) {
  console.log("  Aguardando 2s para liberar arquivos...");
  try {
    execSync("timeout /t 2 /nobreak >nul", { stdio: "pipe", windowsHide: true });
  } catch {
    // ignorar
  }
}

process.exit(0);
