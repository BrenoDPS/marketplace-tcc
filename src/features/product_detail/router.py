"""Rota do detalhe do produto: GET /api/v1/products/{product_id}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.features.orchestrator.mutacoes import MUTACOES, aplicar
from src.features.green_logistics.repository import list_known_prefixes
from src.features.product_detail.composer import compose_product_detail
from src.features.product_detail.repository import fetch_product_offers
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
    x_sdui_mutacao: str | None = Header(
        None,
        description=(
            "Modo apresentacao (V9): o BFF muta a arvore antes de responder. "
            f"Valores: {', '.join(MUTACOES)}. So com SDUI_MUTACOES_DEMO."
        ),
    ),
    session: AsyncSession = Depends(get_db),
) -> ScreenResponse | JSONResponse:
    known = await list_known_prefixes(session)
    if customer_zip_prefix not in known:
        raise HTTPException(
            status_code=422,
            detail=f"customer_zip_prefix desconhecido: {customer_zip_prefix!r}",
        )

    offers = await fetch_product_offers(session, product_id)
    if not offers:
        raise HTTPException(
            status_code=404,
            detail=f"product_id nao encontrado na amostra: {product_id!r}",
        )

    tela = await compose_product_detail(
        session,
        offers=offers,
        customer_zip_prefix=customer_zip_prefix,
    )
    if not x_sdui_mutacao:
        return tela
    if not settings.SDUI_MUTACOES_DEMO:
        raise HTTPException(status_code=403, detail="mutacoes de demonstracao desligadas")
    if x_sdui_mutacao not in MUTACOES:
        raise HTTPException(status_code=422, detail=f"mutacao desconhecida: {x_sdui_mutacao!r}")
    # JSON e nao o modelo: o bloco desconhecido e o envelope sem `actions` nao
    # passariam pelo `response_model` — e sao eles que o cliente tem de aguentar.
    return JSONResponse(aplicar(tela.model_dump(mode="json"), x_sdui_mutacao))
