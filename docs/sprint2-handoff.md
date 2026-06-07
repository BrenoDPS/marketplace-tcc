# Handoff — Sprint 2: Motor de sustentabilidade + Home com dados reais (Olist)

> **Próxima sprint:** ver [sprint3-handoff.md](sprint3-handoff.md). Contexto geral: [PROJECT_BOOTSTRAP.md](PROJECT_BOOTSTRAP.md).

## Fonte de verdade

Leia e siga (nesta ordem):

- @docs/prd.md
- @docs/tech_spec.md
- @.cursorrules
- @README.md
- @src/schemas/sdui.py
- @src/features/home_contextual/
- @data/raw/

**Não** siga transcripts antigos como spec; use só este handoff + arquivos acima.

---

## Objetivo desta sprint

Implementar o **motor de logística verde (MVP)** com dados **reais amostrados** do Olist e integrar na **Home SDUI** com produtos vindos do banco — substituindo mocks e `_MOCK_GREEN_BADGE`.

---

## Decisões fechadas (não reinterpretar)


| Tópico          | Decisão                                                                                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Distância       | **Haversine** em Python (centroides por prefixo de CEP). **Sem PostGIS** nesta sprint.                                                                                                   |
| ETL             | **~1.000 `order_items`** após filtros; amostra **aleatória com seed fixa** (`random_state=42` ou equivalente). **Não** carregar dataset completo.                                        |
| Geolocation     | Só prefixos usados na amostra; **1 lat/lng por prefixo** (usar **mediana** de lat e de lng por `geolocation_zip_code_prefix`).                                                           |
| Emissão         | E = d \times p \times FE; **p** em toneladas (`product_weight_g / 1_000_000`); **FE = 0.102** kg CO₂/(t·km) (GHG Protocol).                                                              |
| Selo UI         | **Apenas distância:** `d_km < 100` ⇒ preencher `SustainabilityProps` no `ProductCard`; senão `badge: null`.                                                                              |
| Baseline 139 km | **Remover** menções no repositório (`prd.md`, `tech_spec.md`, `README.md`, `.cursorrules`, docstrings em `green_logistics`, etc.). **Fora de escopo** nesta sprint.                      |
| Home            | **Opção A:** montar `ProductCard` a partir de **produtos reais da amostra** no Postgres (não `prod_001` mock). Manter `context` para hero/categorias se fizer sentido.                   |
| Cliente         | Query `**customer_zip_prefix`** (prefixo Olist, ex. `"01310"`). **Obrigatório**; validar contra dados carregados; **422** se inválido. Documentar um prefixo de demo no README após ETL. |
| Infra           | Incluir `**docker-compose.yml`**: Postgres **sem PostGIS** (imagem `postgres:16` ou similar). Redis **opcional** no compose, mas **não usar** cache nesta sprint.                        |
| Fora de escopo  | PostGIS, Redis em runtime, Locust, checkout real, pagamento, orchestrator, CORS, carregamento adiado SDUI (above the fold).                                                              |


---

## Entregáveis esperados

### 1. Docker + config

- `docker-compose.yml` com serviço `postgres` (porta 5432, db `olist`, user/senha alinhados a `.env.example`).
- README: como subir `docker compose up -d`, rodar ETL, rodar API.

### 2. ETL (`scripts/etl_load_sample.py` ou equivalente)

Fluxo sugerido:

1. Ler CSVs em `data/raw/`.
2. Amostrar **~1000 linhas** de `olist_order_items_dataset.csv` com **seed fixa**.
3. Filtrar: `product_weight_g` válido; CEPs de customer/seller presentes; prefixos com geolocation após agregação.
4. Derivar subset de `orders`, `customers`, `sellers`, `products`, `geolocation` (só prefixos necessários).
5. Carregar tabelas no Postgres (SQLAlchemy models ou SQL direto).
6. Criar tabela `**cep_centroids`** (`zip_prefix`, `lat`, `lng`) via mediana por prefixo.
7. (Opcional) tabela `**distance_lookup**` seller_prefix × customer_prefix → `distance_km` pré-calculada com Haversine.

Dependência: `pandas` aceitável para o script ETL (pode ir em `requirements.txt` ou `requirements-dev.txt` — documentar).

### 3. Fatia `green_logistics`

Criar em `src/features/green_logistics/`:

- `distance.py` — Haversine(lat1, lng1, lat2, lng2) → km.
- `co2.py` — `EMISSION_FACTOR = 0.102`; `calculate_co2(distance_km, weight_kg) -> float` (converter peso para toneladas).
- `badge.py` (ou similar) — `build_sustainability_props(distance_km) -> SustainabilityProps | None` se `distance_km < 100`; label sugerido: `"Entrega local (~{d:.0f} km)"` (sem baseline CO₂).
- Serviço async que, dado `customer_zip_prefix` + `seller_zip_prefix` (+ peso se precisar no futuro), retorna distância e badge.

**Não** registrar router público obrigatório nesta sprint, a menos que facilite testes; foco é ser **consumido por `home_contextual`**.

### 4. Modelos / acesso a dados

- Models SQLAlchemy (ex. `src/core/models/` ou `src/features/.../repository.py`) para consultar produtos da amostra com `seller_zip_code_prefix`, `price`, `product_id`, `product_weight_g`, categoria se útil para `context`.

### 5. `home_contextual`

- `router.py`: adicionar query param `**customer_zip_prefix: str**` (obrigatório).
- `composer.py`:
  - Remover `_MOCK_GREEN_BADGE` e listas estáticas de `prod_xxx` como fonte principal.
  - Buscar N produtos reais (ex. 4–8) filtrados por `context`/categoria quando possível.
  - Para cada card: calcular distância via `green_logistics`; injetar `badge` ou `null`.
  - Manter envelope SDUI `{ type, version, props, actions }` e `ScreenResponse.schema_version`.

### 6. Documentação (atualizar)

- `docs/tech_spec.md` §3: distância via **Haversine** (MVP); **EF = 0,102**; selo **< 100 km**; **remover** PostGIS e baseline 139 km **nesta fase** (PostGIS = evolução futura opcional).
- `README.md`: Fase 2 atual = esta sprint; EF 0,102; docker + ETL; remover 0,062 e 139 km.
- `.cursorrules`: trocar PostGIS por Haversine/centroides CEP nesta fase; remover baseline 139 km.
- `docs/prd.md`: remover validação ~139 km se existir; manter selo < 100 km.

### 7. Testes

- `tests/test_distance.py` — Haversine com par de pontos conhecido.
- `tests/test_co2.py` — FE 0,102 e conversão g → toneladas.
- `tests/test_badge.py` — 99 km ⇒ badge; 101 km ⇒ None.
- Atualizar `tests/test_home_contextual.py` — incluir `customer_zip_prefix` válido; 422 para prefixo inválido; pelo menos um card com badge quando distância < 100 km (usar fixtures ou seed conhecida do ETL).

Critério: `**pytest` verde**.

---

## Critérios de aceite

- `docker compose up -d` + ETL carrega amostra (~1000 order_items, seed 42).
- `GET /api/v1/home?context=...&customer_zip_prefix=...` retorna `ProductCard` com **product_id reais** da amostra.
- Badge aparece **somente** quando Haversine **< 100 km**; caso contrário `badge: null`.
- `_MOCK_GREEN_BADGE` removido.
- FE **0,102** centralizado; sem referências a **0,062** ou **139 km** no repo.
- Swagger `/docs` reflete novo query param.
- `pytest` passa.

---

## Ordem de implementação sugerida

1. docker-compose + models + ETL script
2. green_logistics (distance, co2, badge)
3. Integração home_contextual + router
4. Testes
5. Limpeza docs + README

---

## Notas

- `ProductCardProps` **não precisa** expor `seller_id` no JSON SDUI; seller/CEP ficam na camada de serviço.
- Se amostra aleatória dificultar teste estável de badge, documentar no README **um par** (customer_prefix, seller_prefix) da seed 42 que fique < 100 km.
- Monografia TCC cita Haversine — implementação alinhada.

