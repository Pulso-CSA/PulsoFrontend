import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  root: __dirname,
  base: "./",
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5174,
    // Atenção: true permite qualquer host (usar só em dev)
    allowedHosts: true,
  },
  preview: {
    // Atenção: true permite qualquer host (usar só em ambiente controlado)
    allowedHosts: true,
  },
});
