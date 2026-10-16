import { expect, test } from "@playwright/test";

/**
 * Modo apresentacao (V9): as mutacoes da §3.3 feitas pelo PROPRIO BFF, ao vivo,
 * escolhidas num seletor da tela. Diferente de `contract-mutation.spec.ts`,
 * nada aqui intercepta a rede: o cliente so pede (`X-SDUI-Mutacao`) e o
 * servidor muta a arvore que ele mesmo montou.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const CEP = "05311";

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/home?customer_zip_prefix=${CEP}`).catch(() => null);
  if (!res?.ok) throw new Error(`Backend indisponivel em ${API}: suba a pilha (ver journey.spec.ts).`);
});

test("modo apresentacao: o servidor muta a arvore e a tela obedece, sem recarregar", async ({ page }) => {
  await page.goto(`/?customer_zip_prefix=${CEP}&context=conscious_buyer`);
  await page.getByRole("button", { name: "SDUI" }).click();
  await page.evaluate(() => ((window as unknown as Record<string, unknown>).__contexto = "intacto"));

  await page.locator("main button:has(h3)").first().click();
  const dialog = page.locator("dialog[open]");
  const arvore = dialog.locator("p.font-mono.leading-relaxed").first();
  const relogio = dialog.getByText(/mesma página desde/);
  await expect(arvore).toHaveText(/^product_detail → impact_banner/);
  const carregadaEm = await relogio.innerText();
  const original = (await arvore.innerText()).split(" → ");

  const mutar = (valor: string) => dialog.getByLabel("Mutação do servidor").selectOption(valor);

  await mutar("reordenar");
  await expect(arvore).toHaveText([...original].reverse().join(" → "));

  await mutar("selo");
  await expect(dialog.locator("span", { hasText: "Selo injetado pelo servidor" }).first()).toBeVisible();

  await mutar("bloco_novo");
  await expect(dialog.getByRole("heading", { name: "Card que o detalhe nunca emitiu" })).toBeVisible();

  await mutar("bloco_desconhecido");
  await expect(dialog.getByText("não tem componente no")).toBeVisible();

  await mutar("sem_actions");
  await expect(arvore).toHaveText(original.join(" → "));
  await expect(dialog.getByRole("heading").first()).toBeVisible();

  await mutar("");
  await expect(dialog.getByText("mutação do servidor:")).toHaveCount(0);

  // Nada recarregou: o marcador do window e a hora de carga sobreviveram.
  expect(await page.evaluate(() => (window as unknown as Record<string, unknown>).__contexto)).toBe("intacto");
  await expect(relogio).toHaveText(carregadaEm);
});
