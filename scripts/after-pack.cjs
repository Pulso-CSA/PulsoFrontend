/**
 * Hook afterPack: (1) copia pulso-csa-api/ (microsserviço CSA versionado no PulsoFrontend) → resources/PulsoAPI/api;
 * (2) no Windows, aplica rcedit no Pulso.exe antes do NSIS empacotar.
 */
const path = require("path");
const fs = require("fs");
const { rceditPulsoExe, getDefaultIconPath } = require("./rcedit-pulso-icon.cjs");

/**
 * @param {string} rootDir Raiz do PulsoFrontend (pasta com package.json)
 * @returns {string|null}
 */
function findCsaApiSource(rootDir) {
  const abs = path.resolve(rootDir, "pulso-csa-api");
  if (fs.existsSync(abs) && fs.existsSync(path.join(abs, "app", "pulso_csa_local", "main.py"))) {
    return abs;
  }
  return null;
}

/**
 * @param {string} src
 * @param {string} dest
 */
function copyPulsoApiFiltered(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  if (fs.existsSync(dest)) {
    fs.rmSync(dest, { recursive: true, force: true });
  }
  fs.cpSync(src, dest, {
    recursive: true,
    filter: (source) => {
      const base = path.basename(source);
      if (base === "__pycache__" || base === ".venv" || base === "venv" || base === ".git") {
        return false;
      }
      if (source.endsWith(".pyc")) return false;
      return true;
    },
  });
}

/** @param {{ electronPlatformName: string; appOutDir: string; packager: { appInfo: { productFilename: string } } }} context */
module.exports = async function afterPack(context) {
  const rootDir = path.join(__dirname, "..");
  const resourcesDir = path.join(context.appOutDir, "resources");
  const destApi = path.join(resourcesDir, "PulsoAPI", "api");

  const srcApi = findCsaApiSource(rootDir);
  if (!srcApi) {
    throw new Error(
      "after-pack: falta pulso-csa-api/ na raiz do PulsoFrontend (com app/pulso_csa_local/main.py). " +
        "O microsserviço CSA deve estar versionado neste repositório — não se puxa outro repo na build.",
    );
  }

  copyPulsoApiFiltered(srcApi, destApi);
  console.log(`after-pack: PulsoAPI/api copiado de ${srcApi} → ${destApi}`);

  if (context.electronPlatformName !== "win32") {
    return;
  }

  const iconPath = getDefaultIconPath(rootDir);
  if (!fs.existsSync(iconPath)) {
    throw new Error(
      `after-pack: falta ${iconPath}. Execute npm run build:icon antes do electron-builder.`,
    );
  }

  const productFilename = context.packager.appInfo.productFilename;
  const exePath = path.join(context.appOutDir, `${productFilename}.exe`);
  if (!fs.existsSync(exePath)) {
    throw new Error(`after-pack: executável não encontrado: ${exePath}`);
  }

  await rceditPulsoExe(exePath, iconPath);
  console.log(`after-pack: ícone incorporado em ${exePath}`);
};
