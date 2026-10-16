import { expect, test, type Locator, type Page } from "@playwright/test";

/**
 * A jornada da defesa, do jeito que ela e apresentada:
 * CEP -> busca -> categoria -> produto -> carrinho -> simular -> trocar
 * modalidade e ver frete, CO2 e selo se moverem juntos.
 *
 * Roda contra a pilha REAL. Ver o cabecalho de `playwright.config.ts` para o
 * porque de isto nao estar no CI.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
/** Sao Paulo: a amostra tem vendedores perto daqui, entao ha selo verde. */
const CEP = "05311";
/** Maior categoria do Olist — presente em qualquer amostra razoavel. */
const TERM = "cama mesa banho";

/** "R$ 1.234,56" -> 1234.56 */
const brl = (text: string) => Number(text.replace(/[^\d,]/g, "").replace(",", "."));

/** `co2Label` exibe gramas ate 1 kg ("8,48 g", "21,2 g") e kg acima ("1,50 kg"). */
const co2 = (text: string) => {
  const value = Number(text.replace(/[^\d,]/g, "").replace(",", "."));
  return text.includes("kg") ? value : value / 1000;
};

/** O `<dd>` que segue um `<dt>` com este texto exato. */
const fact = (scope: Locator | Page, term: string) =>
  scope.locator("dt").filter({ hasText: new RegExp(`^${term}$`) }).locator("xpath=following-sibling::dd[1]");

/** So um `<dialog>` fica aberto por vez, e fechado ele nao renderiza filhos. */
const modal = (page: Page) => page.locator("dialog[open]");

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/home?customer_zip_prefix=${CEP}`).catch(() => null);
  if (!res?.ok) {
    throw new Error(
      `Backend indisponivel em ${API} (${res?.status ?? "sem resposta"}).\n` +
        "Este E2E roda contra a pilha real. Suba tudo antes:\n" +
        "  docker compose up -d\n" +
        "  python -m scripts.etl_load_sample\n" +
        "  uvicorn src.main:app --reload",
    );
  }
});

test("jornada da defesa: do CEP ao comparativo de entrega", async ({ page }) => {
  await test.step("informa o CEP e recebe a vitrine", async () => {
    await page.goto("/");

    // A tela de entrada e um Client Component dentro de um Server Component:
    // um `fill` que chega antes da hidratacao escreve no DOM mas nao no estado
    // do React, e o botao (`disabled={!zip.trim()}`) continua desabilitado.
    // Repetir ate o React registrar e mais honesto que um sleep fixo.
    const zip = page.getByLabel("Prefixo do CEP");
    const enter = page.getByRole("button", { name: "Entrar" });
    await expect(async () => {
      await zip.fill(CEP);
      await expect(enter).toBeEnabled({ timeout: 500 });
    }).toPass({ timeout: 20_000 });
    await enter.click();

    await expect(page).toHaveURL(new RegExp(`customer_zip_prefix=${CEP}`));
    await expect(page.locator("main h3")).not.toHaveCount(0);
  });

  await test.step("busca por categoria filtra a vitrine", async () => {
    await page.getByLabel("Buscar por categoria").fill(TERM);
    await page.getByRole("button", { name: "Buscar" }).click();

    // O titulo do hero e escrito pelo SERVIDOR a partir do termo: se ele
    // aparece, a busca chegou ao backend e voltou como tela.
    await expect(page.getByRole("heading", { name: `Busca: ${TERM}` })).toBeVisible();
    // Todo card visivel pertence a categoria buscada.
    await expect(page.locator("main h3").first()).toHaveText(/Cama, mesa e banho/i);
  });

  await test.step("chip de categoria marca a selecao", async () => {
    const first = page.locator("ul button[aria-current]").first();
    const label = (await first.textContent())?.trim() ?? "";
    await first.click();

    await expect(page).toHaveURL(/category=/);
    // `aria-current` vem do servidor (`selected` no bloco), nao do cliente.
    await expect(page.locator('ul button[aria-current="true"]')).toContainText(
      label.replace(/\d+$/, "").trim(),
    );
  });

  await test.step("volta a vitrine completa pelo CTA do servidor", async () => {
    await page.getByRole("button", { name: "Ver tudo" }).click();
    await expect(page).not.toHaveURL(/category=/);
  });

  await test.step("ordena a vitrine por menor preco (opcao vinda do servidor)", async () => {
    const ordenar = page.getByRole("navigation", { name: "Ordenar a vitrine" });
    await ordenar.getByRole("button", { name: "Menor preço" }).click();
    await expect(page).toHaveURL(/sort=preco/);
    await expect(ordenar.getByRole("button", { name: "Menor preço" })).toHaveAttribute("aria-current", "true");
    const precos = await page.locator("main button:has(h3) p.font-display").allInnerTexts();
    const valores = precos.map(brl);
    expect(valores).toEqual([...valores].sort((a, b) => a - b));
  });

  await test.step("abre o detalhe de um produto com selo verde", async () => {
    // O detalhe vem de `GET /products/{id}`: e outra tela do servidor, nao um
    // remonte do card. Escolher um card COM selo garante < 100 km, e portanto
    // selo tambem no checkout.
    const green = page.locator("main button:has(h3)").filter({ hasText: "Entrega local" }).first();
    await expect(green).toBeVisible();
    await green.click();

    await expect(modal(page).getByRole("button", { name: "Adicionar ao carrinho" })).toBeVisible();
    // Um selo por tela (D6): o do `product_detail`; o `impact_banner` explica
    // o numero sem repetir o selo.
    // O selo e "Entrega local (~N km ...)"; o comparador de origens tambem
    // escreve "entrega local", mas como rotulo de linha, nao como selo.
    await expect(modal(page).getByText(/^Entrega local \(/)).toHaveCount(1);
  });

  await test.step("adiciona ao carrinho e simula a compra", async () => {
    await modal(page).getByRole("button", { name: "Ir para o carrinho" }).click();

    await expect(modal(page).getByRole("heading", { name: "1 produto" })).toBeVisible();
    await modal(page).getByRole("button", { name: "Simular compra" }).click();

    // Checkout e PAGINA (D5), com URL propria: nada de modal por cima.
    const checkout = page.locator("main");
    await expect(checkout.getByRole("heading", { name: "Compra simulada" })).toBeVisible();
    await expect(page).toHaveURL(/etapa=checkout/);
    await expect(page.locator("dialog[open]")).toHaveCount(0);
    await expect(checkout.getByRole("heading", { name: "Como entregar" })).toBeVisible();
  });

  await test.step("etapas levam aos blocos e a recarga refaz a simulacao", async () => {
    const etapas = page.getByRole("navigation", { name: "Etapas da compra" });
    await etapas.getByRole("button", { name: /Impacto/ }).click();
    await expect(page.locator("#shipment_breakdown")).toBeFocused();

    // F5: a resposta do POST se perde, o carrinho nao — a pagina refaz.
    await page.reload();
    await expect(page.getByRole("heading", { name: "Compra simulada" })).toBeVisible();
  });

  await test.step("trocar de modalidade move frete, CO₂ e selo juntos", async () => {
    const dialog = page.locator("main");
    const modes = dialog.getByRole("radiogroup", { name: "Modalidade de entrega" });
    const freight = fact(dialog, "Frete");
    const footprint = fact(dialog, "CO₂ estimado");
    const badge = dialog.getByText(/Entrega local/).first();

    await expect(modes.getByRole("radio", { name: "Padrão" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    const base = {
      freight: brl(await freight.innerText()),
      co2: co2(await footprint.innerText()),
      badge: await badge.innerText(),
    };

    await modes.getByRole("radio", { name: "Verde" }).click();
    // A tela inteira e recomposta pelo servidor; esperar o selo mudar de texto
    // e o sinal de que a resposta nova chegou.
    await expect(badge).not.toHaveText(base.badge);

    // A modalidade verde e mais barata (0,85x) e menos emissiva (0,6x) que a
    // padrao. Nao basta "mudou": tem que mudar na direcao que a tela promete.
    expect(brl(await freight.innerText())).toBeLessThan(base.freight);
    expect(co2(await footprint.innerText())).toBeLessThan(base.co2);

    await modes.getByRole("radio", { name: "Expressa" }).click();
    await expect(modes.getByRole("radio", { name: "Expressa" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(brl(await freight.innerText())).toBeGreaterThan(base.freight);
    expect(co2(await footprint.innerText())).toBeGreaterThan(base.co2);
  });

  await test.step("voltar do navegador sai do checkout para a vitrine", async () => {
    await page.goBack();
    await expect(page).not.toHaveURL(/etapa=checkout/);
    await expect(page.getByRole("heading", { name: "Compra simulada" })).toHaveCount(0);
  });
});
