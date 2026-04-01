/**
 * OPCIONAL — não usado na CI nem no release.
 * Copia uma pasta api externa (ex.: clone legado PulsoAPI/api) para pulso-csa-api/,
 * para migração manual ou alinhamento local. O produto assume pulso-csa-api versionado no Git.
 */
const fs = require("fs");
const path = require("path");

const rootDir = path.join(__dirname, "..");
const dest = path.join(rootDir, "pulso-csa-api");

const sources = [
  process.env.PULSO_SYNC_CSA_SOURCE?.trim(),
  path.join(rootDir, "PulsoAPI", "api"),
  path.join(rootDir, "..", "PulsoAPI", "api"),
].filter(Boolean);

function marker(p) {
  return path.join(p, "app", "pulso_csa_local", "main.py");
}

function findSrc() {
  for (const s of sources) {
    const abs = path.resolve(s);
    if (fs.existsSync(marker(abs))) return abs;
  }
  return null;
}

function copyFiltered(src, out) {
  if (fs.existsSync(out)) fs.rmSync(out, { recursive: true, force: true });
  fs.cpSync(src, out, {
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

const src = findSrc();
if (!src) {
  console.error(
    "sync-pulso-csa-api (opcional): fonte não encontrada.\n" +
      "  Defina PULSO_SYNC_CSA_SOURCE ou tenha PulsoAPI/api como irmão / em PulsoFrontend/PulsoAPI.",
  );
  process.exit(1);
}

copyFiltered(src, dest);
console.log(`sync-pulso-csa-api: copiado\n  de ${src}\n  → ${dest}`);
console.log("Revise as alterações e faça commit de pulso-csa-api/ no PulsoFrontend.");
