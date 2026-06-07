"""Regra de negocio do selo de Logistica Verde.

Sprint 2: selo apenas por distancia (`d_km < 100`).
Sprint 3: quando `weight_g` disponivel, o label inclui o CO2 estimado.
"""

from __future__ import annotations

from src.features.green_logistics.co2 import calculate_co2_kg
from src.schemas.sdui import SustainabilityProps

DISTANCE_THRESHOLD_KM: float = 100.0


def build_sustainability_props(
    distance_km: float, weight_g: float | None = None
) -> SustainabilityProps | None:
    """Selo verde apenas para entregas com `d_km < 100`. Senao retorna None.

    Quando `weight_g` valido (> 0), inclui o CO2 estimado no label
    (compativel com Sprint 2 quando o peso esta ausente).
    """
    if distance_km >= DISTANCE_THRESHOLD_KM:
        return None
    if weight_g is not None and weight_g > 0:
        co2_kg = calculate_co2_kg(distance_km, weight_g)
        label = f"Entrega local (~{distance_km:.0f} km · ~{co2_kg:.2f} kg CO₂)"
    else:
        label = f"Entrega local (~{distance_km:.0f} km)"
    return SustainabilityProps(
        label=label,
        impact_level="green",
        icon="leaf",
    )
