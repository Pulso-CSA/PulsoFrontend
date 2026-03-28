/**
 * Incorpora ícone e metadados no .exe (workaround para signAndEditExecutable: false).
 * Usado pelo hook afterPack do electron-builder e pelo script embed-exe-icon.cjs.
 */
const path = require("path");

const VERSION_STRING = {
  FileDescription: "Pulso - Dashboard Operacional Inteligente",
  ProductName: "Pulso",
  CompanyName: "Pulso Tech",
};

/**
 * @param {string} exePath
 * @param {string} iconPath
 */
async function rceditPulsoExe(exePath, iconPath) {
  const { rcedit } = await import("rcedit");
  await rcedit(exePath, {
    icon: iconPath,
    "version-string": VERSION_STRING,
  });
}

function getDefaultIconPath(rootDir) {
  return path.join(rootDir, "build", "icon.ico");
}

module.exports = { rceditPulsoExe, getDefaultIconPath, VERSION_STRING };
