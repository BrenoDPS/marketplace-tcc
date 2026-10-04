import math

import pytest

from src.features.green_logistics.co2 import (
    CIRCUITY_FACTOR,
    FE_LAST_MILE_KG_PER_T_KM,
    FE_LINE_HAUL_KG_PER_T_KM,
    LAST_MILE_KM,
    calculate_co2_kg,
    chargeable_weight_g,
    road_distance_km,
)


def test_constantes_sao_as_das_fontes_citadas() -> None:
    """Mudar um destes numeros exige mudar a fonte citada em co2.py."""
    assert CIRCUITY_FACTOR == 1.345  # Goncalves et al. (2014)
    assert LAST_MILE_KM == 15.0  # WEF (2024), limite inferior de 15-20 km
    assert FE_LINE_HAUL_KG_PER_T_KM == 0.092  # GLEC v2, HGV > 20 t, WTW
    assert FE_LAST_MILE_KG_PER_T_KM == 0.680  # GLEC v2, van < 3,5 t, WTW


def test_linha_reta_vira_estrada_pela_circuidade() -> None:
    assert road_distance_km(100.0) == pytest.approx(134.5)


def test_100km_1000g_transferencia_mais_ultima_milha() -> None:
    # estrada 134,5 km: 119,5 km de caminhao + 15 km de van, 0,001 t
    # (119,5 * 0,092 + 15 * 0,680) * 0,001 = (10,994 + 10,2) / 1000
    assert math.isclose(calculate_co2_kg(100, 1000), 0.021194, rel_tol=1e-9)


def test_entrega_curta_vai_inteira_de_van() -> None:
    # 10 km de linha reta -> 13,45 km de estrada < 15: tudo de van
    # 13,45 * 0,680 * 0,0025 t = 0,0228650
    assert math.isclose(calculate_co2_kg(10, 2500), 0.022865, rel_tol=1e-9)


def test_sem_salto_no_limite_da_ultima_milha() -> None:
    """Um corte rigido faria a entrega a 99 km emitir ~4x a de 101 km."""
    limite = LAST_MILE_KM / CIRCUITY_FACTOR
    antes = calculate_co2_kg(limite - 1e-6, 1000)
    depois = calculate_co2_kg(limite + 1e-6, 1000)
    assert depois == pytest.approx(antes, rel=1e-5)


def test_emissao_cresce_com_a_distancia() -> None:
    distancias = [1, 5, 11, 12, 50, 99, 101, 432, 2483]
    emissoes = [calculate_co2_kg(d, 1000) for d in distancias]
    assert emissoes == sorted(emissoes)
    assert len(set(emissoes)) == len(emissoes)


def test_compra_local_continua_mais_limpa_mas_nao_22x() -> None:
    """O numero que mudou a tese (Sprint 9): mediana real 432 km x local 20 km."""
    razao = calculate_co2_kg(432, 1000) / calculate_co2_kg(20, 1000)
    assert 5 < razao < 6  # era 21,6x com o fator unico de caminhao pesado


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
