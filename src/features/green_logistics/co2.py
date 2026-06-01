"""Calculo de emissao de CO2 para deslocamento de carga.

Formula: E = d * w * FE
- d em km
- w em toneladas (converter de gramas via /1_000_000)
- FE = 0.102 kg CO2/(t.km) (GHG Protocol, transporte rodoviario padrao)
"""

from __future__ import annotations

EMISSION_FACTOR_KG_PER_T_KM: float = 0.102


def calculate_co2_kg(distance_km: float, weight_g: float) -> float:
    """Retorna emissao estimada em kg de CO2."""
    weight_t = weight_g / 1_000_000
    return distance_km * weight_t * EMISSION_FACTOR_KG_PER_T_KM
