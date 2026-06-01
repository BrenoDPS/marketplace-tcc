import math

from src.features.green_logistics.co2 import EMISSION_FACTOR_KG_PER_T_KM, calculate_co2_kg


def test_emission_factor_value() -> None:
    assert EMISSION_FACTOR_KG_PER_T_KM == 0.102


def test_100km_1000g() -> None:
    # 100 km * (1000 g -> 0.001 t) * 0.102 = 0.0102 kg
    assert math.isclose(calculate_co2_kg(100, 1000), 0.0102, rel_tol=1e-9)


def test_50km_2500g() -> None:
    # 50 * (2500/1_000_000) * 0.102 = 0.01275 kg
    assert math.isclose(calculate_co2_kg(50, 2500), 0.01275, rel_tol=1e-9)


def test_zero_weight_is_zero() -> None:
    assert calculate_co2_kg(100, 0) == 0.0


def test_zero_distance_is_zero() -> None:
    assert calculate_co2_kg(0, 1000) == 0.0
