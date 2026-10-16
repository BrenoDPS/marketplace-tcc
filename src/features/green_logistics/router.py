"""Rota da metodologia: GET /api/v1/methodology."""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.features.green_logistics.metodologia import compose_metodologia
from src.schemas.sdui import ScreenResponse

router = APIRouter(tags=["Green Logistics"])


@router.get("/methodology", response_model=ScreenResponse)
async def get_methodology(
    customer_zip_prefix: str | None = Query(
        None,
        max_length=5,
        pattern=r"^\d{1,5}$",
        description="Opcional: so monta o 'Voltar a vitrine' com o CEP de quem veio de la.",
    ),
) -> ScreenResponse:
    # Sem banco nem cache: texto montado das constantes, custo de microssegundos.
    return compose_metodologia(customer_zip_prefix)
