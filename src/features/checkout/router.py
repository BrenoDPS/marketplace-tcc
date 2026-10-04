"""Rota do checkout simulado: POST /api/v1/checkout/simulate."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.features.checkout.composer import compose_checkout
from src.features.checkout.repository import CheckoutProductRow, fetch_products_for_checkout
from src.features.checkout.schemas import CheckoutSimulateRequest
from src.features.green_logistics.delivery_options import MODES_BY_ID
from src.features.green_logistics.offers import escolher_oferta
from src.features.green_logistics.repository import list_known_prefixes
from src.features.green_logistics.service import compute_distance_km
from src.schemas.sdui import ScreenResponse

router = APIRouter(tags=["Checkout"])


async def _oferta_do_comprador(
    session: AsyncSession, customer_zip_prefix: str, ofertas: list[CheckoutProductRow]
) -> CheckoutProductRow:
    """A MESMA oferta que a vitrine e o detalhe mostraram a este comprador."""
    medidas = []
    for oferta in ofertas:
        d = await compute_distance_km(session, customer_zip_prefix, oferta.seller_zip_prefix)
        medidas.append((float("inf") if d is None else d, oferta))
    return escolher_oferta(medidas, lambda o: o.unit_price)[1]


@router.post("/checkout/simulate", response_model=ScreenResponse)
async def simulate_checkout(
    payload: CheckoutSimulateRequest,
    session: AsyncSession = Depends(get_db),
) -> ScreenResponse:
    if payload.delivery_option is not None and payload.delivery_option not in MODES_BY_ID:
        raise HTTPException(
            status_code=422,
            detail=(
                f"delivery_option desconhecido: {payload.delivery_option!r}. "
                f"Validos: {sorted(MODES_BY_ID)}"
            ),
        )

    known = await list_known_prefixes(session)
    if payload.customer_zip_prefix not in known:
        raise HTTPException(
            status_code=422,
            detail=f"customer_zip_prefix desconhecido: {payload.customer_zip_prefix!r}",
        )

    ofertas = await fetch_products_for_checkout(
        session, [item.product_id for item in payload.items]
    )
    missing = [i.product_id for i in payload.items if i.product_id not in ofertas]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"product_id nao encontrado na amostra: {missing!r}",
        )

    products = {
        pid: await _oferta_do_comprador(session, payload.customer_zip_prefix, rows)
        for pid, rows in ofertas.items()
    }

    # Mesmo produto repetido no carrinho vira uma linha so: duas linhas iguais
    # dariam dois fretes na agregacao por vendedor e um resumo confuso.
    quantities: dict[str, int] = {}
    for item in payload.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    return await compose_checkout(
        session,
        lines=[(products[pid], qty) for pid, qty in quantities.items()],
        customer_zip_prefix=payload.customer_zip_prefix,
        delivery_option=payload.delivery_option,
    )
