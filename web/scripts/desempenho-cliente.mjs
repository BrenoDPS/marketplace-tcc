// Desempenho no cliente (T5): build de produção, medido no navegador.
// A API mede o servidor; aqui se mede o que o comprador espera na tela, incluindo a
// interpretação da árvore SDUI pelo React.
//
// Uso, com a API no ar e o build servido (de web/: npm run build && npx next start -p 3200):
//   node scripts/desempenho-cliente.mjs   # grava ../docs/resultados/desempenho-cliente.md
//
// Cada rodada usa um contexto novo do navegador (sem cache HTTP: primeira visita).
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { chromium } from "playwright";

const BASE = process.env.WEB_URL ?? "http://localhost:3200";
const RODADAS = 10;
const CEP = "05311";

const mediana = (xs) => { const s = [...xs].sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const p90 = (xs) => [...xs].sort((a, b) => a - b)[Math.ceil(0.9 * xs.length) - 1];
const br = (x, casas = 0) => x.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

const OBSERVAR = () => {
  window.__lcp = 0; window.__cls = 0;
  new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__lcp = e.startTime; }).observe({ type: "largest-contentful-paint", buffered: true });
  new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; }).observe({ type: "layout-shift", buffered: true });
};

async function vitrine(browser, celular) {
  const ctx = await browser.newContext(celular ? { viewport: { width: 390, height: 844 }, isMobile: true, deviceScaleFactor: 2 } : { viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  if (celular) {
    const cdp = await ctx.newCDPSession(page);
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
  }
  await page.addInitScript(OBSERVAR);
  await page.goto(`${BASE}/?customer_zip_prefix=${CEP}`, { waitUntil: "load" });
  await page.locator("main button:has(h3)").first().waitFor();
  await page.waitForTimeout(300);
  const m = await page.evaluate(() => {
    const n = performance.getEntriesByType("navigation")[0];
    const fcp = performance.getEntriesByName("first-contentful-paint")[0]?.startTime ?? 0;
    return { ttfb: n.responseStart, fcp, lcp: window.__lcp, cls: window.__cls, load: n.loadEventEnd };
  });
  await ctx.close();
  return m;
}

async function jornada(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/?customer_zip_prefix=${CEP}&sort=co2`, { waitUntil: "load" });
  const cards = page.locator("main button:has(h3)");
  await cards.nth(4).waitFor();
  let t = performance.now();
  await cards.nth(4).click();
  await page.locator("dialog[open]").getByText("De onde este produto pode sair").waitFor();
  const detalhe = performance.now() - t;
  await page.locator("dialog[open]").getByRole("button", { name: "Ir para o carrinho" }).click();
  const simular = page.locator("dialog[open]").getByRole("button", { name: "Simular compra" });
  await simular.waitFor();
  t = performance.now();
  await simular.click();
  await page.getByRole("radio", { name: /Verde/ }).waitFor();
  const checkout = performance.now() - t;
  await ctx.close();
  return { detalhe, checkout };
}

const browser = await chromium.launch();
await vitrine(browser, false); // aquecimento do servidor Next e da API (não entra na conta)
await jornada(browser);
const desk = [], cel = [], jor = [];
for (let i = 0; i < RODADAS; i++) {
  desk.push(await vitrine(browser, false));
  cel.push(await vitrine(browser, true));
  jor.push(await jornada(browser));
}
await browser.close();

const linha = (nome, xs, campo, unid = "ms", casas = 0) =>
  `| ${nome} | ${br(mediana(xs.map((x) => x[campo])), casas)} ${unid} | ${br(p90(xs.map((x) => x[campo])), casas)} ${unid} |`;
const commit = execSync("git rev-parse --short HEAD").toString().trim();
const md = `# Desempenho no cliente (build de produção)

> Gerado por \`node scripts/desempenho-cliente.mjs\` (de \`web/\`) no commit \`${commit}\`. Next.js em
> produção (\`next build\` + \`next start\`), API local com cache de respostas ligado, Chromium do
> Playwright, ${RODADAS} rodadas com contexto novo (primeira visita, sem cache HTTP). CEP ${CEP}.
> "Celular simulado" = 390 px com a CPU 4× mais lenta (Chrome DevTools).

## Página inicial (renderizada no servidor a partir da ScreenResponse)

| Métrica | Mediana | p90 |
|---|---|---|
${linha("Desktop — tempo até o primeiro byte", desk, "ttfb")}
${linha("Desktop — primeira pintura (FCP)", desk, "fcp")}
${linha("Desktop — maior pintura (LCP)", desk, "lcp")}
${linha("Desktop — carga completa", desk, "load")}
${linha("Celular simulado — FCP", cel, "fcp")}
${linha("Celular simulado — LCP", cel, "lcp")}
${linha("Celular simulado — carga completa", cel, "load")}

Deslocamento de layout acumulado (CLS): mediana ${br(mediana(desk.map((x) => x.cls)), 3)} no desktop e ${br(mediana(cel.map((x) => x.cls)), 3)} no celular simulado (bom: abaixo de 0,1).

## Interações (tela pedida ao servidor e interpretada no cliente)

| Interação | Mediana | p90 |
|---|---|---|
${linha("Clique no produto → detalhe com comparador na tela", jor, "detalhe")}
${linha("Simular compra → checkout com modalidades na tela", jor, "checkout")}

JavaScript enviado ao navegador: ~190 KB comprimidos (620 KB sem compressão), em 10 arquivos
(\`.next/static/chunks\`).

**Referências do Google para Core Web Vitals:** LCP bom até 2,5 s; CLS bom até 0,1.
`;
writeFileSync("../docs/resultados/desempenho-cliente.md", md);
console.log(md);
