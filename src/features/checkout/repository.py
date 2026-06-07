"""Acesso async aos dados do produto para o checkout simulado.

Frete: usa o `freight_value` da PRIMEIRA linha de `order_items` daquele
`product_id` na amostra (decisao fechada no handoff da Sprint 3).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import OrderItem, Product, Seller


@dataclass(frozen=True, slots=True)
class CheckoutProductRow:
    product_id: str
    seller_id: str
    seller_zip_prefix: str
    unit_price: float
    freight_value: float
    weight_g: float | None
    category: str | None


async def fetch_product_for_checkout(
    session: AsyncSession, product_id: str
) -> CheckoutProductRow | None:
    """Retorna a primeira linha de order_items para o `product_id`, ou None."""
    stmt = (
        select(
            OrderItem.product_id,
            OrderItem.seller_id,
            Seller.seller_zip_code_prefix,
            OrderItem.price,
            OrderItem.freight_value,
            Product.product_weight_g,
            Product.product_category_name,
        )
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Seller, Seller.seller_id == OrderItem.seller_id)
        .where(OrderItem.product_id == product_id)
        .order_by(OrderItem.order_id, OrderItem.order_item_id)
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        return None

    product_id, seller_id, zip_prefix, price, freight_value, weight_g, category = row
    return CheckoutProductRow(
        product_id=product_id,
        seller_id=seller_id,
        seller_zip_prefix=zip_prefix,
        unit_price=float(price),
        freight_value=float(freight_value) if freight_value is not None else 0.0,
        weight_g=float(weight_g) if weight_g is not None else None,
        category=category,
    )
