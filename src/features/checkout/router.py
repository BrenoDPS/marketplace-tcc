"""Rota do checkout simulado: POST /api/v1/checkout/simulate."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.features.checkout.composer import compose_checkout
from src.features.checkout.repository import fetch_product_for_checkout
from src.features.checkout.schemas import CheckoutSimulateRequest
from src.features.green_logistics.repository import list_known_prefixes
from src.schemas.sdui import ScreenResponse

router = APIRouter(tags=["Checkout"])


@router.post("/checkout/simulate", response_model=ScreenResponse)
async def simulate_checkout(
    payload: CheckoutSimulateRequest,
    session: AsyncSession = Depends(get_db),
) -> ScreenResponse:
    known = await list_known_prefixes(session)
    if payload.customer_zip_prefix not in known:
        raise HTTPException(
            status_code=422,
            detail=f"customer_zip_prefix desconhecido: {payload.customer_zip_prefix!r}",
        )

    product = await fetch_product_for_checkout(session, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"product_id nao encontrado na amostra: {payload.product_id!r}",
        )

    return await compose_checkout(
        session,
        product=product,
        customer_zip_prefix=payload.customer_zip_prefix,
        quantity=payload.quantity,
    )
