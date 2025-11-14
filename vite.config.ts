import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: true,
    allowedHosts: ["pulsofrontend-production.up.railway.app"],
    port: process.env.PORT ? parseInt(process.env.PORT) : 8080,
  }
});

