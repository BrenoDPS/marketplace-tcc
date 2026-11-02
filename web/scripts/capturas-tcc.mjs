// Captura as telas da aplicação para figuras candidatas da monografia.
// Uso, com a pilha no ar (de web/): node scripts/capturas-tcc.mjs ../docs/tcc/figuras/candidatas
import path from "node:path";
import { chromium } from "playwright";

const BASE = "http://localhost:3000";
const OUT = process.argv[2];
const shot = (page, nome, opts = {}) => page.screenshot({ path: path.join(OUT, `${nome}.png`), ...opts });
// O modal tem altura maxima e corpo rolavel; para a figura, libera a altura e
// fotografa so o dialogo inteiro (precisa de viewport alta para caber).
const DESTRAVA =
  "dialog[open], dialog[open] > div, dialog[open] .overflow-y-auto " +
  "{ max-height: none !important; overflow: visible !important; }";
const shotModal = async (page, nome) => {
  const estilo = await page.addStyleTag({ content: DESTRAVA });
  await page.waitForTimeout(300);
  await page.locator("dialog[open]").screenshot({ path: path.join(OUT, `${nome}.png`) });
  await estilo.evaluate((el) => el.remove());
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(`${BASE}/`);
  await page.waitForLoadState("networkidle");
  await shot(page, "c01-entrada-cep");

  await page.goto(`${BASE}/?customer_zip_prefix=05311`);
  await page.getByText("Em alta em SP", { exact: true }).waitFor();
  await shot(page, "c02-home-regional-sp", { fullPage: true });

  await page.goto(`${BASE}/?customer_zip_prefix=60165`);
  await page.waitForLoadState("networkidle");
  await shot(page, "c03-home-regional-ce");

  await page.goto(`${BASE}/?customer_zip_prefix=69005`);
  await page.waitForLoadState("networkidle");
  await shot(page, "c04-home-sem-sinal-am");

  await page.goto(`${BASE}/?customer_zip_prefix=05311&context=conscious_buyer&sort=co2`);
  await page.waitForLoadState("networkidle");
  await shot(page, "c05-home-consciente-menor-co2", { fullPage: true });

  // Detalhe do 5º card da vitrine padrão por menor CO2 (Atibaia, roteiro da banca)
  await page.goto(`${BASE}/?customer_zip_prefix=05311&sort=co2`);
  await page.waitForLoadState("networkidle");
  await page.setViewportSize({ width: 1440, height: 2600 });
  await page.locator("main button:has(h3)").nth(4).click();
  const dialog = page.locator("dialog[open]");
  await dialog.getByText("Como calculamos?").click();
  await page.waitForTimeout(800);
  await shotModal(page, "c06-detalhe-selo-mapa-comparador");

  // Carrinho e checkout a 1440x900: o modal tem corpo rolavel (redesenho de 02/11)
  // e, na viewport de 2600 px, o checkout abria fora do recorte e a espera estourava.
  await page.setViewportSize({ width: 1440, height: 900 });
  // Checkout com sugestao de troca dentro do teto de 20% (T7): o item de Atibaia
  // (R$ 27,90) nao tem substituto ate R$ 33,48; o 3o card da vitrine padrao tem
  // (o mesmo do e2e/impacto.spec.ts). Carrinho limpo para a figura ter um item.
  await page.goto(`${BASE}/?customer_zip_prefix=05311`);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForLoadState("networkidle");
  await page.locator("main button:has(h3)").nth(2).click();
  await dialog.getByRole("button", { name: "Ir para o carrinho" }).click();
  await page.waitForTimeout(500);
  await shot(page, "c07-carrinho");
  await page.locator("dialog[open]").getByRole("button", { name: "Simular compra" }).click();
  await page.getByRole("heading", { name: "Compra simulada" }).waitFor();
  await page.waitForTimeout(800);
  await shot(page, "c08-checkout-completo", { fullPage: true });

  await page.goto(`${BASE}/metodologia`);
  await page.waitForLoadState("networkidle");
  await shot(page, "c09-metodologia", { fullPage: true });

  await page.goto(`${BASE}/pesquisa`);
  await page.waitForLoadState("networkidle");
  await shot(page, "c10-pesquisa", { fullPage: true });

  // Modo SDUI no detalhe, com mutação do servidor
  await page.goto(`${BASE}/?customer_zip_prefix=05311&sort=co2`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: "SDUI" }).click();
  await page.setViewportSize({ width: 1440, height: 2600 });
  await page.locator("main button:has(h3)").nth(4).click();
  await page.waitForTimeout(800);
  await shotModal(page, "c11-detalhe-inspecao-sdui");
  await page.locator("dialog[open]").getByLabel("Mutação do servidor").selectOption("reordenar");
  await page.waitForTimeout(800);
  await shotModal(page, "c12-detalhe-mutacao-servidor-reordenar");

  // Home no modo de inspecao SDUI (Figura 5), 1280x860 a 2x, como a figura original.
  const h = await browser.newPage({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2 });
  await h.goto(`${BASE}/?customer_zip_prefix=05311`);
  await h.getByText("Em alta em SP", { exact: true }).waitFor();
  await h.getByRole("button", { name: "SDUI" }).click();
  await h.waitForTimeout(800);
  await shot(h, "c15-home-inspecao-sdui");
  await h.close();

  // Celular
  const m = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, deviceScaleFactor: 2 });
  await m.goto(`${BASE}/?customer_zip_prefix=05311`);
  await m.waitForLoadState("networkidle");
  await m.screenshot({ path: path.join(OUT, "c13-mobile-home.png") });
  await m.locator("main button:has(h3)").first().click();
  await m.waitForTimeout(800);
  await m.screenshot({ path: path.join(OUT, "c14-mobile-detalhe.png") });

  await browser.close();
  console.log("ok");
})().catch((e) => { console.error(e); process.exit(1); });
