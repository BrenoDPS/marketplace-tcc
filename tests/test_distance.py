from src.features.green_logistics.distance import haversine_km


def test_same_point_is_zero() -> None:
    assert haversine_km(-23.55, -46.63, -23.55, -46.63) == 0.0


def test_sao_paulo_rio_de_janeiro() -> None:
    """Distancia conhecida SP-RJ ~358 km (tolerancia +/-5 km)."""
    distance = haversine_km(-23.55, -46.63, -22.91, -43.17)
    assert 353.0 <= distance <= 363.0


def test_symmetry() -> None:
    a = haversine_km(-23.55, -46.63, -22.91, -43.17)
    b = haversine_km(-22.91, -43.17, -23.55, -46.63)
    assert a == b


def test_haversine_vetorizado_das_analises_bate_com_o_escalar() -> None:
    """`scripts.concentracao_regional` usa uma copia numpy; tem de dar o mesmo numero."""
    import numpy as np

    from scripts.concentracao_regional import _haversine

    pares = [(-23.55, -46.63, -22.91, -43.17), (-12.97, -38.50, -3.73, -38.52), (0.0, 0.0, 0.0, 0.0)]
    vetor = _haversine(*map(np.array, zip(*pares)))
    for (a, b, c, d), v in zip(pares, vetor):
        assert abs(v - haversine_km(a, b, c, d)) < 1e-9


def test_ordem_haversine_osrm_mede_a_escolha_e_o_custo_da_divergencia() -> None:
    """`scripts.haversine_osrm`: a linha reta escolhe B (100 km), a estrada prefere A."""
    import pandas as pd

    from scripts.haversine_osrm import _ordem

    b = pd.DataFrame({
        "grupo": [0, 0, 1, 1],
        "origem": ["A", "B", "C", "D"],
        "hav_km": [100.5, 100.0, 10.0, 50.0],
        "osrm_km": [120.0, 125.0, 0.0, 70.0],  # grupo 1: vendedor no prefixo do comprador
    })
    o = _ordem(b)
    assert o["topo"] == 0.5
    assert o["divergentes"] == 1 and o["custo_km_max"] == 5.0
    assert o["empate_na_regra"] == 1  # 0,5 km de diferenca: dentro do piso de 1 km
    assert o["concordantes"] == 0.5
