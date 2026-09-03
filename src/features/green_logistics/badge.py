"""Regra de negocio do selo de Logistica Verde.

Sprint 2: selo apenas por distancia (`d_km < 100`).
Sprint 3: quando `weight_g` disponivel, o label inclui o CO2 estimado.
Sprint 4: `co2_factor` reflete a modalidade escolhida, para o selo nao
contradizer o bloco `delivery_options` na mesma tela.
"""

from __future__ import annotations

from src.features.green_logistics.co2 import calculate_co2_kg, format_co2
from src.schemas.sdui import SustainabilityProps

DISTANCE_THRESHOLD_KM: float = 100.0


def build_sustainability_props(
    distance_km: float,
    weight_g: float | None = None,
    co2_factor: float = 1.0,
) -> SustainabilityProps | None:
    """Selo verde apenas para entregas com `d_km < 100`. Senao retorna None.

    Quando `weight_g` valido (> 0), inclui o CO2 estimado no label
    (compativel com Sprint 2 quando o peso esta ausente). `co2_factor` = 1.0 e
    a linha de base rodoviaria: a Home usa o default, o checkout passa o fator
    da modalidade selecionada.
    """
    if distance_km >= DISTANCE_THRESHOLD_KM:
        return None
    if weight_g is not None and weight_g > 0:
        co2_kg = calculate_co2_kg(distance_km, weight_g) * co2_factor
        label = f"Entrega local (~{distance_km:.0f} km · ~{format_co2(co2_kg)} CO₂)"
    else:
        label = f"Entrega local (~{distance_km:.0f} km)"
    return SustainabilityProps(
        label=label,
        impact_level="green",
        icon="leaf",
    )
