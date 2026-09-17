"""Composicao da tela SDUI de detalhe do produto (Sprint 6).

Ate a Sprint 5 o detalhe era a UNICA tela que o cliente montava sozinho: o
modal reaproveitava os `props` que ja tinham vindo no `product_card`. Isso era
uma excecao a tese do trabalho — se a interface e dirigida pelo servidor, o
detalhe tambem tem de ser. Agora ele vem de `GET /api/v1/products/{id}`.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.green_logistics.badge import (
    RESOLUTION_FLOOR_KM,
    build_sustainability_props,
)
from src.features.green_logistics.co2 import calculate_co2_kg, format_co2
from src.features.green_logistics.service import compute_distance_km
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

INFINITY = float("inf")


def _title_for(product: ProductDetailRow) -> str:
    if product.category:
        return product.category.replace("_", " ").title()
    return product.product_id


def _origem(product: ProductDetailRow) -> str:
    where = ", ".join(p for p in (product.seller_city, product.seller_state) if p)
    return f" ({where})" if where else ""


def _impact_message(product: ProductDetailRow, distance_km: float | None) -> str:
    if distance_km is None:
        return f"Não foi possível estimar a distância até este vendedor{_origem(product)}."
    if distance_km < RESOLUTION_FLOOR_KM:
        return f"Este produto sai de um vendedor na sua região{_origem(product)}."
    return f"Este produto sai de ~{distance_km:.0f} km de você{_origem(product)}."


def _mensagem_comparativa(
    escolhida: tuple[float, ProductDetailRow],
    descartadas: list[tuple[float, ProductDetailRow]],
) -> str | None:
    """Diz o que a escolha evitou, quando havia outra origem para comparar.

    Sem isto a feature fica invisivel: a tela mostraria o vendedor mais proximo
    sem revelar que existia um mais distante — e o argumento do trabalho e
    exatamente a comparacao, nao o resultado dela.

    So compara com a PIOR origem medivel: e ela que dimensiona o que estava em
    jogo. Comparar com a mediana diria menos e exigiria explicar a mediana.
    """
    mediveis = [par for par in descartadas if par[0] != INFINITY]
    if not mediveis:
        return None

    perto_km, perto = escolhida
    if perto_km == INFINITY:
        return None
    longe_km, longe = max(mediveis, key=lambda par: par[0])
    if longe_km <= perto_km:
        return None

    # So descreve a alternativa: a frase anterior ja disse de onde sai a
    # escolhida, e repetir isso dava "um vendedor na sua regiao (recife, PE)
    # [...] contra um vendedor na sua regiao (recife, PE)".
    if len(descartadas) == 1:
        base = f"O outro vendedor deste item fica a ~{longe_km:.0f} km{_origem(longe)}."
    else:
        base = (
            f"Este item tem {len(descartadas) + 1} vendedores na amostra; "
            f"o mais distante fica a ~{longe_km:.0f} km{_origem(longe)}."
        )
    if not perto.weight_g:
        return base

    evitado = calculate_co2_kg(longe_km - perto_km, perto.weight_g)
    return f"{base} Comprar do mais próximo evita ~{format_co2(evitado)} de CO₂."


async def compose_product_detail(
    session: AsyncSession,
    offers: list[ProductDetailRow],
    customer_zip_prefix: str,
) -> ScreenResponse:
    """Escolhe a oferta mais proxima do comprador entre as do produto."""
    medidas: list[tuple[float, ProductDetailRow]] = []
    for offer in offers:
        distance = await compute_distance_km(
            session, customer_zip_prefix, offer.seller_zip_prefix
        )
        medidas.append((INFINITY if distance is None else distance, offer))
    # Estavel: a consulta ja ordena por `seller_id`, e `sort` do Python preserva
    # a ordem de entrada em empates.
    medidas.sort(key=lambda par: par[0])

    escolhida, *descartadas = medidas
    bruto, product = escolhida
    medido = None if bruto == INFINITY else bruto
    badge = (
        build_sustainability_props(medido, product.weight_g)
        if medido is not None
        else None
    )

    # Abaixo do piso de resolucao o banner nao afirma numero nenhum: o cliente
    # ja omite a linha quando o campo vem nulo, entao a regra vale para as duas
    # telas sem tocar no frontend. "Nao resolvemos" e "nao sabemos" caem no
    # mesmo nulo de proposito — a `message` distingue os dois casos em texto.
    mesma_regiao = medido is not None and medido < RESOLUTION_FLOOR_KM
    distance_km = None if mesma_regiao else medido

    co2_kg: float | None = None
    if distance_km is not None and product.weight_g:
        co2_kg = calculate_co2_kg(distance_km, product.weight_g)

    comparativo = _mensagem_comparativa(escolhida, descartadas)
    mensagem = _impact_message(product, medido)
    if comparativo:
        mensagem = f"{mensagem} {comparativo}"

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
                message=mensagem,
            ),
        ),
    ]

    return ScreenResponse(
        screen_id="product_detail",
        context="product",
        components=components,
    )
