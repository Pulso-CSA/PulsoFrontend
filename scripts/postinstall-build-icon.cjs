/**
 * Gera build/icon.ico após npm install quando devDependencies (to-ico) existem.
 * Ignora silenciosamente em installs só de produção para não quebrar o CI.
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const root = path.join(__dirname, "..");
const toIcoPkg = path.join(root, "node_modules", "to-ico", "package.json");

if (!fs.existsSync(toIcoPkg)) {
  process.exit(0);
}

try {
  execFileSync(process.execPath, [path.join(__dirname, "build-icon.cjs")], {
    cwd: root,
    stdio: "inherit",
  });
} catch (e) {
  console.warn("postinstall-build-icon:", e?.message || e);
  process.exit(1);
}
