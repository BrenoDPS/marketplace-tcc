import pytest

from src.features.green_logistics.badge import (
    DISTANCE_THRESHOLD_KM,
    build_sustainability_props,
)


def test_threshold_constant_is_100() -> None:
    assert DISTANCE_THRESHOLD_KM == 100.0


def test_below_threshold_returns_badge() -> None:
    badge = build_sustainability_props(99.0)
    assert badge is not None
    assert badge.impact_level == "green"
    assert "km" in badge.label


def test_at_threshold_returns_none() -> None:
    assert build_sustainability_props(100.0) is None


def test_above_threshold_returns_none() -> None:
    assert build_sustainability_props(101.0) is None


def test_zero_distance_returns_badge() -> None:
    """Distancia zero e entrega local, nao ausencia de dado."""
    badge = build_sustainability_props(0.0)
    assert badge is not None


# ---------------------------------------------------------------------------
# Piso de resolucao do modelo de centroides
# ---------------------------------------------------------------------------

def test_abaixo_do_piso_o_selo_nao_afirma_numero() -> None:
    """O centroide e a mediana dos enderecos do prefixo; um endereco real fica
    a 0,50 km dele na mediana. Abaixo de 1 km o modelo nao distingue a
    distancia de zero, e "~0 km" anunciaria precisao inexistente."""
    badge = build_sustainability_props(0.0, weight_g=1000.0)
    assert badge is not None
    assert badge.label == "Entrega local (mesma região)"


def test_abaixo_do_piso_nao_afirma_co2_zero() -> None:
    """O bug que motivou a regra: "~0,00 g CO₂".

    Nao e so feio — afirma emissao ZERO onde a verdade e "abaixo do que da para
    medir", numa tela cujo assunto e credibilidade ambiental.
    """
    badge = build_sustainability_props(0.4, weight_g=1000.0)
    assert badge is not None
    assert "0,00" not in badge.label
    assert "CO₂" not in badge.label


def test_acima_do_piso_volta_a_informar_distancia_e_co2() -> None:
    """A regra e um piso, nao um silenciador: 1 km ja e medivel."""
    badge = build_sustainability_props(1.0, weight_g=5000.0)
    assert badge is not None
    assert "1 km" in badge.label
    assert "CO₂" in badge.label


def test_o_piso_nao_engole_o_limiar_do_selo() -> None:
    """Guarda: o selo continua sumindo a 100 km, piso ou nao."""
    assert build_sustainability_props(0.5) is not None
    assert build_sustainability_props(150.0) is None


def test_label_includes_co2_when_weight_provided() -> None:
    badge = build_sustainability_props(50.0, weight_g=2500.0)
    assert badge is not None
    assert "km" in badge.label
    assert "CO₂" in badge.label
    assert "37,5 g" in badge.label  # gramas ate 1 kg (Sprint 13)


def test_label_only_km_when_weight_absent() -> None:
    badge = build_sustainability_props(50.0)
    assert badge is not None
    assert "CO₂" not in badge.label


def test_label_only_km_when_weight_zero() -> None:
    badge = build_sustainability_props(50.0, weight_g=0.0)
    assert badge is not None
    assert "CO₂" not in badge.label


def test_above_threshold_with_weight_returns_none() -> None:
    assert build_sustainability_props(150.0, weight_g=2500.0) is None


# --- explicador do selo (Sprint 15, V2) ---------------------------------------

def test_explicacao_repete_a_conta_do_selo_passo_a_passo() -> None:
    from src.features.green_logistics.co2 import FONTES, calculate_co2_kg

    badge = build_sustainability_props(50.0, weight_g=2500.0, explain=True)
    assert badge is not None and badge.explanation is not None
    e = badge.explanation
    assert e.road_km == pytest.approx(50.0 * 1.345)
    assert e.last_mile_km == 15.0
    assert e.line_haul_km == pytest.approx(e.road_km - 15.0)
    # Os passos fecham no mesmo numero do selo — nunca uma segunda conta.
    passos = e.chargeable_weight_g / 1e6 * (e.line_haul_km * e.fe_line_haul + e.last_mile_km * e.fe_last_mile)
    assert passos == pytest.approx(e.co2_kg)
    assert e.co2_kg == pytest.approx(calculate_co2_kg(50.0, 2500.0))
    assert e.sources == list(FONTES)


def test_explicacao_so_quando_pedida_e_quando_ha_numero() -> None:
    assert build_sustainability_props(50.0, weight_g=2500.0).explanation is None
    # Mesma regiao e sem peso: o selo nao afirma CO2, entao nao ha o que explicar.
    assert build_sustainability_props(0.4, weight_g=2500.0, explain=True).explanation is None
    assert build_sustainability_props(50.0, explain=True).explanation is None
