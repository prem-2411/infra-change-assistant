import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the UI calls /api/*, which is proxied to the FastAPI server with the prefix removed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
});
