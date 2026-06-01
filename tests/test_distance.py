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
