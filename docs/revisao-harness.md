# Pacote de revisão — proposta de Harness Engineering

> **Status: AGUARDANDO REVISÃO.** Este documento existe para ser lido por um
> revisor (modelo ou pessoa) **sem** que ele precise explorar o repositório. Nada
> do que ele descreve foi implementado. Apagar depois do veredito, ou manter como
> registro da decisão — a escolha é do autor.

## 0. Como usar

Você é o **revisor**. Sua tarefa é aceitar ou rejeitar cada item da proposta e
apontar o que está errado.

**Não explore o repositório por conta própria.** O estado verificado está na
seção 2, e o apêndice traz o comando que confirma cada afirmação. Varrer o repo
inteiro custaria ~143k caracteres de docs e ~300k de código para chegar ao que já
está aqui.

Responda no formato da seção 7.

---

## 1. O produto (não confundir com o harness)

Marketplace com **Server-Driven UI (SDUI)** sobre o dataset público Olist.

- **Backend:** FastAPI + Pydantic v2 + SQLAlchemy async. Monta uma árvore JSON de
  blocos de UI e a devolve pronta: `{ type, version, props, actions }`, mais um
  `ScreenResponse` com `schema_version`.
- **Frontend:** Next.js 16 (App Router). **Não decide a composição da tela** — só
  renderiza por `type` (via um `REGISTRY`) e executa as `actions` que o servidor
  mandou (`navigate`, `api_call`, `open_modal`).
- **Tese do TCC:** personalização contextual + logística verde (distância entre
  CEPs, selo de entrega local < 100 km, CO₂ estimado).

**Não existe LLM no produto.** Verificado: nenhuma dependência de LLM em
`requirements.txt`, nenhuma ocorrência de `openai`/`anthropic`/`langchain` no
código, nenhuma chave de API, nenhum endpoint de agente. O produto não usa IA
generativa — ele usa SDUI.

---

## 2. Estado verificado do repositório

Cada linha foi conferida; os comandos estão no apêndice.

### 2.1 Testes e CI

1. **162** funções `test_` em `tests/` (12 arquivos).
2. **~32** casos vitest em `web/tests/sdui.test.tsx`.
3. Dois E2E Playwright: `journey.spec.ts` (jornada da defesa) e
   `contract-mutation.spec.ts` (mutação de contrato).
4. Locust em `load/locustfile.py`; resultados em `load/results/`.
5. CI (`.github/workflows/ci.yml`): pytest + lint + typecheck + vitest + build.

### 2.2 Contrato SDUI — o ponto crítico

6. `src/schemas/sdui.py` é a **fonte de verdade** do contrato.
7. `web/lib/sdui.ts` é um espelho **escrito à mão**, mantido em paralelo.
8. **Nada verifica que os dois concordam.** Não há schema compartilhado, geração
   de tipo, nem teste que compare os dois.
9. O E2E de mutação prova que o **cliente aceita** árvores mutadas em runtime —
   intercepta a resposta real, reordena blocos, injeta selo, acrescenta bloco novo
   e bloco desconhecido, e confere que a página **não recarrega nem reconstrói
   bundle**. **Não roda no CI** (depende de `data/raw/`, que é gitignored).
10. O mesmo arquivo declara em docstring o que **não** prova: *"que o backend
    saiba produzir estas árvores específicas"*.

### 2.3 Dados e SQL

11. **Nenhum teste toca SQL** — por decisão, documentada no CI (*"usa
    `dependency_overrides`; se um teste passar a exigir banco, ele quebra aqui, e
    essa quebra é a informação útil"*) e no docstring de `scripts/snapshot_api.py`.
12. O N+1 que fazia **63 queries por requisição** para montar 6 cards só foi
    descoberto por **medição manual**, na 6ª sprint. Nenhum sensor automático
    pegaria — e ainda não pegaria.
13. Existe `scripts/snapshot_api.py`, instrumento manual que congela a resposta da
    API em JSON para diff antes/depois. `docs/snapshots/antes.json` existe;
    **`depois.json` nunca foi gerado** — o procedimento prescrito no próprio
    docstring nunca foi concluído.

### 2.4 A documentação contradiz a si mesma

14. `README.md` tem **duas seções sobre Redis que se contradizem**:
    - *"### Redis — variável de experimento, não arquitetura"* → *"Desligado por
      padrão"*, com `docker compose up -d redis` e `FLUSHALL`;
    - *"Descartado com medição"* → *"O client stub, a dependência e a `REDIS_URL`
      foram removidos para o código não contradizer a decisão."*
15. O código contradiz a segunda: existe `src/core/cache.py` (86 linhas, client
    real com TTL), `redis>=5.0` em `requirements.txt`, `REDIS_URL` e
    `CACHE_ENABLED` em `src/core/config.py`, `await client.ping()` no lifespan, e
    um serviço `redis:7-alpine` no `docker-compose.yml`.
16. `docs/tech_spec.md` repete a afirmação falsa: *"O client stub, a dependência e
    a `REDIS_URL` foram removidos"* e *"**Sem Redis**"*.
17. `.cursorrules` **proíbe** o que o código tem: *"Redis foi avaliado e
    descartado… Não readicionar sem um caso novo."*
18. O que **de fato** aconteceu: a 6ª sprint concluiu contra o Redis **por
    inferência**; a 7ª o reinseriu como **variável de experimento** (atrás de
    `CACHE_ENABLED=false`) para que a decisão virasse medição.

### 2.5 Mapa desatualizado

19. `docs/PROJECT_BOOTSTRAP.md` diz **"Sprint ativa"** apontando para o
    `sprint5-handoff.md`, que está concluído.
20. `README.md` diz **"## Sprint 6 (em andamento)"** — a sprint 6 está concluída.
21. Existem `load/results/s7-*` e `src/core/cache.py` (marcas da 7ª sprint), e
    **não existem** `docs/sprint6-handoff.md` nem `docs/sprint7-handoff.md`.
22. O `.cursorrules` manda o agente ler *"o handoff da sprint ativa"* — que não
    existe para as duas últimas sprints.

### 2.6 Arquivos de regra para agentes

23. `web/AGENTS.md` é **gerado por `next dev`** (bloco
    `BEGIN/END:nextjs-agent-rules`) — seu conteúdo é um aviso de que o Next 16 tem
    breaking changes.
24. `web/CLAUDE.md` contém **uma linha**: `@AGENTS.md`.
25. Os dois são **versionados** (entraram no commit `548c96d`, o primeiro do
    frontend) e nunca foram editados desde então.
26. **Não existe `CLAUDE.md` na raiz.** Uma sessão do Claude Code aberta na raiz
    recebe **zero** regras de projeto: sem mapa, sem contrato, sem fronteiras.

### 2.7 Tamanho do corpus de docs

27. `docs/*.md` + `README.md` + `.cursorrules` = **143.091 caracteres**
    (~36k tokens).
28. `README.md` sozinho = **28.269 caracteres** (534 linhas) — o maior documento,
    e o primeiro que um agente abre.

---

## 3. A leitura do artigo que origina a proposta

O guia citado é sobre **harness para agentes de código**. O diagrama da §1 lista
oito peças: `contract | context | policy | tools | state | checks | traces |
recovery`. O exemplo de contrato da §2 usa *"tests pass"* e *"screenshots cover
desktop and mobile"*; a ferramenta da §4 é `edit_file` com *"path is inside
allowed workspace"*; o mapa da §3 aponta para `apps/web/`, `services/api/`,
`tests/`.

Aplicado a **este** repositório, isso significa que **o harness já está meio
construído, na forma de documento**:

| Peça (§1) | O que já existe aqui |
|---|---|
| `contract` | `docs/sprintN-handoff.md` — Objetivo · Decisões fechadas (*não reinterpretar*) · Critérios de aceite · Fora de escopo |
| `context` | `PROJECT_BOOTSTRAP.md` (mapa) + handoffs (retrieval) + `.cursorrules` (instruções locais) + docstrings |
| `policy` | `.cursorrules` + lista *"O que não fazer sem pedido explícito"* + gates do CI |
| `tools` | vêm do host do agente (shell, editor, git); o repo **endereça** tool (*"Medir antes de otimizar — a suíte está em `load/locustfile.py`"*) |
| `state` | a cadeia de handoffs; `docs/snapshots/`; `load/results/` |
| `checks` | 162 pytest + vitest + lint + typecheck + build + 2 E2E + Locust |
| `traces` | `docs/evidencia/*.png`, `load/results/*.csv`, `docs/performance.md` |
| `recovery` | *"Duas armadilhas já pagas"*, *"O que a correção NÃO resolveu"*, *"O que continua em aberto"* |

**A leitura alternativa — construir um runtime de agente dentro do produto
(`TaskContract`, `ToolGateway`, `/tasks`, `/runs`, `/approvals`, tabelas
`agent_runs`, dashboard) — foi considerada e descartada.** Motivos: (a) exigiria
introduzir LLM num produto que hoje não tem nenhum, mudando o objeto do TCC; (b)
custaria de 4 a 8 semanas pelo cronograma originalmente proposto; (c) cinco dos
doze itens daquela proposta só teriam objeto depois do runtime existir.

**A proposta abaixo, portanto, não cria runtime.** Ela fecha apenas a **metade
mecânica** e a **coerência** do que já existe como documento.

---

## 4. A proposta

**12 arquivos. Zero dependência nova, zero tabela nova, zero endpoint novo, zero
LLM.**

| # | Level (§16) | Ação | Arquivo |
|---|---|---|---|
| 1 | 1 | criar | `docs/_template-handoff.md` — o contrato da §2, com `→ <comando>` em cada item de aceite |
| 2 | 1 | criar | `docs/harness.md` — a spec da §17, preenchida com os valores deste repo |
| 3 | 4 | criar | `docs/sprint6-handoff.md` (reconstruído) |
| 4 | 4 | criar | `docs/sprint7-handoff.md` (reconstruído) |
| 5 | 2 | criar | `AGENTS.md` (raiz) — o mapa |
| 6 | 2 | criar | `CLAUDE.md` (raiz) — uma linha: `@AGENTS.md` |
| 7 | 2 | criar | `tests/test_docs.py` — sensor de frescor do mapa |
| 8 | 2 | criar | `scripts/preflight.py` — a escada de verificação em um comando |
| 9 | 2 | editar | `docs/PROJECT_BOOTSTRAP.md` — sprints 5/6/7; aponta o handoff ativo |
| 10 | 2 | editar | `.cursorrules` — ponteiro para `@AGENTS.md`; remover a proibição de Redis |
| 11 | 2 | editar | `README.md` — "Sprint 6 (em andamento)" → concluída; corrigir o parágrafo falso sobre Redis |
| 12 | 2 | editar | `docs/tech_spec.md` — corrigir "foram removidos" / "Sem Redis" |

O item **6** (`CLAUDE.md` na raiz) **não é invenção**: é o padrão que o próprio
repo já usa em `web/`, onde `CLAUDE.md` contém `@AGENTS.md`. Custo: 12 caracteres.

O item **1** troca, no handoff, a frase *"`pytest` verde"* por
*"`pytest -q` verde"* — a diferença é que a sessão seguinte **reexecuta** em vez
de acreditar.

### 4.1 `AGENTS.md` (raiz) — texto integral proposto

É o único arquivo carregado em toda sessão. Julgue-o com rigor: ~3,3k caracteres
(~800 tokens).

```markdown
# AGENTS.md — mapa do projeto

**Produto:** marketplace com **Server-Driven UI** sobre o dataset Olist. O backend
(FastAPI) envia uma árvore JSON de blocos (`type`, `version`, `props`, `actions`)
e o front (Next.js) só renderiza e executa ações. Eixo do TCC: **personalização
contextual** + **logística verde** (distância por CEP, selo < 100 km, CO₂).

Este arquivo é só o **mapa**: onde olhar. As regras de código estão em
`.cursorrules` e não são repetidas aqui.

## Mapa — abra só o que a tarefa pede

| Preciso de | Vá para |
|---|---|
| Visão geral, sprints concluídas | `docs/PROJECT_BOOTSTRAP.md` |
| **Tarefa atual (contrato)** | `docs/sprint7-handoff.md` — ou o de **maior N** em `docs/` |
| O contrato SDUI (fonte de verdade) | `src/schemas/sdui.py`; descrição em `docs/tech_spec.md` §2 |
| O espelho do contrato no front | `web/lib/sdui.ts` — escrito **à mão**, sem sensor |
| Latência, N+1, Redis, decisões descartadas | `docs/performance.md` §8–9 |
| Evidência já produzida | `docs/evidencia/`, `load/results/`, `docs/snapshots/` |

**Não leia por padrão** (histórico; só com motivo): `docs/frontend-sprint1.md`,
`docs/frontend-sprint2.md`, `docs/sprint2..6-handoff.md`, `docs/performance.md` §1–7.

## Comandos

| Quero | Comando |
|---|---|
| Subir a pilha | `docker compose up -d` |
| Carregar a amostra | `python -m scripts.etl_load_sample` |
| Subir a API | `uvicorn src.main:app --reload` |
| Escada de verificação | `python -m scripts.preflight` |
| Jornada real (exige pilha) | `cd web && npm run e2e` |

## Frescor

- O handoff da tarefa é o de **maior N** em `docs/`. Divergiu do disco? O mapa é
  que está errado. `tests/test_docs.py` verifica isto.
- **`web/AGENTS.md` é gerado por `next dev`** — não escreva nele. Regra de
  frontend vai para este arquivo.
- Não use transcripts antigos como especificação.

## Fronteiras — não altere sem pedido explícito

`data/raw/*` · `load/results/*` · `docs/evidencia/*` · `docs/snapshots/*` ·
`.github/workflows/*` · `src/core/cache.py`

São dado bruto ou evidência: reescrever apaga a prova.

## O que NÃO fazer (além da lista do bootstrap)

- **Não existe LLM no produto.** Não introduza runtime de agente — `/tasks`,
  `/runs`, `/approvals`, `ToolGateway`, tabelas `agent_runs`/`run_state`. Este
  harness governa os agentes que trabalham **no repositório**; o produto é um
  marketplace SDUI.
- **Docs são estado, não especificação.** O contrato é `src/schemas/sdui.py`.
  Não "conserte" o código para bater com um doc — escolha um e diga qual.
- **Não expanda o harness além do que serve a próxima entrega.** Doc novo sem
  sensor que o verifique é dívida, não governança.
```

As **três últimas linhas** são, em ordem, as respostas aos três riscos discutidos:
divergência de escopo, alucinação por doc obsoleto, e desvio de foco para o
harness. Estão dentro do artefato — e não na conversa — para sobreviverem entre
sessões.

### 4.2 `docs/harness.md` — as 8 seções da §17

Esqueleto com os valores **deste** repo. Não é novo conteúdo: é o que já está nos
docs, reunido e verificável num só lugar.

```markdown
# Harness do projeto

Preenchimento da §17 do guia ("A Reusable Harness Specification"). Não governa
um agente no produto — governa os agentes que trabalham neste repositório.

## 1. CONTRACT
- Fonte: `docs/sprintN-handoff.md`, o de maior N. Molde: `docs/_template-handoff.md`
- Um contrato responde: objetivo · escopo · restrições · aprovação humana · evidência
- "Evidence" são comandos, não afirmações.

## 2. CONTEXT
- **always-loaded:** `AGENTS.md` (mapa) + `.cursorrules` (regras)
- **retrieval:** `docs/PROJECT_BOOTSTRAP.md`, `docs/tech_spec.md`, `src/schemas/sdui.py`
- **local instructions:** docstrings (co2, locustfile, snapshot_api, playwright.config)
- **freshness:** handoff de maior N; `tests/test_docs.py` verifica
- **não carregar:** docs históricos e `performance.md` §1–7 (ver AGENTS.md)

## 3. TOOLS
- Fornecidas pelo host (shell, editor, git). O repo não as define.
- O que o repo faz: **endereçar** a certa — cada verificação tem entrada em
  `AGENTS.md` → Comandos, e `scripts/preflight.py` roda a escada.
- Fronteiras de path: ver "Fronteiras" em `AGENTS.md`.

## 4. STATE
- Fatos e decisões: handoffs. Lições: seções "Falhas encontradas" + bootstrap
- Checkpoint: `docs/snapshots/` (diff de API) e `load/results/` (medidas)
- Lacuna conhecida: `docs/snapshots/depois.json` nunca foi gerado.

## 5. POLICY
- Automático: editar código, rodar testes, ler qualquer arquivo
- **Aprovação humana:** dataset completo · pagamento real · PostGIS · Redis como
  arquitetura · `--workers` em produção · substituir uma medição do
  `performance.md`
- Proibido: alterar `data/raw/`, `load/results/`, `docs/evidencia/`,
  `docs/snapshots/`, `.github/workflows/` sem pedido

## 6. VERIFICATION
- **Determinístico:** pytest · vitest · lint · typecheck · build · 2 E2E · Locust
- **Adversarial:** `contract-mutation.spec.ts` (muta a resposta real do servidor)
- **Regra de aceite:** vermelho bloqueia. "Verde" só vale com o comando anexado.
- Buracos declarados: contrato sdui.ts↔sdui.py sem sensor; nenhum teste toca SQL;
  E2E e Locust fora do CI (`data/raw/` gitignored)

## 7. RECOVERY
- Classes: teste falhando · typecheck/lint · regressão de resposta (snapshot) ·
  medição contradizendo afirmação
- Toda falha recorrente tem de terminar em **sensor** ou em **seção de doc** —
  não pode ficar só na prosa. É o que produziu "Duas armadilhas já pagas".

## 8. OBSERVABILITY
- Artefatos: `docs/evidencia/*.png` · `load/results/*_stats.csv` ·
  `docs/performance.md` (com metodologia, ambiente e confundidores)
- métrica útil (§18): trabalho aceito por minuto de revisão humana. Não medido.
- O que este repo já faz de exemplar: **registrar o próprio confundidor e
  retratar conclusões** (`performance.md` §9).
```

### 4.3 `docs/_template-handoff.md` — o molde que falta

```markdown
# Handoff — Sprint N: <título>

> **Para agentes sem contexto:** leia `AGENTS.md` primeiro (mapa), depois este arquivo.

## Contrato

| Campo | |
|---|---|
| **Objetivo** | o que tem de existir ao final |
| **Escopo** | o que pode ser tocado — por caminho |
| **Restrições** | o que NÃO pode mudar |
| **Aprovação humana** | o que exige pedido explícito |
| **Evidência** | como se prova que ficou pronto — **cada item nomeia o COMANDO** |

## Decisões fechadas (não reinterpretar)

| Tópico | Decisão |
|---|---|

## Evidência de conclusão

- [ ] <afirmação verificável> → `<comando que prova>`

## Fora de escopo

## Falhas encontradas e o que virou regra

| Falha | Virou |
|---|---|
| <o que quebrou> | `<teste novo>` ou `<seção no AGENTS.md>` |
```

A última seção é o *flywheel* da §16 (*"harness updates from recurring failures"*):
obriga a segunda metade — falha registrada tem de virar sensor ou regra.

### 4.4 Handoffs 6 e 7 — os fatos, com a fonte na mesma linha

**Este é o artefato de maior risco** de alucinação da proposta: os handoffs são
**reconstruídos** de artefatos (git, `performance.md`, `load/results/`,
docstrings), não escritos durante o sprint. Por isso cada fato carrega a fonte ao
lado, e o cabeçalho declarará que é reconstrução. Um handoff errado é pior que
nenhum, porque parece autoritativo — **se você desconfiar de qualquer linha,
rejeite-a e eu verifico contra o artefato citado.**

**Fronteira adotada** (confirmada pelo autor): Sprint 6 termina em `f6c052d`;
Sprint 7 = `7697552` → `d9b966b` (13 commits).

#### Sprint 6 — "o N+1 e a primeira medição"

| Fato | Fonte |
|---|---|
| Remessas ordenadas por **emissão decrescente** | `8d0fe15`; `README.md` §Sprint 6 |
| `alternatives[]`: mesma categoria em vendedor mais próximo, com `co2_saved_kg`; ranking por **economia de CO₂** | `8d0fe15`; `src/features/checkout/alternatives.py` |
| Carrinho persistido em **`localStorage`**; a `checkoutAction` **não** é persistida (relida por `findCheckoutAction`) | `59cf745`; `README.md` §Frontend |
| **Modo de inspeção SDUI** — no wrapper `<Block>`, expõe envelope + JSON; bloco sem renderer aparece em vermelho | `7656260`; `README.md` |
| **`product_detail`** server-driven (`GET /products/{id}`); a tela de detalhe **deixou de ser montada pelo cliente** | `c7735d8`; `docs/tech_spec.md` |
| `rating`/`review_count` **reais** de `olist_order_reviews` (6.528/6.575 com avaliação) | `README.md` §Detalhe |
| `open_modal` **deixa de ter emissor** (tipo permanece no contrato) | `docs/tech_spec.md` |
| **E2E Playwright** da jornada; porta 3100; `localhost` e não `127.0.0.1` | `f62f52c`; `web/playwright.config.ts` |
| **Medição com Locust** — a meta de 200 ms não era cumprida e o motivo não era cache | `68b200b`; `performance.md` §2 |
| **Diagnóstico:** 63 queries/requisição; metade repetindo o CEP do comprador | `performance.md` §3 |
| **Memo por requisição** — `conscious_buyer` 150 → 63 ms | `c649eae`; `performance.md` §6 |
| **`cep_centroids` em memória** — 63 → 2 queries; 150 → 12 ms (1 usuário) | `056a23b`; `performance.md` §7 |
| **50 usuários: o limite passa a ser o worker único** — `--workers 4`: p50 940 → 58 ms | `performance.md` §7 |
| **Redis removido do código** — decisão por inferência | `f6c052d` |
| `npm run lint` entra no CI (estava vermelho sem ninguém ver) | `README.md` §Sprint 6 |
| `next typegen` antes do `tsc` | `c3a9b6f` |

**Inferência minha, não fato:** as três sugestões finais do handoff da Sprint 5
(ordenar o carrinho por pegada, persistir o carrinho, E2E Playwright) foram
**todas entregues** na 6 — o que mostraria o *steering loop* funcionando. Deduzido
de comparar os dois documentos.

#### Sprint 7 — "fidelidade e validade"

| Fato | Fonte |
|---|---|
| Vitrine trocava de produtos a cada recarga do ETL | `7697552` |
| **`offers`** derivada de `order_items`; home, detalhe e checkout passam a lê-la | `79970c3`, `e528274` |
| **ETL completava ofertas**: amostragem crua escondia **474 casos** de mesmo produto com vendedores distantes | `428118a`; `README.md` §Demo multi-vendedor |
| Par de demo: Recife/PE ↔ Maringá/PR, **2.483 km**, mesmo preço | `README.md` |
| "Mesmo produto, vendedor mais próximo" | `9fb08b6` |
| Selo **não afirma** "0 km" nem "0,00 g CO₂" | `b87acc1` |
| **Mutação de contrato SDUI** — objetivo (d), metade "flexibilidade" | `6856b1e`; `web/e2e/contract-mutation.spec.ts` |
| Evidência visual das 4 mutações | `docs/evidencia/*.png` |
| **Prazo medido** (`ETA_BANDS`) substitui o arbitrado: <50 km 4,9 d … >1.200 km 17,2 d; mediana de **95.921** entregas | `a3a4b16`; `README.md` §Prazo |
| `base_days`/`km_per_day` extintos → um `eta_factor` por modalidade (express 0,5 · standard 1,0 · green 1,5) | `docs/sprint4-handoff.md`; `delivery_options.py` |
| **Peso cubado** entra no CO₂ (6.000 cm³ = 1 kg): 66,7% dos produtos com cubado > real; agregado 1,41× | `98807f9`; `co2.chargeable_weight_g` (GLEC/ISO 14083) |
| **A correção AUMENTA a emissão** — números anteriores subestimavam | `README.md` §Peso cubado |
| Locust: **CEPs reais** (53.114 clientes, 12.809 prefixos) em vez de 2 fixos | `b3dc39c`; `load/locustfile.py` |
| `wait_time` 0,5–2,0 s → **`between(1, 3)`**, alinhado à §3.3 da metodologia | idem |
| Cada VU **mantém o CEP** pela jornada → chaves ativas ≈ nº de VUs | idem |
| Linha de base: p50 **16 ms**, p95 140, p99 470; **0 falhas em 1.490** | `performance.md` §8 |
| **O selo não custa nada** (14 ms com × 15 ms sem) | `performance.md` §8 |
| **54%** das requisições sem selo — a maioria não tem vendedor próximo na amostra | `performance.md` §8 |
| **`echo` do SQLAlchemy estava ligado em TODAS as medições anteriores** | `performance.md` §9; `src/core/database.py` |
| **Redis volta como variável de experimento** (`CACHE_ENABLED=false`) | `2319bde`; `src/core/cache.py` |
| Sondagem limpa: p50 14 → **7 ms**; acerto **77,2%**; controle `/products` e `/checkout` não se moveram | `performance.md` §9 |
| **1 ensaio não decide a cauda** — duas execuções de "off" deram p95 140 e 210 ms | `performance.md` §9 |
| `list_known_prefixes` ganha 0,54 ms/requisição (fazia `set()` de 12.809 strings) | `770b9d8`; `performance.md` §9 |
| `docs/Plano Mestre de Engenharia.docx` removido | `d9b966b` |

**Pendência registrada, não consertada nesta proposta:** `scripts/snapshot_api.py`
prescreve um diff de API antes/depois para provar equivalência; `antes.json`
existe e **`depois.json` nunca foi gerado**.

---

## 5. Riscos — auto-crítica explícita

Numerados para você poder rejeitar por número.

1. ***Harness railroading*** — o agente passa a otimizar docs e testes em vez do
   produto, porque o harness virou o assunto visível do repo.
   *Defesa proposta:* `AGENTS.md` abre com o produto (não com o harness) e fecha
   com *"não expanda o harness além do que serve à próxima entrega"*.
2. **Doc virando especificação** — o agente "conserta" o código para bater com um
   documento, criando divergência real.
   *Defesa:* *"docs são estado, não spec; o contrato é `src/schemas/sdui.py`"*.
3. **Reconstrução alucinada** — os handoffs 6 e 7 são reconstruídos de artefatos
   (ver 4.4). Um handoff errado parece autoritativo.
   *Defesa:* fonte na mesma linha + cabeçalho declarando reconstrução. **Ainda é o
   item de maior risco da proposta.**
4. **Custo de token** — medido: corpus de docs **+27%** (143k → ~182k chars);
   carregado por sessão **+~800 tokens** (hoje: 0, porque não há arquivo na raiz).
   *Contrapartida:* o mapa manda **não** ler ~35k chars de docs históricos.
   *Crítica contra mim mesmo:* o `README.md` (28k chars) é o maior doc e o primeiro
   que um agente abre; a proposta só faz 3 edições nele. **Se o gargalo de token
   for o README, esta proposta está incompleta** — e essa é uma conclusão válida.
5. **Acoplamento docs↔build** — `tests/test_docs.py` no CI pode reprovar um PR de
   código por motivo de documentação.
   *Decisão aberta:* rodar no CI (bloqueia) ou só reportar. Peço sua opinião.
6. **Contra-argumento geral** — é um TCC com prazo de entrega; cada hora de harness
   é uma hora que não é SDUI. As falhas recorrentes (N+1, `0,00 kg CO₂`, `echo`
   ligado, 2 CEPs fixos) custaram **tempo e afirmações retratadas**, não código
   quebrado. **"Faça só o Level 2 e pare" é uma conclusão defensável**; o autor do
   plano concorda que é.

---

## 6. O que a proposta NÃO faz

- Não cria `/tasks`, `/runs`, `/approvals`, `ToolGateway`, dashboard, nem tabelas
  `agent_runs`/`run_state` — é a leitura alternativa, descartada na seção 3.
- **Não toca Redis no código.** `src/core/cache.py` fica intacto; apenas a
  documentação para de afirmar que ele foi removido.
- Não gera o `depois.json` pendente (vira fato registrado, não conserto).
- Não amplia o ETL, não adota PostGIS, não põe E2E/Locust no CI.
- Não cria sensor para o contrato `sdui.ts` ↔ `sdui.py` (Level 5, próxima rodada).
- Não altera `data/raw/`, `load/results/`, `docs/evidencia/`, `docs/snapshots/`.

---

## 7. Veredito pedido

**Para cada um dos 12 itens da seção 4:**
`ACEITAR` / `REJEITAR` / `ACEITAR COM MUDANÇA` + uma linha de motivo.

**Depois, responda:**

1. O `AGENTS.md` proposto (4.1) induz o modelo a divergir do plano principal
   (marketplace com SDUI)? **Onde, exatamente no texto?**
2. Ele reduz ou aumenta o gasto de token por sessão? Qual item é o mais caro?
3. Há risco de o agente otimizar o harness em vez do produto? **Qual linha do
   texto piora isso?**
4. Algum item é redundante com o que já existe no repo?
5. Qual é o menor subconjunto que ainda entrega valor? (O plano afirma que "só o
   Level 2" é defensável — concorda?)
6. O que está **faltando** para o objetivo (d) da tese — provar que o cliente
   renderiza por contrato, sem rebuild?
7. Quais das linhas da seção 4.4 você considera não confiáveis?

---

## Apêndice — como conferir cada afirmação

Os comandos que produziram a seção 2, para verificação em um passo em vez de
varredura. Raiz do repo, PowerShell.

| Seção | Comando |
|---|---|
| 2.1 (1) | `(Select-String -Path tests/*.py -Pattern '^\s*(async )?def test_' -AllMatches).Matches.Count` |
| 2.1 (2) | `Select-String -Path web/tests/*.tsx -Pattern '\b(it\|test)\(' -AllMatches` |
| 2.2 (6,7,8) | `Get-Content src/schemas/sdui.py` e `Get-Content web/lib/sdui.ts` |
| 2.2 (9,10) | `Get-Content web/e2e/contract-mutation.spec.ts -TotalCount 46` |
| 2.3 (11) | `Get-Content .github/workflows/ci.yml` |
| 2.3 (13) | `Get-ChildItem docs/snapshots` |
| 2.4 (14) | `Select-String -Path README.md -Pattern 'Redis'` |
| 2.4 (15) | `Get-Content src/core/cache.py`; `Select-String -Path requirements.txt -Pattern redis` |
| 2.4 (17) | `Select-String -Path .cursorrules -Pattern Redis` |
| 2.5 (19,20) | `Select-String -Path docs/PROJECT_BOOTSTRAP.md,README.md -Pattern 'Sprint ativa\|em andamento'` |
| 2.5 (21) | `Get-ChildItem docs -Filter 'sprint*-handoff.md'` |
| 2.6 (26) | `Test-Path CLAUDE.md` |
| 2.7 (27) | `(Get-ChildItem docs/*.md,README.md,.cursorrules \| Get-Content -Raw \| Measure-Object -Character).Characters` |
| 4.4 | `git --no-pager log --oneline -40` |
| Fronteira | `git --no-pager log --oneline -S'chargeable_weight' -- src/` |

---

*Documento gerado para revisão. Nada aqui foi implementado.*