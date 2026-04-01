import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { readFileSync } from "fs";
import { componentTagger } from "lovable-tagger";

const pkg = JSON.parse(readFileSync(path.join(__dirname, "package.json"), "utf-8"));

/** Onde o Vite encaminha /auth, /api, etc. em `npm run dev` (backend local, ex. uvicorn na porta configurada). */
const DEV_API_PROXY = (process.env.VITE_DEV_API_PROXY || "http://127.0.0.1:8000").replace(/\/$/, "");

const proxyToDevApi = {
  target: DEV_API_PROXY,
  changeOrigin: true,
};

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base: "./",
  define: {
    "import.meta.env.VITE_APP_VERSION": JSON.stringify(pkg.version || "0.0.0"),
  },
  server: {
    host: "::",
    port: 8080,
    // Atenção: true permite qualquer host (usar só em dev)
    allowedHosts: true,
    proxy: {
      "/health": proxyToDevApi,
      "/auth": proxyToDevApi,
      "/api": proxyToDevApi,
      "/subscription": proxyToDevApi,
      "/profiles": proxyToDevApi,
      "/inteligencia-dados": proxyToDevApi,
      "/insights": proxyToDevApi,
      "/finops": proxyToDevApi,
      "/infra": proxyToDevApi,
      "/deploy": proxyToDevApi,
      "/venv": proxyToDevApi,
      "/comprehension": proxyToDevApi,
      "/comprehension-js": proxyToDevApi,
      "/preview": proxyToDevApi,
      "/workflow": proxyToDevApi,
      "/chat-history": proxyToDevApi,
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Atenção: true permite qualquer host (usar só em ambiente controlado)
  preview: {
    allowedHosts: true,
  },
  build: {
    target: "es2020",
    minify: "esbuild",
    cssMinify: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          ui: [
            "@radix-ui/react-dialog",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-tabs",
          ],
          charts: ["recharts"],
        },
        chunkFileNames: "assets/[name]-[hash].js",
        entryFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
    chunkSizeWarningLimit: 600,
  },
}));
