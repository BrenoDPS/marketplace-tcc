"""Tests de GET /api/v1/products/{product_id}.

Nao depende de Postgres: `dependency_overrides` + monkeypatch nos repositorios,
mesmo padrao dos outros endpoints.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db
from src.features.product_detail.repository import ProductDetailRow
from src.main import app
from src.schemas.sdui import SustainabilityProps

KNOWN_PREFIXES = {"05311", "01000"}

PRODUCT = ProductDetailRow(
    product_id="prod_real_1",
    category="informatica_acessorios",
    weight_g=2500.0,
    rating=4.25,
    review_count=8,
    unit_price=199.90,
    seller_id="seller_close",
    seller_zip_prefix="08275",
    seller_city="sao paulo",
    seller_state="SP",
)

# Produto sem nenhum pedido avaliado: a tela precisa OMITIR, nao inventar.
PRODUCT_UNRATED = ProductDetailRow(
    product_id="prod_sem_nota",
    category="bebes",
    weight_g=800.0,
    rating=None,
    review_count=0,
    unit_price=59.90,
    seller_id="seller_far",
    seller_zip_prefix="60000",
    seller_city=None,
    seller_state=None,
)

CATALOG = {p.product_id: p for p in (PRODUCT, PRODUCT_UNRATED)}
DISTANCE_BY_SELLER_ZIP = {"08275": 27.0, "60000": 2000.0}


async def _override_get_db() -> AsyncIterator[None]:
    yield None


async def _fake_list_known_prefixes(_session: object) -> set[str]:
    return KNOWN_PREFIXES


async def _fake_fetch(_session: object, product_id: str) -> ProductDetailRow | None:
    return CATALOG.get(product_id)


async def _fake_badge_for_pair(
    _session: object,
    customer_zip_prefix: str,
    seller_zip_prefix: str,
    weight_g: float | None = None,
    co2_factor: float = 1.0,
) -> tuple[float | None, SustainabilityProps | None]:
    d = DISTANCE_BY_SELLER_ZIP.get(seller_zip_prefix)
    if d is None or d >= 100.0:
        return d, None
    return d, SustainabilityProps(
        label=f"Entrega local (~{d:.0f} km)", impact_level="green"
    )


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(
        "src.features.product_detail.router.list_known_prefixes",
        _fake_list_known_prefixes,
    )
    monkeypatch.setattr(
        "src.features.product_detail.router.fetch_product_detail", _fake_fetch
    )
    monkeypatch.setattr(
        "src.features.product_detail.composer.build_badge_for_pair",
        _fake_badge_for_pair,
    )
    yield
    app.dependency_overrides.clear()


async def _get(path: str) -> tuple[int, dict]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)
    return response.status_code, response.json()


def _block(body: dict, block_type: str) -> dict:
    return next(c for c in body["components"] if c["type"] == block_type)


# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------

async def test_returns_a_screen_response() -> None:
    status, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    assert status == 200
    assert body["screen_id"] == "product_detail"
    assert body["context"] == "product"
    assert [c["type"] for c in body["components"]] == ["product_detail", "impact_banner"]


async def test_detail_carries_real_dataset_fields() -> None:
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    props = _block(body, "product_detail")["props"]
    assert props["title"] == "Informatica Acessorios"
    assert props["price"] == pytest.approx(199.90)
    assert props["weight_g"] == pytest.approx(2500.0)
    assert props["seller_city"] == "sao paulo"
    assert props["seller_state"] == "SP"


async def test_rating_comes_from_the_dataset() -> None:
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    props = _block(body, "product_detail")["props"]
    assert props["rating"] == pytest.approx(4.25)
    assert props["review_count"] == 8


async def test_product_without_reviews_omits_the_rating() -> None:
    """Nenhum pedido avaliado => `rating` nulo. Preencher com um valor
    'plausivel' seria inventar dado numa tela sobre credibilidade."""
    _, body = await _get("/api/v1/products/prod_sem_nota?customer_zip_prefix=05311")
    props = _block(body, "product_detail")["props"]
    assert props["rating"] is None
    assert props["review_count"] == 0


async def test_badge_and_impact_reflect_the_customer_distance() -> None:
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    assert _block(body, "product_detail")["props"]["badge"] is not None
    banner = _block(body, "impact_banner")["props"]
    assert banner["distance_km"] == pytest.approx(27.0)
    # 27 km * (2500 g -> 0.0025 t) * 0.102
    assert banner["co2_kg"] == pytest.approx(27.0 * (2500.0 / 1_000_000) * 0.102)
    assert "27 km" in banner["message"]
    assert "sao paulo" in banner["message"]


async def test_distant_seller_has_no_badge() -> None:
    _, body = await _get("/api/v1/products/prod_sem_nota?customer_zip_prefix=05311")
    assert _block(body, "product_detail")["props"]["badge"] is None


async def test_detail_carries_the_checkout_action() -> None:
    """A tela de detalhe tem de dizer COMO comprar — senao o cliente precisaria
    lembrar da acao que veio no card."""
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    actions = _block(body, "product_detail")["actions"]
    assert any(
        a["type"] == "api_call" and a["payload"]["body_key"] == "checkout"
        for a in actions
    )


async def test_unknown_product_returns_404() -> None:
    status, body = await _get("/api/v1/products/nao_existe?customer_zip_prefix=05311")
    assert status == 404
    assert "product_id" in body["detail"]


async def test_unknown_cep_returns_422() -> None:
    status, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=99999")
    assert status == 422
    assert "customer_zip_prefix" in body["detail"]


async def test_missing_cep_returns_422() -> None:
    status, _ = await _get("/api/v1/products/prod_real_1")
    assert status == 422
