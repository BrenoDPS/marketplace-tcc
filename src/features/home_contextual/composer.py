"""Composicao da Home contextual (Sprint 2 - dados reais Olist + selo verde).

Heros sao estaticos por contexto. Os ProductCards vem do Postgres (amostra
ETL) e o `badge` e injetado pela fatia `green_logistics` (Haversine sobre
centroides de CEP). Sem mocks de product_id.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.green_logistics.service import (
    build_badge_for_pair,
    compute_distance_km,
)
from src.features.home_contextual.repository import (
    ProductRow,
    category_for_context,
    fetch_products_for_home,
)
from src.schemas.sdui import (
    ApiCallAction,
    ApiCallPayload,
    HeroBannerBlock,
    HeroBannerProps,
    NavigateAction,
    NavigatePayload,
    OpenModalAction,
    OpenModalPayload,
    ProductCardBlock,
    ProductCardProps,
    ScreenResponse,
    UIComponent,
)

CONSCIOUS_BUYER_CONTEXT = "conscious_buyer"
_DEFAULT_LIMIT = 6
_CONSCIOUS_POOL_LIMIT = 24

_HEROS: dict[str, HeroBannerBlock] = {
    "electronics_expert": HeroBannerBlock(
        props=HeroBannerProps(
            title="Tech Deals",
            subtitle="Eletronicos com entrega rapida",
            image_url="https://placeholders.dev/800x400?text=Tech+Deals",
        ),
        actions=[NavigateAction(payload=NavigatePayload(path="/categories/electronics"))],
    ),
    "beauty_lover": HeroBannerBlock(
        props=HeroBannerProps(
            title="Semana da Beleza",
            subtitle="Ate 40% OFF em skincare",
            image_url="https://placeholders.dev/800x400?text=Beauty+Sale",
        ),
        actions=[NavigateAction(payload=NavigatePayload(path="/categories/beauty"))],
    ),
    CONSCIOUS_BUYER_CONTEXT: HeroBannerBlock(
        props=HeroBannerProps(
            title="Consumo consciente",
            subtitle="Entregas locais com menor impacto ambiental",
            image_url="https://placeholders.dev/800x400?text=Entregas+Locais",
        ),
        actions=[NavigateAction(payload=NavigatePayload(path="/explore"))],
    ),
}

_DEFAULT_HERO = HeroBannerBlock(
    props=HeroBannerProps(
        title="Olist Marketplace",
        subtitle="Compre de pequenos vendedores brasileiros",
        image_url="https://placeholders.dev/800x400?text=Olist",
    ),
    actions=[NavigateAction(payload=NavigatePayload(path="/explore"))],
)


def _hero_for(context: str) -> HeroBannerBlock:
    return _HEROS.get(context, _DEFAULT_HERO)


def _title_for(product_id: str, category: str | None) -> str:
    if category:
        return category.replace("_", " ").title()
    return product_id


async def _rank_by_proximity(
    session: AsyncSession,
    products: list[ProductRow],
    customer_zip_prefix: str,
    limit: int,
) -> list[ProductRow]:
    """Ordena produtos por distancia ascendente (sem centroide vai para o fim)."""
    INFINITY = float("inf")

    async def _distance(product: ProductRow) -> float:
        distance = await compute_distance_km(
            session, customer_zip_prefix, product.seller_zip_prefix
        )
        return distance if distance is not None else INFINITY

    scored = [(await _distance(product), product) for product in products]
    scored.sort(key=lambda item: item[0])
    return [product for _, product in scored[:limit]]


def _checkout_action() -> ApiCallAction:
    return ApiCallAction(
        payload=ApiCallPayload(
            method="POST",
            path="/api/v1/checkout/simulate",
            body_key="checkout",
        )
    )


async def compose_home(
    session: AsyncSession,
    context: str,
    customer_zip_prefix: str,
) -> ScreenResponse:
    if context == CONSCIOUS_BUYER_CONTEXT:
        pool = await fetch_products_for_home(
            session, category=None, limit=_CONSCIOUS_POOL_LIMIT
        )
        products = await _rank_by_proximity(
            session, pool, customer_zip_prefix, limit=_DEFAULT_LIMIT
        )
    else:
        products = await fetch_products_for_home(
            session, category=category_for_context(context), limit=_DEFAULT_LIMIT
        )

    components: list[UIComponent] = [_hero_for(context)]
    for product in products:
        _, badge = await build_badge_for_pair(
            session,
            customer_zip_prefix=customer_zip_prefix,
            seller_zip_prefix=product.seller_zip_prefix,
            weight_g=product.weight_g,
        )
        components.append(
            ProductCardBlock(
                props=ProductCardProps(
                    product_id=product.product_id,
                    price=product.price,
                    title=_title_for(product.product_id, product.category),
                    image_url=None,
                    badge=badge,
                ),
                actions=[
                    OpenModalAction(
                        payload=OpenModalPayload(
                            modal_id="product_detail",
                            title=None,
                        )
                    ),
                    _checkout_action(),
                ],
            )
        )

    return ScreenResponse(
        screen_id="home",
        context=context,
        components=components,
    )
