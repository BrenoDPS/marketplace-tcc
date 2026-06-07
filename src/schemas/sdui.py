"""Contrato SDUI (Server-Driven UI) — Fase 1.

Implementa o envelope `{ type, version, props, actions }` definido em
docs/tech_spec.md §2. Mantém uma unica `ScreenResponse`; cache Redis real,
PostGIS, ingestao Olist e wiring real das `actions` ficam para Fase 2.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Acoes (comportamento definido pelo servidor)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Props (apresentacao / dados para renderizar)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Blocos de UI (envelope: type + version + props + actions)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Resposta de tela
# ---------------------------------------------------------------------------

class ScreenResponse(BaseModel):
    schema_version: int = 1
    screen_id: str
    context: str
    components: list[UIComponent]
