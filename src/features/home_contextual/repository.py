"""Repository da home: consulta produtos reais da amostra Olist."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import OrderItem, Product, Seller


@dataclass(frozen=True, slots=True)
class ProductRow:
    """Estrutura interna (nao SDUI) para passar dados do Postgres ao composer."""

    product_id: str
    seller_id: str
    seller_zip_prefix: str
    price: float
    weight_g: float | None
    category: str | None


# Heuristica context -> categoria Olist. Pode ser refinada na Sprint 3.
_CONTEXT_TO_CATEGORY: dict[str, str] = {
    "electronics_expert": "informatica_acessorios",
    "beauty_lover": "beleza_saude",
}


def category_for_context(context: str) -> str | None:
    return _CONTEXT_TO_CATEGORY.get(context)


async def fetch_products_for_home(
    session: AsyncSession,
    category: str | None = None,
    limit: int = 6,
) -> list[ProductRow]:
    """Retorna ate `limit` produtos distintos da amostra.

    JOIN order_items -> products -> sellers. Filtra por categoria quando informada;
    se nao houver produtos da categoria, faz fallback para sem filtro.
    """
    stmt = (
        select(
            OrderItem.product_id,
            OrderItem.seller_id,
            Seller.seller_zip_code_prefix,
            OrderItem.price,
            Product.product_weight_g,
            Product.product_category_name,
        )
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Seller, Seller.seller_id == OrderItem.seller_id)
    )
    if category is not None:
        stmt = stmt.where(Product.product_category_name == category)
    stmt = stmt.limit(limit * 4)  # margem para de-dup por product_id

    result = await session.execute(stmt)
    rows = result.all()

    if not rows and category is not None:
        return await fetch_products_for_home(session, category=None, limit=limit)

    seen: set[str] = set()
    out: list[ProductRow] = []
    for product_id, seller_id, zip_prefix, price, weight_g, cat in rows:
        if product_id in seen:
            continue
        seen.add(product_id)
        out.append(
            ProductRow(
                product_id=product_id,
                seller_id=seller_id,
                seller_zip_prefix=zip_prefix,
                price=float(price),
                weight_g=float(weight_g) if weight_g is not None else None,
                category=cat,
            )
        )
        if len(out) >= limit:
            break
    return out
