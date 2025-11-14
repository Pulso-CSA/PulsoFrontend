import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    allowedHosts: ["pulsofrontend-production.up.railway.app"],
    port: process.env.PORT ? parseInt(process.env.PORT) : 8080,
  },
});
