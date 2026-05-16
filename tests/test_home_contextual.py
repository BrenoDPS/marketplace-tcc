from httpx import ASGITransport, AsyncClient

from src.main import app


async def _get(path: str) -> tuple[int, dict]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)
    return response.status_code, response.json()


async def test_home_returns_200_with_default_context() -> None:
    status, body = await _get("/api/v1/home")
    assert status == 200
    assert body["screen_id"] == "home"
    assert body["context"] == "default"
    assert body["schema_version"] == 1
    assert isinstance(body["components"], list)
    assert len(body["components"]) > 0


async def test_home_electronics_context() -> None:
    status, body = await _get("/api/v1/home?context=electronics_expert")
    assert status == 200
    assert body["context"] == "electronics_expert"
    types = [c["type"] for c in body["components"]]
    assert "hero_banner" in types
    assert "product_card" in types


async def test_home_beauty_context() -> None:
    status, body = await _get("/api/v1/home?context=beauty_lover")
    assert status == 200
    assert body["context"] == "beauty_lover"
    types = [c["type"] for c in body["components"]]
    assert "hero_banner" in types
    assert "product_card" in types


async def test_home_response_matches_sdui_envelope() -> None:
    status, body = await _get("/api/v1/home?context=electronics_expert")
    assert status == 200
    assert "schema_version" in body
    assert "screen_id" in body
    assert "context" in body
    assert "components" in body
    for component in body["components"]:
        assert "type" in component
        assert "version" in component
        assert "props" in component
        assert "actions" in component
        assert isinstance(component["actions"], list)


async def test_product_card_carries_green_badge() -> None:
    """Cumpre regra do .cursorrules: ProductCard deve carregar selo de Logistica Verde."""
    status, body = await _get("/api/v1/home?context=electronics_expert")
    assert status == 200
    product_cards = [c for c in body["components"] if c["type"] == "product_card"]
    assert len(product_cards) > 0
    assert any(
        card["props"].get("badge", {}).get("impact_level") == "green"
        for card in product_cards
    )
