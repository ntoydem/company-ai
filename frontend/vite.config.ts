import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev server only (`make dev-frontend`). The browser talks to one origin (this server);
// API paths are forwarded to the backend, exactly as Caddy does in `make up` — so the
// app never needs an absolute API URL and the backend never needs CORS.
const apiTarget = process.env.VITE_DEV_API_TARGET ?? "http://backend:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": apiTarget,
      "/health": apiTarget,
      "/ask": apiTarget,
    },
  },
});
