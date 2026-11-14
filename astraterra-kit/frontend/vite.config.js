import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// When the backend exists, proxy /api to it. Until then the app reads /sample.json.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
