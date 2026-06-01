"""Regra de negocio do selo de Logistica Verde (Sprint 2: apenas distancia)."""

from __future__ import annotations

from src.schemas.sdui import SustainabilityProps

DISTANCE_THRESHOLD_KM: float = 100.0


def build_sustainability_props(distance_km: float) -> SustainabilityProps | None:
    """Selo verde apenas para entregas com `d_km < 100`. Senao retorna None."""
    if distance_km >= DISTANCE_THRESHOLD_KM:
        return None
    return SustainabilityProps(
        label=f"Entrega local (~{distance_km:.0f} km)",
        impact_level="green",
        icon="leaf",
    )
