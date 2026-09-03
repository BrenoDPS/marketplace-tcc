"""Rota do detalhe do produto: GET /api/v1/products/{product_id}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.features.green_logistics.repository import list_known_prefixes
from src.features.product_detail.composer import compose_product_detail
from src.features.product_detail.repository import fetch_product_detail
from src.schemas.sdui import ScreenResponse

router = APIRouter(tags=["Product Detail"])


@router.get("/products/{product_id}", response_model=ScreenResponse)
async def get_product_detail(
    product_id: str,
    customer_zip_prefix: str = Query(
        ...,
        min_length=1,
        max_length=5,
        description="Prefixo do CEP do comprador — define distancia, CO2 e selo.",
    ),
    session: AsyncSession = Depends(get_db),
) -> ScreenResponse:
    known = await list_known_prefixes(session)
    if customer_zip_prefix not in known:
        raise HTTPException(
            status_code=422,
            detail=f"customer_zip_prefix desconhecido: {customer_zip_prefix!r}",
        )

    product = await fetch_product_detail(session, product_id)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"product_id nao encontrado na amostra: {product_id!r}",
        )

    return await compose_product_detail(
        session,
        product=product,
        customer_zip_prefix=customer_zip_prefix,
    )
