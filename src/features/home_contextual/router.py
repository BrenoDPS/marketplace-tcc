from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.features.green_logistics.repository import list_known_prefixes
from src.features.home_contextual.composer import compose_home
from src.features.home_contextual.repository import list_categories, normalize_search
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
    q: str | None = Query(
        None,
        max_length=60,
        description=(
            "Busca sobre o nome da categoria. O Olist nao tem nome de produto: "
            "'moveis' encontra moveis_decoracao, acentos sao ignorados."
        ),
    ),
    category: str | None = Query(
        None,
        max_length=120,
        description="Filtro exato por `product_category_name` da amostra.",
    ),
    session: AsyncSession = Depends(get_db),
) -> ScreenResponse:
    known = await list_known_prefixes(session)
    if customer_zip_prefix not in known:
        raise HTTPException(
            status_code=422,
            detail=f"customer_zip_prefix desconhecido: {customer_zip_prefix!r}",
        )

    if category is not None:
        slugs = {row.slug for row in await list_categories(session)}
        if category not in slugs:
            raise HTTPException(
                status_code=422,
                detail=f"category desconhecida na amostra: {category!r}",
            )

    # Normaliza uma vez, na borda: dai para dentro o termo ou e util ou e None.
    # Entrada que some ao normalizar (so espacos) vira "sem busca" — o hero nao
    # pode anunciar "Busca: " sobre uma vitrine que nao esta filtrada.
    search = normalize_search(q) or None if q else None

    return await compose_home(
        session,
        context=context,
        customer_zip_prefix=customer_zip_prefix,
        search=search,
        category=category,
    )
