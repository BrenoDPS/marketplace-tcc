# Bootstrap do projeto — leitura rápida para agentes

Use este arquivo ao **iniciar uma conversa nova** (sem histórico). Regras de código e mapa: `AGENTS.md` (raiz).

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
| **4** | Bloco `delivery_options` (comparativo de modalidades), correção do CO₂ exibido como `0,00 kg` |
| **5** | Busca (`q`) e filtro por categoria com `category_grid`; carrinho multi-item com `shipment_breakdown`; Vitest e CI |
| **6** | Remessas por emissão + `alternatives`; carrinho em `localStorage`; modo de inspeção SDUI; `product_detail` server-driven; E2E Playwright; Locust e correção do N+1 (63 → 2 queries). Commits até `f6c052d` |
| **7** | Tabela `offers`; mesmo produto em vendedor mais próximo; selo sem "0 km"; E2E de mutação de contrato; prazo medido (`ETA_BANDS`); peso cubado no CO₂; Locust com CEPs reais; Redis como variável de experimento. Commits `7697552` → `d9b966b` |

Sprints 6 e 7 **não têm handoff**: o registro está no `README.md` (seções "Sprint 6" e "Sprint 7") e em `docs/performance.md` §§6–9.

## Sprint ativa

**Nenhuma com handoff.** Uma sprint nova começa escrevendo `docs/sprint<N>-handoff.md` (próxima: 8) no formato dos anteriores (objetivo · decisões fechadas · critérios de aceite · fora de escopo), com duas exigências:

- cada critério de aceite nomeia o **comando** que o prova (`pytest -q`, não "pytest verde");
- falha recorrente encontrada na sprint termina num **teste** ou numa **regra** do `AGENTS.md`, não só na prosa.

Ao abrir a sprint, atualize esta seção para apontar o handoff.

## Subir o ambiente

```bash
docker compose up -d
python -m scripts.etl_load_sample   # CSVs em data/raw/
uvicorn src.main:app --reload
```

Com a pilha no ar, `cd web && npm run e2e` percorre a jornada inteira da defesa (Playwright). É o check de pré-apresentação — não roda no CI porque `data/raw/` é gitignored.

Demo Home (após ETL): `customer_zip_prefix=05311` — ver `README.md`.

## Estrutura (VSA)

```
src/features/
  home_contextual/   # Composição da Home
  green_logistics/   # Distância, CO₂, selo, modalidades de entrega
  checkout/          # Sprint 3: checkout simulado
  product_detail/    # Sprint 6: GET /products/{id}
  orchestrator/      # Stub futuro
src/schemas/sdui.py  # Contrato JSON global
web/                 # Frontend Next.js (App Router) que consome o SDUI
```

## Documentos

| Arquivo | Uso |
|---------|-----|
| `AGENTS.md` | Mapa + regras de implementação (carregado em toda sessão) |
| `docs/sprint5-handoff.md` | Spec Sprint 5 (histórico) |
| `docs/sprint4-handoff.md` | Spec Sprint 4 (histórico) |
| `docs/sprint3-handoff.md` | Spec Sprint 3 (histórico) |
| `docs/sprint2-handoff.md` | Spec Sprint 2 (histórico) |
| `docs/tech_spec.md` | Contrato SDUI + logística |
| `docs/performance.md` | Medição de latência (Locust) e diagnóstico do N+1 |
| `docs/prd.md` | Produto |
| `docs/frontend-sprint2.md` | Consumo da API pelo front (histórico da Sprint 2 + notas “Hoje:”) |

## O que não fazer sem pedido explícito

- Pagamento real, PostGIS, dataset Olist completo
- Redis como arquitetura: hoje é **variável de experimento**, desligado por padrão (`CACHE_ENABLED=false`); a decisão depende dos ensaios do protocolo (`docs/performance.md` §9)
- Locust: **feito** — `load/locustfile.py`
- Reimplementar Sprint 1–7 do zero
- Apresentar os fatores de `delivery_options.py` como dado medido do Olist — são cenário declarado (ler o docstring do módulo)
- Prometer busca por **nome de produto**: o Olist não tem esse campo. A busca é sobre `product_category_name` (ler o docstring de `home_contextual/repository.py`)
- Afirmar que **consolidar remessas reduz CO₂**: o modelo é linear na massa, então agrupar economiza frete e não emissão (ver "O achado que mudou a premissa" no handoff da Sprint 5)
- Inventar **descrição de produto ou tags de sustentabilidade**: o Olist tem só o *comprimento* da descrição e nenhuma tag. Nota e vendedor, esses sim, são reais (`olist_order_reviews` / `olist_sellers`)
- Seguir transcripts antigos em vez dos handoffs em `docs/`
