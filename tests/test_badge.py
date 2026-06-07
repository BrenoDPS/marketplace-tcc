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
    badge = build_sustainability_props(0.0)
    assert badge is not None
    assert "0 km" in badge.label


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
