import { expect, test, type Page } from "@playwright/test";

/**
 * Teste de mutacao de contrato — objetivo especifico (d) do TCC, a metade
 * "flexibilidade" que faltava ser demonstrada.
 *
 * A secao 3.3 da metodologia promete:
 *
 *   "testes de mutacao de contrato no servidor BFF, alterando dinamicamente a
 *   hierarquia dos nos da arvore JSON, como a reordenacao de blocos de
 *   conteudo, a injecao condicional de selos ecologicos de logistica verde e a
 *   insercao de novos componentes visuais sem alteracoes no codigo-fonte do
 *   cliente web. A validacao do desacoplamento sera atestada pela capacidade
 *   do renderizador generico em React de interpretar e refletir as novas
 *   diretrizes visuais em tempo de execucao (runtime), sem demandar
 *   recompilacao de pacotes (build)."
 *
 * ONDE A MUTACAO ACONTECE, E POR QUE AQUI
 *
 * A Home e um Server Component: o `ScreenResponse` e buscado pelo servidor do
 * Next e chega ao browser ja como HTML, entao nao ha requisicao do browser para
 * interceptar. Ja o DETALHE chega por `api_call` executada no cliente
 * (`fetch` em `sdui-context.tsx`), e e a MESMA `ScreenRenderer` que desenha as
 * duas telas. Mutar o detalhe exercita exatamente o mesmo renderizador.
 *
 * A mutacao e aplicada sobre a RESPOSTA REAL do backend (`route.fetch()` e
 * depois transforma), nao sobre uma fixture: o ponto de partida e sempre uma
 * arvore que o BFF produziu de verdade.
 *
 * O QUE ISTO PROVA — E O QUE NAO PROVA
 *
 * Prova: o cliente nao tem conhecimento previo da COMPOSICAO da tela. A ordem
 * dos blocos, a presenca do selo e quais blocos existem sao ditados pela
 * arvore JSON, em runtime.
 *
 * Nao prova: que o backend saiba produzir estas arvores especificas. Isso e
 * outro teste — e as telas que o backend ja produz estao cobertas pelos 147
 * testes de `pytest` e pela jornada em `journey.spec.ts`.
 *
 * A PAGINA NUNCA RECARREGA. Nenhuma das mutacoes provoca reload: o modal
 * refaz o `fetch` e redesenha. Um marcador plantado no `window` antes da
 * primeira mutacao e conferido no fim — se a pagina tivesse recarregado, ou o
 * bundle sido reconstruido, ele teria sumido. E a forma mais direta de mostrar
 * "sem recompilacao de pacotes": o mesmo contexto de execucao do JavaScript
 * atravessa as tres mutacoes.
 */

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const CEP = "05311";

/** So um `<dialog>` fica aberto por vez, e fechado ele nao renderiza filhos. */
const modal = (page: Page) => page.locator("dialog[open]");

/**
 * O modo de inspecao desenha a arvore que o servidor mandou —
 * `hero_banner → product_card → ...`. E a assercao mais direta sobre a
 * HIERARQUIA: le a composicao, nao um efeito colateral visual dela.
 */
const arvore = (page: Page) =>
  modal(page).locator("p.font-mono.leading-relaxed").first();

type Bloco = {
  type: string;
  version: number;
  props: Record<string, unknown>;
  // O envelope do contrato SEMPRE tem `actions` (Pydantic usa
  // `default_factory=list`). Omitir aqui produziria uma arvore que o backend
  // nao consegue emitir — e o cliente quebra nela, ver o card de robustez.
  actions: unknown[];
};

type Tela = { components: Bloco[] };

/**
 * Intercepta a resposta REAL do detalhe e aplica a mutacao antes de entregar
 * ao cliente. Chamar de novo troca a mutacao em vigor.
 */
async function mutarContrato(page: Page, mutacao: (tela: Tela) => void) {
  await page.unroute("**/api/v1/products/**").catch(() => {});
  await page.route("**/api/v1/products/**", async (route) => {
    const resposta = await route.fetch();
    const tela = (await resposta.json()) as Tela;
    mutacao(tela);
    await route.fulfill({ response: resposta, json: tela });
  });
}

/**
 * Evidencia para a defesa: `EVIDENCIA=1 npx playwright test contract-mutation`
 * grava um PNG por mutacao em `docs/evidencia/`. Atras de flag porque um
 * binario reescrito a cada execucao local so suja o `git status`.
 */
const EVIDENCIA = process.env.EVIDENCIA === "1";

async function registrar(page: Page, nome: string) {
  if (!EVIDENCIA) return;
  await modal(page).screenshot({ path: `../docs/evidencia/${nome}.png` });
}

/** Fecha e reabre o detalhe: novo `fetch`, nova arvore, MESMA pagina. */
async function reabrirDetalhe(page: Page) {
  const aberto = modal(page);
  if (await aberto.count()) {
    await aberto.getByRole("button", { name: "Fechar" }).click();
    await expect(aberto).toHaveCount(0);
  }
  await page.locator("main button:has(h3)").first().click();
  await expect(modal(page)).toBeVisible();
}

test.beforeAll(async () => {
  const res = await fetch(`${API}/api/v1/home?customer_zip_prefix=${CEP}`).catch(
    () => null,
  );
  if (!res?.ok) {
    throw new Error(
      `Backend indisponivel em ${API} (${res?.status ?? "sem resposta"}).\n` +
        "Este E2E roda contra a pilha real. Suba tudo antes:\n" +
        "  docker compose up -d\n" +
        "  python -m scripts.etl_load_sample\n" +
        "  uvicorn src.main:app",
    );
  }
});

test("mutacao de contrato: o cliente obedece a arvore, sem rebuild", async ({
  page,
}) => {
  await test.step("entra na vitrine e liga o modo de inspecao", async () => {
    await page.goto("/");

    // Mesma espera da jornada: um `fill` antes da hidratacao escreve no DOM
    // mas nao no estado do React, e o botao continua desabilitado.
    const zip = page.getByLabel("Prefixo do CEP");
    const entrar = page.getByRole("button", { name: "Entrar" });
    await expect(async () => {
      await zip.fill(CEP);
      await expect(entrar).toBeEnabled({ timeout: 500 });
    }).toPass({ timeout: 20_000 });
    await entrar.click();
    await expect(page.locator("main h3")).not.toHaveCount(0);

    await page.getByRole("button", { name: "SDUI" }).click();

    // O marcador que prova que nada recarregou daqui para a frente.
    await page.evaluate(() => {
      (window as unknown as Record<string, unknown>).__contexto = "intacto";
    });
  });

  await test.step("linha de base: a arvore que o backend produz de verdade", async () => {
    await reabrirDetalhe(page);
    await expect(arvore(page)).toHaveText("product_detail → impact_banner");
    await registrar(page, "0-linha-de-base");
  });

  await test.step("mutacao 1: reordenar os blocos inverte a tela", async () => {
    await mutarContrato(page, (tela) => tela.components.reverse());
    await reabrirDetalhe(page);

    await expect(arvore(page)).toHaveText("impact_banner → product_detail");

    // A arvore inverteu no DOM tambem, nao so na etiqueta de inspecao: o
    // `<h2>` do detalhe agora vem DEPOIS do texto do banner de impacto.
    const tipos = await modal(page)
      .locator("details > summary")
      .allInnerTexts();
    expect(tipos[0]).toContain("impact_banner");
    expect(tipos[1]).toContain("product_detail");
    await registrar(page, "1-reordenacao");
  });

  await test.step("mutacao 2: injetar selo faz o selo aparecer", async () => {
    await mutarContrato(page, (tela) => {
      for (const bloco of tela.components) {
        bloco.props.badge = {
          label: "Selo injetado pelo contrato",
          impact_level: "green",
          icon: "leaf",
        };
      }
    });
    await reabrirDetalhe(page);

    // `span` e nao `getByText` solto: o inspetor tambem imprime o JSON do
    // bloco, entao o texto casa dentro do `<pre>` colapsado — que esta oculto.
    // Ancorar no elemento do selo mede o que a tela DESENHA.
    await expect(
      modal(page).locator("span", { hasText: "Selo injetado pelo contrato" }).first(),
    ).toBeVisible();
    await registrar(page, "2-injecao-de-selo");
  });

  await test.step("mutacao 3a: bloco novo na tela aparece sem tocar no cliente", async () => {
    await mutarContrato(page, (tela) => {
      // `product_card` existe no REGISTRY mas o detalhe NUNCA o emitiu. Se a
      // tela o desenhar, a composicao e do servidor — nao ha caminho no
      // cliente que ponha um card aqui.
      tela.components.push({
        type: "product_card",
        version: 1,
        props: {
          product_id: "injetado-pelo-contrato",
          price: 12.34,
          title: "Card que o detalhe nunca emitiu",
          image_url: null,
          badge: null,
        },
        actions: [],
      });
    });
    await reabrirDetalhe(page);

    await expect(arvore(page)).toHaveText(
      "product_detail → impact_banner → product_card",
    );
    await expect(
      modal(page).getByRole("heading", { name: "Card que o detalhe nunca emitiu" }),
    ).toBeVisible();
    await registrar(page, "3a-bloco-novo");
  });

  await test.step("mutacao 3b: bloco DESCONHECIDO degrada, nao quebra", async () => {
    await mutarContrato(page, (tela) => {
      tela.components.push({
        type: "promo_carousel_que_nao_existe",
        version: 7,
        props: { titulo: "bloco de um cliente mais novo" },
        actions: [],
      });
    });
    await reabrirDetalhe(page);

    // A propriedade que sustenta a tese na pratica: o servidor pode evoluir
    // adiante do cliente sem derrubar a tela de quem ainda nao atualizou.
    await expect(modal(page).getByRole("heading").first()).toBeVisible();
    await expect(
      modal(page).getByText("não tem componente no"),
    ).toBeVisible();

    // O painel do bloco desconhecido fica no fim da tela; sem rolar ate ele a
    // evidencia mostraria o topo do modal e nao o que se quer provar.
    await modal(page).getByText("não tem componente no").scrollIntoViewIfNeeded();
    await registrar(page, "3b-bloco-desconhecido");
  });

  await test.step("nada disso recarregou a pagina nem reconstruiu o bundle", async () => {
    const contexto = await page.evaluate(
      () => (window as unknown as Record<string, unknown>).__contexto,
    );
    expect(
      contexto,
      "a pagina recarregou no meio das mutacoes: a prova de 'sem rebuild' cai",
    ).toBe("intacto");
  });
});
