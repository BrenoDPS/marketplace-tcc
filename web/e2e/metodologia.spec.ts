import { expect, test } from "@playwright/test";

/**
 * Do selo a metodologia, dela ao painel da pesquisa e de volta (V7, V8): o
 * explicador "Como calculamos?" leva a tela que o servidor monta, e o "Voltar a
 * vitrine" devolve o mesmo CEP.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const CEP = "05311";

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/methodology`).catch(() => null);
  if (!res?.ok) throw new Error(`Backend indisponivel em ${API}: suba a pilha (ver journey.spec.ts).`);
});

test("do selo do detalhe para a metodologia e de volta a vitrine", async ({ page }) => {
  await page.goto(`/?customer_zip_prefix=${CEP}&context=conscious_buyer`);
  await page.locator("main button:has(h3)").first().click();
  const dialog = page.locator("dialog[open]");
  await dialog.getByText("Como calculamos?").click();
  await dialog.getByRole("link", { name: "Ver metodologia completa" }).click();

  await expect(page).toHaveURL(new RegExp(`/metodologia\\?customer_zip_prefix=${CEP}`));
  await expect(page.getByRole("heading", { name: "Como calculamos" })).toBeVisible();
  // Os numeros da pagina sao os do motor (o pytest confere a origem; aqui, que chegam a tela).
  await expect(page.getByText(/linha reta × 1,345/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Fontes" })).toBeVisible();

  // Da metodologia ao painel da pesquisa (V8): as tabelas do Cap. 5, montadas pelo servidor.
  await page.getByRole("button", { name: "Resultados da pesquisa" }).click();
  await expect(page).toHaveURL(new RegExp(`/pesquisa\\?customer_zip_prefix=${CEP}`));
  await expect(page.getByRole("heading", { name: "O que a pesquisa encontrou" })).toBeVisible();
  await expect(page.getByRole("row", { name: /^CO₂ evitado \d/ })).toContainText("254,2 kg CO₂e (9,8%)");
  await expect(page.getByRole("row", { name: /^Brasil/ })).toContainText("94,7%");

  await page.getByRole("button", { name: "Voltar à vitrine" }).click();
  await expect(page).toHaveURL(new RegExp(`/\\?customer_zip_prefix=${CEP}`));
  await expect(page.locator("main h3").first()).toBeVisible();
});
