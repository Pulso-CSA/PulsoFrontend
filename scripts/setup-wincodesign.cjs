/**
 * Workaround para erro "Cannot create symbolic link" no electron-builder no Windows.
 * Baixa o winCodeSign em formato ZIP (sem symlinks problemáticos) e extrai no cache.
 * Execute uma vez: node scripts/setup-wincodesign.cjs
 * Ref: https://github.com/electron-userland/electron-builder/issues/8149
 */
const fs = require("fs");
const path = require("path");
const https = require("https");
const { execSync } = require("child_process");

const CACHE_DIR = path.join(
  process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE || "", "AppData", "Local"),
  "electron-builder",
  "Cache",
  "winCodeSign",
  "winCodeSign-2.6.0"
);
const ZIP_URL = "https://github.com/electron-userland/electron-builder-binaries/archive/refs/tags/winCodeSign-2.6.0.zip";
const ZIP_PATH = path.join(__dirname, "../.cache-wincodesign.zip");

function download(url) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(ZIP_PATH);
    https.get(url, { redirect: "follow" }, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        return download(res.headers.location).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on("finish", () => {
        file.close();
        resolve();
      });
    }).on("error", (err) => {
      fs.unlink(ZIP_PATH, () => {});
      reject(err);
    });
  });
}

function main() {
  if (process.platform !== "win32") {
    console.log("Este script é apenas para Windows. Ignorando.");
    process.exit(0);
  }

  if (fs.existsSync(path.join(CACHE_DIR, "osslsigncode.exe"))) {
    console.log("winCodeSign já está configurado em:", CACHE_DIR);
    process.exit(0);
  }

  console.log("Configurando winCodeSign (workaround para symlink no Windows)...");
  fs.mkdirSync(path.dirname(CACHE_DIR), { recursive: true });

  download(ZIP_URL)
    .then(() => {
      try {
        execSync(`powershell -Command "Expand-Archive -Path '${ZIP_PATH}' -DestinationPath '${path.dirname(CACHE_DIR)}' -Force"`, {
          stdio: "inherit",
        });
        const extracted = path.join(path.dirname(CACHE_DIR), "electron-builder-binaries-winCodeSign-2.6.0", "winCodeSign");
        if (fs.existsSync(extracted)) {
          fs.cpSync(extracted, CACHE_DIR, { recursive: true });
          console.log("winCodeSign configurado em:", CACHE_DIR);
        } else {
          throw new Error("Estrutura do ZIP inesperada. Extraído em: " + path.dirname(CACHE_DIR));
        }
      } catch (e) {
        console.error("Erro ao extrair. Tente manualmente:");
        console.error("1. Baixe:", ZIP_URL);
        console.error("2. Extraia o conteúdo de winCodeSign para:", CACHE_DIR);
        process.exit(1);
      } finally {
        try {
          fs.unlinkSync(ZIP_PATH);
        } catch (_) {}
      }
    })
    .catch((err) => {
      console.error("Erro ao baixar:", err.message);
      console.error("Alternativa: execute o terminal como Administrador ou ative o Modo Desenvolvedor no Windows.");
      process.exit(1);
    });
}

main();
