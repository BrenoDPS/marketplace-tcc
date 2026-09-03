"""Composicao da tela SDUI de detalhe do produto (Sprint 6).

Ate a Sprint 5 o detalhe era a UNICA tela que o cliente montava sozinho: o
modal reaproveitava os `props` que ja tinham vindo no `product_card`. Isso era
uma excecao a tese do trabalho — se a interface e dirigida pelo servidor, o
detalhe tambem tem de ser. Agora ele vem de `GET /api/v1/products/{id}`.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.green_logistics.co2 import calculate_co2_kg
from src.features.green_logistics.service import build_badge_for_pair
from src.features.product_detail.repository import ProductDetailRow
from src.schemas.sdui import (
    ApiCallAction,
    ApiCallPayload,
    ImpactBannerBlock,
    ImpactBannerProps,
    ProductDetailBlock,
    ProductDetailProps,
    ScreenResponse,
    UIComponent,
)


def _title_for(product: ProductDetailRow) -> str:
    if product.category:
        return product.category.replace("_", " ").title()
    return product.product_id


def _impact_message(product: ProductDetailRow, distance_km: float | None) -> str:
    where = ", ".join(p for p in (product.seller_city, product.seller_state) if p)
    origem = f" ({where})" if where else ""
    if distance_km is None:
        return f"Não foi possível estimar a distância até este vendedor{origem}."
    return f"Este produto sai de ~{distance_km:.0f} km de você{origem}."


async def compose_product_detail(
    session: AsyncSession,
    product: ProductDetailRow,
    customer_zip_prefix: str,
) -> ScreenResponse:
    distance_km, badge = await build_badge_for_pair(
        session,
        customer_zip_prefix=customer_zip_prefix,
        seller_zip_prefix=product.seller_zip_prefix,
        weight_g=product.weight_g,
    )

    co2_kg: float | None = None
    if distance_km is not None and product.weight_g:
        co2_kg = calculate_co2_kg(distance_km, product.weight_g)

    components: list[UIComponent] = [
        ProductDetailBlock(
            props=ProductDetailProps(
                product_id=product.product_id,
                title=_title_for(product),
                price=product.unit_price,
                image_url=None,
                category=product.category,
                weight_g=product.weight_g,
                seller_id=product.seller_id,
                seller_city=product.seller_city,
                seller_state=product.seller_state,
                # Nota so aparece se houver pedido avaliado; nunca preenchida
                # com um valor "plausivel".
                rating=product.rating if product.review_count else None,
                review_count=product.review_count,
                badge=badge,
            ),
            # A mesma acao de checkout dos cards: o cliente monta o carrinho e
            # decide QUANDO chamar; o servidor segue dizendo COMO.
            actions=[
                ApiCallAction(
                    payload=ApiCallPayload(
                        method="POST",
                        path="/api/v1/checkout/simulate",
                        body_key="checkout",
                    )
                ),
            ],
        ),
        ImpactBannerBlock(
            props=ImpactBannerProps(
                distance_km=distance_km,
                co2_kg=co2_kg,
                badge=badge,
                message=_impact_message(product, distance_km),
            ),
        ),
    ]

    return ScreenResponse(
        screen_id="product_detail",
        context="product",
        components=components,
    )
