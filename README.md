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
| [docs/sprint3-handoff.md](docs/sprint3-handoff.md) | **Sprint 3 (atual):** checkout simulado, CO2 no selo, conscious_buyer, CORS |
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
# Na Sprint 3 o label inclui o CO2 estimado quando o produto tem peso:
#   "Entrega local (~27 km · ~0.01 kg CO₂)"
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&context=electronics_expert"

# Badge null em todos os cards (cliente em Fortaleza/CE, sellers da amostra em SP/SE)
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=60165&context=default"

# 422 quando o prefixo nao existe na amostra
curl -i "http://localhost:8000/api/v1/home?customer_zip_prefix=00000"

# Home consumidor consciente: produtos ordenados por proximidade (mais perto primeiro)
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&context=conscious_buyer"
```

### Checkout simulado (Sprint 3)

`POST /api/v1/checkout/simulate` retorna uma tela SDUI com os blocos
`checkout_summary` (subtotal, frete, total) e `impact_banner` (distancia, CO2 e
selo verde). Sem pagamento, estoque ou persistencia de pedido. O `product_id`
deve ser um id real retornado pela Home.

```bash
# Checkout simulado (substitua <PRODUCT_ID> por um id retornado na Home)
curl -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","product_id":"<PRODUCT_ID>","quantity":1}'

# 422 quando o customer_zip_prefix nao existe em cep_centroids
curl -i -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"00000","product_id":"<PRODUCT_ID>"}'

# 404 quando o product_id nao existe na amostra
curl -i -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","product_id":"inexistente"}'
```

> **Decisao (handoff ambiguo "404 ou 422"):** produto inexistente retorna
> **404** (recurso nao encontrado); `customer_zip_prefix` invalido retorna
> **422** (entrada que nao casa com `cep_centroids`), consistente com `GET /home`.
> O frete usado e o `freight_value` da primeira linha de `order_items` daquele
> `product_id` na amostra.

### CORS (desenvolvimento)

Quando `APP_ENV=development` (padrao em `.env`), a API habilita CORS para as
origens locais `http://localhost:5173`, `http://127.0.0.1:5173` e
`http://localhost:3000` (Vite/React). Em producao o CORS permissivo fica
desabilitado.

## Testes

```bash
pytest
```

Os testes nao dependem de Postgres rodando (uso de `app.dependency_overrides` + monkeypatch nos repositorios). Para validacao end-to-end use o fluxo de cima.

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
    checkout/                # Sprint 3: checkout simulado (POST /checkout/simulate)
    orchestrator/            # Stub (sprint futura)
scripts/
  etl_load_sample.py         # ETL offline: 10000 order_items + cep_centroids
docker-compose.yml           # Postgres 16 (sem PostGIS nesta sprint)
```

## Logistica Verde

- **Distancia:** Haversine puro em Python sobre centroides por prefixo de CEP (mediana de lat/lng por `geolocation_zip_code_prefix`).
- **Selo:** `SustainabilityProps` no `ProductCard` quando `distance_km < 100`; senao `badge: null`.
- **CO2:** `EMISSION_FACTOR = 0,102` kg CO2/(t.km) (GHG Protocol) em `green_logistics/co2.py`.

## Sprint 3 (concluida)

Escopo em [docs/sprint3-handoff.md](docs/sprint3-handoff.md):

- CO2 no label do selo (km + kg CO2 quando `weight_g` disponivel)
- Contexto `conscious_buyer` — produtos ordenados por proximidade ao `customer_zip_prefix`
- `POST /api/v1/checkout/simulate` — tela SDUI (`checkout_summary` + `impact_banner`) com frete, distancia, CO2 e selo
- `api_call` (POST `/api/v1/checkout/simulate`) nos `ProductCard` da Home
- CORS habilitado em `APP_ENV=development` (origens Vite/React locais)

Exemplos `curl` na secao [Demo](#demo) acima.

## Roadmap (proximas sprints)

- **green_logistics:** evolucao opcional para PostGIS (`ST_DistanceSphere`) com indexacao espacial.
- **orchestrator:** versionamento de blocos por `version`, roteamento dinamico e cache Redis de fragmentos SDUI.
- **Cache Redis em runtime:** cliente em `core/redis.py`; uso em runtime pendente.
- **Locust / TTFB:** testes de carga e meta &lt; 200 ms (TCC2).
