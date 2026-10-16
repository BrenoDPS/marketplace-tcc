"""Projecao do mapa de origem (Sprint 15, V3): lat/lng -> coordenadas do SVG.

Equiretangular com a longitude encolhida pelo cosseno da latitude media do
Brasil: para um mapa de "de onde sai" isso basta, e cabe em quatro linhas sem
biblioteca de mapas. A mesma funcao desenha o fundo (`scripts/mapa_base.py`) e
posiciona comprador e vendedores no bloco `origin_map`, entao os dois sempre
casam — e o cliente nao faz conta geografica nenhuma, so desenha.
"""

from __future__ import annotations

from math import cos, radians

LAT_N, LAT_S, LNG_O, LNG_L = 5.5, -34.0, -74.0, -34.0
_K = cos(radians(-14.0))
ESCALA = 20.0  # unidades do SVG por grau de latitude
LARGURA = round((LNG_L - LNG_O) * _K * ESCALA)
ALTURA = round((LAT_N - LAT_S) * ESCALA)
_KM_POR_GRAU = 111.32
# Recorte minimo (~6 graus de altura, ~1.000 km de largura): uma entrega de
# 4 km nao vira um ponto solto num quadro em branco, e o raio de 100 km ainda
# cabe com folga.
_LADO_MINIMO = 6.0 * ESCALA
_PROPORCAO = 16 / 10  # largura / altura do recorte: baixo o bastante para o modal


def dentro_do_brasil(lat: float, lng: float) -> bool:
    """O `olist_geolocation` tem pontos fora do pais (erros de digitacao)."""
    return LAT_S <= lat <= LAT_N and LNG_O <= lng <= LNG_L


def projetar(lat: float, lng: float) -> tuple[float, float]:
    return round((lng - LNG_O) * _K * ESCALA, 1), round((LAT_N - lat) * ESCALA, 1)


def raio(km: float) -> float:
    return round(km / _KM_POR_GRAU * ESCALA, 1)


def recorte(pontos: list[tuple[float, float]]) -> str:
    """`viewBox` que enquadra os pontos com folga, num retangulo de proporcao
    fixa e sem sair do mapa."""
    xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    largura = max((max(xs) - min(xs)) * 1.3, (max(ys) - min(ys)) * 1.3 * _PROPORCAO, _LADO_MINIMO * _PROPORCAO)
    altura = largura / _PROPORCAO
    x0 = min(max(cx - largura / 2, 0), max(LARGURA - largura, 0))
    y0 = min(max(cy - altura / 2, 0), max(ALTURA - altura, 0))
    return f"{x0:.0f} {y0:.0f} {largura:.0f} {altura:.0f}"


if __name__ == "__main__":
    # Sao Paulo cai dentro do quadro; recorte de dois pontos proximos respeita o minimo.
    x, y = projetar(-23.55, -46.63)
    assert 0 < x < LARGURA and 0 < y < ALTURA
    _, _, w, h = map(float, recorte([(x, y), (x + 1, y + 1)]).split())
    assert w >= _LADO_MINIMO * _PROPORCAO - 1 and abs(w / h - _PROPORCAO) < 0.01
    assert raio(_KM_POR_GRAU) == ESCALA
    print("ok", LARGURA, ALTURA)
