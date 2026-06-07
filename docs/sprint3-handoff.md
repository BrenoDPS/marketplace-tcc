# Handoff — Sprint 3: Checkout simulado + Vitrine verde (CO₂) + CORS dev

> **Para agentes sem contexto:** leia primeiro `@docs/PROJECT_BOOTSTRAP.md`, depois este arquivo.
> Sprints 1–2 **já estão implementadas** — não reimplementar do zero.

## Fonte de verdade (ordem de leitura)

1. **Este arquivo** (`docs/sprint3-handoff.md`) — escopo desta entrega
2. `@docs/PROJECT_BOOTSTRAP.md` — visão geral do repo
3. `@README.md` — como subir docker + ETL + API
4. `@docs/tech_spec.md` — contrato SDUI (inclui blocos novos da Sprint 3)
5. `@docs/prd.md` — produto
6. `@.cursorrules` — regras de código

Código existente (referência, não refatorar sem necessidade):

- `@src/schemas/sdui.py`
- `@src/features/green_logistics/`
- `@src/features/home_contextual/`
- `@src/core/models.py`
- `@scripts/etl_load_sample.py`

**Não** usar transcripts antigos como especificação.

---

## Objetivo

| Trilha | Entrega |
|--------|---------|
| **B — Vitrine verde** | CO₂ no label do selo; contexto `conscious_buyer` com produtos ordenados por proximidade |
| **A — Checkout simulado** | `POST /api/v1/checkout/simulate` retornando tela SDUI (frete + distância + CO₂ + selo) |
| **C — CORS dev** | Middleware CORS quando `APP_ENV=development` (~5% do esforço) |

Foco: **~95% backend**. Documento `frontend-sprint3.md` é opcional (não bloquear sprint).

---

## Estado atual (Sprint 2 — já feito)

- ETL: ~1000 `order_items`, seed 42, Postgres via `docker compose`
- Home: `GET /api/v1/home?customer_zip_prefix=...&context=...` com produtos reais
- Selo: `distance_km < 100` → `SustainabilityProps`; senão `badge: null`
- Label do selo: **só distância** (ex.: `"Entrega local (~27 km)"`)
- `calculate_co2_kg` existe em `co2.py` mas **não aparece na UI**
- `checkout/` e `orchestrator/` são stubs; só `home_router` registrado em `main.py`
- Sem CORS

---

## Decisões fechadas (não reinterpretar)

| Tópico | Decisão |
|--------|---------|
| Distância / selo | Haversine + centroides (Sprint 2); selo se `d_km < 100` |
| CO₂ | `FE = 0.102` kg CO₂/(t·km) em `co2.py`; exibir no **label do badge** quando `weight_g` disponível |
| Checkout | **Simulado** — sem pagamento, PIX, estoque ou persistência de pedido |
| Frete | Usar `freight_value` da **primeira linha** de `order_items` daquele `product_id` na amostra |
| `conscious_buyer` | **Sem** filtro de categoria; **ordenar** produtos por distância crescente ao `customer_zip_prefix` |
| Demais `context` | Comportamento Sprint 2 (filtro categoria + ordem atual); documentar se adicionar tie-break por distância |
| CORS | Só `APP_ENV=development`; origens `localhost:5173`, `127.0.0.1:5173`, `localhost:3000` |
| ETL | **Não** ampliar amostra nesta sprint (salvo bug crítico) |

---

## Trilha B — Vitrine verde (Home)

### B1. CO₂ no label do selo

**Arquivo:** `src/features/green_logistics/badge.py`

- Assinatura: `build_sustainability_props(distance_km: float, weight_g: float | None = None)`
- Se `distance_km >= 100`: retornar `None`
- Se `weight_g` válido (> 0):  
  `label = f"Entrega local (~{distance_km:.0f} km · ~{co2_kg:.2f} kg CO₂)"`  
  (usar `calculate_co2_kg` de `co2.py`)
- Se peso ausente: manter label só com km (compatível Sprint 2)

**Arquivo:** `src/features/green_logistics/service.py`

- `build_badge_for_pair(..., weight_g: float | None = None)` repassar peso ao badge

**Arquivo:** `src/features/home_contextual/composer.py`

- Passar `product.weight_g` ao chamar `build_badge_for_pair`

### B2. Contexto `conscious_buyer`

**Arquivo:** `src/features/home_contextual/repository.py` (e/ou composer)

- Adicionar `conscious_buyer` ao mapa de contextos (sem categoria obrigatória)
- Buscar pool maior de candidatos (ex. `limit * 4`)
- Para cada produto: calcular distância via `green_logistics.compute_distance_km`
- Ordenar por distância ascendente; `None` (sem centroide) vai para o fim
- Retornar top `limit` (padrão 6)

Hero sugerido: título/subtítulo sobre consumo consciente / entregas locais.

### B3. Testes B

- `tests/test_badge.py`: label contém `CO₂` ou `kg` quando `weight_g` informado
- `tests/test_home_contextual.py`: `context=conscious_buyer` → ordem de cards reflete distância (mock)

---

## Trilha A — Checkout simulado

### A1. Endpoint

```
POST /api/v1/checkout/simulate
Content-Type: application/json
```

**Body:**

```json
{
  "customer_zip_prefix": "05311",
  "product_id": "abc...",
  "quantity": 1
}
```

| Campo | Regras |
|-------|--------|
| `customer_zip_prefix` | Obrigatório; deve existir em `cep_centroids` → **422** se inválido |
| `product_id` | Obrigatório; deve existir na amostra → **404** ou **422** |
| `quantity` | Opcional, default `1`, inteiro ≥ 1 |

**Response:** `ScreenResponse` com:

- `screen_id`: `"checkout_simulate"`
- `context`: echo ou `"checkout"`
- `components`: lista de blocos SDUI (ver tech_spec §2)

### A2. Fatia `src/features/checkout/`

Criar:

| Arquivo | Responsabilidade |
|---------|------------------|
| `schemas.py` | `CheckoutSimulateRequest` (Pydantic) |
| `repository.py` | Buscar produto + seller + `freight_value` + peso por `product_id` |
| `composer.py` | Montar `ScreenResponse` (distância, CO₂, selo, totais) |
| `router.py` | Rota POST + `Depends(get_db)` |

Reutilizar `green_logistics` para distância, CO₂ e badge.

**Totais sugeridos:**

- `subtotal = unit_price * quantity`
- `freight = freight_value` (da order_item escolhida)
- `total = subtotal + freight`

### A3. Novos blocos SDUI

Atualizar `src/schemas/sdui.py` e `docs/tech_spec.md` §2:

1. **`checkout_summary`** (`version: 1`)  
   Props: `product_id`, `title`, `quantity`, `unit_price`, `subtotal`, `freight`, `total`

2. **`impact_banner`** (`version: 1`)  
   Props: `distance_km`, `co2_kg`, `badge` (`SustainabilityProps | null`), `message` (string curta)

Incluir ambos no `UIComponent` union discriminada.

**Actions na tela checkout (exemplo):**

- `navigate` → path `/` ou home com query de CEP
- (opcional) `navigate` “Continuar comprando”

### A4. Wiring na Home

Em `composer.py`, nos `ProductCardBlock.actions`:

- Manter ou ajustar `open_modal` se desejado
- Adicionar **`api_call`**: `method: "POST"`, `path: "/api/v1/checkout/simulate"`  
  O front envia body com `product_id`, `customer_zip_prefix`, `quantity` (contrato documentado no README)

### A5. `main.py`

```python
app.include_router(checkout_router, prefix="/api/v1")
```

### A6. Testes A

**Arquivo:** `tests/test_checkout_simulate.py`

- 200 com payload válido (dependency_overrides / mocks)
- Resposta contém `checkout_summary` e `impact_banner`
- `co2_kg` coerente quando distância e peso válidos
- 422 CEP inválido; 404/422 produto inexistente

---

## Trilha C — CORS (desenvolvimento)

Em `src/main.py` (ou `src/core/cors.py`):

- Se `settings.APP_ENV == "development"`: `CORSMiddleware` com origens locais (Vite/React)
- **Não** habilitar CORS permissivo em produção

Documentar no `README.md`.

---

## Ordem de implementação

1. B1 — CO₂ no badge + testes  
2. B2 — `conscious_buyer` + testes home  
3. A3 — novos schemas SDUI + testes schema  
4. A2 + A5 — checkout repository/composer/router  
5. A4 — `api_call` na Home  
6. C — CORS  
7. Docs (`README`, `tech_spec`, `.cursorrules`) + smoke curl  

---

## Critérios de aceite

- [ ] Badge local inclui **km e CO₂** quando `weight_g` disponível
- [ ] `GET /home?context=conscious_buyer&customer_zip_prefix=...` lista produtos **mais próximos primeiro**
- [ ] `POST /checkout/simulate` retorna SDUI com frete, distância, CO₂ e selo coerentes com a Home
- [ ] Pelo menos um `ProductCard` com `action.type == "api_call"` para checkout
- [ ] CORS funciona em dev (`APP_ENV=development`)
- [ ] `pytest` verde
- [ ] Swagger `/docs` documenta checkout e novos blocos
- [ ] README com exemplos `curl` de checkout

---

## Fora de escopo (não implementar)

- Pagamento, PIX, gateway, controle de estoque
- Redis em runtime, Locust, PostGIS
- Fatia `orchestrator` (além de stub)
- Hidratação SDUI “above the fold”
- Ampliar ETL / dataset completo
- `frontend-sprint3.md` (opcional, não bloqueante)

---

## Exemplos curl (aceite — preencher após implementação)

```bash
# Home consumidor consciente (produtos por proximidade)
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&context=conscious_buyer"

# Checkout simulado
curl -X POST "http://localhost:8000/api/v1/checkout/simulate" \
  -H "Content-Type: application/json" \
  -d '{"customer_zip_prefix":"05311","product_id":"<ID_DA_AMOSTRA>","quantity":1}'
```

Substituir `<ID_DA_AMOSTRA>` por um `product_id` real retornado na Home.
