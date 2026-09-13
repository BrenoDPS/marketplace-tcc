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


async def fetch_product_detail(
    session: AsyncSession, product_id: str
) -> ProductDetailRow | None:
    """Oferta default do produto, com vendedor e avaliacao.

    `is_default` e a mesma oferta que o checkout usa, e e por isso que o preco
    da tela bate com o da simulacao de compra. Quando o detalhe passar a listar
    todas as ofertas, esta funcao devolve varias e o desempate sai daqui.
    """
    stmt = (
        select(
            Product.product_id,
            Product.product_category_name,
            Product.product_weight_g,
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
        .where(Offer.is_default)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None

    (
        pid,
        category,
        weight_g,
        rating,
        review_count,
        price,
        seller_id,
        zip_prefix,
        city,
        state,
    ) = row
    return ProductDetailRow(
        product_id=pid,
        category=category,
        weight_g=float(weight_g) if weight_g is not None else None,
        rating=float(rating) if rating is not None else None,
        review_count=int(review_count or 0),
        unit_price=float(price),
        seller_id=seller_id,
        seller_zip_prefix=zip_prefix,
        seller_city=city,
        seller_state=state,
    )
