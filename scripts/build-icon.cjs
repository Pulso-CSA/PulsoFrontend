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
} else if (fs.existsSync(publicPath)) {
  inputPath = publicPath;
} else {
  console.error("App.png não encontrado na raiz nem em public/.");
  process.exit(1);
}

fs.mkdirSync(outputDir, { recursive: true });

const pngBuffer = fs.readFileSync(inputPath);

toIco([pngBuffer], { resize: true, sizes: [16, 32, 48, 64, 128, 256] })
  .then((buf) => {
    fs.writeFileSync(outputPath, buf);
    const publicFavicon = path.join(rootDir, "public", "favicon.ico");
    fs.copyFileSync(outputPath, publicFavicon);
    console.log("Ícone gerado:", outputPath);
    console.log("Favicon atualizado:", publicFavicon);
  })
  .catch((err) => {
    console.error("Erro ao gerar ícone:", err);
    process.exit(1);
  });
