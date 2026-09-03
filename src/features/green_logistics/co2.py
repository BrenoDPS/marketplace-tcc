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


def format_co2(kg: float) -> str:
    """Formata emissao para exibicao em pt-BR, escolhendo a unidade legivel.

    A amostra Olist tem pesos baixos e, com a densidade de CEPs da amostra de
    10k, as distancias caem para poucos km: a emissao fica na ordem de
    0,0004 kg e um `.2f` em kg imprimiria "0,00 kg" — apagando justamente o
    numero que sustenta o argumento de logistica verde. Abaixo de 10 g,
    exibimos em gramas.
    """
    if kg >= 0.01:
        return f"{kg:.2f} kg".replace(".", ",")
    return f"{kg * 1000:.2f} g".replace(".", ",")
