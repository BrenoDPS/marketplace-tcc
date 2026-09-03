"""Composicao da tela SDUI do checkout simulado (Sprint 3).

Reutiliza a fatia `green_logistics` para distancia, CO2 e selo, mantendo
coerencia com a Home. Sem pagamento, estoque ou persistencia de pedido.

Sprint 4: a tela passa a trazer `delivery_options`. A modalidade escolhida
manda em frete, CO2 e selo — os tres saem do MESMO `mode`, senao a tela se
contradiz (selo dizendo um numero, comparativo dizendo outro).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.checkout.repository import CheckoutProductRow
from src.features.green_logistics.delivery_options import (
    NOTE,
    build_delivery_options,
    mode_co2_kg,
    resolve_mode,
)
from src.features.green_logistics.service import build_badge_for_pair
from src.schemas.sdui import (
    ApiCallAction,
    ApiCallPayload,
    CheckoutSummaryBlock,
    CheckoutSummaryProps,
    DeliveryOptionsBlock,
    DeliveryOptionsProps,
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


def _impact_message(
    distance_km: float | None, badge_present: bool, mode_label: str
) -> str:
    if distance_km is None:
        return "Nao foi possivel estimar a distancia desta entrega."
    if badge_present:
        return (
            f"Entrega local (~{distance_km:.0f} km) na modalidade {mode_label}, "
            "com menor impacto ambiental."
        )
    return f"Entrega a ~{distance_km:.0f} km do vendedor na modalidade {mode_label}."


async def compose_checkout(
    session: AsyncSession,
    product: CheckoutProductRow,
    customer_zip_prefix: str,
    quantity: int,
    delivery_option: str | None = None,
) -> ScreenResponse:
    mode = resolve_mode(delivery_option)

    # A emissao acompanha a massa embarcada: 2 unidades pesam 2x. O frete nao
    # e multiplicado — na amostra ele e o valor de um envio (decisao Sprint 3).
    shipped_weight_g = (product.weight_g or 0.0) * quantity or None

    distance_km, badge = await build_badge_for_pair(
        session,
        customer_zip_prefix=customer_zip_prefix,
        seller_zip_prefix=product.seller_zip_prefix,
        weight_g=shipped_weight_g,
        co2_factor=mode.co2_factor,
    )

    co2_kg = mode_co2_kg(mode, distance_km, shipped_weight_g)

    # Arredonda em centavos: float acumula residuo (199.8 + 33.9 sai
    # 233.70000000000002) e esses valores vao crus no JSON da API.
    subtotal = round(product.unit_price * quantity, 2)
    freight = round(product.freight_value * mode.price_factor, 2)
    total = round(subtotal + freight, 2)

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
        DeliveryOptionsBlock(
            props=DeliveryOptionsProps(
                product_id=product.product_id,
                quantity=quantity,
                distance_km=distance_km,
                selected_id=mode.id,
                options=build_delivery_options(
                    base_freight=product.freight_value,
                    distance_km=distance_km,
                    weight_g=shipped_weight_g,
                    selected_id=mode.id,
                ),
                note=NOTE,
            ),
            # Uma acao para o bloco todo: o cliente devolve o id da opcao
            # clicada e a MESMA tela e recomposta pelo servidor.
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
                message=_impact_message(distance_km, badge is not None, mode.label),
            ),
        ),
    ]

    return ScreenResponse(
        screen_id="checkout_simulate",
        context="checkout",
        components=components,
    )
