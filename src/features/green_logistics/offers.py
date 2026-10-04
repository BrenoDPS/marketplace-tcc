"""Qual oferta de um produto o comprador recebe — uma regra so, para as tres telas.

Vitrine, detalhe e checkout escolhiam cada um a seu modo: as duas primeiras pela
distancia, o checkout pela "oferta padrao" do ETL (`offers.is_default`, o
primeiro vendedor que apareceu nos pedidos). O detalhe dizia "sai de ~2 km de
voce; comprar do mais proximo evita ~0,10 kg de CO2" e o checkout simulava a
entrega a partir do vendedor a 2.485 km — emitindo exatamente o que a tela
anterior dizia evitar (Sprint 10).

**A regra:** a oferta mais proxima; entre as praticamente equidistantes, a mais
barata. "Praticamente" = ate `TOLERANCIA_RELATIVA` da menor distancia, com piso
na resolucao do modelo (`RESOLUTION_FLOOR_KM`). 1% de distancia e ~1% de CO2 —
abaixo da incerteza do proprio motor, cuja circuidade (1,345) e uma media
nacional. Ai a distancia deixa de distinguir as ofertas, e o preco distingue.
Nunca troca uma oferta com selo por uma sem: o desempate nao pode custar o selo.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from src.features.green_logistics.badge import DISTANCE_THRESHOLD_KM, RESOLUTION_FLOOR_KM

T = TypeVar("T")

TOLERANCIA_RELATIVA = 0.01


def escolher_oferta(medidas: Sequence[tuple[float, T]], preco: Callable[[T], float]) -> tuple[float, T]:
    """`medidas` = `(distancia_km, oferta)`; distancia desconhecida = `inf`.

    Empate de preco fica com a mais proxima, e empate total com a primeira da
    lista — as consultas ordenam por `seller_id`, entao a escolha e estavel.
    Sem nenhuma distancia conhecida, vale a mais barata: nao ha o que medir.
    """
    menor = min(d for d, _ in medidas)
    tolerancia = max(RESOLUTION_FLOOR_KM, TOLERANCIA_RELATIVA * menor)
    com_selo = menor < DISTANCE_THRESHOLD_KM
    candidatas = [
        (i, d, oferta)
        for i, (d, oferta) in enumerate(medidas)
        if d <= menor + tolerancia and (d < DISTANCE_THRESHOLD_KM) == com_selo
    ]
    i, _, _ = min(candidatas, key=lambda c: (preco(c[2]), c[1], c[0]))
    # O proprio item de `medidas`, nao uma tupla nova: quem chama separa as
    # descartadas por identidade.
    return medidas[i]
