# Bootstrap do projeto — leitura rápida para agentes

Use este arquivo ao **iniciar uma conversa nova** (sem histórico). Depois leia o handoff da sprint ativa.

## O que é

Marketplace inspirado no **dataset Olist** com **Server-Driven UI (SDUI)**: o backend envia JSON com blocos de tela (`type`, `version`, `props`, `actions`); o front React só renderiza e executa ações.

Eixos do TCC: **personalização contextual** + **logística verde** (distância CEP, selo &lt; 100 km, CO₂).

## Stack

- **API:** FastAPI + Pydantic v2 + SQLAlchemy async (asyncpg)
- **Dados:** PostgreSQL 16 (Docker, porta **5433** no host)
- **ETL offline:** `scripts/etl_load_sample.py` (pandas + psycopg), amostra ~10000 `order_items`, seed 42
- **Distância:** Haversine em Python sobre centroides de CEP (mediana lat/lng)
- **FE CO₂:** 0,102 kg CO₂/(t·km) — `src/features/green_logistics/co2.py`

## Sprints concluídas

| Sprint | Entrega |
|--------|---------|
| **1** | Contrato SDUI, `GET /api/v1/home` mock, testes de schema |
| **2** | Docker + ETL Olist, produtos reais na Home, `customer_zip_prefix` obrigatório, selo por distância |
| **3** | Checkout simulado (`POST /checkout/simulate`), CO₂ no selo, `conscious_buyer` por proximidade, CORS dev |

## Sprint ativa

Ver **`docs/sprint4-handoff.md`**: bloco `delivery_options` (comparativo de modalidades de entrega), correção do CO₂ exibido como `0,00 kg`, frontend Next.js em `web/` renderizando o bloco.

## Subir o ambiente

```bash
docker compose up -d
python -m scripts.etl_load_sample   # CSVs em data/raw/
uvicorn src.main:app --reload
```

Demo Home (após ETL): `customer_zip_prefix=05311` — ver `README.md`.

## Estrutura (VSA)

```
src/features/
  home_contextual/   # Composição da Home
  green_logistics/   # Distância, CO₂, selo, modalidades de entrega
  checkout/          # Sprint 3: checkout simulado
  orchestrator/      # Stub futuro
src/schemas/sdui.py  # Contrato JSON global
web/                 # Frontend Next.js (App Router) que consome o SDUI
```

## Documentos

| Arquivo | Uso |
|---------|-----|
| `docs/sprint4-handoff.md` | Spec da sprint atual |
| `docs/sprint3-handoff.md` | Spec Sprint 3 (histórico) |
| `docs/sprint2-handoff.md` | Spec Sprint 2 (histórico) |
| `docs/tech_spec.md` | Contrato SDUI + logística |
| `docs/prd.md` | Produto |
| `docs/frontend-sprint2.md` | Guia para dev front |
| `.cursorrules` | Regras de implementação |

## O que não fazer sem pedido explícito

- Pagamento real, Redis/Locust, PostGIS, dataset Olist completo
- Reimplementar Sprint 1–4 do zero
- Apresentar os fatores de `delivery_options.py` como dado medido do Olist — são cenário declarado (ler o docstring do módulo)
- Seguir transcripts antigos em vez dos handoffs em `docs/`
