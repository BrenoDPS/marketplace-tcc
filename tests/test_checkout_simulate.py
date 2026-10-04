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
from src.features.checkout.repository import AlternativeRow, CheckoutProductRow
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

# Mesmo vendedor de PRODUCT_FIXTURE: os dois viajam numa remessa so, e o frete
# da remessa e o MAIOR dos dois (9.90 < 15.50 -> 15.50).
PRODUCT_SAME_SELLER = CheckoutProductRow(
    product_id="prod_same_seller",
    seller_id="seller_close",
    seller_zip_prefix="08275",
    unit_price=49.90,
    freight_value=9.90,
    weight_g=500.0,
    category="telefonia",
)

# Vendedor distante: segunda remessa, sem selo verde e dominando o CO2.
PRODUCT_FAR_SELLER = CheckoutProductRow(
    product_id="prod_far",
    seller_id="seller_far",
    seller_zip_prefix="60000",
    unit_price=89.90,
    freight_value=30.00,
    weight_g=1000.0,
    category="bebes",
)

# Sprint 10: o mesmo produto em dois vendedores. A oferta LONGE vem primeiro
# (`seller_a...` < `seller_b...`), como a default do ETL vinha: se o checkout
# pegasse a primeira em vez de escolher pela distancia, passaria por acidente.
PRODUCT_TWO_SELLERS = [
    CheckoutProductRow(
        product_id="prod_dois", seller_id="seller_a_longe", seller_zip_prefix="60000",
        unit_price=39.90, freight_value=25.00, weight_g=1000.0, category="relogios_presentes",
    ),
    CheckoutProductRow(
        product_id="prod_dois", seller_id="seller_b_perto", seller_zip_prefix="08275",
        unit_price=39.90, freight_value=12.00, weight_g=1000.0, category="relogios_presentes",
    ),
]

CATALOG = {
    p.product_id: [p]
    for p in (PRODUCT_FIXTURE, PRODUCT_SAME_SELLER, PRODUCT_FAR_SELLER)
} | {"prod_dois": PRODUCT_TWO_SELLERS}

# Distancias por prefixo do seller: uma perto (com selo) e uma longe (sem).
DISTANCE_BY_SELLER_ZIP = {"08275": 27.0, "60000": 2000.0}

# --- sugestoes de troca (Sprint 6) ------------------------------------------
# O cliente fica em (0, 0). No equador, 1 grau de longitude ~ 111,19 km, entao
# a longitude do candidato define a distancia de forma previsivel.
CUSTOMER_CENTROID = (0.0, 0.0)

ALTERNATIVES = [
    # Mesma categoria de PRODUCT_FAR_SELLER (2000 km), a ~500 km: reduz muito.
    AlternativeRow(
        product_id="prod_bebes_perto",
        category="bebes",
        unit_price=79.90,
        weight_g=1000.0,
        seller_id="seller_bebes_perto",
        lat=0.0,
        lng=4.5,
    ),
    # Mesma categoria, ainda mais perto, MAS quatro vezes mais pesado: emite
    # mais que o de 500 km. Existe para provar que o ranking olha distancia E
    # massa, nao so distancia.
    AlternativeRow(
        product_id="prod_bebes_pesado",
        category="bebes",
        unit_price=59.90,
        weight_g=4000.0,
        seller_id="seller_bebes_pesado",
        lat=0.0,
        lng=3.0,
    ),
    # Mesma categoria de PRODUCT_FIXTURE, porem a ~111 km — mais longe que os
    # 27 km atuais, entao nao pode ser sugerido.
    AlternativeRow(
        product_id="prod_info_longe",
        category="informatica_acessorios",
        unit_price=149.90,
        weight_g=2500.0,
        seller_id="seller_info_longe",
        lat=0.0,
        lng=1.0,
    ),
]


async def _override_get_db() -> AsyncIterator[None]:
    yield None


async def _fake_list_known_prefixes(_session: object) -> set[str]:
    return KNOWN_PREFIXES


async def _fake_fetch_products(
    _session: object, product_ids: list[str]
) -> dict[str, list[CheckoutProductRow]]:
    """Todas as ofertas do produto, ordenadas por vendedor — igual a consulta."""
    return {pid: CATALOG[pid] for pid in product_ids if pid in CATALOG}


async def _fake_compute_distance(
    _session: object, customer_zip_prefix: str, seller_zip_prefix: str
) -> float | None:
    return DISTANCE_BY_SELLER_ZIP.get(seller_zip_prefix)


async def _fake_badge_for_pair(
    _session: object,
    customer_zip_prefix: str,
    seller_zip_prefix: str,
    weight_g: float | None = None,
    co2_factor: float = 1.0,
    volume_cm3: float | None = None,
) -> tuple[float | None, SustainabilityProps | None]:
    """Espelha a regra real: selo so abaixo de 100 km, CO2 = d * massa * FE."""
    d = DISTANCE_BY_SELLER_ZIP.get(seller_zip_prefix)
    if d is None:
        return None, None
    if d >= 100.0:
        return d, None
    return d, SustainabilityProps(
        label=f"Entrega local (~{d:.0f} km)", impact_level="green"
    )


async def _fake_get_centroid(
    _session: object, zip_prefix: str
) -> tuple[float, float] | None:
    return CUSTOMER_CENTROID


async def _fake_fetch_alternatives(
    _session: object,
    categories: list[str],
    exclude_seller_ids: list[str],
    limit: int = 300,
) -> list[AlternativeRow]:
    """Espelha o filtro real: mesma categoria e vendedor fora do carrinho."""
    return [
        a
        for a in ALTERNATIVES
        if a.category in set(categories) and a.seller_id not in set(exclude_seller_ids)
    ]


@pytest.fixture(autouse=True)
def patch_checkout_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(
        "src.features.checkout.router.list_known_prefixes",
        _fake_list_known_prefixes,
    )
    monkeypatch.setattr(
        "src.features.checkout.router.fetch_products_for_checkout",
        _fake_fetch_products,
    )
    monkeypatch.setattr(
        "src.features.checkout.router.compute_distance_km",
        _fake_compute_distance,
    )
    monkeypatch.setattr(
        "src.features.checkout.composer.build_badge_for_pair",
        _fake_badge_for_pair,
    )
    monkeypatch.setattr(
        "src.features.checkout.composer.get_centroid",
        _fake_get_centroid,
    )
    monkeypatch.setattr(
        "src.features.checkout.composer.fetch_alternative_candidates",
        _fake_fetch_alternatives,
    )
    yield
    app.dependency_overrides.clear()


async def _post(body: dict) -> tuple[int, dict]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/checkout/simulate", json=body)
    return response.status_code, response.json()


async def _cart(*items: tuple[str, int], **extra) -> tuple[int, dict]:
    """Atalho: `_cart(("prod_real_1", 2))` monta o corpo do carrinho."""
    return await _post(
        {
            "customer_zip_prefix": extra.pop("cep", "05311"),
            "items": [{"product_id": pid, "quantity": q} for pid, q in items],
            **extra,
        }
    )


def _block(body: dict, block_type: str) -> dict:
    return next(c for c in body["components"] if c["type"] == block_type)


# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------

async def test_valid_payload_returns_checkout_screen() -> None:
    status, body = await _cart(("prod_real_1", 2))
    assert status == 200
    assert body["screen_id"] == "checkout_simulate"
    assert body["context"] == "checkout"

    types = [c["type"] for c in body["components"]]
    assert "checkout_summary" in types
    assert "shipment_breakdown" in types
    assert "impact_banner" in types


async def test_totals_are_coherent() -> None:
    _, body = await _cart(("prod_real_1", 2))
    props = _block(body, "checkout_summary")["props"]
    assert props["subtotal"] == pytest.approx(199.90 * 2)
    assert props["freight"] == pytest.approx(15.50)
    assert props["total"] == pytest.approx(199.90 * 2 + 15.50)


async def test_impact_banner_has_coherent_co2() -> None:
    _, body = await _cart(("prod_real_1", 1))
    props = _block(body, "impact_banner")["props"]
    assert props["distance_km"] == pytest.approx(27.0)
    # 27 km de linha reta -> 36,315 km de estrada: 21,315 de caminhao + 15 de van
    # (21,315 * 0,092 + 15 * 0,680) * 0,0025 t = 0,03040245 kg
    assert props["co2_kg"] == pytest.approx(0.03040245)
    assert props["badge"] is not None


async def test_default_quantity_is_one() -> None:
    status, body = await _post(
        {"customer_zip_prefix": "05311", "items": [{"product_id": "prod_real_1"}]}
    )
    assert status == 200
    items = _block(body, "checkout_summary")["props"]["items"]
    assert items[0]["quantity"] == 1


async def test_invalid_cep_returns_422() -> None:
    status, body = await _cart(("prod_real_1", 1), cep="99999")
    assert status == 422
    assert "customer_zip_prefix" in body["detail"]


async def test_unknown_product_returns_404() -> None:
    status, body = await _cart(("does_not_exist", 1))
    assert status == 404
    assert "product_id" in body["detail"]


async def test_quantity_zero_returns_422() -> None:
    status, _ = await _cart(("prod_real_1", 0))
    assert status == 422


async def test_empty_cart_returns_422() -> None:
    status, _ = await _post({"customer_zip_prefix": "05311", "items": []})
    assert status == 422


# ---------------------------------------------------------------------------
# Sprint 4: delivery_options
# ---------------------------------------------------------------------------

def _options(body: dict) -> dict:
    return {o["id"]: o for o in _block(body, "delivery_options")["props"]["options"]}


async def test_screen_includes_delivery_options() -> None:
    _, body = await _cart(("prod_real_1", 1))
    block = _block(body, "delivery_options")
    assert block["props"]["selected_id"] == "standard"
    assert block["props"]["note"]
    assert [a["type"] for a in block["actions"]] == ["api_call"]


async def test_default_option_freight_matches_sample_value() -> None:
    """Sem escolha explicita, o frete tem de ser o da amostra, intocado."""
    _, body = await _cart(("prod_real_1", 1))
    assert _block(body, "checkout_summary")["props"]["freight"] == pytest.approx(15.50)


async def test_choosing_green_lowers_freight_and_co2() -> None:
    _, standard = await _cart(("prod_real_1", 1))
    _, green = await _cart(("prod_real_1", 1), delivery_option="green")

    def freight(body: dict) -> float:
        return _block(body, "checkout_summary")["props"]["freight"]

    def co2(body: dict) -> float:
        return _block(body, "impact_banner")["props"]["co2_kg"]

    assert freight(green) < freight(standard)
    assert co2(green) < co2(standard)


async def test_selection_is_reflected_in_the_block() -> None:
    _, body = await _cart(("prod_real_1", 1), delivery_option="express")
    options = _options(body)
    assert options["express"]["selected"] is True
    assert options["standard"]["selected"] is False


async def test_summary_total_uses_the_chosen_freight() -> None:
    _, body = await _cart(("prod_real_1", 2), delivery_option="express")
    props = _block(body, "checkout_summary")["props"]
    assert props["total"] == pytest.approx(props["subtotal"] + props["freight"])
    assert props["freight"] > 15.50


async def test_co2_scales_with_quantity() -> None:
    """2 unidades embarcam o dobro da massa, logo emitem o dobro."""

    async def co2_for(quantity: int) -> float:
        _, body = await _cart(("prod_real_1", quantity))
        return _block(body, "impact_banner")["props"]["co2_kg"]

    assert await co2_for(2) == pytest.approx(await co2_for(1) * 2)


async def test_unknown_delivery_option_returns_422() -> None:
    status, body = await _cart(("prod_real_1", 1), delivery_option="teleporte")
    assert status == 422
    assert "delivery_option" in body["detail"]


# ---------------------------------------------------------------------------
# Sprint 5: carrinho multi-item e agregacao por vendedor
# ---------------------------------------------------------------------------

def _shipments(body: dict) -> list[dict]:
    return _block(body, "shipment_breakdown")["props"]["shipments"]


async def test_summary_lists_every_cart_line() -> None:
    _, body = await _cart(("prod_real_1", 2), ("prod_far", 1))
    items = _block(body, "checkout_summary")["props"]["items"]
    assert [(i["product_id"], i["quantity"]) for i in items] == [
        ("prod_real_1", 2),
        ("prod_far", 1),
    ]
    assert items[0]["line_total"] == pytest.approx(199.90 * 2)


async def test_same_seller_items_become_one_shipment() -> None:
    _, body = await _cart(("prod_real_1", 1), ("prod_same_seller", 3))
    shipments = _shipments(body)
    assert len(shipments) == 1
    assert shipments[0]["seller_id"] == "seller_close"
    assert set(shipments[0]["product_ids"]) == {"prod_real_1", "prod_same_seller"}
    assert shipments[0]["total_quantity"] == 4


async def test_different_sellers_become_separate_shipments() -> None:
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    assert {s["seller_id"] for s in _shipments(body)} == {"seller_close", "seller_far"}


async def test_one_freight_per_shipment_sized_by_its_largest_item() -> None:
    """Dois itens do mesmo vendedor pagam UM frete, o maior deles (15,50 e nao
    15,50 + 9,90). Somar os fretes suporia que cada item viaja sozinho."""
    _, body = await _cart(("prod_real_1", 1), ("prod_same_seller", 1))
    assert _block(body, "checkout_summary")["props"]["freight"] == pytest.approx(15.50)


async def test_freight_adds_up_across_shipments() -> None:
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    assert _block(body, "checkout_summary")["props"]["freight"] == pytest.approx(45.50)


async def test_shipment_weight_sums_the_items_it_carries() -> None:
    _, body = await _cart(("prod_real_1", 2), ("prod_same_seller", 1))
    assert _shipments(body)[0]["weight_g"] == pytest.approx(2500.0 * 2 + 500.0)


async def test_cart_co2_is_the_sum_of_its_shipments() -> None:
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    total = _block(body, "impact_banner")["props"]["co2_kg"]
    assert total == pytest.approx(sum(s["co2_kg"] for s in _shipments(body)))


async def test_co2_share_points_at_the_dominant_shipment() -> None:
    """A leitura util do carrinho: qual vendedor domina a pegada. O distante
    (2000 km) tem de dominar mesmo pesando menos que o proximo."""
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    shipments = {s["seller_id"]: s for s in _shipments(body)}
    assert shipments["seller_far"]["co2_share"] > shipments["seller_close"]["co2_share"]
    assert sum(s["co2_share"] for s in shipments.values()) == pytest.approx(1.0)


async def test_badge_only_on_the_local_shipment() -> None:
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    shipments = {s["seller_id"]: s for s in _shipments(body)}
    assert shipments["seller_close"]["badge"] is not None
    assert shipments["seller_far"]["badge"] is None


async def test_multi_shipment_banner_reports_shipments_not_one_distance() -> None:
    """Com varias remessas nao existe UMA distancia; quem detalha e o
    shipment_breakdown."""
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    props = _block(body, "impact_banner")["props"]
    assert props["distance_km"] is None
    assert "2 remessas" in props["message"]
    assert "% do CO₂" in props["message"]


async def test_repeated_product_collapses_into_one_line() -> None:
    """Duas linhas do mesmo produto dariam dois fretes na agregacao."""
    _, body = await _cart(("prod_real_1", 1), ("prod_real_1", 2))
    items = _block(body, "checkout_summary")["props"]["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 3
    assert len(_shipments(body)) == 1


async def test_delivery_options_price_the_whole_cart() -> None:
    """O comparativo e sobre o carrinho: a base e a soma dos fretes das remessas."""
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    assert _options(body)["standard"]["price"] == pytest.approx(45.50)


async def test_delivery_eta_follows_the_farthest_shipment() -> None:
    """O pedido so esta completo quando a ultima remessa chega."""
    _, near = await _cart(("prod_real_1", 1))
    _, both = await _cart(("prod_real_1", 1), ("prod_far", 1))
    assert _options(both)["standard"]["eta_days"] > _options(near)["standard"]["eta_days"]


# ---------------------------------------------------------------------------
# Sprint 6: ordenacao por pegada e sugestao de vendedor mais proximo
# ---------------------------------------------------------------------------

async def test_shipments_come_sorted_by_footprint() -> None:
    """A remessa que mais pesa vem primeiro — e onde o usuario pode agir."""
    # prod_real_1 entra ANTES no carrinho, mas emite menos que o distante.
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    shipments = _shipments(body)
    assert [s["seller_id"] for s in shipments] == ["seller_far", "seller_close"]
    assert shipments[0]["co2_kg"] > shipments[1]["co2_kg"]


async def test_alternatives_only_on_the_worst_shipment() -> None:
    """Sugerir troca nas remessas menores seria ruido: mexer nelas quase nao
    move a pegada."""
    _, body = await _cart(("prod_real_1", 1), ("prod_far", 1))
    worst, rest = _shipments(body)[0], _shipments(body)[1:]
    assert worst["alternatives"]
    assert all(s["alternatives"] == [] for s in rest)


async def test_alternative_reduces_co2_and_reports_the_saving() -> None:
    _, body = await _cart(("prod_far", 1))
    shipment = _shipments(body)[0]
    alt = shipment["alternatives"][0]

    assert alt["distance_km"] < shipment["distance_km"]
    assert alt["co2_kg"] < shipment["co2_kg"]
    assert alt["co2_saved_kg"] == pytest.approx(shipment["co2_kg"] - alt["co2_kg"])
    assert 0 < alt["saved_share"] < 1
    assert alt["replaces_product_id"] == "prod_far"


async def test_ranking_weighs_mass_not_only_distance() -> None:
    """`prod_bebes_pesado` esta mais perto (334 km vs 500 km) mas pesa 4x, entao
    emite mais. Vence quem economiza mais CO2, nao quem esta mais perto."""
    _, body = await _cart(("prod_far", 1))
    alt = _shipments(body)[0]["alternatives"][0]
    assert alt["product_id"] == "prod_bebes_perto"


async def test_no_alternative_when_nothing_is_closer() -> None:
    """O unico candidato de informatica esta a ~111 km, mais longe que os 27 km
    atuais. Sugerir uma troca que piora seria pior do que nao sugerir nada."""
    _, body = await _cart(("prod_real_1", 1))
    assert _shipments(body)[0]["alternatives"] == []


async def test_alternative_never_comes_from_a_seller_already_in_the_cart() -> None:
    _, body = await _cart(("prod_far", 1), ("prod_real_1", 1))
    sellers_in_cart = {s["seller_id"] for s in _shipments(body)}
    for alt in _shipments(body)[0]["alternatives"]:
        assert alt["seller_id"] not in sellers_in_cart


async def test_alternative_carries_price_so_the_trade_off_is_visible() -> None:
    """A troca nao e equivalente — e outro produto da mesma categoria. Sem
    preco e distancia na tela, o usuario decidiria no escuro."""
    _, body = await _cart(("prod_far", 1))
    alt = _shipments(body)[0]["alternatives"][0]
    assert alt["price"] == pytest.approx(79.90)
    assert alt["title"] == "Bebes"


# ---------------------------------------------------------------------------
# Sprint 10: o checkout entrega da MESMA oferta que a vitrine mostrou
# ---------------------------------------------------------------------------

async def test_checkout_entrega_do_vendedor_mais_proximo_nao_da_oferta_default() -> None:
    """Antes: o detalhe dizia "sai de ~2 km; comprar do mais proximo evita
    0,10 kg" e o checkout entregava do vendedor a 2.485 km, emitindo esses
    0,10 kg. A oferta default (a primeira) e a longe; vale a perto."""
    status, body = await _cart(("prod_dois", 1))
    assert status == 200

    remessa = next(c for c in body["components"] if c["type"] == "shipment_breakdown")
    (envio,) = remessa["props"]["shipments"]
    assert envio["seller_id"] == "seller_b_perto"
    assert envio["distance_km"] == 27.0
    assert envio["freight"] == 12.00, "o frete e o da oferta escolhida"
