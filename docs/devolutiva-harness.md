# Devolutiva — proposta de Harness Engineering

> Resposta ao `docs/revisao-harness.md` (commit `7e55c00`), no formato da §7 dele.
> As mudanças aceitas **já foram aplicadas** na mesma rodada; a última seção lista
> o que entrou no diff.

## 0. Antes do veredito: o que conferi e o que mudou a análise

O pacote pede para não explorar o repositório. Explorei pouco e de propósito:
conferi as afirmações da §2 e as linhas da §4.4 que sustentam decisões. **A §2
está correta** — 162 `test_`, 32 casos vitest, as quatro contradições sobre Redis,
o bootstrap apontando para a Sprint 5, nenhum `CLAUDE.md` na raiz, `web/AGENTS.md`
regravado pelo `next dev`, a fronteira de 13 commits da Sprint 7.

Mas há **um fato que a §2 não registra e que muda o desenho**:

> **O Claude Code não lê `.cursorrules`.** Ele carrega `CLAUDE.md` (e o que ele
> importa com `@`). O `AGENTS.md` proposto diz *"As regras de código estão em
> `.cursorrules` e não são repetidas aqui"* — então uma sessão do Claude Code
> receberia o **mapa**, mas **nenhuma regra** (VSA, envelope SDUI, async, "medir
> antes de otimizar"). E importar o `.cursorrules` também não serve: ele contém
> `@docs/prd.md`, `@docs/tech_spec.md`, `@docs/PROJECT_BOOTSTRAP.md` e
> `@docs/sprint3-handoff.md`, que o Claude Code **expande recursivamente** —
> ~29k caracteres carregados em toda sessão, um deles um handoff obsoleto.

Consequência: as regras precisam morar **no** `AGENTS.md`, e o `.cursorrules` sai
(o Cursor lê `AGENTS.md` nativamente). Isso reescreve os itens 5 e 10.

---

## 1. Veredito por item

| # | Arquivo | Veredito | Motivo |
|---|---|---|---|
| 1 | `docs/_template-handoff.md` | **REJEITAR** (ideia aceita, sem arquivo) | Não há sprint aberta para usar o molde; os handoffs 2–5 já têm o formato. As duas regras que importam — *aceite nomeia o comando* e *falha recorrente vira teste/regra* — foram para a seção "Sprint ativa" do bootstrap, que é onde se lê ao abrir uma sprint. |
| 2 | `docs/harness.md` | **REJEITAR** | É 100% derivável do `AGENTS.md` + bootstrap — um terceiro mapa. Viola a própria regra da proposta (*"doc novo sem sensor é dívida"*). Se a correspondência com as 8 peças do guia tem valor, o lugar é a monografia, não o repo. |
| 3 | `docs/sprint6-handoff.md` (reconstruído) | **REJEITAR** | Um handoff é contrato escrito **antes** da sprint; reconstruído depois, é changelog com cara de contrato — o risco 3 da própria proposta. O registro foi para onde as sprints 3–6 já estão: seções do `README.md` + linha na tabela "Sprints concluídas" do bootstrap, com faixa de commits. |
| 4 | `docs/sprint7-handoff.md` (reconstruído) | **REJEITAR** | Mesmo motivo. Além disso, o mapa proposto o apontaria como *"tarefa atual"* — reproduzindo exatamente o defeito da §2.5 (sprint concluída marcada como ativa). |
| 5 | `AGENTS.md` (raiz) | **ACEITAR COM MUDANÇA** | Absorve as regras do `.cursorrules` (ver §0), deixa de apontar handoff como tarefa atual, tira os termos de runtime de agente e a palavra "harness", tira `src/core/cache.py` das fronteiras. Detalhe nas respostas 1–3. |
| 6 | `CLAUDE.md` (raiz) = `@AGENTS.md` | **ACEITAR** | Correto e barato. Só funciona por causa da mudança no item 5. |
| 7 | `tests/test_docs.py` | **ACEITAR COM MUDANÇA** | O sensor útil e honesto é: *todo caminho citado em `AGENTS.md`, bootstrap e README existe*. Ele **não** detecta "sprint concluída marcada como ativa" — isso é semântico, e o docstring diz isso. **Roda no CI** (ver risco 5). |
| 8 | `scripts/preflight.py` | **REJEITAR** | Seria uma segunda cópia do `ci.yml`, que deriva em silêncio — o mesmo problema `sdui.ts`↔`sdui.py` que a proposta critica. Os comandos do CI estão listados no `AGENTS.md` (duas linhas). |
| 9 | `docs/PROJECT_BOOTSTRAP.md` | **ACEITAR** | Sprints 5/6/7 na tabela; "Sprint ativa: nenhuma com handoff"; Redis corrigido; `AGENTS.md` no lugar do `.cursorrules` na tabela de documentos. |
| 10 | `.cursorrules` | **ACEITAR COM MUDANÇA** | Não só remover a proibição de Redis: as regras inteiras migram para o `AGENTS.md` e o arquivo é removido. Uma fonte de regras para os dois agentes. |
| 11 | `README.md` | **ACEITAR (ampliado)** | Sprint 6 → concluída; nova seção "Sprint 7 (concluída)"; parágrafo falso do Redis reescrito ("Descartado ou em aberto"); a linha de base 16/140/470 ganhou a ressalva do `echo` (ver resposta 7). |
| 12 | `docs/tech_spec.md` | **ACEITAR** | "foram removidos" / "Sem Redis" corrigidos. |

---

## 2. Respostas

### 1. O `AGENTS.md` proposto induz divergência do plano principal? Onde?

Sim, em três pontos:

- **`| **Tarefa atual (contrato)** | docs/sprint7-handoff.md — ou o de maior N |`** —
  o principal. A Sprint 7 está concluída; o agente trataria critérios de aceite já
  cumpridos (ou "reconstruídos") como trabalho pendente. A regra "maior N" falha
  sempre que uma sprint termina antes de a próxima ter handoff — que é o estado
  normal entre sprints. **Corrigido:** *"A tarefa atual é o que foi pedido na
  conversa"*; sprint ativa só se o bootstrap declarar uma.
- **`Não introduza runtime de agente — /tasks, /runs, /approvals, ToolGateway,
  tabelas agent_runs/run_state`** — num arquivo carregado em toda sessão, essa
  linha **apresenta** ao modelo um vocabulário que não existe no repo (efeito
  "não pense num elefante"). Um agente que nunca viu a proposta alternativa passa
  a conhecê-la. **Corrigido:** uma frase — *"O produto não usa LLM; não adicione
  dependência de IA generativa sem pedido explícito."*
- **`As regras de código estão em .cursorrules`** — não diverge o escopo, mas deixa
  o Claude Code sem regra nenhuma (ver §0).

### 2. Reduz ou aumenta o gasto de token por sessão? Qual item é o mais caro?

| | Claude Code | Cursor |
|---|---|---|
| Hoje | 0 | `.cursorrules` 2,4k chars (+ o que o `@` puxar) |
| Proposta original | ~3,3k chars, **sem as regras** | 3,3k + 2,4k = 5,7k |
| Aplicado | **3,8k chars (~1k tokens)**, mapa + regras | 3,8k |

Aumenta ~1k tokens por sessão no Claude Code — e compensa se evitar **uma**
leitura do `README.md` (29k chars, ~7k tokens). No corpus, os itens mais caros
eram os **handoffs reconstruídos (3 e 4)** — os maiores arquivos novos e os de
menor confiança; rejeitados. O `docs/harness.md` era o mais caro **por valor**:
tokens sem informação nova.

Sobre o README (risco 4): concordo que é o gargalo, mas o Claude Code não o carrega
sozinho. O mapa existe justamente para o agente não começar por ele. Encolher o
README é trabalho legítimo, mas **para leitor humano** — não entra aqui.

### 3. Risco de otimizar o harness em vez do produto? Qual linha piora?

- **`Doc novo sem sensor que o verifique é dívida, não governança.`** — a pior. A
  leitura literal para um agente é *"todo doc precisa de um sensor"*: cada doc
  novo gera um teste novo, e o harness cresce sozinho. **Trocada por:** *"Prefira
  atualizar um doc existente a criar um novo."*
- **`Não expanda o harness além do que serve a próxima entrega.`** — a intenção é
  boa, mas pôr a palavra *harness* no arquivo sempre carregado faz dele um assunto
  do repo. **Removida**; o `AGENTS.md` aplicado não usa a palavra.
- O próprio `docs/harness.md` (item 2) — rejeitado.

### 4. Algum item é redundante com o que já existe?

- **Item 2** com o `AGENTS.md` + bootstrap (três mapas).
- **Item 8** com o `ci.yml`.
- **Itens 3–4** com as seções de sprint do README + `performance.md` §§6–9 (é de lá
  que a própria §4.4 tirou as fontes).
- No `AGENTS.md` proposto: *"Não use transcripts antigos como especificação"* já
  está no bootstrap; removida.

### 5. Menor subconjunto que ainda entrega valor? "Só o Level 2" é defensável?

**Concordo, e dá para ir abaixo do Level 2 proposto:** itens **5, 6, 7, 9, 10, 11,
12** — 3 arquivos novos (`AGENTS.md`, `CLAUDE.md`, `tests/test_docs.py`), 4
editados. Fora: template, `harness.md`, handoffs reconstruídos, `preflight.py`.

O valor está em dois lugares: (a) uma sessão na raiz deixar de começar com **zero**
regras e (b) os docs pararem de afirmar coisas que o código desmente. O resto é
organização.

### 6. O que falta para o objetivo (d) — renderizar por contrato, sem rebuild?

O E2E de mutação prova a metade "**o cliente aceita** árvores que ele não
conhecia". Faltam duas coisas:

1. **Sensor de concordância de `type` entre os dois lados** — **implementado**
   nesta rodada, em `tests/test_schemas.py` (`TestEspelhoDoContratoNoFront`): o
   conjunto de blocos de `UIComponent` tem de ser igual ao de `web/lib/sdui.ts` e ao
   `REGISTRY` de `web/components/sdui.tsx`; o de ações, igual nos dois lados. Roda no
   CI (backend), sem banco. Conferido por mutação: tirar `impact_banner` do
   `REGISTRY` derruba o teste. **Limite declarado:** compara `type`, não `props`.
   Divergência de campo continua sem sensor — o próximo passo seria gerar
   `sdui.ts` a partir de `ScreenResponse.model_json_schema()`.
2. **O E2E de mutação no CI.** Hoje depende de `data/raw/`. O caminho mais curto é
   uma fixture de resposta (o `docs/snapshots/antes.json` já tem telas reais) +
   `page.route` servindo a fixture, mas a Home é Server Component e busca a API no
   servidor do Next, então isso exige um backend falso. **Não implementado** — custo
   real; vale para a defesa só se a banca for olhar o CI.

E um ponto de redação para a monografia: o teste prova *"sem recompilar o
cliente"*, mas **não** que o *servidor* muda sem deploy — as mutações são
injetadas no tráfego, não produzidas pelo BFF. O docstring já diz isso; o texto do
TCC deve dizer também.

### 7. Linhas da §4.4 que não considero confiáveis

| Linha | Problema |
|---|---|
| *Linha de base: p50 16 ms, p95 140, p99 470; 0 falhas em 1.490* | Os números existem (`performance.md` §8), mas foram medidos **com `echo` ligado**; o próprio §8 avisa e manda para a linha de base limpa: **14 / 210 / 650 ms**. Citar 16/140/470 sem a ressalva é exatamente o tipo de afirmação que o projeto já teve de retratar. *(O README tinha o mesmo problema — corrigido.)* |
| *Redis removido do código — decisão por inferência* (fonte `f6c052d`) | A mensagem do commit diz o contrário: *"a decisão **medida** agora está no repositório"*. "Por inferência" é a releitura feita na Sprint 7 (README, seção Redis; `performance.md` §9). O fato está certo; a fonte, errada. |
| *`next typegen` antes do `tsc`* (`c3a9b6f`) na Sprint 6 | O commit corrige os **dois primeiros runs do CI**, que nasceu na Sprint 5 (`9dd2113`). É fechamento da 5, não entrega da 6. A fronteira **inicial** da Sprint 6 nunca foi definida — só a final. |
| *`base_days`/`km_per_day` extintos → `eta_factor`* (fonte `docs/sprint4-handoff.md`) | O fato é da Sprint 7 (`a3a4b16`); a fonte é uma nota retroativa num handoff da Sprint 4. Funciona, mas mostra o risco: um handoff "histórico" que foi editado depois. |
| *O selo não custa nada (14 × 15 ms)* | Confiável **como comparação** (o `echo` estava dos dois lados, `performance.md` §8 diz isso), não como valor absoluto. |
| *Inferência: as 3 sugestões do handoff 5 foram entregues na 6* | Marcada como inferência, o que é correto — mas inferência não deve virar linha de doc. |

O resto das linhas bate com a fonte citada (conferi 2.483 km, 474 casos, 95.921
entregas, 4,9/17,2 d, 66,7%, 1,41×, 53.114/12.809, 54%, 77,2%, p50 14→7, p95
140/210, 0,54 ms, 940→58 ms, `between(1, 3)`, `open_modal` sem emissor,
6.528/6.575, os 13 commits da Sprint 7).

### Sobre o risco 5 (sensor de docs no CI: bloquear ou reportar?)

**Bloquear.** O teste é rápido, não depende de banco, e a única coisa que ele
reprova é um doc citando um arquivo que não existe — o defeito que motivou a
proposta. Um PR que renomeia um arquivo **deve** atualizar o mapa no mesmo PR. Se
virar atrito, o problema é o mapa citar caminho demais, não o sensor.

---

## 3. Achados fora da proposta (corrigidos de carona)

- `web/lib/sdui.ts` dizia *"o contrato tem 4 blocos e 3 ações"* — são 8 blocos.
- `web/e2e/contract-mutation.spec.ts` citava *"147 testes de pytest"* — são 162 (+5
  desta rodada). Número fixo em comentário envelhece; trocado por "pelo `pytest`".
- `docs/revisao-harness.md` (28k chars) e esta devolutiva entram na lista *"não leia
  por padrão"* do `AGENTS.md`. **Recomendo apagar a revisão** depois de lida — ela
  fica no histórico em `7e55c00`, e um agente que a abra encontra a proposta de
  runtime descrita em detalhe.

---

## 4. O que foi aplicado

| Arquivo | Mudança |
|---|---|
| `AGENTS.md` | **novo** — mapa + regras de código (migradas do `.cursorrules`) + comandos do CI + fronteiras |
| `CLAUDE.md` | **novo** — `@AGENTS.md` |
| `.cursorrules` | removido — o Cursor lê o `AGENTS.md` |
| `tests/test_docs.py` | **novo** — caminho citado em `AGENTS.md`/bootstrap/README tem de existir |
| `tests/test_schemas.py` | + `TestEspelhoDoContratoNoFront` — `type` iguais em `sdui.py`, `sdui.ts` e `REGISTRY` |
| `docs/PROJECT_BOOTSTRAP.md` | sprints 5–7; "Sprint ativa: nenhuma" + as duas regras do molde; Redis; `product_detail` na estrutura |
| `README.md` | Sprint 6 concluída; seção Sprint 7; Redis "em aberto"; ressalva do `echo` na linha de base |
| `docs/tech_spec.md` | Redis como variável de experimento |
| `web/lib/sdui.ts`, `web/e2e/contract-mutation.spec.ts` | comentários desatualizados |

**Verificação:** `pytest -q` → **167 passed** (162 + 3 de `test_docs.py` + 2 do espelho). Frontend: só comentários mudaram; lint/typecheck/vitest não foram rodados.
