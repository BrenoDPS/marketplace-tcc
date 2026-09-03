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
| [docs/PROJECT_BOOTSTRAP.md](docs/PROJECT_BOOTSTRAP.md) | Visao geral para agentes/conversas novas |
| [docs/sprint5-handoff.md](docs/sprint5-handoff.md) | **Sprint 5 (atual):** busca e categorias, carrinho multi-item, testes de frontend e CI |
| [docs/sprint4-handoff.md](docs/sprint4-handoff.md) | Sprint 4 (historico) |
| [docs/sprint3-handoff.md](docs/sprint3-handoff.md) | Sprint 3 (historico) |
| [docs/sprint2-handoff.md](docs/sprint2-handoff.md) | Sprint 2 (historico) |
| [docs/frontend-sprint2.md](docs/frontend-sprint2.md) | Guia para dev frontend |
| [docs/tech_spec.md](docs/tech_spec.md) | Contrato SDUI e logistica verde |

## Fluxo completo (Sprint 2+)

Sequencia recomendada para subir do zero:

```bash
# 1. Subir o Postgres (porta 5433 externa para nao colidir com Postgres nativo do Windows)
docker compose up -d

# 2. Carregar amostra (~10000 order_items, seed=42). Os CSVs do Olist
#    devem estar em data/raw/ (nao versionados).
python -m scripts.etl_load_sample

# 3. Subir a API
uvicorn src.main:app --reload
```

Acesse a documentacao interativa em **http://localhost:8000/docs**.

## Demo

Apos o ETL, o script imprime no console um par `(customer_zip_prefix, seller_zip_prefix)` com distancia < 100 km, util para testar o selo de Logistica Verde.

Par de demo conhecido (amostra padrao, `seed=42`): `customer_zip_prefix=05311` (Sao Paulo, SP), seller correspondente em `08275` — distancia Haversine ~27 km, **badge presente**.

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

Pontos que economizam tempo de quem for mexer:

- **Bloco novo no backend = uma linha no `REGISTRY`.** Tipo desconhecido renderiza `null` de proposito: a tela degrada em vez de quebrar.
- **A busca usa `next/form`** (`action="/"`, GET): os campos viram query string, a navegacao e client-side e o formulario continua funcionando sem JS. Nao trocar por `onSubmit` + `router.push` sem motivo.
- **Sem CORS em dev:** `web/next.config.ts` faz rewrite de `/api/v1/*` para a API, entao o fetch do browser sai da mesma origem.
- **Fontes sao self-hosted via `@fontsource`**, nao `next/font/google` — `fonts.googleapis.com` e instavel/bloqueado em algumas redes e o build quebra sem mensagem obvia. Nao trocar sem saber disso.
- **O carrinho e estado do cliente** (`sdui-context.tsx`), nao do servidor: o `api_call` de checkout envia a lista de itens. A acao vem do `product_card` e fica guardada ao adicionar o primeiro item — quem manda no COMO continua sendo o servidor.

## Testes

```bash
# Backend
pytest

# Frontend
cd web && npm test        # Vitest (use `npm run test:watch` para watch)
cd web && npm run typecheck
```

Os testes de backend nao dependem de Postgres rodando (uso de `app.dependency_overrides` + monkeypatch nos repositorios). Os de frontend cobrem as duas pecas com logica nao trivial — o executor de `actions` e o `ScreenRenderer` —; o resto e apresentacao e nao ganha teste de proposito. Para validacao end-to-end use o fluxo de cima.

### CI

`.github/workflows/ci.yml` roda em push/PR para `main` e `development`: `pytest` (backend) e `npm run typecheck` + `npm test` + `npm run build` (frontend).

## Arquitetura (Vertical Slice)

```
src/
  schemas/sdui.py            # Contrato SDUI (envelope + UIAction + ScreenResponse)
  core/
    config.py                # Pydantic settings
    database.py              # AsyncEngine + AsyncSession
    models.py                # Modelos SQLAlchemy 2.0 (Olist + cep_centroids)
    redis.py                 # Stub do client async (sem uso runtime nesta sprint)
  features/
    home_contextual/         # Composicao de tela: hero por contexto + produtos reais
    green_logistics/         # Haversine + centroides CEP + CO2 (FE 0,102) + selo < 100 km
      delivery_options.py    # Sprint 4: modalidades comparaveis (cenario declarado)
    checkout/                # Sprint 3: checkout simulado (POST /checkout/simulate)
    orchestrator/            # Stub (sprint futura)
scripts/
  etl_load_sample.py         # ETL offline: 10000 order_items + cep_centroids
web/                         # Frontend Next.js (consome o SDUI) — ver secao acima
docker-compose.yml           # Postgres 16 (sem PostGIS nesta sprint)
```

## Logistica Verde

- **Distancia:** Haversine puro em Python sobre centroides por prefixo de CEP (mediana de lat/lng por `geolocation_zip_code_prefix`).
- **Selo:** `SustainabilityProps` no `ProductCard` quando `distance_km < 100`; senao `badge: null`.
- **CO2:** `EMISSION_FACTOR = 0,102` kg CO2/(t.km) (GHG Protocol) em `green_logistics/co2.py`. A emissao acompanha a **massa embarcada**: `quantity` unidades pesam `quantity` vezes mais.
- **Exibicao do CO2:** `format_co2` escolhe a unidade (g abaixo de 10 g, kg acima). Com a amostra de 10k as distancias caem para poucos km e um `.2f` em kg imprimia `0,00 kg` em todo selo — apagando o numero que sustenta o trabalho.
- **Modalidades:** `green_logistics/delivery_options.py`. **Leia o docstring do modulo antes de citar esses numeros no TCC.** Distancia, massa e o FE base sao reais; `standard` usa o frete real da amostra sem fator. Os fatores de preco/emissao/prazo de `express` e `green` sao um **cenario declarado**, nao dado do Olist — o dataset nao tem modalidade nem transportadora. A ressalva viaja no proprio JSON (campo `note`) e e exibida na tela.

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

## Roadmap (proximas sprints)

- **green_logistics:** evolucao opcional para PostGIS (`ST_DistanceSphere`) com indexacao espacial.
- **orchestrator:** versionamento de blocos por `version`, roteamento dinamico e cache Redis de fragmentos SDUI.
- **Cache Redis em runtime:** cliente em `core/redis.py`; uso em runtime pendente.
- **Locust / TTFB:** testes de carga e meta &lt; 200 ms (TCC2).
