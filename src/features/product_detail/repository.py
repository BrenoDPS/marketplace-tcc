"""Acesso async aos dados do detalhe do produto (Sprint 6)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Offer, Product, Seller


@dataclass(frozen=True, slots=True)
class ProductDetailRow:
    product_id: str
    category: str | None
    weight_g: float | None
    rating: float | None
    review_count: int
    unit_price: float
    seller_id: str
    seller_zip_prefix: str
    seller_city: str | None
    seller_state: str | None
    # Volume do dataset; entra no CO2 como massa cubada quando ela supera
    # a real. Default `None` para quem so tem massa (fixtures, chamadas antigas).
    volume_cm3: float | None = None


async def fetch_product_offers(
    session: AsyncSession, product_id: str
) -> list[ProductDetailRow]:
    """TODAS as ofertas do produto — uma linha por vendedor.

    O detalhe mostrava a oferta `is_default`, que e um desempate arbitrario
    herdado de quando o catalogo saia de `order_items`. Para 579 produtos da
    amostra isso significava esconder origens: o mesmo item sai de Recife ou de
    Maringa, a 2483 km de distancia, e a tela anunciava uma delas sem dizer que
    havia outra.

    Quem escolhe e o composer, que sabe onde o comprador esta. Lista vazia
    significa produto inexistente na amostra — quem chama decide se e 404.
    """
    stmt = (
        select(
            Product.product_id,
            Product.product_category_name,
            Product.product_weight_g,
            Product.product_volume_cm3,
            Product.rating,
            Product.review_count,
            Offer.price,
            Offer.seller_id,
            Seller.seller_zip_code_prefix,
            Seller.seller_city,
            Seller.seller_state,
        )
        .join(Offer, Offer.product_id == Product.product_id)
        .join(Seller, Seller.seller_id == Offer.seller_id)
        .where(Product.product_id == product_id)
        # Desempate estavel entre ofertas equidistantes.
        .order_by(Offer.seller_id)
    )
    rows = (await session.execute(stmt)).all()

    return [
        ProductDetailRow(
            product_id=pid,
            category=category,
            weight_g=float(weight_g) if weight_g is not None else None,
            volume_cm3=float(volume) if volume is not None else None,
            rating=float(rating) if rating is not None else None,
            review_count=int(review_count or 0),
            unit_price=float(price),
            seller_id=seller_id,
            seller_zip_prefix=zip_prefix,
            seller_city=city,
            seller_state=state,
        )
        for (
            pid,
            category,
            weight_g,
            volume,
            rating,
            review_count,
            price,
            seller_id,
            zip_prefix,
            city,
            state,
        ) in rows
    ]
