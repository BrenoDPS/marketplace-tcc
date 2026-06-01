"""Acesso async a `cep_centroids`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import CepCentroid


async def get_centroid(
    session: AsyncSession, zip_prefix: str
) -> tuple[float, float] | None:
    stmt = select(CepCentroid.lat, CepCentroid.lng).where(
        CepCentroid.zip_prefix == zip_prefix
    )
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        return None
    return float(row.lat), float(row.lng)


async def list_known_prefixes(session: AsyncSession) -> set[str]:
    stmt = select(CepCentroid.zip_prefix)
    result = await session.execute(stmt)
    return {row[0] for row in result.all()}
