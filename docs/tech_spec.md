Technical Specification: SDUI Engine & Backend
1. Arquitetura (Vertical Slice)
    - /src/features/home_contextual: Composição de layouts por categoria.
    - /src/features/green_logistics: Motor de geoprocessamento e cálculo de CO2.
    - /src/features/checkout: Checkout simulado (Sprint 3: `POST /api/v1/checkout/simulate`; sem pagamento real).
    - /src/features/orchestrator: Gerenciamento de versões de componentes e roteamento dinâmico.
    
2. Contrato SDUI (Schemas Pydantic)

Cada bloco enviado ao cliente segue o envelope **`{ type, version, props, actions }`**: `props` carrega apenas dados de apresentação; `actions` define comportamentos interpretados pelo app (PRD: *Sistema de Ações Dinâmicas*). O campo `version` por bloco permite compatibilidade quando o contrato evoluir (alinhado ao fatiamento `orchestrator`).

Validação com **Pydantic v2** e **discriminated unions** em `UIComponent` e em cada item de `actions`, para o OpenAPI refletir variantes com clareza.

**Sprint 3** adiciona blocos `checkout_summary` e `impact_banner` (tela de checkout simulado). Até a implementação, o código em `src/schemas/sdui.py` pode conter apenas `hero_banner` e `product_card`.

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


# --- Props (somente apresentação / dados para renderizar) ---


class SustainabilityProps(BaseModel):
    label: str
    impact_level: Literal["green", "neutral"] = "green"
    icon: str | None = None


class ProductCardProps(BaseModel):
    product_id: str
    price: float
    title: str | None = None
    image_url: str | None = None
    badge: SustainabilityProps | None = None


class HeroBannerProps(BaseModel):
    title: str
    subtitle: str | None = None
    image_url: str


# --- Blocos de UI (envelope por tipo de componente) ---


class ProductCardBlock(BaseModel):
    type: Literal["product_card"] = "product_card"
    version: int = 1
    props: ProductCardProps
    actions: list[UIAction] = Field(default_factory=list)


class HeroBannerBlock(BaseModel):
    type: Literal["hero_banner"] = "hero_banner"
    version: int = 1
    props: HeroBannerProps
    actions: list[UIAction] = Field(default_factory=list)


class CheckoutSummaryProps(BaseModel):
    product_id: str
    title: str | None = None
    quantity: int
    unit_price: float
    subtotal: float
    freight: float
    total: float


class ImpactBannerProps(BaseModel):
    distance_km: float | None = None
    co2_kg: float | None = None
    badge: SustainabilityProps | None = None
    message: str


class CheckoutSummaryBlock(BaseModel):
    type: Literal["checkout_summary"] = "checkout_summary"
    version: int = 1
    props: CheckoutSummaryProps
    actions: list[UIAction] = Field(default_factory=list)


class ImpactBannerBlock(BaseModel):
    type: Literal["impact_banner"] = "impact_banner"
    version: int = 1
    props: ImpactBannerProps
    actions: list[UIAction] = Field(default_factory=list)


UIComponent = Annotated[
    Union[
        ProductCardBlock,
        HeroBannerBlock,
        CheckoutSummaryBlock,
        ImpactBannerBlock,
    ],
    Field(discriminator="type"),
]


class ScreenResponse(BaseModel):
    schema_version: int = 1
    screen_id: str
    context: str
    components: list[UIComponent]

```

3. Logística Verde e Validação

- **Distância (MVP):** **Haversine** em Python sobre **centroides por prefixo de CEP** (mediana de `lat`/`lng` por `geolocation_zip_code_prefix` derivada no ETL Olist).
- **SFD:** “menor distância factível” = geodésica do modelo (sem roteamento rodoviário completo no MVP).
- **Emissão:** \(E = d \cdot w \cdot EF\) com \(d\) km, \(w\) em toneladas, \(EF = 0,102\) kg CO₂/(t·km) (GHG Protocol).
- **Selo na UI:** distância **\< 100 km** ⇒ elegível a selo (PRD); lógica na fatia **`green_logistics`**, dados no SDUI (`SustainabilityProps` / `ProductCard`). **Sprint 3:** label do selo inclui **CO₂ estimado** quando `product_weight_g` disponível (`E = d · w · FE`).
- **Home consciente:** query `context=conscious_buyer` ordena produtos por **proximidade** ao `customer_zip_prefix` (sem filtro rígido de categoria).
- **Checkout simulado (Sprint 3):** `POST /api/v1/checkout/simulate` — body `{ customer_zip_prefix, product_id, quantity }`; resposta `ScreenResponse` com blocos `checkout_summary` + `impact_banner` (frete da amostra Olist, distância, CO₂, selo).
- **Evolução futura (opcional):** migração para PostGIS (`ST_DistanceSphere`) quando custos de query justificarem indexação espacial.

4. Performance, Cache e Hidratação

- **Meta:** TTFB **\< 200 ms**; backend **async**; cache onde couber.
- **SDUI:** 1ª resposta com blocos “above the fold”; restante em **resposta(s) seguinte(s)** ou paginação (documentar o endpoint/decisão no repo).
- **Redis:** cache de **distâncias/CEP** e **fragmentos JSON SDUI** alinhados a `version` do bloco e `schema_version` da tela.

5. Stack de Referência

- **Python 3.12+, FastAPI (async), Pydantic v2**, servidor ASGI (ex. Uvicorn).
- **PostgreSQL** (PostGIS = evolução futura opcional), **Redis** (cache em fase futura).
- **Front (referência):** renderiza por `type`, lê `props`, executa `actions`, hidrata em fases se o backend entregar em etapas.
- **CORS (dev):** habilitado quando `APP_ENV=development` para front local (Vite/React); ver Sprint 3.
