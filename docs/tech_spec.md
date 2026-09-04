Technical Specification: SDUI Engine & Backend
1. Arquitetura (Vertical Slice)
    - /src/features/home_contextual: Composição de layouts por categoria.
    - /src/features/green_logistics: Motor de geoprocessamento e cálculo de CO2.
    - /src/features/checkout: Checkout simulado com carrinho multi-item (`POST /api/v1/checkout/simulate`; sem pagamento real).
    - /src/features/orchestrator: Gerenciamento de versões de componentes e roteamento dinâmico.
    
2. Contrato SDUI (Schemas Pydantic)

Cada bloco enviado ao cliente segue o envelope **`{ type, version, props, actions }`**: `props` carrega apenas dados de apresentação; `actions` define comportamentos interpretados pelo app (PRD: *Sistema de Ações Dinâmicas*). O campo `version` por bloco permite compatibilidade quando o contrato evoluir (alinhado ao fatiamento `orchestrator`).

Validação com **Pydantic v2** e **discriminated unions** em `UIComponent` e em cada item de `actions`, para o OpenAPI refletir variantes com clareza.

> **Fonte de verdade: `src/schemas/sdui.py`.** Este documento descreve o contrato; não o duplica.
> Até a Sprint 5 o arquivo trazia uma cópia integral dos schemas, que ficou defasada em duas
> sprints (faltavam três blocos e o `checkout_summary` estava com os props antigos). Manter o
> mirror à mão não se pagou — as `actions` abaixo continuam em código porque são estáveis
> desde a Sprint 1; os blocos viraram tabela.

```python
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# --- Ações (comportamento definido pelo servidor) ---


class NavigatePayload(BaseModel):
    path: str
    replace: bool = False


class ApiCallPayload(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str
    body_key: str | None = None


class OpenModalPayload(BaseModel):
    modal_id: str
    title: str | None = None


class NavigateAction(BaseModel):
    type: Literal["navigate"] = "navigate"
    payload: NavigatePayload


class ApiCallAction(BaseModel):
    type: Literal["api_call"] = "api_call"
    payload: ApiCallPayload


class OpenModalAction(BaseModel):
    type: Literal["open_modal"] = "open_modal"
    payload: OpenModalPayload


UIAction = Annotated[
    Union[NavigateAction, ApiCallAction, OpenModalAction],
    Field(discriminator="type"),
]


# --- Blocos de UI ---
# Uniao discriminada por `type`, um modelo por bloco, todos no envelope
# `{ type, version, props, actions }`. Ver a tabela abaixo e, para os campos
# exatos, `src/schemas/sdui.py`.
UIComponent = Annotated[Union[...], Field(discriminator="type")]


class ScreenResponse(BaseModel):
    schema_version: int = 1
    screen_id: str
    context: str
    components: list[UIComponent]

```

### Blocos implementados

Todos seguem o envelope e estão na união discriminada `UIComponent` (`version: 1`).

| `type` | Tela | Props principais | Desde |
|--------|------|------------------|-------|
| `hero_banner` | Home | `title`, `subtitle`, `image_url`, `cta_label` | S1 (`cta_label` na S5) |
| `product_card` | Home | `product_id`, `price`, `title`, `image_url`, `badge` | S1 |
| `product_detail` | Detalhe | `product_id`, `title`, `price`, `category`, `weight_g`, `seller_id`, `seller_city`, `seller_state`, `rating`, `review_count`, `badge` | S6 |
| `category_grid` | Home | `title`, `categories[]` — cada item com `slug`, `label`, `product_count`, `selected` e **`actions` próprias** | S5 |
| `checkout_summary` | Checkout | `items[]` (`product_id`, `title`, `quantity`, `unit_price`, `line_total`), `subtotal`, `freight`, `total` | S3 (virou carrinho na S5) |
| `delivery_options` | Checkout | `distance_km`, `selected_id`, `options[]` (`id`, `label`, `eta_days`, `price`, `co2_kg`, `recommended`, `selected`), `note` | S4 |
| `shipment_breakdown` | Checkout | `title`, `shipments[]` (`seller_id`, `product_ids`, `total_quantity`, `weight_g`, `distance_km`, `freight`, `co2_kg`, `co2_share`, `badge`, `alternatives[]`), `note` | S5 (`alternatives` na S6) |
| `impact_banner` | Checkout | `distance_km`, `co2_kg`, `badge`, `message` | S3 |

`SustainabilityProps` (`label`, `impact_level`, `icon`) é o selo verde, reaproveitado por
`product_card`, `shipment_breakdown` e `impact_banner`.

**Duas exceções ao envelope, ambas deliberadas:**

- `category_grid` põe `actions` **no item**, não no bloco: cada categoria navega para um
  caminho diferente e o envelope só comporta uma ação para o conjunto.
- `delivery_options` tem **uma** `api_call` para o bloco todo: o cliente já sabe qual opção
  foi clicada e devolve o `id` no corpo, então três ações seriam redundantes.
- `shipment_breakdown` põe `actions` em cada `alternatives[]` (mesma razão do
  `category_grid`: cada sugestão é uma troca diferente).

**Sugestão de troca (Sprint 6):** `shipments[]` vem ordenada por emissão decrescente, e a
**primeira** — a que domina a pegada — traz `alternatives[]`: produtos da **mesma categoria**
em vendedores mais próximos, com `co2_saved_kg` e `saved_share`. Não é "o mesmo produto em
outro vendedor" — o Olist não tem catálogo compartilhado entre sellers, então o substituto é
outro produto da mesma categoria, e por isso a tela mostra preço e distância dele. O ranking
usa **distância e massa juntas**: um vendedor mais perto com produto mais pesado pode emitir
mais. Ver `src/features/checkout/alternatives.py`.

**Degradação graciosa:** bloco de `type` desconhecido renderiza `null` no cliente
(`REGISTRY` em `web/components/sdui.tsx`) — a tela degrada em vez de quebrar. Há teste
cobrindo isso.

**`open_modal` não tem emissor (desde a Sprint 6).** O detalhe do produto passou a vir de
`GET /products/{id}` via `api_call`, então nenhum bloco emite `open_modal` hoje. O tipo
segue no contrato e o cliente ignora ações que não trata — mesma degradação graciosa dos
blocos desconhecidos.

**`api_call` com `GET` devolve outra tela.** É como o detalhe chega: o mesmo `ScreenRenderer`
desenha, sem o cliente remontar nada. `POST` com `body_key: "checkout"` continua sendo a
simulação de compra. O cliente distingue **pelo método**, não pela ordem das ações — o
`product_card` carrega as duas.

**Modo de inspeção (Sprint 6):** o botão `SDUI` no header contorna cada bloco e expõe
`type`, `version`, número de `actions` e o JSON integral que o servidor enviou, além dos
metadados da `ScreenResponse`. Implementado no wrapper `<Block>`, então nenhum componente
de bloco precisou mudar e blocos futuros ganham inspeção de graça. Com o modo ligado, um
bloco sem renderer **aparece** em vez de sumir — a degradação graciosa fica visível, que é
o argumento do SDUI na prática.

3. Logística Verde e Validação

- **Distância (MVP):** **Haversine** em Python sobre **centroides por prefixo de CEP** (mediana de `lat`/`lng` por `geolocation_zip_code_prefix` derivada no ETL Olist).
- **SFD:** “menor distância factível” = geodésica do modelo (sem roteamento rodoviário completo no MVP).
- **Emissão:** \(E = d \cdot w \cdot EF\) com \(d\) km, \(w\) em toneladas, \(EF = 0,102\) kg CO₂/(t·km) (GHG Protocol).
- **Selo na UI:** distância **\< 100 km** ⇒ elegível a selo (PRD); lógica na fatia **`green_logistics`**, dados no SDUI (`SustainabilityProps` / `ProductCard`). **Sprint 3:** label do selo inclui **CO₂ estimado** quando `product_weight_g` disponível (`E = d · w · FE`).
- **Home consciente:** query `context=conscious_buyer` ordena produtos por **proximidade** ao `customer_zip_prefix` (sem filtro rígido de categoria).
- **Detalhe do produto (Sprint 6):** `GET /api/v1/products/{id}?customer_zip_prefix=...` devolve `product_detail` + `impact_banner`. `rating`/`review_count` são **reais**, agregados de `olist_order_reviews` no ETL (a nota no Olist é do **pedido**, não do item — atribuí-la ao produto é aproximação, mas o número não é inventado); `seller_city`/`seller_state` vêm de `olist_sellers`. **Descrição e tags de sustentabilidade ficaram de fora**: o dataset tem só o comprimento da descrição e nenhuma tag.
- **Busca e categorias (Sprint 5):** `GET /home` aceita `q` e `category`. A busca é sobre **`product_category_name`** — o Olist não tem nome de produto, e o `title` do card já é a categoria formatada. Acentos são dobrados no termo do usuário; `%` e `_` escapados antes do `ILIKE`.
- **Checkout simulado (Sprint 3, carrinho na Sprint 5):** `POST /api/v1/checkout/simulate` — body `{ customer_zip_prefix, items[], delivery_option? }` com 1 a 20 itens `{ product_id, quantity }`; resposta `ScreenResponse` com `checkout_summary` + `delivery_options` + `shipment_breakdown` + `impact_banner`.
- **Modalidades de entrega (Sprint 4):** `express` / `standard` / `green` em `green_logistics/delivery_options.py`. `standard` é o frete real da amostra **sem fator**; os fatores das outras duas são **cenário declarado**, não dado do Olist — o dataset não tem modalidade nem transportadora. A ressalva viaja no campo `note` do bloco.
- **Agregação por vendedor (Sprint 5):** uma remessa por `seller_id`, pagando **um** frete (o maior item do grupo). **Consolidar não reduz CO₂:** o modelo é linear na massa, então `Σᵢ (d · wᵢ · FE) = d · (Σᵢ wᵢ) · FE`. Agrupar economiza frete, não emissão. O que o carrinho entrega é o **`co2_share`** por remessa — qual vendedor domina a pegada. Ver `docs/sprint5-handoff.md` para por que um termo fixo por remessa foi descartado.
- **Exibição do CO₂:** `format_co2` (backend) e `co2Label` (frontend) aplicam a mesma regra — gramas abaixo de 10 g, kg acima, vírgula pt-BR. Com a amostra de 10k as distâncias caíram e um `.2f` em kg imprimia `0,00 kg` em todo selo.
- **Evolução futura (opcional):** migração para PostGIS (`ST_DistanceSphere`) quando custos de query justificarem indexação espacial.

4. Performance, Cache e Hidratação

- **Meta:** TTFB **\< 200 ms**; backend **async**; cache onde couber.
- **SDUI:** 1ª resposta com blocos “above the fold”; restante em **resposta(s) seguinte(s)** ou paginação (documentar o endpoint/decisão no repo).
- **Redis:** cache de **distâncias/CEP** e **fragmentos JSON SDUI** alinhados a `version` do bloco e `schema_version` da tela.

5. Stack de Referência

- **Python 3.12+, FastAPI (async), Pydantic v2**, servidor ASGI (ex. Uvicorn).
- **PostgreSQL** (PostGIS = evolução futura opcional), **Redis** (cache em fase futura).
- **Front:** **Next.js 16 (App Router) em `web/`** — renderiza por `type` via `REGISTRY`, lê `props`, executa `actions`. As telas vêm de Server Components; só o executor de `actions` e o carrinho rodam no cliente.
- **CORS (dev):** habilitado quando `APP_ENV=development` para front local; em desenvolvimento o `web/next.config.ts` faz rewrite de `/api/v1/*` e o CORS nem entra no caminho.
- **Testes:** `pytest` (backend, sem Postgres — `dependency_overrides` + monkeypatch) e **Vitest** em `web/`. CI em `.github/workflows/ci.yml`.
- **E2E (Sprint 6):** um teste **Playwright** (`web/e2e/journey.spec.ts`, `npm run e2e`) percorre a jornada da defesa contra a **pilha real** — CEP → busca → categoria → `product_detail` → carrinho → `checkout/simulate` → troca de modalidade. Verifica que frete, CO₂ e selo se movem **juntos e na direção certa** (`green` = 0,85× preço e 0,6× emissão; `express` = 1,6× e 2,5×), que é a afirmação que o bloco `delivery_options` faz na tela. Fora do CI de propósito: `data/raw/` é gitignored, então o runner não tem os CSVs para popular o banco.
