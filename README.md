# Olist SDUI Marketplace

Marketplace contextual adaptativo com Server-Driven UI, baseado no dataset real da Olist.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

> `pandas` e `psycopg` sao usados **somente** pelo script ETL offline; o runtime da API permanece async (SQLAlchemy + asyncpg).

## Fluxo completo (Sprint 2)

Sequencia recomendada para subir do zero:

```bash
# 1. Subir o Postgres (porta 5433 externa para nao colidir com Postgres nativo do Windows)
docker compose up -d

# 2. Carregar amostra (~1000 order_items, seed=42). Os CSVs do Olist
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
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&context=electronics_expert"

# Badge null em todos os cards (cliente em Fortaleza/CE, sellers da amostra em SP/SE)
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=60165&context=default"

# 422 quando o prefixo nao existe na amostra
curl -i "http://localhost:8000/api/v1/home?customer_zip_prefix=00000"
```

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
    checkout/                # Stub (sprint futura)
    orchestrator/            # Stub (sprint futura)
scripts/
  etl_load_sample.py         # ETL offline: 1000 order_items + cep_centroids
docker-compose.yml           # Postgres 16 (sem PostGIS nesta sprint)
```

## Logistica Verde (Sprint 2)

- **Distancia:** Haversine puro em Python sobre centroides por prefixo de CEP (mediana de lat/lng por `geolocation_zip_code_prefix`).
- **Selo:** `SustainabilityProps` injetado no `ProductCard` apenas quando `distance_km < 100`. Caso contrario `badge: null`.
- **CO2:** `EMISSION_FACTOR = 0,102` kg CO2/(t.km) (GHG Protocol). Implementado em `green_logistics/co2.py` mesmo que o selo nesta sprint use somente distancia.

## Roadmap (proximas sprints)

- **green_logistics:** evolucao opcional para PostGIS (`ST_DistanceSphere`) com indexacao espacial.
- **checkout:** persistencia de pedidos/sessoes e validacao de frete (`docs/prd.md` secao 4).
- **orchestrator:** versionamento de blocos por `version`, roteamento dinamico e chaves de cache SDUI no Redis alinhadas a `schema_version` da tela e `version` por bloco.
- **Wiring real das actions:** hoje as `actions` apontam para rotas/modais mock; futuro conecta com endpoints reais (ex.: `api_call` para `/api/v1/checkout`).
- **Cache Redis em runtime:** cliente existe em `core/redis.py` mas ainda nao e usado para fragmentos SDUI.
