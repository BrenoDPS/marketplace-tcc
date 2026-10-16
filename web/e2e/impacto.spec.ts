import { expect, test } from "@playwright/test";

/**
 * "Seu impacto" (V6): a troca sugerida no checkout soma o CO2 evitado que o
 * SERVIDOR calculou para ela (`co2_saved_kg`), e o contador sobrevive a recarga.
 * O 3o card da vitrine regional de 05311 sai de Sao Jose do Rio Preto (~400 km)
 * e tem alternativa mais perto; se o ETL mudar, escolher outro card com troca.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const CEP = "05311";

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/home?customer_zip_prefix=${CEP}`).catch(() => null);
  if (!res?.ok) throw new Error(`Backend indisponivel em ${API}: suba a pilha (ver journey.spec.ts).`);
});

test("trocar pelo vendedor mais perto soma o CO2 evitado no checkout", async ({ page }) => {
  await page.goto(`/?customer_zip_prefix=${CEP}`);
  await page.locator("main button:has(h3)").nth(2).click();
  const dialog = page.locator("dialog[open]");
  await dialog.getByRole("button", { name: "Ir para o carrinho" }).click();
  await page.locator("dialog[open]").getByRole("button", { name: "Simular compra" }).click();
  await expect(page.getByRole("heading", { name: "Compra simulada" })).toBeVisible();

  const impacto = page.getByRole("status").filter({ hasText: "Seu impacto nesta sessão" });
  await expect(impacto).toHaveCount(0);

  // O valor que o servidor mandou na sugestao, ex.: "(41,4 g a menos)".
  const sugestao = page.locator("li").filter({ has: page.getByRole("button", { name: "Trocar" }) }).first();
  const evitado = (await sugestao.getByText(/a menos\)/).innerText()).match(/\((.+) a menos\)/)![1];
  await sugestao.getByRole("button", { name: "Trocar" }).click();

  await expect(impacto).toContainText(`${evitado} de CO₂ a menos em 1 troca`);
  await page.reload();
  await expect(page.getByRole("status").filter({ hasText: "Seu impacto nesta sessão" })).toContainText(`${evitado} de CO₂ a menos em 1 troca`);
});
