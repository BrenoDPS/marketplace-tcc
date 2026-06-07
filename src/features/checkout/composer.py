"""Composicao da tela SDUI do checkout simulado (Sprint 3).

Reutiliza a fatia `green_logistics` para distancia, CO2 e selo, mantendo
coerencia com a Home. Sem pagamento, estoque ou persistencia de pedido.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.checkout.repository import CheckoutProductRow
from src.features.green_logistics.co2 import calculate_co2_kg
from src.features.green_logistics.service import build_badge_for_pair
from src.schemas.sdui import (
    CheckoutSummaryBlock,
    CheckoutSummaryProps,
    ImpactBannerBlock,
    ImpactBannerProps,
    NavigateAction,
    NavigatePayload,
    ScreenResponse,
    UIComponent,
)


def _title_for(product: CheckoutProductRow) -> str:
    if product.category:
        return product.category.replace("_", " ").title()
    return product.product_id


def _impact_message(distance_km: float | None, badge_present: bool) -> str:
    if distance_km is None:
        return "Nao foi possivel estimar a distancia desta entrega."
    if badge_present:
        return f"Entrega local (~{distance_km:.0f} km) com menor impacto ambiental."
    return f"Entrega a ~{distance_km:.0f} km do vendedor."


async def compose_checkout(
    session: AsyncSession,
    product: CheckoutProductRow,
    customer_zip_prefix: str,
    quantity: int,
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

    subtotal = product.unit_price * quantity
    freight = product.freight_value
    total = subtotal + freight

    components: list[UIComponent] = [
        CheckoutSummaryBlock(
            props=CheckoutSummaryProps(
                product_id=product.product_id,
                title=_title_for(product),
                quantity=quantity,
                unit_price=product.unit_price,
                subtotal=subtotal,
                freight=freight,
                total=total,
            ),
            actions=[
                NavigateAction(
                    payload=NavigatePayload(path=f"/?customer_zip_prefix={customer_zip_prefix}")
                ),
            ],
        ),
        ImpactBannerBlock(
            props=ImpactBannerProps(
                distance_km=distance_km,
                co2_kg=co2_kg,
                badge=badge,
                message=_impact_message(distance_km, badge is not None),
            ),
        ),
    ]

    return ScreenResponse(
        screen_id="checkout_simulate",
        context="checkout",
        components=components,
    )
