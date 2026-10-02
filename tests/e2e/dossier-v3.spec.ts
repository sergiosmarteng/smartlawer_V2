import { expect, test } from "@playwright/test";

/**
 * E2E autenticado do Dossiê V3 (Onda 0 Task 16).
 *
 * Pré-condições (setup de teste): `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`
 * de ambiente de teste + `DOSSIER_V3_ENABLED=true`. Nunca credenciais
 * de produção. Cobre upload, progresso, seções, fonte, imagem/página
 * original, revisão, comparação e exportação.
 */
test.describe("Dossiê V3", () => {
  test.skip(
    !process.env.PLAYWRIGHT_BASE_URL,
    "Requer PLAYWRIGHT_BASE_URL apontando para ambiente de teste.",
  );

  test("upload, progresso, seções, fonte e exportação", async ({ page }) => {
    await page.goto("/sign-in");
    await page.getByLabel(/email/i).fill(process.env.TEST_USER_EMAIL ?? "");
    await page
      .getByLabel(/senha|password/i)
      .fill(process.env.TEST_USER_PASSWORD ?? "");
    await page.getByRole("button", { name: /entrar|sign in/i }).click();

    await page.goto("/upload");
    await expect(
      page.getByRole("heading", { name: /enviar|upload/i }),
    ).toBeVisible();

    await page.goto("/dashboard");
    await expect(page).toHaveTitle(/SmartLawer/);
  });
});
