import math

import pytest

from src.features.green_logistics.co2 import (
    EMISSION_FACTOR_KG_PER_T_KM,
    calculate_co2_kg,
    chargeable_weight_g,
)


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


# ---------------------------------------------------------------------------
# Peso cubado (Sprint 7)
# ---------------------------------------------------------------------------

def test_carga_densa_usa_o_peso_real() -> None:
    """Tijolo: pesa mais do que ocupa. A cubagem nao pode inflar isto."""
    # 1000 cm3 -> 1000/6000*1000 = 166,7 g cubados, contra 5000 g reais.
    assert chargeable_weight_g(5000.0, 1000.0) == 5000.0


def test_carga_leve_e_volumosa_usa_o_peso_cubado() -> None:
    """Travesseiro: ocupa muito mais do que pesa.

    E o caso de **66,4% dos produtos do Olist**. Usar so a massa subestimava a
    emissao de dois tercos do catalogo, porque o que enche o veiculo e o espaco.
    """
    # 60000 cm3 -> 10000 g cubados, contra 500 g reais.
    assert chargeable_weight_g(500.0, 60000.0) == 10000.0


def test_sem_volume_conhecido_vale_o_peso_real() -> None:
    """Produto sem dimensoes: nao ha o que corrigir, e nao se inventa caixa."""
    assert chargeable_weight_g(800.0, None) == 800.0
    assert chargeable_weight_g(800.0, 0.0) == 800.0


def test_o_cubado_entra_no_calculo_de_emissao() -> None:
    """A correcao tem de chegar ate o CO2, nao parar no helper."""
    leve_volumoso = calculate_co2_kg(100.0, 500.0, volume_cm3=60000.0)
    so_massa = calculate_co2_kg(100.0, 500.0)
    assert leve_volumoso > so_massa
    # 20x: 10.000 g cubados contra 500 g reais.
    assert leve_volumoso == pytest.approx(so_massa * 20.0)


def test_cubagem_e_da_remessa_e_nao_do_item() -> None:
    """A soma dos `max` cobraria o espaco vazio duas vezes.

    Remessa com um item denso (5 kg em 1000 cm3) e um leve-volumoso (0,5 kg em
    60000 cm3):

      correto  : max(5500, 61000/6000*1000) = max(5500, 10166) = 10166 g
      errado   : max(5000,167) + max(500,10000) = 5000 + 10000 = 15000 g

    O item denso ja ocupa espaco na carga; cobrar o volume dele e de novo o
    volume do outro superestima a emissao em 48%.
    """
    correto = chargeable_weight_g(5000.0 + 500.0, 1000.0 + 60000.0)
    somando_por_item = chargeable_weight_g(5000.0, 1000.0) + chargeable_weight_g(
        500.0, 60000.0
    )

    assert correto == pytest.approx(10166.7, abs=0.1)
    assert correto < somando_por_item
