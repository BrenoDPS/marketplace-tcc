import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  // `resolve.tsconfigPaths` e nativo do Vite e resolve o alias `@/` do
  // tsconfig — o plugin vite-tsconfig-paths seria uma dependencia a mais
  // fazendo o que o Vite ja faz.
  resolve: { tsconfigPaths: true },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
