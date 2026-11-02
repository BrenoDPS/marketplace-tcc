import { writeFileSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * Acessibilidade automatizada (T9): axe-core nas seis telas da jornada, regras
 * WCAG 2.0/2.1 A e AA. Complementa o teste de teclado (teclado.spec.ts) com
 * contraste, rotulos e papeis ARIA. Falha so com violacao "critical"; as demais
 * ficam por tela e gravidade em test-results/acessibilidade.json, que vira
 * docs/resultados/acessibilidade.md.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const CEP = "05311";
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

type Achado = { tela: string; regra: string; gravidade: string; nos: number; ajuda: string; exemplo: string; detalhe: string };
const achados: Achado[] = [];

async function auditar(page: Page, tela: string, incluir?: string) {
  let axe = new AxeBuilder({ page }).withTags(TAGS);
  if (incluir) axe = axe.include(incluir);
  const { violations } = await axe.analyze();
  for (const v of violations) {
    achados.push({
      tela,
      regra: v.id,
      gravidade: v.impact ?? "?",
      nos: v.nodes.length,
      ajuda: v.help,
      exemplo: v.nodes[0]?.target.join(" ") ?? "",
      detalhe: v.nodes[0]?.failureSummary ?? "",
    });
  }
}

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/home?customer_zip_prefix=${CEP}`).catch(() => null);
  if (!res?.ok) throw new Error(`Backend indisponivel em ${API}: suba a pilha (ver journey.spec.ts).`);
});

test.afterAll(() => {
  writeFileSync("test-results/acessibilidade.json", JSON.stringify(achados, null, 2));
});

test("axe-core nas seis telas da jornada", async ({ page }) => {
  test.setTimeout(120_000);

  await page.goto("/");
  await expect(page.getByLabel("Prefixo do CEP")).toBeVisible();
  await auditar(page, "entrada");

  await page.goto(`/?customer_zip_prefix=${CEP}`);
  await expect(page.locator("main h3").first()).toBeVisible();
  await auditar(page, "home");

  await page.locator("main button:has(h3)").first().click();
  const dialog = page.locator("dialog[open]");
  await expect(dialog.getByRole("button", { name: "Ir para o carrinho" })).toBeVisible();
  await auditar(page, "detalhe (dialog)", "dialog[open]");

  await dialog.getByRole("button", { name: "Ir para o carrinho" }).click();
  await page.locator("dialog[open]").getByRole("button", { name: "Simular compra" }).click();
  await expect(page.getByRole("heading", { name: "Compra simulada" })).toBeVisible();
  await auditar(page, "checkout");

  await page.goto(`/metodologia?customer_zip_prefix=${CEP}`);
  await expect(page.getByRole("heading", { name: "Como calculamos" })).toBeVisible();
  await auditar(page, "metodologia");

  await page.goto(`/pesquisa?customer_zip_prefix=${CEP}`);
  await expect(page.getByRole("heading", { name: "O que a pesquisa encontrou" })).toBeVisible();
  await auditar(page, "pesquisa");

  // Trava so o pior nivel: as "serious" de hoje estao listadas no relatorio.
  expect(achados.filter((a) => a.gravidade === "critical")).toEqual([]);
});
