import { defineConfig } from "@playwright/test";

/**
 * E2E do Dossiê V3 (Onda 0 Task 16).
 *
 * Usa `PLAYWRIGHT_BASE_URL` (sem credenciais fixas no repositório);
 * usuário e fixture vêm do setup de teste, nunca de produção.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
  },
});
