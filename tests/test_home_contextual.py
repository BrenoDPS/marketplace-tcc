"""Tests do endpoint /api/v1/home.

Nao depende de Postgres. Usamos `app.dependency_overrides[get_db]` para evitar
qualquer conexao real e monkeypatch das funcoes de repositorio/servico nos
namespaces onde foram importadas pelos modulos do home_contextual.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db
from src.features.home_contextual.repository import CategoryRow, ProductRow
from src.main import app
from src.schemas.sdui import SustainabilityProps

# Demo: customer mora em "01000" e ha 3 sellers conhecidos
KNOWN_PREFIXES = {"01000", "20000", "60000"}

PRODUCTS_FIXTURE = [
    ProductRow(
        product_id="prod_real_1",
        seller_id="seller_close",
        seller_zip_prefix="01001",
        price=199.90,
        weight_g=500.0,
        category="informatica_acessorios",
    ),
    ProductRow(
        product_id="prod_real_2",
        seller_id="seller_far",
        seller_zip_prefix="60000",
        price=89.50,
        weight_g=300.0,
        category="informatica_acessorios",
    ),
    # Categoria diferente e seller sem centroide: exercita filtro e o
    # "sem distancia vai para o fim" da ordenacao do conscious_buyer.
    ProductRow(
        product_id="prod_beauty",
        seller_id="seller_unknown",
        seller_zip_prefix="99999",
        price=49.90,
        weight_g=200.0,
        category="beleza_saude",
    ),
]

CATEGORIES_FIXTURE = [
    CategoryRow(slug="informatica_acessorios", product_count=2),
    CategoryRow(slug="beleza_saude", product_count=1),
]


async def _override_get_db() -> AsyncIterator[None]:
    yield None


async def _fake_list_known_prefixes(_session: object) -> set[str]:
    return KNOWN_PREFIXES


async def _fake_list_categories(
    _session: object, limit: int | None = None
) -> list[CategoryRow]:
    return CATEGORIES_FIXTURE[:limit] if limit else CATEGORIES_FIXTURE


async def _fake_fetch_products(
    _session: object,
    category: str | None = None,
    limit: int = 6,
    search: str | None = None,
) -> list[ProductRow]:
    """Espelha o filtro real: categoria exata e busca sobre o nome da categoria."""
    rows = PRODUCTS_FIXTURE
    if category is not None:
        rows = [r for r in rows if r.category == category]
    if search:
        rows = [
            r for r in rows if search in (r.category or "").replace("_", " ").lower()
        ]
    return rows[:limit]


async def _fake_badge_close(
    _session: object,
    customer_zip_prefix: str,
    seller_zip_prefix: str,
    weight_g: float | None = None,
) -> tuple[float | None, SustainabilityProps | None]:
    """Sellers em zip que comeca com '0100' -> proximo (50km); outros -> longe (500km)."""
    if seller_zip_prefix.startswith("0100"):
        d = 50.0
        return d, SustainabilityProps(label=f"Entrega local (~{d:.0f} km)", impact_level="green")
    return 500.0, None


# Distancias por seller para testar a ordenacao do conscious_buyer:
# prod_real_2 (60000) deve ficar ANTES de prod_real_1 (01001).
_DISTANCE_BY_SELLER = {"01001": 80.0, "60000": 20.0}


async def _fake_compute_distance(
    _session: object,
    customer_zip_prefix: str,
    seller_zip_prefix: str,
) -> float | None:
    return _DISTANCE_BY_SELLER.get(seller_zip_prefix)


@pytest.fixture(autouse=True)
def patch_home_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(
        "src.features.home_contextual.router.list_known_prefixes",
        _fake_list_known_prefixes,
    )
    monkeypatch.setattr(
        "src.features.home_contextual.composer.fetch_products_for_home",
        _fake_fetch_products,
    )
    monkeypatch.setattr(
        "src.features.home_contextual.composer.list_categories",
        _fake_list_categories,
    )
    monkeypatch.setattr(
        "src.features.home_contextual.router.list_categories",
        _fake_list_categories,
    )
    monkeypatch.setattr(
        "src.features.home_contextual.composer.build_badge_for_pair",
        _fake_badge_close,
    )
    monkeypatch.setattr(
        "src.features.home_contextual.composer.compute_distance_km",
        _fake_compute_distance,
    )
    yield
    app.dependency_overrides.clear()


async def _get(path: str) -> tuple[int, dict | list]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)
    return response.status_code, response.json()


# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------

async def test_missing_customer_zip_prefix_returns_422() -> None:
    status, _ = await _get("/api/v1/home")
    assert status == 422


async def test_invalid_customer_zip_prefix_returns_422() -> None:
    status, body = await _get("/api/v1/home?customer_zip_prefix=99999")
    assert status == 422
    assert isinstance(body, dict)
    assert "customer_zip_prefix" in body["detail"]


async def test_valid_prefix_returns_screen_with_real_products() -> None:
    status, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&context=electronics_expert"
    )
    assert status == 200
    assert isinstance(body, dict)
    assert body["schema_version"] == 1
    assert body["context"] == "electronics_expert"

    product_ids = [
        c["props"]["product_id"]
        for c in body["components"]
        if c["type"] == "product_card"
    ]
    assert "prod_real_1" in product_ids
    assert "prod_real_2" in product_ids


async def test_badge_present_for_nearby_seller() -> None:
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&context=electronics_expert"
    )
    assert isinstance(body, dict)
    cards = [c for c in body["components"] if c["type"] == "product_card"]
    close_card = next(c for c in cards if c["props"]["product_id"] == "prod_real_1")
    assert close_card["props"]["badge"] is not None
    assert close_card["props"]["badge"]["impact_level"] == "green"


async def test_badge_null_for_distant_seller() -> None:
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&context=electronics_expert"
    )
    assert isinstance(body, dict)
    cards = [c for c in body["components"] if c["type"] == "product_card"]
    far_card = next(c for c in cards if c["props"]["product_id"] == "prod_real_2")
    assert far_card["props"]["badge"] is None


async def test_sdui_envelope_preserved() -> None:
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&context=default"
    )
    assert isinstance(body, dict)
    assert {"schema_version", "screen_id", "context", "components"} <= body.keys()
    for block in body["components"]:
        assert {"type", "version", "props", "actions"} <= block.keys()
        assert isinstance(block["actions"], list)


async def test_default_context_has_default_hero() -> None:
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000"
    )
    assert isinstance(body, dict)
    hero = next(c for c in body["components"] if c["type"] == "hero_banner")
    assert hero["props"]["title"] == "Olist Marketplace"


async def test_conscious_buyer_orders_cards_by_proximity() -> None:
    status, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&context=conscious_buyer"
    )
    assert status == 200
    assert isinstance(body, dict)
    assert body["context"] == "conscious_buyer"

    product_ids = [
        c["props"]["product_id"]
        for c in body["components"]
        if c["type"] == "product_card"
    ]
    # prod_real_2 (20 km) antes de prod_real_1 (80 km); prod_beauty nao tem
    # centroide e por isso fecha a lista.
    assert product_ids == ["prod_real_2", "prod_real_1", "prod_beauty"]


# ---------------------------------------------------------------------------
# Sprint 5: busca e categorias
# ---------------------------------------------------------------------------

def _cards(body: dict) -> list[str]:
    return [
        c["props"]["product_id"] for c in body["components"] if c["type"] == "product_card"
    ]


def _grid(body: dict) -> dict:
    return next(c for c in body["components"] if c["type"] == "category_grid")


def _hero(body: dict) -> dict:
    return next(c for c in body["components"] if c["type"] == "hero_banner")


async def test_home_includes_category_grid() -> None:
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000")
    assert isinstance(body, dict)
    grid = _grid(body)
    assert [c["slug"] for c in grid["props"]["categories"]] == [
        "informatica_acessorios",
        "beleza_saude",
    ]
    assert grid["props"]["categories"][0]["label"] == "Informatica Acessorios"
    assert grid["props"]["categories"][0]["product_count"] == 2


async def test_category_item_carries_its_own_navigate_action() -> None:
    """Cada categoria navega para um caminho diferente: a acao vive no item,
    e o caminho ja vem montado com CEP e contexto pelo servidor."""
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&context=beauty_lover")
    assert isinstance(body, dict)
    item = _grid(body)["props"]["categories"][0]
    action = item["actions"][0]
    assert action["type"] == "navigate"
    path = action["payload"]["path"]
    assert "customer_zip_prefix=01000" in path
    assert "context=beauty_lover" in path
    assert "category=informatica_acessorios" in path


async def test_category_filter_narrows_the_cards() -> None:
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&category=beleza_saude"
    )
    assert isinstance(body, dict)
    assert _cards(body) == ["prod_beauty"]


async def test_selected_category_is_flagged_in_the_grid() -> None:
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&category=beleza_saude"
    )
    assert isinstance(body, dict)
    selected = [c["slug"] for c in _grid(body)["props"]["categories"] if c["selected"]]
    assert selected == ["beleza_saude"]


async def test_unknown_category_returns_422() -> None:
    status, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&category=categoria_inexistente"
    )
    assert status == 422
    assert isinstance(body, dict)
    assert "category" in body["detail"]


async def test_search_matches_category_name() -> None:
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&q=beleza")
    assert isinstance(body, dict)
    assert _cards(body) == ["prod_beauty"]


async def test_search_ignores_accents_and_case() -> None:
    """"informática" e "informatica" tem de chegar iguais na consulta."""
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&q=INFORM%C3%81TICA")
    assert isinstance(body, dict)
    assert _cards(body) == ["prod_real_1", "prod_real_2"]


async def test_search_hero_reports_what_was_searched() -> None:
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&q=beleza")
    assert isinstance(body, dict)
    hero = _hero(body)
    assert hero["props"]["title"] == "Busca: beleza"
    assert "1 produto" in hero["props"]["subtitle"]


async def test_filtered_hero_offers_a_way_back() -> None:
    """Sem uma acao de limpar o filtro, o cliente teria de inventar a URL de
    volta — que e exatamente o que o SDUI evita."""
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&q=beleza")
    assert isinstance(body, dict)
    hero = _hero(body)
    assert hero["props"]["cta_label"] == "Ver tudo"
    path = hero["actions"][0]["payload"]["path"]
    assert "q=" not in path and "category=" not in path


async def test_unfiltered_hero_keeps_the_context_cta() -> None:
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000")
    assert isinstance(body, dict)
    assert _hero(body)["props"]["cta_label"] is None


async def test_search_without_results_says_so_instead_of_falling_back() -> None:
    """Filtro explicito que nao casa devolve vitrine vazia. Mostrar produtos
    aleatorios seria mentir sobre o resultado da busca."""
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&q=tratores")
    assert isinstance(body, dict)
    assert _cards(body) == []
    assert "Nenhum produto" in _hero(body)["props"]["subtitle"]


async def test_blank_search_is_treated_as_no_search() -> None:
    """So espacos: normaliza para string vazia. Anunciar 'Busca: ' sobre uma
    vitrine que na verdade nao esta filtrada seria pior do que ignorar."""
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&q=%20%20%20")
    assert isinstance(body, dict)
    assert _hero(body)["props"]["title"] == "Olist Marketplace"
    assert _cards(body)


async def test_punctuation_search_is_a_real_search_with_no_results() -> None:
    """`###` sobrevive a normalizacao (e ASCII) e por isso e busca de verdade:
    zero resultados, nao vitrine sem filtro."""
    _, body = await _get("/api/v1/home?customer_zip_prefix=01000&q=%23%23%23")
    assert isinstance(body, dict)
    assert _cards(body) == []
    assert _hero(body)["props"]["title"] == "Busca: ###"


async def test_search_composes_with_conscious_buyer_ranking() -> None:
    """Filtrar nao desliga a ordenacao por proximidade: da "informatica mais
    perto de mim"."""
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&context=conscious_buyer&q=informatica"
    )
    assert isinstance(body, dict)
    assert _cards(body) == ["prod_real_2", "prod_real_1"]


async def test_explicit_category_overrides_context_category() -> None:
    """`beauty_lover` mapeia para beleza_saude, mas o pedido do usuario vence."""
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000"
        "&context=beauty_lover&category=informatica_acessorios"
    )
    assert isinstance(body, dict)
    assert _cards(body) == ["prod_real_1", "prod_real_2"]


async def test_product_card_has_checkout_api_call() -> None:
    _, body = await _get(
        "/api/v1/home?customer_zip_prefix=01000&context=default"
    )
    assert isinstance(body, dict)
    cards = [c for c in body["components"] if c["type"] == "product_card"]
    assert cards
    actions = cards[0]["actions"]
    api_calls = [a for a in actions if a["type"] == "api_call"]
    assert any(
        a["payload"]["path"] == "/api/v1/checkout/simulate"
        and a["payload"]["method"] == "POST"
        for a in api_calls
    )
