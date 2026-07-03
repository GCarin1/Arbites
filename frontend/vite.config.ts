import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em dev a SPA roda no Vite (5173) e fala com o backend em 8347;
// em produção local o FastAPI serve o build de dist/ (contrato http-api).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8347",
    },
  },
});
