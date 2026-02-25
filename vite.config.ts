import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { readFileSync } from "fs";
import { componentTagger } from "lovable-tagger";

const pkg = JSON.parse(readFileSync(path.join(__dirname, "package.json"), "utf-8"));

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base: "./",
  define: {
    "import.meta.env.VITE_APP_VERSION": JSON.stringify(pkg.version || "0.0.0"),
  },
  server: {
    host: "::",
    port: 8080,
    proxy: {
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/auth": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/subscription": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/profiles": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/inteligencia-dados": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/finops": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/infra": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/deploy": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/venv": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/comprehension": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/workflow": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/chat-history": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
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
