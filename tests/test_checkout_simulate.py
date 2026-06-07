"""Tests do endpoint POST /api/v1/checkout/simulate.

Nao depende de Postgres: `app.dependency_overrides[get_db]` evita conexao real
e monkeypatch substitui o repositorio e o servico de selo nos namespaces do
modulo checkout.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db
from src.features.checkout.repository import CheckoutProductRow
from src.main import app
from src.schemas.sdui import SustainabilityProps

KNOWN_PREFIXES = {"05311", "01000"}

PRODUCT_FIXTURE = CheckoutProductRow(
    product_id="prod_real_1",
    seller_id="seller_close",
    seller_zip_prefix="08275",
    unit_price=199.90,
    freight_value=15.50,
    weight_g=2500.0,
    category="informatica_acessorios",
)


async def _override_get_db() -> AsyncIterator[None]:
    yield None


async def _fake_list_known_prefixes(_session: object) -> set[str]:
    return KNOWN_PREFIXES


async def _fake_fetch_product(
    _session: object, product_id: str
) -> CheckoutProductRow | None:
    if product_id == PRODUCT_FIXTURE.product_id:
        return PRODUCT_FIXTURE
    return None


async def _fake_badge_for_pair(
    _session: object,
    customer_zip_prefix: str,
    seller_zip_prefix: str,
    weight_g: float | None = None,
) -> tuple[float | None, SustainabilityProps | None]:
    d = 27.0
    return d, SustainabilityProps(
        label=f"Entrega local (~{d:.0f} km)", impact_level="green"
    )


@pytest.fixture(autouse=True)
def patch_checkout_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(
        "src.features.checkout.router.list_known_prefixes",
        _fake_list_known_prefixes,
    )
    monkeypatch.setattr(
        "src.features.checkout.router.fetch_product_for_checkout",
        _fake_fetch_product,
    )
    monkeypatch.setattr(
        "src.features.checkout.composer.build_badge_for_pair",
        _fake_badge_for_pair,
    )
    yield
    app.dependency_overrides.clear()


async def _post(body: dict) -> tuple[int, dict]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/checkout/simulate", json=body)
    return response.status_code, response.json()


# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------

async def test_valid_payload_returns_checkout_screen() -> None:
    status, body = await _post(
        {"customer_zip_prefix": "05311", "product_id": "prod_real_1", "quantity": 2}
    )
    assert status == 200
    assert body["screen_id"] == "checkout_simulate"
    assert body["context"] == "checkout"

    types = [c["type"] for c in body["components"]]
    assert "checkout_summary" in types
    assert "impact_banner" in types


async def test_totals_are_coherent() -> None:
    _, body = await _post(
        {"customer_zip_prefix": "05311", "product_id": "prod_real_1", "quantity": 2}
    )
    summary = next(c for c in body["components"] if c["type"] == "checkout_summary")
    props = summary["props"]
    assert props["subtotal"] == pytest.approx(199.90 * 2)
    assert props["freight"] == pytest.approx(15.50)
    assert props["total"] == pytest.approx(199.90 * 2 + 15.50)


async def test_impact_banner_has_coherent_co2() -> None:
    _, body = await _post(
        {"customer_zip_prefix": "05311", "product_id": "prod_real_1"}
    )
    banner = next(c for c in body["components"] if c["type"] == "impact_banner")
    props = banner["props"]
    assert props["distance_km"] == pytest.approx(27.0)
    # 27 km * (2500 g -> 0.0025 t) * 0.102 = 0.0068850 kg
    assert props["co2_kg"] == pytest.approx(27.0 * (2500.0 / 1_000_000) * 0.102)
    assert props["badge"] is not None


async def test_default_quantity_is_one() -> None:
    _, body = await _post(
        {"customer_zip_prefix": "05311", "product_id": "prod_real_1"}
    )
    summary = next(c for c in body["components"] if c["type"] == "checkout_summary")
    assert summary["props"]["quantity"] == 1


async def test_invalid_cep_returns_422() -> None:
    status, body = await _post(
        {"customer_zip_prefix": "99999", "product_id": "prod_real_1"}
    )
    assert status == 422
    assert "customer_zip_prefix" in body["detail"]


async def test_unknown_product_returns_404() -> None:
    status, body = await _post(
        {"customer_zip_prefix": "05311", "product_id": "does_not_exist"}
    )
    assert status == 404
    assert "product_id" in body["detail"]


async def test_quantity_zero_returns_422() -> None:
    status, _ = await _post(
        {"customer_zip_prefix": "05311", "product_id": "prod_real_1", "quantity": 0}
    )
    assert status == 422
