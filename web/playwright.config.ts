import { defineConfig, devices } from "@playwright/test";

/**
 * E2E da jornada da defesa. Roda contra a PILHA REAL (Postgres + ETL +
 * FastAPI), nao contra fixtures: o valor deste teste e responder "a demo da
 * apresentacao ainda funciona?", e um mock responderia outra pergunta.
 *
 * Por isso NAO esta no CI: `data/raw/` e gitignored, entao o runner do GitHub
 * nao tem os CSVs do Olist para popular o banco. E um check local de
 * pre-defesa — `npm run e2e` com a pilha no ar.
 */
export default defineConfig({
  testDir: "./e2e",
  // A jornada e sequencial por natureza (carrinho -> checkout) e o servidor de
  // dev e um so; paralelizar aqui so criaria corrida por porta.
  workers: 1,
  reporter: [["list"]],
  use: {
    // `localhost` e nao `127.0.0.1`: o dev server do Next 16 responde 403 no
    // chunk do cliente para origens que ele nao reconhece, e a pagina fica
    // servida mas NAO hidratada — o teste veria a tela e nenhum clique
    // funcionaria. Levou uma sessao de depuracao; nao trocar de volta.
    baseURL: "http://localhost:3100",
    locale: "pt-BR",
    // So guarda rastro do que falhou: verde nao precisa de 40 MB de video.
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // Porta 3100 e nao 3000 de proposito: a 3000 costuma estar ocupada por
    // outro app na maquina de desenvolvimento, e o Next cai para a 3001
    // silenciosamente — o teste passaria a medir a aplicacao errada.
    command: "npm run dev -- -p 3100",
    url: "http://localhost:3100",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
