const fs = require("fs");
const path = require("path");
const toIco = require("to-ico");

const rootDir = path.join(__dirname, "..");
const publicPath = path.join(rootDir, "public", "App.png");
const rootPath = path.join(rootDir, "App.png");
const outputDir = path.join(rootDir, "build");
const outputPath = path.join(outputDir, "icon.ico");

// Fonte única: App.png na raiz (quando existir) → sincroniza public/ para o Vite/Electron servirem o mesmo ficheiro
let inputPath;
if (fs.existsSync(rootPath)) {
  fs.mkdirSync(path.join(rootDir, "public"), { recursive: true });
  fs.copyFileSync(rootPath, publicPath);
  inputPath = publicPath;
  console.log("App.png (raiz) → public/App.png");
  const installerPublicDir = path.join(rootDir, "installer", "public");
  const installerAppPng = path.join(installerPublicDir, "App.png");
  try {
    fs.mkdirSync(installerPublicDir, { recursive: true });
    fs.copyFileSync(rootPath, installerAppPng);
    console.log("App.png (raiz) → installer/public/App.png");
  } catch (e) {
    console.warn("Não foi possível copiar App.png para installer/public:", e?.message || e);
  }
} else if (fs.existsSync(publicPath)) {
  inputPath = publicPath;
  const installerPublicDir = path.join(rootDir, "installer", "public");
  const installerAppPng = path.join(installerPublicDir, "App.png");
  try {
    fs.mkdirSync(installerPublicDir, { recursive: true });
    fs.copyFileSync(publicPath, installerAppPng);
    console.log("public/App.png → installer/public/App.png");
  } catch (e) {
    console.warn("Não foi possível copiar para installer/public:", e?.message || e);
  }
} else {
  console.error("App.png não encontrado na raiz nem em public/.");
  process.exit(1);
}

fs.mkdirSync(outputDir, { recursive: true });

const pngBuffer = fs.readFileSync(inputPath);

async function writeIcons() {
  const buf = await toIco([pngBuffer], { resize: true, sizes: [16, 32, 48, 64, 128, 256] });
  fs.writeFileSync(outputPath, buf);
  const publicFavicon = path.join(rootDir, "public", "favicon.ico");
  fs.copyFileSync(outputPath, publicFavicon);
  const publicPulsoIco = path.join(rootDir, "public", "pulso-icon.ico");
  fs.copyFileSync(outputPath, publicPulsoIco);
  console.log("Ícone gerado:", outputPath);
  console.log("Favicon atualizado:", publicFavicon);
  console.log("public/pulso-icon.ico (Electron barra de tarefas):", publicPulsoIco);
}

writeIcons().catch((err) => {
  console.error("Erro ao gerar ícone:", err);
  process.exit(1);
});
