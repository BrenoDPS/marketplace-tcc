"""Modalidades de entrega comparaveis (Sprint 4).

HONESTIDADE DOS DADOS — ler antes de citar estes numeros no TCC:

O dataset Olist traz UM `freight_value` por `order_item` e nenhuma informacao
de modalidade, transportadora ou modal de transporte. As tres opcoes abaixo
sao um CENARIO DECLARADO sobre uma linha de base MEDIDA. O que e real:

- `distance_km`: Haversine sobre centroides de CEP da amostra
- `weight_g`: `product_weight_g` do dataset
- emissao base: FE = 0,102 kg CO2/(t.km) do GHG Protocol (`co2.py`)
- `standard`: usa o `freight_value` real da amostra, sem fator
- **prazo da linha de base: medido em 95.921 entregas reais** — ver `ETA_BANDS`

O que e arbitrado: os fatores de preco, emissao e prazo de `express` e `green`
EM RELACAO a essa linha de base. Sao coeficientes fixos, escolhidos para
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


# Prazo MEDIDO, nao arbitrado: mediana de dias entre a compra e a entrega ao
# cliente, por faixa de distancia, sobre as 95.921 entregas do Olist que tem
# data de entrega e distancia calculavel. Cada par e (limite superior da faixa
# em km, dias).
#
#   faixa (km)        n      p50     media    p90
#      0 -   50    11.758    4,9      6,1    11,3
#     50 -  100     6.133    5,8      7,1    13,3
#    100 -  300    13.340    8,2     10,0    17,4
#    300 -  600    31.477   10,3     12,6    21,9
#    600 - 1200    21.019   12,8     14,8    24,9
#   1200 -  inf    12.194   17,2     19,6    32,6
#
# **Comprar perto e 3,5x mais rapido** — e um argumento a favor de logistica
# local que nao depende de CO2 nenhum, medido e nao estimado.
#
# Mediana e nao media de proposito: a distribuicao tem cauda longa (media 6,1
# contra p50 4,9 ja na faixa mais curta), e a media descreveria uma experiencia
# que a maioria nao tem.
#
# `scripts.etl_load_sample` rederiva estes numeros a cada carga e avisa se
# divergirem daqui — eles saem dos CSVs, que sao fixos, entao nao devem mudar.
ETA_BANDS: tuple[tuple[float, float], ...] = (
    (50.0, 4.9),
    (100.0, 5.8),
    (300.0, 8.2),
    (600.0, 10.3),
    (1200.0, 12.8),
    (float("inf"), 17.2),
)

# Distancia desconhecida (vendedor sem centroide): p50 de TODAS as 95.921
# entregas. Nao sabemos a distancia, entao respondemos com o tipico geral em
# vez de escolher uma faixa.
ETA_UNKNOWN_DISTANCE_DAYS: float = 10.2


@dataclass(frozen=True, slots=True)
class DeliveryMode:
    id: str
    label: str
    description: str
    price_factor: float
    co2_factor: float
    # Multiplicador sobre o prazo medido. `standard` e 1.0 porque a linha de
    # base E a entrega real do Olist; os outros dois sao declarados.
    eta_factor: float


MODES: tuple[DeliveryMode, ...] = (
    DeliveryMode(
        id="express",
        label="Expressa",
        description="Carga fracionada com prioridade na malha e veículo dedicado.",
        price_factor=1.6,
        co2_factor=2.5,
        eta_factor=0.5,
    ),
    DeliveryMode(
        id="standard",
        label="Padrão",
        description="Frete rodoviário praticado na amostra Olist.",
        price_factor=1.0,
        co2_factor=1.0,
        eta_factor=1.0,
    ),
    DeliveryMode(
        id="green",
        label="Verde",
        description="Carga consolidada com outros pedidos da região: menos viagens.",
        price_factor=0.85,
        co2_factor=0.6,
        eta_factor=1.5,
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


def base_eta_days(distance_km: float | None) -> float:
    """Prazo tipico medido para essa distancia, antes do fator da modalidade."""
    if distance_km is None:
        return ETA_UNKNOWN_DISTANCE_DAYS
    for limite, dias in ETA_BANDS:
        if distance_km < limite:
            return dias
    # A ultima faixa termina em `inf`, entao so chega aqui com NaN.
    return ETA_UNKNOWN_DISTANCE_DAYS


def eta_days(mode: DeliveryMode, distance_km: float | None) -> int:
    """Prazo medido para a distancia, escalado pelo fator da modalidade.

    O modelo anterior era `dias_fixos + ceil(distancia / km_por_dia)`, com os
    dois numeros arbitrados — e subestimava muito: dava 3 dias para uma entrega
    local que na amostra leva 4,9, e 7 dias para 2000 km que levam 17,2.

    # ponytail: o fator escala o prazo INTEIRO, mas o tempo medido inclui
    # aprovacao e separacao, que uma modalidade mais rapida quase nao comprime.
    # Separar processamento de transito exigiria `order_delivered_carrier_date`,
    # que o dataset tem — fazer se o prazo virar objeto de analise, e nao so
    # rotulo comparativo entre modalidades.
    """
    return math.ceil(base_eta_days(distance_km) * mode.eta_factor)


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
