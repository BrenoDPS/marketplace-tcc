from src.features.green_logistics.co2 import calculate_co2_kg, format_co2
from src.features.green_logistics.delivery_options import (
    DEFAULT_MODE_ID,
    GREENEST_MODE_ID,
    MODES,
    MODES_BY_ID,
    build_delivery_options,
    eta_days,
    mode_co2_kg,
    resolve_mode,
)


def test_standard_is_the_unmodified_baseline() -> None:
    """`standard` precisa espelhar o frete real da amostra, sem fator."""
    standard = MODES_BY_ID[DEFAULT_MODE_ID]
    assert standard.price_factor == 1.0
    assert standard.co2_factor == 1.0


def test_greenest_mode_emits_least() -> None:
    greenest = MODES_BY_ID[GREENEST_MODE_ID]
    assert all(greenest.co2_factor <= mode.co2_factor for mode in MODES)


def test_greener_modes_are_slower() -> None:
    """Se a opcao verde fosse mais rapida E mais barata, nao haveria trade-off."""
    by_co2 = sorted(MODES, key=lambda m: m.co2_factor)
    etas = [eta_days(mode, 100.0) for mode in by_co2]
    assert etas == sorted(etas, reverse=True)


def test_resolve_mode_defaults_to_standard() -> None:
    assert resolve_mode(None).id == DEFAULT_MODE_ID


def test_eta_grows_with_distance() -> None:
    mode = MODES_BY_ID[DEFAULT_MODE_ID]
    assert eta_days(mode, 10.0) < eta_days(mode, 5000.0)


def test_eta_falls_back_to_base_without_distance() -> None:
    mode = MODES_BY_ID[DEFAULT_MODE_ID]
    assert eta_days(mode, None) == mode.base_days


def test_mode_co2_applies_factor_over_ghg_baseline() -> None:
    mode = MODES_BY_ID[GREENEST_MODE_ID]
    expected = calculate_co2_kg(50.0, 2500.0) * mode.co2_factor
    assert mode_co2_kg(mode, 50.0, 2500.0) == expected


def test_mode_co2_is_none_without_distance_or_weight() -> None:
    mode = MODES_BY_ID[DEFAULT_MODE_ID]
    assert mode_co2_kg(mode, None, 2500.0) is None
    assert mode_co2_kg(mode, 50.0, None) is None
    assert mode_co2_kg(mode, 50.0, 0.0) is None


def test_build_returns_one_option_per_mode() -> None:
    options = build_delivery_options(
        base_freight=20.0, distance_km=50.0, weight_g=2500.0
    )
    assert [o.id for o in options] == [m.id for m in MODES]


def test_build_marks_selection_and_recommendation() -> None:
    options = build_delivery_options(
        base_freight=20.0, distance_km=50.0, weight_g=2500.0, selected_id="express"
    )
    assert [o.id for o in options if o.selected] == ["express"]
    assert [o.id for o in options if o.recommended] == [GREENEST_MODE_ID]


def test_standard_option_price_equals_sample_freight() -> None:
    options = build_delivery_options(
        base_freight=20.0, distance_km=50.0, weight_g=2500.0
    )
    standard = next(o for o in options if o.id == DEFAULT_MODE_ID)
    assert standard.price == 20.0


def test_green_option_is_cheaper_and_cleaner_than_express() -> None:
    options = {
        o.id: o
        for o in build_delivery_options(
            base_freight=20.0, distance_km=50.0, weight_g=2500.0
        )
    }
    green, express = options[GREENEST_MODE_ID], options["express"]
    assert green.price < express.price
    assert green.co2_kg is not None and express.co2_kg is not None
    assert green.co2_kg < express.co2_kg
    assert green.eta_days > express.eta_days


# --- format_co2 -------------------------------------------------------------
# Regressao do bug que motivou a Sprint 4: com a amostra de 10k as distancias
# cairam e todo selo passou a exibir "~0.00 kg CO2".

def test_format_co2_uses_grams_below_ten_grams() -> None:
    assert format_co2(0.0004184) == "0,42 g"


def test_format_co2_uses_kg_above_ten_grams() -> None:
    assert format_co2(1.5) == "1,50 kg"


def test_format_co2_never_renders_a_bare_zero() -> None:
    assert format_co2(0.0004184) not in ("0,00 kg", "0.00 kg")
