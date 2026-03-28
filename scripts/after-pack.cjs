/**
 * Hook afterPack: aplica rcedit (pacote npm) no Pulso.exe ANTES do NSIS empacotar.
 * signAndEditExecutable: true obriga extrair winCodeSign.7z (symlinks falham sem admin).
 */
const path = require("path");
const fs = require("fs");
const { rceditPulsoExe, getDefaultIconPath } = require("./rcedit-pulso-icon.cjs");

/** @param {{ electronPlatformName: string; appOutDir: string; packager: { appInfo: { productFilename: string } } }} context */
module.exports = async function afterPack(context) {
  if (context.electronPlatformName !== "win32") {
    return;
  }

  const rootDir = path.join(__dirname, "..");
  const iconPath = getDefaultIconPath(rootDir);
  if (!fs.existsSync(iconPath)) {
    throw new Error(
      `after-pack: falta ${iconPath}. Execute npm run build:icon antes do electron-builder.`
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
