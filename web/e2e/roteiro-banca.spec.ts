import { expect, test, type Page } from "@playwright/test";

/**
 * Ensaio do roteiro da banca (`docs/roteiro-banca.md`): os MESMOS cliques, na
 * mesma ordem, conferindo os numeros que a fala cita. Se o ETL ou o codigo
 * mudarem a vitrine, isto falha antes da defesa — nao durante.
 *
 * Video de contingencia (plano B):
 *   GRAVAR=1 npx playwright test roteiro-banca
 * grava em test-results/ com pausas de leitura; copiar o .webm para docs/banca/.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const CEP = "05311";
const GRAVAR = process.env.GRAVAR === "1";

test.use({ viewport: { width: 1280, height: 800 }, video: GRAVAR ? "on" : "off" });
test.setTimeout(GRAVAR ? 6 * 60_000 : 90_000);

/** Pausa de leitura so na gravacao; no ensaio, nenhuma. */
const pausa = (page: Page, segundos: number) => (GRAVAR ? page.waitForTimeout(segundos * 1000) : Promise.resolve());

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/home?customer_zip_prefix=${CEP}`).catch(() => null);
  if (!res?.ok) throw new Error(`Backend indisponivel em ${API}: suba a pilha (ver docs/roteiro-banca.md).`);
});

test("roteiro da banca: CEP → vitrine regional → menor CO2 → detalhe → checkout → mutacao ao vivo", async ({ page }) => {
  await test.step("1. entrada pelo CEP e vitrine da regiao (objetivo c)", async () => {
    await page.goto("/");
    const zip = page.getByLabel("Prefixo do CEP");
    const entrar = page.getByRole("button", { name: "Entrar" });
    await expect(async () => {
      await zip.fill(CEP);
      await expect(entrar).toBeEnabled({ timeout: 500 });
    }).toPass({ timeout: 20_000 });
    await pausa(page, 2);
    await entrar.click();
    await expect(page.getByRole("heading", { name: "Em alta em SP: Alimentos" })).toBeVisible();
    await expect(page.getByText(/levam 1,3× mais desta categoria/)).toBeVisible();
    await pausa(page, 5);
  });

  await test.step("2. ordenar por menor CO2: o mais leve a 106 km vem antes (objetivo b)", async () => {
    await page.getByRole("navigation", { name: "Ordenar a vitrine" }).getByRole("button", { name: "Menor CO₂" }).click();
    await expect(page).toHaveURL(/sort=co2/);
    const cards = page.locator("main button:has(h3)");
    await expect(cards.nth(1)).toContainText("106 km");
    await expect(cards.nth(4)).toContainText("Sai de Atibaia");
    await pausa(page, 6);
  });

  await test.step("3. detalhe: selo explicado, mapa e comparador de origens (objetivos b e c)", async () => {
    await page.locator("main button:has(h3)").nth(4).click();
    const dialog = page.locator("dialog[open]");
    await expect(dialog.getByText(/^Entrega local \(~50 km/)).toBeVisible();
    await pausa(page, 2);
    await dialog.getByText("Como calculamos?").click();
    await expect(dialog.getByText(/479 g \(o produto pesa 150 g/)).toBeVisible();
    await pausa(page, 6);
    await dialog.getByRole("heading", { name: "De onde sai" }).scrollIntoViewIfNeeded();
    await expect(dialog.getByRole("img", { name: /escolhida: Atibaia, SP · 50 km/ })).toBeVisible();
    await pausa(page, 4);
    const comparador = dialog.locator("section").filter({ hasText: "De onde este produto pode sair" });
    await comparador.scrollIntoViewIfNeeded();
    await expect(comparador.getByText("Videira · SC")).toBeVisible();
    await expect(comparador.getByText(/5,5× a emissão da escolhida/)).toBeVisible();
    await expect(comparador.getByText("R$ 39,90")).toBeVisible();
    await pausa(page, 6);
  });

  await test.step("4. checkout em pagina: modalidade verde muda frete e CO2 juntos", async () => {
    await page.locator("dialog[open]").getByRole("button", { name: "Ir para o carrinho" }).click();
    await page.locator("dialog[open]").getByRole("button", { name: "Simular compra" }).click();
    await expect(page.getByRole("heading", { name: "Compra simulada" })).toBeVisible();
    await pausa(page, 3);
    await page.getByRole("navigation", { name: "Etapas da compra" }).getByRole("button", { name: /Entrega/ }).click();
    await page.getByRole("radio", { name: /Verde/ }).click();
    await expect(page.getByRole("radio", { name: /Verde/ })).toHaveAttribute("aria-checked", "true");
    await expect(page.getByRole("radio", { name: /Verde/ })).toContainText("4,30 g CO₂");
    await pausa(page, 6);
    await page.getByRole("button", { name: "← Voltar à vitrine" }).click();
    await expect(page.getByRole("heading", { name: "Compra simulada" })).toHaveCount(0);
  });

  await test.step("5. modo apresentacao: o servidor muta a arvore, sem recarregar (objetivos a e d)", async () => {
    await page.getByRole("button", { name: "SDUI" }).click();
    // Carrinho com item + SDUI ligado a 1280 px quebrava o cabecalho em 2 linhas
    // (achado na 1a gravacao deste roteiro).
    const cabecalho = await page.locator("header").boundingBox();
    expect(cabecalho?.height).toBeLessThanOrEqual(64);
    await pausa(page, 3);
    await page.locator("main button:has(h3)").nth(4).click();
    const dialog = page.locator("dialog[open]");
    const relogio = dialog.getByText(/mesma página desde/);
    const carregadaEm = await relogio.innerText();
    const arvore = dialog.locator("p.font-mono.leading-relaxed").first();
    const original = await arvore.innerText();
    await pausa(page, 4);
    await dialog.getByLabel("Mutação do servidor").selectOption("reordenar");
    await expect(arvore).toHaveText(original.split(" → ").reverse().join(" → "));
    await pausa(page, 5);
    await dialog.getByLabel("Mutação do servidor").selectOption("bloco_desconhecido");
    await expect(dialog.getByText("não tem componente no")).toBeVisible();
    await dialog.getByText("não tem componente no").scrollIntoViewIfNeeded();
    await pausa(page, 5);
    await expect(relogio).toContainText(carregadaEm);
    await dialog.getByLabel("Mutação do servidor").selectOption("");
    await pausa(page, 2);
  });
});
