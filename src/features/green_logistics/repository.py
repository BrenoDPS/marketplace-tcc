"""Acesso async a `cep_centroids`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import CepCentroid


_CENTROID_CACHE = "green_logistics.centroids"


async def get_centroid(
    session: AsyncSession, zip_prefix: str
) -> tuple[float, float] | None:
    """Centroide de um prefixo de CEP, memoizado pelo tempo da requisicao.

    O memo vive em `session.info`, e `get_db` abre uma sessao por requisicao —
    entao ele nasce e morre com a request, sem estado global entre elas. E
    seguro porque `cep_centroids` e dado de referencia estatico: escrito uma vez
    pelo ETL, nunca em runtime. Dentro de uma requisicao a resposta nao muda.

    Existe porque a mesma pergunta era feita dezenas de vezes na mesma request:
    montar a Home do `conscious_buyer` custava 63 idas ao banco, das quais 30
    pediam o centroide do COMPRADOR — o mesmo valor, 30 vezes, porque
    `compute_distance_km` busca os dois lados do par a cada chamada.

    Resultado: 63 -> 27 queries, e 150 ms -> 63 ms com um usuario. Sob
    concorrencia o ganho e bem menor — o gargalo dominante passou a ser o
    `list_known_prefixes`. Numeros em `docs/performance.md`.
    """
    cache: dict[str, tuple[float, float] | None]
    cache = session.info.setdefault(_CENTROID_CACHE, {})
    # `in` e nao `.get()`: prefixo sem centroide guarda None, e esse None e uma
    # resposta valida para memoizar. Com `.get()` o CEP desconhecido — o caso do
    # cliente fora da amostra — voltaria ao banco a cada consulta.
    if zip_prefix in cache:
        return cache[zip_prefix]

    stmt = select(CepCentroid.lat, CepCentroid.lng).where(
        CepCentroid.zip_prefix == zip_prefix
    )
    result = await session.execute(stmt)
    row = result.first()
    centroid = None if row is None else (float(row.lat), float(row.lng))
    cache[zip_prefix] = centroid
    return centroid


async def list_known_prefixes(session: AsyncSession) -> set[str]:
    stmt = select(CepCentroid.zip_prefix)
    result = await session.execute(stmt)
    return {row[0] for row in result.all()}
