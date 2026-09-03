"""Acesso async aos dados do detalhe do produto (Sprint 6)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import OrderItem, Product, Seller


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
    """Primeira linha de `order_items` do produto, com vendedor e avaliacao.

    Mesma regra de "primeira order_item" do checkout (Sprint 3), para preco e
    vendedor do detalhe baterem com os da simulacao de compra.
    """
    stmt = (
        select(
            Product.product_id,
            Product.product_category_name,
            Product.product_weight_g,
            Product.rating,
            Product.review_count,
            OrderItem.price,
            OrderItem.seller_id,
            Seller.seller_zip_code_prefix,
            Seller.seller_city,
            Seller.seller_state,
        )
        .join(OrderItem, OrderItem.product_id == Product.product_id)
        .join(Seller, Seller.seller_id == OrderItem.seller_id)
        .where(Product.product_id == product_id)
        .order_by(OrderItem.order_id, OrderItem.order_item_id)
        .limit(1)
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
