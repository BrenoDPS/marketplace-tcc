"""Acesso async aos dados do produto para o checkout simulado.

Frete: usa o `freight_value` da PRIMEIRA linha de `order_items` daquele
`product_id` na amostra (decisao fechada no handoff da Sprint 3).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import CepCentroid, Offer, Product, Seller


@dataclass(frozen=True, slots=True)
class AlternativeRow:
    """Candidato a substituto: mesmo `category`, outro vendedor.

    Traz `lat`/`lng` do centroide do vendedor para o Haversine acontecer em
    Python (decisao da Sprint 2) sem uma consulta por candidato.
    """

    product_id: str
    category: str | None
    unit_price: float
    weight_g: float | None
    seller_id: str
    lat: float
    lng: float


@dataclass(frozen=True, slots=True)
class CheckoutProductRow:
    product_id: str
    seller_id: str
    seller_zip_prefix: str
    unit_price: float
    freight_value: float
    weight_g: float | None
    category: str | None


async def fetch_products_for_checkout(
    session: AsyncSession, product_ids: list[str]
) -> dict[str, CheckoutProductRow]:
    """Mapa `product_id` -> oferta default daquele produto.

    Uma consulta para o carrinho inteiro: com 20 itens, buscar um a um seriam
    20 round-trips para montar uma tela so. Produto ausente simplesmente nao
    aparece no mapa — quem chama decide se isso e 404.
    """
    if not product_ids:
        return {}

    stmt = (
        select(
            Offer.product_id,
            Offer.seller_id,
            Seller.seller_zip_code_prefix,
            Offer.price,
            Offer.freight_value,
            Product.product_weight_g,
            Product.product_category_name,
        )
        .join(Product, Product.product_id == Offer.product_id)
        .join(Seller, Seller.seller_id == Offer.seller_id)
        .where(Offer.product_id.in_(set(product_ids)))
        .where(Offer.is_default)
    )
    result = await session.execute(stmt)

    out: dict[str, CheckoutProductRow] = {}
    for product_id, seller_id, zip_prefix, price, freight, weight_g, category in result:
        out[product_id] = CheckoutProductRow(
            product_id=product_id,
            seller_id=seller_id,
            seller_zip_prefix=zip_prefix,
            unit_price=float(price),
            freight_value=float(freight) if freight is not None else 0.0,
            weight_g=float(weight_g) if weight_g is not None else None,
            category=category,
        )
    return out


# ponytail: pool fixo em vez de ordenar por distancia no banco — ordenar
# exigiria Haversine em SQL, e a decisao da Sprint 2 e manter o calculo em
# Python. Com 6,5k produtos o pool cobre as categorias com folga; se o dataset
# crescer, avaliar PostGIS (ja esta no roadmap).
ALTERNATIVE_POOL_LIMIT = 300


async def fetch_alternative_candidates(
    session: AsyncSession,
    categories: list[str],
    exclude_seller_ids: list[str],
    limit: int = ALTERNATIVE_POOL_LIMIT,
) -> list[AlternativeRow]:
    """Produtos das mesmas categorias vendidos por OUTROS vendedores.

    O JOIN com `cep_centroids` traz o centroide do vendedor na mesma consulta:
    sem ele seriam N idas ao banco so para medir distancia dos candidatos.
    Vendedor sem centroide cai fora do JOIN — e nao daria para medir mesmo.
    """
    if not categories:
        return []

    stmt = (
        select(
            Offer.product_id,
            Product.product_category_name,
            Offer.price,
            Product.product_weight_g,
            Offer.seller_id,
            CepCentroid.lat,
            CepCentroid.lng,
        )
        .join(Product, Product.product_id == Offer.product_id)
        .join(Seller, Seller.seller_id == Offer.seller_id)
        .join(CepCentroid, CepCentroid.zip_prefix == Seller.seller_zip_code_prefix)
        .where(Product.product_category_name.in_(set(categories)))
        .where(Product.product_weight_g.is_not(None))
        .where(Offer.is_default)
        .order_by(Offer.product_id)
        .limit(limit)
    )
    if exclude_seller_ids:
        stmt = stmt.where(Offer.seller_id.not_in(set(exclude_seller_ids)))

    result = await session.execute(stmt)

    out: list[AlternativeRow] = []
    for product_id, category, price, weight_g, seller_id, lat, lng in result:
        out.append(
            AlternativeRow(
                product_id=product_id,
                category=category,
                unit_price=float(price),
                weight_g=float(weight_g) if weight_g is not None else None,
                seller_id=seller_id,
                lat=float(lat),
                lng=float(lng),
            )
        )
    return out
