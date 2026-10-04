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
