"""Modalidades de entrega comparaveis (Sprint 4).

HONESTIDADE DOS DADOS — ler antes de citar estes numeros no TCC:

O dataset Olist traz UM `freight_value` por `order_item` e nenhuma informacao
de modalidade, transportadora ou modal de transporte. As tres opcoes abaixo
sao um CENARIO DECLARADO, nao um dado medido. O que e real:

- `distance_km`: Haversine sobre centroides de CEP da amostra
- `weight_g`: `product_weight_g` do dataset
- emissao base: FE = 0,102 kg CO2/(t.km) do GHG Protocol (`co2.py`)
- `standard`: usa o `freight_value` real da amostra, sem fator

O que e arbitrado: os fatores de preco/emissao/prazo de `express` e `green`
em relacao a essa linha de base. Sao coeficientes fixos, escolhidos para
representar carga fracionada prioritaria (mais rapida, mais cara, mais
emissiva) e carga consolidada (mais lenta, mais barata, menos emissiva).

Sem esse recorte nao ha como comparar escolhas de entrega a partir do Olist —
com ele, a comparacao existe e a origem de cada numero fica declarada.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.features.green_logistics.co2 import calculate_co2_kg
from src.schemas.sdui import DeliveryOptionProps


@dataclass(frozen=True, slots=True)
class DeliveryMode:
    id: str
    label: str
    description: str
    price_factor: float
    co2_factor: float
    base_days: int
    km_per_day: float


MODES: tuple[DeliveryMode, ...] = (
    DeliveryMode(
        id="express",
        label="Expressa",
        description="Carga fracionada com prioridade na malha e veículo dedicado.",
        price_factor=1.6,
        co2_factor=2.5,
        base_days=1,
        km_per_day=900.0,
    ),
    DeliveryMode(
        id="standard",
        label="Padrão",
        description="Frete rodoviário praticado na amostra Olist.",
        price_factor=1.0,
        co2_factor=1.0,
        base_days=2,
        km_per_day=450.0,
    ),
    DeliveryMode(
        id="green",
        label="Verde",
        description="Carga consolidada com outros pedidos da região: menos viagens.",
        price_factor=0.85,
        co2_factor=0.6,
        base_days=4,
        km_per_day=350.0,
    ),
)

MODES_BY_ID: dict[str, DeliveryMode] = {mode.id: mode for mode in MODES}
DEFAULT_MODE_ID = "standard"
GREENEST_MODE_ID = min(MODES, key=lambda mode: mode.co2_factor).id

NOTE = (
    "Distância e massa vêm do dataset Olist; preço, prazo e emissão por "
    "modalidade são um cenário declarado sobre o frete real da amostra."
)


def resolve_mode(mode_id: str | None) -> DeliveryMode:
    """Modalidade pelo id, caindo no padrao quando ausente. Levanta se invalida."""
    if mode_id is None:
        return MODES_BY_ID[DEFAULT_MODE_ID]
    return MODES_BY_ID[mode_id]


def eta_days(mode: DeliveryMode, distance_km: float | None) -> int:
    """Prazo = dias fixos da modalidade + trechos de `km_per_day` a percorrer."""
    if distance_km is None:
        return mode.base_days
    return mode.base_days + math.ceil(distance_km / mode.km_per_day)


def mode_co2_kg(
    mode: DeliveryMode, distance_km: float | None, weight_g: float | None
) -> float | None:
    """Emissao da modalidade, ou None quando falta distancia ou massa."""
    if distance_km is None or not weight_g:
        return None
    return calculate_co2_kg(distance_km, weight_g) * mode.co2_factor


def build_delivery_options(
    base_freight: float,
    distance_km: float | None,
    weight_g: float | None,
    selected_id: str = DEFAULT_MODE_ID,
) -> list[DeliveryOptionProps]:
    """Uma opcao por modalidade, na ordem de MODES (mais rapida -> mais verde)."""
    return [
        DeliveryOptionProps(
            id=mode.id,
            label=mode.label,
            description=mode.description,
            eta_days=eta_days(mode, distance_km),
            price=round(base_freight * mode.price_factor, 2),
            co2_kg=mode_co2_kg(mode, distance_km, weight_g),
            recommended=mode.id == GREENEST_MODE_ID,
            selected=mode.id == selected_id,
        )
        for mode in MODES
    ]
