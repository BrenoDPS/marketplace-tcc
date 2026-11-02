// Captura as telas da aplicação para figuras candidatas da monografia.
// Uso, com a pilha no ar (de web/): node scripts/capturas-tcc.mjs ../docs/tcc/figuras/candidatas
import path from "node:path";
import { chromium } from "playwright";

const BASE = "http://localhost:3000";
const OUT = process.argv[2];
const shot = (page, nome, opts = {}) => page.screenshot({ path: path.join(OUT, `${nome}.png`), ...opts });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(`${BASE}/`);
  await page.waitForLoadState("networkidle");
  await shot(page, "c01-entrada-cep");

  await page.goto(`${BASE}/?customer_zip_prefix=05311`);
  await page.getByRole("heading", { name: /Em alta em SP/ }).waitFor();
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
  await shot(page, "c06-detalhe-selo-mapa-comparador");

  await dialog.getByRole("button", { name: "Ir para o carrinho" }).click();
  await page.waitForTimeout(500);
  await shot(page, "c07-carrinho", { clip: { x: 0, y: 0, width: 1440, height: 900 } });
  await page.locator("dialog[open]").getByRole("button", { name: "Simular compra" }).click();
  await page.getByRole("heading", { name: "Compra simulada" }).waitFor();
  await page.waitForTimeout(800);
  await page.setViewportSize({ width: 1440, height: 900 });
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
  await page.setViewportSize({ width: 1440, height: 2000 });
  await page.locator("main button:has(h3)").nth(4).click();
  await page.waitForTimeout(800);
  await shot(page, "c11-detalhe-inspecao-sdui");
  await page.locator("dialog[open]").getByLabel("Mutação do servidor").selectOption("reordenar");
  await page.waitForTimeout(800);
  await shot(page, "c12-detalhe-mutacao-servidor-reordenar");

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
