"""Composicao da tela SDUI do checkout simulado (Sprint 3).

Reutiliza a fatia `green_logistics` para distancia, CO2 e selo, mantendo
coerencia com a Home. Sem pagamento, estoque ou persistencia de pedido.

Sprint 4: a tela passa a trazer `delivery_options`. A modalidade escolhida
manda em frete, CO2 e selo — os tres saem do MESMO `mode`, senao a tela se
contradiz (selo dizendo um numero, comparativo dizendo outro).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.checkout.alternatives import build_alternatives
from src.features.checkout.repository import (
    CheckoutProductRow,
    fetch_alternative_candidates,
)
from src.features.green_logistics.repository import get_centroid
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
    CartLineProps,
    CheckoutSummaryBlock,
    CheckoutSummaryProps,
    DeliveryOptionsBlock,
    DeliveryOptionsProps,
    ImpactBannerBlock,
    ImpactBannerProps,
    NavigateAction,
    NavigatePayload,
    ScreenResponse,
    ShipmentBreakdownBlock,
    ShipmentBreakdownProps,
    ShipmentProps,
    UIComponent,
)

# Uma remessa por vendedor paga UM frete: o maior item da remessa dimensiona o
# envio. E uma simplificacao declarada — a amostra tem `freight_value` por
# `order_item` e nenhuma nocao de remessa —, mas somar os fretes suporia que
# cada item viaja sozinho, o que anularia qualquer efeito de consolidacao.
CONSOLIDATION_NOTE = (
    "Uma remessa por vendedor: itens do mesmo vendedor pagam um frete só, o "
    "maior da remessa. A emissão não cai por agrupar — ela é proporcional à "
    "massa e à distância. O que o agrupamento revela é qual vendedor domina a "
    "pegada do carrinho."
)


def _title_for(product: CheckoutProductRow) -> str:
    if product.category:
        return product.category.replace("_", " ").title()
    return product.product_id


def _impact_message(shipments: list[ShipmentProps], mode_label: str) -> str:
    if len(shipments) > 1:
        local = sum(1 for s in shipments if s.badge is not None)
        base = (
            f"{len(shipments)} remessas na modalidade {mode_label}"
            f" — {local} de entrega local."
        )
        # Sem a remessa dominante o total vira um numero solto; com ela, o
        # carrinho aponta onde mexer para reduzir a pegada.
        ranked = [s for s in shipments if s.co2_share is not None]
        if ranked:
            worst = max(ranked, key=lambda s: s.co2_share or 0.0)
            base += f" Uma delas responde por {(worst.co2_share or 0) * 100:.0f}% do CO₂."
        return base

    distance_km = shipments[0].distance_km if shipments else None
    if distance_km is None:
        return "Nao foi possivel estimar a distancia desta entrega."
    if shipments[0].badge is not None:
        return (
            f"Entrega local (~{distance_km:.0f} km) na modalidade {mode_label}, "
            "com menor impacto ambiental."
        )
    return f"Entrega a ~{distance_km:.0f} km do vendedor na modalidade {mode_label}."


def _checkout_action() -> ApiCallAction:
    return ApiCallAction(
        payload=ApiCallPayload(
            method="POST",
            path="/api/v1/checkout/simulate",
            body_key="checkout",
        )
    )


def _group_by_seller(
    lines: list[tuple[CheckoutProductRow, int]],
) -> dict[str, list[tuple[CheckoutProductRow, int]]]:
    """Uma remessa por vendedor, na ordem em que os itens entraram no carrinho."""
    groups: dict[str, list[tuple[CheckoutProductRow, int]]] = {}
    for product, quantity in lines:
        groups.setdefault(product.seller_id, []).append((product, quantity))
    return groups


async def _attach_alternatives(
    session: AsyncSession,
    shipments: list[ShipmentProps],
    groups: dict[str, list[tuple[CheckoutProductRow, int]]],
    customer_zip_prefix: str,
    cart_product_ids: set[str],
    co2_factor: float,
) -> list[ShipmentProps]:
    """Anexa sugestoes de troca a remessa de MAIOR emissao (a primeira).

    So a pior: sugerir troca nas outras seria ruido — mexer nelas quase nao
    move a pegada, e a tela ja tem resumo, modalidades e remessas.
    """
    if not shipments:
        return shipments

    worst = shipments[0]
    if worst.co2_kg is None or worst.distance_km is None:
        return shipments

    customer = await get_centroid(session, customer_zip_prefix)
    if customer is None:
        return shipments

    group = groups[worst.seller_id]
    categories = [p.category for p, _ in group if p.category]
    candidates = await fetch_alternative_candidates(
        session,
        categories=categories,
        exclude_seller_ids=list(groups),
    )
    alternatives = build_alternatives(
        group,
        current_distance_km=worst.distance_km,
        candidates=candidates,
        customer_lat=customer[0],
        customer_lng=customer[1],
        co2_factor=co2_factor,
        cart_product_ids=cart_product_ids,
    )
    if not alternatives:
        return shipments

    # Cada sugestao carrega a acao de re-simular: o cliente troca o item no
    # carrinho e a MESMA tela e recomposta pelo servidor, igual ao que o
    # `delivery_options` faz ao mudar de modalidade.
    alternatives = [
        a.model_copy(update={"actions": [_checkout_action()]}) for a in alternatives
    ]
    return [worst.model_copy(update={"alternatives": alternatives}), *shipments[1:]]


async def compose_checkout(
    session: AsyncSession,
    lines: list[tuple[CheckoutProductRow, int]],
    customer_zip_prefix: str,
    delivery_option: str | None = None,
) -> ScreenResponse:
    mode = resolve_mode(delivery_option)

    groups = _group_by_seller(lines)

    shipments: list[ShipmentProps] = []
    base_freight_total = 0.0
    for seller_id, group in groups.items():
        # A emissao acompanha a massa embarcada: 2 unidades pesam 2x, e a
        # remessa carrega a soma dos itens daquele vendedor.
        weight_g = sum((p.weight_g or 0.0) * q for p, q in group) or None
        # Um frete por remessa, dimensionado pelo maior item (ver
        # CONSOLIDATION_NOTE). Com um item so, e o frete da Sprint 3 intacto.
        base_freight = max(p.freight_value for p, _ in group)
        base_freight_total += base_freight

        distance_km, badge = await build_badge_for_pair(
            session,
            customer_zip_prefix=customer_zip_prefix,
            seller_zip_prefix=group[0][0].seller_zip_prefix,
            weight_g=weight_g,
            co2_factor=mode.co2_factor,
        )
        shipments.append(
            ShipmentProps(
                seller_id=seller_id,
                product_ids=[p.product_id for p, _ in group],
                total_quantity=sum(q for _, q in group),
                weight_g=weight_g,
                distance_km=distance_km,
                freight=round(base_freight * mode.price_factor, 2),
                co2_kg=mode_co2_kg(mode, distance_km, weight_g),
                badge=badge,
            )
        )

    co2_values = [s.co2_kg for s in shipments if s.co2_kg is not None]
    co2_kg = sum(co2_values) if co2_values else None
    if co2_kg:
        shipments = [
            s.model_copy(update={"co2_share": s.co2_kg / co2_kg})
            if s.co2_kg is not None
            else s
            for s in shipments
        ]

    # A remessa que mais pesa vem primeiro: e onde o usuario pode agir. Sem
    # centroide (co2 None) vai para o fim, como no ranking da Home.
    shipments.sort(key=lambda s: (s.co2_kg is None, -(s.co2_kg or 0.0)))

    shipments = await _attach_alternatives(
        session,
        shipments=shipments,
        groups=groups,
        customer_zip_prefix=customer_zip_prefix,
        cart_product_ids={p.product_id for p, _ in lines},
        co2_factor=mode.co2_factor,
    )

    # Arredonda em centavos: float acumula residuo (199.8 + 33.9 sai
    # 233.70000000000002) e esses valores vao crus no JSON da API.
    subtotal = round(sum(p.unit_price * q for p, q in lines), 2)
    freight = round(sum(s.freight for s in shipments), 2)
    total = round(subtotal + freight, 2)

    # O banner agrega o carrinho; a distancia so faz sentido como numero unico
    # quando ha uma remessa. Com varias, quem detalha e o shipment_breakdown.
    distance_km = shipments[0].distance_km if len(shipments) == 1 else None
    badge = shipments[0].badge if len(shipments) == 1 else None

    # O comparativo de modalidades e sobre o carrinho inteiro. O prazo sai da
    # remessa mais distante: o pedido so esta completo quando a ultima chega.
    distances = [s.distance_km for s in shipments if s.distance_km is not None]
    weights = [s.weight_g for s in shipments if s.weight_g is not None]
    eta_distance_km = max(distances) if distances else None
    cart_weight_g = sum(weights) if weights else None

    components: list[UIComponent] = [
        CheckoutSummaryBlock(
            props=CheckoutSummaryProps(
                items=[
                    CartLineProps(
                        product_id=p.product_id,
                        title=_title_for(p),
                        quantity=q,
                        unit_price=p.unit_price,
                        line_total=round(p.unit_price * q, 2),
                    )
                    for p, q in lines
                ],
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
                distance_km=eta_distance_km,
                selected_id=mode.id,
                options=build_delivery_options(
                    base_freight=base_freight_total,
                    distance_km=eta_distance_km,
                    weight_g=cart_weight_g,
                    selected_id=mode.id,
                ),
                note=NOTE,
            ),
            # Uma acao para o bloco todo: o cliente devolve o id da opcao
            # clicada e a MESMA tela e recomposta pelo servidor.
            actions=[_checkout_action()],
        ),
        ShipmentBreakdownBlock(
            props=ShipmentBreakdownProps(
                title="Remessas",
                shipments=shipments,
                note=CONSOLIDATION_NOTE,
            ),
        ),
        ImpactBannerBlock(
            props=ImpactBannerProps(
                distance_km=distance_km,
                co2_kg=co2_kg,
                badge=badge,
                message=_impact_message(shipments, mode.label),
            ),
        ),
    ]

    return ScreenResponse(
        screen_id="checkout_simulate",
        context="checkout",
        components=components,
    )
