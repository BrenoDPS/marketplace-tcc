# Olist SDUI Marketplace

Marketplace contextual adaptativo com Server-Driven UI, baseado no dataset real da Olist.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

> `pandas` e `psycopg` sao usados **somente** pelo script ETL offline; o runtime da API permanece async (SQLAlchemy + asyncpg).

## Documentacao

| Arquivo | Conteudo |
|---------|----------|
| [AGENTS.md](AGENTS.md) | Mapa e regras de implementacao para agentes (Cursor, Claude Code via `CLAUDE.md`) |
| [docs/PROJECT_BOOTSTRAP.md](docs/PROJECT_BOOTSTRAP.md) | Visao geral para agentes/conversas novas |
| [docs/tese-rastreabilidade.md](docs/tese-rastreabilidade.md) | **Defesa:** o que a metodologia promete, o teste que prova e o que mudou em relacao ao estabelecido |
| [docs/sprint9-handoff.md](docs/sprint9-handoff.md) | **Sprint 9 (atual):** resultados dos dois eixos da tese, ate 14/10 |
| [docs/sprint8-handoff.md](docs/sprint8-handoff.md) | Sprint 8 (historico): protocolo de carga da §3.3 |
| [docs/sprint5-handoff.md](docs/sprint5-handoff.md) | Sprint 5 (historico) — sprints 6 e 7 nao tem handoff; ver secoes abaixo |
| [docs/sprint4-handoff.md](docs/sprint4-handoff.md) | Sprint 4 (historico) |
| [docs/sprint3-handoff.md](docs/sprint3-handoff.md) | Sprint 3 (historico) |
| [docs/sprint2-handoff.md](docs/sprint2-handoff.md) | Sprint 2 (historico) |
| [docs/frontend-sprint2.md](docs/frontend-sprint2.md) | Guia de consumo da API (historico da Sprint 2, com notas do que mudou ate hoje) |
| [docs/tech_spec.md](docs/tech_spec.md) | Contrato SDUI e logistica verde |
| [docs/performance.md](docs/performance.md) | **Medicao de latencia:** o N+1, o protocolo de carga da §3.3 (27 ensaios) e por que o Redis ficou ligado |

## Fluxo completo (Sprint 2+)

Sequencia recomendada para subir do zero:

```bash
# 1. Subir o Postgres (porta 5433 externa para nao colidir com Postgres nativo do Windows)
docker compose up -d

# 2. Carregar amostra (~10000 order_items, seed=42). Os CSVs do Olist
#    devem estar em data/raw/ (nao versionados).
python -m scripts.etl_load_sample
#    Recarregou o ETL com a API no ar? Esvazie o cache (TTL de 1 h):
#    docker exec olist-redis redis-cli FLUSHALL

# 3. Subir a API
uvicorn src.main:app --reload
```

Acesse a documentacao interativa em **http://localhost:8000/docs**.

## Demo

Apos o ETL, o script imprime no console um par `(customer_zip_prefix, seller_zip_prefix)` com distancia < 100 km, util para testar o selo de Logistica Verde.

Par de demo conhecido (amostra padrao, `seed=42`): `customer_zip_prefix=05311` (Sao Paulo, SP), seller correspondente em `08275` — distancia Haversine ~27 km, **badge presente**.

### Demo multi-vendedor

O ETL tambem imprime o melhor caso de **mesmo produto vendido por vendedores distantes** — a comparacao que sustenta o argumento de logistica verde. Na amostra padrao:

| | |
|---|---|
| `product_id` | `909b87db6cb3a7ab26bd03cc59860136` |
| vendedor A | Recife/PE (`51250`) — R$ 39,90 |
| vendedor B | Maringa/PR (`87050`) — R$ 39,90 |
| separacao | **2.483 km** |

**Mesmo item, mesmo preco, origens a 2.483 km uma da outra.** Preco nao e variavel de confusao aqui: a unica coisa que muda entre as duas opcoes e a distancia — e, portanto, a emissao.

Esse caso so existe porque o ETL **completa as ofertas** dos produtos sorteados. A amostragem crua por linha trazia produto pela metade e escondia 474 casos como este; ver `sample_order_items` em `scripts/etl_load_sample.py`.

```bash
# Badge presente em pelo menos um ProductCard (vendedor proximo)
# O label inclui o CO2 estimado quando o produto tem peso. A unidade e
# escolhida por `format_co2` (g abaixo de 10 g, kg acima):
#   "Entrega local (~21 km · ~4,14 g CO₂)"
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&context=electronics_expert"

# Badge null em todos os cards (cliente em Fortaleza/CE, sellers da amostra em SP/SE)
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=60165&context=default"

# 422 quando o prefixo nao existe na amostra
curl -i "http://localhost:8000/api/v1/home?customer_zip_prefix=00000"

# Home consumidor consciente: produtos ordenados por proximidade (mais perto primeiro)
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&context=conscious_buyer"
```

### Detalhe do produto (Sprint 6)

`GET /api/v1/products/{product_id}?customer_zip_prefix=...` retorna uma tela SDUI
(`product_detail` + `impact_banner`). Ate a Sprint 5 o detalhe era a **unica**
tela montada pelo cliente, reaproveitando os props do `product_card` — uma
excecao a tese do trabalho, agora fechada.

```bash
# Detalhe (o path ja vem pronto na action GET de cada product_card da Home)
curl "http://localhost:8000/api/v1/products/<PRODUCT_ID>?customer_zip_prefix=05311"

# 404 produto inexistente | 422 CEP fora da amostra
curl -i "http://localhost:8000/api/v1/products/inexistente?customer_zip_prefix=05311"
```

> **Nota e vendedor sao dados REAIS, nao mock.** `rating`/`review_count` vem de
> `olist_order_reviews` (agregados no ETL); `seller_city`/`seller_state` de
> `olist_sellers`. Na amostra de 10k, **6.528 dos 6.575 produtos** tem avaliacao.
> Produto sem pedido avaliado vem com `rating: null` e a tela **omite** o campo.
>
> **Descricao e tags de sustentabilidade ficaram de fora**: o Olist tem apenas o
> *comprimento* da descricao (`product_description_lenght`), nao o texto, e nao
> tem nenhuma tag. Inventar isso numa tela cujo assunto e credibilidade
> ambiental seria o pior lugar possivel para dado fabricado.

### Busca e categorias (Sprint 5)

`GET /api/v1/home` aceita `q` (busca) e `category` (filtro exato). Toda resposta
traz o bloco `category_grid` com as 12 maiores categorias da amostra e a
contagem de produtos de cada uma.

> **A busca e sobre o nome da categoria, nao sobre o produto.** O Olist nao tem
> nome de produto: `product_category_name` e o unico campo textual, e o `title`
> que aparece no card ja e essa categoria formatada. Nao existe "fone bluetooth"
> em lugar nenhum da amostra para casar.

```bash
# Busca ignora acento e caixa: encontra informatica_acessorios
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&q=INFORM%C3%81TICA"

# Filtro exato por categoria (slug do dataset)
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&category=bebes"

# Filtro + contexto compoem: produtos de bebe ordenados por proximidade
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&category=bebes&context=conscious_buyer"

# 422 quando a categoria nao existe na amostra
curl -i "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&category=nao_existe"
```

> Filtro que nao casa devolve vitrine **vazia**, com o hero dizendo "Nenhum
> produto encontrado". So a categoria inferida do `context` (heuristica nossa)
> cai para a vitrine geral quando nao rende produtos — quem buscou algo
> especifico precisa saber que nao achou, nao receber produtos aleatorios.

### Checkout simulado (Sprint 3+)

`POST /api/v1/checkout/simulate` recebe um **carrinho** e retorna uma tela SDUI
com `checkout_summary` (linhas, subtotal, frete, total), `delivery_options`
(comparativo de modalidades), `shipment_breakdown` (uma remessa por vendedor) e
`impact_banner` (agregado). Sem pagamento, estoque ou persistencia de pedido.
Os `product_id` devem ser ids reais retornados pela Home.

| Campo | Regras |
|-------|--------|
| `customer_zip_prefix` | Obrigatorio; deve existir em `cep_centroids` → **422** se invalido |
| `items` | Obrigatorio; lista de 1 a 20 `{product_id, quantity}`. Produto ausente da amostra → **404** |
| `items[].quantity` | Opcional, default `1`, inteiro >= 1 |
| `delivery_option` | Opcional; `express`, `standard` (default) ou `green` → **422** se invalido |

```bash
# Um item (substitua <PRODUCT_ID> por um id retornado na Home)
curl -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","items":[{"product_id":"<PRODUCT_ID>","quantity":1}]}'

# Carrinho com varios itens: uma remessa por vendedor
curl -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","items":[{"product_id":"<ID_A>","quantity":2},{"product_id":"<ID_B>"}]}'

# Mesmo carrinho na modalidade verde: frete e CO2 menores, prazo maior
curl -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","items":[{"product_id":"<PRODUCT_ID>"}],"delivery_option":"green"}'

# 422 quando o customer_zip_prefix nao existe em cep_centroids
curl -i -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"00000","items":[{"product_id":"<PRODUCT_ID>"}]}'

# 404 quando algum product_id nao existe na amostra (o detail lista quais)
curl -i -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","items":[{"product_id":"inexistente"}]}'

# 422 quando a modalidade nao existe (o detail lista as validas)
curl -i -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","items":[{"product_id":"<PRODUCT_ID>"}],"delivery_option":"teleporte"}'
```

> **Uma remessa por vendedor.** Itens do mesmo vendedor pagam **um** frete, o
> maior da remessa. **A emissao nao cai por agrupar** — ela e proporcional a
> massa e a distancia, entao consolidar economiza frete, nao CO2. O que o
> carrinho revela e o `co2_share`: qual vendedor domina a pegada. Num carrinho
> de 3 itens, a remessa a 79 km respondeu por 75% do CO2 total.

> **Sugestao de troca (Sprint 6).** As remessas vem ordenadas por emissao
> decrescente e a primeira traz `alternatives`: produtos da **mesma categoria**
> em vendedores mais proximos, com o CO2 economizado. Nao e o mesmo produto em
> outro vendedor — o Olist nao tem catalogo compartilhado entre sellers —, por
> isso a tela mostra preco e distancia do substituto e a decisao e do usuario.
> O ranking pesa **distancia e massa juntas**: um vendedor mais perto com
> produto mais pesado pode emitir mais.

> **Decisao (handoff ambiguo "404 ou 422"):** produto inexistente retorna
> **404** (recurso nao encontrado); `customer_zip_prefix` invalido retorna
> **422** (entrada que nao casa com `cep_centroids`), consistente com `GET /home`.
> O frete base e o `freight_value` da primeira linha de `order_items` daquele
> `product_id` na amostra.

> **Modalidade escolhida manda em tres numeros ao mesmo tempo:** frete, CO2 do
> `impact_banner` e CO2 do label do selo saem todos do mesmo `mode`. Se forem
> calculados em lugares diferentes a tela passa a se contradizer — selo dizendo
> um valor, comparativo dizendo outro.

### CORS (desenvolvimento)

Quando `APP_ENV=development` (padrao em `.env`), a API habilita CORS para as
origens locais `http://localhost:5173`, `http://127.0.0.1:5173` e
`http://localhost:3000` (Vite/React). Em producao o CORS permissivo fica
desabilitado.

## Frontend (`web/`)

App Next.js (App Router) que consome o contrato SDUI. Sobe **depois** da API:

```bash
cd web
npm install
npm run dev        # http://localhost:3000
```

Abra `http://localhost:3000` — a tela inicial pede o CEP; ou va direto:
`http://localhost:3000/?customer_zip_prefix=05311&context=conscious_buyer`.

| Arquivo | Responsabilidade |
|---------|------------------|
| `web/lib/sdui.ts` | Espelho TypeScript de `src/schemas/sdui.py`, mantido a mao |
| `web/lib/api.ts` | Fetch da Home em Server Component (`API_BASE_URL`, default `127.0.0.1:8000`) |
| `web/components/sdui.tsx` | `REGISTRY` de `component.type` -> componente React + modais |
| `web/components/sdui-context.tsx` | Executor de `actions` (`navigate` / `open_modal` / `api_call`) |
| `web/components/blocks.tsx` | Um componente por bloco SDUI |

### Modo de inspeção SDUI

O botao **SDUI** no header liga o modo de inspecao: cada bloco de `components[]`
ganha um contorno e uma etiqueta com `type`, `version` e quantidade de `actions`,
clicavel para ver o **JSON exato que o servidor mandou**. No topo aparecem os
metadados da `ScreenResponse` (`screen_id`, `context`, `schema_version`) e a
sequencia de blocos.

Funciona tambem dentro do modal de checkout, que e outra `ScreenResponse` — util
para mostrar que sao duas telas compostas pelo servidor, nao uma SPA montando
tudo no cliente.

Um bloco de tipo desconhecido, que fora da inspecao some em silencio, aparece em
vermelho: e a degradacao graciosa ficando visivel.

Pontos que economizam tempo de quem for mexer:

- **Bloco novo no backend = uma linha no `REGISTRY`.** Tipo desconhecido renderiza `null` de proposito: a tela degrada em vez de quebrar.
- **A busca usa `next/form`** (`action="/"`, GET): os campos viram query string, a navegacao e client-side e o formulario continua funcionando sem JS. Nao trocar por `onSubmit` + `router.push` sem motivo.
- **Sem CORS em dev:** `web/next.config.ts` faz rewrite de `/api/v1/*` para a API, entao o fetch do browser sai da mesma origem.
- **Fontes sao self-hosted via `@fontsource`**, nao `next/font/google` — `fonts.googleapis.com` e instavel/bloqueado em algumas redes e o build quebra sem mensagem obvia. Nao trocar sem saber disso.
- **O carrinho e estado do cliente** (`sdui-context.tsx`), nao do servidor: o `api_call` de checkout envia a lista de itens. Persiste em `localStorage`, com o conteudo **validado item a item** na leitura — storage sobrevive a deploys e pode ter o formato de uma versao antiga.
- **A `checkoutAction` NAO e persistida**, de proposito: ela vem do servidor a cada carga e pode mudar entre versoes do contrato. Apos um F5 ela e relida da tela por `findCheckoutAction`, senao o carrinho restaurado ficaria sem como fechar a compra.

## Testes

```bash
# Backend
pytest

# Frontend
cd web && npm test        # Vitest (use `npm run test:watch` para watch)
cd web && npm run typecheck
```

Os testes de backend nao dependem de Postgres rodando (uso de `app.dependency_overrides` + monkeypatch nos repositorios). Os de frontend cobrem as duas pecas com logica nao trivial — o executor de `actions` e o `ScreenRenderer` —; o resto e apresentacao e nao ganha teste de proposito.

### Carga — a medicao de latencia

```bash
pip install locust==2.46.5
uvicorn src.main:app --port 8000   # SEM --reload (file-watcher); SQL_ECHO fica desligado (padrao)
locust -f load/locustfile.py --headless -u 50 -r 10 -t 45s --host http://127.0.0.1:8000
```

Percorre a jornada da defesa sob concorrencia, contra a pilha real. O diagnostico
foi um N+1: o `conscious_buyer` fazia **63 idas ao banco para montar 6 cards**,
metade pedindo o mesmo CEP do comprador.

**Corrigido.** `cep_centroids` (6403 linhas, ~1,1 MB) vive em memoria no processo,
e o mesmo `dict` serve `get_centroid` e `list_known_prefixes`:

```
conscious_buyer      63 -> 2 queries     150 ms -> 12 ms  (1 usuario)
p50 agregado, 25 usuarios                 270 ms -> 39 ms
```

**A meta de TTFB < 200 ms passa a ser cumprida ate 25 usuarios.** A 50 o limite
deixa de ser o banco e vira o worker unico: so trocando para `--workers 4`, o p50
cai de 940 ms para 58 ms. Numeros completos em
[docs/performance.md](docs/performance.md).

> **Sprint 7 — validade da medicao.** Ate aqui o `locustfile` usava **dois CEPs
> fixos** e think time de 0,5 a 2,0 s. Com duas chaves, qualquer condicao de
> "cache aquecido" teria ~100% de acerto **por construcao**; e o think time nao
> batia com os 1 a 3 s declarados na metodologia. Os CEPs agora saem de
> `olist_customers` na proporcao real (53.114 clientes, 12.809 prefixos), cada
> usuario virtual mantem o seu pela jornada, e `wait_time` e `between(1, 3)`.
> Linha de base nova: **p50 16 ms, p95 140 ms, p99 470 ms** a 50 VU — ainda com
> o `echo` do SQLAlchemy ligado; a linha de base limpa (p50 14, p95 210, p99
> 650 ms) esta na secao do Redis abaixo.
>
> Dois achados: montar o selo **nao custa nada** (14 ms com selo contra 15 ms
> sem — ruido), e **54%** das requisicoes cairam no perfil sem selo, ou seja, com
> a distribuicao real de clientes a maioria dos compradores nao tem vendedor
> proximo na amostra.

### Redis — ligado por padrao desde a Sprint 8

**Ligado por padrao** (`CACHE_ENABLED=true`, TTL de 1 h, pool bloqueante de 100
conexoes com espera de 5 s). Para medir sem cache: `CACHE_ENABLED=false`. A
historia de como se chegou aqui:

Na Sprint 6, `docs/performance.md` §7 concluiu contra o Redis **sem
nunca ter rodado Redis**, por inferencia sobre o gargalo medido. A secao 3.3 da
metodologia promete tres condicoes de cache, entao ele entra como variavel:

```bash
docker compose up -d redis
docker exec olist-redis redis-cli FLUSHALL        # condicao "frio"
CACHE_ENABLED=true uvicorn src.main:app --port 8000
```

Frio e aquecido **nao sao modos de codigo** — sao procedimento de ensaio. Tres
modos no codigo seriam complexidade inventada para um estado que o `redis-cli`
resolve em uma linha.

Sondagem de 1 ensaio de 60 s por condicao (**nao** o protocolo dos 27):

```
                off      frio
p50 agregado   14 ms     7 ms
p95 agregado  210 ms    75 ms
p99 agregado  650 ms   400 ms
taxa de acerto    —     77,2%
```

Controle interno: `/products/{id}` e `/checkout` nao passam pelo cache e nao se
moveram (8->7 e 20->18 ms) — a queda das rotas de Home e o cache, nao deriva.

**Um ensaio por condicao nao decide a cauda**: duas execucoes da MESMA condicao
"off" deram p95 de 140 e 210 ms. A mediana e estavel entre execucoes, a cauda
nao. A decisao sobre Redis fica pendente dos 27 ensaios do protocolo.

**Protocolo executado (Sprint 8, 27 ensaios, n = 3):** em carga nominal (50 VU) a
meta e cumprida com ou sem cache; a 250 VU, so com cache (p95 613 ms sem, 25-29 ms
com); a 1.000 VU o sistema satura nas tres condicoes, mas o cache multiplica a vazao
por 2,6 e mantem a Home dentro da meta (p95 190-200 ms). Ver
[docs/performance.md](docs/performance.md) §11.

Fora do CI pelo mesmo motivo do E2E: `data/raw/` e gitignored.

### E2E — o check de pre-defesa

```bash
cd web && npm run e2e
```

Um unico teste Playwright percorre a jornada da apresentacao: CEP -> busca ->
categoria -> detalhe do produto -> carrinho -> simular compra -> trocar
modalidade e conferir que **frete, CO2 e selo se movem juntos, e na direcao
certa** (verde e mais barato e menos emissivo que padrao; expressa, o oposto).

Diferente do resto da suite, ele roda contra a **pilha real** — Postgres, ETL
carregado e `uvicorn` no ar. Um mock responderia outra pergunta; esta responde
"a demo ainda funciona?". Se o backend estiver fora, o teste falha na hora com
o passo a passo para subi-lo, em vez de esperar timeout.

O Playwright sobe o front na **porta 3100** de proposito: a 3000 costuma estar
ocupada por outro app na maquina, o Next cai para a 3001 em silencio e o teste
passaria a medir a aplicacao errada.

Duas armadilhas ja pagas, documentadas para nao voltarem:

- **`localhost`, nunca `127.0.0.1`.** O dev server do Next 16 devolve **403 no
  chunk do cliente** para origens que nao reconhece. A pagina e servida e
  parece certa, mas **nao hidrata**: nenhum clique funciona e o erro aparece
  como "botao desabilitado", nao como falha de rede.
- **A tela de entrada e um Client Component:** um `fill` que chega antes da
  hidratacao escreve no DOM e nao no estado do React. O teste repete o
  preenchimento ate o React registrar (`expect(...).toPass()`), em vez de
  dormir um tempo fixo.

### CI

`.github/workflows/ci.yml` roda em push/PR para `main` e `development`: `pytest`
(backend) e `npm run lint` + `npm run typecheck` + `npm test` + `npm run build`
(frontend).

**O E2E nao esta no CI** e nao e um esquecimento: `data/raw/` e gitignored, entao
o runner do GitHub nao tem os CSVs do Olist para popular o banco. Entra quando
existir um fixture de banco semeado.

## Arquitetura (Vertical Slice)

```
src/
  schemas/sdui.py            # Contrato SDUI (envelope + UIAction + ScreenResponse)
  core/
    config.py                # Pydantic settings
    database.py              # AsyncEngine + AsyncSession
    models.py                # Modelos SQLAlchemy 2.0 (Olist + cep_centroids)
  features/
    home_contextual/         # Composicao de tela: hero por contexto + produtos reais
    green_logistics/         # Haversine + centroides CEP + CO2 (FE 0,102) + selo < 100 km
      delivery_options.py    # Sprint 4: modalidades comparaveis (cenario declarado)
    product_detail/          # Sprint 6: GET /products/{id} (tela SDUI de detalhe)
    checkout/                # Sprint 3: checkout simulado (POST /checkout/simulate)
    orchestrator/            # Stub (sprint futura)
scripts/
  etl_load_sample.py         # ETL offline: 10000 order_items + cep_centroids
web/                         # Frontend Next.js (consome o SDUI) — ver secao acima
docker-compose.yml           # Postgres 16 (sem PostGIS nesta sprint) + Redis (cache ligado por padrao)
```

## Logistica Verde

- **Distancia:** Haversine puro em Python sobre centroides por prefixo de CEP (mediana de lat/lng por `geolocation_zip_code_prefix`).
- **Selo:** `SustainabilityProps` no `ProductCard` quando `distance_km < 100`; senao `badge: null`.
- **CO2:** `EMISSION_FACTOR = 0,102` kg CO2/(t.km) (GHG Protocol) em `green_logistics/co2.py`. A emissao acompanha a **massa embarcada**: `quantity` unidades pesam `quantity` vezes mais.
- **Exibicao do CO2:** `format_co2` escolhe a unidade (g abaixo de 10 g, kg acima). Com a amostra de 10k as distancias caem para poucos km e um `.2f` em kg imprimia `0,00 kg` em todo selo — apagando o numero que sustenta o trabalho.
- **Modalidades:** `green_logistics/delivery_options.py`. **Leia o docstring do modulo antes de citar esses numeros no TCC.** Distancia, massa e o FE base sao reais; `standard` usa o frete real da amostra sem fator e o **prazo medido em 95.921 entregas do Olist** (`ETA_BANDS`). Os fatores de preco/emissao/prazo de `express` e `green` sao um **cenario declarado** sobre essa linha de base, nao dado do Olist — o dataset nao tem modalidade nem transportadora. A ressalva viaja no proprio JSON (campo `note`) e e exibida na tela.

### Peso cubado: o que a carga OCUPA, nao o que ela pesa

Ate a Sprint 7 o CO2 saia so da massa (`product_weight_g`). Mas as tres dimensoes do produto estao preenchidas em **100%** dos produtos do Olist e nunca tinham sido usadas — e um veiculo enche por volume antes de atingir o limite de peso quando a carga e leve.

Com o fator de cubagem rodoviario (6.000 cm³ = 1 kg), na amostra carregada:

| | |
|---|---|
| produtos em que o cubado supera o real | **66,7%** |
| razao cubado/real — mediana | 1,44x |
| razao cubado/real — p90 | 4,33x |
| **massa cobravel agregada** | **1,41x a massa real** |

> ⚠️ **A correcao AUMENTA a emissao estimada.** Qualquer numero de CO2 publicado antes desta mudanca subestimava — nao e a mudanca que superestima. Ver `co2.chargeable_weight_g`, que cita GLEC (Smart Freight Centre, 2023) e ISO 14083, ambas ja na bibliografia.

O **peso exibido na tela continua sendo o real**: a cubagem entra no calculo de emissao, nao na ficha do produto. E no checkout ela se aplica a REMESSA (`max(soma_real, soma_cubada)`), nao item a item — somar os `max` cobraria o espaco vazio duas vezes.

### Prazo de entrega: medido, nao arbitrado

Ate a Sprint 7 o prazo saia de `dias_fixos + ceil(distancia / km_por_dia)`, com os dois numeros escolhidos a mao — e subestimava muito. O dataset tem `order_purchase_timestamp` e `order_delivered_customer_date` em 97% dos pedidos, e essa informacao nunca tinha sido usada. Mediana de dias ate a entrega, por faixa de distancia:

| faixa | prazo real (p50) | n |
|---|---|---|
| < 50 km | **4,9 dias** | 11.758 |
| 50–100 km | 5,8 dias | 6.133 |
| 100–300 km | 8,2 dias | 13.340 |
| 300–600 km | 10,3 dias | 31.477 |
| 600–1.200 km | 12,8 dias | 21.019 |
| > 1.200 km | **17,2 dias** | 12.194 |

**Comprar perto e ~3,5x mais rapido.** E um segundo argumento a favor de logistica local, independente de CO2: beneficio direto ao consumidor, medido e nao estimado.

O ETL rederiva a tabela a cada carga e avisa se ela divergir da constante no codigo.

## Sprint 3 (concluida)

Escopo em [docs/sprint3-handoff.md](docs/sprint3-handoff.md):

- CO2 no label do selo (km + kg CO2 quando `weight_g` disponivel)
- Contexto `conscious_buyer` — produtos ordenados por proximidade ao `customer_zip_prefix`
- `POST /api/v1/checkout/simulate` — tela SDUI (`checkout_summary` + `impact_banner`) com frete, distancia, CO2 e selo
- `api_call` (POST `/api/v1/checkout/simulate`) nos `ProductCard` da Home
- CORS habilitado em `APP_ENV=development` (origens Vite/React locais)

Exemplos `curl` na secao [Demo](#demo) acima.

## Sprint 4 (concluida)

Escopo em [docs/sprint4-handoff.md](docs/sprint4-handoff.md):

- Bloco SDUI **`delivery_options`** — comparativo de `express` / `standard` / `green` com preco, prazo e CO2 por modalidade
- `POST /checkout/simulate` aceita `delivery_option`; a escolha recompoe frete, CO2 e selo na mesma tela
- Frontend renderiza o bloco e re-simula pela `action` do proprio bloco (o cliente nao guarda estado de checkout)
- **Correcao:** `format_co2` — todo selo exibia `~0,00 kg CO₂` depois que a amostra subiu para 10k
- **Correcao:** CO2 passa a acompanhar `quantity` (2 unidades embarcam o dobro da massa)
- **Correcao:** valores monetarios arredondados em centavos (`total` saia como `233.70000000000002`)

## Sprint 5 (concluida)

Escopo em [docs/sprint5-handoff.md](docs/sprint5-handoff.md):

**Busca e categorias**

- `GET /home` aceita `q` (busca por nome de categoria, acentos ignorados) e `category` (filtro exato, **422** se desconhecida)
- Bloco SDUI **`category_grid`** — 12 maiores categorias com contagem; cada item carrega a propria `navigate`
- `hero_banner` ganha `cta_label`; com filtro ativo o hero devolve a acao "Ver tudo"
- Filtro compoe com `conscious_buyer`: "produtos de bebe mais proximos de mim"

**Carrinho multi-item**

- `POST /checkout/simulate` recebe `items` (1 a 20) no lugar de um `product_id` solto
- Bloco SDUI **`shipment_breakdown`** — uma remessa por vendedor, com distancia, frete, CO2 e `co2_share`
- `checkout_summary` passa a listar as linhas do carrinho
- Frontend: carrinho no header, tela de revisao com quantidade e remocao

**Testes e CI**

- Vitest em `web/` (14 casos) sobre o executor de `actions` e o `ScreenRenderer`
- `.github/workflows/ci.yml` com dois jobs (backend e frontend)
- `@types/node` alinhado ao Node 22 do projeto (estava em `^20`)

## Sprint 6 (concluida)

- Remessas ordenadas por **emissao decrescente** — a que domina a pegada aparece primeiro
- `alternatives` no `shipment_breakdown`: produtos da mesma categoria em vendedores mais proximos, com CO2 economizado
- Botao "Trocar" substitui o item no carrinho preservando a quantidade e re-simula pelo servidor
- `src/features/checkout/alternatives.py` — ranking por **economia de CO2**, nao por distancia pura
- Carrinho persistido em `localStorage`, sobrevivendo a um F5
- **Modo de inspecao SDUI** — botao no header expoe o envelope e o JSON de cada bloco
- Bloco **`product_detail`** server-driven (`GET /products/{id}`), com nota e vendedor reais do dataset
- ETL passa a agregar `review_score` por produto (6.528/6.575 com avaliacao)
- `npm run lint` entrou no CI (estava vermelho e ninguem via)
- **E2E com Playwright** cobrindo a jornada da defesa de ponta a ponta, contra a pilha real (`npm run e2e`)
- **Locust** mediu a meta de 200 ms; o gargalo era um N+1 (63 queries por requisicao). Memo por requisicao e `cep_centroids` em memoria: 63 -> 2 queries
- Redis removido do codigo por inferencia sobre o gargalo — revertido na Sprint 7

## Sprint 7 (concluida)

Fidelidade dos dados e validade da medicao. Sem handoff; detalhes nas secoes citadas.

- Tabela **`offers`** derivada de `order_items`; Home, detalhe e checkout passam a le-la. A vitrine deixou de trocar de produtos a cada recarga do ETL
- ETL **completa as ofertas** dos produtos sorteados (ver [Demo multi-vendedor](#demo-multi-vendedor)); "mesmo produto, vendedor mais proximo"
- Selo nao afirma mais "0 km" nem "0,00 g CO2"
- **E2E de mutacao de contrato** (`web/e2e/contract-mutation.spec.ts`) — objetivo (d), a parte "flexibilidade"; evidencia em `docs/evidencia/`
- **Prazo medido** (`ETA_BANDS`) substitui o arbitrado; **peso cubado** entra no CO2 (ver [Logistica Verde](#logistica-verde))
- Locust com **CEPs reais** e think time da metodologia; `echo` do SQLAlchemy descoberto como confundidor de todas as medicoes anteriores
- **Redis volta como variavel de experimento** (`CACHE_ENABLED=false`) — ver [Redis](#redis--ligado-por-padrao-desde-a-sprint-8)

## Sprint 8 (concluida)

Escopo em [docs/sprint8-handoff.md](docs/sprint8-handoff.md). Defesa:
[docs/tese-rastreabilidade.md](docs/tese-rastreabilidade.md).

- **Harness para agentes:** `AGENTS.md` na raiz (mapa + regras), `CLAUDE.md`, sensores `tests/test_docs.py` (caminho citado tem de existir) e de espelho do contrato SDUI (`type` iguais em `sdui.py`, `sdui.ts` e `REGISTRY`)
- **Protocolo de carga da §3.3:** 27 ensaios validos, n = 3 (`load/protocolo.py`, `load/resumo.py`); tres defeitos de validade corrigidos antes de medir (TTL, CEP sem semente, `echo`); 13 ensaios em bateria descartados e refeitos — o runner agora nao mede fora da tomada. Resultado em [docs/performance.md](docs/performance.md) §11
- **Redis ligado por padrao**, decisao medida: dispensavel em carga nominal, decisivo a 250 VU, mantem a Home na meta a 1.000 VU; pool bloqueante validado por A/B
- **Bloco sem `actions` degrada em vez de derrubar a tela** (`parseScreen`), com 4a mutacao no E2E
- **Graficos do capitulo 5** (`python -m load.graficos`, `docs/graficos/`)
- Testes: pytest 167, vitest 35, os dois E2E passando com o cache ligado

## Roadmap (proximas sprints)

- **green_logistics:** evolucao opcional para PostGIS (`ST_DistanceSphere`) com indexacao espacial.
  Hoje o calculo nao toca o banco (centroides em memoria, Haversine em Python), entao
  PostGIS moveria a conta de volta para dentro do Postgres. Se pagaria se o app passasse a
  fazer consulta espacial de verdade — "vendedores num raio de X km" com indice — que hoje
  ele nao faz.
- **orchestrator:** versionamento de blocos e roteamento dinamico. **Nao implementado**: o
  campo `version` ja existe no envelope, mas todos valem 1 — nao ha uma segunda versao para
  rotear entre.

### Descartado ou em aberto

- **Cache Redis: descartado por inferencia (Sprint 6), reinserido como experimento (Sprint 7), ligado por padrao por medicao (Sprint 8).** A Sprint 6 o descartou **por inferencia**: a
  lentidao era um N+1 (63 queries para montar 6 cards) e, depois dele, o worker unico — e o
  codigo do Redis foi removido. A Sprint 7 o reinseriu como **variavel de experimento**,
  desligado por padrao (`CACHE_ENABLED=false`, `src/core/cache.py`), para que a decisao vire
  medicao. O protocolo da §3.3 (27 ensaios) mostrou que ele e dispensavel em carga nominal e
  decisivo a partir de 250 usuarios com 1 processo. Ver a secao [Redis](#redis--ligado-por-padrao-desde-a-sprint-8) acima e
  [docs/performance.md](docs/performance.md) §9.
- **Locust / TTFB:** feito — suite em `load/locustfile.py`, numeros em `docs/performance.md`.
