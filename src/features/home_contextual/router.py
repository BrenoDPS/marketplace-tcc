from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.features.green_logistics.repository import list_known_prefixes
from src.features.home_contextual.composer import compose_home
from src.schemas.sdui import ScreenResponse

router = APIRouter(tags=["Home Contextual"])


@router.get("/home", response_model=ScreenResponse)
async def get_home(
    customer_zip_prefix: str = Query(
        ...,
        min_length=1,
        max_length=5,
        description="Prefixo do CEP do comprador (1-5 digitos, formato Olist).",
    ),
    context: str = Query(
        "default",
        description="Contexto adaptativo. Ex: default, electronics_expert, beauty_lover.",
    ),
    session: AsyncSession = Depends(get_db),
) -> ScreenResponse:
    known = await list_known_prefixes(session)
    if customer_zip_prefix not in known:
        raise HTTPException(
            status_code=422,
            detail=f"customer_zip_prefix desconhecido: {customer_zip_prefix!r}",
        )
    return await compose_home(
        session,
        context=context,
        customer_zip_prefix=customer_zip_prefix,
    )
