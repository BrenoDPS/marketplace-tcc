import { expect, test, type Page } from "@playwright/test";

/**
 * A mesma jornada SO com teclado (D10): Tab, Shift+Tab, Enter e Espaco. Nenhum
 * `click`. Se um controle nao recebe foco, ou o foco some atras de um modal,
 * este teste trava no `tabAte`.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const CEP = "05311";

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/home?customer_zip_prefix=${CEP}`).catch(() => null);
  if (!res?.ok) throw new Error(`Backend indisponivel em ${API}: suba a pilha (ver journey.spec.ts).`);
});

/** Aperta Tab ate o elemento focado ter este nome acessivel (ou desiste). */
async function tabAte(page: Page, nome: RegExp, max = 80) {
  for (let i = 0; i < max; i++) {
    await page.keyboard.press("Tab");
    const focado = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement | null;
      return el ? (el.getAttribute("aria-label") ?? el.innerText ?? "").trim() : "";
    });
    if (nome.test(focado)) return;
  }
  throw new Error(`nenhum controle com nome ${nome} recebeu foco em ${max} Tabs`);
}

test("jornada so com teclado: CEP, produto, carrinho e checkout", async ({ page }) => {
  await page.goto(`/?customer_zip_prefix=${CEP}&context=conscious_buyer`);
  await expect(page.locator("main h3").first()).toBeVisible();

  await test.step("abre o primeiro produto e o adiciona", async () => {
    // O chip de categoria tem o mesmo nome e vem antes: o card e o que diz "Sai de".
    await tabAte(page, /Esporte e lazer\s+Sai de/);
    await page.keyboard.press("Enter");
    const dialog = page.locator("dialog[open]");
    await expect(dialog.getByRole("button", { name: "Ir para o carrinho" })).toBeVisible();
    // O <dialog> nativo prende o foco: Tab percorre so o modal.
    await tabAte(page, /^Ir para o carrinho$/);
    await page.keyboard.press("Enter");
    await expect(dialog.getByRole("heading", { name: "1 produto" })).toBeVisible();
  });

  await test.step("simula a compra e chega ao checkout em pagina", async () => {
    await tabAte(page, /^Simular compra$/);
    await page.keyboard.press("Enter");
    await expect(page.getByRole("heading", { name: "Compra simulada" })).toBeVisible();
  });

  await test.step("etapa Entrega e modalidade Verde pelo teclado", async () => {
    await tabAte(page, /Entrega$/);
    await page.keyboard.press("Enter");
    await expect(page.locator("#delivery_options")).toBeFocused();
    await tabAte(page, /^Verde/);
    // Foco visivel: o anel aparece no controle focado pelo teclado.
    const outline = await page.evaluate(() => getComputedStyle(document.activeElement as Element).outlineStyle);
    expect(outline).toBe("solid");
    await page.keyboard.press("Space");
    await expect(page.getByRole("radio", { name: /Verde/ })).toHaveAttribute("aria-checked", "true");
  });
});
