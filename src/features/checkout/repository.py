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


async def fetch_products_for_checkout(
    session: AsyncSession, product_ids: list[str]
) -> dict[str, CheckoutProductRow]:
    """Mapa `product_id` -> primeira linha de order_items daquele produto.

    Uma consulta para o carrinho inteiro: com 20 itens, buscar um a um seriam
    20 round-trips para montar uma tela so. Produto ausente simplesmente nao
    aparece no mapa — quem chama decide se isso e 404.
    """
    if not product_ids:
        return {}

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
        .where(OrderItem.product_id.in_(set(product_ids)))
        .order_by(OrderItem.product_id, OrderItem.order_id, OrderItem.order_item_id)
    )
    result = await session.execute(stmt)

    out: dict[str, CheckoutProductRow] = {}
    for product_id, seller_id, zip_prefix, price, freight, weight_g, category in result:
        # Ordenado por (product_id, order_id, order_item_id): a primeira linha
        # de cada produto e a mesma "primeira order_item" da Sprint 3.
        if product_id in out:
            continue
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
