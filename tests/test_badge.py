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
    assert "kg" in badge.label


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
