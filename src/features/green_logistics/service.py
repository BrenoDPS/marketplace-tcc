"""Servico async que combina centroides + Haversine + regra do selo."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.green_logistics.badge import build_sustainability_props
from src.features.green_logistics.distance import haversine_km
from src.features.green_logistics.repository import get_centroid
from src.schemas.sdui import SustainabilityProps


async def compute_distance_km(
    session: AsyncSession,
    customer_zip_prefix: str,
    seller_zip_prefix: str,
) -> float | None:
    """Retorna distancia Haversine em km; None se algum prefixo nao tem centroide."""
    customer = await get_centroid(session, customer_zip_prefix)
    seller = await get_centroid(session, seller_zip_prefix)
    if customer is None or seller is None:
        return None
    return haversine_km(customer[0], customer[1], seller[0], seller[1])


async def build_badge_for_pair(
    session: AsyncSession,
    customer_zip_prefix: str,
    seller_zip_prefix: str,
) -> tuple[float | None, SustainabilityProps | None]:
    distance = await compute_distance_km(session, customer_zip_prefix, seller_zip_prefix)
    if distance is None:
        return None, None
    return distance, build_sustainability_props(distance)
