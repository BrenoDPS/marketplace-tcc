"""Regra de negocio do selo de Logistica Verde.

Sprint 2: selo apenas por distancia (`d_km < 100`).
Sprint 3: quando `weight_g` disponivel, o label inclui o CO2 estimado.
Sprint 4: `co2_factor` reflete a modalidade escolhida, para o selo nao
contradizer o bloco `delivery_options` na mesma tela.
"""

from __future__ import annotations

from src.features.green_logistics.co2 import (
    CIRCUITY_FACTOR,
    FE_LAST_MILE_KG_PER_T_KM,
    FE_LINE_HAUL_KG_PER_T_KM,
    FONTES,
    LAST_MILE_KM,
    calculate_co2_kg,
    chargeable_weight_g,
    format_co2,
    road_distance_km,
)
from src.schemas.sdui import Co2ExplanationProps, SustainabilityProps

DISTANCE_THRESHOLD_KM: float = 100.0

# Piso de resolucao do modelo. O centroide e a MEDIANA dos enderecos do prefixo,
# e um endereco real fica a 0,50 km dele na mediana — p90 de 1,56 km, medido
# sobre o milhao de pontos de `olist_geolocation`. Dois enderecos quaisquer do
# mesmo prefixo distam tipicamente ~1 km.
#
# Abaixo disto o modelo NAO distingue a distancia de zero. Dizer "~0 km" anuncia
# uma precisao que ele nao tem, e o CO2 correspondente sai como "0,00 g" — que
# le como defeito e, pior, afirma emissao zero onde a verdade e "abaixo do que
# da para medir". Numa tela cujo assunto e credibilidade ambiental, a diferenca
# importa.
RESOLUTION_FLOOR_KM: float = 1.0


def build_sustainability_props(
    distance_km: float,
    weight_g: float | None = None,
    co2_factor: float = 1.0,
    volume_cm3: float | None = None,
    explain: bool = False,
) -> SustainabilityProps | None:
    """Selo verde apenas para entregas com `d_km < 100`. Senao retorna None.

    Quando `weight_g` valido (> 0), inclui o CO2 estimado no label
    (compativel com Sprint 2 quando o peso esta ausente). `co2_factor` = 1.0 e
    a linha de base rodoviaria: a Home usa o default, o checkout passa o fator
    da modalidade selecionada.
    """
    if distance_km >= DISTANCE_THRESHOLD_KM:
        return None
    explanation = None
    if distance_km < RESOLUTION_FLOOR_KM:
        # Mesma regiao: o numero existe, mas seria ruido do modelo — e o CO2
        # sai junto, porque afirmar "0,00 g" e afirmar zero, nao "pouco".
        label = "Entrega local (mesma região)"
    elif weight_g is not None and weight_g > 0:
        co2_kg = calculate_co2_kg(distance_km, weight_g, volume_cm3) * co2_factor
        label = f"Entrega local (~{distance_km:.0f} km · ~{format_co2(co2_kg)} CO₂)"
        if explain:
            explanation = explicar_co2(distance_km, weight_g, volume_cm3, co2_factor, co2_kg)
    else:
        label = f"Entrega local (~{distance_km:.0f} km)"
    return SustainabilityProps(
        label=label,
        impact_level="green",
        icon="leaf",
        explanation=explanation,
    )


def explicar_co2(
    distance_km: float,
    weight_g: float,
    volume_cm3: float | None,
    co2_factor: float,
    co2_kg: float,
) -> Co2ExplanationProps:
    """Os passos de `calculate_co2_kg`, com os mesmos numeros. `co2_kg` vem de
    quem chamou (a conta do selo), para o explicador nunca divergir dele."""
    estrada = road_distance_km(distance_km)
    van = min(estrada, LAST_MILE_KM)
    return Co2ExplanationProps(
        straight_km=distance_km,
        circuity=CIRCUITY_FACTOR,
        road_km=estrada,
        line_haul_km=estrada - van,
        last_mile_km=van,
        weight_g=weight_g,
        chargeable_weight_g=chargeable_weight_g(weight_g, volume_cm3),
        fe_line_haul=FE_LINE_HAUL_KG_PER_T_KM,
        fe_last_mile=FE_LAST_MILE_KG_PER_T_KM,
        mode_factor=co2_factor,
        co2_kg=co2_kg,
        sources=list(FONTES),
    )
